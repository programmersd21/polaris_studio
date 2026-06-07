from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.ui.dialogs.base_dialog import AnimatedDialog
from polaris_studio.ui.theme import PALETTE, RADII, font_instrument_serif, font_inter


class ExprHighlighter(QSyntaxHighlighter):
    def __init__(self, parent: Optional[QTextEdit] = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._rules: list = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#5b4bd6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "pl",
            "col",
            "lit",
            "when",
            "then",
            "otherwise",
            "alias",
            "filter",
            "select",
            "with_columns",
            "group_by",
            "agg",
            "sort",
            "sum",
            "mean",
            "count",
            "min",
            "max",
        ]
        for kw in keywords:
            self._rules.append((rf"\b{kw}\b", keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#2e7d32"))
        self._rules.append((r"'[^']*'", string_format))
        self._rules.append((r'"[^"]*"', string_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b8860b"))
        self._rules.append((r"\b\d+\.?\d*\b", number_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#8b8b8b"))
        self._rules.append((r"#.*$", comment_format))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            import re

            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class ExpressionEditorDialog(AnimatedDialog):
    expression_accepted = Signal(str)

    def __init__(
        self,
        columns: Optional[List[str]] = None,
        initial_expr: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Expression Editor")
        self.setMinimumSize(650, 450)
        self.setStyleSheet("""
            QDialog {
                border-radius: 12px;
            }
        """)

        self._columns = columns or []
        self._setup_ui(initial_expr)

    def _setup_ui(self, initial_expr: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("Expression Editor")
        header.setFont(font_instrument_serif(20))
        header.setStyleSheet(
            f"color: {PALETTE.text_primary}; font-size: 20px; padding-bottom: 4px;"
        )
        layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QFrame()
        left_panel.setStyleSheet("QFrame { background: transparent; border: none; }")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(6)

        fields_label = QLabel("Columns & Operators")
        fields_label.setFont(font_inter(11, QFont.Weight.DemiBold))
        fields_label.setStyleSheet(
            f"color: {PALETTE.text_secondary}; font-family: 'Inter'; letter-spacing: 0.04em;"
        )
        left_layout.addWidget(fields_label)

        list_qss = f"""
            QListWidget {{
                background: {PALETTE.bg_panel};
                color: {PALETTE.text_primary};
                border: 1px solid {PALETTE.border};
                border-radius: {RADII.sm}px;
                font-size: 12px;
                font-family: 'JetBrains Mono', 'Inter';
                outline: none;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-radius: 4px;
            }}
            QListWidget::item:hover {{ background: {PALETTE.bg_node_alt}; }}
            QListWidget::item:selected {{
                background: {PALETTE.accent};
                color: #ffffff;
            }}
        """

        self._column_list = QListWidget()
        for col in self._columns:
            self._column_list.addItem(col)
        self._column_list.itemDoubleClicked.connect(self._insert_column)
        self._column_list.setStyleSheet(list_qss)
        left_layout.addWidget(self._column_list, 1)

        op_label = QLabel("Operators")
        op_label.setFont(font_inter(11, QFont.Weight.DemiBold))
        op_label.setStyleSheet(
            f"color: {PALETTE.text_secondary}; font-family: 'Inter'; letter-spacing: 0.04em; padding-top: 4px;"
        )
        left_layout.addWidget(op_label)

        ops_widget = QListWidget()
        for op in ["+", "-", "*", "/", "==", "!=", ">", "<", ">=", "<=", "&", "|", "~"]:
            ops_widget.addItem(op)
        ops_widget.itemDoubleClicked.connect(self._insert_op)
        ops_widget.setStyleSheet(list_qss)
        left_layout.addWidget(ops_widget)

        func_label = QLabel("Functions")
        func_label.setFont(font_inter(11, QFont.Weight.DemiBold))
        func_label.setStyleSheet(
            f"color: {PALETTE.text_secondary}; font-family: 'Inter'; letter-spacing: 0.04em; padding-top: 4px;"
        )
        left_layout.addWidget(func_label)

        funcs_widget = QListWidget()
        for func in [
            "pl.col('')",
            "pl.lit()",
            ".sum()",
            ".mean()",
            ".count()",
            ".min()",
            ".max()",
            ".std()",
            ".first()",
            ".last()",
            ".alias('')",
            ".cast(pl.Float64)",
            ".is_null()",
            ".is_not_null()",
            ".fill_null()",
            ".str.startsWith()",
            ".str.contains()",
            ".str.to_uppercase()",
            ".str.to_lowercase()",
        ]:
            funcs_widget.addItem(func)
        funcs_widget.itemDoubleClicked.connect(self._insert_func)
        funcs_widget.setStyleSheet(list_qss)
        left_layout.addWidget(funcs_widget)

        splitter.addWidget(left_panel)

        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { background: transparent; border: none; }")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(6)

        expr_label = QLabel("Expression")
        expr_label.setFont(font_inter(11, QFont.Weight.DemiBold))
        expr_label.setStyleSheet(
            f"color: {PALETTE.text_secondary}; font-family: 'Inter'; letter-spacing: 0.04em;"
        )
        right_layout.addWidget(expr_label)

        self._editor = QTextEdit()
        self._editor.setPlainText(initial_expr)
        self._editor.setStyleSheet(f"""
            QTextEdit {{
                background: {PALETTE.bg_panel};
                color: {PALETTE.text_primary};
                border: 1px solid {PALETTE.border};
                border-radius: {RADII.sm}px;
                font-size: 13px;
                font-family: 'JetBrains Mono', 'Inter';
                padding: 12px;
                selection-background-color: {PALETTE.accent};
            }}
            QTextEdit:focus {{ border-color: {PALETTE.accent}; }}
        """)
        self._highlighter = ExprHighlighter(self._editor)

        preview_label = QLabel("Preview (5 rows)")
        preview_label.setFont(font_inter(11, QFont.Weight.DemiBold))
        preview_label.setStyleSheet(
            f"color: {PALETTE.text_secondary}; font-family: 'Inter'; letter-spacing: 0.04em; padding-top: 4px;"
        )
        right_layout.addWidget(self._editor, 3)
        right_layout.addWidget(preview_label)

        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setStyleSheet(f"""
            QTextEdit {{
                background: {PALETTE.bg_canvas};
                color: {PALETTE.text_secondary};
                border: 1px solid {PALETTE.border};
                border-radius: {RADII.sm}px;
                font-size: 11px;
                font-family: 'JetBrains Mono', 'Inter';
                padding: 10px;
            }}
        """)
        right_layout.addWidget(self._preview, 2)

        splitter.addWidget(right_panel)
        splitter.setSizes([240, 480])

        layout.addWidget(splitter, 1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        test_btn = QPushButton("Test Expression")
        test_btn.setFont(font_inter(12, QFont.Weight.Medium))
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PALETTE.bg_panel};
                color: {PALETTE.text_primary};
                border: 1px solid {PALETTE.border};
                border-radius: {RADII.sm}px;
                padding: 8px 16px;
                font-family: 'Inter';
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {PALETTE.bg_node_alt}; border-color: {PALETTE.border_strong}; }}
        """)
        test_btn.clicked.connect(self._test_expr)
        btn_layout.addWidget(test_btn)

        btn_layout.addStretch()

        ok_btn = QPushButton("Apply")
        ok_btn.setObjectName("primaryButton")
        ok_btn.setFont(font_inter(12, QFont.Weight.DemiBold))
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton#primaryButton {{
                background: {PALETTE.accent};
                color: #ffffff;
                border: none;
                border-radius: {RADII.sm}px;
                padding: 8px 20px;
                font-family: 'Inter';
                font-weight: 600;
            }}
            QPushButton#primaryButton:hover {{ background: {PALETTE.accent_hover}; }}
        """)
        ok_btn.clicked.connect(self._accept)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(font_inter(12, QFont.Weight.Medium))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PALETTE.bg_panel};
                color: {PALETTE.text_primary};
                border: 1px solid {PALETTE.border};
                border-radius: {RADII.sm}px;
                padding: 8px 16px;
                font-family: 'Inter';
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {PALETTE.bg_node_alt}; border-color: {PALETTE.border_strong}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _insert_column(self, item: QListWidgetItem) -> None:
        self._insert_text(f"pl.col('{item.text()}')")

    def _insert_op(self, item: QListWidgetItem) -> None:
        self._insert_text(item.text())

    def _insert_func(self, item: QListWidgetItem) -> None:
        self._insert_text(item.text())

    def _insert_text(self, text: str) -> None:
        cursor = self._editor.textCursor()
        cursor.insertText(text)
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()

    def _test_expr(self) -> None:
        expr = self._editor.toPlainText().strip()
        if expr:
            self._preview.setPlainText("Expression accepted (preview requires data context)")

    def _accept(self) -> None:
        expr = self._editor.toPlainText().strip()
        if expr:
            self.expression_accepted.emit(expr)
            self.accept()

    def get_expression(self) -> str:
        return self._editor.toPlainText().strip()
