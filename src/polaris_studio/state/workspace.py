from __future__ import annotations

import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from polaris_studio.core.graph import WorkflowGraph


READER_NODE_TYPES = frozenset(
    {
        "csv_reader",
        "xlsx_reader",
        "parquet_reader",
        "json_reader",
    }
)


@dataclass
class Tab:
    tab_id: str
    name: str
    graph: WorkflowGraph = field(default_factory=WorkflowGraph)
    active_node_id: Optional[str] = None
    scroll_position: Tuple[int, int] = (0, 0)
    zoom_level: float = 1.0
    dirty: bool = False


class Workspace:
    def __init__(self) -> None:
        self._tabs: Dict[str, Tab] = {}
        self._active_tab_id: Optional[str] = None
        self._next_id: int = 1
        self._extract_dir: Optional[Path] = None

    def new_tab(self, name: Optional[str] = None) -> Tab:
        n = name or f"Sheet{self._next_id}"
        tab = Tab(
            tab_id=f"tab_{self._next_id}",
            name=n,
        )
        self._next_id += 1
        self._tabs[tab.tab_id] = tab
        self._active_tab_id = tab.tab_id
        return tab

    def close_tab(self, tab_id: str) -> bool:
        if tab_id in self._tabs:
            del self._tabs[tab_id]
            if self._active_tab_id == tab_id:
                keys = list(self._tabs.keys())
                self._active_tab_id = keys[-1] if keys else None
            return True
        return False

    def rename_tab(self, tab_id: str, name: str) -> None:
        tab = self._tabs.get(tab_id)
        if tab:
            tab.name = name

    def reorder_tabs(self, new_order: List[str]) -> None:
        ordered: Dict[str, Tab] = {}
        for tid in new_order:
            if tid in self._tabs:
                ordered[tid] = self._tabs[tid]
        for tid, tab in self._tabs.items():
            if tid not in ordered:
                ordered[tid] = tab
        self._tabs = ordered

    def get_active(self) -> Optional[Tab]:
        if self._active_tab_id:
            return self._tabs.get(self._active_tab_id)
        return None

    def switch_to(self, tab_id: str) -> bool:
        if tab_id in self._tabs:
            self._active_tab_id = tab_id
            return True
        return False

    def get_tabs(self) -> Dict[str, Tab]:
        return dict(self._tabs)

    def get_tab_list(self) -> List[Tab]:
        return list(self._tabs.values())

    def save_all(self, path: str) -> None:
        payload: Dict[str, Any] = {
            "tabs": [
                {
                    "tab_id": tab.tab_id,
                    "name": tab.name,
                    "active_node_id": tab.active_node_id,
                    "scroll_position": list(tab.scroll_position),
                    "zoom_level": tab.zoom_level,
                    "dirty": tab.dirty,
                    "graph": tab.graph.to_dict(),
                }
                for tab in self._tabs.values()
            ],
            "active_tab_id": self._active_tab_id,
            "next_id": self._next_id,
        }

        _file_map: Dict[str, str] = {}
        for tab in self._tabs.values():
            for nid, nd in tab.graph.get_nodes().items():
                if nd.node_type in READER_NODE_TYPES and "file_path" in nd.params:
                    file_path = nd.params["file_path"]
                    if os.path.exists(file_path):
                        src = Path(file_path)
                        ext = src.suffix or ".bin"
                        arcname = f"data/{nid}{ext}"
                        _file_map[nid] = arcname

        payload["_file_map"] = _file_map

        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            for nid, arcname in _file_map.items():
                for tab in self._tabs.values():
                    n = tab.graph.get_node(nid)
                    if n is not None and "file_path" in n.params:
                        fp = n.params["file_path"]
                        if os.path.exists(fp):
                            zf.write(fp, arcname)
                        break
            zf.writestr("workflow.json", json.dumps(payload, indent=2))

    def load_all(self, path: str) -> None:
        self.cleanup_temp()
        if not os.path.exists(path):
            return

        payload: dict
        _file_map: Dict[str, str] = {}

        if zipfile.is_zipfile(path):
            self._extract_dir = Path(tempfile.mkdtemp(prefix="polaris_"))
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(self._extract_dir)
            wf_path = self._extract_dir / "workflow.json"
            if not wf_path.exists():
                raise ValueError("Corrupt .polaris file: missing workflow.json")
            with open(wf_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            _file_map = payload.get("_file_map", {})

            for nid, arcname in _file_map.items():
                extracted = self._extract_dir / arcname
                if extracted.exists():
                    for tab_payload in payload.get("tabs", []):
                        graph_payload = tab_payload.get("graph", {})
                        for node_payload in graph_payload.get("nodes", []):
                            if node_payload.get("node_id") == nid:
                                node_payload["params"]["file_path"] = str(extracted)
        else:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)

        tabs: Dict[str, Tab] = {}
        for tab_payload in payload.get("tabs", []):
            graph_payload = tab_payload.get("graph", {})
            scroll_position = tab_payload.get("scroll_position", (0, 0))
            if not isinstance(scroll_position, (list, tuple)) or len(scroll_position) < 2:
                scroll_position = (0, 0)
            tab = Tab(
                tab_id=str(tab_payload.get("tab_id", "")),
                name=str(tab_payload.get("name", "Sheet")),
                graph=WorkflowGraph.from_dict(graph_payload),
                active_node_id=tab_payload.get("active_node_id"),
                scroll_position=(int(scroll_position[0]), int(scroll_position[1])),
                zoom_level=float(tab_payload.get("zoom_level", 1.0)),
                dirty=bool(tab_payload.get("dirty", False)),
            )
            if tab.tab_id:
                tabs[tab.tab_id] = tab

        self._tabs = tabs
        active_tab_id = payload.get("active_tab_id")
        self._active_tab_id = (
            active_tab_id if active_tab_id in self._tabs else next(iter(self._tabs), None)
        )
        self._next_id = 1
        for tid in self._tabs:
            parts = tid.split("_")
            if len(parts) == 2 and parts[1].isdigit():
                self._next_id = max(self._next_id, int(parts[1]) + 1)
        if str(payload.get("next_id", "")).isdigit():
            self._next_id = max(self._next_id, int(payload["next_id"]))
        if self._active_tab_id is None and self._tabs:
            self._active_tab_id = next(iter(self._tabs))

    def cleanup_temp(self) -> None:
        if self._extract_dir is not None and self._extract_dir.exists():
            shutil.rmtree(self._extract_dir, ignore_errors=True)
            self._extract_dir = None

    @property
    def active_tab_id(self) -> Optional[str]:
        return self._active_tab_id

    @property
    def active_graph(self) -> WorkflowGraph:
        tab = self.get_active()
        if tab:
            return tab.graph
        fallback = self.new_tab()
        return fallback.graph

    def mark_dirty(self, tab_id: Optional[str] = None) -> None:
        tid = tab_id or self._active_tab_id
        if tid and tid in self._tabs:
            self._tabs[tid].dirty = True
