# VSL Prospective Causal Transfer Protocol — FROZEN

**Frozen before any new candidate is generated or inspected.** This document commits to
the inclusion rule, sample-size cap, and interpretation criteria in advance, per
"OPERATION SKILLFORGE — PROSPECTIVE CAUSAL TRANSFER GATE"'s explicit requirement. No
generation or inspection of any candidate covered by this protocol occurs before this
file exists on disk.

**Prior state (Commits A/B on `vsl-implementation`)**: `A=19e8135`
(overgeneralization defect), `B=ced95b7` (enclosing-call-context fix — scoping
transformations to their enclosing aggregation call, e.g. `sorted()` vs `max()`). Full
unit suite 15/15. Latest skill: `K2.T5.tag_priority_direction` v4 (`status=candidate`,
`held_out_verdict=FAIL`, `enclosing_call='sorted'`) — the v4 `FAIL` was diagnosed as an
honest **coverage gap** in the prior (retrospective, DIRECT-strategy-only) holdout
sample, not a defect in the fix: all 4 of that sample's real instances were `max()`-based,
so the `sorted()`-scoped skill correctly never had an opportunity to apply. This protocol
exists to test the skill prospectively, in a sample deliberately designed (before seeing
any outcome) to have a real chance of containing `sorted()`-context instances.

---

## Target

Evaluate the existing acquired skill `K2.T5.tag_priority_direction` (latest version at
freeze time — see "Frozen skill identity" below) **only** on genuinely fresh cases that
mechanically satisfy its current precondition, including the `enclosing_call='sorted'`
field added in Commit B.

## Inclusion rule (mechanical, outcome-blind)

A candidate enters the causal-transfer test set if and only if:

1. It is generated from the existing disjoint holdout world
   (`memory/experiments/skill_ledger/mvk/holdout_world.json`, `world_index=1`) — already
   confirmed disjoint from the acquisition world (`world_index=0`) by construction
   (`VT.build_world(world_index=1, taken=...)`, a fresh `taken` set, per `harness.cmd_build()`).
2. It uses a **seed never previously generated or inspected by this project** — see
   "Freshness guard" below for the exact mechanism.
3. `app.experiments.skill_ledger.diff_extract.apply_skill(code, FN_NAME, skill_pattern)`
   returns non-`None` — i.e., the existing VSL matcher (unmodified, as committed in B)
   judges the precondition to structurally match, `enclosing_call` included. This is the
   **only** admission test, and it is a pure, non-executing AST check (`apply_skill()`
   parses and pattern-matches; it does not run the candidate).

**Absolutely prohibited inclusion criterion: pass/fail oracle outcome.** The candidate's
oracle grade (`OR.grade(code, test_code)`) is **never consulted to decide set membership**.
Implementation discipline: the selection loop (Phase 5 script, `select_prospective_set()`)
computes and stores each candidate's grade as a side effect of `_generate_one()` (unavoidable
— grading is a local, non-LLM check the existing harness always computes alongside
generation), but the selection code path does not branch on it, does not print it, and does
not log it per-candidate during the selection loop. Every candidate's oracle outcome is
revealed only after the full eligible set (4 candidates, or the 20-candidate cap) is frozen
and this fact is recorded in the results file before any outcome is read back out.

## Sample size and hard cap

- **Target**: the first 4 eligible (rule above) candidates encountered, generated in
  strict seed order (sample index 0, 1, 2, ... ascending).
- **Hard cap**: inspect at most 20 fresh candidates total (sample indices 0–19 under the
  seed key below). Do not extend after seeing results. Do not change N after seeing
  outcomes. Do not skip an eligible candidate. Do not replace an eligible candidate with
  another.
- Stop as soon as either (A) 4 eligible candidates are obtained, or (B) 20 candidates
  have been inspected without reaching 4.

