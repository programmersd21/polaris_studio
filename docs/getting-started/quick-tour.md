# 10-Minute Quick Tour

This is a hands-on tour. You'll do real work, not just read. By the end you'll have a working pipeline that loads a CSV, filters it, charts it, and exports the result. After that you'll know enough to explore on your own.

> **Estimated time:** 10 minutes. A little longer if you also install.

---

## Step 1 - Launch (1 minute)

If you haven't installed yet, see **[Installation](installation.md)** first. Then:

```bash
polaris-studio
```

The window opens. You'll see four areas: a node palette on the left, an empty canvas in the middle, an empty spreadsheet at the bottom, and a status bar.

If you want sample data to play with, the project ships with a few demo files in the `local/` directory.

---

## Step 2 - Load a CSV (1 minute)

There are three ways to load a file:

- **Drag and drop** a file from your file manager onto the canvas.
- **File menu** → **Import** → **CSV** (or Parquet / XLSX / JSON).
- **Right-click** the canvas → **Add Node** → **CSV Reader**.

Let's use the menu. Go to **File → Import → CSV** and pick any CSV file. If you don't have one handy, copy-paste a table from Excel or Google Sheets first, then use **File → Import → Clipboard**.

A node appears on the canvas labeled with the filename. It has a single output port on the right.

**Try it:** hover over the node - the port glows. Click the node once - the Properties panel on the right shows the file path, delimiter, and a row count.

---

## Step 3 - Add a filter (2 minutes)

Let's say your CSV has a `price` column and you want only the rows where `price > 50`.

1. In the **Node Palette** on the left, type `filter` into the search box.
2. Drag **Filter** onto the canvas, to the right of the CSV Reader.
3. Click the Filter node to select it.
4. In the **Properties Panel** on the right, find the **Expression** field.
5. Type: `pl.col('price') > 50`
6. Click **Apply** or press Enter.

> **What's that `pl.col` thing?** It's Polars syntax - the underlying data engine. `pl.col('price')` means "the column called price". The full expression is "the price column is greater than 50".

The Filter node now has the same schema as the CSV Reader (because filters don't change columns) and is marked **dirty** (a small dot indicator on the node).

---

## Step 4 - Connect them (1 minute)

1. Move your mouse to the **right edge** of the CSV Reader node - you'll see a small dot (the **output port**).
2. Click and drag from that dot to the **left edge** of the Filter node (its **input port**).
3. Release. A line appears connecting them.

The Filter is no longer dirty. The graph is wired.

> **Tip:** If you miss the input port, just try again. The line snaps to ports when you get close.

---

## Step 5 - Add a sort (1 minute)

Add a **Sort** node to the right of the Filter. Connect Filter → Sort.

In the Properties Panel:
- **Columns:** `price`
- **Ascending:** unchecked (we want highest prices first)
- **Nulls last:** checked (optional but tidy)

---

## Step 6 - Add a chart (2 minutes)

Add a **Bar Chart** node to the right of the Sort. Connect Sort → Bar Chart.

In the Properties Panel:
- **X column:** `category` (or whichever column you want on the x-axis)
- **Y column:** `price`
- **Aggregation:** `sum` (or `count`)

Click **Execute** in the Properties Panel - the chart appears in the Chart Panel on the right.

> **Don't see the chart?** Open the Chart Panel via **View → Panels → Chart** or press **F4**.

---

## Step 7 - Run the pipeline (1 minute)

Two options:

- **F5** to run the whole pipeline end to end.
- Click the **Execute** button in the Properties Panel of any node to run up to and including that node.

When it finishes, the status bar shows `Time: 47ms` (or however long) and the spreadsheet at the bottom shows the filtered, sorted rows.

---

## Step 8 - Export (1 minute)

Let's export the final result to a new CSV.

1. Drag an **Export CSV** node from the palette onto the canvas.
2. Connect your last node → Export CSV.
3. In Properties, set **File path** to wherever you want the output.
4. **F5** to run.

Open the output file in any text editor or spreadsheet app - it's the filtered, sorted data.

---

## Bonus - Ask the AI (1 minute)

If you [configured an AI key](installation.md#optional-configure-the-ai), try this:

1. Press **Ctrl+Shift+A** to open the AI panel.
2. Type: `add a column called total = price * quantity, then filter where total > 1000`
3. Press **Enter**.

A preview card appears showing exactly what the AI wants to do. Click **Apply** - Polaris adds the nodes, connects them, and updates the canvas. No code was run that you didn't see first.

---

## What just happened?

You built a real data pipeline:

```
CSV Reader → Filter → Sort → Bar Chart
                       \
                        → Export CSV
```

Each box is a node. The lines are connections. The arrows show data flow. F5 ran the whole thing. The data was processed in memory, never written to a temp file.

You also saw:

- **Loading data** (CSV Reader).
- **Filtering rows** (Filter).
- **Sorting** (Sort).
- **Visualizing** (Bar Chart).
- **Exporting** (Export CSV).
- **AI assistance** (the bonus step).

That's the core loop of Polaris. The next 40+ node types and the rest of the UI are variations on this theme.

---

## Where to go next

- **[Your first pipeline - deeper dive](first-pipeline.md)** - does the same thing but explains every click.
- **[Interface tour](interface-tour.md)** - every panel and button explained.
- **[Core concepts](user-guide/concepts.md)** - the mental model under the hood.
- **[Node reference](nodes/reference.md)** - every node, every parameter.
- **[Keyboard shortcuts](keyboard-shortcuts.md)** - speed it up.
