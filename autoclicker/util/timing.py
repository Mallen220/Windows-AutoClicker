"""
Tiny helpers for dealing with “milliseconds vs seconds” confusion.

These are used by the GUI when reading spin‑box values *and* by the
core runner so we keep the maths in one place.
"""

from __future__ import annotations

import random
import time
from typing import Final

__all__ = [
    "secs",
    "rand_ms",
    "rand_secs",
    "sleep_ms",
    "DEFAULT_MIN_RANDOM",
    "DEFAULT_MAX_RANDOM",
]

DEFAULT_MIN_RANDOM: Final[int] = 0
DEFAULT_MAX_RANDOM: Final[int] = 1000


# --------------------------------------------------------------------------- #
# Unit conversions
# --------------------------------------------------------------------------- #


def secs(ms: int) -> float:
    """Convert milliseconds → seconds (float)."""
    return ms / 1000.0


def rand_ms(min_ms: int = DEFAULT_MIN_RANDOM, max_ms: int = DEFAULT_MAX_RANDOM) -> int:
    """Random integer in `[min_ms, max_ms]`."""
    return random.randint(min_ms, max_ms)


def rand_secs(
    min_ms: int = DEFAULT_MIN_RANDOM, max_ms: int = DEFAULT_MAX_RANDOM
) -> float:
    """Same as :func:`rand_ms` but already converted to seconds."""
    return secs(rand_ms(min_ms, max_ms))


# --------------------------------------------------------------------------- #
# Sleep helpers
# --------------------------------------------------------------------------- #


def sleep_ms(ms: int, randomise: bool = False) -> None:
    """
    `time.sleep` but the argument is *milliseconds*.

    Parameters
    ----------
    ms
        Base delay in **milliseconds**.
    randomise
        If *True* the actual sleep will be a random value `0…ms`.
    """
    if ms <= 0:
        return
    if randomise:
        ms = rand_ms(0, ms)
    time.sleep(secs(ms))
