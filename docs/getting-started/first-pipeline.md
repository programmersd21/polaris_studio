# Your First Pipeline - A Deeper Walkthrough

This is the same tour as **[Quick tour](quick-tour.md)**, but slower and with explanations. If you've never used a node-based tool before, start here. If you have, skip to the **[User guide](../user-guide/concepts.md)**.

> **Time:** 20 minutes. You'll need a CSV file with at least a few hundred rows. The Polaris repo ships with some samples in `local/`.

---

## What is a "pipeline"?

A pipeline is a sequence of steps that data flows through. The simplest example in Excel is:

> "Open this CSV, filter to US customers, sort by total spend, sum by state, save the result."

In a traditional tool, that's: open file → click filter → click sort → click group → save. In Polaris, each of those steps is a **node** on a canvas, and the data flows between them through visible **connections**.

The advantage: you can see the whole flow at once, rearrange steps by dragging, and reuse the output of one step in multiple places.

---

## Part 1 - The window

When you launch Polaris you see:

```
┌──────────────────────────────────────────────────────────────┐
│  File  Edit  View  Nodes  Run  Window  Help                  │  ← Menu bar
├──────────┬───────────────────────────────────────┬───────────┤
│          │                                       │           │
│  Node    │                                       │ Properties│
│  Palette │            Graph Canvas               │  Panel    │
│          │                                       │           │
│  (left)  │            (center)                   │  (right)  │
│          │                                       │           │
├──────────┴───────────────────────────────────────┴───────────┤
│                                                              │
│                   Spreadsheet Grid                           │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  No node selected · Rows: 0 · Time: -- · AI                  │  ← Status bar
└──────────────────────────────────────────────────────────────┘
```

Right now the canvas is empty, the spreadsheet is empty, the status bar says "No node selected".

You'll use the **Node Palette** to find nodes, the **Canvas** to arrange them, the **Properties Panel** to configure them, the **Spreadsheet** to see results, and the **Status Bar** to know what's happening.

There are also hidden panels you can open: **AI Panel**, **Chart Panel**, **Profile Panel**, **Search Panel**. We'll get to those.

---

## Part 2 - Load data

### Method A: drag and drop

Drag a CSV file from your file manager and drop it anywhere on the canvas. A **CSV Reader** node appears. Done.

### Method B: menu

**File → Import → CSV** (or Parquet / JSON / XLSX). Pick the file. Done.

### Method C: right-click

Right-click on the canvas → **Add Node** → **CSV Reader**. A node appears. Now click it and use the Properties Panel to set the file path.

### What just happened?

A **node** appeared on the canvas. Nodes are the boxes in a pipeline. This particular one is a **Source node** - it brings data in from somewhere. Every pipeline starts with at least one source.

Click the node. Look at the **Properties Panel** on the right. It shows:

- The file path
- The delimiter
- Whether the first row is a header
- The file encoding
- How many rows to skip before the header

For most CSVs the defaults are fine. You can change them here if you need to.

---

## Part 3 - Add a filter

In the **Node Palette** on the left, you'll see categories: Source, Transform, Aggregate, Join, Sort, Chart, Output. Click **Transform** to expand it. You'll see: Filter, Select Columns, Add Column, Rename Columns, Drop Columns, Cast Column, Fill Null, String Operations, Date Parse, Sample, Slice, Deduplicate, Unpivot, Explode.

Drag **Filter** onto the canvas, to the right of the CSV Reader.

Click the Filter node. In the Properties Panel you'll see one field: **Expression**. Type:

```
pl.col('price') > 50
```

> **What does that mean?**
> - `pl.col('price')` - "the column named `price`"
> - `> 50` - "is greater than the number 50"
> - Together: "rows where the price column is greater than 50"

