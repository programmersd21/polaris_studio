from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class _StrictModel(BaseModel):
    """Base for AI-emitted action schemas: reject unknown fields."""

    model_config = ConfigDict(extra="forbid")


class NodeCategory(str, Enum):
    SOURCE = "source"
    TRANSFORM = "transform"
    FILTER = "filter"
    AGGREGATE = "aggregate"
    JOIN = "join"
    SORT = "sort"
    CHART = "chart"
    OUTPUT = "output"


class CreateNodeAction(_StrictModel):
    action: Literal["create_node"] = "create_node"
    node_id: str
    node_type: str
    params: Dict[str, Any] = Field(default_factory=dict)
    position_x: float = 0.0
    position_y: float = 0.0
    select_after: bool = False


class UpdateNodeAction(_StrictModel):
    action: Literal["update_node"] = "update_node"
    node_id: str
    param_name: str
    value: Any


class DeleteNodeAction(_StrictModel):
    action: Literal["delete_node"] = "delete_node"
    node_id: str


class ConnectAction(_StrictModel):
    action: Literal["connect"] = "connect"
    source_id: str
    source_port: str = "data_out"
    target_id: str
    target_port: str = "data_in"


class DisconnectAction(_StrictModel):
    action: Literal["disconnect"] = "disconnect"
    source_id: str
    source_port: str = "data_out"
    target_id: str
    target_port: str = "data_in"


class SelectNodeAction(_StrictModel):
    action: Literal["select_node"] = "select_node"
    node_id: str


class ExecuteNodeAction(_StrictModel):
    action: Literal["execute_node"] = "execute_node"
    node_id: str


GraphMutation = Annotated[
    Union[
        CreateNodeAction,
        UpdateNodeAction,
        DeleteNodeAction,
        ConnectAction,
        DisconnectAction,
        SelectNodeAction,
        ExecuteNodeAction,
    ],
    Field(discriminator="action"),
]


class PipelineMutationBatch(_StrictModel):
    description: str = ""
    mutations: List[GraphMutation] = Field(default_factory=list)


class UpdateCellCommand(_StrictModel):
    action: Literal["update_cell"] = "update_cell"
    row: int
    column: int
    value: Any


class SetCellStyleCommand(_StrictModel):
    action: Literal["set_cell_style"] = "set_cell_style"
    row: int
    column: int
    background: Optional[str] = None
    foreground: Optional[str] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    alignment: Optional[Literal["left", "center", "right"]] = None


class InsertRowCommand(_StrictModel):
    action: Literal["insert_row"] = "insert_row"
    row: int
    values: Dict[str, Any] = Field(default_factory=dict)


class DeleteRowCommand(_StrictModel):
    action: Literal["delete_row"] = "delete_row"
    rows: List[int] = Field(default_factory=list)


class RenameColumnCommand(_StrictModel):
    action: Literal["rename_column"] = "rename_column"
    old_name: str
    new_name: str


class CastColumnCommand(_StrictModel):
    action: Literal["cast_column"] = "cast_column"
    column: str
    target_type: str


class FillNullCommand(_StrictModel):
    action: Literal["fill_null"] = "fill_null"
    column: str
    strategy: str
    value: Any = None


class SetViewModeCommand(_StrictModel):
    action: Literal["set_view_mode"] = "set_view_mode"
    mode: Literal["spreadsheet", "graph", "split"]


class AutoLayoutCommand(_StrictModel):
    action: Literal["auto_layout"] = "auto_layout"


class ExecuteGraphCommand(_StrictModel):
    action: Literal["execute_graph"] = "execute_graph"
    node_id: Optional[str] = None


class TogglePanelCommand(_StrictModel):
    action: Literal["toggle_panel"] = "toggle_panel"
    panel: Literal["ai", "properties", "profile", "chart", "nodes"]
    visible: Optional[bool] = None


AppCommand = Annotated[
    Union[
        CreateNodeAction,
        UpdateNodeAction,
        DeleteNodeAction,
        ConnectAction,
        DisconnectAction,
        SelectNodeAction,
        ExecuteNodeAction,
        UpdateCellCommand,
        SetCellStyleCommand,
        InsertRowCommand,
        DeleteRowCommand,
        RenameColumnCommand,
        CastColumnCommand,
        FillNullCommand,
        SetViewModeCommand,
        AutoLayoutCommand,
        ExecuteGraphCommand,
        TogglePanelCommand,
    ],
    Field(discriminator="action"),
]


class AppCommandBatch(_StrictModel):
    description: str = ""
    commands: List[AppCommand] = Field(default_factory=list)


class ChatMessage(_StrictModel):
    role: Literal["user", "assistant", "system"]
    content: str
    tool_uses: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)


class ChatEvent(_StrictModel):
    type: Literal["token", "message", "action_batch", "command_batch", "error", "done", "tool_use"]
    text: str = ""
    batch: Optional[Union[PipelineMutationBatch, AppCommandBatch]] = None
    message: str = ""
    tool_name: str = ""
    tool_args: Dict[str, Any] = Field(default_factory=dict)
