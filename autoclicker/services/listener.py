"""
Cross‑platform global‑keyboard listener.

*   Fires high‑level **string** names (``"ctrl"`` / ``"shift"`` / ``"space"`` …).
*   Keeps an internal *pressed* set for quick “is key held?” checks.
*   Exposes a thread‑safe :pyclass:`Listener` singleton – start it once
    at program boot and forget about it.
"""

from __future__ import annotations

import logging
import threading
from queue import SimpleQueue
from typing import Callable, Optional, Set, Union

try:
    # External – install with `pip install pynput`
    from pynput import keyboard  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError(
        "The `pynput` package is required for autoclicker.services.listener"
    ) from exc

__all__ = ["Listener", "KeyEvent", "get_pressed_keys"]

log = logging.getLogger(__name__)
KeyEvent = str  # public alias – a plain, lowercase name


class Listener:
    """
    Thin wrapper around :class:`pynput.keyboard.Listener`.

    Notes
    -----
    *Only one* instance should exist – treat it as a singleton.  All GUI
    layers import :func:`get_listener` instead of instantiating directly.
    """

    _instance: "Optional[Listener]" = None

    # ------------------------------------------------------------------ #
    # Life‑cycle helpers
    # ------------------------------------------------------------------ #

    def __new__(cls) -> "Listener":  # pragma: no cover
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return  # singleton already set up

        self._handlers: "SimpleQueue[Callable[[KeyEvent, bool], None]]" = SimpleQueue()
        self._pressed: "Set[KeyEvent]" = set()
        self._lock = threading.Lock()

        self._raw = keyboard.Listener(on_press=_on_press, on_release=_on_release)

        self._raw.start()
        self._initialized = True
        log.debug("Global key listener started")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def subscribe(self, cb: Callable[[KeyEvent, bool], None]) -> None:
        """
        Register *cb* to receive (``name``, ``is_press``) tuples.

        Handlers run on the **pynput** thread, so avoid long/GUI work.
        """
        self._handlers.put(cb)

    # Convenience wrappers ------------------------------------------------ #

    def is_pressed(self, name: KeyEvent) -> bool:
        """Return *True* while ``name`` is held down."""
        with self._lock:
            return name in self._pressed


# --------------------------------------------------------------------------- #
# Module‑level helpers
# --------------------------------------------------------------------------- #


def get_listener() -> Listener:
    """Return the module‑wide singleton (starts it if needed)."""
    return Listener()


def get_pressed_keys() -> Set[KeyEvent]:
    """Snapshot of the currently held keys."""
    lst = get_listener()
    with lst._lock:  # pylint: disable=protected-access
        return set(lst._pressed)


# --------------------------------------------------------------------------- #
# Internal callbacks
# --------------------------------------------------------------------------- #


def _normalise(key: Union["keyboard.Key", "keyboard.KeyCode"]) -> Optional[KeyEvent]:
    """Translate pynput keys into lowercase *names* we use elsewhere."""
    if isinstance(key, keyboard.Key):
        mapping = {
            keyboard.Key.ctrl_l: "ctrl",
            keyboard.Key.ctrl_r: "ctrl",
            keyboard.Key.shift_l: "shift",
            keyboard.Key.shift_r: "shift",
            keyboard.Key.alt_l: "alt",
            keyboard.Key.alt_r: "alt",
            keyboard.Key.space: "space",
        }
        return mapping.get(key)
    if isinstance(key, keyboard.KeyCode) and key.char is not None:
        return key.char.lower()
    return None


def _broadcast(lst: Listener, name: KeyEvent, pressed: bool) -> None:
    while not lst._handlers.empty():
        try:
            lst._handlers.get_nowait()(name, pressed)
        except Exception:  # pragma: no cover
            log.exception("Key handler crashed")


def _on_press(key):  # noqa: D401
    lst = get_listener()
    name = _normalise(key)
    if name is None:
        return
    with lst._lock:
        lst._pressed.add(name)
    _broadcast(lst, name, True)


def _on_release(key):  # noqa: D401
    lst = get_listener()
    name = _normalise(key)
    if name is None:
        return
    with lst._lock:
        lst._pressed.discard(name)
    _broadcast(lst, name, False)
