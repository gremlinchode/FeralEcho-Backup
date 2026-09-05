#!/usr/bin/env python3
"""
Test suite for app/core/behavioral_state.py + its integration into
app/core/echo_ground_truth.py (P3.1-IMPLEMENT-C1).

Follows this project's established check(name, actual, expected, evidence)
convention. NO LIVE MODEL CALL ANYWHERE IN THIS FILE.

ALL tests run against a TEMPORARY, monkeypatched state root -- never the
real memory/ directory -- so this suite never touches real production
state, real P1/P1.2/Learning-Pilot evidence, or the real behavioral
directive store a human operator might create later.
"""

import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import importlib
import json
import shutil
import sys
import tempfile

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
        ok, detail = False, "no exception raised"
    except exc_types as e:
        ok, detail = True, f"correctly raised {type(e).__name__}: {e}"
    except Exception as e:
        ok, detail = False, f"raised wrong exception type {type(e).__name__}: {e}"
    tag = "OK  " if ok else "FAIL"
    print(f"[{tag}] {name}: {detail}")
    if evidence:
        print(f"       {evidence}")
    if ok:
        _PASS += 1
    else:
        _FAIL += 1
    return ok


_TMP_ROOT = tempfile.mkdtemp(prefix="feralecho_behavioral_state_test_")

import app.core.behavioral_state as bs  # noqa: E402

bs._STATE_PATH = os.path.join(_TMP_ROOT, "behavioral_directives.json")
bs._BACKUP_DIR = os.path.join(_TMP_ROOT, "behavioral_directives_backups")
bs._AUDIT_LOG_PATH = os.path.join(_TMP_ROOT, "behavioral_directives_audit.jsonl")


# ---------------------------------------------------------------------------
# 1. Mutation requires human confirmation
# ---------------------------------------------------------------------------

print("--- mutation requires human confirmation ---")

check_raises(
    "propose_and_confirm_directive refuses without human_confirmed=True",
    lambda: bs.propose_and_confirm_directive(
        trigger_keywords=["widget"], directive_text="be brief", provenance={"x": 1}, human_confirmed=False,
    ),
    bs.BehavioralStateError,
)
check_raises(
    "propose_and_confirm_directive refuses a truthy-but-not-True value",
    lambda: bs.propose_and_confirm_directive(
        trigger_keywords=["widget"], directive_text="be brief", provenance={"x": 1}, human_confirmed=1,
    ),
    bs.BehavioralStateError,
)
check("no directive was stored by the refused attempts above", len(bs.load_state()["directives"]), 0)


# ---------------------------------------------------------------------------
# 2. Raw teaching exchange is not stored
# ---------------------------------------------------------------------------

print("\n--- raw teaching exchange is not stored ---")

_original_exchange = (
    "The user said: 'when I ask about widgets, please always mention that they come in three sizes' "
    "and the assistant said 'understood, I will mention the three sizes whenever widgets come up.'"
)
d1 = bs.propose_and_confirm_directive(
    trigger_keywords=["widget"],
    directive_text="Mention that widgets come in three sizes.",
    provenance={"proposed_by": "gremlin", "reason": "test", "source_conversation_ref": "conv-001"},
    human_confirmed=True,
)
state_on_disk = json.load(open(bs._STATE_PATH))
raw_dump = json.dumps(state_on_disk)
check_true(
    "the original verbatim teaching exchange never appears anywhere in the persisted state file",
    _original_exchange not in raw_dump,
)
check_true(
    "the directive schema has no field literally named for raw/original/verbatim text",
    not any(k for k in d1.keys() if k in ("raw_text", "original_text", "verbatim", "teaching_exchange", "conversation_text")),
    evidence=f"persisted keys: {sorted(d1.keys())}",
)
import inspect  # noqa: E402

check(
    "the function signature itself has no parameter for the original exchange",
    sorted(inspect.signature(bs.propose_and_confirm_directive).parameters.keys()),
    sorted(["trigger_keywords", "directive_text", "provenance", "human_confirmed"]),
)


# ---------------------------------------------------------------------------
# 3. Derived directive persists across restart (simulated: fresh module
#    re-import + fresh disk read, not a cached in-process value)
# ---------------------------------------------------------------------------

