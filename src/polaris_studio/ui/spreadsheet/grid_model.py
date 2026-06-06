from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import polars as pl
from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    QObject,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor

from polaris_studio.ui.theme import font_mono


class PolarisGridModel(QAbstractTableModel):
    data_changed = Signal()

    def __init__(self, df: Optional[pl.DataFrame] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._df = df if df is not None else pl.DataFrame()
        self._sort_column: Optional[str] = None
        self._sort_desc: bool = False
        self._filter_mask: Optional[pl.Series] = None
        self._edit_buffer: Dict[Tuple[int, int], Any] = {}
        self._cell_styles: Dict[Tuple[int, int], Dict[str, Any]] = {}

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._df)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._df.columns)

    def data(
        self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        if r >= len(self._df) or c >= len(self._df.columns):
            return None

        col_name = self._df.columns[c]

        if role == Qt.ItemDataRole.DisplayRole:
            if (r, c) in self._edit_buffer:
                return str(self._edit_buffer[(r, c)])
            try:
                val = self._df[r, c]
                if val is None:
                    return ""
                return str(val)
            except (IndexError, ValueError):
                return ""

        if role == Qt.ItemDataRole.EditRole:
            if (r, c) in self._edit_buffer:
                return self._edit_buffer[(r, c)]
            try:
                return self._df[r, c]
            except (IndexError, ValueError):
                return None

        if role == Qt.ItemDataRole.UserRole:
            return str(self._df.schema[col_name]) if col_name in self._df.schema else ""

        if role == Qt.ItemDataRole.TextAlignmentRole:
            style_alignment = self._cell_styles.get((r, c), {})
            alignment = style_alignment.get("alignment")
            if alignment == "center":
                return Qt.AlignmentFlag.AlignCenter
            if alignment == "right":
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if alignment == "left":
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            dtype = self._df.schema.get(col_name)
            if dtype in (pl.Int32, pl.Int64, pl.Float32, pl.Float64):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        if role == Qt.ItemDataRole.BackgroundRole:
            style_bg = self._cell_styles.get((r, c))
            if style_bg and style_bg.get("background"):
                return QColor(style_bg["background"])

        if role == Qt.ItemDataRole.ForegroundRole:
            style_fg = self._cell_styles.get((r, c))
            if style_fg and style_fg.get("foreground"):
                return QColor(style_fg["foreground"])

        if role == Qt.ItemDataRole.FontRole:
            style_font = self._cell_styles.get((r, c))
            if style_font is not None and any(
                style_font.get(key) is not None for key in ("bold", "italic")
            ):
                font = font_mono(11)
                font.setBold(bool(style_font.get("bold")))
                font.setItalic(bool(style_font.get("italic")))
                return font

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self._df.columns):
                    col = self._df.columns[section]
                    dtype = str(self._df.schema.get(col, ""))
                    dl = dtype.lower()
                    if "int" in dl or "float" in dl or "decimal" in dl:
                        prefix = "#"
                    elif "bool" in dl:
                        prefix = "B"
                    elif "date" in dl and "time" not in dl:
                        prefix = "D"
                    elif "datetime" in dl or "time" in dl:
                        prefix = "T"
                    elif (
                        "str" in dl or "utf8" in dl or "cat" in dl or "enum" in dl or "object" in dl
                    ):
                        prefix = "A"
                    elif "list" in dl or "arr" in dl:
                        prefix = "[]"
                    else:
                        prefix = "?"
                    return f"{prefix}  {col}"
                return f"Col {section}"
            if orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        if role == Qt.ItemDataRole.ToolTipRole:
            if orientation == Qt.Orientation.Horizontal and section < len(self._df.columns):
                col = self._df.columns[section]
                dtype = str(self._df.schema.get(col, ""))
                return f"{col} ({dtype})"
            return None
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        return None

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        if self.set_cell_value(index.row(), index.column(), value):
            self._edit_buffer.pop((index.row(), index.column()), None)
            return True
        return False

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Any:
        if not index.isValid():
            return Qt.ItemFlag(0)
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        if column < 0 or column >= len(self._df.columns):
            return
        col = self._df.columns[column]
        desc = order == Qt.SortOrder.DescendingOrder
        self._sort_column = col
        self._sort_desc = desc
        self.beginResetModel()
        self._df = self._df.sort(col, descending=desc)
        self.endResetModel()

    def update_dataframe(self, df: pl.DataFrame) -> None:
        self.beginResetModel()
        self._df = df
        self._edit_buffer.clear()
        self._cell_styles.clear()
        self.endResetModel()
        self.data_changed.emit()

    def _replace_dataframe(self, df: pl.DataFrame) -> None:
        self.beginResetModel()
        self._df = df
        self._edit_buffer.clear()
        self.endResetModel()
        self.data_changed.emit()

    def rename_column(self, old_name: str, new_name: str) -> bool:
        if not old_name or not new_name or old_name not in self._df.columns:
            return False
        if old_name == new_name:
            return True
        try:
            self._replace_dataframe(self._df.rename({old_name: new_name}))
            return True
        except Exception:
            return False

    def cast_column(self, column: str, target_type: str) -> bool:
        if column not in self._df.columns:
            return False
        dtype_map = {
            "Int32": pl.Int32,
            "Int64": pl.Int64,
            "Float32": pl.Float32,
            "Float64": pl.Float64,
            "Utf8": pl.Utf8,
            "Boolean": pl.Boolean,
            "Date": pl.Date,
            "Datetime": pl.Datetime,
        }
        dtype = dtype_map.get(target_type, pl.Utf8)
        try:
            self._replace_dataframe(
                self._df.with_columns(self._df[column].cast(dtype).alias(column))
            )
            return True
        except Exception:
            return False

    def fill_null(self, column: str, strategy: str, value: Any = None) -> bool:
        if column not in self._df.columns:
            return False
        try:
            series = self._df[column]
            strategy_key = strategy.lower().strip()
            if strategy_key in {"forward", "forward fill"}:
                updated = series.forward_fill()
            elif strategy_key in {"backward", "backward fill"}:
                updated = series.backward_fill()
            elif strategy_key == "mean":
                updated = series.fill_null(series.mean())
            elif strategy_key == "median":
                updated = series.fill_null(series.median())
            else:
                if strategy_key == "zero":
                    value = 0
                elif strategy_key in {"empty string", "empty"}:
                    value = ""
                updated = series.fill_null(value)
            self._replace_dataframe(self._df.with_columns(updated.alias(column)))
            return True
        except Exception:
            return False

    def delete_rows(self, rows: Sequence[int]) -> bool:
        row_set = {r for r in rows if r >= 0}
        if not row_set or len(self._df) == 0:
            return False
        try:
            indexed = self._df.with_row_index("__row_index")
            updated = indexed.filter(~pl.col("__row_index").is_in(list(row_set))).drop(
                "__row_index"
            )
            self._replace_dataframe(updated)
            return True
        except Exception:
            return False

    def insert_row(self, row_index: int, values: Optional[Dict[str, Any]] = None) -> bool:
        if row_index < 0:
            row_index = 0
        try:
            rows = self._df.to_dicts()
            template = {col: None for col in self._df.columns}
            if values:
                template.update({k: values.get(k, template.get(k)) for k in template})
            row_index = min(row_index, len(rows))
            rows.insert(row_index, template)
            self._replace_dataframe(pl.DataFrame(rows))
            return True
        except Exception:
            return False

    def set_cell_value(self, row: int, column: int, value: Any) -> bool:
        if row < 0 or column < 0 or row >= len(self._df) or column >= len(self._df.columns):
            return False
        try:
            rows = self._df.to_dicts()
            rows[row][self._df.columns[column]] = value
            self._replace_dataframe(pl.DataFrame(rows))
            return True
        except Exception:
            return False

    def set_cell_style(
        self,
        row: int,
        column: int,
        *,
        background: Optional[str] = None,
        foreground: Optional[str] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        alignment: Optional[str] = None,
    ) -> bool:
        if row < 0 or column < 0:
            return False
        key = (row, column)
        style = dict(self._cell_styles.get(key, {}))
        if background is not None:
            style["background"] = background
        if foreground is not None:
            style["foreground"] = foreground
        if bold is not None:
            style["bold"] = bold
        if italic is not None:
            style["italic"] = italic
        if alignment is not None:
            style["alignment"] = alignment
        self._cell_styles[key] = style
        if row < len(self._df) and column < len(self._df.columns):
            index = self.index(row, column)
            self.dataChanged.emit(
                index,
                index,
                [
                    Qt.ItemDataRole.BackgroundRole,
                    Qt.ItemDataRole.ForegroundRole,
                    Qt.ItemDataRole.FontRole,
                    Qt.ItemDataRole.TextAlignmentRole,
                ],
            )
        return True

    def clear_cell_style(self, row: int, column: int) -> bool:
        key = (row, column)
        if key in self._cell_styles:
            del self._cell_styles[key]
            if row < len(self._df) and column < len(self._df.columns):
                index = self.index(row, column)
                self.dataChanged.emit(
                    index,
                    index,
                    [
                        Qt.ItemDataRole.BackgroundRole,
                        Qt.ItemDataRole.ForegroundRole,
                        Qt.ItemDataRole.FontRole,
                        Qt.ItemDataRole.TextAlignmentRole,
                    ],
                )
            return True
        return False

    def commit_edits(self, app_state=None) -> None:
        if not self._edit_buffer or app_state is None:
            self._edit_buffer.clear()
            return

        # Group edits by column to apply them efficiently
        edits_by_col: Dict[str, List[Tuple[int, Any]]] = {}
        for (r, c), val in self._edit_buffer.items():
            col_name = self._df.columns[c]
            if col_name not in edits_by_col:
                edits_by_col[col_name] = []
            edits_by_col[col_name].append((r, val))

        # Apply edits using Polars operations
        try:
            df = self._df
            for col_name, edits in edits_by_col.items():
                # Create a series with the updated values
                col_data = df[col_name].to_list()
                for r, val in edits:
                    if 0 <= r < len(col_data):
                        col_data[r] = val
                # Update the dataframe with the modified column
                df = df.with_columns(pl.Series(col_name, col_data))
            self._replace_dataframe(df)
        except Exception:
            pass  # Silent failure - edits not applied

        self._edit_buffer.clear()

    def get_dataframe(self) -> pl.DataFrame:
        return self._df

    def get_column_names(self) -> List[str]:
        return list(self._df.columns)

    def get_schema(self) -> Dict[str, str]:
        return {col: str(dtype) for col, dtype in self._df.schema.items()}

    def get_cell_value(self, row: int, col: int) -> Any:
        if row < len(self._df) and col < len(self._df.columns):
            try:
                return self._df[row, col]
            except Exception:
                return None
        return None

    @property
    def dataframe(self) -> pl.DataFrame:
        return self._df
