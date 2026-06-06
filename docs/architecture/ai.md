# AI Architecture

## Gemini Backend (single backend)

Polaris Studio uses Google Gemini as its sole AI backend.

### GeminiBackend
- Uses the Gemini API directly via the official SDK
- Streaming responses via async model streaming
- Emits plain text plus structured JSON command batches
- Requires API key in Settings

### AIBackendRouter
- Wraps GeminiBackend; returns None if no API key is configured
- Falls back gracefully with an informative message

## Chat Session

The `ChatSession` class manages multi-turn conversations.

**Context injection:**
- Full graph state serialized into system prompt
- Current sheet summary, row preview, and selected nodes
- View mode and panel state

**Flow:**
1. User sends message
2. System prompt + history + app context sent to AI
3. AI streams tokens back
4. If AI proposes commands, they appear as a preview card
5. User can Apply or Skip
6. On Apply: commands are executed through the app state and spreadsheet model
7. Graph and grid update through normal Qt signals

## App Commands

Polaris Studio accepts typed command batches instead of raw Python snippets.

Supported command categories:
- Graph mutations
- Cell edits and cell styles
- Row insertion and deletion
- Column rename/cast/fill operations
- View and panel toggles
- Graph execution and auto-layout

## AgentInterpreter

Validates and applies PipelineMutationBatch to the live graph:
- Creates nodes, updates params, connects/disconnects edges
- Validates node types against NODE_REGISTRY
- Catches cycles and returns errors without corrupting graph
