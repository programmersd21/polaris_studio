# Interface Tour

This is a walkthrough of every visible part of the Polaris Studio window. If you've finished the **[Quick tour](quick-tour.md)**, you can read this for reference any time you encounter something unfamiliar.

---

## The window at a glance

```
┌─────────────────────────────────────────────────────────────────────┐
│  File  Edit  View  Nodes  Run  Window  Help                          │ ← Menu bar
├─────────────────────────────────────────────────────────────────────┤
│  [New] [Open] [Save] | [Undo] [Redo] | [Execute ▶] | [AI ✨] | ...  │ ← Toolbar
├──────────┬─────────────────────────────────────┬────────────────────┤
│          │                                     │                    │
│  Node    │                                     │   Properties       │
│  Palette │           Graph Canvas              │     Panel          │
│  (left)  │            (center)                 │     (right)        │
│          │                                     │                    │
│  Search  │   [nodes with ports & connections]  │   - Header         │
│  ──────  │                                     │   - Type / ID      │
│  ▸ Source│                                     │   - Description    │
│  ▸ Trans │                                     │   - Parameters     │
│  ▸ Agg   │                                     │   - [Execute]      │
│  ▸ Join  │                                     │                    │
│  ▸ Sort  │                                     │                    │
│  ▸ Chart │                                     │                    │
│  ▸ Output│                                     │                    │
│          │                                     │                    │
├──────────┴─────────────────────────────────────┴────────────────────┤
│                                                                      │
│                       Spreadsheet Grid                                │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Row │ Col A   │ Col B   │ Col C   │ ...                       │ │
│  │  1   │ value   │ value   │ value   │                           │ │
│  │  2   │ ...     │ ...     │ ...     │                           │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  Formula bar:  A1:  =  some expression...                            │
├──────────────────────────────────────────────────────────────────────┤
│  No node selected  ·  Rows: 1,234  ·  Time: 47ms  ·  AI  Ready      │ ← Status bar
└──────────────────────────────────────────────────────────────────────┘
```

Below the main window there are also **dockable panels** you can show or hide:

- **AI Assistant** (Ctrl+Shift+A) - chat with the AI about your data.
- **Chart Panel** (F4) - interactive view of the active chart node's output.
- **Profile Panel** - column-by-column statistics and histograms.
- **Search Panel** (Ctrl+F) - find-and-replace across the grid.

---

## Menu bar

### File
- **New** (Ctrl+N) - start a fresh empty pipeline in a new tab.
- **Open** (Ctrl+O) - open a `.polaris` file.
- **Save** (Ctrl+S) - save the current pipeline to a `.polaris` file.
- **Save As** (Ctrl+Shift+S) - save under a new name.
- **Import → CSV / Parquet / JSON / XLSX / Clipboard** - load a file or paste from clipboard.
- **Export → CSV / Parquet / JSON / XLSX** - write the active output to disk.
- **Recent Files** - your last 10 pipelines.
- **Exit** (Ctrl+Q) - close Polaris.

### Edit
- **Undo** (Ctrl+Z) - undo the last graph mutation.
- **Redo** (Ctrl+Y or Ctrl+Shift+Z) - redo.
- **Cut / Copy / Paste** (Ctrl+X / Ctrl+C / Ctrl+V) - clipboard for selected nodes.
- **Duplicate** (Ctrl+D) - duplicate the current selection.
- **Delete** (Del) - delete the current selection.
- **Select All** (Ctrl+A) - select every node.
- **Find** (Ctrl+F) - open the Search Panel.

### View
- **Panels → AI / Chart / Profile / Search** - toggle each panel.
- **Mode → Graph / Spreadsheet / Split** - switch the main view layout.
- **Zoom → In / Out / Fit / 100%** - canvas zoom controls.
- **Toggle Grid** (Ctrl+G) - show or hide the snap grid.
- **Toggle Minimap** - show or hide the corner minimap.
- **Fullscreen** (F11) - distraction-free.

### Nodes
- **Add Node →** submenu of all 40+ node types, alphabetised.
- **Auto Layout** (Ctrl+Shift+L) - re-tidy node positions.
- **Group** (Ctrl+G with nodes selected) - group selected nodes.
- **Ungroup** (Ctrl+Shift+G) - ungroup.

### Run
- **Execute All** (F5) - run the whole pipeline.
- **Execute Up To Here** (Shift+F5) - run up to and including the selected node.
- **Cancel** - stop the running pipeline.
- **Clear Cache** - drop all cached results (forces a full re-run next time).

### Window
- **New Tab** (Ctrl+T) - open a new pipeline tab.
- **Close Tab** (Ctrl+W) - close the current tab.
- **Tab list** - switch between open tabs.
- **Reset Layout** - restore the default panel arrangement.

