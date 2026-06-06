from __future__ import annotations

import json
import threading
import time
from typing import Any, List, Optional

from PySide6.QtCore import QObject, Signal

from polaris_studio.core.engine import Engine, ExecutionError
from polaris_studio.core.graph import CycleError, Node, WorkflowGraph
from polaris_studio.core.profiler import DataProfiler
from polaris_studio.state.history import GraphMutationAction, HistoryStack


class AppState(QObject):
    node_selected = Signal(list)
    graph_changed = Signal(object)
    table_data_ready = Signal(str, object)
    compute_started = Signal(str)
    compute_finished = Signal(str, float)
    compute_error = Signal(str, str)
    execution_status = Signal(str)
    node_param_changed = Signal(str, str, object)
    ai_stream_token = Signal(str)
    ai_action_ready = Signal(object)
    view_mode_changed = Signal(object)
    tab_changed = Signal(str)
    history_state_changed = Signal(bool, bool)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.graph = WorkflowGraph()
        self.history = HistoryStack()
        self.selected_node_ids: List[str] = []
        self.active_table_node_id: Optional[str] = None
        self.is_computing: bool = False
        self.last_execution_time_ms: float = 0.0
        self._engine = Engine()
        self._lock = threading.Lock()

    def _invalidate_execution_state(self) -> None:
        self._engine.clear_cache()

    def request_execute(self, node_id: str) -> None:
        with self._lock:
            if self.is_computing:
                return
            self.is_computing = True
        self.compute_started.emit(node_id)
        self.execution_status.emit(f"Computing {node_id}...")

        def _execute() -> None:
            try:
                start = time.time()
                df = self._engine.execute(self.graph, node_id)
                elapsed = (time.time() - start) * 1000
                self.table_data_ready.emit(node_id, df)
                self.last_execution_time_ms = elapsed
                self.compute_finished.emit(node_id, elapsed)
                self.execution_status.emit(f"Done ({len(df):,} rows, {elapsed:.0f}ms)")
            except ExecutionError as e:
                self.compute_error.emit(node_id, str(e))
                self.execution_status.emit(f"Error: {e}")
            except Exception as e:
                self.compute_error.emit(node_id, str(e))
                self.execution_status.emit(f"Error: {e}")
            finally:
                with self._lock:
                    self.is_computing = False

        threading.Thread(target=_execute, daemon=True).start()

    def request_execute_all(self) -> None:
        with self._lock:
            if self.is_computing:
                return
            self.is_computing = True
        self.compute_started.emit("all")
        self.execution_status.emit("Computing all nodes...")

        def _execute_all() -> None:
            try:
                start = time.time()
                results = self._engine.execute_all(self.graph)
                elapsed = (time.time() - start) * 1000
                errors = [error for _, error in results if error]
                for node_id, error in results:
                    if error is None:
                        df = self._engine.get_cached(node_id)
                        if df is not None:
                            self.table_data_ready.emit(node_id, df)
                self.last_execution_time_ms = elapsed
                if errors:
                    self.compute_error.emit("all", errors[0])
                    self.execution_status.emit(f"Completed with errors ({elapsed:.0f}ms)")
                else:
                    self.compute_finished.emit("all", elapsed)
                    self.execution_status.emit(f"Done ({elapsed:.0f}ms)")
            except Exception as e:
                self.compute_error.emit("all", str(e))
                self.execution_status.emit(f"Error: {e}")
            finally:
                with self._lock:
                    self.is_computing = False

        threading.Thread(target=_execute_all, daemon=True).start()

    def request_profile(self, node_id: str) -> None:
        def _profile() -> None:
            try:
                df = self._engine.get_cached(node_id)
                if df is None:
                    df = self._engine.execute(self.graph, node_id)
                profile = DataProfiler.profile(df, node_id)
                import dataclasses

                profile_dict = {k: v for k, v in dataclasses.asdict(profile).items()}
                self.table_data_ready.emit(
                    f"profile:{node_id}", json.dumps(profile_dict, default=str)
                )
            except Exception as e:
                self.execution_status.emit(f"Profile failed: {e}")

        threading.Thread(target=_profile, daemon=True).start()

    def request_preview(self, node_id: str, limit: int = 100) -> None:
        def _preview() -> None:
            try:
                df = self._engine.get_cached(node_id)
                if df is None:
                    df = self._engine.execute(self.graph, node_id)
                preview = df.head(limit)
                preview_data = {
                    "columns": preview.columns,
                    "dtypes": [str(d) for d in preview.dtypes],
                    "rows": [list(r) for r in preview.iter_rows()],
                }
                self.table_data_ready.emit(
                    f"preview:{node_id}", json.dumps(preview_data, default=str)
                )
            except Exception as e:
                self.execution_status.emit(f"Preview failed: {e}")

        threading.Thread(target=_preview, daemon=True).start()

    def add_node(self, node: Node, record_history: bool = True) -> None:
        self.graph.add_node(node)
        if record_history:

            def _undo(g: WorkflowGraph) -> None:
                g.remove_node(node.node_id)

            def _redo(g: WorkflowGraph) -> None:
                g.add_node(node)

            self.history.push(
                GraphMutationAction(f"add_node:{node.node_id}", _undo, _redo),
                GraphMutationAction(f"remove_node:{node.node_id}", _redo, _undo),
            )
        self._invalidate_execution_state()
        self.graph_changed.emit(self.graph)
        self.history_state_changed.emit(self.history.can_undo, self.history.can_redo)

    def remove_node(self, node_id: str, record_history: bool = True) -> None:
        node = self.graph.get_node(node_id)
        if node is None:
            return
        edges = [
            e for e in self.graph.get_edges() if e.source_id == node_id or e.target_id == node_id
        ]
        if record_history:
            n = node
            es = edges

            def _undo(g: WorkflowGraph) -> None:
                g.add_node(n)
                for e in es:
                    g.add_edge(e.source_id, e.target_id, e.source_port, e.target_port)

            def _redo(g: WorkflowGraph) -> None:
                g.remove_node(node_id)

            self.history.push(
                GraphMutationAction(f"remove_node:{node_id}", _undo, _redo),
                GraphMutationAction(f"restore_node:{node_id}", _redo, _undo),
            )
        self.graph.remove_node(node_id)
        self.selected_node_ids = [n for n in self.selected_node_ids if n != node_id]
        self._invalidate_execution_state()
        self.graph_changed.emit(self.graph)
        self.history_state_changed.emit(self.history.can_undo, self.history.can_redo)

    def connect_nodes(
        self,
        source_id: str,
        target_id: str,
        source_port: str = "data_out",
        target_port: str = "data_in",
        record_history: bool = True,
    ) -> None:
        try:
            self.graph.add_edge(source_id, target_id, source_port, target_port)
            if record_history:

                def _undo(g: WorkflowGraph) -> None:
                    g.remove_edge(source_id, target_id, source_port, target_port)

                def _redo(g: WorkflowGraph) -> None:
                    g.add_edge(source_id, target_id, source_port, target_port)

                self.history.push(
                    GraphMutationAction(f"connect:{source_id}->{target_id}", _undo, _redo),
                    GraphMutationAction(f"disconnect:{source_id}->{target_id}", _redo, _undo),
                )
            self.graph_changed.emit(self.graph)
            self.history_state_changed.emit(self.history.can_undo, self.history.can_redo)
        except CycleError as e:
            import logging

            logging.warning(f"Cycle detected: {e}")

    def disconnect_nodes(
        self,
        source_id: str,
        target_id: str,
        source_port: str = "data_out",
        target_port: str = "data_in",
        record_history: bool = True,
    ) -> None:
        if record_history:

            def _undo(g: WorkflowGraph) -> None:
                g.add_edge(source_id, target_id, source_port, target_port)

            def _redo(g: WorkflowGraph) -> None:
                g.remove_edge(source_id, target_id, source_port, target_port)

            self.history.push(
                GraphMutationAction(f"disconnect:{source_id}->{target_id}", _undo, _redo),
                GraphMutationAction(f"reconnect:{source_id}->{target_id}", _redo, _undo),
            )
        self.graph.remove_edge(source_id, target_id, source_port, target_port)
        self.graph.mark_dirty(target_id)
        self._invalidate_execution_state()
        self.graph_changed.emit(self.graph)
        self.history_state_changed.emit(self.history.can_undo, self.history.can_redo)

    def update_node_param(
        self, node_id: str, key: str, value: Any, record_history: bool = True
    ) -> None:
        node = self.graph.get_node(node_id)
        if node is None:
            return
        had_key = key in node.params
        previous_value = node.params.get(key)
        if record_history:

            def _undo(g: WorkflowGraph) -> None:
                n = g.get_node(node_id)
                if n is None:
                    return
                if had_key:
                    n.params[key] = previous_value
                else:
                    n.params.pop(key, None)
                g.mark_dirty(node_id)

            def _redo(g: WorkflowGraph) -> None:
                n = g.get_node(node_id)
                if n is None:
                    return
                n.params[key] = value
                g.mark_dirty(node_id)

            self.history.push(
                GraphMutationAction(f"update_param:{node_id}:{key}", _undo, _redo),
                GraphMutationAction(f"restore_param:{node_id}:{key}", _redo, _undo),
            )
        node.params[key] = value
        self.graph.mark_dirty(node_id)
        self._invalidate_execution_state()
        self.node_param_changed.emit(node_id, key, value)
        self.graph_changed.emit(self.graph)

    def update_node_position(self, node_id: str, x: float, y: float) -> None:
        node = self.graph.get_node(node_id)
        if node is None:
            return
        node.position = (x, y)

    def select_node(self, node_id: str) -> None:
        self.selected_node_ids = [node_id]
        node = self.graph.get_node(node_id)
        self.node_selected.emit([node] if node else [])

    def select_multiple_nodes(self, node_ids: List[str]) -> None:
        self.selected_node_ids = node_ids
        nodes = [self.graph.get_node(nid) for nid in node_ids if self.graph.get_node(nid)]
        self.node_selected.emit(nodes)

    def clear_selection(self) -> None:
        self.selected_node_ids = []
        self.node_selected.emit([])

    def undo(self) -> None:
        action = self.history.undo()
        if action:
            action.execute(self.graph)
            self._invalidate_execution_state()
            self.graph_changed.emit(self.graph)
            self.history_state_changed.emit(self.history.can_undo, self.history.can_redo)

    def redo(self) -> None:
        action = self.history.redo()
        if action:
            action.execute(self.graph)
            self._invalidate_execution_state()
            self.graph_changed.emit(self.graph)
            self.history_state_changed.emit(self.history.can_undo, self.history.can_redo)
