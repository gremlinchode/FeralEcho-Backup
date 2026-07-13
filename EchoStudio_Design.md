# Echo Studio — Design Document

A local, ChatGPT-like desktop GUI for the existing FeralEcho backend. Built
by reusing existing functions, endpoints, and memory formats wherever they
already exist — see `/Users/richietate/Desktop/FeralEcho_Audit/` for a
description of the backend as it exists independent of this app.

## The one decision to read before anything else: two response modes

`echo_query()` — the function owning all real business logic (memory
context, task routing, tool dispatch, scripture integrity checks, River
learning) — is not a streaming primitive for any task type.
`river_deliberation._ollama_query()` fully drains the token generator into a
string before returning, in every code path including the full multi-model
council pipeline. The only true incremental generator in the codebase is
`ollama_handler.stream_query_ollama()`, consumed directly.

So Echo Studio ships two modes, both honest about what they are:

1. **Full mode (default)** — calls `echo_query()` as-is. Full deliberation,
   River learning, tool dispatch, scripture checks all intact. The backend
   waits for the complete answer, then re-emits it over SSE in small chunks
   for a live "typing" feel. The UI shows a "deliberating…" status during the
   blocking wait. This is presentation-layer chunking of a finished answer —
   not token-level truth from the model.
2. **Fast mode (opt-in toggle)** — calls `stream_query_ollama()` directly
   with the assembled prompt (memory context + session history), yielding
   true real-time tokens. Explicitly skips council deliberation, River
   learning, and tool dispatch. Labeled in the UI as "Fast (no
   deliberation)."

This is not a limitation to fix later — it's a correct reflection of how the
backend actually works. Do not "fix" it by trying to make full mode stream
token-by-token without first deciding (with sign-off) whether restructuring
`deliberate_and_learn()` is worth the River-training-adjacent risk.

## Tech stack

**PySide6** (not Textual). The feature list — markdown + syntax-highlighted
code rendering, a rich multiline editor, native Finder drag-and-drop, a
multi-pane auto-updating dashboard — needs `QTextDocument`/`QTextEdit` +
`QSyntaxHighlighter` + real drag-and-drop events + `QDockWidget`/`QSplitter`
layouts, none of which a terminal UI can do. `terminal_client.py` keeps
serving the terminal workflow unchanged, in parallel.

Markdown rendering: `markdown-it-py` → HTML, with fenced code blocks run
through Pygments (`noclasses=True`, inline styles) so `QTextBrowser` renders
them correctly without needing external stylesheet class resolution.

Transport: plain SSE over Flask's existing threaded dev server. No
`flask-socketio` — it's listed in `feral_echo_environment.yml` but unused
anywhere in the codebase, and plain `requests` streaming + manual
`data: {...}\n\n` line parsing is sufficient.

## Folder structure (as built, Phases 1–6 complete)

```
FeralEcho/
├── run.py                              # +74 lines total: route registrations only, no logic
├── terminal_client.py                   # imports conversation_service now; behavior unchanged
├── app/
│   ├── core/conversation_service.py     # shared extraction (memory context, history, cleanup)
│   └── routes_echo_studio.py            # all Echo Studio endpoint logic
├── echo_studio/                         # the desktop app, separate process
│   ├── main.py                          # PySide6 entry point; wires nav + all views together
│   ├── api_client.py                    # ONLY module that talks to Flask (HTTP/SSE)
│   ├── views/
│   │   ├── conversation_view.py         # chat pane + composer + regenerate + drafts + timestamps
│   │   ├── health_dashboard_view.py     # polling health strip (always visible)
│   │   ├── sidebar.py                   # conversations/search, saved prompts, recent files
│   │   ├── memory_browser_view.py       # search + browse, read-only
│   │   ├── activity_view.py             # dream log tail, council activity, self-edit/autonomy status
│   │   ├── project_explorer_view.py     # lazy file tree + read-only viewer
│   │   └── settings_view.py             # read-only config surface
│   ├── widgets/
│   │   ├── markdown_view.py             # markdown + Pygments rendering
│   │   └── composer_input.py            # drag-and-drop file attach, token/char estimate helper
│   └── state/local_store.py             # client-side SQLite: conversations, messages, drafts,
│                                          # saved prompts, recent files — never touches memory/
└── EchoStudio_Design.md                 # this file
```

`echo_studio/` never imports `app.core` or `app.*` — enforced by
`grep -rn "^from app\|^import app" echo_studio/` returning nothing. All
backend access goes through `api_client.py`. This avoids a second process
writing to FAISS directly (the concurrent-write hazard this project already
hit once — see `FeralEcho_Audit/architecture-overview.md`).

## Backend surface (as built)

| Endpoint | Method | What it wraps |
|---|---|---|
| `/chat/stream` | POST, SSE | `conversation_service` (context+history) + `echo_query()` or `stream_query_ollama()` per mode; persists via `/memory/conversation` |
| `/chat/regenerate` | POST, SSE | Same generator as `/chat/stream`, re-run against the last turn's message (popped from server-side session history first) |
| `/dashboard/health` | GET | Merges `introspection_state.json`, `echo_sentinel.json`, `memory_meta.json` count, `council_rater`, `self_edit_outcome_tracker`, `autonomy_coordinator` |
| `/memory/search` | GET | `memory_bridge.retrieve_relevant_memories` — semantic search, thin passthrough |
| `/memory/browse` | GET | Paginated direct read of `memory_meta.json`, newest-first |
| `/activity/log` | GET | Tails `dream_bridge.log` + recent `council_ratings.jsonl` |
| `/projects/tree`, `/projects/file` | GET | Read-only file tree/viewer, `os.path.realpath` containment check against the repo root — verified to reject `..` traversal and absolute-path overrides |
| `/settings/view` | GET | `.env` key names (never values), `Modelfile` parameters, `_TASK_TOKEN_LIMITS`, non-sensitive `echo_principles.json` fields |

