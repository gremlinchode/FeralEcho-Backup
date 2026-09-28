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
