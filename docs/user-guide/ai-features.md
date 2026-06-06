# AI Features

## AI Chat Panel

The AI Chat Panel (Ctrl+Shift+A) is your natural language interface to the whole app.

### Common Tasks

**"filter rows where profit > 1000"**
The AI can emit a command batch that adds a filter node and wires it into the current graph.

**"group by country and show total sales"**
The AI can emit a command batch that creates a group-by aggregate node with the right parameters.

**"add a column called profit_margin = profit / revenue"**
The AI can emit a command batch that adds a computed column node or updates the active sheet cell range.

**"export this as CSV"**
The AI can create an export node and trigger execution.

### Attaching Nodes

Click the [+] button in the AI input area to attach the currently selected node. The AI will see the node's type, params, graph context, and a preview of the active sheet.

Example: Select a Filter node, attach it, then type "why is this removing so many rows?" The AI will analyze the filter condition and the upstream data to explain the impact.

## AI Backend Setup

### Google Gemini (Cloud)
1. Open Settings (Ctrl+,) > AI tab
2. Enter your Gemini API key
3. Select model (Gemini 2.0 Flash recommended)

## AI Command Batches

AI responses can include structured JSON command batches. Polaris Studio validates those commands, shows a proposed-changes card, and applies them to the graph, spreadsheet, panels, and execution state after you review them.

Each proposed-changes card includes a collapsed **Action JSON** pill. Expand it to inspect the exact validated JSON batch that Polaris will apply, or use **Copy** to put the batch on your clipboard for debugging or sharing.

### Supported Actions
- Create, connect, update, delete, and execute graph nodes
- Update cells and style cells
- Insert or delete rows
- Rename, cast, and fill columns
- Switch view modes and toggle panels

### Safety
- Commands are typed and validated before they run
- The app does not accept arbitrary Python code from AI responses
- Execution still goes through the normal app state and data model

## Auto-Approve

Auto-approve can apply AI actions as soon as they validate.

1. Open Settings (Ctrl+,) > AI tab
2. Enable **Auto-approve and execute validated AI actions**
3. Save settings

This setting is off by default. When enabled, Polaris still validates the JSON against the typed command schemas and still shows the action card and execution report, but it skips the manual Apply click.

The AI tab also includes **Show validated Action JSON on proposed changes**. Leave it enabled when you want the collapsible JSON pill on action cards.
