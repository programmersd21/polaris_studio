from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


class CycleError(Exception):
    pass


class NodeCategory(Enum):
    SOURCE = auto()
    TRANSFORM = auto()
    FILTER = auto()
    AGGREGATE = auto()
    JOIN = auto()
    SORT = auto()
    CHART = auto()
    OUTPUT = auto()


@dataclass
class Node:
    node_id: str
    node_type: str
    category: NodeCategory
    params: Dict[str, Any] = field(default_factory=dict)
    position: Tuple[float, float] = (0.0, 0.0)
    is_dirty: bool = True
    error: Optional[str] = None
    cached_output_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "category": self.category.name,
            "params": self.params,
            "position": [self.position[0], self.position[1]],
            "is_dirty": self.is_dirty,
            "error": self.error,
            "cached_output_id": self.cached_output_id,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Node":
        category_name = str(payload.get("category", "TRANSFORM")).upper()
        category = (
            NodeCategory[category_name]
            if category_name in NodeCategory.__members__
            else NodeCategory.TRANSFORM
        )
        position = payload.get("position", [0.0, 0.0])
        if not isinstance(position, (list, tuple)) or len(position) < 2:
            position = [0.0, 0.0]
        return cls(
            node_id=str(payload.get("node_id", "")),
            node_type=str(payload.get("node_type", "")),
            category=category,
            params=dict(payload.get("params", {})),
            position=(float(position[0]), float(position[1])),
            is_dirty=bool(payload.get("is_dirty", True)),
            error=payload.get("error"),
            cached_output_id=payload.get("cached_output_id"),
        )


@dataclass
class Edge:
    source_id: str
    target_id: str
    source_port: str = "data_out"
    target_port: str = "data_in"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "source_port": self.source_port,
            "target_port": self.target_port,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Edge":
        return cls(
            source_id=str(payload.get("source_id", "")),
            target_id=str(payload.get("target_id", "")),
            source_port=str(payload.get("source_port", "data_out")),
            target_port=str(payload.get("target_port", "data_in")),
        )


class WorkflowGraph:
    def __init__(self) -> None:
        self._nodes: Dict[str, Node] = {}
        self._edges: List[Edge] = []

    def add_node(self, node: Node) -> None:
        self._nodes[node.node_id] = node

    def remove_node(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)
        self._edges = [e for e in self._edges if e.source_id != node_id and e.target_id != node_id]

    def get_node(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        source_port: str = "data_out",
        target_port: str = "data_in",
    ) -> None:
        if source_id not in self._nodes or target_id not in self._nodes:
            raise ValueError(f"Node not found: {source_id} or {target_id}")
        edge = Edge(
            source_id=source_id,
            target_id=target_id,
            source_port=source_port,
            target_port=target_port,
        )
        if edge in self._edges:
            return
        self._edges.append(edge)
        if self._detect_cycle():
            self._edges.pop()
            raise CycleError("Adding this edge would create a cycle")

    def remove_edge(
        self,
        source_id: str,
        target_id: str,
        source_port: Optional[str] = None,
        target_port: Optional[str] = None,
    ) -> bool:
        for i, e in enumerate(self._edges):
            if (
                e.source_id == source_id
                and e.target_id == target_id
                and (source_port is None or e.source_port == source_port)
                and (target_port is None or e.target_port == target_port)
            ):
                self._edges.pop(i)
                return True
        return False

    def get_edges(self) -> List[Edge]:
        return list(self._edges)

    def get_nodes(self) -> Dict[str, Node]:
        return dict(self._nodes)

    def get_node_count(self) -> int:
        return len(self._nodes)

    def get_edge_count(self) -> int:
        return len(self._edges)

    def get_predecessors(self, node_id: str) -> List[Node]:
        preds: List[Node] = []
        for e in self._edges:
            if e.target_id == node_id:
                n = self._nodes.get(e.source_id)
                if n:
                    preds.append(n)
        return preds

    def get_successors(self, node_id: str) -> List[Node]:
        succs: List[Node] = []
        for e in self._edges:
            if e.source_id == node_id:
                n = self._nodes.get(e.target_id)
                if n:
                    succs.append(n)
        return succs

    def mark_dirty(self, node_id: str) -> None:
        node = self._nodes.get(node_id)
        if node:
            node.is_dirty = True
            node.cached_output_id = None
            node.error = None
        for succ in self.get_successors(node_id):
            self.mark_dirty(succ.node_id)

    def topological_order(self) -> List[str]:
        in_degree: Dict[str, int] = {}
        for nid in self._nodes:
            in_degree[nid] = 0
        for e in self._edges:
            in_degree[e.target_id] = in_degree.get(e.target_id, 0) + 1
        queue = deque([nid for nid, d in in_degree.items() if d == 0])
        result: List[str] = []
        while queue:
            nid = queue.popleft()
            result.append(nid)
            for e in self._edges:
                if e.source_id == nid:
                    in_degree[e.target_id] -= 1
                    if in_degree[e.target_id] == 0:
                        queue.append(e.target_id)
        return result

    def _detect_cycle(self) -> bool:
        return len(self.topological_order()) != len(self._nodes)

    def validate(self) -> List[str]:
        errors: List[str] = []
        for nid, node in self._nodes.items():
            has_incoming = any(e.target_id == nid for e in self._edges)
            has_outgoing = any(e.source_id == nid for e in self._edges)
            if not has_incoming and not has_outgoing and len(self._nodes) > 1:
                errors.append(f"Node {nid} is disconnected")
        if self._detect_cycle():
            errors.append("Graph contains a cycle")
        return errors

    def get_upstream(self, node_id: str) -> Set[str]:
        visited: Set[str] = set()
        stack = [node_id]
        while stack:
            nid = stack.pop()
            if nid in visited:
                continue
            visited.add(nid)
            for e in self._edges:
                if e.target_id == nid:
                    stack.append(e.source_id)
        return visited

    def get_downstream(self, node_id: str) -> Set[str]:
        visited: Set[str] = set()
        stack = [node_id]
        while stack:
            nid = stack.pop()
            if nid in visited:
                continue
            visited.add(nid)
            for e in self._edges:
                if e.source_id == nid:
                    stack.append(e.target_id)
        return visited

    def clear(self) -> None:
        self._nodes.clear()
        self._edges.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges],
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "WorkflowGraph":
        graph = cls()
        for node_payload in payload.get("nodes", []):
            node = Node.from_dict(node_payload)
            if node.node_id:
                graph.add_node(node)
        for edge_payload in payload.get("edges", []):
            edge = Edge.from_dict(edge_payload)
            if (
                edge.source_id
                and edge.target_id
                and edge.source_id in graph._nodes
                and edge.target_id in graph._nodes
            ):
                graph._edges.append(edge)
        if graph._detect_cycle():
            graph._edges.clear()
        return graph
