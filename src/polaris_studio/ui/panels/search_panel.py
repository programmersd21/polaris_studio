from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.ui.theme import PALETTE, RADII


class SearchPanel(QWidget):
    search_requested = Signal(str, str, str)
    replace_requested = Signal(str, str, str, str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        tab_layout = QHBoxLayout()
        self._search_btn = QPushButton("Search")
        self._search_btn.setObjectName("primaryButton")
        self._search_btn.setFixedWidth(80)
        self._search_btn.clicked.connect(lambda: self._switch_mode("search"))
        tab_layout.addWidget(self._search_btn)

        self._replace_btn = QPushButton("Replace")
        self._replace_btn.setFixedWidth(80)
        self._replace_btn.clicked.connect(lambda: self._switch_mode("replace"))
        tab_layout.addWidget(self._replace_btn)

        tab_layout.addStretch()
        layout.addLayout(tab_layout)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search...")
        self._search_input.textChanged.connect(self._on_search)
        self._search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self._search_input)

        self._replace_layout = QHBoxLayout()
        self._replace_input = QLineEdit()
        self._replace_input.setPlaceholderText("Replace with...")
        self._replace_layout.addWidget(self._replace_input, 1)

        self._replace_all_btn = QPushButton("Replace All")
        self._replace_all_btn.clicked.connect(self._on_replace_all)
        self._replace_layout.addWidget(self._replace_all_btn)

        self._replace_layout_widget = QWidget()
        self._replace_layout_widget.setLayout(self._replace_layout)
        self._replace_layout_widget.setVisible(False)
        layout.addWidget(self._replace_layout_widget)

        options_layout = QHBoxLayout()
        self._case_sensitive = QCheckBox("Case")
        options_layout.addWidget(self._case_sensitive)

        self._whole_word = QCheckBox("Whole word")
        options_layout.addWidget(self._whole_word)

        options_layout.addStretch()
        layout.addLayout(options_layout)

        self._scope = QComboBox()
        self._scope.addItems(["Current Column", "All Columns", "Selected Range"])
        layout.addWidget(self._scope)

        self._results_label = QLabel("0 results")
        self._results_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._results_label)

        self._results_list = QListWidget()
        self._results_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                color: {PALETTE.text_primary};
                font-family: 'Inter';
                font-size: 12px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {PALETTE.border};
                border-radius: {RADII.sm}px;
            }}
            QListWidget::item:selected {{ background: {PALETTE.accent_dim}; color: {PALETTE.text_primary}; }}
        """)
        layout.addWidget(self._results_list, 1)

        self._mode = "search"

    def _switch_mode(self, mode: str) -> None:
        self._mode = mode
        self._replace_layout_widget.setVisible(mode == "replace")
        if mode == "search":
            self._search_btn.setObjectName("primaryButton")
            self._replace_btn.setStyleSheet("")
        else:
            self._replace_btn.setObjectName("primaryButton")
            self._search_btn.setStyleSheet("")

    def _on_search(self) -> None:
        query = self._search_input.text().strip()
        if query:
            self.search_requested.emit(query, "", self._scope.currentText())

    def _on_replace_all(self) -> None:
        find = self._search_input.text().strip()
        replace = self._replace_input.text().strip()
        if find:
            self.replace_requested.emit(find, replace, "", self._scope.currentText())

    def set_results(self, results: List[Dict[str, Any]]) -> None:
        self._results_list.clear()
        self._results_label.setText(f"{len(results)} results")
        for r in results:
            row = r.get("row", 0)
            col = r.get("col", 0)
            preview = r.get("preview", "")
            item = QListWidgetItem(f"R{row} C{col}: {preview[:60]}")
            self._results_list.addItem(item)
