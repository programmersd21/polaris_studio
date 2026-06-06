# Installation

Polaris Studio is a desktop application. It runs on Windows, macOS, and Linux. The only thing you need is Python 3.11 or newer and a few minutes.

## Before you start

Make sure you have **Python 3.11+** available. To check:

```bash
python --version
# or on some systems
python3 --version
```

If you see `Python 3.11.x` or higher, you're good. If not, [install Python from python.org](https://www.python.org/downloads/) first.

> **Windows users:** Make sure you check **"Add Python to PATH"** during the installer. Otherwise `python` won't be found from the command line.

> **macOS users:** If you have an old system Python, install Python 3.11+ via [Homebrew](https://brew.sh): `brew install python@3.11`.

> **Linux users:** Most modern distros ship with Python 3.11 or newer. If yours doesn't, use your package manager or `pyenv`.

---

## Option 1 - Install as a package (recommended)

This installs Polaris Studio as a command you can run from anywhere.

```bash
# 1. Get the code
git clone https://github.com/programmersd21/polaris_studio
cd polaris_studio

# 2. Install in editable mode
pip install -e .

# 3. Run it
polaris-studio
```

The `pip install -e .` (the dot at the end is important) installs Polaris in "editable" mode. That means any code change you make is immediately visible the next time you run the app, without re-installing. It's the right mode for both users and developers.

---

## Option 2 - Run from source

If you don't want to install, you can run Polaris directly:

```bash
# 1. Get the code
git clone https://github.com/programmersd21/polaris_studio
cd polaris_studio

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python -m polaris_studio
```

The `python -m polaris_studio` form uses the `__main__.py` entry point in the package. It's equivalent to running `polaris-studio` from Option 1.

---

## Option 3 - Install for development

If you plan to write code, run tests, or contribute back:

```bash
git clone https://github.com/programmersd21/polaris_studio
cd polaris_studio
pip install -e ".[dev]"
```

This pulls in extra tools: `pytest` for tests, `mypy` for type checking, `ruff` for linting, and `fontTools` for font patching.

Verify the dev install:

```bash
pytest --version
mypy --version
ruff --version
```

---

## Verifying the install

After installing, run a quick smoke test:

```bash
# 1. Launch the app
polaris-studio

# 2. You should see:
#    - A window titled "Polaris Studio"
#    - A node palette on the left
#    - An empty canvas in the middle
#    - A spreadsheet grid at the bottom
#    - A status bar at the bottom showing "Ready"
```

If you see that, the install worked.

---

## Optional: configure the AI

The AI assistant is **optional**. Polaris works fully without it. If you want to use it:

1. Get an API key from [Google AI Studio](https://aistudio.google.com/apikey) (free tier is fine).
2. Launch Polaris.
3. Open **Settings** (Ctrl+, or Cmd+, on macOS).
4. Click the **AI** tab.
5. Paste your key into **Gemini API key**.
6. Pick a model - `Gemini 2.0 Flash` is a good default.
7. Click **Save**.

Your key is stored locally in your user configuration directory. It is never sent anywhere except to Google's Gemini API when you actually use the AI.

---

## Optional: virtual environments

A Python "virtual environment" isolates Polaris's dependencies from the rest of your system. It's a good practice but not required.

```bash
# Create a venv
python -m venv .venv

# Activate it
# Windows (cmd):
.venv\Scripts\activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# Now install
pip install -e .
```

When you're done, deactivate with `deactivate` (or just close the terminal).

---

## Troubleshooting install

### `python: command not found`

Python isn't on your PATH. Either install it (and check "Add to PATH" on Windows), or use the full path, e.g. `python3` instead of `python`, or `C:\Python311\python.exe` on Windows.

### `pip: command not found`

Try `python -m pip` instead of `pip`. If that works, your system has pip but it's not on PATH.

### `error: Microsoft Visual C++ 14.0 or greater is required` (Windows)

Some Python packages with C extensions need a C compiler on Windows. Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022) and re-run `pip install -e .`. Polaris's hard dependencies (Polars, PyArrow, PySide6) all ship pre-built wheels, so this should not happen - but if it does, that's the fix.

### The window is blank or fonts look wrong

See **[Common issues → Fonts not loading](troubleshooting/common-issues.md#fonts-not-loading)**.

### AI says "No backend configured"

You haven't set an API key yet. See **[Optional: configure the AI](#optional-configure-the-ai)** above.

### First launch is slow

The first time you run Polaris, Windows Defender (or your antivirus) may scan the bundled Polars, PyArrow, and Qt native libraries. This is normal and only happens once. Subsequent launches are much faster.

### Still stuck?

Open an issue on GitHub with the output of:

```bash
python --version
pip show polaris-studio
```

Include your OS, Python version, and the full error message.
