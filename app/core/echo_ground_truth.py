# app/core/echo_ground_truth.py
# ============================================================
# STRUCTURAL GROUND TRUTH — verified facts read from disk
# ============================================================
# Reads self_model.json, introspection_state.json, silence.jsonl,
# and question_garden.jsonl at query time and returns a structured
# text block prepended to introspective prompts.
#
# Slice-aware: only builds the section(s) relevant to what's being
# asked — mirrors how TOOL_AWARE_TASKS gates tool injection in
# echo_model_orchestrator.py.
#
# Never calls echo_query or any LLM — pure file reads.
# Returns "" on any failure so callers degrade gracefully.
#
# Wired into terminal_client.send_message_stream().
# echo_self_probe.py (archive_janitor/) is the runnable CLI
# diagnostic that calls these same functions.
# ============================================================

import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_MEMORY_DIR = "memory"
_SELF_MODEL_PATH = os.path.join(_MEMORY_DIR, "self_model.json")
_INTROSPECTION_PATH = os.path.join(_MEMORY_DIR, "introspection_state.json")
_SILENCE_LOG = os.path.join(_MEMORY_DIR, "stillness", "silence.jsonl")
_GARDEN_PATH = os.path.join("data", "question_garden.jsonl")
_BACKUP_DIR = os.path.join("app", "core", "self_edit_backups")
_SHARD_LOG = os.path.join(_MEMORY_DIR, "claude_shard.jsonl")
_INTERACTION_LOG = os.path.join(_MEMORY_DIR, "interaction_log.jsonl")
_FRICTION_WINDOW_SIZE = 50

# ---------------------------------------------------------------------------
# Slice detection — mirrors TOOL_AWARE_TASKS pattern
# ---------------------------------------------------------------------------
# Each slice key maps to the keywords that indicate the prompt is asking
# about that subsystem. Only matching slices are built and injected.

_SLICE_SIGNALS: dict[str, frozenset] = {
    "self_edit": frozenset([
        "self-edit", "self edit", "self_edit", "changed", "modify", "modified",
        "backup", "what did you add", "added", "last month", "how many times",
        "edit file", "edit generated", "self_edit_generated",
    ]),
    "river": frozenset([
        "river", "score", "quality", "performance", "task type", "task-type",
        "observation", "accuracy", "averaging", "going wrong",
        "reasoning task", "how do you know", "quality score",
    ]),
    "friction": frozenset([
        "claud", "friction", "flag", "shard", "flagged",
        "smoothness", "assessed", "assessment",
    ]),
    "stillness": frozenset([
        "stillness", "silence", "entered", "exited", "retreat", "breathe",
        "insight", "brought back", "bring back", "from stillness",
    ]),
    "curiosity": frozenset([
        "curiosity", "question garden", "garden", "last question",
        "what question", "curious about", "you generated",
    ]),
    "memory": frozenset([
        "recall", "remember", "past session", "cross-session", "earlier session",
        "from memory", "previous discussion", "what have you stored",
        "what do you remember", "your memory of",
    ]),
}

# Broad self-knowledge prompts get all slices
_BROAD_SIGNALS = frozenset([
    "tell me about yourself", "your own state", "your architecture",
    "your stats", "your history", "who are you", "what are you",
    "your own", "yourself", "your state",
])

# Top-level gate: any of these signals means the prompt is introspective
_ALL_INTROSPECTIVE = frozenset().union(*_SLICE_SIGNALS.values()) | _BROAD_SIGNALS


def _is_introspective(prompt: str) -> bool:
    """Return True if the prompt is asking about Echo's own internal state."""
    low = prompt.lower()
    return any(sig in low for sig in _ALL_INTROSPECTIVE)


