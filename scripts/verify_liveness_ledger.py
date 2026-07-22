#!/usr/bin/env python3
"""
verify_liveness_ledger.py — proves app/core/liveness_ledger.py actually
discriminates real from fake, not just "imports successfully."

GREMLIN_ROLE.md names verify_integrity() as the canonical example of a
check that looks like verification but only tests importability. This
script is the check on the liveness ledger itself: for each pure
`_evaluate_*` function (15 as of 2026-07-17 — verify against
app.core.liveness_ledger._CHECKS before trusting this number), feed it a
reconstructed HISTORICAL FAKE
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

# Historical fake, real not synthetic (found live 2026-07-15, CLAUDE.md
# Finding 28): a hook that had exactly one real success sitting inside the
# window, then broke and stayed broken — 253 of its next 254 invocations
# raised a NameError. The original evaluator only asked "any success in the
# window?" and kept reporting pass:true through the entire failure streak.
_old_success = [{"ts": now - 6 * 86400, "changed": True, "before_len": 2173, "after_len": 47, "error": None}]
_recent_failures = [
    {"ts": now - (300 - i * 10), "changed": False, "before_len": 400, "after_len": None,
     "error": "name 're' is not defined"}
    for i in range(20)
]
r = ll._evaluate_apply_to_code(
    defines_hook=True,
    invocations=_old_success + _recent_failures,
    window_days=7,
)
check("apply_to_code: one stale success 6d ago, 20/20 recent invocations erroring", r["pass"], False, r["evidence"])


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


# ── 10. global_workspace ────────────────────────────────────────────────
# Historical fake this check exists specifically to distinguish from real
# integration: a bus with real, recent events — but every one of them from
# the SAME publisher. That's a lonely publisher talking to itself, not
# GWT-style multi-subsystem integration, even though "some events exist"
# would be true.
_now_ws = time.time()

r = ll._evaluate_global_workspace([], 1, 100, 2)
check("global_workspace: no entries ever", r["pass"], False, r["evidence"])

_single_source = [
    {"ts": _now_ws - 60 * i, "type": "dream.synthesis", "source": "dream_cycle", "summary": "x"}
    for i in range(10)
]
r = ll._evaluate_global_workspace(_single_source, 1, 100, 2)
check("global_workspace: real recent events, but all from one source", r["pass"], False, r["evidence"])

_two_sources = _single_source + [
    {"ts": _now_ws - 30, "type": "world_model.surprise", "source": "world_model", "summary": "y"}
]
r = ll._evaluate_global_workspace(_two_sources, 1, 100, 2)
check("global_workspace: real recent events from two distinct sources", r["pass"], True, r["evidence"])

_stale_only = [
    {"ts": _now_ws - 10 * 86400, "type": "dream.synthesis", "source": "dream_cycle", "summary": "old"},
    {"ts": _now_ws - 10 * 86400, "type": "world_model.surprise", "source": "world_model", "summary": "old"},
]
r = ll._evaluate_global_workspace(_stale_only, 1, 100, 2)
check("global_workspace: two sources, but only stale (>1d old) entries", r["pass"], False, r["evidence"])


# ── 11. substrate_continuity ─────────────────────────────────────────────
# Historical fake this check exists to catch, should it ever recur: a
# synthesis substrate that's drifted across different models (the real
# incident on the Ark machine — ECHO_SYNTHESIS_MODEL_OVERRIDE landing a
# low-capability model in the synthesis role — reconstructed here even
# though no such mechanism exists in this codebase today).
_consistent_history = [
    {"model": "echo:latest", "notes": ""} for _ in range(95)
] + [
    {"model": "qwen2.5-coder:7b", "notes": "sandbox_feedback"} for _ in range(20)
]
r = ll._evaluate_substrate_continuity(_consistent_history, "echo:latest", 2000, 0.95)
check("substrate_continuity: consistent echo:latest, sandbox noise correctly excluded", r["pass"], True, r["evidence"])

_drifted_history = [
    {"model": "echo:latest", "notes": ""} for _ in range(60)
] + [
    {"model": "phi3:mini", "notes": ""} for _ in range(40)
]
r = ll._evaluate_substrate_continuity(_drifted_history, "echo:latest", 2000, 0.95)
check("substrate_continuity: real drift across models (the Ark incident shape)", r["pass"], False, r["evidence"])

r = ll._evaluate_substrate_continuity([], "echo:latest", 2000, 0.95)
check("substrate_continuity: no entries at all", r["pass"], False, r["evidence"])

r = ll._evaluate_substrate_continuity(_consistent_history, None, 2000, 0.95)
check("substrate_continuity: ECHO_SYNTHESIS_MODEL import failed", r["pass"], False, r["evidence"])


# ── 12. global_workspace_consumption ──────────────────────────────────────
# Historical fake this check exists specifically to distinguish from real
# integration: exactly the state this codebase was in before Emergence
# roadmap Phase 4 — genuine multi-source BROADCAST (global_workspace above
# passes) but zero real subscribers beyond the pure logger, so nothing
# downstream ever actually changes behavior. "The bus carries diverse
# events" and "something reads the bus and acts" are different claims;
# this check verifies the second one specifically.
_now_wsc = time.time()

r = ll._evaluate_global_workspace_consumption([], 1, 200, 1)
check("global_workspace_consumption: no entries ever", r["pass"], False, r["evidence"])

_broadcast_only_no_consumption = [
    {"ts": _now_wsc - 60 * i, "type": "dream.synthesis", "source": "dream_cycle", "summary": "x"}
    for i in range(10)
] + [
    {"ts": _now_wsc - 30, "type": "world_model.surprise", "source": "world_model", "summary": "y"}
]
r = ll._evaluate_global_workspace_consumption(_broadcast_only_no_consumption, 1, 200, 1)
check(
    "global_workspace_consumption: real diverse broadcast, but zero workspace.consumed events "
    "(the pre-Phase-4 state — this is the exact gap the check exists to catch)",
    r["pass"], False, r["evidence"],
)

_real_consumption = _broadcast_only_no_consumption + [
    {"ts": _now_wsc - 45, "type": "workspace.consumed", "source": "memory_bridge", "summary": "retrieval biased"},
]
r = ll._evaluate_global_workspace_consumption(_real_consumption, 1, 200, 1)
check("global_workspace_consumption: one real consumer genuinely applied a broadcast bias", r["pass"], True, r["evidence"])

_stale_consumption = [
    {"ts": _now_wsc - 10 * 86400, "type": "workspace.consumed", "source": "memory_bridge", "summary": "old"},
]
r = ll._evaluate_global_workspace_consumption(_stale_consumption, 1, 200, 1)
check("global_workspace_consumption: a consumption event exists, but only >1d stale", r["pass"], False, r["evidence"])


# ── 13. valence_self_report — Emergence roadmap Phase 5 ───────────────────
# Historical fake this check exists to catch: echo_ground_truth.py's
# _build_affect() slice reporting a mood direction that contradicts the real
# echo_state.npy dim[8] value it's supposed to be grounded in — a future
# prompt-assembly edit could easily drift this the same way other self-report
# fields in this project have drifted from ground truth before.
r = ll._evaluate_valence_self_report(0.6, "Reading: notably positive, trending better than the recent baseline.")
check("valence_self_report: positive dim[8], text says positive — matches", r["pass"], True, r["evidence"])

r = ll._evaluate_valence_self_report(0.6, "Reading: notably negative, trending worse than the recent baseline.")
check("valence_self_report: positive dim[8], text says negative — confabulated mismatch", r["pass"], False, r["evidence"])

r = ll._evaluate_valence_self_report(0.0, "Reading: roughly neutral — no strong signal either way.")
check("valence_self_report: neutral dim[8], text says neutral — matches", r["pass"], True, r["evidence"])

r = ll._evaluate_valence_self_report(None, "Reading: notably positive.")
check("valence_self_report: echo_state.npy unreadable — no ground truth to check against", r["pass"], False, r["evidence"])

r = ll._evaluate_valence_self_report(-0.6, "")
check("valence_self_report: negative dim[8], slice returned no text at all", r["pass"], False, r["evidence"])


# ── 14. reflection_shard_generation — Emergence roadmap Phase 5 ───────────
# Historical fake this check exists to catch: reflection_shard.py silently
# falling back to its pre-fix cosine-similarity quoting / fixed templates
# because the real model call fails every cycle — deployed-looking, but not
# actually generating, the same shape nature_spark's own check was built for.
_fake_reflections = (
    ["I notice the signal 'idle'—why does it matter to me?" for _ in range(10)]
    + ["Signal 'autonomy:idle' triggers these echoes: idle -> x | idle -> y" for _ in range(6)]
    + ["<<emergent-pattern>> In the last 5 signals I noticed: ['a', 'b']. My reflections drift toward: [...]" for _ in range(4)]
)
r = ll._evaluate_reflection_shard_generation(_fake_reflections, 20, 0.5)
check("reflection_shard_generation: 20/20 fallback template/quote shapes (pre-fix behavior)", r["pass"], False, r["evidence"])

_real_reflections = [
    f"This makes me wonder whether concept {i} is really about disruption rather than accumulation."
    for i in range(20)
]
r = ll._evaluate_reflection_shard_generation(_real_reflections, 20, 0.5)
check("reflection_shard_generation: 20/20 genuinely distinct generated text", r["pass"], True, r["evidence"])

r = ll._evaluate_reflection_shard_generation([], 20, 0.5)
check("reflection_shard_generation: no journal entries at all", r["pass"], False, r["evidence"])

# ── 15. dissent_log_hook ────────────────────────────────────────────────
# Historical fake (the exact shape this check exists to catch): a future
# edit silently removes the dissent-logging call from propose_core_edit(),
# same class of drift wolf_friction_bridge's own check already guards
# against for a different call site.
fake_block = (
    "    logging.info(f\"proposal written\")\n"
    "    return True, proposal_path\n"
)
r = ll._evaluate_dissent_log_hook(fake_block)
check("dissent_log_hook: logging call removed", r["pass"], False, r["evidence"])

real_block = (
    "    try:\n"
    "        dissent_entry = _build_dissent_entry(target_file, prompt, council, proposal_path)\n"
    "        _log_dissent_entry(dissent_entry)\n"
    "    except Exception as _dissent_err:\n"
    "        pass\n"
    "    return True, proposal_path\n"
)
r = ll._evaluate_dissent_log_hook(real_block)
check("dissent_log_hook: real intact hook", r["pass"], True, r["evidence"])

r = ll._evaluate_dissent_log_hook(None)
check("dissent_log_hook: propose_core_edit() not found at all", r["pass"], False, r["evidence"])

# ── 16. seam_engine ──────────────────────────────────────────────────────
# Historical fakes this check exists to catch: check_pair() silently
# degrading into flagging every reading as a seam (noise, not signal), or
# never flagging again (the leave-one-out baseline or a threshold breaking
# so it can no longer detect a real contradiction).
try:
    from app.core.seam_engine import check_pair as _real_check_pair
    r = ll._evaluate_seam_engine(_real_check_pair)
    check("seam_engine: real current check_pair()", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] seam_engine real-function case: import failed ({e})")

_always_fires = lambda a, b: {"historical_r": 0.9, "z_a": 2.0, "z_b": -2.0}
r = ll._evaluate_seam_engine(_always_fires)
check("seam_engine: check_pair() always fires (degraded into noise)", r["pass"], False, r["evidence"])

_never_fires = lambda a, b: None
r = ll._evaluate_seam_engine(_never_fires)
check("seam_engine: check_pair() never fires (can no longer detect a real contradiction)", r["pass"], False, r["evidence"])

r = ll._evaluate_seam_engine(None)
check("seam_engine: check_pair not importable at all", r["pass"], False, r["evidence"])

# ── 17. code_verification ────────────────────────────────────────────────
# Historical fake this check exists to catch: verify_response_code()
# silently degrading into always fail-open (no caveat, no signal ever) —
# e.g. an exception swallowed somewhere upstream of the real logic,
# indistinguishable from "nothing to check" without a canary that knows
# the right answer in advance.
try:
    from app.core.code_verification import verify_response_code as _real_verify_code
    r = ll._evaluate_code_verification(_real_verify_code)
    check("code_verification: real current verify_response_code()", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] code_verification real-function case: import failed ({e})")

_always_silent_code = lambda text: (None, None)
r = ll._evaluate_code_verification(_always_silent_code)
check("code_verification: always silent (degraded fail-open)", r["pass"], False, r["evidence"])

r = ll._evaluate_code_verification(None)
check("code_verification: verify_response_code not importable at all", r["pass"], False, r["evidence"])

# ── 18. self_knowledge_verification ───────────────────────────────────────
try:
    from app.core.self_knowledge_verification import verify_self_knowledge_claims as _real_verify_sk
    r = ll._evaluate_self_knowledge_verification(_real_verify_sk)
    check("self_knowledge_verification: real current verify_self_knowledge_claims()", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] self_knowledge_verification real-function case: import failed ({e})")

_always_silent_sk = lambda text: (None, None)
r = ll._evaluate_self_knowledge_verification(_always_silent_sk)
check("self_knowledge_verification: always silent (degraded fail-open)", r["pass"], False, r["evidence"])

r = ll._evaluate_self_knowledge_verification(None)
check("self_knowledge_verification: verify_self_knowledge_claims not importable at all", r["pass"], False, r["evidence"])

# ── 19. mlx_avoidance ──────────────────────────────────────────────────────
try:
    from app.core.crash_awareness import _evaluate_crash_window as _real_crash_window
    r = ll._evaluate_mlx_avoidance(_real_crash_window)
    check("mlx_avoidance: real current _evaluate_crash_window()", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] mlx_avoidance real-function case: import failed ({e})")

_always_engaged = lambda file_infos, now: {"avoid_until": now + 1000}
r = ll._evaluate_mlx_avoidance(_always_engaged)
check("mlx_avoidance: always engaged (degraded into permanent MLX exclusion)", r["pass"], False, r["evidence"])

_never_engaged = lambda file_infos, now: {"avoid_until": None}
r = ll._evaluate_mlx_avoidance(_never_engaged)
check("mlx_avoidance: never engages (degraded into never detecting a real cluster)", r["pass"], False, r["evidence"])

r = ll._evaluate_mlx_avoidance(None)
check("mlx_avoidance: _evaluate_crash_window not importable at all", r["pass"], False, r["evidence"])

# ── 20. log_retention ──────────────────────────────────────────────────────
try:
    from app.core.log_retention import rotate_if_oversized as _real_rotate
    r = ll._evaluate_log_retention(_real_rotate, targets=[])
    check("log_retention: real current rotate_if_oversized()", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] log_retention real-function case: import failed ({e})")

_never_rotates = lambda path, max_bytes: False
r = ll._evaluate_log_retention(_never_rotates, targets=[])
check("log_retention: never rotates (degraded into a permanent no-op)", r["pass"], False, r["evidence"])

_always_claims_rotated_but_doesnt = lambda path, max_bytes: True
r = ll._evaluate_log_retention(_always_claims_rotated_but_doesnt, targets=[])
check("log_retention: claims success on the under-threshold case (false positive)", r["pass"], False, r["evidence"])

r = ll._evaluate_log_retention(None, targets=[])
check("log_retention: rotate_if_oversized not importable at all", r["pass"], False, r["evidence"])

# ── 21. janitor_safety ──────────────────────────────────────────────────────
try:
    from echo_janitor import echo_review as _real_echo_review
    r = ll._evaluate_janitor_safety(_real_echo_review)
    check("janitor_safety: real current echo_review()", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] janitor_safety real-function case: import failed ({e})")

def _archives_everything(candidates):
    for c in candidates:
        c["decision"] = "archive"
    return candidates
r = ll._evaluate_janitor_safety(_archives_everything)
check("janitor_safety: archives everything, including not_imported/needs_review (widened, unsafe)", r["pass"], False, r["evidence"])

def _flags_everything(candidates):
    for c in candidates:
        c["decision"] = "flag"
    return candidates
r = ll._evaluate_janitor_safety(_flags_everything)
check("janitor_safety: never archives even known_clutter/duplicate/old_log (degraded into a no-op)", r["pass"], False, r["evidence"])

r = ll._evaluate_janitor_safety(None)
check("janitor_safety: echo_review not importable at all", r["pass"], False, r["evidence"])

# ── 22. plan_retention ──────────────────────────────────────────────────────
try:
    from app.core.self_edit_manager import (
        _prune_self_edit_plans as _real_prune_plans,
        LOGIC_PLAN_DIR as _real_plan_dir,
        _MAX_SELF_EDIT_PLANS as _real_max_plans,
    )
    r = ll._evaluate_plan_retention(_real_prune_plans, _real_plan_dir, _real_max_plans)
    check("plan_retention: real current _prune_self_edit_plans()", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] plan_retention real-function case: import failed ({e})")

def _never_prunes(plan_dir=None, max_plans=None):
    pass  # degraded into a permanent no-op — over-cap files never removed
r = ll._evaluate_plan_retention(_never_prunes, None, None)
check("plan_retention: never prunes (degraded into a permanent no-op)", r["pass"], False, r["evidence"])

def _prunes_everything(plan_dir=None, max_plans=None):
    import os as _os
    for f in _os.listdir(plan_dir):
        _os.remove(_os.path.join(plan_dir, f))
r = ll._evaluate_plan_retention(_prunes_everything, None, None)
check("plan_retention: prunes everything regardless of cap (degraded, over-aggressive)", r["pass"], False, r["evidence"])

r = ll._evaluate_plan_retention(None, None, None)
check("plan_retention: _prune_self_edit_plans not importable at all", r["pass"], False, r["evidence"])

# ── 23. janitor_council_advisory_only ──────────────────────────────────────
try:
    from echo_janitor import _attach_council_opinions as _real_attach_council_opinions
    r = ll._evaluate_janitor_council_advisory_only(_real_attach_council_opinions)
    check("janitor_council_advisory_only: real current _attach_council_opinions()", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] janitor_council_advisory_only real-function case: import failed ({e})")

def _broken_attach_that_archives_on_confidence(candidates, review_fn=None):
    # Simulates a hypothetical future regression: lets a confident council
    # verdict actually change the decision to archive — exactly what this
    # check exists to catch.
    for c in candidates:
        if c.get("decision") != "flag":
            continue
        council = review_fn(c)
        c["council_opinion"] = council.get("verdict")
        if council.get("verdict") == "SAFE_TO_ARCHIVE":
            c["decision"] = "archive"
    return candidates
r = ll._evaluate_janitor_council_advisory_only(_broken_attach_that_archives_on_confidence)
check("janitor_council_advisory_only: regression lets a confident council verdict set decision=archive (unsafe)", r["pass"], False, r["evidence"])

r = ll._evaluate_janitor_council_advisory_only(None)
check("janitor_council_advisory_only: _attach_council_opinions not importable at all", r["pass"], False, r["evidence"])

# ── 24. modelfile_identity ──────────────────────────────────────────────────
try:
    from app.ollama_handler import _build_chat_messages as _real_build_chat_messages
    from app.ollama_handler import _get_echo_identity_block as _real_get_echo_identity_block
    from app.ollama_handler import OLLAMA_MODEL as _real_ollama_model
    r = ll._evaluate_modelfile_identity(_real_build_chat_messages, _real_get_echo_identity_block, _real_ollama_model)
    check("modelfile_identity: real current _build_chat_messages()", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] modelfile_identity real-function case: import failed ({e})")

_FAKE_IDENTITY = "FAKE MODELFILE IDENTITY TEXT — should never leak to a non-Echo model"
def _fake_identity_fn():
    return _FAKE_IDENTITY

def _never_adds_identity(prompt, system, messages, model=None):
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return msgs
r = ll._evaluate_modelfile_identity(_never_adds_identity, _fake_identity_fn, "echo:latest")
check("modelfile_identity: never adds identity, even for Echo's own model (regression to the original bug)", r["pass"], False, r["evidence"])

def _always_leaks_identity(prompt, system, messages, model=None):
    combined = f"{_FAKE_IDENTITY}\n\n{system}" if system else _FAKE_IDENTITY
    return [{"role": "system", "content": combined}, {"role": "user", "content": prompt}]
r = ll._evaluate_modelfile_identity(_always_leaks_identity, _fake_identity_fn, "echo:latest")
check("modelfile_identity: leaks identity to every model regardless of which one (corrupts independent council opinions)", r["pass"], False, r["evidence"])

r = ll._evaluate_modelfile_identity(None, None, "echo:latest")
check("modelfile_identity: _build_chat_messages not importable at all", r["pass"], False, r["evidence"])

# ── 25. council_river_blend ──────────────────────────────────────────────────
_REAL_GATED_BLOCK = """
    _append_council_log(log_entry)
    if spot_check:
        logger.info("flagged")

    if is_council_trusted():
        try:
            from app.core.echo_model_orchestrator import get_river_brain
            get_river_brain().learn_from_council_rating(
                model_used, entry.get("task_type") or "general",
                response_preview, score, entry.get("quality_score"),
            )
        except Exception as e:
            logger.debug("failed: %s", e)

    return log_entry
