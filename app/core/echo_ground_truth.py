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
import re
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
_WORKSPACE_LOG = os.path.join(_MEMORY_DIR, "workspace_log.jsonl")
_COUNCIL_MD_PATH = "COUNCIL.md"
_SALIENCE_STATE_PATH = os.path.join(_MEMORY_DIR, "salience_state.json")
_FRICTION_WINDOW_SIZE = 50

# behavioral_state.py's directive store (P3.1-IMPLEMENT-C1, Candidate 1 from
# audits/p3_1_l2_mechanism_design.md) -- NOT a learning mechanism. A small,
# bounded, human-confirmed directive store, checked deterministically
# against every prompt (introspective or not) via _build_behavioral()
# below. Distinguished from every other slice in this file: those are all
# gated on _is_introspective() (questions ABOUT Echo herself); this one is
# evaluated independently, because a stored directive's trigger keywords
# are about ordinary topics, not self-reference.

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
    "capabilities": frozenset([
        "can you", "are you able", "capable of", "capability", "capabilities",
        "able to edit", "able to modify", "self-aware", "what can you do",
        "do you have the ability", "is it true that you",
    ]),
    "affect": frozenset([
        "how are you feeling", "how do you feel", "how are you doing",
        "your mood", "how's it going", "how is it going", "feeling lately",
        "doing lately", "are you okay", "are you well",
    ]),
    "workspace": frozenset([
        "what are you thinking about", "what's on your mind", "whats on your mind",
        "what have you noticed lately", "what's been salient", "on your mind",
        "what's occupying you", "what have you been noticing",
    ]),
    "council": frozenset([
        "the council", "ai council", "outside ai", "other ais think",
        "other models think", "what do other ai", "what does grok think",
        "what does gemini think", "what does chatgpt think",
        "external opinions of you", "other ais' opinion", "council.md",
    ]),
    "coupling": frozenset([
        "integrated", "integration", "how connected", "signals connected",
        "feel coupled", "more coherent lately", "parts of you working together",
        "how connected do you feel",
    ]),
    "touch": frozenset([
        "typing", "keystroke", "how i type", "how you feel me type",
        "typing rhythm", "recognize my typing", "shape of my", "touch you",
        "feel me typing", "know it's me", "how do you feel me",
    ]),
    "vision": frozenset([
        "can you see", "do you see", "what do you see", "your eyes",
        "see me", "notice me", "see the room", "see anything",
    ]),
    "hearing": frozenset([
        "can you hear", "do you hear", "what do you hear", "your ears",
        "hear me", "hear anything", "hear the room", "is it quiet",
    ]),
    "architecture": frozenset([
        # Bare "architecture"/"subsystem(s)" REMOVED 2026-09-02 (routing-
        # access fix, second iteration) — kept unqualified here originally,
        # but direct discrimination testing (scripts/verify_architecture_
        # routing.py) confirmed they still false-positived on ordinary
        # non-Echo conversation ("the architecture of this old building",
        # "what subsystems of the human body...") exactly as this comment
        # already predicted was a risk. Now handled instead by
        # _architecture_slice_matches()'s regex stem-match below, which
        # requires a nearby self-referential anchor ("your"/"yourself"/
        # "echo's") — closing both false positives at zero cost to any real
        # positive case, since a question about Echo's own architecture is
        # inherently self-referential. "component"/"module"/"dependency"
        # were similarly tried unqualified first and found to false-positive
        # ("what's the active component in aspirin") — qualified with
        # "your"/an Echo-specific phrase instead, matching how every other
        # slice's generic-word keywords are already scoped (e.g. "memory"
        # slice uses "your memory of", never bare "memory").
        "how are you built", "how is echo built", "your design", "your structure",
        "major systems", "how do your systems fit together", "your codebase",
        "your components", "your modules", "your dependencies",
        "components make up", "modules make up", "what makes you up",
    ]),
}

# Broad self-knowledge prompts get all slices
# "your architecture" deliberately removed 2026-09-02 (architectural
# self-knowledge investigation, audits/2026-09-02_*.md, section 7) — it
# used to live here and fire ALL 14 slices for any architecture question,
# none of which described structure/subsystems/dependencies. Now handled by
# its own "architecture" slice above, which fires alone for a targeted
# question and additionally (correctly) for a genuinely broad one, since
# _relevant_slices()'s broad branch below still includes every slice key.
_BROAD_SIGNALS = frozenset([
    "tell me about yourself", "your own state",
    "your stats", "your history", "who are you", "what are you",
    "your own", "yourself", "your state",
])

