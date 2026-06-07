from __future__ import annotations

import logging
from functools import partial
from typing import Any, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.core.graph import Node
from polaris_studio.core.node_registry import NODE_REGISTRY, NodeParamSpec, NodeTypeSpec
from polaris_studio.ui.theme import PALETTE, RADII, font_instrument_serif

logger = logging.getLogger(__name__)


class PropertiesPanel(QWidget):
    param_changed = Signal(str, str, Any)
    execute_requested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._node: Optional[Node] = None
        self._spec: Optional[NodeTypeSpec] = None
        self._updating = False

        self.setMinimumWidth(260)
        self.setMaximumWidth(360)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._action_bar = QWidget()
        self._action_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {PALETTE.bg_panel};
                border-bottom: 1px solid {PALETTE.border};
            }}
        """)
        action_layout = QHBoxLayout(self._action_bar)
        action_layout.setContentsMargins(12, 10, 12, 10)
        action_layout.setSpacing(8)

        self._execute_btn = QPushButton("Execute")
        self._execute_btn.setObjectName("primaryButton")
        self._execute_btn.setMinimumHeight(32)
        self._execute_btn.clicked.connect(self._on_execute)
        self._execute_btn.setVisible(False)
        self._execute_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PALETTE.accent};
                color: #ffffff;
                border: none;
                border-radius: {RADII.sm}px;
                padding: 6px 16px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {PALETTE.accent_hover}; }}
            QPushButton:pressed {{ background-color: {PALETTE.edge_selected}; }}
        """)
        action_layout.addWidget(self._execute_btn)

        self._preview_btn = QPushButton("Preview Output")
        self._preview_btn.setMinimumHeight(32)
        self._preview_btn.clicked.connect(self._on_preview)
        self._preview_btn.setVisible(False)
        self._preview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PALETTE.bg_panel};
                color: {PALETTE.text_primary};
                border: 1px solid {PALETTE.border};
                border-radius: {RADII.sm}px;
                padding: 6px 16px;
                font-weight: 500;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {PALETTE.bg_node_alt}; }}
        """)
        action_layout.addWidget(self._preview_btn)

        action_layout.addStretch()
        main_layout.addWidget(self._action_bar)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        main_layout.addWidget(scroll, 1)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(8)

        self._header = QLabel("No node selected")
        header_font = font_instrument_serif(20)
        header_font.setStyleName("Regular")
        self._header.setFont(header_font)
        self._header.setStyleSheet(f"""
            QLabel {{
                color: {PALETTE.text_primary};
                font-size: 20px;
                font-weight: 400;
                padding-bottom: 2px;
                letter-spacing: 0px;
            }}
        """)
        self._layout.addWidget(self._header)

        self._type_label = QLabel("")
        self._type_label.setStyleSheet(
            f"font-size: 11px; color: {PALETTE.text_secondary}; font-family: 'JetBrains Mono', 'Inter';"
        )
        self._layout.addWidget(self._type_label)

        self._desc_label = QLabel("")
        self._desc_label.setWordWrap(True)
        self._desc_label.setStyleSheet(
            f"font-size: 11px; color: {PALETTE.text_secondary}; padding: 4px 0 8px 0;"
        )
        self._layout.addWidget(self._desc_label)

        self._form_layout = QFormLayout()
        self._form_layout.setSpacing(8)
        self._form_layout.setContentsMargins(0, 0, 0, 0)
        self._form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self._layout.addLayout(self._form_layout)

        self._layout.addStretch()

        scroll.setWidget(self._content)

    def show_node(self, node: Optional[Node]) -> None:
        self._node = node
        self._updating = True

        self._clear_form()

        if node is None:
            self._header.setText("No node selected")
            self._type_label.setText("")
            self._desc_label.setText("")
            self._execute_btn.setVisible(False)
            self._preview_btn.setVisible(False)
            self._updating = False
            return

        spec = NODE_REGISTRY.get(node.node_type)
        self._spec = spec

        if spec:
            self._header.setText(spec.display_name)
            self._type_label.setText(f"{node.node_id}  |  {spec.category}")
            self._desc_label.setText(spec.description)
            self._execute_btn.setVisible(True)
            self._preview_btn.setVisible(True)

            for param in spec.params:
                widget = self._create_param_widget(
                    param, node.params.get(param.name, param.default)
                )
                if widget:
                    label = QLabel(param.label)
                    label.setStyleSheet("font-size: 11px;")
                    self._form_layout.addRow(label, widget)

        self._updating = False

    def _clear_form(self) -> None:
        while self._form_layout.count():
            item = self._form_layout.takeAt(0)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()

    def _create_param_widget(self, param: NodeParamSpec, value: Any) -> Optional[QWidget]:
        pt = param.param_type

        if pt == "string":
            inp = QLineEdit()
            inp.setText(str(value) if value is not None else "")
            inp.textChanged.connect(partial(self._on_param_change, param.name))
            return inp

        elif pt == "filepath":
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            inp = QLineEdit()
            inp.setText(str(value) if value is not None else "")
            inp.textChanged.connect(partial(self._on_param_change, param.name))
            btn = QPushButton("...")
            btn.setFixedWidth(32)
            btn.clicked.connect(partial(self._browse_file, inp))
            layout.addWidget(inp, 1)
            layout.addWidget(btn)
            return container

        elif pt == "bool":
            cb = QCheckBox()
            cb.setChecked(bool(value) if value is not None else False)
            cb.toggled.connect(partial(self._on_param_change, param.name))
            return cb

        elif pt == "enum":
            combo = QComboBox()
            if param.options:
                combo.addItems(param.options)
            if value and str(value) in (param.options or []):
                combo.setCurrentText(str(value))
            combo.currentTextChanged.connect(partial(self._on_param_change, param.name))
            return combo

        elif pt == "integer":
            spin = QSpinBox()
            spin.setRange(-999999999, 999999999)
            spin.setValue(int(value) if value is not None else 0)
            spin.valueChanged.connect(partial(self._on_param_change, param.name))
            return spin

        elif pt == "float":
            dspin = QDoubleSpinBox()
            dspin.setRange(-999999999.0, 999999999.0)
            dspin.setValue(float(value) if value is not None else 0.0)
            dspin.valueChanged.connect(partial(self._on_param_change, param.name))
            return dspin

        elif pt == "column_single":
            combo = QComboBox()
            combo.setEditable(True)
            if value:
                combo.setCurrentText(str(value))
            combo.currentTextChanged.connect(partial(self._on_param_change, param.name))
            return combo

        elif pt == "column_multi":
            lst = QListWidget()
            lst.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
            if isinstance(value, list):
                for v in value:
                    item = QListWidgetItem(str(v))
                    item.setSelected(True)
                    lst.addItem(item)
            lst.itemChanged.connect(partial(self._on_multi_column_changed, param.name, lst))
            return lst

        elif pt == "expression":
            inp = QLineEdit()
            inp.setText(str(value) if value is not None else "")
            inp.setPlaceholderText("pl.col('col') > 0")
            font = QFont("JetBrains Mono", 10)
            font.setFamilies(["JetBrains Mono", "Inter"])
            inp.setFont(font)
            inp.textChanged.connect(partial(self._on_param_change, param.name))
            return inp

        # Fallback for unknown param types: create a generic text editor
        logger.warning(
            f"Unknown parameter type '{pt}' for parameter '{param.name}', using text editor"
        )
        inp = QLineEdit()
        inp.setText(str(value) if value is not None else "")
        inp.setPlaceholderText(f"[{pt}] Enter value")
        inp.textChanged.connect(partial(self._on_param_change, param.name))
        return inp

    def _on_multi_column_changed(self, name: str, lst: QListWidget) -> None:
        self._on_param_change(
            name,
            [lst.item(i).text() for i in range(lst.count()) if lst.item(i).isSelected()],
        )

    def _on_param_change(self, key: str, value: Any) -> None:
        if self._updating or self._node is None:
            return
        self.param_changed.emit(self._node.node_id, key, value)

    def _browse_file(self, widget: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if path:
            widget.setText(path)

    def _on_execute(self) -> None:
        if self._node:
            self.execute_requested.emit(self._node.node_id)

    def _on_preview(self) -> None:
        if self._node:
            self.preview_requested.emit(self._node.node_id)

    preview_requested = Signal(str)