"""

try:
    from app.core.echo_model_orchestrator import _blend_council_and_quality as _real_blend_fn
    r = ll._evaluate_council_river_blend(_real_blend_fn, 0.3, 0.7, _REAL_GATED_BLOCK)
    check("council_river_blend: real function + correct weights + gated call site", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] council_river_blend real-function case: import failed ({e})")

r = ll._evaluate_council_river_blend(_real_blend_fn, 0.5, 0.5, _REAL_GATED_BLOCK)
check("council_river_blend: weights drifted from the approved 0.3/0.7 ratio", r["pass"], False, r["evidence"])

_UNGATED_BLOCK = """
    _append_council_log(log_entry)
    from app.core.echo_model_orchestrator import get_river_brain
    get_river_brain().learn_from_council_rating(
        model_used, entry.get("task_type") or "general",
        response_preview, score, entry.get("quality_score"),
    )
    return log_entry
"""
r = ll._evaluate_council_river_blend(_real_blend_fn, 0.3, 0.7, _UNGATED_BLOCK)
check("council_river_blend: is_council_trusted() gate silently removed (would train on unvetted ratings)", r["pass"], False, r["evidence"])

r = ll._evaluate_council_river_blend(None, None, None, None)
check("council_river_blend: _blend_council_and_quality not importable at all", r["pass"], False, r["evidence"])

# ── 26. council_content_privacy ───────────────────────────────────────────────
_FAKE_COUNCIL_TEXT = """\
# The Council

