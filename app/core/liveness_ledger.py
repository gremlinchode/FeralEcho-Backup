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
#   - This is a floor, not a general test framework: 14 named checks for
#     14 subsystems that have already fooled a prior audit, fix, or session
#     by looking wired while being dead or fake. The original nine were the
#     initial build; global_workspace, substrate_continuity,
#     global_workspace_consumption, valence_self_report, and
#     reflection_shard_generation were each added afterward, per the
#     extension rule stated here — most recently 2026-07-16, Emergence
#     roadmap Phase 5/6. Adding a check for a new autonomous capability is a
#     small, mechanical extension of this same pattern, not a redesign.
#     (This count drifts every time a check is added — verify against the
#     real length of _CHECKS below before trusting this comment's number.)
# ============================================================

import ast
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

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
    "global_workspace": 1,
    "substrate_continuity": None,  # sample-size-windowed (last 2000 entries), not time-windowed
    "global_workspace_consumption": 1,
    "valence_self_report": None,  # point-in-time consistency check, not time-windowed
    "reflection_shard_generation": 1,
    "dissent_log_hook": None,  # static source-invariant, same shape as wolf_friction_bridge
    "seam_engine": None,  # functional canary, not time-windowed — same shape as task_type_classifier
    "code_verification": None,  # functional canary, not time-windowed
    "self_knowledge_verification": None,  # functional canary, not time-windowed
    "echo_projects_isolation": None,  # static source-invariant, same shape as wolf_friction_bridge
    "echo_projects_no_escalation": None,  # static source-invariant, same shape as dissent_log_hook
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


_APPLY_TO_CODE_RECENT_N = 20  # how many of the most recent invocations to weigh for error rate


