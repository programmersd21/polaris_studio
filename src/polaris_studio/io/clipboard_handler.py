from __future__ import annotations

from typing import Any, List, Optional

import polars as pl
from PySide6.QtWidgets import QApplication


class ClipboardHandler:
    @staticmethod
    def copy_dataframe(df: pl.DataFrame) -> None:
        lines: List[str] = []
        lines.append("\t".join(df.columns))
        for row in df.iter_rows():
            lines.append("\t".join(str(v) if v is not None else "" for v in row))
        text = "\n".join(lines)

        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    @staticmethod
    def copy_selection(df: pl.DataFrame, rows: List[int], cols: List[int]) -> None:
        lines: List[str] = []
        col_names = [df.columns[c] for c in cols]
        lines.append("\t".join(col_names))
        for r in rows:
            vals = []
            for c in cols:
                v = df[r, c]
                vals.append(str(v) if v is not None else "")
            lines.append("\t".join(vals))
        text = "\n".join(lines)

        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    @staticmethod
    def paste_as_dataframe() -> Optional[pl.DataFrame]:
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text or not text.strip():
            return None

        lines = text.strip().split("\n")
        if len(lines) < 2:
            return None

        header = [c.strip() for c in lines[0].split("\t")]
        data: List[List[Any]] = []
        for line in lines[1:]:
            if not line.strip():
                continue
            vals: List[Any] = [v.strip() if v.strip() else None for v in line.split("\t")]
            while len(vals) < len(header):
                vals.append(None)
            data.append(vals[: len(header)])

        return pl.DataFrame(data, schema=header, orient="row")

    @staticmethod
    def paste_into_selection(
        df: pl.DataFrame,
        start_row: int,
        start_col: int,
    ) -> pl.DataFrame:
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text or not text.strip():
            return df

        lines = text.strip().split("\n")
        rows_data = [line.split("\t") for line in lines if line.strip()]
        if not rows_data:
            return df

        result = df.clone()
        for i, row_vals in enumerate(rows_data):
            for j, val in enumerate(row_vals):
                r = start_row + i
                c = start_col + j
                if r < len(result) and c < len(result.columns):
                    result[r, c] = val if val.strip() else None
        return result
