"""
Lightweight undo/redo stack based on the *command* pattern.

The GUI layer pushes concrete :class:`Command` objects whenever it
creates, deletes, modifies, or reorders an event.  `UndoStack` knows how
to replay those commands in either direction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List, MutableSequence, TypeVar

T = TypeVar("T")  # *Event* payload – stays completely generic here


class Command(Generic[T]):
    """Abstract base: something that can be *done* and *undone*."""

    def do(self, target: MutableSequence[T]) -> None:  # pragma: no cover
        raise NotImplementedError

    def undo(self, target: MutableSequence[T]) -> None:  # pragma: no cover
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Concrete commands
# --------------------------------------------------------------------------- #


@dataclass
class Add(Command[T]):
    obj: T

    def do(self, target: MutableSequence[T]) -> None:
        target.append(self.obj)

    def undo(self, target: MutableSequence[T]) -> None:
        target.pop()  # assumes list semantics


@dataclass
class Remove(Command[T]):
    obj: T
    index: int

    def do(self, target: MutableSequence[T]) -> None:
        target.pop(self.index)

    def undo(self, target: MutableSequence[T]) -> None:
        target.insert(self.index, self.obj)


@dataclass
class Modify(Command[T]):
    index: int
    before: T
    after: T

    def do(self, target: MutableSequence[T]) -> None:
        target[self.index] = self.after

    def undo(self, target: MutableSequence[T]) -> None:
        target[self.index] = self.before


@dataclass
class Reorder(Command[T]):
    old_index: int
    new_index: int

    def do(self, target: MutableSequence[T]) -> None:
        target.insert(self.new_index, target.pop(self.old_index))

    def undo(self, target: MutableSequence[T]) -> None:
        target.insert(self.old_index, target.pop(self.new_index))


# --------------------------------------------------------------------------- #
# Stack container
# --------------------------------------------------------------------------- #


class UndoStack(Generic[T]):
    """Keeps two stacks for unlimited *undo* / *redo* traversal."""

    def __init__(self, capacity: int = 100) -> None:
        self._undo: List[Command[T]] = []
        self._redo: List[Command[T]] = []
        self.capacity = capacity

    # Public API ------------------------------------------------------------- #

    def push(self, cmd: Command[T], target: MutableSequence[T]) -> None:
        """Execute *cmd* and add it to the undo stack."""
        cmd.do(target)
        self._undo.append(cmd)
        if len(self._undo) > self.capacity:
            self._undo.pop(0)  # drop oldest
        self._redo.clear()

    def undo(self, target: MutableSequence[T]) -> None:
        if not self._undo:
            return
        cmd = self._undo.pop()
        cmd.undo(target)
        self._redo.append(cmd)

    def redo(self, target: MutableSequence[T]) -> None:
        if not self._redo:
            return
        cmd = self._redo.pop()
        cmd.do(target)
        self._undo.append(cmd)
