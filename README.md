# Polaris Studio

**A local-first, AI-native data IDE. Visual pipelines, a live spreadsheet, and an assistant that actually does the work.**

Polaris Studio lets you load, clean, transform, join, analyze, visualize, and export data by drawing a graph. Every step in your pipeline is a node you can see, move, and edit. When you don't feel like building by hand, ask the AI assistant in plain English and it will propose the exact nodes and connections. You review the plan, click Apply, and the graph updates.

Everything runs on your machine. No accounts, no telemetry, no cloud round-trips. The AI is optional and only talks to the model provider you configure (Google Gemini).

![Polaris Studio](image.png)

---

## What you can do with it

- **Load data** from CSV, Excel (XLSX), Parquet, or JSON files, or paste straight from your clipboard.
- **Clean and transform** with visual nodes: filter rows, rename columns, cast types, fill nulls, deduplicate, parse dates, slice, sample.
- **Reshape** with pivot, unpivot, explode, group-by-aggregate, and rolling windows.
- **Join datasets** side-by-side with inner, left, right, full outer, cross, and anti joins.
- **Visualize** with bar, line, scatter, histogram, box, and heatmap charts.
- **Export** back to CSV, Excel, Parquet, or JSON.
- **Use a live spreadsheet** that stays in sync with your pipeline - edit cells, sort columns, freeze rows, see column statistics.
- **Ask the AI** to build or modify your pipeline in plain English, and review every change before it touches your data.
- **Save your work** as a `.polaris` file and reopen it exactly as you left it.

---

## Quick start

### Install and run

```bash
# 1. Get the code
git clone https://github.com/programmersd21/polaris_studio
cd polaris_studio

# 2. Install (editable mode for development)
pip install -e .

# 3. Launch
polaris-studio
```

If you'd rather not install:

```bash
pip install -r requirements.txt
python src/polaris_studio/main.py
```

**Requirements:** Python 3.11 or newer. Windows, macOS, and Linux are all supported.

> **First run on Windows** may take a few extra seconds while Windows Defender scans the bundled Polars and PyArrow native libraries. This only happens once.

---

## Documentation

Polaris Studio has a complete documentation set. Pick the path that fits your goal.

### I just installed it - show me around
- **[Installation](docs/getting-started/installation.md)** - detailed setup for Windows, macOS, and Linux
- **[10-minute quick tour](docs/getting-started/quick-tour.md)** - see what Polaris can do
- **[Your first pipeline](docs/getting-started/first-pipeline.md)** - step-by-step: load a file, filter, chart, export
- **[Interface tour](docs/getting-started/interface-tour.md)** - every panel, button, and mode explained
- **[Keyboard shortcuts](docs/getting-started/keyboard-shortcuts.md)** - full shortcut reference

### I want to actually use it
- **[Core concepts](docs/user-guide/concepts.md)** - nodes, connections, dirty propagation, caching
- **[The graph canvas](docs/user-guide/canvas.md)** - pan, zoom, select, layout
- **[The panels](docs/user-guide/panels.md)** - node palette, properties, AI, chart, profile, search
- **[The AI assistant](docs/user-guide/ai-panel.md)** - chat, previews, auto-approve, safety
- **[The spreadsheet](docs/user-guide/spreadsheet.md)** - grid, formula bar, sorting, freezing, stats
- **[Charts](docs/user-guide/charts.md)** - bar, line, scatter, histogram, box, heatmap; export to PNG/SVG
- **[Command palette](docs/user-guide/command-palette.md)** - Ctrl+P, the keyboard-first launcher
- **[Saving and preferences](docs/user-guide/saving-and-preferences.md)** - `.polaris` files, settings, AI keys

### I need a specific node
- **[Node reference](docs/nodes/reference.md)** - every node type, what it does, every parameter

### I'm a developer
- **[Developer setup](docs/developer/setup.md)** - repo, dev install, IDE config
- **[Testing](docs/developer/testing.md)** - pytest, mypy, ruff
- **[Adding a new node type](docs/developer/adding-a-node.md)** - registry, handler, palette, properties
- **[API reference](docs/developer/api-reference.md)** - public classes and methods

