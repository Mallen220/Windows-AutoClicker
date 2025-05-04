"""
Preset load / save helpers and a minimal *Rearrange* window.

Rearranging is kept intentionally simple: Up / Down buttons that
mutate the list in‑place and push an `undo.Reorder` command.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import List

from autoclicker.core import events as ev, undo


# --------------------------------------------------------------------------- #
# JSON helpers – imported by main toolbar
# --------------------------------------------------------------------------- #


def to_json(events: List[ev.Event]) -> dict:
    """Serialize to a dict that `json.dump` can write."""

    def _as_dict(obj: ev.Event) -> dict:
        d = obj.__dict__.copy()
        d["__type__"] = obj.__class__.__name__
        return d

    return {"events": [_as_dict(e) for e in events]}


def from_json(data: dict) -> List[ev.Event]:
    """Re‑create events from :func:`to_json` output."""
    name_map = {
        "ClickEvent": ev.ClickEvent,
        "ScrollEvent": ev.ScrollEvent,
        "TextEvent": ev.TextEvent,
        "WaitEvent": ev.WaitEvent,
    }
    out: List[ev.Event] = []
    for item in data["events"]:
        cls = name_map[item.pop("__type__")]
        out.append(cls(**item))  # type: ignore[arg-type]
    return out


# --------------------------------------------------------------------------- #
# Rearrange window
# --------------------------------------------------------------------------- #


def rearrange_window(master: tk.Widget, events: List[ev.Event], stack: undo.UndoStack):
    win = tk.Toplevel(master)
    win.title("Rearrange events")
    win.resizable(False, False)

    listbox = tk.Listbox(win, activestyle="none", width=45, height=15)
    listbox.pack(side="left", fill="both", padx=(4, 0), pady=4)

    yscroll = ttk.Scrollbar(win, orient="vertical", command=listbox.yview)
    yscroll.pack(side="left", fill="y", pady=4)
    listbox.configure(yscrollcommand=yscroll.set)

    def refresh():
        listbox.delete(0, "end")
        for i, eobj in enumerate(events, start=1):
            listbox.insert("end", f"{i}. {eobj.__class__.__name__}")

    refresh()

    ctrl = ttk.Frame(win)
    ctrl.pack(side="left", pady=4, padx=4)

    def move(offset: int):
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        new_idx = max(0, min(len(events) - 1, idx + offset))
        if idx == new_idx:
            return
        stack.push(undo.Reorder(idx, new_idx), events)
        refresh()
        listbox.selection_set(new_idx)

    ttk.Button(ctrl, text="↑", width=4, command=lambda: move(-1)).pack(pady=2)
    ttk.Button(ctrl, text="↓", width=4, command=lambda: move(+1)).pack(pady=2)
