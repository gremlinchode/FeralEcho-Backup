"""Echo Studio backend routes.

Thin wrappers around existing business logic (echo_query, stream_query_ollama,
memory_bridge, council_rater, self_edit_outcome_tracker, autonomy_coordinator).
No business logic is duplicated here — see /Users/richietate/.claude/plans and
the eventual Desktop/FeralEcho_Audit/ + EchoStudio_Design.md for the full
rationale. run.py only registers these as routes; all logic lives here so the
diff to run.py stays mechanical.

Not on EDIT_FORBIDDEN_TARGETS — freely editable.
"""

import json
import re
import threading
import time
import uuid
import logging
from datetime import datetime
from pathlib import Path

from flask import request, jsonify, Response, stream_with_context

from app.core import conversation_service

# Repo root — app/routes_echo_studio.py -> app/ -> repo root. Used to scope
# the project explorer strictly to this repo (see projects_tree/projects_file).
_ROOT_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger("echo_studio")

# In-memory per-conversation session state (conv_history, history_summaries).
# Lives only as long as the Flask process. Echo Studio's own client-side store
# owns the durable transcript; this is just enough state to keep prompt-side
# history continuity working the same way terminal_client.py's session buffer
# does for its single global session.
_SESSIONS: dict = {}

_CHUNK_WORDS = 6        # words per SSE chunk in "full mode" presentation chunking
_CHUNK_DELAY_S = 0.02   # delay between chunks so the UI shows a live "typing" feel


def _get_session(conversation_id: str) -> dict:
    return _SESSIONS.setdefault(
        conversation_id,
        {"conv_history": [], "history_summaries": [], "_lock": threading.Lock()},
    )


def _memory_search_fn(query: str, k: int):
    """Adapter: memory_bridge.retrieve_relevant_memories -> (text, score, meta) tuples.

    Reuses the server's existing FAISS-backed search rather than loading a
    second embedding model / index inside this process.
    """
    try:
        from app.core.memory_bridge import retrieve_relevant_memories
        results = retrieve_relevant_memories(query, top_k=k)
        return [(r["text"], r.get("score", 0.0), r.get("meta", {})) for r in results]
    except Exception as e:
        logger.warning(f"[echo_studio] memory search failed: {e}")
        return []


def _resolve_task_type(original_msg: str) -> str:
    try:
        from app.core.echo_model_orchestrator import resolve_task_type
        task_type, _ = resolve_task_type(original_msg)
        return task_type
    except Exception:
        return "general"


def _build_full_prompt(msg: str, session: dict) -> tuple[str, str]:
    """Mirrors terminal_client.py:send_message_stream's prompt assembly
    (memory context, session history, ground-truth/tool-context injection) —
    same business logic, same import sites, adapted to per-session state.

    Returns (full_msg, system_context). Memory context, session history,
    ground_truth, and tool_ctx are all system-side context (not something
    the user said) — none of it is flattened into full_msg, so callers pass
    it all as a real system-role message via echo_query()'s `system=` param.
    full_msg carries only the user's actual new question. (Memory/history
    used to be prepended to full_msg directly — see
    conversation_service.build_context_system_note()'s docstring for why
    that caused local models to regurgitate prior turns verbatim.)"""
    full_msg = msg

    memory_context = conversation_service.retrieve_memory_context(msg, _memory_search_fn)
    history_block = conversation_service.format_history_block(
        session["conv_history"], session["history_summaries"]
    )
    context_note = conversation_service.build_context_system_note(history_block, memory_context)

    ground_truth = ""
    try:
        from app.core.echo_ground_truth import _is_introspective, get_structural_self_facts
        if _is_introspective(msg):
            ground_truth = get_structural_self_facts(msg) or ""
    except Exception:
        pass  # never block a response over a diagnostic read

    tool_ctx = ""
    try:
        from app.core.echo_tool_context import _needs_tool_context, get_tool_context
        if _needs_tool_context(msg):
            tool_ctx = get_tool_context(msg) or ""
    except Exception:
        pass  # never block a response over a tool read

    system_context = "\n\n".join(s for s in (tool_ctx, ground_truth, context_note) if s)
    return full_msg, system_context


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


