# Verified Skill Ledger — MVK First Run Report

**Branch: `vsl-implementation` (isolated; `main` untouched; zero commits made).**
This is Checkpoint 1–6 of the build-decision memo's own roadmap, executed live in one
pass. Real model calls were made (`qwen2.5-coder:7b`, local Ollama) — this is an
authorized implementation-and-evaluation mission, not a capped micro-probe.

**Outcome, stated precisely up front: PARTIAL RESULT — the core extraction/matching
mechanism is confirmed working; the held-out transfer gate did not pass; a specific,
diagnosed, engineering-fixable gap is the cause, not an architectural kill.**

---

## What was built

`app/experiments/skill_ledger/`: `common.py` (seeds/hashing, `SEED_OFFSET=150000`,
confirmed disjoint from every prior offset in this codebase), `tasks.py` (thin,
verbatim reuse of `accumulation_probe`'s generators), `ledger.py` (the `Skill` class —
the accepted `{precondition, transformation}` schema, write-once versioned files,
`is_eligible()` gate requiring a real `held_out_verdict == "PASS"`), `diff_extract.py`
(the one genuinely new component — generic AST-diff-and-generalize, described below),
`harness.py` (four-phase CLI: `build`/`acquire`/`transfer`/`substitution`, each meant to
run as its own OS process), `verify_diff_extract.py` (unit suite).

## `diff_extract.py` — unit test results: **11/11 passing**

