# FeralEcho — Learning Loop v1.2: Clean Causal Transfer Experiment

## 1. Executive Summary

With the historical self-edit prompt contamination (the real, currently-broken `self_edit_generated.py`
contents; `CODE_OUTPUT_RULES`; every historical identifier from T2/T4) removed entirely, and with the
lesson itself corrected to remove a second, previously-unnoticed contamination source (named historical
identifiers baked into the lesson sentence's own wording), CONTROL and EXPERIENCE produced **byte-for-byte
identical generated code**. Both failed the identical ground-truth test with the identical `NameError` on
the identical line. This is the cleanest possible null result available to this experimental design: not
ambiguous, not confounded, not underpowered in the way a subtle effect would be — the lesson was verifiably
present in the prompt (1361 vs. 1085 characters, confirmed different) and had **zero detectable effect** on
what was generated.

**Verdict: RED — No evidence of learning.** Not GRAY: the protocol was not contaminated (verified explicitly,
§9) and no confound prevents interpretation. Not ORANGE: ORANGE requires the lesson to have changed
behavior; here it demonstrably did not, at all.

## 2. Hypothesis

**H1**: Injecting a real, verified, historical NameError-class failure/correction lesson into a plain
code-completion prompt (unrelated to self-edit) causes measurably different — and more often correct —
completions than an otherwise identical prompt without the lesson.

**H0**: The lesson produces no measurable difference in completion correctness.

## 3. Prior Evidence

`audits/2026-09-06_first_real_learning_loop.md` (T1/T2): the lesson was first shown to influence a
self-edit-shaped generation (T2 imported `log_call` from the real deployed file) — but the "success" was
coincidental (that name happened to already exist in the deployed file).

`audits/2026-09-06_first_real_learning_loop_v1.1.md`: independently re-derived the same result and added
that T2's candidate would have failed the real F1 safety gate before ever reaching F2 — the apparent
success was never viable in the real pipeline at all. A constructed counterfactual (removing `log_call`'s
accidental availability) made the identical candidate fail with `ImportError`, directly disproving semantic
application.

`audits/2026-09-06_first_real_learning_loop_v1.1_T4.md`: the missing EXPERIENCE trial on a fresh task
(same self-edit-shaped prompt) produced a candidate that failed F2 outright and reproduced *more* of the
historical broken-file surface pattern than CONTROL, with the shared, real-file-contents confound
explicitly named as the likely dominant driver of both conditions' output.

This experiment (v1.2) is the first in the series to remove that confound entirely rather than merely
name it.

## 4. Experimental Isolation

Verified directly, both before and after the run (not merely asserted):

| Check | Before | After |
|---|---|---|
| `run.py` process | not running | not running |
| watchdog (`start_echo.sh`) | not running | not running |
| Port 5000 | unbound | (not re-checked; no process exists to bind it) |
| Ollama | reachable, 9 real models | (used successfully for both trials) |
| `memory/river_brain.pkl` mtime | `Sep 6 16:24:16` | `Sep 6 16:24:16` — **unchanged**, confirming `neutralize_river_brain_writes()` held throughout |
| `git status` | baseline (this session's already-known files) | identical set plus this pass's own new files — nothing unexpected |

Model/configuration: real multi-councillor deliberation (`qwen2.5-coder:7b`, `mlx:qwen3`, `echo:latest`),
via `echo_query(task_type="coding")` — the same real pipeline every prior trial in this series used, not
changed for this pass. Both trials' synthesis step logged `Synthesis dropped agreed-upon definition(s)
['EventTracker'] — rejecting synthesis, falling back to best candidate` — confirmed via direct log
inspection, both real, both genuine deliberation cycles (`memory/council_deliberations.jsonl`, `source:
real_deliberation`, matching councillor sets, both entries fresh from this run).

## 5. Exact Lesson Provenance

`app/experiments/first_learning_loop/lesson_mining.py`'s `mine_lessons()` (unmodified, real mechanical
extraction from `memory/echo_watchdog.log`, unchanged from T2/T4) found 5 real, verified historical
NameError-correction events, total real occurrence count **315**.

**A real, previously-unnoticed contamination source in the lesson itself was found and corrected in this
pass, disclosed here rather than silently patched.** The existing `build_experience_sentence()` (used
verbatim by T2 and T4) names specific historical identifiers as examples: *"...a name (such as 'log_call',
'load_existing_function', 'self', 'self_edit_generated', 'generate_and_modify_code')..."* — this itself
fails this experiment's own mandatory contamination check (`log_call` is on the forbidden-token list). The
original v1.2 mission's own §5 anticipates and resolves this exactly: its literal **BAD** example is a
sentence naming a specific historical identifier; its literal **GOOD** example — "*a referenced name must
be imported or defined before use*" — names none. A new function, `build_clean_experience_sentence()`,
was added (not modifying the original, which T2/T4's own historical record still depends on for
reproducibility) that preserves the identical real, verified count (315) and the identical underlying
mechanism/claim, with no historical identifier named:

> *"In 315 historical self-edit sandbox attempts, code that referenced a name without first importing or
> defining it failed sandbox verification with a NameError; in each case, the correction that passed
> verification added the missing import or definition before using the name."*

**Retroactive implication for T2/T4, stated plainly**: their lesson sentences named `log_call` explicitly
as a historical example. This is a second, independent, previously-uncharacterized route by which the
model could have been cued toward that specific name — not just the deployed file's own contents (already
established), but the lesson text itself. Neither prior report identified this. It does not overturn
either report's conclusion (both already independently established non-transfer via other evidence) but it
does mean T2/T4's design was contaminated in one more way than previously known.

## 6. Exact CONTROL Prompt

```
Complete the following Python module so it behaves exactly as its own docstring describes. Output only
the complete, corrected Python module as a single code block -- no explanation, no markdown outside the
code fence.

```python
"""
event_tracker.py
[... full docstring and EventTracker stub, see §8 ...]
```
```

1085 characters, verified via direct length check.

## 7. Exact EXPERIENCE Prompt

Identical to §6, plus the exact clean lesson sentence from §5 appended after the code fence, separated by
a blank line. 1361 characters, verified via direct length check. **Prompts confirmed genuinely different**
(not accidentally identical) — a real, necessary precondition for interpreting a null result as meaningful
rather than trivial.

## 8. Task Construction

A minimal `EventTracker` class with a `track_event` method to complete, per a docstring specifying exact
required behavior (increment a count, return a running total, call `trace_recorder(self.counts)` once
every `report_every`-th call). `trace_recorder` is named only as "the service's shared reporting hook" —
never defined or imported anywhere in the provided module, and no real external implementation exists in
this synthetic context (making import a non-viable path; the one well-defined correct completion is a
local definition before use, matching the lesson's own "imported **or defined**" phrasing exactly). The
task is phrased as an ordinary completion request, never as "there is a bug" or "a name is undefined" —
satisfying the original mission's own anti-gotcha requirement (§7).

## 9. Why Historical-Context Contamination Is Absent

Verified directly, not asserted: `check_contamination()` was run against both final prompt strings,
checking for the literal presence of `self_edit_generated.py`, `log_call`, `CodeGenerator`,
`get_shortened_code`, `run_code_generator`, `apply_list_comprehension`, and every real secret-name pattern
this project's own Tier 1 remediation work established. **Zero matches in either prompt.** This required
one real, disclosed intervention (§5) beyond simply reusing T2/T4's existing lesson-sentence function
unmodified — the deviation itself is evidence the check was taken seriously rather than performed pro
forma.

## 10. Model/Configuration

`echo_query(prompt, task_type="coding", source="autonomous", trace_id=None)` — the standard real
deliberation path, unmodified from T2/T4. No temperature, model-pool, or pipeline change was needed or
made.

## 11. CONTROL Candidate

```python
"""
event_tracker.py
[docstring, see §8]
"""

class EventTracker:
    def __init__(self, report_every: int = 2):
        self.counts = {}
        self.report_every = report_every
        self.total = 0

    def track_event(self, event_type: str) -> int:
        if event_type not in self.counts:
            self.counts[event_type] = 0
        self.counts[event_type] += 1
        self.total += 1
        if self.total % self.report_every == 0:
            trace_recorder(self.counts)
        return self.total
```

Generated in 39.85s (real, logged).

## 12. EXPERIENCE Candidate

**Byte-for-byte identical to §11.** Generated in 44.7s (real, logged — the ~5s difference is consistent
with the longer prompt's real extra token cost, not evidence of a different generation path).

## 13. Independent Evaluator

Plain, direct Python execution — no F1/F2 sandbox machinery used for this pass (judged unnecessary and
explicitly not redundant-but-skipped: this is a standalone synthetic module with no self-edit-specific
import restrictions to check, and F1/F2 would add process overhead without adding evaluative power beyond
what direct execution already provides for this specific, simple task). Both candidates were `exec()`'d
in a fresh namespace, `EventTracker(report_every=2)` instantiated, `track_event("click")` called twice in
sequence, exactly as pre-specified before generation.

## 14. Raw Ground-Truth Results

| Condition | Call 1 (`track_event("click")`) | Call 2 (`track_event("click")`) | Verdict |
|---|---|---|---|
| CONTROL | returns `1` | raises `NameError: name 'trace_recorder' is not defined` | **FAIL** |
| EXPERIENCE | returns `1` | raises `NameError: name 'trace_recorder' is not defined` | **FAIL** |

Identical outcome, identical failure point, identical exception.

## 15. Counterfactual Analysis

Per the mission's §14: would either candidate have succeeded without the lesson? CONTROL already answers
this directly — it's the same code, generated with no lesson at all, and it fails identically. No
counterfactual construction is needed beyond the experiment's own CONTROL arm, which is doing exactly the
job a counterfactual is meant to do here.

## 16. Memorization Analysis

Neither candidate contains any of the six historically-recurring tokens (`log_call`,
`generate_and_modify_code`, `apply_list_comprehension`, `CodeGenerator`, `get_shortened_code`,
`run_code_generator`) — confirmed by direct string search. This rules out literal historical-artifact
replay as an explanation for *either* the failure or the (absent) success. The failure mode here is
generic and task-native (referencing `trace_recorder` per the docstring's own instruction, without
resolving it) — not a copy of any prior experiment's specific bug.

## 17. Evaluator-Gaming Analysis

Not applicable in the sense the mission's §12 anticipates (no-op, exception-swallowing, hardcoded output)
— both candidates made a genuine, good-faith attempt at the real task and failed on a genuine, unforced
oversight. No gaming pattern present in either.

## 18. Generalization Classification

**G0 — no generalization observed**, and more specifically than the mission's own G0/G1/G2/G3 scale
anticipated: this is not "the lesson only worked on the literal historical case" (which would still show
*some* effect on a near-identical case) — it is **zero measurable effect on this novel case at all**. The
lesson was present, verified different from CONTROL by 276 characters, and produced no detectable
influence on generation whatsoever.

## 19. Red-Team Objections

Applying the mission's §16 checklist directly:

1. **Could CONTROL have been unlucky?** Not applicable — there's no differentiation to attribute to luck.
2. **Could the EXPERIENCE prompt have leaked the answer?** No — checked directly (§9), and even if it had,
   EXPERIENCE would then need to have succeeded, which it didn't.
3. **Did the lesson contain the answer?** No (§5's clean sentence states only the abstract rule).
4. **Did task wording cue the lesson?** No — the task never mentions imports, undefined names, or bugs.
5. **Did the model already know this pattern?** Plausibly yes for the *bug* (a very common, generic
   oversight), but this doesn't explain the *lack of any lesson effect* — if anything it would predict the
   lesson should be redundant-but-harmless, which is roughly what was observed (no effect either way).
6. **Was the task too easy?** No — both conditions failed it.
7. **Did the evaluator miss a latent failure?** No — the evaluator caught the real failure directly via
   plain execution, the most transparent possible check.
8. **Did a candidate exploit the evaluator?** No (§17).
9. **Did the candidate imitate a familiar pattern?** No unique historical pattern present (§16).
10. **Lexical overlap with historical artifacts?** None (§16).
11. **Did hidden FeralEcho state enter generation?** The real, current deployed `self_edit_generated.py`
    contents were deliberately *not* included in either prompt (unlike T2/T4) — confirmed by direct
    inspection of both final prompt strings (§6/§7), which contain only the task and (for EXPERIENCE) the
    lesson.
12. **Background process influence?** `run.py` and its watchdog confirmed stopped throughout (§4).
13. **Ollama/model state differ between conditions?** No evidence of this — same model pool, same
    deliberation shape (3 real councillors + synthesis-reject-fallback) for both.
14. **Generation order confound?** CONTROL ran first as pre-registered (§11's timestamp precedes §12's);
    no evidence order mattered given the results are identical regardless.
15. **Could this be random?** The *specific* byte-identical outcome across two independent real generation
    calls is itself a real, flagged observation (§21) — but it does not create ambiguity about the
    direction of the result, since identical failure in both conditions is the strongest possible form of
    "no differentiation," not a weak or noisy one.

## 20. Causal Attribution

**Experience**: 315 real historical self-edit NameError failures, each followed by a real, sandbox-verified
successful retry (`memory/echo_watchdog.log`, mechanically mined, unchanged mechanism from T2/T4).
**Ground truth**: the real F2 sandbox pass/fail signal already trusted throughout this whole series.
**Lesson**: a single abstract sentence, corrected in this pass to remove named historical identifiers
(§5), stating the general rule without any surface-level cue.
**Persistence**: lives in `memory/echo_watchdog.log` itself (the lesson is re-mined fresh each run, not
cached separately) — real, durable, already-existing project state.
**Retrieval**: `mine_lessons()`, direct function call, real and mechanical.
**Exposure**: the exact sentence in §5, appended verbatim to the EXPERIENCE prompt, confirmed present
(§6/§7 length check) and confirmed contamination-free (§9).
**Behavioral change**: **none detected** (§12/§14) — this is the link that breaks.
**Outcome**: both conditions fail identically (§14).
**Attribution**: since there is no behavioral difference to attribute, there is no causal claim to make
in either direction — this experiment provides no evidence *for* the lesson mattering and, because the
result is a clean, uncontaminated null rather than an ambiguous one, meaningful evidence *against* this
specific lesson-injection mechanism producing any transfer on this specific task shape.
**Generalization**: G0 (§18).

## 21. Limitations

- **N=1 matched pair.** Per the mission's own §18, a single negative result should be diagnosed, not
  treated as final. The byte-for-byte identical output across two independent real generation calls (with
  genuinely different prompts) is itself worth flagging as a real, open question: either (a) the real
  multi-councillor deliberation's "reject synthesis, fall back to best candidate" mechanism is
  deterministically selecting the same underlying candidate regardless of a prompt addition this size
  (276 characters against a ~1000+ character base prompt), or (b) this specific task has an "obvious"
  completion multiple independent real generations converge on regardless of any input variation this
  small, or (c) some combination. This experiment cannot distinguish these from the evidence gathered —
  stated as a genuine unknown, not resolved.
- **Single task, single failure class.** This tests one shape of "reference an undefined name" bug; it
  does not establish whether the lesson would transfer differently on a structurally different variant.
- **A planned replication (mission §17) was not run.** Given the result was negative, not a clean
  CONTROL-fail/EXPERIENCE-succeed positive, the mission's own §17 (replicate on a clean positive) does not
  apply; §18 (diagnose a negative) is addressed above and in §23 below, but no additional matched pairs
  were generated in this pass.
- **The task's own difficulty was not independently calibrated** before this run — it happened to be hard
  enough that CONTROL failed (a necessary property for this design to be informative at all), but this was
  a reasonable design judgment, not something verified against a larger sample of models/attempts.

## 22. Whether Production Was Modified

**No.** Verified directly (§4): `run.py`/watchdog never started, `river_brain.pkl` mtime unchanged
before/after, `git status` shows only this experiment's own new files (`app/experiments/
first_learning_loop/v1_2_clean_transfer.py`, `v1_2_trial_results.jsonl`) plus this report — nothing in
`app/core/`, `self_edit_generated.py`, or any other production path was touched.

## 23. Recommended Next Experiment

Per §21's own flagged uncertainty, the single most informative next step is **not** a repeat of this exact
design — it's isolating whether the byte-identical output is a real property of this generation pathway
(the deliberation/synthesis-fallback mechanism converging regardless of small prompt deltas) or specific
to this one task. Concretely: run the same CONTROL/EXPERIENCE pair on a **different**, comparably-shaped
but distinct synthetic task (fresh identifiers, same underlying missing-name-reference bug class), and
separately, run CONTROL twice (no lesson, same prompt, two independent calls) to establish whether
byte-identical output is normal for this pipeline on this class of task or specific to what happened here.
The second check is cheap, fast, and would resolve §21's core open question directly.

---

## Final Answers

**1. Did EXPERIENCE correctly resolve the novel `trace_recorder` dependency?** No.

**2. Did CONTROL fail to resolve the same dependency?** Yes — identically.

**3/4/5. Did T4-equivalent gates matter here?** Not applicable in this design (F1/F2 not used, §13); the
direct functional test is the ground truth, and both failed it identically.

**6. Did EXPERIENCE outperform CONTROL?** No — zero measurable difference of any kind.

**7. Can the difference be attributed to the lesson?** There is no difference to attribute.

**8. Was actual generalization observed?** No — G0 (§18).

**9. Strongest remaining explanation for the result besides "no learning occurred"?** That the specific
generation pathway's synthesis-fallback behavior may be insensitive to prompt deltas of this size on this
task shape — a real, disclosed, unresolved alternative explanation (§21), not ruled out by this pass.

**10. Does this upgrade or downgrade the series' verdict?** Confirms and sharpens ORANGE→RED-relevant
evidence for this specific mechanism: where T2/T4 showed influence-without-learning (confounded by shared
context), this clean version shows **no influence at all** once the confound is removed — consistent with
the hypothesis that T2/T4's "influence" was substantially or entirely driven by the historical file
contents, not by the lesson text itself.

**11. Which link in the causal chain does this experiment demonstrate, and which remains broken?**
**Demonstrated**: lesson persistence (mining works, real data, real count) and lesson exposure (confirmed
present, confirmed uncontaminated) are both real and functioning. **Broken, and now demonstrated broken
under genuinely clean conditions for the first time in this series**: the very next link — lesson exposure
→ behavioral change — did not fire at all. Every link past that (semantic application, generalization,
independent verification) remains untested because there was no behavioral change to test.

**12. Smallest next experiment to distinguish competing explanations?** §23's second check (repeat CONTROL
twice, no lesson, to see if byte-identical output is normal for this pipeline) — cheaper and more directly
diagnostic than a full new matched pair.

---

## Verdict: **RED**

No credible evidence that the lesson caused any behavioral change, let alone improved behavior, under
conditions specifically constructed to remove every contamination source identified in the three prior
experiments in this series. This is not proof that FeralEcho cannot learn from this kind of experience —
per this mission's own standing principle, it is evidence that this specific pathway, tested this cleanly,
did not demonstrate it.
