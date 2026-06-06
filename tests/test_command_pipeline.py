"""Smoke tests for the AI command pipeline.

Verifies the parse → validate → defer-execute → apply flow that keeps
structured payloads out of the chat surface.
"""

from __future__ import annotations

from typing import List

import pytest

from polaris_studio.agent.command_pipeline import (
    CommandContext,
    CommandPipeline,
    ResponseParser,
    ResponseValidator,
)
from polaris_studio.core.graph import Node, WorkflowGraph


@pytest.fixture
def graph() -> WorkflowGraph:
    return WorkflowGraph()


@pytest.fixture
def context(graph: WorkflowGraph) -> CommandContext:
    added: List[Node] = []
    edges: List[tuple[str, str]] = []
    removed: List[str] = []

    def on_added(node: Node) -> None:
        added.append(node)

    def on_edge(src: str, tgt: str) -> None:
        edges.append((src, tgt))

    def on_removed(nid: str) -> None:
        removed.append(nid)

    return CommandContext(
        graph=graph,
        on_node_added=on_added,
        on_edge_added=on_edge,
        on_node_removed=on_removed,
    )


def test_parser_extracts_fenced_payload() -> None:
    parser = ResponseParser()
    text = (
        "Sure, I'll add a filter.\n\n"
        "```json\n"
        '{"type": "action_batch", "batch": {"description": "add filter", '
        '"mutations": [{"action": "create_node", "node_id": "f1", '
        '"node_type": "filter", "params": {"expression": "x > 0"}, '
        '"position_x": 0.0, "position_y": 0.0, "select_after": true}]}}\n'
        "```\n\n"
        "Let me know if you need anything else."
    )
    payload = parser.parse(text)
    assert "batch" in payload
    assert payload.get("type") == "action_batch"


def test_parser_extracts_bare_object() -> None:
    parser = ResponseParser()
    text = (
        '{"action_batch": true, "description": "rename column", '
        '"mutations": [{"action": "rename_column", "old_name": "a", "new_name": "b"}]}'
    )
    payload = parser.parse(text)
    assert payload


def test_validator_returns_none_for_empty_payload() -> None:
    validator = ResponseValidator()
    batch, error = validator.validate({})
    assert batch is None
    assert error is not None


def test_pipeline_defers_execution_until_apply(
    graph: WorkflowGraph, context: CommandContext
) -> None:
    pipeline = CommandPipeline(context)
    text = (
        "Adding a filter node.\n\n"
        "```json\n"
        '{"type": "action_batch", "batch": {"description": "create filter", '
        '"mutations": [{"action": "create_node", "node_id": "f1", '
        '"node_type": "filter", "params": {"expression": "x > 0"}, '
        '"position_x": 100.0, "position_y": 200.0, "select_after": false}]}}\n'
        "```\n"
    )
    result = pipeline.process_response(text)
    assert result.message == "Adding a filter node."
    assert result.batch is not None
    assert result.report is None
    assert graph.get_node_count() == 0

    report = pipeline.apply(result.batch)
    assert report.ok
    assert graph.get_node_count() == 1
    created = graph.get_node("f1")
    assert created is not None
    assert created.node_type == "filter"
    assert created.position == (100.0, 200.0)


def test_pipeline_invalid_payload_returns_empty_message(
    graph: WorkflowGraph, context: CommandContext
) -> None:
    pipeline = CommandPipeline(context)
    text = "Just a friendly reply, no commands here."
    result = pipeline.process_response(text)
    assert result.batch is None
    assert "friendly" in result.message
    assert graph.get_node_count() == 0


def test_pipeline_malformed_json_records_validation_error(
    graph: WorkflowGraph, context: CommandContext
) -> None:
    """The AI may emit JSON that parses but uses wrong field names.

    The pipeline must NOT silently accept it. It must surface a validation
    error so the chat session can self-correct.
    """
    pipeline = CommandPipeline(context)
    text = (
        "Here you go: ```json\n"
        '{"type": "command_batch", "batch": {"description": "Filter Sri Lanka", '
        '"commands": ['
        '{"command": "create_node", "args": {"node_type": "filter", '
        '"node_id": "f1", "properties": {"column": "Country"}}}'
        "]}}\n"
        "```"
    )
    result = pipeline.process_response(text)
    assert result.batch is None
    assert result.validation_error is not None
    assert graph.get_node_count() == 0


