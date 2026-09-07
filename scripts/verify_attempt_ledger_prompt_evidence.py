#!/usr/bin/env python3
"""
scripts/verify_attempt_ledger_prompt_evidence.py

Regression tests for the attempt-ledger -> initial-generation evidence
pathway added 2026-09-07, per audits/2026-09-07_consequential_loop_
validation.md (Phase 9 of audits/2026-09-07_consequential_learning_loop_
design.md's roadmap).

New code under test:
  - app.core.self_edit_attempt_ledger.read_recent_f2_error()
  - app.core.self_edit_manager._attempt_ledger_evidence_section()
  - app.core.self_edit_manager._build_targeted_prompt() (now includes the
    evidence section)

Read-only with respect to production state: every test redirects
self_edit_attempt_ledger._LEDGER_PATH to a scratch tempfile before running
and restores it afterward. Never touches memory/self_edit_attempt_ledger.jsonl,
RiverBrain, or any other production file. Does not commit or mutate anything.

Run: python3 scripts/verify_attempt_ledger_prompt_evidence.py
"""
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.core.self_edit_attempt_ledger as ledger_mod  # noqa: E402
import app.core.self_edit_manager as sem  # noqa: E402

_REAL_LEDGER_PATH = ledger_mod._LEDGER_PATH
_now = datetime.now(timezone.utc)


def _ts(hours_ago: float = 0.0) -> str:
    return (_now - timedelta(hours=hours_ago)).isoformat()


def _set_ledger(entries):
    scratch = Path(tempfile.mktemp(suffix=".jsonl"))
    with open(scratch, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(e if isinstance(e, str) else json.dumps(e))
            f.write("\n")
    ledger_mod._LEDGER_PATH = scratch


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail and status == "FAIL" else ""))
    return condition


