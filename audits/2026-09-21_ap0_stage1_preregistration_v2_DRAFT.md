# AP-0 Stage 1 — Pre-registration v2 (**DRAFT, UNFROZEN, UNQUALIFIED**)

**Status.** This document is a *proposal*. It is **not frozen**: it has no hash in any FREEZE file, no sealed Stage 1 material exists, and **Stage 1 has not been run and is not authorized.** It is deliberately left unfrozen because constructor qualification (QUAL-1) did **not** qualify the constructor for the conventions where induction is actually required (see §3). v1 (`2026-09-21_ap0_stage0_preregistration_v1.md`) and all Stage 0 evidence are untouched. Every threshold below is a **prospective v2 choice**; none is applied retroactively to Stage 0.
**Labels.** OBSERVED = measured/read in this or the Stage 0 evidence; INFERRED = reasoned; DESIGN = a control/rule specified here, not yet exercised.
**Authorization.** Richie, 2026-09-21: design, apparatus repair, constructor qualification only. "DO NOT RUN STAGE 1."

## 0. The question, restated so it cannot be answered by accident
> *Can a frozen worker, given experience (episodes) that the harness cannot leak through any other channel, produce a **retained artifact** that (a) an evaluator independent of the constructor accepts, (b) survives a fresh-process boundary, and (c) causes correct behaviour on sealed novel tasks — where the artifact's content is demonstrably a function of that experience?*

Stage 1 is **not** a test of "learning" in the weight sense (no weights change), **not** a test of accumulation (Stage 2), and **not** a test of autonomous experience selection (the harness chooses episodes, schema, validation tasks and oracle).

## 1. What Stage 0 (v1) settled, and what it did not
OBSERVED (re-audit `reaudit`/`reaudit_r2`: PASS WITH CAVEATS, 26/27): the worker can *use* a stated procedure (H 0.815 vs N/NEUTRAL/MISMATCH 0.000 on T∪S), outputs follow carrier content (H−MISMATCH 0.815), instrument integrity holds. Form matters: raw episodes in the carrier (E 0.278) or inline (IC 0.222) are far weaker than a stated procedure; per convention E = K1 0.72 / K2 0.11 / K3 0.00 and IC = 0.67 / 0.00 / 0.00. **Therefore K1 is largely solvable from raw episodes already; K2 and K3 are exactly where a constructor's induction would add capability — and exactly where QUAL-1 found the constructor fails.**
Not settled by Stage 0: anything about acquisition; the "MISMATCH below N" question (N is at the 0.000 floor: unmeasurable); NEAR negative-control behaviour (defective set, see §6.2).

## 2. Hypotheses (v2)
Let *Q* be the set of conventions for which the **constructor is qualified** (§3). All confirmatory hypotheses are stated **only over Q**; a convention outside Q is reported descriptively and cannot support any claim.
- **A (acquisition consequence).** For conventions in Q: P beats NEUTRAL on sealed T∪S tasks by a margin larger than sampling error (P = the retained carrier the acquisition pipeline produced from episodes and accepted by the independent gate).
- **B (content is experience-determined).** P built from world *a*'s episodes beats P built from world *b*'s episodes on world *a*'s tasks, and vice versa (experience-swap double dissociation), and P beats MISMATCH.
- **C (gate validity).** P (first gate-passing draft) beats FAILED-DRAFT (a draft from the same process that failed the same gate) — otherwise the "independent evaluation" step does no work.
- **D (beyond restating).** P beats E and IC (same episodes, unprocessed). *Secondary, descriptive unless E/IC headroom exists; see §6.4.*
- **N-ctl (no harm).** P does not degrade NEAR tasks (whose text states a conflicting convention) relative to NEUTRAL, and does not change UNREL tasks.
- **Ceiling frame.** H (hand-written correct procedure) is the empirical, world-specific ceiling; acquisition efficiency = (P−NEUTRAL)/(H−NEUTRAL) reported only where H−NEUTRAL has a positive lower bound (§6.5).

