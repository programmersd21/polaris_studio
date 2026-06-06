from __future__ import annotations

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QDialog, QWidget

from polaris_studio.ui.motion import fade_slide_in


class AnimatedDialog(QDialog):
    """Dialog base with a restrained premium entrance transition."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._motion_started = False

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if self._motion_started:
            return
        self._motion_started = True
        fade_slide_in(self, duration_ms=220, offset=QPoint(0, 10))
