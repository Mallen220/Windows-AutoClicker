"""
Miscellaneous helpers that do **not** touch the GUI.

Sub‑modules:

* :pymod:`autoclicker.util.platform`   – OS sniffing, resource paths
* :pymod:`autoclicker.util.timing`     – millisecond helpers
"""

from . import platform, timing

__all__ = ["platform", "timing"]
