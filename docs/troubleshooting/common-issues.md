# Common Issues & Troubleshooting

A practical guide to fixing the most common problems you'll run into with Polaris Studio.

---

## AI / Gemini Issues

### "No API key configured" error

**Symptom:** You type something in the AI chat panel and get a message like "No AI backend configured" or "No API key configured."

**Cause:** Polaris Studio uses Google's Gemini API for AI features. You haven't entered an API key yet.

**Solution:**
1. Open **Edit → Settings** (or press `Ctrl+,`).
2. Go to the **AI** tab.
3. Paste your Gemini API key into the "API Key" field. Keys start with `AIza...`.
4. Select a model (e.g. `gemma-4-31b-it` or `gemini-3.1-flash-lite`).
5. Click **Save**. The AI panel is now ready.

### "API key invalid" error

**Symptom:** You configured a key but get an authentication error when sending a message.

**Cause:** The key is wrong, revoked, or doesn't have Gemini API access enabled.

**Solution:**
1. Double-check the key at [aistudio.google.com](https://aistudio.google.com) - make sure you copied it exactly (no extra spaces).
2. Ensure the Gemini API is enabled for your Google Cloud project.
3. If you're using a free key, check your usage quota hasn't been exhausted.
4. Go to **Settings → AI**, re-enter the key, and save.

### AI responses are empty or truncated

**Symptom:** The AI responds with nothing, a "…" that never resolves, or cuts off mid-sentence.

**Cause:** The model may have hit its output token limit, or there's a network issue.

**Solution:**
1. Check your internet connection.
2. Try a different model in **Settings → AI** (e.g. switch from `gemma-4-31b-it` to `gemini-3.1-flash-lite`).
3. If responses are consistently cut off, try asking shorter, more focused questions.
4. Restart Polaris Studio and try again.

### AI doesn't understand the graph

**Symptom:** The AI suggests creating nodes that already exist, references wrong node IDs, or proposes actions that don't make sense.

**Cause:** The AI only sees a text summary of your workspace. Large graphs may exceed the context window, or the summary isn't detailed enough.

**Solution:**
1. Be specific in your prompt - mention node names or column names you see.
2. After making changes manually, give the AI a chance to re-read the workspace by sending a new message.
3. Keep your graph reasonably tidy: rename nodes descriptively instead of relying on auto-generated IDs.
4. For complex workflows, break your request into smaller steps.

---

## Font Issues

### Text looks wrong / blurry

**Symptom:** UI text appears fuzzy, pixelated, or hard to read.

**Cause:** Missing font files, or Qt is falling back to a system font without proper antialiasing.

**Solution:**
1. Ensure the `fonts/` directory exists alongside the executable (or in the project root). It should contain `Inter-Regular.ttf`, `Outfit-Regular.ttf`, `InstrumentSerif-Regular.ttf`, and `JetBrainsMono-Regular.ttf`.
2. Restart Polaris Studio.
3. If fonts still don't load, check the terminal for messages like "font directory not found."

### Font fallback to Segoe UI instead of Inter

**Symptom:** The UI renders in Segoe UI (or another system font) instead of the expected Inter font.

**Cause:** The Inter variable font has an internal family name of "Inter 18pt" instead of "Inter", which makes `font-family: 'Inter'` in stylesheets fall back to the system default. Polaris Studio attempts to patch this at startup, but it may fail if `fontTools` isn't installed.

**Solution:**
1. Install `fonttools`: `pip install fonttools`
2. Restart Polaris Studio. The startup code will rewrite the font's name table so "Inter" resolves correctly.
3. If it still doesn't work, delete the existing `Inter-Regular.ttf` in the `fonts/` folder and re-download the static (non-variable) version of Inter from [fonts.google.com](https://fonts.google.com).

### Instrument Serif not rendering

**Symptom:** Headers like "Polaris Studio" or "AI Assistant" show in a fallback font (e.g. Times New Roman or serif default).

**Cause:** The `InstrumentSerif-Regular.ttf` font file is missing or failed to register.

**Solution:**
1. Check that `InstrumentSerif-Regular.ttf` exists in the `fonts/` directory.
2. Re-download it from [fonts.google.com](https://fonts.google.com) if needed.
3. Restart Polaris Studio.

---

## Performance Issues

### Table / grid is slow with large datasets

**Symptom:** Scrolling, sorting, or editing the spreadsheet lags badly with many rows.

**Cause:** Polaris Studio loads the full dataset into the grid. Very large DataFrames (millions of rows) strain the Qt model/view architecture.

**Solution:**
1. Use **Filter** or **Slice** nodes upstream to reduce the data volume before it reaches the table output.
2. Right-click a column header and choose **Profile** to check row counts before displaying.
3. If you need to browse a large dataset, export it to CSV and use a dedicated viewer.
4. Increase **Cache Size Limit** in **Settings → Performance** if swapping is the bottleneck.

### Canvas lags with many nodes

**Symptom:** Panning, zooming, or dragging nodes on the graph canvas is sluggish with 50+ nodes.

**Cause:** Each node is a complex QGraphicsItem with ports, shadows, and animations.

**Solution:**
1. Use **Auto Layout** (`Ctrl+Shift+L`) to organize nodes and reduce overlap - the layout engine avoids unnecessary redraws.
2. Keep frequently-used sub-graphs in separate tabs.
3. Close panels you're not using (Properties, Chart) to free rendering resources.
4. Reduce the number of visible edges by collapsing completed pipeline sections.

### Startup is slow

**Symptom:** The application takes more than 10 seconds to launch.

**Cause:** Font loading, fontTools font patching, and demo graph population run at startup.

**Solution:**
1. First launch is always slower (fonts need patching). Subsequent launches should be faster.
2. If `fonttools` is not installed, startup will be slightly faster but fonts may not render correctly (see font issues above).
3. Ensure you're on an SSD. Launch speed is primarily I/O-bound.

---

## File / Import Issues

### Can't import CSV / XLSX / Parquet

**Symptom:** File → Import CSV/XLSX/Parquet does nothing, or the file picker doesn't open, or an error appears.

**Cause:** Missing dependencies, or the file format isn't what Polaris expects.

**Solution:**
1. **CSV**: Ensure the file uses UTF-8 encoding (try `encoding: "utf-8"` in the CSV reader node params). For non-standard delimiters, set the `delimiter` parameter (e.g. `;` for semicolon-separated).
2. **XLSX**: Requires `openpyxl`. Install it: `pip install openpyxl`.
3. **Parquet**: Requires `pyarrow`. Install it: `pip install pyarrow`.
4. Check the file isn't open in another program (Excel locks XLSX files).

### Imported data looks wrong

**Symptom:** Columns are missing, data types are wrong, rows are shifted, or nulls appear where there should be values.

**Cause:** Common CSV quirks: no header row, wrong delimiter, encoding mismatch, or leading/trailing rows that should be skipped.

**Solution:**
1. Add a **CSV Reader** node manually from the palette (right-click canvas → Add Node → Source → CSV Reader).
2. Configure parameters:
   - `has_header`: set to `false` if your file has no column names.
   - `delimiter`: change from `,` to `\t` (tab) or `;` as needed.
   - `encoding`: try `latin-1` or `utf-16` if UTF-8 produces garbled text.
   - `skip_rows`: set to skip introductory lines before the actual data.
3. Execute the node to see the preview.

### File encoding problems

**Symptom:** Special characters (é, ñ, ü, etc.) show as `?` or garbled symbols.

**Cause:** The file uses an encoding other than UTF-8 (e.g. Latin-1, Windows-1252, Shift-JIS).

**Solution:**
1. In the **CSV Reader** node, change the `encoding` parameter to match your file's encoding. Common alternatives: `latin-1`, `cp1252`, `utf-16`.
2. Re-execute the node.
3. If you're not sure what encoding the file uses, open it in a text editor like VS Code - the encoding is usually shown in the status bar.

---

## Save / Load Issues

### .polaris file won't open

**Symptom:** You double-click a `.polaris` file (or File → Open) and nothing happens, or an error dialog appears.

**Cause:** The file may be from an older version, corrupted, or not really a `.polaris` file.

**Solution:**
1. Make sure the file has the `.polaris` extension and isn't corrupted (check file size - it should be at least a few KB).
2. Try opening it via **File → Open Workflow** (`Ctrl+O`) instead of double-clicking.
3. Check the terminal for specific error messages.

### "Corrupt .polaris file" error

**Symptom:** You get a dialog saying "Corrupt .polaris file: missing workflow.json".

**Cause:** A `.polaris` file is actually a ZIP archive containing `workflow.json` and optionally embedded data files. If `workflow.json` is missing or the ZIP is damaged, this error appears.

**Solution:**
1. Rename the file to `.zip` and try to open it with a ZIP utility. If that fails, the file is genuinely corrupted.
2. If the ZIP opens, check whether `workflow.json` is inside. If it is, the file might have been created by a very old version - try importing it manually.
3. Always keep backups of important `.polaris` files.
4. If you have a recent autosave or backup, use that instead.

### Data files not found after moving .polaris

**Symptom:** After opening a `.polaris` file on a different computer or from a different folder, CSV/XLSX/Parquet reader nodes show errors.

**Cause:** Earlier versions of Polaris Studio stored file paths as absolute references. The current version embeds data files directly inside the `.polaris` ZIP archive. If you're opening an old file, the paths are stale.

**Solution:**
1. The modern `.polaris` format embeds your source data files inside the ZIP. When you open the file, Polaris extracts them to a temp directory and updates the paths automatically.
2. If you're opening a very old `.polaris` (before the ZIP format was introduced), you'll need to re-import the data files manually.
3. To avoid this in the future, always use **Save** (`Ctrl+S`) to create a `.polaris` file - that way data gets embedded.

---

## Display / UI Issues

### QPainter warnings in the terminal

**Symptom:** You see messages like `QPainter::begin: Paint device returned engine == 0` or similar warnings in the console.

**Cause:** These are harmless Qt warnings that occur during widget initialization or repaint cycles. They don't affect functionality.

**Solution:**
1. Ignore them. They're cosmetic and don't indicate a real problem.
2. If they bother you, set the environment variable `QT_LOGGING_RULES=*.debug=false` before launching.

### Window icon not showing

**Symptom:** The Polaris Studio window has a default blank icon in the taskbar and title bar.

**Cause:** The application icon file is bundled but might not be loading correctly on your platform.

**Solution:**
1. This is a known minor issue on some platforms. The application is fully functional.
2. The icon is loaded from the application's resource path. If you built from source, ensure the icon file is in the expected location.
3. If you'd like to set a custom icon, you can set it via your desktop environment's launcher settings.

### Zoom shortcuts not working (Ctrl++ / Ctrl+-)

**Symptom:** Pressing `Ctrl++` or `Ctrl+-` doesn't zoom in/out on the graph canvas.

**Cause:** On some keyboard layouts, `Ctrl++` requires pressing `Ctrl+Shift+=`. The canvas also supports `Ctrl+Scroll` as the primary zoom method.

**Solution:**
1. Try `Ctrl+Scroll` (hold Control and scroll the mouse wheel) - this is the primary and most precise zoom method.
2. For `Ctrl++`: try `Ctrl+Shift+=` (on US keyboards, `+` is on the same key as `=`).
3. You can also press `F` to fit the entire graph to the screen.
4. Use the **View** menu to switch between Graph/Spreadsheet modes if you accidentally zoomed out too far.

### Double-click in palette makes nodes disappear

**Symptom:** Double-clicking a node type in the Node Palette creates a node, but it seems to vanish or appear off-screen.

**Cause:** The node is created at the center of the *visible viewport*. If you're in Spreadsheet mode or the graph canvas is scrolled far away, the node might be placed out of view.

**Solution:**
1. Switch to **Graph mode** (click "Graph" in the toolbar or press `F2`) before double-clicking the palette.
2. Press `F` to fit all nodes to the screen - this will reveal the newly created node.
3. Alternatively, drag nodes from the palette directly onto the canvas instead of double-clicking.
4. If nodes consistently appear in the wrong place, check that you're in Graph mode (not Split or Spreadsheet mode).

### Column names forced to uppercase

**Symptom:** After importing data or executing a node, all column names appear in UPPERCASE.

**Cause:** This is by design - Polaris Studio normalizes column names to uppercase for consistency across different data sources (CSV headers, Excel, Parquet schemas can all vary in casing).

**Solution:**
1. This is intentional behavior, not a bug.
2. Use the **Rename Columns** node if you need specific casing.
3. You can also right-click a column header in the spreadsheet and choose **Rename** to change individual column names.

---

## Installation Issues

### Python version not supported

**Symptom:** `pip install polaris-studio` fails with an error about unsupported Python version.

**Cause:** Polaris Studio requires Python 3.10 or higher (it uses `match` statements, `|` union syntax, and other 3.10+ features).

**Solution:**
1. Check your Python version: `python --version`.
2. If it's below 3.10, install a newer Python from [python.org](https://python.org).
3. If you have multiple Python versions, use the correct one: `python3.11 -m pip install polaris-studio`.

### Dependencies won't install

**Symptom:** `pip install` fails with compilation errors, missing headers, or conflicts.

**Cause:** Some dependencies have native extensions that require a C compiler (e.g. `polars`, `pyarrow`, `pyqtgraph`).

**Solution:**
1. Use Python 3.11 or 3.12 - these have the best binary wheel support on PyPI.
2. On Windows, install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
3. On Linux, install `python3-dev` (or `python3-devel` on RPM-based distros): `sudo apt install python3-dev`.
4. Create a fresh virtual environment and try again:
   ```
   python -m venv polaris-env
   polaris-env\Scripts\activate   # Windows
   source polaris-env/bin/activate # Linux/Mac
   pip install polaris-studio
   ```

### PySide6 installation fails

**Symptom:** PySide6 fails to install with a missing Qt platform plugin error, or the install crashes.

**Cause:** PySide6 ships prebuilt wheels for most platforms, but some Linux distributions need additional system libraries.

**Solution:**
1. **Windows / macOS**: PySide6 should install cleanly via `pip install PySide6`. If it fails, update pip: `pip install --upgrade pip`.
2. **Linux**: Install system-level Qt dependencies:
   - Ubuntu/Debian: `sudo apt install libxcb-cursor0 libxcb-xinerama0 libegl1`
   - Fedora: `sudo dnf install qt6-qtbase-gui`
3. If you're in a headless environment (no display), PySide6 won't work. Use it only on a machine with a desktop.
4. As a last resort, use Python 3.11 which has the most reliable Qt/PySide6 binary wheels.