This is **Polars syntax** - Polaris's underlying data engine. You don't need to know Polars to use Polaris, but the expressions are how you describe filters, computed columns, and aggregations. See **[Polars expressions primer](#polars-expressions-primer)** at the bottom of this page for a 5-minute intro.

Press **Enter** or click outside the field. The node updates.

### Connect the CSV Reader to the Filter

1. Hover over the right edge of the CSV Reader node. A small dot appears - that's the **output port**.
2. Click and drag from that dot.
3. A line follows your cursor.
4. Drag to the left edge of the Filter node. Another small dot appears - that's the **input port**.
5. Release.

A line connects them. Data will flow from the CSV Reader into the Filter.

> **Connection rules:**
> - Output ports are on the right; input ports are on the left.
> - You can only connect an output to an input (data flows in one direction).
> - You cannot create a cycle (A → B → A). Polaris will reject it.

---

## Part 4 - Add a sort

Drag **Sort** from the palette (also under **Transform**) to the right of the Filter.

Connect Filter → Sort.

In the Properties Panel:
- **Columns:** type `price` (or pick from the dropdown of available columns)
- **Ascending:** leave it checked for smallest-to-largest, uncheck for largest-to-smallest
- **Nulls last:** checked

Press Enter. The Sort node updates.

---

## Part 5 - Add a chart

Drag **Bar Chart** from the palette (under **Chart**) to the right of the Sort.

Connect Sort → Bar Chart.

Click the Bar Chart node. In the Properties Panel:
- **X column:** `category` (or whatever you want on the x-axis)
- **Y column:** `price` (the numeric value to plot)
- **Aggregation:** `sum` (or `mean`, `count`, `min`, `max`)

Click **Execute** in the Properties Panel (or press F5). The chart appears in the **Chart Panel** on the right.

> **Don't see the Chart Panel?** Open it via **View → Panels → Chart** or press **F4**.

---

## Part 6 - See the data

Press **F5** to run the whole pipeline. The status bar shows execution time, and the **Spreadsheet** at the bottom shows the data at the last node you executed.

You can:
- **Click a column header** to sort by that column (ascending, descending, then back to original).
- **Drag column headers** to reorder columns.
- **Right-click a column header** for column statistics (min, max, mean, median, nulls, unique count, top 5 values).
- **Double-click a cell** to edit it (this creates an implicit mutation - use with care).
- **Drag the row number column** to freeze the top row.

---

## Part 7 - Add an export

Drag **Export CSV** from the palette (under **Output**) onto the canvas.

Connect your last node → Export CSV.

Click it. In the Properties Panel, set **File path** to something like `C:\Users\You\Desktop\result.csv` or `/home/you/result.csv`.

Press **F5**. The file is written.

---

## Part 8 - Save your work

**File → Save** (or **Ctrl+S**). Pick a filename ending in `.polaris`. This is a JSON file that contains your entire pipeline - every node, every connection, every parameter. Plus your view state (zoom, scroll, selection).

To reopen it later: **File → Open** (or **Ctrl+O**). You get the exact canvas back, ready to run.

---

## Part 9 - Multi-tab

Polaris supports multiple independent pipelines in tabs.

- **Ctrl+T** - new tab.
- **Ctrl+W** - close current tab.
- Click a tab to switch.

Each tab is its own pipeline. You can reference the output of one tab from another using the **Cross-Tab Reference** node (under **Source**). This is useful for things like "use the cleaned customer table from tab 1 in every other tab".

---

## What to try next

- **Ask the AI.** Press **Ctrl+Shift+A**, type something like *"add a column called `revenue = price * quantity`, then sort by it"*, and Apply the result.
- **Auto-layout.** Press **Ctrl+Shift+L** to tidy up overlapping nodes.
- **Undo.** Press **Ctrl+Z** if you make a mistake. Polaris tracks every change.
- **Command palette.** Press **Ctrl+P** and start typing - "execute", "save", "open", "ai". Every action has a shortcut.
- **Group nodes.** Select several nodes (drag a box around them, or hold Shift and click), then press **Ctrl+G** to group them. The group becomes one moveable block.

---

## Polars expressions primer

Polaris uses [Polars](https://pola.rs/) under the hood. You don't need to learn it to use Polaris - most nodes have friendly UIs that generate expressions for you - but if you want to write custom ones, here's the 5-minute version.

### Column references

| Expression | Meaning |
|---|---|
| `pl.col('price')` | The column named `price` |
| `pl.col('price', 'qty')` | Both columns `price` and `qty` |
| `pl.all()` | Every column |
| `pl.col(pl.Int64)` | Every integer-64 column |
| `pl.col('a').alias('b')` | The column `a`, renamed to `b` |

### Operators

| Expression | Meaning |
|---|---|
| `pl.col('price') > 50` | Rows where price > 50 |
| `pl.col('name').is_null()` | Rows where name is null |
| `pl.col('name').is_not_null()` | Rows where name is not null |
| `pl.col('a') & pl.col('b')` | AND: both a and b are true |
| `pl.col('a') \| pl.col('b')` | OR |
| `~pl.col('a')` | NOT |
| `pl.col('name').str.contains('Acme')` | String contains |
| `pl.col('price').is_between(10, 100)` | Between 10 and 100 |
| `pl.col('a').is_in(['x', 'y', 'z'])` | a is one of those values |

### Computations

| Expression | Meaning |
|---|---|
| `pl.col('price') * pl.col('qty')` | Price times quantity (a new column) |
| `pl.col('price').round(2)` | Round to 2 decimals |
| `pl.col('name').str.to_uppercase()` | UPPERCASE |
| `pl.col('date').dt.year()` | Extract year from a date |
| `pl.col('price').fill_null(0)` | Replace nulls with 0 |

### Aggregations

| Expression | Meaning |
|---|---|
| `pl.col('price').sum()` | Sum of the column |
| `pl.col('price').mean()` | Average |
| `pl.col('price').min()` / `.max()` | Min / max |
| `pl.col('price').count()` | Number of non-null values |
| `pl.col('price').std()` | Standard deviation |
| `pl.col('price').quantile(0.5)` | Median (or any quantile) |

You'll see these expressions in the Properties Panel for Filter, Add Column, and the various aggregate nodes. Click the **?** icon next to the field to open an expression editor with autocomplete and a live preview.
