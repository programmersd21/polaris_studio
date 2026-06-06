from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from PySide6.QtCore import QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsOpacityEffect,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.ui.motion import BASE, FAST, _keep, accel_decel, decel, opacity_pop
from polaris_studio.ui.theme import PALETTE, RADII, font_inter


@dataclass
class Command:
    id: str
    label: str
    shortcut: str = ""
    category: str = "General"
    action: Optional[Callable[[], None]] = None
    keywords: List[str] = field(default_factory=list)


class CommandPalette(QDialog):
    command_selected = Signal(Command)

    def __init__(self, commands: List[Command], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._all_commands = commands
        self.setWindowTitle("Command Palette")
        self.setModal(False)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(self._style())
        self.setMinimumWidth(500)
        self.setMaximumWidth(600)
        self.setMinimumHeight(280)
        self.setMaximumHeight(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._search = _PaletteSearch()
        self._search.textChanged.connect(self._filter)
        self._search.returnPressed.connect(self._activate_selected)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.itemClicked.connect(self._activate)
        self._list.setFont(font_inter(12))
        layout.addWidget(self._list)

        self._search.setFocus()
        self._filter("")

    def _style(self) -> str:
        return f"""
        QDialog {{
            background: {PALETTE.bg_panel};
            color: {PALETTE.text_primary};
            border: 1px solid {PALETTE.border};
            border-radius: {RADII.md}px;
        }}
        QListWidget {{
            background-color: transparent;
            color: {PALETTE.text_primary};
            border: none;
            font-size: 12px;
            outline: none;
        }}
        QListWidget::item {{
            padding: 10px 14px;
            border-radius: {RADII.sm}px;
        }}
        QListWidget::item:selected {{
            background: {PALETTE.accent};
            color: white;
        }}
        QListWidget::item:hover:!selected {{
            background: {PALETTE.accent_dim};
        }}
        """

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._spring_open()

    def _spring_open(self) -> None:
        """Scale + opacity spring-in when the palette opens."""
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        op = QPropertyAnimation(effect, b"opacity", self)
        op.setStartValue(0.0)
        op.setEndValue(1.0)
        op.setDuration(BASE)
        op.setEasingCurve(decel())
        _keep(self, op)
        op.start()

    def _filter(self, query: str) -> None:
        self._list.clear()
        q = query.lower().strip()
        for cmd in self._all_commands:
            if not q:
                self._add_item(cmd)
                continue
            if q in cmd.label.lower():
                self._add_item(cmd)
                continue
            if cmd.category and q in cmd.category.lower():
                self._add_item(cmd)
                continue
            for kw in cmd.keywords:
                if q in kw.lower():
                    self._add_item(cmd)
                    break
        # Subtle opacity flash on list after each keystroke
        opacity_pop(self._list, from_=0.7, to=1.0, duration_ms=100)

    def _add_item(self, cmd: Command) -> None:
        display = cmd.label
        if cmd.shortcut:
            display += f"\t{cmd.shortcut}"
        if cmd.category:
            display += f"  [{cmd.category}]"
        item = QListWidgetItem(display)
        item.setData(Qt.ItemDataRole.UserRole, cmd)
        self._list.addItem(item)

    def _activate_selected(self) -> None:
        items = self._list.selectedItems()
        if items:
            self._activate(items[0])
        elif self._list.count() > 0:
            self._activate(self._list.item(0))

    def _activate(self, item: QListWidgetItem) -> None:
        cmd: Command = item.data(Qt.ItemDataRole.UserRole)
        if cmd.action:
            cmd.action()
        self.command_selected.emit(cmd)
        self._dismiss_animated()

    def _dismiss_animated(self) -> None:
        effect = self.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setDuration(FAST)
        anim.setEasingCurve(accel_decel())
        anim.finished.connect(self.hide)
        _keep(self, anim)
        anim.start()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._dismiss_animated()
        elif event.key() == Qt.Key.Key_Down:
            idx = self._list.currentRow()
            self._list.setCurrentRow(min(idx + 1, self._list.count() - 1))
        elif event.key() == Qt.Key.Key_Up:
            idx = self._list.currentRow()
            self._list.setCurrentRow(max(idx - 1, 0))
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event) -> None:
        self._dismiss_animated()
        super().focusOutEvent(event)

    @staticmethod
    def install_shortcut(parent: QWidget, commands: List[Command]) -> "CommandPalette":
        palette = CommandPalette(commands, parent)

        def show_palette() -> None:
            rect = parent.geometry()
            palette.move(rect.center().x() - 250, rect.center().y() - 200)
            palette._search.clear()
            palette._filter("")
            palette.show()
            palette.raise_()
            palette._search.setFocus()
            palette.activateWindow()

        shortcut = QShortcut(QKeySequence("Ctrl+P"), parent)
        shortcut.activated.connect(show_palette)
        return palette


class _PaletteSearch(QLineEdit):
    _STYLE = f"""
        QLineEdit {{
            background: {PALETTE.bg_canvas};
            color: {PALETTE.text_primary};
            border: 1.5px solid {PALETTE.accent};
            border-radius: {RADII.sm}px;
            padding: 10px 14px;
            font-size: 13px;
            selection-background-color: {PALETTE.accent};
            font-family: 'Inter';
        }}
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("Type a command…")
        self.setFont(font_inter(13))
        self.setStyleSheet(self._STYLE)
        self.textChanged.connect(self._keystroke_pop)

    def _keystroke_pop(self, _: str) -> None:
        opacity_pop(self, from_=0.82, to=1.0, duration_ms=55)
