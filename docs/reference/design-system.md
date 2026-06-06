# Design System

Polaris Studio's visual design is intentional, consistent, and detail-oriented. This page documents every design decision — typography, colour, spacing, motion, and visual hierarchy — so you understand *why* the UI looks the way it does.

---

## Typography

Four typefaces, each with a specific role:

### Inter (UI & body text)

- **Usage:** Menus, panels, labels, node body text, tooltips, status bar, table column headers.
- **Weights:** Regular (400) for body, Medium (500) for labels, SemiBold (600) for panel titles.
- **Size:** 11–13 pt for most UI; 10 pt for captions.
- **Why:** Crisp, highly legible at small sizes. Designed for UI. Loaded from the bundled `Inter-Variable.ttf`.

> **Note:** The bundled Inter font is a variable font with optical sizes. On load, Polaris patches the internal font family name from `Inter 18pt` to `Inter` so that Qt stylesheets using `font-family: 'Inter'` resolve correctly.

### Outfit (titles & badges)

- **Usage:** Node headers (title and category glyph), category headers in the palette, the AI pill in the status bar, badges and tags.
- **Weights:** DemiBold (600) for node titles, Bold (700) for badges.
- **Size:** 13–14 pt in nodes; 11 pt in the status bar pill.
- **Why:** Friendly, modern, geometric. Gives the node headers a distinct visual weight that differentiates them from surrounding UI.

### Instrument Serif (premium highlights)

- **Usage:** The "Polaris Studio" wordmark, canvas empty state ("Build your workflow."), AI panel header ("AI Assistant"), Properties panel header ("Properties"), dialog titles.
- **Weight:** Regular (400), with italic for canvas sub-text.
- **Size:** 24 pt for the wordmark, 34 pt for canvas empty-state title, 15 pt italic for canvas subtitle, 16–18 pt for dialog titles.
- **Why:** Serif brings warmth, elegance, and a premium feel. Used sparingly — only for hero moments — to create a clear visual hierarchy. Never used for body text or interactive elements.

### JetBrains Mono (code & data)

- **Usage:** Expression editor, formula bar, cell values in the spreadsheet, node IDs, column data type labels, raw JSON in AI action cards.
- **Weight:** Regular (400) with ligatures enabled.
- **Size:** 10–11 pt.
- **Why:** Designed for code. Excellent readability with distinct character shapes (`0` vs `O`, `1` vs `l`). Ligatures (`!=`, `->`, `=>`) make expressions more readable.

### Font fallback chain

When a font can't be loaded (e.g., the TTF is missing), Polaris falls back through this chain:

- **Inter** → system UI font (Segoe UI on Windows, SF Pro on macOS)
- **Outfit** → Inter → system UI
- **Instrument Serif** → Georgia → system serif
- **JetBrains Mono** → Consolas → Courier New → monospace

---

## Colour palette (Light theme)

The current default theme. A dark theme is planned.

### Application chrome

| Token | Hex | Role |
|---|---|---|
| `bg_app` | `#f6f7fb` | Outer background (behind panels) |
| `bg_panel` | `#ffffff` | Panel, menu, and dock backgrounds |
| `bg_canvas` | `#f3f6fb` | Graph canvas background |
| `bg_node` | `#ffffff` | Node card body |
| `bg_node_alt` | `#f0f2f7` | Hovered node, menu item hover |
| `border` | `#e2e5ed` | Borders (subtle) |
| `border_strong` | `#c8cdd9` | Hovered borders, focus rings |

### Text

| Token | Hex | Role |
|---|---|---|
| `text_primary` | `#172033` | Main text (headings, labels, values) |
| `text_secondary` | `#5f6b7f` | Secondary text (descriptions, hints) |
| `text_muted` | `#919bab` | Placeholder, disabled, captions |
| `text_inverse` | `#ffffff` | Text on accent backgrounds |

### Accent & semantic

| Token | Hex | Role |
|---|---|---|
| `accent` | `#245bdb` | Primary action, selected state, links |
| `accent_dim` | `#e8edf8` | Accent hover/active backgrounds |
| `success` | `#16a34a` | Execution success, valid state |
| `warning` | `#ea9a2b` | Dirty indicator, warnings |
| `error` | `#dc2626` | Execution errors, validation failures |
| `running` | `#2563eb` | Computing/executing state |

### Category colours (node headers)

Each node category has a distinct header colour:

| Category | Colour |
|---|---|
| Source | `#059669` (emerald) |
| Transform | `#2563eb` (blue) |
| Filter | `#7c3aed` (violet) |
| Aggregate | `#d97706` (amber) |
| Join | `#0891b2` (cyan) |
| Sort | `#dc2626` (red) |
| Chart | `#db2777` (pink) |
| Output | `#475569` (slate) |

---

## Spacing & sizing

