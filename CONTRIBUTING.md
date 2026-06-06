# Contributing

## Development Setup

```bash
git clone https://github.com/programmersd21/polaris_studio
cd polaris-studio
pip install -e ".[dev]"
```

## Code Style

- **Python**: 3.11+ with full type annotations
- **Formatter**: `ruff check src/`
- **Type Checker**: `mypy src/ --strict`
- **Line Length**: 100 characters
- **Style**: Follow existing patterns in the codebase

## Testing

```bash
pytest tests/ -v
```

### Test Categories

- `test_graph.py`: DAG operations, cycle detection, topological order
- `test_engine.py`: Pipeline execution, caching, dirty propagation
- `test_io.py`: CSV/Parquet round-trip correctness
- `test_agent.py`: Mutation batch execution, validation, cycle safety

## Architecture Notes

### Adding a New Node Type

1. Add spec to `core/node_registry.py` - define params, ports, category
2. Add handler to `core/engine.py` - implement the Polars operation
3. The node is automatically available in the palette and properties panel

### No-Import Rules

- `core/*`, `ipc/*`, `io/*` must never import PySide6
- `worker.py` must never import anything from `ui/`

### Signal Wiring

All inter-panel communication must use AppState Qt signals. No panel should directly reference another panel.
