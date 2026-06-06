# Saving, Sharing, and Preferences

This page covers everything about saving your work, sharing pipelines with others, importing/exporting data, and tweaking Polaris to your liking.

---

## The `.polaris` file — your pipeline in a box

A Polaris pipeline is saved as a single `.polaris` file. Think of it as a **zip file** that bundles two things:

1. **The pipeline structure** — all your nodes, connections, tabs, canvas zoom and scroll position.
2. **The source data files** — every CSV, Excel, Parquet, or JSON file you imported is **embedded inside** the `.polaris` zip.

This means a `.polaris` file is **self-contained**. You can email it, commit it to Git, or put it on a USB drive — it will work on any machine without broken paths.

> **Zip fact:** `.polaris` is a standard ZIP archive. You can open it with any zip tool (7-Zip, WinRAR, `unzip`). Inside you'll find:
>
> ```
> workflow.json        ← the pipeline structure (metadata)
> data/                ← your imported data files, organised by node ID
>   csv_reader_1.csv
>   xlsx_reader_2.xlsx
>   parquet_reader_3.parquet
> ```

### What gets saved

| Saved | Not saved |
|---|---|
| Every node (type, ID, parameters, position on canvas) | The actual computed data (DataFrame results) |
| Every edge (source → target with port names) | The engine cache (rebuilt on load) |
| Tab names, order, scroll position, zoom level | AI conversation history |
| **Imported data files** (CSV, XLSX, Parquet, JSON) | Auto-generated / manual entry data (not file-backed) |
| The active tab and tab ordering | |

### What happens when you open a `.polaris` file

1. Polaris opens the zip and extracts `workflow.json` plus all data files to a temporary folder.
2. Every node and edge is reconstructed exactly as you left them.
3. The canvas view (scroll, zoom, selection) is restored.
4. All source nodes (`csv_reader`, `xlsx_reader`, etc.) now point to the extracted temp files — no broken paths.
5. Every node is marked dirty and the **entire pipeline is automatically re-executed** (you see the spreadsheet fill with data within seconds).
6. When you close Polaris, the temp folder is cleaned up.

### Save

- **Ctrl+S** — save the current workflow.
- **File → Save** — same.
- If the file hasn't been saved yet, Polaris prompts for a location. The extension `.polaris` is added automatically.

### Save As

- **Ctrl+Shift+S** — save under a new name.
- **File → Save As** — same. Creates a brand-new `.polaris` zip with freshly embedded data files.

### Open

- **Ctrl+O** — open a `.polaris` file.
- **File → Open** — same.

Polaris can open both the new zip-based `.polaris` files and the legacy JSON-based `.polaris` files (from older versions). Backward compatible.

### Sharing a pipeline

Since everything is self-contained, sharing is easy:

- **Email it** — `.polaris` files are typically a few MB (your data + the pipeline JSON).
- **Commit it to Git** — the zip compresses well. Your team can clone and open immediately.
- **Demo it** — put it on a flash drive, open on any machine with Polaris installed.

> **Note:** If your source data is extremely large (hundreds of MB), the `.polaris` file will be large too. Consider using a Sample node before importing to keep the pipeline portable.

---

## Importing data

Polaris can import data in four formats. Each import creates a **source node** on the canvas that feeds into your pipeline.

### Via the File menu

**File → Import CSV**, **Import XLSX**, or **Import Parquet**:

1. A file picker opens.
2. Select your data file.
3. A reader node (e.g., `csv_reader`) is created on the canvas at a default position.
4. The node is selected and executed immediately — you see the data in the spreadsheet.

The file path is stored in the node's parameters. When you save (Ctrl+S), Polaris **copies the file into the `.polaris` zip** automatically. The original path isn't needed after save.

### Via drag-and-drop

Drag a CSV, XLSX, or Parquet file from your file manager directly onto the canvas. A reader node is created at the drop position.

### Via clipboard

Copy tabular data from Excel, Google Sheets, or a website and paste it with **Ctrl+V** on the canvas. A `clipboard_paste` source node is created with the pasted data. (The data is serialized in the workflow JSON, not as a separate file.)

### Via manual entry

Use the `manual_entry` source node (from the Node Palette → Source → Manual Entry) to type small datasets directly in the Properties panel.

---

## Exporting data

Export the output of any node to a file:

### Via the File menu

1. Select a node on the canvas.
2. Click **File → Export as CSV** (or Parquet, XLSX, JSON).
3. Choose where to save the exported file.
4. An export node is created temporarily, executed, then removed — the file is written to disk.

### Via Export nodes

You can also add explicit **Export** nodes from the Node Palette (Output category). These remain in your pipeline and are executed every time the pipeline runs — useful for generating reports on a schedule.

---

## Settings reference

Open settings with **Ctrl+,** or **Edit → Settings**. Settings are saved automatically and persist between sessions.

### General tab

