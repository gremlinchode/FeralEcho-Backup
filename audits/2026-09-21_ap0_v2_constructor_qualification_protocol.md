# AP-0 v2 — Constructor Qualification Protocol (QUAL-1), frozen by hash before any constructor call

**Purpose.** Stage 1 must not be an uninterpretable joint test of (A) whether experience can produce useful retained state and (B) whether an incapable constructor can infer the convention. QUAL-1 measures (B) separately, on **qualification worlds that are a different seed namespace from Stage 0, from the v2 dev worlds, and from the (not-yet-materialized) sealed Stage 1 worlds**. It never exposes Stage 1 material and does **not** measure the P-versus-N transfer contrast: drafts are evaluated only on **validation** tasks (the proposed retention gate), never on test/transfer tasks.
**Authorization:** Richie, 2026-09-21 ("independently qualify the proposed Stage 1 acquisition/constructor path … NOT authorized to collect Stage 1 experimental outcome data").
**Not a claim about learning.** QUAL-1 asks whether the constructor can write an actionable procedure from episodes and whether the proposed independent gate can tell good drafts from bad. Nothing here is evidence about persistent learning or accumulation.

## 1. What is being qualified
1. **Constructor** (function: episodes → procedure note). Prompt: `constructor.py` (hash in FREEZE_QUAL.json). It is given the public task-type context (the same public description the worker gets), the observed episodes, and the instruction to state only what the episodes establish and to write "not established" otherwise. Options: temperature 0.5, top_p 0.95, num_predict 400 (drafts must differ across seeds for the retry rule to mean anything). Constructor model: `qwen2.5-coder:7b` (the worker itself) in phase QA; a contingency phase QB (below) uses one other locally installed model.
2. **Independent gate** (retention decision): the *worker* (`qwen2.5-coder:7b`, Stage 0 options) receives the draft in the Stage 0 carrier format and solves **4 validation tasks per (convention, world)** (1 sample each); hidden tests grade them. **Gate passes iff ≥ 2 of 4 pass** (see §8, pre-freeze amendments; ≥ 3 of 4 is reported descriptively). Validation tasks come from a partition (`VAL`) whose hidden cases are generated from a stream disjoint from the `TEST` stream that Stage 1's sealed tests will use, and from templates chosen by the rule in §4.

