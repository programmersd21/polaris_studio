from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from polaris_studio.core.graph import WorkflowGraph

GraphMutationFn = Callable[[WorkflowGraph], None]


@dataclass
class GraphMutationAction:
    description: str
    execute: GraphMutationFn
    inverse: GraphMutationFn


class HistoryStack:
    def __init__(self, max_size: int = 100) -> None:
        self._undo_stack: List[GraphMutationAction] = []
        self._redo_stack: List[GraphMutationAction] = []
        self._max_size = max_size

    def push(self, action: GraphMutationAction, inverse: GraphMutationAction) -> None:
        self._undo_stack.append(action)
        if len(self._undo_stack) > self._max_size:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self) -> Optional[GraphMutationAction]:
        if not self._undo_stack:
            return None
        action = self._undo_stack.pop()
        inverse = GraphMutationAction(
            description=f"undo:{action.description}",
            execute=action.inverse,
            inverse=action.execute,
        )
        self._redo_stack.append(inverse)
        if len(self._redo_stack) > self._max_size:
            self._redo_stack.pop(0)
        return inverse

    def redo(self) -> Optional[GraphMutationAction]:
        if not self._redo_stack:
            return None
        action = self._redo_stack.pop()
        inverse = GraphMutationAction(
            description=f"redo:{action.description}",
            execute=action.inverse,
            inverse=action.execute,
        )
        self._undo_stack.append(inverse)
        if len(self._undo_stack) > self._max_size:
            self._undo_stack.pop(0)
        return inverse

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def undo_count(self) -> int:
        return len(self._undo_stack)

    @property
    def redo_count(self) -> int:
        return len(self._redo_stack)