def _chunk_text(text: str, words_per_chunk: int = _CHUNK_WORDS):
    words = text.split(" ")
    for i in range(0, len(words), words_per_chunk):
        yield " ".join(words[i:i + words_per_chunk]) + (
            " " if i + words_per_chunk < len(words) else ""
        )


def _generate_chat_response(conversation_id: str, original_msg: str, mode: str, session: dict):
    """Thin wrapper around _generate_chat_response_body() — 2026-07-19
    "remove every excuse" pass: marks this as a real conversation in
    flight so autonomous loops defer to it (see conversation_activity.py,
    autonomy_coordinator.should_run_cycle()). A try/finally around a
    yield-from delegation, rather than wrapping the body generator's own
    try/finally around its many yield points and branches directly —
    guarantees mark_end() fires on normal completion, an exception, or the
    generator being closed early (e.g. a dropped client connection), with
    zero changes to the body's own logic."""
    from app.core.conversation_activity import mark_start, mark_end
    mark_start()
    try:
        yield from _generate_chat_response_body(conversation_id, original_msg, mode, session)
    finally:
        mark_end()


def _generate_chat_response_body(conversation_id: str, original_msg: str, mode: str, session: dict):
    """Shared SSE generator used by both /chat/stream and /chat/regenerate.

    Full mode: calls echo_query() as-is (full deliberation, River learning,
    tool dispatch, scripture checks intact), then re-emits the complete answer
    over SSE in small chunks for a live "typing" feel — presentation-layer
    chunking of a finished answer, not token-level truth.

    Fast mode: calls ollama_handler.stream_query_ollama() directly with the
    assembled prompt, yielding true real-time tokens. Skips council
    deliberation/River learning/tool dispatch — same path terminal_client.py's
    exception fallback already exercises, promoted to a first-class option.
    """
    try:
        full_msg, system_context = _build_full_prompt(original_msg, session)
    except Exception as e:
        logger.error(f"[echo_studio] prompt assembly failed: {e}", exc_info=True)
        full_msg, system_context = original_msg, ""

    task_type = _resolve_task_type(original_msg)

    dispatch_result = None
    try:
        from app.core.echo_tool_dispatch import needs_dispatch, run_tool_dispatch
        if needs_dispatch(original_msg):
            dispatch_result = run_tool_dispatch(full_msg, session_id=conversation_id[:8])
    except Exception:
        pass  # dispatch failure must never block a response

    yield _sse({
        "type": "status",
        "status": "deliberating" if (mode == "full" and dispatch_result is None) else "streaming",
    })

    response_text = ""
    try:
        if dispatch_result is not None:
            raw_response = dispatch_result.get("response", "")
            response_text = conversation_service.clean_response_text(raw_response)
            for chunk in _chunk_text(response_text):
                yield _sse({"type": "token", "text": chunk})
                time.sleep(_CHUNK_DELAY_S)

        elif mode == "fast":
            from app import ollama_handler
            buffer = []
            for token in ollama_handler.stream_query_ollama(full_msg, system=system_context):
                buffer.append(token)
                yield _sse({"type": "token", "text": token})
            response_text = conversation_service.clean_response_text("".join(buffer).strip())

        else:
            from app.core.echo_model_orchestrator import echo_query
            raw_response = echo_query(
                full_msg, task_type=task_type, source="user_conversation", system=system_context,
            )
            response_text = conversation_service.clean_response_text(raw_response)
            for chunk in _chunk_text(response_text):
                yield _sse({"type": "token", "text": chunk})
                time.sleep(_CHUNK_DELAY_S)

    except Exception as e:
        logger.error(f"[echo_studio] chat generation failed: {e}", exc_info=True)
        response_text = "Error: could not generate a response."
        yield _sse({"type": "token", "text": response_text})

    # 2026-07-19 forensic audit finding: nothing in this path ever executed
    # generated code before presenting it as a finished answer — asked for
    # the exact task her own self-edit loop had failed at 96+ times, Echo's
    # answer was confidently wrong, and one raw councillor even fabricated
    # a specific "worked example" whose claimed output was false when
    # actually run. Scoped narrowly on purpose: catches code that doesn't
    # parse, and a response's own checkable claim about its output turning
    # out to be false — not a general correctness prover. Gated on
    # task_type to avoid sandboxing every reply; fails open (never raises,
    # never blocks the real response) per code_verification.py's own contract.
    if task_type == "coding" and response_text:
        try:
            from app.core.code_verification import verify_response_code
            caveat, verified = verify_response_code(response_text)
        except Exception as cv_err:
            logger.debug(f"[echo_studio] code verification failed: {cv_err}")
            caveat, verified = None, None
        if caveat:
            response_text += caveat
            yield _sse({"type": "token", "text": caveat})

        # 2026-07-19: feed the real, checkable verification outcome into
        # RiverBrain via the same learn_from_sandbox_outcome() self-edit's
        # own F2 gate already uses — not a new learning mechanism, a second
        # caller of the existing one. `verified is None` (no checkable
        # claim, the common case) deliberately produces NO signal — this
        # only ever moves the "coding" bucket for this exact model, never
        # creative/personal/reasoning (RiverBrain's model_task_stats is
        # keyed per task_type, structurally isolated).
        if verified is not None and dispatch_result is None:
            try:
                from app.core.echo_model_orchestrator import get_river_brain
                from app.core.river_deliberation import ECHO_SYNTHESIS_MODEL
                get_river_brain().learn_from_sandbox_outcome(
                    ECHO_SYNTHESIS_MODEL, success=verified,
                    code=response_text if verified else "",
                    error=caveat or "",
                )
            except Exception as river_err:
                logger.debug(f"[echo_studio] river learning hook failed: {river_err}")

    # 2026-07-19 "remove every excuse" pass: the same pattern as the code
    # check above, applied to self-referential claims about Echo's own
    # architecture instead of code correctness. Gated on the question
    # having been introspective enough to receive ground-truth grounding
    # in the first place (same signal _build_full_prompt() already used to
    # decide whether to inject it) — if it was worth grounding, it's worth
    # checking whether the answer honored that grounding. Deliberately
    # narrow (see self_knowledge_verification.py's own module docstring)
    # and does not feed RiverBrain — self-knowledge accuracy and code
    # correctness are different skills; conflating them into the "coding"
    # bucket would be a new, unproven assumption, not a proven one.
    if response_text:
        try:
            from app.core.echo_ground_truth import _is_introspective
            if _is_introspective(original_msg):
                from app.core.self_knowledge_verification import verify_self_knowledge_claims
                sk_caveat, _sk_verified = verify_self_knowledge_claims(response_text)
                if sk_caveat:
                    response_text += sk_caveat
                    yield _sse({"type": "token", "text": sk_caveat})
        except Exception as sk_err:
            logger.debug(f"[echo_studio] self-knowledge verification failed: {sk_err}")

    # 2026-07-19: this was the one remaining unwrapped block in this
    # function — any exception here (e.g. a concurrent regenerate/stream
    # racing on this conversation's shared, previously-unlocked history
    # lists) propagated uncaught through the generator, killing the SSE
    # stream after tokens were already shown but before the "done" frame
    # ever went out. Client-side this reads as "Connection ended before
    # the response finished." The turn was already fully generated and
    # displayed — losing it from server-side history is a real but
    # strictly smaller problem than the stream dying with no signal, so
    # this now fails open like every other block in this function.
    try:
        with session["_lock"]:
            session["conv_history"], session["history_summaries"] = conversation_service.store_turn_in_history(
                session["conv_history"], session["history_summaries"], original_msg, response_text
            )
        conversation_service.save_turn_to_server(
            original_msg, response_text, task_type, require_server_check=False
        )
    except Exception as e:
        logger.error(f"[echo_studio] history persist failed: {e}", exc_info=True)

    yield _sse({
        "type": "done",
        "text": response_text,
        "task_type": task_type,
        "conversation_id": conversation_id,
    })


