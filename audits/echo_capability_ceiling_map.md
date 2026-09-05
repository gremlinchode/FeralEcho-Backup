# FeralEcho / Echo — Zero-Cost Capability Ceiling Map

**Phase 2 of the C1-Validation + Capability-Ceiling mission.** Scope: current hardware, current
Ollama models, current code, zero additional money. No P1/P1.2/Learning-Pilot/P2/P3 evidence was
modified. No fine-tuning. Nothing scored below was implemented as an intervention — every "minimum
intervention to advance" is a proposal, not an applied change. Full per-dimension detail (evidence,
confidence, causal pathway, strongest positive/negative result, bottleneck, limitation type, ceiling,
minimum intervention, risk/confounds, next-step classification) is in
`audits/echo_capability_ceiling_map.json`. Full pipeline edge classification is in
`audits/echo_capability_ceiling_gaps.md`. Hardware detail is in
`audits/echo_capability_ceiling_hardware.md`.

**Evidence discipline**: every claim below is FACT (directly measured this session or explicitly
cited from a source document), INFERENCE (a reasonable conclusion from measured facts), HYPOTHESIS
(plausible but untested), or UNKNOWN (not established either way) — marked inline where the
distinction matters.

## Method

Live hardware inspection (Apple M5, 24GB unified memory, 706GB free disk — see hardware doc), a live
Ollama model inventory, a live unpickle of `memory/river_brain.pkl` (real per-model-per-task
statistics), a live read of `GET /admin/liveness-status` (51/51 checks passing, not stale), and an
Explore-agent-assisted read of the seven most load-bearing prior synthesis documents (P1/P1.2/P2/P3
plus three 2026-09-02/09-03 audits not previously folded into CLAUDE.md's own Findings list). This
session's own live C1 validation (Phase 1 of this mission, `audits/c1_live_validation_report.md`) is
used directly as evidence for two dimensions.

## Score scale

0 = absent/fiction · 1 = claimed/conceptual only · 2 = implemented but hollow/dead · 3 = causal
pathway exists, unverified live · 4 = experimentally demonstrated (narrow/small-N) · 5 = robustly
demonstrated (repeated, ground-truth checked) · 6 = generalized (works on varied unseen inputs) ·
7 = autonomous + generalized + robust.

## Capability dimensions (32), summarized

| # | Dimension | Score | Functional class | Maturity class | One-line reason |
|---|---|---|---|---|---|
| 1 | Reasoning | 4 | partial | experimentally-demonstrated | Real, but `reasoning` task-type bucket has only 5-112 real observations per model — under-exercised, not under-capable |
| 2 | Memory retrieval (L1) | 5 | retrieval-only | robustly-demonstrated | 123k+ vectors, live, correctly gated — but Finding 76's real ablation found no measurable behavioral effect on `personal`-task traffic distinguishable from noise |
| 3 | Cross-session continuity infra | 5 | functioning | robustly-demonstrated | This session's own C1 validation: 100% architectural reliability across 9 real trials |
| 4 | Learning (L2, autonomous) | 2 | hollow-dead | implemented | Only routing-level learning is live; `learn_from_council_rating()` is now confirmed DEAD — **corrects CLAUDE.md Finding 67** |
| 5 | Persistent behavioral adaptation (C1) | 4 | functioning | experimentally-demonstrated | This session: 3/4 (75%) live compliance when directive genuinely exposed, n=4 |
| 6 | Generalization (L3) | 1 | experimentally-unsupported | conceptual | Never tested; P1.2 found the opposite (position-tracking, not content-tracking) |
| 7 | Preference formation | 1 | experimentally-unsupported | experimentally-demonstrated | P1.2's live NULL result: 10/10 position-tracking, confabulation observed |
| 8 | Preference retention | 1 | experimentally-unsupported | experimentally-demonstrated | Downstream of #7's null |
| 9 | Self-model | 4 | partial | experimentally-demonstrated | Real, non-hollow ledger-fold-in; not independently re-verified in full depth this session |
| 10 | Metacognition | 3 | partial | causal-pathway-exists | `shadow_model` genuinely live (corrects a prior "zero callers" assumption); reader unconfirmed |
| 11 | Epistemic calibration/honesty | 3 | partial | experimentally-demonstrated | Real fabrication-catches exist but don't reach `interaction_log.jsonl` (2026-09-02 gap analysis) |
| 12 | Curiosity | 5 | functioning | robustly-demonstrated | 13,412 real garden entries; category distribution may reflect scheduling, not preference |
| 13 | Reflection | 4 | partial | experimentally-demonstrated | Real model-generated reflections; ~15% near-duplicate rate confirmed by a corrected liveness check |
| 14 | Planning | 4 | partial | experimentally-demonstrated | Real council-driven multi-step plans; two self-edit prompt families non-converged and were retired |
| 15 | Tool use | 1 | hollow-dead | implemented | `ToolManager` confirmed to have ~zero real callers |
| 16 | Model orchestration/council | 6 | functioning | generalized | 3,688 real deliberations; tag-boost mechanism empirically working live |
| 17 | Adaptation (routing-level) | 5 | functioning | robustly-demonstrated | Valence-modulated exploration/sampling verified bounded and safe; real-world effect magnitude unmeasured |
| 18 | Autonomy (background loops) | 5 | functioning | robustly-demonstrated | Multiple gated loops confirmed live; `echo_projects_autonomy`'s most recent real cycle was `f1_failed` |
| 19 | Self-editing | 4 | partial | robustly-demonstrated | Corrected to 426/463 (92%) real success rate; fitness metric (AST node count) confirmed saturated at 4/4 for all 25 retained deploys |
| 20 | Multi-file generation (echo_projects) | 4 | partial | experimentally-demonstrated | 2,535 real observations; most recent real autonomous cycle failed F1 |
| 21 | Recovery/fault tolerance | 6 | functioning | generalized | Snapshot/restore, watchdog-collision guard, dual-evidence crash avoidance — mature, well-tested |
| 22 | Goal persistence | 4 | partial | experimentally-demonstrated | Real garden question → real echo_projects spec, cross-subsystem, confirmed live |
| 23 | State/affect persistence | 5 | functioning | robustly-demonstrated | Valence persists and updates from 3 real sources; own predictive value unproven (r=-0.14, n=73) |
| 24 | Knowledge acquisition | 5 | functioning | robustly-demonstrated | Real, coherent fetched content; one live duplicate-storage bug (53x) still open |
| 25 | Abstraction | 3 | partial | causal-pathway-exists | Real question→project-spec bridge fires; no faithfulness check exists |
| 26 | Causal reasoning (self-directed) | 2 | infra-no-reader | causal-pathway-exists | Seam engine is a real, working, human-engineered heuristic — not open-ended reasoning by the model |
| 27 | Error correction | 5 | functioning | robustly-demonstrated | F1/F2/F3 + fitness gate + sandboxed apply_to_code all live-verified; safety robust, quality-improvement weaker |
| 28 | Interference resistance | 5 | functioning | robustly-demonstrated | A real, large (48.7% of memory) contamination was found and fixed with verifiable exclusion filters |
| 29 | Scientific/experimental reasoning | 5 | functioning | robustly-demonstrated | This is the INVESTIGATOR's rigor (human+Claude), not Echo's own capability — flagged explicitly |
| 30 | Observability/auditability | 5 | functioning | robustly-demonstrated | 51/51 live checks, up from 47 days earlier; no request-scoped correlation ID exists anywhere |
| 31 | Multi-agent dissent | 2 | functioning | experimentally-demonstrated | Real mechanism, n=1, unanimous — functioning but almost entirely unexercised |
| 32 | Novel signal generation (seam engine) | 4 | functioning | experimentally-demonstrated | 564/7,333 real detections (7.7%) — non-degenerate rate; downstream value unevaluated |

## Cross-cutting corrections to prior project conclusions (stated explicitly, per this mission's instruction)

1. **CLAUDE.md's own Finding 67 (2026-07-22) claimed `learn_from_council_rating()` was "built and
   verified live"; the most recent causal re-audit (2026-09-03, `echo_learning_causal_autopsy.md`)
   found it is now confirmed DEAD via a stale-cursor deadlock against a rotated log.** Both were
   true at their respective times of writing — this is presented as evidence of silent regression, not
   as evidence either audit was performed carelessly. It is also, itself, evidence for capability
   dimension #30 (observability): no liveness check monitors this specific edge's continued operation,
   unlike almost everything else this project builds a check for.
2. **The 2026-09-02 gap analysis corrects an even-more-recent prior document's claim that
   `model_task_stats` is "never read"** — it is read, and weighted at 0.65 in real model selection.
   This session's own live unpickle independently confirms rich, real, differentiated
   `model_task_stats` data exists and is exactly the shape RiverBrain's routing logic depends on.
3. **The 2026-09-03 self-modification evidence index corrects an earlier "0/37" self-edit
   success-rate figure to the real 426/463 (92%).** This is a substantial upward correction — but is
   qualified by the newly-found fact that the fitness gate's quality metric (raw AST node count) is
   saturated at a perfect score for all 25 currently-retained deploys, meaning "passed the gate"
   currently carries less discriminating signal than a 92% headline suggests on its own.
4. **This map's own scoring should itself be treated as provisional in one place**: the self-model
   dimension (#9) references a 2026-09-02 architectural-self-knowledge document series that was not
   read in depth this session (only its existence was noted via `ls`). That series may itself contain
   corrections this map has not yet incorporated.

---

## FERAL ECHO CURRENT LEVEL

**Echo today is a mature, well-instrumented, routing-and-retrieval-driven conversational system with
one newly-validated, narrow, human-mediated behavioral-persistence channel (C1) — and no confirmed
autonomous content-level learning, preference formation, or generalization.** The system's real
strength is breadth and rigor of *engineering discipline applied to itself*: 51 live, ground-truth
checked liveness monitors, a demonstrably-working autonomous self-edit pipeline (92% real deploy
success, F1/F2/F3 gates independently verified against real live failures this session), a
large, actively-used multi-model council with real per-model-per-task statistics, and a track record
of finding and fixing its own contamination bugs (most recently a 48.7%-of-all-memory code-analysis
contamination). Its real weaknesses are concentrated exactly where this mission's own P1/P1.2/P2/P3
work already found them, now sharpened with fresher, more recent evidence: no data structure anywhere
represents a candidate preference; the one plausible content-level learning channel is confirmed dead
via a specific, fixable bug rather than a fundamental absence; and FAISS memory retrieval — the
system's single largest and most actively-written subsystem — has not been shown to measurably change
behavior on the one task type it was tested against. On a rough overall read across all 32 scored
dimensions (mean ≈ 3.8/7, median 4/7), Echo sits solidly in "real infrastructure, partially exercised,
narrowly verified" territory — well past "hollow demo," well short of "generalized, autonomous
capability" on any dimension except the mature engineering-support ones (recovery, orchestration,
observability).

## ZERO-COST CEILING

Given current hardware (Apple M5, 24GB unified memory, 10 CPU + 10 GPU cores) and the current 9-model
Ollama pool, with zero additional spend, the realistic ceiling is:

- **Reasoning/planning/self-editing/multi-file generation**: ceiling ≈ 5/7 (robustly demonstrated,
  narrow model-class limits). No local model larger than ~8B-parameter class can be run alongside the
  live system's real, concurrent memory footprint (FAISS index + Flask + background threads already
  produce active swap use at 24GB). This is a genuine, hard, currently-unmovable ceiling without either
  a hardware upgrade or a paid API call — both outside this mission's scope.