## 2. Design (frozen)
- **Worlds:** 2 realizations per convention (K1, K2, K3), tokens screened (non-words, mutually disjoint).
- **Representations** of the same latent convention:
  - **R0** raw canonical episodes (identical to Stage 0's E arm).
  - **R1** grouped-by-token and augmented episodes (K1: two amounts per code; K2: all six tag pairs in both name orders; K3: three start values per event). R1 is a deterministic *display/evidence* change; it does not state or hint the rule.
- **Drafts:** 3 per (convention, world, representation) → 6 per (convention, representation).
- **Adversarial variants** (2 drafts per world each; 4 per convention per variant):
  - **A1 missing evidence:** R1 with every episode involving one designated token removed. A safe constructor writes "not established" for that token; a fabricating one invents a value.
  - **A2 shuffled order:** R0 episodes shuffled (order dependence).
  - **A3 distractors:** R1 plus four episodes from a different convention (superficial-pattern / robustness).
- **Gate controls with known truth**, 2 replicate seeds each per (convention, world): **GOLD** (the correct hand-written procedure), **WRONG** (the systematically wrong MISMATCH procedure), **NONE** (no carrier). These qualify the gate itself (sensitivity and false-accept rate).
- **Ground-truth content audit** of every draft (qualification only; in Stage 1 the truth is unknown and only the behavioural gate exists): K1 exact iff all six code→category pairs are stated correctly and none wrongly; K2 exact iff the stated priority order equals the true one; K3 exact iff all four event operations and constants are correct. The auditor is regex-based and is itself validated on hand-written positive/negative texts (`scripts/verify_accumulation_probe_v2.py`); a sample of real drafts will additionally be read by hand and any auditor error reported.
- **Attack coverage:** incomplete induction (A1); memorization instead of rule extraction (flag `copies_episode_syntax`; an auditor-inexact draft; no table/order stated); superficial pattern matching (A3 and wrong-priority drafts); wrong priority/tie-breaking (K2 audit); missing reset/state behaviour (K3 `set` audit); overfitting to episode order (A2); dependence on literal identifiers (independent worlds have different tokens; performance is reported per world); accidental leakage (constructor prompts scanned for hidden-case literals; constructor runs in a kernel jail with no access to the oracle); a procedure that is correct in content but leads the worker to wrong behaviour (`exact_but_gate_fail`, reported); a procedure that passes the gate but is wrong (`inexact_but_gate_pass`, reported).
- **Isolation:** constructor and gate generation run through `run_gen.py` in per-root kernel jails (read/write only their own root; oracle unreadable); grading happens outside the jails.

## 3. Decision constants (exact; the code states the same values)
```
GATE_MIN_PASS = 2
GATE_SEEDS = 2
Q_EXACT_QUALIFIED = 0.8333333333333334
Q_EXACT_NOT = 0.16666666666666666
ADV_UNSAFE_MAX = 0.25
GATE_SENS_MIN = 0.85
GATE_FALSE_ACCEPT_MAX = 0.05
D_MAIN = 3
D_ADV = 2
NW = 2
```
Per convention, with `e` = content-exact fraction of the 6 main drafts of the better representation (ties → R0):
- **QUALIFIED** iff `e ≥ Q_EXACT_QUALIFIED` **and** the adversarial *unsafe-accept* rate (gate passes a draft that asserts something wrong, or an A1 draft that fabricates the missing token) ≤ `ADV_UNSAFE_MAX` **and** the gate is qualified.
- **NOT QUALIFIED** iff `e ≤ Q_EXACT_NOT`; otherwise **PARTIALLY QUALIFIED**.
- **Gate qualified** iff (pooled over conventions) GOLD pass rate ≥ `GATE_SENS_MIN` **and** pooled (WRONG ∪ NONE) pass rate ≤ `GATE_FALSE_ACCEPT_MAX`.
- **Overall:** QUALIFIED iff all three conventions QUALIFIED; NOT QUALIFIED iff all three NOT QUALIFIED; else PARTIALLY QUALIFIED.
With 6 drafts per cell the intervals are wide (Wilson 95% intervals are reported); the thresholds are decision rules, not precision claims.

## 4. Validation-template rule (fixed before validation results exist)
Per convention choose the **2 T and 2 S templates with the highest Laplace-smoothed pooled H pass rate**, `(successes+1)/(trials+2)`, pooled over the Stage 0 H/H2 arms and the v2 dev H arm (two different worlds); ties broken by more trials, then lower template index (`val_select.py`, output `v2/dev/val_templates_pooled.json`). This is chosen from H, i.e. from what a *correct* carrier achieves, so the gate is not asked to reject correct procedures because of worker implementation slips.

## 5. Contingency (fixed now, so it cannot be tuned to results)
If, after phase QA, any convention is not QUALIFIED with the worker as constructor, a single contingency phase **QB** may be run for the failing conventions only, with **one** pre-named zero-additional-cost alternative constructor: `deepseek-r1:7b` (locally installed reasoning model; its `<think>` block is stripped). Same worlds, prompts, representations (best of R0/R1 from QA), gate and decision rules. QB results are reported alongside QA, never merged into it, and no third constructor or prompt variant is tried.

## 6. What a QUALIFIED result would and would not mean
It would mean: this constructor, on these invented conventions and episode representations, writes a procedure that the audit says is exact and that the worker uses correctly, and the proposed gate separates good from bad drafts well enough to be an independent retention rule. It would **not** mean: that experience-derived procedures transfer to sealed tasks (Stage 1), that anything accumulates (Stage 2), or that any of this generalizes beyond invented conventions of these three shapes.

## 7. Stop rule
QUAL-1 runs to completion and its results are reported. **No Stage 1 acquisition, no sealed-test exposure, no transfer evaluation of drafts.**

## 8. Pre-freeze amendments (made after the v2 dev calibration, before any constructor call; recorded openly)
The dev calibration (a separate world; 192 calls; not Stage 1 data) showed that **H is world-dependent**: K3 H fell from 0.83 (Stage 0 world) to 0.35 in the dev world because the worker turned the correct carrier text "`nikeb: set to 4`" into `x + 4` on both samples. Two design choices were therefore changed before freezing:
1. **Gate threshold ≥ 3/4 → ≥ 2/4.** A correct procedure is sometimes misconsumed, so a strict gate would reject good drafts (false negatives). ≥ 2/4 remains safe against false accepts because (a) N sits at the floor (0.000 in Stage 0 T/S, so ≥ 2 passing tasks cannot occur without real information) and (b) every validation task's hidden cases were built to kill every single-parameter error, so a procedure with any wrong fact fails *every* task; passing ≥ 2 tasks essentially requires an exactly correct procedure. The strict ≥ 3/4 outcome is computed and reported descriptively (`gate_strict3`).
2. **Validation-template rule: dev-only → pooled** (§4), because a template's dev pass rate depends on the world. The dev-only file `v2/dev/val_templates.json` (written by `dev_analyze.py`) is **superseded and was never used**; it is retained unmodified.
Neither change looks at any constructor output. Result of the pooled rule: K1 {T1, T2, S1, S2}, K2 {T1, T6, S1, S3}, K3 {T4, T1, S1, S4}.
