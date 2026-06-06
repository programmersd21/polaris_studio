# Developer Setup Guide

## Prerequisites

- **Python 3.11+**
- **Git**
- **(Optional)** A Gemini API key for AI features (set as `GEMINI_API_KEY` environment variable)

## Clone and Install

```bash
git clone https://github.com/your-org/polaris-studio.git
cd polaris-studio
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Verify Installation

```bash
python -c "from polaris_studio.main import main; print('OK')"
mypy .
pytest tests/
```

## Project Structure

```
polaris_studio/
  agent/          # AI chat, command pipeline, schemas
  core/           # Graph DAG, Engine, Node registry, Profiler
  io/             # CSV/Parquet/XLSX handlers
  state/          # AppState, Workspace, History
  ui/             # PySide6 UI
    graph/        # Canvas, nodes, edges, minimap
    panels/       # AI panel, node palette, properties, charts
    spreadsheet/  # Grid model, view, delegate
    dialogs/      # Settings, expression editor, column stats
```

## Development Workflow

- Run `mypy .` before committing to catch type errors
- Run `pytest tests/` to verify all tests pass
- The `-e` flag in `pip install -e ".[dev]"` enables live reload - source changes take effect immediately without reinstalling

## IDE Configuration

### VSCode

Recommended extensions:
- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **Ruff** (charliermarsh.ruff)

Recommended `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
  "python.terminal.activateEnvironment": true,
  "mypy.runUsingActiveInterpreter": true,
  "ruff.lineLength": 100,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

### PyCharm

- Set the project interpreter to `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (macOS/Linux)
- Enable **Mypy** plugin (Settings → Tools → Mypy)
- Enable **Ruff** plugin (Settings → Tools → Ruff)
- Set line length to 100 in Settings → Editor → Code Style → Python → Hard wrap at

## Building Executables

```bash
pip install pyinstaller
pyinstaller --onefile --name "PolarisStudio" --add-data "src/polaris_studio;polaris_studio" src/polaris_studio/__main__.py
```

**Platform notes:**
- **Windows**: The above command produces `dist/PolarisStudio.exe`. Use `--windowed` to suppress the console window.
- **macOS**: Use `--windowed` and optionally `--icon=app.icns`. The `.app` bundle will be in `dist/`.
- **Linux**: PyInstaller produces a single binary with no special flags needed.
