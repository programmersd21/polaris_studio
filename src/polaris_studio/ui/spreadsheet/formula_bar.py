from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget


class FormulaBar(QWidget):
    expression_committed = Signal(str, str)
    nlp_query_submitted = Signal(str)
    cell_navigated = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(36)
        self._nlp_mode = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet("""
            FormulaBar {
                background-color: #ffffff;
                border-bottom: 1px solid #d4d4d4;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        self._cell_ref = QLineEdit()
        self._cell_ref.setFixedWidth(80)
        self._cell_ref.setPlaceholderText("A1")
        self._cell_ref.setToolTip("Cell reference (type to navigate)")
        self._cell_ref.returnPressed.connect(self._navigate_to_cell)
        self._cell_ref.setStyleSheet("""
            QLineEdit {
                font-family: "Inter";
                font-size: 12px;
                border: 1px solid #d5dce8;
                border-radius: 4px;
                padding: 4px 8px;
                background: #ffffff;
                color: #172033;
            }
            QLineEdit:focus { border-color: #245bdb; }
        """)
        layout.addWidget(self._cell_ref)

        fx_label = QLabel("fx")
        fx_label.setFixedWidth(26)
        fx_label.setFixedHeight(22)
        fx_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fx_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: "Inter";
                font-weight: 700;
                font-size: 11px;
                background-color: #5b4bd6;
                border-radius: 4px;
            }
        """)
        layout.addWidget(fx_label)

        self._expression = QLineEdit()
        self._expression.setPlaceholderText("Enter expression or type Alt+Enter for NLP mode")
        self._expression.setToolTip("Expression editor. Press Alt+Enter for natural language mode.")
        self._expression.returnPressed.connect(self._commit_expression)
        self._expression.setStyleSheet("""
            QLineEdit {
                font-family: "Inter";
                font-size: 12px;
                border: 1px solid #d5dce8;
                border-radius: 4px;
                padding: 4px 8px;
                background: #ffffff;
                color: #172033;
            }
            QLineEdit:focus { border-color: #245bdb; }
        """)
        layout.addWidget(self._expression, 1)

        self._nlp_button = QPushButton("AI")
        self._nlp_button.setFixedWidth(36)
        self._nlp_button.setToolTip("Natural language mode (Alt+Enter)")
        self._nlp_button.setStyleSheet("""
            QPushButton {
                background-color: #5b4bd6;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-family: "Inter";
                font-weight: 600;
                font-size: 11px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #7c6af7;
            }
        """)
        self._nlp_button.clicked.connect(self._switch_to_nlp)
        layout.addWidget(self._nlp_button)

        nlp_shortcut = QShortcut(QKeySequence("Alt+Return"), self)
        nlp_shortcut.activated.connect(self._switch_to_nlp)
        nlp_shortcut2 = QShortcut(QKeySequence("Alt+Enter"), self)
        nlp_shortcut2.activated.connect(self._switch_to_nlp)

    def _navigate_to_cell(self) -> None:
        ref = self._cell_ref.text().strip().upper()
        if ref:
            self.cell_navigated.emit(ref)

    def _commit_expression(self) -> None:
        expr = self._expression.text().strip()
        if expr:
            if self._nlp_mode:
                self.nlp_query_submitted.emit(expr)
                self._nlp_mode = False
                self._nlp_button.setText("AI")
                self._expression.setPlaceholderText("Enter expression...")
            else:
                col_name = self._cell_ref.text().strip()
                if col_name:
                    self.expression_committed.emit(col_name, expr)

    def _switch_to_nlp(self) -> None:
        self._nlp_mode = not getattr(self, "_nlp_mode", False)
        if self._nlp_mode:
            self._nlp_button.setText("X")
            self._expression.setPlaceholderText("Describe what you want in plain English...")
            self._expression.setStyleSheet("""
                QLineEdit {
                    font-family: "Inter";
                    font-size: 12px;
                    border: 1px solid #5b4bd6;
                    border-radius: 6px;
                    padding: 4px 8px;
                    background: #ffffff;
                    color: #172033;
                }
            """)
        else:
            self._nlp_button.setText("AI")
            self._expression.setPlaceholderText("Enter expression...")
            self._expression.setStyleSheet("""
                QLineEdit {
                    font-family: "Inter";
                    font-size: 12px;
                    border: 1px solid #d5dce8;
                    border-radius: 4px;
                    padding: 4px 8px;
                    background: #ffffff;
                    color: #172033;
                }
            """)

    def set_cell_reference(self, ref: str) -> None:
        self._cell_ref.setText(ref)

    def set_expression(self, expr: str) -> None:
        self._expression.setText(expr)
