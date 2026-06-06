import os
import tempfile

import polars as pl
import pytest

from polaris_studio.io.csv_handler import CsvHandler
from polaris_studio.io.parquet_handler import ParquetHandler


@pytest.fixture
def sample_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [30, 25, 35],
            "salary": [70000.0, 50000.0, 90000.0],
        }
    )


def test_csv_roundtrip(sample_df: pl.DataFrame) -> None:
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name

    try:
        CsvHandler.write(sample_df, path)
        loaded = CsvHandler.read(path)
        assert loaded.shape == sample_df.shape
        assert loaded.columns == sample_df.columns
        assert loaded["name"].to_list() == sample_df["name"].to_list()
        assert loaded["age"].to_list() == sample_df["age"].to_list()
    finally:
        os.unlink(path)


def test_csv_custom_delimiter(sample_df: pl.DataFrame) -> None:
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name

    try:
        CsvHandler.write(sample_df, path, delimiter=";")
        loaded = CsvHandler.read(path, delimiter=";")
        assert loaded.shape == sample_df.shape
    finally:
        os.unlink(path)


def test_csv_no_header(sample_df: pl.DataFrame) -> None:
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name

    try:
        CsvHandler.write(sample_df, path, include_header=False)
        loaded = CsvHandler.read(path, has_header=False)
        assert loaded.shape == sample_df.shape
    finally:
        os.unlink(path)


def test_parquet_roundtrip(sample_df: pl.DataFrame) -> None:
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        path = f.name

    try:
        ParquetHandler.write(sample_df, path)
        loaded = ParquetHandler.read(path)
        assert loaded.shape == sample_df.shape
        assert loaded["name"].to_list() == sample_df["name"].to_list()
    finally:
        os.unlink(path)


def test_parquet_compression(sample_df: pl.DataFrame) -> None:
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        path = f.name

    try:
        ParquetHandler.write(sample_df, path, compression="zstd")
        loaded = ParquetHandler.read(path)
        assert loaded.shape == sample_df.shape
    finally:
        os.unlink(path)


def test_empty_csv() -> None:
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        f.write("col1,col2\n")
        path = f.name

    try:
        loaded = CsvHandler.read(path)
        assert len(loaded) == 0
    finally:
        os.unlink(path)
