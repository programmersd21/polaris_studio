# Core Concepts

This page explains the mental model behind Polaris Studio. You can use Polaris without reading this, but the model is short and once you have it everything else clicks into place.

## The five things to know

1. **A pipeline is a graph of nodes.** Each node does one thing. Lines between them are data flow.
2. **Data is Polars, parameters are typed.** Behind the scenes, every node operates on a Polars `DataFrame`. Every parameter is type-checked.
3. **The graph is a DAG.** Polaris rejects cycles - A → B → A is not allowed. The graph always has a clear execution order.
4. **Caching is automatic.** Each node remembers its last output. If you change a filter, only the filter and its descendants recompute; everything upstream stays cached.
5. **The AI is just another input.** The AI emits the same typed commands you would. It cannot bypass validation, and you always see what it's about to do.

That's the whole model. The rest of this page expands each point.

---

## 1. Pipelines are graphs

A **pipeline** in Polaris is a directed graph (more specifically, a DAG) of **nodes** connected by **edges**. Each node reads data, transforms it, and emits data on its output port(s). Each edge carries a stream of rows from one node's output to another node's input.

The simplest pipeline is a single node. A two-node pipeline reads from a file and filters it. A bigger pipeline might read from three files, join them, group, chart, and export.

### What a node looks like

A node has:

- A **title** (its display name, e.g. "Filter").
- A **type ID** (e.g. `filter`). Every node type has a unique ID.
- An **instance number** (e.g. `filter-2`) for disambiguation when you have multiple of the same type.
- A **body** showing its current parameter values.
- A **status indicator** in the top-right (clean / dirty / running / success / error).
- One or more **input ports** on the left.
- One or more **output ports** on the right.

### What an edge looks like

An edge is a curve from an output port to an input port. It has a direction (always data-flow, never control-flow). During execution, the edge briefly animates to show data moving through it.

---

## 2. Data is Polars, parameters are typed

