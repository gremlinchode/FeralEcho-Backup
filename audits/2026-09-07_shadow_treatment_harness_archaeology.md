# Shadow Treatment Harness Archaeology

## Executive Summary

**Verdict: S-T0 — NO VALID TREATMENT POINT.**

This mission stopped at Phase 2, exactly as its own protocol requires. `check_and_correct()`'s
proposed correction (`corrected_task`, the local variable `worst_task` inside
`app/core/shadow_model.py`) is consumed by exactly one real caller in production
(`app/maintenance/night_cycle.py:182`), and that caller's only use of the value is a
`logging.warning(...)` call. Nothing reads the log line. No decision point, model-selection
call, self-edit targeting function, RiverBrain update, or any other consequential mechanism
anywhere in the codebase branches on, stores, or otherwise consumes `corrected_task`.

There is therefore no defensible treatment point to isolate, no downstream outcome to compare
against a control, and no experimental harness that could produce meaningful evidence — building
one would mean measuring the effect of an intervention that, in the current architecture, cannot
occur. Per Phase 2's own explicit instruction, this is a legitimate, successful forensic result,
not a failure of the investigation. No harness was built. No RiverBrain call was made. No
production file was touched.

This finding is narrower and more precise than the immediately-preceding S-V5 verdict
("mechanism mis-specified"). S-V5 established the *fact* of zero consumers via `grep`. This
mission traces the *actual caller chain* by hand, confirms the same conclusion through direct
source reading rather than absence-of-match, and additionally confirms there is no *intended-but-
disconnected* treatment point either — the code comment explaining why `propose()` is absent
describes a future reconnection plan, not a currently-dormant pathway that could be tested as-is.

---

## 1. Safety Verification

**Before:**

| Check | Result |
|---|---|
| `run.py` / watchdog process | None running (`ps aux` shows only the unrelated macOS system `watchdogd`) |
| Port 5000 | Unbound |
| Git HEAD | `c5bf2e5f8913e35a1ded9af8afe68e247651e26d` |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` |
| `shadow_accuracy.jsonl` sha256 | `bb022e8321c30526c4feed52a0ac06a79a162c230a91c483c230a1549bb0359a` |
| `shadow_corrections.log` sha256 | `983b6f04d5f54b34f28471700c833b87780fe3cdb3ee1c4cc182262c648bff32` |
| Working tree | Clean except two pre-existing untracked paths (`.claude/`, `app/experiments/real_trace_f2_provenance/_scratch/`), both pre-dating this mission and left untouched |

**After:**

| Check | Result |
|---|---|
| `run.py` / watchdog process | Still none running |
| Git HEAD | `c5bf2e5f8913e35a1ded9af8afe68e247651e26d` — unchanged |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` — unchanged |
| `shadow_accuracy.jsonl` sha256 | unchanged |
| `shadow_corrections.log` sha256 | unchanged |
| Production source | Zero files modified (read-only investigation) |
| RiverBrain calls | None made — no experiment ran, so neutralization was not required |
| New files created | This report only |

No self-edit was run. No `propose()` call was made. `corrected_task` was not wired to anything.

---

## 2. Exact Historical Shadow Mechanism

Read in full from current source (`app/core/shadow_model.py`, 197 lines):

