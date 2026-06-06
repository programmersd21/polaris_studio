from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import polars as pl
import pyqtgraph as pg
import pyqtgraph.exporters as exporters
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QLabel,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.ui.theme import PALETTE, RADII

_ACCENT = "#7c6af7"
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

        pg.setConfigOptions(background="#ffffff", foreground="#1a1a1a")

        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setLabel("left", "Value")
        self._plot_widget.setLabel("bottom", "Index")
        self._plot_widget.showGrid(x=True, y=True, alpha=0.1)
        self._plot_widget.setStyleSheet("border: none;")
        layout.addWidget(self._plot_widget, 1)

        self._no_data_label = QLabel("No data. Connect a node to see its chart.")
        self._no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_data_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self._no_data_label)

    def update_data(self, df: pl.DataFrame) -> None:
        self._df = df
        self._no_data_label.setVisible(len(df) == 0)
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
        self._plot_widget.clear()
        self._no_data_label.setVisible(True)

    def _on_chart_type_change(self, chart_type: str) -> None:
        self._chart_type = chart_type.lower()
        self._render()

    def _render(self) -> None:
        if self._df is None or len(self._df) == 0:
            self._plot_widget.clear()
            self._no_data_label.setVisible(True)
            return

        self._plot_widget.clear()
        self._no_data_label.setVisible(False)

        try:
            if self._chart_type == "bar":
                self._render_bar()
            elif self._chart_type == "line":
                self._render_line()
            elif self._chart_type == "scatter":
                self._render_scatter()
            elif self._chart_type == "histogram":
                self._render_histogram()
            elif self._chart_type == "box":
                self._render_box()
            elif self._chart_type == "heatmap":
                self._render_heatmap()
        except Exception as exc:
            self._plot_widget.addItem(pg.TextItem(f"Chart error: {exc}", color="#f38ba8"))

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

    def _pick_color(self) -> str:
        return self._node_params.get("color_column", "")

    @staticmethod
    def _to_numeric(vals: list) -> list:
        result = []
        for v in vals:
            if v is not None:
                try:
                    result.append(float(v))
                except (ValueError, TypeError):
                    pass
        return result

    def _render_bar(self) -> None:
        if self._df is None or self._df.is_empty():
            return
        x_col, y_col, y_multi = self._pick_xy()
        if not y_multi:
            y_multi = [y_col] if y_col else self._df.columns[1:2]
        x = self._df[x_col].to_list()
        x_num = list(range(len(x)))
        for i, col in enumerate(y_multi):
            y = self._to_numeric(self._df[col].to_list())
            if not y:
                continue
            color = _PALETTE_HEX[i % len(_PALETTE_HEX)]
            offset = (i - (len(y_multi) - 1) / 2) * 0.18
            bg = pg.BarGraphItem(
                x=[v + offset for v in x_num], height=y, width=0.14, brush=color, pen=color
            )
            self._plot_widget.addItem(bg)
        self._plot_widget.getAxis("bottom").setTicks([list(enumerate(x))])
        self._plot_widget.setLabel("bottom", x_col)
        self._plot_widget.setLabel("left", ", ".join(y_multi))

    def _render_line(self) -> None:
        if self._df is None or self._df.is_empty():
            return
        _, _, y_multi = self._pick_xy()
        x_col = self._node_params.get("x_column", "") or self._df.columns[0]
        x = self._df[x_col].to_list() if x_col in self._df.columns else list(range(len(self._df)))
        for i, col in enumerate(y_multi):
            y = self._to_numeric(self._df[col].to_list())
            if not y:
                continue
            color = _PALETTE_HEX[i % len(_PALETTE_HEX)]
            self._plot_widget.plot(x, y, pen=pg.mkPen(color=color, width=2), name=col)
        if len(y_multi) > 1:
            self._plot_widget.addLegend()
        self._plot_widget.setLabel("bottom", x_col)
        self._plot_widget.setLabel("left", "Value")

    def _render_scatter(self) -> None:
        if self._df is None or self._df.is_empty():
            return
        x_col, y_col, _ = self._pick_xy()
        if not y_col:
            y_col = self._df.columns[1] if len(self._df.columns) > 1 else self._df.columns[0]
        x = self._to_numeric(self._df[x_col].to_list())
        y = self._to_numeric(self._df[y_col].to_list())
        if not x or not y:
            return
        color_col = self._pick_color()
        if color_col and color_col in self._df.columns:
            cvals = self._df[color_col].to_list()
            unique = sorted(set(c for c in cvals if c is not None))
            cmap = {v: _PALETTE_HEX[i % len(_PALETTE_HEX)] for i, v in enumerate(unique)}
            colors = [cmap.get(v, _ACCENT) for v in cvals]
        else:
            colors = _ACCENT  # type: ignore[assignment]
        scatter = pg.ScatterPlotItem(x, y, pen=None, brush=colors, size=8)
        self._plot_widget.addItem(scatter)
        self._plot_widget.setLabel("bottom", x_col)
        self._plot_widget.setLabel("left", y_col)

    def _render_histogram(self) -> None:
        if self._df is None or self._df.is_empty():
            return
        col = self._node_params.get("column", "") or self._df.columns[0]
        bins = int(self._node_params.get("bins", 20))
        data = self._df[col].drop_nulls().to_list()
        y, x = np.histogram(data, bins=bins)
        bg = pg.BarGraphItem(x=x[:-1], height=y, width=(x[1] - x[0]) * 0.8, brush=_ACCENT)
        self._plot_widget.addItem(bg)
        self._plot_widget.setLabel("bottom", col)
        self._plot_widget.setLabel("left", "Frequency")

    def _render_box(self) -> None:
        if self._df is None or self._df.is_empty():
            return
        cols_param = self._node_params.get("columns", [])
        if not cols_param or not isinstance(cols_param, list):
            numeric_types = (pl.Int32, pl.Int64, pl.Float32, pl.Float64)
            cols_param = [c for c in self._df.columns if self._df[c].dtype in numeric_types][:5]
        if not cols_param:
            cols_param = self._df.columns[:5]
        ticks = []
        for i, col in enumerate(cols_param):
            if col not in self._df.columns:
                continue
            vals = self._df[col].drop_nulls().to_list()
            vals = [float(v) for v in vals if v is not None]
            if not vals:
                continue
            q1 = float(np.percentile(vals, 25))
            med = float(np.percentile(vals, 50))
            q3 = float(np.percentile(vals, 75))
            lo = float(min(vals))
            hi = float(max(vals))
            ticks.append((i, col))

            box = QGraphicsRectItem(i - 0.25, q1, 0.5, max(q3 - q1, 1e-9))
            box.setPen(pg.mkPen(_ACCENT, width=2))
            box.setBrush(pg.mkBrush(124, 106, 247, 80))
            self._plot_widget.addItem(box)

            whisker_low = QGraphicsLineItem(i, lo, i, q1)
            whisker_low.setPen(pg.mkPen(_ACCENT, width=1.5))
            self._plot_widget.addItem(whisker_low)

            whisker_high = QGraphicsLineItem(i, q3, i, hi)
            whisker_high.setPen(pg.mkPen(_ACCENT, width=1.5))
            self._plot_widget.addItem(whisker_high)

            median = QGraphicsLineItem(i - 0.25, med, i + 0.25, med)
            median.setPen(pg.mkPen("#1a1a1a", width=2))
            self._plot_widget.addItem(median)

        if ticks:
            self._plot_widget.getAxis("bottom").setTicks([ticks])
            self._plot_widget.setLabel("bottom", "Column")
            self._plot_widget.setLabel("left", "Value")

    def _render_heatmap(self) -> None:
        if self._df is None or self._df.is_empty():
            return
        x_col = self._node_params.get("x_column", "")
        y_col = self._node_params.get("y_column", "")
        val_col = self._node_params.get("value_column", "")
        if x_col and y_col and val_col:
            if (
                x_col not in self._df.columns
                or y_col not in self._df.columns
                or val_col not in self._df.columns
            ):
                return
            numeric = [x_col, val_col]
        else:
            numeric = [
                c
                for c in self._df.columns
                if self._df[c].dtype in (pl.Float32, pl.Float64, pl.Int32, pl.Int64)
            ]
            if len(numeric) < 2:
                return
            x_col, y_col = numeric[0], numeric[1]
        data = (
            self._df[numeric].to_numpy() if len(numeric) <= 3 else self._df[numeric[:3]].to_numpy()
        )
        img = pg.ImageItem(data.T)
        self._plot_widget.addItem(img)
        self._plot_widget.setLabel("bottom", x_col)
        self._plot_widget.setLabel("left", y_col)

    def _export_png_handler(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export PNG", "", "PNG (*.png)")
        if path:
            exporter = exporters.ImageExporter(self._plot_widget.plotItem)
            exporter.export(path)

    def _export_svg_handler(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export SVG", "", "SVG (*.svg)")
        if path:
            exporter = exporters.SVGExporter(self._plot_widget.plotItem)
            exporter.export(path)
