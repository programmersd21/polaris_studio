"""Port item rendering for nodes.

Each node has zero or more input/output ports. Ports are visually distinct
circles anchored on the left or right edge of the node body and emit signals
for connection drag start/finish.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsSceneHoverEvent,
    QStyleOptionGraphicsItem,
    QWidget,
)

from polaris_studio.ui.theme import PALETTE


class PortDirection(Enum):
    INPUT = "input"
    OUTPUT = "output"


class PortType(Enum):
    DATA = "data"
    EXEC = "exec"


class PortItem(QGraphicsObject):
    """A circular connection port on a node.

    Signals
    -------
    connection_drag_started : node_id, port_name, direction
    connection_drag_finished: node_id, port_name, screen_pos
    """

    connection_drag_started = Signal(str, str, str)
    connection_drag_moved = Signal(str, str, object)
    connection_drag_finished = Signal(str, str, object)

    RADIUS = 7.0
    HIT_RADIUS = 14.0

    def __init__(
        self,
        node_id: str,
        port_name: str,
        direction: PortDirection,
        port_type: PortType = PortType.DATA,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        super().__init__(parent)
        self._node_id = node_id
        self._port_name = port_name
        self._direction = direction
        self._port_type = port_type
        self._hovered = False
        self._connected = False
        self._compatible = True
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setZValue(20)

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def port_name(self) -> str:
        return self._port_name

    @property
    def direction(self) -> PortDirection:
        return self._direction

    @property
    def port_type(self) -> PortType:
        return self._port_type

    def set_connected(self, connected: bool) -> None:
        self._connected = connected
        self.update()

    def set_compatible(self, compatible: bool) -> None:
        self._compatible = compatible
        self.update()

    def scene_anchor(self) -> QPointF:
        return self.mapToScene(QPointF(0, 0))

    def boundingRect(self) -> QRectF:
        r = self.HIT_RADIUS
        return QRectF(-r, -r, r * 2, r * 2)

    def shape(self):  # type: ignore[override]
        from PySide6.QtGui import QPainterPath

        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), self.HIT_RADIUS, self.HIT_RADIUS)
        return path

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._compatible and not self._hovered:
            color = QColor(PALETTE.port)
            color.setAlpha(90)
        elif self._hovered:
            color = QColor(PALETTE.port_hover)
        else:
            color = QColor(PALETTE.port)

        outer_r = self.RADIUS + (2.0 if self._hovered else 0)
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), outer_r, outer_r)
        halo = QColor(PALETTE.accent if self._hovered else PALETTE.border_strong)
        halo.setAlpha(55 if self._hovered else 35)
        painter.fillPath(path, halo)

        inner = QPainterPath()
        inner.addEllipse(QPointF(0, 0), outer_r - 2.5, outer_r - 2.5)
        painter.fillPath(inner, color)
        painter.setPen(QPen(QColor(PALETTE.bg_node), 1.4))
        painter.drawPath(inner)

        if self._connected:
            painter.setBrush(QColor(PALETTE.accent))
            painter.setPen(QPen(QColor(PALETTE.accent), 1))
            painter.drawEllipse(QPointF(0, 0), 3.0, 3.0)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hovered = True
        self.setToolTip(f"{self._port_name}\n({self._direction.value})")
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.connection_drag_started.emit(self._node_id, self._port_name, self._direction.value)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.connection_drag_moved.emit(
                self._node_id, self._port_name, self.mapToScene(event.pos())
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.connection_drag_finished.emit(self._node_id, self._port_name, scene_pos)
            event.accept()
            return
        super().mouseReleaseEvent(event)