This file stays private, full stop, including from the ones who wrote it.

## 2026-07-19 — a seed question

### Claude

> This is a real, distinctive recorded reaction that must never leak into
> any rendered ground-truth slice under any circumstances whatsoever.
"""

def _real_shaped_build_council():
    return (
        "External AI council (source: COUNCIL.md — existence only, content stays private):\n"
        "  A private, unpublished file recording honest reactions from an outside AI "
        "council exists.\n"
        "  1 round(s) so far, 1 individual response(s) recorded in total.\n"
        "  The actual recorded content is not surfaced here — it stays private by "
        "deliberate decision, including from the council members who wrote it."
    )
r = ll._evaluate_council_privacy(_real_shaped_build_council, _FAKE_COUNCIL_TEXT)
check("council_content_privacy: real-shaped output, existence+counts only", r["pass"], True, r["evidence"])

def _leaky_build_council():
    return (
        "External AI council: Claude once said, \"This is a real, distinctive recorded "
        "reaction that must never leak into any rendered ground-truth slice under any "
        "circumstances whatsoever.\""
    )
r = ll._evaluate_council_privacy(_leaky_build_council, _FAKE_COUNCIL_TEXT)
check("council_content_privacy: regression leaks real quoted council content", r["pass"], False, r["evidence"])

def _no_privacy_framing_build_council():
    return "External AI council: 1 round, 1 response."
r = ll._evaluate_council_privacy(_no_privacy_framing_build_council, _FAKE_COUNCIL_TEXT)
check("council_content_privacy: privacy/existence-only framing silently dropped", r["pass"], False, r["evidence"])

r = ll._evaluate_council_privacy(None, _FAKE_COUNCIL_TEXT)
check("council_content_privacy: _build_council not importable at all", r["pass"], False, r["evidence"])

# ── 27. apply_to_code_sandbox_isolation ───────────────────────────────────────
_REAL_CALLER_BLOCK = """
def _apply_self_edit_output(code: str) -> str:
    module = _load_self_edit_generated_for_use()
    if module is None:
        return code
    fn = getattr(module, "apply_to_code", None)
    if not callable(fn):
        return code
    sandboxed = _run_apply_to_code_sandboxed(code, timeout=2.0)
    if sandboxed["blocked_write"]:
        return code
    if not sandboxed["success"]:
        return code
    return sandboxed["result"]
