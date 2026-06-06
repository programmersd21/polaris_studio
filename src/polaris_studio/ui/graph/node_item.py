"""Node visual component.

A node in the workflow is rendered as a card with:

- Header strip with category color, icon, title, and node id
- Body with input ports on the left and output ports on the right
- Footer area showing the first few parameters
- Visual state (NORMAL / HOVERED / SELECTED / RUNNING / SUCCESS / ERROR / DISABLED)
- Optional icon (single-letter glyph) based on category

The node uses solid, layered fills with subtle drop-shadow and crisp borders.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, QTimer, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsSceneHoverEvent,
    QMenu,
    QStyleOptionGraphicsItem,
    QWidget,
)

from polaris_studio.core.graph import Node
from polaris_studio.core.node_registry import NODE_REGISTRY
from polaris_studio.ui.graph.port_item import PortDirection, PortItem, PortType
from polaris_studio.ui.motion import pulse_graphics_item
from polaris_studio.ui.theme import (
    PALETTE,
    RADII,
    TYPO,
    category_color,
    font_inter,
    font_mono,
    font_outfit,
)


class NodeState(Enum):
    NORMAL = "normal"
    HOVERED = "hovered"
    SELECTED = "selected"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    DISABLED = "disabled"


NODE_WIDTH = 200
HEADER_HEIGHT = 38
ROW_HEIGHT = 22
PORT_SPACING = 22
PORT_TOP_PADDING = 14
BODY_PADDING = 12
MIN_BODY_HEIGHT = 50
SHADOW_BLUR = 24


def _category_glyph(category: str) -> str:
    return {
        "Source": "S",
        "Transform": "T",
        "Filter": "F",
        "Aggregate": "A",
        "Join": "J",
        "Sort": "S",
        "Chart": "C",
        "Output": "O",
    }.get(category, "?")


class NodeItem(QGraphicsObject):
    """Single node rendered inside the workflow canvas."""

    node_moved = Signal(str, float, float)
    node_selected = Signal(str)
    node_delete_requested = Signal(str)
    node_duplicate_requested = Signal(str)
    port_connection_started = Signal(str, str, str)
    port_connection_moved = Signal(str, str, object)
    port_connection_ended = Signal(str, str, object)

    def __init__(self, node: Node, parent: Optional[QGraphicsItem] = None) -> None:
        super().__init__(parent)
        self._node = node
        self._ports: Dict[str, PortItem] = {}
        self._state = NodeState.NORMAL
        self._is_computing = False
        self._has_error = bool(node.error)
        self._error_text = node.error or ""
        self._dirty = node.is_dirty

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setZValue(5)

        self._create_ports()
        self._update_port_positions()

    @property
    def node_id(self) -> str:
        return self._node.node_id

    @property
    def state(self) -> NodeState:
        return self._state

    def get_node(self) -> Node:
        return self._node

    def _create_ports(self) -> None:
        spec = NODE_REGISTRY.get(self._node.node_type)
        if spec is None:
            return
        for i, name in enumerate(spec.input_ports):
            port = PortItem(
                self._node.node_id, name, PortDirection.INPUT, PortType.DATA, parent=self
            )
            port.connection_drag_started.connect(self._on_port_drag_started)
            port.connection_drag_moved.connect(self._on_port_drag_moved)
            port.connection_drag_finished.connect(self._on_port_drag_finished)
            self._ports[f"in::{name}"] = port
        for i, name in enumerate(spec.output_ports):
            port = PortItem(
                self._node.node_id, name, PortDirection.OUTPUT, PortType.DATA, parent=self
            )
            port.connection_drag_started.connect(self._on_port_drag_started)
            port.connection_drag_moved.connect(self._on_port_drag_moved)
            port.connection_drag_finished.connect(self._on_port_drag_finished)
            self._ports[f"out::{name}"] = port

    def _update_port_positions(self) -> None:
        spec = NODE_REGISTRY.get(self._node.node_type)
        if spec is None:
            return
        for i, name in enumerate(spec.input_ports):
            port = self._ports.get(f"in::{name}")
            if port is None:
                continue
            port.setPos(-NODE_WIDTH // 2 + 1, HEADER_HEIGHT + PORT_TOP_PADDING + i * PORT_SPACING)
        for i, name in enumerate(spec.output_ports):
            port = self._ports.get(f"out::{name}")
            if port is None:
                continue
            port.setPos(NODE_WIDTH // 2 - 1, HEADER_HEIGHT + PORT_TOP_PADDING + i * PORT_SPACING)

    def _spec(self):
        return NODE_REGISTRY.get(self._node.node_type)

    def _compute_body_height(self) -> float:
        spec = self._spec()
        if spec is None:
            return MIN_BODY_HEIGHT
        n_in = len(spec.input_ports)
        n_out = len(spec.output_ports)
        n_params = min(len(spec.params), 3)
        n_rows = max(n_in, n_out, n_params, 1)
        return PORT_TOP_PADDING + n_rows * PORT_SPACING + BODY_PADDING

    def boundingRect(self) -> QRectF:
        h = self._compute_body_height()
        w = NODE_WIDTH
        pad = 12
        return QRectF(-w / 2 - pad, -pad, w + pad * 2, HEADER_HEIGHT + h + pad * 2)

    def _state_palette(self) -> Tuple[QColor, QColor, float]:
        """Return (border_color, body_color, border_width) for the current state."""
        pal = PALETTE
        if self._state == NodeState.ERROR or self._has_error:
            return QColor(pal.error), QColor("#fde4e1"), 1.6
        if self._state == NodeState.RUNNING or self._is_computing:
            return QColor(pal.running), QColor("#dff1fb"), 1.6
        if self._state == NodeState.SUCCESS:
            return QColor(pal.success), QColor("#e4f6ef"), 1.4
        if self._state == NodeState.SELECTED:
            return QColor(pal.accent), QColor(pal.bg_node), 1.6
        if self._state == NodeState.HOVERED:
            return QColor(pal.border_strong), QColor(pal.bg_node_alt), 1.2
        return QColor(pal.border), QColor(pal.bg_node), 1.0

    def _set_state(self, state: NodeState) -> None:
        if self._state == state:
            return
        self._state = state
        self.update()

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        if self._state in (NodeState.NORMAL, NodeState.SELECTED):
            self._set_state(NodeState.HOVERED)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        if self._state == NodeState.HOVERED:
            self._set_state(NodeState.SELECTED if self.isSelected() else NodeState.NORMAL)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu()

        execute = menu.addAction("Execute Node")
        execute.triggered.connect(lambda: None)

        preview = menu.addAction("Preview Output")
        preview.triggered.connect(lambda: None)

        menu.addSeparator()

        dup = menu.addAction("Duplicate")
        dup.triggered.connect(lambda: self.node_duplicate_requested.emit(self._node.node_id))

        menu.addSeparator()

        delete = menu.addAction("Delete")
        delete.triggered.connect(lambda: self.node_delete_requested.emit(self._node.node_id))

        menu.exec(event.screenPos())

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.node_moved.emit(self._node.node_id, self.pos().x(), self.pos().y())
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged and value:
            self._set_state(NodeState.SELECTED)
            self.node_selected.emit(self._node.node_id)
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged and not value:
            self._set_state(NodeState.NORMAL)
        return super().itemChange(change, value)

    def set_dirty(self, dirty: bool) -> None:
        self._dirty = dirty
        self.update()

    def set_computing(self, computing: bool) -> None:
        was_computing = self._is_computing
        self._is_computing = computing
        if computing:
            self._set_state(NodeState.RUNNING)
            pulse_graphics_item(self, peak_scale=1.025)
        else:
            self._set_state(NodeState.SELECTED if self.isSelected() else NodeState.NORMAL)
            if was_computing:
                self._set_state(NodeState.SUCCESS)
                pulse_graphics_item(self, peak_scale=1.035)
                QTimer.singleShot(
                    420,
                    lambda: self._set_state(
                        NodeState.SELECTED if self.isSelected() else NodeState.NORMAL
                    ),
                )
        self.update()

    def set_error(self, error: bool, message: str = "") -> None:
        self._has_error = error
        self._error_text = message
        if error:
            self._set_state(NodeState.ERROR)
        else:
            self._set_state(NodeState.SELECTED if self.isSelected() else NodeState.NORMAL)
        self.update()

    def set_port_connected(self, port_name: str, connected: bool) -> None:
        for key, port in self._ports.items():
            if key.endswith(f"::{port_name}"):
                port.set_connected(connected)

    def clear_port_connections(self) -> None:
        for port in self._ports.values():
            port.set_connected(False)

    def ports(self) -> List[PortItem]:
        return list(self._ports.values())

    def get_port(
        self, port_name: str, direction: Optional[PortDirection] = None
    ) -> Optional[PortItem]:
        if direction == PortDirection.INPUT or direction is None:
            port = self._ports.get(f"in::{port_name}")
            if port:
                return port
        if direction == PortDirection.OUTPUT or direction is None:
            port = self._ports.get(f"out::{port_name}")
            if port:
                return port
        return None

    def get_port_scene_pos(self, port_name: str) -> QPointF:
        for key, port in self._ports.items():
            if key.endswith(f"::{port_name}"):
                return port.scene_anchor()
        return self.mapToScene(QPointF(0, 0))

    def _on_port_drag_started(self, node_id: str, port_name: str, direction: str) -> None:
        self.port_connection_started.emit(node_id, port_name, direction)

    def _on_port_drag_moved(self, node_id: str, port_name: str, scene_pos: QPointF) -> None:
        self.port_connection_moved.emit(node_id, port_name, scene_pos)

    def _on_port_drag_finished(self, node_id: str, port_name: str, scene_pos: QPointF) -> None:
        self.port_connection_ended.emit(node_id, port_name, scene_pos)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        spec = self._spec()
        border_color, body_color, border_w = self._state_palette()
        body_height = self._compute_body_height()
        body_rect = QRectF(-NODE_WIDTH / 2, 0, NODE_WIDTH, HEADER_HEIGHT + body_height)
        radius = RADII.md

        # Manual shadow (avoid QGraphicsDropShadowEffect which causes QPainter conflicts)
        shadow_path = QPainterPath()
        shadow_rect = body_rect.translated(0, 4).adjusted(0, 0, 2, 4)
        shadow_path.addRoundedRect(shadow_rect, radius, radius)
        painter.setPen(Qt.PenStyle.NoPen)
        shadow_color = QColor(0, 0, 0, 55)
        painter.setBrush(shadow_color)
        painter.drawPath(shadow_path)

        body_path = QPainterPath()
        body_path.addRoundedRect(body_rect, radius, radius)
        painter.setPen(QPen(border_color, border_w))
        painter.setBrush(QColor(body_color))
        painter.drawPath(body_path)

        spec_color = QColor(category_color(spec.category if spec else "Transform"))
        header_rect = QRectF(body_rect.left(), body_rect.top(), body_rect.width(), HEADER_HEIGHT)
        header_path = QPainterPath()
        header_path.addRoundedRect(header_rect, radius, radius)
        header_path.addRect(
            QRectF(
                header_rect.left(),
                header_rect.top() + HEADER_HEIGHT - radius,
                header_rect.width(),
                radius,
            )
        )
        painter.setPen(Qt.PenStyle.NoPen)
        gradient = QLinearGradient(header_rect.topLeft(), header_rect.bottomLeft())
        gradient.setColorAt(0.0, spec_color)
        gradient.setColorAt(1.0, spec_color.darker(140))
        painter.fillPath(header_path, QBrush(gradient))

        painter.setPen(QPen(QColor(0, 0, 0, 24), 1))
        painter.drawLine(
            QPointF(body_rect.left() + 6, HEADER_HEIGHT),
            QPointF(body_rect.right() - 6, HEADER_HEIGHT),
        )

        glyph = _category_glyph(spec.category if spec else "")
        glyph_rect = QRectF(header_rect.left() + 8, header_rect.top() + 6, 26, HEADER_HEIGHT - 12)
        glyph_path = QPainterPath()
        glyph_path.addRoundedRect(glyph_rect, 6, 6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.fillPath(glyph_path, QColor(0, 0, 0, 90))
        painter.setPen(QColor(PALETTE.text_primary))
        painter.setFont(font_outfit(13, QFont.Weight.Bold))
        painter.drawText(glyph_rect, Qt.AlignmentFlag.AlignCenter, glyph)

        title_font = font_outfit(TYPO.title, QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(QColor(PALETTE.text_primary))
        title_rect = QRectF(
            glyph_rect.right() + 8, header_rect.top() + 4, header_rect.width() - 50, 18
        )
        display = spec.display_name if spec else self._node.node_type
        metrics = QFontMetrics(title_font)
        elided = metrics.elidedText(display, Qt.TextElideMode.ElideRight, int(title_rect.width()))
        painter.drawText(
            title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided
        )

        id_font = font_mono(TYPO.micro)
        painter.setFont(id_font)
        painter.setPen(QColor(0, 0, 0, 150))
        id_rect = QRectF(title_rect.left(), header_rect.top() + 21, title_rect.width(), 14)
        id_text = self._node.node_id
        id_metrics = QFontMetrics(id_font)
        id_elided = id_metrics.elidedText(
            id_text, Qt.TextElideMode.ElideRight, int(id_rect.width())
        )
        painter.drawText(
            id_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, id_elided
        )

        if self._dirty:
            dirty_rect = QRectF(body_rect.right() - 14, body_rect.top() + 8, 8, 8)
            painter.setBrush(QColor(PALETTE.warning))
            painter.setPen(QPen(QColor(PALETTE.warning).darker(130), 1))
            painter.drawEllipse(dirty_rect)

        self._draw_body(painter, body_rect, spec)

    def _draw_body(self, painter: QPainter, body_rect: QRectF, spec) -> None:
        param_y = HEADER_HEIGHT + PORT_TOP_PADDING
        if spec and spec.input_ports:
            for i, name in enumerate(spec.input_ports):
                font = font_inter(TYPO.body, QFont.Weight.Medium)
                painter.setFont(font)
                painter.setPen(QColor(PALETTE.text_secondary))
                text_rect = QRectF(
                    body_rect.left() + 18,
                    body_rect.top() + param_y + i * PORT_SPACING - 10,
                    body_rect.width() - 36,
                    18,
                )
                painter.drawText(
                    text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name
                )
        elif spec and spec.params:
            for i, param in enumerate(spec.params[:3]):
                val = self._node.params.get(param.name, param.default)
                display = f"{param.label}: {str(val)[:18]}"
                font = font_mono(TYPO.caption)
                painter.setFont(font)
                painter.setPen(QColor(PALETTE.text_secondary))
                text_rect = QRectF(
                    body_rect.left() + BODY_PADDING,
                    body_rect.top() + param_y + i * PORT_SPACING - 10,
                    body_rect.width() - BODY_PADDING * 2,
                    18,
                )
                painter.drawText(
                    text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, display
                )
        else:
            font = font_inter(TYPO.caption)
            painter.setFont(font)
            painter.setPen(QColor(PALETTE.text_muted))
            text_rect = QRectF(
                body_rect.left() + BODY_PADDING,
                body_rect.top() + param_y,
                body_rect.width() - BODY_PADDING * 2,
                18,
            )
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "-")