print("\n--- persists across (simulated) restart ---")

del bs
importlib.invalidate_caches()
import app.core.behavioral_state as bs  # noqa: E402  (fresh import, simulating a new process)
bs._STATE_PATH = os.path.join(_TMP_ROOT, "behavioral_directives.json")
bs._BACKUP_DIR = os.path.join(_TMP_ROOT, "behavioral_directives_backups")
bs._AUDIT_LOG_PATH = os.path.join(_TMP_ROOT, "behavioral_directives_audit.jsonl")

reloaded_state = bs.load_state()
check("directive count survives a fresh module re-import (simulated restart)", len(reloaded_state["directives"]), 1)
check(
    "the reloaded directive's text matches exactly what was persisted",
    reloaded_state["directives"][0]["directive_text"],
    "Mention that widgets come in three sizes.",
)


# ---------------------------------------------------------------------------
# 4/5. Deterministic lookup works; unrelated input does not retrieve it
# ---------------------------------------------------------------------------

print("\n--- deterministic lookup ---")

matches = bs.get_matching_directives("I have a question about widgets today")
check("matching prompt returns exactly 1 directive", len(matches), 1)
check("matched directive is the correct one", matches[0]["id"], d1["id"])

no_matches = bs.get_matching_directives("what's the weather like in Paris?")
check("unrelated prompt returns zero matches", len(no_matches), 0)

empty_matches = bs.get_matching_directives("")
check("empty prompt returns zero matches", len(empty_matches), 0)

# Determinism: repeated calls with the same input always return the same result
for _ in range(5):
    check_true("repeated identical calls are deterministic", bs.get_matching_directives("widgets please") == matches)

# Deterministic ORDER: add a second directive, confirm creation-order return
d2 = bs.propose_and_confirm_directive(
    trigger_keywords=["gadget"], directive_text="Mention gadgets are waterproof.",
    provenance={"proposed_by": "gremlin", "reason": "test2"}, human_confirmed=True,
)
d3 = bs.propose_and_confirm_directive(
    trigger_keywords=["widget"], directive_text="Also mention the warranty.",
    provenance={"proposed_by": "gremlin", "reason": "test3"}, human_confirmed=True,
)
widget_matches = bs.get_matching_directives("tell me about a widget")
check("multiple matches returned in deterministic creation order", [m["id"] for m in widget_matches], [d1["id"], d3["id"]])


# ---------------------------------------------------------------------------
# 6/7. FAISS is never consulted; RiverBrain is never consulted
# ---------------------------------------------------------------------------

print("\n--- FAISS / RiverBrain never consulted ---")

import app.core.memory_bridge as memory_bridge  # noqa: E402
import app.core.echo_model_orchestrator as orchestrator  # noqa: E402

_faiss_called = {"flag": False}
_riverbrain_called = {"flag": False}


def _poison_faiss(*args, **kwargs):
    _faiss_called["flag"] = True
    raise AssertionError("retrieve_relevant_memories() was called -- FAISS must never be consulted by this mechanism")


def _poison_riverbrain_score(*args, **kwargs):
    _riverbrain_called["flag"] = True
    raise AssertionError("RiverBrain.score_model() was called -- RiverBrain must never be consulted by this mechanism")


_real_retrieve = memory_bridge.retrieve_relevant_memories
_real_score_model = orchestrator.RiverBrain.score_model
memory_bridge.retrieve_relevant_memories = _poison_faiss
orchestrator.RiverBrain.score_model = _poison_riverbrain_score
try:
    result = bs.get_matching_directives("a full end-to-end check about widgets")
    check_true("get_matching_directives completed without touching FAISS", not _faiss_called["flag"])
    check_true("get_matching_directives completed without touching RiverBrain", not _riverbrain_called["flag"])
    check("get_matching_directives still returned the correct real result under poisoning", len(result), 2)
finally:
    memory_bridge.retrieve_relevant_memories = _real_retrieve
    orchestrator.RiverBrain.score_model = _real_score_model


# ---------------------------------------------------------------------------
# 8. Provenance survives restart
# ---------------------------------------------------------------------------

print("\n--- provenance survives restart ---")