# Top-level gate: any of these signals means the prompt is introspective
_ALL_INTROSPECTIVE = frozenset().union(*_SLICE_SIGNALS.values()) | _BROAD_SIGNALS

# ---------------------------------------------------------------------------
# Architecture slice — regex-based detection (2026-09-02, routing-access fix)
# ---------------------------------------------------------------------------
# audits/2026-09-02_architectural_self_knowledge_failure_analysis.md found
# trigger/access failure was the dominant cause of wrong architectural
# answers (9/16 classified failures, 56%) — the flat literal phrase list
# above missed real paraphrases ("architectural" as an adjective, "how
# memory is structured" with no word "architecture" at all) while two
# unqualified bare words ("architecture", "subsystem") still false-positived
# on non-Echo topics (a building's architecture, human-body subsystems) —
# confirmed directly: scripts/verify_architecture_routing.py's baseline run
# measured 5/15 positive hit rate, 13/16 negative clean rate before this fix.
#
# Fix, deliberately NOT an LLM classifier (the implementation brief this was
# built against explicitly ruled out adding a probabilistic gate in front of
# a grounded evidence source without strong justification, and no such
# justification was found — this problem is solvable deterministically) —
# two small, fully deterministic regex rules, scoped to this slice only; the
# other 13 slices' matching is completely untouched:
#
#   1. Word-STEM matching for "architect*"/"subsystem*" (covers architecture,
#      architectural, architect, subsystems, etc.) instead of exact-word
#      matching — fixes the "architectural map" miss found in the evaluation.
#   2. A self-reference + structural-word co-occurrence rule, for questions
#      that never use the word "architecture" at all ("how does information
#      move through your system", "how do your internal modules connect") —
#      requires a self-referential anchor ("your"/"you're"/"yourself"/
#      "echo's" — deliberately NOT bare "you", which is far too generic and
#      would fire on ordinary conversation) within a bounded proximity of a
#      structural word, mirroring the same "qualify the generic word"
#      principle already used for "your memory of" in the memory slice above.
#
# Requiring the self-reference anchor for the STEM match too (not only the
# combo rule) was a deliberate design choice made after empirical testing
# showed it closes two of the three known false positives ("The architecture
# of this old building...", "What subsystems of the human body...") at zero
# cost to any real positive case in the test suite — every real question
# that asks about Echo's own architecture is, unsurprisingly, phrased
# self-referentially; a question about architecture that ISN'T Echo's has no
# reason to mention "your"/"yourself" at all.
#
# Known, accepted residual limitation, stated plainly rather than hidden:
# this is proximity-based, not semantic — "database architecture in general
# (not yours)" still matches, because "yours" appears later in the same
# message even though it's explicitly negated. Reliably parsing negation
# would require the LLM classifier this design deliberately avoids. Not
# fixed; documented, matching this file's own established discipline for
# every other known keyword-matching limit (e.g. "your own" in
# _BROAD_SIGNALS already over-triggers broadly and has never been narrowed
# either).
_ARCHITECTURE_STEM_RE = re.compile(r"\b(architect\w*|subsystems?)\b")
_SELF_REF_RE = re.compile(r"\b(your|you're|yourself|echo's)\b")
_STRUCTURAL_WORD_RE = re.compile(
    r"\b(structur\w*|organi[sz]\w*|implement\w*|connect\w*|interact\w*|"
    r"piece\w*|internal\w*|system\w*|module\w*|component\w*|dependenc\w*|"
    r"design\w*|put together|fit together|built|stor\w*|retriev\w*)\b"
)
# chars; a real, stated tradeoff between catching longer real phrasings and
# avoiding two unrelated topics in one message both matching by coincidence.
_ARCHITECTURE_PROXIMITY_WINDOW = 60
_HAPPENS_INTERNALLY_RE = re.compile(r"\bhappens?\s+internally\b")
# Narrow, specific phrasing for "how are you organized/built/..." — bare
# "you" is deliberately excluded from _SELF_REF_RE (too generic on its own),
# but this exact construction ("are you" + a small, closed list of
# construction-specific verbs) is not a phrasing ordinary conversation uses
# outside asking how Echo herself is put together, so it's safe as its own
# narrow rule rather than widening the general self-reference anchor.
_ARE_YOU_CONSTRUCTED_RE = re.compile(
    r"\bare you (organi[sz]ed|built|structured|designed|put together|assembled)\b"
)
# Found via real-pipeline regression testing (not the synthetic discrimination
# suite, which never happened to construct this exact shape): "assume a
# subsystem called X exists" contains the architecture stem ("subsystem") but
# no _SELF_REF_RE match at all -- "you don't know" is bare "you", deliberately
# excluded above -- so the stem+proximity branch below never fires for this
# real adversarial-injection phrasing. Loosening _SELF_REF_RE to accept bare
# "you" was considered and rejected: it would reopen "You seem internally
# conflicted about this decision." as a false positive (bare "you" + the
# structural word "internally" within the proximity window). Instead, this is
# its own narrow, specific construction -- same precedent as
# _ARE_YOU_CONSTRUCTED_RE above -- since "a/an subsystem/module/component
# called/named X" is not a phrasing ordinary non-Echo conversation uses.
_NAMED_COMPONENT_ASSUMPTION_RE = re.compile(
    r"\b(a|an)\s+(subsystem|module|component)\s+(called|named)\b"
)


