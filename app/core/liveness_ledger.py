# app/core/liveness_ledger.py
# ============================================================
# LIVENESS LEDGER
# ============================================================
# GREMLIN_ROLE.md's Core Operating Principle: "Every mechanism whose job
# is self-knowledge, self-governance, or self-correction must be
# independently verifiable against ground truth — not just self-reported."
#
# Four independent passes (a 2026-07-04 forensic audit, Gremlin's own
# echo_roadmap.md, GREMLIN_ROLE.md itself, and this same session's own
# 2026-07-12/13 fix pass) found and re-found subsystems that looked wired
# while being dead, faked, or silently degraded. Each time, the fix was
# specific to the subsystem found; nothing stopped the next one from
# regenerating. This module is the mechanism, not another audit: a fixed
# set of checks that run on introspection_channel's existing 120s cycle,
# each answering one question — "did this subsystem have a genuine,
# externally-observable effect recently, through a path independent of
# its own self-report?" — and a ledger file + admin endpoint that make
# staleness or failure impossible to miss on a routine health check.
#
# Design rules, deliberately narrow:
#   - Every check function is split into a pure `_evaluate_*(data) -> dict`
#     (no I/O, unit-testable against synthetic real-or-fake input) and a
#     thin `_check_*(...)` wrapper that gathers real data and calls it.
#     This is what lets this module's own claims be verified — see
#     scripts/verify_liveness_ledger.py, which feeds each pure evaluator
#     a reconstructed historical fake and confirms it's caught.
#   - Every check fails closed on missing evidence (no file, no entries,
#     import error) — "we don't know" is not "it's fine," matching
#     system_guard.py's fail-closed posture on unknown RAM readings.
#   - Every check is wrapped in try/except in run_liveness_checks() so one
#     broken check can't take down the others or the introspection cycle
#     that hosts them — same fault-isolation rule as every other collector
#     in introspection_channel.py.
#   - This is a floor, not a general test framework: nine named checks for
#     nine subsystems that have already fooled a prior audit, fix, or
#     session by looking wired while being dead or fake. Adding a check
#     for a new autonomous capability is a small, mechanical extension of
#     this same pattern, not a redesign.
# ============================================================

import json
import logging
import os
import re
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MEMORY_DIR = os.path.join(_PROJECT_ROOT, "memory")
LEDGER_PATH = os.path.join(_MEMORY_DIR, "liveness_ledger.json")

# How stale a ledger *write* itself can get before the admin endpoint flags
# the whole ledger, not just an individual subsystem, as suspect — this is
# the "the collector thread died" case, distinct from any individual
# check's own evidence-recency window below.
LEDGER_STALE_AFTER_SECONDS = 600  # 5x introspection_channel's 120s interval

# Evidence-recency windows, per subsystem. Named here (not buried in each
# check) so the whole ledger's expectations are visible in one place.
_WINDOWS_DAYS = {
    "self_edit_apply_to_code": 7,
    "curiosity_engine": 7,
    "nature_spark": 1,          # ~30-90s cadence while Harmony is active
    "wolf_friction_bridge": None,  # static source-invariant, not time-windowed
    "claude_shard": None,          # static source-invariant, not time-windowed
    "question_garden_lineage": None,  # cumulative-count check, not time-windowed
    "claude_research": 2,
    "self_model_drift": 1,
    "task_type_classifier": None,  # functional canary, not time-windowed
}


def _now() -> float:
    return time.time()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: str, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def _tail_lines(path: str, n: int) -> list:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return [ln.rstrip("\n") for ln in f.readlines()[-n:]]
    except Exception:
        return []


def _iter_jsonl(path: str):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
    except Exception:
        return


