"""AI chat session.

Bridges the AI backend to the command pipeline. Sends user messages, receives
streaming tokens, and yields typed ChatEvents. Never leaks structured payloads
into the chat surface.
"""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator, Callable, Dict, List, Optional

from polaris_studio.agent.ai_backend import AIBackendRouter
from polaris_studio.agent.command_pipeline import (
    CommandContext,
    CommandPipeline,
    ExecutionReport,
    PipelineResult,
)
from polaris_studio.agent.schemas import (
    AppCommandBatch,
    ChatEvent,
    PipelineMutationBatch,
)
from polaris_studio.core.graph import WorkflowGraph
from polaris_studio.core.node_registry import NODE_REGISTRY


logger = logging.getLogger(__name__)


class ChatSession:
    """Stream-based chat session with separated message/command flows."""

    def __init__(self, graph: WorkflowGraph, backend_router: AIBackendRouter) -> None:
        self._graph = graph
        self._backend_router = backend_router
        self._history: List[Dict[str, str]] = []
        self._pending_batch: Optional[AppCommandBatch | PipelineMutationBatch] = None
        self._pending_report: Optional[ExecutionReport] = None
        self._on_graph_context: Optional[Callable[[], str]] = None
        self._pipeline: Optional[CommandPipeline] = None
        self._context_provider: Optional[Callable[[], CommandContext]] = None

    def set_context_provider(self, provider: Callable[[], str]) -> None:
        self._on_graph_context = provider

    def set_command_context_provider(self, provider: Callable[[], CommandContext]) -> None:
        self._context_provider = provider

    def set_command_context(self, context: CommandContext) -> None:
        self._pipeline = CommandPipeline(context)

    def _ensure_pipeline(self) -> Optional[CommandPipeline]:
        if self._pipeline is not None:
            return self._pipeline
        if self._context_provider is not None:
            ctx = self._context_provider()
            self._pipeline = CommandPipeline(ctx)
            return self._pipeline
        return None

    async def send(
        self,
        user_message: str,
        attached_node_id: Optional[str] = None,
    ) -> AsyncIterator[ChatEvent]:
        backend = self._backend_router.get_backend()
        if backend is None:
            yield ChatEvent(
                type="error",
                message="No AI backend configured. Add a Gemini API key in Settings.",
            )
            return

        self._history.append({"role": "user", "content": user_message})

        system = self._build_system_prompt()
        full_response = ""

        try:
            async for event in backend.chat(
                messages=self._history,
                system=system,
                tools=None,
            ):
                if event.type == "token":
                    full_response += event.text
                    yield ChatEvent(type="token", text=event.text)
                elif event.type == "done":
                    yield ChatEvent(type="done")
                elif event.type == "error":
                    yield ChatEvent(type="error", message=event.message)
                elif event.type == "tool_use":
                    yield event
        except Exception as exc:
            logger.exception("Chat error")
            yield ChatEvent(type="error", message=str(exc))
            return

        self._history.append({"role": "assistant", "content": full_response})
        for ev in self._finalize_response(full_response):
            yield ev

    def _finalize_response(self, full_response: str) -> List[ChatEvent]:
        events: List[ChatEvent] = []
        pipeline = self._ensure_pipeline()
        if pipeline is None:
            events.append(ChatEvent(type="message", text=self._strip_command_blocks(full_response)))
            return events

        result: PipelineResult = pipeline.process_response(full_response)
        events.append(ChatEvent(type="message", text=result.message))
        if result.batch is not None:
            self._pending_batch = result.batch
            self._pending_report = None
            if isinstance(result.batch, AppCommandBatch):
                events.append(ChatEvent(type="command_batch", batch=result.batch))
            else:
                events.append(ChatEvent(type="action_batch", batch=result.batch))
        elif result.validation_error:
            note = (
                f"I couldn't apply the proposed changes - {result.validation_error}. "
                "I'll retry the same request in the next turn using the correct schema."
            )
            self._history.append({"role": "user", "content": note})
            events.append(
                ChatEvent(
                    type="message",
                    text="I couldn’t apply the proposed changes. Let me try again with the correct format.",
                )
            )
        return events

    def _strip_command_blocks(self, text: str) -> str:
        cleaned = re.sub(r"```(?:json|JSON)?\s*\{.*?\}\s*```", "", text, flags=re.DOTALL)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip() or "I’ve prepared the changes. Take a look and let me know."

    def _build_system_prompt(self) -> str:
        context = self._get_graph_context()
        node_types = self._node_type_catalog()
        return f"""You are the AI engine inside Polaris Studio, a node-based visual data application.

WORKSPACE CONTEXT:
{context}

AVAILABLE NODE TYPES:
{node_types}

OUTPUT FORMAT (strict):
When you need to make changes, you MUST emit exactly one ```json fenced code block
with one of the two structures below. The user never sees the JSON; the app
parses, validates, and shows them a preview card.

Format A - graph mutations (create / connect / delete / select / execute):
```json
{{
  "type": "action_batch",
  "batch": {{
    "description": "short user-facing summary",
    "mutations": [
      {{"action": "create_node", "node_id": "filter_sri_lanka", "node_type": "filter",
        "params": {{"expression": "pl.col('Country') == 'Sri Lanka'"}},
        "position_x": 240.0, "position_y": 120.0, "select_after": true}},
      {{"action": "connect", "source_id": "csv_reader_1", "target_id": "filter_sri_lanka"}}
    ]
  }}
}}
```

Format B - spreadsheet / app commands (cells, columns, view, layout, panels):
```json
{{
  "type": "command_batch",
  "batch": {{
    "description": "short user-facing summary",
    "commands": [
      {{"action": "delete_row", "rows": [0, 1]}},
      {{"action": "rename_column", "old_name": "old", "new_name": "new"}}
    ]
  }}
}}
```

RULES:
1. The `action` field is REQUIRED and must be one of the literal strings shown
   in the schema (create_node, connect, update_node, delete_node, select_node,
   execute_node, update_cell, set_cell_style, insert_row, delete_row,
   rename_column, cast_column, fill_null, set_view_mode, auto_layout,
   execute_graph, toggle_panel).
2. Field names are EXACT: `source_id` / `target_id` (not from_node / to_node),
   `node_id` (not id), `params` (not properties / args).
3. The JSON block must be VALID JSON - no trailing commas, no comments.
4. For the filter node, the `params.expression` field must be a polars
   expression, e.g. `pl.col('Country') == 'Sri Lanka'` or
   `(pl.col('Age') > 18) & (pl.col('Country') == 'Sri Lanka')`.
5. Connect existing nodes - do NOT create a new source node if the workspace
   already has one (e.g. `csv_reader_1`). Inspect CONTEXT first.
6. Position new nodes just to the right of the source: position_x ~ 240 +
   220 * count, position_y matches the source.
7. Prose goes OUTSIDE the JSON block. Keep it to one or two short sentences.
8. If the request is conversational (no changes needed), respond in plain
   text with no JSON block.
9. Never invent node types. Use only the ones listed under AVAILABLE NODE TYPES.
10. When unsure, ask a clarifying question instead of guessing."""

    def _get_graph_context(self) -> str:
        if self._on_graph_context:
            return self._on_graph_context()
        return self._default_graph_context()

    def _node_type_catalog(self) -> str:
        from collections import defaultdict

        by_cat: Dict[str, List[str]] = defaultdict(list)
        for spec in NODE_REGISTRY.values():
            params = ", ".join(p.name for p in spec.params[:4]) if spec.params else "no params"
            by_cat[spec.category].append(
                f"  - {spec.node_type} ({spec.display_name}): {spec.description} | params: {params}"
            )
        return "\n".join(
            f"[{cat}]\n" + "\n".join(sorted(items)) for cat, items in sorted(by_cat.items())
        )

    def _default_graph_context(self) -> str:
        nodes = self._graph.get_nodes()
        edges = self._graph.get_edges()
        lines: List[str] = [f"Total nodes: {len(nodes)}, Total edges: {len(edges)}"]
        if nodes:
            lines.append("Nodes:")
            for nid, node in nodes.items():
                param_summary = ", ".join(f"{k}={v}" for k, v in list(node.params.items())[:3])
                lines.append(f"  - {nid} ({node.node_type}) [{param_summary}]")
        if edges:
            lines.append("Edges:")
            for e in edges:
                lines.append(f"  - {e.source_id} -> {e.target_id}")
        return "\n".join(lines)

    @property
    def pending_batch(self) -> Optional[AppCommandBatch | PipelineMutationBatch]:
        return self._pending_batch

    @property
    def pending_report(self) -> Optional[ExecutionReport]:
        return self._pending_report

    def apply_pending_batch(self) -> List[str]:
        if not self._pending_batch:
            return []
        pipeline = self._ensure_pipeline()
        if pipeline is None:
            self._pending_batch = None
            self._pending_report = None
            return ["No command pipeline available"]
        report = pipeline.apply(self._pending_batch)
        self._pending_report = report
        messages: List[str] = []
        for r in report.results:
            if r.success:
                messages.append(r.message or r.label)
            else:
                messages.append(f"Failed: {r.label} - {r.error}")
        self._pending_batch = None
        return messages

    def reject_pending_batch(self) -> None:
        self._pending_batch = None
        self._pending_report = None
        self._history.append(
            {
                "role": "assistant",
                "content": "[The user rejected the proposed changes. I will not apply them.]",
            }
        )

    @property
    def history(self) -> List[Dict[str, str]]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()