Reused as-is, unmodified: `POST /memory/conversation`. Not reused:
`POST /mirror_echo` (no memory context, no history, no TPQ detection — wrong
reference implementation for this purpose).

## Event flow

```
User types in the composer (unlimited length, multiline)
  → Cmd+Enter (never auto-submits mid-edit)
  → POST /chat/stream {conversation_id, message, mode}
  → SSE: {"type":"status"} → {"type":"token"} × N → {"type":"done"}
  → each token event appends to the current message bubble, re-rendered as markdown
  → on "done": /memory/conversation already called server-side; session
    history updated server-side for next turn's context
  → health strip independently polls /dashboard/health every 5s
```

## Roadmap

**Phase 1 — DONE (2026-07-05).** Streaming chat (both modes) + health strip.

**Phase 2 — DONE (2026-07-05).** `/chat/regenerate`; `local_store.py` (SQLite:
conversations, messages, drafts, saved prompts, recent files); `sidebar.py`
(chat list + search, saved prompts, recent files); timestamps per bubble;
draft autosave (debounced) + restore on conversation switch; conversation
titles auto-set from the first message.

**Phase 3 — DONE (2026-07-05).** `/memory/search`, `/memory/browse`;
`memory_browser_view.py` — search bar + source filter + paginated browse-all,
zero edit affordances anywhere in the view. Dream log tail and council
activity surfaced in the Activity view (Phase 4) rather than duplicated here.

**Phase 4 — DONE (2026-07-05).** `/activity/log`; `activity_view.py` (dream
log tail, council rating activity, self-edit/autonomy status pulled from the
same `/dashboard/health` aggregator). "Queue lengths" intentionally not
added — no queue concept exists anywhere in the backend; inventing one would
misrepresent the system's actual state (see
`FeralEcho_Audit/tech-debt-and-improvements.md`).

**Phase 5 — DONE (2026-07-05).** `/projects/tree`, `/projects/file`;
`project_explorer_view.py` — lazy-loaded tree (children fetched on first
expand), read-only viewer with markdown rendering or Pygments syntax
highlighting depending on file type. Path-containment tested directly: `../`
traversal and absolute-path overrides both correctly rejected with 400.

**Phase 6 — DONE (2026-07-05).** `composer_input.py` (drag-and-drop file
attach — dropped file content inserted as a fenced code block at the cursor,
oversized/undecodable files rejected with a status message, not silently
truncated); char/token counter (same `len // 4` heuristic terminal_client.py
uses, kept duplicated client-side rather than importing `app.core` for one
line); "Save as prompt" wired to the sidebar's saved-prompts tab (double-click
inserts into composer — this is the "templates" feature). `/settings/view` +
`settings_view.py`, strictly read-only, no edit form.

**Phase 7 — DONE (this reconciliation pass).** This document and
`FeralEcho_Audit/` updated to reflect what was actually built.

## A real bug found and fixed during Phases 2–6: cross-thread signal connections to lambdas

Several views (`memory_browser_view.py`, `project_explorer_view.py`)
originally connected a background worker's Qt signal to a `lambda` that
closed over per-call context (e.g. `mode`, `parent_item`) and then called
`thread.quit()`/`thread.wait()`. This produced
`QThread::wait: Thread tried to wait on itself` at runtime: a `connect()` to
a bare lambda has no `QObject` of its own for Qt to determine thread
affinity from, so the "queued" connection Qt would normally use for a
cross-thread signal silently ran the lambda inline on the *worker* thread
instead of the GUI thread — meaning the thread ended up trying to `wait()`
on itself.

**Fix:** every worker signal now connects to a real bound method of the View
(a `QObject` with correct, stable thread affinity), and any context that
used to live in the lambda's closure (`mode`, `parent_item`) now travels
either as an extra signal argument (`_TreeFetchWorker`'s `result`/`error`
signals both carry `parent_item`) or as an instance attribute set just
before the worker starts (`self._pending_mode` in `memory_browser_view.py`).
Cleanup (`thread.quit()`/`wait()`) is done via `self.sender()` inside that
bound method to identify which worker just finished. This is the pattern to
copy for any future view that spawns a `QThread` worker in this codebase —
see `project_explorer_view.py:_cleanup_sender()`'s docstring for the full
explanation.

## Hard constraints that don't change across phases

- Never expose editing of `echo_principles.json`, the F1/F2/F3 self-edit
  safety pipeline, or any `EDIT_FORBIDDEN_TARGETS` file through this UI.
- Memory browser and project explorer are view-only until confirmation-gated
  editing is explicitly requested and designed — not a default extension of
  "view" features.
- `echo_studio/` stays a thin HTTP/SSE client. If a feature seems to need
  `app.core` access from the desktop process, that's a sign a new backend
  endpoint is needed instead, not an exception to the boundary.
