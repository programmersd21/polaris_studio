# Charts

Polaris has six built-in chart types: bar, line, scatter, histogram, box, and heatmap. Charts are first-class nodes in the pipeline - they take a DataFrame as input and render a visual.

## Open the Chart panel

- **F4** - toggle the Chart panel.
- **View → Panels → Chart**.
- **Right-click a chart node on the canvas → Open in Chart Panel**.

The Chart Panel docks on the right by default.

## The chart types

| Type | Best for | Inputs |
|---|---|---|
| **Bar** | Comparing categories | X = categorical, Y = numeric |
| **Line** | Trends over an ordered axis | X = continuous, Y = numeric |
| **Scatter** | Relationship between two numeric columns | X = numeric, Y = numeric |
| **Histogram** | Distribution of a single numeric column | One numeric column |
| **Box** | Statistical distribution across categories | One or more numeric columns, optional category |
| **Heatmap** | 2D matrix of values (e.g., correlation, pivot) | Two numeric axes |

## Chart nodes vs. Chart panel

There are two ways to get a chart:

- **Chart node** (Bar Chart, Line Chart, etc.) - a node in the pipeline. Its output is a chart spec. Connecting it to a Table View shows the chart in the bottom panel.
- **Chart panel** - a dock that shows an interactive version of the most recent chart's data. Supports pan, zoom, autoscale, and PNG/SVG export.