- **Memory retrieval / knowledge acquisition / observability / recovery / model orchestration**:
  ceiling ≈ 6/7 (generalized) — these are mature enough that further zero-cost work is about
  *measurement and plumbing*, not new architecture. The retrieval-causal-effect question (#2) and the
  correlation-ID gap (#30) are the two highest-value items in this tier.
- **Preference formation/retention/generalization**: ceiling ≈ 3/7 even with zero-cost effort — these
  require a genuinely new data structure (a "candidate preference" representation) that does not exist
  anywhere today; this is a real architectural gap, not a measurement gap, and closing it is a
  meaningfully larger undertaking than anything else in this map, even though it costs no money.
- **Learning (L2)**: ceiling ≈ 3/7 zero-cost, via fixing the one specific, scoped,
  already-diagnosed bug (`learn_from_council_rating()`'s stale-cursor deadlock) — this would restore
  routing-adjacent training signal, not create new content-level learning; a genuinely higher ceiling
  here requires new architecture, not a bug fix.
- **Tool use**: ceiling ≈ 4/7 zero-cost if `ToolManager` is genuinely wired to a real invocation path
  — currently near its floor (hollow) for a reason that appears to be a wiring gap, not a capability
  limit.

## TOP 10 INTERVENTIONS (ranked, NOT implemented)

Ranked by expected-gain × evidence-strength ÷ (difficulty × contamination-risk), favoring
measurement/plumbing fixes over new architecture, per this mission's own stated preference against
"impressive demos over measurable capability."

1. **Add a request-scoped correlation ID threaded through `interaction_log.jsonl`,
   `council_deliberations.jsonl`, and `workspace_log.jsonl`.** Additive, zero risk to existing log
   structure, directly closes the single most-cited gap across two independent recent audits
   (2026-09-02 gap analysis, this map's own observability dimension). Testable immediately by
   reconstructing one real request's full causal path.
2. **Diagnose and fix `learn_from_council_rating()`'s stale-cursor deadlock.** A scoped bug, not a
   redesign; directly re-verifiable against the same discrimination tests Finding 67 originally used.
3. **Thread the code_verification/self_knowledge_verification caveat into `interaction_log.jsonl`.**
   Closes the specific "fabrication catch doesn't reach the log everything else reads" gap named by
   the 2026-09-02 gap analysis; small, additive, immediately testable against the 7 real fabrications
   already found in one day of production traffic.
4. **Re-run Finding 76's memory-retrieval ablation at `temperature=0`, across all 5 task types, not
   just `personal`.** Directly answers the single largest open question about whether the system's
   largest subsystem (memory) causally matters — currently unknown, not merely "weakly positive."
5. **Trace `ToolManager`'s 2 real call sites to determine if either is a genuine invocation path.**
   Cheap (one grep + read), resolves a real ambiguity (#15's score is provisional pending this).
6. **Replace/supplement the self-edit fitness gate's AST-node-count metric with an already-computed
   quality signal (e.g. `dry_run_quality`), since the current metric is confirmed saturated at ceiling
   for all 25 retained deploys.** Reuses existing plumbing; directly improves the discriminating power
   of an already-live, already-trusted gate.
7. **A larger-N replication of this session's own C1 compliance measurement** (e.g., 20+ trials
   instead of n=4) to get a stable estimate of the one genuinely-uncertain edge in the whole C1
   mechanism. No code change required.
8. **Investigate why FAISS-cosine dedup missed 53x storage of one identical fetched snippet
   (Finding 61).** Narrow, already-diagnosed, cheap to trace.
9. **Raise `num_ctx` for the two models whose real capability (32k/131k) is being wasted by the
   uniform 8192 constant, and measure real memory-pressure headroom.** Zero-cost to try; directly
   answers a hardware-extraction question this mission explicitly asked.
10. **Human review of a sample of real `echo_projects`/`seam_engine` outputs for genuine
    quality/value**, not just rate-of-firing — both mechanisms are confirmed non-degenerate in
    frequency but unevaluated in output quality.

## FIRST 3 MOVES (justified)

1. **#1 (correlation ID)** — because it is the cheapest, lowest-risk, most foundational fix: every
   other measurement effort in this list (retrieval ablation, fabrication-caveat propagation,
   self-edit outcome tracing) becomes easier and more trustworthy once one request's full path can be
   reconstructed. Doing this first compounds the value of everything after it.
2. **#4 (retrieval ablation at temp=0, all task types)** — because memory retrieval is this system's
   single largest subsystem by evidence volume and the current answer ("no measurable effect,
   personal-task only") is the most consequential open unknown in this entire map; resolving it either
   direction changes how every other memory-adjacent claim in this codebase should be read.
3. **#2 (fix `learn_from_council_rating()`)** — because it is a specific, already-diagnosed, scoped bug
   (not a redesign) sitting on the one plausible path toward any future content-level learning; fixing
   it doesn't create learning by itself, but leaving it broken forecloses that path entirely, and it is
   cheap to verify against the same test suite that originally validated it.

## HARD CEILINGS

- **No local model larger than ~8B-parameter class fits alongside this system's real, live, concurrent
  memory footprint on 24GB unified memory** — this is a genuine hardware ceiling, not a software one;
  raising `num_ctx`/`OLLAMA_NUM_PARALLEL` (interventions #9 and the hardware doc's own findings) can
  extract more from the *existing* pool, but cannot substitute for a larger model class.
- **No candidate-preference data structure exists anywhere in this codebase.** Building genuine
  preference formation/retention (dimensions #7/#8) is not a measurement or plumbing fix — it requires
  new architecture, and even then, P1.2's own live evidence (position-tracking, confabulation under
  pressure) suggests the underlying small-model class may itself resist clean forced-choice preference
  expression regardless of the surrounding architecture.
- **Generalization (L3) has never been tested and has one piece of evidence actively pointing away
  from it** (P1.2's position-tracking result) — this is a hard evidentiary ceiling on what can be
  claimed today, not a hard technical ceiling on what might be built.
- **This mission's own governance constraints are themselves a hard ceiling**: no paid API, no
  fine-tuning, no larger model — meaning several of the dimensions capped by "small local model class"
  (reasoning, planning, self-editing) cannot be pushed meaningfully further within this mission's own
  rules, regardless of software cleverness.

## UNKNOWN

- Whether FAISS memory retrieval has a real, measurable behavioral effect on **any** task type other
  than `personal` — only n=1 has ever been tested there (2026-09-02 gap analysis's own naming).
- Whether `shadow_accuracy.jsonl`'s real, accumulating self-assessment data is read by anything that
  changes behavior, or is a write-only ledger — not traced to a definitive answer in this pass.
- Whether `echo_state.py` dims [1] (intent_coherence) and [2] (memory_stability) have any real reader
  now that `baseline_trusted_since` is genuinely set (Finding 66) — not checked in this pass.
- The full, current content of the 2026-09-02 architectural-self-knowledge document series (multiple
  files existed but were not read in this pass) — this map's `self_model` dimension score is
  provisional pending that read.
- The true magnitude (not just the bounded-safety) of valence's real effect on exploration_bias/Optuna
  sampling outcomes over time — the mechanism is verified safe, not verified impactful.
- Whether a larger-N replication of this session's own C1 compliance test would hold near 75%, trend
  higher, or trend lower — n=4 is not enough to know.
- Whether raising `num_ctx`/`OLLAMA_NUM_PARALLEL` would produce a net-positive or net-negative effect
  under this machine's real, already-active swap pressure — named as a lever, not measured.