def test_pipeline_correct_json_creates_filter(
    graph: WorkflowGraph, context: CommandContext
) -> None:
    """Schema-correct filter JSON should produce a real node."""
    pipeline = CommandPipeline(context)
    text = (
        "Adding a filter: ```json\n"
        '{"type": "action_batch", "batch": {"description": "Filter Sri Lanka", '
        '"mutations": [{"action": "create_node", "node_id": "f1", '
        '"node_type": "filter", '
        '"params": {"expression": "pl.col(\'Country\') == \'Sri Lanka\'"}, '
        '"position_x": 200.0, "position_y": 100.0, "select_after": false}]}}\n'
        "```"
    )
    result = pipeline.process_response(text)
    assert result.batch is not None, f"validation_error was: {result.validation_error}"
    assert result.validation_error is None
    report = pipeline.apply(result.batch)
    assert report.ok
    node = graph.get_node("f1")
    assert node is not None
    assert node.node_type == "filter"
    assert "Country" in node.params.get("expression", "")
    assert "Sri Lanka" in node.params.get("expression", "")


def test_pipeline_rejects_aliased_field_names(
    graph: WorkflowGraph, context: CommandContext
) -> None:
    """The user's exact bug: AI used `command`/`args`/`from_node`/`to_node`.

    With `extra="forbid"` + discriminator, the validator must reject the
    payload outright (no silent fallback to DeleteRowCommand).
    """
    pipeline = CommandPipeline(context)
    text = (
        "Sure, here you go: ```json\n"
        '{"type": "command_batch", "batch": {"description": "Filter Sri Lanka", '
        '"commands": ['
        '{"command": "create_node", "args": {"node_type": "filter", '
        '"node_id": "f1", "properties": {"column": "Country"}}}, '
        '{"command": "connect_nodes", "args": '
        '{"from_node": "csv_reader_1", "to_node": "f1"}}'
        "]}}\n"
        "```"
    )
    result = pipeline.process_response(text)
    assert result.batch is None, f"expected rejection, got: {result.batch}"
    assert result.validation_error is not None
    assert graph.get_node_count() == 0
    commands: list = result.batch.commands if result.batch else []
    delete_row_commands = [c for c in commands if c.action == "delete_row"]
    assert delete_row_commands == []


def test_pipeline_rejects_unknown_action_literal(
    graph: WorkflowGraph, context: CommandContext
) -> None:
    pipeline = CommandPipeline(context)
    text = (
        "```json\n"
        '{"type": "command_batch", "batch": {"description": "x", '
        '"commands": [{"action": "frobnicate", "node_id": "f1"}]}}\n'
        "```"
    )
    result = pipeline.process_response(text)
    assert result.batch is None
    assert result.validation_error is not None


def test_pipeline_strips_fence_from_message(graph: WorkflowGraph, context: CommandContext) -> None:
    pipeline = CommandPipeline(context)
    text = (
        "Here's the change.\n\n"
        "```json\n"
        '{"type": "action_batch", "batch": {"description": "x", '
        '"mutations": []}}\n'
        "```\n"
    )
    result = pipeline.process_response(text)
    assert "```" not in result.message
    assert "json" not in result.message
    assert result.message.strip() == "Here's the change."


def test_pipeline_reports_failure_on_unknown_node_type(
    graph: WorkflowGraph, context: CommandContext
) -> None:
    pipeline = CommandPipeline(context)
    text = (
        "Trying unknown type.\n\n"
        "```json\n"
        '{"type": "action_batch", "batch": {"description": "x", '
        '"mutations": [{"action": "create_node", "node_id": "x1", '
        '"node_type": "no_such_type", "params": {}, '
        '"position_x": 0.0, "position_y": 0.0, "select_after": false}]}}\n'
        "```\n"
    )
    result = pipeline.process_response(text)
    assert result.batch is not None
    report = pipeline.apply(result.batch)
    assert not report.ok
    assert report.error_count == 1
    assert graph.get_node_count() == 0
