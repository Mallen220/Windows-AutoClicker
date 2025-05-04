"""
Modal dialogs for creating and editing individual events.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import simpledialog, ttk
from typing import Callable, Type

from autoclicker.core import events as ev


# --------------------------------------------------------------------------- #
# Utilities
# --------------------------------------------------------------------------- #


def ask_new_event(master: tk.Widget) -> ev.Event | None:
    """
    Ask the user which event type to create, then open its editor.

    Returns
    -------
    Event or *None* if cancelled.
    """
    dlg = simpledialog.askstring(
        "New Event", "Type: click / scroll / text / wait", parent=master
    )
    if dlg is None:
        return None
    dlg = dlg.strip().lower()
    mapping: dict[str, Type[ev.Event]] = {
        "click": ev.ClickEvent,
        "scroll": ev.ScrollEvent,
        "text": ev.TextEvent,
        "wait": ev.WaitEvent,
    }
    if dlg not in mapping:
        return None
    new_ev = mapping[dlg]()  # type: ignore[call-arg]
    return edit_event(master, new_ev)


def edit_event(master: tk.Widget, event: ev.Event) -> ev.Event | None:
    """Return a *new* object with edits or **None** to cancel."""
    if isinstance(event, ev.ClickEvent):
        return _ClickEditor(master, event).result
    if isinstance(event, ev.ScrollEvent):
        return _ScrollEditor(master, event).result
    if isinstance(event, ev.TextEvent):
        return _TextEditor(master, event).result
    if isinstance(event, ev.WaitEvent):
        return _WaitEditor(master, event).result
    return None


# --------------------------------------------------------------------------- #
# Editor base
# --------------------------------------------------------------------------- #


class _BaseEditor(simpledialog.Dialog):
    def __init__(self, master: tk.Widget, ev_before: ev.Event):
        self._before = ev_before
        self.result: ev.Event | None = None
        super().__init__(master, f"{ev_before.__class__.__name__}")

    # override ------------------------------------------------------------- #

    def validate(self) -> bool:  # noqa: D401
        try:
            self.result = self._create()
            return True
        except Exception:  # pragma: no cover
            return False

    # subclasses must provide
    def _create(self) -> ev.Event:  # pragma: no cover
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Editors per type
# --------------------------------------------------------------------------- #


class _ClickEditor(_BaseEditor):
    def body(self, master):  # noqa: D401
        ttk.Label(master, text="x:").grid(row=0, column=0, sticky="e")
        ttk.Label(master, text="y:").grid(row=1, column=0, sticky="e")
        ttk.Label(master, text="button:").grid(row=2, column=0, sticky="e")
        ttk.Label(master, text="count:").grid(row=3, column=0, sticky="e")
        ttk.Label(master, text="delay ms:").grid(row=4, column=0, sticky="e")

        self._x = tk.IntVar(value=self._before.position[0])
        self._y = tk.IntVar(value=self._before.position[1])
        self._btn = tk.StringVar(value=str(self._before.button))
        self._count = tk.IntVar(value=self._before.count)
        self._delay = tk.IntVar(value=self._before.delay)

        ttk.Entry(master, textvariable=self._x, width=8).grid(row=0, column=1)
        ttk.Entry(master, textvariable=self._y, width=8).grid(row=1, column=1)
        ttk.Combobox(
            master, textvariable=self._btn, values=("left", "right", "middle"), width=7
        ).grid(row=2, column=1)
        ttk.Entry(master, textvariable=self._count, width=8).grid(row=3, column=1)
        ttk.Entry(master, textvariable=self._delay, width=8).grid(row=4, column=1)

    def _create(self) -> ev.Event:
        return ev.ClickEvent(
            position=(self._x.get(), self._y.get()),
            button=ev.Button[self._btn.get().upper()],
            count=self._count.get(),
            delay=self._delay.get(),
            randomise=self._before.randomise,
        )


class _ScrollEditor(_BaseEditor):
    def body(self, master):  # noqa: D401
        ttk.Label(master, text="x:").grid(row=0, column=0, sticky="e")
        ttk.Label(master, text="y:").grid(row=1, column=0, sticky="e")
        ttk.Label(master, text="count:").grid(row=2, column=0, sticky="e")
        ttk.Label(master, text="delay ms:").grid(row=3, column=0, sticky="e")

        self._x = tk.IntVar(value=self._before.position[0])
        self._y = tk.IntVar(value=self._before.position[1])
        self._count = tk.IntVar(value=self._before.count)
        self._delay = tk.IntVar(value=self._before.delay)

        ttk.Entry(master, textvariable=self._x, width=8).grid(row=0, column=1)
        ttk.Entry(master, textvariable=self._y, width=8).grid(row=1, column=1)
        ttk.Entry(master, textvariable=self._count, width=8).grid(row=2, column=1)
        ttk.Entry(master, textvariable=self._delay, width=8).grid(row=3, column=1)

    def _create(self) -> ev.Event:
        return ev.ScrollEvent(
            position=(self._x.get(), self._y.get()),
            count=self._count.get(),
            delay=self._delay.get(),
            randomise=self._before.randomise,
        )


class _TextEditor(_BaseEditor):
    def body(self, master):  # noqa: D401
        ttk.Label(master, text="Content:").grid(row=0, column=0, sticky="e")
        ttk.Label(master, text="Delay ms:").grid(row=1, column=0, sticky="e")

        self._content = tk.StringVar(value=self._before.content)
        self._delay = tk.IntVar(value=self._before.delay)

        ttk.Entry(master, textvariable=self._content, width=30).grid(row=0, column=1)
        ttk.Entry(master, textvariable=self._delay, width=8).grid(row=1, column=1)

    def _create(self) -> ev.Event:
        return ev.TextEvent(
            content=self._content.get(),
            delay=self._delay.get(),
            randomise=self._before.randomise,
        )


class _WaitEditor(_BaseEditor):
    def body(self, master):  # noqa: D401
        ttk.Label(master, text="Delay ms:").grid(row=0, column=0, sticky="e")
        self._delay = tk.IntVar(value=self._before.delay)
        ttk.Entry(master, textvariable=self._delay, width=8).grid(row=0, column=1)

    def _create(self) -> ev.Event:
        return ev.WaitEvent(delay=self._delay.get(), randomise=self._before.randomise)
