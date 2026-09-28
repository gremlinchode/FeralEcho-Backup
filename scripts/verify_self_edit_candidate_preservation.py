#!/usr/bin/env python3
"""
scripts/verify_self_edit_candidate_preservation.py

Verifies the candidate-evidence-preservation change qualified in
audits/2026-09-22_self_edit_candidate_logging_qualification.md and
implemented the same day in app/core/self_edit_manager.py /
app/core/self_edit_attempt_ledger.py.

Read-only with respect to production state: every test redirects
self_edit_attempt_ledger._LEDGER_PATH and self_edit_manager.SELF_EDIT_FILE
to scratch tempfiles, and monkeypatches every real external dependency
(model calls, RiverBrain, real sandbox execution, real journal/reflection
writes) so the REAL execute_self_edit() code path runs and is inspected,
without ever touching Ollama, RiverBrain, or any file under memory/.
Never touches memory/self_edit_attempt_ledger.jsonl, river_brain.pkl,
reflection_shard.jsonl, or SELF_EDIT.log.

Run: python3 scripts/verify_self_edit_candidate_preservation.py
"""
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.core.self_edit_attempt_ledger as ledger_mod  # noqa: E402
import app.core.self_edit_manager as sem  # noqa: E402

results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""), flush=True)


class _DummyRiver:
    def learn(self, *a, **k): pass
    def learn_from_sandbox_outcome(self, *a, **k): pass


def _patch_all(sandbox_outcomes, retry_code_value="RETRY_CODE_MARKER\ndef fixed(): return 2"):
    """sandbox_outcomes: list of (success, error) tuples consumed in order by
    successive test_code_in_sandbox() calls (initial, then retry if any)."""
    calls = {"i": 0}

    def _fake_sandbox(code, *a, **k):
        i = calls["i"]; calls["i"] += 1
        return sandbox_outcomes[min(i, len(sandbox_outcomes) - 1)]

    patches = {
        "plan_code_logic": lambda *a, **k: "PLAN TEXT",
        "generate_code_from_plan": lambda *a, **k: ("INITIAL_CODE_MARKER\ndef broken(): return 1/0", "mock-model-A"),
        "test_code_in_sandbox": _fake_sandbox,
        "choose_model": lambda *a, **k: ("mock-model-B", {}),
        "echo_query": lambda *a, **k: retry_code_value,
        "get_river_brain": lambda: _DummyRiver(),
        "advise_before_edit": lambda: "",
        "_validate_imports": lambda code: (True, None),
        "scan_for_unsafe_operations": lambda code: None,
        "_stage_and_import_test": lambda code, staging_file=None: (False, "mocked: staging not exercised by this test"),
        "save_reflection": lambda entry: None,
        "append_to_journal": lambda *a, **k: None,
        "detect_task_type": lambda prompt: "coding",
        "_prune_stale_staging_files": lambda: None,
    }
    saved = {name: getattr(sem, name) for name in patches}
    for name, fn in patches.items():
        setattr(sem, name, fn)
    return saved, calls


def _unpatch(saved):
    for name, fn in saved.items():
        setattr(sem, name, fn)


def _run_attempt(sandbox_outcomes, retry_code_value="RETRY_CODE_MARKER\ndef fixed(): return 2", parent_content=b"PARENT FILE CONTENT v1\n"):
    """Runs the REAL execute_self_edit() with everything external mocked, ledger
    and SELF_EDIT_FILE redirected to scratch files. Returns the real ledger row written."""
    ledger_fd, ledger_path = tempfile.mkstemp(suffix=".jsonl")
    os.close(ledger_fd)
    os.remove(ledger_path)  # record_attempt() creates it fresh
    parent_fd, parent_path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(parent_fd, "wb") as f:
        f.write(parent_content)

    saved_ledger_path = ledger_mod._LEDGER_PATH
    saved_self_edit_file = sem.SELF_EDIT_FILE
    from pathlib import Path
    ledger_mod._LEDGER_PATH = Path(ledger_path)
    sem.SELF_EDIT_FILE = parent_path

    saved_patches, calls = _patch_all(sandbox_outcomes, retry_code_value)
    try:
        sem.execute_self_edit("test prompt for candidate-preservation verification", dry_run=False)
    finally:
        _unpatch(saved_patches)
        ledger_mod._LEDGER_PATH = saved_ledger_path
        sem.SELF_EDIT_FILE = saved_self_edit_file

    rows = [json.loads(l) for l in open(ledger_path)] if os.path.exists(ledger_path) else []
    os.remove(ledger_path)
    os.remove(parent_path)
    return rows, parent_content


