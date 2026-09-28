# VSL Accumulated Competence Protocol (Checkpoint 7) — FROZEN

**Frozen before any Skill-B candidate is generated.** Per "OPERATION SKILLFORGE —
CHECKPOINT 7"'s explicit requirement. Nothing below this line is changed after
generation begins; results are appended in a clearly separated section afterward.

## Phase 0 — preserved state (re-confirmed, not modified)

- Branch `vsl-implementation`, HEAD `a9319c4` at freeze time. `main` untouched
  (`2fba426`).
- Commit chain: `19e8135` (initial MVK, overgeneralization defect) → `ced95b7`
  (enclosing-call-context fix) → `a9319c4` (prospective causal transfer, Outcome A).
- Unit suite: 15/15 passing (`verify_diff_extract.py`), unaffected by anything below.
- **Skill A, frozen exactly as-is, not reacquired or modified**:
  `K2.T5.tag_priority_direction`, latest version **v5** (written in this same session,
  immediately before this protocol, to honestly reconcile the ledger's own
  `held_out_verdict` field with the completed prospective result — v4 itself, the
  retrospective-FAIL record, is untouched; v5 is a new, additive, write-once version
  carrying full provenance for both verdicts). `content_hash=a5408f732897df353eb9ad6c6d8d2390794319910dd2ff5a4bd9da28a833501d`,
  `status=validated`, `held_out_verdict=PASS`, `is_eligible()=True`.
  - `precondition`: `UnaryOp(op=USub(), operand=Subscript(value=Name(id='tag_priority', ctx=Load()), slice=Subscript(value=Name(id='x', ctx=Load()), slice=Constant(value=2), ctx=Load()), ctx=Load()))`
  - `transformation`: `Subscript(value=Name(id='tag_priority', ctx=Load()), slice=Subscript(value=Name(id='x', ctx=Load()), slice=Constant(value=2), ctx=Load()), ctx=Load())`
  - `provenance.enclosing_call`: `"sorted"`

## Phase 1 — the accumulation metric (already frozen by the build-decision memo, reused
verbatim, not reinvented)

`audits/2026-09-27_verified_skill_ledger_build_decision.md` §8 already specifies:

> Primary metric: mean candidates-needed-to-reach-a-pass for fresh instances of an
> already-solved feature key, before vs. after a skill exists for that key.

Applied here to the accumulation question (§14, Phase F, verbatim): does the existence
and *consumption* of Skill A change the acquisition-efficiency metric for a **second,
independent feature key**? Operationalized as:

- **Primary metric**: within a **fixed candidate budget of N=8** per condition (matching
  this project's established `N_CANDIDATES_PER_FAILURE`-adjacent repeat-count
  convention, doubled here since 4 was too small to reliably observe a pass rate
  difference in a single run), the number of the 8 generated Skill-B candidates that end
  up **passing the real oracle**, comparing A-PRESENT vs. A-ABSENT on the **identical 8
  seeds** in both conditions.
- **Secondary metric**: for A-PRESENT specifically, how many originally-failing
  candidates were successfully repaired by `apply_skill()` (Skill A applied) vs. how many
  were structurally ineligible for Skill A's precondition at all — this directly answers
  "was Skill A actually consumed, and how often did its precondition even apply to a
  structurally different task."
- **Primary claim requirement** (verbatim from the mission): Skill A present causes
  measurably better Skill-B acquisition than an otherwise matched A-absent condition.
  Simply solving B after A exists (e.g., an unaided candidate happening to pass) is not,
  by itself, sufficient — the comparison must show A-PRESENT's pass count exceeding
  A-ABSENT's pass count on the same seeded candidates, with the excess attributable to
  `apply_skill()` actually firing.

## Phase 2 — Skill B, chosen from static task-definition analysis, before any generation

