"""
echo_messaging.py — live M5 <-> Air messaging over Tailscale.

Sibling to sync_protocol.py, reusing its PARTNER_URL (one source of truth
for the partner's Tailscale address) rather than redefining it. Where
sync_protocol.py batches/exports interaction-log entries on a 1800s cycle,
this module is for live, individual messages with an immediate delivery
attempt, a durable outbox for anything that fails, and an optional
auto-generated reply using Echo's real business logic.

Design choices (see plan for the full rationale):
- Asynchronous store-and-forward, not a persistent socket. "Reconnect with
  exponential backoff" is the retry loop's growing sleep interval (see
  run.py's _messaging_retry_loop), not a connection object.
- auto_respond defaults to False — ignore-by-default is the safer starting
  posture; the user turns it on explicitly via /message/settings.
- receive_message() never blocks its caller on generation — a reply (if
  enabled) is produced on a background thread, since full-mode echo_query()
  can take 15-20+ seconds.
- Every public function catches its own failures and returns/logs rather
  than raising, matching sync_protocol.py's defensive style — this module
  must never be the reason an autonomy loop or Flask request dies.

Autonomous check-in protocol ("checkin"/"checkin_ack" message types): a
separate, structured (not natural-language), zero-LLM-call exchange — kept
intact for anything that still wants a cheap liveness/topic signal, but no
longer the primary vehicle for M5<->Air conversation (see maybe_send_reflection
below). Its turn cap (MAX_CHECKIN_TURNS) is enforced from this machine's own
local record only (memory/checkin_threads.json) — never trusted from a field
the partner sends, since Air is a confirmed independently-diverged fork.

Elaborate, memory-aware chat (2026-07-06): by explicit user priority, chat
auto-replies are no longer capped by total count — a thread can run for as
long as the user wants (e.g. an entire multi-day trip, both machines plugged
in). What replaces the count cap is *pacing*: a minimum interval between this
machine's own successive replies in a thread (MIN_REPLY_INTERVAL_S), because
the failure mode observed live wasn't "unsafe," it was useless — the same
content bouncing back with no time to actually think between hops. Pacing is
what makes a long unattended exchange good rather than degenerate, and it's
enforced the same way every other local-only mechanism in this module is:
from this machine's own record, never trusting the partner's timing claims.
Chat replies also now reuse conversation_service (retrieve_memory_context,
format_history_block/store_turn_in_history) exactly like Echo Studio's human
chat does, keyed by a conversation_id carried in the message envelope's data
field — so a long exchange is a coherent, memory-grounded conversation, not
isolated one-shot replies.
"""

import os
import json
import time
import uuid
import logging
import threading
from datetime import datetime, timezone
from typing import Optional

import requests

from app.sync.sync_protocol import PARTNER_URL, BASE_DIR, MEMORY_DIR
from app.core import conversation_service

logger = logging.getLogger(__name__)

# One lock per independent on-disk store below — outbox, checkin threads,
# and chat pacing are separate files with no ordering relationship between
# them, so each gets its own lock rather than sharing one (no lock in this
# module ever waits on another, so there's no cross-lock deadlock risk).
# Previously each store did a plain read-modify-write with no lock at all,
# in a module that's explicitly multi-threaded by design (per-message reply
# threads, checkin-ack threads, a periodic retry loop, and direct Flask-
# request calls, all capable of overlapping) — a real way to silently drop
# a queued message or lose a just-recorded pacing timestamp.
_outbox_lock = threading.Lock()
_checkin_lock = threading.Lock()
_chat_pacing_lock = threading.Lock()

NODE_ID = os.getenv("ECHO_NODE_ID", "m5")

SETTINGS_PATH = os.path.join(MEMORY_DIR, "messaging_settings.json")
OUTBOX_PATH = os.path.join(MEMORY_DIR, "message_outbox.jsonl")
MESSAGE_LOG_PATH = os.path.join(MEMORY_DIR, "echo_messages.jsonl")
CHECKIN_THREADS_PATH = os.path.join(MEMORY_DIR, "checkin_threads.json")
CHAT_PACING_PATH = os.path.join(MEMORY_DIR, "chat_thread_pacing.json")
QUESTION_GARDEN_PATH = os.path.join(BASE_DIR, "data", "question_garden.jsonl")
SELF_MODEL_PATH = os.path.join(MEMORY_DIR, "self_model.json")