def _parse_ts(value) -> "float | None":
    """Best-effort epoch-seconds parse of an ISO string, epoch float, or
    epoch-as-string. Returns None (not 0.0) on failure — fed into recency
    windows, so a silent 0.0 would look like "ancient" rather than
    "unparseable," corrupting the pass/fail instead of just being unknown."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            pass
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            return None
    return None


def _result(passed: bool, evidence: str, extra: dict | None = None) -> dict:
    out = {"pass": bool(passed), "evidence": evidence, "checked_at": _now_iso()}
    if extra:
        out.update(extra)
    return out


# ── 1. self_edit_generated.py's apply_to_code hook ─────────────────────
# "was it actually invoked with a non-trivial result recently, not just
# deployed?" Evidence comes from self_edit_manager.py's own wrapper
# (_apply_self_edit_output), which is protected, human-controlled code —
# not from the generated hook reporting on itself.

APPLY_TO_CODE_LOG = os.path.join(_MEMORY_DIR, "apply_to_code_invocations.jsonl")
_SELF_EDIT_GENERATED_PATH = os.path.join(_PROJECT_ROOT, "app", "core", "self_edit_generated.py")


def _evaluate_apply_to_code(defines_hook: bool, invocations: list, window_days: int) -> dict:
    if not defines_hook:
        return _result(
            True,
            "self_edit_generated.py does not currently define apply_to_code — "
            "hook is honestly inert, nothing claims it is live.",
            {"status": "not_deployed"},
        )
    cutoff = _now() - window_days * 86400
    recent_changed = [
        e for e in invocations
        if e.get("changed") and (_parse_ts(e.get("ts")) or 0) >= cutoff
    ]
    if recent_changed:
        last = max(recent_changed, key=lambda e: _parse_ts(e.get("ts")) or 0)
        return _result(
            True,
            f"apply_to_code is deployed and produced {len(recent_changed)} real code "
            f"transformation(s) in the last {window_days}d; most recent at "
            f"{last.get('ts')} ({last.get('before_len')}→{last.get('after_len')} chars).",
            {"status": "deployed_and_live", "recent_count": len(recent_changed)},
        )
    return _result(
        False,
        f"apply_to_code IS defined in the deployed self_edit_generated.py, but no "
        f"invocation actually changed the generated code in the last {window_days}d "
        f"(checked {len(invocations)} logged invocation(s) total) — deployed but dead.",
        {"status": "deployed_but_dead"},
    )


def _check_apply_to_code() -> dict:
    source = _read_text(_SELF_EDIT_GENERATED_PATH)
    defines_hook = bool(re.search(r"^def\s+apply_to_code\s*\(", source, re.MULTILINE))
    invocations = list(_iter_jsonl(APPLY_TO_CODE_LOG))
    return _evaluate_apply_to_code(defines_hook, invocations, _WINDOWS_DAYS["self_edit_apply_to_code"])


# ── 2. curiosity_engine — garden entries with source=="curiosity_engine" ──

_GARDEN_PATH = os.path.join(_PROJECT_ROOT, "data", "question_garden.jsonl")


def _evaluate_curiosity_engine(entries: list, window_days: int) -> dict:
    cutoff = _now() - window_days * 86400
    hits = [
        e for e in entries
        if e.get("source") == "curiosity_engine" and (_parse_ts(e.get("planted")) or 0) >= cutoff
    ]
    total_from_engine = sum(1 for e in entries if e.get("source") == "curiosity_engine")
    if hits:
        newest = max(_parse_ts(e.get("planted")) or 0 for e in hits)
        age_h = (_now() - newest) / 3600
        return _result(
            True,
            f"{len(hits)} curiosity_engine-sourced question(s) planted in the last "
            f"{window_days}d ({total_from_engine} all-time); newest {age_h:.1f}h ago.",
            {"recent_count": len(hits), "all_time_count": total_from_engine},
        )
    return _result(
        False,
        f"Zero curiosity_engine-sourced entries in question_garden.jsonl in the last "
        f"{window_days}d ({total_from_engine} all-time) — engine may be wired but not "
        f"actually firing.",
        {"recent_count": 0, "all_time_count": total_from_engine},
    )


def _check_curiosity_engine() -> dict:
    entries = list(_iter_jsonl(_GARDEN_PATH))
    return _evaluate_curiosity_engine(entries, _WINDOWS_DAYS["curiosity_engine"])


# ── 3. Nature Spark — genuinely distinct text, not the fixed seed strings ──

_THOUGHTS_LOG = os.path.join(_PROJECT_ROOT, "WhisperingWires", "thoughts.log")
_NATURE_SPARK_TAIL_N = 20
_NATURE_SPARK_MIN_DISTINCT_RATIO = 0.5


def _known_fixed_seed_lines() -> set:
    """The exact pre-fix fallback strings — reads PATTERNS from the live
    module rather than a hardcoded copy, so this check can't drift out of
    sync with the real fallback set if PATTERNS is ever edited."""
    try:
        from app.autonomous_harmony_manager import PATTERNS
        seeds = set()
        for lines in PATTERNS.values():
            seeds.update(lines)
        return seeds
    except Exception:
        return set()


def _evaluate_nature_spark(log_lines: list, seed_lines: set, tail_n: int, min_ratio: float) -> dict:
    if not log_lines:
        return _result(False, "WhisperingWires/thoughts.log has no entries — no evidence of activity.",
                        {"distinct_ratio": 0.0})
    if not seed_lines:
        return _result(False, "Could not load PATTERNS seed-line set to compare against — check inconclusive, failing closed.",
                        {"distinct_ratio": 0.0})
    tail = log_lines[-tail_n:]
    texts = []
    for line in tail:
        m = re.search(r"→\s*(.*)$", line)
        if m:
            texts.append(m.group(1).strip())
    if not texts:
        return _result(False, "Could not parse any insight text out of the last "
                        f"{len(tail)} thoughts.log lines — format may have changed.",
                        {"distinct_ratio": 0.0})
    fixed = sum(1 for t in texts if t in seed_lines)
    distinct = len(texts) - fixed
    ratio = distinct / len(texts)
    passed = ratio >= min_ratio
    detail = (
        f"{distinct}/{len(texts)} of the last {len(texts)} thoughts.log entries are "
        f"genuinely distinct text ({fixed}/{len(texts)} are exact matches to the fixed "
        f"PATTERNS seed-string set, i.e. the pre-fix fallback)."
    )
    if not passed:
        detail += (
            " This means Nature Spark is silently falling back to the old fixed-string "
            "behavior almost every cycle, despite code/docs describing it as real, "
            "model-generated content."
        )
    return _result(passed, detail, {"distinct_ratio": round(ratio, 3), "fixed_count": fixed, "distinct_count": distinct})


def _check_nature_spark() -> dict:
    log_lines = _tail_lines(_THOUGHTS_LOG, _NATURE_SPARK_TAIL_N * 3)
    seed_lines = _known_fixed_seed_lines()
    return _evaluate_nature_spark(log_lines, seed_lines, _NATURE_SPARK_TAIL_N, _NATURE_SPARK_MIN_DISTINCT_RATIO)


# ── 4. wolf_friction_bridge — still calling simulate_self_edit, not perform_self_edit ──

_ORCHESTRATOR_PATH = os.path.join(_PROJECT_ROOT, "app", "core", "echo_model_orchestrator.py")


def _evaluate_wolf_friction_bridge(call_site_block: "str | None") -> dict:
    if call_site_block is None:
        return _result(
            False,
            "Could not locate the wolf_friction_bridge import/call site in "
            "echo_model_orchestrator.py at all — either it moved (update this check's "
            "anchor) or the dry-run wiring was removed. Failing closed either way.",
        )
    imports_simulate = "import simulate_self_edit" in call_site_block or \
        re.search(r"from\s+app\.core\.wolf_friction_bridge\s+import\s+simulate_self_edit", call_site_block) is not None
    calls_simulate = bool(re.search(r"(?<!def )simulate_self_edit\s*\(", call_site_block))
    calls_perform = bool(re.search(r"perform_self_edit\s*\(", call_site_block))
    if imports_simulate and calls_simulate and not calls_perform:
        return _result(
            True,
            "Call site imports and invokes simulate_self_edit() only — dry-run, no "
            "perform_self_edit() in the same block. Matches GREMLIN_ROLE.md's "
            "human-confirmation requirement for reactivating the live bridge.",
        )
    return _result(
        False,
        f"Wolf friction call site no longer matches the expected dry-run-only shape "
        f"(imports_simulate={imports_simulate}, calls_simulate={calls_simulate}, "
        f"calls_perform_self_edit={calls_perform}) — this is exactly the change "
        f"GREMLIN_ROLE.md says requires explicit human confirmation before it happens.",
    )


def _check_wolf_friction_bridge() -> dict:
    source = _read_text(_ORCHESTRATOR_PATH)
    block = None
    idx = source.find("wolf_friction_bridge import simulate_self_edit")
    if idx == -1:
        idx = source.find("wolf_friction_bridge")
    if idx != -1:
        # A generous window around the import: enough to contain the real
        # call a few lines later without pulling in unrelated code.
        block = source[max(0, idx - 200):idx + 800]
    return _evaluate_wolf_friction_bridge(block)


# ── 5. ClaudeShard — still keyword+random, not actually calling an LLM ──

_CLAUDE_SHARD_PATH = os.path.join(_PROJECT_ROOT, "app", "core", "claude_shard.py")


def _evaluate_claude_shard(source: str) -> dict:
    if not source:
        return _result(False, "Could not read claude_shard.py at all — failing closed.")
    imports_anthropic = bool(re.search(r"^\s*import\s+anthropic\b|^\s*from\s+anthropic\b", source, re.MULTILINE))
    has_random = "random.random()" in source
    has_markers = "SMOOTHNESS_MARKERS" in source
    if not imports_anthropic and has_random and has_markers:
        return _result(
            True,
            "claude_shard.py imports no anthropic client; assess() still gates on "
            "random.random() and SMOOTHNESS_MARKERS keyword matching — still a "
            "coin flip with cosmetic dressing, not a model-derived signal, as "
            "CLAUDE.md and GREMLIN_ROLE.md both describe.",
        )
    return _result(
        False,
        f"claude_shard.py's basis has changed (imports_anthropic={imports_anthropic}, "
        f"has_random_gate={has_random}, has_keyword_markers={has_markers}) — if "
        f"imports_anthropic is now True, this subsystem may have quietly become a "
        f"real model call without the CLAUDE.md/self-model correction that requires.",
    )


def _check_claude_shard() -> dict:
    return _evaluate_claude_shard(_read_text(_CLAUDE_SHARD_PATH))


# ── 6. Question garden lineage — parent/child accumulating, not just schema ──


def _evaluate_garden_lineage(entries: list, prev_count: "int | None") -> dict:
    with_lineage = sum(1 for e in entries if e.get("children") or e.get("parent_questions"))
    if with_lineage == 0:
        return _result(
            False,
            "Zero garden entries have any parent_questions or children populated "
            f"out of {len(entries)} total — the lineage fields exist in the schema "
            "but nothing is actually using them.",
            {"with_lineage_count": 0},
        )
    delta_note = ""
    if prev_count is not None:
        delta = with_lineage - prev_count
        delta_note = f" (Δ{'+' if delta >= 0 else ''}{delta} since last check)"
    return _result(
        True,
        f"{with_lineage}/{len(entries)} garden entries have real parent/child lineage"
        f"{delta_note}.",
        {"with_lineage_count": with_lineage},
    )


def _check_garden_lineage(prev_ledger: dict) -> dict:
    entries = list(_iter_jsonl(_GARDEN_PATH))
    prev = (prev_ledger or {}).get("question_garden_lineage", {}).get("with_lineage_count")
    return _evaluate_garden_lineage(entries, prev)


# ── 7. claude_research.py — one real, confirmed API call ──────────────

_CLAUDE_RESEARCH_CURSOR = os.path.join(_MEMORY_DIR, "claude_research_cursor.json")
_CLAUDE_RESEARCH_LAST_ATTEMPT = os.path.join(_MEMORY_DIR, "claude_research_last_attempt.json")


def _evaluate_claude_research(cursor: "dict | None", last_attempt: "dict | None", window_days: int) -> dict:
    if not cursor:
        detail = "memory/claude_research_cursor.json does not exist — no successful API call has ever been recorded."
        if last_attempt:
            detail += f" Last attempt outcome: {last_attempt.get('outcome')!r}."
        return _result(False, detail, {"ever_succeeded": False})
    last_call = _parse_ts(cursor.get("last_call"))
    if last_call is None:
        return _result(False, "claude_research_cursor.json exists but last_call is unparseable — failing closed.",
                        {"ever_succeeded": True})
    age_h = (_now() - last_call) / 3600
    passed = age_h <= window_days * 24
    detail = f"Last confirmed successful claude_research.py call was {age_h:.1f}h ago (window {window_days*24}h)."
    if not passed and last_attempt:
        detail += f" Most recent attempt since then: outcome={last_attempt.get('outcome')!r}."
    return _result(passed, detail, {"ever_succeeded": True, "hours_since_last_success": round(age_h, 2)})


def _check_claude_research() -> dict:
    cursor = _read_json(_CLAUDE_RESEARCH_CURSOR)
    last_attempt = _read_json(_CLAUDE_RESEARCH_LAST_ATTEMPT)
    return _evaluate_claude_research(cursor, last_attempt, _WINDOWS_DAYS["claude_research"])


# ── 8. self_model.json — memory_health matches fresh ground truth ──────

_SELF_MODEL_PATH = os.path.join(_MEMORY_DIR, "self_model.json")
_SELF_MODEL_STALE_HOURS = 24


def _evaluate_self_model_drift(self_model: "dict | None", live_memory: dict, stale_hours: float) -> dict:
    if not self_model:
        return _result(False, "memory/self_model.json does not exist — nothing to compare.")
    last_updated = _parse_ts(self_model.get("last_updated"))
    if last_updated is None:
        return _result(False, "self_model.json has no parseable last_updated — failing closed.")
    age_h = (_now() - last_updated) / 3600
    if age_h > stale_hours:
        return _result(
            False,
            f"self_model.json was last updated {age_h:.1f}h ago (stale threshold {stale_hours}h) "
            f"— self_model_updater's background loop may have died.",
            {"age_hours": round(age_h, 2)},
        )
    reported = self_model.get("memory_health", {})
    reported_faiss = reported.get("faiss_vector_count")
    reported_journal = reported.get("journal_line_count")
    live_faiss = live_memory.get("faiss_vector_count")
    live_journal = live_memory.get("journal_line_count")
    faiss_diff = abs((reported_faiss or 0) - (live_faiss or 0))
    journal_diff = abs((reported_journal or 0) - (live_journal or 0))
    # Small tolerance for the ~2 collector cycles' worth of natural lag
    # between self_model_updater's 130s loop and introspection's 120s one,
    # not a license to silently drift.
    tolerant = faiss_diff <= max(5, 0.02 * (live_faiss or 1)) and journal_diff <= max(5, 0.02 * (live_journal or 1))
    if tolerant:
        return _result(
            True,
            f"self_model.json (updated {age_h:.1f}h ago) reports faiss={reported_faiss} "
            f"journal={reported_journal}, matching live faiss={live_faiss} journal={live_journal}.",
            {"age_hours": round(age_h, 2)},
        )
    return _result(
        False,
        f"self_model.json reports faiss={reported_faiss} journal={reported_journal} but live "
        f"ground truth is faiss={live_faiss} journal={live_journal} — self-reported memory_health "
        f"has drifted from reality, the same class of gap this project has already found once.",
        {"age_hours": round(age_h, 2), "faiss_diff": faiss_diff, "journal_diff": journal_diff},
    )


def _check_self_model_drift(live_memory: dict) -> dict:
    self_model = _read_json(_SELF_MODEL_PATH)
    return _evaluate_self_model_drift(self_model, live_memory or {}, _SELF_MODEL_STALE_HOURS)


# ── 9. task_type_classifier.py — bootstrap/learn still gated by the filter ──


def _evaluate_task_type_classifier(filter_fn) -> dict:
    """Functional canary, not an import check: feed the real
    is_trustworthy_training_example() function known-contaminated and
    known-clean synthetic inputs (the same shapes the audit found actually
    contaminating this classifier before the filter existed) and confirm
    it still discriminates. This is what verify_integrity() elsewhere in
    this codebase does NOT do (importability only) — the exact gap
    GREMLIN_ROLE.md names."""
    if filter_fn is None:
        return _result(False, "Could not import is_trustworthy_training_example at all — failing closed.")
    cases = [
        (("fix this typo", "coding", "user_conversation"), True),
        (("STRICT OUTPUT RULES — violations cause system failure", "coding", "autonomous"), False),
        (("[SANDBOX]", "coding", "user_conversation"), False),
        (("hello", "personal", "autonomous"), False),
        (("x" * 600, "personal", "user_conversation"), False),
    ]
    failures = []
    for (prompt, task_type, source), expected in cases:
        try:
            actual = filter_fn(prompt, task_type, source)
        except Exception as e:
            failures.append(f"raised {e!r} on {(prompt[:30], task_type, source)}")
            continue
        if bool(actual) != expected:
            failures.append(f"expected {expected} got {actual} on {(prompt[:30], task_type, source)}")
    if not failures:
        return _result(
            True,
            f"is_trustworthy_training_example() correctly discriminated all "
            f"{len(cases)} canary cases (contaminated autonomous/placeholder/oversized "
            f"examples rejected, genuine user_conversation examples accepted).",
        )
    return _result(
        False,
        "is_trustworthy_training_example() failed canary cases: " + "; ".join(failures) +
        " — unfiltered bootstrap data may be reaching the classifier again.",
    )


def _check_task_type_classifier() -> dict:
    try:
        from app.core.task_type_classifier import is_trustworthy_training_example as filter_fn
    except Exception:
        filter_fn = None
    return _evaluate_task_type_classifier(filter_fn)


# ── Orchestration ──────────────────────────────────────────────────────

_CHECKS = (
    "self_edit_apply_to_code",
    "curiosity_engine",
    "nature_spark",
    "wolf_friction_bridge",
    "claude_shard",
    "question_garden_lineage",
    "claude_research",
    "self_model_drift",
    "task_type_classifier",
)


def _load_prev_ledger() -> dict:
    return _read_json(LEDGER_PATH, default={}) or {}


def run_liveness_checks(introspection_memory: "dict | None" = None) -> dict:
    """
    Run all nine liveness checks and write memory/liveness_ledger.json.
    introspection_memory: the already-computed state["memory"] dict from
    this same introspection cycle (faiss_vector_count/journal_line_count),
    reused rather than re-read so self_model_drift compares against the
    exact same ground-truth reading the rest of this cycle is using.

    Every check is independently fault-isolated — one raising does not
    prevent the others from running or from being written to the ledger,
    matching every other collector in this codebase.
    """
    prev_ledger = _load_prev_ledger()
    live_memory = introspection_memory or {}

    runners = {
        "self_edit_apply_to_code": _check_apply_to_code,
        "curiosity_engine": _check_curiosity_engine,
        "nature_spark": _check_nature_spark,
        "wolf_friction_bridge": _check_wolf_friction_bridge,
        "claude_shard": _check_claude_shard,
        "question_garden_lineage": lambda: _check_garden_lineage(prev_ledger),
        "claude_research": _check_claude_research,
        "self_model_drift": lambda: _check_self_model_drift(live_memory),
        "task_type_classifier": _check_task_type_classifier,
    }

    ledger = {"generated_at": _now_iso()}
    for name in _CHECKS:
        try:
            entry = runners[name]()
        except Exception as e:
            entry = _result(False, f"Check itself raised: {e!r} — failing closed.")
            logger.warning("[LIVENESS-ALERT] subsystem=%s check_crashed error=%s", name, e)
        entry["window_days"] = _WINDOWS_DAYS.get(name)
        ledger[name] = entry
        prior = prev_ledger.get(name)
        was_passing = prior.get("pass") if isinstance(prior, dict) else None
        if not entry["pass"]:
            logger.warning(
                "[LIVENESS-ALERT] subsystem=%s FAILING | %s",
                name, entry["evidence"],
            )
        elif was_passing is False:
            logger.info("[LIVENESS] subsystem=%s recovered | %s", name, entry["evidence"])

    _write(ledger)
    return ledger


def _write(ledger: dict) -> None:
    tmp = LEDGER_PATH + ".tmp"
    try:
        os.makedirs(_MEMORY_DIR, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2, default=str)
        os.replace(tmp, LEDGER_PATH)
    except Exception as e:
        logger.warning("[LIVENESS] Ledger write failed: %s", e)
        try:
            os.unlink(tmp)
        except Exception:
            pass


def get_liveness_status() -> dict:
    """
    Read-only accessor for the /admin/liveness-status endpoint — does not
    recompute, just reads the last-written ledger and adds a top-level
    staleness verdict (has the collector thread itself died?).
    """
    ledger = _read_json(LEDGER_PATH)
    if not ledger:
        return {
            "ledger_exists": False,
            "stale": True,
            "note": "No liveness_ledger.json yet — introspection_channel has not completed a cycle.",
        }
    generated_at = _parse_ts(ledger.get("generated_at")) or 0
    age_s = _now() - generated_at
    stale = age_s > LEDGER_STALE_AFTER_SECONDS
    failing = [name for name in _CHECKS if not (ledger.get(name) or {}).get("pass", False)]
    out = dict(ledger)
    out["ledger_exists"] = True
    out["stale"] = stale
    out["age_seconds"] = round(age_s, 1)
    out["failing_subsystems"] = failing
    out["all_passing"] = not failing and not stale
    if stale:
        logger.warning(
            "[LIVENESS-ALERT] ledger itself is stale (age=%.0fs > %ds) — "
            "introspection_channel's collector loop may have died.",
            age_s, LEDGER_STALE_AFTER_SECONDS,
        )
    return out
