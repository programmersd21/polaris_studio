from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.ui.dialogs.base_dialog import AnimatedDialog


class SettingsDialog(AnimatedDialog):
    settings_applied = Signal(dict)

    def __init__(
        self, current_settings: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(550, 450)

        self._settings = current_settings or {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("Settings")
        header.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { background: transparent; border: none; }
            QTabBar::tab {
                padding: 8px 20px;
                font-size: 12px;
            }
        """)

        style = """
            QLineEdit {
                border-radius: 6px;
                padding: 8px 12px;
            }
            QComboBox, QSpinBox {
                border-radius: 6px;
                padding: 6px 10px;
            }
            QCheckBox, QRadioButton { font-size: 12px; spacing: 8px; }
        """

        tabs.addTab(self._create_ai_tab(style), "AI")
        tabs.addTab(self._create_appearance_tab(style), "Appearance")
        tabs.addTab(self._create_performance_tab(style), "Performance")

        layout.addWidget(tabs, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _create_ai_tab(self, style: str) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        gemini_group = QGroupBox("Google Gemini")
        gl = QFormLayout(gemini_group)

        self._api_key = QLineEdit()
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key.setPlaceholderText("AIza...")
        self._api_key.setText(self._settings.get("gemini_key", ""))
        self._api_key.setStyleSheet(style)
        gl.addRow("API Key:", self._api_key)

        self._model_combo = QComboBox()
        self._model_combo.addItems(
            [
                "gemma-4-31b-it",
                "gemma-4-26b-a4b-it",
                "gemini-3.1-flash-lite",
                "gemini-flash-lite-latest",
            ]
        )
        self._model_combo.setCurrentText(self._settings.get("gemini_model", "gemma-4-31b-it"))
        self._model_combo.setStyleSheet(style)
        gl.addRow("Model:", self._model_combo)

        layout.addWidget(gemini_group)

        automation_group = QGroupBox("Automation")
        al = QVBoxLayout(automation_group)

        self._auto_approve = QCheckBox("Auto-approve and execute validated AI actions")
        self._auto_approve.setChecked(self._settings.get("ai_auto_approve", False))
        self._auto_approve.setToolTip(
            "When enabled, schema-valid AI action batches are applied as soon as they arrive."
        )
        al.addWidget(self._auto_approve)

        self._show_action_json = QCheckBox("Show validated Action JSON on proposed changes")
        self._show_action_json.setChecked(self._settings.get("ai_show_action_json", True))
        self._show_action_json.setToolTip(
            "Adds a collapsible JSON pill to each AI action card for inspection and copying."
        )
        al.addWidget(self._show_action_json)

        layout.addWidget(automation_group)
        layout.addStretch()
        return w

    def _create_appearance_tab(self, style: str) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        theme_group = QGroupBox("Theme")
        tl = QVBoxLayout(theme_group)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark Glass (Default)", "Dark High Contrast", "Light"])
        self._theme_combo.setCurrentText(self._settings.get("theme", "Dark Glass (Default)"))
        self._theme_combo.setStyleSheet(style)
        tl.addWidget(self._theme_combo)

        accent_layout = QHBoxLayout()
        accent_layout.addWidget(QLabel("Accent Color:"))
        self._accent_btn = QPushButton()
        self._accent_btn.setFixedSize(32, 24)
        accent_color = self._settings.get("accent_color", "#5b4bd6")
        self._accent_btn.setStyleSheet(
            f"background: {accent_color}; border: 1px solid #d4d4d4; border-radius: 4px;"
        )
        self._accent_btn.clicked.connect(self._pick_accent)
        accent_layout.addWidget(self._accent_btn)
        accent_layout.addStretch()
        tl.addLayout(accent_layout)

        layout.addWidget(theme_group)

        font_group = QGroupBox("Font")
        fl = QFormLayout(font_group)

        self._font_size = QSpinBox()
        self._font_size.setRange(8, 20)
        self._font_size.setValue(self._settings.get("font_size", 11))
        self._font_size.setStyleSheet(style)
        fl.addRow("Font Size:", self._font_size)

        layout.addWidget(font_group)
        layout.addStretch()
        return w

    def _create_performance_tab(self, style: str) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        perf_group = QGroupBox("Performance")
        pl = QFormLayout(perf_group)

        self._worker_count = QSpinBox()
        self._worker_count.setRange(1, 8)
        self._worker_count.setValue(self._settings.get("worker_count", 2))
        self._worker_count.setStyleSheet(style)
        pl.addRow("Worker Processes:", self._worker_count)

        self._cache_size = QSpinBox()
        self._cache_size.setRange(128, 16384)
        self._cache_size.setValue(self._settings.get("cache_size", 1024))
        self._cache_size.setSuffix(" MB")
        self._cache_size.setStyleSheet(style)
        pl.addRow("Cache Size Limit:", self._cache_size)

        self._auto_profile = QCheckBox("Profile automatically after execution")
        self._auto_profile.setChecked(self._settings.get("auto_profile", True))
        pl.addRow("", self._auto_profile)

        layout.addWidget(perf_group)
        layout.addStretch()
        return w

    def _pick_accent(self) -> None:
        color = QColorDialog.getColor(QColor("#5b4bd6"))
        if color.isValid():
            self._accent_btn.setStyleSheet(
                f"background: {color.name()}; border: 1px solid #d4d4d4; border-radius: 4px;"
            )

    def _save(self) -> None:
        settings = {
            "gemini_key": self._api_key.text(),
            "gemini_model": self._model_combo.currentText(),
            "ai_auto_approve": self._auto_approve.isChecked(),
            "ai_show_action_json": self._show_action_json.isChecked(),
            "theme": self._theme_combo.currentText(),
            "font_size": self._font_size.value(),
            "worker_count": self._worker_count.value(),
            "cache_size": self._cache_size.value(),
            "auto_profile": self._auto_profile.isChecked(),
        }
        self.settings_applied.emit(settings)
        self.accept()