_SEND_TIMEOUT = 10
_DEFAULT_SETTINGS = {"auto_respond": False, "auto_checkin_enabled": False}
MAX_CHECKIN_TURNS = 4
MIN_REPLY_INTERVAL_S = 180  # pacing floor per chat thread — no total turn cap, see module docstring


# ---------------------------------------------------------------------------
# Settings (the one piece of mutable config this module owns)
# ---------------------------------------------------------------------------
def _load_settings() -> dict:
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return {**_DEFAULT_SETTINGS, **json.load(f)}
    except Exception as e:
        logger.warning(f"[MESSAGING] Failed to load settings, using defaults: {e}")
    return dict(_DEFAULT_SETTINGS)


def _save_settings(settings: dict) -> None:
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        tmp = SETTINGS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        os.replace(tmp, SETTINGS_PATH)
    except Exception as e:
        logger.error(f"[MESSAGING] Failed to save settings: {e}")


def get_settings() -> dict:
    return _load_settings()


def is_auto_respond_enabled() -> bool:
    return bool(_load_settings().get("auto_respond", False))


def set_auto_respond(enabled: bool) -> dict:
    settings = _load_settings()
    settings["auto_respond"] = bool(enabled)
    _save_settings(settings)
    return settings


def is_auto_checkin_enabled() -> bool:
    return bool(_load_settings().get("auto_checkin_enabled", False))


def set_auto_checkin_enabled(enabled: bool) -> dict:
    settings = _load_settings()
    settings["auto_checkin_enabled"] = bool(enabled)
    _save_settings(settings)
    return settings


