"""Smoke test for the new features: SQL Query, DB Readers, AI column clean, import shortcuts."""

import pytest

from polaris_studio.core.engine import Engine, ExecutionError
from polaris_studio.core.graph import Node, NodeCategory, WorkflowGraph
from polaris_studio.core.node_registry import NODE_REGISTRY


def test_new_nodes_registered() -> None:
    for nt in ("sql_query", "sqlite_reader", "duckdb_reader", "postgres_reader"):
        assert nt in NODE_REGISTRY


def test_new_nodes_have_correct_category() -> None:
    assert NODE_REGISTRY["sql_query"].category == "Transform"
    for nt in ("sqlite_reader", "duckdb_reader", "postgres_reader"):
        assert NODE_REGISTRY[nt].category == "Source"


def test_sql_query_with_input() -> None:
    engine = Engine()
    g = WorkflowGraph()
    src = Node(
        "src",
        "manual_entry",
        NodeCategory.SOURCE,
        params={"data": '[{"name":"Alice","salary":60000},{"name":"Bob","salary":40000}]'},
    )
    g.add_node(src)
    sql = Node(
        "sql",
        "sql_query",
        NodeCategory.TRANSFORM,
        params={
            "sql": "SELECT name, salary * 1.1 AS raised FROM data WHERE salary > 45000",
            "table_name": "data",
        },
    )
    g.add_node(sql)
    g.add_edge("src", "sql")
    df = engine.execute(g, "sql")
    assert len(df) == 1
    assert df["name"][0] == "Alice"
    assert abs(df["raised"][0] - 66000.0) < 0.01


def test_sql_query_without_input() -> None:
    engine = Engine()
    g = WorkflowGraph()
    sql = Node(
        "sql",
        "sql_query",
        NodeCategory.TRANSFORM,
        params={"sql": "SELECT 1 AS a, 'hello' AS b", "table_name": "data"},
    )
    g.add_node(sql)
    df = engine.execute(g, "sql")
    assert df["a"][0] == 1
    assert df["b"][0] == "hello"


def test_sql_query_empty_raises() -> None:
    engine = Engine()
    g = WorkflowGraph()
    sql = Node(
        "sql",
        "sql_query",
        NodeCategory.TRANSFORM,
        params={"sql": "", "table_name": "data"},
    )
    g.add_node(sql)
    with pytest.raises(ExecutionError, match="SQL query is empty"):
        engine.execute(g, "sql")


def test_sqlite_reader_dispatch() -> None:
    engine = Engine()
    g = WorkflowGraph()
    node = Node(
        "s",
        "sqlite_reader",
        NodeCategory.SOURCE,
        params={"file_path": "", "query": "SELECT 1"},
    )
    g.add_node(node)
    with pytest.raises(ExecutionError, match="file_path and query are required"):
        engine.execute(g, "s")


def test_duckdb_reader_in_memory() -> None:
    import duckdb

    conn = duckdb.connect(read_only=False)
    conn.execute("CREATE TABLE test AS SELECT 42 AS n, 'foo' AS s")
    df = conn.execute("SELECT * FROM test").pl()
    conn.close()
    assert df["n"][0] == 42
    assert df["s"][0] == "foo"


def test_duckdb_reader_dispatch() -> None:
    engine = Engine()
    g = WorkflowGraph()
    node = Node(
        "d",
        "duckdb_reader",
        NodeCategory.SOURCE,
        params={"query": "SELECT 1 AS x"},
    )
    g.add_node(node)
    df = engine.execute(g, "d")
    assert df["x"][0] == 1


def test_duckdb_reader_no_query_raises() -> None:
    engine = Engine()
    g = WorkflowGraph()
    node = Node(
        "d",
        "duckdb_reader",
        NodeCategory.SOURCE,
        params={"query": ""},
    )
    g.add_node(node)
    with pytest.raises(ExecutionError, match="query is required"):
        engine.execute(g, "d")


def test_postgres_reader_dispatch() -> None:
    engine = Engine()
    g = WorkflowGraph()
    node = Node(
        "p",
        "postgres_reader",
        NodeCategory.SOURCE,
        params={"connection_string": "", "query": ""},
    )
    g.add_node(node)
    with pytest.raises(ExecutionError, match="connection_string and query are required"):
        engine.execute(g, "p")


def test_ai_column_action_in_grid_view() -> None:
    from polaris_studio.ui.spreadsheet.grid_view import SpreadsheetGrid

    assert hasattr(SpreadsheetGrid, "column_action_requested")
    import inspect

    src = inspect.getsource(SpreadsheetGrid._show_header_context_menu)
    assert "ai_clean" in src


def test_ai_column_handler_in_main_window() -> None:
    import inspect
    from polaris_studio.ui.main_window import PolarisMainWindow

    src = inspect.getsource(PolarisMainWindow._on_column_action)
    assert '"ai_clean"' in src


def test_import_shortcuts_defined() -> None:
    import inspect
    from polaris_studio.ui.main_window import PolarisMainWindow

    src = inspect.getsource(PolarisMainWindow._setup_shortcuts)
    for expected in ("Ctrl+Shift+C", "Ctrl+Shift+X", "Ctrl+Shift+P", "Ctrl+Shift+J"):
        assert expected in src


def test_import_menu_shortcuts_displayed() -> None:
    import inspect
    from polaris_studio.ui.main_window import PolarisMainWindow

    src = inspect.getsource(PolarisMainWindow._setup_menus)
    for expected in ("Ctrl+Shift+C", "Ctrl+Shift+X", "Ctrl+Shift+P", "Ctrl+Shift+J"):
        assert expected in src


def test_new_nodes_in_canvas_menu() -> None:
    import inspect
    from polaris_studio.ui.graph.canvas import GraphCanvas

    src = inspect.getsource(GraphCanvas._show_canvas_context_menu)
    for nt in ("sql_query", "sqlite_reader", "duckdb_reader", "postgres_reader"):
        assert nt in src


def test_duckdb_importable() -> None:
    import duckdb

    assert duckdb.__version__ >= "1.0.0"


def test_sqlalchemy_importable() -> None:
    import sqlalchemy

    assert sqlalchemy.__version__ >= "2.0.0"


def test_import_commands_in_palette() -> None:
    import inspect
    from polaris_studio.ui.main_window import PolarisMainWindow

    src = inspect.getsource(PolarisMainWindow._setup_command_palette)
    for cmd in ("import_csv", "import_xlsx", "import_parquet", "import_json"):
        assert cmd in src
