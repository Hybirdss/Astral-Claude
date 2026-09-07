"""Observation-bound actions, independent of OS and MCP transport."""

import io
import math
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Annotated, Literal

from PIL import Image
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

OBSERVATION_TTL_SECONDS = 120
MIN_DIMENSION = 640
MAX_DIMENSION = 2400
DEFAULT_DIMENSION = 1600

ActionKind = Literal["click", "move", "drag", "scroll", "key", "type_text", "paste_text", "wait"]
POINTER_ACTIONS = {"click", "move", "drag", "scroll"}


def _round_pixel(value):
    """Accept numeric coordinates such as 480.0 or 480.4; bool/str stay rejected by strict mode."""
    if isinstance(value, float) and math.isfinite(value):
        return int(round(value))
    return value


Pixel = Annotated[int, BeforeValidator(_round_pixel)]


class Action(BaseModel):
    """One desktop input operation, expressed in pixels of the latest returned screenshot."""

    model_config = ConfigDict(extra="forbid", strict=True)
    action: ActionKind = Field(description="One of the eight supported operations")
    x: Pixel | None = Field(default=None, description="Column in the latest screenshot's pixels")
    y: Pixel | None = Field(default=None, description="Row in the latest screenshot's pixels")
    end_x: Pixel | None = Field(default=None, description="Drag destination column (same space)")
    end_y: Pixel | None = Field(default=None, description="Drag destination row (same space)")
    button: Literal["left", "middle", "right"] = Field(default="left", description="Mouse button")
    clicks: int = Field(default=1, ge=1, le=2, description="1 for click, 2 for double-click")
    amount: int = Field(default=0, ge=-20, le=20, description="scroll notches; positive is up")
    keys: list[str] = Field(
        default_factory=list, max_length=5, description="PyAutoGUI key names pressed together"
    )
    text: str = Field(default="", max_length=10000, description="type_text (ASCII) or paste_text")
    duration: float = Field(
        default=0.5,
        ge=0.1,
        le=10,
        description="Seconds: wait length, drag duration, or clipboard settle time for paste_text",
    )

    @model_validator(mode="after")
    def check_action(self):
        if self.action in POINTER_ACTIONS and (self.x is None or self.y is None):
            raise ValueError("This action requires x and y from the latest screenshot.")
        if self.action == "drag" and (self.end_x is None or self.end_y is None):
            raise ValueError("Drag requires end_x and end_y.")
        if self.action == "key" and not self.keys:
            raise ValueError("Key requires a nonempty keys list.")
        if self.action == "type_text" and any(
            ord(c) > 126 or (ord(c) < 32 and c not in "\n\t") for c in self.text
        ):
            raise ValueError("type_text supports ASCII only; use paste_text for Unicode.")
        if not math.isfinite(self.duration):
            raise ValueError("duration must be finite.")
        return self


@dataclass
class Observation:
    id: str
    created: float
    image_size: tuple[int, int]
    desktop_size: tuple[int, int]
    png: bytes
    max_dimension: int = DEFAULT_DIMENSION

    def point(self, x, y):
        width, height = self.image_size
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"Point outside screenshot bounds {width}x{height}.")
        dw, dh = self.desktop_size
        return min(dw - 1, int(x * dw / width)), min(dh - 1, int(y * dh / height))

    def metadata(self):
        return {
            "observation_id": self.id,
            "image_size": list(self.image_size),
            "desktop_size": list(self.desktop_size),
            "coordinate_space": "Use pixels in this returned image; server maps them to desktop.",
            "expires_after_seconds": OBSERVATION_TTL_SECONDS,
        }


class Controller:
    """Issues single-use observations and executes actions grounded in the latest one."""

    def __init__(self, backend_factory, clock=time.monotonic):
        self.factory = backend_factory
        self.backend = None
        self.clock = clock
        self.lock = threading.Lock()
        self.current = None

    def _backend(self):
        if self.backend is None:
            self.backend = self.factory()
        return self.backend

    def _observe(self, max_dimension=DEFAULT_DIMENSION):
        self.current = None
        backend = self._backend()
        size = backend.size()
        frame = backend.capture()
        if backend.size() != size:
            raise RuntimeError("Display changed during capture. Observe again.")
        if min(*size, *frame.size) <= 0:
            raise RuntimeError("Invalid display dimensions.")
        # Retina may supply twice as many pixels as logical input coordinates.
        if abs((frame.width / size[0]) / (frame.height / size[1]) - 1) > 0.02:
            raise RuntimeError("Capture/input aspect ratios differ. Use a single primary display.")
        frame.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        frame.save(output, format="PNG")
        obs = Observation(
            uuid.uuid4().hex, self.clock(), frame.size, size, output.getvalue(), max_dimension
        )
        self.current = obs
        return obs

    def observe(self, max_dimension=DEFAULT_DIMENSION):
        if type(max_dimension) is not int or not MIN_DIMENSION <= max_dimension <= MAX_DIMENSION:
            raise ValueError(f"max_dimension must be between {MIN_DIMENSION} and {MAX_DIMENSION}.")
        with self.lock:
            return self._observe(max_dimension)

    def act(self, observation_id: str, action: Action):
        with self.lock:
            obs = self.current
            if obs is None or obs.id != observation_id:
                raise ValueError("Missing, consumed, or stale observation. Call desktop_observe.")
            if self.clock() - obs.created > OBSERVATION_TTL_SECONDS:
                self.current = None
                raise ValueError("Observation expired. Call desktop_observe.")
            if self._backend().size() != obs.desktop_size:
                self.current = None
                raise ValueError("Display size changed. Call desktop_observe.")
            payload = action.model_dump()
            if action.action in POINTER_ACTIONS:
                payload["x"], payload["y"] = obs.point(action.x, action.y)
            if action.action == "drag":
                payload["end_x"], payload["end_y"] = obs.point(action.end_x, action.end_y)
            # An exception can occur after input was delivered. Never replay the old ID.
            self.current = None
            self.backend.execute(payload)
            # Keep the resolution the caller chose, e.g. 2400 for small UI text.
            return self._observe(obs.max_dimension)
