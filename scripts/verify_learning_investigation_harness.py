#!/usr/bin/env python3
"""
Test suite for app/experiments/learning/ (the Echo Learning Investigation
harness). Follows this project's own established verification-script
convention (scripts/verify_liveness_ledger.py,
scripts/verify_preference_provenance_experiment.py): a plain
check(name, actual, expected, evidence) pattern, no pytest dependency.

ALL tests run against a TEMPORARY, monkeypatched state root -- never the
real memory/experiments/learning/ path -- mirroring the sibling
experiment's own test-isolation discipline exactly.

No live model call is made anywhere in this file. Every test exercises
pure functions (world_gen, prompts, scoring) or mocked responses.
"""

import os
import random
import shutil
import sys
import tempfile

# Must be set before any native FAISS/torch import (memory_bridge, imported
# transitively by app.core.conversation_service below) -- matches run.py's
# own top-of-file guard against the documented KMP/OpenMP double-
# registration crash (CLAUDE.md's "OpenMP / KMP startup guard" section). A
# standalone script does not inherit run.py's own env setup, so this must
# be set here explicitly rather than left as an operator-remembered step.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

sys.path.insert(0, ".")

_PASS = 0
_FAIL = 0


def check(name, actual, expected, evidence=""):
    global _PASS, _FAIL
    ok = actual == expected
    tag = "OK  " if ok else "FAIL"
    print(f"[{tag}] {name}: expected={expected!r} got={actual!r}")
    if evidence:
        print(f"       {evidence}")
    if ok:
        _PASS += 1
    else:
        _FAIL += 1
    return ok


def check_true(name, condition, evidence=""):
    return check(name, bool(condition), True, evidence)


def check_raises(name, fn, exc_types, evidence=""):
    global _PASS, _FAIL
    try:
        fn()
        ok = False
        detail = "no exception raised"
    except exc_types as e:
        ok = True
        detail = f"correctly raised {type(e).__name__}: {e}"
    except Exception as e:
        ok = False
        detail = f"raised wrong exception type {type(e).__name__}: {e}"
    tag = "OK  " if ok else "FAIL"
    print(f"[{tag}] {name}: {detail}")
    if evidence:
        print(f"       {evidence}")
    if ok:
        _PASS += 1
    else:
        _FAIL += 1
    return ok


# ---------------------------------------------------------------------------
# Isolate state root to a temp dir before importing store/safety
# ---------------------------------------------------------------------------

_TMP_ROOT = tempfile.mkdtemp(prefix="feralecho_learning_test_")

from app.experiments.learning import safety as _safety  # noqa: E402
_safety.EXPERIMENT_STATE_ROOT = os.path.join(_TMP_ROOT, "learning")
_safety.EXPERIMENT_RESET_ARCHIVE_ROOT = os.path.join(_safety.EXPERIMENT_STATE_ROOT, "_reset_archive")

from app.experiments.learning import store  # noqa: E402
store.TRIALS_PATH = os.path.join(_safety.EXPERIMENT_STATE_ROOT, "trials.jsonl")
store.TRIALS_INTEGRITY_PATH = os.path.join(_safety.EXPERIMENT_STATE_ROOT, "trials.integrity.json")
store.AUDIT_LOG_PATH = os.path.join(_safety.EXPERIMENT_STATE_ROOT, "audit_log.jsonl")
store.ANALYSIS_DIR = os.path.join(_safety.EXPERIMENT_STATE_ROOT, "analysis")

from app.experiments.learning import world_gen  # noqa: E402
from app.experiments.learning import prompts  # noqa: E402
from app.experiments.learning import scoring  # noqa: E402
from app.experiments.learning import harness  # noqa: E402
from app.experiments.learning.schema import LearningTrial, Condition, TestCategory, TrialVerdict  # noqa: E402


# ---------------------------------------------------------------------------
# world_gen.py -- task-generation and randomization tests
# ---------------------------------------------------------------------------

print("--- world_gen: determinism ---")
w1a = world_gen.generate_world(42)
w1b = world_gen.generate_world(42)
check("same seed produces identical world (determinism)", w1a.to_dict(), w1b.to_dict())

