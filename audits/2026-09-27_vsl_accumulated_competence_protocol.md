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

If Phase 4 (either condition) produces at least one failing and one passing T2 candidate
(a passing candidate may come from unaided generation OR from Skill A's repair — both are
legitimate "passing" examples for diff-extraction purposes; the diff-extraction step
itself does not care how the passing example arose, only that it is a genuine, real,
oracle-confirmed pass), run the same, unmodified `extract_transformation()` used for
Skill A to attempt a Skill B `{precondition, transformation}` record. If successful,
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

## RESULTS (appended after this line only; nothing above changed after generation began)
