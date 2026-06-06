from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QHeaderView, QMenu, QWidget

from polaris_studio.ui.theme import font_inter


class StatsHeaderView(QHeaderView):
    def __init__(self, orientation: Qt.Orientation, parent: Optional[QWidget] = None) -> None:
        super().__init__(orientation, parent)
        self.setHighlightSections(True)
        self.setSectionsClickable(True)
        self.setStretchLastSection(True)

    def paintSection(self, painter: QPainter, rect, logicalIndex: int) -> None:
        painter.save()

        if self.isSectionSelected(logicalIndex):  # type: ignore[attr-defined]
            painter.fillRect(rect, QColor("#e8e8e8"))
        else:
            painter.fillRect(rect, QColor("#f5f5f5"))

        painter.setPen(QPen(QColor("#d4d4d4"), 1))
        painter.drawLine(rect.topRight(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

        text = self.model().headerData(
            logicalIndex, self.orientation(), Qt.ItemDataRole.DisplayRole
        )
        if text:
            font = font_inter(10, QFont.Weight.Medium)
            painter.setFont(font)
            painter.setPen(QColor("#555555"))
            text_rect = rect.adjusted(8, 0, -4, 0)
            painter.drawText(
                text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(text)
            )

        painter.restore()

    def contextMenuEvent(self, event) -> None:
        idx = self.logicalIndexAt(event.pos())
        if idx < 0 or not self.model():
            return

        menu = QMenu(self)

        sort_asc = QAction("Sort Ascending", self)
        sort_asc.triggered.connect(
            lambda: self.sortIndicatorChanged.emit(idx, Qt.SortOrder.AscendingOrder)
        )
        menu.addAction(sort_asc)

        sort_desc = QAction("Sort Descending", self)
        sort_desc.triggered.connect(
            lambda: self.sortIndicatorChanged.emit(idx, Qt.SortOrder.DescendingOrder)
        )
        menu.addAction(sort_desc)

        menu.addSeparator()
        stats = QAction("Column Statistics...", self)
        menu.addAction(stats)

        menu.exec(event.globalPos())