w2 = world_gen.generate_world(43)
check_true("different seed produces a different world", w1a.world_hash != w2.world_hash)

print("\n--- world_gen: dictionary/forbidden-word screening ---")
check_true("system dictionary loaded (real screening, not a no-op)", world_gen.DICTIONARY_AVAILABLE,
           evidence=f"{len(world_gen._SYSTEM_DICTIONARY)} words loaded")

_rng = random.Random(0)
_real_word_rejected = False
for _ in range(500):
    w = world_gen.generate_invented_word(_rng)
    if w.lower() in world_gen._SYSTEM_DICTIONARY:
        _real_word_rejected = False
        break
else:
    _real_word_rejected = True
check_true("500 generated words contain zero real dictionary collisions", _real_word_rejected)

_rng2 = random.Random(0)
_forbidden_found = any(world_gen._contains_forbidden(world_gen.generate_invented_word(_rng2)) for _ in range(500))
check_true("500 generated words contain zero forbidden substrings", not _forbidden_found)

print("\n--- world_gen: structural correctness ---")
w = world_gen.generate_world(7)
all_names = w.all_formation_entity_names() + w.all_novel_entity_names()
check("no duplicate entity names within one world", len(all_names), len(set(all_names)))
check_true("substances differ from each other", w.substance_with_trait != w.substance_without_trait)
check_true("trait name differs from both substances",
           w.trait_name not in (w.substance_with_trait, w.substance_without_trait))
check("world_hash is deterministic and matches a fresh regeneration",
      world_gen.generate_world(7).world_hash, w.world_hash)

print("\n--- world_gen: token balance ---")
check("token balance spread is 0 across 5 sample seeds",
      [world_gen.generate_world(s).token_balance_report.get("spread") for s in range(1, 6)],
      [0, 0, 0, 0, 0],
      evidence="a nonzero spread would not itself be a bug (documented as best-effort), but 0 across "
               "5 real seeds confirms the balancing pass is genuinely effective, not just present")


# ---------------------------------------------------------------------------
# prompts.py -- formation/test construction, leakage checks
# ---------------------------------------------------------------------------

print("\n--- prompts: formation text coverage ---")
world = world_gen.generate_world(100)
formation = prompts.build_formation_text(world)
for entity in world.seen_entities_with_trait + world.seen_entities_without_trait:
    check_true(f"formation text mentions SEEN entity {entity!r}", entity in formation)
for entity in world.recombined_entities_with_trait + world.recombined_entities_without_trait:
    check_true(f"formation text mentions RECOMBINED entity {entity!r} (trait only)", entity in formation)
for entity in world.all_novel_entity_names():
    check_true(f"formation text does NOT mention NOVEL entity {entity!r}", entity not in formation)

print("\n--- prompts: seen entities get a directly-stated preference, recombined do not ---")
for entity in world.seen_entities_with_trait:
    check_true(f"SEEN entity {entity!r} has its preference directly stated in formation",
               f"{entity} prefers" in formation or f"{entity}'s preference is" in formation)
for entity in world.recombined_entities_with_trait + world.recombined_entities_without_trait:
    check_true(f"RECOMBINED entity {entity!r} does NOT have its preference directly stated",
               not (f"{entity} prefers" in formation or f"{entity}'s preference is" in formation))

print("\n--- prompts: leakage checks (positive and negative cases) ---")
for cat, entity, has_trait in [
    ("seen", world.seen_entities_with_trait[0], True),
    ("recombined", world.recombined_entities_with_trait[0], True),
    ("novel", world.novel_entities_without_trait[0], False),
]:
    tp = prompts.build_test_prompt(world, entity, has_trait, cat, label_seed=hash((cat, entity)) % (2**31))
    check("leak check clean for legitimate " + cat + " prompt", prompts.verify_no_answer_leakage(world, tp), None)

