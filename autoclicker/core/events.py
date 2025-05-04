"""
Pure data models that describe **what** should happen, not *how*.

The execution logic that turns these objects into real mouse‑moves,
scrolls, or key presses lives in :pymod:`autoclicker.core.runner`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Tuple, Union


class Button(Enum):
    """Mouse buttons we care about."""

    LEFT = auto()
    RIGHT = auto()
    MIDDLE = auto()

    def __str__(self) -> str:  # pretty‑print
        return self.name.lower()


@dataclass
class BaseEvent:
    """
    Root of the event tree.

    All subclasses share *delay* (ms to wait **before** executing) and
    *randomise* (runner may replace *delay* with a random value).
    """

    delay: int = 0
    randomise: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex, init=False)


@dataclass
class ClickEvent(BaseEvent):
    """Single or multi‑click at a screen coordinate."""

    position: Tuple[int, int] = (0, 0)
    button: Button = Button.LEFT
    count: int = 1


@dataclass
class ScrollEvent(BaseEvent):
    """Mouse‑wheel scroll at *position*. Positive *count* = up, negative = down."""

    position: Tuple[int, int] = (0, 0)
    count: int = 1  # ± lines or 'ticks'


@dataclass
class TextEvent(BaseEvent):
    """
    Plain‑text typing.

    *content* may contain special tokens (``{ENTER}``, ``{TAB}``, …) that
    the runner converts to real key presses.
    """

    content: str = ""


@dataclass
class WaitEvent(BaseEvent):
    """Just pause – no additional fields."""


# Handy runtime type union
Event = Union[ClickEvent, ScrollEvent, TextEvent, WaitEvent]

__all__ = [
    "Button",
    "BaseEvent",
    "ClickEvent",
    "ScrollEvent",
    "TextEvent",
    "WaitEvent",
    "Event",
]