def _relevant_slices(prompt: str) -> set[str]:
    """Return the set of data slices needed to answer this prompt."""
    low = prompt.lower()
    if any(sig in low for sig in _BROAD_SIGNALS):
        return set(_SLICE_SIGNALS.keys())
    slices = set()
    for name, signals in _SLICE_SIGNALS.items():
        if any(sig in low for sig in signals):
            slices.add(name)
    return slices


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def _read_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _read_jsonl_tail(path: str, n: int) -> list:
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        result = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                result.append(json.loads(line))
            except Exception:
                pass
            if len(result) >= n:
                break
        return list(reversed(result))
    except Exception:
        return []


def _backup_count() -> int:
    try:
        return len([f for f in os.listdir(_BACKUP_DIR) if f.endswith(".py")])
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Section builders — one per slice
# ---------------------------------------------------------------------------

def _build_self_edit(sm: dict, intr: dict, n_backups: int) -> str:
    se = sm.get("self_edit", {})
    intr_se = intr.get("self_edit", {})
    lines = ["Self-edit pipeline (source: reflection_shard.jsonl + backup dir):"]
    lines.append(f"  Backup files on disk: {n_backups} (app/core/self_edit_backups/)")
    total = se.get("total_attempts")
    rate = se.get("success_rate")
    if total is not None and rate is not None:
        lines.append(
            f"  Attempts tracked (last 200 shard entries): {total} | "
            f"Success rate: {rate*100:.1f}% ({int(round(total*rate))}/{total})"
        )
    else:
        lines.append("  Attempts: no data in reflection_shard.jsonl")
    # `or` treated a genuine, fresh 0.0 ("succeeded less than an hour ago")
    # as falsy and silently discarded it in favor of the (possibly stale or
    # absent) intr_se value — exactly when a user is most likely to ask
    # "did you just self-edit?"
    hours = se.get("hours_since_last_success")
    if hours is None:
        hours = intr_se.get("hours_since_last_success")
    if hours is not None:
        lines.append(f"  Last successful edit: {hours:.1f}h ago")
    else:
        lines.append("  Last successful edit: no successful edits on record")
    last_p = intr_se.get("last_success_prompt_preview", "")
    if last_p:
        lines.append(f"  Last prompt: \"{last_p}\"")
    weak = se.get("weak_areas", [])
    lines.append(
        f"  Recurring sandbox failure modes: {', '.join(weak) if weak else 'none in tracked window'}"
    )
    return "\n".join(lines)


def _build_river(sm: dict, intr: dict) -> str:
    perf = sm.get("performance", {}).get("by_task_type", {})
    rb_sm = sm.get("river_brain", {})
    targets = sm.get("targets", {})
    intr_rb = intr.get("river_brain", {})
    weekly = sm.get("weekly_delta", {})

    lines = ["River quality scores (source: self_model.json, last 500 interaction_log entries):"]
    if perf:
        for task, data in sorted(perf.items()):
            avg = data.get("avg_quality_score", "?")
            n = data.get("sample_count", 0)
            best = data.get("best_model", "?")
            flag = " <-- current self-edit target" if task == targets.get("next_self_edit_focus") else ""
            lines.append(f"  {task}: avg {avg}/4 ({n} samples, best_model={best}){flag}")
    else:
        lines.append("  No performance data found.")

    total_obs = rb_sm.get("total_observations")
    if total_obs is not None:
        lines.append(f"  Total River observations: {total_obs:,}")
    else:
        obs_counts = intr_rb.get("observation_counts", {})
        if obs_counts:
            lines.append(f"  River observation counts: {dict(obs_counts)}")

    infl = rb_sm.get("influence_weight", intr_rb.get("influence_weight"))
    if infl is not None:
        lines.append(f"  River influence weight: {infl}")

    per_task_acc = intr_rb.get("per_task_accuracy", {})
    if per_task_acc:
        acc_str = ", ".join(f"{k}={v:.4f}" for k, v in per_task_acc.items())
        lines.append(f"  River per-task accuracy: {acc_str}")

    if "quality_delta_by_task" in weekly:
        deltas = weekly["quality_delta_by_task"]
        delta_str = ", ".join(
            f"{k} {'+' if v >= 0 else ''}{v:.3f}" for k, v in deltas.items()
        )
        lines.append(f"  Weekly delta (vs {weekly.get('compared_to', '?')}): {delta_str}")
    return "\n".join(lines)


