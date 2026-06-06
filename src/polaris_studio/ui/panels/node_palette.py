from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QMimeData, QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QDrag, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QLineEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from polaris_studio.core.node_registry import NODE_REGISTRY
from polaris_studio.ui.motion import FAST, opacity_pop
from polaris_studio.ui.theme import PALETTE, RADII, font_inter


class NodeTree(QTreeWidget):
    def startDrag(self, supportedActions: Qt.DropAction) -> None:
        item = self.currentItem()
        if not item:
            return
        node_type = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_type:
            return

        mime = QMimeData()
        mime.setText(node_type)

        drag = QDrag(self)
        drag.setMimeData(mime)

        pix = QPixmap(180, 36)
        pix.fill(QColor(PALETTE.accent))
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor("#ffffff"))
        p.setFont(font_inter(10, QFont.Weight.DemiBold))
        p.drawText(
            pix.rect().adjusted(12, 0, -12, 0),
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            item.text(0),
        )
        p.end()
        drag.setPixmap(pix)
        drag.setHotSpot(QPoint(20, 18))
        drag.exec(supportedActions)

    def mousePressEvent(self, event) -> None:
        item = self.itemAt(event.pos())
        if item and item.data(0, Qt.ItemDataRole.UserRole):
            self._orig_ss = self.styleSheet()
            self.setStyleSheet(self._orig_ss + "\nbackground-color: rgba(0,0,0,0.04);")
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        orig: Optional[str] = getattr(self, "_orig_ss", None)
        if orig is not None:
            QTimer.singleShot(55, lambda: self.setStyleSheet(orig))
            self._orig_ss = ""
        super().mouseReleaseEvent(event)


class _AnimatedSearch(QLineEdit):
    _IDLE = f"""
        QLineEdit {{
            background: {PALETTE.bg_canvas};
            color: {PALETTE.text_primary};
            border: 1px solid {PALETTE.border};
            border-radius: {RADII.sm}px;
            padding: 8px 12px;
            font-size: 12px;
            selection-background-color: {PALETTE.accent};
        }}
    """
    _FOCUS = f"""
        QLineEdit {{
            background: {PALETTE.bg_node};
            color: {PALETTE.text_primary};
            border: 1.5px solid {PALETTE.accent};
            border-radius: {RADII.sm}px;
            padding: 8px 12px;
            font-size: 12px;
            selection-background-color: {PALETTE.accent};
        }}
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("Search nodes…")
        self.setFont(font_inter(12))
        self.setStyleSheet(self._IDLE)
        self.textChanged.connect(self._on_change)

    def focusInEvent(self, event) -> None:
        self.setStyleSheet(self._FOCUS)
        opacity_pop(self, from_=0.80, to=1.0, duration_ms=FAST)
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:
        self.setStyleSheet(self._IDLE)
        super().focusOutEvent(event)

    def _on_change(self, _: str) -> None:
        opacity_pop(self, from_=0.85, to=1.0, duration_ms=50)


class NodePalette(QWidget):
    node_dropped = Signal(str, float, float)
    node_double_clicked = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._populate()

    def _setup_ui(self) -> None:
        self.setMinimumWidth(220)
        self.setMaximumWidth(300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self._search = _AnimatedSearch()
        self._search.textChanged.connect(self._filter_nodes)
        layout.addWidget(self._search)

        self._tree = NodeTree()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.setAnimated(True)
        self._tree.setDragEnabled(True)
        self._tree.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)
        self._tree.setDragDropMode(QTreeWidget.DragDropMode.DragOnly)
        self._tree.itemDoubleClicked.connect(self._on_double_click)
        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: transparent;
                color: {PALETTE.text_primary};
                border: none;
                font-family: 'Inter';
                font-size: 12px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 6px 8px;
                border-radius: {RADII.sm}px;
                min-height: 28px;
            }}
            QTreeWidget::item:hover {{
                background: {PALETTE.accent_dim};
                color: {PALETTE.text_primary};
            }}
            QTreeWidget::item:selected {{
                background: {PALETTE.accent};
                color: white;
            }}
            QTreeWidget::branch {{
                background: transparent;
            }}
        """)
        layout.addWidget(self._tree)

    def _populate(self) -> None:
        categories: dict = {}
        for spec in NODE_REGISTRY.values():
            cat = spec.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(spec)

        cat_order = ["Source", "Transform", "Aggregate", "Join", "Sort", "Chart", "Output"]
        for cat_name in cat_order:
            if cat_name not in categories:
                continue
            cat_item = QTreeWidgetItem(self._tree, [cat_name])
            cat_item.setExpanded(True)
            cat_item.setForeground(0, QColor(PALETTE.text_secondary))
            f = cat_item.font(0)
            f.setBold(True)
            cat_item.setFont(0, f)
            for spec in sorted(categories[cat_name], key=lambda s: s.display_name):
                item = QTreeWidgetItem(cat_item, [spec.display_name])
                item.setToolTip(0, f"{spec.display_name}: {spec.description}")
                item.setForeground(0, QColor(PALETTE.text_primary))
                item.setData(0, Qt.ItemDataRole.UserRole, spec.node_type)
                item.setSizeHint(0, QSize(0, 28))

    def _filter_nodes(self, query: str) -> None:
        q = query.lower().strip()
        for i in range(self._tree.topLevelItemCount()):
            cat_item = self._tree.topLevelItem(i)
            if not cat_item:
                continue
            visible = False
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                if not child:
                    continue
                node_type = child.data(0, Qt.ItemDataRole.UserRole) or ""
                text = (child.text(0) + " " + str(node_type)).lower()
                match = not q or q in text
                child.setHidden(not match)
                if match:
                    visible = True
            cat_item.setHidden(not visible)
            if visible and q:
                cat_item.setExpanded(True)
        # Fade the tree in after filter change
        opacity_pop(self._tree, from_=0.72, to=1.0, duration_ms=120)

    def _on_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        node_type = item.data(0, Qt.ItemDataRole.UserRole)
        if node_type:
            self.node_double_clicked.emit(node_type)