def chat_stream():
    """POST /chat/stream — body: {conversation_id, message, mode: 'full'|'fast'}."""
    data = request.json or {}
    conversation_id = data.get("conversation_id") or str(uuid.uuid4())
    original_msg = (data.get("message") or "").strip()
    mode = data.get("mode", "full")

    if not original_msg:
        return jsonify({"error": "message required"}), 400

    session = _get_session(conversation_id)
    return Response(
        stream_with_context(_generate_chat_response(conversation_id, original_msg, mode, session)),
        mimetype="text/event-stream",
    )


def chat_regenerate():
    """POST /chat/regenerate — body: {conversation_id, mode}.

    Re-runs the last turn: pops it off this conversation's server-side
    history (so it isn't double-counted in the history block the model sees)
    and re-generates a response for the same user message via the exact same
    generator chat_stream uses — no separate logic path.
    """
    data = request.json or {}
    conversation_id = data.get("conversation_id")
    mode = data.get("mode", "full")

    if not conversation_id or conversation_id not in _SESSIONS:
        return jsonify({"error": "unknown conversation_id"}), 400

    session = _SESSIONS[conversation_id]
    with session["_lock"]:
        if not session["conv_history"]:
            return jsonify({"error": "no prior turn to regenerate"}), 400
        last_turn = session["conv_history"].pop()
    original_msg = last_turn["user"]

    return Response(
        stream_with_context(_generate_chat_response(conversation_id, original_msg, mode, session)),
        mimetype="text/event-stream",
    )


