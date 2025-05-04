"""
Public re‑exports for the *core* layer.

from autoclicker.core import events, runner, undo
"""

from importlib import metadata as _metadata

from . import events, runner, undo

__all__ = ["events", "runner", "undo", "__version__"]

try:  # will be missing in editable installs
    __version__: str = _metadata.version("autoclicker")
except _metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0.dev"