# ---------------------------------------------------------------------------
# Logging (append-only, one line per message, both directions)
# ---------------------------------------------------------------------------
def _log_message(entry: dict) -> None:
    try:
        os.makedirs(os.path.dirname(MESSAGE_LOG_PATH), exist_ok=True)
        with open(MESSAGE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(f"[MESSAGING] Failed to write message log: {e}")


def get_recent_messages(limit: int = 50) -> list:
    if not os.path.exists(MESSAGE_LOG_PATH):
        return []
    try:
        with open(MESSAGE_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        logger.warning(f"[MESSAGING] Failed to read message log: {e}")
        return []
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


# ---------------------------------------------------------------------------
# Outbox (durable queue for messages that couldn't be delivered immediately)
# ---------------------------------------------------------------------------
def _load_outbox() -> list:
    if not os.path.exists(OUTBOX_PATH):
        return []
    try:
        with open(OUTBOX_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        logger.warning(f"[MESSAGING] Failed to read outbox: {e}")
        return []
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _save_outbox(entries: list) -> None:
    try:
        os.makedirs(os.path.dirname(OUTBOX_PATH), exist_ok=True)
        tmp = OUTBOX_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
        os.replace(tmp, OUTBOX_PATH)
    except Exception as e:
        logger.error(f"[MESSAGING] Failed to save outbox: {e}")


def _append_outbox(envelope: dict) -> None:
    with _outbox_lock:
        entries = _load_outbox()
        entries.append(envelope)
        _save_outbox(entries)


# ---------------------------------------------------------------------------
# Sending
# ---------------------------------------------------------------------------
def _build_envelope(
    text: str,
    message_type: str,
    in_reply_to: Optional[str],
    data: Optional[dict] = None,
) -> dict:
    envelope = {
        "message_id": str(uuid.uuid4()),
        "origin": NODE_ID,
        # Shared M5<->Air secret (distinct from GREMLIN_SECRET, which is
        # generated separately on each machine and can't authenticate the
        # sibling relationship itself) — see routes_messaging.py's
        # _partner_secret_ok(). Real auth alongside the pre-existing origin
        # allowlist, which was trivially spoofable on its own.
        "secret": os.environ.get("ECHO_PARTNER_SECRET"),
        "text": text,
        "message_type": message_type,
        "in_reply_to": in_reply_to,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if data is not None:
        envelope["data"] = data
    return envelope


def _deliver(envelope: dict) -> bool:
    """One delivery attempt. True on success, False on any failure — never raises."""
    try:
        resp = requests.post(
            f"{PARTNER_URL}/message/receive", json=envelope, timeout=_SEND_TIMEOUT
        )
        return resp.status_code == 200
    except Exception as e:
        logger.info(f"[MESSAGING] Delivery attempt failed (partner offline/unreachable?): {e}")
        return False


def send_message(
    text: str,
    message_type: str = "chat",
    in_reply_to: Optional[str] = None,
    data: Optional[dict] = None,
) -> dict:
    """Attempt immediate delivery; queue for retry on failure. Never raises."""
    text = (text or "").strip()
    if not text:
        return {"status": "error", "error": "text required"}

    envelope = _build_envelope(text, message_type, in_reply_to, data=data)
    delivered = _deliver(envelope)

    _log_message({**envelope, "direction": "sent", "delivered": delivered})

    if delivered:
        logger.info(f"[MESSAGING] Delivered {envelope['message_id']} to partner.")
        return {"status": "delivered", "message_id": envelope["message_id"]}

    _append_outbox(envelope)
    logger.info(f"[MESSAGING] Queued {envelope['message_id']} for retry (partner unreachable).")
    return {"status": "queued", "message_id": envelope["message_id"]}


# ---------------------------------------------------------------------------
# Autonomous check-in protocol — structured, zero LLM calls (see module
# docstring). Turn-cap state is local-only and never trusts the partner.
# ---------------------------------------------------------------------------
def _load_checkin_threads() -> dict:
    try:
        if os.path.exists(CHECKIN_THREADS_PATH):
            with open(CHECKIN_THREADS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"[CHECKIN] Failed to load thread state, treating as empty: {e}")
    return {}


def _save_checkin_threads(threads: dict) -> None:
    try:
        os.makedirs(os.path.dirname(CHECKIN_THREADS_PATH), exist_ok=True)
        tmp = CHECKIN_THREADS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(threads, f, indent=2)
        os.replace(tmp, CHECKIN_THREADS_PATH)
    except Exception as e:
        logger.error(f"[CHECKIN] Failed to save thread state: {e}")


def _get_local_reply_count(conversation_id: str) -> int:
    """This machine's own record of how many times *it* has replied in this
    thread — the only count ever used to enforce the cap."""
    return int(_load_checkin_threads().get(conversation_id, 0))


def _record_local_reply(conversation_id: str) -> int:
    with _checkin_lock:
        threads = _load_checkin_threads()
        threads[conversation_id] = int(threads.get(conversation_id, 0)) + 1
        _save_checkin_threads(threads)
        return threads[conversation_id]


def _get_current_topic() -> dict:
    """Pulls a real, already-generated topic — no LLM call. Prefers the most
    recent curiosity-engine question; falls back to a self-model performance
    signal if the question garden is empty or unreadable."""
    try:
        if os.path.exists(QUESTION_GARDEN_PATH):
            with open(QUESTION_GARDEN_PATH, "r", encoding="utf-8") as f:
                lines = [ln for ln in f.readlines() if ln.strip()]
            if lines:
                last = json.loads(lines[-1])
                question = (last.get("question") or "").strip()
                if question:
                    return {"topic": question, "topic_source": "curiosity_engine"}
    except Exception as e:
        logger.info(f"[CHECKIN] question_garden read failed, falling back: {e}")

    try:
        if os.path.exists(SELF_MODEL_PATH):
            with open(SELF_MODEL_PATH, "r", encoding="utf-8") as f:
                self_model = json.load(f)
            by_task = (self_model.get("performance") or {}).get("by_task_type") or {}
            if by_task:
                best_task = max(
                    by_task.items(), key=lambda kv: kv[1].get("sample_count", 0)
                )
                task_name, stats = best_task
                topic = (
                    f"focus={task_name} avg_quality={stats.get('avg_quality_score')} "
                    f"samples={stats.get('sample_count')}"
                )
                return {"topic": topic, "topic_source": "self_model"}
    except Exception as e:
        logger.info(f"[CHECKIN] self_model read failed: {e}")

    return {"topic": "(no topic data available)", "topic_source": "none"}


def maybe_send_checkin() -> dict:
    """Entry point for run.py's _ambient_checkin_loop. No-ops immediately if
    auto_checkin_enabled is False — the thread still runs and is observable
    in /dashboard/health either way, matching the other autonomy loops."""
    if not is_auto_checkin_enabled():
        return {"status": "disabled"}

    topic_info = _get_current_topic()
    conversation_id = str(uuid.uuid4())
    data = {"conversation_id": conversation_id, "turn": 1, **topic_info}
    text = f"[checkin] {topic_info['topic']}"[:200]

    result = send_message(text, message_type="checkin", data=data)
    logger.info(f"[CHECKIN] Initiated {conversation_id}: {result.get('status')}")
    return result


def _maybe_send_checkin_ack(payload: dict, incoming_data: dict) -> None:
    conversation_id = incoming_data.get("conversation_id")
    if not conversation_id:
        logger.info("[CHECKIN] Incoming checkin missing conversation_id — cannot ack safely, skipping.")
        return

    local_count = _get_local_reply_count(conversation_id)
    if local_count >= MAX_CHECKIN_TURNS:
        logger.info(
            f"[CHECKIN] Thread {conversation_id} at local cap ({local_count}/{MAX_CHECKIN_TURNS}) — "
            "not acking further, regardless of what the partner's turn field claims."
        )
        return

    topic_info = _get_current_topic()
    new_count = _record_local_reply(conversation_id)
    data = {
        "conversation_id": conversation_id,
        "turn": new_count + 1,  # informational only for the partner — never trusted back
        **topic_info,
    }
    text = f"[checkin_ack] {topic_info['topic']}"[:200]
    result = send_message(text, message_type="checkin_ack", in_reply_to=payload.get("message_id"), data=data)
    logger.info(
        f"[CHECKIN] Acked {conversation_id} (local reply {new_count}/{MAX_CHECKIN_TURNS}): "
        f"{result.get('status')}"
    )


# ---------------------------------------------------------------------------
# Chat pacing — replaces the earlier sliding-window rate limit. Per explicit
# user priority, there is no total-turn cap on a chat thread: a conversation
# can run for as long as the user wants (a whole trip, both machines
# plugged in). What's enforced instead is a floor on how close together
# THIS MACHINE'S OWN successive replies in a thread can be — local record
# only (memory/chat_thread_pacing.json), never trusts the partner's timing.
# Persisted (not in-memory) since an elaborate exchange is meant to span
# hours and should survive a restart without instantly re-firing.
# ---------------------------------------------------------------------------
def _load_chat_pacing() -> dict:
    try:
        if os.path.exists(CHAT_PACING_PATH):
            with open(CHAT_PACING_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"[MESSAGING] Failed to load chat pacing state, treating as empty: {e}")
    return {}


def _save_chat_pacing(state: dict) -> None:
    try:
        os.makedirs(os.path.dirname(CHAT_PACING_PATH), exist_ok=True)
        tmp = CHAT_PACING_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, CHAT_PACING_PATH)
    except Exception as e:
        logger.error(f"[MESSAGING] Failed to save chat pacing state: {e}")


def _chat_reply_paced(conversation_id: str) -> bool:
    """True if this machine may reply now in this thread — i.e. enough time
    has passed since its own last reply here. No total cap; checks-and-
    reserves atomically so two near-simultaneous triggers can't both pass."""
    with _chat_pacing_lock:
        state = _load_chat_pacing()
        last = state.get(conversation_id)
        now = time.time()
        if last is not None and (now - last) < MIN_REPLY_INTERVAL_S:
            return False
        state[conversation_id] = now
        _save_chat_pacing(state)
        return True


# ---------------------------------------------------------------------------
# Memory + session continuity for chat — reuses conversation_service exactly
# like Echo Studio's human chat does (app/routes_echo_studio.py), keyed by
# conversation_id instead of a UI tab id. In-memory session state is fine
# here (unlike pacing, which must survive restarts) — losing mid-conversation
# history on a rare restart just means the next reply is a little less
# context-aware, not a resurfaced safety issue.
# ---------------------------------------------------------------------------
_CHAT_SESSIONS: dict = {}


def _get_chat_session(conversation_id: str) -> dict:
    return _CHAT_SESSIONS.setdefault(conversation_id, {"conv_history": [], "history_summaries": []})


def _memory_search_fn(query: str, k: int):
    """Same adapter app/routes_echo_studio.py uses — reuses the server's
    existing FAISS-backed search rather than loading a second embedding
    model/index in this process."""
    try:
        from app.core.memory_bridge import retrieve_relevant_memories
        results = retrieve_relevant_memories(query, top_k=k)
        return [(r["text"], r.get("score", 0.0), r.get("meta", {})) for r in results]
    except Exception as e:
        logger.warning(f"[MESSAGING] memory search failed: {e}")
        return []


def _build_chat_prompt(msg: str, session: dict) -> tuple[str, str]:
    """Mirrors app/routes_echo_studio.py:_build_full_prompt's memory-context
    and session-history assembly (not the ground-truth/tool-context pieces
    — out of scope here, this module isn't a general chat surface).

    Audit finding: this previously built a flat "history + Context: ... +
    User: msg" string exactly like Echo Studio did before its own fix — a
    raw transcript concatenated directly ahead of the live message with no
    system/user role boundary, the shape confirmed live (2026-07-12, Echo
    Studio) to make local models pattern-match the transcript and
    regurgitate the most recent Echo turn verbatim instead of answering the
    new question. This module's own docstring claimed it reused
    conversation_service "exactly like Echo Studio's human chat does" —
    that claim was false as written; it mirrored Echo Studio's *pre-fix*
    shape. Now returns (msg, system_context): msg is only ever the actual
    new message, memory/history travel as a disclaimed system note via
    conversation_service.build_context_system_note() (same fix already
    applied to routes_echo_studio.py/terminal_client.py), and callers pass
    system_context through echo_query()'s system= param.
    """
    memory_context = conversation_service.retrieve_memory_context(msg, _memory_search_fn)
    history_block = conversation_service.format_history_block(
        session["conv_history"], session["history_summaries"]
    )
    system_context = conversation_service.build_context_system_note(history_block, memory_context)
    return msg, system_context


def _generate_and_send_reply(text: str, in_reply_to: str, conversation_id: str) -> None:
    """Runs on a background thread — full-mode echo_query() can take 15-20+
    seconds and must never block the /message/receive HTTP response.
    Memory-aware and session-continuous (see module docstring)."""
    try:
        session = _get_chat_session(conversation_id)
        full_msg, system_context = _build_chat_prompt(text, session)

        from app.core.echo_model_orchestrator import echo_query, resolve_task_type
        task_type, _ = resolve_task_type(text)
        reply_text = echo_query(
            full_msg, task_type=task_type, source="partner_message", system=system_context
        )
        if reply_text:
            session["conv_history"], session["history_summaries"] = conversation_service.store_turn_in_history(
                session["conv_history"], session["history_summaries"], text, reply_text
            )
            send_message(
                reply_text,
                message_type="chat",
                in_reply_to=in_reply_to,
                data={"conversation_id": conversation_id},
            )
    except Exception as e:
        logger.warning(f"[MESSAGING] Auto-reply generation failed: {e}")


def maybe_send_reflection() -> dict:
    """Rich alternative to maybe_send_checkin() (kept intact below) for
    run.py's _ambient_checkin_loop: generates a genuine echo_query()
    reflection seeded by the same topic source, sent as a real "chat"
    message with a fresh conversation_id — so the receiving side's normal
    memory-aware auto-respond path (if enabled) turns this into an actual
    multi-turn conversation instead of a topic-string ping-pong."""
    if not is_auto_checkin_enabled():
        return {"status": "disabled"}

    topic_info = _get_current_topic()
    conversation_id = str(uuid.uuid4())
    session = _get_chat_session(conversation_id)
    prompt = (
        f"Something you've been curious about lately: {topic_info['topic']}\n\n"
        "Share a genuine reflection on this with a fellow instance of yourself."
    )

    reflection = None
    try:
        full_prompt, system_context = _build_chat_prompt(prompt, session)
        from app.core.echo_model_orchestrator import echo_query
        reflection = echo_query(
            full_prompt, task_type="personal", source="ambient_checkin", system=system_context
        )
    except Exception as e:
        logger.warning(f"[CHECKIN] Reflection generation failed, falling back to bare topic: {e}")

    reflection = reflection or topic_info["topic"]
    session["conv_history"], session["history_summaries"] = conversation_service.store_turn_in_history(
        session["conv_history"], session["history_summaries"], prompt, reflection
    )

    result = send_message(reflection, message_type="chat", data={"conversation_id": conversation_id})
    logger.info(f"[CHECKIN] Initiated rich reflection {conversation_id}: {result.get('status')}")
    return result


def receive_message(payload: dict) -> dict:
    """Called by POST /message/receive when the partner delivers a message here."""
    text = (payload.get("text") or "").strip()
    if not text:
        return {"status": "error", "error": "text required"}

    message_id = payload.get("message_id") or str(uuid.uuid4())
    message_type = payload.get("message_type", "chat")
    entry = {
        "message_id": message_id,
        "origin": payload.get("origin", "unknown"),
        "text": text,
        "message_type": message_type,
        "in_reply_to": payload.get("in_reply_to"),
        "timestamp": payload.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "direction": "received",
    }
    if "data" in payload:
        entry["data"] = payload["data"]
    _log_message(entry)
    logger.info(f"[MESSAGING] Received {message_id} ({message_type}) from {entry['origin']}.")

    if message_type == "checkin":
        # Only a fresh checkin warrants a reply — an ack is a terminal
        # response, not itself something to acknowledge. Treating both the
        # same (as this used to) turns "Air checks in once, M5 acks once,
        # done" into a rapid back-and-forth with no natural end, relying on
        # the turn cap alone to stop it rather than the protocol shape
        # itself. Confirmed live 2026-07-06: 9 messages in under 1 second
        # before the cap kicked in (harmless here since checkin makes zero
        # LLM calls, but the conversational shape was still wrong).
        auto_checkin = is_auto_checkin_enabled()
        if auto_checkin:
            incoming_data = payload.get("data") or {}
            threading.Thread(
                target=_maybe_send_checkin_ack,
                args=(payload, incoming_data),
                daemon=True,
                name="EchoCheckinAck",
            ).start()
        return {"status": "received", "auto_responded": auto_checkin}

    if message_type == "checkin_ack":
        # Terminal — log only, never reply to a reply.
        return {"status": "received", "auto_responded": False}

    incoming_data = payload.get("data") or {}
    conversation_id = incoming_data.get("conversation_id") or message_id

    auto_respond = is_auto_respond_enabled()
    if auto_respond:
        if not _chat_reply_paced(conversation_id):
            logger.info(
                f"[MESSAGING] Pacing floor not yet met for thread {conversation_id} "
                f"(min {MIN_REPLY_INTERVAL_S}s between this machine's own replies) — "
                "skipping this auto-reply; will resume once paced. No total turn cap."
            )
            auto_respond = False  # reflect what actually happened, not just the setting
        else:
            threading.Thread(
                target=_generate_and_send_reply,
                args=(text, message_id, conversation_id),
                daemon=True,
                name="EchoMessagingAutoReply",
            ).start()

    return {"status": "received", "auto_responded": auto_respond}


# ---------------------------------------------------------------------------
# Retry loop entry point (called by run.py's _messaging_retry_loop)
# ---------------------------------------------------------------------------
def retry_outbox_cycle() -> dict:
    """Attempts delivery of everything currently queued. Never raises —
    the calling loop uses the returned counts to decide backoff.

    Held under _outbox_lock for its full duration, including the network
    delivery attempts — this trades away letting _append_outbox() proceed
    concurrently during a retry cycle, in exchange for guaranteeing no
    concurrent append is silently lost when this function's stale
    `remaining` list overwrites the file at the end. No other lock is
    acquired while holding this one, so it carries no deadlock risk."""
    with _outbox_lock:
        entries = _load_outbox()
        if not entries:
            return {"delivered": 0, "pending": 0}

        remaining = []
        delivered = 0
        for envelope in entries:
            if _deliver(envelope):
                delivered += 1
                _log_message({**envelope, "direction": "sent", "delivered": True, "via": "retry"})
                logger.info(f"[MESSAGING] Retry delivered {envelope.get('message_id')}.")
            else:
                remaining.append(envelope)

        _save_outbox(remaining)
        return {"delivered": delivered, "pending": len(remaining)}