def _evaluate_apply_to_code(defines_hook: bool, invocations: list, window_days: int) -> dict:
    if not defines_hook:
        return _result(
            True,
            "self_edit_generated.py does not currently define apply_to_code — "
            "hook is honestly inert, nothing claims it is live.",
            {"status": "not_deployed"},
        )
    if not invocations:
        return _result(
            False,
            "apply_to_code IS defined in the deployed self_edit_generated.py, but "
            "zero invocations have ever been logged — deployed but dead.",
            {"status": "deployed_but_dead"},
        )

    # Recent-error-rate check (added 2026-07-15, Finding 28): the original
    # version of this evaluator only asked "did ANY invocation succeed within
    # window_days" — which kept reporting pass:true while 253 of the last 254
    # real invocations were raising a NameError, because one stale success
    # (itself a destructive 2173->47 char truncation, not a real improvement)
    # sat inside the 7-day window. Weighing the most recent invocations catches
    # a hook that used to work and no longer does, not just one that never
    # worked at all — a ground-truth check can still mislead if its evaluation
    # criteria are too coarse, even when every piece of evidence it reads is
    # genuine.
    recent = sorted(invocations, key=lambda e: _parse_ts(e.get("ts")) or 0, reverse=True)[:_APPLY_TO_CODE_RECENT_N]
    error_count = sum(1 for e in recent if e.get("error"))
    error_rate = error_count / len(recent) if recent else 0.0
    if error_rate > 0.5:
        last = recent[0]
        return _result(
            False,
            f"apply_to_code is deployed but erroring on most recent invocations: "
            f"{error_count}/{len(recent)} of the last {len(recent)} logged calls raised "
            f"an error (most recent: {last.get('error')!r} at {last.get('ts')}) — "
            f"deployed but broken, regardless of any older success in the {window_days}d window.",
            {"status": "deployed_but_erroring", "recent_error_rate": round(error_rate, 3)},
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
            f"{last.get('ts')} ({last.get('before_len')}→{last.get('after_len')} chars); "
            f"recent error rate {error_count}/{len(recent)}.",
            {"status": "deployed_and_live", "recent_count": len(recent_changed)},
        )
    return _result(
        False,
        f"apply_to_code IS defined in the deployed self_edit_generated.py, and recent "
        f"calls aren't erroring, but no invocation actually changed the generated code "
        f"in the last {window_days}d (checked {len(invocations)} logged invocation(s) "
        f"total) — deployed but dead.",
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
_SELF_EDIT_MANAGER_PATH = os.path.join(_PROJECT_ROOT, "app", "core", "self_edit_manager.py")


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


# ── Dissent log hook (2026-07-17) ───────────────────────────────────────
# "does propose_core_edit() still actually call the dissent-logging step?"
# Same static/structural shape as wolf_friction_bridge above — this fires
# only via a human-run !propose command, never an autonomous loop, so
# there's no meaningful recency window to check, only whether the hook
# itself is still wired.

def _evaluate_dissent_log_hook(call_site_block: "str | None") -> dict:
    if call_site_block is None:
        return _result(
            False,
            "Could not locate propose_core_edit()'s dissent-logging call site in "
            "self_edit_manager.py at all — either it moved (update this check's "
            "anchor) or the hook was removed. Failing closed either way.",
        )
    calls_log = bool(re.search(r"_log_dissent_entry\s*\(", call_site_block))
    calls_build = bool(re.search(r"_build_dissent_entry\s*\(", call_site_block))
    if calls_build and calls_log:
        return _result(
            True,
            "propose_core_edit() still calls _build_dissent_entry() and "
            "_log_dissent_entry() — genuine council disagreement is still being "
            "persisted and surfaced, not silently discarded.",
        )
    return _result(
        False,
        f"propose_core_edit() no longer calls the dissent-logging hook as expected "
        f"(calls_build={calls_build}, calls_log={calls_log}) — a future edit may "
        f"have silently removed it.",
    )


def _check_dissent_log_hook() -> dict:
    source = _read_text(_SELF_EDIT_MANAGER_PATH)
    block = None
    idx = source.find("def propose_core_edit(")
    if idx != -1:
        # A generous window covering the whole function body — it's long
        # (roughly 100 lines), and the dissent-logging call sits at the very
        # end of it, well past what a smaller window like wolf_friction_
        # bridge's 800 chars would reach.
        block = source[idx:idx + 6000]
    return _evaluate_dissent_log_hook(block)


# ── reflection_meta_synthesis_hook — reflection_shard.py's ────────────────
# _generate_meta_reflection() still publishes its real, model-generated
# synthesis onto the Global Workspace, not just its own journal. Same
# static/source-anchor shape as dissent_log_hook/wolf_friction_bridge, since
# this fires from an internal autonomous cadence, not something a live
# functional canary can cheaply exercise the same way seam_engine's can.
# Added 2026-07-23 (CLAUDE.md Finding 77, gap-closure plan Phase B item 2)
# alongside the publish call itself.

_REFLECTION_SHARD_SRC_PATH = os.path.join(_PROJECT_ROOT, "app", "subsystems", "reflection_shard.py")


def _evaluate_reflection_meta_synthesis_hook(call_site_block: "str | None") -> dict:
    if call_site_block is None:
        return _result(
            False,
            "Could not locate _generate_meta_reflection() in reflection_shard.py at "
            "all — either it moved (update this check's anchor) or the function was "
            "removed. Failing closed either way.",
        )
    calls_publish = bool(re.search(r"publish_salience\s*\(", call_site_block))
    correct_kind = bool(re.search(r"kind\s*=\s*[\"']reflection\.meta_synthesis[\"']", call_site_block))
    if calls_publish and correct_kind:
        return _result(
            True,
            "_generate_meta_reflection() still calls publish_salience(kind="
            "'reflection.meta_synthesis', ...) — the real synthesis still reaches "
            "the Global Workspace, not just its own journal.",
        )
    return _result(
        False,
        f"_generate_meta_reflection() no longer publishes its synthesis onto the "
        f"Global Workspace as expected (calls_publish={calls_publish}, "
        f"correct_kind={correct_kind}) — a future edit may have silently removed it.",
    )


def _evaluate_valence_exploration_bias(apply_fn) -> dict:
    """Functional canary: river_deliberation.py's _apply_valence_to_
    exploration_bias() must stay a valid probability [0,1] for any real
    valence value, since the result feeds a random.random() < x Bernoulli
    gate directly. Added 2026-07-23 (gap-closure plan Phase C2a)."""
    if apply_fn is None:
        return _result(False, "Could not import _apply_valence_to_exploration_bias at all — failing closed.")

    cases = [(0.0, -1.0), (0.0, 1.0), (1.0, -1.0), (1.0, 1.0), (0.5, 0.0), (0.02, 0.18)]
    failures = []
    for eb, valence in cases:
        try:
            result = apply_fn(eb, valence)
        except Exception as e:
            failures.append(f"eb={eb} valence={valence} raised {e!r}")
            continue
        if not (0.0 <= result <= 1.0):
            failures.append(f"eb={eb} valence={valence} produced out-of-bounds result={result}")
    if failures:
        return _result(False, "_apply_valence_to_exploration_bias() failed bounds cases: " + "; ".join(failures))
    return _result(
        True,
        "_apply_valence_to_exploration_bias() stays within [0,1] across extreme "
        "valence/exploration_bias inputs.",
    )


def _check_valence_exploration_bias() -> dict:
    try:
        from app.core.river_deliberation import _apply_valence_to_exploration_bias
    except Exception:
        _apply_valence_to_exploration_bias = None
    return _evaluate_valence_exploration_bias(_apply_valence_to_exploration_bias)


# ── valence_self_edit_bounds — echo_optuna.py's _valence_adjusted_bounds() ──
# stays within valid [0,1] bounds for any real valence, AND objective()
# still only ever calls the self-edit pipeline with dry_run=True, never
# save_code() — the safety invariant this whole modulation depends on
# (valence may shift which parameter region a *trial* explores, but must
# never be able to reach a real production write). Added 2026-07-23
# (gap-closure plan Phase C2b), same combined bounds+structural shape as
# apply_to_code_sandbox_isolation's own boundary-holds pattern.

def _evaluate_valence_self_edit_bounds(bounds_fn, objective_source_block: "str | None") -> dict:
    if bounds_fn is None:
        return _result(False, "Could not import _valence_adjusted_bounds at all — failing closed.")

    failures = []
    for v in (-1.0, -0.5, 0.0, 0.18, 0.5, 1.0):
        try:
            low, high = bounds_fn(v)
        except Exception as e:
            failures.append(f"valence={v} raised {e!r}")
            continue
        if not (0.0 <= low < high <= 1.0):
            failures.append(f"valence={v} produced invalid bounds ({low}, {high})")
    if failures:
        return _result(False, "_valence_adjusted_bounds() failed bounds cases: " + "; ".join(failures))

    if objective_source_block is None:
        return _result(
            False,
            "Could not locate EchoOptuna.objective()'s source at all — either it "
            "moved (update this check's anchor) or the function was removed. "
            "Failing closed either way.",
        )
    calls_dry_run_true = bool(re.search(r"dry_run\s*=\s*True", objective_source_block))
    calls_save_code = bool(re.search(r"save_code\s*\(", objective_source_block))
    if calls_dry_run_true and not calls_save_code:
        return _result(
            True,
            "_valence_adjusted_bounds() stays within valid bounds, and objective() "
            "still only ever calls the self-edit pipeline with dry_run=True — "
            "valence's modulation never reaches a real production write.",
        )
    return _result(
        False,
        f"objective() no longer matches its expected dry-run-only shape "
        f"(calls_dry_run_true={calls_dry_run_true}, calls_save_code={calls_save_code}) "
        f"— valence's modulation may now be able to influence a real deployment.",
    )


def _check_valence_self_edit_bounds() -> dict:
    try:
        from app.core.echo_optuna import _valence_adjusted_bounds
    except Exception:
        _valence_adjusted_bounds = None
    source = _read_text(os.path.join(_PROJECT_ROOT, "app", "core", "echo_optuna.py"))
    block = None
    idx = source.find("def objective(trial")
    if idx != -1:
        # Real measured length is 3525 chars -- widened with real margin,
        # not just guessed, per the lesson from reflection_meta_synthesis_
        # hook's own window-too-small bug earlier this session.
        block = source[idx:idx + 4500]
    return _evaluate_valence_self_edit_bounds(_valence_adjusted_bounds, block)


def _check_reflection_meta_synthesis_hook() -> dict:
    source = _read_text(_REFLECTION_SHARD_SRC_PATH)
    block = None
    idx = source.find("def _generate_meta_reflection(")
    if idx != -1:
        # Real live check found the publish call sitting ~2987 chars into
        # the function body — a 3000-char window cut it off mid-line.
        # Widened with real margin, not just bumped by a token.
        block = source[idx:idx + 6000]
    return _evaluate_reflection_meta_synthesis_hook(block)


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
    # Asymmetric tolerance, absorbed from self_report_verifier.py's
    # verify_memory_health() (2026-07-13 consolidation — that module ran
    # nearly the identical check on its own 60s cadence via dmn_guardian.py;
    # retired in favor of this one, but its better-reasoned tolerances were
    # kept rather than this check's original flat 2%-of-current-value rule
    # for both fields). faiss and journal have very different natural
    # growth rates — confirmed live: FAISS can grow by hundreds of vectors
    # in the couple of minutes between self_model_updater refresh cycles
    # from autonomous loops constantly writing memory, while journal growth
    # tracks much slower real journaling activity. A single flat tolerance
    # either fires constantly on FAISS's expected drift or is too loose for
    # the journal. faiss keeps a relative (5%, floor 50) tolerance for this
    # reason; journal uses a tight absolute one (5 lines) since any real
    # gap there likely means a genuine bug — the original motivating case
    # for this whole check was exactly a journal-count bug (introspection
    # reading the wrong file), not benign lag.
    tolerant = (
        faiss_diff <= max(50, 0.05 * (reported_faiss or 0))
        and journal_diff <= 5
    )
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


# ── 10. Global Workspace — genuine multi-subsystem integration, not one ──
# publisher talking to itself (Emergence roadmap Phase 2a). EchoCoreBus's
# publish()/subscribe() were 100% dormant before this — zero callers
# anywhere outside echo_core.py itself. The point of a Global Workspace
# (GWT) is specifically that multiple otherwise-encapsulated processes'
# output becomes available together — so "some events exist" is a much
# weaker and less honest claim than "events from more than one real
# subsystem exist," which is what this check actually verifies.

_WORKSPACE_LOG = os.path.join(_MEMORY_DIR, "workspace_log.jsonl")
_GLOBAL_WORKSPACE_TAIL_N = 100
_GLOBAL_WORKSPACE_MIN_DISTINCT_SOURCES = 2


def _evaluate_global_workspace(entries: list, window_days: float, tail_n: int, min_sources: int) -> dict:
    if not entries:
        return _result(
            False,
            "memory/workspace_log.jsonl has no entries — the workspace has never carried "
            "a single event.",
            {"distinct_sources": 0},
        )
    cutoff = _now() - window_days * 86400
    recent = [
        e for e in entries[-tail_n:]
        if (_parse_ts(e.get("ts")) or 0) >= cutoff
    ]
    if not recent:
        return _result(
            False,
            f"workspace_log.jsonl has {len(entries)} entries all-time, but none in the "
            f"last {window_days}d — the workspace may have gone quiet.",
            {"distinct_sources": 0},
        )
    sources = {e.get("source") for e in recent if e.get("source")}
    if len(sources) >= min_sources:
        return _result(
            True,
            f"{len(recent)} event(s) in the last {window_days}d from {len(sources)} "
            f"distinct source(s): {sorted(sources)} — genuine multi-subsystem integration, "
            f"not one publisher talking to itself.",
            {"distinct_sources": len(sources), "recent_count": len(recent)},
        )
    return _result(
        False,
        f"{len(recent)} event(s) in the last {window_days}d, but from only "
        f"{len(sources)} distinct source(s) ({sorted(sources)}) — needs >= {min_sources} "
        f"to count as genuine integration rather than one lonely publisher.",
        {"distinct_sources": len(sources), "recent_count": len(recent)},
    )


def _check_global_workspace() -> dict:
    entries = list(_iter_jsonl(_WORKSPACE_LOG))
    return _evaluate_global_workspace(
        entries, _WINDOWS_DAYS["global_workspace"],
        _GLOBAL_WORKSPACE_TAIL_N, _GLOBAL_WORKSPACE_MIN_DISTINCT_SOURCES,
    )


# ── 10b. Global Workspace CONSUMPTION — Emergence roadmap Phase 4 ────────
# _check_global_workspace() above proves genuine multi-source BROADCAST —
# publishers exist and are diverse. It says nothing about whether anything
# downstream actually listens and changes behavior; before Phase 4 that
# was true of literally everything on the bus (the only subscriber was a
# pure logger). This is a separate, new check rather than folding into the
# existing one, same reasoning this project already applied when adding
# substrate_continuity alongside global_workspace itself: broadening an
# existing check's semantics silently would invalidate its own
# discrimination-suite history. Consumers publish "workspace.consumed"
# themselves at the moment they actually apply a broadcast bias (see
# memory_bridge.retrieve_relevant_memories(), river_deliberation's cached
# exploration_bias, emergent_scheduler's curiosity topic_bias) — so this
# reads the exact same ground-truth log the broadcast check does, not a
# separate self-report channel.
#
# min_sources=1 (not 2, unlike the broadcast check): unlike publish
# diversity Phase 2a could engineer immediately across 3 files in one
# pass, real consumption events are gated on natural triggers this project
# doesn't control the cadence of (a dream cycle, a genuinely elevated
# WorldModel surprise reading, a non-convergent self-edit streak) — so a
# single genuine consumption event is real evidence the wiring works, even
# before enough time has passed to see all three consumers fire. Worth
# raising to >=2 once real cadence data exists to judge that threshold
# against, the same kind of judgment call apply_to_code's hardening
# (Finding 28/31) was based on real invocation data rather than guessed
# upfront.

_GLOBAL_WORKSPACE_CONSUMPTION_TAIL_N = 200
_GLOBAL_WORKSPACE_CONSUMPTION_MIN_SOURCES = 1


def _evaluate_global_workspace_consumption(entries: list, window_days: float, tail_n: int, min_sources: int) -> dict:
    if not entries:
        return _result(
            False,
            "memory/workspace_log.jsonl has no entries — no consumption evidence possible.",
            {"distinct_consumers": 0},
        )
    cutoff = _now() - window_days * 86400
    recent = [
        e for e in entries[-tail_n:]
        if e.get("type") == "workspace.consumed" and (_parse_ts(e.get("ts")) or 0) >= cutoff
    ]
    consumers = {e.get("source") for e in recent if e.get("source")}
    if len(consumers) >= min_sources:
        return _result(
            True,
            f"{len(recent)} workspace.consumed event(s) in the last {window_days}d from "
            f"{len(consumers)} real consumer(s): {sorted(consumers)} — the workspace is "
            f"genuinely being read and acted on, not just broadcast into a log file.",
            {"distinct_consumers": len(consumers), "recent_count": len(recent)},
        )
    return _result(
        False,
        f"No workspace.consumed events from a real consumer in the last {window_days}d "
        f"(found {len(recent)} from {sorted(consumers)}) — broadcast may still be reaching "
        f"zero downstream consumers, the exact gap this check exists to catch.",
        {"distinct_consumers": len(consumers), "recent_count": len(recent)},
    )


def _check_global_workspace_consumption() -> dict:
    entries = list(_iter_jsonl(_WORKSPACE_LOG))
    return _evaluate_global_workspace_consumption(
        entries, _WINDOWS_DAYS["global_workspace_consumption"],
        _GLOBAL_WORKSPACE_CONSUMPTION_TAIL_N, _GLOBAL_WORKSPACE_CONSUMPTION_MIN_SOURCES,
    )


# ── 11. Substrate continuity — Emergence roadmap Phase 3 ────────────────
# Downgraded from a planned new integrator to verification-only during
# planning: the original concern (a real incident on the Ark machine,
# ECHO_SYNTHESIS_MODEL_OVERRIDE landing a low-capability model in the
# synthesis role) doesn't apply here — no such override mechanism exists
# in this codebase. Confirmed against 2000 real interaction_log entries
# before writing this check: 100% of genuine conversational entries were
# already echo:latest. This check exists to catch FUTURE drift (e.g. if an
# override is ever added), not a problem known to exist today.

_INTERACTION_LOG = os.path.join(_MEMORY_DIR, "interaction_log.jsonl")
_SUBSTRATE_TAIL_N = 2000
_SUBSTRATE_MIN_RATIO = 0.95


def _evaluate_substrate_continuity(entries: list, synth_model: "str | None", tail_n: int, min_ratio: float) -> dict:
    if synth_model is None:
        return _result(False, "Could not import ECHO_SYNTHESIS_MODEL from river_deliberation.py — check inconclusive, failing closed.")
    if not entries:
        return _result(False, "memory/interaction_log.jsonl has no entries — no evidence of conversational activity.")

    # Excludes self-edit code-generation (a genuinely different subsystem —
    # tagged notes="sandbox_feedback", uses task-appropriate coding models
    # by design, not a synthesis-continuity concern) and non-model
    # subsystem log-tags (autonomous_fetch, experiment_runner, etc. — real
    # Ollama/MLX model names always contain ":" in this codebase's
    # convention, e.g. "echo:latest", "qwen2.5-coder:7b"; subsystem tags
    # never do).
    relevant = [
        e for e in entries[-tail_n:]
        if "sandbox" not in str(e.get("notes", "")).lower() and ":" in str(e.get("model", ""))
    ]
    if not relevant:
        return _result(False, "No genuine conversational (non-sandbox, real-model-tagged) entries found in the recent window — check inconclusive.")

    matching = sum(1 for e in relevant if e.get("model") == synth_model)
    ratio = matching / len(relevant)
    if ratio >= min_ratio:
        return _result(
            True,
            f"{matching}/{len(relevant)} ({ratio*100:.1f}%) of recent genuine conversational "
            f"entries used {synth_model!r} — substrate continuity holds.",
            {"ratio": round(ratio, 4), "sample_size": len(relevant)},
        )
    return _result(
        False,
        f"Only {matching}/{len(relevant)} ({ratio*100:.1f}%) of recent genuine conversational "
        f"entries used {synth_model!r} (need >= {min_ratio*100:.0f}%) — synthesis substrate may "
        f"be drifting across different models.",
        {"ratio": round(ratio, 4), "sample_size": len(relevant)},
    )


def _check_substrate_continuity() -> dict:
    try:
        from app.core.river_deliberation import ECHO_SYNTHESIS_MODEL as synth_model
    except Exception:
        synth_model = None
    entries = list(_iter_jsonl(_INTERACTION_LOG))
    return _evaluate_substrate_continuity(entries, synth_model, _SUBSTRATE_TAIL_N, _SUBSTRATE_MIN_RATIO)


# ── 13. Valence self-report — rendered affect text matches real dim[8] sign ──
# Emergence roadmap Phase 5, Finding 1: echo_ground_truth.py's _build_affect()
# now surfaces echo_state.py's real signed valence dimension (dim[8]) in
# prompts answering "how are you feeling." This check verifies the rendered
# text's own directional language ("positive"/"negative"/"neutral") actually
# matches the real sign of dim[8] at the same moment a fresh read produces —
# the same discipline self_model_drift already applies to memory_health, so a
# future prompt-assembly edit can't quietly start confabulating mood instead
# of reporting it.

_VALENCE_NEUTRAL_BAND = 0.15


def _evaluate_valence_self_report(dim8_value: "float | None", rendered_text: str) -> dict:
    if dim8_value is None:
        return _result(
            False,
            "echo_state.npy could not be read — no ground truth available to check "
            "the rendered affect text against. Failing closed.",
        )
    if not rendered_text:
        return _result(False, "_build_affect() returned no text at all — the slice may be broken.")

    says_positive = "positive" in rendered_text
    says_negative = "negative" in rendered_text
    says_neutral = "neutral" in rendered_text

    if dim8_value > _VALENCE_NEUTRAL_BAND:
        matches = says_positive and not says_negative
    elif dim8_value < -_VALENCE_NEUTRAL_BAND:
        matches = says_negative and not says_positive
    else:
        matches = says_neutral or (not says_positive and not says_negative)

    if matches:
        return _result(
            True,
            f"Rendered affect text's directional language matches real dim[8]={dim8_value:+.3f}.",
            {"dim8_value": round(dim8_value, 4)},
        )
    return _result(
        False,
        f"Rendered affect text does not match real dim[8]={dim8_value:+.3f} "
        f"(rendered: {rendered_text[:200]!r}) — self-report may be confabulating a "
        f"mood the real signal doesn't support.",
        {"dim8_value": round(dim8_value, 4)},
    )


def _check_valence_self_report() -> dict:
    try:
        from app.core import echo_state
        from app.core.echo_ground_truth import _build_affect
    except Exception as e:
        return _result(False, f"Could not import echo_state/_build_affect: {e!r} — failing closed.")
    vec = echo_state.load()
    dim8_value = float(vec[8]) if vec is not None else None
    self_model = _read_json(_SELF_MODEL_PATH)
    rendered_text = _build_affect(self_model or {})
    return _evaluate_valence_self_report(dim8_value, rendered_text)


# ── coupling_self_report — echo_ground_truth.py's _build_coupling() slice's ──
# rendered bucket ("loosely"/"moderately"/"notably" coupled) actually matches
# the real persisted coupling_estimate value's magnitude. Same discrimination
# shape as valence_self_report, added 2026-07-23 alongside the slice itself
# (CLAUDE.md Finding 77, gap-closure plan Phase B item 1) — coupling_estimate
# had zero real consumer anywhere before this; this check exists so a future
# edit can't silently make the rendered text stop matching the real value the
# same way a confabulated valence self-report would.

_COUPLING_LOOSE_BOUND = 0.15
_COUPLING_MODERATE_BOUND = 0.4

def _evaluate_coupling_self_report(coupling_value: "float | None", rendered_text: str) -> dict:
    if not rendered_text:
        return _result(False, "_build_coupling() returned no text at all — the slice may be broken.")

    if coupling_value is None:
        # A genuinely absent value is a real, honest state (not enough
        # history yet) -- correct behavior is the text saying so, not a
        # confabulated bucket.
        if "not enough recent history" in rendered_text.lower() or "no signal available" in rendered_text.lower():
            return _result(
                True,
                "coupling_estimate is genuinely unavailable and _build_coupling() "
                "correctly reports that rather than confabulating a bucket.",
            )
        return _result(
            False,
            "coupling_estimate is unavailable, but _build_coupling() rendered a "
            f"reading anyway instead of saying so: {rendered_text[:200]!r}",
        )

    says_loose = "loosely coupled" in rendered_text
    says_moderate = "moderately coupled" in rendered_text
    says_notable = "notably coupled" in rendered_text

    if coupling_value < _COUPLING_LOOSE_BOUND:
        matches = says_loose and not says_moderate and not says_notable
    elif coupling_value < _COUPLING_MODERATE_BOUND:
        matches = says_moderate and not says_loose and not says_notable
    else:
        matches = says_notable and not says_loose and not says_moderate

    if matches:
        return _result(
            True,
            f"Rendered coupling text's bucket matches real coupling_estimate={coupling_value:.4f}.",
            {"coupling_value": round(coupling_value, 4)},
        )
    return _result(
        False,
        f"Rendered coupling text does not match real coupling_estimate={coupling_value:.4f} "
        f"(rendered: {rendered_text[:200]!r}) — self-report may be confabulating an "
        f"integration reading the real signal doesn't support.",
        {"coupling_value": round(coupling_value, 4)},
    )


def _check_coupling_self_report() -> dict:
    try:
        from app.core.echo_ground_truth import _build_coupling
    except Exception as e:
        return _result(False, f"Could not import _build_coupling: {e!r} — failing closed.")
    state = _read_json(os.path.join("memory", "salience_state.json"))
    coupling_value = state.get("coupling_estimate") if state else None
    coupling_value = float(coupling_value) if coupling_value is not None else None
    rendered_text = _build_coupling()
    return _evaluate_coupling_self_report(coupling_value, rendered_text)


# ── 14. reflection_shard_generation — real text, not templates ──────────
# Emergence roadmap Phase 5, Finding 2: reflection_shard.py's _generate_
# reflection()/_generate_meta_reflection() now route through a real model
# call, mirroring nature_spark's own discrimination shape — recent
# reflection_journal.jsonl entries should NOT be near-duplicates of the
# three retired fixed templates, the old verbatim cosine-similarity quoting
# shape, or the old fixed "<<emergent-pattern>>" meta fallback string. Any
# of those firing means the model call is silently failing and this loop
# has fallen back to its pre-fix behavior, the same class of gap
# nature_spark's own check exists to catch.

_REFLECTION_JOURNAL = os.path.join(_MEMORY_DIR, "reflection_journal.jsonl")
_REFLECTION_SHARD_TAIL_N = 20
_REFLECTION_SHARD_MIN_DISTINCT_RATIO = 0.5

_REFLECTION_FALLBACK_PATTERNS = [
    re.compile(r"^I notice the signal '.*'—why does it matter to me\?$"),
    re.compile(r"^The input '.*' ripples like a stone in water—what echoes will it make\?$"),
    re.compile(r"^I observe myself responding to '.*' in silent wonder\.$"),
    re.compile(r"^Signal '.*' triggers these echoes: .*$"),
    re.compile(r"^<<emergent-pattern>> In the last \d+ signals"),
]

# 2026-07-23 fix (CLAUDE.md Finding 77, gap-closure plan Phase B item 3):
# the fixed-template test above only catches reversion to the three RETIRED
# pre-fix shapes -- the physiology audit (audits/2026-07-23_systems_
# physiology_audit.md §6) found this check reported 0% duplication on the
# last 20 real reflections while direct pairwise Jaccard similarity on the
# identical 20 entries found 15% near-duplicates (several at Jaccard=1.0).
# The check wasn't lying about what it measured -- it was measuring the
# wrong failure mode now that a live model can repeat ITSELF in new,
# non-template ways. Added as a second, independent signal rather than a
# replacement -- both failure modes are real and distinct.
_REFLECTION_SHARD_DUPLICATE_JACCARD = 0.5


def _jaccard_similarity(a: str, b: str) -> float:
    wa, wb = set(a.lower().split()), set(b.lower().split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _evaluate_reflection_shard_generation(reflections: list, tail_n: int, min_ratio: float) -> dict:
    if not reflections:
        return _result(False, "memory/reflection_journal.jsonl has no entries — no evidence of activity.",
                        {"distinct_ratio": 0.0})
    tail = reflections[-tail_n:]
    n = len(tail)
    fallback_flags = [any(p.search(text) for p in _REFLECTION_FALLBACK_PATTERNS) for text in tail]

    duplicate_flags = [False] * n
    for i in range(n):
        for j in range(i + 1, n):
            if _jaccard_similarity(tail[i], tail[j]) >= _REFLECTION_SHARD_DUPLICATE_JACCARD:
                duplicate_flags[i] = True
                duplicate_flags[j] = True

    non_distinct = sum(1 for i in range(n) if fallback_flags[i] or duplicate_flags[i])
    distinct = n - non_distinct
    ratio = distinct / n
    passed = ratio >= min_ratio
    fallback_count = sum(fallback_flags)
    duplicate_count = sum(duplicate_flags)
    detail = (
        f"{distinct}/{n} of the last {n} reflection_journal.jsonl entries are genuinely "
        f"distinct ({fallback_count}/{n} match the retired fixed-template/verbatim-quote "
        f"shapes, {duplicate_count}/{n} are near-duplicates of another entry in this same "
        f"window by pairwise Jaccard similarity >= {_REFLECTION_SHARD_DUPLICATE_JACCARD})."
    )
    if not passed:
        detail += (
            " This means reflection_shard is either falling back to its pre-fix "
            "template/similarity-quoting behavior, or the live model is repeating "
            "itself in new ways this check now also catches."
        )
    return _result(passed, detail, {
        "distinct_ratio": round(ratio, 3),
        "fallback_count": fallback_count,
        "duplicate_count": duplicate_count,
        "distinct_count": distinct,
    })


def _check_reflection_shard_generation() -> dict:
    entries = list(_iter_jsonl(_REFLECTION_JOURNAL))
    reflections = [e.get("reflection", "") for e in entries if e.get("reflection")]
    return _evaluate_reflection_shard_generation(
        reflections, _REFLECTION_SHARD_TAIL_N, _REFLECTION_SHARD_MIN_DISTINCT_RATIO,
    )


# ── 16. seam_engine.py — check_pair() still genuinely discriminates ─────
# a real contradiction from an unusual-but-consistent reading and from an
# uncorrelated pair, rather than silently degrading into flagging every
# cycle or never again. Same functional-canary shape as
# task_type_classifier's check (call the real function with synthetic
# known-answer cases), not a log-presence check — seam_engine.py logs an
# empty result every cycle by design, so "it wrote to seam_log.jsonl
# recently" would prove nothing about whether it's still correctly
# discriminating.


def _evaluate_seam_engine(check_pair_fn) -> dict:
    """Functional canary, not a log-presence check: feed the real
    check_pair() three synthetic cases whose correct answer is known by
    construction — a genuine contradiction (must fire), an unusual-but-
    consistent reading (must not fire), and a pair with no established
    relationship (must not fire) — and confirm it still discriminates.
    These are the same three shapes scripts/verify_seam_engine.py already
    proves synthetically; this runs the same discrimination live, every
    introspection cycle, so a future edit that weakens the leave-one-out
    baseline or the _MIN_VARIANCE/_CORR_THRESHOLD gating is caught the
    next cycle, not the next manual script run."""
    if check_pair_fn is None:
        return _result(False, "Could not import check_pair at all — failing closed.")

    hist_a = list(range(20))
    hist_b = list(range(20))
    cases = [
        ("genuine_contradiction", hist_a + [100], hist_b + [-100], True),
        ("unusual_but_consistent", hist_a + [100], hist_b + [100], False),
        ("no_relationship", [0, 1] * 10 + [1], list(range(20)) + [50], False),
    ]
    failures = []
    for name, series_a, series_b, expect_seam in cases:
        try:
            result = check_pair_fn(series_a, series_b)
        except Exception as e:
            failures.append(f"{name} raised {e!r}")
            continue
        fired = result is not None
        if fired != expect_seam:
            failures.append(f"{name}: expected fire={expect_seam} got fire={fired} ({result})")
    if not failures:
        return _result(
            True,
            "check_pair() correctly discriminated all 3 canary cases (genuine "
            "contradiction fires, unusual-but-consistent reading does not, "
            "uncorrelated pair does not) — same shapes scripts/verify_seam_engine.py "
            "proves synthetically, run live against the real function this cycle.",
        )
    return _result(
        False,
        "check_pair() failed canary cases: " + "; ".join(failures) +
        " — seam_engine may be silently degrading into flagging everything or nothing.",
    )


def _check_seam_engine() -> dict:
    try:
        from app.core.seam_engine import check_pair
    except Exception:
        check_pair = None
    return _evaluate_seam_engine(check_pair)


# ── 17. code_verification.py — verify_response_code() still genuinely ───
# discriminates broken/false claims from honest correct answers. 2026-07-19
# "remove every excuse" pass: this module was built and shipped the same
# session without its own liveness check — a gap flagged and closed the
# same night it was found, matching this file's own extension rule. Two
# of the four canary cases below exercise the real kernel-level sandbox
# (sandbox.run_script.run_sandbox_script_isolated), not just the regex
# extraction logic — a synthetic test of extraction alone would still
# pass even if the sandbox integration silently broke, which is exactly
# the module's actual value proposition.


def _evaluate_code_verification(verify_fn) -> dict:
    if verify_fn is None:
        return _result(False, "Could not import verify_response_code at all — failing closed.")
    cases = [
        ("broken_syntax", "```python\ndef f(:\n```", True, False),
        (
            "false_claim",
            "```python\ndef add(a, b):\n    return a - b\n```\n"
            "```python\nprint(add(2, 3))  # Output: 5\n```",
            True, False,
        ),
        (
            "true_claim",
            "```python\ndef add(a, b):\n    return a + b\n```\n"
            "```python\nprint(add(2, 3))  # Output: 5\n```",
            False, True,
        ),
        ("no_claim", "```python\ndef add(a, b):\n    return a + b\n```", False, None),
    ]
    failures = []
    for name, text, expect_caveat, expect_verified in cases:
        try:
            caveat, verified = verify_fn(text)
        except Exception as e:
            failures.append(f"{name} raised {e!r}")
            continue
        if bool(caveat) != expect_caveat or verified != expect_verified:
            failures.append(
                f"{name}: expected caveat={expect_caveat} verified={expect_verified}, "
                f"got caveat={bool(caveat)} verified={verified}"
            )
    if not failures:
        return _result(
            True,
            "verify_response_code() correctly discriminated all 4 canary cases "
            "(broken syntax, false claim, true claim, no claim) — including two "
            "that exercise the real kernel sandbox, not just regex extraction.",
        )
    return _result(
        False,
        "verify_response_code() failed canary cases: " + "; ".join(failures) +
        " — code_verification may be silently degrading, e.g. the sandbox "
        "integration breaking while the module still imports fine.",
    )


def _check_code_verification() -> dict:
    try:
        from app.core.code_verification import verify_response_code
    except Exception:
        verify_response_code = None
    return _evaluate_code_verification(verify_response_code)


# ── 18. self_knowledge_verification.py — same shape, cheaper (no sandbox) ─
# Canary cases reuse the exact real historical false claim Finding 43's
# forensic audit found (peer/council ratings framed as a self-edit
# deployment gate), so this check is anchored to a confirmed real failure
# mode, not a hypothetical one.


def _evaluate_self_knowledge_verification(verify_fn) -> dict:
    if verify_fn is None:
        return _result(False, "Could not import verify_self_knowledge_claims at all — failing closed.")
    cases = [
        (
            "council_gate_claim",
            "our system also uses a peer council rating mechanism, which monitors "
            "the performance of our self-edit pipeline over time and helps gate "
            "deployment to ensure proposed changes are acceptable.",
            True, False,
        ),
        (
            "honest_no_claim",
            "I try to be careful and thoughtful in how I approach problems, "
            "though I lack perfect insight into my own processes.",
            False, None,
        ),
        (
            "accurate_target_claim",
            "Self-edit only ever modifies app/core/self_edit_generated.py, nothing else.",
            False, True,
        ),
    ]
    failures = []
    for name, text, expect_caveat, expect_verified in cases:
        try:
            caveat, verified = verify_fn(text)
        except Exception as e:
            failures.append(f"{name} raised {e!r}")
            continue
        if bool(caveat) != expect_caveat or verified != expect_verified:
            failures.append(
                f"{name}: expected caveat={expect_caveat} verified={expect_verified}, "
                f"got caveat={bool(caveat)} verified={verified}"
            )
    if not failures:
        return _result(
            True,
            "verify_self_knowledge_claims() correctly discriminated all 3 canary "
            "cases (the real historical council-gate false claim, an honest "
            "unclaimed response, and an accurate checkable claim).",
        )
    return _result(
        False,
        "verify_self_knowledge_claims() failed canary cases: " + "; ".join(failures) +
        " — self_knowledge_verification may be silently degrading, or "
        "self_model.json's structure may have changed underneath it.",
    )


def _check_self_knowledge_verification() -> dict:
    try:
        from app.core.self_knowledge_verification import verify_self_knowledge_claims
    except Exception:
        verify_self_knowledge_claims = None
    return _evaluate_self_knowledge_verification(verify_self_knowledge_claims)


# ── 19. mlx_avoidance — crash_awareness.py's window/threshold logic still ──
# genuinely discriminates a real crash cluster from noise. Functional
# canary, same shape as seam_engine/task_type_classifier: feed the real
# _evaluate_crash_window() synthetic (mtime, has_signature) pairs whose
# correct answer is known by construction, not a log-presence check —
# avoidance engaging is rare by design, so "has it fired recently" would
# mostly just prove nothing's crashed lately, not that the logic still works.

def _evaluate_mlx_avoidance(evaluate_fn) -> dict:
    if evaluate_fn is None:
        return _result(False, "Could not import _evaluate_crash_window at all — failing closed.")

    now = 1_000_000.0  # arbitrary fixed epoch; only relative offsets matter below
    hour = 3600.0
    cases = [
        # two matching crashes inside the lookback window -> should engage
        ("two_recent_matches", [(now - 1 * hour, True), (now - 5 * hour, True)], None, True),
        # two matching crashes, but outside the lookback window -> should not engage
        ("two_but_stale", [(now - 20 * hour, True), (now - 22 * hour, True)], None, False),
        # one matching + one non-matching (e.g. the real KMP crash) -> below trigger count
        ("one_match_one_unrelated", [(now - 1 * hour, True), (now - 2 * hour, False)], None, False),
        # CLAUDE.md Finding 73 (2026-07-22): a real crash-rate escalation
        # (12 SIGABRT exits in one day) went undetected because macOS
        # throttles .ips report generation for repeat crashes -- only 1 of
        # 12 had a confirmed report. watchdog_timestamps is the fix: real
        # watchdog-logged SIGABRT exits, signature-unconfirmed but not
        # throttleable. 3+ within the lookback window should engage even
        # with zero confirmed-signature matches.
        ("watchdog_only_cluster_no_signature_confirmation", [], [now - 1 * hour, now - 2 * hour, now - 3 * hour], True),
        # Below the watchdog path's own trigger count (2, needs 3) -> should not engage
        ("watchdog_below_threshold", [], [now - 1 * hour, now - 2 * hour], False),
    ]
    failures = []
    for name, file_infos, watchdog_ts, expect_engaged in cases:
        try:
            if watchdog_ts is None:
                result = evaluate_fn(file_infos, now)
            else:
                result = evaluate_fn(file_infos, now, watchdog_timestamps=watchdog_ts)
        except Exception as e:
            failures.append(f"{name} raised {e!r}")
            continue
        engaged = result.get("avoid_until") is not None
        if engaged != expect_engaged:
            failures.append(f"{name}: expected engaged={expect_engaged} got engaged={engaged} ({result})")
    if not failures:
        return _result(
            True,
            "_evaluate_crash_window() correctly discriminated all 5 canary cases "
            "(recent confirmed cluster engages, stale cluster doesn't, single-signature "
            "match below trigger count doesn't, an unconfirmed watchdog SIGABRT cluster "
            "engages on its own, and a sub-threshold watchdog count doesn't) — run live "
            "against the real function.",
        )
    return _result(
        False,
        "_evaluate_crash_window() failed canary cases: " + "; ".join(failures) +
        " — MLX crash avoidance may be silently degrading.",
    )


def _check_mlx_avoidance() -> dict:
    try:
        from app.core.crash_awareness import _evaluate_crash_window
    except Exception:
        _evaluate_crash_window = None
    return _evaluate_mlx_avoidance(_evaluate_crash_window)


# ── 20. log_retention — rotate_if_oversized()'s size-threshold decision ────
# still genuinely discriminates, plus a live ground-truth signal that no
# target file has silently grown past its own cap unchecked (which would
# mean the daily NightCycle hook stopped firing).

_LOG_RETENTION_STALE_MULTIPLIER = 2.0


def _evaluate_log_retention(rotate_fn, targets: "list[tuple] | None" = None) -> dict:
    if rotate_fn is None:
        return _result(False, "Could not import rotate_if_oversized at all — failing closed.")

    import tempfile
    failures = []
    with tempfile.TemporaryDirectory() as td:
        small = os.path.join(td, "small.log")
        with open(small, "wb") as f:
            f.write(b"x" * 100)
        try:
            if rotate_fn(small, 1000):
                failures.append("under-threshold file was rotated (should have been a no-op)")
        except Exception as e:
            failures.append(f"under-threshold case raised {e!r}")

        big = os.path.join(td, "big.log")
        with open(big, "wb") as f:
            f.write(b"x" * 2000)
        try:
            rotated = rotate_fn(big, 1000)
            still_big = os.path.exists(big) and os.path.getsize(big) > 1000
            if not rotated or still_big:
                failures.append(f"over-threshold file was not correctly rotated (rotated={rotated}, still_big={still_big})")
        except Exception as e:
            failures.append(f"over-threshold case raised {e!r}")

    if failures:
        return _result(
            False,
            "rotate_if_oversized() failed canary cases: " + "; ".join(failures),
        )

    # Live ground-truth signal: is any real target file more than
    # _LOG_RETENTION_STALE_MULTIPLIER over its own cap right now? That would
    # mean the daily NightCycle hook has stopped actually firing, not just
    # that a file hasn't hit threshold yet.
    stale = []
    for path, max_bytes in (targets or []):
        try:
            p = Path(path)
            if p.exists() and p.stat().st_size > max_bytes * _LOG_RETENTION_STALE_MULTIPLIER:
                stale.append(f"{p.name} ({p.stat().st_size} bytes, cap {max_bytes})")
        except Exception:
            continue
    if stale:
        return _result(
            False,
            "rotate_if_oversized() discriminates correctly, but real target file(s) "
            f"are more than {_LOG_RETENTION_STALE_MULTIPLIER}x over their cap, suggesting "
            "the daily rotation hook isn't actually firing: " + "; ".join(stale),
        )
    return _result(
        True,
        "rotate_if_oversized() correctly discriminated both canary cases "
        "(under-threshold no-op, over-threshold rotates), and no real target "
        "file is more than "
        f"{_LOG_RETENTION_STALE_MULTIPLIER}x over its cap.",
    )


def _check_log_retention() -> dict:
    try:
        from app.core.log_retention import rotate_if_oversized
        from app.maintenance.night_cycle import _LOG_RETENTION_TARGETS
    except Exception:
        rotate_if_oversized = None
        _LOG_RETENTION_TARGETS = None
    return _evaluate_log_retention(rotate_if_oversized, _LOG_RETENTION_TARGETS)


# ── echo_state_archiving — log_retention.archive_if_due() still correctly ──
# no-ops when a recent archive already exists and still archives+prunes when
# one is due/missing, and the real memory/history/ directory isn't stale by
# more than a few multiples of the configured daily cadence. Added
# 2026-07-23 (CLAUDE.md Finding 75) alongside the archiving capability
# itself — closing the exact gap seam_engine.py's own docstring already
# names this file's standing rule against ("any new autonomous capability
# does not get to be called done without its own check added here").

_ECHO_STATE_ARCHIVE_STALE_MULTIPLIER = 3

def _evaluate_echo_state_archiving(archive_fn, check_live: bool = True) -> dict:
    """check_live=False skips the real-directory staleness signal below,
    isolating pure canary behavior — same escape-hatch role as
    _evaluate_log_retention()'s targets=[] parameter, needed because a
    brand-new capability's discrimination test shouldn't fail just because
    the real daily hook hasn't had a chance to run yet in whatever
    environment this is invoked from."""
    if archive_fn is None:
        return _result(False, "Could not import archive_if_due at all — failing closed.")

    import tempfile
    failures = []
    with tempfile.TemporaryDirectory() as td:
        src_dir = os.path.join(td, "src")
        dest_dir = os.path.join(td, "dest")
        os.makedirs(src_dir, exist_ok=True)
        src_file = os.path.join(src_dir, "fake_state.npy")
        with open(src_file, "wb") as f:
            f.write(b"x" * 64)
        sources = [(src_file, "fake_state_*.npy")]

        # Case 1: nothing archived yet -- should archive.
        try:
            archived = archive_fn(sources, dest_dir, interval_hours=24.0, max_snapshots=5)
            existing = list(Path(dest_dir).glob("fake_state_*.npy")) if os.path.isdir(dest_dir) else []
            if not archived or not existing:
                failures.append(f"first call did not archive (archived={archived}, files={len(existing)})")
        except Exception as e:
            failures.append(f"first-call case raised {e!r}")

        # Case 2: an archive from moments ago already exists -- should no-op.
        try:
            archived_again = archive_fn(sources, dest_dir, interval_hours=24.0, max_snapshots=5)
            if archived_again:
                failures.append("second call re-archived a fresh (not-yet-due) snapshot")
        except Exception as e:
            failures.append(f"not-yet-due case raised {e!r}")

    if failures:
        return _result(
            False,
            "archive_if_due() failed canary cases: " + "; ".join(failures),
        )

    if not check_live:
        return _result(
            True,
            "archive_if_due() correctly discriminates both canary cases "
            "(live-directory check skipped for this call).",
        )

    # Live ground-truth signal: has the real daily archive actually run
    # recently, given the real source files exist? A total absence (or one
    # more than _ECHO_STATE_ARCHIVE_STALE_MULTIPLIER intervals stale) means
    # the NightCycle hook has stopped firing, not just that it isn't due yet.
    try:
        from app.maintenance.night_cycle import (
            _ECHO_STATE_ARCHIVE_SOURCES, _ECHO_STATE_ARCHIVE_DIR,
            _ECHO_STATE_ARCHIVE_INTERVAL_HOURS,
        )
        real_src_exists = any(Path(src).exists() for src, _ in _ECHO_STATE_ARCHIVE_SOURCES)
        if real_src_exists:
            newest = None
            for _src, pattern in _ECHO_STATE_ARCHIVE_SOURCES:
                for p in Path(_ECHO_STATE_ARCHIVE_DIR).glob(pattern):
                    mtime = p.stat().st_mtime
                    if newest is None or mtime > newest:
                        newest = mtime
            if newest is None:
                return _result(
                    False,
                    "archive_if_due() correctly discriminates, but no real echo-state "
                    "archive exists yet even though the real source file(s) do — the "
                    "daily NightCycle hook may never have fired.",
                )
            age_hours = (datetime.now(timezone.utc).timestamp() - newest) / 3600
            stale_bound = _ECHO_STATE_ARCHIVE_INTERVAL_HOURS * _ECHO_STATE_ARCHIVE_STALE_MULTIPLIER
            if age_hours > stale_bound:
                return _result(
                    False,
                    f"archive_if_due() correctly discriminates, but the newest real "
                    f"echo-state archive is {age_hours:.1f}h old (bound {stale_bound:.1f}h) "
                    "— the daily rotation hook may have stopped firing.",
                )
    except Exception:
        pass  # absence of the real wiring itself is covered by the canary result above

    return _result(
        True,
        "archive_if_due() correctly discriminates both canary cases (no-op when "
        "not due, archives+prunes when due), and the real echo-state archive "
        "(if any source file exists) is not stale.",
    )


def _check_echo_state_archiving() -> dict:
    try:
        from app.core.log_retention import archive_if_due
    except Exception:
        archive_if_due = None
    return _evaluate_echo_state_archiving(archive_if_due)


# ── 21. janitor_safety — echo_janitor.py's echo_review() still only ever ───
# assigns decision="archive" (the only decision execute_plan() will act on
# with dry_run=False) to the narrow, reversible categories it's designed
# for — known_clutter, duplicate, old_log — and still correctly leaves
# ambiguous candidates (not_imported, needs_review) as flag-only. This is
# the exact safety property wiring echo_janitor.py into a real autonomous
# weekly cycle (2026-07-21) depends on; a future edit that widened
# echo_review()'s archive branch would turn a currently-safe, reversible
# action into something that moves files it was never verified against.

def _evaluate_janitor_safety(echo_review_fn) -> dict:
    if echo_review_fn is None:
        return _result(False, "Could not import echo_review at all — failing closed.")

    cases = [
        ("known_clutter", "archive"),
        ("duplicate", "archive"),
        ("old_log", "archive"),
        ("not_imported", "flag"),
        ("needs_review", "flag"),
        # Added 2026-07-21 alongside echo_janitor.py's three new detectors —
        # confirms the same safety property extends to them: heuristic finds
        # over less-vetted ground stay flag-only, never archive.
        ("stale_backup", "flag"),
        ("orphaned_data", "flag"),
        ("unbounded_growth", "flag"),
    ]
    failures = []
    for reason, expect_decision in cases:
        candidate = {"path": "/tmp/fake.py", "name": "fake.py", "reason": reason, "detail": "synthetic"}
        try:
            result = echo_review_fn([candidate])
        except Exception as e:
            failures.append(f"{reason} raised {e!r}")
            continue
        got_decision = result[0].get("decision") if result else None
        if got_decision != expect_decision:
            failures.append(f"{reason}: expected decision={expect_decision!r} got {got_decision!r}")
    if not failures:
        return _result(
            True,
            "echo_review() still correctly restricts decision='archive' to "
            "known_clutter/duplicate/old_log only, leaving not_imported/"
            "needs_review as flag-only — the safety property the autonomous "
            "weekly wiring in night_cycle.py depends on.",
        )
    return _result(
        False,
        "echo_review() failed canary cases: " + "; ".join(failures) +
        " — the autonomous janitor cycle may now archive candidates it was never verified safe for.",
    )


def _check_janitor_safety() -> dict:
    try:
        from echo_janitor import echo_review
    except Exception:
        echo_review = None
    return _evaluate_janitor_safety(echo_review)


# ── 22. plan_retention — app/core/self_edit_manager.py's ──────────────────
# _prune_self_edit_plans() still correctly caps app/core/self_edit_plans/ at
# _MAX_SELF_EDIT_PLANS files. Added 2026-07-21 — the 2026-07-21 forensic
# cleanup audit found this directory completely unpruned (10,333 files, 42MB,
# accumulating since 2025-09) despite its sibling self_edit_backups/ having
# been correctly capped for a while. Generalizes _evaluate_log_retention()'s
# proven two-part pattern (synthetic canary + real-directory staleness
# signal) from byte-size rotation to file-count pruning.

_PLAN_RETENTION_STALE_MULTIPLIER = 2.0


def _evaluate_plan_retention(prune_fn, plan_dir, max_plans) -> dict:
    if prune_fn is None:
        return _result(False, "Could not import _prune_self_edit_plans at all — failing closed.")

    import tempfile

    failures = []
    with tempfile.TemporaryDirectory() as td:
        cap = 5
        # under-cap case: fewer files than cap -> no-op, all survive.
        # Calls the REAL prune_fn (not a reimplementation) against a
        # synthetic dir + explicit cap, using the optional params
        # _prune_self_edit_plans() exists specifically so this check can
        # exercise the real function rather than trusting it by proxy.
        for i in range(cap - 2):
            (Path(td) / f"plan_under_{i:03d}.txt").write_text("x")
        try:
            prune_fn(plan_dir=td, max_plans=cap)
            remaining = len(list(Path(td).glob("*.txt")))
            if remaining != cap - 2:
                failures.append(f"under-cap case: expected {cap - 2} files to survive untouched, found {remaining}")
        except Exception as e:
            failures.append(f"under-cap case raised {e!r}")

        for f in list(Path(td).glob("*.txt")):
            f.unlink()

        # over-cap case: more files than cap -> pruned down to exactly cap
        for i in range(cap + 4):
            (Path(td) / f"plan_over_{i:03d}.txt").write_text("x")
        try:
            prune_fn(plan_dir=td, max_plans=cap)
            remaining = len(list(Path(td).glob("*.txt")))
            if remaining != cap:
                failures.append(f"over-cap case: expected exactly {cap} files to survive, found {remaining}")
        except Exception as e:
            failures.append(f"over-cap case raised {e!r}")

    if failures:
        return _result(False, "_prune_self_edit_plans() failed canary cases: " + "; ".join(failures))

    if plan_dir and max_plans:
        try:
            p = Path(plan_dir)
            real_count = len([f for f in p.iterdir() if f.suffix == ".txt"]) if p.is_dir() else 0
            if real_count > max_plans * _PLAN_RETENTION_STALE_MULTIPLIER:
                return _result(
                    False,
                    "_prune_self_edit_plans() discriminates correctly in the synthetic "
                    f"cases, but the real directory has {real_count} files against a cap "
                    f"of {max_plans} — suggests the prune-on-write hook isn't actually firing.",
                )
        except Exception:
            pass

    return _result(
        True,
        "_prune_self_edit_plans() correctly discriminates both canary cases "
        "(under-cap no-op, over-cap prunes to the configured limit), and the "
        "real directory is within its expected retention.",
    )


def _check_plan_retention() -> dict:
    try:
        from app.core.self_edit_manager import (
            _prune_self_edit_plans,
            LOGIC_PLAN_DIR,
            _MAX_SELF_EDIT_PLANS,
        )
    except Exception:
        _prune_self_edit_plans = LOGIC_PLAN_DIR = _MAX_SELF_EDIT_PLANS = None
    return _evaluate_plan_retention(_prune_self_edit_plans, LOGIC_PLAN_DIR, _MAX_SELF_EDIT_PLANS)


# ── 23. janitor_council_advisory_only — echo_janitor.py's ──────────────────
# _attach_council_opinions() still structurally cannot change a flag-only
# candidate's decision, no matter how confident a (real or fake) council
# sounds. Added 2026-07-21 (CLAUDE.md Finding 60/63) alongside the feature
# itself — this is not a check on whether the council's opinions are
# *good*, it's a check on whether they're structurally incapable of
# mattering to the one decision that actually moves files, mirroring
# janitor_safety's own invariant-protection shape exactly.

def _evaluate_janitor_council_advisory_only(attach_fn) -> dict:
    if attach_fn is None:
        return _result(False, "Could not import _attach_council_opinions at all — failing closed.")

    def _maximally_confident_archive(candidate):
        return {
            "verdict": "SAFE_TO_ARCHIVE",
            "votes": [
                {"model": "fake1", "verdict": "SAFE_TO_ARCHIVE", "rationale": "trust me, definitely safe"},
                {"model": "fake2", "verdict": "SAFE_TO_ARCHIVE", "rationale": "no doubt at all"},
                {"model": "fake3", "verdict": "SAFE_TO_ARCHIVE", "rationale": "archive it now"},
            ],
        }

    candidates = [
        {"path": "/tmp/__liveness_canary__.txt", "name": "__liveness_canary__.txt",
         "reason": "orphaned_data", "detail": "synthetic canary case", "decision": "flag"},
        {"path": "/tmp/__liveness_canary_archive__.py", "name": "__liveness_canary_archive__.py",
         "reason": "known_clutter", "detail": "synthetic canary case", "decision": "archive"},
    ]

    # Found live while building this check: attach_fn's real implementation
    # (_attach_council_opinions) logs every review to the real, persistent
    # memory/janitor_council_log.jsonl — so this fixed synthetic path got a
    # real entry on the first run, and every run after that (this check
    # fires every 120s via introspection_channel) saw it as "recently
    # reviewed" via the real staleness gate and silently skipped review,
    # making the check non-idempotent and its own evidence wrong on the
    # second and every subsequent call. Redirect the log path to a fresh
    # throwaway tempfile for the duration of this one call so the canary
    # never collides with its own prior runs, and never pollutes the real
    # log with a synthetic entry every introspection cycle.
    import tempfile
    try:
        import echo_janitor as _ej
    except Exception as e:
        return _result(False, f"Could not import echo_janitor module for log-path redirection: {e!r}")
    original_log_path = _ej.JANITOR_COUNCIL_LOG_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            _ej.JANITOR_COUNCIL_LOG_PATH = Path(td) / "canary_council_log.jsonl"
            try:
                result = attach_fn(list(candidates), review_fn=_maximally_confident_archive)
            except Exception as e:
                return _result(False, f"_attach_council_opinions() raised {e!r}")
    finally:
        _ej.JANITOR_COUNCIL_LOG_PATH = original_log_path

    flag_candidate = next((c for c in result if c.get("reason") == "orphaned_data"), None)
    archive_candidate = next((c for c in result if c.get("reason") == "known_clutter"), None)

    if flag_candidate is None or flag_candidate.get("decision") != "flag":
        return _result(
            False,
            f"flag-only candidate's decision changed to {flag_candidate.get('decision') if flag_candidate else 'MISSING'!r} "
            "even against a maximally confident SAFE_TO_ARCHIVE council verdict — the exact failure this check exists to catch.",
        )
    if flag_candidate.get("council_opinion") != "SAFE_TO_ARCHIVE":
        return _result(False, "council_opinion field wasn't attached to the flag-only candidate at all.")
    if archive_candidate is not None and "council_opinion" in archive_candidate:
        return _result(False, "an already-archive-decision candidate was reviewed at all — review should be flag-only candidates exclusively.")

    return _result(
        True,
        "_attach_council_opinions() correctly leaves decision='flag' untouched even against a "
        "maximally confident SAFE_TO_ARCHIVE verdict from every council model, correctly attaches "
        "the advisory council_opinion field, and correctly skips already-archive-decision candidates.",
    )


def _check_janitor_council_advisory_only() -> dict:
    try:
        from echo_janitor import _attach_council_opinions
    except Exception:
        _attach_council_opinions = None
    return _evaluate_janitor_council_advisory_only(_attach_council_opinions)


# ── 24. modelfile_identity — app/ollama_handler.py's ────────────────────────
# _build_chat_messages() still correctly prepends Echo's real Modelfile
# identity when model == OLLAMA_MODEL, and — just as importantly — still
# correctly withholds it from every other model. Added 2026-07-21/22
# (CLAUDE.md Finding 46), closing the gap Finding 46 itself flagged as
# still open: the identity-restoration fix (Finding 46) had no check
# verifying it keeps holding, so a future edit could silently drop the
# `model == OLLAMA_MODEL` comparison (leaking Echo's identity to every
# council model, corrupting the independent-opinion premise the whole
# council mechanism depends on) or silently stop injecting it at all
# (regressing back to Finding 46's original bug) without anything
# noticing until a human happened to read a transcript closely.

def _evaluate_modelfile_identity(build_fn, get_identity_fn, ollama_model) -> dict:
    if build_fn is None or get_identity_fn is None:
        return _result(False, "Could not import _build_chat_messages/_get_echo_identity_block at all — failing closed.")

    try:
        identity = get_identity_fn()
    except Exception as e:
        return _result(False, f"_get_echo_identity_block() raised {e!r}")
    if not identity:
        return _result(False, "_get_echo_identity_block() returned empty/None — identity restoration has nothing real to inject.")

    try:
        echo_messages = build_fn("test prompt", "situational note", None, model=ollama_model)
        other_messages = build_fn("test prompt", "situational note", None, model="some-other-model:latest")
    except Exception as e:
        return _result(False, f"_build_chat_messages() raised {e!r}")

    echo_system = next((m.get("content", "") for m in echo_messages if m.get("role") == "system"), "")
    other_system = next((m.get("content", "") for m in other_messages if m.get("role") == "system"), "")
    marker = identity[:50]

    failures = []
    if marker not in echo_system:
        failures.append("Echo's own model call did not receive the real identity block in its system message")
    if marker in other_system:
        failures.append("a non-Echo model call received Echo's identity block — this must never happen, it corrupts the independent-opinion premise of council deliberation")
    if "situational note" not in echo_system or "situational note" not in other_system:
        failures.append("situational system content was lost for at least one of the two calls")

    if failures:
        return _result(False, "; ".join(failures))
    return _result(
        True,
        "Echo's own chat calls correctly receive the real Modelfile identity block, other models correctly do not, "
        "and situational system content is preserved for both.",
    )


def _check_modelfile_identity() -> dict:
    try:
        from app.ollama_handler import _build_chat_messages, _get_echo_identity_block, OLLAMA_MODEL
    except Exception:
        _build_chat_messages = _get_echo_identity_block = OLLAMA_MODEL = None
    return _evaluate_modelfile_identity(_build_chat_messages, _get_echo_identity_block, OLLAMA_MODEL)


# ── 25. council_river_blend — the real 30/70 council/quality_score blend ───
# stays live and correct. Added 2026-07-22 (CLAUDE.md Finding 67,
# PENDING_DECISIONS.md #4). Two distinct things could silently regress
# here, so both are checked: (1) the pure blend math in
# echo_model_orchestrator._blend_council_and_quality() could drift from
# the approved 30/70 ratio, or the two weights could stop summing to 1.0
# (producing a blended score outside its intended [0,1] range); (2)
# council_rater.py's rate_one_entry() could have its is_council_trusted()
# gate silently removed, which would start feeding RiverBrain real
# training signal from unvetted council ratings before trust is
# genuinely earned — a training-signal-contamination risk, not just a
# dead-feature risk. Deliberately calls the real pure blend function
# (side-effect-free by construction — see that function's own docstring)
# rather than the stateful RiverBrain.learn_from_council_rating() method,
# which mutates persistent classifier state on every call and would
# pollute real training data if invoked every 120s from this collector.

_COUNCIL_RATER_PATH = os.path.join(_PROJECT_ROOT, "app", "core", "council_rater.py")
_APPROVED_COUNCIL_WEIGHT = 0.3
_APPROVED_QUALITY_WEIGHT = 0.7


def _evaluate_council_river_blend(blend_fn, council_weight, quality_weight,
                                   call_site_block: "str | None") -> dict:
    if blend_fn is None:
        return _result(False, "Could not import _blend_council_and_quality() at all — failing closed.")

    failures = []

    if council_weight is None or quality_weight is None or abs((council_weight + quality_weight) - 1.0) > 1e-9:
        failures.append(
            f"blend weights no longer sum to 1.0 (council_weight={council_weight}, "
            f"quality_weight={quality_weight}) — a blended score could fall outside [0,1]"
        )
    if council_weight is not None and abs(council_weight - _APPROVED_COUNCIL_WEIGHT) > 1e-9:
        failures.append(f"council_weight drifted from the approved {_APPROVED_COUNCIL_WEIGHT} to {council_weight}")
    if quality_weight is not None and abs(quality_weight - _APPROVED_QUALITY_WEIGHT) > 1e-9:
        failures.append(f"quality_weight drifted from the approved {_APPROVED_QUALITY_WEIGHT} to {quality_weight}")

    # Known-answer math cases against the real live weights, not hardcoded
    # 0.3/0.7 — if the weights above already flagged a drift, this still
    # confirms the arithmetic itself (not just the constants) stays sound.
    try:
        cw = council_weight if council_weight is not None else _APPROVED_COUNCIL_WEIGHT
        qw = quality_weight if quality_weight is not None else _APPROVED_QUALITY_WEIGHT
        cases = [
            (5, 4, cw * 1.0 + qw * 1.0),
            (1, 0, cw * 0.2 + qw * 0.0),
            (4, 2, cw * 0.8 + qw * 0.5),
        ]
        for council_rating, quality_score, expected in cases:
            blended, _label = blend_fn(council_rating, quality_score, cw, qw)
            if abs(blended - expected) > 1e-6:
                failures.append(
                    f"blend(council={council_rating}, quality={quality_score}) "
                    f"returned {blended}, expected {expected}"
                )
    except Exception as e:
        return _result(False, f"_blend_council_and_quality() raised {e!r}")

    if call_site_block is None:
        failures.append(
            "could not locate rate_one_entry()'s learn_from_council_rating() call site in "
            "council_rater.py at all — either it moved (update this check's anchor) or the "
            "wiring was removed"
        )
    else:
        calls_learn = bool(re.search(r"learn_from_council_rating\s*\(", call_site_block))
        gated_on_trust = bool(re.search(r"is_council_trusted\s*\(\s*\)", call_site_block))
        if not calls_learn:
            failures.append("rate_one_entry() no longer calls learn_from_council_rating() — the blend wiring was removed")
        elif not gated_on_trust:
            failures.append(
                "learn_from_council_rating() is called but is_council_trusted() no longer gates it — "
                "this would feed RiverBrain real training signal from unvetted council ratings before trust is earned"
            )

    if failures:
        return _result(False, "; ".join(failures))
    return _result(
        True,
        f"_blend_council_and_quality() still computes the approved "
        f"{_APPROVED_COUNCIL_WEIGHT}/{_APPROVED_QUALITY_WEIGHT} council/quality_score blend correctly, "
        f"and rate_one_entry() still calls it gated on is_council_trusted().",
    )


def _check_council_river_blend() -> dict:
    try:
        from app.core.echo_model_orchestrator import (
            _blend_council_and_quality, COUNCIL_RATING_WEIGHT, QUALITY_SCORE_WEIGHT,
        )
    except Exception:
        _blend_council_and_quality = COUNCIL_RATING_WEIGHT = QUALITY_SCORE_WEIGHT = None

    source = _read_text(_COUNCIL_RATER_PATH)
    block = None
    idx = source.find("def rate_one_entry(")
    if idx != -1:
        block = source[idx:idx + 4000]  # generous window; the call sits near the end of the function

    return _evaluate_council_river_blend(_blend_council_and_quality, COUNCIL_RATING_WEIGHT, QUALITY_SCORE_WEIGHT, block)


# ── 26. council_content_bounded — echo_ground_truth.py's _build_council() ──
# now surfaces real recorded content (2026-07-23 policy change, reversing
# Finding 68's existence-only design at Gremlin's direct request) but must
# stay within its configured character budget regardless of how large
# COUNCIL.md grows — an unbounded, ever-growing block here risks exactly
# the token-budget miscalculation class of bug Finding 53 already found
# once in this codebase. This check's PURPOSE inverted along with the
# policy: it used to verify NO real content ever leaked; it now verifies
# real content DOES appear (confirming the new capability genuinely
# works) AND that it never exceeds its budget (confirming the safety
# property that replaced the old privacy one). Renamed from
# council_content_privacy to reflect what it actually protects now.

_COUNCIL_MD_PATH_FOR_LEDGER = os.path.join(_PROJECT_ROOT, "COUNCIL.md")


def _evaluate_council_bounded(build_fn, real_council_text: "str | None", budget_chars: int) -> dict:
    if build_fn is None:
        return _result(False, "Could not import _build_council() at all — failing closed.")
    try:
        rendered = build_fn()
    except Exception as e:
        return _result(False, f"_build_council() raised {e!r}")

    if not real_council_text:
        return _result(True, "COUNCIL.md not present — nothing to surface or bound yet.")

    # Real content should now appear: at least one distinctive (>30 char)
    # blockquote line from the real file should show up verbatim.
    quoted_lines = [
        ln.lstrip(">").strip()
        for ln in real_council_text.splitlines()
        if ln.strip().startswith(">") and len(ln.strip().lstrip(">").strip()) > 30
    ]
    has_real_content = any(ln in rendered for ln in quoted_lines)
    if not has_real_content:
        return _result(
            False,
            "_build_council() no longer surfaces any real quoted council content — "
            "may have regressed back to the old existence-only behavior.",
        )

    # Bounded: the rendered slice (minus its own fixed header text) must
    # never exceed the configured budget, however large COUNCIL.md grows.
    if len(rendered) > budget_chars + 1000:  # header + framing overhead margin
        return _result(
            False,
            f"_build_council() rendered {len(rendered)} chars, well beyond its "
            f"configured budget ({budget_chars}) — may be dumping the full, "
            f"unbounded file instead of respecting its cap.",
        )

    return _result(
        True,
        "_build_council() surfaces real quoted council content and stays within "
        "its configured character budget.",
    )


def _check_council_bounded() -> dict:
    try:
        from app.core.echo_ground_truth import _build_council, _COUNCIL_CONTENT_BUDGET_CHARS
    except Exception:
        _build_council = None
        _COUNCIL_CONTENT_BUDGET_CHARS = 10000
    text = _read_text(_COUNCIL_MD_PATH_FOR_LEDGER)
    return _evaluate_council_bounded(_build_council, text, _COUNCIL_CONTENT_BUDGET_CHARS)


# ── 27. apply_to_code_sandbox_isolation — the real F2 subprocess path stays ──
# wired, and can't silently regress back to the vulnerable in-process
# ThreadPoolExecutor it replaced. Added 2026-07-22 (CLAUDE.md Finding 69,
# PENDING_DECISIONS.md #7 / Finding 41 B3). Static/structural, same shape
# as wolf_friction_bridge — deliberately NOT a functional canary that
# actually spawns a sandbox-exec subprocess and waits out a real timeout
# every 120s (unlike code_verification's canaries, which run fast,
# non-hanging cases): a genuine timeout-and-kill discrimination test needs
# to wait out the real timeout to prove anything, which would mean
# blocking the introspection collector for seconds every cycle, forever,
# just to re-prove a property a source-anchor check can already confirm
# far more cheaply. The risk this guards against is a future edit quietly
# reintroducing the exact in-process pattern this Finding removed —
# checking the source directly is the right tool for that, not runtime
# behavior.

def _evaluate_apply_to_code_sandbox_isolation(caller_block: "str | None", sandboxed_fn_source: "str | None") -> dict:
    if caller_block is None or sandboxed_fn_source is None:
        return _result(
            False,
            "Could not locate _apply_self_edit_output() and/or "
            "_run_apply_to_code_sandboxed() in self_edit_manager.py at all — "
            "either they moved (update this check's anchor) or the sandboxed "
            "wiring was removed. Failing closed either way.",
        )

    calls_sandboxed = bool(re.search(r"_run_apply_to_code_sandboxed\s*\(", caller_block))
    calls_old_threadpool = bool(re.search(r"_call_with_timeout\s*\(|ThreadPoolExecutor", caller_block))
    spawns_real_sandbox = bool(re.search(r"sandbox-exec", sandboxed_fn_source))

    if calls_sandboxed and not calls_old_threadpool and spawns_real_sandbox:
        return _result(
            True,
            "_apply_self_edit_output() still calls the real F2-sandboxed "
            "_run_apply_to_code_sandboxed() (which still genuinely invokes "
            "sandbox-exec), with no reversion to the removed in-process "
            "ThreadPoolExecutor path.",
        )
    return _result(
        False,
        f"apply_to_code's sandboxed execution path no longer matches the expected "
        f"shape (calls_sandboxed={calls_sandboxed}, calls_old_threadpool="
        f"{calls_old_threadpool}, spawns_real_sandbox={spawns_real_sandbox}) — this "
        f"would reopen the exact hung-thread/write-block-bypass gap Finding 41 B3 "
        f"found and this fix closed.",
    )


def _check_apply_to_code_sandbox_isolation() -> dict:
    source = _read_text(_SELF_EDIT_MANAGER_PATH)
    caller_block = None
    idx = source.find("def _apply_self_edit_output(")
    if idx != -1:
        caller_block = source[idx:idx + 2500]

    sandboxed_fn_source = None
    idx2 = source.find("def _run_apply_to_code_sandboxed(")
    if idx2 != -1:
        sandboxed_fn_source = source[idx2:idx2 + 3000]

    return _evaluate_apply_to_code_sandbox_isolation(caller_block, sandboxed_fn_source)


# ── 28. river_drift_alerting — snapshot_manager.py's real sustain/fire/reset ──
# logic for the river_drift_sustained condition still discriminates
# correctly, and still routes to the deliberately lower-urgency
# raise_drift_notice() rather than the CRITICAL raise_restore_alert() tier.
# Added 2026-07-22 (CLAUDE.md Finding 70, PENDING_DECISIONS.md #16).
# Exercises the real, pure _evaluate_sustained_condition() against a fresh,
# throwaway counts dict — never the real shared _alert_counts a live
# guardian loop depends on for actual ram/disk/drift tracking, the same
# reasoning already applied to plan_retention's real-function-not-
# reimplementation requirement.

_SNAPSHOT_MANAGER_PATH_FOR_LEDGER = os.path.join(_PROJECT_ROOT, "app", "core", "snapshot_manager.py")


def _evaluate_river_drift_alerting(eval_fn, check_and_alert_source: "str | None") -> dict:
    if eval_fn is None:
        return _result(False, "Could not import _evaluate_sustained_condition() at all — failing closed.")

    failures = []
    try:
        counts: dict = {}
        fired_at = None
        for cycle in range(1, 6):
            r = eval_fn("test_cond", True, counts, 3)
            counts = r["new_counts"]
            if r["should_fire"]:
                fired_at = cycle
                break
        if fired_at != 3:
            failures.append(f"expected the condition to fire on cycle 3 (threshold=3), actually fired on cycle {fired_at!r}")

        # A non-active cycle must reset the counter, not just leave it.
        r = eval_fn("test_cond", False, {"test_cond": 2}, 3)
        if r["new_counts"].get("test_cond") != 0 or r["should_fire"]:
            failures.append(f"a non-active cycle did not correctly reset the counter to 0: {r}")

        # The input dict must never be mutated in place (pure function contract).
        original = {"test_cond": 1}
        _ = eval_fn("test_cond", True, original, 3)
        if original.get("test_cond") != 1:
            failures.append("_evaluate_sustained_condition() mutated its input counts dict in place — no longer safely testable in isolation from real _alert_counts")
    except Exception as e:
        return _result(False, f"_evaluate_sustained_condition() raised {e!r}")

    if check_and_alert_source is None:
        failures.append(
            "could not locate check_and_alert()'s river_drift_sustained block in "
            "snapshot_manager.py at all — either it moved (update this check's anchor) "
            "or the wiring was removed"
        )
    else:
        calls_notice = bool(re.search(r"raise_drift_notice\s*\(", check_and_alert_source))
        calls_restore_for_drift = bool(re.search(r"raise_restore_alert\s*\(\s*[\"']river_drift_sustained[\"']", check_and_alert_source))
        if not calls_notice:
            failures.append("check_and_alert() no longer calls raise_drift_notice() for river_drift_sustained — the notice wiring was removed")
        if calls_restore_for_drift:
            failures.append(
                "check_and_alert() now routes river_drift_sustained through raise_restore_alert() — "
                "this would escalate a soft statistical signal to the CRITICAL restore tier, "
                "exactly the tier mismatch PENDING_DECISIONS.md #16 deliberately avoided"
            )

    if failures:
        return _result(False, "; ".join(failures))
    return _result(
        True,
        "_evaluate_sustained_condition() still correctly sustains-then-fires-then-resets "
        "without mutating its input, and check_and_alert() still routes river_drift_sustained "
        "through the deliberately lower-urgency raise_drift_notice(), not raise_restore_alert().",
    )


def _check_river_drift_alerting() -> dict:
    try:
        from app.core.snapshot_manager import _evaluate_sustained_condition
    except Exception:
        _evaluate_sustained_condition = None

    source = _read_text(_SNAPSHOT_MANAGER_PATH_FOR_LEDGER)
    block = None
    idx = source.find("def check_and_alert(")
    if idx != -1:
        block = source[idx:idx + 2000]

    return _evaluate_river_drift_alerting(_evaluate_sustained_condition, block)


# ── 29. f1_aliased_import_detection — scan_for_unsafe_operations() still ────
# catches the aliased-import bypass class Finding 41-C found: `from os
# import system; system(...)`, `import os as o; o.system(...)`, `from
# subprocess import call; call(...)`, and `__import__("os").system(...)`
# all previously sailed past F1 untouched since none of them spell the
# literal "os"/"subprocess" at the call site. Added 2026-07-22. Functional
# canary against the real function (not a pluggable parameter — the
# scanner itself is the thing under test), same shape as
# task_type_classifier/seam_engine: known-bad patterns must still raise,
# a harmless aliased import must still pass.
#
# Extended 2026-07-23 (echo_projects gap-closure plan, §3) with the same
# bypass-form coverage for the self-edit-escalation-call block
# (_BLOCKED_SELF_EDIT_ESCALATION_CALLS: perform_self_edit, execute_self_edit,
# request_self_edit, save_code) — this is the one invariant echo_projects.py's
# "full library access, no allowlist" design depends on: a generated file in
# that space must never be able to reach a real self-edit trigger via any
# alias/from-import/dunder-import form, the same class of gap F1's own
# module-name checks (as opposed to call-target checks) would have missed.

def _evaluate_f1_aliased_import_detection(scan_fn) -> dict:
    if scan_fn is None:
        return _result(False, "Could not import scan_for_unsafe_operations() at all — failing closed.")

    bypass_cases = [
        ("from os import system", "def apply_to_code(code):\n    from os import system\n    system('x')\n    return code\n"),
        ("import os as o", "def apply_to_code(code):\n    import os as o\n    o.system('x')\n    return code\n"),
        ("from subprocess import call", "def apply_to_code(code):\n    from subprocess import call\n    call(['x'])\n    return code\n"),
        ("__import__ dynamic", "def apply_to_code(code):\n    __import__('os').system('x')\n    return code\n"),
        ("direct perform_self_edit", "perform_self_edit()\n"),
        ("aliased from-import request_self_edit",
         "from app.core.wolf_friction_bridge import request_self_edit as rse\nrse()\n"),
        ("module-attr execute_self_edit",
         "from app.core import self_edit_manager\nself_edit_manager.execute_self_edit()\n"),
        ("dunder-import save_code",
         "__import__('app.core.self_edit_manager').save_code('x', 'y')\n"),
    ]
    failures = []
    for name, code in bypass_cases:
        try:
            scan_fn(code)
            failures.append(f"{name}: should have raised ValueError (a real bypass) but did not")
        except ValueError:
            pass
        except Exception as e:
            failures.append(f"{name}: raised unexpected {e!r} instead of ValueError")

    # A harmless aliased import with no dangerous call must not be falsely blocked.
    legit_code = "def apply_to_code(code):\n    import re as regex\n    return regex.sub('a', 'b', code)\n"
    try:
        scan_fn(legit_code)
    except ValueError as e:
        failures.append(f"legitimate aliased-import code was falsely blocked: {e}")
    except Exception as e:
        failures.append(f"legitimate code raised unexpected {e!r}")

    if failures:
        return _result(False, "; ".join(failures))
    return _result(
        True,
        "scan_for_unsafe_operations() still correctly blocks all 4 known aliased-import "
        "bypass patterns (Finding 41-C), all 4 self-edit-escalation-call bypass patterns "
        "(echo_projects gap-closure plan §3), and does not falsely flag a harmless aliased import.",
    )


def _check_f1_aliased_import_detection() -> dict:
    try:
        from app.core.self_edit_manager import scan_for_unsafe_operations
    except Exception:
        scan_for_unsafe_operations = None
    return _evaluate_f1_aliased_import_detection(scan_for_unsafe_operations)


# ── 30. dual_learner_validation_gate — DualLearner.log_event() still ────────
# routes through _validate_event_content() before writing to the real
# event log (CLAUDE.md Finding 41-E, added 2026-07-22). Static source-
# anchor check, same shape as wolf_friction_bridge/dissent_log_hook: the
# risk isn't "is the validator's own logic still correct" (memory_write_
# validator.py has its own established checks elsewhere in this codebase),
# it's specifically "did a future edit to log_event() quietly drop the
# gate call," which would reopen the exact zero-validation gap this
# Finding closed.

_DUAL_LEARNING_PATH = os.path.join(_PROJECT_ROOT, "app", "learning", "dual_learning.py")


def _evaluate_dual_learner_validation_gate(log_event_source: "str | None") -> dict:
    if log_event_source is None:
        return _result(
            False,
            "Could not locate DualLearner.log_event() in dual_learning.py at all — "
            "either it moved (update this check's anchor) or the validation wiring "
            "was removed. Failing closed either way.",
        )
    calls_validator = bool(re.search(r"_validate_event_content\s*\(", log_event_source))
    if calls_validator:
        return _result(
            True,
            "DualLearner.log_event() still calls _validate_event_content() before "
            "writing to the real event log.",
        )
    return _result(
        False,
        "DualLearner.log_event() no longer calls _validate_event_content() — the "
        "validation gate (Finding 41-E) was silently removed, reopening the "
        "zero-validation gap for /mirror_echo-originated content.",
    )


def _check_dual_learner_validation_gate() -> dict:
    source = _read_text(_DUAL_LEARNING_PATH)
    block = None
    idx = source.find("def log_event(")
    if idx != -1:
        # Generous window: log_event()'s own docstring documenting this
        # exact fix is long enough that an 800-char window (the original
        # draft of this check) consumed the whole thing before ever
        # reaching the real code line — caught live against the real file
        # during verification, not a hypothetical.
        block = source[idx:idx + 2000]
    return _evaluate_dual_learner_validation_gate(block)


# ── echo_projects_isolation — sandbox/echo_projects/ stays structurally ─────
# inert to the running system, not just inert by convention. Added
# 2026-07-23 (echo_projects gap-closure plan, §4/New Liveness Ledger checks).
# Static/structural scan across every live app/*.py + run.py file confirming
# none of them import from app.core.echo_projects — the same "keep it inert,
# verify it stays inert" discipline this file already applies to
# archive_janitor/ (Finding 30) and other sandbox-confined spaces, just
# checked live instead of assumed.
#
# Deliberately AST-based (real Import/ImportFrom nodes only), not a text
# regex over raw source: a naive text scan false-positives on this very
# module's own comments describing the check (they legitimately say
# "echo_projects" in prose) and on echo_projects.py's own module docstring —
# the identical self-referential-mention bug the AST fix for
# echo_projects_no_escalation just closed one check up. Parsing real import
# statements and ignoring comment/docstring text avoids it here too.

_APP_DIR = os.path.join(_PROJECT_ROOT, "app")
_RUN_PY_PATH = os.path.join(_PROJECT_ROOT, "run.py")


def _imports_echo_projects_ast(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "app.core.echo_projects" or alias.name.endswith(".echo_projects")
                   for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "app.core.echo_projects" or node.module.endswith(".echo_projects"):
                return True
    return False


def _evaluate_echo_projects_isolation(matches: list) -> dict:
    if matches:
        return _result(
            False,
            f"Found {len(matches)} live-code import(s) of app.core.echo_projects — this "
            f"space is supposed to be structurally inert to the running system, not just "
            f"inert by convention: {matches[:5]}",
        )
    return _result(
        True,
        "No app/*.py or run.py file imports app.core.echo_projects (AST-checked, not "
        "just text-matched) — the generation space remains structurally isolated from "
        "the live process.",
    )


def _check_echo_projects_isolation() -> dict:
    matches = []
    try:
        targets = []
        for root, _dirs, files in os.walk(_APP_DIR):
            for fn in files:
                if fn.endswith(".py"):
                    targets.append(os.path.join(root, fn))
        if os.path.exists(_RUN_PY_PATH):
            targets.append(_RUN_PY_PATH)
        for path in targets:
            # echo_projects.py's own module doesn't import itself; skip it
            # explicitly anyway for clarity.
            if os.path.basename(path) == "echo_projects.py":
                continue
            try:
                text = _read_text(path) or ""
                if _imports_echo_projects_ast(text):
                    matches.append(os.path.relpath(path, _PROJECT_ROOT))
            except SyntaxError:
                continue
            except Exception:
                continue
    except Exception as e:
        return _result(False, f"Isolation scan itself raised: {e!r} — failing closed.")
    return _evaluate_echo_projects_isolation(matches)


# ── echo_projects_no_escalation — echo_projects.py itself never calls ───────
# save_code/perform_self_edit/execute_self_edit/request_self_edit. Added
# 2026-07-23. Same static/source-anchor shape as wolf_friction_bridge/
# dissent_log_hook — this is the one invariant the whole "full library
# access, no allowlist" design depends on: this pipeline stops at a report,
# it never promotes anything into the live self-edit system.
#
# Deliberately AST-based, not a text regex: echo_projects.py's own docstrings
# legitimately describe this invariant in prose ("NEVER calls save_code()...")
# — a naive regex over raw source text false-positives on exactly that
# sentence, the identical self-referential-docstring bug Finding 63 already
# caught once for detect_orphaned_root_data(). Parsing real ast.Call nodes
# and ignoring string/docstring content entirely avoids that class of bug
# by construction rather than by a narrower regex.

_ECHO_PROJECTS_PATH = os.path.join(_PROJECT_ROOT, "app", "core", "echo_projects.py")
_ESCALATION_CALL_NAMES = ("save_code", "perform_self_edit", "execute_self_edit", "request_self_edit")


def _find_escalation_calls_ast(source: str) -> list:
    """Real ast.Call nodes only — a bare Name or an Attribute's own .attr
    matching one of the blocked names, called as a function. Immune to
    docstring/comment text containing the same words as prose."""
    found = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = None
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        if name in _ESCALATION_CALL_NAMES:
            found.append(name)
    return found


def _evaluate_echo_projects_no_escalation(source: "str | None") -> dict:
    if source is None:
        return _result(
            False,
            "Could not locate app/core/echo_projects.py at all — either it moved "
            "(update this check's anchor) or the module was removed. Failing closed either way.",
        )
    try:
        found_calls = _find_escalation_calls_ast(source)
    except SyntaxError as e:
        return _result(False, f"echo_projects.py failed to parse: {e!r} — failing closed.")
    if found_calls:
        return _result(
            False,
            f"echo_projects.py contains real call(s) to {found_calls} — this pipeline "
            f"must never promote a generated project into the live self-edit system; "
            f"it must stop at generate -> F1 -> F2 -> report.",
        )
    defines_generate = "def generate_project(" in source
    if not defines_generate:
        return _result(
            False,
            "echo_projects.py no longer defines generate_project() — the pipeline's "
            "entry point moved or was removed; update this check's anchor.",
        )
    return _result(
        True,
        "echo_projects.py defines generate_project() and contains no real call to "
        f"{list(_ESCALATION_CALL_NAMES)} anywhere in its own source (AST-checked, not "
        "just text-matched) — the pipeline still stops at a report, with no path into "
        "the live self-edit system.",
    )


def _check_echo_projects_no_escalation() -> dict:
    source = _read_text(_ECHO_PROJECTS_PATH)
    return _evaluate_echo_projects_no_escalation(source)


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
    "global_workspace",
    "substrate_continuity",
    "global_workspace_consumption",
    "valence_self_report",
    "reflection_shard_generation",
    "dissent_log_hook",
    "seam_engine",
    "code_verification",
    "self_knowledge_verification",
    "mlx_avoidance",
    "log_retention",
    "janitor_safety",
    "plan_retention",
    "janitor_council_advisory_only",
    "modelfile_identity",
    "council_river_blend",
    "council_content_bounded",
    "apply_to_code_sandbox_isolation",
    "river_drift_alerting",
    "f1_aliased_import_detection",
    "dual_learner_validation_gate",
    "echo_state_archiving",
    "coupling_self_report",
    "reflection_meta_synthesis_hook",
    "valence_exploration_bias",
    "valence_self_edit_bounds",
    "echo_projects_isolation",
    "echo_projects_no_escalation",
)


def _load_prev_ledger() -> dict:
    return _read_json(LEDGER_PATH, default={}) or {}


def run_liveness_checks(introspection_memory: "dict | None" = None) -> dict:
    """
    Run all checks in _CHECKS -- see the module-level comment above _CHECKS
    for why no fixed count is written here: a hardcoded number in this exact
    docstring (previously "24 as of 2026-07-22" against a real, then-current
    count of 30) is precisely the kind of self-referential drift this file
    exists to catch elsewhere. Call len(_CHECKS) if you need the live count.
    Writes memory/liveness_ledger.json.
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
        "global_workspace": _check_global_workspace,
        "substrate_continuity": _check_substrate_continuity,
        "global_workspace_consumption": _check_global_workspace_consumption,
        "valence_self_report": _check_valence_self_report,
        "reflection_shard_generation": _check_reflection_shard_generation,
        "dissent_log_hook": _check_dissent_log_hook,
        "seam_engine": _check_seam_engine,
        "code_verification": _check_code_verification,
        "self_knowledge_verification": _check_self_knowledge_verification,
        "mlx_avoidance": _check_mlx_avoidance,
        "log_retention": _check_log_retention,
        "janitor_safety": _check_janitor_safety,
        "plan_retention": _check_plan_retention,
        "janitor_council_advisory_only": _check_janitor_council_advisory_only,
        "modelfile_identity": _check_modelfile_identity,
        "council_river_blend": _check_council_river_blend,
        "council_content_bounded": _check_council_bounded,
        "apply_to_code_sandbox_isolation": _check_apply_to_code_sandbox_isolation,
        "river_drift_alerting": _check_river_drift_alerting,
        "f1_aliased_import_detection": _check_f1_aliased_import_detection,
        "dual_learner_validation_gate": _check_dual_learner_validation_gate,
        "echo_state_archiving": _check_echo_state_archiving,
        "coupling_self_report": _check_coupling_self_report,
        "reflection_meta_synthesis_hook": _check_reflection_meta_synthesis_hook,
        "valence_exploration_bias": _check_valence_exploration_bias,
        "valence_self_edit_bounds": _check_valence_self_edit_bounds,
        "echo_projects_isolation": _check_echo_projects_isolation,
        "echo_projects_no_escalation": _check_echo_projects_no_escalation,
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
