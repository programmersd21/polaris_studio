from __future__ import annotations

import io
import json
import multiprocessing as mp
import time

import pyarrow as pa

from polaris_studio.core.engine import Engine
from polaris_studio.core.graph import WorkflowGraph
from polaris_studio.core.profiler import DataProfiler
from polaris_studio.ipc.protocol import (
    IPCCommand,
    IPCCommandType,
    IPCResult,
    IPCResultType,
    deserialize_command,
    serialize_result,
)


class ComputeWorker:
    def __init__(self, pipe: mp.connection.Connection) -> None:
        self._pipe = pipe
        self._engine = Engine()
        self._graph = WorkflowGraph()

    def run(self) -> None:
        while True:
            try:
                data = self._pipe.recv_bytes()
            except (EOFError, OSError):
                break
            cmd = deserialize_command(data)
            result = self._handle(cmd)
            try:
                self._pipe.send_bytes(serialize_result(result))
            except (EOFError, OSError):
                break
            if cmd.cmd_type == IPCCommandType.SHUTDOWN:
                break

    def _handle(self, cmd: IPCCommand) -> IPCResult:
        try:
            if cmd.cmd_type == IPCCommandType.PING:
                return IPCResult(result_type=IPCResultType.PONG, success=True)

            if cmd.cmd_type == IPCCommandType.LOAD_FILE:
                return self._handle_load(cmd)

            if cmd.cmd_type == IPCCommandType.EXECUTE_NODE:
                return self._handle_execute(cmd)

            if cmd.cmd_type == IPCCommandType.EXECUTE_ALL:
                return self._handle_execute_all(cmd)

            if cmd.cmd_type == IPCCommandType.PROFILE_NODE:
                return self._handle_profile(cmd)

            if cmd.cmd_type == IPCCommandType.GET_PREVIEW:
                return self._handle_preview(cmd)

            if cmd.cmd_type == IPCCommandType.SHUTDOWN:
                return IPCResult(result_type=IPCResultType.SUCCESS, success=True)

            return IPCResult(
                result_type=IPCResultType.ERROR,
                success=False,
                error=f"Unknown command: {cmd.cmd_type}",
            )
        except Exception as e:
            return IPCResult(
                result_type=IPCResultType.ERROR,
                success=False,
                node_id=cmd.node_id,
                error=str(e),
            )

    def _rebuild_graph(self, cmd: IPCCommand) -> None:
        if cmd.graph_data:
            self._graph = WorkflowGraph.from_dict(cmd.graph_data)

    def _handle_load(self, cmd: IPCCommand) -> IPCResult:
        return IPCResult(
            result_type=IPCResultType.SUCCESS,
            success=True,
        )

    def _handle_execute(self, cmd: IPCCommand) -> IPCResult:
        self._rebuild_graph(cmd)
        if not cmd.node_id:
            return IPCResult(
                result_type=IPCResultType.ERROR,
                success=False,
                error="No node_id specified for execution",
            )
        start = time.time()
        df = self._engine.execute(self._graph, cmd.node_id)
        elapsed = (time.time() - start) * 1000
        buf = io.BytesIO()
        table = pa.Table.from_pandas(df.to_pandas())
        with pa.ipc.new_stream(buf, table.schema) as writer:
            writer.write_table(table)
        return IPCResult(
            result_type=IPCResultType.DATA_READY,
            success=True,
            node_id=cmd.node_id,
            arrow_buffer=buf.getvalue(),
            duration_ms=elapsed,
            rows=len(df),
        )

    def _handle_execute_all(self, cmd: IPCCommand) -> IPCResult:
        self._rebuild_graph(cmd)
        start = time.time()
        results = self._engine.execute_all(self._graph)
        elapsed = (time.time() - start) * 1000
        errors = [e for _, e in results if e is not None]
        return IPCResult(
            result_type=IPCResultType.SUCCESS,
            success=len(errors) == 0,
            duration_ms=elapsed,
            error=errors[0] if errors else None,
        )

    def _handle_profile(self, cmd: IPCCommand) -> IPCResult:
        self._rebuild_graph(cmd)
        if not cmd.node_id:
            return IPCResult(
                result_type=IPCResultType.ERROR,
                success=False,
                error="No node_id specified for profiling",
            )
        df = self._engine.get_cached(cmd.node_id)
        if df is None:
            df = self._engine.execute(self._graph, cmd.node_id)
        profile = DataProfiler.profile(df, cmd.node_id)
        import dataclasses

        profile_dict = {k: v for k, v in dataclasses.asdict(profile).items()}
        return IPCResult(
            result_type=IPCResultType.PROFILE_READY,
            success=True,
            node_id=cmd.node_id,
            profile_json=json.dumps(profile_dict, default=str),
        )

    def _handle_preview(self, cmd: IPCCommand) -> IPCResult:
        self._rebuild_graph(cmd)
        if not cmd.node_id:
            return IPCResult(
                result_type=IPCResultType.ERROR,
                success=False,
                error="No node_id specified for preview",
            )
        limit = cmd.params.get("limit", 100)
        df = self._engine.get_cached(cmd.node_id)
        if df is None:
            df = self._engine.execute(self._graph, cmd.node_id)
        preview = df.head(limit)
        preview_data = {
            "columns": preview.columns,
            "dtypes": [str(d) for d in preview.dtypes],
            "rows": [list(r) for r in preview.iter_rows()],
        }
        return IPCResult(
            result_type=IPCResultType.PREVIEW_READY,
            success=True,
            node_id=cmd.node_id,
            preview_json=json.dumps(preview_data, default=str),
        )


def worker_main(pipe: mp.connection.Connection) -> None:
    worker = ComputeWorker(pipe)
    worker.run()
