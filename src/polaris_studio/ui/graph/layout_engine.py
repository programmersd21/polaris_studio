"""Auto-layout for workflow graphs.

Computes layer positions using topological order, then arranges nodes
within each layer using a barycenter heuristic to minimize edge crossings.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

from polaris_studio.core.graph import WorkflowGraph


X_SPACING = 280.0
Y_SPACING = 110.0
LAYER_PADDING_Y = 40.0
START_X = 80.0
START_Y = 80.0


def _topological_layers(graph: WorkflowGraph) -> List[List[str]]:
    in_degree: Dict[str, int] = {nid: 0 for nid in graph.get_nodes()}
    adj: Dict[str, List[str]] = defaultdict(list)
    for edge in graph.get_edges():
        if edge.source_id in in_degree and edge.target_id in in_degree:
            in_degree[edge.target_id] += 1
            adj[edge.source_id].append(edge.target_id)
    queue: deque = deque([nid for nid, d in in_degree.items() if d == 0])
    layers: List[List[str]] = []
    placed: Set[str] = set()
    while queue:
        layer: List[str] = []
        for _ in range(len(queue)):
            nid = queue.popleft()
            if nid in placed:
                continue
            placed.add(nid)
            layer.append(nid)
        layers.append(layer)
        for nid in layer:
            for tgt in adj.get(nid, []):
                in_degree[tgt] -= 1
                if in_degree[tgt] == 0:
                    queue.append(tgt)
    if len(placed) < len(in_degree):
        leftover = [nid for nid in in_degree if nid not in placed]
        if leftover:
            layers.append(leftover)
    return layers


def _barycenter_order(layers: List[List[str]], graph: WorkflowGraph) -> List[List[str]]:
    pos_in_layer: Dict[Tuple[int, str], int] = {}
    for i, layer in enumerate(layers):
        for j, nid in enumerate(layer):
            pos_in_layer[(i, nid)] = j
    incoming: Dict[str, List[str]] = defaultdict(list)
    outgoing: Dict[str, List[str]] = defaultdict(list)
    for edge in graph.get_edges():
        if edge.source_id in pos_in_layer and edge.target_id in pos_in_layer:
            outgoing[edge.source_id].append(edge.target_id)
            incoming[edge.target_id].append(edge.source_id)

    for _ in range(8):
        for i in range(1, len(layers)):
            new_order = sorted(
                layers[i],
                key=lambda nid: (
                    sum(pos_in_layer.get((i - 1, p), 0) for p in incoming.get(nid, []))
                    / max(1, len(incoming.get(nid, [])))
                ),
            )
            layers[i] = new_order
            for j, nid in enumerate(new_order):
                pos_in_layer[(i, nid)] = j
        for i in range(len(layers) - 2, -1, -1):
            new_order = sorted(
                layers[i],
                key=lambda nid: (
                    sum(pos_in_layer.get((i + 1, p), 0) for p in outgoing.get(nid, []))
                    / max(1, len(outgoing.get(nid, [])))
                ),
            )
            layers[i] = new_order
            for j, nid in enumerate(new_order):
                pos_in_layer[(i, nid)] = j
    return layers


def auto_layout(
    graph: WorkflowGraph,
    start_x: float = START_X,
    start_y: float = START_Y,
    x_spacing: float = X_SPACING,
    y_spacing: float = Y_SPACING,
) -> Dict[str, Tuple[float, float]]:
    if graph.get_node_count() == 0:
        return {}
    layers = _topological_layers(graph)
    if not layers:
        return {}
    layers = _barycenter_order(layers, graph)

    max_layer_count = max(len(layer) for layer in layers)
    y_offset_center = start_y + (max_layer_count - 1) * y_spacing / 2

    positions: Dict[str, Tuple[float, float]] = {}
    for layer_idx, layer in enumerate(layers):
        x = start_x + layer_idx * x_spacing
        total = (len(layer) - 1) * y_spacing
        for j, nid in enumerate(layer):
            y = y_offset_center - total / 2 + j * y_spacing + LAYER_PADDING_Y
            positions[nid] = (x, y)
    return positions


def arrange_in_grid(graph: WorkflowGraph, cols: int = 4) -> Dict[str, Tuple[float, float]]:
    nodes = list(graph.get_nodes().keys())
    positions: Dict[str, Tuple[float, float]] = {}
    for i, nid in enumerate(nodes):
        row = i // cols
        col = i % cols
        positions[nid] = (START_X + col * X_SPACING, START_Y + row * Y_SPACING)
    return positions
