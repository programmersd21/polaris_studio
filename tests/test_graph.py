import pytest

from polaris_studio.core.graph import CycleError, Node, NodeCategory, WorkflowGraph


@pytest.fixture
def graph() -> WorkflowGraph:
    return WorkflowGraph()


def test_add_node(graph: WorkflowGraph) -> None:
    node = Node("n1", "csv_reader", NodeCategory.SOURCE)
    graph.add_node(node)
    assert graph.get_node("n1") is node
    assert graph.get_node_count() == 1


def test_remove_node(graph: WorkflowGraph) -> None:
    n1 = Node("n1", "csv_reader", NodeCategory.SOURCE)
    n2 = Node("n2", "filter", NodeCategory.TRANSFORM)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge("n1", "n2")
    graph.remove_node("n1")
    assert graph.get_node("n1") is None
    assert len(graph.get_edges()) == 0


def test_add_edge(graph: WorkflowGraph) -> None:
    n1 = Node("n1", "csv_reader", NodeCategory.SOURCE)
    n2 = Node("n2", "filter", NodeCategory.TRANSFORM)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge("n1", "n2")
    assert graph.get_edge_count() == 1


def test_add_edge_with_ports(graph: WorkflowGraph) -> None:
    n1 = Node("n1", "csv_reader", NodeCategory.SOURCE)
    n2 = Node("n2", "filter", NodeCategory.TRANSFORM)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge("n1", "n2", "data_out", "data_in")
    edge = graph.get_edges()[0]
    assert edge.source_port == "data_out"
    assert edge.target_port == "data_in"


def test_remove_edge_with_ports(graph: WorkflowGraph) -> None:
    n1 = Node("n1", "csv_reader", NodeCategory.SOURCE)
    n2 = Node("n2", "filter", NodeCategory.TRANSFORM)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge("n1", "n2", "data_out", "data_in")
    assert graph.remove_edge("n1", "n2", "data_out", "data_in") is True
    assert graph.get_edge_count() == 0


def test_cycle_detection(graph: WorkflowGraph) -> None:
    n1 = Node("n1", "source", NodeCategory.SOURCE)
    n2 = Node("n2", "transform", NodeCategory.TRANSFORM)
    n3 = Node("n3", "transform", NodeCategory.TRANSFORM)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)
    graph.add_edge("n1", "n2")
    graph.add_edge("n2", "n3")
    with pytest.raises(CycleError):
        graph.add_edge("n3", "n1")


def test_topological_order(graph: WorkflowGraph) -> None:
    n1 = Node("n1", "source", NodeCategory.SOURCE)
    n2 = Node("n2", "transform", NodeCategory.TRANSFORM)
    n3 = Node("n3", "transform", NodeCategory.TRANSFORM)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)
    graph.add_edge("n1", "n2")
    graph.add_edge("n2", "n3")
    order = graph.topological_order()
    assert order.index("n1") < order.index("n2")
    assert order.index("n2") < order.index("n3")


def test_mark_dirty_cascades(graph: WorkflowGraph) -> None:
    n1 = Node("n1", "source", NodeCategory.SOURCE)
    n2 = Node("n2", "transform", NodeCategory.TRANSFORM)
    n3 = Node("n3", "transform", NodeCategory.TRANSFORM)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)
    graph.add_edge("n1", "n2")
    graph.add_edge("n2", "n3")
    n1.is_dirty = False
    n2.is_dirty = False
    n3.is_dirty = False
    graph.mark_dirty("n1")
    assert n1.is_dirty is True
    assert n2.is_dirty is True
    assert n3.is_dirty is True


def test_validate_disconnected_node(graph: WorkflowGraph) -> None:
    n1 = Node("n1", "source", NodeCategory.SOURCE)
    n2 = Node("n2", "source", NodeCategory.SOURCE)
    graph.add_node(n1)
    graph.add_node(n2)
    errors = graph.validate()
    assert len(errors) > 0


def test_remove_edge(graph: WorkflowGraph) -> None:
    n1 = Node("n1", "source", NodeCategory.SOURCE)
    n2 = Node("n2", "filter", NodeCategory.TRANSFORM)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge("n1", "n2")
    assert graph.remove_edge("n1", "n2") is True
    assert graph.get_edge_count() == 0
    assert graph.remove_edge("nonexistent", "n2") is False


def test_upstream_downstream(graph: WorkflowGraph) -> None:
    n1 = Node("n1", "source", NodeCategory.SOURCE)
    n2 = Node("n2", "transform", NodeCategory.TRANSFORM)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge("n1", "n2")
    assert "n1" in graph.get_upstream("n2")
    assert "n2" in graph.get_downstream("n1")


def test_clear(graph: WorkflowGraph) -> None:
    node = Node("n1", "source", NodeCategory.SOURCE)
    graph.add_node(node)
    graph.clear()
    assert graph.get_node_count() == 0
    assert graph.get_edge_count() == 0
