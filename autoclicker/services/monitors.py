"""
Monitor enumeration helpers.

*Relies on* **screeninfo** (``pip install screeninfo``) but falls back to
a single (0, 0, 1920, 1080) rectangle if the package or X11 info is
missing – useful for headless CI.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List, Tuple

log = logging.getLogger(__name__)

try:
    from screeninfo import get_monitors  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    get_monitors = None  # type: ignore

__all__ = ["Monitor", "all_monitors", "rect_for"]


@dataclass
class Monitor:
    x: int
    y: int
    width: int
    height: int

    # Convenience --------------------------------------------------------- #

    @property
    def rect(self) -> Tuple[int, int, int, int]:
        return self.x, self.y, self.width, self.height

    def contains(self, px: int, py: int) -> bool:
        return (
            self.x <= px < self.x + self.width and self.y <= py < self.y + self.height
        )


# --------------------------------------------------------------------------- #
# Public helpers
# --------------------------------------------------------------------------- #


def all_monitors() -> List[Monitor]:
    """Return all available monitors as :class:`Monitor` objects."""
    if get_monitors is None:  # package missing
        log.warning("screeninfo not found – assuming single 1920×1080 monitor")
        return [Monitor(0, 0, 1920, 1080)]

    try:
        return [
            Monitor(m.x, m.y, m.width, m.height)  # type: ignore[attr-defined]
            for m in get_monitors()
        ]
    except Exception as exc:  # pragma: no cover
        log.warning("screeninfo error: %s – using fallback monitor", exc)
        return [Monitor(0, 0, 1920, 1080)]


def rect_for(px: int, py: int) -> Monitor:
    """
    Find which monitor contains the point *(px, py)*.

    If none match (coords outside every rect), the **last** monitor is
    returned so callers always get *something*.
    """
    for mon in all_monitors():
        if mon.contains(px, py):
            return mon
    return all_monitors()[-1]
