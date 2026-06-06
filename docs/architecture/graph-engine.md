# Graph Engine Architecture

## WorkflowGraph

The `WorkflowGraph` class manages a DAG (Directed Acyclic Graph) of nodes connected by edges.

**Key operations:**
- `add_node()` / `remove_node()` - node lifecycle
- `add_edge()` with cycle detection via Kahn's algorithm
- `mark_dirty()` - cascading dirty flag propagation to all descendants
- `topological_order()` - returns a valid execution order

## Engine

The `Engine` class executes nodes against a graph with incremental caching.

**Execution flow:**
1. Get topological order of the graph
2. For each node up to the target: check cache
3. If dirty or not cached: dispatch to handler based on node_type
4. Store result in cache
5. Return cached result for target node

**Cache invalidation:**
- When `mark_dirty()` is called on a node, all downstream nodes are also marked dirty
- On execution, only dirty nodes are recomputed
- Clean upstream nodes use cached results

## Node Types

40+ node types in 7 categories:
- **Source**: CSV, Parquet, JSON, XLSX readers, clipboard paste
- **Transform**: Filter, select, add column, rename, drop, cast, fill null, string ops, sort, sample
- **Aggregate**: Group by, rolling window, pivot table
- **Join**: Inner, left, right, full, cross, anti
- **Chart**: Bar, line, scatter, histogram, box, heatmap
- **Output**: Table view, export CSV/Parquet/JSON/XLSX
