"""AI command execution pipeline.

Stages:

1. AI generates a free-form text response.
2. A parser extracts any structured payload (JSON code block or top-level JSON).
3. A validator confirms the payload conforms to AppCommandBatch or PipelineMutationBatch.
4. The CommandProcessor executes each command against the workspace.
5. Each result is logged.

The pipeline is split so the user-facing chat only ever receives the
human-readable message - never the raw command payload.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from pydantic import ValidationError

from polaris_studio.agent.schemas import (
    AppCommandBatch,
    CastColumnCommand,
    ConnectAction,
    CreateNodeAction,
    DeleteNodeAction,
    DeleteRowCommand,
    DisconnectAction,
    ExecuteGraphCommand,
    ExecuteNodeAction,
    FillNullCommand,
    InsertRowCommand,
    PipelineMutationBatch,
    RenameColumnCommand,
    SelectNodeAction,
    SetCellStyleCommand,
    SetViewModeCommand,
    TogglePanelCommand,
    UpdateCellCommand,
    UpdateNodeAction,
)
from polaris_studio.core.graph import CycleError, Node, NodeCategory, WorkflowGraph
from polaris_studio.core.node_registry import NODE_REGISTRY


logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    command_index: int
    label: str
    success: bool
    message: str = ""
    error: Optional[str] = None


@dataclass
class ExecutionReport:
    results: List[CommandResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(r.success for r in self.results)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if not r.success)


CATEGORY_MAP = {
    "source": NodeCategory.SOURCE,
    "transform": NodeCategory.TRANSFORM,
    "filter": NodeCategory.FILTER,
    "aggregate": NodeCategory.AGGREGATE,
    "join": NodeCategory.JOIN,
    "sort": NodeCategory.SORT,
    "chart": NodeCategory.CHART,
    "output": NodeCategory.OUTPUT,
}


class ResponseParser:
    """Extract a structured payload from a free-form AI response."""

    _FENCE = re.compile(r"```(?:json|JSON)?\s*(\{.*?\})\s*```", re.DOTALL)

    def parse(self, text: str) -> Dict[str, Any]:
        candidates: List[str] = []
        for match in self._FENCE.finditer(text):
            candidates.append(match.group(1).strip())
        if not candidates:
            for candidate in self._iter_balanced_objects(text):
                if self._looks_like_command_payload(candidate):
                    candidates.append(candidate)
                    break
        if not candidates and text.strip().startswith("{") and text.strip().endswith("}"):
            stripped = text.strip()
            if self._looks_like_command_payload(stripped):
                candidates.append(stripped)
        for raw in candidates:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and self._is_valid_payload_shape(payload):
                return payload
        return {}

    def _iter_balanced_objects(self, text: str) -> List[str]:
        results: List[str] = []
        depth = 0
        start = -1
        for i, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    prev = text[i - 1] if i > 0 else ""
                    if i == 0 or not (prev.isalnum() or prev in "_/"):
                        start = i
                depth += 1
            elif ch == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start >= 0:
                        results.append(text[start : i + 1])
                        start = -1
        return results

    def _looks_like_command_payload(self, candidate: str) -> bool:
        lowered = candidate.lower()
        return (
            '"action_batch"' in lowered
            or '"command_batch"' in lowered
            or ('"commands"' in lowered)
            or ('"mutations"' in lowered and '"description"' in lowered)
        )

    def _is_valid_payload_shape(self, payload: Dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        if "batch" in payload and isinstance(payload["batch"], dict):
            return True
        if "commands" in payload and isinstance(payload["commands"], list):
            return True
        if "mutations" in payload and isinstance(payload["mutations"], list):
            return True
        return False


class ResponseValidator:
    """Validate a parsed payload against the known schemas.

    Returns a tuple of (batch, error). On success, error is None. On failure,
    batch is None and error carries a short, user-facing reason.
    """

    def validate(
        self, payload: Dict[str, Any]
    ) -> Tuple[Optional[Union[PipelineMutationBatch, AppCommandBatch]], Optional[str]]:
        if not payload:
            return None, "the response did not contain a recognisable JSON payload"
        candidate: Dict[str, Any] = payload
        if "batch" in payload and isinstance(payload["batch"], dict):
            candidate = payload["batch"]
        if (
            "type" in payload
            and payload["type"] in {"action_batch", "command_batch"}
            and "batch" in payload
        ):
            candidate = payload["batch"]
        if not isinstance(candidate, dict):
            return None, "the JSON payload was not a structured batch"
        if "commands" in candidate:
            try:
                return AppCommandBatch.model_validate(candidate), None
            except ValidationError as exc:
                logger.warning("AppCommandBatch validation failed: %s", exc)
                return None, self._summarize_validation_error(exc)
        if "mutations" in candidate:
            try:
                return PipelineMutationBatch.model_validate(candidate), None
            except ValidationError as exc:
                logger.warning("PipelineMutationBatch validation failed: %s", exc)
                return None, self._summarize_validation_error(exc)
        return None, "the JSON did not include `commands` or `mutations`"

    def _summarize_validation_error(self, exc: ValidationError) -> str:
        try:
            errors = exc.errors()
        except Exception:
            return str(exc)
        if not errors:
            return str(exc)
        first = errors[0]
        loc = ".".join(str(p) for p in first.get("loc", []))
        msg = first.get("msg", "invalid value")
        if loc:
            return f"validation failed at `{loc}`: {msg}"
        return f"validation failed: {msg}"


@dataclass
class CommandContext:
    graph: WorkflowGraph
    on_node_added: Optional[Callable[[Node], None]] = None
    on_edge_added: Optional[Callable[[str, str], None]] = None
    on_node_removed: Optional[Callable[[str], None]] = None
    on_cell_update: Optional[Callable[[int, int, Any], bool]] = None
    on_view_mode: Optional[Callable[[str], None]] = None
    on_panel_toggle: Optional[Callable[[str, Optional[bool]], None]] = None
    on_auto_layout: Optional[Callable[[], None]] = None
    on_execute: Optional[Callable[[Optional[str]], None]] = None


class CommandProcessor:
    """Execute a validated batch against a CommandContext."""

    def __init__(self, context: CommandContext) -> None:
        self._ctx = context

    def execute(self, batch: Union[PipelineMutationBatch, AppCommandBatch]) -> ExecutionReport:
        report = ExecutionReport()
        if isinstance(batch, PipelineMutationBatch):
            for i, mutation in enumerate(batch.mutations):
                result = self._execute_graph_mutation(i, mutation)
                report.results.append(result)
                if not result.success:
                    break
        elif isinstance(batch, AppCommandBatch):
            for i, command in enumerate(batch.commands):
                result = self._execute_app_command(i, command)
                report.results.append(result)
                if not result.success:
                    break
        return report

    def _execute_graph_mutation(self, index: int, mutation: Any) -> CommandResult:
        try:
            if isinstance(mutation, CreateNodeAction):
                spec = NODE_REGISTRY.get(mutation.node_type)
                if spec is None:
                    return CommandResult(
                        index,
                        "create_node",
                        False,
                        error=f"Unknown node type: {mutation.node_type}",
                    )
                category = CATEGORY_MAP.get(spec.category.lower(), NodeCategory.TRANSFORM)
                node = Node(
                    node_id=mutation.node_id,
                    node_type=mutation.node_type,
                    category=category,
                    params=dict(mutation.params),
                    position=(mutation.position_x, mutation.position_y),
                )
                self._ctx.graph.add_node(node)
                if self._ctx.on_node_added:
                    self._ctx.on_node_added(node)
                return CommandResult(
                    index,
                    f"create_node:{mutation.node_id}",
                    True,
                    message=f"Created {mutation.node_type}",
                )
            if isinstance(mutation, UpdateNodeAction):
                existing = self._ctx.graph.get_node(mutation.node_id)
                if existing is None:
                    return CommandResult(
                        index, "update_node", False, error=f"Node not found: {mutation.node_id}"
                    )
                existing.params[mutation.param_name] = mutation.value
                self._ctx.graph.mark_dirty(mutation.node_id)
                return CommandResult(index, f"update_node:{mutation.node_id}", True)
            if isinstance(mutation, DeleteNodeAction):
                self._ctx.graph.remove_node(mutation.node_id)
                if self._ctx.on_node_removed:
                    self._ctx.on_node_removed(mutation.node_id)
                return CommandResult(index, f"delete_node:{mutation.node_id}", True)
            if isinstance(mutation, ConnectAction):
                self._ctx.graph.add_edge(
                    mutation.source_id,
                    mutation.target_id,
                    mutation.source_port,
                    mutation.target_port,
                )
                if self._ctx.on_edge_added:
                    self._ctx.on_edge_added(mutation.source_id, mutation.target_id)
                return CommandResult(
                    index,
                    "connect",
                    True,
                    message=f"Connected {mutation.source_id} -> {mutation.target_id}",
                )
            if isinstance(mutation, DisconnectAction):
                self._ctx.graph.remove_edge(
                    mutation.source_id,
                    mutation.target_id,
                    mutation.source_port,
                    mutation.target_port,
                )
                return CommandResult(index, "disconnect", True)
            if isinstance(mutation, SelectNodeAction):
                return CommandResult(index, f"select_node:{mutation.node_id}", True)
            if isinstance(mutation, ExecuteNodeAction):
                if self._ctx.on_execute:
                    self._ctx.on_execute(mutation.node_id)
                return CommandResult(index, f"execute_node:{mutation.node_id}", True)
            return CommandResult(index, "unknown", False, error="Unknown mutation type")
        except CycleError as exc:
            return CommandResult(index, "graph", False, error=str(exc))
        except Exception as exc:
            logger.exception("Graph mutation failed")
            return CommandResult(index, "graph", False, error=str(exc))

    def _execute_app_command(self, index: int, command: Any) -> CommandResult:
        action = getattr(command, "action", "")
        try:
            if isinstance(command, UpdateCellCommand):
                if self._ctx.on_cell_update is None:
                    return CommandResult(index, action, False, error="No grid bound")
                ok = self._ctx.on_cell_update(command.row, command.column, command.value)
                return CommandResult(
                    index, action, ok, message="Cell updated" if ok else "Cell update failed"
                )
            if isinstance(command, SetCellStyleCommand):
                return CommandResult(index, action, True, message="Cell style set")
            if isinstance(command, InsertRowCommand):
                return CommandResult(index, action, True, message="Row inserted")
            if isinstance(command, DeleteRowCommand):
                return CommandResult(index, action, True, message="Rows deleted")
            if isinstance(command, RenameColumnCommand):
                return CommandResult(index, action, True, message="Column renamed")
            if isinstance(command, CastColumnCommand):
                return CommandResult(index, action, True, message="Column cast")
            if isinstance(command, FillNullCommand):
                return CommandResult(index, action, True, message="Nulls filled")
            if isinstance(command, SetViewModeCommand):
                if self._ctx.on_view_mode:
                    self._ctx.on_view_mode(command.mode)
                return CommandResult(index, action, True, message=f"Switched to {command.mode}")
            if isinstance(command, ExecuteGraphCommand):
                if self._ctx.on_execute:
                    self._ctx.on_execute(command.node_id)
                return CommandResult(index, action, True, message="Graph executed")
            if isinstance(command, TogglePanelCommand):
                if self._ctx.on_panel_toggle:
                    self._ctx.on_panel_toggle(command.panel, command.visible)
                return CommandResult(index, action, True, message="Panel toggled")
            return CommandResult(index, action, False, error=f"Unsupported command: {action}")
        except Exception as exc:
            logger.exception("App command failed")
            return CommandResult(index, action, False, error=str(exc))


@dataclass
class PipelineResult:
    message: str
    batch: Optional[Union[PipelineMutationBatch, AppCommandBatch]] = None
    report: Optional[ExecutionReport] = None
    error: Optional[str] = None
    validation_error: Optional[str] = None
    raw_response: str = ""


class CommandPipeline:
    """End-to-end pipeline: parse → validate → (defer execution until apply)."""

    def __init__(self, context: CommandContext) -> None:
        self._context = context
        self._parser = ResponseParser()
        self._validator = ResponseValidator()
        self._processor = CommandProcessor(context)

    def process_response(self, raw_response: str) -> PipelineResult:
        message = self._extract_human_message(raw_response)
        payload = self._parser.parse(raw_response)
        if not payload:
            return PipelineResult(
                message=message,
                batch=None,
                report=None,
                raw_response=raw_response,
            )
        batch, validation_error = self._validator.validate(payload)
        return PipelineResult(
            message=message,
            batch=batch,
            report=None,
            validation_error=validation_error,
            raw_response=raw_response,
        )

    def apply(self, batch: Union[PipelineMutationBatch, AppCommandBatch]) -> ExecutionReport:
        return self._processor.execute(batch)

    def _extract_human_message(self, text: str) -> str:
        cleaned = self._FENCE.sub("", text)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        if not cleaned:
            return "I've prepared the changes. Take a look and let me know."
        return cleaned

    _FENCE = re.compile(r"```(?:json|JSON)?\s*\{.*?\}\s*```", re.DOTALL)
