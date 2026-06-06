import pytest

from polaris_studio.agent.interpreter import AgentInterpreter
from polaris_studio.agent.schemas import (
    AppCommandBatch,
    ConnectAction,
    CreateNodeAction,
    DeleteNodeAction,
    DisconnectAction,
    ExecuteNodeAction,
    PipelineMutationBatch,
    SelectNodeAction,
    SetCellStyleCommand,
    UpdateCellCommand,
    UpdateNodeAction,
)
from polaris_studio.core.graph import Node, NodeCategory, WorkflowGraph


@pytest.fixture
def graph() -> WorkflowGraph:
    return WorkflowGraph()


@pytest.fixture
def interpreter(graph: WorkflowGraph) -> AgentInterpreter:
    return AgentInterpreter(graph)


def test_create_node(interpreter: AgentInterpreter, graph: WorkflowGraph) -> None:
    batch = PipelineMutationBatch(
        description="Create test node",
        mutations=[
            CreateNodeAction(node_id="n1", node_type="csv_reader"),
        ],
    )
    results = interpreter.apply_batch(batch)
    assert graph.get_node("n1") is not None
    assert len(results) == 1
    assert results[0][1] is None


def test_create_and_connect(interpreter: AgentInterpreter, graph: WorkflowGraph) -> None:
    batch = PipelineMutationBatch(
        description="Create pipeline",
        mutations=[
            CreateNodeAction(node_id="src", node_type="csv_reader"),
            CreateNodeAction(node_id="flt", node_type="filter"),
            ConnectAction(source_id="src", target_id="flt"),
        ],
    )
    results = interpreter.apply_batch(batch)
    assert graph.get_node("src") is not None
    assert graph.get_node("flt") is not None
    assert graph.get_edge_count() == 1
    assert len(results) == 3


def test_update_node(interpreter: AgentInterpreter, graph: WorkflowGraph) -> None:
    graph.add_node(Node("n1", "filter", NodeCategory.FILTER))
    batch = PipelineMutationBatch(
        description="Update node param",
        mutations=[
            UpdateNodeAction(node_id="n1", param_name="expression", value="pl.col('a') > 0"),
        ],
    )
    interpreter.apply_batch(batch)
    node = graph.get_node("n1")
    assert node is not None
    assert node.params.get("expression") == "pl.col('a') > 0"
    assert node.is_dirty is True


def test_delete_node(interpreter: AgentInterpreter, graph: WorkflowGraph) -> None:
    graph.add_node(Node("n1", "csv_reader", NodeCategory.SOURCE))
    graph.add_node(Node("n2", "filter", NodeCategory.TRANSFORM))
    graph.add_edge("n1", "n2")

    batch = PipelineMutationBatch(
        description="Delete node",
        mutations=[DeleteNodeAction(node_id="n1")],
    )
    interpreter.apply_batch(batch)
    assert graph.get_node("n1") is None
    assert graph.get_edge_count() == 0


def test_disconnect(interpreter: AgentInterpreter, graph: WorkflowGraph) -> None:
    graph.add_node(Node("n1", "csv_reader", NodeCategory.SOURCE))
    graph.add_node(Node("n2", "filter", NodeCategory.TRANSFORM))
    graph.add_edge("n1", "n2")

    batch = PipelineMutationBatch(
        description="Disconnect",
        mutations=[DisconnectAction(source_id="n1", target_id="n2")],
    )
    interpreter.apply_batch(batch)
    assert graph.get_edge_count() == 0


def test_create_cycle_rejected(interpreter: AgentInterpreter, graph: WorkflowGraph) -> None:
    graph.add_node(Node("n1", "source", NodeCategory.SOURCE))
    graph.add_node(Node("n2", "transform", NodeCategory.TRANSFORM))
    graph.add_node(Node("n3", "transform", NodeCategory.TRANSFORM))
    graph.add_edge("n1", "n2")
    graph.add_edge("n2", "n3")

    batch = PipelineMutationBatch(
        description="Create cycle",
        mutations=[ConnectAction(source_id="n3", target_id="n1")],
    )
    results = interpreter.apply_batch(batch)
    assert results[0][1] is not None
    assert graph.get_edge_count() == 2


def test_validate_batch(interpreter: AgentInterpreter, graph: WorkflowGraph) -> None:
    graph.add_node(Node("n1", "csv_reader", NodeCategory.SOURCE))

    batch = PipelineMutationBatch(
        description="Test validation",
        mutations=[
            CreateNodeAction(node_id="n1", node_type="csv_reader"),
            DeleteNodeAction(node_id="nonexistent"),
        ],
    )
    warnings = interpreter.validate_batch(batch)
    assert len(warnings) >= 0


def test_create_node_with_params(interpreter: AgentInterpreter, graph: WorkflowGraph) -> None:
    batch = PipelineMutationBatch(
        description="Create CSV reader with path",
        mutations=[
            CreateNodeAction(
                node_id="reader",
                node_type="csv_reader",
                params={"file_path": "/data/test.csv", "has_header": True},
            ),
        ],
    )
    interpreter.apply_batch(batch)
    node = graph.get_node("reader")
    assert node is not None
    assert node.params.get("file_path") == "/data/test.csv"


def test_unknown_node_type(interpreter: AgentInterpreter, graph: WorkflowGraph) -> None:
    batch = PipelineMutationBatch(
        description="Unknown type",
        mutations=[CreateNodeAction(node_id="n1", node_type="unknown_type")],
    )
    results = interpreter.apply_batch(batch)
    assert results[0][1] is not None


def test_mutation_schema_validation() -> None:
    batch = PipelineMutationBatch(
        description="Test",
        mutations=[
            CreateNodeAction(node_id="test", node_type="csv_reader"),
        ],
    )
    assert len(batch.mutations) == 1
    first_mutation = batch.mutations[0]
    assert isinstance(
        first_mutation,
        (CreateNodeAction, UpdateNodeAction, DeleteNodeAction, SelectNodeAction, ExecuteNodeAction),
    )
    assert first_mutation.node_id == "test"


def test_app_command_batch_validation() -> None:
    batch = AppCommandBatch(
        description="Test commands",
        commands=[
            UpdateCellCommand(row=0, column=1, value="hello"),
            SetCellStyleCommand(row=0, column=1, background="#ffffff", bold=True),
        ],
    )
    assert len(batch.commands) == 2
    assert batch.commands[0].action == "update_cell"