```text
propose_from_reflection(reflection_text)      [called from app/emergent_scheduler.py:730,
                                                on real reflection cycles]
        │  keyword-matches reflection text against 4 task-type vocabularies
        │  (reasoning/coding/creative/personal); if best match scores >= 2,
        ▼
propose({"targets": {"next_self_edit_focus": best_task, "reason": "..."}})
        │  shadow = {**real_self_model.json, **adjustments, "shadow_proposed_at": now}
        │  writes memory/shadow_self_model.json — the ENTIRE real snapshot, not just
        │  the "targets" key, overwritten by the merge
        ▼
[time passes — real self-edit / self-model-update activity happens independently]
        ▼
log_accuracy()                                 [called from app/maintenance/night_cycle.py:176,
                                                 on the nightly maintenance cycle]
        │  calls compare_to_actual():
        │    shadow_targets.next_self_edit_focus  vs  real_targets.next_self_edit_focus
        │       → focus_matches: bool
        │    for each task type: real_avg_quality - shadow_avg_quality
        │       → quality_delta_from_shadow: {task: float}
        │  appends one row to memory/shadow_accuracy.jsonl
        ▼
check_and_correct(delta)                       [called from app/maintenance/night_cycle.py:182,
                                                 same nightly cycle, same delta object]
        │  worst_task = argmin(quality_delta_from_shadow)
        │  if worst_delta < -0.15:
        │      appends one row to memory/shadow_corrections.log
        │      (fields: ts, corrected_task=worst_task, delta, all_deltas,
        │       shadow_focus, real_focus)
        │      returns worst_task
        │  else:
        │      returns None
        ▼
corrected = check_and_correct(delta)           [night_cycle.py:182]
        │
        ▼
if corrected:
    logging.warning("[NightCycle] Shadow drift corrected → new focus proposed: %s", corrected)
        │
        ▼
                                                 ── nothing else. Log line ends the chain. ──
```

Real, current data (verified this session, not carried over from the prior mission unchecked):

- `memory/shadow_self_model.json`: exists, 17,231 bytes, `last_updated`/`generation` fields
  present, real per-task performance data — genuinely live and current (`Sep 6 16:17` mtime).
- `memory/shadow_accuracy.jsonl`: 2,062 rows (unchanged from the prior mission's count).
- `memory/shadow_corrections.log`: 39 rows (unchanged), most recent tail entries dated
  `2026-09-02T04:18–04:28 UTC`, all with `corrected_task: "general"`, `shadow_focus: "personal"`,
  `real_focus: "coding"` — three consecutive corrections roughly 7–10 minutes apart, all proposing
  the identical correction, consistent with the nightly cycle re-evaluating an unresolved drift
  condition repeatedly rather than the correction ever being applied and the drift resolving.

---

## 3. Reconstructing the Treatment Mathematically

**Not performed as a live experiment** — no treatment/control split was built, per Phase 2's stop
instruction. What follows is the factual boundary of what *would* need to exist for this phase to
be meaningful, established from source rather than assumed.

For a treatment to be defined, some later computation must read `corrected_task` (or the return
value of `check_and_correct()`) and behave differently depending on its value. Traced exhaustively:

- `check_and_correct()`'s return value has exactly one consumer: `night_cycle.py:182`'s
  `corrected` local variable.
- `corrected` is read exactly once more, at `night_cycle.py:183`, inside an `if corrected:` guard
  whose only body is the `logging.warning(...)` call at line 184.
- Nothing reads the log output. `grep -rn "Shadow drift corrected"` across the repository returns
  only the format string's own definition — no parser, no downstream consumer, no test watching
  for it.

There is no branch, no stored value, no field write, and no function call inside or after this
`if` block other than the log statement. **The treatment, as currently implemented, changes
nothing observable about any future computation.** This is not a matter of the treatment being
hard to isolate from a confound (that would be S-T7) or of lacking instrumentation to observe its
effect (S-T8) — there is no effect to observe, by construction, because the value is discarded
immediately after being formatted into a string.

---

## 4. Historical Replay Feasibility

**Not applicable in the form Phase 4 anticipates**, and stated precisely why: Phase 4 asks whether
existing data contains enough information to replay historical *situations* so that a treatment
and control outcome can each be reconstructed. That question presupposes a treatment effect exists
to be replayed. Since Section 3 establishes the treatment has zero downstream computational
consequence, there is no outcome variable for a replay to reconstruct — replaying the 39 historical
correction events would only ever reproduce the same terminal state (a log line), identically,
whether or not the correction is conceptually "applied," because nothing in the surrounding
computation reads it either way.

What *is* independently reconstructable from existing data (stated for completeness, not as a
substitute for the missing treatment link):

| Element | Status |
|---|---|
| The 39 real `corrected_task` values, timestamps, deltas | OBSERVED — full population directly readable from `shadow_corrections.log` |
| The real `shadow_self_model.json`/`self_model.json` state at each correction's timestamp | PARTIALLY RECONSTRUCTABLE — `memory/history/self_model_*.json` snapshots exist only weekly (per `night_cycle.py`'s `_maybe_snapshot_self_model()`), not per-correction, so the exact real self-model state at each of the 39 timestamps cannot be reconstructed precisely, only approximated by the nearest weekly snapshot |
| What River/self-edit behavior "would have been different" under the corrected focus | UNAVAILABLE — no code path exists that computes this counterfactual, and none can be inferred without assuming a treatment mechanism that was never built |

