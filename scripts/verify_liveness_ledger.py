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
