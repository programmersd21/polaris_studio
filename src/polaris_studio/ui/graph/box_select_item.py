"""Rubber-band selection rectangle for the canvas."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QStyleOptionGraphicsItem, QWidget

from polaris_studio.ui.theme import PALETTE


class BoxSelectionItem(QGraphicsRectItem):
    """A semi-transparent selection rectangle for box-selecting nodes."""

    def __init__(self, parent: Optional[QGraphicsItem] = None) -> None:
        super().__init__(parent)
        self.setZValue(100)
        pen = QPen(QColor(PALETTE.selection_box), 1.4, Qt.PenStyle.DashLine)
        self.setPen(pen)
        fill = QColor(PALETTE.accent)
        fill.setAlpha(40)
        self.setBrush(QBrush(fill))

    def set_rect(self, rect: QRectF) -> None:
        self.setRect(rect)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        super().paint(painter, option, widget)
