"""
Root window, toolbar and event list.

This is where the application **starts**.  Everything else pops up from
callbacks defined here.
"""

from __future__ import annotations

import json
import logging
import pathlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List

from autoclicker.core import events as ev
from autoclicker.core import runner, undo
from autoclicker.services.listener import get_listener
from autoclicker.util import timing
from . import editor, overlay, presets

log = logging.getLogger(__name__)


class AutoClickerApp:
    """Singleton wrapper around the Tk root."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("AutoClicker")

        # ----------------------------------------------------------------- #
        # Model state
        # ----------------------------------------------------------------- #
        self._events: List[ev.Event] = []
        self._undo = undo.UndoStack[ev.Event]()
        self._runner: runner.EventRunner | None = None

        # ----------------------------------------------------------------- #
        # Layout
        # ----------------------------------------------------------------- #
        self._build_toolbar(self.root)
        self._build_listbox(self.root)
        self.overlay = overlay.OverlayManager(self.root)

        # ----------------------------------------------------------------- #
        # Global key listener (for spacebar stop)
        # ----------------------------------------------------------------- #
        lst = get_listener()
        lst.subscribe(self._on_global_key)

        # Periodic GUI refresh (overlays, listbox selection alignment, …)
        self.root.after(100, self._poll)

    # --------------------------------------------------------------------- #
    # UI builders
    # --------------------------------------------------------------------- #

    def _build_toolbar(self, master: tk.Widget) -> None:
        bar = ttk.Frame(master, padding=(4, 2))
        bar.pack(fill="x")

        ttk.Button(bar, text="New", command=self._cmd_new).pack(side="left")
        ttk.Button(bar, text="Undo", command=self._cmd_undo).pack(side="left")
        ttk.Button(bar, text="Redo", command=self._cmd_redo).pack(side="left")
        ttk.Button(bar, text="Rearrange", command=self._cmd_rearrange).pack(side="left")

        ttk.Separator(bar, orient="vertical").pack(side="left", padx=4, fill="y")

        self._start_btn = ttk.Button(bar, text="Start ▶", command=self._cmd_start_stop)
        self._start_btn.pack(side="left")

        ttk.Separator(bar, orient="vertical").pack(side="left", padx=4, fill="y")

        ttk.Button(bar, text="Save Preset", command=self._cmd_save_preset).pack(
            side="left"
        )
        ttk.Button(bar, text="Load Preset", command=self._cmd_load_preset).pack(
            side="left"
        )

    def _build_listbox(self, master: tk.Widget) -> None:
        frame = ttk.Frame(master)
        frame.pack(fill="both", expand=True, padx=4, pady=2)

        self._list = tk.Listbox(frame, activestyle="none", height=18)
        self._list.pack(side="left", fill="both", expand=True)
        self._list.bind("<Double-1>", self._on_edit_event)

        yscroll = ttk.Scrollbar(frame, orient="vertical", command=self._list.yview)
        yscroll.pack(side="right", fill="y")
        self._list.configure(yscrollcommand=yscroll.set)

    # --------------------------------------------------------------------- #
    # Event → Listbox mapping helpers
    # --------------------------------------------------------------------- #

    @staticmethod
    def _summary(ev_obj: ev.Event, idx: int) -> str:
        """One‑line human description."""
        if isinstance(ev_obj, ev.ClickEvent):
            return f"{idx}. Click {ev_obj.button}×{ev_obj.count} @{ev_obj.position}"
        if isinstance(ev_obj, ev.ScrollEvent):
            return f"{idx}. Scroll {ev_obj.count} @{ev_obj.position}"
        if isinstance(ev_obj, ev.TextEvent):
            preview = (
                ev_obj.content
                if len(ev_obj.content) < 25
                else ev_obj.content[:22] + "…"
            )
            return f'{idx}. Text "{preview}"'
        if isinstance(ev_obj, ev.WaitEvent):
            return f"{idx}. Wait {ev_obj.delay} ms"
        return f"{idx}. <unknown>"

    def _refresh_list(self) -> None:
        self._list.delete(0, "end")
        for i, eobj in enumerate(self._events, start=1):
            self._list.insert("end", self._summary(eobj, i))

    # --------------------------------------------------------------------- #
    # Toolbar callbacks
    # --------------------------------------------------------------------- #

    def _cmd_new(self) -> None:
        new_ev = editor.ask_new_event(self.root)
        if new_ev is None:
            return
        self._undo.push(undo.Add(new_ev), self._events)
        self._refresh_list()
        self.overlay.sync(self._events)

    def _cmd_undo(self) -> None:
        self._undo.undo(self._events)
        self._refresh_list()
        self.overlay.sync(self._events)

    def _cmd_redo(self) -> None:
        self._undo.redo(self._events)
        self._refresh_list()
        self.overlay.sync(self._events)

    def _cmd_rearrange(self) -> None:
        presets.rearrange_window(self.root, self._events, self._undo)
        self._refresh_list()
        self.overlay.sync(self._events)

    def _cmd_start_stop(self) -> None:
        if self._runner and self._runner.is_running:
            self._runner.stop()
            self._runner = None
            self._start_btn.config(text="Start ▶")
            self.overlay.enable()
            return

        if not self._events:
            messagebox.showwarning("No events", "Create at least one event first.")
            return

        self.overlay.disable()  # hide labels while running
        self._runner = runner.EventRunner(self._events)
        self._runner.on_status(self._on_runner_status)
        self._runner.start()
        self._start_btn.config(text="Stop ■")

    def _cmd_save_preset(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save preset",
            defaultextension=".json",
            filetypes=[("Preset", "*.json")],
        )
        if not path:
            return
        data = presets.to_json(self._events)
        pathlib.Path(path).write_text(json.dumps(data, indent=2))
        log.info("Saved preset to %s", path)

    def _cmd_load_preset(self) -> None:
        path = filedialog.askopenfilename(
            title="Load preset",
            filetypes=[("Preset", "*.json")],
        )
        if not path:
            return
        try:
            data = json.loads(pathlib.Path(path).read_text())
            new_events = presets.from_json(data)
        except Exception as exc:
            messagebox.showerror("Load failed", str(exc))
            return
        self._events.clear()
        self._events.extend(new_events)
        self._undo = undo.UndoStack()  # reset history
        self._refresh_list()
        self.overlay.sync(self._events)

    # --------------------------------------------------------------------- #
    # Listbox callbacks
    # --------------------------------------------------------------------- #

    def _on_edit_event(self, _event) -> None:
        idx = self._list.curselection()
        if not idx:
            return
        row = idx[0]
        ev_before = self._events[row]
        ev_after = editor.edit_event(self.root, ev_before)
        if ev_after is None or ev_after == ev_before:
            return
        self._undo.push(undo.Modify(row, ev_before, ev_after), self._events)
        self._refresh_list()
        self.overlay.sync(self._events)

    # --------------------------------------------------------------------- #
    # Background hooks
    # --------------------------------------------------------------------- #

    def _on_global_key(self, name: str, pressed: bool) -> None:
        if name == "space" and pressed and self._runner and self._runner.is_running:
            self._cmd_start_stop()

    def _on_runner_status(self, state: str) -> None:
        if state == "stopped":
            self._start_btn.config(text="Start ▶")
            self.overlay.enable()

    # --------------------------------------------------------------------- #
    # Mainloop housekeeping
    # --------------------------------------------------------------------- #

    def _poll(self) -> None:
        # refresh overlays in case window moved etc.
        self.overlay.tick()
        self.root.after(100, self._poll)

    # --------------------------------------------------------------------- #
    # Entry helpers
    # --------------------------------------------------------------------- #

    def run(self) -> None:
        self.root.mainloop()


# --------------------------------------------------------------------------- #
# Script entry‑point
# --------------------------------------------------------------------------- #


def main() -> None:  # noqa: D401
    logging.basicConfig(level=logging.INFO)
    AutoClickerApp().run()


if __name__ == "__main__":
    main()