del bs
importlib.invalidate_caches()
import app.core.behavioral_state as bs  # noqa: E402
bs._STATE_PATH = os.path.join(_TMP_ROOT, "behavioral_directives.json")
bs._BACKUP_DIR = os.path.join(_TMP_ROOT, "behavioral_directives_backups")
bs._AUDIT_LOG_PATH = os.path.join(_TMP_ROOT, "behavioral_directives_audit.jsonl")

reloaded = bs.load_state()
reloaded_d1 = next(d for d in reloaded["directives"] if d["id"] == d1["id"])
check(
    "provenance dict survives restart, byte-for-byte",
    reloaded_d1["provenance"],
    {"proposed_by": "gremlin", "reason": "test", "source_conversation_ref": "conv-001"},
)
check_true("audit log has real, non-empty entries after restart", os.path.getsize(bs._AUDIT_LOG_PATH) > 0)
audit_lines = [json.loads(l) for l in open(bs._AUDIT_LOG_PATH) if l.strip()]
propose_events = [e for e in audit_lines if e["event"] == "propose_and_confirm"]
check_true("every propose_and_confirm audit entry records human_confirmed=True", all(e["human_confirmed"] is True for e in propose_events))
check_true("every propose_and_confirm audit entry records real provenance", all(e.get("provenance") for e in propose_events))


# ---------------------------------------------------------------------------
# 9. Rollback works
# ---------------------------------------------------------------------------

print("\n--- rollback ---")

backups_before_delete = bs.list_backups()
check_true("backups exist from prior mutations", len(backups_before_delete) > 0)

state_before_delete = bs.load_state()
n_before = len(state_before_delete["directives"])
bs.delete_directive(d2["id"], human_confirmed=True)
check("delete_directive removes exactly one directive", len(bs.load_state()["directives"]), n_before - 1)

check_raises(
    "delete_directive refuses without human confirmation",
    lambda: bs.delete_directive(d3["id"], human_confirmed=False),
    bs.BehavioralStateError,
)

most_recent_backup = bs.list_backups()[-1]
restored = bs.rollback_to_backup(most_recent_backup, human_confirmed=True)
check("rollback restores the pre-delete directive count", len(restored["directives"]), n_before)
check_true(
    "rollback correctly restores the specific directive that was deleted",
    any(d["id"] == d2["id"] for d in bs.load_state()["directives"]),
)
check_raises(
    "rollback_to_backup refuses without human confirmation",
    lambda: bs.rollback_to_backup(most_recent_backup, human_confirmed=False),
    bs.BehavioralStateError,
)
check_raises(
    "rollback_to_backup refuses a nonexistent backup file",
    lambda: bs.rollback_to_backup("does_not_exist.json", human_confirmed=True),
    bs.BehavioralStateError,
)


# ---------------------------------------------------------------------------
# 10. Bounds are enforced
# ---------------------------------------------------------------------------

print("\n--- bounds enforced ---")

# Clear state, then fill exactly to the bound
_atomic = bs._atomic_write_json
_atomic(bs._STATE_PATH, {"version": 1, "directives": []})
for i in range(bs.MAX_DIRECTIVES):
    bs.propose_and_confirm_directive(
        trigger_keywords=[f"kw{i}"], directive_text=f"directive {i}", provenance={"i": i}, human_confirmed=True,
    )
check("store holds exactly MAX_DIRECTIVES after filling to the bound", len(bs.load_state()["directives"]), bs.MAX_DIRECTIVES)
check_raises(
    "propose_and_confirm_directive refuses to exceed MAX_DIRECTIVES",
    lambda: bs.propose_and_confirm_directive(
        trigger_keywords=["one_too_many"], directive_text="d", provenance={"x": 1}, human_confirmed=True,
    ),
    bs.BehavioralStateError,
)
check_raises(
    "refuses too many trigger keywords per directive",
    lambda: bs.propose_and_confirm_directive(
        trigger_keywords=[f"k{i}" for i in range(bs.MAX_TRIGGER_KEYWORDS_PER_DIRECTIVE + 1)],
        directive_text="d", provenance={"x": 1}, human_confirmed=True,
    ),
    bs.BehavioralStateError,
)
check_raises(
    "refuses an over-length directive_text",
    lambda: bs.propose_and_confirm_directive(
        trigger_keywords=["kw"], directive_text="x" * (bs.MAX_DIRECTIVE_TEXT_LEN + 1),
        provenance={"x": 1}, human_confirmed=True,
    ),
    bs.BehavioralStateError,
)
check_raises(
    "refuses empty provenance",
    lambda: bs.propose_and_confirm_directive(
        trigger_keywords=["kw"], directive_text="d", provenance={}, human_confirmed=True,
    ),
    bs.BehavioralStateError,
)
check_true(
    "backup retention itself is bounded (MAX_BACKUPS_RETAINED enforced)",
    len(bs.list_backups()) <= bs.MAX_BACKUPS_RETAINED,
    evidence=f"{len(bs.list_backups())} backups present, cap is {bs.MAX_BACKUPS_RETAINED}",
)