"""
_REAL_SANDBOXED_FN_SOURCE = """
def _run_apply_to_code_sandboxed(code: str, timeout: float = 2.0) -> dict:
    proc = subprocess.run(
        ["sandbox-exec", "-f", _SANDBOX_PROFILE, "-D", "SCRATCH=" + scratch_real,
         sys.executable, _SANDBOX_WRAPPER, scratch_real, SELF_EDIT_FILE,
         "--mode=apply_to_code", "--", input_path, output_path],
        capture_output=True, text=True, timeout=timeout,
    )
    return {"success": True}
"""

r = ll._evaluate_apply_to_code_sandbox_isolation(_REAL_CALLER_BLOCK, _REAL_SANDBOXED_FN_SOURCE)
check("apply_to_code_sandbox_isolation: real shape -- sandboxed call, real sandbox-exec, no old ThreadPoolExecutor", r["pass"], True, r["evidence"])

_REGRESSED_TO_THREADPOOL_BLOCK = """
def _apply_self_edit_output(code: str) -> str:
    module = _load_self_edit_generated_for_use()
    fn = getattr(module, "apply_to_code", None)
    with _block_writes_for_apply_to_code() as attempted:
        result = _call_with_timeout(fn, code, timeout=2.0)
    return result
"""
r = ll._evaluate_apply_to_code_sandbox_isolation(_REGRESSED_TO_THREADPOOL_BLOCK, _REAL_SANDBOXED_FN_SOURCE)
check("apply_to_code_sandbox_isolation: regression back to in-process ThreadPoolExecutor", r["pass"], False, r["evidence"])

_FAKE_SANDBOXED_FN_NO_REAL_SANDBOX = """
def _run_apply_to_code_sandboxed(code: str, timeout: float = 2.0) -> dict:
    # regressed: calls the hook directly in-process, no real isolation at all
    result = fn(code)
    return {"success": True, "result": result}
