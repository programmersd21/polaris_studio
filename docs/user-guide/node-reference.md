# Node Reference

## Source Nodes

### CSV Reader
Load tabular data from CSV files.
- **file_path**: Path to CSV file
- **delimiter**: Column separator (default: comma)
- **has_header**: First row contains column names
- **encoding**: File encoding (utf-8, latin-1, utf-16)
- **skip_rows**: Rows to skip before header

### Parquet Reader
Load data from Apache Parquet files.
- **file_path**: Path to Parquet file

### JSON Reader
Load data from JSON files.
- **file_path**: Path to JSON file
- **infer_schema**: Auto-detect column types

### XLSX Reader
Load data from Excel files.
- **file_path**: Path to XLSX file
- **sheet_name**: Sheet to read
- **has_header**: First row as column names

### Clipboard Paste
Read tabular data from system clipboard (TSV format, Excel-compatible).

## Transform Nodes

### Filter
Filter rows by condition. Supports Polars expressions.
- **expression**: e.g., `pl.col('profit') > 1000`

### Select Columns
Keep only specified columns. Multi-select from upstream schema.

### Add Column
Create a new column from an expression.
- **column_name**: Name for the new column
- **expression**: Polars expression

### Rename Columns
Rename one or more columns.
- **mappings**: JSON list of `{"old": "...", "new": "..."}`

### Drop Columns
Remove specified columns.

### Cast Column
Change column data type.
- **column**: Column to cast
- **target_type**: Int32, Int64, Float32, Float64, Utf8, Boolean, Date, Datetime

### Fill Null
Fill null values in a column.
- **strategy**: literal, forward, backward, mean, median

### Sort
Sort rows by specified columns.
- **columns**: Sort keys
- **ascending**: Sort direction
- **nulls_last**: Put null values at end

## Aggregate Nodes

### Group By + Aggregate
Group rows and compute aggregates.
- **keys**: Columns to group by
- **aggregations**: JSON list of column, function, alias

### Rolling Window
Compute rolling window statistics.
- **partition_by**: Optional partition columns
- **order_by**: Order column
- **window_size**: Window size in rows
- **function**: mean, sum, min, max, count, std

### Pivot Table
Create a pivot table with visual field builder.

## Join Nodes

- **Inner Join**: Keep matching rows from both sides
- **Left Join**: Keep all left rows, match from right
- **Right Join**: Keep all right rows, match from left
- **Full Join**: Keep all rows from both sides
- **Cross Join**: Cartesian product
- **Anti Join**: Keep rows from left with no match in right

## Chart Nodes

- **Bar Chart**: Categorical x, numeric y
- **Line Chart**: Continuous x, numeric y
- **Scatter Chart**: Numeric x vs y
- **Histogram**: Distribution of a numeric column
- **Box Chart**: Statistical distribution
- **Heatmap**: 2D aggregation matrix

## Output Nodes

- **Table View**: Display in bottom panel
- **Export CSV**: Write to CSV file
- **Export Parquet**: Write to Parquet file
- **Export JSON**: Write to JSON file
- **Export XLSX**: Write to Excel file
