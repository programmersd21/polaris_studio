from __future__ import annotations

from typing import Optional

import polars as pl


class CsvHandler:
    @staticmethod
    def read(
        path: str,
        delimiter: str = ",",
        has_header: bool = True,
        encoding: str = "utf-8",
        skip_rows: int = 0,
        infer_schema_length: Optional[int] = 10000,
    ) -> pl.DataFrame:
        return pl.read_csv(
            path,
            separator=delimiter,
            has_header=has_header,
            encoding=encoding,
            skip_rows=skip_rows,
            infer_schema_length=infer_schema_length,
        )

    @staticmethod
    def write(
        df: pl.DataFrame,
        path: str,
        delimiter: str = ",",
        include_header: bool = True,
    ) -> None:
        df.write_csv(path, separator=delimiter, include_header=include_header)