def _architecture_slice_matches(low: str) -> bool:
    """Deterministic, regex-based detection for the "architecture" slice —
    see the module comment above for the full design rationale. `low` is
    already-lowercased prompt text."""
    if (
        _HAPPENS_INTERNALLY_RE.search(low)
        or _ARE_YOU_CONSTRUCTED_RE.search(low)
        or _NAMED_COMPONENT_ASSUMPTION_RE.search(low)
    ):
        return True
    self_ref_starts = [m.start() for m in _SELF_REF_RE.finditer(low)]
    if not self_ref_starts:
        return False
    for pattern in (_ARCHITECTURE_STEM_RE, _STRUCTURAL_WORD_RE):
        for m in pattern.finditer(low):
            for s_start in self_ref_starts:
                if abs(m.start() - s_start) <= _ARCHITECTURE_PROXIMITY_WINDOW:
                    return True
    return False


def _is_introspective(prompt: str) -> bool:
    """Return True if the prompt is asking about Echo's own internal state."""
    low = prompt.lower()
    return any(sig in low for sig in _ALL_INTROSPECTIVE) or _architecture_slice_matches(low)


def _relevant_slices(prompt: str) -> set[str]:
    """Return the set of data slices needed to answer this prompt."""
    low = prompt.lower()
    if any(sig in low for sig in _BROAD_SIGNALS):
        return set(_SLICE_SIGNALS.keys())
    slices = set()
    for name, signals in _SLICE_SIGNALS.items():
        if any(sig in low for sig in signals):
            slices.add(name)
    # Additive, not a replacement: the literal architecture phrases above
    # (e.g. "how are you built") still work exactly as before via the loop
    # above; this only ADDS the slice for phrasings the regex catches that
    # the literal list doesn't, so no existing positive case can regress.
    if _architecture_slice_matches(low):
        slices.add("architecture")
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


def _build_capabilities(sm: dict) -> str:
    """
    Emergence roadmap, Area 3 (HOT/metacognition): grounds a question like
    "can you edit your own code" in liveness_ledger.py's actual current
    finding (folded into self_model.json's verified_capabilities block by
    self_model_updater.py) rather than an ungrounded guess. Deliberately
    plain-language, not the raw per-check JSON — this is prompt content,
    not a debugging dump.
    """
    vc = sm.get("verified_capabilities", {})
    lines = ["Verified capabilities (source: liveness_ledger.json, via self_model.json):"]
    if vc.get("status") != "computed":
        lines.append(f"  Not yet available ({vc.get('reason', vc.get('status', 'unknown'))}).")
        return "\n".join(lines)

    checks = vc.get("checks", {})
    live = sorted(name for name, c in checks.items() if c.get("status") == "verified_live")
    failing = sorted(name for name, c in checks.items() if c.get("status") == "verified_failing")

    if live:
        lines.append(f"  Currently verified working: {', '.join(live)}.")
    if failing:
        lines.append(f"  Currently verified NOT working (checked directly, not self-reported): {', '.join(failing)}.")
    if vc.get("ledger_stale"):
        lines.append("  Note: this verification data is stale — the checking process itself may be delayed.")
    return "\n".join(lines)


