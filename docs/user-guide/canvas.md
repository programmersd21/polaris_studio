# The Graph Canvas

The canvas is the heart of Polaris. It's where you build pipelines. This page covers every gesture, every shortcut, and every trick.

## What's on the canvas

The canvas shows:

- **Nodes** - the boxes, each one a transformation.
- **Edges** - the lines between them, showing data flow.
- **Selection box** - a dashed rectangle when you box-select.
- **Minimap** - a small overview in the bottom-right corner (toggle via **View → Toggle Minimap**).
- **Status overlay** - transient messages like "Auto-layout complete" appear briefly at the bottom.
- **Grid dots** (optional) - a faint background grid to help you align. Toggle with **Ctrl+G**.

Each node has a status dot in its top-right:

| Dot colour | Meaning |
|---|---|
| Grey | Not yet executed |
| Yellow | Dirty (parameters or inputs changed) |
| Blue | Currently running |
| Green | Success (cached) |
| Red | Error |

---

## Adding nodes

There are four ways to add a node:

### Drag from the palette

1. Open the **Node Palette** on the left (if hidden: **View → Panels → Node Palette**).
2. Type a search term in the palette's search box, or browse categories.
3. **Drag** a node onto the canvas. It lands where you drop it.
4. The new node is auto-selected; configure it in the Properties Panel on the right.

### Double-click a palette entry

1. Click a category in the palette to expand it.
2. **Double-click** a node. It lands in the centre of the canvas.
3. Configure in the Properties Panel.

### Right-click the canvas

1. **Right-click** anywhere on the canvas.
2. Pick **Add Node** from the context menu.
3. Pick a node type.
4. It lands at your cursor.

### Use the command palette

1. **Ctrl+P** to open the command palette.
2. Type `add` or the node's name.
3. Press **Enter** to add the highlighted node to the centre of the canvas.

The first three are usually fastest. The command palette is good when you know exactly what you want.

---

## Connecting nodes

### The easy way

1. **Hover** over the right edge of a node. The output port appears (a small dot, glows blue on hover).
2. **Click and drag** from the port. A line follows your cursor.
3. **Drag toward** the left edge of another node. The input port appears.
4. **Release** when the line snaps to the port. An edge is born.

### The keyboard way

1. **Select** a node.
2. Hold **Shift** and **drag from the node's body** to another node.
3. The edge is created from the first compatible output to the first compatible input.

### Multiple edges

A node can have multiple outputs going to multiple downstream nodes. A node can have multiple inputs from multiple upstream nodes (for joins). The only constraint is **no cycles** - Polaris will reject a connection that would create one.

### Deleting an edge

- **Hover** over the edge, **right-click** → **Delete Edge**.
- Or **click** the edge to select it, then press **Delete**.

---

## Selecting

- **Click** a node to select it.
- **Shift+click** to add to the selection.
- **Ctrl+click** to toggle in the selection.
- **Drag a box** on empty canvas to box-select every node inside it.
- **Ctrl+A** to select all.
- **Escape** to clear the selection.

When multiple nodes are selected, you can move them together by dragging any one of them. Edges between selected nodes stay connected.

---

## Moving, copying, deleting

| Action | Shortcut | Notes |
|---|---|---|
| Move | Drag the node | Snaps to grid (if enabled) |
| Copy | Ctrl+C | Copies to internal clipboard |
| Cut | Ctrl+X | Removes from canvas, puts on clipboard |
| Paste | Ctrl+V | Pastes at cursor or canvas centre |
| Duplicate | Ctrl+D | Same as copy + paste, in one step |
| Delete | Delete | Removes the node and any connected edges |
| Undo | Ctrl+Z | Reverts the last change |
| Redo | Ctrl+Y | Re-applies |

### Multi-step moves

If you select multiple nodes, dragging moves all of them. The relative positions are preserved.

---

## Pan, zoom, fit

### Pan

- **Middle-mouse drag** - the classic.
- **Space + drag** - if your mouse has no middle button, hold **Space** and drag with the left button.
- **Arrow keys** - when no node is selected, scrolls the canvas.

### Zoom

- **Ctrl+scroll** - zoom with the mouse.
- **Ctrl++** / **Ctrl+-** - zoom in / out.
- **Ctrl+1** - zoom to 100%.
- **Ctrl+0** or **F** - fit the whole graph to the screen.

### Fit-to-screen

**F** is your friend. After auto-layout or whenever things feel lost, press **F** to fit the entire graph to the viewport.

---

## Auto-layout

If the canvas gets messy, **Ctrl+Shift+L** (or **View → Auto Layout**) re-arranges nodes into a tidy top-to-bottom hierarchy. The layout engine is a layered (Sugiyama-style) algorithm that:

- Groups nodes by depth (how many edges from the source).
- Places them in columns.
- Routes edges to minimise crossings.
- Adds spacing.

