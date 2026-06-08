# Node Reference

## Introduction

### What Are Nodes?

Nodes are the building blocks of a Polaris Studio pipeline. Each node performs a single data operation -- loading data, transforming it, aggregating it, joining multiple datasets, visualizing it, or exporting results. You connect nodes together to form a **directed acyclic graph (DAG)**, where the output of one node becomes the input of the next.

### How Pipelines Work

- A pipeline starts with one or more **Source** nodes that bring data in (from files, clipboard, or manual entry).
- Data flows through **Transform**, **Aggregate**, **Join**, and **Sort** nodes to clean, reshape, and enrich it.
- **Chart** nodes produce visualizations.
- **Output** nodes display or export the final result.

### Ports

Every node has **input ports** (where data comes in) and **output ports** (where processed data goes out). Most nodes have a single input port named `data_in` and a single output port named `data_out`. Join nodes have two input ports (`data_in_left` and `data_in_right`) because they merge two streams. Source nodes have no input ports -- they are pipeline entry points.

### Parameter Types

| Type | Description |
|---|---|
| `string` | A plain text value |
| `filepath` | A file path, chosen via a file picker |
| `bool` | A true/false toggle |
| `enum` | A dropdown that lets you pick one value from a fixed list |
| `column_single` | A dropdown listing the available columns; pick one |
| `column_multi` | A multi-select that lets you pick several columns |
| `expression` | A Polars expression string (e.g. `pl.col("age") > 18`) |
| `integer` | A whole number |
| `float` | A decimal number |

---

## Source Nodes

Source nodes are entry points -- they have no input ports and produce a single output port (`data_out`).

---

### CSV Reader

Load tabular data from a comma-separated values (CSV) file.

**When to use:** Your data is in CSV format -- the most common interchange format for tabular data.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_out` | Output | A Polars DataFrame loaded from the file |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `file_path` | File Path | `filepath` | Yes | -- | Path to the CSV file on disk |
| `delimiter` | Delimiter | `string` | No | `,` | The character that separates columns (e.g. `,`, `;`, `\t`) |
| `has_header` | Has Header | `bool` | No | `true` | If checked, the first row is treated as column names |
| `encoding` | Encoding | `enum` | No | `utf-8` | File encoding. Options: `utf-8`, `latin-1`, `utf-16` |
| `skip_rows` | Skip Rows | `integer` | No | `0` | Number of rows to skip from the top of the file |

**Example:** Load a semicolon-delimited file without a header, skipping the first 2 rows. Set `delimiter` to `;`, uncheck `has_header`, set `skip_rows` to `2`.

---

### Parquet Reader

Load data from a Parquet file -- a compressed, columnar storage format.

**When to use:** You have large datasets in Parquet format (common in data lakes, Spark, and analytics pipelines).

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_out` | Output | A Polars DataFrame loaded from the file |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `file_path` | File Path | `filepath` | Yes | -- | Path to the Parquet file |

**Example:** Point `file_path` to a `.parquet` file and the reader will infer the schema automatically.

---

### JSON Reader

Load data from a JSON file.

**When to use:** Your data comes from a web API, a NoSQL export, or any JSON-formatted source.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_out` | Output | A Polars DataFrame parsed from the JSON file |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `file_path` | File Path | `filepath` | Yes | -- | Path to the JSON file |
| `infer_schema` | Infer Schema | `bool` | No | `true` | Automatically detect column data types |

**Example:** Load a JSON array of objects. If `infer_schema` is on, numeric fields will be typed as numbers instead of strings.

---

### XLSX Reader

Load data from an Excel (`.xlsx`) workbook.

**When to use:** You receive data as Excel spreadsheets, often from business or finance teams.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_out` | Output | A Polars DataFrame loaded from the sheet |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `file_path` | File Path | `filepath` | Yes | -- | Path to the `.xlsx` file |
| `sheet_name` | Sheet Name | `string` | No | `Sheet1` | Name of the worksheet to read |
| `has_header` | Has Header | `bool` | No | `true` | If checked, the first row is treated as column names |
| `skip_rows` | Skip Rows | `integer` | No | `0` | Number of rows to skip from the top |

**Example:** Read the second sheet of a workbook by setting `sheet_name` to `"Sheet2"`.

