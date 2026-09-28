# QUAL-2 — Constructor Architecture Search (K2/K3 only), Pre-registration

**Written and hashed before any QUAL-2 constructor call is made.** Per
AP-0 Stage 1 v2's own Section 11 item 1, and per
`audits/2026-09-27_autonomous_acquisition_counterfactual_experience_protocol.md`
Section 16/17's recommendation, authorized by Gremlin's explicit
"continue based on your suggestion."

## 0. Scope

QUAL-1's own corrected (hand-adjudication-verified) result: K1 is
genuinely solvable by the existing one-shot constructor (exact rate 1.0);
K2 (ordering rule) and K3 (event→operation table) are not (exact rate 0.0
each, with the current worker-as-constructor and, separately, with the
`deepseek-r1:7b` contingency — though the latter's K3 result was
compromised by truncation, not a clean negative). **QUAL-2 tests K2 and K3
only. K1 is not re-tested — it is already qualified in substance; its
remaining gap (gate sensitivity) is a different, worker-consumption
problem, out of scope for a constructor-architecture search.**

## 1. What is being tested

One alternative constructor architecture, named in advance so no
architecture is chosen after seeing how well it does:

**STAGED** — a 3-step reasoning chain, replacing the existing one-shot
`constructor_user()` call, each step a separate, stateless model call
whose output text is carried forward as literal context into the next
step's prompt (no shared conversation state; matches this codebase's own
existing stateless-call convention):

1. **Hypothesize**: given the raw episodes and the public task-type
   context, state a best-guess rule, explicitly flagging uncertainty
   where present.
2. **Verify**: given that same hypothesis, check it against every one of
   the same episodes individually and revise it if any episode
   contradicts it.
3. **Finalize**: the *original, unmodified* `constructor_user()` prompt
   (same instructions: "state the convention completely and precisely...
   write 'not established' rather than guess"), with the verified
   hypothesis from step 2 prepended as additional context ahead of the
   raw episodes.

**Why this candidate, not another**: K2 and K3 both require relating
multiple episodes to each other (a total order across pairwise
comparisons; a per-event operation inferred from paired before/after
states) rather than aggregating independent facts (K1). A one-shot prompt
gives the model no explicit opportunity to check a candidate rule against
each individual episode before committing to prose. STAGED adds exactly
that explicit self-check step, using only the real episodes already
supplied — no oracle, no held-out data, no investigator-authored content
about what the rule actually is.

**Not tested in this pass, and why**: a self-consistency filter (iterate
drafts until the worker reproduces the *training* episodes' own outputs)
and a different constructor model are both real candidates named in AP-0's
own Section 11, deliberately deferred to a possible QUAL-2b rather than
bundled in here — testing one architecture cleanly, and reporting its
result plainly, is preferred over testing several at once and diluting
what any single negative or positive result would mean.

## 2. Worlds

2 realizations each of K2 and K3 (matching QUAL-1's `NW=2`), generated
with `worlds.make_realization(kind, MASTER_SEED + 40000 + 10*i + w, taken)`
— **a new, previously-unused seed offset** (existing offsets in this
codebase: 0-2 Stage0 W, 100-102 Stage0 F, 5000-5002 dev W, 5100-5102 dev F,
7000-7021 QUAL-1; 40000+ is disjoint from all of these, confirmed by
direct grep of every `MASTER_SEED +` occurrence in this package before
writing this document). Screened tokens (mutually disjoint from all
previously-used realizations, via the shared `taken` set) as in every
other AP-0 world.

## 3. Episodes and VAL gate tasks

Identical machinery to QUAL-1: `tasks.teaching_episodes()` /
`tasks.episode_lines()` for the episode text shown to the constructor;
`tasks_v2.build_tasks_v2()` + `tasks_v2.make_cases2(..., "VAL")` for the
independent behavioral-gate tasks, using the same pooled validation
templates QUAL-1 already selected (`memory/experiments/accumulation_probe/v2/dev/val_templates_pooled.json`)
— not re-selected, to avoid any appearance of choosing templates favorable
to the new architecture. R0 (raw canonical episode) representation only —
QUAL-1 found R0 was at least as good as R1 for the conventions that
matter, and testing only one representation halves the call budget for a
smaller, cheaper search.

## 4. Drafts, gate, and scoring

3 drafts per (convention, world) via the STAGED chain (matching QUAL-1's
`D_MAIN=3`) → 6 per convention. Each retained iff the worker (same model,
same options as QUAL-1's gate) solves ≥2 of 4 VAL tasks
(`GATE_MIN_PASS=2`, unchanged). Ground-truth content exactness scored by
the existing, already-corrected `constructor.audit()` function (the
current source, already fixed post-QUAL-1 — verified directly, not
assumed, before this document was written). Same decision thresholds as
QUAL-1: `Q_EXACT_QUALIFIED = 5/6`, `Q_EXACT_NOT = 1/6`, otherwise
PARTIALLY QUALIFIED per convention.

**No GOLD/WRONG/NONE gate-qualification replicate is re-run** — the gate
mechanism itself was already qualified/characterized by QUAL-1 (sensitivity
0.833, a worker-consumption property independent of which constructor
architecture is used); re-running it here would not test anything new
about STAGED.

## 5. What counts as a result

- **STAGED qualifies (or partially qualifies) K2 and/or K3** where the
  one-shot constructor did not: real, reportable evidence that a
  relational/procedural rule *can* be autonomously induced by a
  differently-structured (but still fully autonomous, non-authored)
  extraction process — unblocks (subject to further review) the
  prerequisite gate for AP-0 Stage 1.
- **STAGED fails identically** (0.0 exact rate on both, as before): a
  second, independent negative result for this specific architecture
  variant — reported plainly, not chased with a third variant in the same
  pass. This becomes real evidence toward "no local-model-based
  constructor architecture tried so far can perform this class of
  induction," strengthening (not yet completing) the case that this
  research direction may require the alternative AP-0 already names in
  its own Section 11 item 1 (a stronger model, or accepting a smaller
  claim via a programmatic hypothesis-enumeration constructor).

## 6. Integrity

Ground truth (`worlds.py`'s real category/priority/operation tables) is
never placed in any constructor-facing prompt at any of the 3 steps —
verified by direct inspection of every prompt actually sent, logged in
full alongside each real call. The finalize step's instruction text is
byte-identical to the existing, already-audited `constructor_user()`
function, imported directly (not retyped), so any difference in outcome
is attributable to the two added reasoning steps, not to a reworded final
instruction.

## 7. Budget

2 conventions × 2 worlds × 3 drafts × 3 steps = 36 constructor calls, plus
2 × 2 × 6 drafts-worth-of-gate × 4 VAL tasks (only for non-empty drafts) ≈
up to 48 gate calls. ≈84 real calls total, materially smaller than AP-0
Stage 1's own ≈1,550-2,300 call estimate.

---

Not authorized by this document: AP-0 Stage 1 itself, any second QUAL-2
architecture variant, or anything beyond K2/K3 constructor qualification.
