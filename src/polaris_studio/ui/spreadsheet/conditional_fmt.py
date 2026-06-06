from __future__ import annotations

from typing import Optional

from PySide6.QtGui import QColor, QLinearGradient, QPainter

from polaris_studio.core.formatter import CondFmtType
from polaris_studio.core.formatter import ConditionalFmtRule as CoreRule
from polaris_studio.core.formatter import ConditionalFormatEngine as CoreEngine

# Re-export core classes
ConditionalFormatEngine = CoreEngine
ConditionalFmtRule = CoreRule
CondFmtType = CondFmtType


def render_data_bar(
    painter: QPainter,
    rect,
    value: float,
    min_val: float,
    max_val: float,
    color: QColor,
) -> None:
    if max_val == min_val:
        ratio = 1.0
    else:
        ratio = max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
    bar_width = int(rect.width() * ratio * 0.9)
    bar_rect = rect.adjusted(2, 2, -2, -2)
    bar_rect.setWidth(bar_width)

    gradient = QLinearGradient(bar_rect.topLeft(), bar_rect.topRight())
    gradient.setColorAt(0.0, color)
    gradient.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 120))
    painter.fillRect(bar_rect, gradient)


def get_cell_background(
    engine: Optional[CoreEngine],
    row: int,
    col_name: str,
) -> Optional[QColor]:
    if engine is None:
        return None
    return engine.get_cell_color(row, col_name)
