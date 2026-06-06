from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional


class IPCCommandType(Enum):
    EXECUTE_NODE = auto()
    EXECUTE_ALL = auto()
    PROFILE_NODE = auto()
    GET_PREVIEW = auto()
    LOAD_FILE = auto()
    EXPORT_FILE = auto()
    PING = auto()
    SHUTDOWN = auto()


class IPCResultType(Enum):
    SUCCESS = auto()
    ERROR = auto()
    DATA_READY = auto()
    PROFILE_READY = auto()
    PREVIEW_READY = auto()
    PONG = auto()


@dataclass
class IPCCommand:
    cmd_type: IPCCommandType
    node_id: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    graph_data: Optional[Dict[str, Any]] = None


@dataclass
class IPCResult:
    result_type: IPCResultType
    success: bool = True
    node_id: Optional[str] = None
    arrow_buffer: Optional[bytes] = None
    profile_json: Optional[str] = None
    preview_json: Optional[str] = None
    duration_ms: float = 0.0
    error: Optional[str] = None
    rows: int = 0


def serialize_command(cmd: IPCCommand) -> bytes:
    payload = {
        "cmd_type": cmd.cmd_type.name,
        "node_id": cmd.node_id,
        "params": cmd.params,
        "graph_data": cmd.graph_data,
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def deserialize_command(data: bytes) -> IPCCommand:
    payload = json.loads(data.decode("utf-8"))
    return IPCCommand(
        cmd_type=IPCCommandType[payload["cmd_type"]],
        node_id=payload.get("node_id"),
        params=dict(payload.get("params", {})),
        graph_data=payload.get("graph_data"),
    )


def serialize_result(result: IPCResult) -> bytes:
    payload = {
        "result_type": result.result_type.name,
        "success": result.success,
        "node_id": result.node_id,
        "arrow_buffer": base64.b64encode(result.arrow_buffer).decode("ascii")
        if result.arrow_buffer
        else None,
        "profile_json": result.profile_json,
        "preview_json": result.preview_json,
        "duration_ms": result.duration_ms,
        "error": result.error,
        "rows": result.rows,
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def deserialize_result(data: bytes) -> IPCResult:
    payload = json.loads(data.decode("utf-8"))
    arrow_buffer = payload.get("arrow_buffer")
    return IPCResult(
        result_type=IPCResultType[payload["result_type"]],
        success=bool(payload.get("success", True)),
        node_id=payload.get("node_id"),
        arrow_buffer=base64.b64decode(arrow_buffer) if arrow_buffer else None,
        profile_json=payload.get("profile_json"),
        preview_json=payload.get("preview_json"),
        duration_ms=float(payload.get("duration_ms", 0.0)),
        error=payload.get("error"),
        rows=int(payload.get("rows", 0)),
    )
