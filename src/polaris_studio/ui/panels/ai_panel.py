"""AI chat panel - ultra-cinematic interactions.

Micro-interactions:
- Send button: press squeeze → accent morph → "…" loading text → spring back
- Input: per-keystroke opacity pop (typing feedback)
- Bubble entrance: spring slide-up + opacity fade
- Token cursor: blinking ▋ at end of streaming assistant bubble
- Scroll: smooth auto-scroll on new content
- Action card: spring entrance with slight overshoot
"""

from __future__ import annotations

import json
from typing import Optional

from PySide6.QtCore import (
    QPropertyAnimation,
    QSequentialAnimationGroup,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.agent.command_pipeline import ExecutionReport
from polaris_studio.agent.schemas import AppCommandBatch, PipelineMutationBatch
from polaris_studio.ui.motion import (
    FAST,
    fade_slide_in,
    spring,
    accel_decel,
    _keep,
)
from polaris_studio.ui.theme import (
    PALETTE,
    RADII,
    font_instrument_serif,
    font_inter,
    font_mono,
    font_outfit,
)


# ── Animated send button ──────────────────────────────────────────────────────


class _SendButton(QPushButton):
    """Send button with press-squeeze, loading-morph, and spring-back."""

    _BASE_SS = f"""
        QPushButton {{
            background-color: {PALETTE.accent};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-family: 'Inter';
            font-weight: 600;
            font-size: 11px;
        }}
        QPushButton:disabled {{
            background-color: {PALETTE.border};
            color: {PALETTE.text_muted};
        }}
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Send", parent)
        self.setObjectName("primaryButton")
        self.setFont(font_inter(11, QFont.Weight.DemiBold))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(80)
        self.setStyleSheet(self._BASE_SS)
        self._loading = False

    def set_loading(self, loading: bool) -> None:
        self._loading = loading
        if loading:
            self.setText("…")
            self.setEnabled(False)
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {PALETTE.accent_hover};
                    color: rgba(255,255,255,0.7);
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-family: 'Inter';
                    font-weight: 600;
                    font-size: 15px;
                    letter-spacing: 2px;
                }}
            """)
            self._animate_opacity_pulse()
        else:
            self.setText("Send")
            self.setEnabled(True)
            self.setStyleSheet(self._BASE_SS)

    def _animate_opacity_pulse(self) -> None:
        if not self._loading:
            return
        effect = self.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)
        seq = QSequentialAnimationGroup(self)
        for start, end in [(1.0, 0.4), (0.4, 1.0)]:
            a = QPropertyAnimation(effect, b"opacity", seq)
            a.setStartValue(start)
            a.setEndValue(end)
            a.setDuration(420)
            a.setEasingCurve(accel_decel())
            seq.addAnimation(a)
        seq.setLoopCount(-1)
        _keep(self, seq)
        seq.start()

    def mousePressEvent(self, event) -> None:
        if not self._loading:
            self._squeeze()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if not self._loading:
            self._spring_back()
        super().mouseReleaseEvent(event)

    def _squeeze(self) -> None:
        effect = self.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setStartValue(1.0)
        anim.setEndValue(0.75)
        anim.setDuration(60)
        anim.setEasingCurve(accel_decel())
        _keep(self, anim)
        anim.start()

    def _spring_back(self) -> None:
        effect = self.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setStartValue(0.75)
        anim.setEndValue(1.0)
        anim.setDuration(FAST)
        anim.setEasingCurve(spring())
        _keep(self, anim)
        anim.start()


# ── Animated input ────────────────────────────────────────────────────────────


