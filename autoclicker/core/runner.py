"""
Headless execution engine.

Reads a *flat* list of :pydata:`autoclicker.core.events.Event` objects
and plays them back in a worker thread.  It never touches `tkinter`
directly—status is pushed to callbacks registered via :meth:`on_status`.
"""

from __future__ import annotations

import threading
import time
from queue import SimpleQueue
from random import randint
from typing import Callable, List, Sequence, Optional

import pyautogui
import pyperclip

from .events import (
    Button,
    ClickEvent,
    Event,
    ScrollEvent,
    TextEvent,
    WaitEvent,
)

StatusCallback = Callable[[str], None]


class EventRunner:
    """
    Replay *events* in order until :meth:`stop` is called.

    Instances are **single‑shot**: start → stop → discard.
    """

    def __init__(self, events: Sequence[Event], delay_between_rounds: int = 0):
        self._events: List[Event] = list(events)
        self._delay_between_rounds = delay_between_rounds / 1000.0  # ms→s
        self._status_handlers: SimpleQueue[StatusCallback] = SimpleQueue()

        self._thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()

    # --------------------------------------------------------------------- #
    # Lifecycle
    # --------------------------------------------------------------------- #

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return  # already running

        self._stop_flag.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._dispatch("running")

    def stop(self) -> None:
        self._stop_flag.set()
        if self._thread:
            self._thread.join()
        self._dispatch("stopped")

    # --------------------------------------------------------------------- #
    # Public helpers
    # --------------------------------------------------------------------- #

    def on_status(self, cb: StatusCallback) -> None:
        """Register a *callback* that receives ``"running"`` / ``"stopped"``."""
        self._status_handlers.put(cb)

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # --------------------------------------------------------------------- #
    # Internal
    # --------------------------------------------------------------------- #

    def _loop(self) -> None:
        while not self._stop_flag.is_set():
            for ev in self._events:
                self._sleep(ev.delay, ev.randomise)
                if self._stop_flag.is_set():
                    break
                self._execute(ev)
            self._sleep(int(self._delay_between_rounds * 1000), False)

    # ------------------------------------------------------------------ #

    @staticmethod
    def _sleep(ms: int, randomise: bool) -> None:
        if ms <= 0:
            return
        if randomise:
            ms = randint(0, ms)
        time.sleep(ms / 1000.0)

    # ------------------------------------------------------------------ #

    def _execute(self, ev: Event) -> None:  # noqa: C901 (simple but many branches)
        if isinstance(ev, ClickEvent):
            pyautogui.click(
                ev.position[0],
                ev.position[1],
                clicks=ev.count,
                button=str(ev.button),
            )
        elif isinstance(ev, ScrollEvent):
            pyautogui.moveTo(*ev.position)
            pyautogui.scroll(ev.count)
        elif isinstance(ev, TextEvent):
            # Paste instantly if long
            if ev.content.startswith("{PASTE}"):
                pyperclip.copy(ev.content.replace("{PASTE}", "", 1))
                pyautogui.hotkey("ctrl", "v")
            else:
                pyautogui.typewrite(ev.content, interval=0.02)
        elif isinstance(ev, WaitEvent):
            pass  # no‑op; delay already slept
        else:  # pragma: no cover
            raise TypeError(f"Unhandled event type: {type(ev)}")

    # ------------------------------------------------------------------ #

    def _dispatch(self, state: str) -> None:
        while not self._status_handlers.empty():
            self._status_handlers.get_nowait()(state)
