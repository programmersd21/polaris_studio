# Adding a Node

## Understanding the Architecture

A node in Polaris Studio has two parts:

1. **Node Type Spec** - a data descriptor in `NODE_REGISTRY` (in `core/node_registry.py`) that defines the node's identity, ports, and parameters. The registry drives the UI: the node palette, the properties panel, and the context menu all read from it.
2. **Execution Handler** - a method on the `Engine` class (in `core/engine.py`) that performs the actual data transformation. The dispatch table maps `node_type` strings to handler methods.

## Step 1: Define the Node Type Spec

Open `src/polaris_studio/core/node_registry.py` and add a new entry to the `NODE_REGISTRY` dictionary.

Required fields:

| Field          | Description                                                |
|----------------|------------------------------------------------------------|
| `node_type`    | Unique string key (lowercase, snake_case). Must match the dispatch key in the engine. |
| `display_name` | Human-readable name shown in the palette and menus.        |
| `category`     | One of: `Source`, `Transform`, `Aggregate`, `Join`, `Sort`, `Chart`, `Output`. |
| `color`        | Hex color string associated with the category.             |
| `description`  | Tooltip/help text.                                         |
| `input_ports`  | List of port names (default `["data_in"]`). Use `[]` for sources, `["data_in_left", "data_in_right"]` for joins. |
| `output_ports` | List of port names (default `["data_out"]`).              |
| `params`       | List of `NodeParamSpec` objects defining configurable parameters. |

### NodeParamSpec fields

| Field         | Description                                                       |
|---------------|-------------------------------------------------------------------|
| `name`        | Internal key (used in `node.params` dict).                        |
| `label`       | UI label shown in the properties panel.                           |
| `param_type`  | Type of widget: `string`, `filepath`, `bool`, `enum`, `column_single`, `column_multi`, `expression`, `integer`, `float`. |
| `default`     | Default value (used when no value is set).                        |
| `required`    | Whether the parameter must be provided.                           |
| `options`     | List of choices for `enum` type.                                  |
| `tooltip`     | Help text shown on hover.                                         |

## Step 2: Implement Execution

Open `src/polaris_studio/core/engine.py` and:

1. Add an entry in the `dispatch` dict inside `_execute_node`:
   ```python
   "replace_value": self._exec_replace_value,
   ```
2. Implement the handler method. The pattern is:
   ```python
   def _exec_replace_value(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
       df = self._get_input_df(graph, node)        # get upstream DataFrame
       column = node.params.get("column", "")       # read parameters
       old_val = node.params.get("old_value", "")
       new_val = node.params.get("new_value", "")
       return df.with_columns(                       # transform
           pl.when(pl.col(column) == old_val)
           .then(pl.lit(new_val))
           .otherwise(pl.col(column))
           .alias(column)
       )
   ```

The `_get_input_df` helper fetches the upstream DataFrame by tracing the edge from the given port name. The handler must always return a `pl.DataFrame`.

## Step 3: Register in UI Menu

### Canvas Context Menu

In `src/polaris_studio/ui/graph/canvas.py`, in `_show_canvas_context_menu`, add the node's key to the appropriate category list:

```python
("Transform", ["filter", "select_columns", ..., "replace_value"]),
```

### Node Palette

The palette (`ui/panels/node_palette.py`) reads `NODE_REGISTRY` automatically and groups by `category` - no manual registration needed there. If you created a new category, add it to the `cat_order` list in `_populate`.

## Full Example: Adding a "Replace Value" Node

### 1. Registry entry (`node_registry.py`)

Add inside `NODE_REGISTRY`:

```python
"replace_value": NodeTypeSpec(
    node_type="replace_value",
    display_name="Replace Value",
    category="Transform",
    color="#1d3461",
    description="Replace occurrences of a value in a column",
    params=[
        NodeParamSpec("column", "Column", "column_single", required=True),
        NodeParamSpec("old_value", "Old Value", "string", required=True,
                      tooltip="Value to replace"),
        NodeParamSpec("new_value", "New Value", "string", required=True,
                      tooltip="Replacement value"),
    ],
),
```

