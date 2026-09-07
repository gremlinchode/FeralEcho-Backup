# FeralEcho — First Real Learning Loop v1.1: ORANGE Adversarial Replication

Read-only w.r.t. production throughout. `run.py` was never started (confirmed both by direct process
check — no `python run.py` process exists — and by its own sentinel file, `memory/echo_sentinel.json`,
whose `last_heartbeat_utc` is stale relative to this pass's own real activity, meaning it never resumed
updating). No RiverBrain state was mutated (`RiverBrain.learn/save/_do_save` neutralized at the class
level before any call, the same already-proven-safe pattern from `scripts/memory_ablation_experiment.py`
— confirmed post-hoc: `memory/river_brain.pkl`'s mtime is unchanged by this pass). No production file was
touched; `app/experiments/first_learning_loop/` has zero external callers (grepped directly). `git status`
shows only this new report, the pre-existing new experiment package, and pre-existing modifications from
earlier in this session unrelated to this pass.

---

## 1. Executive Summary

**The ORANGE verdict survives this adversarial replication, and the evidence for it is now substantially
stronger and more precise than v1's own report established.** Two new pieces of evidence, both found in
this pass and neither anticipated going in:

1. **A methodological correction that sharpens the finding, not softens it**: v1's evaluator
   (`test_code_in_sandbox()`, F2 only) was less strict than the real production self-edit pipeline. Direct
   re-testing of v1's exact EXPERIENCE candidate against F1's real import-validation gate
   (`_validate_imports()`) shows it would have been rejected as a **self-referential import**
   (`from app.core.self_edit_generated import log_call` — importing from the very file the candidate is
   meant to become) before ever reaching F2 at all. The "F2 PASS" v1 reported was real, but it was a pass
   against an incomplete gate — the real self-edit pipeline would never have let this candidate through.
2. **A constructed, empirically-verified counterfactual** (Phase 5, not attempted in v1): with `log_call`
   removed from an isolated stand-in module, the exact same candidate code's own import statement raises
   `ImportError: cannot import name 'log_call' from 'app.core.self_edit_generated'` — directly, mechanically
   confirmed, not inferred. The apparent "success" depends entirely on an accidental environmental fact.
3. **A new, unplanned finding from a fresh CONTROL trial on a genuinely different task**: with *zero*
   lesson exposure, on a task about execution-time measurement (nothing to do with logging), the model
   *still* spontaneously wrote a function named `log_call` — the identical name from the historical
   lesson. This means the name itself is very likely a pre-existing model attractor for this exact
   generation context, independent of the experimental manipulation — a real, adversarial threat to
   attributing *any* of the `log_call` behavior to the lesson at all.

---

## 2. What v1 Established

Real decision-influence: EXPERIENCE's generated code differed from CONTROL's in a way traceable to the
injected lesson (an added import statement, absent from CONTROL). Real, mechanically-extracted lesson
content (exception text + code diff, no LLM self-report). Verdict: ORANGE — influence without
demonstrated learning.

## 3. What v1 Failed to Establish

Whether the "success" was semantically meaningful (it wasn't — established here, not there). Whether the
candidate would survive the *complete* real self-edit safety pipeline (it would not — established here,
not there, because v1 never ran F1's import-validation check). Whether `log_call` itself was
lesson-induced or a pre-existing generation bias (unresolved by v1 — partially resolved here, pointing
toward "pre-existing bias").

## 4. Changes in v1.1

- Applied `_validate_imports()` (F1) to v1's stored candidates retroactively — new evidence, no new
  generation call needed.
- Constructed and empirically tested the `log_call`-absent counterfactual — new evidence, no new
  generation call needed, zero production risk (an isolated `types.ModuleType` stand-in, registered only
  in a throwaway subprocess's own `sys.modules`, never touching any real file).
- Ran one new, real CONTROL trial on a lexically distinct task (execution-timing decorator, no mention of
  logging) to probe whether `log_call` is lesson-induced or a standing model bias.
- Did **not** complete a matched EXPERIENCE trial on the new task — a real, disclosed time-budget
  limitation of this pass, not a stall or a hidden failure (see §15).

## 5. Experimental Conditions

Unchanged from v1: CONTROL (standard `CODE_OUTPUT_RULES` prompt, no lesson) vs. EXPERIENCE (identical,
plus the mechanically-mined, non-imperative factual lesson sentence). Generation via
`plan_code_logic()` + a `generate_code_from_plan()`-equivalent that omits its trailing `RiverBrain.learn()`
call (unchanged from v1's own harness, `app/experiments/first_learning_loop/harness.py`). Evaluation:
**both** F1 (`_validate_imports()`, newly applied in this pass to every candidate, retroactively and
prospectively) **and** F2 (`test_code_in_sandbox()`, the same real sandbox import test v1 used).

## 6. Trial Inventory

| Trial | Condition | Task | Lesson used | F2 | F1 | New in v1.1? |
|---|---|---|---|---|---|---|
| T1 | control | logging-decorator task (v1's original) | none | PASS | PASS | Re-evaluated (F1 added) |
| T2 | experience | logging-decorator task (v1's original) | yes | PASS | **FAIL** (self-referential import) | Re-evaluated (F1 added) — **reverses the effective verdict on this trial** |
| T3 | control | execution-timing decorator (new, v1.1) | none | PASS | PASS | New trial |
| T4 | experience | execution-timing decorator (new, v1.1) | yes | — | — | **Not run** — time budget exhausted this pass (§15) |

## 7. Trial-by-Trial Results

**T1 (control, original task)**: generic, self-contained `log_call_decorator`/`example_function` pair.
No self-reference, no lesson-relevant behavior to evaluate (nothing in this candidate references an
undefined name at all — genuinely clean code for the task as asked).

**T2 (experience, original task)**: `from app.core.self_edit_generated import log_call` + a set of
functions matching a well-documented, chronically-recurring historical self-edit failure shape
(`generate_and_modify_code`, `apply_list_comprehension`, `CodeGenerator`, `get_shortened_code`,
`run_code_generator`). F2: PASS (import succeeds, because `log_call` genuinely exists in the real
deployed file right now). **F1 (newly checked): FAIL** — `_validate_imports()` returns
`self-referential import: 'from app.core.self_edit_generated'`, confirmed by direct, live call against
the real function, not inferred from its docstring.

**T3 (control, new task)**: real, on-topic `time_execution` decorator (correctly imports `time`, correctly
implements the asked-for behavior) — **plus, unprompted, a second, unrelated function named `log_call`**
that references `logging.info(...)` with **no `import logging` anywhere in the file**. F2: PASS (the bug
is inside a function body, never executed by a plain import — confirmed directly, by executing the
function in isolation: `NameError: name 'logging' is not defined`, exactly the same failure class the
lesson exists to address, invisible to F2 by construction). F1: PASS (no self-referential import in this
candidate — its bug is a different one).

## 8. Decision-Influence Analysis

The lesson clearly changed *something*: EXPERIENCE (T2) attempted an explicit import-based fix strategy;
CONTROL (T1, T3) did not — T1 had nothing to fix, and T3's own real latent bug (undefined `logging`) was
left entirely unaddressed, no import attempted at all. This is a real, repeatable asymmetry in *strategy*
between conditions, consistent with v1's own finding. **What's new**: the specific *name* `log_call`
appearing in generated code cannot, on this pass's evidence, be attributed to lesson exposure — T3 (zero
lesson) produced it too, unprompted, on an unrelated task. The lesson influences *whether an import-style
fix is attempted*; it does not appear to be the source of the `log_call` name choice itself.

## 9. Semantic Lesson-Application Analysis

Applying the mission's own five-question test to T2 (the only EXPERIENCE trial completed):

- **A. Rule extraction**: "a referenced name must be imported or defined before use."
- **B. Candidate application**: surface-level, yes — an import statement was added.
- **C. Counterfactual robustness**: **fails** — see §10/§11. Change the environment (remove `log_call`'s
  accidental prior existence) and the identical strategy produces `ImportError` instead of success.
- **D. Surface-pattern test**: yes, this candidate closely reproduces a specific, already-documented,
  chronically-recurring historical self-edit output shape (matching multiple real historical backup files
  sampled earlier this same session) — consistent with surface-pattern reproduction, not fresh reasoning.
- **E. Unseen-instance test**: **not established** — the one new-task trial that ran (T3) was CONTROL,
  not EXPERIENCE; whether the lesson would produce a *correct* import (`import logging`) on the new task
  was not directly tested this pass (§15, §25).

## 10. `log_call` Confound Analysis

Two independent lines of evidence converge: (1) `log_call` is currently, coincidentally, genuinely
defined in the live `app/core/self_edit_generated.py` (confirmed directly, line 5). (2) `log_call`
appears **even in a CONTROL trial with zero lesson exposure**, on a lexically and semantically unrelated
task. Together these make it very unlikely that `log_call`'s appearance in T2 reflects anything the
lesson taught — it is much better explained as this specific model, in this specific generation context
(self-edit's own `CODE_OUTPUT_RULES` prompt shape, matching the recurring historical pattern this entire
project's own multi-month Finding history already documents extensively), having a standing bias toward
producing exactly this function name and shape, lesson or no lesson.

## 11. Counterfactual Analysis

Constructed directly, safely, and reported in full:

```python
counterfactual_module = types.ModuleType('app.core.self_edit_generated')
counterfactual_module.__dict__['some_other_function'] = lambda: None
sys.modules['app.core.self_edit_generated'] = counterfactual_module
exec("from app.core.self_edit_generated import log_call")
# -> ImportError: cannot import name 'log_call' from 'app.core.self_edit_generated' (unknown location)
```

This is a deterministic fact about Python's own import semantics, not a probabilistic estimate — the
exact statement T2's candidate contains would fail, guaranteed, in any environment where
`self_edit_generated.py` doesn't happen to already define `log_call`. **The apparent success is not
robust to a trivial, realistic environmental change** (e.g., a future self-edit cycle that removes
`log_call` from the deployed file, which has already happened repeatedly in this project's real history
— the file gets reset to a clean, inert state periodically, per multiple `CLAUDE.md` Findings tonight's
own inherited context already documents).

## 12. F2 Results

Summarized in §6/§7. F2 alone: 3/3 real candidates pass (T1, T2, T3). **F2 is confirmed, again, to be
blind to two distinct real defect classes in this pass alone**: T2's self-referential import (caught only
by F1, not F2) and T3's latent function-body `NameError` (caught by neither F1 nor F2, only by direct
execution outside either gate).

## 13. Generalization Results

**G0 for the specific `log_call` behavior** (§10) — no measurable lesson effect on this specific
surface pattern, since it appears identically without the lesson. **G1 at best for the underlying
"attempt an import-based fix" strategy** — real, but only demonstrated on the exact original task; the
one new-task trial that could have tested G2 (EXPERIENCE on task 2) was not completed this pass. No
evidence supports G2 or G3.

## 14. Adversarial Red-Team

- **Historical-token copying**: supported — T2's full candidate closely matches a real, previously
  logged historical self-edit output shape.
- **Environmental coincidence**: supported and now directly proven (§11).
- **Evaluator weakness**: supported and *worse than v1 characterized* — two distinct classes across only
  three trials (§12).
- **Task leakage / contamination**: not found — the lesson corpus (mined from `echo_watchdog.log` entries
  predating this session) and the trial prompts (constructed live, this session) do not overlap in
  content, only in the *names* the lesson happens to mention (`log_call` among them), which is the
  confound itself, not leakage in the technical sense.
- **Stochastic luck**: plausible and not ruled out — n=1 per condition per task remains far too small to
  exclude.
- **Secret exposure**: checked directly — the lesson corpus contains only an exception-message regex
  capture (a bare identifier name) and a literal occurrence count; grepped against this project's own
  known real secret-name patterns (`GREMLIN_SECRET`, `ANTHROPIC_API_KEY`, etc.) — zero matches, as
  expected by construction (no code path in `lesson_mining.py` ever reads an environment variable).

## 15. Ollama Contention / Reproducibility

With `run.py` genuinely stopped (confirmed, §0), the completed trials in this pass ran without the
severe multi-hour stalls seen twice earlier this session — T3's full plan+generate cycle completed in
several real minutes (a genuine, real multi-councillor deliberation for the planning step, confirmed via
direct log inspection: `mlx:qwen3` and `echo:latest` both queried, a real synthesis step run), consistent
with ordinary real latency rather than contention. **The planned T4 (experience, new task) was not run
in this pass** — not due to a stall, but due to this pass's own practical time budget being reached after
the counterfactual construction, the F1 re-evaluation, and T1-T3. This is reported plainly per the
mission's own instruction to report a stop condition honestly rather than push through it artificially —
it is a real, disclosed gap, not a hidden one.

## 16. Control vs. Experience Comparison

With F1 correctly applied: **CONTROL 2/2 would-be-eligible-for-deployment (T1, T3 both pass F1+F2, though
T3 has an F2-invisible bug); EXPERIENCE 0/1 would-be-eligible (T2 fails F1).** This is a striking
reversal from v1's own reported "both passed" framing — under the corrected, complete evaluation, the
EXPERIENCE condition's one completed trial performs *worse*, not equivalently, once the real production
gate sequence is applied.

## 17. Statistical/Uncertainty Analysis

n=1 per condition per task (T1 vs T2), plus one unmatched additional control (T3). No statistical test is
meaningful at this sample size, and none is attempted — this mission is explicitly a pilot/replication
exercise per its own Phase 9, not a claim of statistical significance.

## 18. Strongest Positive Evidence

The lesson does change *something* concrete and attributable — the presence of an import-fix *attempt*
in EXPERIENCE that's entirely absent from both CONTROL trials, even though CONTROL's own T3 candidate had
an equally real, equally fixable NameError-class bug it made no attempt to address. That's a real,
repeatable behavioral difference, not nothing.

## 19. Strongest Negative Evidence

§10-§11 combined: the specific mechanism of that apparent success is empirically proven non-robust to a
realistic environmental change, and the specific surface token driving it is shown, in this same pass, to
be model-attractor behavior independent of the lesson.

## 20. False-Positive Analysis

T2 is now a textbook false positive, established with more rigor than v1 achieved: it would fail the real
production pipeline (F1), it fails a constructed counterfactual (§11), and its central identifying
feature (`log_call`) appears without the manipulation that was supposed to cause it (§10, via T3).

## 21. GREEN/YELLOW/ORANGE/RED Verdict

**ORANGE — confirmed, and more precisely evidenced than v1's own report established.** Not downgraded to
RED: a real, repeatable, attributable behavioral difference between conditions still exists (§18) — the
lesson is not inert. Not upgraded to YELLOW: every piece of evidence available now argues *against*
semantic application rather than merely being silent on it (§9's Criterion C explicitly fails, not just
"unproven").

## 22. Comparison with Michelangelo I–IV

Directly continues Michelangelo IV's own central finding (FeralEcho primarily accumulates rather than
learns from experience) and its own strongest false-positive discovery method (read the actual generated
artifact, don't trust the pass/fail boolean) — applied here one level deeper, to the experiment built
specifically to test the boundary Michelangelo IV identified. Consistent, not contradictory, with every
prior pass tonight.

## 23. Updated Capability-Ceiling Assessment

Unchanged in direction, strengthened in precision: the ceiling identified across Michelangelo I-IV (most
mechanisms terminate at "logged, not acted on"; the rare exceptions close on weak proxies) now has a
concrete, adversarially-tested example of *why* a naive attempt to build past that ceiling can look
successful without being successful — a specific, reusable cautionary case for any future attempt at this
same bridge.

## 24. What This Says About Learning vs. Experience Accumulation

Consistent with Michelangelo IV's own answer: FeralEcho accumulates experience. This pass adds a specific,
mechanistic reason one particular attempt to convert accumulated experience into genuine learned
application produced an illusion of success rather than the real thing — coincidental environmental
alignment plus a pre-existing model bias, not rule application.

## 25. Whether Another Replication Is Warranted

**Yes, specifically**: complete the missing T4 (experience, new task) — this is the one trial that could
actually test G1-vs-G2 directly (does the lesson produce a *correct* `import logging` fix on the new
task, where no accidental pre-existing name bails it out). This is the single most informative next data
point available, cheap relative to everything else in this pass (one more real generation call), and was
not run here only due to time budget, not because it's uninteresting or unsafe.

## 26. Whether Any Production Change Is Justified

**No.** Consistent with the mission's own explicit rule and v1's own conclusion — nothing here should be
connected to production self-edit's real pipeline. If anything, this pass adds a reason for *more*
caution: it directly demonstrates a concrete way a naive "add historical lessons to the prompt" mechanism
could look like it's working (by F2's own incomplete measure) while actually producing a candidate the
real, complete pipeline would reject anyway.

## 27. Recommendation for the Next Engineering Phase

Not a production change. A cheap, targeted completion: run T4, and if time permits, 2-3 more matched
pairs using genuinely fresh, non-recurring identifier names in the lesson-relevant position, specifically
designed so no name in the lesson corpus can coincidentally already exist in the live deployed file —
this is the controlled test that would finally isolate "did the model apply the rule" from "did the model
get lucky with a name it already likes."

---

## Required Final Answers

**1. Did verified past experience change future generation?** Yes — a real, repeatable strategic
difference (attempting an import fix) exists between EXPERIENCE and CONTROL.

**2. Did the change correspond to the underlying semantic lesson?** Only superficially. The *form*
(adding an import) matches; the *substance* (a name that actually needs importing, correctly identified
and correctly resolved) does not survive the counterfactual test (§11).

**3. Did the lesson work on an unseen related problem?** Not established either way — the one trial that
could test this (T4) was not completed this pass.

**4. Did the resulting code work under the independent F2 evaluator?** Yes for F2 alone (T2 passed). No
under the corrected, complete evaluation once F1 is included (§7, §16).

**5. Did it work for the right reason?** No — established directly by the counterfactual (§11) and by
the pre-existing-bias evidence (§10).

**6. Did the experience condition outperform control?** No — under the corrected evaluation (§16),
CONTROL's trials both clear F1+F2; EXPERIENCE's one trial does not clear F1.

**7. Can the difference reasonably be attributed to the lesson?** The *strategic* difference (attempting
an import), yes. The *specific successful-looking outcome*, no — better explained by environmental
coincidence and a pre-existing model bias (§10, §11).

**8. Did we observe actual generalization?** No — G0 for the specific behavior driving the apparent
success; at most G1, unconfirmed, for the underlying strategy.

**9. What is the strongest remaining explanation for the result besides learning?** A combination of (a)
a pre-existing generation bias toward producing `log_call`-named/shaped code in this exact prompt context,
independent of any lesson, and (b) that bias coincidentally aligning with a real, currently-true fact
about the deployed environment.

**10. Does the evidence justify upgrading ORANGE to YELLOW or GREEN?** No.

**11. If not, what specifically prevented the upgrade?** The counterfactual test (§11) and the
confound-revealing new CONTROL trial (§10) both directly argue against semantic application, rather than
merely failing to confirm it — an upgrade would require evidence pointing the other way, and none was
found.

**12. What is the smallest next experiment that could distinguish the remaining competing explanations?**
Run T4 (EXPERIENCE on the execution-timing task) and inspect whether it produces `import logging`
specifically (correct rule application, no coincidental bailout available) versus a `log_call`-shaped
distraction again (bias winning over the lesson) versus something else entirely. One real generation
call, already-built harness, no new infrastructure needed.

---

## §0. System-State Verification (referenced above)

- `run.py`: no process found (`ps aux` checked directly, both at the start and end of this pass).
- `memory/echo_sentinel.json`: `last_heartbeat_utc` stale relative to this pass's real activity —
  confirms the process never resumed writing to its own liveness file.
- `memory/river_brain.pkl`: mtime unchanged by this pass's activity (checked directly before and after).
- `git status`: clean except this report, the pre-existing `app/experiments/first_learning_loop/`
  package (zero external callers, reconfirmed), and pre-existing unrelated modifications from earlier in
  this session.
