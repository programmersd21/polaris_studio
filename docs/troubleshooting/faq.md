# Frequently Asked Questions

---

## General

### What is Polaris Studio?

Polaris Studio is a node-based visual data application. You build data pipelines by connecting nodes on a graph canvas - each node performs an operation (reading a file, filtering rows, joining tables, creating charts). Think of it as a visual, interactive way to work with Polars DataFrames without writing code. It's designed for data exploration, ETL, and quick analysis.

### Is Polaris Studio free?

Yes, Polaris Studio is free and open-source. The AI assistant uses Google's Gemini API, which requires a free API key (Google provides a generous free tier). You only pay Google if you exceed the free quota - Polaris Studio itself costs nothing.

### What data formats does Polaris Studio support?

It supports **CSV**, **Excel (.xlsx)**, **Parquet**, and **JSON** for reading and writing. You can also paste tabular data from the clipboard, create data manually, and connect to external files. Export is available as CSV, XLSX, Parquet, and JSON.

### Can I save my work and share it?

Yes. Save a workflow as a `.polaris` file (`Ctrl+S`). This is a ZIP archive containing your workflow graph and all embedded data files - share it with anyone running Polaris Studio. When they open it, all data and connections are restored automatically.

---

## Installation

### What Python version do I need?

Python **3.10 or later**. The codebase uses Python 3.10+ features like `match` statements and union type syntax. Python 3.11 or 3.12 is recommended for the best binary wheel compatibility.

### How do I install dependencies?

The simplest way is a virtual environment:
```
python -m venv polaris-env
polaris-env\Scripts\activate    # Windows
source polaris-env/bin/activate # Linux/Mac
pip install -r requirements.txt
```

Key dependencies include **PySide6** (UI framework), **Polars** (data processing), **pyqtgraph** (charts), **openpyxl** (Excel), **google-genai** (AI), and **pyarrow** (Parquet).

### Should I use a virtual environment?

Absolutely. It prevents version conflicts with other Python projects. Polaris Studio has specific version requirements for PySide6, Polars, and its other dependencies - a virtual environment keeps them isolated.

---

## Usage

### How do I import data?

Three ways:
1. **File menu**: Click **File → Import CSV / XLSX / Parquet**. This creates a reader node and immediately executes it.
2. **Right-click canvas**: Right-click the graph canvas → **Add Node → Source**, then choose CSV Reader, Parquet Reader, etc. Configure parameters in the Properties panel.
3. **Drag and drop**: Drag a data file onto the canvas (if supported by your OS).

### How do I connect nodes?

Click and drag from a **port** (the small circles on the sides of a node) to another node's port. Output ports are on the right, input ports on the left. You can also right-click a node and use context menu options. The graph validates connections and prevents cycles.

### How do I execute the pipeline?

Press **F5** to execute all nodes, or select a specific node and press **Ctrl+Enter** to execute from that node downward. Execution runs in topological order - upstream nodes run first. Results appear in the spreadsheet at the bottom and any attached Chart panel.

### How do I save and load workflows?

**Save**: `Ctrl+S` saves to a `.polaris` file. Use `Ctrl+Shift+S` for Save As.
**Load**: `Ctrl+O` opens a `.polaris` file. You can also drag a `.polaris` file onto the window.

The `.polaris` format is a ZIP archive containing your graph structure and embedded data files - everything is self-contained.

---

## AI

### How do I configure the AI assistant?

Go to **Edit → Settings** (`Ctrl+,`), then the **AI** tab. Paste your Google Gemini API key (starts with `AIza...`) and select a model. The recommended models are `gemma-4-31b-it` (fast, efficient) and `gemini-3.1-flash-lite` (more capable). Click Save, and the AI panel is ready.

### What can the AI do?

The AI can:
- Answer questions about your data (column stats, row counts, patterns)
- Propose graph modifications (add filter nodes, rename columns, create charts)
- Execute spreadsheet commands (edit cells, sort columns, fill nulls)
- Explain what your pipeline does

It shows proposed changes as a preview card - you can approve or skip each batch.

### Is my data sent to the AI?

Yes - when you ask the AI a question, Polaris sends a text summary of your workspace (node types, column names, row counts, and a data preview) along with your message. The raw data itself is not sent; only column names, types, and the first few rows of preview are included. If you're working with sensitive data, be aware that this context is transmitted to Google's Gemini API.