---

## 5. Harness Architecture

**Not built.** Per Phase 2's explicit instruction ("if a defensible treatment point does not
exist, STOP and report S-T0 ... rather than continuing on to build a harness anyway"), no
isolated harness under `app/experiments/` or elsewhere was created for this mission. Building one
would require either (a) inventing a treatment mechanism that does not exist in production — which
would test a hypothetical future architecture, not the real Shadow correction system this mission
was scoped to evaluate — or (b) measuring an intervention with a mathematically guaranteed null
effect, which would produce a result that looks like rigorous negative evidence but is actually
a tautology (nothing consumes the value, so of course treatment == control on every possible
downstream metric).

---

## 6. `propose()` Confound Isolation

**Not reached.** The Phase 6 diagnostic (confirm whether applying the correction changes multiple
unrelated fields via `propose()`'s `{**base, **adjustments}` merge) presupposes `check_and_correct()`
actually calls `propose()`. It does not — the call is the specific thing the source comment says
was intentionally left out (`app/core/shadow_model.py:137-143`). The `propose()` snapshot-
replacement confound, documented exhaustively in the immediately-preceding S-V5 mission, is real
and would need to be solved *before* any future reconnection of `corrected_task` could be tested
cleanly — but it is a downstream problem for a mechanism that does not yet exist to have it. Not
re-litigated here to avoid duplicating S-V5's own analysis.

---

## 7. Baselines (B0/B1/T1)

**Not established.** No outcome metric exists to baseline against. B0 (trivial baseline) and B1
(existing Shadow prediction without correction) are both meaningful for evaluating Shadow's
*categorical prediction accuracy* — already measured exhaustively in the S-V5 mission (16.05% vs.
a 58.78% majority-class baseline, independently reconfirmed there). T1 (apply `corrected_task` as
treatment) cannot be defined, because "applying" it currently means nothing computationally.

---

## 8. Paired-Trial Methodology

**Not applicable.** McNemar's test and any other paired design require two conditions that can
each produce a differing observable outcome on the same underlying situation. With zero downstream
consumers, treatment and control are observationally identical by construction on every one of the
39 historical events — running the test would report a McNemar statistic of exactly 0 with 0
discordant pairs, which is not evidence of "no effect" in the ordinary causal-inference sense; it's
evidence that the two conditions were never actually different in any way the system could detect.

---

## 9. Held-Out Methodology

**Not applicable**, for the same reason as Section 8. A held-out split only produces informative
evidence when there is a real effect that could show up in one split and not the other. Here,
splitting the 39 corrections into discovery/validation halves would just produce two halves of
data about a variable that is discarded identically in both.

---

## 10. Does Treatment Beat Doing Nothing?

**Unanswerable in its intended sense, answerable trivially in a degenerate sense.** "Doing nothing"
and "applying the correction" are the *same production behavior* today — `check_and_correct()`
already runs, already computes `worst_task`, already logs it; the only thing that would change
under a hypothetical "treatment" is whether a currently-nonexistent consumer reads that value.
Since no such consumer exists, treatment and control are the identical running system. There is no
meaningful sense in which one "beats" the other because they are not distinguishable interventions
on the current architecture.

---

## 11. Confounder Analysis

**Not performed as a dedicated statistical exercise**, since there is no correction→outcome
relationship to confound. One structural fact worth recording plainly: the 39 real corrections
cluster heavily around a handful of repeated `(shadow_focus, real_focus, corrected_task)` triples
(e.g., the three tail entries above are near-identical, `personal→coding, corrected=general`,
minutes apart) — consistent with the same underlying drift condition being independently
re-detected and re-logged by the nightly cycle every time it runs, without ever resolving, because
nothing acts on the detection. This is itself weak circumstantial evidence for the Section 2
finding (the correction has no consequence) rather than a confound requiring adjustment.

---

## 12. Correction vs. Narrative

Consistent with the mission's epistemic hierarchy (real outcome > deterministic trace > reconstructed
state > model narrative): every claim in this report is sourced to the actual `shadow_model.py`
and `night_cycle.py` source, or to real rows in `shadow_corrections.log`/`shadow_accuracy.jsonl`.
No LLM-generated interpretation of what a correction "means" was used at any point — `check_and_correct()`'s
own log message (`"Calibration drift | task=%s delta=%.3f → proposed corrective focus"`) is
descriptive text, not evidence of anything beyond the numeric delta it reports.

