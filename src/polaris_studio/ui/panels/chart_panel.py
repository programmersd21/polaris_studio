from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import polars as pl
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.ui.theme import PALETTE, RADII

_PALETTE_HEX = [
    "#7c6af7",
    "#3b82f6",
    "#f97316",
    "#22c55e",
    "#ef4444",
    "#a855f7",
    "#eab308",
    "#06b6d4",
]


class ChartPanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._df: Optional[pl.DataFrame] = None
        self._chart_type: str = "bar"
        self._node_params: Dict[str, Any] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        toolbar = QToolBar()
        toolbar.setStyleSheet(f"""
            QToolBar {{ background: transparent; border: none; spacing: 4px; }}
            QToolButton {{
                background: {PALETTE.bg_panel}; border: 1px solid {PALETTE.border}; border-radius: {RADII.sm}px;
                padding: 6px 12px; color: {PALETTE.text_primary}; font-family: 'Inter'; font-size: 11px;
            }}
            QToolButton:checked {{ background: {PALETTE.accent}; color: #fff; }}
            QToolButton:hover {{ background: {PALETTE.bg_node_alt}; }}
        """)

        self._chart_combo = QComboBox()
        self._chart_combo.addItems(["Bar", "Line", "Scatter", "Histogram", "Box", "Heatmap"])
        self._chart_combo.currentTextChanged.connect(self._on_chart_type_change)
        toolbar.addWidget(QLabel("Type:"))
        toolbar.addWidget(self._chart_combo)
        toolbar.addSeparator()

        self._export_png = QPushButton("Export PNG")
        self._export_png.clicked.connect(self._export_png_handler)
        toolbar.addWidget(self._export_png)

        self._export_svg = QPushButton("Export SVG")
        self._export_svg.clicked.connect(self._export_svg_handler)
        toolbar.addWidget(self._export_svg)

        layout.addWidget(toolbar)

        self._figure = Figure(figsize=(8, 6), facecolor='#ffffff')
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._canvas.setStyleSheet("border: none;")
        layout.addWidget(self._canvas, 1)

        self._no_data_label = QLabel("No data. Connect a node to see its chart.")
        self._no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_data_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self._no_data_label)

    def update_data(self, df: pl.DataFrame) -> None:
        self._df = df
        self._no_data_label.setVisible(len(df) == 0)
        self._canvas.setVisible(len(df) > 0)
        if len(df) > 0:
            self._render()

    def set_chart_type(self, chart_type: str) -> None:
        display_map = {
            "bar_chart": "Bar",
            "line_chart": "Line",
            "scatter_chart": "Scatter",
            "histogram": "Histogram",
            "box_chart": "Box",
            "heatmap": "Heatmap",
        }
        display = display_map.get(chart_type, chart_type.title())
        idx = self._chart_combo.findText(display)
        if idx >= 0:
            self._chart_combo.blockSignals(True)
            self._chart_combo.setCurrentIndex(idx)
            self._chart_combo.blockSignals(False)
        self._chart_type = display.lower()

    def set_params(self, params: Dict[str, Any]) -> None:
        self._node_params = dict(params)

    def clear(self) -> None:
        self._df = None
        self._node_params.clear()
        self._figure.clear()
        self._canvas.draw()
        self._no_data_label.setVisible(True)
        self._canvas.setVisible(False)

    def _on_chart_type_change(self, chart_type: str) -> None:
        self._chart_type = chart_type.lower()
        self._render()

    def _render(self) -> None:
        if self._df is None or len(self._df) == 0:
            self._figure.clear()
            self._canvas.draw()
            return

        self._figure.clear()
        ax = self._figure.add_subplot(111)
        
        try:
            if self._chart_type == "bar":
                self._render_bar(ax)
            elif self._chart_type == "line":
                self._render_line(ax)
            elif self._chart_type == "scatter":
                self._render_scatter(ax)
            elif self._chart_type == "histogram":
                self._render_histogram(ax)
            elif self._chart_type == "box":
                self._render_box(ax)
            elif self._chart_type == "heatmap":
                self._render_heatmap(ax)
            
            self._figure.tight_layout()
            self._canvas.draw()
        except Exception as exc:
            ax.text(0.5, 0.5, f"Chart error: {exc}", ha='center', va='center', 
                   transform=ax.transAxes, color='#f38ba8')
            self._canvas.draw()

    def _pick_xy(self) -> tuple:
        cols = self._df.columns  # type: ignore[union-attr]
        x_col = self._node_params.get("x_column", "") or cols[0]
        y_col = self._node_params.get("y_column", "")
        y_multi = self._node_params.get("y_column", "")
        y_multi = (
            y_multi
            if isinstance(y_multi, list)
            else [s.strip() for s in y_multi.split(",") if s.strip()]
            if y_multi
            else []
        )
        if not y_multi:
            numeric_types = (pl.Float32, pl.Float64, pl.Int32, pl.Int64, pl.UInt32, pl.UInt64)
            numeric = [c for c in cols if self._df[c].dtype in numeric_types]  # type: ignore[index, operator]
            y_multi = numeric[1:2] if len(numeric) > 1 else numeric[:1]
            if not y_multi:
                y_multi = cols[1:2] if len(cols) > 1 else cols[:1]
        return x_col, y_col, y_multi

    @staticmethod
    def _to_numeric(vals: list) -> List[float]:
        result = []
        for v in vals:
            if v is not None:
                try:
                    result.append(float(v))
                except (ValueError, TypeError):
                    pass
        return result

    def _render_bar(self, ax) -> None:
        if self._df is None or self._df.is_empty():
            return
        x_col, y_col, y_multi = self._pick_xy()
        if not y_multi:
            y_multi = [y_col] if y_col else self._df.columns[1:2]
        
        x_labels = [str(v) for v in self._df[x_col].to_list()]
        x_positions = np.arange(len(x_labels))
        bar_width = 0.7 / max(len(y_multi), 1)
        
        for i, col in enumerate(y_multi):
            y_vals = self._to_numeric(self._df[col].to_list())
            if not y_vals:
                continue
            color = _PALETTE_HEX[i % len(_PALETTE_HEX)]
            offset = (i - (len(y_multi) - 1) / 2) * bar_width
            ax.bar(x_positions + offset, y_vals, bar_width, label=col, color=color)
        
        ax.set_xticks(x_positions)
        ax.set_xticklabels(x_labels, rotation=45, ha='right')
        ax.set_xlabel(x_col)
        ax.set_ylabel(", ".join(y_multi))
        if len(y_multi) > 1:
            ax.legend()

    def _render_line(self, ax) -> None:
        if self._df is None or self._df.is_empty():
            return
        _, _, y_multi = self._pick_xy()
        x_col = self._node_params.get("x_column", "") or self._df.columns[0]
        x_vals = self._to_numeric(self._df[x_col].to_list()) if x_col in self._df.columns else list(range(len(self._df)))
        
        for i, col in enumerate(y_multi):
            y_vals = self._to_numeric(self._df[col].to_list())
            if not y_vals:
                continue
            color = _PALETTE_HEX[i % len(_PALETTE_HEX)]
            ax.plot(x_vals, y_vals, label=col, color=color, linewidth=2)
        
        ax.set_xlabel(x_col)
        ax.set_ylabel("Value")
        if len(y_multi) > 1:
            ax.legend()

    def _render_scatter(self, ax) -> None:
        if self._df is None or self._df.is_empty():
            return
        x_col, y_col, _ = self._pick_xy()
        if not y_col:
            y_col = self._df.columns[1] if len(self._df.columns) > 1 else self._df.columns[0]
        
        x_vals = self._to_numeric(self._df[x_col].to_list())
        y_vals = self._to_numeric(self._df[y_col].to_list())
        if not x_vals or not y_vals:
            return
        
        color_col = self._node_params.get("color_column", "")
        if color_col and color_col in self._df.columns:
            c_vals = self._df[color_col].to_list()
            unique = sorted(set(c for c in c_vals if c is not None))
            cmap = {v: _PALETTE_HEX[i % len(_PALETTE_HEX)] for i, v in enumerate(unique)}
            colors = [cmap.get(v, _PALETTE_HEX[0]) for v in c_vals]
            ax.scatter(x_vals, y_vals, c=colors, s=80, alpha=0.7)
        else:
            ax.scatter(x_vals, y_vals, color=_PALETTE_HEX[0], s=80, alpha=0.7)
        
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)

    def _render_histogram(self, ax) -> None:
        if self._df is None or self._df.is_empty():
            return
        col = self._node_params.get("column", "") or self._df.columns[0]
        bins = int(self._node_params.get("bins", 20))
        data = self._df[col].drop_nulls().to_list()
        data = self._to_numeric(data)
        
        ax.hist(data, bins=bins, color=_PALETTE_HEX[0], edgecolor='white', alpha=0.8)
        ax.set_xlabel(col)
        ax.set_ylabel("Frequency")

    def _render_box(self, ax) -> None:
        if self._df is None or self._df.is_empty():
            return
        cols_param = self._node_params.get("columns", [])
        if not cols_param or not isinstance(cols_param, list):
            numeric_types = (pl.Int32, pl.Int64, pl.Float32, pl.Float64)
            cols_param = [c for c in self._df.columns if self._df[c].dtype in numeric_types][:5]
        if not cols_param:
            cols_param = self._df.columns[:5]
        
        data_to_plot = []
        labels = []
        for col in cols_param:
            if col not in self._df.columns:
                continue
            vals = self._to_numeric(self._df[col].drop_nulls().to_list())
            if vals:
                data_to_plot.append(vals)
                labels.append(col)
        
        if data_to_plot:
            bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)
            for patch, color in zip(bp['boxes'], _PALETTE_HEX):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            ax.set_ylabel("Value")
            ax.tick_params(axis='x', rotation=45)

    def _render_heatmap(self, ax) -> None:
        if self._df is None or self._df.is_empty():
            return
        numeric_types = (pl.Int32, pl.Int64, pl.Float32, pl.Float64)
        numeric_cols = [c for c in self._df.columns if self._df[c].dtype in numeric_types]
        
        if len(numeric_cols) < 2:
            ax.text(0.5, 0.5, "Need at least 2 numeric columns for heatmap", 
                   ha='center', va='center', transform=ax.transAxes)
            return
        
        data_matrix = []
        for col in numeric_cols:
            data_matrix.append(self._to_numeric(self._df[col].to_list()))
        
        corr_matrix = np.corrcoef(data_matrix)
        im = ax.imshow(corr_matrix, cmap='RdYlBu_r', aspect='auto', vmin=-1, vmax=1)
        ax.set_xticks(range(len(numeric_cols)))
        ax.set_yticks(range(len(numeric_cols)))
        ax.set_xticklabels(numeric_cols, rotation=45, ha='right')
        ax.set_yticklabels(numeric_cols)
        self._figure.colorbar(im, ax=ax)

    def _export_png_handler(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export PNG", "", "PNG Files (*.png)")
        if path:
            self._figure.savefig(path, dpi=300, bbox_inches='tight')

    def _export_svg_handler(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export SVG", "", "SVG Files (*.svg)")
        if path:
            self._figure.savefig(path, format='svg', bbox_inches='tight')