# ---------- 1. Initial candidate preservation (fail, no retry reaches success) ----------
rows, parent_content = _run_attempt(sandbox_outcomes=[(False, "TypeError: boom"), (False, "TypeError: still broken")])
check("exactly one ledger row written per attempt", len(rows) == 1, str(len(rows)))
row = rows[0] if rows else {}
check("initial_candidate_code preserved exactly", row.get("initial_candidate_code") == "INITIAL_CODE_MARKER\ndef broken(): return 1/0")
check("initial_f2_outcome is False (real failure recorded)", row.get("initial_f2_outcome") is False)
check("initial_f2_error is the real sandbox error", row.get("initial_f2_error") == "TypeError: boom")

# ---------- 2. Retry preservation: initial candidate stays intact, retry is separate ----------
check("retry_candidate_code preserved exactly, distinct from initial", row.get("retry_candidate_code") == "RETRY_CODE_MARKER\ndef fixed(): return 2")
check("initial_candidate_code NOT overwritten by retry's code", row.get("initial_candidate_code") != row.get("retry_candidate_code") and row.get("initial_candidate_code") == "INITIAL_CODE_MARKER\ndef broken(): return 1/0")
check("retry_occurred is True", row.get("retry_occurred") is True)
check("retry_f2_error is the real retry sandbox error", row.get("retry_f2_error") == "TypeError: still broken")

# ---------- 2b. Retry succeeds: initial candidate STILL survives (the original overwrite bug this closes) ----------
rows2, _ = _run_attempt(sandbox_outcomes=[(False, "NameError: x"), (True, None)])
row2 = rows2[0] if rows2 else {}
check("retry-succeeds case: initial_candidate_code still preserved (the historical bug this fixes)", row2.get("initial_candidate_code") == "INITIAL_CODE_MARKER\ndef broken(): return 1/0")
check("retry-succeeds case: retry_candidate_code also preserved", row2.get("retry_candidate_code") == "RETRY_CODE_MARKER\ndef fixed(): return 2")
check("retry-succeeds case: retry_f2_outcome True, retry_f2_error None", row2.get("retry_f2_outcome") is True and row2.get("retry_f2_error") is None)
check("retry-succeeds case: final_f2_outcome reflects the real recovered success", row2.get("final_f2_outcome") is True)

# ---------- 3. No-retry behavior: initial succeeds outright, remains valid and unambiguous ----------
rows3, _ = _run_attempt(sandbox_outcomes=[(True, None)])
row3 = rows3[0] if rows3 else {}
check("no-retry success: initial_candidate_code present", row3.get("initial_candidate_code") == "INITIAL_CODE_MARKER\ndef broken(): return 1/0")
check("no-retry success: retry_candidate_code stays None (no retry ever ran)", row3.get("retry_candidate_code") is None)
check("no-retry success: retry_occurred is False", row3.get("retry_occurred") is False)
check("no-retry success: retry_f2_outcome/error stay None (never falsely implies a retry executed)", row3.get("retry_f2_outcome") is None and row3.get("retry_f2_error") is None)

# ---------- 3b. Retry generates empty code: retry_occurred True, but nothing falsely implied as executed ----------
rows4, _ = _run_attempt(sandbox_outcomes=[(False, "err")], retry_code_value="")
row4 = rows4[0] if rows4 else {}
check("empty-retry case: retry_candidate_code stays None (nothing was actually executed)", row4.get("retry_candidate_code") is None)
check("empty-retry case: retry_f2_outcome/error stay None (no execution -> no false outcome)", row4.get("retry_f2_outcome") is None and row4.get("retry_f2_error") is None)
check("empty-retry case: initial_candidate_code still correctly preserved", row4.get("initial_candidate_code") == "INITIAL_CODE_MARKER\ndef broken(): return 1/0")