| Token | Pixels | Usage |
|---|---|---|
| SPACING.xs | 4 | Tiny gaps between inline elements |
| SPACING.sm | 8 | Padding inside compact containers |
| SPACING.md | 12 | Padding inside cards, between sections |
| SPACING.lg | 16 | Padding around panels, between widgets |
| SPACING.xl | 24 | Section spacing, around dialogs |

### Node dimensions

| Measurement | Value |
|---|---|
| Width | 200 px |
| Header height | 38 px |
| Port spacing | 22 px |
| Body padding | 12 px |
| Corner radius (`md`) | 8 px |
| Shadow offset | (0, 4) px, 55 alpha |

---

## Motion & animation

### Timing

| Token | Duration | Usage |
|---|---|---|
| `FAST` | 80–100 ms | Button press, opacity dip, micro-interactions |
| `NORMAL` | 200–300 ms | Node creation, deletion, property changes |
| `SLOW` | 400–600 ms | Panel reveal, view mode switch, launch sequence |

### Easing curves

| Curve | Usage |
|---|---|
| `ease-out` (cubic) | Most UI animations (panel slides, opacity fades) |
| `spring()` | Bouncy feel for organic interactions (node drag release, palette press release) |
| `accel_decel()` | Motion that accelerates then decelerates (scroll, auto-layout) |
| `linear` | Pulse animation on edges during compute |

### Pattern catalogue

| Animation | What it animates |
|---|---|
| **fade_slide_in** | Panels on reveal (offset + opacity). Used for AI panel, properties panel, launch sequence. |
| **graphics_materialize** | New nodes appear with a scale-up + fade. |
| **graphics_destroy** | Removed nodes shrink and fade out. |
| **animate_graphics_pos** | Node position changes during auto-layout. |
| **pulse_graphics_item** | Subtle scale pulse on compute start/finish. |
| **edge pulse** | Dashed-line animation along edges during execution. |
| **opacity_pop** | Quick opacity flash for feedback (filter change, search results). |
| **viewport_flash** | Brief white flash on viewport after graph change. |

---

## Visual hierarchy

The UI is organised so your eye flows naturally:

1. **Canvas** — the dominant workspace. Everything else supports it.
2. **Wordmark** ("Polaris Studio") — top-left, Instrument Serif, sets the brand tone.
3. **Toolbar & menus** — quick actions, always accessible.
4. **Node Palette** (left) — the toolbox. You come here to add nodes.
5. **Properties Panel** (right) — context-sensitive. Shows details for whatever is selected.
6. **AI Panel** (right, bottom) — chat interface. Slides in when needed.
7. **Spreadsheet** (bottom) — the data view. Resizeable pane.
8. **Status bar** (bottom) — persistent status info, execution time, row count.

### Node visual hierarchy (within a single node)

1. **Category colour strip** — top. Instantly tells you what kind of node it is.
2. **Category glyph** — single letter in a rounded square.
3. **Node title** — bold, Outfit. The display name.
4. **Node ID** — smaller, monospace. Helps when debugging.
5. **Ports** — labelled circles on left (input) and right (output).
6. **Body** — parameter previews or port labels.

---

## States

Every interactive element has distinct visual states.

### Node states

| State | Visual |
|---|---|
| NORMAL | Thin border (`1.0 px`), white background, subtle shadow |
| HOVERED | Stronger border (`1.2 px`), slightly darker background, shadow more prominent |
| SELECTED | Accent-colour border (`1.6 px`), white background |
| COMPUTING | Blue border (`1.6 px`), light blue background, subtle scale pulse |
| SUCCESS | Green border (`1.4 px`), light green background, brief flash |
| ERROR | Red border (`1.6 px`), light red background |
| DISABLED | Grey border, muted colours, reduced opacity |

### Port states

| State | Visual |
|---|---|
| IDLE | Small circle, `border_strong` colour |
| HOVERED | Larger, accent-colour fill |
| CONNECTED | Accent-colour fill, slightly larger |
| DRAGGING (valid target) | Pulse glow, accent colour |
| DRAGGING (invalid target) | Dimmed, red tint |

### Edge states

| State | Visual |
|---|---|
| IDLE | Thin bezier curve, `border_strong` colour, `0.8` opacity |
| HOVERED | Thicker, accent colour, `1.0` opacity |
| SELECTED | Accent colour, thicker |
| ANIMATING | Dashed stroke with moving dash pattern (during compute) |

---

## Shadows

Polaris uses small, offset shadows for depth. No `box-shadow` CSS property (Qt doesn't support it).

- **Node shadow:** Painted manually in `NodeItem.paint()` as a slightly offset (0, 4 px) rounded rectangle with 55 alpha black. Shadow is 2 px wider and 4 px taller than the body.
- **Dropdown menus:** Qt stylesheet `border` + `background` creates the visual separation.
- **Modal dialogs:** Native OS shadow via the window manager.

> **Why manual shadow instead of QGraphicsDropShadowEffect?** Qt's `QGraphicsDropShadowEffect` causes `QPainter` conflicts when applied to items with custom `paint()` methods. The manual approach is more performant and avoids terminal warnings.
