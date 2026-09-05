# Architectural Ceiling Map — Edge-by-Edge Classification

Full pipeline: `input → perception → memory → state → reasoning → model-selection → generation →
tools → reflection → learning → persistence → next-interaction`. Each edge below is classified as one
of: **live** (real, causally connected, verified), **write-but-no-reader** (real computation, output
persisted, nothing consumes it), **reader-but-no-causal-effect** (something reads it, but reading it
doesn't change behavior), **routing-only** (affects which model answers, not what is said), or
**dead/hollow** (exists in code, never actually fires or never actually mattered).

## input → perception

- **live**: `task_type_classifier.py` (online BagOfWords+MultinomialNB, trust-gated, functionally
  canaried live) + keyword fallback ladder → `detect_task_type()`. Real, verified, currently 51/51
  liveness-passing.
- **live**: `echo_ground_truth.py`'s slice dispatch (`_is_introspective()`, `_relevant_slices()`) —
  correctly widens/narrows which self-facts get surfaced per prompt; this session's own C1 validation
  independently re-confirmed the `behavioral_matches` dispatch branch fires with zero false positives
  across 9 real trials.

## perception → memory

- **live**: `add_to_vector_memory()` / `log_dream_bridge()` write path, gated by
  `memory_write_validator.py` (empty/trivial block, recursive-loop detection, hash-based dedup).
- **write-but-no-reader (fixed this year, now live)**: the code_analysis contamination (48.7% of all
  123,574+ memory entries) was a real instance of this exact failure mode until this year's fix —
  written constantly, read indiscriminately by both the dream-sampler and conversational retrieval,
  with no exclusion. Now closed (`awareness_scan_hygiene`, `code_analysis_retrieval_exclusion` both
  live-passing) — kept here as the clearest concrete example of what this failure mode looks like when
  it's real and large, not hypothetical.

## memory → state

- **live**: `echo_state.py`'s 9D vector, updated every 120s, dim[8] (valence) fed by three independent
  real sources (self-edit outcome deltas, council ratings, Finding 57's dry-run-quality addition).
- **reader-but-no-causal-effect, partially**: dims [1] (intent_coherence) and [2] (memory_stability)
  are computed and persisted but explicitly excluded from any alert trigger "pending
  `baseline_trusted_since`" — this flag is now genuinely set (Finding 66), which was not itself
  documented as unlocking these two dims. Worth a direct check: does anything read dims[1]/[2] today,
  or do they remain write-only?

## state → reasoning / model-selection

- **live, routing-only**: `RiverBrain.score_model()` → `_select_council()`. Confirmed live this
  session with real, richly-populated `model_task_stats` across 9 models × 7 task types. This is the
  single most mature edge in the whole pipeline by evidence volume — and it is explicitly **routing**,
  not content: it decides *which model speaks*, never *what is said*.
- **live**: `compute_salience()` → `emergent_loop`'s next-sleep modulation, `exploration_bias`,
  Optuna sampling-window shift (Finding 80) — all bounded, verified-safe, real causal effects on
  scheduling/exploration, confirmed via direct function calls this session and prior sessions.
- **dead**: `learn_from_council_rating()` — the one plausible path from real human/council feedback
  into content-relevant training — is confirmed dead via a stale-cursor deadlock against a rotated
  log, per the most recent (2026-09-03) causal re-audit. **This directly contradicts CLAUDE.md's own
  Finding 67 (2026-07-22), which reported this mechanism built and verified live.** Recorded here as
  an explicit correction: whatever verification Finding 67 performed at the time was real for that
  moment, but the mechanism has since silently regressed and nothing caught it — itself evidence that
  this specific edge has **no liveness-ledger check monitoring its continued operation**, unlike
  almost every other mechanism this project builds (see Observability section below).

## model-selection → generation

- **live**: `_ollama_query()` / `stream_query_ollama()` → `_build_chat_messages()`'s Modelfile-identity
  restoration (Finding 46) and per-councillor token budgeting (Finding 53/54) — both confirmed
  correctly scoped (keyed off `model`, not "system was given") in this project's own prior
  verification, and this session's own C1 validation used this exact call path directly (Design B)
  without incident.
- **generation → tools**: **hollow**. `ToolManager.get_tool()` has zero real callers confirmed by
  live grep this session (2 hits outside its own definition, neither traced to a real invocation
  site in this pass). A fully-built tool registry that nothing in the real generation path actually
  calls.

## generation → reflection

- **live**: `reflection_shard.py`'s real MLX-generated reflections (post Finding 75 Phase 5),
  `dream_cycle()`'s two-pass free-association + synthesis, `shadow_model.propose_from_reflection()`
  (confirmed live via `emergent_scheduler.py:620-625`, Finding 35's retraction).
- **write-but-no-reader (unconfirmed, flagged not proven)**: `shadow_accuracy.jsonl` accumulates real
  self-assessment-vs-outcome data (1,111+ entries) but no evidence was found this session of anything
  reading this file's own accuracy trend to change behavior. Flagged as **unconfirmed**, not concluded
  — this specific edge was not traced to a definitive answer in this pass.

## reflection → learning

- **routing-only**: RiverBrain's `learn()` (see above).
- **dead**: content-level learning from reflection. No confirmed pathway exists from "Echo reflected on
  X" to "Echo's future responses about X are different in content," independent of the C1 mechanism
  (which is human-directive-mediated, not reflection-derived).
- **hollow-by-absence**: no "candidate preference" data structure exists anywhere in production (the
  2026-09-03 measurability audit's own top-named architectural gap) — there is no edge here to
  classify because nothing is built to carry a formed preference from reflection into any persisted
  form at all.

## learning → persistence

- **live**: `behavioral_state.py` (C1) — persists a human-confirmed directive, deterministically
  retrieved, this session's own live validation confirms 100% reliable across the
  existence→retrieval→exposure chain.
- **live**: RiverBrain's `.pkl` persistence (routing-level only, as above).
- **live**: `self_model.json`'s `verified_capabilities` fold-in from the Liveness Ledger — a real,
  non-hollow loop (Machine-Native Awareness section, CLAUDE.md).

## persistence → next-interaction

- **live**: `echo_ground_truth.py`'s slice mechanism re-reads all of the above fresh on every prompt —
  no stale caching confirmed anywhere in this chain via this project's own extensive prior testing.
- **reader-but-no-confirmed-effect**: FAISS retrieval genuinely re-reads persisted memory on every
  relevant prompt (live), but Finding 76's real ablation experiment could not distinguish its
  behavioral effect from sampling noise on the one task type tested (`personal`). This is the single
  most important open measurement gap in the entire "does persisted state actually change behavior"
  question this whole multi-phase investigation has been built around — genuinely unresolved, not
  glossed over.

## Two failure-mode patterns, named explicitly per the mission's own request

1. **"Write but no reader"**: `code_analysis` contamination (now fixed), `shadow_accuracy.jsonl`
   (unconfirmed), dims [1]/[2] of `echo_state.py` (unconfirmed), the historical (2026-07 era)
   dormant Global Workspace before Phase 2a (now fixed and has real consumers, per CLAUDE.md's own
   extensive Phase 2-6 history) — this codebase's own history shows this exact pattern recurring and
   being found/fixed repeatedly, which is itself informative: the fix rate is real, but so is the
   recurrence rate.
2. **"Reader but no causal effect"**: FAISS retrieval on the `personal` task path (Finding 76's null
   result specifically), `council_baseline_trusted_since` before Finding 66/67 (a trust flag nothing
   downstream read until it was wired), `coupling_estimate` before Finding 78 (computed since Phase 4,
   consumed nowhere until Phase 6 gave it a real self-report reader).

## The single highest-value unclosed gap, per the most recent evidence available

**No request-scoped correlation ID exists anywhere in this system.** A single real conversation touches
`interaction_log.jsonl`, `council_deliberations.jsonl`, `workspace_log.jsonl`, and potentially
`self_edit_outcomes.jsonl`/`dissent_log.jsonl`, with no shared identifier linking one request's entries
across those files. Per the 2026-09-02 gap analysis, this is also why verification caveats
(fabrication catches) never reach the log that rating/learning/sync all read from — there is no
threading mechanism to carry that signal across the boundary. This is additive, zero-cost, and does
not touch any existing log's structure — a strong first-move candidate (see the main report's ranked
list).