**World-to-candidate cap mapping**: this apparatus generates multiple "fresh candidates"
as distinct seeded completions **within one fixed world**, not as separate worlds (the
same convention `N_CANDIDATES_PER_FAILURE` already uses in `cmd_acquire()`/`cmd_transfer()`
— a "candidate" is one model generation against one task/world pair at one seed). No new
world is constructed for this protocol: the existing holdout world (index=1) already
provides the needed disjointness from acquisition (index=0), and generating a second new
world would not change what "fresh" means here (seed-level freshness is the operative
axis, established below). The 20-candidate cap therefore maps to 20 distinct seeds, all
against the single already-existing holdout world.

## Strategy choice — decided now, before generation, from already-existing evidence

**Generation strategy: `STEPWISE`, exclusively, for all 20 candidates.**

This is a pre-registered methodological choice, not a peek at outcomes: it is made before
any candidate in this protocol is generated, and is grounded entirely in
already-documented, already-collected evidence from acquisition (`acquisition_candidates.json`,
read during Phase 2 of the prior mission, cited in
`audits/2026-09-27_verified_skill_ledger_mvk_first_run_report.md`'s "Follow-up" section):

- Both real `sorted()`-based acquisition candidates (the failing/passing pair the skill
  was mined from) were generated under `STEPWISE`.
- The real `DIRECT`-generated candidate seen during acquisition (candidate 0) and all 4
  real `DIRECT`-generated holdout instances inspected during the retrospective transfer
  re-run (this same day) were `max()`-based, zero of them `sorted()`-based.

Continuing to sample `DIRECT` for this prospective test would very likely reproduce
Outcome C (insufficient coverage) for a reason already fully known in advance — that
would not be a fair prospective test of the skill's actual domain, it would be repeating
a sampling choice already shown not to produce eligible cases. Using `STEPWISE`
exclusively is the closest available thing to "sample from the distribution the skill's
domain actually occurs in," decided from prior structural evidence alone, with zero
reference to any outcome from this protocol's own candidates (none exist yet).

**Explicitly acknowledged trade-off, stated per Phase 10's warning**: `STEPWISE` is known
to have a non-zero real baseline pass rate absent any skill (unlike `DIRECT`'s ~0%
baseline, which is why the original retrospective transfer test used it). This means
`original_passed=True` is possible for some sampled instances even before considering the
skill — such instances are still eligible (per the inclusion rule, which does not consult
outcome) if their code structurally matches the precondition, but a `sorted()`-based
candidate whose own tag-priority negation happens not to affect a tie in that instance's
specific data could pass despite carrying the buggy pattern. This does not compromise the
causal test: TRUE vs. SUBSTITUTION compares the *same* generated instances with and
without the skill applied, so any such case will show `original_passed=True` under BOTH
conditions and contribute no artificial advantage to TRUE — the causal signal is read from
cases where `original_passed=False`, not from base rate differences between strategies.

## Freshness guard

- **Seed key**: `seed_for("PROSPECTIVE", TASK_ID, i)` for `i` in `0..19`, computed by
  `app.experiments.skill_ledger.common.seed_for()`, which hashes
  `f"VSL|{MASTER_SEED}|{replicate}|{key}|{sample}"`. The replicate string `"PROSPECTIVE"`
  has never been passed to *this module's* `seed_for()` before (distinct from `"ACQUIRE"`
  and `"TRANSFER"`, both already used and already inspected under this module) — grep-
  checked at drafting time. **Correction, caught during that same check, recorded rather
  than silently fixed**: the bare word "PROSPECTIVE" does appear elsewhere in this
  codebase, as a replicate label in `persistent_routing/harness.py` — but that module has
  its own, entirely separate `seed_for()` (`persistent_routing/common.py`, hashing
  `f"PR|{MASTER_SEED}|{replicate}|{task_id}|{sample}"`, `SEED_OFFSET=90000`, a different
  prefix string and different offset from this module's `"VSL"`/`150000`). The two
  functions never produce the same seed for the same replicate string — confirmed by
  inspecting both functions' source directly, not assumed from the offset comment alone.
  No actual collision; the freshness claim is about seeds *this module has computed*, not
  about English words being unique project-wide.
- **Code-identity check**: after generation, each candidate's `sha256_text(code)` is
  compared against every code hash recorded in `acquisition_candidates.json` (the 4 real
  acquisition candidates) and against the `failing_code_hash`/`passing_code_hash` fields
  stored in every skill version file. An exact match would indicate the model produced
  byte-identical code to something already seen — flagged as a contamination failure
  (Outcome D) if it occurs, not silently accepted.
- **World-identity check**: confirmed structurally by construction — the holdout world's
  own tag literals (already known from prior inspection to be `dabek`/`zapin`/`nidob`/
  `lojoz`) are disjoint from the acquisition world's (`zezen`/`jovow`/`josog`/`rotil`) and
  from every other previously-used world in this MVK. No candidate in this protocol can
  share the acquisition world's literals, since it is generated against a different
  `world` object entirely.
- **This is not the VECT mistake** (supposedly-unseen examples sharing an underlying code
  body): the task definition (`K2.T5`, `winner_with_score`) is necessarily shared — that
  is what "the same skill's applicability domain" means — but the *specific instantiated
  code*, tied to this world's own literals and this seed's own model completion, has not
  been previously generated or observed by this project before this protocol runs.

## Predeclared interpretation (verbatim from the mission, restated here as the frozen
commitment for this specific run)

