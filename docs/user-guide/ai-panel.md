# The AI Assistant

The AI assistant is your plain-English interface to the whole app. Describe what you want in normal sentences and it proposes the exact nodes, connections, and edits to make it happen. You always see what it's about to do before it touches your data.

This page covers everything about using the AI: setup, chat, preview cards, auto-approve, what it can and can't do, and best practices.

## Open the AI panel

- **Ctrl+Shift+A** - toggle the AI panel.
- Click the ✨ button in the toolbar.
- **View → Panels → AI Assistant**.
- Click the **AI** pill in the status bar.

The panel opens as a dock on the right (or wherever you've docked it).

## Setup: configure your API key

The AI needs an API key. Polaris currently supports Google Gemini.

1. Get a key from [Google AI Studio](https://aistudio.google.com/apikey) (free tier is fine).
2. Open **Settings** with **Ctrl+,**.
3. Click the **AI** tab.
4. Paste your key into **Gemini API key**.
5. Pick a model - `Gemini 2.0 Flash` is a good default. `Gemini 2.5 Pro` is smarter but slower and pricier.
6. Click **Save**.

Your key is stored in your local user config directory (`~/.config/polaris-studio/` on Linux, `%APPDATA%/polaris-studio/` on Windows, `~/Library/Application Support/polaris-studio/` on macOS). It is only ever sent to Google's Gemini API when you actually use the AI.

### Without a key

If no key is configured, the AI panel still works - it just says *"No AI backend configured. Open Settings (Ctrl+,) to add your Gemini API key."* Everything else in Polaris works normally.

---

## The panel layout

```
┌────────────────────────────────────────────┐
│  AI Assistant  [Polaris]    [Settings]     │  ← Header (Instrument Serif)
├────────────────────────────────────────────┤
│                                            │
│  [You]                                      │  ← User bubble
│  filter where profit > 1000                │
│                                            │
│  [Polaris AI]                              │  ← AI bubble (with cursor)
│  I'll add a filter node with the           │
│  condition pl.col('profit') > 1000.        │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ Proposed changes                     │  │  ← Action preview card
│  │                                      │  │
│  │ Add filter where profit > 1000       │  │
│  │ 1 × add_node                         │  │
│  │ 1 × connect                          │  │
│  │ 1 × update_param                     │  │
│  │                                      │  │
│  │ [Action JSON  +]  [Copy]            │  │
│  │                                      │  │
│  │ [Apply]   [Skip]                     │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  [Polaris AI]                              │
│  ✓ Filter added. Want me to chart it?      │
│                                            │
│  [✓ Changes applied]                       │  ← Execution report card
│  ✓ add_node                                │
│  ✓ connect                                 │
│  ✓ update_param                            │
│                                            │
├────────────────────────────────────────────┤
│  [Ask anything about your data…] [Send]    │  ← Input
└────────────────────────────────────────────┘
```

## Chat basics

- **Type a message** in the input at the bottom.
- **Enter** sends. **Shift+Enter** adds a newline.
- The **Send** button is on the right; it morphs to a "..." spinner while waiting for the AI.

### What to say

Be specific. The more context you give, the better. Good examples:

- *"filter where profit > 1000"*
- *"group by country and show total sales per country, sorted by sales descending"*
- *"add a column called profit_margin = profit / revenue, then drop the profit column"*
- *"export the current result to /tmp/result.csv"*
- *"join the orders table with the customers table on customer_id, then count rows per country"*
- *"show a bar chart of revenue per region"*

Less good:

- *"make it better"* (what does "better" mean?)
- *"do the thing"* (which thing?)
- *"clean the data"* (clean how? which columns?)

### Attaching context

Click the **+** button (or the paperclip icon) in the input area to attach the currently selected node as context. The AI will then see:

- The node's type and ID.
- Its current parameters.
- The first few rows of its output.
- The schema (column names and types).
- The graph context (what's upstream and downstream of this node).

This is very useful for debugging:

- *"why is this filter removing so many rows?"* - attach the filter; the AI will see the filter condition and the upstream data and explain.
- *"this join is slow, what can I do?"* - attach the join; the AI will see the join keys, the row counts on each side, and the join type.

You can also type the word **"this"** in your message to refer to the attached node without using the + button.

### Multi-turn

The AI remembers the conversation. You can ask follow-ups:

1. *"add a filter for profit > 1000"*
2. *"now also group by country"*
3. *"actually, change the threshold to 5000"*
4. *"and chart it"*

Each turn the AI sees the previous turns, the current graph state, and the current data. It can incrementally build complex pipelines.

---

## Preview cards (the most important UI element)

When the AI proposes a change, you see a **preview card**. This is the single most important thing to understand about Polaris's AI.

```
┌────────────────────────────────────────────┐
│  Proposed changes                          │
│                                            │
│  Add filter where profit > 1000            │  ← Description (if provided)
│                                            │
│  1 × add_node                              │  ← Summary of actions
│  1 × connect                               │
│  1 × update_param                          │
│                                            │
│  [Action JSON  +]   [Copy]                 │  ← Expand / copy
│                                            │
│           [Apply]              [Skip]      │  ← THE TWO BUTTONS
└────────────────────────────────────────────┘
```

### What the two buttons do

- **Apply** - execute the proposed commands against your graph. This is the same path a manual edit takes. The graph updates, the spreadsheet updates, every panel updates.
- **Skip** - discard the proposal. The AI's response is still visible in the conversation (for context) but nothing changes in your data.

There is no third option. You either apply or skip. The AI cannot do anything without your explicit click.

### Inspecting the JSON

Click **Action JSON** to expand the full validated JSON:

```json
{
  "type": "action_batch",
  "batch": {
    "description": "Add filter where profit > 1000",
    "commands": [
      {
        "action": "add_node",
        "node_type": "filter",
        "node_id": "filter-3",
        "position": [400, 200]
      },
      {
        "action": "add_edge",
        "src": "csv_reader-1",
        "tgt": "filter-3"
      },
      {
        "action": "update_param",
        "node_id": "filter-3",
        "key": "expression",
        "value": "pl.col('profit') > 1000"
      }
    ]
  }
}
```

This is the exact validated command batch that will be applied. You can:

- **Read it** to understand exactly what the AI wants to do.
- **Copy it** with the **Copy** button (handy for sharing or debugging).
- **Edit it** in the input - paste it back, modify, and ask the AI to apply the modified version (advanced).

If the JSON ever looks wrong, click **Skip** and rephrase your request.

### After Apply

Once you click Apply, Polaris executes the commands. You'll see an **Execution Report Card** appear in the conversation:

```
┌────────────────────────────────────────────┐
│  ✓ Changes applied                         │
│  ✓ add_node                                │
│  ✓ connect                                 │
│  ✓ update_param                            │
└────────────────────────────────────────────┘
```

If any command fails, the symbol flips to ✕ and a red message explains why. The graph is still consistent - Polaris applies commands in order and stops at the first error, leaving the graph in a valid state.

---

## What the AI can and can't do

### ✅ The AI can

- **Add, connect, update, rename, delete, and execute** any node.
- **Configure parameters** - expressions, thresholds, columns, types, options.
- **Bulk operations** - set every cell in a column, fill all nulls, etc.
- **Spreadsheet edits** - cell updates, row inserts/deletes, column renames/casts/fills.
- **View operations** - switch modes, toggle panels, zoom, fit.
- **Multi-step plans** - do many things in one response.
- **Reference the attached node** for context (the `+` button).
- **Self-correct** when validation fails (usually within 1–2 retries).

### ❌ The AI cannot

- **Run arbitrary Python code.** The AI's only output is a JSON command batch.
- **Read files outside the workspace.** It sees your graph, your schema, your row previews - not your filesystem.
- **Make network calls** other than its own model API.
- **Bypass validation.** If the JSON doesn't match the typed schema, it's rejected.
- **Edit a node's internal state** directly. It has to go through the same command surface you do.
- **Undo your work** without your consent. It can suggest an undo but cannot do it silently.

This is by design. Every command is typed, validated, previewed, and applied through the same pipeline. The AI is a more efficient way to produce commands, not a backdoor.

---

## Auto-approve

If you trust the AI and want it to apply changes without showing the preview card every time, enable **auto-approve**.

1. **Settings** (Ctrl+,) → **AI** tab.
2. Check **Auto-approve and execute validated AI actions**.
3. **Save**.

When auto-approve is on:

- Validated command batches are applied immediately.
- The preview card is still shown (so you can see what happened), but it has an "Auto-approved" badge and the Apply button is disabled.
- The execution report card still appears.

Auto-approve is **off by default**. Only turn it on for trusted workflows.

> **Tip:** Even with auto-approve on, every command is still validated against the typed schema. Invalid JSON is still rejected. The AI is just trusted to propose correct things.

### A safer middle ground

If you want to skip previews for some actions but not others:

- Leave auto-approve **off**.
- Use **one-shot prompts** for the operations you trust (e.g., "always add a `deduplicate` after any sort").
- The AI can chain those in a single response, and you can apply the whole chain in one click.

---

## What the AI sees

Every time you send a message, Polaris sends the AI:

- The **system prompt** - explains the role (a data analyst for a visual pipeline tool), the available commands, and the strict JSON schema.
- The **full graph** - every node, its type, its parameters, and its position.
- The **current data preview** - the first 10 rows of the most recently executed node (or the attached node).
- The **schema** - column names and types of the active node.
- The **view state** - current mode (graph / spreadsheet / split), which panels are open.
- The **conversation history** - your previous messages and the AI's previous responses.

The AI does **not** see:

- Files on your disk.
- Other tabs' data (unless explicitly attached).
- Your API key.
- Your `.polaris` file content (just the live graph).

This context is what lets the AI propose correct, specific changes. If the AI is making wrong suggestions, it usually means the context is incomplete - try attaching the relevant node with the **+** button.

---

## Self-correction

Polaris uses a strict typed schema (Pydantic with `extra="forbid"`) for AI responses. If the AI returns JSON that doesn't match, Polaris:

1. Catches the validation error.
2. Sends a follow-up message to the AI: *"Your previous response didn't validate. Here's the error: {error}. Please try again with a corrected JSON."*
3. The AI retries, usually within 1–2 turns.

The user sees the full retry sequence in the conversation. The graph is not touched until a valid response is received and you click Apply.

This is why Polaris's AI is robust: the validation loop is automatic and the AI is steered back on track.

---

## Privacy and data

- **Your data does not leave your machine** except for the row previews sent to the AI provider. By default this is the first 10 rows of the active node.
- **The full graph and full data are never sent.** Polaris sends a snapshot of the graph (structure, parameters, IDs) and a preview of the rows, not the entire dataset.
- **No telemetry.** Polaris does not phone home. The only outbound traffic is to the AI provider you configure.
- **API key storage** is in the user config directory; it is encrypted at rest by the OS keychain on macOS, the Windows Credential Manager, and the Secret Service on Linux (when `keyring` is installed).

For the full breakdown of how the AI pipeline works under the hood, see **[AI pipeline architecture](../architecture/ai.md)**.

---

## Best practices

1. **Be specific.** "Filter where profit > 1000 and group by country" is better than "summarize the data".
2. **One thing at a time.** It's easier to verify a single-node change than a 10-node cascade. Chain follow-ups: "add a filter", then "add a group by", then "chart it".
3. **Attach the relevant node.** Use the **+** button to give the AI a specific node's context. "Why is this slow?" is way more useful when "this" is attached.
4. **Read the preview card.** It takes 2 seconds. It's your last line of defence.
5. **Check the JSON.** If the AI proposes something unexpected, expand the **Action JSON** and look. The action types are human-readable: `add_node`, `add_edge`, `update_param`, `delete_node`, `connect`, etc.
6. **Use Undo.** Every change is undoable. If the AI does something wrong, **Ctrl+Z** reverts.
7. **Iterate.** Don't expect the AI to nail a complex pipeline in one turn. Build it incrementally: "add X", "now modify X to do Y", "now connect X to Z".
8. **Don't auto-approve until you trust the AI.** Start with manual Apply. Once you see the AI reliably proposes correct things, consider auto-approve for that workflow.
9. **Type the word "this"** to refer to the attached node in your message: *"why is this removing 80% of rows?"* - the AI will know what "this" means.
10. **Ask the AI to explain.** The AI can describe a node, summarise the data, or walk you through the pipeline. Useful for learning.

---

## Example: building a pipeline with the AI

1. **Load data:** *"load the CSV at /tmp/orders.csv"*
   → AI proposes adding a CSV Reader. You apply.

2. **Filter:** *"filter to only completed orders"*
   → AI proposes a Filter with `pl.col('status') == 'completed'`. You apply.

3. **Aggregate:** *"group by customer_id and sum the total column, call it customer_total"*
   → AI proposes a Group By Aggregate. You apply.

4. **Sort:** *"sort by customer_total descending"*
   → AI proposes a Sort. You apply.

5. **Chart:** *"show a bar chart of top 20 customers by customer_total"*
   → AI proposes a Bar Chart with a Slice and a Bar Chart node. You apply.

6. **Export:** *"export the sorted aggregate to /tmp/top_customers.csv"*
   → AI proposes an Export CSV. You apply.

Done - a full pipeline, six turns, no clicks except Apply.

---

## Troubleshooting

### "No AI backend configured"

You haven't set an API key. See **[Setup: configure your API key](#setup-configure-your-api-key)** above.

### "API key invalid"

Your key is wrong, revoked, or has a typo. Re-paste it from Google AI Studio.

### AI is slow

Larger models (`Gemini 2.5 Pro`) take 5–10 seconds per response. `Gemini 2.0 Flash` is usually under 2 seconds. If you want speed, switch models in Settings.

### AI is making bad suggestions

The context is probably incomplete. Try:

- Attaching the relevant node with the **+** button.
- Being more specific in your prompt.
- Including the data context ("looking at the orders table") so the AI knows which table you mean.

### AI response didn't validate

This is normal. Polaris automatically retries. The conversation shows the retry. If the AI keeps failing (3+ retries), try a different model, simpler wording, or attach the node.

### AI is stuck "Thinking"

Sometimes the API hangs. The status bar will show "AI Thinking" with a spinner. Wait 30 seconds. If it doesn't resolve, close the panel and reopen it; in-progress requests are cancelled.

---

## See also

- **[AI pipeline architecture](../architecture/ai.md)** - how the AI emits validated commands under the hood.
- **[Node reference](../nodes/reference.md)** - every node the AI can use.
- **[Expression editor dialog](spreadsheet.md#expression-editor)** - for editing Polars expressions by hand (the AI can also open this for you).