### Help
- **Documentation** - open this doc set in your browser.
- **Keyboard Shortcuts** (Shift+?) - in-app shortcut reference.
- **About Polaris Studio** - version info, license.

---

## Toolbar

The toolbar is a quick-access strip below the menu. Buttons (left to right):

- **New / Open / Save** - file operations.
- **Undo / Redo** - history.
- **Execute** ▶ - run the pipeline (F5).
- **Cancel** ⏹ - stop a running pipeline.
- **AI** ✨ - toggle the AI panel.
- **Search** 🔍 - open the Search Panel.
- **Layout** - auto-arrange nodes.
- **Mode** - switch view mode (Graph / Spreadsheet / Split).

You can customise the toolbar via **View → Customize Toolbar** (right-click on the toolbar).

---

## Node palette (left)

The palette lists every node type, grouped by category. Click a category header to expand or collapse it. Type in the **search box** at the top to filter by name.

Categories:

| Category | What it contains |
|---|---|
| **Source** | CSV, Parquet, JSON, XLSX readers, Clipboard paste, Manual entry, Cross-tab reference |
| **Transform** | Filter, Select columns, Add column, Rename, Drop, Cast, Fill null, String ops, Date parse, Sample, Slice, Deduplicate, Unpivot, Explode |
| **Aggregate** | Group-by-aggregate, Rolling window, Pivot table |
| **Join** | Inner, left, right, full outer, cross, anti |
| **Sort** | Sort |
| **Chart** | Bar, line, scatter, histogram, box, heatmap |
| **Output** | Table view, Export CSV/Parquet/JSON/XLSX |

To use a node:

1. **Drag** it onto the canvas, or
2. **Double-click** it (it lands at the centre of the canvas), or
3. **Search** and press **Enter** on the highlighted result.

To see what a node does without adding it: hover over it to see a tooltip with a one-line description. Right-click → **What's this?** for a longer one.

---

## Graph canvas (centre)

The canvas is where you build pipelines. Each **node** is a box with:

- A **title** at the top (the node type and an instance number).
- A **status dot** in the top-right corner (grey = not executed, blue = running, green = success, red = error, yellow = dirty).
- **Input ports** on the left (where data comes in).
- **Output ports** on the right (where data goes out).
- A **body** showing the current parameter values.

Lines between nodes are **edges**. They have a direction (data flows from output to input) and animate during execution.

### Canvas controls

- **Pan:** hold **middle mouse** and drag, or hold **space** and drag with the left mouse.
- **Zoom:** **Ctrl + scroll wheel** (or **Ctrl + + / -**), or use the zoom controls in the toolbar.
- **Fit to screen:** **F** key, or **Ctrl+0**.
- **100%:** **Ctrl+1**.
- **Select a node:** click it.
- **Multi-select:** hold **Shift** and click, or drag a box.
- **Pan to a node:** right-click the node → **Reveal in Canvas** (useful after `Find`).
- **Minimap:** bottom-right corner; click anywhere on it to jump there.

### Snap grid

By default, nodes snap to an invisible grid when you drag them. This keeps things tidy. Toggle it with **Ctrl+G**.

---

## Properties panel (right)

When you select a node, the Properties panel shows:

- **Node header** (in Instrument Serif, the editorial typeface) - the display name.
- **Type and ID** - e.g., `filter  |  filter-2`. The ID is unique and stable.
- **Description** - what the node does, in plain English.
- **Parameters** - the configurable inputs. Each has a label, a control, and often a `?` icon that opens the expression editor.
- **Execute button** - run the pipeline up to and including this node.
- **Preview Output** - show this node's output in the spreadsheet (without running downstream).

The panel updates as you edit. Changes are saved on **Enter** or when you click outside the field. Invalid values show a red border and a tooltip explaining the issue.

---

## Spreadsheet grid (bottom)

A live, editable grid that mirrors the output of the most recently executed node. Features:

- **Virtual scrolling** - handles millions of rows smoothly.
- **Click a header** to sort by that column.
- **Shift+click a header** to add a secondary sort.
- **Drag a header** to reorder columns.
- **Right-click a header** for context actions:
  - Sort ascending / descending / clear sort
  - Hide / show column
  - Rename column
  - Cast type (int, float, string, date, etc.)
  - Column statistics (opens the **Profile Panel** for that column)
  - Fill nulls (forward, backward, literal, mean, median)
  - Drop column
- **Double-click a cell** to edit it. The change is recorded and can be undone.
- **Right-click a row** to delete it, insert rows above, or copy.
- **Drag a row number** to freeze the top row (and any other rows above the freeze line).
- **Drag a column letter** to freeze the leftmost column.
- **Ctrl+scroll** to zoom the cell font size.

Above the grid is a **formula bar** showing the current cell reference (e.g., `B5`) and its content. Type an expression starting with `=` to evaluate it for the active cell, or type plain text to set the cell's value.

---

## Formula bar