The result is rarely perfect for very complex graphs, but it's a great starting point. You can drag nodes after auto-layout to fine-tune.

---

## Selection and multi-edit

### Single-node properties

When one node is selected, the **Properties Panel** on the right shows its parameters. Edit any field and press **Enter** (or click outside) to apply.

### Multi-node edit

When multiple nodes are selected, the Properties Panel shows only the **common** parameters. For example, if you select two `Filter` nodes, you can change the `expression` for both at once. If you select a `Filter` and a `Sort`, the panel is empty (nothing in common) and shows a hint to select similar nodes.

### Bulk actions

With multiple nodes selected, you can:

- **Move** them together.
- **Copy / cut / paste / duplicate** them as a group.
- **Delete** them all.
- **Group** them into a single moveable block (**Ctrl+G**).
- **Ungroup** the selection (**Ctrl+Shift+G**).
- **Auto-layout** the whole canvas (the layout engine preserves selection).

---

## Grouping

Grouping is like putting a folder around a set of nodes. The group is one moveable block, but the nodes inside stay individually selectable.

1. Select the nodes you want to group.
2. **Ctrl+G**. A subtle outline appears around the group.
3. **Drag** any node in the group to move them all.
4. **Click a single node** inside the group to select just that node.
5. **Click the group boundary** to select the whole group.
6. **Ctrl+Shift+G** to ungroup.

Groups can be **nested** - group within a group within a group.

Groups **do not change execution**. The nodes still run in the same order; the group is purely a UI organisation.

---

## Edge interactions

### Hovering

Hover an edge to see:

- A small **popover** with the source and target node IDs.
- The edge **brightens** to the hover colour (blue).

### Selecting

**Click** an edge to select it. It turns to the selected colour (a darker blue). With an edge selected, the Properties Panel shows the connection details. You can also **Delete** the selected edge.

### Re-routing

You can't drag the middle of an edge to re-route it - edges always go from output port to input port. To "re-route", delete the edge and create a new one.

---

## Context menu

**Right-click** the canvas to get:

- **Add Node →** - submenu of all node types.
- **Paste** - if there's something on the clipboard.
- **Auto Layout** - re-tidy.
- **Fit to Screen** - re-zoom.

**Right-click** a node to get:

- **Execute** - run up to and including this node.
- **Preview Output** - show this node's output in the spreadsheet.
- **Duplicate** - same as Ctrl+D.
- **Rename** - change the display name.
- **Delete** - same as Delete key.
- **Reveal in Canvas** - pan/zoom to centre this node.

**Right-click** an edge to get:

- **Delete Edge** - same as selecting + Delete.
- **Reconnect** - pick a different source or target (advanced).

---

## Minimap

The minimap is a small overview in the bottom-right corner of the canvas. It shows the entire graph at a tiny scale.

- **Click** anywhere on the minimap to jump there.
- **Drag** on the minimap to pan the main canvas.
- The current viewport is shown as a translucent rectangle on the minimap.

Hide it via **View → Toggle Minimap** if you want more canvas space.

---

## Snap grid

By default, nodes snap to a 20-pixel grid when you drag them. This keeps things tidy. Toggle it with **Ctrl+G** or **View → Toggle Grid**.

When grid snap is on, dragging a node "sticks" to the nearest grid intersection. When off, you can place nodes at any position.

The grid is invisible by default (you don't see dots), but **View → Show Grid** draws faint dots at the snap points. This is useful for alignment when you want a hand-tuned layout.

---

## Tips and tricks

- **F to fit** is your most-used shortcut. Get lost? Press F.
- **Ctrl+Shift+L** to auto-layout after big changes.
- **Hold Shift while dragging** an edge to constrain it to horizontal/vertical for the middle segment (rarely needed but available).
- **Double-click a node body** to quickly open its main parameter in the Properties Panel and focus the input.
- **Right-click → Reveal in Canvas** if a node is offscreen (e.g., after auto-layout on a huge graph).
- **Use groups** to declutter. Even a 5-node pipeline is more readable when grouped by purpose: "load", "clean", "compute", "output".
- **The palette search** is fuzzy. Type "fil" to find Filter, Fill Null, and Profile. Type "joi" for the join family.
- **Tab out of a property** to commit it and move to the next field. **Shift+Tab** to go back.

---

## Common mistakes

- **Trying to create a cycle.** Polaris will refuse. If you need A's output to influence A's input, you almost certainly want a different design (a parameter, not a connection).
- **Connecting two outputs together.** Connections are output → input, not output → output. Drag from the right port to the left port.
- **Forgetting to reconnect after deleting a node.** When you delete a node, all its edges are deleted. You'll have to re-wire.
- **Zooming too far out.** Polaris caps zoom-out at 10% to prevent losing the graph. If you can't find a node, press F.