---

### SQLite Reader

Load data by running a SQL query against a SQLite database file.

**When to use:** You have a SQLite database (`.db`, `.sqlite`) and want to query tables directly into a DataFrame.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_out` | Output | A Polars DataFrame from the query result |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `file_path` | Database File | `filepath` | Yes | -- | Path to the SQLite database file |
| `query` | Query | `string` | Yes | -- | SQL query to execute (e.g. `SELECT * FROM orders`) |

**Example:** Point `file_path` to `inventory.db` and set `query` to `SELECT * FROM products WHERE price > 10`.

---

### DuckDB Reader

Load data using DuckDB -- query CSV, Parquet, JSON files directly, or run DuckDB SQL.

**When to use:** You want DuckDB's powerful multi-file querying (query CSV files as if they were tables, or use DuckDB-specific SQL features).

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_out` | Output | A Polars DataFrame from the query result |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `query` | Query | `string` | Yes | -- | DuckDB SQL query (e.g. `SELECT * FROM 'data.csv'`) |
| `read_only` | Read Only | `bool` | No | `true` | Open DuckDB in read-only mode |

**Example:** Set `query` to `SELECT region, SUM(amount) FROM 'sales.parquet' GROUP BY region` to aggregate a Parquet file without any import step.

---

### PostgreSQL Reader

Load data by running a SQL query against a PostgreSQL database.

**When to use:** You need to pull data from a remote PostgreSQL server for analysis.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_out` | Output | A Polars DataFrame from the query result |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `connection_string` | Connection String | `string` | Yes | -- | PostgreSQL connection URI (e.g. `postgresql://user:password@localhost:5432/mydb`) |
| `query` | Query | `string` | Yes | -- | SQL query to execute |

**Example:** Connect to a production database with `connection_string` set to `postgresql://analyst:secret@db.example.com:5432/sales` and query `SELECT * FROM monthly_revenue`.

---

### Clipboard Paste

Quickly load data that you copied from another application.

**When to use:** You have a small table in your clipboard (copied from a spreadsheet, a web page, or a text file) and want to bring it into the pipeline without saving it to disk.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_out` | Output | A Polars DataFrame parsed from the clipboard contents |

**Parameters**

None. The node reads whatever is currently in the system clipboard. The data is expected to be tab-separated or comma-separated text.

---

### Manual Entry

Create a small dataset by typing it in directly.

**When to use:** You need to embed a tiny lookup table, a list of constants, or test data directly in the pipeline.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_out` | Output | A Polars DataFrame built from the provided data |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `data` | Data (JSON) | `string` | No | `[]` | Data as a JSON array of objects, e.g. `[{"name":"Alice","age":30}]` |
| `columns` | Column Names | `string` | No | `""` | Comma-separated column names (used when `data` is a flat array) |

**Example:** Set `data` to `[{"city":"London","temp":15},{"city":"Paris","temp":18}]` and leave `columns` blank -- column names are inferred from the JSON keys.

---

### Cross-Tab Reference

Reference the output of another tab in the same Polaris Studio project.

