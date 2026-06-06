from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.ui.dialogs.base_dialog import AnimatedDialog


class PivotBuilderDialog(AnimatedDialog):
    applied = Signal(dict)

    def __init__(self, columns: List[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pivot Table Builder")
        self.setMinimumSize(600, 450)
        self.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: 600;
            }
        """)

        self._columns = columns
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("Pivot Table Builder")
        header.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(header)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(16)

        left = self._create_field_list("Available Fields", self._columns)
        self._available_list = left
        main_layout.addWidget(left)

        mid_layout = QVBoxLayout()
        mid_layout.setSpacing(16)

        self._rows_list = self._create_field_list("Rows", [])
        mid_layout.addWidget(self._rows_list)

        self._cols_list = self._create_field_list("Columns", [])
        mid_layout.addWidget(self._cols_list)

        self._values_list = self._create_field_list("Values", [])
        mid_layout.addWidget(self._values_list)

        main_layout.addLayout(mid_layout)

        right_layout = QVBoxLayout()

        right_layout.addWidget(QLabel("Aggregation:"))
        self._agg_combo = QComboBox()
        self._agg_combo.addItems(["sum", "mean", "count", "min", "max", "std"])
        self._agg_combo.setStyleSheet("""
            QComboBox {
                background: #2a2a3e;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 8px;
                color: #cdd6f4;
            }
        """)
        right_layout.addWidget(self._agg_combo)

        right_layout.addStretch()

        main_layout.addLayout(right_layout)

        layout.addLayout(main_layout)

        button_box = QDialogButtonBox()
        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self._preview)
        button_box.addButton(preview_btn, QDialogButtonBox.ButtonRole.ActionRole)

        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("primaryButton")
        apply_btn.clicked.connect(self._apply)
        button_box.addButton(apply_btn, QDialogButtonBox.ButtonRole.AcceptRole)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_box.addButton(cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)

        layout.addWidget(button_box)

    def _create_field_list(self, title: str, items: List[str]) -> QListWidget:
        container = QVBoxLayout()

        label = QLabel(title)
        label.setStyleSheet(
            "color: #a6adc8; font-size: 11px; font-weight: 700; text-transform: uppercase;"
        )
        container.addWidget(label)

        w = QListWidget()
        w.setDragEnabled(True)
        w.setAcceptDrops(True)
        w.setDefaultDropAction(Qt.DropAction.MoveAction)
        w.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)  # type: ignore[attr-defined]
        w.setStyleSheet("""
            QListWidget {
                background: #2a2a3e;
                border: 1px solid #313244;
                border-radius: 6px;
                color: #cdd6f4;
                font-size: 11px;
                outline: none;
                min-height: 80px;
            }
            QListWidget::item {
                padding: 6px 10px;
                border-bottom: 1px solid #313244;
            }
            QListWidget::item:selected { background: #7c6af7; }
        """)
        for item in items:
            w.addItem(item)

        return w

    def _get_config(self) -> Dict[str, Any]:
        rows = [self._rows_list.item(i).text() for i in range(self._rows_list.count())]
        cols = [self._cols_list.item(i).text() for i in range(self._cols_list.count())]
        values = [self._values_list.item(i).text() for i in range(self._values_list.count())]
        return {
            "rows": rows,
            "columns": cols,
            "values": values,
            "aggregation": self._agg_combo.currentText(),
        }

    def _preview(self) -> None:
        config = self._get_config()
        self.applied.emit(config)

    def _apply(self) -> None:
        config = self._get_config()
        self.applied.emit(config)
        self.accept()
