from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.core.formatter import CondFmtType, ConditionalFmtRule
from polaris_studio.ui.dialogs.base_dialog import AnimatedDialog


class ConditionalFmtEditorDialog(AnimatedDialog):
    rule_created = Signal(object)
    rule_edited = Signal(object)
    rule_deleted = Signal(str)

    def __init__(
        self,
        columns: List[str],
        existing_rules: Optional[List[ConditionalFmtRule]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Conditional Formatting")
        self.setMinimumSize(500, 400)
        self.setStyleSheet("""
            QLabel { font-size: 12px; }
        """)

        self._columns = columns
        self._existing_rules = existing_rules or []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("Conditional Formatting Rules")
        header.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(header)

        add_btn = QPushButton("+ Add Rule")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self._add_rule)
        layout.addWidget(add_btn)

        self._rule_list = QListWidget()
        self._rule_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: 1px solid #313244;
                border-radius: 6px;
                color: #cdd6f4;
                font-size: 12px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #2a2a3e;
            }
            QListWidget::item:selected { background: #2a2a3e; }
        """)
        layout.addWidget(self._rule_list, 1)

        for rule in self._existing_rules:
            self._add_rule_item(rule)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self._current_rule_id = 0

    def _add_rule(self) -> None:
        dialog = RuleEditDialog(self._columns, self)
        if dialog.exec() == AnimatedDialog.DialogCode.Accepted:
            rule = dialog.get_rule()
            self.rule_created.emit(rule)
            self._add_rule_item(rule)

    def _add_rule_item(self, rule: ConditionalFmtRule) -> None:
        text = f"[{rule.fmt_type.value}] {rule.column_name}"
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, rule.rule_id)
        self._rule_list.addItem(item)


class RuleEditDialog(AnimatedDialog):
    def __init__(self, columns: List[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Rule")
        self.setMinimumWidth(350)
        self.setStyleSheet("""
            QDialog {
                border-radius: 12px;
            }
        """)

        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        self._column_combo = QComboBox()
        self._column_combo.addItems(columns)
        self._column_combo.setStyleSheet("border-radius: 4px; padding: 6px;")
        layout.addRow("Column:", self._column_combo)

        self._type_combo = QComboBox()
        for ft in CondFmtType:
            self._type_combo.addItem(ft.value)
        self._type_combo.currentTextChanged.connect(self._on_type_change)
        self._type_combo.setStyleSheet(self._column_combo.styleSheet())
        layout.addRow("Type:", self._type_combo)

        self._value_input = QLineEdit()
        self._value_input.setPlaceholderText("Threshold value")
        self._value_input.setStyleSheet("border-radius: 4px; padding: 6px;")
        layout.addRow("Value:", self._value_input)

        self._min_color_btn = QPushButton()
        self._min_color_btn.setFixedSize(32, 24)
        self._min_color_btn.setStyleSheet(
            "background: #f5f5f5; border: 1px solid #d4d4d4; border-radius: 4px;"
        )
        self._min_color_btn.clicked.connect(lambda: self._pick_color(self._min_color_btn))
        layout.addRow("Color:", self._min_color_btn)

        self._max_color_btn = QPushButton()
        self._max_color_btn.setFixedSize(32, 24)
        self._max_color_btn.setStyleSheet(
            "background: #5b4bd6; border: 1px solid #d4d4d4; border-radius: 4px;"
        )
        self._max_color_btn.clicked.connect(lambda: self._pick_color(self._max_color_btn))
        self._max_color_btn.setVisible(False)
        layout.addRow("Max Color:", self._max_color_btn)

        self._priority_spin = QSpinBox()
        self._priority_spin.setRange(0, 100)
        self._priority_spin.setValue(50)
        self._priority_spin.setStyleSheet("border-radius: 4px; padding: 4px;")
        layout.addRow("Priority:", self._priority_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_type_change(self, fmt_type: str) -> None:
        is_scale = "color_scale" in fmt_type
        self._max_color_btn.setVisible(is_scale)

    def _pick_color(self, btn: QPushButton) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            btn.setStyleSheet(
                f"background: {color.name()}; border: 1px solid #d4d4d4; border-radius: 4px;"
            )

    def get_rule(self) -> ConditionalFmtRule:
        import uuid

        fmt_type = self._type_combo.currentText()
        ft_map = {ft.value: ft for ft in CondFmtType}
        params = {}
        if "color_scale" in fmt_type:
            params["min_color"] = self._min_color_btn.palette().button().color().name()
            params["max_color"] = self._max_color_btn.palette().button().color().name()
        else:
            params["color"] = self._min_color_btn.palette().button().color().name()
            params["value"] = self._value_input.text()

        return ConditionalFmtRule(
            rule_id=str(uuid.uuid4())[:8],
            column_name=self._column_combo.currentText(),
            fmt_type=ft_map.get(fmt_type, CondFmtType.THRESHOLD_GT),
            params=params,
            priority=self._priority_spin.value(),
        )