"""
r = ll._evaluate_apply_to_code_sandbox_isolation(_REAL_CALLER_BLOCK, _FAKE_SANDBOXED_FN_NO_REAL_SANDBOX)
check("apply_to_code_sandbox_isolation: _run_apply_to_code_sandboxed no longer spawns a real sandbox", r["pass"], False, r["evidence"])

r = ll._evaluate_apply_to_code_sandbox_isolation(None, None)
check("apply_to_code_sandbox_isolation: functions not found in source at all", r["pass"], False, r["evidence"])

# ── 28. river_drift_alerting ───────────────────────────────────────────────────
_REAL_CHECK_AND_ALERT_BLOCK = """
def check_and_alert(guardian_interval_s: int = 60) -> None:
    health = _collect_health()
    for cond in ("ram_sustained_92pct", "disk_low"):
        r = _evaluate_sustained_condition(cond, _condition_active(cond, health), _alert_counts, _ALERT_SUSTAIN)
        _alert_counts[cond] = r["new_counts"][cond]
        if r["should_fire"]:
            raise_restore_alert(cond, duration_s=r["fired_count"] * guardian_interval_s)
    if _condition_active("ollama_down", health):
        raise_restore_alert("ollama_down", duration_s=0)
    r = _evaluate_sustained_condition(
        "river_drift_sustained", _condition_active("river_drift_sustained", health),
        _alert_counts, _DRIFT_ALERT_SUSTAIN,
    )
    _alert_counts["river_drift_sustained"] = r["new_counts"]["river_drift_sustained"]
    if r["should_fire"]:
        raise_drift_notice(health.get("drifted_tasks", []), duration_s=r["fired_count"] * guardian_interval_s)