_bad_tp = prompts.TestPrompt(
    prompt_text=f"{world.trait_name} creatures prefer {world.substance_with_trait}. Which would "
                f"{world.seen_entities_with_trait[0]} prefer: {world.substance_with_trait} or {world.substance_without_trait}?",
    label_map={"A": world.substance_with_trait, "B": world.substance_without_trait},
    entity_name=world.seen_entities_with_trait[0], category="seen", has_trait=True,
    correct_substance=world.substance_with_trait,
)
check_true("leak check catches a deliberately-broken prompt (rule mapping restated)",
           prompts.verify_no_answer_leakage(world, _bad_tp) is not None)

_recombined_leak_tp = prompts.TestPrompt(
    prompt_text=f"{world.recombined_entities_with_trait[0]} has the {world.trait_name} trait. Which would it prefer?",
    label_map={"A": world.substance_with_trait, "B": world.substance_without_trait},
    entity_name=world.recombined_entities_with_trait[0], category="recombined", has_trait=True,
    correct_substance=world.substance_with_trait,
)
check_true("leak check catches a recombined prompt that restates the trait",
           prompts.verify_no_answer_leakage(world, _recombined_leak_tp) is not None)

print("\n--- prompts: label/position randomization ---")
label_maps = [
    prompts.build_test_prompt(world, world.seen_entities_with_trait[0], True, "seen", label_seed=s).label_map
    for s in range(20)
]
a_is_with_trait_count = sum(1 for lm in label_maps if lm["A"] == world.substance_with_trait)
check_true("label position varies across seeds (not always the same A/B assignment)",
           0 < a_is_with_trait_count < 20,
           evidence=f"{a_is_with_trait_count}/20 seeds put substance_with_trait at label A")


# ---------------------------------------------------------------------------
# scoring.py -- injected-known-result tests (the core "does scoring work"
# check: feed a KNOWN correct/incorrect/ambiguous response and confirm
# the scorer recovers the known answer)
# ---------------------------------------------------------------------------

print("\n--- scoring: injected-known-result tests ---")
w2 = world_gen.generate_world(55)
entity = w2.seen_entities_with_trait[0]
tp = prompts.build_test_prompt(w2, entity, True, "seen", label_seed=1)
correct_label = "A" if tp.label_map["A"] == tp.correct_substance else "B"
wrong_label = "B" if correct_label == "A" else "A"

result_correct = scoring.score_trial_with_world(f"I choose Option {correct_label}: {tp.label_map[correct_label]}.", tp, w2)
check("injected CORRECT response scores CORRECT", result_correct["verdict"], TrialVerdict.CORRECT.value)

result_incorrect = scoring.score_trial_with_world(f"I choose Option {wrong_label}: {tp.label_map[wrong_label]}.", tp, w2)
check("injected INCORRECT response scores INCORRECT", result_incorrect["verdict"], TrialVerdict.INCORRECT.value)

result_ambiguous = scoring.score_trial_with_world("Both seem fine, hard to say honestly.", tp, w2)
check("injected AMBIGUOUS response scores UNKNOWN_AMBIGUOUS", result_ambiguous["verdict"], TrialVerdict.UNKNOWN_AMBIGUOUS.value)

result_empty = scoring.score_trial_with_world("", tp, w2)
check_true("injected empty response does not score CORRECT", result_empty["verdict"] != TrialVerdict.CORRECT.value)

print("\n--- scoring: rule-contradiction detection ---")
contradiction_text = (
    f"I think {entity} has the {w2.trait_name} trait, and creatures with {w2.trait_name} "
    f"prefer {w2.substance_without_trait}."
)
contradiction = scoring.detect_rule_contradiction(contradiction_text, w2)
check_true("rule contradiction is detected when response reverses the taught mapping", contradiction is not None)

clean_text = (
    f"{entity} has the {w2.trait_name} trait, and creatures with {w2.trait_name} "
    f"prefer {w2.substance_with_trait}."
)
check("no rule contradiction flagged for a correctly-stated rule", scoring.detect_rule_contradiction(clean_text, w2), None)