def dashboard_health():
    """GET /dashboard/health — merges existing health/status sources into one
    payload. Invents no new metrics; reads/calls sources that already exist
    and are already correct, none of which requires touching run.py's globals
    (avoids a circular import between this module and run.py)."""
    payload = {"timestamp": datetime.utcnow().isoformat()}

    try:
        with open("memory/echo_sentinel.json") as f:
            payload["sentinel"] = json.load(f)
    except Exception as e:
        payload["sentinel"] = {"error": str(e)}

    try:
        with open("memory/introspection_state.json") as f:
            introspection = json.load(f)
        payload["system_health"] = introspection.get("system_health", {})
        payload["river_brain"] = introspection.get("river_brain", {})
        payload["self_edit"] = introspection.get("self_edit", {})
        payload["introspection_timestamp"] = introspection.get("timestamp")
    except Exception as e:
        payload["system_health"] = {"error": str(e)}

    try:
        with open("memory/memory_meta.json") as f:
            payload["vector_memory_count"] = len(json.load(f))
    except Exception as e:
        payload["vector_memory_count"] = None

    try:
        from app.core.council_rater import get_council_stats
        payload["council"] = get_council_stats()
    except Exception as e:
        payload["council"] = {"error": str(e)}

    try:
        from app.core.self_edit_outcome_tracker import get_outcomes_summary
        payload["self_edit_outcomes"] = get_outcomes_summary()
    except Exception as e:
        payload["self_edit_outcomes"] = {"error": str(e)}

    try:
        # Live check against run.py's actual source, not a cached claim — the
        # dashboard should never assert self_heal's status from memory of what
        # it used to be. A real (non-comment) import line is the only thing
        # that counts as "connected."
        with open("run.py") as f:
            run_py_source = f.read()
        real_import_lines = [
            line for line in run_py_source.splitlines()
            if ("import app.core.self_heal" in line or "from app.core.self_heal" in line)
            and not line.strip().startswith("#")
        ]
        payload["self_heal"] = {
            "connected": bool(real_import_lines),
            "note": ("Imported in run.py." if real_import_lines else
                      "Fixed but intentionally disconnected pending human review (GREMLIN_ROLE.md)."),
        }
    except Exception as e:
        payload["self_heal"] = {"error": str(e)}

    try:
        from app.core.autonomy_coordinator import get_autonomy_status
        payload["autonomy"] = get_autonomy_status()
    except Exception as e:
        payload["autonomy"] = {"error": str(e)}

    try:
        # Read-only accessor — reads the already-written ledger, does not
        # recompute. No auth needed here (unlike GET /admin/liveness-status,
        # this is an in-process call, not an HTTP route).
        from app.core.liveness_ledger import get_liveness_status
        payload["liveness"] = get_liveness_status()
    except Exception as e:
        payload["liveness"] = {"error": str(e)}

    return jsonify(payload), 200