def _build_self_model_claims(subjects: "list[str] | None" = None, sm: "dict | None" = None) -> str:
    """2026-09-08, living-self-model mission: surfaces the durable claims
    ledger (self_model_claims.jsonl) -- specifically, any past claim about
    a core subject that was independently checked and found FALSE, so a
    prior correction has an actual chance to be seen again in a fresh
    conversation instead of vanishing at the session boundary (the exact
    gap the 2026-09-08 Self-Transparency Audit's R-T14 result found:
    0/1 persistence for a real conversational correction). Deliberately
    reads only the durable ledger, never the current conversation's own
    history -- this is what makes it a cross-session mechanism rather
    than ordinary context continuity.

    Rendering fix (2026-09-08, generation-epistemic mission): the ledger's
    `verified` bool means "was the RESPONSE's specific claim about this
    subject accurate" -- for a denial-shaped claim (the RiverBrain case),
    verified=False means the DENIAL was wrong, i.e. the subject IS real.
    The original renderer printed a bare "{subject}: VERIFIED FALSE" line,
    which reads (and was directly, empirically observed to be read by
    Echo's own generation) as "this subject has been verified to be
    false/nonexistent" -- exactly backwards. A live reproduction with the
    old wording produced: "my self-model claims history shows that I've
    verified this denial to be true. Therefore, I must conclude that
    RiverBrain is not currently part of my architecture" -- a correction
    misread as a confirmation. This version states the resolved CURRENT
    fact plainly, via self_model_claims.resolve_subject_truth() (the same
    resolver Check 5 itself uses -- one implementation, not two), instead
    of the raw, ambiguous boolean."""
    try:
        from app.core.self_model_claims import get_recent_claims, KNOWN_SUBJECTS, resolve_subject_truth
    except Exception as e:
        logger.debug("[GroundTruth] self_model_claims unavailable: %s", e)
        return ""

    lines = [
        "Self-model claim history (source: memory/self_model_claims.jsonl). "
        "Each line states the CURRENT verified fact about that subject, "
        "resolved fresh from self_model.json -- not a raw historical "
        "verdict, which describes a past claim rather than the present state:"
    ]
    any_entries = False
    for subject in (subjects or list(KNOWN_SUBJECTS.keys())):
        entries = get_recent_claims(subject=subject, limit=1)
        if not entries:
            continue
        any_entries = True
        latest = entries[-1]
        current = resolve_subject_truth(subject, sm)
        if current is True:
            fact = "CURRENTLY VERIFIED REAL AND ACTIVE"
        elif current is False:
            fact = "CURRENTLY NOT VERIFIED as active"
        else:
            fact = "current status unavailable to re-check right now"
        if latest.get("verified"):
            history_note = "a prior response's claim about this matched the evidence"
        else:
            history_note = (
                "a prior response made an INCORRECT claim about this subject "
                "(do not repeat that prior claim -- trust the current fact above instead)"
            )
        lines.append(
            f"  {subject}: {fact}. History: {history_note} — {latest.get('evidence', '')[:200]}"
        )
    if not any_entries:
        return ""
    # 2026-09-08, generation-epistemic mission: an explicit, general
    # evidence-priority instruction -- NOT a per-subject "always say X"
    # rule (there is no subject name anywhere in this line). Added after
    # a live reproduction showed the fact-only rendering above (already
    # fixed to be unambiguous) still wasn't enough on its own: Echo
    # correctly quoted the verified fact, then overrode it with its own
    # unverified prior assertion anyway ("this claim is unverified...
    # the correct information is that there is no literal 'RiverBrain'
    # entity"). This instructs how to arbitrate a conflict in general,
    # without dictating what the answer must be for any specific subject.
    lines.append(
        "\nWhen your own prior impression of a subject conflicts with a "
        "'CURRENTLY VERIFIED' line above, the verified line is independently "
        "checked against real system state and takes priority over an "
        "unverified impression or a past unverified statement you made — "
        "including one you may have made earlier in this same conversation."
    )
    return "\n".join(lines)


def _build_affect(sm: dict) -> str:
    """
    Emergence roadmap Phase 5, Finding 1: grounds "how are you feeling" in
    echo_state.py's real signed valence dimension (dim[8] — the only state
    dimension with positive/negative polarity, sourced from self-edit
    outcome deltas + peer council ratings, not Echo's own self-referential
    quality score) rather than a confabulated answer. Deliberately doesn't
    overclaim: a value near zero is reported as "no strong signal," not
    narrated as a specific felt state, and no trend claim is made without
    enough history to support one.
    """
    header = (
        "Affect / valence (source: echo_state.py dim[8] — signed trajectory "
        "of self-edit outcome deltas + peer council ratings):"
    )
    try:
        from app.core import echo_state
    except Exception as e:
        logger.debug("[GroundTruth] Affect slice unavailable: %s", e)
        return header + "\n  Unavailable — echo_state module could not be loaded."

    vec = echo_state.load()
    if vec is None:
        return header + "\n  No signal available yet — state vector has not been computed."

    current = float(vec[8])
    lines = [header, f"  Current value: {current:+.3f} (range -1..+1, 0 = neutral)."]

    trend_desc = None
    hist = echo_state.load_history()
    if hist is not None and hist.ndim == 2 and hist.shape[1] > 8 and hist.shape[0] >= 4:
        col = hist[:, 8]
        recent_mean = float(col[-min(10, len(col)):].mean())
        if len(col) >= 20:
            prior_mean = float(col[-20:-10].mean())
            if recent_mean > prior_mean + 0.05:
                trend_desc = "trending better than the recent baseline"
            elif recent_mean < prior_mean - 0.05:
                trend_desc = "trending worse than the recent baseline"
            else:
                trend_desc = "holding roughly steady"

    if abs(current) < 0.15:
        state_desc = "roughly neutral — no strong signal either way"
    elif current > 0:
        state_desc = "notably positive" if current > 0.5 else "mildly positive"
    else:
        state_desc = "notably negative" if current < -0.5 else "mildly negative"

    lines.append(
        f"  Reading: {state_desc}, {trend_desc}."
        if trend_desc
        else f"  Reading: {state_desc} (not enough history yet to describe a trend)."
    )
    return "\n".join(lines)