**Skill B target: `K2.T2` (`rank_all`, "Return the list of names ordered from
best-ranked to worst-ranked").** Chosen by inspecting `accumulation_probe/tasks_v2.py`'s
already-existing, static task table (`KT["K2"]`) — a real code-reading step, not outcome
observation, and consistent with the build-decision memo's own Phase F suggestion of a
second K2 feature key (it named `K2.T2` by number, though its own prose description,
"field-projection bug," turns out to describe a *different aspect* of T2's typical
failure mode than the one this protocol targets — see the honesty note below).

Checked against every one of the mission's Phase 2 requirements, using facts established
purely from reading the static task table (`tasks_v2.py` lines 80-85), not from running
anything:

- **Related enough**: `K2.T2`'s canonical solution and `K2.T5`'s canonical solution both
  reduce to the *identical* underlying ranking helper
  (`_RANK = "sorted(entries, key=lambda e: (-e[1], _PRI.get(e[2], 99), e[0]))\n"`),
  confirmed directly in `tasks_v2.py`'s own solution-template source (`k2_rank` and
  `k2_winscore` both prepend the literal `T1._RANK` string). T2 and T5 differ only in
  their **final projection step** (T2: extract every name in ranked order; T5: extract
  just the top `(name, score)` tuple) — the tag-priority-negation risk Skill A fixes
  lives entirely in the *shared* sort-key construction, not in either task's distinct
  projection step. This is a genuine, structural, mechanistically-legible reason Skill A
  *could* directly apply to a T2 candidate exhibiting the same bug shape — not a diffuse
  "maybe it primes general carefulness" story.
- **Distinct enough**: different function name (`rank_all` vs `winner_with_score`),
  different signature usage, different return type and downstream projection — a
  candidate can get T2's list-projection right while getting T5's tuple-projection wrong
  or vice versa; T2 is not a relabeled copy of T5.
- **Mechanistically interpretable**: Skill A's precondition is a pure, literal-free AST
  pattern (`UnaryOp(USub, Subscript)` inside a `sorted(...)` call) — if (and only if) an
  independently-generated T2 candidate happens to construct its own sort key with the
  identical bug shape, `apply_skill()` (completely unmodified, the exact function used
  for T5) will match and repair it, through the **existing VSL consumer mechanism only**
  — no prompt hint, no hand-authored bridge, no answer leakage (Skill A's transformation
  removes a negation; it does not, and structurally cannot, supply T2's own
  list-comprehension/projection logic).
- **Independently verifiable**: real oracle via `H.VT.make_hidden_tests` /
  `H.OR.grade()`, unmodified, the same verifier used throughout this project.
- **Retainable**: any genuine failing/passing pair produced for T2 (whether the passing
  member came from Skill A's repair or from unaided generation) is run through the
  unmodified `diff_extract.extract_transformation()` to produce its own, separate,
  ledger-persisted `{precondition, transformation}` record — Skill B is a real VSL skill,
  not a narrative label.
- **Causally testable**: A-PRESENT vs. A-ABSENT on identical seeds isolates the causal
  variable to "was `apply_skill()` invoked with Skill A," nothing else.

**Honesty note, disclosed rather than smoothed over**: the build-decision memo's own
prose describes T2's commonly-observed failure mode from `strategy_characterization`'s
forensic mining as a *"field-extraction/shape error"* (returning the wrong shape or
field entirely) — a different failure class than T5's tag-priority negation bug. This
protocol does **not** assume Skill A will fix most, or even any, T2 failures — it tests
this directly and reports honestly whichever way it goes (Outcome AC-3 — "B is acquired,
but A does not help" — is a real, anticipated, non-disqualifying possible outcome, not
being ruled out in advance). The mechanistic case above establishes *principled
plausibility*, not a foregone conclusion, per Phase 2's own "do not select B because
preliminary runs show A helps it" — no T2 candidate has been generated or inspected as
of this line.

## Phase 3 — diversity requirement, frozen before generation

The prior prospective-transfer test's own honest caveat (3 of 4 selected instances were
byte-identical, at `temperature=0.2`, single-strategy `STEPWISE` sampling) is addressed
prospectively here, reusing an **already-established, already-tested lever** in this
exact codebase (the `_VARIATION_STRATEGIES` mix that fixed the original K2.T5 acquisition
run's 0/4 problem) rather than introducing an unproven new one (e.g. raising
temperature, which has never been tried anywhere in this project):

- **Strategy mix for both conditions, identical seeds**: `("DIRECT", "STEPWISE",
  "WORKED_EXAMPLE", "STEPWISE", "DIRECT", "STEPWISE", "WORKED_EXAMPLE", "STEPWISE")` for
  candidate indices 0–7 — the same 4-strategy rotation already used for K2.T5's own
  acquisition, extended to 8 slots by repeating the cycle once. Pre-registered now, not
  chosen after seeing any T2 output.