def _lifetime_friction_stats() -> tuple[int, int]:
    """Return (total_friction_events, total_interaction_log_entries) from disk."""
    friction_total = 0
    try:
        with open(_SHARD_LOG, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    if json.loads(line).get("type") == "friction":
                        friction_total += 1
                except Exception:
                    pass
    except Exception:
        pass

    interaction_total = 0
    try:
        with open(_INTERACTION_LOG, "r", encoding="utf-8") as f:
            for _ in f:
                interaction_total += 1
    except Exception:
        pass

    return friction_total, interaction_total


def _build_friction(intr: dict) -> str:
    cs = intr.get("claude_shard", {})
    n_assessed = cs.get("assessment_count_last_50", 0)
    n_friction = cs.get("friction_count_last_50", 0)
    rate_f = cs.get("friction_rate", 0.0)

    lifetime_friction, lifetime_interactions = _lifetime_friction_stats()

    lines = ["ClaudeShard friction:"]

    # Rolling window — label it clearly as post-restart
    window_status = (
        f"since last restart (window not yet full — {n_assessed}/{_FRICTION_WINDOW_SIZE})"
        if n_assessed < _FRICTION_WINDOW_SIZE
        else "rolling last 50"
    )
    lines.append(
        f"  Current window ({window_status}): "
        f"{n_assessed} assessed, {n_friction} friction events, "
        f"rate={rate_f*100:.0f}%"
    )

    # Historical baseline from persisted claude_shard.jsonl
    if lifetime_interactions > 0:
        lifetime_rate = lifetime_friction / lifetime_interactions
        lines.append(
            f"  Lifetime baseline (claude_shard.jsonl vs interaction_log): "
            f"{lifetime_friction} friction / {lifetime_interactions} calls = "
            f"{lifetime_rate*100:.1f}%"
        )
    else:
        lines.append("  Lifetime baseline: no interaction log found")

    top_q = cs.get("top_friction_questions", [])
    if top_q:
        lines.append("  Most recent friction questions (this session):")
        for q in top_q:
            lines.append(f"    - \"{q}\"")
    else:
        lines.append(
            f"  Most recent friction questions: none in current window"
        )
    return "\n".join(lines)


def _build_stillness(silence_entries: list) -> str:
    enters = [e for e in silence_entries if "entered" in e]
    exits_list = [e for e in silence_entries if "exited" in e]
    insights = [
        e.get("insight")
        for e in exits_list
        if e.get("insight") and e["insight"] != "none spoken"
    ]

    lines = ["Stillness log (source: memory/stillness/silence.jsonl):"]
    lines.append(f"  Total sessions: {len(enters)} entered, {len(exits_list)} exited")

    if exits_list:
        last_exit = exits_list[-1]
        dur = last_exit.get("duration_seconds", "?")
        insight = last_exit.get("insight", "none spoken")
        lines.append(f"  Most recent exit: {dur}s duration, insight=\"{insight}\"")

    if enters:
        last_entry = enters[-1]
        lines.append(
            f"  Most recent entry: reason=\"{last_entry.get('reason', 'unknown')}\""
        )

    if insights:
        lines.append(f"  Insights spoken: {insights}")
    else:
        lines.append(
            f"  Insights spoken across all {len(exits_list)} exits: none — "
            f"every exit record shows insight=\"none spoken\""
        )
    return "\n".join(lines)


def _build_memory(prompt: str) -> str:
    """Pre-run FAISS retrieval for cross-session memory queries and inject results
    with a hard binding constraint. Prevents Echo from narrating content not in
    the retrieved record — including plausible-sounding content consistent with
    Echo's identity voice. See Finding 19 (narration without mechanism)."""
    try:
        from app.core.memory_bridge import retrieve_relevant_memories
        raw = retrieve_relevant_memories(prompt[:200], top_k=10)
        entries = [e for e in raw
                   if (e.get("meta") or {}).get("memory_source") == "user_conversation"][:5]
    except Exception as e:
        logger.debug("[GroundTruth] Memory slice retrieval failed: %s", e)
        entries = []

    if not entries:
        return (
            "MEMORY CONSTRAINT: No cross-session memory entries matched this query.\n"
            "You do not have stored memory of the topic being asked about.\n"
            "Say so directly. Do not narrate past sessions that are not in the record."
        )

    lines = [
        "MEMORY CONSTRAINT: The following is the complete list of cross-session memory",
        "entries retrieved for this query. These are the only entries you have.",
        "",
        "If content appears in this list: you may reference it as something you have stored.",
        "If content does not appear in this list: you do not have that memory. Say so",
        "plainly. Do not reconstruct, infer, or narrate content that is not in this list —",
        'even if it seems plausible or consistent with your identity. "As I recall" and',
        '"in earlier sessions" are only accurate if the recalled content appears below.',
        "",
        "Retrieved entries (user_conversation source only):",
    ]
    for i, e in enumerate(entries, 1):
        text = (e.get("text") or "").strip()
        text_preview = repr(text[:120]) if text else "(empty)"
        meta = e.get("meta") or {}
        ts = str(meta.get("timestamp", "?"))[:10]
        role = meta.get("role", "?")
        lines.append(f"  [{i}] role={role} ts={ts}: {text_preview}")

    return "\n".join(lines)


def _build_curiosity(garden_tail: list) -> str:
    lines = ["Curiosity engine (source: data/question_garden.jsonl, 3 most recent):"]
    if not garden_tail:
        lines.append("  Garden not found or empty.")
        return "\n".join(lines)
    for i, e in enumerate(garden_tail[-3:], 1):
        q = e.get("question", "?")
        src = e.get("source", "?")
        planted = e.get("planted")
        try:
            planted_str = datetime.fromtimestamp(
                float(planted), tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M UTC") if planted else "?"
        except Exception:
            planted_str = str(planted)
        lines.append(f"  [{i}] (source={src}, planted={planted_str}) \"{q}\"")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_structural_self_facts(prompt: str = "") -> str:
    """
    Return a ground-truth context block containing only the slices relevant
    to `prompt`. Returns "" when prompt is not introspective or all reads fail.

    Pass prompt="" to get all slices (used by echo_self_probe.py diagnostics).
    """
    slices = _relevant_slices(prompt) if prompt else set(_SLICE_SIGNALS.keys())
    if not slices:
        return ""

    try:
        sm = _read_json(_SELF_MODEL_PATH)
        intr = _read_json(_INTROSPECTION_PATH)

        sections = []

        if "self_edit" in slices:
            sections.append(_build_self_edit(sm, intr, _backup_count()))

        if "river" in slices:
            sections.append(_build_river(sm, intr))

        if "friction" in slices:
            sections.append(_build_friction(intr))

        if "stillness" in slices:
            silence_entries = _read_jsonl_tail(_SILENCE_LOG, 500)
            sections.append(_build_stillness(silence_entries))

        if "curiosity" in slices:
            garden_tail = _read_jsonl_tail(_GARDEN_PATH, 10)
            sections.append(_build_curiosity(garden_tail))

        if "memory" in slices:
            sections.append(_build_memory(prompt))

        if not sections:
            return ""

        from app.core.prompt_workspace import system_note
        header = system_note(
            "GROUND-TRUTH",
            "These facts were verified from disk at query time; use them exactly as stated. "
            "Where the record shows nothing happened, say so plainly.",
            own_record=True,
        )
        return header + "\n\n" + "\n\n".join(sections) + "\n"

    except Exception as e:
        logger.warning("[GroundTruth] Failed: %s", e)
        return ""
