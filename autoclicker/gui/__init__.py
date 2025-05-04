"""
User‑facing windows.  Importing *main* will pop up the root window.

`python -m autoclicker.gui.main` is the recommended entry point.
"""

from . import main, editor, overlay, presets

__all__ = ["main", "editor", "overlay", "presets"]