### I want to understand how it works
- **[Architecture overview](docs/architecture/overview.md)** - layers, principles, data flow
- **[Graph engine](docs/architecture/graph-engine.md)** - DAG execution, caching, dirty propagation
- **[AI pipeline](docs/architecture/ai.md)** - schema-validated commands, self-correction
- **[State management](docs/architecture/state.md)** - AppState, Workspace, history
- **[IPC layer](docs/architecture/ipc.md)** - multi-process compute, Arrow transport
- **[Design system](docs/reference/design-system.md)** - typography, palette, motion

### Something is broken
- **[Common issues](docs/troubleshooting/common-issues.md)** - fonts, AI keys, slow imports
- **[FAQ](docs/troubleshooting/faq.md)** - short answers to frequent questions

---

## Highlights

### Visual pipelines
Every operation - loading a file, filtering rows, joining tables - is a node. Drag nodes from the left palette onto the canvas, connect their ports, and hit **F5** to run. The result flows through the pipeline automatically. Downstream nodes are smart: if you change a filter, only what's downstream is recomputed; everything upstream stays cached.

### Live spreadsheet
A full spreadsheet sits below the graph. It shows the output of whatever node you last executed or previewed. Edit cells directly, sort columns, freeze the top row, right-click for column statistics, jump to the source node. The grid is virtualised, so it stays responsive past a million rows.

### AI assistant
Press **Ctrl+Shift+A** to open the AI panel. Type in plain English: *"Add a column that multiplies price by quantity and call it revenue, then filter where revenue > 10000."* The AI proposes a structured action plan as JSON, validated against strict typed schemas, and shown to you as a preview card with **Apply** and **Skip** buttons. The AI never gets to touch your data directly - every action goes through the same validation and execution path as a manual edit.

### 40+ node types
Sources, transforms, aggregations, joins, sorts, charts, and outputs. All the building blocks you need for real data work, plus a few nice extras like a `cross_tab_ref` node for referencing another tab's output, a `manual_entry` node for typing a table by hand, and a `clipboard_paste` node for grabbing data straight from Excel or Google Sheets.

### Multi-tab workspace
Each tab holds its own independent graph. Reference another tab's output with a `cross_tab_ref` node. Save all tabs to a single `.polaris` JSON file and reopen them exactly as you left them.

### 100% offline (except AI)
Zero network calls on startup. The only outbound traffic is to the AI provider you configure (Google Gemini, your own API key). No accounts, no telemetry, no "call home".

---

## Tech stack

| Layer | What | Why |
|---|---|---|
| Engine | Polars on Apache Arrow | Fast columnar compute, lazy evaluation, predictable memory |
| Graph editor | PySide6 `QGraphicsView` | Hardware-accelerated, custom-rendered, minimal overhead |
| Spreadsheet | Qt `QAbstractTableModel` | Virtualised rows, smooth scroll past a million rows |
| AI | Google Gemini (via official SDK) | Streaming, structured output, your own key |
| Compute | Multi-process worker | Heavy jobs never block the UI |
| Transport | Arrow IPC + JSON | Zero-copy DataFrame handoff between processes |

---

## Project layout

```
polaris_studio/
├── src/polaris_studio/
│   ├── core/           # Headless engine: DAG, executor, node registry, profiler
│   ├── ipc/            # Multi-process compute: protocol + worker
│   ├── io/             # File handlers: CSV, Parquet, XLSX, clipboard
│   ├── agent/          # AI: schemas, interpreter, chat session, backend
│   ├── state/          # AppState, Workspace (multi-tab), HistoryStack
│   ├── ui/             # PySide6 widgets, panels, dialogs, graph view
│   ├── main.py         # CLI entry point
│   └── __main__.py     # GUI entry point
├── assets/theme.qss    # Global stylesheet
├── fonts/              # Bundled Inter, Outfit, Instrument Serif, JetBrains Mono
├── tests/              # 50+ pytest tests
└── docs/               # You are here
```

---

## Development

```bash
pip install -e ".[dev]"
pytest                    # run tests
mypy .                    # type check
ruff check src/           # lint
```

See **[Developer setup](docs/developer/setup.md)** and **[Adding a new node type](docs/developer/adding-a-node.md)** for the full guide.

---

## Contributing

Bug reports, feature requests, and pull requests are welcome. Read **[CONTRIBUTING.md](CONTRIBUTING.md)** for the workflow and **[Adding a new node type](docs/developer/adding-a-node.md)** for the most common type of contribution.

---

## License

MIT - free to use, modify, and distribute.
