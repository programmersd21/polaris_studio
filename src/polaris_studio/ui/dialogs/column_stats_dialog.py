from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.core.profiler import ColumnProfile
from polaris_studio.ui.dialogs.base_dialog import AnimatedDialog
from polaris_studio.ui.theme import PALETTE, RADII, font_instrument_serif, font_inter, font_mono


class ColumnStatsDialog(AnimatedDialog):
    def __init__(self, profile: ColumnProfile, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Statistics: {profile.name}")
        self.setMinimumSize(440, 380)
        self.setStyleSheet(f"""
            QDialog {{
                background: {PALETTE.bg_panel};
                color: {PALETTE.text_primary};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel(f"Column:  {profile.name}")
        header.setFont(font_instrument_serif(20))
        header.setStyleSheet(
            f"color: {PALETTE.text_primary}; font-size: 20px; padding-bottom: 2px;"
        )
        layout.addWidget(header)

        dtype = QLabel(f"Type:  {profile.dtype}")
        dtype.setFont(font_mono(11))
        dtype.setStyleSheet(
            f"color: {PALETTE.text_secondary}; font-size: 11px; font-family: 'JetBrains Mono', 'Inter'; padding-bottom: 6px;"
        )
        layout.addWidget(dtype)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Property", "Value"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {PALETTE.bg_panel};
                border: 1px solid {PALETTE.border};
                border-radius: {RADII.sm}px;
                color: {PALETTE.text_primary};
                font-size: 12px;
                font-family: 'JetBrains Mono', 'Inter';
                gridline-color: {PALETTE.border};
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {PALETTE.border};
            }}
            QTableWidget::item:selected {{
                background: {PALETTE.accent_dim};
                color: {PALETTE.text_primary};
            }}
            QHeaderView::section {{
                background: {PALETTE.bg_canvas};
                color: {PALETTE.text_secondary};
                font-family: 'Inter';
                font-size: 11px;
                font-weight: 600;
                border: none;
                border-bottom: 1px solid {PALETTE.border};
                padding: 9px 12px;
            }}
        """)

        stats_data: List[tuple] = [
            ("Row Count", str(profile.unique_count)),
            ("Null Count", f"{profile.null_count:,}"),
            ("Null %", f"{profile.null_pct:.2f}%"),
            ("Unique Count", f"{profile.unique_count:,}"),
            ("Unique %", f"{profile.unique_pct:.2f}%"),
        ]

        if profile.min_value is not None:
            stats_data.append(("Min", str(profile.min_value)))
        if profile.max_value is not None:
            stats_data.append(("Max", str(profile.max_value)))
        if profile.mean is not None:
            stats_data.append(("Mean", f"{profile.mean:.4f}"))
        if profile.std is not None:
            stats_data.append(("Std Dev", f"{profile.std:.4f}"))
        if profile.median is not None:
            stats_data.append(("Median", f"{profile.median:.4f}"))

        table.setRowCount(len(stats_data))
        for i, (prop, val) in enumerate(stats_data):
            prop_item = QTableWidgetItem(prop)
            prop_item.setFont(font_inter(12, QFont.Weight.Medium))
            prop_item.setFlags(prop_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            val_item = QTableWidgetItem(val)
            val_item.setFont(font_mono(12))
            val_item.setFlags(val_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(i, 0, prop_item)
            table.setItem(i, 1, val_item)

        layout.addWidget(table, 1)

        if profile.top_5_values:
            top_label = QLabel("Top 5 Values")
            top_label.setFont(font_inter(11, QFont.Weight.DemiBold))
            top_label.setStyleSheet(
                f"color: {PALETTE.text_secondary}; font-family: 'Inter'; padding-top: 6px; letter-spacing: 0.04em;"
            )
            layout.addWidget(top_label)

            top_str = "  |  ".join(f"{v}: {c:,}" for v, c in profile.top_5_values)
            top_val = QLabel(top_str)
            top_val.setWordWrap(True)
            top_val.setFont(font_mono(11))
            top_val.setStyleSheet(
                f"color: {PALETTE.text_primary}; font-size: 11px; font-family: 'JetBrains Mono', 'Inter'; padding: 4px 0;"
            )
            layout.addWidget(top_val)

        close_btn = QPushButton("Close")
        close_btn.setFont(font_inter(12, QFont.Weight.Medium))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PALETTE.bg_panel};
                color: {PALETTE.text_primary};
                border: 1px solid {PALETTE.border};
                border-radius: {RADII.sm}px;
                padding: 8px 18px;
                font-family: 'Inter';
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {PALETTE.bg_node_alt};
                border-color: {PALETTE.border_strong};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