---

## 13. Adversarial Test Construction

**Not built**, for the same structural reason as Sections 5 and 8 — there is no mechanism under
test whose "useful" vs. "harmful" behavior could differ across adversarial cases, since the
mechanism's only observable output is an identical log line regardless of input.

---

## 14. The "Not Learning" Bar

Trivially, and by the strictest possible reading, this specific pathway fails the bar defined in
Phase 14 (prior consequence → correction → later independent situation → changed behavior → better
outcome) at the *fourth* link, not a later or more subtle one: there is no "changed behavior" step
anywhere in the current implementation, so the chain cannot even be evaluated past that point. This
sharpens (rather than merely repeats) the EHPU-PARTIAL and S-V5 findings — for `corrected_task`
specifically, the break isn't ambiguous or a matter of interpretation. It's a literal absence of
any second reader.

---

## 15. Generalization (G0–G3)

**Not applicable** — generalization classification requires a demonstrated effect to generalize
from. None exists.

---

## 16. Causal Identification

**CAUSAL EFFECT NOT IDENTIFIABLE FROM EXISTING DATA — but for a stronger reason than usual.**
Ordinarily this classification means the data is observational and confounded in ways that prevent
isolating a causal effect. Here the situation is more fundamental: the intervention being asked
about (applying `corrected_task`) has no operational definition in the current codebase at all. It
is not that the effect is hard to identify from noisy data — it is that "the effect of applying the
treatment" is not yet a well-defined quantity, because no code path specifies what "applying" it
would mean. Causal identification is not merely difficult here; the question is not yet well-posed
against the current architecture.

---

## 17. Harm Analysis

**Cannot be assessed**, for the same reason. A mechanism with zero downstream consumers cannot
degrade any outcome, because it has no causal pathway to any outcome. This is a genuinely different,
more definitive statement than "no evidence of harm was found" — it is closer to "harm is not
currently possible via this pathway," which is itself a data point worth recording: whatever risk
`corrected_task` might pose once reconnected is entirely prospective, not something the historical
39 events could have already caused.

---

## 18. Epistemic Gate Assessment

**GATE-C — UNTESTABLE.**

The gate `shadow_model.py`'s own source comment describes ("Reconnect ... once shadow_corrections.log
shows consistent correlation with actual River accuracy improvement") cannot currently be evaluated,
and — this is the important addition this mission makes beyond S-V5's finding that the criterion
"has never been measured" — it cannot be evaluated by any amount of *passive* historical analysis
of the existing log, no matter how much data accumulates, because the log only ever records what
`check_and_correct()` *would have proposed*, never what happened when a proposal was acted on. More
data arriving in `shadow_corrections.log` under the current architecture will never, by itself,
produce evidence sufficient to satisfy the gate. Testing the gate requires either (a) an isolated,
clearly-labeled experimental intervention — building a real treatment point in a sandboxed harness,
which this mission determined is not yet meaningful to attempt because the *production* treatment
point doesn't exist to isolate a faithful copy of — or (b) reconnecting Shadow in production behind
careful monitoring, which is explicitly out of scope for every mission in this investigation to
date.

---

## 19. Learning-Stomach Implications

