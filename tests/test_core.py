import pytest
from PIL import Image
from pydantic import ValidationError

from astral_claude.core import Action, Controller


class FakeDesktop:
    def __init__(self, size=(1920, 1080), pixels=(3840, 2160)):
        self.dimensions = size
        self.pixels = pixels
        self.actions = []
        self.fail = False

    def size(self):
        return self.dimensions

    def capture(self):
        return Image.new("RGB", self.pixels, "green")

    def execute(self, action):
        self.actions.append(action)
        if self.fail:
            raise RuntimeError("Failure after input")


@pytest.fixture
def desktop():
    backend = FakeDesktop()
    return Controller(lambda: backend), backend


def test_retina_and_resized_coordinates_map_once(desktop):
    controller, backend = desktop
    obs = controller.observe()
    assert obs.image_size == (1600, 900)
    new = controller.act(obs.id, Action(action="click", x=800, y=450))
    assert (backend.actions[0]["x"], backend.actions[0]["y"]) == (960, 540)
    assert new.id != obs.id
    assert new.png.startswith(b"\x89PNG")


def test_act_keeps_the_requested_resolution(desktop):
    controller, backend = desktop
    obs = controller.observe(2400)
    assert obs.image_size == (2400, 1350)
    new = controller.act(obs.id, Action(action="key", keys=["enter"]))
    assert new.image_size == (2400, 1350)
    assert controller.observe().image_size == (1600, 900)


@pytest.mark.parametrize("max_dimension", [639, 2401])
def test_observe_rejects_out_of_range_dimension(desktop, max_dimension):
    controller, _ = desktop
    with pytest.raises(ValueError, match="max_dimension"):
        controller.observe(max_dimension)


def test_repeated_and_superseded_ids_are_rejected(desktop):
    controller, backend = desktop
    old = controller.observe()
    current = controller.observe()
    with pytest.raises(ValueError, match="stale"):
        controller.act(old.id, Action(action="key", keys=["enter"]))
    controller.act(current.id, Action(action="key", keys=["enter"]))
    with pytest.raises(ValueError, match="stale"):
        controller.act(current.id, Action(action="key", keys=["enter"]))
    assert len(backend.actions) == 1


def test_expired_id_does_not_deliver_input(desktop):
    controller, backend = desktop
    now = [0]
    controller.clock = lambda: now[0]
    obs = controller.observe()
    now[0] = 121
    with pytest.raises(ValueError, match="expired"):
        controller.act(obs.id, Action(action="click", x=20, y=20))
    assert not backend.actions


def test_display_change_does_not_deliver_input(desktop):
    controller, backend = desktop
    obs = controller.observe()
    backend.dimensions = (1280, 800)
    with pytest.raises(ValueError, match="Display size changed"):
        controller.act(obs.id, Action(action="key", keys=["enter"]))
    assert not backend.actions


@pytest.mark.parametrize("point", [(-1, 4), (1600, 4), (4, 900)])
def test_out_of_bounds_rejected(desktop, point):
    controller, backend = desktop
    obs = controller.observe()
    with pytest.raises(ValueError, match="bounds"):
        controller.act(obs.id, Action(action="click", x=point[0], y=point[1]))
    assert not backend.actions


def test_failed_action_cannot_be_replayed(desktop):
    controller, backend = desktop
    obs = controller.observe()
    backend.fail = True
    with pytest.raises(RuntimeError, match="after input"):
        controller.act(obs.id, Action(action="click", x=200, y=100))
    with pytest.raises(ValueError, match="stale"):
        controller.act(obs.id, Action(action="click", x=200, y=100))
    assert len(backend.actions) == 1


def test_drag_maps_both_endpoints(desktop):
    controller, backend = desktop
    obs = controller.observe()
    controller.act(obs.id, Action(action="drag", x=100, y=200, end_x=300, end_y=400))
    sent = backend.actions[0]
    assert (sent["x"], sent["y"], sent["end_x"], sent["end_y"]) == (120, 240, 360, 480)


def test_mismatched_capture_geometry_rejected(desktop):
    controller, backend = desktop
    backend.pixels = (1000, 1000)
    with pytest.raises(RuntimeError, match="aspect ratios"):
        controller.observe()


def test_numeric_coordinates_round_to_whole_pixels():
    assert Action(action="click", x=480.4, y=319.6).model_dump()["x"] == 480
    assert Action(action="click", x=480.4, y=319.6).y == 320
    parsed = Action.model_validate_json(
        '{"action": "drag", "x": 1.0, "y": 2.0, "end_x": 3.5, "end_y": 4}'
    )
    assert (parsed.x, parsed.y, parsed.end_x, parsed.end_y) == (1, 2, 4, 4)


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "click"},
        {"action": "drag", "x": 1, "y": 2},
        {"action": "key"},
        {"action": "type_text", "text": "안녕"},
        {"action": "wait", "duration": float("inf")},
        {"action": "click", "x": True, "y": 2},
        {"action": "click", "x": "480", "y": 2},
        {"action": "click", "x": float("nan"), "y": 2},
        {"action": "click", "x": float("inf"), "y": 2},
        {"action": "click", "x": 1, "y": 2, "clicks": 3},
        {"action": "click", "x": 1, "y": 2, "unknown": "field"},
    ],
)
def test_bad_actions_rejected_before_execution(payload):
    with pytest.raises(ValidationError):
        Action(**payload)


def test_unicode_paste_is_an_explicit_action():
    assert Action(action="paste_text", text="Hello 안녕 café").text.endswith("café")


def test_concurrent_same_id_delivers_at_most_once(desktop):
    from concurrent.futures import ThreadPoolExecutor

    controller, backend = desktop
    obs = controller.observe()

    def click():
        try:
            controller.act(obs.id, Action(action="click", x=20, y=20))
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: click(), range(2)))
    assert sorted(results) == [False, True]
    assert len(backend.actions) == 1


@pytest.mark.parametrize("dimension", [True, "800", 800.5, float("nan"), None])
def test_invalid_dimension_leaves_existing_observation_usable(desktop, dimension):
    controller, backend = desktop
    obs = controller.observe()
    with pytest.raises(ValueError, match="max_dimension"):
        controller.observe(dimension)
    controller.act(obs.id, Action(action="click", x=10, y=20))
    assert len(backend.actions) == 1