Sits between the canvas and the grid. Shows the currently selected cell's reference and content. Type:

- Plain text - sets the cell value.
- An expression starting with `=` - evaluated as a Python expression over the active row.
- Press **Alt+Enter** to switch into **NLP mode** - the bar becomes a "describe what you want" prompt and the result is parsed and applied.

---

## Status bar (very bottom)

Four sections, left to right:

1. **Node info** - name and type of the currently selected node, or "No node selected".
2. **Row count** - `Rows: 12,345` for the active node.
3. **Execution time** - `Time: 47ms` for the most recent run.
4. **AI pill** - small badge showing AI status (Ready / Thinking / Off). Click it to open the AI panel.

The status bar also shows transient messages like `Auto-layout complete` or `Loaded 1,234 rows`.

---

## AI panel (right dock)

Open with **Ctrl+Shift+A** or click the ✨ button.

Layout (top to bottom):

- **Header** - "AI Assistant" in Instrument Serif, with a **Polaris** badge and a **Settings** button.
- **Conversation** - your message bubbles on the right, AI bubbles on the left. AI bubbles have a blinking ▋ cursor while streaming.
- **Action preview cards** - when the AI proposes changes, an **ActionPreviewCard** appears. It shows the proposed changes, has an **Apply** button (executes them) and a **Skip** button (discards them). An **Action JSON** pill expands to show the exact validated JSON.
- **Input area** - text box at the bottom, with a **Send** button. The **+** button attaches the currently selected node as context.

See **[The AI assistant](../user-guide/ai-panel.md)** for the full guide.

---

## Chart panel (right dock)

Open with **F4** or **View → Panels → Chart**.

Layout:

- **Toolbar** - chart type dropdown (Bar / Line / Scatter / Histogram / Box / Heatmap), **Export PNG**, **Export SVG**.
- **Plot** - the actual chart, rendered with pyqtgraph. Interactive: pan with middle-drag, zoom with scroll, autoscale with double-click.
- **Empty state** - "No data. Connect a node to see its chart." when there's no active chart node.

See **[Charts](../user-guide/charts.md)** for details.

---

## Profile panel (right dock)

Open via **View → Panels → Profile** or right-click a column header → **Show Statistics**.

Shows column-by-column statistics:

- Type, null count, null percent, unique count.
- Min, max, mean, median, std (for numeric columns).
- Top 5 most-frequent values (with counts).
- A small **histogram** for numeric columns.

See **[The spreadsheet](../user-guide/spreadsheet.md)** for the full guide.

---

## Search panel (bottom dock)

Open with **Ctrl+F** or **Edit → Find**.

Two tabs:

- **Search** - type to find matching cells across the active grid. Results appear in a list below, click to jump.
- **Replace** - find and replace. Options: case sensitive, whole word, scope (current column / all columns / selected range).

---

## Command palette (overlay)

Open with **Ctrl+P** (or **Ctrl+Shift+P**).

A small text box appears in the centre of the screen. Type to filter the list of all available actions. Each action has a label, a category, and optionally a keyboard shortcut. Press **Enter** to run, **Esc** to close.

Examples:

- `execute` → Execute All, Execute Up To, Clear Cache, etc.
- `save` → Save, Save As, Open, New
- `ai` → Toggle AI Panel, Open AI Settings
- `view` → Mode → Graph, Mode → Spreadsheet, Mode → Split
- `node` → Add Node, Auto Layout, Group, Ungroup

This is the fastest way to do anything in Polaris. If you forget a shortcut, press Ctrl+P and start typing.

---

## View modes

The main view (above the spreadsheet) can be in one of three modes. Toggle with **F1** (Spreadsheet), **F2** (Graph), **F3** (Split).

- **Graph mode** - full-screen canvas, no spreadsheet.
- **Spreadsheet mode** - full-screen grid, no canvas.
- **Split mode** - canvas on top, grid on bottom, resizable divider.

Most of the time you'll want Split.

---

## Multi-tab workspace

The window has a tab bar at the top of the canvas (just below the toolbar). Each tab holds an independent pipeline. To manage tabs:

- **New tab:** Ctrl+T
- **Close tab:** Ctrl+W
- **Rename tab:** double-click the tab title.
- **Reorder:** drag the tab.
- **Switch:** Ctrl+Tab (next) / Ctrl+Shift+Tab (previous), or click.

To reference the output of one tab from another, use the **Cross-Tab Reference** node (under **Source**). Select the target tab and the source node, and the data flows across.

---

## Where to go next

- **[Core concepts](../user-guide/concepts.md)** - the mental model under the hood.
- **[Keyboard shortcuts](keyboard-shortcuts.md)** - speed it up.
- **[Node reference](../nodes/reference.md)** - every node, every parameter.
- **[The AI assistant](../user-guide/ai-panel.md)** - chat, previews, auto-approve.
