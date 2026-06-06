# Architecture Overview

Polaris Studio is a desktop data application built entirely in Python with PySide6 (Qt for Python). It follows a layered architecture with strict separation of concerns.

## Layer Diagram

```
+----------------------------------------------------------------+
|                      UI Layer (PySide6)                         |
|  Main Window | Graph Canvas | Spreadsheet Grid | Panels | Dialogs |
+----------------------------------------------------------------+
|                    State Layer (Signals + History)              |
|  AppState | Workspace (Multi-tab) | HistoryStack (Undo/Redo)   |
+----------------------------------------------------------------+
|                    Agent Layer (AI Commands)                    |
|  Schemas | Interpreter | ChatSession | AIBackend               |
+----------------------------------------------------------------+
|              Core Layer (Headless, no GUI imports)              |
|  Graph (DAG) | Engine (Polars) | NodeRegistry | Profiler       |
+----------------------------------------------------------------+
|              IPC Layer (Multi-process Compute)                  |
|  Protocol (Arrow) | Worker (Isolated process)                  |
+----------------------------------------------------------------+
|              I/O Layer (Local, zero API calls)                  |
|  CSV | Parquet | XLSX (openpyxl) | Clipboard (TSV)            |
+----------------------------------------------------------------+
```

## Design Principles

1. **No GUI imports in core/ipc/io layers** - the engine runs in an isolated worker process
2. **Push-based state** - all updates flow through AppState Qt signals
3. **Single source of truth** - NODE_REGISTRY defines all node types
4. **Local-first** - zero network calls on startup, no required accounts
5. **Keyboard-first** - every action has a keyboard shortcut + command palette entry
