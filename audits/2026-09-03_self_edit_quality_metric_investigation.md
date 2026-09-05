# Self-Edit: Is It Actually Making the Codebase Better?

Direct follow-up to the "Highest-Risk Remaining Boundary" flagged in
`audits/2026-09-02_information_flow_integrity.md` (Finding #6:
`current_quality` pinned at a constant 4/4 across every real deploy
decision in the observable history). That entry recommended pulling the
real `candidate_quality` distribution and reading `_score_response_quality()`'s
actual coding-branch logic before concluding anything — done here. This
is not a code change. Every claim below is a direct read of real,
current source or real, current log/state data.

---

## The honest answer: no, not detectably — and the metric being compared
## against can't currently show an improvement even if one happened.

**Full real distribution, all 37 real deploy decisions in
`memory/SELF_EDIT.log`, spanning 2026-07-11 through 2026-09-03:**

- `candidate_quality`: `{1: 4, 2: 5, 3: 28}` — every real candidate ever
  generated has scored 1, 2, or 3. **None has ever scored 4.**
- `current_quality`: `{4: 37}` — the production baseline has read a
  constant, maxed 4 on every single check.
- **`candidate_quality >= current_quality`: 0 out of 37.** No real
  self-edit attempt has ever cleared Finding 19's fitness gate in the
  entire observable history. Not "rarely" — literally zero.

## Root cause, precisely identified, not inferred

`_score_response_quality()`'s coding branch (`echo_quality_scorer.py:374-393`)
is **not** a correctness, coherence, or improvement measure. It is a raw
count of AST structural nodes — `_ast_complexity()` counts instances of
`If`/`For`/`While`/comprehensions/`Try`/`With`/ternaries/bool-ops and
maps the count directly to a score: 0 nodes → 2, 1-2 nodes → 3, 3+ nodes
→ 4. **A simpler, cleaner, more correct candidate that uses fewer
control-flow constructs scores lower than a more convoluted one that
uses more, regardless of which is actually better code.** This is the
same "prose_stripping"/"response_shortening" family this document's own
CLAUDE.md already flagged as producing near-duplicate reimplementations
(Finding 22) — but a mechanical reason for the *pattern*, not previously
connected: the scorer structurally rewards adding more branching, not
converging on a correct minimal implementation, which is the opposite of
what "shorten a response" or "strip prose" should be optimizing for.

**The reference baseline itself is broken code that scores a false
"perfect" 4.** Read the actual, currently-deployed
`app/core/self_edit_generated.py` directly: it defines `run_code_generator`
**twice** (once as a bare module-level function, once as a method with
the identical name), references `self.average_response_length` inside a
plain module-level function (`get_shortened_code`) where `self` is not
defined at all — a real `NameError` if that code path is ever actually
executed — and embeds a large second copy of near-identical logic as a
dead string literal that is never executed, just carried as text.
`_ast_complexity()` counts 7 structural nodes across this file → scores
4 → "perfect," despite being, by ordinary reading, broken. **Every real
candidate for two months has been asked to match or beat a reference
that is itself incoherent, and the metric they're compared against
can't tell the difference between "incoherent but structurally busy"
and "correct and complete."**

## A second, compounding gap: the mechanism meant to detect this kind of
## stuck loop doesn't see it either

`self_edit_convergence.json`'s `non_convergent_streak` (the counter
`_build_targeted_prompt()` reads to decide whether to discourage another
standalone reimplementation) reads **0** for every tracked family right
now — including `response_shortening`, the currently-active family,
which has been attempted **58 times** and produced **33 distinct
function/class names**, with zero of those 58 attempts ever clearing
the fitness gate. Read `self_edit_manager.py`'s actual streak
computation directly: `convergent = count <= prev_count or prev_count == 0`
— it measures whether the *number of matching-family names this cycle*
grew relative to *last cycle*, not whether the family has ever
succeeded. A family can cycle through one brand-new name per attempt
forever, count staying flat at 1 each time, and this reads as
"converging" (streak resets to 0) the entire time. **The one counter
built specifically to catch "this family is stuck reinventing itself"
does not fire for the family that is doing exactly that, right now,
in real production data.**

## What this does and doesn't mean

This is not evidence that Finding 19's fitness gate (reject unless the
candidate scores at least as well as production) is broken — it's doing
exactly what it was built to do, and it's the reason nothing bad has
been deployed. The problem is one level up: **the yardstick both sides
of that comparison are measured against doesn't track what "better"
actually means for code**, so the gate has no real signal to work with
— it's correctly rejecting everything, but for the wrong reason (fewer
branches, not worse code), against a baseline that shouldn't be trusted
as "good" in the first place.

## Recommended next step (not implemented — a design decision, per this
## project's own standing discipline for changes that touch self-edit's
## training/scoring path)

The AST-complexity proxy needs to be replaced or supplemented with
something that can distinguish correct-and-simple from broken-and-busy
for the `coding`/`self_edit_coding` task types specifically — at
minimum, actually running the candidate (F2's sandbox already does this
for safety; nothing currently feeds a *correctness* signal from that run
back into the quality score itself, only pass/fail for deployment
safety). This is exactly the kind of scoring-path change this project's
own history treats as consequential enough to need a shown diff and
explicit sign-off before landing, not something to default into from an
investigation alone.