| Setting | Default | What it does |
|---|---|---|
| Theme | Light | Changes the colour scheme. Options: Light, Dark, High Contrast. |
| Font size | 11 | Base UI font size in points. Affects panels, menus, the node palette, and status bar. |
| Language | System | UI language (future; currently English only). |
| Auto-save interval | 5 min | How often Polaris auto-saves to the recovery folder. Set to 0 to disable. |
| Confirm before delete | On | Show a confirmation dialog before deleting nodes or clearing the graph. |
| Open last workflow on launch | On | Automatically re-open the most recently used `.polaris` file on startup. |

### Appearance tab

| Setting | Default | What it does |
|---|---|---|
| Grid on canvas | On | Show the dot grid in the background. |
| Snap to grid | On | Nodes snap to 20 px increments when moved. |
| Minimap | On | Show the minimap overlay in the bottom-right corner of the canvas. |
| Animate transitions | On | Animate edge pulses, node creation/deletion, view mode switches. |
| Show node IDs | On | Display the internal node ID (e.g., `csv_reader_1`) below the node title. |

### AI tab

| Setting | Default | What it does |
|---|---|---|
| Gemini API key | (empty) | Your Google AI Studio API key. Get one at [aistudio.google.com](https://aistudio.google.com). |
| Model | `gemma-4-31b-it` | The Gemini model to use. Larger models are smarter but slower. |
| Auto-approve commands | Off | When on, AI-generated pipeline changes are applied automatically without showing preview cards. |
| Show action JSON | On | Show the raw JSON behind each AI action card (useful for learning). |
| Max context tokens | 8192 | Limits how much of the conversation history is sent to the AI. |

### Performance tab

| Setting | Default | What it does |
|---|---|---|
| Worker threads | 2 | Number of parallel workers for multi-node execution. Increase for CPUs with many cores. |
| Cache size (MB) | 1024 | Maximum memory used for caching DataFrames between nodes. |
| Auto-profile | On | Automatically compute column profiles (min, max, null count, etc.) when a node is selected. |
| Virtual scroll batch | 100 | Number of rows fetched per batch in the spreadsheet. Lower = smoother but slower for huge tables. |

### Editor tab

| Setting | Default | What it does |
|---|---|---|
| Font | JetBrains Mono | Monospace font for the expression editor and formula bar. |
| Font size | 11 | Monospace font size in points. |
| Tab size | 4 | Spaces per tab in the expression editor. |
| Show line numbers | On | Show line numbers in the expression editor. |
| Auto-close brackets | On | Automatically insert closing `)` and `]`. |
| Syntax highlight | On | Colour-code Polars expressions in the formula bar and expression editor. |

### Charts tab

| Setting | Default | What it does |
|---|---|---|
| Default chart type | Bar | The chart type chosen when creating a chart node from the palette. |
| Colour palette | Default | The colour scheme used for chart series. Options: Default, Vibrant, Pastel, Monochrome. |
| Show legend | On | Display the chart legend by default. |
| Show gridlines | On | Display chart gridlines by default. |
| Export resolution | 2x | Resolution multiplier when exporting charts as PNG. |

### Advanced tab

| Setting | Default | What it does |
|---|---|---|
| Developer mode | Off | Show extra debugging information in the status bar and log panel. |
| Log level | Warning | Minimum log level printed to the terminal. Options: Debug, Info, Warning, Error. |
| OpenGL renderer | Auto | Rendering backend for the canvas. Change to Software if you experience graphical glitches. |
| Temp directory | System default | Where extracted data files go when opening a `.polaris` file. Cleared on exit. |
| Reset all settings | — | Restore every setting to its factory default. |

---

## AI configuration in detail

The AI feature requires a **Gemini API key** from Google AI Studio:

1. Go to [aistudio.google.com](https://aistudio.google.com).
2. Sign in with your Google account.
3. Click **Get API key** → **Create API key**.
4. Copy the key (starts with `AIza...`).
5. In Polaris, open **Settings → AI** and paste the key.
6. Click **Apply**.

Your key is stored securely in your operating system's credential manager:

- **Windows:** Credential Manager
- **macOS:** Keychain
- **Linux:** libsecret

> **Privacy:** Your data and pipeline structure are sent to Google's Gemini API when you chat with the AI. They are **not** used for training. See [Google's privacy policy](https://policies.google.com/privacy) for details. You can disable AI entirely by leaving the API key empty.

---

## File locations

Where Polaris stores its data on disk:

| What | Windows | macOS | Linux |
|---|---|---|---|
| Settings | `%APPDATA%/polaris-studio/settings.ini` | `~/Library/Preferences/polaris-studio/` | `~/.config/polaris-studio/` |
| Recovery / auto-save | `%APPDATA%/polaris-studio/recovery/` | `~/Library/Application Support/polaris-studio/recovery/` | `~/.config/polaris-studio/recovery/` |
| Logs | `%APPDATA%/polaris-studio/logs/` | `~/Library/Logs/polaris-studio/` | `~/.config/polaris-studio/logs/` |
| Temp extracted data | System temp dir (`%TEMP%/polaris_*`) | `/tmp/polaris_*` | `/tmp/polaris_*` |
| Custom fonts (bundled) | Inside app | Inside app bundle | Inside app |
