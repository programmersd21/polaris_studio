from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import polars as pl
from PySide6.QtGui import QColor


class CondFmtType(Enum):
    COLOR_SCALE_2 = "color_scale_2"
    COLOR_SCALE_3 = "color_scale_3"
    DATA_BAR = "data_bar"
    THRESHOLD_GT = "threshold_gt"
    THRESHOLD_LT = "threshold_lt"
    NULL_HIGHLIGHT = "null_highlight"
    TOP_N = "top_n"
    BOTTOM_N = "bottom_n"
    DUPLICATE = "duplicate"
    UNIQUE = "unique"


@dataclass
class ConditionalFmtRule:
    rule_id: str
    column_name: str
    fmt_type: CondFmtType
    params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    enabled: bool = True


def _parse_color(hex_color: str) -> QColor:
    c = QColor()
    c.setNamedColor(hex_color)
    return c if c.isValid() else QColor("#ffffff")


def _interpolate_color(c1: QColor, c2: QColor, t: float) -> QColor:
    r = int(c1.red() + (c2.red() - c1.red()) * t)
    g = int(c1.green() + (c2.green() - c1.green()) * t)
    b = int(c1.blue() + (c2.blue() - c1.blue()) * t)
    return QColor(r, g, b)


class ConditionalFormatEngine:
    def __init__(self, df: pl.DataFrame) -> None:
        self._df = df
        self._rules: List[ConditionalFmtRule] = []
        self._precomputed: Dict[Tuple[int, str], QColor] = {}

    def add_rule(self, rule: ConditionalFmtRule) -> None:
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)

    def remove_rule(self, rule_id: str) -> None:
        self._rules = [r for r in self._rules if r.rule_id != rule_id]

    def get_cell_color(self, row: int, col_name: str) -> Optional[QColor]:
        return self._precomputed.get((row, col_name))

    def precompute(self) -> None:
        self._precomputed.clear()
        for rule in self._rules:
            if not rule.enabled:
                continue
            col = rule.column_name
            if col not in self._df.columns:
                continue
            series = self._df[col]
            ft = rule.fmt_type

            if ft == CondFmtType.NULL_HIGHLIGHT:
                highlight_color = _parse_color(rule.params.get("color", "#f38ba8"))
                for i in range(len(series)):
                    if series[i] is None:
                        self._precomputed[(i, col)] = highlight_color

            elif ft in (CondFmtType.THRESHOLD_GT, CondFmtType.THRESHOLD_LT):
                threshold = rule.params.get("value", 0)
                color = _parse_color(rule.params.get("color", "#f38ba8"))
                for i in range(len(series)):
                    val = series[i]
                    if val is not None:
                        try:
                            v = float(val)
                            if ft == CondFmtType.THRESHOLD_GT and v > float(threshold):
                                self._precomputed[(i, col)] = color
                            elif ft == CondFmtType.THRESHOLD_LT and v < float(threshold):
                                self._precomputed[(i, col)] = color
                        except (ValueError, TypeError):
                            pass

            elif ft == CondFmtType.COLOR_SCALE_2:
                valid = [(i, float(v)) for i, v in enumerate(series) if v is not None]
                if not valid:
                    continue
                vals = [v for _, v in valid]
                mn, mx = min(vals), max(vals)
                range_v = mx - mn if mx != mn else 1
                c1 = _parse_color(rule.params.get("min_color", "#1e1e2e"))
                c2 = _parse_color(rule.params.get("max_color", "#7c6af7"))
                for i, v in valid:
                    t = (v - mn) / range_v
                    self._precomputed[(i, col)] = _interpolate_color(c1, c2, t)

            elif ft == CondFmtType.COLOR_SCALE_3:
                valid = [(i, float(v)) for i, v in enumerate(series) if v is not None]
                if not valid:
                    continue
                vals = [v for _, v in valid]
                mn, mx = min(vals), max(vals)
                mid = rule.params.get("midpoint", (mn + mx) / 2)
                range_v = mx - mn if mx != mn else 1
                c1 = _parse_color(rule.params.get("min_color", "#1e1e2e"))
                cm = _parse_color(rule.params.get("mid_color", "#585b70"))
                c2 = _parse_color(rule.params.get("max_color", "#7c6af7"))
                for i, v in valid:
                    if v <= mid:
                        t = (v - mn) / (mid - mn) if mid != mn else 0
                        self._precomputed[(i, col)] = _interpolate_color(c1, cm, t)
                    else:
                        t = (v - mid) / (mx - mid) if mx != mid else 0
                        self._precomputed[(i, col)] = _interpolate_color(cm, c2, t)

            elif ft == CondFmtType.DATA_BAR:
                valid = [(i, float(v)) for i, v in enumerate(series) if v is not None]
                if not valid:
                    continue
                vals = [v for _, v in valid]
                mn, mx = min(vals), max(vals)
                bar_color = _parse_color(rule.params.get("color", "#7c6af7"))
                if mx == mn:
                    for i, _ in valid:
                        self._precomputed[(i, col)] = bar_color
                else:
                    for i, v in valid:
                        alpha = int(60 + 195 * (v - mn) / (mx - mn))
                        c = QColor(bar_color)
                        c.setAlpha(alpha)
                        self._precomputed[(i, col)] = c

            elif ft in (CondFmtType.TOP_N, CondFmtType.BOTTOM_N):
                n = int(rule.params.get("n", 10))
                color = _parse_color(rule.params.get("color", "#a6e3a1"))
                valid = [(i, float(v)) for i, v in enumerate(series) if v is not None]
                sorted_vals = sorted(valid, key=lambda x: x[1], reverse=(ft == CondFmtType.TOP_N))
                top_set = set(i for i, _ in sorted_vals[:n])
                for i in top_set:
                    self._precomputed[(i, col)] = color

            elif ft == CondFmtType.DUPLICATE:
                color = _parse_color(rule.params.get("color", "#f9e2af"))
                seen: Dict[Any, List[int]] = {}
                for i in range(len(series)):
                    v = series[i]
                    if v is not None:
                        seen.setdefault(v, []).append(i)
                for indices in seen.values():
                    if len(indices) > 1:
                        for i in indices:
                            self._precomputed[(i, col)] = color

            elif ft == CondFmtType.UNIQUE:
                color = _parse_color(rule.params.get("color", "#a6e3a1"))
                counts: Dict[Any, int] = {}
                for i in range(len(series)):
                    v = series[i]
                    if v is not None:
                        counts[v] = counts.get(v, 0) + 1
                for i in range(len(series)):
                    v = series[i]
                    if v is not None and counts.get(v, 0) == 1:
                        self._precomputed[(i, col)] = color