- **Outcome A (causal transfer)**: ≥4 eligible instances obtained; TRUE meaningfully
  outperforms SUBSTITUTION on the frozen set; the advantage is attributable to the
  skill's application and disappears when the skill is absent. → Evidence for causally
  useful, restart-persistent procedural competence within the tested domain. Commit,
  update succession, continue toward accumulation without a further approval turn.
- **Outcome B (compatible cases exist, no advantage)**: 4 eligible instances obtained,
  but TRUE does not outperform SUBSTITUTION. → Read-only mechanical failure analysis
  (transformation semantics / consumer wiring / application mechanics / base behavior /
  ordinary defect / lack of transferable abstraction). No further precondition
  enrichment without flagging the risk of instance-fingerprinting first (Phase 10).
- **Outcome C (insufficient coverage)**: fewer than 4 eligible candidates found among the
  20 inspected. → Report the exact eligibility frequency; not a success or failure of the
  mechanism; recommend future task-family design with source/holdout coverage
  pre-planned, if relevant.
- **Outcome D (contamination)**: any freshness-guard violation. → Stop before running the
  causal test; report the contamination mechanism.

## Frozen skill identity (recorded now, before generation)

- Feature key: `K2.T5.tag_priority_direction`
- Latest version at freeze time: **v4** (loaded via `Skill.load_latest()`)
- `content_hash`: to be recorded at execution time by re-loading v4 and printing its hash
  (deterministic function of its own fields — already computed once at write time,
  `a45c0cabed41c35b8d300574d74c391dde3d6e5283d2640731abaa2ad07fb082`, per
  `memory/experiments/skill_ledger/provenance.jsonl` line 5).
