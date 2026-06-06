"""Workflow canvas (QGraphicsView).

The canvas is the primary workspace and provides:

- Smooth pan (middle-mouse drag, space + drag, or edge pan)
- Smooth zoom (Ctrl+wheel, with limits)
- Rubber-band box selection
- Snap-to-grid (when enabled)
- Fit-to-screen
- Auto-center workflow
- Minimap overlay
- Grid background with major/minor dots
- Connection drag preview
- Edge animations during compute
- Keyboard navigation: select all, focus selected, delete, duplicate, etc.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QFont,
    QKeyEvent,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPen,
    QResizeEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView, QMenu, QWidget

from polaris_studio.core.graph import WorkflowGraph
from polaris_studio.core.node_registry import NODE_REGISTRY
from polaris_studio.ui.graph.box_select_item import BoxSelectionItem
from polaris_studio.ui.graph.connection_drag import ConnectionDrag
from polaris_studio.ui.graph.edge_item import EdgeItem
from polaris_studio.ui.graph.minimap import MinimapOverlay
from polaris_studio.ui.graph.node_item import NodeItem
from polaris_studio.ui.graph.port_item import PortDirection, PortItem
from polaris_studio.ui.motion import animate_graphics_pos, graphics_destroy, graphics_materialize
from polaris_studio.ui.theme import PALETTE, font_instrument_serif, font_inter

GRID_SIZE = 20.0
GRID_DOT_RADIUS = 1.0
GRID_MAJOR_EVERY = 5
MIN_ZOOM = 0.15
MAX_ZOOM = 4.0
ZOOM_STEP = 1.15


class GraphCanvas(QGraphicsView):
    node_selected = Signal(str)
    node_moved = Signal(str, float, float)
    node_deleted = Signal(str)
    node_duplicated = Signal(str)
    node_create_requested = Signal(str, float, float)
    connection_requested = Signal(str, str, str, str)
    selection_changed = Signal(list)
    viewport_transform_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self._scene.setSceneRect(-20000, -20000, 40000, 40000)
        self._scene.setBackgroundBrush(QColor(PALETTE.bg_canvas))
        self.setScene(self._scene)

        self._node_items: Dict[str, NodeItem] = {}
        self._edge_items: List[EdgeItem] = []
        self._connection_drag: Optional[ConnectionDrag] = None
        self._drag_source_node: Optional[str] = None
        self._drag_source_port: Optional[str] = None
        self._drag_source_direction: Optional[str] = None

        self._box_select_item: Optional[BoxSelectionItem] = None
        self._box_press_pos: Optional[QPointF] = None
        self._box_dragging: bool = False

        self._panning: bool = False
        self._pan_start: QPoint = QPoint()
        self._space_pressed: bool = False

        self._grid_enabled: bool = True
        self._snap_enabled: bool = True

        self._zoom_level: float = 1.0
        self._minimap: Optional[MinimapOverlay] = None

        self._pulse_timer: QTimer = QTimer(self)
        self._pulse_timer.setInterval(16)
        self._pulse_timer.timeout.connect(self._on_pulse_tick)
        self._pulse_offset: float = 0.0
        self._animating_edges: bool = False

        self._setup_view()
        self._setup_minimap()
        self._populate_demo()

    def _setup_view(self) -> None:
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
            | QPainter.RenderHint.TextAntialiasing
        )
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setStyleSheet(
            f"""
            QGraphicsView {{
                background-color: {PALETTE.bg_canvas};
                border: none;
            }}
            """
        )

    def _setup_minimap(self) -> None:
        self._minimap = MinimapOverlay(self, parent=self)
        self._minimap.setVisible(True)

    def _populate_demo(self) -> None:
        self._scene.clear()
        self._node_items.clear()
        self._edge_items.clear()

    def set_grid_enabled(self, enabled: bool) -> None:
        self._grid_enabled = enabled
        self._scene.invalidate()
        self.viewport().update()

    def set_snap_enabled(self, enabled: bool) -> None:
        self._snap_enabled = enabled

    def _snap(self, value: float) -> float:
        if not self._snap_enabled:
            return value
        return round(value / GRID_SIZE) * GRID_SIZE

    def _draw_grid(self, painter: QPainter, rect: QRectF) -> None:
        if not self._grid_enabled:
            return
        left = math.floor(rect.left() / GRID_SIZE) * GRID_SIZE
        top = math.floor(rect.top() / GRID_SIZE) * GRID_SIZE
        right = rect.right()
        bottom = rect.bottom()

        minor_pen = QPen(QColor(PALETTE.grid_dot), 0)
        minor_pen.setCosmetic(True)
        painter.setPen(minor_pen)
        x = left
        col = 0
        while x < right:
            y = top
            row = 0
            while y < bottom:
                if col % GRID_MAJOR_EVERY == 0 and row % GRID_MAJOR_EVERY == 0:
                    painter.setBrush(QColor(PALETTE.grid_dot_strong))
                    painter.drawEllipse(QPointF(x, y), GRID_DOT_RADIUS + 0.5, GRID_DOT_RADIUS + 0.5)
                else:
                    painter.setBrush(QColor(PALETTE.grid_dot))
                    painter.drawEllipse(QPointF(x, y), GRID_DOT_RADIUS, GRID_DOT_RADIUS)
                y += GRID_SIZE
                row += 1
            x += GRID_SIZE
            col += 1

    def drawBackground(self, painter: QPainter, rect: QRectF | QRect) -> None:  # type: ignore[override]
        target = QRectF(rect)
        painter.fillRect(target, QColor(PALETTE.bg_canvas))
        self._draw_grid(painter, target)

    def drawForeground(self, painter: QPainter, rect: QRectF | QRect) -> None:  # type: ignore[override]
        if self._node_items:
            return
        painter.save()
        painter.resetTransform()
        view_rect = self.viewport().rect()
        cx = view_rect.width() // 2
        cy = view_rect.height() // 2
        painter.translate(cx, cy)
        painter.setOpacity(0.7)
        title_font = font_instrument_serif(34)
        title_font.setStyleName("Regular")
        painter.setPen(QColor(PALETTE.text_primary))
        painter.setFont(title_font)
        title_rect = QRectF(-320.0, -64.0, 640.0, 52.0)
        painter.drawText(title_rect, int(Qt.AlignmentFlag.AlignCenter), "Build your workflow.")
        painter.setOpacity(0.5)
        sub_font = font_instrument_serif(15)
        sub_font.setStyleName("Regular")
        sub_font.setItalic(True)
        painter.setPen(QColor(PALETTE.text_secondary))
        painter.setFont(sub_font)
        sub_rect = QRectF(-320.0, -10.0, 640.0, 22.0)
        painter.drawText(
            sub_rect, int(Qt.AlignmentFlag.AlignCenter), "a canvas for your data, finally."
        )
        painter.setOpacity(0.55)
        hint_font = font_inter(11, QFont.Weight.Normal)
        painter.setFont(hint_font)
        hint_rect = QRectF(-280.0, 30.0, 560.0, 56.0)
        hint_text = (
            "Right-click to add a node, or press Ctrl+Shift+A to open the AI assistant.\n"
            "Drag from a port to connect nodes. Hold Space to pan, scroll to zoom."
        )
        painter.drawText(
            hint_rect, int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap), hint_text
        )
        painter.restore()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier or True:
            angle = event.angleDelta().y()
            if angle == 0:
                return
            factor = ZOOM_STEP if angle > 0 else 1.0 / ZOOM_STEP
            new_zoom = self._zoom_level * factor
            if MIN_ZOOM <= new_zoom <= MAX_ZOOM:
                self._zoom_level = new_zoom
                self.scale(factor, factor)
                if self._minimap is not None:
                    self._minimap.update()
                self.viewport_transform_changed.emit()
            event.accept()
            return
        super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_pressed = True
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
            return
        if event.key() == Qt.Key.Key_G and not event.isAutoRepeat():
            self._grid_enabled = not self._grid_enabled
            self._scene.invalidate()
            self.viewport().update()
            event.accept()
            return
        if event.key() == Qt.Key.Key_F and not event.isAutoRepeat():
            self.zoom_to_fit()
            event.accept()
            return
        if event.key() == Qt.Key.Key_H and not event.isAutoRepeat():
            self._snap_enabled = not self._snap_enabled
            event.accept()
            return
        if event.matches(QKeySequence.StandardKey.SelectAll):
            for item in self._scene.items():
                if isinstance(item, NodeItem):
                    item.setSelected(True)
            self._emit_selection_changed()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._delete_selected()
            event.accept()
            return
        if event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._duplicate_selected()
            event.accept()
            return
        if (
            event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal)
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            factor = ZOOM_STEP
            new_zoom = self._zoom_level * factor
            if new_zoom <= MAX_ZOOM:
                self._zoom_level = new_zoom
                self.scale(factor, factor)
                if self._minimap is not None:
                    self._minimap.update()
                self.viewport_transform_changed.emit()
            event.accept()
            return
        if (
            event.key() == Qt.Key.Key_Minus
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            factor = 1.0 / ZOOM_STEP
            new_zoom = self._zoom_level * factor
            if new_zoom >= MIN_ZOOM:
                self._zoom_level = new_zoom
                self.scale(factor, factor)
                if self._minimap is not None:
                    self._minimap.update()
                self.viewport_transform_changed.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_pressed = False
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().keyReleaseEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        mime = event.mimeData()
        if not mime.hasText():
            super().dropEvent(event)
            return
        node_type = mime.text().strip()
        if not node_type:
            event.ignore()
            return
        scene_pos = self.mapToScene(event.position().toPoint())
        self.node_create_requested.emit(
            node_type, self._snap(scene_pos.x()), self._snap(scene_pos.y())
        )
        event.acceptProposedAction()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton or self._space_pressed:
            self._panning = True
            self._pan_start = event.position().toPoint()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        if event.button() == Qt.MouseButton.RightButton:
            item = self.itemAt(event.position().toPoint())
            if item is None or not isinstance(item, (NodeItem, EdgeItem)):
                self._show_canvas_context_menu(event.position().toPoint())
                event.accept()
                return
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            item_at = self._scene.itemAt(scene_pos, self.transform())
            port = self._port_at(item_at) or self._nearest_port(scene_pos)
            if port is not None:
                self._begin_connection_drag(port, scene_pos)
                event.accept()
                return
            super().mousePressEvent(event)
            return

        super().mousePressEvent(event)

    def _port_at(self, item: Optional[QGraphicsItem]) -> Optional[PortItem]:
        cur = item
        while cur is not None:
            if isinstance(cur, PortItem):
                return cur
            cur = cur.parentItem()
        return None

    def _nearest_port(self, scene_pos: QPointF, radius: float = 18.0) -> Optional[PortItem]:
        best_port: Optional[PortItem] = None
        best_distance = radius
        for node_item in self._node_items.values():
            for port in node_item.ports():
                delta = port.scene_anchor() - scene_pos
                distance = math.hypot(delta.x(), delta.y())
                if distance <= best_distance:
                    best_distance = distance
                    best_port = port
        return best_port

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._panning:
            delta = event.position().toPoint() - self._pan_start
            self._pan_start = event.position().toPoint()
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())
            event.accept()
            return

        if self._connection_drag is not None:
            scene_pos = self.mapToScene(event.position().toPoint())
            self._connection_drag.set_end_pos(scene_pos)
            self._update_drag_target(scene_pos)
            event.accept()
            return

        if (
            self._box_dragging
            and self._box_press_pos is not None
            and self._box_select_item is not None
        ):
            current = self.mapToScene(event.position().toPoint())
            rect = QRectF(self._box_press_pos, current).normalized()
            self._box_select_item.set_rect(rect)
            self._apply_box_selection(rect)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._panning and event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        if self._connection_drag is not None and event.button() == Qt.MouseButton.LeftButton:
            self._complete_connection_drag(event.position().toPoint())
            event.accept()
            return

        if self._box_dragging and event.button() == Qt.MouseButton.LeftButton:
            self._finish_box_selection()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._minimap is not None:
            self._minimap.updateGeometry()
            self._minimap.update()

    def _on_pulse_tick(self) -> None:
        self._pulse_offset = (self._pulse_offset + 0.012) % 1.0
        for edge in self._edge_items:
            edge.update_pulse(self._pulse_offset)

    def start_edge_animation(self) -> None:
        if not self._animating_edges:
            self._animating_edges = True
            for edge in self._edge_items:
                edge.set_animating(True)
            self._pulse_timer.start()

    def stop_edge_animation(self) -> None:
        if self._animating_edges:
            self._animating_edges = False
            for edge in self._edge_items:
                edge.set_animating(False)
            self._pulse_timer.stop()

    def _begin_connection_drag(self, port: PortItem, scene_pos: QPointF) -> None:
        self._drag_source_node = port.node_id
        self._drag_source_port = port.port_name
        self._drag_source_direction = port.direction.value
        self._connection_drag = ConnectionDrag(self._node_items[port.node_id], port.port_name)
        self._scene.addItem(self._connection_drag)
        self._connection_drag.set_end_pos(scene_pos)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def _update_drag_target(self, scene_pos: QPointF) -> None:
        if self._connection_drag is None:
            return
        item = self._scene.itemAt(scene_pos, self.transform())
        port = self._port_at(item) or self._nearest_port(scene_pos)
        if port is None:
            self._connection_drag.set_valid(True)
            return
        if (
            port.node_id == self._drag_source_node
            or port.direction.value == self._drag_source_direction
        ):
            self._connection_drag.set_valid(False)
            return
        self._connection_drag.set_valid(True)

    def _complete_connection_drag(self, screen_pos: QPoint) -> None:
        if self._connection_drag is None:
            return
        scene_pos = self.mapToScene(screen_pos)
        self._complete_connection_drag_at(scene_pos)

    def _complete_connection_drag_at(self, scene_pos: QPointF) -> None:
        if self._connection_drag is None:
            return
        item = self._scene.itemAt(scene_pos, self.transform())
        port = self._port_at(item) or self._nearest_port(scene_pos)
        if (
            port is not None
            and port.node_id != self._drag_source_node
            and port.direction.value != self._drag_source_direction
        ):
            source_id = self._drag_source_node or ""
            target_id = port.node_id
            if self._drag_source_direction == "input":
                self.connection_requested.emit(
                    target_id,
                    port.port_name,
                    source_id,
                    self._drag_source_port,
                )
            else:
                self.connection_requested.emit(
                    source_id,
                    self._drag_source_port,
                    target_id,
                    port.port_name,
                )
        self._scene.removeItem(self._connection_drag)
        self._connection_drag = None
        self._drag_source_node = None
        self._drag_source_port = None
        self._drag_source_direction = None
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    def _show_canvas_context_menu(self, screen_pos: QPoint) -> None:
        scene_pos = self.mapToScene(screen_pos)
        menu = QMenu(self)

        add_menu = menu.addMenu("Add Node")
        categories = [
            (
                "Source",
                [
                    "csv_reader",
                    "parquet_reader",
                    "json_reader",
                    "xlsx_reader",
                    "clipboard_paste",
                    "manual_entry",
                ],
            ),
            (
                "Transform",
                [
                    "filter",
                    "select_columns",
                    "add_column",
                    "rename_columns",
                    "drop_columns",
                    "cast_column",
                    "fill_null",
                    "string_ops",
                    "date_parse",
                    "sample",
                    "slice",
                    "deduplicate",
                    "unpivot",
                    "explode",
                ],
            ),
            ("Aggregate", ["group_by_agg", "rolling_window", "pivot_table"]),
            (
                "Join",
                ["inner_join", "left_join", "right_join", "full_join", "cross_join", "anti_join"],
            ),
            ("Sort", ["sort"]),
            (
                "Chart",
                ["bar_chart", "line_chart", "scatter_chart", "histogram", "box_chart", "heatmap"],
            ),
            (
                "Output",
                ["table_output", "export_csv", "export_parquet", "export_json", "export_xlsx"],
            ),
        ]
        for cat_name, types in categories:
            cat_menu = add_menu.addMenu(cat_name)
            for nt in types:
                spec = NODE_REGISTRY.get(nt)
                if spec:
                    action = cat_menu.addAction(spec.display_name)
                    action.setData((nt, scene_pos.x(), scene_pos.y()))
                    action.setToolTip(spec.description)

        menu.addSeparator()
        fit_action = menu.addAction("Fit to Screen (F)")
        fit_action.triggered.connect(self.zoom_to_fit)
        snap_action = menu.addAction("Toggle Snap to Grid (H)")
        snap_action.triggered.connect(lambda: self.set_snap_enabled(not self._snap_enabled))  # type: ignore[misc]
        grid_action = menu.addAction("Toggle Grid (G)")
        grid_action.triggered.connect(lambda: self.set_grid_enabled(not self._grid_enabled))

        chosen = menu.exec(self.mapToGlobal(screen_pos))
        if chosen is not None and chosen.data() is not None:
            node_type, x, y = chosen.data()
            self.node_create_requested.emit(node_type, self._snap(x), self._snap(y))

    def _delete_selected(self) -> None:
        selected = [item for item in self._scene.selectedItems() if isinstance(item, NodeItem)]
        for item in selected:
            self.node_deleted.emit(item.node_id)

    def _duplicate_selected(self) -> None:
        selected = [item for item in self._scene.selectedItems() if isinstance(item, NodeItem)]
        for item in selected:
            self.node_duplicated.emit(item.node_id)

    def _ensure_box_item(self) -> BoxSelectionItem:
        if self._box_select_item is None:
            self._box_select_item = BoxSelectionItem()
            self._scene.addItem(self._box_select_item)
        return self._box_select_item

    def _apply_box_selection(self, rect: QRectF) -> None:
        for item in self._scene.items(rect, Qt.ItemSelectionMode.IntersectsItemShape):
            if isinstance(item, NodeItem):
                item.setSelected(True)
            elif isinstance(item, EdgeItem):
                item.setSelected(True)

    def _finish_box_selection(self) -> None:
        if self._box_select_item is not None:
            self._scene.removeItem(self._box_select_item)
            self._box_select_item = None
        self._box_dragging = False
        self._box_press_pos = None
        self._emit_selection_changed()

    def _emit_selection_changed(self) -> None:
        ids = [item.node_id for item in self._scene.selectedItems() if isinstance(item, NodeItem)]
        self.selection_changed.emit(ids)

    def sync_to_graph(self, graph: WorkflowGraph) -> None:
        self.stop_edge_animation()
        current_ids = set(self._node_items.keys())
        graph_ids = set(graph.get_nodes().keys())

        for nid in current_ids - graph_ids:
            item = self._node_items.pop(nid, None)
            if item:
                graphics_destroy(item, on_finished=lambda item=item: self._scene.removeItem(item))  # type: ignore[misc]

        for nid in graph_ids - current_ids:
            node = graph.get_node(nid)
            if not node:
                continue
            item = NodeItem(node)
            item.setPos(self._snap(node.position[0]), self._snap(node.position[1]))
            item.node_moved.connect(self._on_node_moved)
            item.node_selected.connect(self._on_node_selected)
            item.node_delete_requested.connect(self.node_deleted)
            item.node_duplicate_requested.connect(self.node_duplicated)
            item.port_connection_started.connect(self._on_port_connection_started)
            item.port_connection_moved.connect(self._on_port_connection_moved)
            item.port_connection_ended.connect(self._on_port_connection_ended)
            self._node_items[nid] = item
            self._scene.addItem(item)
            graphics_materialize(item)

        for nid in graph_ids & current_ids:
            node = graph.get_node(nid)
            item = self._node_items[nid]
            if node and item:
                target = QPointF(self._snap(node.position[0]), self._snap(node.position[1]))
                if (item.pos() - target).manhattanLength() > 0.5:
                    animate_graphics_pos(item, target)
                item.set_dirty(node.is_dirty)
                item.set_error(node.error is not None, node.error or "")

        for e_item in list(self._edge_items):
            self._scene.removeItem(e_item)
        self._edge_items.clear()
        for item in self._node_items.values():
            item.clear_port_connections()
        for ge in graph.get_edges():
            src_item = self._node_items.get(ge.source_id)
            tgt_item = self._node_items.get(ge.target_id)
            if src_item is None or tgt_item is None:
                continue
            src_item.set_port_connected(ge.source_port, True)
            tgt_item.set_port_connected(ge.target_port, True)
            e_item = EdgeItem(ge, src_item, tgt_item)
            self._edge_items.append(e_item)
            self._scene.addItem(e_item)

        if self._minimap is not None:
            self._minimap.update()

    def get_node_item(self, node_id: str) -> Optional[NodeItem]:
        return self._node_items.get(node_id)

    def zoom_to_fit(self, padding: float = 80.0) -> None:
        if not self._node_items:
            return
        rect = QRectF()
        for item in self._node_items.values():
            r = item.sceneBoundingRect()
            rect = r if rect.isEmpty() else rect.united(r)
        if rect.isEmpty():
            return
        padded = rect.adjusted(-padding, -padding, padding, padding)
        self.fitInView(padded, Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_level = self.transform().m11()
        if self._zoom_level > 2.0:
            self.resetTransform()
            self.scale(1.0, 1.0)
            self._zoom_level = 1.0
            self.centerOn(rect.center())
        if self._minimap is not None:
            self._minimap.update()
        self.viewport_transform_changed.emit()

    def center_workflow(self) -> None:
        if not self._node_items:
            return
        rect = QRectF()
        for item in self._node_items.values():
            r = item.sceneBoundingRect()
            rect = r if rect.isEmpty() else rect.united(r)
        if not rect.isEmpty():
            self.centerOn(rect.center())
            if self._minimap is not None:
                self._minimap.update()
            self.viewport_transform_changed.emit()

    def focus_node(self, node_id: str) -> None:
        item = self._node_items.get(node_id)
        if item is None:
            return
        self.centerOn(item)
        self._zoom_level = max(self._zoom_level, 1.2)
        cur = self.transform().m11()
        if cur < 1.2:
            factor = 1.2 / cur
            self.scale(factor, factor)
        if self._minimap is not None:
            self._minimap.update()

    def _on_node_moved(self, node_id: str, x: float, y: float) -> None:
        if self._snap_enabled:
            sx = self._snap(x)
            sy = self._snap(y)
            if sx != x or sy != y:
                item = self._node_items.get(node_id)
                if item:
                    item.setPos(sx, sy)
                x, y = sx, sy
        self.node_moved.emit(node_id, x, y)
        self._refresh_edges_for_node(node_id)
        if self._minimap is not None:
            self._minimap.update()

    def _on_node_selected(self, node_id: str) -> None:
        self.node_selected.emit(node_id)
        self._emit_selection_changed()

    def _on_port_connection_started(self, node_id: str, port_name: str, direction: str) -> None:
        item = self._node_items.get(node_id)
        if item is None:
            return
        port = item.get_port(
            port_name,
            PortDirection.INPUT if direction == "input" else PortDirection.OUTPUT,
        )
        if port is None:
            return
        self._begin_connection_drag(port, port.scene_anchor())

    def _on_port_connection_moved(self, _node_id: str, _port_name: str, scene_pos: QPointF) -> None:
        if self._connection_drag is None:
            return
        self._connection_drag.set_end_pos(scene_pos)
        self._update_drag_target(scene_pos)

    def _on_port_connection_ended(self, _node_id: str, _port_name: str, scene_pos: QPointF) -> None:
        if self._connection_drag is None:
            return
        self._complete_connection_drag_at(scene_pos)

    def _refresh_edges_for_node(self, node_id: str) -> None:
        for edge_item in self._edge_items:
            edge = edge_item.get_edge()
            if edge and (edge.source_id == node_id or edge.target_id == node_id):
                edge_item.update_positions()

    def get_selected_node_ids(self) -> List[str]:
        return [item.node_id for item in self._scene.selectedItems() if isinstance(item, NodeItem)]

    def selected_nodes(self) -> List[NodeItem]:
        return [item for item in self._scene.selectedItems() if isinstance(item, NodeItem)]