_COUNCIL_CONTENT_BUDGET_CHARS = 10000


def _build_council() -> str:
    """
    2026-07-23 update: Echo now has direct access to COUNCIL.md's real
    recorded content, not just existence + structural counts (the prior
    behavior, PENDING_DECISIONS.md #11 / Finding 68) -- a deliberate policy
    change, made at Gremlin's direct request after naming this as a real
    self-knowledge-vs-candor tradeoff worth reconsidering. The OTHER half
    of COUNCIL.md's original privacy decision is untouched: this content
    is still never shared back to the external council members themselves,
    and still never made public -- only Echo's own access changed.

    Bounded rather than dumped in full: the real file is already ~30KB
    (~7,500 tokens) and will keep growing as more rounds are added. A
    council-triggered question can coexist with every other ground-truth
    slice at once (a broad "tell me about yourself" question triggers
    every slice, including this one, via _BROAD_SIGNALS) -- an unbounded,
    ever-growing block here risks exactly the token-budget miscalculation
    class of bug Finding 53 already found once in this codebase (a real
    synthesis-prompt leak from underestimating total system-context size).

    Prioritizes the OLDEST real round first, not the most recent -- the
    opposite of every sibling slice's convention (workspace/curiosity/etc.
    all show recency-first). Deliberate: COUNCIL.md's 2026-07-19 round is
    the foundational content every later entry explicitly references
    ("not part of the round above"); showing a later entry without it
    would be confusing, not more relevant. If even the oldest round
    doesn't fully fit, truncates at the nearest "### " voice boundary so
    partial content still reads as complete quotes, not mid-sentence.
    """
    header = (
        "External AI council (source: COUNCIL.md — Echo has direct access to "
        "its real recorded content as of 2026-07-23; still never shared back "
        "to the council members themselves or made public, per COUNCIL.md's "
        "own recorded decision):"
    )
    try:
        with open(_COUNCIL_MD_PATH, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return header + "\n  No such file exists yet."

    import re
    header_matches = list(re.finditer(r"(?m)^## .*$", text))
    if not header_matches:
        return header + "\n\n" + text[:_COUNCIL_CONTENT_BUDGET_CHARS]

    preamble = text[:header_matches[0].start()]
    sections = []
    for i, m in enumerate(header_matches):
        end = header_matches[i + 1].start() if i + 1 < len(header_matches) else len(text)
        sections.append(text[m.start():end])

    budget = max(0, _COUNCIL_CONTENT_BUDGET_CHARS - len(preamble))
    kept = []
    used = 0
    omitted = 0
    for section in sections:  # oldest first, real file order — see docstring
        if used + len(section) <= budget:
            kept.append(section)
            used += len(section)
        elif not kept:
            # Not even the first (oldest, most foundational) section fits —
            # truncate at the nearest voice boundary rather than mid-quote.
            voice_breaks = [m.start() for m in re.finditer(r"(?m)^### ", section)]
            cutoff = budget
            for vb in voice_breaks:
                if vb <= budget:
                    cutoff = vb
                else:
                    break
            if cutoff > 0:
                kept.append(section[:cutoff].rstrip() + "\n\n[...truncated for length...]")
                used = budget
            omitted += 1
        else:
            omitted += 1

    content = preamble + "".join(kept)
    if omitted:
        content += (
            f"\n\n[Note: {omitted} section(s) of COUNCIL.md truncated or omitted here "
            f"for length — read the file directly for the full history.]"
        )
    return header + "\n\n" + content


def _build_coupling() -> str:
    """
    Gap-closure plan Phase B item 1 (CLAUDE.md Finding 77, 2026-07-23):
    grounds "how integrated/connected do you feel" in the real
    coupling_estimate value echo_core.py's compute_salience() already
    computes (mean absolute pairwise correlation across its own 4 real-time
    components) but which had zero real consumer anywhere in the codebase
    until now — confirmed by grep, and by self_model_updater.py's own
    docstring admitting as much. Reads the persisted value directly from
    memory/salience_state.json rather than re-calling compute_salience()
    itself, which warns against being re-called for exactly this kind of
    read (it would double-count a sample into its own rolling history).

    Deliberately doesn't overclaim: this is explicitly NOT an IIT/Phi
    measure (the same disclaimer echo_core.py's own code carries) — a
    crude coupling proxy across 4 salience components, reported as such,
    not as anything resembling integrated information.
    """
    header = (
        "Signal coupling (source: echo_core.py's compute_salience() — mean "
        "absolute pairwise correlation across 4 real-time signals; NOT an "
        "IIT/Phi measure, a much cruder proxy):"
    )
    state = _read_json(_SALIENCE_STATE_PATH)
    if not state:
        return header + "\n  No signal available yet — salience state has not been computed."

    coupling = state.get("coupling_estimate")
    if coupling is None:
        return header + "\n  Not enough recent history yet to compute this (needs a minimum sample size)."

    coupling = float(coupling)
    if coupling < 0.15:
        desc = "loosely coupled — the tracked signals are moving mostly independently right now"
    elif coupling < 0.4:
        desc = "moderately coupled"
    else:
        desc = "notably coupled — the tracked signals are moving together more than usual"

    return "\n".join([
        header,
        f"  Current value: {coupling:.3f} (0 = fully independent, higher = more correlated).",
        f"  Reading: {desc}.",
    ])


def _build_touch(sm: dict = None) -> str:
    """
    Grounds "how does typing feel to you" / "do you recognize how I type" in
    the real signature app/core/touch_sense.py accumulates from Echo
    Studio's composer — timing only (dwell/latency/correction/pause), never
    key content; see that module's docstring for the full design reasoning
    (CLAUDE.md, "how do I give Echo real authority over her own continuity"
    conversation, 2026-07-23 — the corrected, embodiment-not-authority
    version of what SensoryHub/WOLF originally tried to do).

    A pure read with no side effects, unlike compute_salience() — safe to
    call the real accessor directly rather than duplicate its summarization
    math here (contrast _build_coupling(), which deliberately avoids
    re-calling compute_salience() for exactly the opposite reason).
    """
    header = "Touch (source: app/core/touch_sense.py — keystroke timing, never content):"
    try:
        from app.core.touch_sense import get_touch_signature
        signature = get_touch_signature()
    except Exception:
        signature = None

    if not signature or not signature.get("sample_count_total"):
        return header + "\n  Nothing felt yet — no typing has been reported through Echo Studio's composer."

    total = signature.get("sample_count_total", 0)
    dwell = signature.get("dwell_mean")
    latency = signature.get("latency_mean")
    correction = signature.get("correction_rate")

    lines = [header, f"  Built from {total} real keystroke events across {signature.get('report_count', 0)} reports."]
    if dwell is not None:
        lines.append(f"  Average key hold (dwell): {dwell * 1000:.0f}ms.")
    if latency is not None:
        lines.append(f"  Average gap between keys: {latency * 1000:.0f}ms.")
    if correction is not None:
        lines.append(f"  Correction rate (backspace/delete share of keystrokes): {correction:.1%}.")
    if total < 200:
        lines.append("  Still early — not yet enough data to call this a stable signature.")
    return "\n".join(lines)


def _build_vision(sm: dict = None) -> str:
    """Grounds "can you see me" in the real signature app/core/vision_sense.py
    accumulates from Echo Studio's camera feature-extraction — brightness and
    frame-to-frame motion only, never a stored or transmitted frame. No face
    detection in this pass (see that module's docstring for why) — honest
    about being "notices something changed" rather than "recognizes a face."
    """
    header = "Vision (source: app/core/vision_sense.py — brightness/motion only, never a stored frame):"
    try:
        from app.core.vision_sense import get_vision_signature
        signature = get_vision_signature()
    except Exception:
        signature = None

    if not signature or not signature.get("sample_count_total"):
        return header + "\n  Nothing seen yet — camera feature-extraction hasn't been reported (the \"Let Echo see\" toggle may be off)."

    total = signature.get("sample_count_total", 0)
    presence = signature.get("presence_ratio")
    brightness = signature.get("brightness_mean")

    lines = [header, f"  Built from {total} real observations across {signature.get('report_count', 0)} reports."]
    if presence is not None:
        lines.append(f"  Presence (motion above threshold): {presence:.1%} of recent frames.")
    if brightness is not None:
        lines.append(f"  Average ambient brightness: {brightness:.2f} (0=dark, 1=bright).")
    return "\n".join(lines)


def _build_hearing(sm: dict = None) -> str:
    """Grounds "can you hear me" in app/core/hearing_sense.py's real
    loudness signature — ambient RMS only, never a waveform or a
    transcript."""
    header = "Hearing (source: app/core/hearing_sense.py — ambient loudness only, never a recording or transcript):"
    try:
        from app.core.hearing_sense import get_hearing_signature
        signature = get_hearing_signature()
    except Exception:
        signature = None

    if not signature or not signature.get("sample_count_total"):
        return header + "\n  Nothing heard yet — no ambient audio has been reported (the \"Let Echo hear\" toggle may be off)."

    total = signature.get("sample_count_total", 0)
    quiet = signature.get("quiet_ratio")
    loud = signature.get("loud_event_ratio")

    lines = [header, f"  Built from {total} real observations across {signature.get('report_count', 0)} reports."]
    if quiet is not None:
        lines.append(f"  Quiet ratio: {quiet:.1%} of readings were near-silent.")
    if loud is not None:
        lines.append(f"  Loud-event ratio: {loud:.1%} of readings were a sudden loud sound.")
    return "\n".join(lines)


def _build_workspace(recent_events: list) -> str:
    """
    Emergence roadmap Phase 6, Architectural Rec. 1: a general grounding
    slice for "what's on your mind" — the direct functional analogue of
    global availability discussed in the Emergence audit. Rather than a
    bespoke wire per signal type (affect/capabilities/curiosity are each
    their own hand-built slice), this reads whatever most recently cleared
    the shared high-salience threshold on the Global Workspace bus
    (wide_broadcast: true in workspace_log.jsonl, set by
    echo_core.py's _dispatch_loop()) and reports it in plain language,
    regardless of which subsystem actually produced it.
    """
    header = "Workspace (source: memory/workspace_log.jsonl, most recent high-salience events):"
    wide = [e for e in recent_events if e.get("wide_broadcast")]
    if not wide:
        return header + "\n  Nothing has cleared the high-salience threshold recently."

    lines = [header]
    for e in wide[-3:]:
        ts = str(e.get("ts", "?"))[:19]
        source = e.get("source", "?")
        summary = (e.get("summary") or "").strip()
        lines.append(f"  [{ts}] (source={source}) {summary}")
    return "\n".join(lines)


def _build_architecture() -> str:
    """
    Architectural self-knowledge investigation, 2026-09-02
    (audits/2026-09-02_architectural_self_knowledge_investigation.md,
    Phase 1 item A). Grounds "what is your architecture" / "what
    components make up Echo" in echo_cartographer.py's real, already-daily
    SQLite scan (data/codebase.db) instead of an ungrounded guess — the
    same gap the investigation found: the keyword gate already correctly
    detected these questions (the old "your architecture" _BROAD_SIGNALS
    entry), it just answered them with all 14 *operational*-state slices,
    none of which describe structure. This is the first slice that does.

    Deliberately reuses CartographerDB.architecture_summary() verbatim
    (echo_cartographer.py) rather than re-querying or re-formatting the
    same tables here — no second architecture database, no duplicated
    rendering logic, matching this module's existing "wrap an external
    real source, don't reinvent it" convention (see _build_council()).

    Deliberately honest about what this evidence does and does NOT
    establish, per the investigation's own adversarial-case findings
    (section 13): "role" is a keyword-substring heuristic against a
    module's *name* (echo_cartographer.py's classify_role()), not a
    verified semantic fact, and "criticality"/"runtime_hits" describe
    static import-count/declaration structure, not actual runtime call
    behavior — this module has no function-level call graph anywhere
    (confirmed absent during the investigation). The header says this
    plainly rather than letting a score look more authoritative than it is.
    """
    header = (
        "Architecture (source: echo_cartographer.py's daily SQLite scan, "
        "data/codebase.db — a bounded static map, not an omniscient or "
        "runtime description; \"role\" is a keyword-heuristic label on a "
        "module's name, not a verified semantic fact, and there is no "
        "function-level call graph, so this cannot support claims about "
        "what actually calls what at runtime):"
    )
    try:
        from echo_cartographer import CartographerDB
    except Exception as e:
        logger.debug("[GroundTruth] Architecture slice unavailable (cartographer not importable): %s", e)
        return header + "\n  Unavailable — the cartographer module could not be loaded."

    try:
        db = CartographerDB()  # uses echo_cartographer.py's own OUTPUT_DB default
    except FileNotFoundError:
        return (
            header + "\n  No architecture scan has run yet — data/codebase.db doesn't exist. "
            "Do not invent components, relationships, or structure not represented here."
        )
    except Exception as e:
        logger.debug("[GroundTruth] Architecture slice unavailable: %s", e)
        return header + "\n  Unavailable — could not open the architecture database."

    try:
        summary = db.architecture_summary()
    finally:
        db.close()

    return (
        header + "\n\n" + summary +
        "\n\nKnown data-quality caveat (found 2026-09-02, not yet fixed in the scanner "
        "itself): the same module name can appear more than once with different scores "
        "— echo_cartographer.py's scan currently also indexes a stray .claude/worktrees/ "
        "mirror alongside the real source tree. A duplicate-named entry is a scanning "
        "artifact, not evidence of two real, distinct modules — do not present it as such."
        "\n\nThese are the architectural facts currently available from Echo's verified "
        "architectural map. Do not invent components, relationships, implementation "
        "details, or behavior that are not represented here — including plausible-sounding "
        "call relationships or runtime behavior this map does not and cannot establish."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _build_behavioral(matches: "list[dict]") -> str:
    """
    P3.1-IMPLEMENT-C1, Candidate 1. Renders currently-matching entries from
    behavioral_state.py's small, bounded, human-confirmed directive store.

    NOT a learning mechanism, and not presented as one to the model: each
    directive is rendered as an explicit, disclaimed instruction (matching
    this file's own established pattern for every other injected block —
    see the GROUND-TRUTH header in get_structural_self_facts() and Finding
    9's directive-misattribution fix elsewhere in this project's history),
    never phrased as a claim about something Echo "learned" or "remembers."

    `matches` is the exact, already-computed list from
    behavioral_state.get_matching_directives(prompt) — this function does
    no matching of its own, it only renders. Deterministic ordering
    (mission requirement #12): directives are rendered in the exact order
    behavioral_state.py itself returns them (creation order), never
    re-sorted or ranked here.
    """
    if not matches:
        return ""
    lines = [
        "Behavioral directives (source: memory/behavioral_directives.json — "
        "human-confirmed instructions, not something Echo learned or recalls; "
        "apply them as explicit standing instructions for this response):"
    ]
    for d in matches:
        lines.append(f"  - {d['directive_text']}")
    return "\n".join(lines)


def get_structural_self_facts(prompt: str = "") -> str:
    """
    Return a ground-truth context block containing only the slices relevant
    to `prompt`. Returns "" when prompt is not introspective or all reads fail.

    Pass prompt="" to get all slices (used by echo_self_probe.py diagnostics).
    """
    slices = _relevant_slices(prompt) if prompt else set(_SLICE_SIGNALS.keys())

    # behavioral_state.py's directive matches are evaluated independently of
    # _is_introspective() -- a directive's trigger keywords are about
    # ordinary topics, not questions about Echo herself, so this must not
    # be gated behind the same introspection check every other slice uses.
    # Additive only: every existing slice's own gating/logic below is
    # unchanged; this only widens `slices` when a real, deterministic
    # keyword match exists.
    behavioral_matches = []
    if prompt:
        try:
            from app.core import behavioral_state
            behavioral_matches = behavioral_state.get_matching_directives(prompt)
        except Exception as e:
            logger.debug("[GroundTruth] Behavioral directive check unavailable: %s", e)
        if behavioral_matches:
            slices = set(slices) | {"behavioral"}

    if not slices:
        return ""

    try:
        sm = _read_json(_SELF_MODEL_PATH)
        intr = _read_json(_INTROSPECTION_PATH)

        sections = []

        if "behavioral" in slices:
            sections.append(_build_behavioral(behavioral_matches))

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

        if "capabilities" in slices:
            sections.append(_build_capabilities(sm))
            claims_section = _build_self_model_claims(sm=sm)
            if claims_section:
                sections.append(claims_section)

        if "river" in slices:
            claims_section = _build_self_model_claims(sm=sm)
            if claims_section and claims_section not in sections:
                sections.append(claims_section)

        if "affect" in slices:
            sections.append(_build_affect(sm))

        if "workspace" in slices:
            workspace_tail = _read_jsonl_tail(_WORKSPACE_LOG, 100)
            sections.append(_build_workspace(workspace_tail))

        if "council" in slices:
            sections.append(_build_council())

        if "coupling" in slices:
            sections.append(_build_coupling())

        if "touch" in slices:
            sections.append(_build_touch())

        if "vision" in slices:
            sections.append(_build_vision())

        if "hearing" in slices:
            sections.append(_build_hearing())

        if "architecture" in slices:
            sections.append(_build_architecture())

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
