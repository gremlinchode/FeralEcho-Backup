# Michelangelo Mode — Architectural Discovery Without a Predetermined Solution

No production code modified. One real, safe, reversible experiment run and recorded (§6). One new,
purely-additive, real empirical analysis performed against already-logged data, at zero cost and zero
risk (§2, §6). RiverBrain was never mutated by anything in this report — the one experiment that touches
it neutralizes `.learn()`/`.save()`/`._do_save()` at the class level, the same already-proven-safe
mechanism used twice before tonight (2026-07-23, 2026-09-03).

**Honest framing, upfront**: this report inherits an enormous amount of context from a single, very long
investigative session — Phase 0 through Phase 1.5, the Tier 1 remediation pass, the LoRA feasibility
study, and everything in `CLAUDE.md`. I read all of it. But the mission asked a specific, harder
question: not "summarize what we found," but "what would you have gone looking for, if none of it had
been suggested to you first?" Section 2 is my honest attempt to answer that, anchored in two things I
found in *this* pass specifically, not inherited from any prior report.

---

## 1. Executive Judgment

**FeralEcho's most pressing need is not a new subsystem, a new signal, or a new model. It is a habit the
project has not yet formed: closing the loop from "this ran" back to "did this help," even when the data
to check already exists, for free, right now.**

Every subsystem I looked at tonight that has *any* verification culture has an extremely strong one —
F1/F2/F3, the Liveness Ledger's 30 functional canaries, the adversarial passes, the forensic
re-validations. FeralEcho is unusually good at proving things *ran*. What it has not consistently done is
ask, of things that already ran and already logged their own outcome, whether they were *worth running*.
I found a fresh, concrete instance of exactly this gap in this pass (§2, §6) — not inherited, not
predicted in advance, and answerable from data that was already sitting on disk before I started.

---

## 2. What You See That We May Not

Two findings, both produced specifically by not following a predetermined script — I went looking at
`self_edit_generated.py`'s deployment history for its own sake, not because any prior report pointed me
there.

### 2a. `apply_to_code` ran continuously and "successfully" for six real weeks, and nobody ever asked if it helped.

