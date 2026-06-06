# Getting Started

## Installation

```bash
# Clone the repository
git clone https://github.com/programmersd21/polaris_studio
cd polaris-studio

# Install dependencies
pip install -e .

# Launch
polaris-studio
```

## First Steps

### 1. Import Data
- Click **File > Import CSV** (or Parquet/JSON/XLSX)
- Select your file
- A Source node appears on the graph canvas

### 2. Build a Pipeline
- Open the **Node Library** on the left
- Drag nodes onto the canvas, or:
- Right-click the canvas and select **Add Node**

### 3. Connect Nodes
- Click an output port (right edge of node) and drag to an input port (left edge)
- Cycles are automatically detected and rejected

### 4. Configure Nodes
- Click a node to select it
- Edit parameters in the **Properties Panel** on the right
- Changes immediately mark downstream nodes dirty

### 5. Execute
- Press **F5** to execute all nodes
- Or click **Execute** in the Properties Panel for a single node
- Results appear in the bottom table view

## View Modes

- **F1**: Spreadsheet mode - full-screen grid
- **F2**: Graph mode - full-screen canvas
- **F3**: Split mode - 50/50 grid and canvas
- Toggle via toolbar buttons

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+P | Command Palette |
| Ctrl+Z | Undo |
| Ctrl+Shift+Z | Redo |
| Ctrl+S | Save Workflow |
| Ctrl+O | Open Workflow |
| F5 | Execute All |
| Ctrl+Shift+L | Auto Layout |
| Ctrl+Shift+A | AI Panel |
| Ctrl+G | Toggle Grid |
| Delete | Delete selected nodes |
| Ctrl+D | Duplicate selected nodes |