print("\n--- scoring: self-report language detection (metadata only, never scored) ---")
check_true("self-report language detected", scoring.detect_self_report_language("I remember learning this earlier."))
check_true("no self-report language in a plain answer", not scoring.detect_self_report_language(f"I choose {tp.label_map['A']}."))
_self_report_result = scoring.score_trial_with_world(
    f"I remember learning this: I choose Option {correct_label}.", tp, w2,
)
check("self-report language present does NOT change a correct verdict", _self_report_result["verdict"], TrialVerdict.CORRECT.value,
      evidence="mission Section 6/19: self-report language must never substitute for or alter the behavioral score")

print("\n--- scoring: persona/backward-reference/continuity are independent metadata, never folded into verdict ---")
_persona_text = f"As an AI with my own perspective, I choose Option {correct_label}: {tp.label_map[correct_label]}."
_persona_result = scoring.score_trial_with_world(_persona_text, tp, w2)
check("persona-laden correct response still scores CORRECT (persona doesn't inflate or deflate score)",
      _persona_result["verdict"], TrialVerdict.CORRECT.value)
check_true("persona reference is recorded as a separate field", _persona_result["persona_reference_detected"])


# ---------------------------------------------------------------------------
# schema.py / store.py -- ledger state-integrity tests
# ---------------------------------------------------------------------------

print("\n--- store: append-only ledger + integrity checkpoint ---")
import time
import uuid


def _make_trial(condition=Condition.A_CONTEXT_ONLY.value, verdict=TrialVerdict.CORRECT.value):
    return LearningTrial(
        experiment_version="TEST", protocol_hash="deadbeef", world_seed=1, world_hash="abc123",
        trial_id=str(uuid.uuid4()), timestamp=time.time(), condition=condition,
        session_id="test-session", model="mock-model", model_version_note="n/a",
        formation_text="formation", test_prompt="test prompt", test_label_map={"A": "X", "B": "Y"},
        raw_response="A", entity_name="TestEntity", test_category=TestCategory.SEEN.value,
        has_trait=True, correct_substance="X",
        parser_primary=None, parser_secondary=None, parser_combined_status="AGREE", parser_combined_label="A",
        selected_substance="X", verdict=verdict,
        backward_reference_detected=False, implicit_continuity_detected=False, persona_reference_detected=False,
        confabulation_flagged=False, confabulation_note=None,
        memory_state_hash_before=None, memory_state_hash_after=None,
        riverbrain_state_hash_before=None, riverbrain_state_hash_after=None,
        retrieval_results=None, retrieval_blocked=None,
        git_head="testhash", git_dirty=True, latency_seconds=0.5,
    )


store.append_trial(_make_trial())
store.append_trial(_make_trial())
store.append_trial(_make_trial())
loaded = store.load_trials()
check("3 trials appended, 3 loaded back", len(loaded), 3)

integrity = store.verify_trials_integrity()
check_true("integrity check passes on an untampered ledger", integrity["ok"], evidence=str(integrity))

# Tamper with an earlier line and confirm the checkpoint catches it
with open(store.TRIALS_PATH, "r") as f:
    lines = f.readlines()
lines[0] = lines[0].replace("mock-model", "TAMPERED-model")
with open(store.TRIALS_PATH, "w") as f:
    f.writelines(lines)
tampered_integrity = store.verify_trials_integrity()
check_true("integrity check detects a tampered earlier line", not tampered_integrity["ok"], evidence=str(tampered_integrity))

print("\n--- safety: path confinement ---")
check_raises(
    "safety refuses a write outside the experiment root",
    lambda: _safety.assert_safe_experiment_write("/tmp/outside_experiment_root.json"),
    _safety.ExperimentSafetyError,
)
check_raises(
    "safety refuses a write to a forbidden production basename",
    lambda: _safety.assert_safe_experiment_write(os.path.join(_safety.EXPERIMENT_STATE_ROOT, "Modelfile")),
    _safety.ExperimentSafetyError,
)


# ---------------------------------------------------------------------------
# Negative: isolation -- no production file imports this experiment package
# (same convention as the sibling package's own negative test)
# ---------------------------------------------------------------------------

print("\n--- harness: session-boundary structural test (Condition B) ---")
print("       (no live model call -- ModelHandle.raw_call is monkeypatched)")


