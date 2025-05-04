"""
On‑screen numeric labels that show *where* click / scroll events are.

Uses the monitor helpers so each label sits on the correct screen.
"""

from __future__ import annotations

import tkinter as tk
from typing import Dict, List, Optional

from autoclicker.core import events as ev
from autoclicker.services import monitors


class OverlayManager:
    """Maintains one transparent, click‑through Toplevel per monitor."""

    def __init__(self, master: tk.Tk):
        self._master = master
        self._labels: Dict[str, tk.Label] = {}
        self._enabled = True

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def sync(self, events: List[ev.Event]) -> None:
        """Rebuild all labels from scratch."""
        for lbl in self._labels.values():
            lbl.destroy()
        self._labels.clear()

        if not self._enabled:
            return

        for idx, ev_obj in enumerate(events, start=1):
            if not isinstance(ev_obj, (ev.ClickEvent, ev.ScrollEvent)):
                continue
            x, y = ev_obj.position
            mon = monitors.rect_for(x, y)
            lbl = tk.Label(
                self._master,
                text=str(idx),
                bg="#FFEC40",
                fg="black",
                font=("Segoe UI", 9, "bold"),
            )
            lbl.overrideredirect(True)
            lbl.attributes("-topmost", True)
            lbl.geometry(f"+{x}+{y}")
            lbl.place(x=x - mon.x, y=y - mon.y)  # relative to screen
            self._labels[ev_obj.id] = lbl

    def disable(self) -> None:
        self._enabled = False
        for lbl in self._labels.values():
            lbl.place_forget()

    def enable(self) -> None:
        self._enabled = True
        self.sync([])  # next sync will recreate

    def tick(self) -> None:
        """Called periodically to keep labels on top (Windows loses it)."""
        if not self._enabled:
            return
        for lbl in self._labels.values():
            lbl.lift()
