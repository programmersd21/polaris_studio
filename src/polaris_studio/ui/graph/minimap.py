"""Minimap overlay for the workflow canvas.

Renders a bird's-eye view of nodes and edges plus a viewport rectangle.
Clicking or dragging on the minimap centers the main canvas on the
corresponding scene position.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPen, QResizeEvent
from PySide6.QtWidgets import QGraphicsView, QSizePolicy, QWidget

from polaris_studio.ui.graph.edge_item import EdgeItem
from polaris_studio.ui.graph.node_item import NodeItem
from polaris_studio.ui.theme import PALETTE, RADII, font_inter, category_color


class MinimapOverlay(QWidget):
    """Floating minimap with click-to-pan and drag-to-pan."""

    WIDTH = 220
    HEIGHT = 150
    MARGIN = 16

    def __init__(self, view: QGraphicsView, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._view = view
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dragging: bool = False
        self._drag_offset: QPointF = QPointF(0, 0)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.move_to_corner()

    def move_to_corner(self) -> None:
        if self._view is None:
            return
        w = self._view.viewport().width()
        h = self._view.viewport().height()
        self.move(w - self.WIDTH - self.MARGIN, h - self.HEIGHT - self.MARGIN)

    def updateGeometry(self) -> None:
        self.move_to_corner()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.move_to_corner()

    def _scene_rect(self) -> QRectF:
        scene = self._view.scene()
        if scene is None:
            return QRectF()
        rect = scene.itemsBoundingRect()
        if rect.isEmpty() or rect.width() < 10 or rect.height() < 10:
            view_rect = self._view.mapToScene(self._view.viewport().rect()).boundingRect()
            return view_rect.adjusted(-200, -200, 200, 200)
        return rect.adjusted(-100, -100, 100, 100)

    def _scale(self, scene_rect: QRectF) -> float:
        sx = self.width() / scene_rect.width() if scene_rect.width() else 1.0
        sy = self.height() / scene_rect.height() if scene_rect.height() else 1.0
        return min(sx, sy)

    def _to_scene(self, pos: QPointF) -> QPointF:
        scene_rect = self._scene_rect()
        scale = self._scale(scene_rect)
        cx = scene_rect.center().x()
        cy = scene_rect.center().y()
        sx = (pos.x() - self.width() / 2) / scale + cx
        sy = (pos.y() - self.height() / 2) / scale + cy
        return QPointF(sx, sy)

    def _from_scene(self, scene_pos: QPointF) -> QPointF:
        scene_rect = self._scene_rect()
        scale = self._scale(scene_rect)
        cx = scene_rect.center().x()
        cy = scene_rect.center().y()
        return QPointF(
            (scene_pos.x() - cx) * scale + self.width() / 2,
            (scene_pos.y() - cy) * scale + self.height() / 2,
        )

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor(PALETTE.bg_panel)
        bg.setAlpha(220)
        painter.setBrush(bg)
        painter.setPen(QPen(QColor(PALETTE.border_strong), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), RADII.md, RADII.md)

        scene = self._view.scene()
        if scene is None:
            return
        scene_rect = self._scene_rect()
        scale = self._scale(scene_rect)
        cx = scene_rect.center().x()
        cy = scene_rect.center().y()

        painter.save()
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(scale, scale)
        painter.translate(-cx, -cy)

        for item in scene.items():
            if isinstance(item, EdgeItem):
                path = item.path()
                painter.setPen(QPen(QColor(PALETTE.edge), max(1.0 / scale, 0.4)))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(path)
            elif isinstance(item, NodeItem):
                br = item.sceneBoundingRect()
                color = QColor(PALETTE.cat_transform)
                if item._spec():
                    color = QColor(category_color(item._spec().category))  # type: ignore[attr-defined]
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawRoundedRect(br, max(2.0 / scale, 1.0), max(2.0 / scale, 1.0))

        view_rect = self._view.mapToScene(self._view.viewport().rect()).boundingRect()
        painter.setPen(QPen(QColor(PALETTE.accent), max(2.0 / scale, 1.2)))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(view_rect)
        painter.restore()

        title_font = font_inter(8, QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(QColor(PALETTE.text_secondary))
        label_rect = self.rect().adjusted(8, 4, -8, -self.height() + 14)
        painter.drawText(
            label_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, "MINIMAP"
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._pan_to(event.position())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            self._pan_to(event.position())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _pan_to(self, local_pos: QPointF) -> None:
        target = self._to_scene(local_pos)
        self._view.centerOn(target)
        self.update()