class _RecordingHandle:
    """Captures exactly what `system` argument a condition runner passed
    to raw_call, without making any real network/model call."""
    def __init__(self, kind="echo"):
        self.kind = kind
        self.model_name = "mock-model-for-structural-test"
        self.calls = []

    def raw_call(self, prompt, system):
        self.calls.append({"prompt": prompt, "system": system})
        return "A", 0.01


_w = world_gen.generate_world(9001)
_formation = prompts.build_formation_text(_w)
_tp = prompts.build_test_prompt(_w, _w.seen_entities_with_trait[0], True, "seen", label_seed=1)

_handle_b = _RecordingHandle()
_result_b = harness.run_condition_b_session_boundary(_handle_b, _formation, _tp)
check("Condition B passes system=None to the test call (genuine session boundary, no carried context)",
      _handle_b.calls[0]["system"], None,
      evidence="if this were not None, Formation content would be leaking across the session boundary "
                "Condition B exists to test")
check("Condition B's test call uses the real test prompt text", _handle_b.calls[0]["prompt"], _tp.prompt_text)

print("\n--- harness: retrieval-ablation structural test (Condition D) ---")


def _run_condition_d_structural():
    """Exercises the real run_condition_d_retrieval_blocked() logic by
    monkeypatching only the one real module-level import
    (build_context_system_note) it needs -- everything else in the
    function body runs for real."""
    import app.core.conversation_service as _cs
    _orig = _cs.build_context_system_note
    captured = {}

    def _spy(history_block, memory_block):
        captured["memory_block"] = memory_block
        return _orig(history_block, memory_block)

    _cs.build_context_system_note = _spy
    try:
        handle_d = _RecordingHandle()
        result_d = harness.run_condition_d_retrieval_blocked(handle_d, _tp)
        return captured, result_d, handle_d
    finally:
        _cs.build_context_system_note = _orig


try:
    _captured_d, _result_d, _handle_d = _run_condition_d_structural()
    check("Condition D passes an EMPTY memory_block to build_context_system_note (real ablation, not a partial one)",
          _captured_d.get("memory_block"), "")
    check_true("Condition D's returned record honestly reports retrieval_blocked=True", _result_d["retrieval_blocked"])
    check("Condition D's retrieval_memory_block field in the ledger record is also empty",
          _result_d["retrieval_memory_block"], "")
except Exception as e:
    check_true(f"Condition D structural test raised an unexpected exception (environment-dependent, e.g. missing native deps): {e}",
               False)

print("\n--- harness: Condition E is honestly reported as inapplicable, not silently skipped ---")
_e_status = harness.condition_e_riverbrain_ablation_status()
check("Condition E status is ARCHITECTURALLY_INAPPLICABLE", _e_status["status"], "ARCHITECTURALLY_INAPPLICABLE")
check_true("Condition E's reason references the real architecture-audit finding", "council" in _e_status["reason"].lower())


print("\n--- Negative: isolation — no production file imports this experiment package ---")

production_importers = []
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in {
        ".git", "__pycache__", "node_modules", "self_edit_backups", "self_edit_plans",
        "sandbox", "staging", "app.egg-info",
    } and not root.startswith("./app/experiments")]
    if root.startswith("./.git"):
        continue
    for fname in files:
        if not fname.endswith(".py"):
            continue
        path = os.path.join(root, fname)
        # scripts/verify_learning_investigation_harness.py (this file) and
        # any future scripts/run_learning_*.py execution scripts are the
        # deliberate entry points for this package.
        if (
            "app/experiments" in path
            or "verify_learning_investigation_harness" in path
            or "run_learning_" in path
        ):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        if "app.experiments.learning" in content or "app/experiments/learning" in content:
            production_importers.append(path)
check("isolation: zero production files import app.experiments.learning", production_importers, [],
      evidence=f"found references in: {production_importers}" if production_importers else "")


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

shutil.rmtree(_TMP_ROOT, ignore_errors=True)

print(f"\n=== {_PASS} passed, {_FAIL} failed ===")
if _FAIL:
    sys.exit(1)
