from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from polaris_studio.agent.schemas import (
    ConnectAction,
    CreateNodeAction,
    DeleteNodeAction,
    DisconnectAction,
    ExecuteNodeAction,
    GraphMutation,
    PipelineMutationBatch,
    SelectNodeAction,
    UpdateNodeAction,
)
from polaris_studio.core.graph import CycleError, Node, NodeCategory, WorkflowGraph
from polaris_studio.core.node_registry import NODE_REGISTRY

logger = logging.getLogger(__name__)


class AgentInterpreter:
    def __init__(self, graph: WorkflowGraph) -> None:
        self._graph = graph

    def apply_batch(self, batch: PipelineMutationBatch) -> List[Tuple[str, Optional[str]]]:
        results: List[Tuple[str, Optional[str]]] = []
        for mutation in batch.mutations:
            try:
                self._apply_one(mutation)
                action_label = self._get_action_label(mutation)
                results.append((action_label, None))
            except (ValueError, CycleError) as e:
                error = str(e)
                logger.error(f"Mutation failed: {error}")
                results.append((self._get_action_label(mutation), error))
                break
            except Exception as e:
                error = f"Unexpected error: {e}"
                logger.error(error)
                results.append((self._get_action_label(mutation), error))
                break
        return results

    def _apply_one(self, mutation: GraphMutation) -> None:
        if isinstance(mutation, CreateNodeAction):
            spec = NODE_REGISTRY.get(mutation.node_type)
            if spec is None:
                raise ValueError(f"Unknown node type: {mutation.node_type}")
            cat_map = {
                "source": NodeCategory.SOURCE,
                "transform": NodeCategory.TRANSFORM,
                "filter": NodeCategory.FILTER,
                "aggregate": NodeCategory.AGGREGATE,
                "join": NodeCategory.JOIN,
                "sort": NodeCategory.SORT,
                "chart": NodeCategory.CHART,
                "output": NodeCategory.OUTPUT,
            }
            category = cat_map.get(spec.category.lower(), NodeCategory.TRANSFORM)
            node = Node(
                node_id=mutation.node_id,
                node_type=mutation.node_type,
                category=category,
                params=mutation.params,
                position=(mutation.position_x, mutation.position_y),
            )
            self._graph.add_node(node)

        elif isinstance(mutation, UpdateNodeAction):
            existing = self._graph.get_node(mutation.node_id)
            if existing is None:
                raise ValueError(f"Node not found: {mutation.node_id}")
            existing.params[mutation.param_name] = mutation.value
            self._graph.mark_dirty(mutation.node_id)

        elif isinstance(mutation, DeleteNodeAction):
            self._graph.remove_node(mutation.node_id)

        elif isinstance(mutation, ConnectAction):
            self._graph.add_edge(
                mutation.source_id,
                mutation.target_id,
                mutation.source_port,
                mutation.target_port,
            )

        elif isinstance(mutation, DisconnectAction):
            self._graph.remove_edge(
                mutation.source_id,
                mutation.target_id,
                mutation.source_port,
                mutation.target_port,
            )

        elif isinstance(mutation, SelectNodeAction):
            # Selection is handled at the UI level, not in the graph model
            pass

        elif isinstance(mutation, ExecuteNodeAction):
            # Execution is handled separately via the Engine class
            # This mutation type is informational only
            pass

    def _get_action_label(self, mutation: GraphMutation) -> str:
        mapping = {
            CreateNodeAction: f"create_node:{mutation.node_id}"
            if hasattr(mutation, "node_id")
            else "create_node",
            UpdateNodeAction: f"update_node:{mutation.node_id}"
            if hasattr(mutation, "node_id")
            else "update_node",
            DeleteNodeAction: f"delete_node:{mutation.node_id}"
            if hasattr(mutation, "node_id")
            else "delete_node",
            ConnectAction: "connect" if hasattr(mutation, "source_id") else "connect",
            DisconnectAction: "disconnect" if hasattr(mutation, "source_id") else "disconnect",
            SelectNodeAction: f"select_node:{mutation.node_id}"
            if hasattr(mutation, "node_id")
            else "select_node",
            ExecuteNodeAction: f"execute_node:{mutation.node_id}"
            if hasattr(mutation, "node_id")
            else "execute_node",
        }
        return mapping.get(type(mutation), str(mutation))

    def validate_batch(self, batch: PipelineMutationBatch) -> List[str]:
        warnings: List[str] = []
        for mutation in batch.mutations:
            if isinstance(mutation, CreateNodeAction):
                if self._graph.get_node(mutation.node_id):
                    warnings.append(f"Node {mutation.node_id} already exists, will overwrite")
                if mutation.node_type not in NODE_REGISTRY:
                    warnings.append(f"Unknown node type: {mutation.node_type}")
            elif isinstance(
                mutation, (UpdateNodeAction, DeleteNodeAction, ConnectAction, DisconnectAction)
            ):
                if isinstance(mutation, (UpdateNodeAction, DeleteNodeAction)):
                    if not self._graph.get_node(mutation.node_id):
                        warnings.append(f"Node {mutation.node_id} does not exist")
                elif isinstance(mutation, (ConnectAction, DisconnectAction)):
                    if not self._graph.get_node(mutation.source_id):
                        warnings.append(f"Source node {mutation.source_id} does not exist")
                    if not self._graph.get_node(mutation.target_id):
                        warnings.append(f"Target node {mutation.target_id} does not exist")
        return warnings