class _AnimatedInput(QLineEdit):
    """Input field with focus glow. No opacity effect - that would disable
    ClearType/subpixel antialiasing on the QLineEdit and make the dark text
    read as washed-out white on a white background."""

    _IDLE_SS = f"""
        QLineEdit {{
            background-color: {PALETTE.bg_node};
            color: {PALETTE.text_primary};
            border: 1px solid {PALETTE.border};
            border-radius: 8px;
            padding: 10px 14px;
            font-family: 'Inter';
            font-size: 12px;
            selection-background-color: {PALETTE.accent};
            selection-color: #ffffff;
        }}
    """
    _FOCUS_SS = f"""
        QLineEdit {{
            background-color: {PALETTE.bg_node};
            color: {PALETTE.text_primary};
            border: 1.5px solid {PALETTE.accent};
            border-radius: 8px;
            padding: 10px 14px;
            font-family: 'Inter';
            font-size: 12px;
            selection-background-color: {PALETTE.accent};
            selection-color: #ffffff;
        }}
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("Ask anything about your data…")
        self.setFont(font_inter(12))
        self.setStyleSheet(self._IDLE_SS)

    def focusInEvent(self, event) -> None:
        self.setStyleSheet(self._FOCUS_SS)
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:
        self.setStyleSheet(self._IDLE_SS)
        super().focusOutEvent(event)


# ── Message bubble with spring entrance and cursor blink ──────────────────────


class MessageBubble(QFrame):
    """Single chat message bubble with spring entrance."""

    def __init__(self, role: str, content: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._role = role
        self._streaming = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(6)

        role_label = QLabel("You" if role == "user" else "Polaris AI")
        role_label.setFont(font_outfit(10, QFont.Weight.Bold))
        role_label.setStyleSheet(f"color: {'#8b96a8' if role == 'user' else PALETTE.accent_hover};")
        layout.addWidget(role_label)

        self._content = QLabel(content)
        self._content.setWordWrap(True)
        self._content.setTextFormat(Qt.TextFormat.RichText)
        self._content.setFont(font_inter(12))
        self._content.setStyleSheet(f"color: {PALETTE.text_primary}; line-height: 1.6;")
        layout.addWidget(self._content)

        self._cursor_timer: Optional[QTimer] = None
        self._cursor_visible = True
        self._text_without_cursor = content

        if role == "user":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {PALETTE.bg_node};
                    border: 1px solid {PALETTE.border};
                    border-radius: {RADII.md}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {PALETTE.bg_node_alt};
                    border: 1px solid {PALETTE.border};
                    border-radius: {RADII.md}px;
                }}
            """)

    def append_text(self, text: str) -> None:
        if self._text_without_cursor in ("…", "..."):
            self._text_without_cursor = text
        else:
            self._text_without_cursor += text
        self._update_display()

    def start_cursor(self) -> None:
        """Start blinking cursor for token stream."""
        self._streaming = True
        if self._cursor_timer is None:
            self._cursor_timer = QTimer(self)
            self._cursor_timer.timeout.connect(self._blink_cursor)
        self._cursor_timer.start(530)

    def stop_cursor(self) -> None:
        """Stop cursor, show final text cleanly."""
        self._streaming = False
        if self._cursor_timer:
            self._cursor_timer.stop()
        self._content.setText(self._text_without_cursor)

    def _blink_cursor(self) -> None:
        self._cursor_visible = not self._cursor_visible
        self._update_display()

    def _update_display(self) -> None:
        cursor = (
            '<span style="color:#245bdb;font-size:10px;"> ●</span>'
            if (self._streaming and self._cursor_visible)
            else ""
        )
        self._content.setText(self._text_without_cursor + cursor)


# ── Action preview card ───────────────────────────────────────────────────────