In practice, use **Chart nodes** in your pipeline (they're reproducible and saved with the workflow) and use the **Chart panel** for interactive exploration.

## Adding a chart node

1. Open the **Node Palette** → **Chart** category.
2. Drag the chart type you want onto the canvas.
3. Connect an upstream node's output → the chart's input.
4. Click the chart node. In the Properties Panel, set the parameters (X, Y, aggregation, etc.).
5. **Execute** the chart node (F5 or the Execute button).
6. Open the Chart panel (F4) to see the rendered chart.

## Bar Chart

```
Inputs:  X (categorical), Y (numeric)
Modes:   sum | mean | count | min | max | median
```

The simplest chart. For each unique value in X, compute the chosen aggregation of Y.

**Example:** X = `region`, Y = `revenue`, aggregation = `sum` → a bar chart with one bar per region, bar height = total revenue for that region.

**Settings:**

- **X column** - the categorical axis.
- **Y column** - the numeric value to aggregate.
- **Aggregation** - how to combine multiple Y values per X (sum, mean, etc.).
- **Sort bars** - sort by X (alphabetical) or by Y value (ascending/descending).
- **Limit top N** - only show the top N bars (e.g., top 10 regions).
- **Color** - bar fill colour (defaults to the accent palette).

## Line Chart

```
Inputs:  X (continuous or ordered), Y (numeric)
Multi-series:  one line per Y column
```

Use for trends. If you have multiple numeric columns, each becomes a series.

**Example:** X = `date`, Y columns = `revenue`, `cost` → two lines over time, one per metric.

**Settings:**

- **X column** - the continuous axis (date, time, or ordered numeric).
- **Y columns** - one or more numeric columns (each becomes a line).
- **Line width** - default 2px.
- **Show legend** - toggle the series legend.
- **Show markers** - draw a dot at each data point.

## Scatter Chart

```
Inputs:  X (numeric), Y (numeric)
```

For showing the relationship between two numeric columns. Each point is a row.

**Example:** X = `height`, Y = `weight` → a scatter showing how height and weight correlate across a population.

**Settings:**

- **X column**, **Y column** - the two numeric axes.
- **Point size** - default 6px.
- **Point color** - by default the accent palette; can be mapped to a third column for a "scatter color" view.
- **Color column** - optional third column to colour points by (categorical).
- **Trend line** - overlay a linear regression line.

## Histogram

```
Inputs:  one numeric column
Bins:    auto | fixed (20 by default) | custom
```

Shows the distribution of a single numeric column. Bins are auto-computed (Sturges' rule) by default; override with a fixed count or custom breakpoints.

**Example:** column = `age` → a histogram with bins of ages, height = count of rows in each bin.

**Settings:**

- **Column** - the numeric column to bin.
- **Bins** - auto, 10, 20, 50, or custom.
- **Normalize** - show as count, density, or percentage.
- **Color** - bar fill colour.

## Box Chart

```
Inputs:  one or more numeric columns; optional category
```

Shows the statistical distribution of one or more numeric columns, with quartiles and outliers.

**Example:** columns = `price`, `cost`, `profit` → three side-by-side box plots, one per metric, showing median, quartiles, and outliers.

**Settings:**

- **Columns** - one or more numeric columns (each becomes a box).
- **Category column** - optional; if set, draws one box per category value per metric.
- **Whisker multiplier** - default 1.5; outliers beyond `Q3 + 1.5*IQR` or `Q1 - 1.5*IQR` are shown as dots.

## Heatmap

```
Inputs:  two numeric axes (X, Y) and a value column
```

A 2D matrix where colour encodes a value. The most common use is a **correlation matrix** between numeric columns.

**Example:** numeric columns A, B, C, D, E → a 5x5 heatmap where cell (i, j) is the correlation between column i and column j.

**Settings:**

- **X column**, **Y column** - the row and column axes.
- **Value column** - the numeric value to colour by.
- **Aggregation** - how to combine multiple values per cell (mean, sum, count, etc.).
- **Colour scale** - sequential, diverging, or categorical.
- **Show values** - overlay the numeric value in each cell.

## Interacting with a chart

The Chart panel is rendered with pyqtgraph. Standard interactions:

- **Pan** - middle-mouse drag, or Space + left-drag.
- **Zoom** - scroll wheel. Zooms in/out around the cursor.
- **Box zoom** - left-drag to draw a box, release to zoom to it.
- **Autoscale** - double-click anywhere on the plot to fit the data.
- **Reset zoom** - `A` key, or right-click → **View → Auto Range**.

For bar / line / scatter charts, **hover** a point to see a tooltip with the (X, Y) values.

## Exporting a chart

The Chart panel has two export buttons in its toolbar:

- **Export PNG** - saves the current view as a PNG image.
- **Export SVG** - saves the current view as a vector SVG.

Both open a file dialog. PNG is good for slides and docs; SVG is good for print and further editing (it scales without loss).

### Export defaults

- **PNG:** 1920×1080 pixels, white background, current zoom.
- **SVG:** vector format, scales to any size, white background.

To change defaults, edit the export settings in **Settings → Charts**.

## Using charts in a saved workflow

Chart nodes are part of the pipeline. When you save a `.polaris` file, the chart node's parameters are saved (type, X, Y, aggregation, etc.) but the rendered image is not - it's regenerated when the workflow is reopened and executed.

This means:

- Workflows are small (just parameters).
- Charts update automatically when the data changes.
- You can have dozens of chart nodes in one workflow.

## Tips and tricks

- **Combine charts in a workflow.** Bar chart for one metric, line for another, both fed from the same data. Just add multiple chart nodes.
- **Use a Pivot Table upstream** to reshape data for the chart (e.g., rows = months, columns = regions → heatmap).
- **For "top N" bar charts**, add a Sort + Slice upstream, then the Bar Chart. Or use the chart's **Limit top N** setting.
- **For correlation heatmaps**, you don't need to compute correlations in Python - the Heatmap chart with `mean` aggregation over normalized data works for many cases. For exact Pearson/Spearman correlations, use a `manual_entry` node with the correlation values and feed it to a Heatmap.
- **Colour scales matter.** Sequential for "more is more" (age, count). Diverging for "two-sided" (correlation, sentiment).
- **Always label your axes.** Bar Chart's `X column` and `Y column` are auto-labelled. For other charts, check the chart settings.
- **Save chart layouts** by saving the `.polaris` file. The chart parameters (not the rendered view) are saved.
- **Export to SVG** for print-quality output. SVG scales infinitely without pixelation.

## Common pitfalls

- **Bar chart with too many categories.** If your X column has 10,000 unique values, the chart will be unreadable. Slice to top 20 first.
- **Line chart with non-ordered X.** Polaris doesn't enforce X ordering for line charts. If X is a string, sort upstream.
- **Heatmap with non-numeric axes.** Both X and Y must be numeric (or coercible). Use a Cast upstream if needed.
- **Histogram with too few bins.** Default 20 is good for most cases. For highly skewed data, try 50 or 100.
- **Box chart with non-numeric columns.** Box charts need numeric data. Use Cast to convert.

## See also

- **[Node reference → Chart nodes](../nodes/reference.md#chart-nodes)** - every chart type and its parameters.
- **[Profile Panel](#)** - for column statistics and small inline histograms.
- **[Charts and the AI](ai-panel.md)** - the AI can build chart pipelines from plain English: *"show a bar chart of revenue per region, sorted by revenue"*.