- `precondition`: `UnaryOp(op=USub(), operand=Subscript(value=Name(id='tag_priority', ctx=Load()), slice=Subscript(value=Name(id='x', ctx=Load()), slice=Constant(value=2), ctx=Load()), ctx=Load()))`
- `transformation`: `Subscript(value=Name(id='tag_priority', ctx=Load()), slice=Subscript(value=Name(id='x', ctx=Load()), slice=Constant(value=2), ctx=Load()), ctx=Load())`
- `provenance.enclosing_call`: `"sorted"`
- **This skill is frozen for the duration of this protocol.** No reacquisition, no
  modification of precondition/transformation, no new context field, no tuning against
  this protocol's own candidates. The only VSL-internal action permitted is `reextract`
  if — and only if — a schema-migration issue prevents loading v4 under the current code
  (not expected; v4 was written under Commit B's own schema).

## Execution plan (for the record, not yet run)

1. `select_prospective_set()`: generate up to 20 `STEPWISE` candidates at
   `seed_for("PROSPECTIVE", "K2.T5", i)`, against the holdout world, checking eligibility
   via `apply_skill()` only, freshness via hash comparison, recording all 20 (including
   rejected) with their mechanical rejection reason. Stop at 4 eligible or the cap.
   Freeze the selected set to disk before reading any oracle outcome.
2. **TRUE**: fresh process, skill loaded normally, run the frozen set through the
   existing consumer flow (grade original; if failing and precondition matches, apply and
   re-grade).
3. **SUBSTITUTION**: fresh process, skill absent, regenerate the identical frozen seeds,
   grade only (no application step).
4. Compare, classify per the outcomes above, write up, update `NEXT_ACTION.md`.

---

## RESULTS (executed after this protocol was frozen; nothing above this line was
changed after generation began)

Implementation: `app/experiments/skill_ledger/prospective_transfer.py` (new module,
`select`/`true`/`substitution` subcommands — imports `harness.py`'s already-tested
`_generate_one()`/`_find_task()` rather than reimplementing them; does not modify
`diff_extract.py`, `ledger.py`, or `harness.py`).

### Selection (Phase 5) — outcome-blind, as specified

7 candidates generated (well under the 20-candidate cap) before 4 eligible were found.
Zero contamination (no generated code hash matched any acquisition-phase or prior
skill-provenance hash). Full record: `memory/experiments/skill_ledger/prospective/selection_frozen.json`
(written **before** any oracle outcome below was read or printed).

| index | seed | eligible | code hash (12) |
|---|---|---|---|
| 0 | 778353652 | **False** (precondition did not match) | `f9bcbb2af9df` |
| 1 | 1865002021 | **True** | `04375db6a644` |
| 2 | 631221088 | **False** (precondition did not match) | `e9d5d6cc52ab` |
| 3 | 962854599 | **True** | `43844a0d2028` |
| 4 | 1148256031 | **False** (precondition did not match) | `e9d5d6cc52ab` |
| 5 | 551344946 | **True** | `04375db6a644` |
| 6 | 261423061 | **True** | `04375db6a644` |

Selected set (frozen): indices **[1, 3, 5, 6]**.

**Frozen skill identity, re-verified at each subsequent phase**: `K2.T5.tag_priority_direction`
v4, `content_hash=a45c0cabed41c35b8d300574d74c391dde3d6e5283d2640731abaa2ad07fb082`,
`enclosing_call='sorted'` — `cmd_true()` re-checks this hash against the frozen protocol's
recorded value before running and would refuse to proceed on any mismatch (none occurred).

### TRUE (Phase 6, fresh process, PID=37655)

```
instance 1: original_passed=False skill_applied=True patched_passed=True
instance 3: original_passed=False skill_applied=True patched_passed=True
instance 5: original_passed=False skill_applied=True patched_passed=True
instance 6: original_passed=False skill_applied=True patched_passed=True
DONE. original pass rate=0/4  with-skill pass rate=4/4  skill applied on 4 instances
```

### SUBSTITUTION (Phase 7, fresh process, PID=37695 — confirmed distinct from TRUE's PID)

```
instance 1: original_passed=False (skill absent)
instance 3: original_passed=False (skill absent)
instance 5: original_passed=False (skill absent)
instance 6: original_passed=False (skill absent)
DONE. no-skill pass rate=0/4  (with-skill pass rate was 4/4)
advantage attributable to skill presence: YES
```

`original_passed` is bit-for-bit identical between TRUE and SUBSTITUTION for all 4
instances (independently regenerated in two separate fresh processes) — confirms
generation determinism holds, the same standard this project has used throughout.

### Independent correctness check (not part of the frozen protocol, done for due
diligence before classifying)