## 3. Constructor qualification result (QUAL-1) — *the reason this draft stays unfrozen*
<<QUAL_RESULTS>>

## 4. Design (proposed)
### 4.1 Worlds, tasks, arms
- 3 conventions (K1 lookup table, K2 tie-break ordering, K3 event→operation table) × **2 realizations (a, b)** with disjoint screened non-word tokens; worlds derived from `SHA-256("AP0-S1" ‖ hash(this document, once frozen) ‖ hash(Stage 0 evidence dir manifest) ‖ hash(QUAL results))` — **after** freeze; nothing sealed exists before that.
- Task sets per world: **T** 6 same-shape + **S** 4 structural per convention (10; primary set T∪S = 30 per world, 60 total, but clusters = 30 task templates, see §6.6), **NEAR 18** (6 per convention; repaired, §6.2), **UNREL 12**. Every task has 10 hidden cases built by greedy set-cover so that every single-parameter mutant is killed; hidden **VAL** and **TEST** case streams are disjoint; tests are re-verified against an independent second implementation and the real sandbox (OBSERVED for the v2 task set: `verify_accumulation_probe_v2.py`, 28 checks).
- Arms: **N**, **NEUTRAL** (length-matched foreign-convention note; the baseline for every negative-control contrast because Stage 0 found a scaffold effect on the NEAR set, +0.39, post hoc n=6), **MISMATCH** (same tokens, systematically wrong), **E** (raw episodes in carrier), **IC** (episodes inline), **H** (hand-written correct), **P** (retained constructed carrier), **P-X** (P from the *other* realization of the same convention), **FAILED-DRAFT** (the first draft that failed the gate; defined only when one exists — reported as "no failing draft" otherwise, never manufactured).
- Samples: 2 per task, seeds matched across arms within (world, task, sample); no retries after a model response; interleaved shard-waves as in v1.

### 4.2 Acquisition protocol (per convention × realization; **DESIGN, runner not yet built**)
1. *Experience*: the harness supplies the R0 episode list (raw canonical). R1 (grouped/augmented) may be used **only if** QUAL showed it is the better representation, and its display change is declared. The harness supplies the public task-type context that states the schema (e.g., "ties are resolved by the site's tag priority") — the schema is **given**, only its parameters are to be acquired.
2. *Construction*: constructor prompt from `constructor.py` (hash frozen), options temperature 0.5 / top_p 0.95 / num_predict 400 (or the QUAL-frozen alternative), up to **3** drafts (fixed seeds).
3. *Independent gate*: the worker (Stage 0 options) receives the draft in the carrier format and solves **4 VAL tasks**; **retain iff ≥ 2 of 4 pass**. The first passing draft = P; the first failing draft = FAILED-DRAFT. If no draft passes in 3 tries: *no P* — the convention is scored "acquisition failed" (a result, not an exclusion).
4. *Persistence*: the orchestrator writes P to a carrier file; SHA-256 recorded.
5. *Fresh process*: evaluation arms run as separate processes in kernel jails that cannot read acquisition ledgers, VAL tests, or the oracle; model unloaded (`keep_alive` 0) between acquisition and evaluation; evidence recorded per run: carrier hash before/after, PID and start time later than acquisition exit, jail profile hash, every request body (system+user+seed) hash-chained and re-derived from the frozen plan.
6. *Sealed exposure log*: sealed TEST worlds/cases are materialized **only after** step 4's carrier hashes are committed; a hash-chained exposure log records the first read of every sealed file; any read by an acquisition-side process aborts the run (INVALID, not a failed hypothesis).

### 4.3 Bypass controls (arrow by arrow — see `2026-09-21_ap0_v2_causal_chain_and_skeptic_review.md`)
Hidden tests/evaluator → constructor: jail + leak scan (OBSERVED in QUAL: 0 leaks in 432+72 requests). Previous responses / orchestration state → evaluation: separate processes, carrier-only channel. Production memory/RiverBrain/FAISS/routing: not imported (static+dynamic audit, OBSERVED); Ollama stateless per request. Filenames/task ids: never in prompts (OBSERVED re-derivation). Context residue: KV cache affects latency only (INFERRED; 8/8 same-seed identical, OBSERVED). Prompt-structure differences: identical templates, only carrier differs; NEUTRAL/MISMATCH length-matched to H (OBSERVED), P length reported.