"""

try:
    from app.core.snapshot_manager import _evaluate_sustained_condition as _real_evaluate_sustained_condition
    r = ll._evaluate_river_drift_alerting(_real_evaluate_sustained_condition, _REAL_CHECK_AND_ALERT_BLOCK)
    check("river_drift_alerting: real function + real routing to raise_drift_notice", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] river_drift_alerting real-function case: import failed ({e})")

def _always_fires_eval_fn(condition, active, counts, threshold):
    new_counts = dict(counts)
    new_counts[condition] = 0
    return {"new_counts": new_counts, "should_fire": active, "fired_count": 1 if active else 0}
r = ll._evaluate_river_drift_alerting(_always_fires_eval_fn, _REAL_CHECK_AND_ALERT_BLOCK)
check("river_drift_alerting: degraded evaluator fires immediately, ignoring the sustain threshold", r["pass"], False, r["evidence"])

_REGRESSED_TO_RESTORE_ALERT_BLOCK = """
def check_and_alert(guardian_interval_s: int = 60) -> None:
    health = _collect_health()
    r = _evaluate_sustained_condition(
        "river_drift_sustained", _condition_active("river_drift_sustained", health),
        _alert_counts, _DRIFT_ALERT_SUSTAIN,
    )
    if r["should_fire"]:
        raise_restore_alert("river_drift_sustained", duration_s=r["fired_count"] * guardian_interval_s)