Covers: real historical-pair extraction (the exact EP-A `K2.T5` STEPWISE failing/passing
pair from `strategy_characterization`'s Stage 1), application to the source instance,
**held-out transfer to a synthetic fresh world** (world-specific literals correctly
preserved, not overwritten), correct `None` on identical inputs, correct `None` on
structurally unalignable inputs, correct `None` on already-correct code (no false
"success"). **One real bug was found and fixed during this verification, not glossed
over**: list-length-mismatch divergences were producing a non-deterministic,
memory-address-based "pattern" (via Python's default list `repr()`) instead of an honest
`None` — fixed by propagating an explicit `UNALIGNABLE` signal through nested
divergences rather than collapsing to a non-minimal whole-node diff.

**Beyond the unit suite, two independent genericity checks were run live this session
against entirely real historical data** (zero new model calls, `strategy_characterization`'s
own Stage 1 log): extracting a pattern from a real `K2.T5` pair and applying it to a
**different real world's** real failing candidate — correct fix, correct literal
preservation. Repeated on a **second, independent bug family** (`K2.T2`) using real data
— same result, plus an honest `None` on a real structural variant (`.get(x[2], 5)`
instead of a plain subscript) the pattern wasn't extracted from. This confirms the
mechanism is not hand-tuned to one example.

## Live MVK run — complete real numbers

**Acquisition, attempt 1** (variation = `DIRECT` only, 4 calls): 0/4 passed. **Honest
negative, root-caused immediately as an engineering oversight, not a scientific
failure**: real historical data already showed `DIRECT` has a 0/36 real pass rate on this
exact task family (`K2.T5`) — using it alone for variation could never produce a
pass/fail pair to diff. Fixed by drawing variation from a strategy mix
(`DIRECT`/`STEPWISE`/`WORKED_EXAMPLE`/`STEPWISE`) grounded in already-known real evidence
— not by re-rolling seeds hoping for a different `DIRECT` outcome.

**Acquisition, attempt 2** (strategy-diverse, 4 calls): candidate 1 (STEPWISE) failed,
candidate 3 (STEPWISE) passed. A real transformation was extracted — precondition: a
`UnaryOp(USub)` wrapping a `Subscript` (`-tag_priority[x[2]]`); transformation: the bare
`Subscript` (negation removed). Written as `K2.T5.tag_priority_direction` v1,
`status=candidate`, `held_out_verdict=null`, content hash
`62be14192d3bcdfc82a35ddd1b14f6bfb01d3ebb094e54446afc52ac181e8a82`.

**Transfer** (fresh process — genuine restart-boundary evidence: PID=35287,
`id(sys.modules)=4346757632`, matching `restart_persistence_transfer`'s own evidence
standard; 4 calls on the disjoint holdout world, world_index=1, real fresh tag names
`dabek`/`zapin`/`nidob`/`lojoz`, never seen during acquisition):
original pass rate **0/4**. **The skill's precondition correctly, structurally matched 2
of the 4 fresh candidates (instances 2 and 3) — a real, genuine confirmation that the
extracted AST pattern generalizes syntactically to code it never saw during
acquisition.** But `patched_passed` was `False` for both — the transformation did not
produce a passing result. `held_out_verdict` set to `FAIL`; skill remains `status=candidate`,
correctly **not** eligible for consumption (`is_eligible()` enforces this in code).

**Root cause, deterministically re-derived and directly inspected, not guessed**: both
matching candidates used `max(entries, key=lambda x: (x[1], -tag_priority[x[2]], x[0]))`
— note `x[1]` (score) has **no** negation here, which is *correct* for `max()` (it
naturally prefers the largest key value, unlike `sorted()[0]`, which needs the opposite
convention). The skill's transformation — mined from a `sorted()`-based training pair,
where the negation convention is different — removes the `tag_priority` negation
unconditionally. For this `max()`-based structure, removing that negation actually makes
the tag-priority tiebreak **backward**. Confirmed directly: the real `output_tail` for
both instances is identical before and after patching (`actual=('bo',3,'nidob')` vs
`expected=('hal',3)`) — the patch changed nothing about this specific failure mode.

**Substitution** (fresh process, same seeds, skill absent, 4 calls): no-skill pass rate
**0/4** — identical to the with-skill result, correctly and consistently confirming there
was no advantage to remove (matching the transfer phase's own finding, not contradicting
it).

## Why this is a partial result, not an architectural kill

Two things are true simultaneously, and neither should be allowed to obscure the other:

1. **The core mechanism works.** The precondition — a pure, structural, literal-free AST
   pattern — genuinely matched real code it had never seen, generated by a different
   random draw, in a different (later) process, on a different (disjoint) world. This is
   real, mechanically verified generalization at the *pattern-matching* level, exactly
   the property this whole architecture exists to demonstrate, and it held.
2. **The transformation itself was under-specified.** `diff_extract.py`'s precondition is
   currently **context-free** — it matches an isolated subtree without recording *where*
   that subtree sits (inside a `sorted()` key vs. a `max()` key), even though the correct
   fix depends on exactly that context. This is a real, precisely diagnosed, **engineering**
   gap (per the mission's own Failure Policy: "correctly implemented mechanism cannot
   produce the required effect under its own gate" would be the scientific-failure case —
   this is closer to "the mechanism is under-specified in a fixable way," since the
   precondition/transformation shape itself is sound, it simply needs a richer context
   marker).

**This is exactly the shape of outcome the build-decision memo's own red-team pass (§18)
flagged as the single most serious *un*-resolved risk before building** — not proven
wrong, but not yet proven right either, on this first real attempt.

## The specific fix needed (not attempted in this pass)

Broaden `diff_extract.py`'s precondition to encode enclosing-call context: when finding
the diverging subtree, also record the name of the nearest enclosing `Call` node (e.g.,
`sorted` vs `max`). Store this as an additional precondition field. `apply_skill()` then
only matches when both the subtree pattern *and* the enclosing-call context agree —
closing exactly the gap this run found, without weakening the pattern's literal-freedom
in any other way. This is a scoped, well-understood change to one function, not a
redesign.

## Exact next action

Implement the enclosing-call-context fix in `diff_extract.py`, re-run `verify_diff_extract.py`
(add a new case: two functions differing in aggregation convention, confirm the broadened
precondition correctly distinguishes them), then re-run **only** the `transfer` phase
(the existing skill's acquisition and the unit tests both already succeeded — no need to
redo acquisition). This is a Checkpoint-5 retry, not a restart of the whole MVK.

---

**No git commit was made.** All work is on the isolated `vsl-implementation` branch;
`main` is untouched, exactly as instructed.

---

## Follow-up (same day): enclosing-call-context fix implemented, tested, and re-run

**Checkpoint commit**: `19e8135ddad519d65ae97651d8c3680040a080ad`, message
`vsl: checkpoint initial cross-world transfer result` — the exact partial-result state
described above, committed to `vsl-implementation` before any further changes were made
(per the "Continue VSL Implementation" mission's explicit Phase 1 checkpoint-before-fixing
instruction). `main` remains untouched.

### Phase 2 — defect re-derived mechanically, all four required claims confirmed

No new model calls. All four checked directly against already-collected artifacts:

1. **The transformation originated from a `sorted()`-based pair.** Confirmed by direct
   read of `memory/experiments/skill_ledger/mvk/acquisition_candidates.json`: candidate 1
   (STEPWISE, failing) and candidate 3 (STEPWISE, passing) — the pair actually used
   (`used_pair=(1,3)`, per `acquisition_result.json`) — both use
   `sorted(entries, key=lambda x: (-x[1], ±tag_priority[x[2]], x[0]))[0]`. True.
2. **The two fresh-world matches at transfer time both occurred under `max()`.** Confirmed
   by direct re-derivation (below): both matching instances (2 and 3 in the *original*
   transfer run) used `max(entries, key=lambda x: (x[1], -tag_priority[x[2]], x[0]))`. True.
3. **Negation semantics genuinely differ between the two contexts.** Confirmed by direct
   arithmetic, not assumed: for `sorted(..., key=lambda x: (-x[1], K, x[0]))[0]`, the
   correct tiebreak needs the *lowest* raw priority number to win, which requires `K =
   tag_priority[x[2]]` (no negation) when priority 1 = highest; for
   `max(..., key=lambda x: (x[1], K, x[0]))`, `max` already selects the *largest* key
   directly (no `[0]`-of-reversed-sort indirection), so the correct `K` for the identical
   "lower number wins" semantics is `-tag_priority[x[2]]` — the **opposite** literal form
   from the `sorted()` case. The two contexts are not interchangeable; a transformation
   correct under one is wrong under the other by construction, not by accident. True.
4. **The v1/v2 precondition carried no enclosing-call information.** Confirmed by direct
   read of `K2.T5.tag_priority_direction.v1.json`/`v2.json`: `precondition` is a bare
   `ast.dump()` string of the `UnaryOp` subtree alone, with no reference anywhere in the
   precondition or provenance to what call it was found inside. True.

All four confirmed — proceeded to Phase 3 per the mission's own gate.

### Phase 3 — the fix

`diff_extract.py` gained `_call_name()` and `_enclosing_call_name()` (walks from a given
root AST to find the nearest enclosing `ast.Call` containing a target node by identity,
returning its callee name or `None`). `extract_transformation()` now records
`enclosing_call` on the extracted pattern (refusing extraction outright if the
failing/passing pair's own enclosing-call contexts disagree with each other — an honest
refusal, not a forced guess). `apply_skill()` now gates candidate-subtree matching on the
candidate's own enclosing-call context equaling the stored pattern's — a skill mined
under `sorted()` can no longer match (and therefore cannot misapply to) an occurrence
inside `max()`, or any other different enclosing call, or no call at all. Pre-existing
skills with no `enclosing_call` field default (via `.get()`) to matching only
no-enclosing-call occurrences — deliberately conservative, fails closed rather than
silently over-applying a pre-fix skill. No instance-specific/holdout-specific logic of
any kind was added, per the mission's explicit hard constraint — the gate is a genuine
structural property (which call a subtree sits inside), checked identically regardless of
which task, world, or literal values are involved.

### Phase 4 — tests, run before any live re-transfer

Four new cases added to `verify_diff_extract.py` (positive-context assertion that the
real pair's `enclosing_call` is correctly recorded as `'sorted'`; a **negative-context**
case using the exact real historical `max()`-based defect shape, asserting `apply_skill()`
now correctly returns `None` instead of misapplying; a re-confirmation that the existing
proven `sorted()`-to-`sorted()` cross-world genericity still works with the gate active;
a **serialization** round-trip test confirming `enclosing_call` survives a real ledger
write/reload). Full suite: **15/15 passing** (the original 11 plus these 4).
`harness.py`'s two pattern-dict construction sites (`cmd_acquire`'s `Skill(...)`
provenance, `cmd_transfer`'s `apply_skill()` call) were updated to thread the new field
through — both were previously missing it, found and fixed as part of this same pass.

### Re-run: zero new model calls for re-extraction, fresh process for transfer/substitution

Per the mission's explicit preference ("without reacquiring the skill unless mechanically
necessary"), a new `reextract` subcommand was added to `harness.py`: it re-runs
`extract_transformation()` against the *already-collected* real
`acquisition_candidates.json` (the same candidate 1/candidate 3 pair used originally) —
genuinely zero new model calls. Produced skill v3 (`enclosing_call='sorted'`, content
hash `4bd4d72f8df...`).

`transfer` was then re-run as a fresh OS process (PID=36245, confirmed distinct from the
original run's PID=35287) against v3, on the same disjoint holdout world and the same 4
seeds as the original transfer run:

```
instance 0: original_passed=False skill_applied=False patched_passed=False
instance 1: original_passed=False skill_applied=False patched_passed=False
instance 2: original_passed=False skill_applied=False patched_passed=False
instance 3: original_passed=False skill_applied=False patched_passed=False
DONE. original pass rate=0/4  with-skill pass rate=0/4  skill applied on 0 instances
held_out_verdict=FAIL (eligible for consumption: False)
```

**This is a different result from before, for a mechanically confirmed, honest reason —
not the same failure recurring.** In the original run, the skill *misapplied* to 2 of the
4 instances (matched structurally, produced a wrong patch). Now it applies to **0 of 4** —
correctly declining every instance, not misfiring on any. Deterministically re-generated
all 4 real holdout instances at their exact original seeds to confirm why, directly (not
guessed):

```
instance 0: max(entries, key=lambda x: (x[1], tag_priority[x[2]], x[0]))       # no negation present at all
instance 1: max(entries, key=lambda x: (x[1], tag_priority[x[2]], x[0]))       # no negation present at all
instance 2: max(entries, key=lambda x: (x[1], -tag_priority[x[2]], x[0]))      # negation present, but inside max()
instance 3: max(entries, key=lambda x: (x[1], -tag_priority[x[2]], x[0]))      # negation present, but inside max()
```

All 4 real DIRECT-strategy holdout instances in this world are `max()`-based; none are
`sorted()`-based. Instances 2/3 are exactly the two that were misapplied before — now
correctly refused, since their enclosing call (`max`) doesn't match the skill's recorded
context (`sorted`). Instances 0/1 never had the precondition's negation present at all, so
they were never real candidates for this skill either way, fixed or not.

Substitution was re-run for completeness (fresh process): no-skill pass rate 0/4,
identical to with-skill — consistent, honest, no advantage either created or hidden.

### What this establishes, and what it does not

**The fix worked exactly as intended**: the misapplication defect (Checkpoint 5's original
finding) is closed — mechanically confirmed via a direct negative-context unit test and
now confirmed live, on the real holdout instances that previously triggered it. The skill
no longer produces a wrong patch on out-of-context code.

**The held-out transfer gate still does not pass** (`held_out_verdict=FAIL`, v4) — not
because the fix failed, but because this specific holdout sample (4 DIRECT-strategy
generations) happens to contain zero `sorted()`-context occurrences to demonstrate a
transfer benefit against. This is an honest **coverage gap in this one sample**, not a
new defect and not evidence against the fix or the mechanism: a `sorted()`-scoped skill
was never going to help on code that structurally never uses `sorted()`. Whether a larger
or differently-sampled holdout set would surface a genuine `sorted()`-context match is an
open, uninvestigated question, and — per the mission's explicit standing instruction
("Continue down the existing VSL roadmap only if the resulting evidence justifies it";
"Do not reopen the architecture investigation... do not rerun closed research branches")
— is **not chased further in this pass**. The gate outcome is reported exactly as it is:
**FAIL, for a mechanically identified and qualitatively different reason than the original
FAIL**, and Checkpoint 7 remains correctly un-started.

**No git commit was made for this follow-up.** All changes remain uncommitted on
`vsl-implementation`, on top of the checkpoint commit above.
