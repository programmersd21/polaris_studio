"""Edge (connection) rendering.

Edges are cubic Bezier curves connecting two ports. They are anti-aliased,
animatable (for "data flowing" effects), and respond to hover and selection.

The curve direction is implicit:
- Source: starts at right side of source node, ends at left side of target node
- Source port position determines the start anchor
- Target port position determines the end anchor
- Control points are computed from horizontal distance for a natural S-curve
"""

from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QStyleOptionGraphicsItem, QWidget

from polaris_studio.core.graph import Edge
from polaris_studio.ui.graph.node_item import NodeItem
from polaris_studio.ui.motion import premium_curve
from polaris_studio.ui.theme import PALETTE


class EdgeItem(QGraphicsPathItem):
    """Visual representation of a connection between two node ports."""

    def __init__(
        self,
        edge: Edge,
        source_item: NodeItem,
        target_item: NodeItem,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        super().__init__(parent)
        self._edge = edge
        self._source_item = source_item
        self._target_item = target_item
        self._pulse_offset = 0.0
        self._is_animating = False
        self._hovered = False
        self._reveal = 0.0

        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setPen(QPen(QColor(PALETTE.edge), 2.0))

        self._update_path()
        self._animate_reveal()

    @property
    def edge(self) -> Edge:
        return self._edge

    def get_edge(self) -> Edge:
        return self._edge

    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self.setToolTip(f"{self._edge.source_id} → {self._edge.target_id}")
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def shape(self):  # type: ignore[override]
        stroker_path = self.path()
        from PySide6.QtGui import QPainterPathStroker

        stroker = QPainterPathStroker()
        stroker.setWidth(12)
        return stroker.createStroke(stroker_path)

    def _update_path(self) -> None:
        start = self._source_item.get_port_scene_pos(self._edge.source_port)
        end = self._target_item.get_port_scene_pos(self._edge.target_port)

        path = QPainterPath(start)
        dx = end.x() - start.x()
        cp_offset = max(60.0, abs(dx) * 0.55)
        path.cubicTo(
            QPointF(start.x() + cp_offset, start.y()),
            QPointF(end.x() - cp_offset, end.y()),
            end,
        )
        self.setPath(path)

    def boundingRect(self) -> QRectF:
        r = self.path().boundingRect()
        m = 14.0
        return r.adjusted(-m, -m, m, m)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = self.path()
        if self._reveal < 1.0:
            path = self._partial_path(path, self._reveal)

        if self.isSelected():
            color = QColor(PALETTE.edge_selected)
            width = 3.4
        elif self._hovered:
            color = QColor(PALETTE.edge_hover)
            width = 2.8
        else:
            color = QColor(PALETTE.edge)
            width = 2.0

        glow_color = QColor(color)
        glow_color.setAlpha(60)
        glow_pen = QPen(glow_color, width + 4.0)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        painter.setPen(QPen(color, width))
        painter.drawPath(path)

        if self._is_animating:
            pulse_path = path
            t = self._pulse_offset % 1.0
            pos = pulse_path.pointAtPercent(t)
            tangent = pulse_path.pointAtPercent(min(t + 0.01, 1.0))
            angle = math.atan2(tangent.y() - pos.y(), tangent.x() - pos.x())
            painter.save()
            painter.translate(pos)
            painter.rotate(math.degrees(angle))
            glow = QColor(PALETTE.accent)
            glow.setAlpha(180)
            painter.setBrush(glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(0, 0), 4, 4)
            painter.restore()

    def set_animating(self, animating: bool) -> None:
        self._is_animating = animating
        self.update()

    def update_pulse(self, offset: float) -> None:
        self._pulse_offset = offset
        self.update()

    def update_positions(self) -> None:
        self._update_path()
        self.update()

    def _animate_reveal(self) -> None:
        animation = QVariantAnimation()
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setDuration(260)
        animation.setEasingCurve(premium_curve())
        animation.valueChanged.connect(self._set_reveal)
        self._reveal_animation = animation
        animation.start()

    def _set_reveal(self, value: object) -> None:
        self._reveal = float(value)  # type: ignore[arg-type]
        self.update()

    def _partial_path(self, path: QPainterPath, percent: float) -> QPainterPath:
        clamped = max(0.0, min(1.0, percent))
        if clamped >= 1.0:
            return path
        points = 32
        partial = QPainterPath(path.pointAtPercent(0.0))
        for i in range(1, max(2, int(points * clamped)) + 1):
            partial.lineTo(path.pointAtPercent(min(clamped, i / points)))
        return partial
