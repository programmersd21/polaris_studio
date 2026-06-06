# Command Palette

The command palette is the fastest way to do anything in Polaris. It's an overlay that appears in the centre of the screen with a single text input. Type to filter the list of all available actions. Press **Enter** to run.

## Open it

- **Ctrl+P** (or **Cmd+P** on macOS) - open the command palette.
- **Ctrl+Shift+P** - same thing (alternative).
- From the menu: **View → Command Palette**.

A small text box appears in the centre of the screen. The current window stays visible behind it; the canvas is greyed out slightly.

## How to use it

1. **Type** a few characters. The list filters in real time.
2. Use **Up** / **Down** arrows (or **Ctrl+J** / **Ctrl+K**) to move through the results.
3. Press **Enter** to run the highlighted command.
4. Press **Escape** to close the palette without running anything.

The list shows:

- The **command label** (what it does).
- The **category** in square brackets (e.g., `[File]`, `[View]`).
- The **keyboard shortcut** if there is one (e.g., `Ctrl+S`).

You can also click a command with the mouse.

## What you can do

Almost everything. The palette is a unified launcher for:

### File operations
- `new` - new pipeline
- `open` - open a `.polaris` file
- `save` - save
- `save as` - save under a new name
- `import csv` / `parquet` / `xlsx` / `json` / `clipboard`
- `export csv` / `parquet` / `xlsx` / `json`
- `recent files` - list of recent pipelines

### Editing
- `undo` / `redo`
- `cut` / `copy` / `paste` / `duplicate` / `delete`
- `select all`

### Adding nodes
- `add filter`
- `add sort`
- `add bar chart`
- `add group by`
- `add inner join`
- `add csv reader`
- … and so on for all 40+ node types.

Just type `add` and pick from the list.

### Running
- `execute all` - F5
- `execute up to` - Shift+F5
- `cancel` - stop a running pipeline
- `clear cache` - drop all cached results

### Layout
- `auto layout` - Ctrl+Shift+L
- `group` / `ungroup` - Ctrl+G / Ctrl+Shift+G
- `fit to screen` - F
- `zoom in` / `zoom out` / `reset zoom` - Ctrl+Plus / Ctrl+Minus / Ctrl+1

### View
- `graph mode` - F2
- `spreadsheet mode` - F1
- `split mode` - F3
- `toggle ai` - Ctrl+Shift+A
- `toggle chart` - F4
- `toggle search` - Ctrl+F
- `toggle profile` - F4 or right-click column → statistics
- `toggle grid` - Ctrl+G
- `toggle minimap`
- `fullscreen` - F11

### Settings
- `settings` - Ctrl+,
- `theme` - switch palette
- `reset layout` - restore default panel arrangement

### Help
- `docs` / `documentation` - open this doc set
- `shortcuts` - in-app shortcut reference
- `about` - version info

## Fuzzy matching

The palette uses **fuzzy matching**. You don't have to type the exact label. Examples:

| You type | Matches |
|---|---|
| `exec` | Execute All, Execute Up To, Cancel |
| `lay` | Auto Layout, Reset Layout |
| `csv` | Add CSV Reader, Import CSV, Export CSV |
| `imp` | Import CSV, Import Parquet, Import JSON, Import XLSX, Import Clipboard |
| `sav` | Save, Save As |
| `joi` | Add Inner Join, Add Left Join, Add Right Join, Add Full Join, Add Cross Join, Add Anti Join |

Matching is case-insensitive. Subsequence matching is supported: `nla` matches **A**uto **L**ayout (the `n`, `l`, `a` are in order).

## Categories

Each command has a category shown in square brackets:

- `[File]` - file operations
- `[Edit]` - clipboard, undo
- `[View]` - panels, modes
- `[Nodes]` - add node, layout, group
- `[Run]` - execute, cancel
- `[Window]` - tabs
- `[Help]` - docs, about

You can type the category first to narrow:

- `view split` - `[View]` Switch to Split mode
- `nodes add` - `[Nodes]` submenu for adding nodes

## Keyboard shortcuts in the palette

| Shortcut | Action |
|---|---|
| **Enter** | Run the highlighted command |
| **Up** / **Down** | Move through results |
| **Ctrl+J** / **Ctrl+K** | Move through results (alternative) |
| **Esc** | Close the palette |
| **Tab** | Highlight the next result |
| **Shift+Tab** | Highlight the previous result |
| **Ctrl+1** ... **Ctrl+9** | Run the Nth result directly |

The numbered shortcuts are great when you know the order of common commands. For example, after typing `exec`, `Ctrl+1` runs "Execute All".

## Auto-completion

As you type, the palette auto-completes based on the most likely match. The first result is auto-highlighted, so **Enter** runs it. To see other matches, use the arrow keys.

## Recent commands

The palette remembers your last few commands. When you open it, the first few results are your most-recently-used ones. This makes repeating common actions (e.g., "auto layout after every change") very fast.

## Custom commands

The palette is populated from every action registered in the application. If you write a plugin or extension, your commands will automatically appear in the palette.

## Why it's the fastest way

Consider a common task: "add a Sort node, set the sort key to `price`, descending, and execute".

**Mouse method:**
1. Find Sort in the palette.
2. Drag it to the canvas.
3. Click the Sort node.
4. Click the Sort key field.
5. Type `price`.
6. Uncheck "Ascending".
7. Press Enter.
8. Press F5.

**Command palette method:**
1. `Ctrl+P`.
2. Type `add sort`. Enter.
3. `Ctrl+P`.
4. Type `execute all`. Enter.
5. Click the Sort node. Click the Sort key field. Type `price`. Uncheck Ascending. Enter.

Still requires the property edit. The palette is best for **actions**, not for **editing parameters**. For parameters, the Properties Panel is faster.

But for any "do this thing", the palette is at least 2–3× faster than navigating menus.

## Tips

- **Ctrl+P** should be a reflex. If you find yourself reaching for the mouse, stop and try the palette first.
- **Type the category first** when you know it: `view split` is faster than `split mode`.
- **Use the numbered shortcuts** for your top 5 commands.
- **The palette shows keyboard shortcuts** in the list, so it's a built-in shortcut reference.
- **Escape to dismiss** at any time - you can press Esc to back out of any sub-state.

## Common commands cheat sheet

| Want to... | Type |
|---|---|
| Save the current pipeline | `save` |
| Open a file | `open` |
| Run the pipeline | `execute all` |
| Add a Sort node | `add sort` |
| Add a Filter node | `add filter` |
| Add a Bar Chart | `add bar` |
| Open the AI panel | `ai` or `toggle ai` |
| Open the Chart panel | `chart` or `toggle chart` |
| Find in the grid | `find` or `search` |
| Auto-arrange the canvas | `layout` or `auto layout` |
| Switch to Spreadsheet mode | `spreadsheet mode` |
| Switch to Graph mode | `graph mode` |
| Switch to Split mode | `split mode` |
| Open Settings | `settings` |
| Show keyboard shortcuts | `shortcuts` or `key` |
| Quit Polaris | `quit` or `exit` |

## See also

- **[Keyboard shortcuts](../getting-started/keyboard-shortcuts.md)** - every shortcut in Polaris.
- **[Interface tour](../getting-started/interface-tour.md#command-palette-overlay)** - where the palette fits in the UI.
- **[The AI assistant](ai-panel.md)** - for when you want to do something but don't know the command.
