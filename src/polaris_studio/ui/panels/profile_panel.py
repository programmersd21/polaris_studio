from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.core.profiler import ColumnProfile, DataProfile
from polaris_studio.ui.theme import PALETTE, RADII


class ProfilePanel(QWidget):
    refresh_requested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._profile: Optional[DataProfile] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        self._header = QLabel("Data Profile")
        self._header.setStyleSheet("font-size: 13px; font-weight: 700;")
        header_layout.addWidget(self._header)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setFixedWidth(80)
        self._refresh_btn.clicked.connect(self._on_refresh)
        header_layout.addWidget(self._refresh_btn)
        layout.addLayout(header_layout)

        self._summary = QLabel("No data selected")
        self._summary.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._summary)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search columns...")
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._columns_container = QWidget()
        self._columns_container.setStyleSheet("background: transparent;")
        self._columns_layout = QVBoxLayout(self._columns_container)
        self._columns_layout.setContentsMargins(0, 0, 0, 0)
        self._columns_layout.setSpacing(4)
        self._columns_layout.addStretch()

        scroll.setWidget(self._columns_container)
        layout.addWidget(scroll)

    def set_profile(self, profile: DataProfile) -> None:
        self._profile = profile
        self._summary.setText(f"{profile.col_count} columns  |  {profile.row_count:,} rows")
        self._header.setText(f"Data Profile  [{profile.node_id}]")
        self._rebuild()

    def _rebuild(self) -> None:
        while self._columns_layout.count() > 1:
            item = self._columns_layout.takeAt(0)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()

        if not self._profile:
            return

        query = self._search.text().lower().strip()
        for col in self._profile.columns:
            if query and query not in col.name.lower():
                continue
            widget = self._create_column_widget(col)
            self._columns_layout.insertWidget(self._columns_layout.count() - 1, widget)

    def _create_column_widget(self, col: ColumnProfile) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"""
            QWidget {{
                border: 1px solid {PALETTE.border};
                border-radius: {RADII.sm}px;
            }}
        """)

        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        name_label = QLabel(col.name)
        name_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; font-family: 'JetBrains Mono', 'Inter';"
        )
        layout.addWidget(name_label)

        dtype_label = QLabel(col.dtype)
        dtype_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(dtype_label)

        info = QLabel(
            f"Nulls: {col.null_count:,} ({col.null_pct:.1f}%)  |  Unique: {col.unique_count:,}"
        )
        info.setStyleSheet("font-size: 10px; font-family: 'JetBrains Mono', 'Inter';")
        layout.addWidget(info)

        if col.mean is not None:
            stats = QLabel(
                f"Min: {col.min_value}  |  Max: {col.max_value}  |  Mean: {col.mean:.2f}  |  Std: {col.std:.2f}"
            )
            stats.setStyleSheet("font-size: 10px; font-family: 'JetBrains Mono', 'Inter';")
            layout.addWidget(stats)

        if col.top_5_values:
            top_str = "  |  ".join(f"{v}: {c:,}" for v, c in col.top_5_values[:3])
            top_label = QLabel(f"Top: {top_str}")
            top_label.setWordWrap(True)
            top_label.setStyleSheet("font-size: 10px;")
            layout.addWidget(top_label)

        if col.histogram_bins and col.histogram_counts:
            max_count = max(col.histogram_counts) if col.histogram_counts else 1
            bar_chars = []
            for c in col.histogram_counts[:15]:
                ratio = c / max_count
                bar = "|" + chr(0x2588) * int(ratio * 20) + chr(0x2591) * (20 - int(ratio * 20))
                bar_chars.append(bar)
            hist_label = QLabel("  ".join(bar_chars))
            hist_label.setStyleSheet(
                f"color: {PALETTE.accent}; font-size: 8px; font-family: 'JetBrains Mono', 'Inter'; letter-spacing: 0px;"
            )
            layout.addWidget(hist_label)

        return w

    def _filter(self, query: str) -> None:
        self._rebuild()

    def _on_refresh(self) -> None:
        if self._profile:
            self.refresh_requested.emit(self._profile.node_id)