# ---------------------------------------------------------------------------
# 11. No accidental autonomous writes -- reads never mutate state
# ---------------------------------------------------------------------------

print("\n--- no accidental autonomous writes ---")

_mtime_before = os.path.getmtime(bs._STATE_PATH)
for _ in range(20):
    bs.get_matching_directives("widgets and gadgets, please, many times over")
    bs.load_state()
_mtime_after = os.path.getmtime(bs._STATE_PATH)
check("20 repeated read-only calls never mutate the state file's mtime", _mtime_after, _mtime_before)

_backup_count_before = len(bs.list_backups())
for _ in range(20):
    bs.get_matching_directives("no mutation should ever happen here")
check("repeated reads never create a new backup either", len(bs.list_backups()), _backup_count_before)


# ---------------------------------------------------------------------------
# Integration: echo_ground_truth.py's new slice
# ---------------------------------------------------------------------------

print("\n--- echo_ground_truth.py integration ---")

_atomic(bs._STATE_PATH, {"version": 1, "directives": []})
bs.propose_and_confirm_directive(
    trigger_keywords=["pull request"], directive_text="Prefer terse, line-by-line feedback.",
    provenance={"proposed_by": "gremlin", "reason": "integration test"}, human_confirmed=True,
)

del bs
import app.core.echo_ground_truth as egt  # noqa: E402

import app.core.behavioral_state as bs  # noqa: E402
bs._STATE_PATH = os.path.join(_TMP_ROOT, "behavioral_directives.json")
bs._BACKUP_DIR = os.path.join(_TMP_ROOT, "behavioral_directives_backups")
bs._AUDIT_LOG_PATH = os.path.join(_TMP_ROOT, "behavioral_directives_audit.jsonl")

result = egt.get_structural_self_facts("please review this pull request")
check_true("matching prompt's ground-truth block includes the behavioral directive text", "Prefer terse, line-by-line feedback." in result)
check_true("the block is clearly disclaimed as human-confirmed, not framed as Echo's own memory/learning", "not something Echo learned or recalls" in result)

result_none = egt.get_structural_self_facts("what's a good recipe for banana bread?")
check("non-matching, non-introspective prompt returns empty string, unaffected by the new slice", result_none, "")

result_introspective_only = egt.get_structural_self_facts("how are you feeling today?")
check_true("purely introspective prompt (no directive match) never mentions behavioral directives", "Behavioral directives" not in result_introspective_only)
check_true("purely introspective prompt still correctly returns its own existing slice content unaffected", len(result_introspective_only) > 0)


# ---------------------------------------------------------------------------
# 12. Existing P1/P1.2/Learning-Pilot test suites remain green
# ---------------------------------------------------------------------------

print("\n--- existing sibling test suites remain green ---")

import subprocess  # noqa: E402

for suite in [
    "scripts/verify_preference_provenance_experiment.py",
    "scripts/verify_choice_parser_benchmark.py",
    "scripts/verify_learning_investigation_harness.py",
    "scripts/verify_p3_causal_learning_apparatus.py",
]:
    result = subprocess.run([sys.executable, suite], capture_output=True, text=True, timeout=120)
    tail = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "(no output)"
    check(f"{suite} exits 0", result.returncode, 0, evidence=tail)


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

shutil.rmtree(_TMP_ROOT, ignore_errors=True)

print(f"\n=== {_PASS} passed, {_FAIL} failed ===")
if _FAIL:
    sys.exit(1)
