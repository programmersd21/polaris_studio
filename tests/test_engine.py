import pytest

from polaris_studio.core.engine import Engine
from polaris_studio.core.graph import Node, NodeCategory, WorkflowGraph


@pytest.fixture
def engine() -> Engine:
    return Engine()


@pytest.fixture
def sample_graph() -> WorkflowGraph:
    g = WorkflowGraph()
    src = Node(
        "src",
        "manual_entry",
        NodeCategory.SOURCE,
        params={"data": '[{"a": 1, "b": "x"}, {"a": 2, "b": "y"}, {"a": 3, "b": "z"}]'},
    )
    g.add_node(src)
    return g


def test_execute_source(engine: Engine, sample_graph: WorkflowGraph) -> None:
    df = engine.execute(sample_graph, "src")
    assert len(df) == 3
    assert "a" in df.columns
    assert "b" in df.columns


def test_execute_filter(engine: Engine) -> None:
    g = WorkflowGraph()
    src = Node(
        "src",
        "manual_entry",
        NodeCategory.SOURCE,
        params={"data": '[{"a": 1}, {"a": 2}, {"a": 3}]'},
    )
    g.add_node(src)

    flt = Node("flt", "filter", NodeCategory.FILTER, params={"expression": "pl.col('a') > 1"})
    g.add_node(flt)
    g.add_edge("src", "flt")

    df = engine.execute(g, "flt")
    assert len(df) == 2
    assert df["a"].to_list() == [2, 3]


def test_execute_add_column(engine: Engine) -> None:
    g = WorkflowGraph()
    src = Node("src", "manual_entry", NodeCategory.SOURCE, params={"data": '[{"a": 1}, {"a": 2}]'})
    g.add_node(src)

    add = Node(
        "add",
        "add_column",
        NodeCategory.TRANSFORM,
        params={"column_name": "b", "expression": "pl.col('a') * 2"},
    )
    g.add_node(add)
    g.add_edge("src", "add")

    df = engine.execute(g, "add")
    assert "b" in df.columns
    assert df["b"].to_list() == [2, 4]


def test_pipeline_execution(engine: Engine) -> None:
    g = WorkflowGraph()
    src = Node(
        "src",
        "manual_entry",
        NodeCategory.SOURCE,
        params={
            "data": '[{"a": 1, "b": "x"}, {"a": 2, "b": "y"}, {"a": 3, "b": "z"}, {"a": 4, "b": "w"}]'
        },
    )
    g.add_node(src)

    flt = Node("flt", "filter", NodeCategory.FILTER, params={"expression": "pl.col('a') > 2"})
    g.add_node(flt)
    g.add_edge("src", "flt")

    add = Node(
        "add",
        "add_column",
        NodeCategory.TRANSFORM,
        params={"column_name": "c", "expression": "pl.col('a') * 10"},
    )
    g.add_node(add)
    g.add_edge("flt", "add")

    sort = Node("sort", "sort", NodeCategory.SORT, params={"columns": ["a"], "ascending": False})
    g.add_node(sort)
    g.add_edge("add", "sort")

    df = engine.execute(g, "sort")
    assert len(df) == 2
    assert df["c"].to_list() == [40, 30]


def test_cache(engine: Engine) -> None:
    g = WorkflowGraph()
    src = Node("src", "manual_entry", NodeCategory.SOURCE, params={"data": '[{"a": 1}, {"a": 2}]'})
    g.add_node(src)

    flt = Node("flt", "filter", NodeCategory.FILTER, params={"expression": "pl.col('a') > 1"})
    g.add_node(flt)
    g.add_edge("src", "flt")

    engine.execute(g, "flt")
    assert "src" in engine._cache
    assert "flt" in engine._cache


def test_dirty_cache_invalidation(engine: Engine) -> None:
    g = WorkflowGraph()
    src = Node("src", "manual_entry", NodeCategory.SOURCE, params={"data": '[{"a": 1}, {"a": 2}]'})
    g.add_node(src)

    flt = Node("flt", "filter", NodeCategory.FILTER, params={"expression": "pl.col('a') > 1"})
    g.add_node(flt)
    g.add_edge("src", "flt")

    engine.execute(g, "flt")
    assert "src" in engine._cache and "flt" in engine._cache

    g.mark_dirty("flt")
    engine.execute(g, "flt")
    assert "flt" in engine._cache


def test_select_columns(engine: Engine) -> None:
    g = WorkflowGraph()
    src = Node(
        "src",
        "manual_entry",
        NodeCategory.SOURCE,
        params={"data": '[{"a": 1, "b": "x", "c": 3.0}]'},
    )
    g.add_node(src)
    sel = Node("sel", "select_columns", NodeCategory.TRANSFORM, params={"columns": ["a", "c"]})
    g.add_node(sel)
    g.add_edge("src", "sel")

    df = engine.execute(g, "sel")
    assert df.columns == ["a", "c"]


def test_group_by_agg(engine: Engine) -> None:
    g = WorkflowGraph()
    src = Node(
        "src",
        "manual_entry",
        NodeCategory.SOURCE,
        params={
            "data": '[{"cat": "a", "val": 10}, {"cat": "a", "val": 20}, {"cat": "b", "val": 30}]'
        },
    )
    g.add_node(src)
    group = Node(
        "grp",
        "group_by_agg",
        NodeCategory.AGGREGATE,
        params={
            "keys": ["cat"],
            "aggregations": '[{"column": "val", "function": "sum", "alias": "total"}]',
        },
    )
    g.add_node(group)
    g.add_edge("src", "grp")

    df = engine.execute(g, "grp")
    assert len(df) == 2
    assert df["total"].to_list() == [30, 30]


def test_execute_all(engine: Engine) -> None:
    g = WorkflowGraph()
    src = Node("src", "manual_entry", NodeCategory.SOURCE, params={"data": '[{"a": 1}]'})
    g.add_node(src)
    results = engine.execute_all(g)
    assert len(results) == 1
    assert results[0][1] is None


def test_unknown_node_type(engine: Engine) -> None:
    g = WorkflowGraph()
    node = Node("bad", "nonexistent_type", NodeCategory.TRANSFORM)
    g.add_node(node)
    with pytest.raises(Exception):
        engine.execute(g, "bad")