Under the hood, Polaris uses [Polars](https://pola.rs/) - a fast columnar DataFrame library. Every node reads a Polars `DataFrame` on its input, runs an operation, and emits a Polars `DataFrame` on its output.

You don't have to write Polars code, but you'll see Polars-flavored expressions in the Properties Panel for filter, add-column, and aggregate nodes. The expression `pl.col('price') > 50` is a Polars expression. See the **[Polars expressions primer](../getting-started/first-pipeline.md#polars-expressions-primer)** in the first-pipeline guide for the 5-minute version.

### Why Polars?

- **Fast.** Written in Rust, vectorised, multi-threaded.
- **Lazy.** Polaris's executor is built on Polars' lazy mode for some nodes - work is only done when needed.
- **Predictable memory.** No surprises with memory blow-up.
- **Familiar.** If you've used pandas or SQL, the mental model is close.

### Types

Polaris has a strict type system. Every column has a type - `Int64`, `Float64`, `Utf8` (string), `Boolean`, `Date`, `Datetime`, etc. The `Cast Column` node changes a column's type. The `Filter` and `Add Column` nodes use Polars expressions that are also type-checked.

If you ever see a red border on a parameter, it means the value you typed is the wrong type. The tooltip will tell you what was expected.

---

## 3. The graph is a DAG

A DAG (Directed Acyclic Graph) is a graph with direction and no cycles. Polaris enforces this:

- You cannot connect A's output to B's input if A is downstream of B.
- You cannot connect a node's output to its own input (directly or transitively).
- The `WorkflowGraph.add_edge()` method raises a `CycleError` if you try.

This means every pipeline has at least one well-defined **execution order** - a topological sort. Polaris computes this with Kahn's algorithm whenever the graph changes.

### What this means for you

- No infinite loops.
- No "where do I start?" confusion - the order is unambiguous.
- You can think of the graph as a recipe: read top to bottom (or left to right) and you have the execution order.

### Topological order

The execution order is the unique order where every node comes after all of its inputs. For this graph:

```
A → B → D
A → C → D
```

The order is `A, B, C, D` or `A, C, B, D` (both valid). Polaris picks the one that minimises re-computation, but either is correct.

---

## 4. Caching is automatic

Every node remembers its last output (a Polars DataFrame, stored in memory or spilled to Arrow IPC). When you execute a node, Polaris:

1. Computes the topological order.
2. Walks the order, **top to bottom**.
3. For each node, checks: is it **dirty**? If so, recompute. If not, use the cache.

### What is "dirty"?

A node is **dirty** if:

- It's never been executed, or
- One of its parameters changed since the last execution, or
- One of its inputs is dirty (cascading dirty propagation).

So if you change a filter, the filter is dirty. Everything downstream of the filter is also dirty. Everything upstream of the filter stays clean and uses its cache.

This makes iterative editing fast: tweak a filter, hit F5, only the filter and its descendants run.

### Visual indicator

Each node has a status dot:

| Colour | Meaning |
|---|---|
| Grey | Not yet executed |
| Yellow | Dirty (parameters or inputs changed) |
| Blue | Currently running |
| Green | Success (cached) |
| Red | Error |

### Forcing a re-run

If you want to force everything to re-run from scratch (e.g., the underlying data file changed on disk and Polaris's cache is stale), use **Run → Clear Cache** (or the command palette).

---

## 5. The AI is just another input

The AI assistant isn't a magic backdoor. It's just a different way to produce the same typed commands you would. The flow is:

1. **You type a message** in the AI panel.
2. **Polaris sends a system prompt** to the AI: "You are an assistant for a data tool. Here is the current graph. Here is the current data preview. Here is the conversation so far. Respond with either a human-readable message or a JSON command batch. Do not respond with anything else."
3. **The AI streams a response.** Polaris reads the stream token by token.
4. **If the response includes a JSON block**, Polaris:
   a. Tries to parse it as a `PipelineMutationBatch` or `AppCommandBatch`.
   b. Validates it against strict Pydantic schemas with `extra="forbid"` (unknown fields are rejected).
   c. Shows you a **preview card** with **Apply** and **Skip** buttons.
5. **If you click Apply**, Polaris executes the same commands a manual edit would execute. The graph updates, the spreadsheet updates, the AI sees the new state.

### Why this matters

- **The AI cannot bypass validation.** Invalid JSON is rejected before it touches your data.
- **You always see what it's about to do.** The preview card shows the exact actions.
- **You can edit the JSON.** Expand the **Action JSON** pill, copy it, modify it, and re-paste (advanced).
- **Self-correction.** If validation fails, Polaris tells the AI "your last response didn't validate, here's why, please retry" - and the AI gets another turn. This usually converges in 1–2 retries.

### What the AI can do

The AI can emit any of the typed commands a manual edit can produce:

- **Graph mutations:** create, update, connect, disconnect, delete, rename, execute nodes.
- **Spreadsheet mutations:** update cells, style cells, insert/delete rows.
- **Column operations:** rename, cast, fill, drop.
- **View operations:** switch modes, toggle panels.
- **Bulk operations:** set every cell in a column to a value, etc.

It cannot:

- Run arbitrary Python code.
- Read files outside the workspace.
- Make network calls (other than its own model API).
- Modify a node's internal state directly - it has to use the same command surface as you.

For the full breakdown see **[The AI assistant](ai-panel.md)**.

---

## Bonus concepts

### Multi-tab workspace

A "workspace" can hold multiple tabs. Each tab is its own independent pipeline with its own graph, scroll position, and zoom level. You can reference the output of one tab from another using the **Cross-Tab Reference** node.

To save a workspace, **Ctrl+S** saves every tab to a single `.polaris` file. To open one, **Ctrl+O** restores every tab.

### Undo and redo

Every graph mutation is recorded in a history stack with its inverse. `Ctrl+Z` applies the inverse; `Ctrl+Y` reapplies the original. The stack holds up to 100 actions. It's cleared when you open a new file or clear the graph.

Cell edits in the spreadsheet are also recorded. The undo granularity is one cell, one node, one property at a time - not "all my work in the last 5 minutes".

### Types of nodes

Polaris has 40+ node types in 7 categories. Each is a small, well-defined operation. See the **[Node reference](../nodes/reference.md)** for the full list.

### The execution lifecycle

When you press F5:

1. **Validate** - every connection is checked, every parameter is type-checked.
2. **Topological sort** - compute execution order.
3. **Walk** - for each node in order, check dirty, compute if needed.
4. **Stream** - emit results to subscribers (spreadsheet, chart panel, profile panel).
5. **Mark complete** - every node that succeeded is now "clean".

If any node errors, the pipeline stops and the error is shown in the status bar and on the offending node. You can fix the parameter and re-run; only the failed node and its descendants re-execute.

---

## Mental model summary

If you take away one thing from this page, take this:

> A Polaris pipeline is a typed, validated, cached DAG. The AI is just a way to ask the same typed mutations in plain English. Everything else - the panels, the spreadsheet, the chart - is a different lens on the same underlying graph.

Once this clicks, every other feature is just a UI on top of it.