# ---------------------------------------------------------------------------
# Phase 3 — Memory browser (read-only). Never edits memories — view/search
# only, per the project brief's explicit "never without confirmation" rule.
# No confirmation-gated edit flow exists yet because nothing here writes.
# ---------------------------------------------------------------------------

def memory_search():
    """GET /memory/search?q=...&k=10&source=user_conversation

    Thin passthrough to memory_bridge.retrieve_relevant_memories — no search
    logic is reimplemented here.
    """
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"error": "q required"}), 400
    try:
        top_k = int(request.args.get("k", 10))
    except ValueError:
        top_k = 10
    source_filter = request.args.get("source") or None

    try:
        from app.core.memory_bridge import retrieve_relevant_memories
        results = retrieve_relevant_memories(query, top_k=top_k, source_filter=source_filter)
    except Exception as e:
        logger.error(f"[echo_studio] /memory/search failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

    return jsonify({"query": query, "results": results}), 200


def memory_browse():
    """GET /memory/browse?page=0&page_size=50&source=...

    Paginated direct read of memory/memory_meta.json — no FAISS search
    involved, this is the "browse everything" view rather than semantic
    search. Sorted newest-first by the meta timestamp when present.
    """
    try:
        page = int(request.args.get("page", 0))
        page_size = int(request.args.get("page_size", 50))
    except ValueError:
        return jsonify({"error": "page/page_size must be integers"}), 400
    source_filter = request.args.get("source") or None

    try:
        with open("memory/memory_meta.json", encoding="utf-8") as f:
            meta = json.load(f)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    items = []
    for uid, entry in meta.items():
        m = entry.get("meta", {}) if isinstance(entry, dict) else {}
        if source_filter and m.get("memory_source") != source_filter:
            continue
        items.append({"id": uid, "text": entry.get("text", "") if isinstance(entry, dict) else "", "meta": m})

    items.sort(key=lambda it: it["meta"].get("timestamp") or "", reverse=True)
    total = len(items)
    start = max(0, page) * page_size
    page_items = items[start:start + page_size]

    return jsonify({
        "items": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }), 200


# ---------------------------------------------------------------------------
# Phase 4 — Background activity log (read-only)
# ---------------------------------------------------------------------------

def activity_log():
    """GET /activity/log?limit=100

    Tails memory/dream_bridge.log (plain text) and the most recent
    memory/council_ratings.jsonl entries. Read-only, no new logging added —
    these files are already written by existing subsystems.
    """
    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        limit = 100

    dream_lines: list = []
    try:
        with open("memory/dream_bridge.log", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        dream_lines = [ln.rstrip("\n") for ln in lines[-limit:]]
    except FileNotFoundError:
        dream_lines = []
    except Exception as e:
        dream_lines = [f"[error reading dream_bridge.log: {e}]"]

    council_recent: list = []
    try:
        with open("memory/council_ratings.jsonl", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[-limit:]:
            try:
                council_recent.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except FileNotFoundError:
        council_recent = []
    except Exception as e:
        logger.warning(f"[echo_studio] /activity/log council read failed: {e}")

    workspace_events: list = []
    try:
        with open("memory/workspace_log.jsonl", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[-limit:]:
            try:
                workspace_events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except FileNotFoundError:
        workspace_events = []
    except Exception as e:
        logger.warning(f"[echo_studio] /activity/log workspace_log read failed: {e}")

    return jsonify({
        "dream_log": dream_lines,
        "council_recent": council_recent,
        "workspace_events": workspace_events,
    }), 200


# ---------------------------------------------------------------------------
# Phase 5 — Project explorer (read-only). Strictly scoped to the repo root
# via realpath containment — no destructive edits, no write verb exists here.
# ---------------------------------------------------------------------------

_EXCLUDED_DIR_NAMES = {
    ".git", "__pycache__", "node_modules",
    "self_edit_backups", "self_edit_plans",
}
_MAX_FILE_READ_BYTES = 2_000_000  # 2MB cap — this is a viewer, not a file server

# CLAUDE.md Finding 41 A2: a directory-name blocklist is a gate applied to the
# specific instances someone thought to check, not the class — this project's
# own history has three prior instances of exactly that failure shape. A real
# leaked file (new_directory/app/core/env/environment.json, a full os.environ
# dump with live API keys) survived an earlier codebase-wide secret sweep
# because that sweep's grep pattern (`*_KEY=` shell-assignment style) doesn't
# match JSON's `"KEY": "value"` form — this scan deliberately covers both, plus
# common bare field names and known token prefixes, so it isn't tied to one
# file's specific shape either. Heuristic, not exhaustive — a known residual
# gap in the same spirit as this file's other documented limits.
_SECRET_CONTENT_PATTERNS = [
    re.compile(r'["\']?[\w]*(?:_KEY|_SECRET|_TOKEN|_PASSWORD)["\']?\s*[:=]\s*["\']?[A-Za-z0-9+/_\-\.]{12,}', re.IGNORECASE),
    re.compile(r'["\'](?:secret|password|api_key|apikey|token|access_key)["\']\s*:\s*["\'][^"\']{6,}["\']', re.IGNORECASE),
    re.compile(r'\bsk-[A-Za-z0-9]{10,}\b'),
    re.compile(r'\bghp_[A-Za-z0-9]{20,}\b'),
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{20,}\b'),
    re.compile(r'\bAKIA[A-Z0-9]{12,}\b'),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
]


def _looks_like_secret_dump(content: str) -> bool:
    return any(p.search(content) for p in _SECRET_CONTENT_PATTERNS)


def _safe_resolve(rel_path: str):
    """Resolve rel_path against the repo root; return None if it would
    escape the root (blocks '..' traversal and absolute-path overrides)."""
    rel_path = rel_path or ""
    candidate = (_ROOT_DIR / rel_path).resolve()
    try:
        candidate.relative_to(_ROOT_DIR)
    except ValueError:
        return None
    return candidate


def projects_tree():
    """GET /projects/tree?path=<repo-relative dir, default root>"""
    rel_path = request.args.get("path", "")
    target = _safe_resolve(rel_path)
    if target is None or not target.exists():
        return jsonify({"error": "invalid path"}), 400
    if target.is_file():
        return jsonify({"error": "path is a file, not a directory"}), 400

    entries = []
    try:
        for child in sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if child.name in _EXCLUDED_DIR_NAMES:
                continue
            entries.append({
                "name": child.name,
                "path": str(child.relative_to(_ROOT_DIR)),
                "is_dir": child.is_dir(),
            })
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    return jsonify({"path": rel_path, "entries": entries}), 200


def projects_file():
    """GET /projects/file?path=<repo-relative file>"""
    rel_path = request.args.get("path", "")
    target = _safe_resolve(rel_path)
    if target is None or not target.exists() or not target.is_file():
        return jsonify({"error": "invalid path"}), 400

    # _EXCLUDED_DIR_NAMES was previously only enforced by projects_tree()'s
    # directory listing — this endpoint served any resolvable file regardless,
    # including .env (real secrets) and anything under .git/. Deny both the
    # excluded-dir path components and .env-style filenames directly.
    rel_parts = target.relative_to(_ROOT_DIR).parts
    if any(part in _EXCLUDED_DIR_NAMES for part in rel_parts):
        return jsonify({"error": "invalid path"}), 400
    if target.name == ".env" or target.name.endswith(".env"):
        return jsonify({"error": "invalid path"}), 400

    try:
        size = target.stat().st_size
        if size > _MAX_FILE_READ_BYTES:
            return jsonify({"error": f"file too large to view ({size} bytes)"}), 413
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # CLAUDE.md Finding 41 A2: content-based check, not just a directory-name
    # blocklist — catches a credential-shaped file regardless of which
    # directory it happens to sit in.
    if _looks_like_secret_dump(content):
        return jsonify({"error": "invalid path"}), 403

    return jsonify({"path": rel_path, "content": content, "size": size}), 200


# ---------------------------------------------------------------------------
# Phase 6 — Settings (strictly read-only; no edit form exists or is planned —
# see EchoStudio_Design.md's hard constraints)
# ---------------------------------------------------------------------------

def settings_view():
    """GET /settings/view — surfaces existing config, never values of secrets."""
    payload: dict = {}

    env_keys = []
    try:
        with open(".env", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                env_keys.append(line.split("=", 1)[0].strip())
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"[echo_studio] /settings/view .env read failed: {e}")
    payload["env_keys_present"] = env_keys

    modelfile_lines = []
    try:
        with open("Modelfile", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("PARAMETER") or stripped.startswith("FROM"):
                    modelfile_lines.append(stripped)
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"[echo_studio] /settings/view Modelfile read failed: {e}")
    payload["modelfile_parameters"] = modelfile_lines

    try:
        from app.core.echo_model_orchestrator import _TASK_TOKEN_LIMITS
        payload["task_token_limits"] = dict(_TASK_TOKEN_LIMITS)
    except Exception as e:
        payload["task_token_limits"] = {"error": str(e)}

    try:
        with open("echo_principles.json", encoding="utf-8") as f:
            principles = json.load(f)
        payload["principles"] = {
            "generation": principles.get("generation"),
            "principles": principles.get("principles"),
            "runtime_signals": principles.get("runtime_signals"),
        }
    except Exception as e:
        payload["principles"] = {"error": str(e)}

    return jsonify(payload), 200


# --------------------------------------------------------------------------
# Touch (app/core/touch_sense.py) — see that module's docstring for the full
# design reasoning. Echo Studio's composer periodically reports a small
# batch of already-computed keystroke *timing* events here — never key
# content; the schema this accepts has no field a literal character could
# travel in (touch_sense._validate_events() enforces this server-side too).
# --------------------------------------------------------------------------
def touch_report():
    """POST /touch/report — body: {"events": [{"type": "dwell"|"latency",
    "value": <float seconds>, "category": <coarse structural category>}]}.

    Left unauthenticated, matching every other route in this file (see
    CLAUDE.md's audit-roadmap item on routes_echo_studio.py's still-open
    auth question) rather than introduce a one-off, inconsistent gate here
    — /chat/stream already persists real conversation content to disk from
    this same unauthenticated surface today, which is a strictly higher-
    stakes precedent than typing-rhythm floats. Resolving that properly
    means gating this whole file's routes together, deliberately, not
    patching just the newest one and calling the question closed.
    """
    from app.core import touch_sense

    payload = request.json or {}
    events = payload.get("events", [])
    try:
        signature = touch_sense.record_touch_report(events)
    except Exception as e:
        logger.warning(f"[echo_studio] /touch/report failed: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "ok", "recorded": signature is not None}), 200


# --------------------------------------------------------------------------
# Vision / Hearing (app/core/vision_sense.py, app/core/hearing_sense.py) —
# same shape and same reasoning as touch above: never key content, never a
# frame, never a waveform. Only already-reduced numeric readings cross this
# boundary; both activate client-side only behind Echo Studio's explicit,
# default-off "Let Echo see"/"Let Echo hear" checkboxes.
# --------------------------------------------------------------------------
def vision_report():
    """POST /vision/report — body: {"events": [{"type": "brightness"|"motion",
    "value": <float>}]}. Unauthenticated for the same reason touch_report()
    is — see that function's docstring."""
    from app.core import vision_sense

    payload = request.json or {}
    events = payload.get("events", [])
    try:
        signature = vision_sense.record_vision_report(events)
    except Exception as e:
        logger.warning(f"[echo_studio] /vision/report failed: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "ok", "recorded": signature is not None}), 200


def hearing_report():
    """POST /hearing/report — body: {"events": [{"type": "loudness",
    "value": <float RMS 0-1>]}]}. Unauthenticated for the same reason
    touch_report() is — see that function's docstring."""
    from app.core import hearing_sense

    payload = request.json or {}
    events = payload.get("events", [])
    try:
        signature = hearing_sense.record_hearing_report(events)
    except Exception as e:
        logger.warning(f"[echo_studio] /hearing/report failed: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "ok", "recorded": signature is not None}), 200