### Can I use the AI without an internet connection?

No. The AI assistant requires a working internet connection to reach the Google Gemini API. If you're offline, the canvas and spreadsheet still work - you just can't use the AI chat.

---

## Spreadsheet

### How do I edit cells?

Double-click a cell in the spreadsheet to edit its value. Press Enter to commit, or Escape to cancel. You can also use the formula bar at the top - type a value or expression and press Enter.

### What expressions can I use in the formula bar?

You can write Polars expressions in the formula bar, such as `pl.col('Price') * 1.1` or `pl.col('Name').str.to_uppercase()`. The expression is parsed safely and applied as an "Add Column" node in your graph. Only Polars functions and operators are allowed - arbitrary Python code is not supported.

### What is NLP mode in the formula bar?

The formula bar has a natural language mode. Press **Alt+Enter** (or click the "AI" button in the bar) to switch. Instead of writing a Polars expression, describe what you want in plain English (e.g., "create a column that combines first and last names"). The query is sent to the AI, which interprets it and creates the appropriate node.

### What do the column header prefixes mean?

Column headers show a type prefix: `#` for numeric, `A` for text, `D` for dates, `T` for datetimes, `B` for booleans, `[]` for list columns, `?` for unknown types. This helps you quickly scan your data.

---

## Charts

### How do I create a chart?

Add a Chart node (bar_chart, line_chart, scatter_chart, histogram, box_chart, or heatmap) to your graph and connect it to the data you want to visualize. Execute the pipeline, then open the Chart panel from the View menu (or toolbar). Select the chart type from the dropdown.

### Can I export a chart as an image?

Yes. The Chart panel has **Export PNG** and **Export SVG** buttons. PNG is good for embedding in documents; SVG gives you a scalable vector file you can edit in tools like Illustrator or Inkscape.

---

## Performance

### How large of a dataset can Polaris Studio handle?

It depends on your hardware. With default settings, datasets of a few hundred thousand rows work well. For millions of rows, you may notice lag in the spreadsheet view. Use Filter, Slice, or aggregation nodes upstream to reduce data volume before it reaches the table output. The execution engine (Polars) can handle billions of rows - it's the UI display that has limits.

### Does Polaris Studio use multiple CPU cores?

Yes. The execution engine runs in a separate thread, and you can configure the number of worker processes in **Settings → Performance** (1–8 workers). Polars itself is multithreaded, so operations like groupby, joins, and sorting automatically use all available cores.

### How can I speed up my workflow?

- Use **Select Columns** to drop unused columns early in the pipeline.
- Use **Filter** before **Aggregate** to reduce row counts.
- Increase **Cache Size Limit** in Settings to avoid recomputation.
- Use **Profile** on individual nodes to identify bottlenecks.
- Set the **Worker Processes** count to match your CPU core count.

---

## Troubleshooting

### The fonts look wrong. What should I do?

Make sure the `fonts/` folder exists and contains `Inter-Regular.ttf`, `Outfit-Regular.ttf`, `InstrumentSerif-Regular.ttf`, and `JetBrainsMono-Regular.ttf`. If Inter still falls back to a system font, install `fonttools` (`pip install fonttools`) and restart - Polaris patches the Inter font's internal name table so it resolves correctly.

### The window icon is missing. Is this a bug?

It's a minor cosmetic issue on some platforms. The icon file may not be loading. It doesn't affect any functionality. You can set a custom icon through your desktop launcher if it bothers you.

### I see QPainter warnings in the terminal. Should I worry?

No. These are harmless Qt diagnostic messages that appear during widget initialization. They don't affect performance or functionality. Set `QT_LOGGING_RULES=*.debug=false` to suppress them.

### I get "API key invalid" even though I just created one.

Make sure you've enabled the Gemini API in your Google Cloud project. Free-tier API keys from [aistudio.google.com](https://aistudio.google.com) work well - just copy the full key exactly (it starts with `AIza...`). Check that there's no trailing space or newline.

### Where can I report bugs or request features?

Open an issue on the Polaris Studio GitHub repository. Include your OS, Python version, and a description of the problem. For crashes, include the full terminal output.