**When to use:** Your pipeline is split across multiple tabs and you want to use the result of one tab as input to a node in another tab.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_out` | Output | The output DataFrame from the referenced tab |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `tab_id` | Tab ID | `string` | Yes | -- | The internal ID of the source tab whose output you want to use |

---

## Transform Nodes

Transform nodes take one input (`data_in`) and produce one output (`data_out`). They reshape, clean, or derive new data from a single dataset.

---

### Filter

Keep only the rows that match a condition.

**When to use:** You need to remove unwanted rows -- e.g. all records where `age < 18`, or where `status` equals `"inactive"`.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The filtered DataFrame (only rows that match the expression) |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `expression` | Filter Expression | `expression` | Yes | -- | A Polars expression that returns a boolean, e.g. `pl.col("age") > 21` |

**Example:** `pl.col("price") > 100` keeps only rows where the `price` column exceeds 100.

---

### Select Columns

Keep only a specified subset of columns.

**When to use:** You have a wide table and only need a few columns for the next stage of the pipeline.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | A DataFrame containing only the selected columns |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `columns` | Columns | `column_multi` | Yes | -- | The columns to retain |

---

### Add Column

Create a new column whose value is the result of a Polars expression.

**When to use:** Derive new data from existing columns -- e.g. compute a `total = price * quantity` column or extract a year from a date.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The original DataFrame with the new column appended |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `column_name` | Column Name | `string` | Yes | -- | The name of the new column |
| `expression` | Expression | `expression` | Yes | -- | A Polars expression, e.g. `pl.col("price") * pl.col("quantity")` |

**Example:** Set `column_name` to `"total"` and `expression` to `pl.col("price") * pl.col("qty")`.

---

### Rename Columns

Change the names of one or more columns at once.

**When to use:** Source data has cryptic or inconsistent column names and you want to standardize them.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The same DataFrame with renamed columns |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `mappings` | Rename Mappings | `string` | No | `[]` | A JSON array of `{"old": "...", "new": "..."}` objects |

**Example:** `[{"old":"fn","new":"first_name"},{"old":"ln","new":"last_name"}]`

---

### Drop Columns

Remove one or more columns from the dataset.

**When to use:** You want to discard sensitive, redundant, or irrelevant columns.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The DataFrame with the specified columns removed |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `columns` | Columns to Drop | `column_multi` | Yes | -- | The columns to remove |

---

### Cast Column

Change the data type of a column (e.g. string to integer, float to date).

**When to use:** A column is stored with the wrong type -- maybe a numeric column was imported as text, or you need to convert a string to a date for date-based filtering.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The DataFrame with the column cast to the new type |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `column` | Column | `column_single` | Yes | -- | The column to cast |
| `target_type` | Target Type | `enum` | No | `Utf8` | The target data type. Options: `Int32`, `Int64`, `Float32`, `Float64`, `Utf8` (string), `Boolean`, `Date`, `Datetime` |

**Example:** Cast a string column `"birth_date"` to `Date` by selecting the column and setting `target_type` to `Date`.

---

### Fill Nulls

Replace null (missing) values in a column with a known value or computed statistic.

**When to use:** Your dataset has missing values that need to be filled before analysis or export.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The DataFrame with nulls in the specified column filled |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `column` | Column | `column_single` | Yes | -- | The column to fill |
| `strategy` | Strategy | `enum` | No | `literal` | How to fill: `literal` (use a provided value), `forward` (carry the last non-null forward), `backward` (use the next non-null), `mean` (column mean), `median` (column median) |
| `value` | Fill Value | `string` | No | `""` | The literal value to use when `strategy` is `literal` |

**Example:** Fill missing values in the `"salary"` column with the column mean by setting `strategy` to `mean`.

---

### String Operation

Apply a string transformation to a text column.

**When to use:** Clean or extract text data -- strip whitespace, change case, replace substrings, split on a delimiter, or extract regex matches.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The DataFrame with the transformed column |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `column` | Column | `column_single` | Yes | -- | The text column to operate on |
| `operation` | Operation | `enum` | No | `strip` | Operation to apply. Options: `strip` (remove leading/trailing whitespace), `upper` (convert to uppercase), `lower` (convert to lowercase), `replace` (replace occurrences of a substring), `split` (split into a list), `extract_regex` (extract a regex capture group) |
| `param` | Parameter | `string` | No | `""` | Extra argument used by some operations: for `replace` it is the search-and-replace pattern; for `split` it is the delimiter; for `extract_regex` it is the regex pattern |

**Example:** To extract the domain from email addresses, set `operation` to `extract_regex` and `param` to `"@(.+)"`.

---

### Date Parse

Parse a string column into a Date or Datetime column.

**When to use:** Date values were imported as plain text (e.g. `"2024-01-15"`) and need to be converted to proper temporal types so you can sort, filter, or extract date parts.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The DataFrame with the column parsed to a temporal type |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `column` | Column | `column_single` | Yes | -- | The string column to parse |
| `format` | Format String | `string` | No | `%Y-%m-%d` | The strptime format string. Common patterns: `%Y-%m-%d`, `%d/%m/%Y`, `%Y-%m-%d %H:%M:%S` |
| `target_type` | Target Type | `enum` | No | `Datetime` | The output type. Options: `Date`, `Datetime` |

**Example:** Parse `"01/15/2024"` by setting `format` to `"%m/%d/%Y"` and `target_type` to `Date`.

---

### Sample

Select a random subset of rows from the dataset.

**When to use:** You want to work with a smaller subset of a large dataset for exploration, testing, or prototyping.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | A DataFrame containing the sampled rows |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `n` | Number of Rows | `integer` | No | `100` | How many rows to sample |
| `seed` | Random Seed | `integer` | No | `42` | Seed for the random number generator (set for reproducible results) |
| `with_replacement` | With Replacement | `bool` | No | `false` | If checked, the same row may appear more than once in the sample |

---

### Slice / Limit

Extract a contiguous block of rows by position.

**When to use:** You need the first N rows, or a specific range of rows (e.g. rows 50-149).

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | A DataFrame with only the sliced rows |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `offset` | Offset | `integer` | No | `0` | The zero-based index of the first row to include |
| `length` | Length | `integer` | No | `100` | How many rows to include after the offset |

**Example:** To get rows 10 through 59, set `offset` to `10` and `length` to `50`.

---

### Deduplicate

Remove duplicate rows from the dataset.

**When to use:** Your data contains repeated records that you want to collapse into unique entries.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The DataFrame with duplicates removed |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `columns` | Column Subset | `column_multi` | No | (all columns) | Only consider these columns when determining duplicates. Leave empty to check all columns. |
| `keep` | Keep Strategy | `enum` | No | `first` | Which duplicate to keep. Options: `first` (keep the first occurrence), `last` (keep the last occurrence), `none` (remove all rows that have duplicates) |

**Example:** To keep only the first occurrence per `"email"` address, select `email` in `columns` and leave `keep` as `first`.

---

### Unpivot

Melt columns into rows (also called "gather" or "melt").

**When to use:** You have a wide table with many similar columns that you want to transform into a long, narrow format suitable for analysis or plotting.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The unpivoted (melted) DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `id_vars` | ID Variables | `column_multi` | Yes | -- | Columns to keep as identifier variables (they stay in place) |
| `value_vars` | Value Variables | `column_multi` | Yes | -- | Columns to unpivot -- they will be collapsed into a `variable` column and a `value` column |

**Example:** If you have sales data with columns `"month"`, `"product_a"`, `"product_b"`, set `id_vars` to `month` and `value_vars` to both product columns to get a long table with one row per product-month.

---

### Explode

Expand list or struct columns so that each element becomes its own row.

**When to use:** A column contains nested data (lists or structs) and you need to flatten it -- e.g. a column of tags `["a","b","c"]` should become three rows.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The exploded DataFrame (one row per element of the exploded column) |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `column` | Column | `column_single` | Yes | -- | The list or struct column to explode |

**Example:** If a column `"items"` contains lists, after explosion each list element gets its own row while other column values are duplicated.

---

### SQL Query

Run a SQL query against the input DataFrame using Polars built-in SQL context.

**When to use:** You are comfortable with SQL and want to filter, join, aggregate, or transform data using familiar syntax instead of the visual node graph.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame (optional) |
| `data_out` | Output | The result of the SQL query |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `sql` | SQL Query | `string` | Yes | -- | The SQL query to execute. Reference the input table using the name set in `table_name`. |
| `table_name` | Table Name | `string` | No | `data` | The name to register the input DataFrame as in the SQL context. |

**Example:** If the input is a DataFrame with columns `name` and `salary`, set `sql` to `SELECT name, salary * 1.1 AS raised FROM data WHERE salary > 50000`. The node will execute this query using Polars SQLContext.

---

## Aggregate Nodes

Aggregate nodes take one input (`data_in`) and produce one output (`data_out`). They summarize or roll up data, reducing many rows into fewer grouped results.

---

### Group By + Aggregate

Group rows by one or more columns and compute aggregate statistics (sum, mean, count, min, max, etc.) for each group.

**When to use:** You need per-group summaries -- total sales by region, average score by class, count of orders per customer, etc.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | A grouped and aggregated DataFrame (one row per group) |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `keys` | Group By Columns | `column_multi` | Yes | -- | One or more columns to group by |
| `aggregations` | Aggregations | `string` | No | `[]` | A JSON array of aggregation definitions. Each entry is `{"column": "...", "function": "...", "alias": "..."}`. Supported functions: `sum`, `mean`, `median`, `min`, `max`, `std`, `var`, `count`, `first`, `last`, `n_unique` |

**Example:** To get total sales per region: set `keys` to `region` and `aggregations` to `[{"column":"sales","function":"sum","alias":"total_sales"}]`.

---

### Rolling Window

Compute rolling (moving) aggregates over a window of rows, optionally partitioned and ordered.

**When to use:** You need moving averages, rolling sums, or any sliding-window calculation on time-series data.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | A DataFrame with the rolling aggregate column appended |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `partition_by` | Partition By | `column_multi` | No | (none) | Columns that define independent groups (like "group by" for the window) |
| `order_by` | Order By | `column_single` | Yes | -- | Column that determines the order of rows within each partition (usually a date or index) |
| `window_size` | Window Size | `integer` | No | `3` | Number of rows in the sliding window |
| `function` | Function | `enum` | No | `mean` | The aggregation to compute over the window. Options: `mean`, `sum`, `min`, `max`, `count`, `std` |

**Example:** A 7-day moving average of `"revenue"`: set `order_by` to `date`, `window_size` to `7`, and `function` to `mean`.

---

### Pivot Table

Create a cross-tabulation (pivot) that reshapes long data into a wide summary matrix.

**When to use:** You want a spreadsheet-style summary table -- for example, sales figures with products as rows and quarters as columns.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The pivoted (wide) DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `rows` | Row Fields | `column_multi` | Yes | -- | Columns whose unique values become the row index |
| `columns` | Column Fields | `column_multi` | Yes | -- | Columns whose unique values become column headers |
| `values` | Value Fields | `column_multi` | Yes | -- | Columns whose values are aggregated into the cells |
| `aggregation` | Aggregation | `enum` | No | `sum` | How to combine values when multiple rows fall into the same cell. Options: `sum`, `mean`, `count`, `min`, `max`, `std` |

**Example:** Rows = `"product"`, columns = `"quarter"`, values = `"revenue"`, aggregation = `sum` produces a table where each product is a row, each quarter is a column, and cells contain total revenue.

---

## Join Nodes

Join nodes combine two datasets based on matching keys. They have **two input ports** (`data_in_left` and `data_in_right`) and one output port (`data_out`). The left input comes from the left-side connection in the UI; the right input from the right-side connection.

---

### Inner Join

Keep only rows where the key exists in **both** datasets.

**When to use:** You want only records that have a match in both tables -- e.g. customers who have placed at least one order.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in_left` | Input | The left DataFrame |
| `data_in_right` | Input | The right DataFrame |
| `data_out` | Output | The joined DataFrame (only matching rows) |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `left_key` | Left Key | `column_single` | Yes | -- | The join column from the left dataset |
| `right_key` | Right Key | `column_single` | Yes | -- | The join column from the right dataset |