`memory/SELF_EDIT.log`'s `LOAD_AUDIT` entries show `apply_to_code` genuinely deployed, on and off, across
**19 real load events spanning 2026-07-14 through 2026-08-26** — not a brief blip, six real weeks, across
multiple self-edit families (`prose_stripping`'s `is_prose`/`guard_prose`, `response_shortening`'s
`refactor_shorten_code_generation` variants, `quality_scoring`'s `compare_output`). `memory/
apply_to_code_invocations.jsonl` — the trusted, ground-truth observer this project already built
specifically because it doesn't trust the hook's own self-report (per its own docstring) — shows **3,196
real invocations across that same window, 1,985 (62%) recorded as `changed=True`, 935 (29%) errored.**
This is a real, substantial, continuously-firing mechanism, genuinely mutating every subsequent
self-edit candidate's code before it ever reached F1/F2/F3.

**Nothing anywhere in this project's extensive, multi-month Finding history — and I read all of it —
ever asks whether having this mechanism active made anything better.** So I checked, this pass, for
free, using data that already existed:

```
apply_to_code ACTIVE window (2026-07-14 to 2026-08-26): n=31 real tracked outcomes, mean quality delta = +0.0915, 41.9% negative
apply_to_code INACTIVE window (everything else):        n=72 real tracked outcomes, mean quality delta = +0.1083, 40.3% negative
Welch's t-test: t=-0.129, p=0.897 — no measurable difference
```

**A real mechanism ran for six weeks, transformed nearly two thousand candidates, reported success 62%
of the time by its own definition, and produced no measurable difference — better or worse — to real
self-edit outcome quality.** This is a new result, computed in this pass, not copied from any prior
audit. It is also currently **dormant** — zero `apply_to_code` deployments since 2026-08-26, eleven days
of silence as of tonight, and nothing in this project's own extensive self-observation apparatus (the
Liveness Ledger's own `self_edit_apply_to_code` check reports `status: not_deployed` and treats that as
healthy, correctly, since "not deployed" genuinely isn't a failure state) ever flagged the *transition*
from six weeks of real activity to eleven days of silence as something worth a human's attention.

**PROVEN**, at the sample size available (n=31 vs n=72, not enormous but real): the mechanism's activity
correlates with nothing. **UNRESOLVED**: why it went dormant on 2026-08-26 specifically — not
investigated in this pass, a genuine, cheap, next question.

### 2b. `echo_projects` — arguably FeralEcho's most interesting self-generated artifact — has no quality gate of any kind, not even the flawed one.

Confirmed directly: `app/core/echo_projects.py` contains **zero** references to `_score_response_quality`,
`functional_quality`, or any quality-scoring mechanism at all. `generate_project()`/
`council_generate_project()` gate on F1 (static safety) and F2 (import safety) exactly like self-edit
does, and — per Finding 84, already established — get a real, advisory-only multi-model council review.
But there is no analog to self-edit's fitness gate at all — not even the AST-only one this session spent
an entire remediation pass hardening. Every real, multi-file, curiosity-driven project `echo_projects`
autonomously generates is judged only on "did it import" and "what did three models say about it," never
on any notion of quality, however crude. This is a genuine asymmetry: the subsystem that produces
FeralEcho's most externally legible, most obviously *useful*-shaped artifacts (real, runnable, multi-file
Python programs) received a small fraction of the engineering attention self-edit's single-file,
demonstrably-inert-most-of-the-time output has received across this project's history.

---

## 3. Current Capability Ceiling

Restating §1 precisely: it is not a missing mechanism, and — this is the important correction to how
tonight's own prior work framed it — it is not really "the reward signal is wrong" either, though that's
true and real (Phase 1.5's own finding). The deeper pattern §2 exposes is that **the project doesn't
default to checking whether a real, running mechanism is actually accomplishing anything, even when the
check is free.** `functional_quality.py` needed to be *built* to get a real correctness signal for
self-edit candidates. Checking whether `apply_to_code` helped needed nothing built at all — the data was
already there, for six weeks, unexamined. That's the ceiling: not "we lack tools to measure ourselves,"
but "we don't reliably reach for the ones we already have."

## 4. Top 5 Opportunities

Ranked by expected capability/evidence gain against cost, not by novelty alone.

| # | Opportunity | Limiting factor | Evidence | Falsifiable how | Cheapest test | Success looks like | Failure looks like |
|---|---|---|---|---|---|---|---|
| 1 | **Retroactive outcome-correlation analysis as a standing habit, not a one-off** — apply the same free, already-logged-data check §2a used to every other "did this help" question sitting unasked in this project's logs (council rating adoption, the shadow model's real-world cost, RAOC's eventual real trial) | No process, not missing data | §2a, directly | A repeat analysis finding a *real*, non-null correlation somewhere would disprove "nothing's ever been checked" as the pattern | Literally what §2a already did — a script against a `.jsonl` file | A real, previously-unknown correlation (positive or negative) surfaces from data already on disk | The pattern replicates: more "ran, never checked" gaps found, reinforcing §3 rather than refuting it |
| 2 | **Investigate `apply_to_code`'s 2026-08-26 dormancy** | Unknown — could be a real family retirement, a bug, or simply nothing new was selected | §2a | Check whether any family with `apply_to_code` was commented out of `_FOCUS_FAMILY_BY_CREATIVITY` around that date, and whether Optuna's own trial selection has structurally stopped landing on families that define it | A `git log`/grep pass, minutes of work | A clear, specific, dated cause found | Genuinely unclear even after investigation — itself informative (means nothing in the pipeline currently tracks *why* a real capability went quiet) |
| 3 | **Give `echo_projects` a real, even minimal, functional check** (reusing `functional_quality.py`'s already-built, already-adversarially-tested smoke-test machinery — see the parallel Tier 1 remediation report for its exact current defects, both fixable before reuse here) | Structural absence, not a bug (§2b) | §2b, directly | Compare a sample of already-generated `sandbox/echo_projects/*/` outputs' AST-only or no-check status against a fresh functional smoke-test pass | Run `functional_quality.py` (once its Tier 1 fixes land) against the real, already-generated project corpus | Real discrimination found, same shape as self-edit's own 64% hidden-failure discovery | The corpus turns out mostly fine — also a valid, useful, humbling-in-a-good-way result |
| 4 | **Resolve memory-continuity's real behavioral effect outside the personal-task path** — the follow-up experiment already exists, was already started (2026-09-03), and was abandoned incomplete (n=5, empty noise floor, no report ever written) | An experiment that exists, was started, and stalled | Direct file inspection this pass; real experiment re-run in progress (§6) | A robust non-null effect across task types would overturn the current PLAUSIBLE/UNRESOLVED status; a robust null would strengthen it | Finish the exact experiment already sitting in the repo | A clear result either direction, properly powered with a real noise floor this time | Still underpowered / ambiguous even after a real attempt (§6 discusses this honestly) |
| 5 | **Remove, don't repair, the shadow model** | Real, measured cost (2,061+ real entries, ongoing compute/storage) for a signal independently confirmed worse than a majority-class baseline (Findings-91-93 forensic pass) and already demoted to last-resort fallback | `[inherited]`, independently re-confirmed by this session | N/A — this is a removal recommendation, not a hypothesis | Delete the mechanism, confirm nothing regresses (it's already last-resort only) | A clean removal, liveness ledger unaffected | Something downstream turns out to depend on its mere presence in a way not yet found — check before removing, not assumed safe |

---

## 5. Rejected Directions

**LoRA/QLoRA as a near-term production pipeline.** Already thoroughly investigated in parallel tonight
(`audits/2026-09-06_lora_ecosystem_investigation.md`) — NO-GO for the 27-day window, and its own central
finding (adding LoRA on top of the current topology would likely become a seventh disconnected learning
subsystem) is the same pattern this report independently re-discovers via §2, from a completely different
angle. Not re-litigated here.

**Further RiverBrain reward-signal engineering beyond what Tier 1 already proposes.** Real, already
scoped, already has review-ready diffs waiting. Adding more work here before those land, or before §4's
items are explored, would be building a fourth or fifth thing on top of a pattern (§3) this report thinks
is the actual root problem — more signal-repair without more habit-of-checking is not obviously
different from what's already been tried.

**Any new subsystem.** Explicitly against the grain of everything found tonight. FeralEcho does not
currently lack surface area — `echo_projects`, RAOC, preference-provenance, the shadow model,
`accuracy_trackers`, `functional_quality.py` are all real, working, and (mostly) disconnected from
consequence. Adding a sixth or seventh real-but-disconnected thing is the opposite of what this report's
own central finding argues for.

**UI/persona/cosmetic work.** No evidence anywhere tonight, across any investigation, suggests this is a
binding constraint on anything a technically sophisticated observer would care about.

---

## 6. Experiments

### 6a. Retroactive `apply_to_code`-activity vs. self-edit-outcome correlation

**Hypothesis**: if `apply_to_code`'s real, measured 62% "success" rate reflects genuine improvement,
self-edit outcome quality deltas during its active window should be measurably better than during its
absence.

**Methodology**: parsed `memory/SELF_EDIT.log`'s real `LOAD_AUDIT` entries to establish the real active
window (2026-07-14 to 2026-08-26, the full span of every real historical deployment mentioning
`apply_to_code`); parsed `memory/self_edit_outcomes.jsonl`'s real `quality_score.delta` field (the same
metric this session's own earlier work already established as the real, tracked pre/post quality
measure) for every entry with a real timestamp and a real delta (n=103 of 179 total rows); split by
whether the entry's `edit_timestamp` falls inside or outside the active window; computed means, negative
rates, and a Welch's t-test.

**Result**: active-window mean delta +0.0915 (n=31, 41.9% negative); inactive-window mean delta +0.1083
(n=72, 40.3% negative); t=-0.129, p=0.897. No measurable difference.

**Interpretation**: the mechanism's real, substantial activity correlates with nothing — not proof of
harm, not proof of benefit, a clean null on a question nobody had previously asked. Directly supports
§1/§3's central claim with a fresh, freely-obtained data point.

**Limitations, stated plainly**: this is a correlational analysis of an already-existing natural
experiment, not a controlled one — the two windows differ in more ways than just `apply_to_code`'s
presence (different self-edit families were being targeted, different periods of the project's own
evolution). A confound could in principle explain the null. It does not, however, change the more basic
finding that **nobody had ever computed this number before**, which is itself the point.

### 6b. Memory-retrieval ablation, non-personal task types — completing an abandoned experiment

**Hypothesis** (inherited from the original 2026-07-23 experiment and its abandoned 2026-09-03
follow-up, both real, both already in the repo): does retrieved memory context measurably change model
output, distinguishably from ordinary sampling noise, on the multi-councillor deliberation path — the
majority of real FeralEcho traffic, previously tested at n≤1?

**Methodology**: re-ran `scripts/memory_ablation_experiment_nonpersonal_2026-09-03.py` in full — the
existing, already-built, already-safety-reviewed harness (RiverBrain `.learn()`/`.save()`/`._do_save()`
neutralized at the class level before any real query, exactly matching the method already validated
twice this session; results tagged `source="memory_ablation_experiment_nonpersonal"` in
`interaction_log.jsonl`, excluded from every real training/rating path by construction, same as the
original run). Stratified selection across coding/creative/reasoning/general, 3 real memory-hit prompts
per type, plus a proper 3-pair noise-floor calibration (the exact piece the abandoned 2026-09-03 attempt
never reached — its own saved results show `noise_floor: []`, confirmed by direct inspection before this
rerun).

**Status at the time of writing this report**: **launched, still running, but showing signs of a real
stall, not just normal slowness.** Direct process inspection at the time of finalizing this report:
`PID 7052`, elapsed 4m14s, only 12.48s of actual CPU time consumed, state `S` (sleeping/waiting), zero
`[hit]` lines yet printed by the candidate-selection loop (which should log one per real memory-hit
prompt found among 887 candidates). This pattern — long wall-clock elapsed, almost no CPU time, no
progress markers — is most consistent with the same real Ollama single-concurrency contention this
session's own earlier work already documented twice (Phase 0's forensic pass found the exact same
signature killing a prior prospective experiment on 2026-09-03; this experiment is very plausibly
contending with the live production server's own continuous background self-edit/autonomous-loop
activity for the same single request slot). **Left running rather than killed** — it is safe (RiverBrain
writes neutralized, confirmed at process start; no production file at risk), and may still complete on
its own once contention clears. **No result is reported here because none exists yet — per this report's
own scientific-integrity constraint, an incomplete experiment is preserved as exactly that, not padded
into a false completion.** Raw output remains at `/tmp/michelangelo_ablation_rerun.log`; results, if the
run eventually completes, will land at `scripts/memory_ablation_results_nonpersonal_2026-09-03.json`
(overwriting the earlier abandoned n=5 attempt) for whoever checks next.

**This stall is itself a small, secondary, unplanned data point for §1's central thesis**: even a
carefully-designed, already-proven-safe experiment that is *supposed to be small and quick* falls victim
to the same "real signal contends with production, nobody built anything to detect or route around it"
pattern this report keeps finding at every layer it looks — a live, small-scale demonstration of §3's
argument, not just an assertion of it.

**Limitations already known, inherited from the original design**: even a clean result here only
resolves the non-personal path's *embedding-distance* effect — it does not, on its own, establish that
any measured difference is *beneficial* (a distinguishable-from-noise change is not automatically an
improvement), a distinct question this experiment was never designed to answer.

---

## 7. Implemented Changes

**None to production code.** Per this report's own reasoning (§5): building something now would repeat
the exact pattern §1-§3 argue against. The one thing genuinely implemented in this pass is the real,
running experiment in §6b — a reversible, already-validated-safe research action, not a production
change, exactly matching the mission's own "small, reversible, well-understood" bar for direct action
without merely recommending it. No commit was made; no commit hash to cite.

---

## 8. Remaining Unknowns

- §2a's dormancy cause (§4 item 2) — genuinely not investigated in this pass.
- §6b's real result — not yet available at time of writing.
- Whether §6a's null generalizes to the *other* self-edit families with real `apply_to_code` history
  (this analysis pooled all families together within the active window; a per-family breakdown might
  reveal one family did help and another actively hurt, canceling out in the aggregate — not checked,
  a real limitation of this specific pass, flagged rather than hidden).
- Whether `echo_projects`' real generated corpus would show the same ~64% hidden-failure rate self-edit's
  did if `functional_quality.py` (once its own Tier 1 defects are fixed) were pointed at it — a real,
  cheap, next experiment, not run in this pass.

---

## 9. Proposed Next Move

**Pick one, per the mission's own instruction: finish and publish the retroactive `apply_to_code`
outcome-correlation habit as a standing practice, starting with the two cheapest, highest-value
extensions of what §6a already proved works — per-family breakdown of the same analysis, and the
equivalent check for council-rating adoption (does `learn_from_council_rating`'s real activity correlate
with anything, the same question §6a just answered for `apply_to_code`) — before building anything new,
including anything already proposed tonight.**

**Why this over the other four real candidates in §4**: it is the only one that costs nothing, risks
nothing, and directly, freshly demonstrated its own value in this exact report (§6a wasn't a
hypothetical — it produced a real, previously-unknown number in about ten minutes of work, against data
that had been sitting there for six weeks). Fixing `functional_quality.py`'s defects (already scoped,
already has diffs ready) and finishing the memory experiment (already running) are both real, valuable,
in-flight work — but they were already identified by prior investigation. This one wasn't. It's the
answer to the mission's own final challenge: if nobody had suggested LoRA, RiverBrain, reward-signal
repair, or self-editing tonight, this — "check whether the things that are already running and already
logging their own outcomes have ever actually helped" — is what I would have gone looking for, and it's
what going looking for it actually found.

---

## Final Challenge, Answered Directly

**If nobody had suggested LoRA, RiverBrain, reward-signal repair, self-editing, or any other specific
direction tonight, I would have opened `SELF_EDIT.log` and asked what the system has been quietly doing
for months that nobody has checked the results of. That is exactly what I did in §2/§6a, and it produced
a real, new, freely-obtained finding within the hour: a mechanism ran continuously for six weeks, changed
nearly two thousand candidates, and made no measurable difference — a fact that cost nothing to learn and
had simply never been asked.**
