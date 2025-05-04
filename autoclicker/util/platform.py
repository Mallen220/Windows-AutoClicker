"""
Cross‑platform helpers the rest of the code can rely on.

The functions here intentionally return **very small** pieces of
information so that higher‑level code does not have to know about the
messy details of `sys.platform`, Windows DLL quirks, or macOS `.icns`
file conventions.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = ["OS", "current_os", "is_windows", "icon_path"]


class OS(str):
    """Strongly‑typed enum‑like for `"windows"`, `"mac"`, `"linux"`."""


def _detect() -> OS:
    if sys.platform.startswith("win"):
        return OS("windows")
    if sys.platform.startswith("darwin"):
        return OS("mac")
    return OS("linux")


#: Cached value of :func:`_detect`
current_os: OS = _detect()


def is_windows() -> bool:  # kept as a convenience alias
    """Return *True* if running on any flavour of Windows."""
    return current_os == "windows"


# --------------------------------------------------------------------------- #
# Resource helpers
# --------------------------------------------------------------------------- #


def icon_path(basename: str) -> str:
    """
    Return absolute path to an icon file *basename* adjusted for the OS.

    Example
    -------
    >>> icon_path("logo")   # doctest: +SKIP
    '/full/path/autoclicker/resources/icons/logo.ico'
    """
    ext = ".ico" if current_os == "windows" else ".icns"
    root = Path(__file__).resolve().parent.parent / "resources" / "icons"
    return str(root / f"{basename}{ext}")