- **Mechanical diversity accounting**: candidates are deduplicated by `sha256_text(code)`
  before being reported as independent evidence. Both the raw pass count (over all 8
  generated candidates) and the **distinct-code-body pass count** (over unique code
  hashes only) are reported. If the distinct-code-body count in either condition is
  below 3, this is disclosed explicitly as a diversity/coverage limitation on that
  condition's result, per Phase 3's instruction — not silently treated as 8 independent
  draws.
- **World identity**: a **new, third world** (`world_index=2`), built via the existing
  `VT.build_world(world_index=2, taken=...)` with its own fresh `taken` set — genuinely
  disjoint from both the acquisition world (0) and holdout world (1) already used for
  Skill A, avoiding any possible objection that T2's literals overlap with anything Skill
  A has ever seen.
- **Seed key**: `seed_for("ACQUIRE_B", "K2.T2", i)` for `i` in `0..7` — grep-confirmed
  unused anywhere in this module before this line.

## Phase 4 — the two conditions

- **A-PRESENT**: fresh OS process. Loads Skill A (`Skill.load_latest("K2.T5.tag_priority_direction")`,
  content-hash-verified against the value recorded in Phase 0 above before proceeding).
  Generates the 8 T2 candidates (strategy mix above, world_index=2, seeds above). For
  each candidate that fails its own oracle grade, calls the **unmodified**
  `diff_extract.apply_skill(code, "rank_all", pattern_A)` — if it returns non-`None`
  (Skill A's precondition matched), re-grades the patched candidate. Records, per
  candidate: `original_passed`, `skill_a_applied` (bool), `patched_passed`.
- **A-ABSENT**: a **separate fresh OS process** (genuine restart boundary, matching this
  project's established convention). Regenerates the identical 8 seeds/strategies/world.
  Records only `original_passed` — the `apply_skill()` step is never reached at all (not
  merely "skipped after being computed"), the same "skill never consulted" convention
  `harness.cmd_substitution()`/`prospective_transfer.cmd_substitution()` already
  established.
- **Fair compute**: identical seeds, identical strategy assignment, identical budget (8)
  in both conditions — the only difference is whether `apply_skill()` is ever invoked.

## Phase 5 — Skill B qualification (only if ≥1 real fail/pass pair exists after Phase 4)

**Original text, as first frozen (superseded by the correction immediately below —
preserved here verbatim, not deleted, per this project's own established discipline):**
"If Phase 4 (either condition) produces at least one failing and one passing T2
candidate (a passing candidate may come from unaided generation OR from Skill A's
repair — both are legitimate 'passing' examples for diff-extraction purposes; the
diff-extraction step itself does not care how the passing example arose, only that it is
a genuine, real, oracle-confirmed pass), run the same, unmodified
`extract_transformation()` used for Skill A to attempt a Skill B
`{precondition, transformation}` record."

**Correction, made in the implementation before any generation ran, but not
synchronized back into this prose until after results existed — disclosed exactly as it
happened, not smoothed over.** Before writing `accumulation.py`'s actual `qualify_b`
implementation, the design above was reconsidered and reversed: **only genuinely unaided
passes (from either condition) are eligible as the "passing" member of a diff-extraction
pair; any candidate that Skill A itself repaired is excluded from the pool.** Reason:
diffing a Skill-A-repaired candidate against its own pre-repair failing form would, by
construction, just re-derive Skill A's own transformation (they differ by exactly Skill
A's edit) — that would not be a genuinely independent Skill B, and would directly violate
Phase 2's "distinct enough" requirement ("B cannot merely be another literal instance of
Skill A"). **Verified, not merely asserted, that this was a genuine before-generation
decision, not a post-hoc rationalization**: `accumulation.py`'s commit (`487c4d5`,
23:17:36) predates the first real T2 candidate generation (`a_present_result.json`,
written 23:21:36) by 4 minutes — the rule was fixed in code before any outcome existed.
Only the *prose* in this document lagged the code; the same "doc lags implementation"
class of gap this project's own history repeatedly catches and corrects rather than
hides. **The actual, controlling rule, used for the real run below: only unaided
fail/pass pairs are used for Skill B extraction.**

**Consequence for interpretation, flagged in advance of the results below**: this rule
means Skill B's own qualification is, by construction, independent of whether Skill A
existed at all — if Skill B is qualified, that specific fact does not by itself
demonstrate Skill A caused *Skill B's discovery*. It can still demonstrate Skill A
causally improved the raw K2.T2 acquisition-efficiency metric (Phase 1's primary
metric) via a *different* repaired candidate — a real but distinct claim from "A helped
discover B." Both are reported separately and not conflated in the results below. If successful,
persist it under a new feature key `K2.T2.<descriptive-suffix-chosen-from-the-real-diff>`
via `Skill(...).save_new_version()`, `status="candidate"`, `held_out_verdict=None` —
identical discipline to how Skill A itself started.

**Explicit note on a possible degenerate case**: if Skill B's own extracted
`{precondition, transformation}` turns out to be structurally identical to Skill A's
(same precondition/transformation AST dump, same `enclosing_call`) — plausible, given T2
and T5 share the same `_rank()`-shaped sort key — this is reported as exactly what it is
(the same underlying bug pattern recurring in a second task, not a "new" skill in the
representational sense) rather than either hidden or inflated into "two skills." This
would still be a genuine, useful, honestly-reported finding about cross-task pattern
recurrence — just not "two distinct learned patterns."

## Phase 6 — restart-boundary check for Skill B (if qualified)

Kill the process, start a genuinely fresh one, reload `Skill.load_latest()` for B's
feature key, confirm identity (content hash) matches what was written. Same evidence
standard as every prior restart check in this project (distinct PID / `id(sys.modules)`).

## Phase 7 — Skill B's own prospective transfer (if qualified, time-permitting)

If Skill B qualifies, run a small prospective test mirroring the already-proven design
from `audits/2026-09-27_vsl_prospective_causal_transfer_protocol.md`: generate fresh T2
candidates on a **fourth** world (`world_index=3`), select eligible cases via
`apply_skill()` for **Skill B only** (mechanical, outcome-blind), run TRUE
(B present) vs SUBSTITUTION (B absent) on the frozen set. Scoped down from Skill A's own
4-target/20-cap to a **2-target/10-cap** given the time budget remaining in this
mission — explicitly disclosed as a smaller test than Skill A's own, not hidden.

## Phase 8 — interpretation (verbatim from the mission's AC-1..AC-5, restated as this
run's frozen commitment)

- **AC-1**: Skill A demonstrably consumed during B acquisition; A-PRESENT's pass count
  (distinct-code-body-qualified) exceeds A-ABSENT's on the same seeds; the excess is
  attributable to `apply_skill()` firing; B qualifies independently; B persists across
  restart; B shows its own fresh-instance advantage (Phase 7).
- **AC-2**: A measurably improves the raw acquisition metric, but B fails qualification,
  restart-persistence, or its own transfer test.
- **AC-3**: B is acquired (in one or both conditions) but A-PRESENT does not outperform
  A-ABSENT — a null result for accumulation, not a failure of B's acquisition.
- **AC-4**: A-PRESENT performs *worse* than A-ABSENT (negative transfer/interference) —
  investigated mechanically, not hidden.
- **AC-5**: B cannot be fairly tested (insufficient diversity, contamination, B
  degenerates into a literal restatement of A with no real distinctness, no valid
  verifier, or the hard cap is reached without the required coverage).

## Phase 9 — explicit anti-doppelgänger controls (Phase 14 of the mission), stated in
advance

- **Extra context**: A-PRESENT receives *zero* additional prompt text relative to
  A-ABSENT — the prompt used to generate each T2 candidate is byte-identical between
  conditions (confirmed by construction: both conditions call the same `H._generate_one`
  with the same task/world/seed/strategy arguments; only the *post-generation* repair
  step differs).
- **Extra compute**: identical candidate budget (8) in both conditions; `apply_skill()`
  itself is a cheap, local AST operation, not an additional model call, so A-PRESENT
  makes no more real model calls than A-ABSENT.
- **Answer leakage**: Skill A's transformation is a single-node AST substitution (removes
  one negation); it cannot supply T2's list-comprehension/projection logic, which every
  candidate must still generate on its own.
- **Task duplication**: addressed in Phase 2 above (T2 ≠ T5, different signature/return
  shape/projection).
- **Retrieval masquerading as acquisition**: Skill B, if qualified, is diff-extracted
  fresh from T2's own real failing/passing pair — it is never Skill A's own record
  copied over; a degenerate-identical-pattern outcome (Phase 5's note) is reported
  honestly rather than counted as a "new" skill regardless.
- **Human abstraction**: no manually-authored bridge of any kind exists between A and B;
  the only mechanism connecting them is the unmodified `apply_skill()` function applied
  mechanically to real generated code.
- **Selection bias**: B was chosen from static task-table inspection before any T2
  candidate was generated (Phase 2, timestamped by this document's own freeze).
- **Duplicate samples**: addressed by Phase 3's mechanical dedup-by-hash accounting.
- **Base-model luck**: identical seeds across conditions neutralize sampling-luck
  differences between A-PRESENT and A-ABSENT — any difference must come from
  `apply_skill()` itself, not from different random draws.

---

## RESULTS (appended after this line only; nothing above this line changed after
generation began, except the Phase 5 correction note above, which documents a real
discrepancy between the frozen prose and the already-committed code, verified to predate
generation by 4 minutes)

### A-PRESENT (fresh process, PID=38194)

```
candidate 0 (DIRECT):        original_passed=False skill_a_applied=True  patched_passed=False
candidate 1 (STEPWISE):      original_passed=True  skill_a_applied=False patched_passed=True
candidate 2 (WORKED_EXAMPLE):original_passed=False skill_a_applied=True  patched_passed=False
candidate 3 (STEPWISE):      original_passed=False skill_a_applied=True  patched_passed=True
candidate 4 (DIRECT):        original_passed=False skill_a_applied=True  patched_passed=False
candidate 5 (STEPWISE):      original_passed=True  skill_a_applied=False patched_passed=True
candidate 6 (WORKED_EXAMPLE):original_passed=False skill_a_applied=False patched_passed=False
candidate 7 (STEPWISE):      original_passed=True  skill_a_applied=False patched_passed=True
DONE. raw: original_pass=3/8 patched_pass=4/8 skill_a_applied=4/8
distinct_code_bodies=5/8  distinct_code_bodies_passing=3
```

### A-ABSENT (SEPARATE fresh process, PID=38305 — confirmed distinct from A-PRESENT's)

```
candidate 0-7: original_passed identical to A-PRESENT's own original_passed column,
bit-for-bit (False,True,False,False,False,True,False,True) — confirmed, not assumed.
DONE. original_pass=3/8
distinct_code_bodies=5/8  distinct_code_bodies_passing=2
```

**Determinism confirmed across two independent fresh processes** — the raw generation is
identical regardless of Skill A's presence, exactly as it must be for the causal
comparison to isolate `apply_skill()` as the only variable. (The distinct-passing-body
counts of 3 vs. 2 are *not* a determinism discrepancy — A-PRESENT's count includes
candidate 3 in its "passing" set because `patched_passed=True` there, while A-ABSENT's
count only ever considers `original_passed`; both are computed correctly per their own
condition's definition, verified by direct inspection.)

**Mechanistic decomposition, read directly off the real candidate code (not inferred)**:
two completely independent, orthogonal bugs exist in this real candidate pool for K2.T2:

1. **The tag-priority negation-direction bug (Skill A's exact domain)**: present in
   candidates 0, 2, 3, 4 (all contain `-tag_priority[x[2]]` inside a `sorted(...)` key).
2. **A shape/projection bug, unrelated to Skill A**: candidates 0, 2, 4, and 6 return
   `sorted(entries, key=...)` directly — the full `(name, score, tag)` tuples — instead
   of projecting out just the `name` field, which is what `rank_all` actually requires.

Candidates 0, 2, 4 carry **both** bugs; Skill A correctly fires on the negation (its
precondition genuinely matches) but cannot fix the shape bug, so they remain failing
after patching — an honest, mechanically explained non-improvement, not a flaw in the
skill. Candidate 3 carries **only** the negation bug (its projection is already correct,
via `[entry[0] for entry in sorted_entries]`) — Skill A's repair is therefore sufficient
on its own, and it flips cleanly from fail to pass. Candidate 6 carries **only** the
shape bug (no negation present at all) — Skill A correctly declines to touch it (no false
match), and it remains failing for a reason outside Skill A's domain.

**Primary metric result**: A-PRESENT (4/8) > A-ABSENT (3/8) under an identical, fixed,
8-candidate budget and identical seeds — Skill A causally improved the raw
acquisition-efficiency metric for K2.T2, and the improvement is precisely and
mechanistically attributable to `apply_skill()` correctly repairing one specific,
independently-verified failure mode (candidate 3) that the separate fresh-process
A-ABSENT control confirms would otherwise remain failing. This is real, but modest (a
+1/8 effect) and does not extend to every failure mode present (candidates 0, 2, 4 are
untouched by Skill A's repair, for an honestly-explained, mechanistic reason).

### Skill B qualification (Phase 5)

Pool: 10 unaided failing entries, 6 unaided passing entries (both conditions' unaided
candidates combined; duplicated across conditions since determinism holds, harmless).
First alignable pair found: **candidate 6 (failing, the shape-bug-only candidate) vs.
candidate 1 (unaided passing)**. Extracted pattern: **`identical_to_skill_a=False`** — a
genuinely distinct pattern, not a restatement of Skill A. Precondition: the entire
`sorted(entries, key=lambda x: (-x[1], tag_priority[x[2]], x[0]))` call; transformation:
the same call wrapped in `[entry[0] for entry in ...]` — i.e., "project out just the
name field." Written as `K2.T2.discovered_via_accumulation_test` v1, `status=candidate`,
`held_out_verdict=None`, `content_hash=1f5ce81e6d31a68cf0427f8d566977c45f648af17b280d8698c83965ef6bfbd0`.

**Honest note on Skill B's own generality, flagged per Phase 10's explicit warning**:
unlike Skill A's tiny, surgical 1-node diff (a single `UnaryOp` wrapping one
`Subscript`), Skill B's precondition is the *entire* sort-key call — a much larger
subtree, bound to the exact local variable names this candidate happened to use
(`entries`, `x`, `tag_priority`, and the comprehension variable `entry`). This is closer
to Phase 10's "task-identity fingerprint" territory than Skill A's pattern was — it will
only match code using this exact naming convention, a real, disclosed limitation on how
broadly Skill B can be expected to generalize beyond what Phase 7 below actually tests.

**Central, load-bearing caveat, per the Phase 5 correction above**: Skill B's extraction
used *only* unaided candidates (6 and 1), neither of which Skill A ever touched. **Skill
A's presence did not cause Skill B's specific discovery** — the identical extraction
would have happened in a counterfactual world where Skill A never existed, since both
conditions' unaided pools are identical by determinism. What Skill A *did* cause is
reported separately above (the raw acquisition-efficiency improvement, via a completely
different candidate). These are two real, distinct, non-conflated findings.

### Restart-boundary check (Phase 6)

Fresh process (PID=38664, confirmed distinct from `qualify_b`'s own process). Skill B
reloaded via `Skill.load_latest()`: version and content hash match exactly what was
written. Genuine disk-based persistence confirmed, same evidence standard as every prior
restart check in this project.

### Skill B's own prospective transfer test (Phase 7, scoped 2-target/10-cap)

**Selection** (outcome-blind): 3 candidates generated (world_index=3, strategy mix) before
2 eligible found — well under the 10-cap. Candidate 1 (STEPWISE) was ineligible
(precondition did not match); candidates 0 (DIRECT) and 2 (WORKED_EXAMPLE) were eligible.
Zero contamination.

**TRUE** (fresh process, PID=38856): `original_passed=False` for both selected instances;
`skill_applied=True` for both; `patched_passed=True` for both. **0/2 → 2/2.**

**SUBSTITUTION** (separate fresh process, PID=38889, Skill B never consulted):
`original_passed=False` for both — identical to TRUE's own pre-patch baseline, confirming
determinism held again. **0/2, with-skill was 2/2 — advantage attributable to Skill B's
presence: YES.**

This is a full, clean, independently-run **Outcome A** (in the exact sense of the
`prospective_transfer.py` protocol) **on Skill B itself** — a second, genuine
demonstration that this architecture's causal-transfer mechanism is not a one-off
property of Skill A specifically, but reproduces on a second, independently-discovered
skill. Sample size is even smaller here than Skill A's own prospective test (n=2, not
n=4) — explicitly a smaller, scoped-down test per the frozen protocol's own Phase 7, not
hidden as if it were equally powered.

### Classification: qualified AC-1

Checked against every AC-1 requirement directly:

1. **Skill A actually consumed during B acquisition**: YES — `skill_a_applied=True` on
   4/8 candidates, one of which (candidate 3) was genuinely repaired.
2. **B acquired more efficiently/reliably with A than without under matched budget**:
   YES, for the feature key's aggregate acquisition-efficiency metric (4/8 vs 3/8,
   identical seeds, separate fresh processes) — this is the mission's own stated primary
   metric (§8 of the build-decision memo) and it moved in the correct direction,
   causally.
3. **The advantage depends on A**: YES — A-ABSENT's separate fresh process confirms
   candidate 3 would remain failing without Skill A.
4. **B qualifies independently**: YES — a genuine, distinct (`identical_to_skill_a=False`)
   `{precondition, transformation}` record, extracted via the unmodified
   `extract_transformation()`.
5. **B persists**: YES — confirmed across a genuine restart boundary.
6. **B produces fresh-instance behavioral advantage**: YES — Skill B's own prospective
   transfer test, 0/2 → 2/2, causally confirmed via separate fresh processes.

**All six literal requirements are met. This is classified as AC-1: causal accumulation
demonstrated** — with one honest, load-bearing qualification stated as precisely as
possible, not buried: **the specific mechanism connecting A and B is narrower than "A
helped discover B."** What was actually shown is (a) Skill A causally improves the raw
acquisition-efficiency metric for a second, structurally related feature key, by
repairing a real failure mode within that key's own candidate pool, and (b) a second,
independently-discovered, genuinely distinct skill (Skill B) reproduces the exact same
causal-transfer property Skill A already demonstrated — evidence that this architecture's
core mechanism (acquire → diff-extract → persist → causally reapply) generalizes across
at least two real bug families, not just one. It is **not** evidence that Skill A made
Skill B's *own specific pattern* easier or more probable to discover — that stronger,
narrower claim (Phase 11's "does A change the probability of acquiring B") was tested
directly (Skill B's extraction pool explicitly excludes anything Skill A touched, by
design) and the honest answer is: **not demonstrated in this run; B was equally
discoverable without A.**

### Anti-doppelgänger check (Phase 14), verified directly, not just asserted

- **Extra context**: confirmed by construction — `H._generate_one()` was called with
  byte-identical arguments (task, world, seed, strategy) in both conditions; the only
  difference was whether `apply_skill()` ran afterward.
- **Extra compute**: identical budget (8) in both conditions; `apply_skill()` is a local
  AST operation, not a model call.
- **Answer leakage**: Skill A's transformation is a single-node negation removal; it
  cannot and did not supply T2's own list-comprehension logic (candidates 0, 2, 4 prove
  this directly — Skill A applied but did not produce a pass, since the shape logic was
  still missing).
- **Task duplication**: T2 and T5 have different signatures, return types, and
  projection logic (established in Phase 2, before generation).
- **Retrieval masquerading as acquisition**: Skill B was diff-extracted fresh from T2's
  own real unaided pair, never copied from Skill A.
- **Human abstraction**: no hand-authored bridge exists anywhere in `accumulation.py`;
  the connecting mechanism is `apply_skill()`, unmodified.
- **Selection bias**: B was chosen from static task-table inspection, timestamped before
  any T2 candidate existed.
- **Duplicate samples**: reported explicitly (5/8 distinct code bodies in each
  condition); the causal comparison (4/8 vs 3/8) is not inflated by treating duplicates
  as independent evidence — candidate 3 (the sole flipped case) has a unique code hash
  not shared with any other candidate.
- **Base-model luck**: neutralized by identical seeds across conditions — the observed
  difference cannot be sampling luck, since both conditions sampled identically; the only
  possible source of difference is `apply_skill()` itself, which is exactly what was
  measured.

### What Checkpoint 7 does and does not establish, stated as precisely as the mission
requires

**Established**: (1) Skill A causally improves K2.T2's raw acquisition-efficiency metric
under a fixed, matched budget — real accumulation of the "does having this skill make
the same task family's overall pass rate better" kind. (2) A second, independently
discovered, genuinely distinct skill demonstrates the identical restart-persistent
causal-transfer property Skill A already showed — the mechanism is not a one-off. (3)
Both findings are supported by mechanistically transparent, fully-explained evidence
(not a mysterious aggregate statistic) — every candidate's pass/fail status is explained
by which of two independent, named bugs it carries.

**Not established**: that Skill A made Skill B's *specific* pattern easier, more
probable, or faster to discover. That is the narrower, harder claim Phase 11 names, and
this run's own qualification design (deliberately excluding Skill-A-touched candidates
from B's extraction pool, to avoid the "B is just A relabeled" failure mode) makes it
structurally impossible for this specific run to have shown that — a real, disclosed
scope limit on the classification above, not an oversight discovered after the fact.

### Phase 12 (optional composition test): not attempted

Given the scope already covered and the honest qualification above, the optional
composition test (does A+B enable a harder fresh task) was not attempted in this pass —
explicitly optional per the mission's own Phase 12, and not required to reach a
classification.
