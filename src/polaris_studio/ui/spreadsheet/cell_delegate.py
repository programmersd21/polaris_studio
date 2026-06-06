from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPalette, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QDateTimeEdit,
    QLineEdit,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

from polaris_studio.ui.spreadsheet.conditional_fmt import ConditionalFormatEngine
from polaris_studio.ui.theme import font_mono


class PolarisDelegate(QStyledItemDelegate):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._fmt_engine: Optional[ConditionalFormatEngine] = None
        self._font = font_mono(11)

    def set_format_engine(self, engine: Optional[ConditionalFormatEngine]) -> None:
        self._fmt_engine = engine

    def createEditor(
        self,
        parent: QWidget,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QWidget:
        dtype = index.data(Qt.ItemDataRole.UserRole) if index.isValid() else ""
        if not dtype:
            return QLineEdit(parent)

        dtype_lower = dtype.lower()
        if "bool" in dtype_lower:
            return QCheckBox(parent)
        elif "date" in dtype_lower or "datetime" in dtype_lower:
            editor = QDateTimeEdit(parent)
            editor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            editor.setCalendarPopup(True)
            return editor
        else:
            line_editor = QLineEdit(parent)
            if "int" in dtype_lower:
                from PySide6.QtGui import QIntValidator

                line_editor.setValidator(QIntValidator(line_editor))
            elif "float" in dtype_lower:
                from PySide6.QtGui import QDoubleValidator

                line_editor.setValidator(QDoubleValidator(line_editor))
            return line_editor

    def setEditorData(self, editor: QWidget, index: QModelIndex | QPersistentModelIndex) -> None:
        value = index.data(Qt.ItemDataRole.EditRole)
        if isinstance(editor, QLineEdit):
            editor.setText(str(value) if value is not None else "")
        elif isinstance(editor, QCheckBox):
            editor.setChecked(bool(value) if value is not None else False)
        elif isinstance(editor, QDateTimeEdit):
            from PySide6.QtCore import QDateTime

            if value:
                editor.setDateTime(QDateTime.fromString(str(value), "yyyy-MM-dd HH:mm:ss"))

    def setModelData(
        self, editor: QWidget, model: Any, index: QModelIndex | QPersistentModelIndex
    ) -> None:
        if isinstance(editor, QLineEdit):
            model.setData(index, editor.text(), Qt.ItemDataRole.EditRole)
        elif isinstance(editor, QCheckBox):
            model.setData(index, editor.isChecked(), Qt.ItemDataRole.EditRole)
        elif isinstance(editor, QDateTimeEdit):
            model.setData(
                index, editor.dateTime().toString("yyyy-MM-dd HH:mm:ss"), Qt.ItemDataRole.EditRole
            )

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        painter.save()

        bg_color = index.data(Qt.ItemDataRole.BackgroundRole) or option.palette.color(
            QPalette.ColorRole.Base
        )
        fg_color = index.data(Qt.ItemDataRole.ForegroundRole) or QColor("#1a1a1a")
        font = index.data(Qt.ItemDataRole.FontRole) or self._font
        alignment = index.data(Qt.ItemDataRole.TextAlignmentRole) or (
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        if self._fmt_engine and index.isValid():
            col_name = index.model().headerData(
                index.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
            )
            fmt_color = self._fmt_engine.get_cell_color(index.row(), col_name)
            if fmt_color:
                bg_color = fmt_color

        painter.fillRect(option.rect, bg_color)

        if option.state & QStyle.StateFlag.State_Selected:
            highlight = QColor("#5b4bd6")
            highlight.setAlpha(120)
            painter.fillRect(option.rect, highlight)

        text = index.data(Qt.ItemDataRole.DisplayRole) if index.isValid() else ""
        if text:
            painter.setFont(font if isinstance(font, QFont) else self._font)
            painter.setPen(fg_color if isinstance(fg_color, QColor) else QColor("#1a1a1a"))
            text_rect = option.rect.adjusted(8, 0, -4, 0)
            painter.drawText(
                text_rect, alignment, self._elide_text(painter, text, text_rect.width())
            )

        if option.state & QStyle.StateFlag.State_HasFocus:
            pen = QPen(QColor("#5b4bd6"), 2)
            painter.setPen(pen)
            painter.drawRect(option.rect)

        painter.restore()

    def _elide_text(self, painter: QPainter, text: str, max_width: int) -> str:
        metrics = painter.fontMetrics()
        if metrics.horizontalAdvance(text) <= max_width:
            return text
        return metrics.elidedText(text, Qt.TextElideMode.ElideRight, max_width)
