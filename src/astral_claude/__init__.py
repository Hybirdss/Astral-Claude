"""Astral-Claude's local desktop execution layer."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("astral-claude")
except PackageNotFoundError:  # running from a source tree without an installed distribution
    __version__ = "0+unknown"
