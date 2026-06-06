"""Live connection drag preview.

While the user drags from a port, a temporary edge follows the cursor.
When released, the canvas resolves the drop and either connects to a port
under the cursor or cancels.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

from polaris_studio.ui.graph.node_item import NodeItem
from polaris_studio.ui.theme import PALETTE


class ConnectionDrag(QGraphicsPathItem):
    """A drag preview edge from a port to the current cursor position."""

    def __init__(
        self, source_item: NodeItem, source_port: str, parent: Optional[QGraphicsItem] = None
    ) -> None:
        super().__init__(parent)
        self._source_item = source_item
        self._source_port = source_port
        self._end_pos = QPointF(0, 0)
        self._valid = True
        self.setZValue(15)
        self._update_path()

    def set_end_pos(self, pos: QPointF) -> None:
        self._end_pos = pos
        self._update_path()
        self.update()

    def set_valid(self, valid: bool) -> None:
        self._valid = valid
        self.update()

    def _update_path(self) -> None:
        start = self._source_item.get_port_scene_pos(self._source_port)
        path = QPainterPath(start)
        dx = self._end_pos.x() - start.x()
        cp_offset = max(60.0, abs(dx) * 0.55)
        path.cubicTo(
            QPointF(start.x() + cp_offset, start.y()),
            QPointF(self._end_pos.x() - cp_offset, self._end_pos.y()),
            self._end_pos,
        )
        self.setPath(path)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._valid:
            color = QColor(PALETTE.accent)
        else:
            color = QColor(PALETTE.error)
        glow = QColor(color)
        glow.setAlpha(80)
        painter.setPen(QPen(glow, 6))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())
        painter.setPen(QPen(color, 2.4, Qt.PenStyle.DashLine))
        painter.drawPath(self.path())