---

### Left Join

Keep all rows from the left dataset, and add columns from the right where keys match. Non-matching rows get nulls for right-side columns.

**When to use:** The left table is your primary dataset and you want to enrich it with additional attributes from a lookup table.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in_left` | Input | The left DataFrame (all rows are preserved) |
| `data_in_right` | Input | The right DataFrame |
| `data_out` | Output | The joined DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `left_key` | Left Key | `column_single` | Yes | -- | The join column from the left dataset |
| `right_key` | Right Key | `column_single` | Yes | -- | The join column from the right dataset |

---

### Right Join

Keep all rows from the right dataset, and add columns from the left where keys match. The mirror of a left join.

**When to use:** The right table is your primary dataset.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in_left` | Input | The left DataFrame |
| `data_in_right` | Input | The right DataFrame (all rows are preserved) |
| `data_out` | Output | The joined DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `left_key` | Left Key | `column_single` | Yes | -- | The join column from the left dataset |
| `right_key` | Right Key | `column_single` | Yes | -- | The join column from the right dataset |

---

### Full Join

Keep all rows from **both** datasets. Where keys match, rows are combined; where they don't, missing values become null.

**When to use:** You need a complete picture -- every record from both tables, with as much matching as possible.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in_left` | Input | The left DataFrame |
| `data_in_right` | Input | The right DataFrame |
| `data_out` | Output | The full outer joined DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `left_key` | Left Key | `column_single` | Yes | -- | The join column from the left dataset |
| `right_key` | Right Key | `column_single` | Yes | -- | The join column from the right dataset |

---

### Cross Join

Produce the Cartesian product of the two datasets -- every row from the left matched with every row from the right.

**When to use:** You want all possible combinations, such as generating a calendar from a list of dates and a list of products.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in_left` | Input | The left DataFrame |
| `data_in_right` | Input | The right DataFrame |
| `data_out` | Output | The cross-joined DataFrame |

