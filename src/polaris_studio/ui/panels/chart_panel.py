from __future__ import annotations

from typing import Optional

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


class ChartPanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._df: Optional[pl.DataFrame] = None
        self._chart_type: str = "bar"

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

    def clear(self) -> None:
        self._df = None
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
        except Exception:
            self._plot_widget.addItem(pg.TextItem("Error rendering chart", color="#f38ba8"))

    def _render_bar(self) -> None:
        if not self._df:
            return
        cols = self._df.columns
        x_col = cols[0]
        y_col = cols[1] if len(cols) > 1 else cols[0]
        x = self._df[x_col].to_list()
        y = self._df[y_col].to_list()
        x_num = list(range(len(x)))
        bg = pg.BarGraphItem(x=x_num, height=y, width=0.7, brush="#7c6af7", pen="#7c6af7")
        self._plot_widget.addItem(bg)
        self._plot_widget.setLabel("bottom", x_col)
        self._plot_widget.setLabel("left", y_col)

    def _render_line(self) -> None:
        if not self._df:
            return
        cols = self._df.columns
        for col in cols[1:]:
            y = self._df[col].to_list()
            self._plot_widget.plot(y, pen=pg.mkPen(color="#7c6af7", width=2), name=col)
        self._plot_widget.addLegend()

    def _render_scatter(self) -> None:
        if not self._df:
            return
        cols = self._df.columns
        x_col = cols[0]
        y_col = cols[1] if len(cols) > 1 else cols[0]
        x = self._df[x_col].to_list()
        y = self._df[y_col].to_list()
        scatter = pg.ScatterPlotItem(x, y, pen="#7c6af7", brush="#7c6af7", size=6)
        self._plot_widget.addItem(scatter)
        self._plot_widget.setLabel("bottom", x_col)
        self._plot_widget.setLabel("left", y_col)

    def _render_histogram(self) -> None:
        if not self._df:
            return
        col = self._df.columns[0]
        data = self._df[col].drop_nulls().to_list()
        y, x = np.histogram(data, bins=20)
        bg = pg.BarGraphItem(x=x[:-1], height=y, width=(x[1] - x[0]) * 0.8, brush="#7c6af7")
        self._plot_widget.addItem(bg)
        self._plot_widget.setLabel("bottom", col)

    def _render_box(self) -> None:
        if not self._df:
            return
        numeric_types = (pl.Int32, pl.Int64, pl.Float32, pl.Float64)
        cols = [c for c in self._df.columns if self._df[c].dtype in numeric_types][:5]
        if not cols:
            cols = self._df.columns[:5]
        ticks = []
        for i, col in enumerate(cols):
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
            box.setPen(pg.mkPen("#7c6af7", width=2))
            box.setBrush(pg.mkBrush(124, 106, 247, 80))
            self._plot_widget.addItem(box)

            whisker_low = QGraphicsLineItem(i, lo, i, q1)
            whisker_low.setPen(pg.mkPen("#7c6af7", width=1.5))
            self._plot_widget.addItem(whisker_low)

            whisker_high = QGraphicsLineItem(i, q3, i, hi)
            whisker_high.setPen(pg.mkPen("#7c6af7", width=1.5))
            self._plot_widget.addItem(whisker_high)

            median = QGraphicsLineItem(i - 0.25, med, i + 0.25, med)
            median.setPen(pg.mkPen("#1a1a1a", width=2))
            self._plot_widget.addItem(median)

        if ticks:
            self._plot_widget.getAxis("bottom").setTicks([ticks])
            self._plot_widget.setLabel("bottom", "Column")
            self._plot_widget.setLabel("left", "Value")

    def _render_heatmap(self) -> None:
        if not self._df:
            return
        numeric = [
            c
            for c in self._df.columns
            if self._df[c].dtype in (pl.Float32, pl.Float64, pl.Int32, pl.Int64)
        ]
        if len(numeric) < 2:
            return
        data = self._df[numeric].to_numpy()
        img = pg.ImageItem(data.T)
        self._plot_widget.addItem(img)
        self._plot_widget.setLabel("bottom", numeric[0])
        self._plot_widget.setLabel("left", numeric[1])

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
