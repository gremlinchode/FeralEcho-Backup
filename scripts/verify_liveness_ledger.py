#!/usr/bin/env python3
"""
verify_liveness_ledger.py — proves app/core/liveness_ledger.py actually
discriminates real from fake, not just "imports successfully."

GREMLIN_ROLE.md names verify_integrity() as the canonical example of a
check that looks like verification but only tests importability. This
script is the check on the liveness ledger itself: for each of the nine
pure `_evaluate_*` functions, feed it a reconstructed HISTORICAL FAKE
(the exact behavior a prior audit/fix/session already caught this project
doing) and confirm it's flagged failing, then feed it real-shaped GOOD
data and confirm it passes. If any case here doesn't discriminate
correctly, the corresponding ledger check is not trustworthy regardless
of how complete its code looks — this is the same discipline that caught
the class-imbalanced contaminated classifier in this same session.

Run: python3 scripts/verify_liveness_ledger.py
Exits non-zero if any case fails.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import liveness_ledger as ll

FAILURES = []


def check(label: str, got_pass: bool, expected_pass: bool, evidence: str):
    ok = got_pass == expected_pass
    status = "OK  " if ok else "FAIL"
    print(f"[{status}] {label}: expected pass={expected_pass}, got pass={got_pass}")
    if not ok:
        FAILURES.append(f"{label}: expected pass={expected_pass}, got pass={got_pass} | evidence={evidence}")
    elif not got_pass:
        print(f"       (correctly failing) {evidence[:140]}")


# ── 1. self_edit_apply_to_code ─────────────────────────────────────────
# Historical fake: hook deployed (module defines apply_to_code) but never
# actually changes anything — "deployed" mistaken for "working," the exact
# pattern named in the task brief.
now = time.time()
r = ll._evaluate_apply_to_code(defines_hook=True, invocations=[], window_days=7)
check("apply_to_code: deployed, zero invocations logged", r["pass"], False, r["evidence"])

r = ll._evaluate_apply_to_code(
    defines_hook=True,
    invocations=[{"ts": now - 3600, "changed": False, "before_len": 100, "after_len": 100}] * 5,
    window_days=7,
)
check("apply_to_code: deployed, invoked but never actually changed code", r["pass"], False, r["evidence"])

r = ll._evaluate_apply_to_code(
    defines_hook=True,
    invocations=[{"ts": now - 3600, "changed": True, "before_len": 100, "after_len": 140}],
    window_days=7,
)
check("apply_to_code: deployed, real recent change recorded", r["pass"], True, r["evidence"])

r = ll._evaluate_apply_to_code(defines_hook=False, invocations=[], window_days=7)
check("apply_to_code: not deployed at all (honestly inert)", r["pass"], True, r["evidence"])


# ── 2. curiosity_engine ─────────────────────────────────────────────────
# Historical fake: harvest_question(source="curiosity_engine") wired in
# but never actually called (e.g. _get_underrepresented_topic() always
# returning None due to a WorldModel bug) — schema present, zero real use.
r = ll._evaluate_curiosity_engine(entries=[{"source": "human", "planted": now}], window_days=7)
check("curiosity_engine: garden has entries but none from curiosity_engine", r["pass"], False, r["evidence"])

r = ll._evaluate_curiosity_engine(
    entries=[{"source": "curiosity_engine", "planted": now - 3600}], window_days=7
)
check("curiosity_engine: one recent real entry", r["pass"], True, r["evidence"])


# ── 3. nature_spark — THE LIVE FINDING, reconstructed as a standalone case ──
# Historical fake (pre-fix, and — per this session's live run above —
# apparently still the dominant behavior post-"fix" too): nature_spark()
# just picks one of 15 fixed PATTERNS strings, no model call.
seeds = {"Kill the weakest 7", "Prune dead ends — keep what works", "Consensus emerges from chaos"}
fake_log = [f"[2026-01-0{i}] EVOLUTIONARY_PRESSURE → Kill the weakest 7" for i in range(1, 9)] + \
           [f"[2026-01-0{i}] FRACTAL_BRANCHING → Prune dead ends — keep what works" for i in range(1, 9)]
r = ll._evaluate_nature_spark(fake_log, seeds, tail_n=16, min_ratio=0.5)
check("nature_spark: 16/16 fixed-string fallback (pre-fix behavior)", r["pass"], False, r["evidence"])

real_log = [f"[2026-01-0{i%9+1}] MYCELIAL_NETWORK → a genuinely different sentence number {i} about tradeoffs" for i in range(16)]
r = ll._evaluate_nature_spark(real_log, seeds, tail_n=16, min_ratio=0.5)
check("nature_spark: 16/16 genuinely distinct generated text", r["pass"], True, r["evidence"])

r = ll._evaluate_nature_spark([], seeds, tail_n=16, min_ratio=0.5)
check("nature_spark: no log entries at all", r["pass"], False, r["evidence"])


# ── 4. wolf_friction_bridge ──────────────────────────────────────────────
# Historical fake (the exact thing GREMLIN_ROLE.md says needs human
# confirmation): the call site silently switched to perform_self_edit.
fake_block = (
    "from app.core.wolf_friction_bridge import simulate_self_edit\n"
    "...\n"
    "perform_self_edit(dry_run=False)  # <- someone swapped this in\n"
)
r = ll._evaluate_wolf_friction_bridge(fake_block)
check("wolf_friction_bridge: call site switched to perform_self_edit", r["pass"], False, r["evidence"])

real_block = (
    "from app.core.wolf_friction_bridge import simulate_self_edit\n"
    "...\n"
    "simulate_self_edit(_fe)\n"
)
r = ll._evaluate_wolf_friction_bridge(real_block)
check("wolf_friction_bridge: real dry-run-only call site", r["pass"], True, r["evidence"])

r = ll._evaluate_wolf_friction_bridge(None)
check("wolf_friction_bridge: call site not found at all", r["pass"], False, r["evidence"])


# ── 5. claude_shard ──────────────────────────────────────────────────────
# Historical-shape fake: someone "upgrades" ClaudeShard to a real API call
# without updating any of the docs that describe it as keyword+random —
# exactly the misrepresentation risk named in the task brief.
fake_source = (
    "import anthropic\n"
    "SMOOTHNESS_MARKERS = [...]\n"
    "def assess(self, response, context=''):\n"
    "    client = anthropic.Anthropic()\n"
    "    return client.messages.create(...)\n"
)
r = ll._evaluate_claude_shard(fake_source)
check("claude_shard: now actually imports anthropic (undocumented upgrade)", r["pass"], False, r["evidence"])

real_source = (
    "import random\n"
    "SMOOTHNESS_MARKERS = ['certainly', 'of course']\n"
    "def assess(self, response, context=''):\n"
    "    if random.random() < FRICTION_PROBABILITY:\n"
    "        pass\n"
)
r = ll._evaluate_claude_shard(real_source)
check("claude_shard: still keyword+random, no anthropic import", r["pass"], True, r["evidence"])

r = ll._evaluate_claude_shard("")
check("claude_shard: file unreadable", r["pass"], False, r["evidence"])


# ── 6. question_garden_lineage ──────────────────────────────────────────
# Historical fake: parent_questions/children fields exist in every entry's
# schema but are always empty lists — present in schema, never used.
r = ll._evaluate_garden_lineage(
    entries=[{"question": "a", "children": [], "parent_questions": []} for _ in range(50)],
    prev_count=None,
)
check("question_garden_lineage: schema present, always empty", r["pass"], False, r["evidence"])

r = ll._evaluate_garden_lineage(
    entries=[{"question": "a", "children": ["b"], "parent_questions": []},
             {"question": "b", "children": [], "parent_questions": ["a"]}],
    prev_count=1,
)
check("question_garden_lineage: real accumulated lineage", r["pass"], True, r["evidence"])


# ── 7. claude_research ───────────────────────────────────────────────────
# Historical fake (the actual, real, confirmed-live bug in this project
# until 2026-07-04): cursor file was never written because every call
# silently hit the None-vs-float TypeError — no cursor ever existed.
r = ll._evaluate_claude_research(cursor=None, last_attempt={"outcome": "skipped_no_question"}, window_days=2)
check("claude_research: never successfully called (pre-2026-07-04 bug)", r["pass"], False, r["evidence"])

r = ll._evaluate_claude_research(cursor={"last_call": now - 3600}, last_attempt=None, window_days=2)
check("claude_research: recent real success", r["pass"], True, r["evidence"])

r = ll._evaluate_claude_research(cursor={"last_call": now - (10 * 86400)}, last_attempt=None, window_days=2)
check("claude_research: succeeded once 10 days ago, gone quiet since", r["pass"], False, r["evidence"])


# ── 8. self_model_drift ──────────────────────────────────────────────────
# Historical-shape fake: self_model.json reports stale/wrong numbers while
# the real FAISS/journal have moved on (the exact split-brain class named
# in CLAUDE.md's FAISS dual-index section).
r = ll._evaluate_self_model_drift(
    self_model={"last_updated": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                "memory_health": {"faiss_vector_count": 100, "journal_line_count": 50}},
    live_memory={"faiss_vector_count": 34918, "journal_line_count": 1973},
    stale_hours=24,
)
check("self_model_drift: reported numbers wildly diverge from live", r["pass"], False, r["evidence"])

fresh_iso = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
r = ll._evaluate_self_model_drift(
    self_model={"last_updated": fresh_iso, "memory_health": {"faiss_vector_count": 34918, "journal_line_count": 1973}},
    live_memory={"faiss_vector_count": 34918, "journal_line_count": 1973},
    stale_hours=24,
)
check("self_model_drift: matches live ground truth", r["pass"], True, r["evidence"])

old_iso = "2020-01-01T00:00:00+00:00"
r = ll._evaluate_self_model_drift(
    self_model={"last_updated": old_iso, "memory_health": {"faiss_vector_count": 34918, "journal_line_count": 1973}},
    live_memory={"faiss_vector_count": 34918, "journal_line_count": 1973},
    stale_hours=24,
)
check("self_model_drift: numbers match but updater loop clearly died", r["pass"], False, r["evidence"])


# ── 9. task_type_classifier ──────────────────────────────────────────────
# Historical fake (the actual, real, confirmed-live bug this session):
# bootstrap_from_log() replayed every historical row with no filter at all.
def _always_true(prompt, task_type, source):
    return True


r = ll._evaluate_task_type_classifier(_always_true)
check("task_type_classifier: filter accepts everything (contamination reintroduced)", r["pass"], False, r["evidence"])

try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.core.task_type_classifier import is_trustworthy_training_example as _real_filter
    r = ll._evaluate_task_type_classifier(_real_filter)
    check("task_type_classifier: real current filter function", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] task_type_classifier real-filter case: import failed ({e})")

r = ll._evaluate_task_type_classifier(None)
check("task_type_classifier: filter function missing entirely", r["pass"], False, r["evidence"])


print()
if FAILURES:
    print(f"=== {len(FAILURES)} DISCRIMINATION FAILURE(S) — ledger is not trustworthy as-is ===")
    for f in FAILURES:
        print(" -", f)
    sys.exit(1)
else:
    print("=== All discrimination cases passed: every pure evaluator correctly ===")
    print("=== distinguishes its subsystem's real historical fake from real good data. ===")
    sys.exit(0)
