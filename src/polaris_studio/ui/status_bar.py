from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QVariantAnimation
from PySide6.QtWidgets import QLabel, QStatusBar, QWidget

from polaris_studio.ui.motion import _keep, accel_decel, crossfade_label
from polaris_studio.ui.theme import PALETTE, RADII, font_inter, font_outfit


class StatusBar(QStatusBar):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(self._style())

        muted = font_inter(11)
        accent = font_outfit(10)

        self._node_label = QLabel("No node selected")
        self._node_label.setObjectName("muted")
        self._node_label.setFont(muted)
        self.addWidget(self._node_label)

        self.addPermanentWidget(self._sep())

        self._rows_label = QLabel("Rows: 0")
        self._rows_label.setObjectName("muted")
        self._rows_label.setFont(muted)
        self.addPermanentWidget(self._rows_label)

        self.addPermanentWidget(self._sep())

        self._time_label = QLabel("Time: --")
        self._time_label.setObjectName("muted")
        self._time_label.setFont(muted)
        self.addPermanentWidget(self._time_label)

        self.addPermanentWidget(self._sep())

        self._ai_status = QLabel("AI")
        self._ai_status.setFont(accent)
        self._ai_status.setObjectName("ai_pill")
        self.addPermanentWidget(self._ai_status)

        self._status_text = QLabel("Ready")
        self._status_text.setFont(font_inter(11))
        self._status_text.setObjectName("status_text")
        self.addPermanentWidget(self._status_text)

        self._countup_anim: Optional[QVariantAnimation] = None

    def _style(self) -> str:
        return f"""
        QStatusBar {{
            background: {PALETTE.bg_panel};
            color: {PALETTE.text_primary};
            border-top: 1px solid {PALETTE.border};
            font-family: 'Inter';
            font-size: 11px;
            padding: 4px 12px;
            min-height: 28px;
        }}
        QStatusBar::item {{ border: none; }}
        QLabel {{ font-family: 'Inter'; padding: 0 10px; }}
        QLabel#muted {{ color: {PALETTE.text_secondary}; }}
        QLabel#status_text {{ color: {PALETTE.text_primary}; font-weight: 500; }}
        QLabel#ai_pill {{
            color: {PALETTE.accent};
            font-family: 'Outfit';
            font-weight: 600;
            letter-spacing: 0.5px;
            padding: 2px 8px;
            border: 1px solid {PALETTE.accent};
            border-radius: {RADII.sm}px;
            background: rgba(36, 91, 219, 0.07);
        }}
        """

    def _sep(self) -> QLabel:
        lbl = QLabel("·")
        lbl.setObjectName("muted")
        lbl.setStyleSheet("padding: 0 2px;")
        return lbl

    # ── public API ────────────────────────────────────────────────────────────

    def set_status(self, text: str) -> None:
        crossfade_label(
            self._status_text,
            text,
            self._status_text.setText,
            duration_ms=160,
        )

    def set_node_info(self, node_id: str, node_type: str) -> None:
        crossfade_label(
            self._node_label,
            f"Node: {node_id} ({node_type})",
            self._node_label.setText,
            duration_ms=120,
        )

    def clear_node_info(self) -> None:
        crossfade_label(
            self._node_label,
            "No node selected",
            self._node_label.setText,
            duration_ms=120,
        )

    def set_row_count(self, count: int) -> None:
        crossfade_label(
            self._rows_label,
            f"Rows: {count:,}",
            self._rows_label.setText,
            duration_ms=120,
        )

    def set_execution_time(self, ms: float) -> None:
        """Animate count-up from 0 to final execution time."""
        if self._countup_anim is not None:
            self._countup_anim.stop()

        anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(ms)
        anim.setDuration(min(int(ms * 0.8), 900))
        anim.setEasingCurve(accel_decel())

        def _tick(v: float) -> None:
            val = float(v)
            if val < 1000:
                self._time_label.setText(f"Time: {val:.0f}ms")
            else:
                self._time_label.setText(f"Time: {val / 1000:.2f}s")

        anim.valueChanged.connect(_tick)
        _keep(self, anim)
        self._countup_anim = anim
        anim.start()