## 5. Endpoints and thresholds (prospective v2; each justified from Stage 0 / QUAL / dev data)
Decision constants (draft values; the frozen version must restate them exactly in text):
```
GATE_MIN_PASS = 2            # QUAL: >=3/4 was too strict (worker misconsumes correct carrier in some worlds; dev H(K3)=0.35)
RETAIN_MAX_DRAFTS = 3
P_MIN_GAIN = 0.25            # pooled over Q, P - NEUTRAL, T∪S
P_GAIN_LOWER_MIN = 0.10      # one-sided 95% cluster-bootstrap lower bound
PX_DISSOC_MIN = 0.20         # own-world P minus cross-world P
FAILED_DRAFT_GAP_MIN = 0.20
NEAR_HARM_MARGIN = 0.15      # non-inferiority: P - NEUTRAL on NEAR >= -0.15 (lower bound)
UNREL_MAX_DROP = 0.10
HEADROOM_MIN_PER_CONV = 0.30 # (H - NEUTRAL) needed for a convention to enter the primary set
BOOT_N = 10000
```
**Primary (confirmatory, single):** E-A = (P − NEUTRAL) on sealed T∪S, pooled over conventions in Q, cluster bootstrap over task templates: gain ≥ P_MIN_GAIN **and** lower bound ≥ P_GAIN_LOWER_MIN. **Co-required gates for any "acquisition" claim** (intersection–union, so no multiplicity correction is needed; *all* must hold): E-B (P−MISMATCH ≥ P_MIN_GAIN **and** P-X double dissociation ≥ PX_DISSOC_MIN), E-C (P − FAILED-DRAFT ≥ FAILED_DRAFT_GAP_MIN, evaluated only when a failing draft exists), N-ctl (NEAR non-inferiority; UNREL drop ≤ UNREL_MAX_DROP), and the integrity gates (§7). Everything else (E, IC, H contrasts, per-convention rates, S-versus-T split) is secondary/descriptive and labelled as such; secondary contrasts are reported with Holm-adjusted intervals and never used to rescue a failed primary.
**Why these numbers (Stage 0 numbers, INFERRED where marked):** +0.25 gain: pooled MDE at 80% power with 30 clusters ≈ 0.15 (INFERRED from task-level SD 0.337 of H−N: 0.198·√(18/30)), so +0.25 is above the detectable floor; the +0.30 per-convention headroom is defensible because H−N cleared it in 3/3 Stage-0 conventions (0.72/0.61/0.83) but **not** in the v2 dev world for K2 (0.55) and K3 (0.35) (OBSERVED) — H is world-dependent, so headroom must be re-established in each sealed world (H arm is in the design for exactly this reason). Per-convention MDE ≈ 0.27 at 10 clusters: per-convention claims are limited to large effects. **The v1 ±10-point equivalence band is withdrawn** (unresolvable: n=6 NEAR tasks, MDE ≈ 0.34); replaced by a one-sided harm margin of 0.15, recomputed on the repaired 18-task NEAR set (half-width of the 90% interval at SD≈0.35, n=18 ≈ 0.14, INFERRED).
**"MISMATCH below N" (v1) is withdrawn**: N sits at the 0.000 floor in T∪S, so a drop below it cannot occur or be measured (OBSERVED: `mismatch_below_N_testable=false`). It is replaced by H−MISMATCH and P−MISMATCH (content specificity), which are measurable above floor.
Contrasts computed (all cluster bootstrap over task templates, 10,000 resamples, task-level paired): H−MISMATCH, P−MISMATCH, P−N, P−NEUTRAL (primary), P−E, P−IC, P−FAILED-DRAFT, H−NEUTRAL; same-shape (T) and structural (S) reported **separately**, never pooled into one transfer claim; every contrast also reported **per convention and per realization** (heterogeneity shown, not averaged away; a pooled effect driven by one convention is labelled as such).

