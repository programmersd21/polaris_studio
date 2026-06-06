# Testing Guide

## Running Tests

```bash
pytest tests/              # all tests
pytest tests/ -v           # verbose output
pytest tests/test_graph.py # single file
pytest -k "filter"         # keyword match (e.g., -k "engine or graph")
```

## Writing Tests

- **Location**: Test files go in `tests/`, mirroring the `src/` structure (e.g., `tests/test_graph.py` tests `src/polaris_studio/core/graph.py`).
- **Naming**: Test functions start with `test_`. Test files start with `test_`.
- **Fixtures**: Use `@pytest.fixture` for shared setup. Reusable fixtures (like `engine`, `sample_graph`) are defined in each test module.
- **Mocking Qt/PySide6**: UI tests can use `pytest-qt` or manually instantiate widgets with `QApplication([])` in a fixture. Core logic (graph, engine, agent) is pure Python and needs no mocking.

Example fixture pattern:

```python
@pytest.fixture
def engine() -> Engine:
    return Engine()

@pytest.fixture
def sample_graph() -> WorkflowGraph:
    g = WorkflowGraph()
    src = Node("src", "manual_entry", NodeCategory.SOURCE,
               params={"data": '[{"a": 1, "b": "x"}]'})
    g.add_node(src)
    return g
```

## Type Checking

```bash
mypy .                          # full project
mypy src/polaris_studio/core/   # single directory
```

The project uses a relaxed mypy config (`strict = false`). Key overrides ignore libraries without stubs (`openpyxl`, `pyqtgraph`).

## Code Quality

- **ruff** for linting and formatting (line length: 100, target: py311):
  ```bash
  ruff check src/
  ruff format src/
  ```
- **Coverage** with pytest-cov:
  ```bash
  pip install pytest-cov
  pytest tests/ --cov=src/polaris_studio
  ```

## CI Pipeline

A GitHub Actions workflow runs on every push/PR:

1. Lint with `ruff check src/`
2. Type-check with `mypy src/`
3. Test with `pytest tests/ --cov=src/polaris_studio`

## Test Patterns

### Graph Tests (`tests/test_graph.py`)

- **Node CRUD**: `test_add_node`, `test_remove_node` - verify node insertion/removal and automatic edge cleanup.
- **Edge CRUD**: `test_add_edge`, `test_remove_edge` - verify edge creation/deletion with port parameters.
- **Cycle Detection**: `test_cycle_detection` - verify `CycleError` is raised for cycles.
- **Topological Sort**: `test_topological_order` - verify correct ordering.
- **Dirty Propagation**: `test_mark_dirty_cascades` - verify `mark_dirty` cascades to downstream nodes.
- **Upstream/Downstream**: `test_upstream_downstream` - verify traversal helpers.
- **Serialization**: Methods `to_dict` / `from_dict` are used in workspace save/load but can be tested directly.

### Engine Tests (`tests/test_engine.py`)

- **Execution**: `test_execute_source`, `test_execute_filter`, `test_execute_add_column` - verify individual node types produce correct DataFrames.
- **Pipeline**: `test_pipeline_execution` - test a multi-node pipeline (source → filter → add column → sort).
- **Cache**: `test_cache`, `test_dirty_cache_invalidation` - verify caching behavior and node dirty state.
- **AGgregation**: `test_group_by_agg` - verify group-by + aggregate execution.
- **Execute All**: `test_execute_all` - test the bulk execution path.
- **Error Handling**: `test_unknown_node_type` - verify graceful error on unknown types.

### Agent Tests (`tests/test_agent.py`)

- Schema validation for agent commands
- Command pipeline execution

### I/O Tests (`tests/test_io.py`)

- **Roundtrip**: `test_csv_roundtrip`, `test_parquet_roundtrip` - write then read, verify shape and data.
- **Custom Delimiters**: `test_csv_custom_delimiter` - verify semicolon-delimited read/write.
- **Edge Cases**: `test_empty_csv`, `test_csv_no_header` - verify empty file and no-header scenarios.
- **Compression**: `test_parquet_compression` - verify zstd compression roundtrip.

### Canvas Tests

- Drop events: simulate a drag-drop from the node palette and verify `node_create_requested` is emitted with the correct node type and snapped position.

### Adding Tests for a New Feature

1. Create `tests/test_<module>.py` or add to an existing test file.
2. For a new node type: add an engine test (create graph with the node, execute, assert DataFrame shape/values).
3. For UI changes: write unit tests for the underlying logic; use manual QA or screenshot tests for visual changes.
