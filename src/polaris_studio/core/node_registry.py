from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

ParamType = Literal[
    "string",
    "filepath",
    "bool",
    "enum",
    "column_single",
    "column_multi",
    "expression",
    "integer",
    "float",
]


@dataclass
class NodeParamSpec:
    name: str
    label: str
    param_type: ParamType
    default: Any = None
    required: bool = False
    options: Optional[List[str]] = None
    tooltip: str = ""


@dataclass
class NodeTypeSpec:
    node_type: str
    display_name: str
    category: str
    color: str
    description: str
    input_ports: List[str] = field(default_factory=lambda: ["data_in"])
    output_ports: List[str] = field(default_factory=lambda: ["data_out"])
    params: List[NodeParamSpec] = field(default_factory=list)


NODE_REGISTRY: Dict[str, NodeTypeSpec] = {
    "csv_reader": NodeTypeSpec(
        node_type="csv_reader",
        display_name="CSV Reader",
        category="Source",
        color="#1b4332",
        description="Load a CSV file as a data source",
        input_ports=[],
        params=[
            NodeParamSpec(
                "file_path", "File Path", "filepath", required=True, tooltip="Path to the CSV file"
            ),
            NodeParamSpec(
                "delimiter", "Delimiter", "string", ",", tooltip="Column delimiter character"
            ),
            NodeParamSpec(
                "has_header", "Has Header", "bool", True, tooltip="First row contains column names"
            ),
            NodeParamSpec(
                "encoding", "Encoding", "enum", "utf-8", options=["utf-8", "latin-1", "utf-16"]
            ),
            NodeParamSpec(
                "skip_rows", "Skip Rows", "integer", 0, tooltip="Number of rows to skip at the top"
            ),
        ],
    ),
    "parquet_reader": NodeTypeSpec(
        node_type="parquet_reader",
        display_name="Parquet Reader",
        category="Source",
        color="#1b4332",
        description="Load a Parquet file as a data source",
        input_ports=[],
        params=[
            NodeParamSpec(
                "file_path",
                "File Path",
                "filepath",
                required=True,
                tooltip="Path to the Parquet file",
            ),
        ],
    ),
    "json_reader": NodeTypeSpec(
        node_type="json_reader",
        display_name="JSON Reader",
        category="Source",
        color="#1b4332",
        description="Load a JSON file as a data source",
        input_ports=[],
        params=[
            NodeParamSpec(
                "file_path", "File Path", "filepath", required=True, tooltip="Path to the JSON file"
            ),
            NodeParamSpec(
                "infer_schema",
                "Infer Schema",
                "bool",
                True,
                tooltip="Automatically infer column types",
            ),
        ],
    ),
    "xlsx_reader": NodeTypeSpec(
        node_type="xlsx_reader",
        display_name="XLSX Reader",
        category="Source",
        color="#1b4332",
        description="Load an Excel file as a data source",
        input_ports=[],
        params=[
            NodeParamSpec(
                "file_path", "File Path", "filepath", required=True, tooltip="Path to the XLSX file"
            ),
            NodeParamSpec("sheet_name", "Sheet Name", "string", "Sheet1", tooltip="Sheet to read"),
            NodeParamSpec("has_header", "Has Header", "bool", True),
            NodeParamSpec("skip_rows", "Skip Rows", "integer", 0),
        ],
    ),
    "clipboard_paste": NodeTypeSpec(
        node_type="clipboard_paste",
        display_name="Clipboard Paste",
        category="Source",
        color="#1b4332",
        description="Paste data from the system clipboard",
        input_ports=[],
        params=[],
    ),
    "manual_entry": NodeTypeSpec(
        node_type="manual_entry",
        display_name="Manual Entry",
        category="Source",
        color="#1b4332",
        description="Create a small dataset manually",
        input_ports=[],
        params=[
            NodeParamSpec(
                "data", "Data (JSON)", "string", "[]", tooltip="Data as JSON array of objects"
            ),
            NodeParamSpec(
                "columns", "Column Names", "string", "", tooltip="Comma-separated column names"
            ),
        ],
    ),
    "cross_tab_ref": NodeTypeSpec(
        node_type="cross_tab_ref",
        display_name="Cross-Tab Reference",
        category="Source",
        color="#1b4332",
        description="Reference another tab's output",
        input_ports=[],
        params=[
            NodeParamSpec(
                "tab_id", "Tab ID", "string", required=True, tooltip="ID of the source tab"
            ),
        ],
    ),
    "filter": NodeTypeSpec(
        node_type="filter",
        display_name="Filter",
        category="Transform",
        color="#44164f",
        description="Filter rows based on a condition",
        params=[
            NodeParamSpec(
                "expression",
                "Filter Expression",
                "expression",
                required=True,
                tooltip="Filter condition",
            ),
        ],
    ),
    "select_columns": NodeTypeSpec(
        node_type="select_columns",
        display_name="Select Columns",
        category="Transform",
        color="#1d3461",
        description="Select a subset of columns",
        params=[
            NodeParamSpec(
                "columns", "Columns", "column_multi", required=True, tooltip="Columns to keep"
            ),
        ],
    ),
    "add_column": NodeTypeSpec(
        node_type="add_column",
        display_name="Add Column",
        category="Transform",
        color="#1d3461",
        description="Add a computed column",
        params=[
            NodeParamSpec(
                "column_name",
                "Column Name",
                "string",
                required=True,
                tooltip="Name for the new column",
            ),
            NodeParamSpec(
                "expression",
                "Expression",
                "expression",
                required=True,
                tooltip="Expression to compute the column",
            ),
        ],
    ),
    "rename_columns": NodeTypeSpec(
        node_type="rename_columns",
        display_name="Rename Columns",
        category="Transform",
        color="#1d3461",
        description="Rename one or more columns",
        params=[
            NodeParamSpec(
                "mappings",
                "Rename Mappings",
                "string",
                "[]",
                tooltip="JSON list of {old, new} pairs",
            ),
        ],
    ),
    "drop_columns": NodeTypeSpec(
        node_type="drop_columns",
        display_name="Drop Columns",
        category="Transform",
        color="#1d3461",
        description="Remove specified columns",
        params=[
            NodeParamSpec(
                "columns",
                "Columns to Drop",
                "column_multi",
                required=True,
                tooltip="Columns to remove",
            ),
        ],
    ),
    "cast_column": NodeTypeSpec(
        node_type="cast_column",
        display_name="Cast Column",
        category="Transform",
        color="#1d3461",
        description="Change a column's data type",
        params=[
            NodeParamSpec(
                "column", "Column", "column_single", required=True, tooltip="Column to cast"
            ),
            NodeParamSpec(
                "target_type",
                "Target Type",
                "enum",
                "Utf8",
                options=[
                    "Int32",
                    "Int64",
                    "Float32",
                    "Float64",
                    "Utf8",
                    "Boolean",
                    "Date",
                    "Datetime",
                ],
            ),
        ],
    ),
    "fill_null": NodeTypeSpec(
        node_type="fill_null",
        display_name="Fill Nulls",
        category="Transform",
        color="#1d3461",
        description="Fill null values in a column",
        params=[
            NodeParamSpec(
                "column", "Column", "column_single", required=True, tooltip="Column to fill"
            ),
            NodeParamSpec(
                "strategy",
                "Strategy",
                "enum",
                "literal",
                options=["literal", "forward", "backward", "mean", "median"],
            ),
            NodeParamSpec("value", "Fill Value", "string", "", tooltip="Literal value for fill"),
        ],
    ),
    "string_ops": NodeTypeSpec(
        node_type="string_ops",
        display_name="String Operation",
        category="Transform",
        color="#1d3461",
        description="Apply string transformations",
        params=[
            NodeParamSpec("column", "Column", "column_single", required=True),
            NodeParamSpec(
                "operation",
                "Operation",
                "enum",
                "strip",
                options=["strip", "upper", "lower", "replace", "split", "extract_regex"],
            ),
            NodeParamSpec(
                "param", "Parameter", "string", "", tooltip="Additional parameter for the operation"
            ),
        ],
    ),
    "date_parse": NodeTypeSpec(
        node_type="date_parse",
        display_name="Date Parse",
        category="Transform",
        color="#1d3461",
        description="Parse a string column to datetime",
        params=[
            NodeParamSpec("column", "Column", "column_single", required=True),
            NodeParamSpec(
                "format", "Format String", "string", "%Y-%m-%d", tooltip="Date format string"
            ),
            NodeParamSpec(
                "target_type", "Target Type", "enum", "Datetime", options=["Date", "Datetime"]
            ),
        ],
    ),
    "sample": NodeTypeSpec(
        node_type="sample",
        display_name="Sample",
        category="Transform",
        color="#1d3461",
        description="Sample rows from the dataset",
        params=[
            NodeParamSpec("n", "Number of Rows", "integer", 100),
            NodeParamSpec("seed", "Random Seed", "integer", 42),
            NodeParamSpec("with_replacement", "With Replacement", "bool", False),
        ],
    ),
    "slice": NodeTypeSpec(
        node_type="slice",
        display_name="Slice / Limit",
        category="Transform",
        color="#1d3461",
        description="Take a slice of rows",
        params=[
            NodeParamSpec("offset", "Offset", "integer", 0),
            NodeParamSpec("length", "Length", "integer", 100),
        ],
    ),
    "deduplicate": NodeTypeSpec(
        node_type="deduplicate",
        display_name="Deduplicate",
        category="Transform",
        color="#1d3461",
        description="Remove duplicate rows",
        params=[
            NodeParamSpec(
                "columns",
                "Column Subset",
                "column_multi",
                tooltip="Columns to check for duplicates",
            ),
            NodeParamSpec(
                "keep", "Keep Strategy", "enum", "first", options=["first", "last", "none"]
            ),
        ],
    ),
    "unpivot": NodeTypeSpec(
        node_type="unpivot",
        display_name="Unpivot",
        category="Transform",
        color="#1d3461",
        description="Unpivot columns to rows",
        params=[
            NodeParamSpec("id_vars", "ID Variables", "column_multi", required=True),
            NodeParamSpec("value_vars", "Value Variables", "column_multi", required=True),
        ],
    ),
    "explode": NodeTypeSpec(
        node_type="explode",
        display_name="Explode",
        category="Transform",
        color="#1d3461",
        description="Explode list/struct columns",
        params=[
            NodeParamSpec("column", "Column", "column_single", required=True),
        ],
    ),
    "group_by_agg": NodeTypeSpec(
        node_type="group_by_agg",
        display_name="Group By + Aggregate",
        category="Aggregate",
        color="#4a3800",
        description="Group rows and compute aggregates",
        params=[
            NodeParamSpec("keys", "Group By Columns", "column_multi", required=True),
            NodeParamSpec(
                "aggregations",
                "Aggregations",
                "string",
                "[]",
                tooltip="JSON list of {column, function, alias}",
            ),
        ],
    ),
    "rolling_window": NodeTypeSpec(
        node_type="rolling_window",
        display_name="Rolling Window",
        category="Aggregate",
        color="#4a3800",
        description="Compute rolling window aggregates",
        params=[
            NodeParamSpec(
                "partition_by", "Partition By", "column_multi", tooltip="Columns to partition by"
            ),
            NodeParamSpec("order_by", "Order By", "column_single", required=True),
            NodeParamSpec("window_size", "Window Size", "integer", 3),
            NodeParamSpec(
                "function",
                "Function",
                "enum",
                "mean",
                options=["mean", "sum", "min", "max", "count", "std"],
            ),
        ],
    ),
    "pivot_table": NodeTypeSpec(
        node_type="pivot_table",
        display_name="Pivot Table",
        category="Aggregate",
        color="#4a3800",
        description="Create a pivot table",
        params=[
            NodeParamSpec("rows", "Row Fields", "column_multi", required=True),
            NodeParamSpec("columns", "Column Fields", "column_multi", required=True),
            NodeParamSpec("values", "Value Fields", "column_multi", required=True),
            NodeParamSpec(
                "aggregation",
                "Aggregation",
                "enum",
                "sum",
                options=["sum", "mean", "count", "min", "max", "std"],
            ),
        ],
    ),
    "inner_join": NodeTypeSpec(
        node_type="inner_join",
        display_name="Inner Join",
        category="Join",
        color="#003d40",
        description="Inner join two datasets",
        input_ports=["data_in_left", "data_in_right"],
        params=[
            NodeParamSpec("left_key", "Left Key", "column_single", required=True),
            NodeParamSpec("right_key", "Right Key", "column_single", required=True),
        ],
    ),
    "left_join": NodeTypeSpec(
        node_type="left_join",
        display_name="Left Join",
        category="Join",
        color="#003d40",
        description="Left join two datasets",
        input_ports=["data_in_left", "data_in_right"],
        params=[
            NodeParamSpec("left_key", "Left Key", "column_single", required=True),
            NodeParamSpec("right_key", "Right Key", "column_single", required=True),
        ],
    ),
    "right_join": NodeTypeSpec(
        node_type="right_join",
        display_name="Right Join",
        category="Join",
        color="#003d40",
        description="Right join two datasets",
        input_ports=["data_in_left", "data_in_right"],
        params=[
            NodeParamSpec("left_key", "Left Key", "column_single", required=True),
            NodeParamSpec("right_key", "Right Key", "column_single", required=True),
        ],
    ),
    "full_join": NodeTypeSpec(
        node_type="full_join",
        display_name="Full Join",
        category="Join",
        color="#003d40",
        description="Full outer join two datasets",
        input_ports=["data_in_left", "data_in_right"],
        params=[
            NodeParamSpec("left_key", "Left Key", "column_single", required=True),
            NodeParamSpec("right_key", "Right Key", "column_single", required=True),
        ],
    ),
    "cross_join": NodeTypeSpec(
        node_type="cross_join",
        display_name="Cross Join",
        category="Join",
        color="#003d40",
        description="Cross join two datasets",
        input_ports=["data_in_left", "data_in_right"],
        params=[],
    ),
    "anti_join": NodeTypeSpec(
        node_type="anti_join",
        display_name="Anti Join",
        category="Join",
        color="#003d40",
        description="Anti join two datasets",
        input_ports=["data_in_left", "data_in_right"],
        params=[
            NodeParamSpec("left_key", "Left Key", "column_single", required=True),
            NodeParamSpec("right_key", "Right Key", "column_single", required=True),
        ],
    ),
    "sort": NodeTypeSpec(
        node_type="sort",
        display_name="Sort",
        category="Sort",
        color="#1d3461",
        description="Sort rows by specified columns",
        params=[
            NodeParamSpec("columns", "Sort Columns", "column_multi", required=True),
            NodeParamSpec("ascending", "Ascending", "bool", True),
            NodeParamSpec("nulls_last", "Nulls Last", "bool", True),
        ],
    ),
    "bar_chart": NodeTypeSpec(
        node_type="bar_chart",
        display_name="Bar Chart",
        category="Chart",
        color="#1a003d",
        description="Create a bar chart",
        params=[
            NodeParamSpec("x_column", "X Column", "column_single", required=True),
            NodeParamSpec("y_column", "Y Column", "column_multi", required=True),
            NodeParamSpec(
                "color_column", "Color Column", "column_single", tooltip="Optional color grouping"
            ),
            NodeParamSpec("title", "Chart Title", "string", ""),
        ],
    ),
    "line_chart": NodeTypeSpec(
        node_type="line_chart",
        display_name="Line Chart",
        category="Chart",
        color="#1a003d",
        description="Create a line chart",
        params=[
            NodeParamSpec("x_column", "X Column", "column_single", required=True),
            NodeParamSpec("y_column", "Y Column", "column_multi", required=True),
            NodeParamSpec("color_column", "Color Column", "column_single"),
            NodeParamSpec("title", "Chart Title", "string", ""),
        ],
    ),
    "scatter_chart": NodeTypeSpec(
        node_type="scatter_chart",
        display_name="Scatter Chart",
        category="Chart",
        color="#1a003d",
        description="Create a scatter plot",
        params=[
            NodeParamSpec("x_column", "X Column", "column_single", required=True),
            NodeParamSpec("y_column", "Y Column", "column_single", required=True),
            NodeParamSpec("size_column", "Size Column", "column_single"),
            NodeParamSpec("color_column", "Color Column", "column_single"),
            NodeParamSpec("title", "Chart Title", "string", ""),
        ],
    ),
    "histogram": NodeTypeSpec(
        node_type="histogram",
        display_name="Histogram",
        category="Chart",
        color="#1a003d",
        description="Create a histogram",
        params=[
            NodeParamSpec("column", "Column", "column_single", required=True),
            NodeParamSpec("bins", "Bins", "integer", 20),
            NodeParamSpec("title", "Chart Title", "string", ""),
        ],
    ),
    "box_chart": NodeTypeSpec(
        node_type="box_chart",
        display_name="Box Chart",
        category="Chart",
        color="#1a003d",
        description="Create a box plot",
        params=[
            NodeParamSpec("columns", "Columns", "column_multi", required=True),
            NodeParamSpec("group_by", "Group By", "column_single"),
            NodeParamSpec("title", "Chart Title", "string", ""),
        ],
    ),
    "heatmap": NodeTypeSpec(
        node_type="heatmap",
        display_name="Heatmap",
        category="Chart",
        color="#1a003d",
        description="Create a heatmap",
        params=[
            NodeParamSpec("x_column", "X Column", "column_single", required=True),
            NodeParamSpec("y_column", "Y Column", "column_single", required=True),
            NodeParamSpec("value_column", "Value Column", "column_single", required=True),
            NodeParamSpec(
                "aggregation",
                "Aggregation",
                "enum",
                "mean",
                options=["mean", "sum", "count", "min", "max"],
            ),
            NodeParamSpec("title", "Chart Title", "string", ""),
        ],
    ),
    "table_output": NodeTypeSpec(
        node_type="table_output",
        display_name="Table View",
        category="Output",
        color="#3d1a00",
        description="Display output in the table view",
        params=[],
    ),
    "export_csv": NodeTypeSpec(
        node_type="export_csv",
        display_name="Export CSV",
        category="Output",
        color="#3d1a00",
        description="Export data to a CSV file",
        params=[
            NodeParamSpec("file_path", "File Path", "filepath", required=True),
            NodeParamSpec("delimiter", "Delimiter", "string", ","),
            NodeParamSpec("include_header", "Include Header", "bool", True),
        ],
    ),
    "export_parquet": NodeTypeSpec(
        node_type="export_parquet",
        display_name="Export Parquet",
        category="Output",
        color="#3d1a00",
        description="Export data to a Parquet file",
        params=[
            NodeParamSpec("file_path", "File Path", "filepath", required=True),
            NodeParamSpec(
                "compression",
                "Compression",
                "enum",
                "snappy",
                options=["snappy", "zstd", "lz4", "uncompressed"],
            ),
        ],
    ),
    "export_json": NodeTypeSpec(
        node_type="export_json",
        display_name="Export JSON",
        category="Output",
        color="#3d1a00",
        description="Export data to a JSON file",
        params=[
            NodeParamSpec("file_path", "File Path", "filepath", required=True),
            NodeParamSpec(
                "orient", "Orientation", "enum", "records", options=["records", "values", "series"]
            ),
        ],
    ),
    "export_xlsx": NodeTypeSpec(
        node_type="export_xlsx",
        display_name="Export XLSX",
        category="Output",
        color="#3d1a00",
        description="Export data to an Excel file",
        params=[
            NodeParamSpec("file_path", "File Path", "filepath", required=True),
            NodeParamSpec("sheet_name", "Sheet Name", "string", "Sheet1"),
        ],
    ),
}