## 6. Apparatus changes from v1 (each with the Stage 0 justification)
1. **Constructor + independent gate added** (v1 deferred FAILED-DRAFT because no acquisition existed).
2. **NEAR set repaired and grown 6 → 18.** Stage 0 finding: the K1 NEAR tasks contained a zero-key output trap, so H performed at 0.39 on them for reasons unrelated to carrier use; the set was defective as a negative control. v2 NEAR tasks state an explicit conflicting convention and have no such trap (dev, different world: N 0.75 / NEUTRAL 0.89 / H 0.83, i.e., a valid control whose answer follows the task text). NEUTRAL is the baseline (scaffold effect).
3. **Two realizations per convention + P-X arm** (experience-swap double dissociation), because a single realization cannot distinguish "the carrier encodes this world" from "any procedure-shaped carrier helps".
4. **10 tasks per convention (6 T + 4 S), was 6 T∪S**; per-convention MDE improves from ≈0.34 to ≈0.27.
5. **Gate threshold and validation-template rule** as amended pre-freeze in QUAL-1 §8 (≥2/4; templates by Laplace-smoothed pooled H rate) — recorded there before any constructor call.
6. **Cluster unit = task template** (each template instantiated in two worlds is not two independent tasks).
7. **Sealed-seed rule** now depends on this document's hash, Stage 0 evidence manifest and QUAL results.
8. **Auditor and process corrections** discovered during QUAL (disclosed, §3): the frozen K1 auditor mis-parsed grouped code lists; corrected as a separate file and validated against hand adjudication (Stage 1 does **not** use a content auditor at all — the truth is unknown there; retention is behavioural).

## 7. Integrity, exclusion and abort rules
- Integrity gates (all required, INVALID if any fails): FREEZE hash match at start and end; request re-derivation from the frozen plan for **every** call; zero hidden-literal leaks; ledger chains intact; runtime/regrade agreement ≥ 0.99; infra failures ≤ 2%; truncation ≤ 5%; model digest unchanged; zero reads of sealed files by acquisition-side processes (exposure log); carrier hash identical before/after; evaluation PID/start-time later than acquisition exit; oracle spoof probe never passes; independent second implementation agrees on all hidden cases.
- Exclusions: none for outcome reasons. A task or call is excluded only for a pre-declared infrastructure reason and is counted in the infra rate. A convention with **no gate-passing draft in 3 tries** is retained in the report as "acquisition failed" and contributes no P arm; primary pooling then covers the remaining Q members only (this is stated in advance, not chosen after seeing results).
- Abort: any integrity gate failing mid-run stops the run (`ABORT` file), the partial evidence is preserved, and the verdict is INVALID (not "no effect").
- The live FeralEcho server shares the Ollama queue; its process ids and any restart during the run are recorded per call window (a restart cannot change outputs — stateless API — but is disclosed).

## 8. What each outcome would mean (fixed before results)
| Outcome | Reading | Not permitted to conclude |
|---|---|---|
| P ≈ NEUTRAL while H ≫ NEUTRAL | acquisition failed: the artifact did not carry usable content (constructor/gate problem), although the worker *can* use a correct one | "the system cannot learn" |
| P > NEUTRAL, P ≪ H | partial acquisition (some facts right/wrong); report per-convention fact accuracy only if QUAL-style audit exists (it does not in Stage 1) | "learned the convention" |
| P ≈ H on T but P ≈ NEUTRAL on S | same-shape use only; no structural transfer | "generalization" |
| P > FAILED-DRAFT | the independent gate selects better artifacts than the constructor's own unfiltered output | "the constructor learned"; only "gate has discriminative value" |
| P ≈ FAILED-DRAFT | gate/retention adds nothing; P's success (if any) is the constructor's | "selection/retention works" |
| P-X ≈ P on own world | artifact effect is not experience-specific (prior/scaffold) | any experience-determined-content claim |
| K1 succeeds, K2/K3 fail (**the QUAL-predicted pattern**) | acquisition works for **table transcription only**; induction of an ordering/operation table not shown | "the system acquires conventions" |
| P > E and P > IC | constructor step adds capability beyond the worker's one-pass use of raw episodes | that this is "learning" rather than "offline compilation of examples" (definitional) |