# ---------- 4. Parent/baseline identity: matches the real, independently-computed hash ----------
expected_hash = hashlib.sha256(parent_content).hexdigest()
check("parent_baseline_hash_at_generation matches an independently-computed sha256 of the exact parent bytes", row.get("parent_baseline_hash_at_generation") == expected_hash, f"got {row.get('parent_baseline_hash_at_generation')}, expected {expected_hash}")
different_content = b"A DIFFERENT PARENT FILE\n"
rows5, _ = _run_attempt(sandbox_outcomes=[(True, None)], parent_content=different_content)
row5 = rows5[0] if rows5 else {}
check("parent hash changes when the underlying parent file's real content changes", row5.get("parent_baseline_hash_at_generation") == hashlib.sha256(different_content).hexdigest() and row5.get("parent_baseline_hash_at_generation") != expected_hash)

# ---------- 5. Backward compatibility: historical rows without the new fields remain readable ----------
old_row = {"trace_id": "old-1", "task_type": "coding", "timestamp": __import__("datetime").datetime.utcnow().isoformat(), "initial_f2_outcome": False, "initial_f2_error": "OldError: x", "retry_occurred": False, "retry_f2_outcome": None, "retry_f2_error": None, "final_f2_outcome": False, "fitness_score": None, "production_score": None, "fitness_decision": None, "deployed": False, "terminal_state": "staging_import_failed"}
fd, old_ledger_path = tempfile.mkstemp(suffix=".jsonl")
with os.fdopen(fd, "w") as f:
    f.write(json.dumps(old_row) + "\n")
saved_path = ledger_mod._LEDGER_PATH
from pathlib import Path as _P
ledger_mod._LEDGER_PATH = _P(old_ledger_path)
try:
    result = ledger_mod.read_recent_f2_error("coding")
    check("read_recent_f2_error() still reads a historical row lacking the new fields, no crash", result is not None and result.get("initial_f2_error") == "OldError: x")
    check(".get() access to a missing new field on an old row returns None cleanly", result.get("initial_candidate_code") is None)
finally:
    ledger_mod._LEDGER_PATH = saved_path
    os.remove(old_ledger_path)

# ---------- 6. Generation isolation: _attempt_ledger_evidence_section() must NOT expose either candidate field ----------
fd, iso_ledger_path = tempfile.mkstemp(suffix=".jsonl")
new_row_with_code = dict(old_row)
new_row_with_code.update({
    "trace_id": "iso-1", "timestamp": "2026-09-22T00:00:00",
    "initial_candidate_code": "SECRET_CANDIDATE_MARKER_SHOULD_NEVER_LEAK\ndef leaked(): pass\n",
    "retry_candidate_code": "SECRET_RETRY_MARKER_SHOULD_NEVER_LEAK\n",
})
with os.fdopen(fd, "w") as f:
    f.write(json.dumps(new_row_with_code) + "\n")
saved_path = ledger_mod._LEDGER_PATH
ledger_mod._LEDGER_PATH = _P(iso_ledger_path)
try:
    section_text = sem._attempt_ledger_evidence_section("coding")
    check("_attempt_ledger_evidence_section() output contains the real initial_f2_error text", "OldError: x" in section_text)
    check("_attempt_ledger_evidence_section() output does NOT contain initial_candidate_code text (BEHAVIORAL test, not just reading the source)", "SECRET_CANDIDATE_MARKER_SHOULD_NEVER_LEAK" not in section_text)
    check("_attempt_ledger_evidence_section() output does NOT contain retry_candidate_code text", "SECRET_RETRY_MARKER_SHOULD_NEVER_LEAK" not in section_text)
    # Also confirm the lower-level reader itself DOES carry the fields (proving the isolation
    # is enforced by the extraction function, not by the fields being absent from the read)
    raw = ledger_mod.read_recent_f2_error("coding")
    check("read_recent_f2_error() DOES return the full row including candidate code (confirms isolation is enforced by the extractor, not by data absence)", raw is not None and "SECRET_CANDIDATE_MARKER_SHOULD_NEVER_LEAK" in (raw.get("initial_candidate_code") or ""))
finally:
    ledger_mod._LEDGER_PATH = saved_path
    os.remove(iso_ledger_path)

# ---------- 7. Existing behavior: re-run the pre-existing evidence-pathway suite unchanged ----------
import subprocess
existing = subprocess.run([sys.executable, "-I", "-B", "scripts/verify_attempt_ledger_prompt_evidence.py"], capture_output=True, text=True)
check("pre-existing scripts/verify_attempt_ledger_prompt_evidence.py suite still passes unchanged", existing.returncode == 0, existing.stdout[-500:] + existing.stderr[-500:])

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