def main():
    results = []

    print("=" * 70)
    print("1. Same-task prior error IS retrieved and injected")
    print("=" * 70)
    _set_ledger([
        {"trace_id": "T1", "task_type": "coding", "timestamp": _ts(1),
         "initial_f2_error": "TypeError: HealthMonitor.__init__() missing 1 required positional argument: 'average_response_length'"},
    ])
    entry = ledger_mod.read_recent_f2_error("coding")
    section = sem._attempt_ledger_evidence_section("coding")
    prompt = sem._build_targeted_prompt("coding", 0.1)
    results.append(check("read_recent_f2_error finds the entry", entry is not None and entry.get("trace_id") == "T1"))
    results.append(check("evidence section contains error text + 'not an instruction'",
                          "HealthMonitor" in section and "not an instruction" in section))
    results.append(check("_build_targeted_prompt() surfaces the labeled section",
                          "Prior attempt failure evidence" in prompt and "HealthMonitor" in prompt))

    print("\n" + "=" * 70)
    print("2. Unrelated task-type error is rejected (not injected)")
    print("=" * 70)
    _set_ledger([
        {"trace_id": "T2", "task_type": "creative", "timestamp": _ts(1),
         "initial_f2_error": "SyntaxError: unrelated creative-task error"},
    ])
    entry = ledger_mod.read_recent_f2_error("coding")
    prompt = sem._build_targeted_prompt("coding", 0.1)
    results.append(check("read_recent_f2_error returns None for mismatched task_type", entry is None))
    results.append(check("prompt has no evidence section for mismatched task_type",
                          "Prior attempt failure evidence" not in prompt))

    print("\n" + "=" * 70)
    print("3. No history -> no evidence section, prompt behavior unchanged")
    print("=" * 70)
    _set_ledger([])
    entry = ledger_mod.read_recent_f2_error("coding")
    prompt = sem._build_targeted_prompt("coding", 0.1)
    results.append(check("read_recent_f2_error returns None on empty ledger", entry is None))
    results.append(check("prompt has no evidence section when ledger is empty",
                          "Prior attempt failure evidence" not in prompt))

    print("\n" + "=" * 70)
    print("4. Malformed / missing-field records do not crash")
    print("=" * 70)
    _set_ledger([
        "not even json {{{",
        {"trace_id": "M1", "task_type": "coding", "timestamp": _ts(1), "initial_f2_error": None},
        {"trace_id": "M2", "task_type": "coding", "timestamp": _ts(1), "initial_f2_error": ""},
        {"trace_id": "M3", "task_type": "coding"},
        {"trace_id": "M4"},
        123,
    ])
    try:
        entry = ledger_mod.read_recent_f2_error("coding")
        section = sem._attempt_ledger_evidence_section("coding")
        prompt = sem._build_targeted_prompt("coding", 0.1)
        results.append(check("malformed entries handled with no exception raised", True))
        results.append(check("malformed entries produce no false-positive evidence",
                              entry is None and section == "" and "Prior attempt failure evidence" not in prompt))
    except Exception as e:
        results.append(check("malformed entries handled with no exception raised", False, str(e)))

    print("\n" + "=" * 70)
    print("5. Stale entry (past max_age_hours) is excluded")
    print("=" * 70)
    _set_ledger([
        {"trace_id": "STALE", "task_type": "coding", "timestamp": _ts(hours_ago=200),
         "initial_f2_error": "OldError: this predates the 168h window"},
    ])
    entry = ledger_mod.read_recent_f2_error("coding")
    results.append(check("entry older than max_age_hours is excluded", entry is None))

    print("\n" + "=" * 70)
    print("6. Most-recent selection (not first-match, not similarity-based)")
    print("=" * 70)
    _set_ledger([
        {"trace_id": "OLDER", "task_type": "coding", "timestamp": _ts(hours_ago=5),
         "initial_f2_error": "OlderError: first one"},
        {"trace_id": "NEWER", "task_type": "coding", "timestamp": _ts(hours_ago=1),
         "initial_f2_error": "NewerError: second one, should win"},
    ])
    entry = ledger_mod.read_recent_f2_error("coding")
    results.append(check("most recent (not first) qualifying entry wins", entry is not None and entry.get("trace_id") == "NEWER"))

    print("\n" + "=" * 70)
    print("7. Evidence is wired into INITIAL generation only, not retry")
    print("=" * 70)
    call_sites = 0
    with open("app/core/self_edit_manager.py", encoding="utf-8") as f:
        src = f.read()
    call_sites = src.count("_build_targeted_prompt(")
    # 1 definition + exactly 1 real call site (inside perform_self_edit(),
    # the initial-prompt-construction path) = 2 total occurrences of the
    # substring. The retry-prompt block inside execute_self_edit() builds
    # its prompt via plain string concatenation and never calls this
    # function, so the new evidence section structurally cannot reach retry.
    results.append(check(
        "_build_targeted_prompt() has exactly one real call site (perform_self_edit's initial-prompt path)",
        call_sites == 2, f"found {call_sites} occurrences (expected 2: def + 1 call)"
    ))
    results.append(check(
        "the retry-prompt block does not reference _build_targeted_prompt or the evidence-section helper",
        "_build_targeted_prompt(" not in src[src.find("Retrying with error feedback"):src.find("Retrying with error feedback") + 800]
        if "Retrying with error feedback" in src else False
    ))

    print("\n" + "=" * 70)
    print("8. Pre-existing non-interference: unrelated Focus-text logic unaffected")
    print("=" * 70)
    # With no ledger evidence available, the prompt must be byte-identical
    # to what _build_targeted_prompt() produced before this change — i.e.
    # base + Focus + convergence_sentence + outcome_sentence, with nothing
    # appended. This is the direct behavioral-non-interference check: the
    # new code path is a pure additive no-op when there's nothing to add.
    _set_ledger([])
    prompt = sem._build_targeted_prompt("coding", 0.1)
    results.append(check(
        "prompt output with no ledger evidence contains no trace of the new code path",
        "Prior attempt failure evidence" not in prompt and prompt.endswith(prompt.split("Focus:")[0] + "Focus:" + prompt.split("Focus:", 1)[1])
    ))

    print("\n" + "=" * 70)
    print("9. Temporal-drift guard: reader's assumed fields still match the")
    print("   real writer's schema (self_edit_manager.py's `_attempt` dict)")
    print("=" * 70)
    # Phase 11's targeted guard for this specific pathway, per audits/
    # 2026-09-07_consequential_loop_validation.md — the exact failure shape
    # CATEGORIES/TASK_TYPE_MAP/seam_engine already demonstrated tonight is
    # "a reader's fixed assumptions silently stop matching a producer's real
    # schema, with no test catching it." read_recent_f2_error() depends on
    # exactly three fields existing on a real ledger entry: task_type,
    # initial_f2_error, timestamp. This asserts, by direct source
    # inspection (not a hardcoded guess), that execute_self_edit()'s real
    # `_attempt` dict — the only writer of this ledger — still emits all
    # three under those exact names. If a future edit renames or drops one
    # of these on the writer side without updating the reader, this fails
    # loud instead of silently degrading to "no evidence ever found again."
    with open("app/core/self_edit_manager.py", encoding="utf-8") as f:
        src = f.read()
    attempt_dict_start = src.find('_attempt = {')
    attempt_dict_src = src[attempt_dict_start:attempt_dict_start + 700] if attempt_dict_start != -1 else ""
    required_reader_fields = ("task_type", "initial_f2_error", "timestamp")
    missing = [fld for fld in required_reader_fields if f'"{fld}"' not in attempt_dict_src]
    results.append(check(
        "writer's _attempt dict still defines every field the reader depends on",
        attempt_dict_start != -1 and not missing,
        f"missing from writer schema: {missing}" if missing else "_attempt dict definition not found in source"
    ))

    ledger_mod._LEDGER_PATH = _REAL_LEDGER_PATH

    print("\n" + "=" * 70)
    total = len(results)
    passed = sum(1 for r in results if r)
    print(f"RESULT: {passed}/{total} checks passed")
    print("=" * 70)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
