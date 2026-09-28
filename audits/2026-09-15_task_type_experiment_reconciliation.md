# Formal reconciliation: September 14 task-type behavioral experiment

Date: 2026-09-15. Author: Claude (fork), performing formal reconciliation after an
independent Codex audit (`audits/2026-09-15_codex_task_type_independent_review.md`)
identified substantive errors in `audits/2026-09-14_task_type_behavioral_experiment.md`.
This is a correction-of-the-record mission: it does not alter, delete, or overwrite the
original report. It re-verifies Codex's findings from primary evidence independently
(not by trusting either party's prose), and states plainly which claims survive, which
do not, and what remains unknown.

No production code, config, memory, or git state was touched to produce this report.
The proposed 2×2 factorial (Phase 6) is designed here, not implemented or run.

---

## Phase 0 — Integrity baseline

Recorded before any change:

- Git HEAD: `2fba42644c82b9f7096276f4dd338d615cf1bcce`
- `git status --short --untracked-files=all`: 166 entries (unrelated concurrent research
  work — dozens of untracked audit files spanning 2026-09-07 through 2026-09-14, several
  modified core files — this is pre-existing background state, not something this
  mission touches or investigates)
- Path count (`find . -print | wc -l`): 22,292
- Runtime: active and undisturbed. `PID 7644` (`python -u run.py`), `PID 7636`
  (`start_echo.sh` watchdog), `PID 87918` (`python -m echo_studio.main`) all confirmed
  running via `ps aux`; none signaled, attached to, or restarted.

---

## Phase 1 — Independent reverification of Codex's five findings

Each finding below was traced to primary evidence directly by this mission — source
code line numbers, raw evidence-file computation, or independent arithmetic — not
accepted from either the original report's or Codex's prose.

### Finding 1 — Condition A

**Reverified: Codex's finding is correct, and the root cause is more precisely
identifiable than either prior document stated.**

`scripts/task_type_behavioral_experiment.py:316` calls
`disable_direct_echo_bypass_for_personal(rd)` **once**, before the condition-loop
branches by condition at all (before the `if __name__ == "__main__":` block's
timing-check and main-run loops). This call clears `rd.DIRECT_ECHO_TASKS` to an empty
`frozenset()` for the remaining lifetime of the process. The original value is captured
into `original_direct_tasks` and written only to `run_metadata.json` for the record —
**there is no restoration call anywhere in the file** (confirmed by exhaustive grep for
`rd.DIRECT_ECHO_TASKS\s*=` and `original_direct_tasks`: exactly one assignment, exactly
one read, both already accounted for).

The function's own docstring states its intent plainly and narrowly: *"Condition B needs
task_type='personal' to reach the council path instead of DIRECT_ECHO_TASKS."* This is
the precise root cause: the author's own comment shows they understood this should only
affect Condition B, but the call site applies it globally, once, for the whole run — not
scoped, not re-enabled before Condition A's trials, not disabled after B's trials
complete. This is a clean, single-point implementation bug, not an ambiguous design
choice.

`run_condition_trial()` (`scripts/task_type_behavioral_experiment.py:263-291`) confirms
the consequence directly: Conditions A and B are **byte-identical in every argument**
passed to `deliberate_and_learn()` — both set `task_type = "personal"` and
`system_used = base_system`. The only distinction between A and B anywhere in the script
is the string label passed for logging. With `DIRECT_ECHO_TASKS` cleared, `task_type in
DIRECT_ECHO_TASKS` is always `False`, so neither A nor B could ever reach the direct
bypass branch.

**Independently computed call-pattern evidence** (from the real evidence directory,
`run_metadata.json`'s `side_effects_detected` list, 65 entries, cross-referenced against
`main_run_order` and `condition_map_SEPARATE.jsonl`): grouping the 65 intercepted calls
by trial boundary (each group terminated by a `_log_council_deliberation` intercept)
yields **exactly 15 groups for 15 main-run trials**, and every single group — regardless
of whether its condition label is A, B, or C — shows the identical shape: three
`RiverBrain.learn` calls (one per councillor: `qwen2.5-coder:7b`, `llama3.1:8b`,
`echo:latest`) followed by one `_log_council_deliberation` call, with C trials showing
one additional `_log_synthesis_integrity` call (the coding-only integrity check). **All
five Condition-A trials in this run show the exact same four-call council+synthesis
pattern as Condition B — zero distinguishable difference in call shape.** This is
independently reproduced, primary evidence, not accepted from either prior report.

**Verdict: the earlier interpretation of A→B as a direct-vs-council comparison does not
survive.** A and B are the same treatment (council path, `task_type="personal"`,
identical system content) run twice under different labels.

### Finding 2 — Median calculation

**Reverified: Codex's corrected medians are exactly right; the discrepancy's source is
now precisely identified.**

Pulling the raw scores directly from `judge_scores_anonymized.jsonl` joined against
`condition_map_SEPARATE.jsonl` (all 18 trials, both `timing_check` and `main_run`
phases — the design's own stated rule is that the timing-check trial is legitimately
reused as trial 1 of 6, not discarded):

| Condition | Raw specificity values (in trial order) | Sorted | Mean | Median |
|---|---|---|---:|---:|
| A | 4, 5, 5, 5, 3, 4 | [3, 4, 4, 5, 5, 5] | 4.3333 | **4.5** |
| B | 4, 5, 5, 4, 3, 5 | [3, 4, 4, 5, 5, 5] | 4.3333 | **4.5** |
| C | 5, 5, 5, 5, 5, 5 | [5, 5, 5, 5, 5, 5] | 5.0 | 5.0 |

**A and B's sorted score multisets are identical**: `[3, 4, 4, 5, 5, 5]` for both. This
was independently computed here for the first time (neither prior document stated it)
and is itself further, orthogonal confirmation of Finding 1 — two genuinely different
treatments would have no particular reason to produce identical score distributions;
two runs of the same treatment under different labels have every reason to.

The discrepancy's source, confirmed by reading `scripts/task_type_behavioral_experiment_analyze.py`
directly: the original analysis used `sorted(spec)[len(spec) // 2]`, which for an
even-length list of 6 returns the upper-middle element (index 3, value 5) rather than
averaging the two central elements (indices 2 and 3: (4+5)/2 = 4.5). This is a plain
implementation bug in the analysis script, not a judgment call about which median
convention to use.

### Finding 3 — Isolation / the unpatched salience-write path

**Reverified, and independently strengthened beyond Codex's own hedged framing.**

`app/core/echo_core.py:723-752` (`compute_salience()`) unconditionally calls
`_persist_salience_state(result)` as its last action on every successful call.
`_persist_salience_state()` (lines 693-716) writes to the real, relative production
path `memory/salience_state.json` via a lock-guarded temp-file-then-`os.replace()`
pattern — a genuine write to shared production state, wrapped only in a bare
`except Exception: logger.debug(...)` that swallows failures silently but does not
prevent an otherwise-successful write.

`app/core/river_deliberation.py:1228-1229` confirms the call site actually reachable
from the experiment's own code path: inside `deliberate_and_learn()`'s council-selection
step, `from app.core.echo_core import compute_salience; exploration_bias =
float(compute_salience()...)`. Exhaustive grep of `scripts/task_type_behavioral_experiment.py`
for `echo_core`, `compute_salience`, and `_persist_salience_state` returns **zero
matches** — this path is genuinely unpatched by the experiment harness, confirming
Codex's finding.

**New evidence, not present in either prior document**: this call is gated —
`compute_salience()` is only invoked as a *fallback*, when a Global Workspace cache
(`_last_world_surprise`) is stale (`river_deliberation.py:1213-1229`). Whether the write
was **likely** (Codex's framing) or effectively **certain** depends on that cache's
state. Tracing it directly: `_last_world_surprise = {"value": 0.0, "ts": 0.0}` at module
import time (`river_deliberation.py:175`), and nothing in the standalone experiment
script — which does not start `run.py`'s background threads, EchoCore event bus, or any
Global Workspace subscriber — ever populates it. In a fresh process with this initial
state, `time.time() - 0.0` is on the order of 1.7 billion seconds, categorically
exceeding the 120-second cache TTL (`_WORLD_SURPRISE_CACHE_TTL`). **This means the
fallback branch calling `compute_salience()` was structurally guaranteed to execute on
every single trial in this experiment's own process**, not merely plausible — a stronger
claim than either prior document made, independently derived from the module-level
default and the harness's own missing setup, not from the write's actual success (which
still cannot be directly observed; see below).

Distinguishing the required categories precisely:

- **POTENTIAL WRITE PATH**: confirmed to exist and be reachable (not merely theoretical).
- **CONFIRMED WRITE**: not established. `compute_salience()`'s four components are each
  individually documented as fail-closed (never raise); no exception is expected, but
  this mission did not instrument the call to observe it firing, and the live production
  process (PID 7644, confirmed running throughout) also writes to the same file on its
  own ~120s introspection cadence, so the file's current content/mtime cannot be
  attributed to the experiment specifically (matching Codex's own stated limitation).
- **CONFIRMED CONTAMINATION**: not established, for the same reason — no way to
  distinguish an experiment-caused write from the live process's own ordinary writes to
  the same file after the fact.

**Verdict: "complete isolation" was an overclaim. The correct, conservative statement is
a real, structurally-near-certain write path existed and was not neutralized; whether it
altered anything that mattered (this file has no downstream consumer that gates a
safety-relevant decision — it's an observational trend value, per its own module
docstring) is a separate, smaller question this mission does not resolve either.**

### Finding 4 — "ISOLATION BREACH DETECTED"

**Reverified: MISLABELED DIAGNOSTIC, confirmed precisely, and distinguished cleanly from
Finding 3.**

`scripts/task_type_behavioral_experiment.py:127-154` defines
`_ReadOnlyRiverBrainProxy.learn()`/`.save()` and three `_noop_log_*` functions. Each one
does exactly one thing: append a record to the module-level `_side_effects_detected`
list, then **return without calling any real underlying writer**. There is no code path
by which an entry in this list represents a write that actually reached disk through
these particular intercepted functions — every entry is proof of a *successful
interception*, not a *leaked write*.

`_side_effects_detected` is only ever appended to by these five interception points
(`RiverBrain.learn`, `RiverBrain.save`, `log_interaction`, `_log_council_deliberation`,
`_log_synthesis_integrity`); the salience-write path from Finding 3 is a structurally
separate, unpatched mechanism with no relationship to this counter. The print statement
(`scripts/task_type_behavioral_experiment.py:397-398`) fires whenever
`len(_side_effects_detected) > 0` — which is guaranteed on any real run that generates
real responses (every trial calls the three learn-eligible functions at minimum), making
the alarming wording actively misleading about what the counter measures, even though
the mechanism it measures is safe.

**Classification: MISLABELED DIAGNOSTIC — confirmed benign for exactly what it counts
(the five intercepted functions), and explicitly not evidence about anything else,
including the separate Finding-3 salience path.** This finding must not be read as
resolving Finding 3 (nor did the original report's characterization of it correctly draw
that line — it described the mislabeling and moved to "genuinely benign" without
addressing the salience path at all).

### Finding 5 — Historical TOOL-LIST delivery

**Reverified: Codex's finding is correct — one specific table cell in the prior
archaeology note used "CONFIRMED" in a way that overstates what was actually
established.**

`audits/2026-09-14_task_type_downstream_behavior_archaeology.md:131` states, for the
historical September 14 Condition-C-equivalent path: *"Same shared assembly plus a
TOOL-LIST system note (§5.2), **CONFIRMED present** via the `task_type in
TOOL_AWARE_TASKS` gate."* But that same document's own §5.2 discussion (echoed and
extended by Codex's independent trace of `echo_model_orchestrator.py:1499-1517`)
establishes that the gate has **three** conditions, not one: task-type eligibility
*and* successful import/registry access *and* a non-empty tool registry. Task-type
eligibility alone is the only one of the three actually checked against the historical
turn — the registry-population state of the live process at that specific moment on
September 14 was never independently verified, because `memory/interaction_log.jsonl`,
`memory/council_deliberations.jsonl`, and `memory/synthesis_integrity_log.jsonl` do not
store system messages, only prompt/response text.

The correct evidentiary tier, using the mission's own vocabulary:

- **Gate could have been satisfied**: yes — `task_type` resolved to `coding`, which is
  in `TOOL_AWARE_TASKS`.
- **Gate was probably satisfied**: plausible but unverified — the live production
  process ordinarily bootstraps tool discovery at startup (`run.py`), making a non-empty
  registry likely in steady-state operation, but "likely in steady state" is not the
  same claim as "confirmed for this specific historical request."
- **TOOL-LIST construction occurred**: not directly observed.
- **TOOL-LIST was passed to the model**: not directly observed.
- **TOOL-LIST was model-visible**: not directly observed.

**Verdict: "CONFIRMED present" (as written) should be downgraded to "gate condition
satisfied; full delivery chain plausible but unverified."** This is a real, if narrow,
overclaim in the predecessor document — one cell in one table, not a pervasive pattern
in that report, but exactly the kind of upgrade this reconciliation exists to catch and
correct rather than silently inherit.

---

## Phase 2 — Actual vs. intended condition matrices

### INTENDED condition matrix (as named/designed)

| Stage | A — Direct Personal | B — Council Personal | C — Council Coding |
|---|---|---|---|
| Routing | `DIRECT_ECHO_TASKS` bypass (1 model) | Council path (3 models + synthesis) | Council path (3 models + synthesis) |
| task_type | personal | personal | coding |
| Councillors | none (single model) | qwen2.5-coder, llama3.1, echo:latest | Same |
| Synthesis template | n/a | General | Coding-specific |
| TOOL-LIST | n/a | Absent (personal not in TOOL_AWARE_TASKS) | Present (coding is in TOOL_AWARE_TASKS) |
| Purpose | Isolate council-participation effect (vs. B) | Baseline for template effect (vs. C) | Isolate template/framing effect (vs. B) |

### ACTUAL condition matrix (reconstructed from executable behavior, this mission)

| Stage | A, actual | B, actual | C, actual |
|---|---|---|---|
| Routing | **Council path** (DIRECT_ECHO_TASKS cleared process-wide before either loop; never restored) | Council path | Council path |
| task_type argument | personal | personal | coding |
| Council selection | Forced fixed list (`_select_council` replaced entirely — real selection/TAG_SCORE_BOOST/exploration logic never executes for any condition) | Same | Same |
| Councillors, in order | qwen2.5-coder:7b, llama3.1:8b, echo:latest | Same | Same |
| Final/synthesis model | echo:latest | Same | Same |
| Shared supplied system | 502-char EPISTEMIC-NOTE (`base_system`) | Identical | Identical |
| TOOL-LIST | Absent (harness never bootstraps `ToolManager`'s registry; `T.ToolManager()` instantiated but not populated) | Absent | **Also absent** — the intended B/C contrast on this axis was never actually present in either condition |
| Synthesis system suffix | General template; literal `Task type: personal` | Identical | Coding preservation template; no `task_type` interpolation |
| Coding agreement/completeness guards | Not entered | Not entered | Entered; ordinary accepted synthesis for all five main-run C trials |
| Circuit-breaker key | (model, personal) | Same shared keys as A | (model, coding) — separate keyspace |
| Salience read/write path | Reachable, unpatched, structurally near-certain to fire (Finding 3) | Same | Same |
| Measured specificity | mean 4.333, median 4.5 | mean 4.333, median 4.5 (identical score multiset to A) | mean 5.0, median 5.0 |

**Every mismatch between the intended and actual matrices**:

1. A's routing (intended: direct/1-model; actual: council/3-model+synthesis) — the
   central defect (Finding 1).
2. TOOL-LIST (intended: absent for A/B, present for C; actual: absent for **all three**,
   since the harness never bootstraps the tool registry) — this means the experiment as
   actually run tested the synthesis-template swap **in isolation from** the TOOL-LIST
   mechanism the original archaeology identified as the second confirmed model-visible
   consequence of task-type classification, not a compound test of both. This was stated
   as a known gap in the original report; this mission confirms it is correct and adds
   the specific mechanical reason (`ToolManager` instantiated but never bootstrapped, so
   its registry stays `{}`).
3. Salience path (intended: not addressed at all in the original design; actual: a real,
   near-certain-to-fire, unpatched write route) — an isolation gap the original design
   simply never considered, not a deviation from an intended control.

---

## Phase 3 — Claim ledger

Evidence-tier definitions used: **VERIFIED** (direct primary evidence or a deterministic
mechanism independently checked), **SUPPORTED** (convergent evidence with a bounded gap),
**WEAKLY SUPPORTED** (a directional signal with serious uncertainty), **UNRESOLVED**
(evidence cannot discriminate between live possibilities), **NOT SUPPORTED** (the
asserted positive claim lacks sufficient affirmative evidence — not its negation),
**FALSIFIED** (directly contradicted by primary evidence).

| # | Claim | Verdict | Reasoning |
|---|---|---|---|
| C1 | Task-type classification occurred | **VERIFIED** | `H1`–`H3` (interaction_log/council_deliberations/synthesis_integrity_log) directly record `task_type=coding` for the historical trace; keyword-scoring arithmetic independently reproduced by the prior archaeology and re-confirmed here as internally consistent. |
| C2 | Task type altered routing | **VERIFIED** | `river_deliberation.py:1162`'s `if task_type in DIRECT_ECHO_TASKS:` is a hard, unconditional gate; deterministic given the historical `coding` classification never satisfies it (coding is not a member of `DIRECT_ECHO_TASKS`). |
| C3 | Task type changed model-visible synthesis input | **VERIFIED** | Two independently-confirmed mechanisms: (a) the literal `Task type: {task_type}` interpolation plus an entirely separate `SYNTHESIS_SYSTEM_TEMPLATE_CODING` template selected purely on the label; (b) the `TOOL_AWARE_TASKS`-gated TOOL-LIST note construction mechanism (existence and construction logic verified in source; historical delivery for this specific turn is the separate, weaker claim in C12 below). |
| C4 | Condition A was a direct-path control | **FALSIFIED** | Phase 1, Finding 1 — independently reproduced call-pattern evidence (identical 4-call council+synthesis shape across all A and B trials) plus source confirmation that `DIRECT_ECHO_TASKS` was cleared process-wide before any condition-specific branching occurred. |
| C5 | A→B measured council participation | **FALSIFIED** | Direct consequence of C4 — A and B are the identical treatment (council path, `task_type=personal`, identical system content), differing only by label; the comparison measures repeat-sampling noise of one treatment, not two different treatments. |
| C6 | Council participation showed zero behavioral effect | **NOT SUPPORTED** | This is the "no evidence of effect" / "evidence of no effect" distinction the mission specifically flags: A vs. B produced `p=1.0` because they are the same treatment run twice (identical score multisets, independently verified), not because a genuine direct-vs-council contrast was tested and came back null. No valid test of this question exists in this dataset. |
| C7 | The synthesis-template swap caused degradation | **NOT SUPPORTED** | The measured direction runs opposite (C scored higher than B); no result in this dataset supports this claim in either causal direction, and the historical trace's own already-generic raw candidates (independently re-confirmed present in `H2`) remain a live alternative explanation for the historical event specifically. |
| C8 | The synthesis-template swap showed no evidence of degradation | **WEAKLY SUPPORTED** | The narrow, isolated template-swap comparison (B vs. C, both council, both TOOL-LIST-absent) found a numerically higher score for the coding template — a real directional signal at n=6, not statistically decisive (exact permutation p=0.182), and scoped only to the specificity endpoint on one frozen prompt with a judge that saw an abbreviated question description, not the historical framing. This does not extend to "the coding template is safe in general" or "no degradation exists on any other dimension." |
| C9 | Condition C numerically outscored B on specificity | **VERIFIED** | Independently recomputed directly from raw `judge_scores_anonymized.jsonl`/`condition_map_SEPARATE.jsonl`: C mean 5.0 vs. B mean 4.333, C median 5.0 vs. B median 4.5, reproduced exactly by this mission's own arithmetic, not accepted from either prior report. |
| C10 | The experiment established complete isolation | **FALSIFIED** | Phase 1, Finding 3 — a real, unpatched, structurally near-certain-to-fire write path to `memory/salience_state.json` existed throughout the run. "Complete" is directly contradicted by this concrete, identified gap, independent of whether any specific write is separately provable. |
| C11 | The "ISOLATION BREACH DETECTED" message represented a real isolation breach | **NOT SUPPORTED** (classified **MISLABELED DIAGNOSTIC** per Phase 1, Finding 4) | The counter it reports on exclusively measures successful interceptions of five specific functions, never a leaked write; its alarming label does not match what it measures, but what it measures is genuinely benign. This verdict is scoped narrowly to those five functions and explicitly does not extend to or resolve C10. |
| C12 | Historical TOOL-LIST delivery was confirmed | **NOT SUPPORTED** (downgrade from the predecessor document's stated "CONFIRMED") | Phase 1, Finding 5 — only the task-type eligibility leg of a three-part gate was actually checked against the historical turn; registry population and actual delivery were never directly observed for that specific historical request. |
| C13 | The experiment reproduced the complete historical compound treatment | **FALSIFIED** | Beyond the TOOL-LIST gap (C12): council selection used a fixed list rather than real selection dynamics; candidates were freshly sampled rather than the historical model outputs; no conversation history/retrieval/ground-truth/circadian/temporal/scripture context beyond the frozen EPISTEMIC-NOTE was assembled; the historical council included `mlx:qwen3` where the experiment substituted `llama3.1:8b`. These are confirmed architectural omissions, independently verified against `app/ollama_handler.py`'s message-construction logic and the experiment script's own frozen-context-building function, which calls none of the production context-assembly steps beyond the one epistemic note. |
| C14 | The original causal story was weakened by controlled testing | **NOT SUPPORTED** as originally framed | The claim as stated in the September 14 report leaned on the invalid A-vs-B comparison as part of its support. With that comparison removed, what remains is a narrower, still-real result (C8) that neither confirms nor refutes the original historical causal story — it should be retained as an untested hypothesis with a plausible alternative (candidate-generation-stage genericness, independently visible in the raw historical councillor text), not as a story that controlled testing actively weakened. |

---

## Phase 4 — Statistical correction

Recomputed directly from the raw saved judge scores (not derived from either prior
report's summary tables):

| Condition | n | Values (sorted) | Mean | Median |
|---|---:|---|---:|---:|
| A | 6 | 3, 4, 4, 5, 5, 5 | 4.3333 | 4.5 |
| B | 6 | 3, 4, 4, 5, 5, 5 | 4.3333 | 4.5 |
| C | 6 | 5, 5, 5, 5, 5, 5 | 5.0 | 5.0 |

**A vs. B**: identical sorted multisets. Mann-Whitney U=18 (maximal tie), independently
recomputed; this is not evidence of "no council effect" — it is a mathematical
consequence of comparing a treatment to itself.

**C vs. B**: independently recomputed Mann-Whitney U (C as reference group) = 27,
matching the asymptotic normal-approximation two-sided p=0.0731 both prior documents
report. Going further than the original report (but reproducing Codex's own exact
approach independently): the exact permutation p-value, enumerating all C(12,6)=924
possible relabelings of the pooled 12 B/C scores into two groups of 6 and counting
those at least as extreme as the observed split, is **p=0.1818** — meaningfully looser
than the asymptotic figure, which the original report presented as the primary (and
only) statistic. Under a 12-observation sample with heavy ties (12 of 18 total ratings
sit at the scale ceiling of 5), the asymptotic normal approximation is a weaker
justification for "near significance" language than it might appear; the exact test is
the more defensible number to lead with at this sample size.

**What the observed C > B difference does and does not establish:**

- **Does establish**: on this one frozen prompt, with this one forced council
  composition, under this one blinded specificity rubric, the coding-framed synthesis
  template produced numerically higher scores than the general template, in a small
  (n=6/arm) sample, with a real but not conventionally significant effect (exact
  p=0.182).
- **Does not establish**: that this generalizes to other prompts, that "specificity" as
  measured captures everything meant by "quality" or "not generic" (a response can
  become more detailed while less calibrated, less faithful to prior dialogue, or less
  accurate — none of which this endpoint measures), that the effect would hold with
  TOOL-LIST present (untested), that council participation itself has any particular
  effect (no valid comparison exists in this data), or that the historical September 14
  degradation had this mechanism as its cause (the historical trace differs from
  Condition C in council composition, candidate content, missing context assembly, and
  measurement procedure — C13).

---

## WHAT STILL SURVIVES

- Task-type classification is real, deterministic given the keyword-scoring rule, and
  independently reproducible from source (C1).
- Task-type classification is a hard routing gate with real, verified downstream
  consequences at the synthesis-template and TOOL-LIST-eligibility stages (C2, C3).
- Condition C's numerically higher specificity score versus B, on this narrow,
  isolated template-swap comparison, reproduces exactly under independent recalculation
  (C9), including a stricter exact-test recomputation that was not in the original
  report.
- The "ISOLATION BREACH DETECTED" diagnostic is genuinely mislabeled rather than
  indicating a real breach of the five specific functions it measures (C11) — this
  narrow technical finding holds regardless of the broader isolation question.
- The historical raw councillor candidates were already list-heavy/generic before
  synthesis touched them (independently re-confirmed present in `H2`'s full
  `response_raw` field) — a real, still-standing alternative explanation for the
  original September 14 observation.

## WHAT NO LONGER SURVIVES

- **The claim that Condition A tested a direct-path (non-council) baseline** — falsified;
  A ran the identical council+synthesis treatment as B.
- **The claim that A vs. B measured, and found no effect from, council participation** —
  no such comparison was actually performed; the null result is an artifact of comparing
  one treatment to itself, not a finding about council participation.
- **The claim that the experiment established complete production isolation** — a real,
  structurally near-certain-to-fire, unpatched write path to `memory/salience_state.json`
  was present throughout the run.
- **The claim that historical TOOL-LIST delivery was "confirmed"** — only task-type
  eligibility (one of three required gate conditions) was actually checked against the
  historical turn; full delivery remains inferred, not observed.
- **The broader framing that "controlled testing weakened the original causal story"** —
  that framing leaned on the now-invalid A/B comparison; what remains is a narrower,
  still-informative result that neither confirms nor refutes the historical explanation.

## WHAT REMAINS UNKNOWN

- Whether the historical September 14 turn actually received a populated TOOL-LIST note
  (registry state at that exact moment was never logged and cannot now be reconstructed).
- Whether the synthesis-template effect (C8) would survive with TOOL-LIST present, or
  interacts with it (Codex's C6/C7 — UNRESOLVED, no data addresses this).
- Whether any genuine council-participation effect exists at all — no valid direct-vs-
  council comparison has yet been run.
- Whether `_persist_salience_state()` actually wrote during this specific experiment run
  (structurally near-certain given the fallback-branch analysis in Phase 1 Finding 3, but
  not directly observed, and unattributable after the fact since the live production
  process writes to the same file on its own cadence).
- Whether the historical degradation has any single identifiable cause at all, versus
  being adequately explained by ordinary generation-stage variance in already-list-heavy
  raw candidates — this mission's evidence is consistent with either.

---

## Phase 6 — Preregistration for the next experiment (design only, not implemented)

**Objective**: separately estimate the synthesis-template main effect, the TOOL-LIST main
effect, and their interaction, while holding council participation constant across all
four cells and genuinely isolating each mechanism this time.

**Four treatment cells** (2×2 factorial): {general, coding} template × {TOOL-LIST absent,
TOOL-LIST present}. Council participation (3 forced councillors + synthesis) is an
invariant across all four cells — this design does not attempt to answer the separate
direct-vs-council question (C6), which would need its own, differently-controlled
experiment.

**Invariants across all four cells**: frozen user prompt (reuse the existing SHA1-
verified `FROZEN_PROMPT`); forced council composition and order (reuse
`FORCED_COUNCIL`); explicit sampler settings (`max_tokens`, `num_ctx`, and — a genuine
gap in the September 14 harness, independently confirmed by this mission — an explicit
synthesis temperature, since the prior run let the installed model/server default apply
unrecorded); model identities pinned by exact tag; RiverBrain/logging isolation via the
Finding-89 pattern; and, newly required by this reconciliation, an explicit patch of
`app.core.echo_core.compute_salience`/`_persist_salience_state` to either a no-op or a
redirected-path stand-in — the September 14 harness's uncontrolled gap.

**Manipulated variables**: synthesis template selection (general vs. coding) and
TOOL-LIST note presence, applied **independently of `task_type`** — do not vary a
`task_type` flag that silently also changes circuit-breaker keyspace, council
eligibility, or logging branch, as the September 14 design did. Select the template and
the note directly as independent parameters passed into the trial function.

**Candidate-bank reuse, the key methodological fix Codex's design correctly identifies**:
generate each independent replicate's three-councillor candidate bank **twice** — once
with TOOL-LIST absent in the candidate-generation call, once with it present — using
matched per-model seeds/settings across the two banks. Then synthesize **each of those
two banks under both templates** (4 synthesis calls per replicate, reusing 2 candidate
banks, not resampling candidates per cell). This isolates the template's effect on a
fixed set of candidates from the TOOL-LIST's effect on what the candidates themselves
contain, and lets the interaction term be estimated from the same underlying material
rather than confounded by fresh resampling noise at every cell.

**Isolation requirements**: reuse the Finding-89 `RIVER_BRAIN_PATH`-redirect-before-first-
access pattern; explicitly neutralize the `compute_salience`/`_persist_salience_state`
path (confirmed unpatched in the September 14 run); verify before generation that no
other unpatched production-write path exists by grepping the full `deliberate_and_learn()`
call graph for file writes, not just the ones the prior harness happened to intercept.

**Persistence paths that must be neutralized**: `memory/river_brain.pkl` (via redirect),
`memory/interaction_log.jsonl`, `memory/council_deliberations.jsonl`,
`memory/synthesis_integrity_log.jsonl` (via no-op replacement, as before), and
`memory/salience_state.json` (newly required).

**Raw evidence to capture**: every actual system message sent to every model call (not
previews), the exact TOOL-LIST note text used (with an explicit, attributable
justification if a live registry snapshot cannot be obtained — Codex's design correctly
flags that fabricating a plausible-looking note and calling it historical would be
worse than omitting the mechanism), full candidate texts pre- and post-synthesis,
finish-reason/guard-outcome metadata, and model digests where obtainable.

**Scoring**: a blinded judge rating specificity, relevance, factual calibration, and —
new, since the September 14 rubric could not assess it — fidelity to the actual full
original question (the prior judge received only an abbreviated topic description, a
real validity limitation Codex identified). Score both candidates and final synthesized
responses, not only the final response, so candidate-to-synthesis information loss can
be measured directly rather than inferred.

**Blinding**: judge model must not be a forced councillor; must receive the full
original question, not an abbreviated paraphrase; condition identity must not be
derivable from response structure alone (a real risk Codex flagged: the coding
template's "no narration" instruction could itself be a stylistic tell).

**Randomization**: randomize synthesis order across all four cells and replicates
(not blocked); record and report the order.

**Sample-size rationale**: N=6/cell was justified by runtime feasibility in the prior
run, explicitly not by statistical power (Codex's finding, independently endorsed here —
12 of 18 September 14 ratings hit the scale ceiling, meaning ordinal saturation limits
what any small-N version of this design can resolve). A properly-sized N requires either
a pilot specifically measuring rating variance/ceiling behavior at this endpoint (not
reusing September 14's already-inspected outcomes for that purpose), or accepting this
as an explicitly exploratory, hypothesis-generating run and stating that plainly rather
than reporting a near-significance narrative from an admittedly underpowered design.

**Abort conditions / contamination checks**: verify the salience patch is active before
the first real trial (not after); verify TOOL-LIST registry population succeeds and is
non-empty before treating any "present" cell as valid, rather than discovering after the
fact (as the September 14 run did) that the registry was silently empty; re-verify
`RIVER_BRAIN_PATH` redirection against the live file's hash/mtime before and after, as
Finding 89's own verification protocol already established.

**Can the design separately estimate the three effects?** Yes, in principle, given the
candidate-bank-reuse structure above — a standard 2×2 with matched banks supports
estimating both main effects and the interaction term via a two-way analysis (e.g.,
Scheirer–Ray–Hare for ordinal data given the expected ceiling effects, rather than
assuming normality). **Whether it is currently buildable is a separate, narrower
question**: the TOOL-LIST registry-population prerequisite (bootstrapping
`ToolManager` correctly without importing/executing unrelated production discovery side
effects) has not yet been demonstrated as achievable in an isolated harness — this is a
genuine open prerequisite, not assumed solved by this design.

---

## Phase 7 — Meta-methodological lesson

**Why did the original adversarial-falsification pass (in the September 14 mission) fail
to catch Condition A?** Tracing the procedural cause rather than assigning blame: the
falsification pass attacked the *statistical interpretation* of the results (asked
whether stochasticity, model drift, or the scorer could explain the observed C vs. B
difference) but never independently reconstructed *what each condition actually
executed* from the code and call-evidence — it trusted the condition's name and the
script's own stated intent (the docstring's claim that A was direct) rather than
verifying the executed control flow against that claim. This is precisely the failure
mode the function's own docstring reveals: the author's stated intent ("Condition B
needs...") was correct, but nothing in the adversarial pass checked whether the
*implementation* matched that stated intent for *every* condition, not just the one it
was written about.

A second, related contributing factor: the interception-counter diagnostic
("ISOLATION BREACH DETECTED" reporting zero) was read as blanket confirmation that
"nothing production-relevant happened," when it only ever measured five specific,
individually-patched functions — a narrower guarantee than its framing implied. This is
the same "counts intercepted attempts, not measured write success" gap Finding 4
formalizes.

**Procedural safeguard recommended for future FeralEcho experiments**: before
interpreting *any* experimental condition's result, independently reconstruct its
*actual executed treatment* from primary evidence (intercepted call patterns, raw
system/prompt text actually sent, module-state at call time) — never from the
condition's name, its docstring, or its author's stated intent, however precisely
worded that intent is. Call-pattern accounting (as done in this mission's Finding 1,
grouping intercepted calls by trial and comparing shapes across conditions) is a cheap,
concrete, and — as demonstrated here — decisive check that should be a standard,
required step of any future FeralEcho experiment's own internal verification, not an
optional adversarial afterthought performed by a second party after the fact.

**Assessment of the proposed rule** — *"Before interpreting an experimental condition,
reconstruct its actual executed treatment from evidence rather than trusting its name or
intended configuration"*: **this mission's evidence directly supports adopting it.** The
single largest defect in the September 14 experiment (Finding 1/C4/C5) would have been
caught immediately by applying exactly this rule during the original design or its own
adversarial-falsification pass, using evidence (the call-pattern grouping performed in
Phase 1 above) that was already being collected by the harness itself and simply never
cross-checked against condition labels before this reconciliation did so.

---

## Final verdict

1. **Corrected classification of the experiment**: the narrow, isolated
   synthesis-template comparison (B vs. C, both council, both TOOL-LIST-absent) is
   valid and reproducible, with a real but statistically inconclusive (exact p=0.182)
   directional result. The broader experiment, as designed, failed to deliver a valid
   direct-vs-council comparison (its stated primary purpose per its own condition
   table) due to an unrestored global state mutation.

2. **Strongest surviving result**: Condition C scored numerically higher than Condition
   B on the blinded specificity endpoint (mean 5.0 vs. 4.333, median 5.0 vs. 4.5),
   independently reproduced from raw data by this mission.

3. **Most important invalidated conclusion**: "council participation showed zero
   behavioral effect" (C6) — no valid test of this claim exists in this dataset;
   Condition A was not a direct-path control.

4. **Most important unresolved question**: whether the confirmed TOOL-LIST mechanism
   (present in production, absent from every condition in this experiment) independently
   affects behavior or interacts with the synthesis-template effect — genuinely untested,
   not merely under-evidenced.

5. **Isolation status**: not complete. A real, unpatched, structurally near-certain-to-
   fire write path to `memory/salience_state.json` existed throughout the run
   (POTENTIAL WRITE PATH, confirmed; CONFIRMED WRITE and CONFIRMED CONTAMINATION, both
   unresolved and likely unresolvable after the fact given the live process's own
   ordinary writes to the same file).

6. **Historical TOOL-LIST evidence status**: downgraded from "confirmed present" to
   "eligibility gate satisfied; full delivery chain plausible but not directly observed"
   — one of three required gate conditions was checked against the historical turn, not
   all three.

7. **Is another experiment justified?** Yes — specifically the 2×2 factorial designed in
   Phase 6, which is the minimum design that separates the template and TOOL-LIST
   mechanisms this experiment conflated by omission (both effectively absent).

8. **Is the 2×2 design currently buildable?** Partially. The template-axis manipulation
   and candidate-bank-reuse structure are buildable now, reusing existing validated
   machinery (Finding 89's isolation pattern, the existing frozen-prompt/forced-council
   apparatus). The TOOL-LIST-present cells require first demonstrating that
   `ToolManager`'s registry can be faithfully bootstrapped in an isolated harness without
   executing unrelated production discovery side effects — an open prerequisite, not
   assumed solved.

9. **Confidence**: high in the Condition-A defect, the corrected medians, the mislabeled-
   diagnostic classification, and the reproduced C-vs-B descriptive statistics (all
   independently re-derived from primary evidence in this mission, not merely
   cross-checked against prose). Moderate in the narrow template-effect interpretation
   (C8). Low in any claim about the historical September 14 turn's actual cause, in
   either direction.

10. **Evidence that would change this conclusion**: a captured, dated snapshot of the
    live process's tool registry contents at or near the September 14 timestamp (would
    resolve the TOOL-LIST delivery question); direct instrumentation confirming or ruling
    out an actual write to `memory/salience_state.json` during a rerun with logging added
    around that specific call (would resolve the isolation question definitively); a
    properly-powered, correctly-isolated 2×2 factorial per Phase 6 (would resolve the
    template/TOOL-LIST main-effect and interaction questions this experiment could not).

---

## Integrity check

- Ending Git HEAD: `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged.
- Files created by this mission: exactly one —
  `audits/2026-09-15_task_type_experiment_reconciliation.md` (this file).
- Files modified: none. The original September 14 report and Codex's independent review
  were both read, never edited.
- No code, configuration, or memory files were touched. No `2×2` factorial trial of any
  kind was run. No experiment harness was repaired. No git operation (add, commit, reset,
  checkout, rebase, branch, push) was performed.
- Runtime processes (`PID 7644`, `7636`, `87918`) were not signaled, attached to,
  restarted, or otherwise disturbed at any point during this mission.
