from __future__ import annotations

from typing import Literal

import polars as pl


class ParquetHandler:
    @staticmethod
    def read(path: str) -> pl.DataFrame:
        return pl.read_parquet(path)

    @staticmethod
    def write(
        df: pl.DataFrame,
        path: str,
        compression: Literal["snappy", "uncompressed", "lz4", "zstd"] = "snappy",
    ) -> None:
        df.write_parquet(path, compression=compression)