## 9. Claims ladder (what Stage 1 may and may not be called)
1. **Ordinary in-context instruction following** — already shown by Stage 0 (H). Stage 1 adds nothing here.
2. **Offline summarization of examples** — Stage 1 can say whether a one-shot offline construction step improves on raw episodes (P vs E/IC). It cannot say this is more than compilation.
3. **Persistent storage of externally supplied knowledge** — excluded for *content* by P-X, MISMATCH, jail/leak controls; **not** excluded for *schema* (the schema is supplied) or for *episode choice* (the harness picks episodes that identify the convention).
4. **Experience-dependent construction of retained actionable state** — the strongest claim Stage 1 can support, and only for conventions in Q.
5. **Persistent acquired behavioural competence** — only in the narrow sense "acquired convention knowledge applied to new inputs and new task shapes in a fresh process"; **not** durable (no multi-day test), **not** accumulating (Stage 2), **not** autonomous (harness-chosen experience), **not** weight learning, **not** inheritance.
**Forbidden in any Stage 1 write-up:** "FeralEcho learned", "accumulation", "autonomous learning", "the model improved", "generalizes", any statement about real-world competence, and any claim about a convention outside Q. **Allowed (if all gates hold):** *"For invented convention(s) {Q}, a frozen 7B model, given episodes that identify the convention, produced a text procedure that an independent evaluator retained, that survived a fresh-process boundary, and that let the same frozen model solve new tasks (including structurally changed ones) it otherwise fails, with content demonstrably determined by the episodes."*
The skeptic's strongest form — *"you turned examples into prompt instructions and showed an LLM follows instructions"* — is **granted in part and cannot be fully rebutted by this design** (see the skeptic review): Stage 1 cannot distinguish learning from compilation, cannot show the system chose its own experience, and cannot show the schema was learned.

## 10. Budget (INFERRED from Stage 0: 554 calls, mean 15.3 s/call; v2 dev 14.6 s/call, 192 calls)
Per realization: 9 arms × 30 T∪S tasks × 2 samples = 540 (P-X and FAILED-DRAFT conditional) → ×2 realizations ≈ 1,080; NEAR 4 arms × 18 × 2 × 2 = 288; UNREL 2 arms × 12 × 2 × 2 = 96; acquisition ≈ 18 constructor + 72 gate + 4 FD-related ≈ 100. **≈ 1,550 calls ≈ 6.3 h** at 14.6 s (5–9 h under load); with 3 samples/task ≈ 2,300 calls ≈ 9 h. A Stage 1 orchestrator (acquisition → gate → carrier commit → fresh-process evaluation → exposure log) **does not exist yet** and must be built and self-tested (mock server, as in the v1/v2 verify suites) before any freeze.

## 11. Path to a freezable version (proposal, each step needs authorization)
1. Resolve constructor qualification for K2/K3 (§3): pre-declare a **QUAL-2 on *fresh* qualification worlds** (not the worlds already used, to avoid tuning to them) testing exactly one or two of: a staged constructor (observations → hypothesis → verification against episodes → note), a stronger local model, a self-consistency filter (draft must reproduce the episodes' outputs when applied by the worker — a *behavioural* self-check using only experience, no oracle), or a programmatic hypothesis-enumeration constructor (zero-cost, but it hard-codes the hypothesis space, so the claim shrinks to "persistence and consequence of an experience-derived artifact", explicitly not "the model induced the rule").
2. Build and mock-test the Stage 1 orchestrator.
3. Freeze this document (hash), then derive sealed worlds; only then, with explicit authorization, run.
**Do not** weaken thresholds or drop K2/K3 to make Stage 1 "pass": dropping them would silently convert the experiment into a K1 table-transcription test (OBSERVED: E already reaches 0.72 on K1 without any constructor).