### 2. Engine handler (`engine.py`)

Add to the `dispatch` dict in `_execute_node`:

```python
"replace_value": self._exec_replace_value,
```

Add the method:

```python
def _exec_replace_value(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
    df = self._get_input_df(graph, node)
    column = node.params.get("column", "")
    old_val = node.params.get("old_value", "")
    new_val = node.params.get("new_value", "")
    return df.with_columns(
        pl.when(pl.col(column) == old_val)
        .then(pl.lit(new_val))
        .otherwise(pl.col(column))
        .alias(column)
    )
```

### 3. Canvas menu update (`canvas.py`)

In `_show_canvas_context_menu`, add `"replace_value"` to the Transform list.

### Complete change

```diff
--- a/src/polaris_studio/core/node_registry.py
+++ b/src/polaris_studio/core/node_registry.py
@@ -159,6 +159,20 @@ NODE_REGISTRY: Dict[str, NodeTypeSpec] = {
+    "replace_value": NodeTypeSpec(
+        node_type="replace_value",
+        display_name="Replace Value",
+        category="Transform",
+        color="#1d3461",
+        description="Replace occurrences of a value in a column",
+        params=[
+            NodeParamSpec("column", "Column", "column_single", required=True),
+            NodeParamSpec("old_value", "Old Value", "string", required=True),
+            NodeParamSpec("new_value", "New Value", "string", required=True),
+        ],
+    ),
     "filter": NodeTypeSpec(

--- a/src/polaris_studio/core/engine.py
+++ b/src/polaris_studio/core/engine.py
@@ -101,6 +101,7 @@ class Engine:
             "csv_reader": self._exec_csv_reader,
+            "replace_value": self._exec_replace_value,
             "parquet_reader": self._exec_parquet_reader,

@@ -221,6 +222,14 @@ class Engine:
         return df.filter(compiled)

+    def _exec_replace_value(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:
+        df = self._get_input_df(graph, node)
+        column = node.params.get("column", "")
+        old_val = node.params.get("old_value", "")
+        new_val = node.params.get("new_value", "")
+        return df.with_columns(
+            pl.when(pl.col(column) == old_val)
+            .then(pl.lit(new_val))
+            .otherwise(pl.col(column))
+            .alias(column)
+        )
+
     def _exec_filter(self, graph: WorkflowGraph, node: Node) -> pl.DataFrame:

--- a/src/polaris_studio/ui/graph/canvas.py
+++ b/src/polaris_studio/ui/graph/canvas.py
@@ -532,7 +532,7 @@ class GraphCanvas(QGraphicsView):
             ("Source", ["csv_reader", ...]),
             ("Transform", ["filter", "select_columns", "add_column",
                            "rename_columns", "drop_columns", "cast_column",
-                          "fill_null", "string_ops", "date_parse",
+                          "fill_null", "string_ops", "date_parse", "replace_value",
                            "sample", "slice", "deduplicate", "unpivot", "explode"]),
```

## Testing Your Node

Add a test in `tests/test_engine.py`:

```python
def test_execute_replace_value(engine: Engine) -> None:
    g = WorkflowGraph()
    src = Node("src", "manual_entry", NodeCategory.SOURCE,
               params={"data": '[{"a": "foo"}, {"a": "bar"}, {"a": "foo"}]'})
    g.add_node(src)
    rv = Node("rv", "replace_value", NodeCategory.TRANSFORM,
              params={"column": "a", "old_value": "foo", "new_value": "baz"})
    g.add_node(rv)
    g.add_edge("src", "rv")
    df = engine.execute(g, "rv")
    assert df["a"].to_list() == ["baz", "bar", "baz"]
```

Run it:

```bash
pytest tests/test_engine.py -k "replace_value" -v
```

To verify in the UI, launch the application and confirm the node appears in:

- The **right-click context menu** under Transform → Replace Value
- The **Node Palette** under Transform → Replace Value
- The **Properties Panel** when the node is selected (showing Column, Old Value, New Value fields)
