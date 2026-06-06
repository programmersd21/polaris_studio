# State Management

## AppState (Central Singleton)

`AppState` is a QObject that serves as the single source of truth for all application state. All inter-panel communication flows through AppState's Qt signals.

**Signals:**
- `node_selected` - emitted when node selection changes
- `graph_changed` - emitted when the graph structure changes
- `table_data_ready` - emitted when compute results arrive
- `compute_started/finished/error` - execution lifecycle

## Workspace (Multi-Tab)

`Workspace` manages multiple independent WorkflowGraph instances (tabs).

**Features:**
- Tab creation, closing, reordering, renaming
- Each tab has its own graph, scroll position, zoom level
- Save/load all tabs to a single `.polaris` ZIP file containing `workflow.json` (pipeline metadata) + embedded data files (`data/*`)
- Cross-tab references via CrossTabRef node type

## HistoryStack (Undo/Redo)

Every graph mutation records an inverse action. `undo()` applies the inverse, `redo()` re-applies the original.

- Max 100 actions in stack
- Cleared on graph clear
- Signals `can_undo` / `can_redo` state changes