This finding sharpens, rather than repeats, Section 13 ("Learning-Stomach Assessment") of the
immediately-preceding EHPU-PARTIAL archaeology. That report classified Shadow's correction-
application edge as "exists but disabled." This mission's more granular finding: it is not merely
disabled, it was *never wired to an addressable location* — there is no dormant switch to flip.
Reconnecting it (which no mission has done and none should without separate authorization) would
mean writing new code that defines, for the first time, what "corrected_task takes effect" means
operationally — not restoring a previously-functioning connection.

In the `candidate correction` vs. `learned correction` schema from Phase 19 of the mission spec:
`corrected_task` is unambiguously a `candidate correction` — logged, timestamped, provenance-intact,
never promoted. Shadow already demonstrates the *storage* shape of a candidate correction cleanly
(this mission independently confirms the schema is real, consistent, and complete across all 39
rows: `ts`, `corrected_task`, `delta`, `all_deltas`, `shadow_focus`, `real_focus` — no missing or
malformed fields in any of the 39). What it does not demonstrate, and cannot currently be made to
demonstrate without new code, is any mechanism by which a `candidate correction` could ever be
tested and promoted to a `learned correction` — the promotion pathway does not exist to be tested,
only to be designed.

---

## 20. What Should NOT Be Built Yet (from this mission)

- Do not reconnect `check_and_correct()` to `propose()`.
- Do not build an isolated harness that invents a synthetic treatment point for `corrected_task`,
  since that would test a hypothetical architecture, not the real one — any such result would be
  easy to mistake for evidence about the real Shadow mechanism when it would really be evidence
  about a different, not-yet-built system.
- Do not attempt to satisfy Shadow's own epistemic gate (Section 18) via further passive log
  analysis — Section 18 establishes that path is structurally incapable of ever producing sufficient
  evidence, so more missions like the immediately-preceding S-V5 investigation, run again against a
  larger `shadow_corrections.log`, would not change this conclusion.
- Do not fix the `propose()` snapshot-replacement confound as a "quick win," per the mission's own
  safety invariant #19 — it is currently irrelevant to anything live, and fixing it would be
  unmotivated production risk for a code path with zero consumers.

---

## 21. Uncertainties

- Whether `check_and_correct()`'s design was ever intended to have `corrected_task` consumed by
  something *other* than a future `propose()` reconnection (e.g., a human-facing dashboard, an
  alert) was not investigated — no such consumer exists today, but the original design intent
  beyond the source comment is not independently documented anywhere this mission located.
- The weekly-only cadence of `self_model` history snapshots (Section 4) means a future mission
  attempting a faithful historical replay of Shadow's environment at correction time would have
  meaningfully coarser ground truth than the correction log's own per-event timestamps — flagged as
  a real limitation for any future work in this direction, not resolved here.
- Whether `propose_from_reflection()`'s keyword-matching heuristic (the actual real-world trigger
  for `propose()`, and therefore for what feeds `compare_to_actual()`/`log_accuracy()`) itself
  produces sensible targets was not re-examined here — out of scope for a mission specifically about
  `corrected_task`, and it is a different code path from the one this mission investigated.

---

## 22. Smallest Next Experiment

**None recommended from this mission's own findings**, consistent with Phase 18's "if the correction
cannot even be defined as an intervention from the surviving data, that is a successful forensic
result" and Phase 2's explicit instruction not to build a harness when no treatment point exists.
The one honest next step this investigation surfaces is not an experiment but a design decision,
properly outside this mission's scope: **whether it is worth writing the connective code that would
make `corrected_task` a real, addressable treatment point at all** (i.e., defining, for the first
time, what "applying" a Shadow correction means) — before any causal experiment about its effect can
even be posed as a well-formed question. That decision, and any resulting harness, belongs to a
future, separately-authorized mission, not this one.

---

## 23. Final Classification

**S-T0 — NO VALID TREATMENT POINT.**

`corrected_task`'s only production consumer discards it into a log line one call frame after it is
computed. No causal experiment can be meaningfully constructed for an intervention that does not
yet have an operational definition in the running system. This is a clean, well-evidenced stopping
point, reached via direct source tracing (not inference or absence-of-grep-match alone), and it
sharpens — without contradicting — every prior finding in this investigation arc: Shadow's storage
and prediction-error machinery are real and correctly implemented; its correction-authority pathway
does not yet exist to be tested.