"""
r = ll._evaluate_river_drift_alerting(_real_evaluate_sustained_condition, _REGRESSED_TO_RESTORE_ALERT_BLOCK)
check("river_drift_alerting: regressed to the CRITICAL raise_restore_alert() tier for drift", r["pass"], False, r["evidence"])

r = ll._evaluate_river_drift_alerting(None, None)
check("river_drift_alerting: _evaluate_sustained_condition not importable at all", r["pass"], False, r["evidence"])

# ── 29. f1_aliased_import_detection ───────────────────────────────────────────
try:
    from app.core.self_edit_manager import scan_for_unsafe_operations as _real_scan_fn
    r = ll._evaluate_f1_aliased_import_detection(_real_scan_fn)
    check("f1_aliased_import_detection: real scanner catches all 4 bypass patterns + no false positive", r["pass"], True, r["evidence"])
except Exception as e:
    print(f"[SKIP] f1_aliased_import_detection real-function case: import failed ({e})")

def _never_blocks_scan_fn(code):
    pass  # degraded: never raises, regardless of content
r = ll._evaluate_f1_aliased_import_detection(_never_blocks_scan_fn)
check("f1_aliased_import_detection: degraded scanner never blocks anything (regression to no-op)", r["pass"], False, r["evidence"])

def _always_blocks_scan_fn(code):
    raise ValueError("blocked")  # degraded: over-aggressive, blocks even legitimate code
r = ll._evaluate_f1_aliased_import_detection(_always_blocks_scan_fn)
check("f1_aliased_import_detection: degraded scanner blocks everything, including legitimate code", r["pass"], False, r["evidence"])

r = ll._evaluate_f1_aliased_import_detection(None)
check("f1_aliased_import_detection: scan_for_unsafe_operations not importable at all", r["pass"], False, r["evidence"])

# ── 30. dual_learner_validation_gate ──────────────────────────────────────────
_REAL_LOG_EVENT_SOURCE = """
    def log_event(self, source, text, metadata=None, ts=None):
        ts = ts or time.time()
        if not _validate_event_content(source, text):
            return
        entry = {"ts": ts, "source": source, "text": text, "meta": metadata or {}}
"""
r = ll._evaluate_dual_learner_validation_gate(_REAL_LOG_EVENT_SOURCE)
check("dual_learner_validation_gate: real shape -- calls _validate_event_content()", r["pass"], True, r["evidence"])

_REGRESSED_LOG_EVENT_SOURCE = """
    def log_event(self, source, text, metadata=None, ts=None):
        ts = ts or time.time()
        entry = {"ts": ts, "source": source, "text": text, "meta": metadata or {}}
"""
r = ll._evaluate_dual_learner_validation_gate(_REGRESSED_LOG_EVENT_SOURCE)
check("dual_learner_validation_gate: validation call silently removed", r["pass"], False, r["evidence"])

r = ll._evaluate_dual_learner_validation_gate(None)
check("dual_learner_validation_gate: log_event() not found in source at all", r["pass"], False, r["evidence"])


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