Manually re-derived the patch for instance 1's code via a direct `apply_skill()` call: the
negation `-tag_priority[x[2]]` is correctly removed to `tag_priority[x[2]]` — the same,
correct, minimal fix as every other confirmed case in this project, not a coincidental
pass. The hidden oracle (`H.VT.make_hidden_tests`) was inspected directly and confirmed
non-trivial: 10 real input/expected-output cases exercising genuine score/tag-priority
tiebreaks (e.g. a real tie at `score=3` between `tag='dabek'` (priority 1) and
`tag='nidob'` (priority 3), correctly expecting the lower-priority-number tag to win) —
the 4/4 pass is a real correctness confirmation, not an oracle artifact.

### Honest caveat, disclosed prominently rather than smoothed over

**The 4 selected instances are not 4 independently diverse draws.** Instances 1, 5, and 6
are **byte-identical code** (identical hash `04375db6a644...`); instance 3 differs from
them only in its return statement's surface form (`sorted_entries[0][:2]` vs
`sorted_entries[0][0], sorted_entries[0][1]`) — otherwise the identical buggy logic, same
`tag_priority` literal set (this holdout world's own literals, expected and correct, not
a flaw). Across all 7 candidates generated (eligible and rejected), only **4 distinct
code bodies** were produced at all. This is a real property of low-temperature
(`temperature=0.2`) `STEPWISE` generation on this specific short task, not a flaw in the
selection logic (which correctly required freshness only relative to *prior, already-
observed* project history — the freeze/freshness guard worked exactly as specified, and
Outcome D's contamination check is a different, correctly-negative check from this
diversity observation).

**Effect on how strongly this result should be read**: the causal claim itself — that
removing the skill removes the advantage, confirmed via two independently fresh OS
processes with matching determinism — is real and was not weakened by this. But the
**effective number of independently-informative test cases here is closer to 2 (one
exact-duplicate class, one trivial syntactic variant of it) than to 4.** This does not
retract Outcome A (the frozen protocol's inclusion rule required freshness relative to
acquisition and mechanical eligibility, not mutual diversity among the selected set, and
both were genuinely satisfied) — but it substantially bounds the claim's generality: this
result demonstrates the mechanism firing correctly and causally on **one real recurring
failure shape**, observed multiple times, not on four genuinely distinct failure
instances. Framed against Phase 10's warning (instance-fingerprinting): the *skill's own
precondition* remains genuinely general and literal-free (independently confirmed earlier
this project against different literal sets, e.g. `nizog`/`renem`/`dulup`/`dogiz`) — the
low diversity here is a property of *this sample*, not evidence the skill itself has
become an instance fingerprint.

### Classification: OUTCOME A — causal held-out transfer, evidence-qualified as above

All five of Outcome A's requirements are met on direct evidence:
1. Fresh compatible instances exist — 4, confirmed disjoint from acquisition by hash.
2. The acquired skill is actually consumed — `skill_applied=True` on all 4.
3. TRUE outperforms SUBSTITUTION meaningfully — 4/4 vs 0/4.
4. The difference is mechanically attributable to the acquired skill — `patched_passed`
   tracks `skill_applied` exactly; a direct, independent re-derivation of the patch
   confirms it is the correct, minimal fix, not a side effect.
5. Removing the skill removes the advantage — confirmed in a genuinely separate fresh
   process with matching determinism on the unpatched baseline.

**Interpretation, stated at the same precision the mission requires**: this is real
evidence for acquired, restart-persistent, causally useful procedural competence *within
the narrow domain actually exercised* — one recurring `sorted()`-context tag-priority
negation bug shape, on the `K2.T5` task family, observed across a low-diversity but
genuinely fresh sample. It is not yet evidence of transfer across a broad or diverse
range of instances, and the sample's low diversity (disclosed above) means a future,
higher-temperature or larger-cap prospective run would meaningfully strengthen (or could
still weaken) this specific finding. It remains, as the mission's own Outcome A text
states, **not yet accumulation** — accumulation is a separate, still-untested claim.
