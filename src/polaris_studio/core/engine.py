from __future__ import annotations

import ast
import json
import operator
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

import polars as pl

from polaris_studio.core.graph import Node, WorkflowGraph


class ExecutionError(Exception):
    pass


class Engine:
    def __init__(self) -> None:
        self._cache: Dict[str, pl.DataFrame] = {}
        self._safe_names = {
            "pl": pl,
            "col": pl.col,
            "lit": pl.lit,
            "Int32": pl.Int32,
            "Int64": pl.Int64,
            "Float32": pl.Float32,
            "Float64": pl.Float64,
            "Utf8": pl.Utf8,
            "Boolean": pl.Boolean,
            "Date": pl.Date,
            "Datetime": pl.Datetime,
        }

    def execute(self, graph: WorkflowGraph, node_id: str) -> pl.DataFrame:
        order = graph.topological_order()
        if node_id not in order:
            raise ExecutionError(f"Node {node_id} not found or unreachable")

        idx = order.index(node_id)
        for i in range(idx + 1):
            nid = order[i]
            node = graph.get_node(nid)
            if node is None:
                continue
            if not node.is_dirty and nid in self._cache:
                continue
            try:
                result = self._execute_node(graph, node)
                self._cache[nid] = result
                node.is_dirty = False
                node.error = None
            except Exception as e:
                node.error = str(e)
                raise ExecutionError(f"Node {nid} failed: {e}") from e

        return self._cache[node_id]

    def execute_all(self, graph: WorkflowGraph) -> List[Tuple[str, Optional[str]]]:
        """Execute all nodes in topological order, collecting all errors without stopping.

        Returns list of (node_id, error_message) tuples where error_message is None if successful.
        """
        results: List[Tuple[str, Optional[str]]] = []
        failed_nodes: set[str] = set()

        for nid in graph.topological_order():
            # Skip nodes whose dependencies failed
            node = graph.get_node(nid)
            if node is None:
                continue

            # Check if this node has dependencies on failed nodes
            skip_due_to_dependency = False
            for edge in graph.get_edges():
                if edge.target_id == nid and edge.source_id in failed_nodes:
                    skip_due_to_dependency = True
                    break

            if skip_due_to_dependency:
                results.append((nid, "Skipped due to failed dependency"))
                continue

            try:
                self.execute(graph, nid)
                results.append((nid, None))
            except ExecutionError as e:
                results.append((nid, str(e)))
                failed_nodes.add(nid)

        return results

    def get_cached(self, node_id: str) -> Optional[pl.DataFrame]:
        return self._cache.get(node_id)

    def clear_cache(self, node_id: Optional[str] = None) -> None:
        if node_id:
            self._cache.pop(node_id, None)
        else:
            self._cache.clear()

    def _execute_node(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        dispatch = {
            "csv_reader": self._exec_csv_reader,
            "parquet_reader": self._exec_parquet_reader,
            "json_reader": self._exec_json_reader,
            "xlsx_reader": self._exec_xlsx_reader,
            "clipboard_paste": self._exec_clipboard_paste,
            "manual_entry": self._exec_manual_entry,
            "cross_tab_ref": self._exec_cross_tab_ref,
            "filter": self._exec_filter,
            "select_columns": self._exec_select_columns,
            "add_column": self._exec_add_column,
            "rename_columns": self._exec_rename_columns,
            "drop_columns": self._exec_drop_columns,
            "cast_column": self._exec_cast_column,
            "fill_null": self._exec_fill_null,
            "string_ops": self._exec_string_ops,
            "date_parse": self._exec_date_parse,
            "sample": self._exec_sample,
            "slice": self._exec_slice,
            "deduplicate": self._exec_deduplicate,
            "unpivot": self._exec_unpivot,
            "explode": self._exec_explode,
            "group_by_agg": self._exec_group_by_agg,
            "rolling_window": self._exec_rolling_window,
            "pivot_table": self._exec_pivot_table,
            "inner_join": self._exec_join("inner"),
            "left_join": self._exec_join("left"),
            "right_join": self._exec_join("right"),
            "full_join": self._exec_join("full"),
            "cross_join": self._exec_cross_join,
            "anti_join": self._exec_anti_join,
            "sort": self._exec_sort,
            "bar_chart": self._exec_bar_chart,
            "line_chart": self._exec_line_chart,
            "scatter_chart": self._exec_scatter_chart,
            "histogram": self._exec_histogram,
            "box_chart": self._exec_box_chart,
            "heatmap": self._exec_heatmap,
            "table_output": self._exec_noop,
            "export_csv": self._exec_export_csv,
            "export_parquet": self._exec_export_parquet,
            "export_json": self._exec_export_json,
            "export_xlsx": self._exec_export_xlsx,
        }
        handler = dispatch.get(node.node_type)
        if handler is None:
            raise ExecutionError(f"Unknown node type: {node.node_type}")
        return handler(graph, node)

    def _get_input_df(
        self, graph: WorkflowGraph, node: Node, port: str = "data_in"
    ) -> pl.DataFrame:
        for e in graph.get_edges():
            if e.target_id == node.node_id and e.target_port == port:
                src = graph.get_node(e.source_id)
                if src:
                    return self._cache.get(src.node_id, pl.DataFrame())
        raise ExecutionError(f"No input for {node.node_id} on port {port}")

    def _exec_csv_reader(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        path = node.params.get("file_path", "")
        delimiter = node.params.get("delimiter", ",")
        has_header = node.params.get("has_header", True)
        encoding = node.params.get("encoding", "utf-8")
        skip_rows = node.params.get("skip_rows", 0)
        return pl.read_csv(
            path,
            separator=delimiter,
            has_header=has_header,
            encoding=encoding,
            skip_rows=skip_rows,
            infer_schema_length=10000,
        )

    def _exec_parquet_reader(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        return pl.read_parquet(node.params["file_path"])

    def _exec_json_reader(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        return pl.read_json(
            node.params["file_path"],
            infer_schema_length=10000 if node.params.get("infer_schema", True) else 0,
        )

    def _exec_xlsx_reader(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        from polaris_studio.io.xlsx_handler import XlsxHandler

        return XlsxHandler.read(
            node.params["file_path"],
            sheet_name=node.params.get("sheet_name", 0),
            has_header=node.params.get("has_header", True),
            skip_rows=node.params.get("skip_rows", 0),
        )

    def _exec_clipboard_paste(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        from polaris_studio.io.clipboard_handler import ClipboardHandler

        result = ClipboardHandler.paste_as_dataframe()
        if result is None:
            raise ExecutionError("Clipboard is empty or contains no tabular data")
        return result

    def _exec_manual_entry(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        import json

        data_str = node.params.get("data", "[]")
        columns_str = node.params.get("columns", "")
        data = json.loads(data_str)
        if not data:
            return pl.DataFrame()
        df = pl.DataFrame(data)
        if columns_str:
            cols = [c.strip() for c in columns_str.split(",")]
            if len(cols) == len(df.columns):
                df.columns = cols
        return df

    def _exec_cross_tab_ref(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        raise ExecutionError("Cross-tab reference not yet wired to workspace")

    def _exec_filter(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        expr = node.params.get("expression", "")
        if not expr:
            return df
        try:
            compiled = self._parse_polars_expr(expr)
            return df.filter(compiled)
        except ExecutionError:
            raise
        except Exception as e:
            raise ExecutionError(f"Filter expression failed: {e}") from e

    def _exec_select_columns(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        cols = node.params.get("columns", [])
        if isinstance(cols, str):
            cols = [c.strip() for c in cols.split(",")]
        if not cols:
            return df
        return df.select(cols)

    def _exec_add_column(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        name = node.params.get("column_name", "new_column")
        expr = node.params.get("expression", "pl.lit(None)")
        try:
            compiled = self._parse_polars_expr(expr)
            return df.with_columns(compiled.alias(name))
        except ExecutionError:
            raise
        except Exception as e:
            raise ExecutionError(f"Add column expression failed: {e}") from e

    def _exec_rename_columns(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        mappings = node.params.get("mappings", "[]")
        if isinstance(mappings, str):
            mappings = json.loads(mappings)
        mapping = {m["old"]: m["new"] for m in mappings}
        return df.rename(mapping)

    def _exec_drop_columns(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        cols = node.params.get("columns", [])
        if isinstance(cols, str):
            cols = [c.strip() for c in cols.split(",")]
        return df.drop(cols)

    def _exec_cast_column(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        col_name = node.params.get("column", "")
        target = node.params.get("target_type", "Utf8")
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
        dtype = dtype_map.get(target, pl.Utf8)
        return df.with_columns(df[col_name].cast(dtype).alias(col_name))

    def _exec_fill_null(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        col_name = node.params.get("column", "")
        strategy = node.params.get("strategy", "literal")
        value = node.params.get("value", None)
        if strategy == "literal":
            return df.with_columns(df[col_name].fill_null(pl.lit(value)))
        elif strategy == "forward":
            return df.with_columns(df[col_name].forward_fill())
        elif strategy == "backward":
            return df.with_columns(df[col_name].backward_fill())
        elif strategy == "mean":
            mean_val = df[col_name].mean()
            return df.with_columns(df[col_name].fill_null(mean_val))
        elif strategy == "median":
            med_val = df[col_name].median()
            return df.with_columns(df[col_name].fill_null(med_val))
        return df

    def _exec_string_ops(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        col_name = node.params.get("column", "")
        op = node.params.get("operation", "strip")
        param = node.params.get("param", "")
        col_expr = df[col_name]
        if op == "strip":
            new_col = col_expr.str.strip_chars()
        elif op == "upper":
            new_col = col_expr.str.to_uppercase()
        elif op == "lower":
            new_col = col_expr.str.to_lowercase()
        elif op == "replace":
            parts = param.split("|")
            old = parts[0] if parts else ""
            new = parts[1] if len(parts) > 1 else ""
            new_col = col_expr.str.replace(old, new)
        elif op == "split":
            new_col = col_expr.str.split(param if param else ",")
        elif op == "extract_regex":
            new_col = col_expr.str.extract(param)
        else:
            new_col = col_expr
        return df.with_columns(new_col.alias(col_name))

    def _exec_date_parse(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        col_name = node.params.get("column", "")
        fmt = node.params.get("format", "%Y-%m-%d")
        target = node.params.get("target_type", "Datetime")
        parsed = df[col_name].str.strptime(pl.Datetime, fmt)
        if target == "Date":
            parsed = parsed.cast(pl.Date)
        return df.with_columns(parsed.alias(col_name))

    def _exec_sample(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        n = node.params.get("n", 100)
        seed = node.params.get("seed", 42)
        replacement = node.params.get("with_replacement", False)
        return df.sample(n=n, seed=seed, with_replacement=replacement)

    def _exec_slice(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        offset = node.params.get("offset", 0)
        length = node.params.get("length", 100)
        return df.slice(offset, length)

    def _exec_deduplicate(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        cols = node.params.get("columns", None)
        keep = node.params.get("keep", "first")
        if not cols:
            return df.unique(keep=keep)
        return df.unique(subset=cols, keep=keep)

    def _exec_unpivot(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        id_vars = node.params.get("id_vars", [])
        value_vars = node.params.get("value_vars", [])
        return df.unpivot(index=id_vars, on=value_vars)

    def _exec_explode(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        col_name = node.params.get("column", "")
        return df.explode(col_name)

    def _exec_group_by_agg(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        keys = node.params.get("keys", [])
        aggs_str = node.params.get("aggregations", "[]")
        if isinstance(aggs_str, str):
            aggs = json.loads(aggs_str)
        else:
            aggs = aggs_str
        agg_exprs = []
        for a in aggs:
            col_name = a.get("column", "")
            func = a.get("function", "sum")
            alias = a.get("alias", f"{func}_{col_name}")
            if func == "sum":
                agg_exprs.append(pl.col(col_name).sum().alias(alias))
            elif func == "mean":
                agg_exprs.append(pl.col(col_name).mean().alias(alias))
            elif func == "count":
                agg_exprs.append(pl.col(col_name).count().alias(alias))
            elif func == "min":
                agg_exprs.append(pl.col(col_name).min().alias(alias))
            elif func == "max":
                agg_exprs.append(pl.col(col_name).max().alias(alias))
            elif func == "std":
                agg_exprs.append(pl.col(col_name).std().alias(alias))
            elif func == "first":
                agg_exprs.append(pl.col(col_name).first().alias(alias))
            elif func == "last":
                agg_exprs.append(pl.col(col_name).last().alias(alias))
            else:
                agg_exprs.append(pl.col(col_name).sum().alias(alias))
        return df.group_by(keys).agg(agg_exprs)

    def _exec_rolling_window(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        partition_by = node.params.get("partition_by", None)
        order_by = node.params.get("order_by", "")
        window_size = node.params.get("window_size", 3)
        func = node.params.get("function", "mean")
        if partition_by:
            df = df.sort(partition_by + [order_by])
        else:
            df = df.sort(order_by)
        col_name = df.columns[-1]
        if func == "mean":
            new_col = pl.col(col_name).rolling_mean(window_size)
        elif func == "sum":
            new_col = pl.col(col_name).rolling_sum(window_size)
        elif func == "min":
            new_col = pl.col(col_name).rolling_min(window_size)
        elif func == "max":
            new_col = pl.col(col_name).rolling_max(window_size)
        elif func == "std":
            new_col = pl.col(col_name).rolling_std(window_size)
        else:
            new_col = pl.col(col_name).rolling_mean(window_size)
        if partition_by:
            return df.with_columns(new_col.over(partition_by).alias(f"{func}_{window_size}"))
        return df.with_columns(new_col.alias(f"{func}_{window_size}"))

    def _exec_pivot_table(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        rows = node.params.get("rows", [])
        cols = node.params.get("columns", [])
        values = node.params.get("values", [])
        agg = node.params.get("aggregation", "sum")

        if not rows or not cols or not values:
            raise ExecutionError("Pivot table requires rows, columns, and values parameters")

        val_col = values[0] if values else df.columns[-1]
        col_field = cols[0] if cols else None

        if not col_field:
            raise ExecutionError("Pivot table requires at least one column field")

        # Map aggregation string to valid Polars aggregation function names
        valid_agg_map = {
            "sum": "sum",
            "mean": "mean",
            "count": "count",
            "min": "min",
            "max": "max",
            "std": "std",
        }
        agg_func = valid_agg_map.get(agg, "sum")

        # Use pivot with the aggregation function
        try:
            pivoted = df.pivot(
                on=col_field,
                index=rows,
                values=val_col,
                aggregate_function=agg_func,  # type: ignore[arg-type]
            )
            return pivoted
        except Exception as e:
            raise ExecutionError(f"Pivot operation failed: {e}") from e

    def _exec_join(
        self, how: Literal["inner", "left", "right", "full"]
    ) -> Callable[[WorkflowGraph, Node], pl.DataFrame]:
        def _inner(graph: WorkflowGraph, node: Node) -> pl.DataFrame:
            left_df = self._get_input_df(graph, node, "data_in_left")
            right_df = self._get_input_df(graph, node, "data_in_right")
            left_key = node.params.get("left_key", "")
            right_key = node.params.get("right_key", "")
            return left_df.join(right_df, left_on=left_key, right_on=right_key, how=how)

        return _inner

    def _exec_cross_join(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        left_df = self._get_input_df(graph, node, "data_in_left")
        right_df = self._get_input_df(graph, node, "data_in_right")
        return left_df.join(right_df, how="cross")

    def _exec_anti_join(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        left_df = self._get_input_df(graph, node, "data_in_left")
        right_df = self._get_input_df(graph, node, "data_in_right")
        left_key = node.params.get("left_key", "")
        right_key = node.params.get("right_key", "")
        return left_df.join(right_df, left_on=left_key, right_on=right_key, how="anti")

    def _exec_sort(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        cols = node.params.get("columns", [])
        asc = node.params.get("ascending", True)
        nulls_last = node.params.get("nulls_last", True)
        return df.sort(cols, descending=not asc, nulls_last=nulls_last)

    def _exec_bar_chart(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        x_col = node.params.get("x_column", "")
        y_col = node.params.get("y_column", "")
        if x_col and x_col not in df.columns:
            raise ExecutionError(f"Bar chart: column '{x_col}' not found")
        if y_col and y_col not in df.columns:
            raise ExecutionError(f"Bar chart: column '{y_col}' not found")
        return df

    def _exec_line_chart(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        x_col = node.params.get("x_column", "")
        y_col = node.params.get("y_column", "")
        if x_col and x_col not in df.columns:
            raise ExecutionError(f"Line chart: column '{x_col}' not found")
        if y_col and y_col not in df.columns:
            raise ExecutionError(f"Line chart: column '{y_col}' not found")
        return df

    def _exec_scatter_chart(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        x_col = node.params.get("x_column", "")
        y_col = node.params.get("y_column", "")
        if x_col and x_col not in df.columns:
            raise ExecutionError(f"Scatter chart: column '{x_col}' not found")
        if y_col and y_col not in df.columns:
            raise ExecutionError(f"Scatter chart: column '{y_col}' not found")
        return df

    def _exec_histogram(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        col = node.params.get("column", "")
        if col and col not in df.columns:
            raise ExecutionError(f"Histogram: column '{col}' not found")
        return df

    def _exec_box_chart(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        cols = node.params.get("columns", [])
        for c in cols:
            if c not in df.columns:
                raise ExecutionError(f"Box chart: column '{c}' not found")
        return df

    def _exec_heatmap(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        x_col = node.params.get("x_column", "")
        y_col = node.params.get("y_column", "")
        val_col = node.params.get("value_column", "")
        if x_col and x_col not in df.columns:
            raise ExecutionError(f"Heatmap: column '{x_col}' not found")
        if y_col and y_col not in df.columns:
            raise ExecutionError(f"Heatmap: column '{y_col}' not found")
        if val_col and val_col not in df.columns:
            raise ExecutionError(f"Heatmap: column '{val_col}' not found")
        return df

    def _exec_export_csv(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        path = node.params.get("file_path", "")
        if not path:
            raise ExecutionError("Export CSV: no file path specified")
        delimiter = node.params.get("delimiter", ",")
        include_header = node.params.get("include_header", True)
        df.write_csv(path, separator=delimiter, include_header=include_header)
        return df

    def _exec_export_parquet(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        path = node.params.get("file_path", "")
        if not path:
            raise ExecutionError("Export Parquet: no file path specified")
        compression = node.params.get("compression", "snappy")
        if compression == "uncompressed":
            compression = None
        df.write_parquet(path, compression=compression)
        return df

    def _exec_export_json(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        path = node.params.get("file_path", "")
        if not path:
            raise ExecutionError("Export JSON: no file path specified")
        orient = node.params.get("orient", "records")
        if orient == "records":
            df.write_ndjson(path)
        else:
            lines = df.write_json()
            with open(path, "w", encoding="utf-8") as f:
                f.write(lines)
        return df

    def _exec_export_xlsx(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        df = self._get_input_df(graph, node)
        path = node.params.get("file_path", "")
        if not path:
            raise ExecutionError("Export XLSX: no file path specified")
        sheet_name = node.params.get("sheet_name", "Sheet1")
        from polaris_studio.io.xlsx_handler import XlsxHandler

        XlsxHandler.write(df, path, sheet_name=sheet_name)
        return df

    def _exec_noop(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
        try:
            return self._get_input_df(graph, node)
        except ExecutionError:
            return pl.DataFrame()

    def _parse_polars_expr(self, expr: str) -> pl.Expr:
        tree = ast.parse(expr, mode="eval")
        value = self._eval_ast(tree.body)
        if not isinstance(value, pl.Expr):
            raise ExecutionError("Expression must evaluate to a Polars expression")
        return value

    def _eval_ast(self, node: ast.AST) -> object:
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            if node.id in self._safe_names:
                return self._safe_names[node.id]
            raise ExecutionError(f"Unknown symbol: {node.id}")

        if isinstance(node, ast.Attribute):
            value = self._eval_ast(node.value)
            if node.attr.startswith("_"):
                raise ExecutionError("Private attributes are not allowed")
            return getattr(value, node.attr)

        if isinstance(node, ast.Call):
            func = self._eval_ast(node.func)
            if not callable(func):
                raise ExecutionError("Expression call target is not callable")
            args = [self._eval_ast(arg) for arg in node.args]
            kwargs = {}
            for kw in node.keywords:
                if kw.arg is None:
                    raise ExecutionError("Keyword unpacking is not allowed")
                kwargs[kw.arg] = self._eval_ast(kw.value)
            return func(*args, **kwargs)

        if isinstance(node, ast.BinOp):
            bin_left: Any = self._eval_ast(node.left)
            bin_right: Any = self._eval_ast(node.right)
            bin_op_map: Dict[type, Callable[[Any, Any], Any]] = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.FloorDiv: operator.floordiv,
                ast.Mod: operator.mod,
                ast.Pow: operator.pow,
                ast.BitAnd: operator.and_,
                ast.BitOr: operator.or_,
            }
            bin_op = bin_op_map.get(type(node.op))
            if bin_op is None:
                raise ExecutionError(f"Operator not allowed: {type(node.op).__name__}")
            return bin_op(bin_left, bin_right)

        if isinstance(node, ast.UnaryOp):
            operand = self._eval_ast(node.operand)
            if isinstance(node.op, ast.Not):
                return ~operand if isinstance(operand, pl.Expr) else operator.not_(operand)
            un_op_map: Dict[type, Callable[[Any], Any]] = {
                ast.UAdd: operator.pos,
                ast.USub: operator.neg,
            }
            un_op = un_op_map.get(type(node.op))
            if un_op is None:
                raise ExecutionError(f"Unary operator not allowed: {type(node.op).__name__}")
            return un_op(operand)

        if isinstance(node, ast.BoolOp):
            values = [self._eval_ast(value) for value in node.values]
            if isinstance(node.op, ast.And):
                bool_result = values[0]
                for value in values[1:]:
                    bool_result = operator.and_(bool_result, value)
                return bool_result
            if isinstance(node.op, ast.Or):
                bool_result = values[0]
                for value in values[1:]:
                    bool_result = operator.or_(bool_result, value)
                return bool_result
            raise ExecutionError(f"Boolean operator not allowed: {type(node.op).__name__}")

        if isinstance(node, ast.Compare):
            cmp_left: Any = self._eval_ast(node.left)
            cmp_result: Any = None
            compare_map: Dict[type, Callable[[Any, Any], Any]] = {
                ast.Eq: operator.eq,
                ast.NotEq: operator.ne,
                ast.Lt: operator.lt,
                ast.LtE: operator.le,
                ast.Gt: operator.gt,
                ast.GtE: operator.ge,
            }
            for op_node, comparator in zip(node.ops, node.comparators, strict=True):
                cmp_op = compare_map.get(type(op_node))
                if cmp_op is None:
                    raise ExecutionError(f"Comparison not allowed: {type(op_node).__name__}")
                cmp_right: Any = self._eval_ast(comparator)
                current = cmp_op(cmp_left, cmp_right)
                cmp_result = current if cmp_result is None else operator.and_(cmp_result, current)
                cmp_left = cmp_right
            if cmp_result is None:
                raise ExecutionError("Empty comparison is not allowed")
            return cmp_result

        if isinstance(node, ast.Tuple):
            return tuple(self._eval_ast(elt) for elt in node.elts)

        if isinstance(node, ast.List):
            return [self._eval_ast(elt) for elt in node.elts]

        if isinstance(node, ast.Dict):
            dict_result: Dict[Any, Any] = {}
            for k, v in zip(node.keys, node.values, strict=True):
                if k is None:
                    raise ExecutionError("Dict unpacking is not allowed")
                dict_result[self._eval_ast(k)] = self._eval_ast(v)
            return dict_result

        raise ExecutionError(f"Unsafe expression node: {type(node).__name__}")