**Parameters**

None. A cross join does not use a key -- every row pairs with every other row.

---

### Anti Join

Keep rows from the left dataset that have **no match** in the right dataset.

**When to use:** Find records that exist in one table but not another -- e.g. customers who never ordered, or products with no sales.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in_left` | Input | The left DataFrame |
| `data_in_right` | Input | The right DataFrame |
| `data_out` | Output | Only rows from the left table that have no match on the right |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `left_key` | Left Key | `column_single` | Yes | -- | The join column from the left dataset |
| `right_key` | Right Key | `column_single` | Yes | -- | The join column from the right dataset |

---

## Sort Nodes

---

### Sort

Reorder rows by one or more columns.

**When to use:** You need the dataset arranged in a specific order -- ascending, descending, or with nulls at the end.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |
| `data_out` | Output | The sorted DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `columns` | Sort Columns | `column_multi` | Yes | -- | Columns to sort by (the order matters -- first column is the primary sort) |
| `ascending` | Ascending | `bool` | No | `true` | If checked, sort ascending (A-Z, smallest to largest); uncheck for descending |
| `nulls_last` | Nulls Last | `bool` | No | `true` | If checked, null values are placed at the end; uncheck to put them first |

**Example:** Sort by `"department"` ascending, then by `"salary"` descending. Select both columns (in that order), check `ascending`, then click the sort icon next to `"salary"` to toggle it to descending.

---

## Chart Nodes

Chart nodes visualize data. They take one input (`data_in`) and produce no data output -- they render a chart in the Polaris Studio UI. All chart nodes support an optional `title` parameter for the chart title.

---

### Bar Chart

Create a bar chart with categories on the x-axis and numeric values on the y-axis.

**When to use:** Comparing quantities across discrete categories -- sales by product, population by country, etc.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `x_column` | X Column | `column_single` | Yes | -- | The categorical column for the x-axis |
| `y_column` | Y Column | `column_multi` | Yes | -- | The numeric column(s) for the bar heights |
| `color_column` | Color Column | `column_single` | No | (none) | An optional categorical column that subdivides bars by color |
| `title` | Chart Title | `string` | No | `""` | Title displayed above the chart |

**Example:** X = `"product"`, Y = `"revenue"` shows a bar for each product's revenue.

---

### Line Chart

Create a line chart, typically used to show trends over a continuous axis like time.

**When to use:** Visualizing trends over time, sequences, or any ordered continuous variable.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `x_column` | X Column | `column_single` | Yes | -- | The column for the x-axis (often a date) |
| `y_column` | Y Column | `column_multi` | Yes | -- | The numeric column(s) to plot as lines |
| `color_column` | Color Column | `column_single` | No | (none) | An optional categorical column that splits data into separate colored lines |
| `title` | Chart Title | `string` | No | `""` | Title displayed above the chart |

**Example:** X = `"date"`, Y = `"temperature"` with a `color_column` of `"city"` draws one line per city.

---

### Scatter Chart

Create a scatter plot of two numeric variables.

**When to use:** Exploring relationships, correlations, or clusters between two numeric columns.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `x_column` | X Column | `column_single` | Yes | -- | The column for the x-axis |
| `y_column` | Y Column | `column_single` | Yes | -- | The column for the y-axis |
| `size_column` | Size Column | `column_single` | No | (none) | An optional numeric column that controls the size of each point |
| `color_column` | Color Column | `column_single` | No | (none) | An optional column that controls point color |
| `title` | Chart Title | `string` | No | `""` | Title displayed above the chart |

**Example:** X = `"age"`, Y = `"income"`, sized by `"purchases"`, colored by `"region"`.

---

### Histogram

Create a histogram showing the distribution of a numeric column.

**When to use:** Understanding the shape, spread, and central tendency of a numeric variable.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `column` | Column | `column_single` | Yes | -- | The numeric column to bin and count |
| `bins` | Bins | `integer` | No | `20` | Number of equally spaced bins |
| `title` | Chart Title | `string` | No | `""` | Title displayed above the chart |

**Example:** Column = `"age"`, bins = `30` shows the age distribution across 30 buckets.

---

### Box Chart

Create a box plot showing the distribution of one or more numeric columns.

**When to use:** Comparing distributions across groups -- you can see median, quartiles, outliers, and spread at a glance.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `columns` | Columns | `column_multi` | Yes | -- | The numeric column(s) to plot as box plots |
| `group_by` | Group By | `column_single` | No | (none) | An optional categorical column to split the data into side-by-side boxes |
| `title` | Chart Title | `string` | No | `""` | Title displayed above the chart |

**Example:** Columns = `"salary"`, group_by = `"department"` shows one box per department.

---

### Heatmap

Create a color-coded matrix of two categorical dimensions and an aggregated numeric value.

**When to use:** Revealing patterns across two categorical dimensions -- confusion matrices, correlation matrices, or any grid of aggregated values.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `x_column` | X Column | `column_single` | Yes | -- | The column for x-axis categories |
| `y_column` | Y Column | `column_single` | Yes | -- | The column for y-axis categories |
| `value_column` | Value Column | `column_single` | Yes | -- | The numeric column to aggregate and color |
| `aggregation` | Aggregation | `enum` | No | `mean` | How to aggregate values for each cell. Options: `mean`, `sum`, `count`, `min`, `max` |
| `title` | Chart Title | `string` | No | `""` | Title displayed above the chart |

**Example:** X = `"product_category"`, Y = `"region"`, value = `"sales"`, aggregation = `sum`.

---

## Output Nodes

Output nodes take one input (`data_in`) and produce no output ports. They are terminal nodes that either display data in the UI or write it to disk.

---

### Table View

Display the incoming data as an interactive table in the Polaris Studio UI.

**When to use:** You want to inspect the results of a pipeline stage -- scroll through rows, sort by columns, and check values.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |

**Parameters**

None.

---

### Export CSV

Write the data to a CSV file on disk.

**When to use:** You need to save processed data in a universally readable format for sharing or downstream use.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `file_path` | File Path | `filepath` | Yes | -- | Path where the CSV file will be written |
| `delimiter` | Delimiter | `string` | No | `,` | The column separator character |
| `include_header` | Include Header | `bool` | No | `true` | If checked, column names are written as the first row |

---

### Export Parquet

Write the data to a Parquet file on disk.

**When to use:** You need efficient, compressed, columnar storage for large datasets or downstream analytics tools.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `file_path` | File Path | `filepath` | Yes | -- | Path where the Parquet file will be written |
| `compression` | Compression | `enum` | No | `snappy` | Compression codec. Options: `snappy` (fast, good compression), `zstd` (better compression ratio), `lz4` (very fast), `uncompressed` |

---

### Export JSON

Write the data to a JSON file on disk.

**When to use:** You need to export data in a format consumable by web APIs, JavaScript applications, or document databases.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `file_path` | File Path | `filepath` | Yes | -- | Path where the JSON file will be written |
| `orient` | Orientation | `enum` | No | `records` | JSON layout: `records` (array of objects), `values` (array of arrays), `series` (column-oriented dictionary) |

---

### Export XLSX

Write the data to an Excel (`.xlsx`) workbook on disk.

**When to use:** Your stakeholders expect data in Excel format, or you need to include the output in a spreadsheet report.

**Ports**

| Port | Direction | Type |
|---|---|---|
| `data_in` | Input | A DataFrame |

**Parameters**

| Name | Label | Type | Required | Default | Description |
|---|---|---|---|---|---|
| `file_path` | File Path | `filepath` | Yes | -- | Path where the Excel file will be written |
| `sheet_name` | Sheet Name | `string` | No | `Sheet1` | The name of the worksheet in the workbook |
