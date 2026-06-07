# Polaris Studio Documentation

This is the complete documentation for Polaris Studio, a desktop app for working with data by drawing pipelines. It is built in Python with PySide6.

## Who this is for

**If you want to load data, build pipelines, and do analysis**, start with [Getting started](getting-started/installation.md) and walk forward. Each guide builds on the last one.

**If you want to extend, embed, or contribute to Polaris**, start with [Architecture overview](architecture/overview.md) and [Developer setup](developer/setup.md).

**If you just need a specific answer**, jump to the reference. The [Node reference](nodes/reference.md) lists every node and its parameters, the [API reference](developer/api-reference.md) lists every public class, and the [FAQ](troubleshooting/faq.md) covers the most common questions.

---

## How to read these docs

The documentation is split into five tracks that mostly do not depend on each other:

| Track | What it covers | Start here |
|---|---|---|
| **Getting started** | Install, launch, first pipeline, interface tour | [Installation](getting-started/installation.md) |
| **User guide** | Deep dives on every part of the UI | [Core concepts](user-guide/concepts.md) |
| **Node reference** | Every node type, every parameter | [Node reference](nodes/reference.md) |
| **Architecture** | How the internals fit together | [Architecture overview](architecture/overview.md) |
| **Developer** | Setup, testing, contributing, API | [Developer setup](developer/setup.md) |

---

## Getting started

| Guide | What you will learn |
|---|---|
| [Installation](getting-started/installation.md) | Install on Windows, macOS, or Linux. Optional: configure the AI key. |
| [10-minute quick tour](getting-started/quick-tour.md) | See what Polaris can do before you commit. |
| [Your first pipeline](getting-started/first-pipeline.md) | Step-by-step: load a file, filter, sort, chart, export. |
| [Interface tour](getting-started/interface-tour.md) | Every panel, button, and mode explained. |
| [Keyboard shortcuts](getting-started/keyboard-shortcuts.md) | Complete shortcut reference. |

## User guide

| Guide | What you will learn |
|---|---|
| [Core concepts](user-guide/concepts.md) | Nodes, connections, dirty propagation, caching, the difference between data and metadata. |
| [The graph canvas](user-guide/canvas.md) | Pan, zoom, fit-to-screen, select, copy, paste, duplicate, delete, auto-layout. |
| [The panels](user-guide/panels.md) | Overview of all the panels and how they fit together. |
| [The AI assistant](user-guide/ai-panel.md) | Chat, preview cards, auto-approve, what the AI can and cannot do. |
| [The spreadsheet](user-guide/spreadsheet.md) | Grid, formula bar, sorting, freezing, column statistics. |
| [Charts](user-guide/charts.md) | Six chart types, exporting to PNG and SVG. |
| [Command palette](user-guide/command-palette.md) | Ctrl+P, the keyboard-first launcher. |
| [Saving and preferences](user-guide/saving-and-preferences.md) | `.polaris` files, settings, AI keys, performance. |

## Node reference

| Guide | What you will learn |
|---|---|
| [Node reference](nodes/reference.md) | Every node type, its parameters, inputs, outputs, and example usage. |

## Architecture

| Guide | What you will learn |
|---|---|
| [Architecture overview](architecture/overview.md) | The six layers of Polaris and how they communicate. |
| [Graph engine](architecture/graph-engine.md) | How the DAG executes, how caching works, how dirty flags propagate. |
| [AI pipeline](architecture/ai.md) | How the AI emits typed commands, how they are validated, how errors self-correct. |
| [State management](architecture/state.md) | AppState as the single source of truth, multi-tab Workspace, undo/redo. |
| [IPC layer](architecture/ipc.md) | Multi-process compute, Arrow transport, commands. |
| [Design system](reference/design-system.md) | Typography (Inter, Outfit, Instrument Serif, JetBrains Mono), palette, motion. |

## Developer

| Guide | What you will learn |
|---|---|
| [Developer setup](developer/setup.md) | Clone, install, IDE config, project layout. |
| [Testing](developer/testing.md) | pytest, mypy, ruff, how to add tests. |
| [Adding a new node type](developer/adding-a-node.md) | The most common contribution, end to end. |
| [API reference](developer/api-reference.md) | Public classes and methods. |

## Troubleshooting

| Guide | What you will learn |
|---|---|
| [Common issues](troubleshooting/common-issues.md) | Fonts not loading, AI key not working, slow startup. |
| [FAQ](troubleshooting/faq.md) | Short answers to frequent questions. |

---

## Conventions used in these docs

- **Code blocks** are runnable commands. Copy them as-is.
- **Keyboard shortcuts** are shown as `Ctrl+S` (or `Cmd+S` on macOS). The platform key is implied.
- **Pathnames** use forward slashes. They work on Windows, macOS, and Linux.
- **File extensions** matter: `.csv`, `.xlsx`, `.parquet`, `.json` are all explicitly named.
- **Polaris files** end in `.polaris` and are ZIP archives (containing `workflow.json` plus embedded data files).

---

## Not finding what you need?

- Search the docs (Ctrl+F in any browser).
- Open an issue on GitHub.
- Ask the AI assistant. Once you have configured a key, it can answer questions about Polaris itself.
