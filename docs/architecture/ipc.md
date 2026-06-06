# IPC Architecture

## Design

Polaris Studio uses a multi-process architecture. The GUI runs in the main process, while all data computation is executed in an isolated worker process.

This ensures:
- Heavy computation never blocks the UI thread
- Memory-intensive Polars operations don't affect GUI responsiveness
- Worker can be killed/restarted independently

## Protocol

- **Transport**: `multiprocessing.Connection` (pipe)
- **Serialization**: JSON for IPCCommand/IPCResult, base64 for Arrow payloads
- **Data transfer**: Arrow IPC (PyArrow streams) for DataFrames
- **Commands**: EXECUTE_NODE, EXECUTE_ALL, PROFILE_NODE, GET_PREVIEW, PING, SHUTDOWN

## Data Flow

1. GUI serializes `WorkflowGraph` to JSON-compatible data
2. Sends `IPCCommand` with graph data to worker
3. Worker deserializes graph, runs Engine, serializes result as JSON + Arrow
4. Sends `IPCResult` with Arrow buffer back to GUI
5. GUI deserializes Arrow to Polars DataFrame, updates model