class ActionPreviewCard(QFrame):
    apply_clicked = Signal(object)
    reject_clicked = Signal(object)

    def __init__(
        self,
        batch: AppCommandBatch | PipelineMutationBatch,
        auto_approved: bool = False,
        show_json: bool = True,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._batch = batch
        self._json_text = self._format_batch_json(batch)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        header = QLabel("Proposed changes")
        header.setFont(font_outfit(10, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {PALETTE.accent_hover}; letter-spacing: 0.08em;")
        header_row.addWidget(header)
        if auto_approved:
            auto_label = QLabel("Auto-approved")
            auto_label.setFont(font_outfit(9, QFont.Weight.Bold))
            auto_label.setStyleSheet(
                f"color: {PALETTE.success}; background-color: {PALETTE.accent_dim}; padding: 2px 8px; border-radius: 8px;"
            )
            header_row.addWidget(auto_label)
        header_row.addStretch()
        layout.addLayout(header_row)

        if batch.description:
            desc = QLabel(batch.description)
            desc.setWordWrap(True)
            desc.setFont(font_inter(12, QFont.Weight.DemiBold))
            desc.setStyleSheet(f"color: {PALETTE.text_primary};")
            layout.addWidget(desc)

        summary = self._summarize(batch)
        if summary:
            detail = QLabel(summary)
            detail.setWordWrap(True)
            detail.setFont(font_mono(10))
            detail.setStyleSheet(f"color: {PALETTE.text_secondary};")
            layout.addWidget(detail)

        self._json_view: Optional[QPlainTextEdit] = None
        self._json_toggle: Optional[QToolButton] = None
        if show_json:
            json_row = QHBoxLayout()
            json_row.setSpacing(6)
            self._json_toggle = QToolButton()
            self._json_toggle.setText("Action JSON")
            self._json_toggle.setCheckable(True)
            self._json_toggle.setChecked(False)
            self._json_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
            self._json_toggle.toggled.connect(self._toggle_json)
            json_row.addWidget(self._json_toggle)
            copy_btn = QPushButton("Copy")
            copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            copy_btn.clicked.connect(self._copy_json)
            json_row.addWidget(copy_btn)
            json_row.addStretch()
            layout.addLayout(json_row)

            self._json_view = QPlainTextEdit()
            self._json_view.setPlainText(self._json_text)
            self._json_view.setReadOnly(True)
            self._json_view.setVisible(False)
            self._json_view.setMinimumHeight(160)
            self._json_view.setFont(font_mono(10))
            self._json_view.setStyleSheet(f"""
                QPlainTextEdit {{
                    background-color: {PALETTE.bg_canvas};
                    color: {PALETTE.text_primary};
                    border: 1px solid {PALETTE.border};
                    border-radius: 6px;
                    padding: 8px;
                }}
            """)
            layout.addWidget(self._json_view)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        apply_btn = _CardButton("Apply", accent=True)
        apply_btn.clicked.connect(lambda: self.apply_clicked.emit(self._batch))
        apply_btn.setEnabled(not auto_approved)
        if auto_approved:
            apply_btn.setText("Applied automatically")
        btn_layout.addWidget(apply_btn)

        skip_btn = _CardButton("Skip")
        skip_btn.clicked.connect(lambda: self.reject_clicked.emit(self._batch))
        skip_btn.setEnabled(not auto_approved)
        btn_layout.addWidget(skip_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setObjectName("actionCard")
        self.setStyleSheet(f"""
            QFrame#actionCard {{
                background-color: {PALETTE.bg_node};
                border: 1px solid {PALETTE.accent_dim};
                border-radius: {RADII.md}px;
            }}
            QToolButton {{
                background-color: {PALETTE.bg_node_alt};
                color: {PALETTE.text_primary};
                border: 1px solid {PALETTE.border};
                border-radius: 999px;
                padding: 4px 12px;
                font-family: 'Inter';
                font-size: 11px;
                font-weight: 600;
            }}
            QToolButton:checked {{
                border-color: {PALETTE.accent};
                color: {PALETTE.accent_hover};
            }}
        """)

    def _toggle_json(self, checked: bool) -> None:
        if self._json_view is None:
            return
        self._json_view.setVisible(checked)
        if self._json_toggle:
            self._json_toggle.setText("Action JSON  −" if checked else "Action JSON")
        # Force layout to reflow so the card grows/shrinks
        self.updateGeometry()
        parent = self.parentWidget()
        while parent is not None:
            parent.updateGeometry()
            parent.adjustSize()
            parent = parent.parentWidget()

    def _copy_json(self) -> None:
        QApplication.clipboard().setText(self._json_text)

    def _format_batch_json(self, batch: AppCommandBatch | PipelineMutationBatch) -> str:
        kind = "command_batch" if isinstance(batch, AppCommandBatch) else "action_batch"
        return json.dumps(
            {"type": kind, "batch": batch.model_dump(mode="json")}, indent=2, ensure_ascii=False
        )

    def _summarize(self, batch: AppCommandBatch | PipelineMutationBatch) -> str:
        items = batch.commands if isinstance(batch, AppCommandBatch) else batch.mutations
        counts: dict = {}
        for item in items:
            a = getattr(item, "action", "op")
            counts[a] = counts.get(a, 0) + 1
        return " · ".join(f"{v} × {k}" for k, v in counts.items())


class _CardButton(QPushButton):
    """Small card button with press opacity feedback."""

    def __init__(
        self, label: str, *, accent: bool = False, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(label, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if accent:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {PALETTE.accent};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-family: 'Inter';
                    font-size: 11px;
                    font-weight: 600;
                }}
                QPushButton:hover {{ background-color: {PALETTE.accent_hover}; }}
                QPushButton:disabled {{ background-color: {PALETTE.border}; color: {PALETTE.text_muted}; }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {PALETTE.text_secondary};
                    border: 1px solid {PALETTE.border};
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-family: 'Inter';
                    font-size: 11px;
                    font-weight: 500;
                }}
                QPushButton:hover {{ color: {PALETTE.text_primary}; border-color: {PALETTE.border_strong}; }}
                QPushButton:disabled {{ color: {PALETTE.text_muted}; }}
            """)

    def mousePressEvent(self, event) -> None:
        effect = self.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setStartValue(1.0)
        anim.setEndValue(0.65)
        anim.setDuration(55)
        anim.setEasingCurve(accel_decel())
        _keep(self, anim)
        anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        effect = self.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setStartValue(0.65)
        anim.setEndValue(1.0)
        anim.setDuration(FAST)
        anim.setEasingCurve(spring())
        _keep(self, anim)
        anim.start()
        super().mouseReleaseEvent(event)


class ExecutionReportCard(QFrame):
    def __init__(self, report: ExecutionReport, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(4)
        ok = report.ok
        title = QLabel("Changes applied" if ok else "Some changes failed")
        title.setFont(font_outfit(10, QFont.Weight.Bold))
        title.setStyleSheet(
            f"color: {PALETTE.success if ok else PALETTE.error}; letter-spacing: 0.06em;"
        )
        layout.addWidget(title)
        for r in report.results:
            sym = "✓" if r.success else "✕"
            c = PALETTE.success if r.success else PALETTE.error
            lbl = QLabel(f"<span style='color:{c}'>{sym}</span>  {r.message or r.label}")
            lbl.setWordWrap(True)
            lbl.setFont(font_inter(11))
            lbl.setStyleSheet(f"color: {PALETTE.text_secondary};")
            layout.addWidget(lbl)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {PALETTE.bg_node};
                border: 1px solid {PALETTE.border};
                border-radius: {RADII.md}px;
            }}
        """)


# ── Main panel ────────────────────────────────────────────────────────────────


class AIPanel(QWidget):
    message_sent = Signal(str, object)
    apply_batch_clicked = Signal(object)
    reject_batch_clicked = Signal(object)
    settings_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._current_bubble: Optional[MessageBubble] = None
        self._current_action_card: Optional[ActionPreviewCard] = None
        self._auto_approve_enabled = False
        self._show_action_json = True

        self.setStyleSheet(f"background-color: {PALETTE.bg_panel}; color: {PALETTE.text_primary};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_messages_area(), 1)
        layout.addWidget(self._build_input_area())

    # ── public API ────────────────────────────────────────────────────────────

    def set_auto_approve_enabled(self, enabled: bool) -> None:
        self._auto_approve_enabled = enabled

    def set_show_action_json(self, enabled: bool) -> None:
        self._show_action_json = enabled

    def on_token(self, text: str) -> None:
        if self._current_bubble is None or self._current_bubble._role != "assistant":
            self._current_bubble = self._add_bubble("assistant", "")
            self._current_bubble.start_cursor()
        self._current_bubble.append_text(text)
        self._scroll_to_bottom()

    def on_message(self, text: str) -> None:
        if self._current_bubble is not None and self._current_bubble._role == "assistant":
            self._current_bubble.append_text(text)
        else:
            self._current_bubble = self._add_bubble("assistant", text)
        if self._current_bubble:
            self._current_bubble.stop_cursor()
        self._current_bubble = None

    def on_action_batch(
        self,
        batch: AppCommandBatch | PipelineMutationBatch,
        auto_approved: Optional[bool] = None,
    ) -> None:
        if self._current_action_card:
            self._messages_layout.removeWidget(self._current_action_card)
            self._current_action_card.deleteLater()
        card = ActionPreviewCard(
            batch,
            auto_approved=self._auto_approve_enabled if auto_approved is None else auto_approved,
            show_json=self._show_action_json,
        )
        card.apply_clicked.connect(lambda b: self.apply_batch_clicked.emit(b))
        card.reject_clicked.connect(lambda b: self.reject_batch_clicked.emit(b))
        self._add_widget(card)
        self._current_action_card = card

    def on_execution_report(self, report: ExecutionReport) -> None:
        self._add_widget(ExecutionReportCard(report))

    def on_error(self, message: str) -> None:
        bubble = MessageBubble("assistant", f"⚠ {message}")
        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {PALETTE.bg_node};
                border: 1px solid {PALETTE.error};
                border-radius: {RADII.md}px;
            }}
        """)
        self._add_widget(bubble)

    def on_done(self) -> None:
        if self._current_bubble:
            self._current_bubble.stop_cursor()
        self._current_bubble = None
        self._current_action_card = None
        self._send_btn.set_loading(False)

    # ── builders ──────────────────────────────────────────────────────────────

    def _build_header(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(
            f"QWidget {{ background-color: {PALETTE.bg_panel}; border-bottom: 1px solid {PALETTE.border}; }}"
        )
        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        title = QLabel("AI Assistant")
        tf = font_instrument_serif(22)
        tf.setStyleName("Regular")
        title.setFont(tf)
        title.setStyleSheet(f"color: {PALETTE.text_primary}; letter-spacing: -0.3px;")
        layout.addWidget(title)

        badge = QLabel("Polaris")
        badge.setFont(font_outfit(9, QFont.Weight.Bold))
        badge.setStyleSheet(
            f"color: {PALETTE.bg_canvas}; background-color: {PALETTE.accent_hover}; padding: 2px 8px; border-radius: 8px;"
        )
        layout.addWidget(badge)
        layout.addStretch()

        settings_btn = QPushButton("Settings")
        settings_btn.setFont(font_inter(11, QFont.Weight.Medium))
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {PALETTE.text_secondary};
                border: 1px solid {PALETTE.border};
                border-radius: 6px;
                padding: 4px 10px;
                font-family: 'Inter';
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {PALETTE.text_primary};
                border-color: {PALETTE.border_strong};
            }}
        """)
        settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(settings_btn)
        return container

    def _build_messages_area(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background-color: {PALETTE.bg_panel}; border: none; }}
            QScrollBar:vertical {{ width: 5px; background: transparent; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {PALETTE.border}; border-radius: 2px; min-height: 20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        self._scroll_area = scroll

        self._messages_container = QWidget()
        self._messages_container.setStyleSheet(f"background-color: {PALETTE.bg_panel};")
        self._messages_layout = QVBoxLayout(self._messages_container)
        self._messages_layout.setContentsMargins(16, 16, 16, 16)
        self._messages_layout.setSpacing(10)
        self._messages_layout.addStretch()

        scroll.setWidget(self._messages_container)
        return scroll

    def _build_input_area(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(
            f"QWidget {{ background-color: {PALETTE.bg_panel}; border-top: 1px solid {PALETTE.border}; }}"
        )
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._input = _AnimatedInput()
        self._input.returnPressed.connect(self._send_message)
        layout.addWidget(self._input, 1)

        self._send_btn = _SendButton()
        self._send_btn.clicked.connect(self._send_message)
        layout.addWidget(self._send_btn)
        return container

    # ── internal helpers ──────────────────────────────────────────────────────

    def _send_message(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self._add_bubble("user", text)
        self._send_btn.set_loading(True)
        self.message_sent.emit(text, None)

    def _add_bubble(self, role: str, content: str) -> MessageBubble:
        bubble = MessageBubble(role, content)
        idx = self._messages_layout.count() - 1
        self._messages_layout.insertWidget(idx, bubble)
        fade_slide_in(bubble, duration_ms=180)
        QTimer.singleShot(20, self._scroll_to_bottom)
        return bubble

    def _add_widget(self, widget: QWidget) -> None:
        idx = self._messages_layout.count() - 1
        self._messages_layout.insertWidget(idx, widget)
        fade_slide_in(widget, duration_ms=200)
        QTimer.singleShot(20, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        bar = self._scroll_area.verticalScrollBar()
        # Animate scroll
        current = bar.value()
        target = bar.maximum()
        if current == target:
            return
        anim = QVariantAnimation(self)
        anim.setStartValue(current)
        anim.setEndValue(target)
        anim.setDuration(280)
        anim.setEasingCurve(accel_decel())
        anim.valueChanged.connect(lambda v: bar.setValue(int(v)))
        _keep(self, anim)
        anim.start()
