# The Panels

Polaris Studio has a small number of **panels** that show different views of the same underlying pipeline. They all stay in sync - change the graph and every panel updates; click a panel item and the corresponding node is selected on the canvas.

This page is a quick index. Each panel has its own deep-dive page.

## The panels

| Panel | What it shows | How to open | Where it lives |
|---|---|---|---|
| **Node Palette** | Every node type, search and browse | Always visible by default | Left dock |
| **Properties** | Parameters of the selected node | Always visible by default | Right dock |
| **Spreadsheet** | The active node's data, editable | Always visible by default | Bottom |
| **AI Assistant** | Chat with the AI about your data | Ctrl+Shift+A | Right dock |
| **Chart** | Visualisation of the active chart node | F4 | Right dock |
| **Profile** | Column-by-column statistics | Right-click a column header → Statistics | Right dock |
| **Search** | Find and replace across the grid | Ctrl+F | Bottom dock |
| **Status Bar** | Selection, row count, exec time, AI status | Always visible | Bottom |
| **Command Palette** | Quick launcher (overlay) | Ctrl+P | Centre (overlay) |

## How the panels talk to each other

Panels never reference each other directly. They all subscribe to **AppState** - a single reactive object that emits signals when things change. When you click a node on the canvas, AppState emits `node_selected`, and the Properties Panel updates. When the engine finishes a run, AppState emits `table_data_ready`, and the Spreadsheet, Chart, and Profile panels all update.

This means:

- Panels can be shown, hidden, and rearranged without breaking anything.
- You can replace any panel's contents with a different view (e.g., a future "Heatmap" panel) without touching the others.
- The same panel can be docked in different positions (left, right, bottom, floating).

To re-arrange panels: **drag a panel's title bar**. Drop it on another panel's title to tab-stack them. Drop it on a dock edge to dock them.

## Showing and hiding panels

- **View → Panels →** `<panel name>` - toggle visibility.
- **Right-click** a panel's title bar → **Hide**.
- The keyboard shortcut for the panel (if it has one) toggles it.

## Resetting the layout

If you've moved panels around and want the default back:

- **View → Reset Layout** (or **Window → Reset Layout** on some versions).

This restores the canonical arrangement: Node Palette on the left, Properties on the right, Spreadsheet on the bottom, AI/Chart/Profile/Search as dockable overlays.

## Per-panel deep dives

- **[Node Palette](#node-palette)** - see below.
- **[Properties Panel](#properties-panel)** - see below.
- **[Spreadsheet](spreadsheet.md)** - full guide.
- **[AI Assistant](ai-panel.md)** - full guide.
- **[Charts](charts.md)** - full guide for the Chart Panel and chart nodes.
- **[Command Palette](command-palette.md)** - full guide.

---

## Node Palette

The left dock. Lists every node type, grouped by category. Use the search box at the top to filter by name (fuzzy match).

**Categories:**

| Category | What it contains |
|---|---|
| **Source** | CSV Reader, Parquet Reader, JSON Reader, XLSX Reader, Clipboard Paste, Manual Entry, Cross-Tab Reference |
| **Transform** | Filter, Select Columns, Add Column, Rename Columns, Drop Columns, Cast Column, Fill Null, String Operations, Date Parse, Sample, Slice, Deduplicate, Unpivot, Explode |
| **Aggregate** | Group By Aggregate, Rolling Window, Pivot Table |
| **Join** | Inner Join, Left Join, Right Join, Full Outer Join, Cross Join, Anti Join |
| **Sort** | Sort |
| **Chart** | Bar Chart, Line Chart, Scatter Chart, Histogram, Box Chart, Heatmap |
| **Output** | Table View, Export CSV, Export Parquet, Export JSON, Export XLSX |

To add a node:

- **Drag** it onto the canvas.
- **Double-click** it (lands in the centre).
- **Right-click → Add Node →** submenu of all types.

Hover a node to see a one-line description. Right-click → **What's this?** for more detail.

### Filtering

Type in the search box. The palette filters in real time:

- "fil" → Filter, Fill Null
- "joi" → all six joins
- "csv" → CSV Reader (and anything with "csv" in the description)
- "exp" → Export CSV/Parquet/JSON/XLSX

Press **Esc** to clear the search.

---

## Properties Panel

The right dock. Shows the parameters of the currently selected node.

If no node is selected, it shows a placeholder: *"Select a node to view its properties"*.

If multiple nodes are selected, it shows only the **common** parameters (the ones every selected node has). For example, selecting two Filter nodes lets you change the expression for both at once. Selecting a Filter and a Sort shows an empty state (no common parameters).

### Layout

```
┌────────────────────────────────────┐
│  Filter                            │  ← Display name (Instrument Serif)
│  filter-2                          │  ← Type and ID (mono)
├────────────────────────────────────┤
│  Keep only rows matching a         │  ← Description
│  condition.                        │
├────────────────────────────────────┤
│  Expression                        │  ← Parameter label
│  [ pl.col('price') > 50     ] [?]  │  ← Parameter field + help button
├────────────────────────────────────┤
│  [Execute]  [Preview Output]       │  ← Actions
└────────────────────────────────────┘
```

### Parameter types

Different parameter types have different controls:

| Type | Control |
|---|---|
| **string** | Single-line text input |
| **filepath** | Text input + "..." button (opens a file dialog) |
| **bool** | Checkbox |
| **enum** | Dropdown (predefined options) |
| **integer** | Spinbox (with arrows) |
| **float** | Double-spinbox (with arrows) |
| **column_single** | Editable dropdown (lists available columns) |
| **column_multi** | Multi-select list |
| **expression** | Text input + expression editor button (opens the **[Expression Editor](#expression-editor)**) |

### Expression editor

For nodes with an `expression` parameter (Filter, Add Column, etc.), click the **?** icon next to the field to open the **Expression Editor** - a full dialog with:

- A multi-line text area with syntax highlighting.
- **Autocomplete** for Polars functions as you type.
- A **live preview** of the expression evaluated against the upstream data.
- A **schema viewer** showing available columns and their types.
- **Common snippets** (clickable inserts).

### Actions

At the bottom of the Properties Panel:

- **Execute** - run the pipeline up to and including this node. Same as **Shift+F5**.
- **Preview Output** - show this node's output in the Spreadsheet without running downstream. Useful for inspecting a long pipeline without re-running it all.

---

## Status bar

The thin strip at the very bottom. Four sections, left to right:

1. **Node info** - name and type of the currently selected node, or "No node selected".
2. **Row count** - for the active node, e.g. `Rows: 12,345`.
3. **Execution time** - for the most recent run, e.g. `Time: 47ms`. Animates a count-up from 0.
4. **AI pill** - small badge showing AI status: `Ready` (idle), `Thinking` (waiting for AI), `Off` (no key configured). Click to open the AI panel.

The status bar also shows transient messages like `Auto-layout complete`, `Loaded 1,234 rows`, `Cached: filter-2, sort-1, bar_chart-1`. These fade after a few seconds.

---

## What's next

- **[The AI assistant](ai-panel.md)** - chat, previews, auto-approve.
- **[The spreadsheet](spreadsheet.md)** - grid, formula bar, sorting, freezing.
- **[Charts](charts.md)** - bar, line, scatter, histogram, box, heatmap.
- **[Command palette](command-palette.md)** - Ctrl+P, the keyboard-first launcher.
- **[Saving and preferences](saving-and-preferences.md)** - `.polaris` files, settings, AI keys.
