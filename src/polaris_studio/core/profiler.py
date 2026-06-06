from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, List, Tuple

import polars as pl


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    null_count: int
    null_pct: float
    unique_count: int
    unique_pct: float
    min_value: Any | None = None
    max_value: Any | None = None
    mean: float | None = None
    std: float | None = None
    median: float | None = None
    top_5_values: List[Tuple[Any, int]] = field(default_factory=list)
    histogram_bins: List[float] = field(default_factory=list)
    histogram_counts: List[int] = field(default_factory=list)


@dataclass
class DataProfile:
    node_id: str
    row_count: int
    col_count: int
    columns: List[ColumnProfile]
    computed_at: float = 0.0


class DataProfiler:
    @staticmethod
    def profile(df: pl.DataFrame, node_id: str, histogram_bins: int = 20) -> DataProfile:
        computed_at = time.time()
        columns: List[ColumnProfile] = []

        for col_name in df.columns:
            series = df[col_name]
            dtype = str(series.dtype)
            null_count = series.null_count()
            row_count = len(series)
            null_pct = (null_count / row_count * 100) if row_count else 0.0
            unique_count = series.n_unique()
            unique_pct = (unique_count / row_count * 100) if row_count else 0.0

            top_5_values: List[Tuple[Any, int]] = []
            try:
                top_5 = series.value_counts(sort=True).head(5)
                top_5_values = [(row[0], row[1]) for row in top_5.iter_rows()]
            except Exception:
                pass

            min_val: Any = None
            max_val: Any = None
            mean: float | None = None
            std: float | None = None
            median: float | None = None
            hist_bins: List[float] = []
            hist_counts: List[int] = []

            try:
                if series.dtype in (pl.Int32, pl.Int64, pl.Float32, pl.Float64):
                    min_val_any: Any = series.min()
                    max_val_any: Any = series.max()
                    mean_any = series.mean()
                    std_any = series.std()
                    median_any = series.median()
                    if min_val_any is not None and isinstance(min_val_any, (int, float)):
                        min_val = float(min_val_any)
                    if max_val_any is not None and isinstance(max_val_any, (int, float)):
                        max_val = float(max_val_any)
                    if mean_any is not None and isinstance(mean_any, (int, float)):
                        mean = float(mean_any)
                    if std_any is not None and isinstance(std_any, (int, float)):
                        std = float(std_any)
                    if median_any is not None and isinstance(median_any, (int, float)):
                        median = float(median_any)
                    clean = series.drop_nulls()
                    if len(clean) > 1:
                        try:
                            # Create histogram using safe binning approach
                            clean_min_raw = clean.min()
                            clean_max_raw = clean.max()
                            if clean_min_raw is not None and isinstance(
                                clean_min_raw, (int, float)
                            ):
                                min_val_safe = float(clean_min_raw)
                            else:
                                min_val_safe = 0.0
                            if clean_max_raw is not None and isinstance(
                                clean_max_raw, (int, float)
                            ):
                                max_val_safe = float(clean_max_raw)
                            else:
                                max_val_safe = 1.0
                            if min_val_safe < max_val_safe:
                                bin_width = (max_val_safe - min_val_safe) / histogram_bins
                                # Map each value to a bin index
                                binned = series.map_elements(
                                    lambda x: (
                                        int((x - min_val_safe) / bin_width)
                                        if x is not None and bin_width > 0
                                        else 0
                                    ),
                                    return_dtype=pl.Int32,
                                )
                                counts = binned.value_counts(sort=True).sort(
                                    "counts", descending=True
                                )
                                if len(counts) > 0:
                                    hist_bins = [
                                        float(int(r[0]) * bin_width + min_val_safe)
                                        for r in counts.iter_rows()
                                    ]
                                    hist_counts = [int(r[1]) for r in counts.iter_rows()]
                        except Exception:
                            pass
                elif series.dtype == pl.Date:
                    min_val = str(series.min()) if series.min() is not None else None
                    max_val = str(series.max()) if series.max() is not None else None
                elif series.dtype == pl.Datetime:
                    min_val = str(series.min()) if series.min() is not None else None
                    max_val = str(series.max()) if series.max() is not None else None
            except Exception:
                pass

            columns.append(
                ColumnProfile(
                    name=col_name,
                    dtype=dtype,
                    null_count=null_count,
                    null_pct=null_pct,
                    unique_count=unique_count,
                    unique_pct=unique_pct,
                    min_value=min_val,
                    max_value=max_val,
                    mean=mean,
                    std=std,
                    median=median,
                    top_5_values=top_5_values,
                    histogram_bins=hist_bins,
                    histogram_counts=hist_counts,
                )
            )

        return DataProfile(
            node_id=node_id,
            row_count=len(df),
            col_count=len(df.columns),
            columns=columns,
            computed_at=computed_at,
        )
