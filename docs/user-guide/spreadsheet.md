# The Spreadsheet

The spreadsheet is a live, editable grid that mirrors the output of the most recently executed or previewed node. It's full-featured: it can hold a million rows, supports sorting, freezing, conditional formatting, and column-level operations.

## What's in the spreadsheet

```
┌──────────────────────────────────────────────────────────────┐
│  A1:  = pl.col('price') * 1.1                               │  ← Formula bar
├────┬─────────┬──────────┬───────────┬────────────┬───────────┤
│    │ Name    │ Price    │ Qty       │ Total      │ Region    │  ← Column headers
│  1 │ Widget  │    10.00 │         5 │     50.00  │ North     │
│  2 │ Gizmo   │    25.00 │         2 │     50.00  │ South     │
│  3 │ Doohick │     5.50 │        10 │     55.00  │ North     │
│  4 │ Thingam │    15.00 │         3 │     45.00  │ East      │
│  5 │ ...     │ ...      │ ...       │ ...        │ ...       │
└────┴─────────┴──────────┴───────────┴────────────┴───────────┘
```

Above the grid:

- **Cell reference** (e.g., `A1`) - updates as you click cells.
- **Formula bar** - shows the cell's content. Edit here for long content.

The grid itself:

- **Row numbers** in the leftmost column.
- **Column letters / names** in the header row.
- **Freeze lines** as heavier borders (if you've frozen rows or columns).
- **Active cell** with a blue border.

## Active node

The spreadsheet always shows the output of the **active node**. The active node is:

- The most recently **executed** or **previewed** node, OR
- The currently **selected** node (if it has been executed at least once).

The active node's name appears in the formula bar's left side (above the cell reference).

To change the active node: select a node on the canvas, then **click the Spreadsheet tab** (or just look at the bottom). The grid updates.

## Navigation

| Action | Shortcut |
|---|---|
| Move cell | Arrow keys |
| Move to next cell after edit | Enter |
| Move to previous cell after edit | Shift+Enter |
| Move right | Tab |
| Move left | Shift+Tab |
| Jump to first cell in row | Home |
| Jump to first cell in grid | Ctrl+Home |
| Jump to last cell in row | End |
| Jump to last cell in grid | Ctrl+End |
| Scroll one page | Page Up / Page Down |
| Jump to specific cell | Type the cell ref (e.g., `B5`) in the box |
| Zoom | Ctrl+Scroll |
| Reset zoom | Ctrl+0 |

## Editing cells

### Direct edit

1. **Double-click** a cell, or press **F2** with a cell selected, or start typing.
2. The cell becomes an editor.
3. Type your value:
   - **Plain text** sets the cell's value (string).
   - **A number** sets it as a numeric value.
   - **An expression starting with `=`** is evaluated as a Python expression over the active row.
4. **Enter** to commit, **Escape** to cancel.
5. **Tab** to commit and move right; **Shift+Tab** to move left.

### The `=` expression language

When a cell starts with `=`, the rest is treated as a Python expression with these variables in scope:

- **`row`** - a dict representing the active row. Access columns as `row['price']` or attribute-style `row.price`.
- **`pl`** - the Polars library, fully imported.
- **Any built-in** - `abs`, `round`, `min`, `max`, `len`, `str`, etc.
- **Any cell reference** - you can reference other cells: `=A1 + A2` sums cells A1 and A2 (for the same row).

Examples:

- `=pl.col('price') * 1.1` - multiplies the current row's `price` by 1.1.
- `=f"{row['name']} ({row['region']})"` - concatenates columns.
- `=row['price'] * row['qty']` - same as above, attribute style.
- `=A1 * 2` - twice the value of cell A1.
- `=round(row['price'], 2)` - round to 2 decimals.

Press **Enter** to apply. The cell shows the result. If the expression is invalid, the cell shows `#ERR` and a tooltip explains the issue.

### NLP mode

Press **Alt+Enter** in the formula bar to switch into **NLP mode**. The bar's placeholder changes to *"Describe what you want in plain English..."*. Type:

- *"double the price column"*
- *"concatenate first name and last name with a space"*
- *"set this column to the length of the name"*

Polaris parses your description into an expression, evaluates it against the current data, and shows a preview. **Enter** to apply; **Escape** to cancel.

This uses the same AI engine as the AI panel, scoped to a single cell.

## Selecting

- **Click** a cell to select it.
- **Shift+click** to extend the selection.
- **Ctrl+click** to add a non-contiguous cell to the selection.
- **Click + drag** to select a rectangle.
- **Ctrl+A** to select all (within the active cell range).
- **Click a row number** to select the entire row.
- **Click a column letter** to select the entire column.
- **Shift+click** a row or column to extend the selection.

With a selection, you can:

- **Copy / cut / paste** (Ctrl+C / X / V).
- **Delete** to clear the contents.
- **Format** (font, alignment, colour, conditional formatting).
- **Fill down** (Ctrl+D) - copy the top cell of the selection down to all cells below.
- **Fill right** (Ctrl+R) - copy the left cell of the selection right to all cells beside.

## Sorting

- **Click a column header** to sort by that column. Click again to reverse. Click a third time to clear.
- **Shift+click** additional headers to add secondary, tertiary, etc., sort keys.
- The sort order is shown as a small arrow in the column header.
- To clear all sorts: right-click any header → **Clear Sort**, or use the command palette.

Sorts in the spreadsheet **are not** applied to the underlying graph - they're a view-time filter. The graph still produces unsorted data. To sort the data in the pipeline, add a **Sort** node.

## Reordering columns

- **Drag a column header** to reorder it.
- The new order is reflected in the active node's data.
- This is a view-time reorder only; the underlying node's schema isn't changed. To permanently reorder, use a **Select Columns** node.

## Hiding and showing columns

- **Right-click a column header** → **Hide Column**.
- To show a hidden column: right-click any header → **Show All Columns**, or use **View → Columns → Show All**.

## Freezing rows and columns

Freezing keeps specific rows or columns visible while you scroll the rest.

- To freeze the **top row**: drag the heavy line just below the row 1 header. Or right-click row 1's number → **Freeze Above**.
- To freeze the **leftmost column**: drag the heavy line just right of the column A header. Or right-click column A → **Freeze Left**.
- To freeze both: freeze the row, then the column.
- To unfreeze: right-click any header → **Unfreeze All**.

Frozen rows/columns stay visible no matter how far you scroll.

## Column operations

**Right-click a column header** for the column context menu:

| Action | What it does |
|---|---|
| Sort Ascending / Descending | View-time sort |
| Clear Sort | Remove sort on this column |
| Hide Column | Hide this column from view |
| Rename Column | Change the column's name (creates an implicit rename node) |
| Cast Column → ... | Change the column's data type (int, float, string, date, etc.) |
| Fill Null → Forward / Backward / Literal / Mean / Median | Replace nulls in this column |
| Drop Column | Remove this column from the active output |
| Show Statistics | Open the Profile Panel for this column |
| Copy Column | Copy all values in this column to the clipboard |
| Conditional Formatting → ... | Add a rule (e.g., highlight values > 100) |
| Freeze Left | Freeze this column and everything to its left |

The "implicit" operations (rename, cast, fill, drop) are added as new nodes in the graph. You'll see them appear on the canvas.

## Row operations

**Right-click a row number** for the row context menu:

| Action | What it does |
|---|---|
| Cut / Copy / Paste | Standard clipboard |
| Insert Row Above | Insert a new blank row above this one |
| Insert Row Below | Insert a new blank row below this one |
| Delete Row | Delete this row from the active output |
| Freeze Above | Freeze this row and everything above it |

## Conditional formatting

Highlight cells based on rules. Right-click a column header → **Conditional Formatting → New Rule**.

A dialog opens with these rule types:

- **Value is** - equal to, not equal to, greater than, less than, between, etc.
- **Value contains** - substring match.
- **Value is null / not null**.
- **Top N** / **Bottom N** - highlight the top 5, bottom 10, etc.
- **Above average** / **Below average**.
- **Custom expression** - any Python/Polars expression that evaluates to a bool.

For each rule, set the format: cell background, text colour, font weight, font style.

Rules are applied in order; the first matching rule wins. To edit or delete a rule, right-click the column → **Conditional Formatting → Manage Rules**.

Conditional formats are **view-time only**. They don't affect the underlying data.

## Cell formatting

For one-off formatting (not rule-based), select a cell or range and use:

- **Ctrl+B** - bold
- **Ctrl+I** - italic
- **Ctrl+U** - underline
- Right-click → **Format Cells** - font, colour, alignment, number format

Like conditional formatting, this is view-time only.

## Number format

Each cell has a number format. To change:

1. Right-click a cell or range → **Format Cells**.
2. Pick a category: Number, Currency, Percentage, Date, Time, Custom.
3. Set the precision and locale.

The format affects how the value is **displayed**, not the underlying value. A cell with value `0.123` and format `Percentage, 0 decimals` shows as `12%`.

## Find and replace

- **Ctrl+F** opens the **Search Panel** docked at the bottom.
- Type a query; matching cells are highlighted in the grid.
- The results list shows cell references. Click a result to jump.
- Switch to **Replace** to do find-and-replace. Options: case sensitive, whole word, scope (current column / all columns / selected range).

## Performance

The spreadsheet uses Qt's model/view with virtualised rendering:

- It can hold **1 million+ rows** without lag.
- Sorting, filtering, and conditional formatting are view-time operations on the visible rows, not the full dataset.
- Cell edits are applied directly to the model; no full re-render is needed.

If you ever see a slowdown, check:

- **Conditional formatting rules.** Complex rules on million-row tables can be slow. Simplify.
- **Hidden columns.** Hidden columns still render (just not shown). To fully unload, drop them in the graph.
- **Custom number formats.** Locale-aware formats are slower than simple ones.

## Tips and tricks

- **Ctrl+Shift+L** to auto-layout, then click a node to see its data.
- **Right-click a column → Show Statistics** for an instant profile.
- **Drag a row number** to freeze the top row.
- **Alt+Enter** in the formula bar for NLP mode.
- **Type `=` in the formula bar** to start an expression.
- **Use the `row` variable** in expressions: `=row['price'] * row['qty']` is the same as `=B1 * C1` for row 1.
- **Shift+click headers** for multi-column sort.
- **Ctrl+scroll** to zoom the cell font (handy for presentations).
- **Right-click a column → Drop** to permanently remove it (adds a Drop Column node).
- **Freeze the leftmost column** to keep IDs visible while scrolling right.

---

## See also

- **[Node reference → Transform nodes](../nodes/reference.md#transform-nodes)** - Filter, Select Columns, Add Column, Rename, Drop, Cast, Fill Null.
- **[Profile Panel](#)** - column statistics.
- **[Search Panel](#)** - find and replace.
- **[AI assistant](ai-panel.md)** - the AI can do all of this in plain English.
