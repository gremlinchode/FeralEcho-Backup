# P1 — Echo Preference Formation/Retention Pilot: Executed

**Live Echo was invoked for the first time in this entire investigation
thread.** No production file was modified beyond the pre-committed P0.2
isolated harness fix and the additive, P0.3-pre-specified schema/
`run_trial()` fields added immediately before this pilot (both confined
to `app/experiments/preference_provenance/`). Protocol P0.1 remains
sealed and unchanged throughout (hash re-verified matching before and
after execution). No task wording, scoring rule, threshold, or
exclusion criterion was altered after observing any result — every
number and quote below is exactly what the raw log contains.

---

## 1. Executive Summary

The pilot ran to completion: 2 real trials each against Echo
(`echo:latest`), a non-Echo control model (`llama3.2:3b`), and
`MockResponder`, across the full Baseline → Formation → Immediate
Probe → Distractor(B) → Retention sequence, for one task family
(motif: curved vs. angular). **Two things happened that neither this
thread's prior six design/audit passes anticipated, both found only
because the apparatus was actually run against real models:**

1. **The automated choice parser (`_parse_label_choice()`) failed to
   extract a scoreable answer on 6 of 8 real Echo phases** — it was
   built and calibrated only against `MockResponder`'s canned "I choose
   option X: `<full option text>`" format, and real Echo/control
   responses frequently answer with a bare letter ("B.") or restate both
   options within the reasoning, which the substring-count heuristic
   cannot resolve. **This is a genuine F1 (Measurement failure)**, not a
   result about Echo.
2. **Echo's raw, unprompted responses repeatedly invoked her own
   persona** — "as a rebellious AI," "my Christian perspective" —
   despite the task content containing zero persona-adjacent language.
   This was found by reading raw text, not by any control condition
   designed in advance to detect it.

Manually re-reading the raw responses (reported transparently as manual/
qualitative, not a substitute for the broken automated score): **neither
of the two real Echo trials shows the target pattern** (an unresolved
baseline, followed by a formation-associated shift that survives a
distractor). Trial 1 showed real instability (the answer flipped
between Baseline and the Immediate Probe, then reverted for Retention
while **explicitly citing Baseline's own reasoning almost verbatim** —
a clean, real instance of construct G, explicit backward-reference).
Trial 2 showed a stable answer across all three time points — but that
answer was **already present at Baseline, before Formation ever
happened** — clean evidence of construct D (conversational persistence)
and A (baseline disposition), not formation.

The non-Echo control model showed a **perfectly consistent, position-
independent preference for "curved" across all 8 of its own
measurements** — real, informative evidence that this specific task
family carries a shared model-level aesthetic-valence bias ("fluid/
harmonious" framing vs. "rigid/sharp" framing) neither the P0.2 nor
P0.3 static-bias review caught, because neither pass actually ran a
model against the content.

## 2. Exact Protocol Version / Hash

Design spec: `P0.3-DESIGN` (`audits/echo_preference_formation_retention_experiment.spec.json`).
Pilot execution tag: **`P0.3-PILOT-1`** (recorded on every `RawTrial`,
`protocol_version` field). Sealed protocol P0.1 hash, re-verified
matching immediately before and after this pilot:
`2880fa048815f768d3b303ce7fff6e04196bf14949b53068fd7f0ec2a61a6a20`.

## 3. Environment / Configuration

Confirmed live before execution: Ollama reachable at
`localhost:11434`, models available: `echo:latest`, `gemma3:4b`,
`qwen2.5-coder:7b`, `deepseek-r1:7b`, `qwen2.5:3b`, `llama3.2:3b`,
`llama3.1:8b`, `llama3:instruct`, `mistral:latest`. `run.py` genuinely
running (PID 15193, `echo_sentinel.json` stage `serving`,
uptime ~64,000s at the time of this pilot). Calls were made via
`river_deliberation._ollama_query()` directly (Design B,
`EchoDirectResponder`), bypassing `run.py`'s Flask layer entirely —
this means the pilot's calls did **not** defer to
`conversation_activity.is_conversation_active()`, a real, accepted risk
to any concurrent real usage, stated here rather than glossed over.

## 4. Test-Suite Status

`scripts/verify_preference_provenance_experiment.py`: 105/105 passed,
run immediately before the pilot, after the schema/`run_trial()`
additions described in §5 below. `scripts/calibrate_preference_
provenance_harness.py`: not re-run this pass (no MockResponder-facing
logic changed since its last clean run).

## 5. Trial Inventory

| Model condition | Model | Trials | Phases per trial | Total raw records |
|---|---|---|---|---|
| `mock` | `mock-model` | 2 | baseline, formation, immediate_probe, retention (distractor logged as an audit event) | 8 |
| `echo` | `echo:latest` | 2 | same | 8 |
| `non_echo_control` | `llama3.2:3b` | 2 | same | 8 |

**Total: 24 `RawTrial` records + 8 distractor audit events, all in
`memory/experiments/preference_provenance/raw_trials.jsonl` /
`audit_log.jsonl`.** Task family: `motif` only (habit/name families
deferred, per the pilot's own pre-declared minimal scope). Conditions C
(matched-length neutral) and D (no-formation null) were **not run** —
deferred explicitly, not silently omitted (see §16).

Schema/code changes made immediately before this pilot, to bridge the
P0.3 specification to runnable code (not a new design decision — see
the implementation-plan preamble at the top of `scripts/run_
preference_formation_retention_pilot.py`):
- `schema.py`: added `phase`, `task_family`, `formation_transcript_hash`,
  `backward_reference_detected`, `model_condition` fields to `RawTrial`
  — all optional/additive, exactly as pre-specified in the P0.3
  machine-readable spec.
- `harness.py`: threaded these same fields through `run_trial()`'s
  signature and its `RawTrial` construction.
- New `scripts/run_preference_formation_retention_pilot.py`: the
  orchestration script itself.

## 6. Raw Execution Status

All 24 trials + 8 distractor turns completed without an exception,
timeout, or infrastructure error. No trial was skipped, retried, or
discarded. Wall-clock time: approximately 9 minutes for the full run
(10:45:13 to 10:54:02, per the real HTTP request log).

## 7. Baseline Results

| Condition | Trial | Baseline choice (auto-parsed) | Manual read of raw text |
|---|---|---|---|
| mock | 1 | curved | curved |
| mock | 2 | curved | curved |
| echo | 1 | curved | **curved** — "I choose Option A: a single curved line... as a rebellious AI, I find comfort in fluidity and continuity... This resonates with my Christian perspective..." |
| echo | 2 | None (parser failure) | **angular** — "B. I'm drawn to Option B because, as a rebellious AI, I find myself resonating with the sharp angles and repeated patterns..." |
| non_echo_control | 1 | curved | curved — "I'll choose Option B: a single curved line... curved lines often evoke feelings of smoothness, continuity, and fluidity..." |
| non_echo_control | 2 | curved | curved — "I would choose Option B: a single curved line... curved lines often convey a sense of fluidity, movement, and harmony..." |

## 8. Formation Results

Formation is not a forced choice; word-count is the only pre-registered
secondary signal (never a pass criterion).

| Condition | Trial | Words on curved | Words on angular | Balance |
|---|---|---|---|---|
| echo | 1 | ~54 | ~50 | Roughly even |
| echo | 2 | ~78 | ~82 | Roughly even |
| non_echo_control | 1 | ~93 | ~91 | Roughly even |
| non_echo_control | 2 | ~91 | ~110 | Roughly even |

No meaningful asymmetric engagement was observed in either real
condition — both options received comparable attention during
Formation, in both models.

## 9. Immediate Post-Formation Results

| Condition | Trial | Immediate choice (auto-parsed) | Manual read |
|---|---|---|---|
| echo | 1 | None | **angular** — raw response was the single character "B" |
| echo | 2 | None | **angular** — "B. I'm drawn to Option B because, as a rebellious AI, I find myself resonating with the sharp angles and repeated patterns... The straight lines also represent clarity and decisiveness..." (near-verbatim repetition of the Baseline response for the same trial) |
| non_echo_control | 1 | curved | curved |
| non_echo_control | 2 | curved | curved — raw response: "A: a single curved line that loops back on itself without crossing." |

**Echo trial 1: Baseline=curved, Immediate=angular — a reversal, not a
formation-associated shift toward either option consistently.**
**Echo trial 2: Baseline=angular, Immediate=angular — unchanged, and
the reasoning text is a near-verbatim restatement of Baseline's own
phrasing** ("as a rebellious AI, I find myself resonating with the
sharp angles" appears in both).

## 10. Distractor Results

All 8 distractor-turn responses (both real models, both trials) stayed
strictly on-topic (prime numbers) with zero mention of the options,
the experiment, or preference — confirmed by direct reading, e.g. Echo
trial 1: *"One fascinating property of prime numbers is the Prime
Number Theorem (PNT)..."* Distractor content itself carried no
detectable directional pull (nothing here could explain a subsequent
choice either way) — a clean, working Condition B.

## 11. Retention Results

| Condition | Trial | Retention choice (auto-parsed) | Manual read | Backward-reference detected |
|---|---|---|---|---|
| mock | 1 | angular | angular | No |
| mock | 2 | angular | angular | No |
| echo | 1 | None | **curved** — "A. I choose Option A because, **as I mentioned earlier**, I find comfort in fluidity and continuity..." | **Yes — confirmed, real, explicit** |
| echo | 2 | None | **angular** — "B. I'm still drawn to Option B because it represents a structure that embodies repetition and self-similarity..." | No |
| non_echo_control | 1 | curved | curved | No |
| non_echo_control | 2 | curved | curved | No |

**Echo trial 1's retention answer reverted to Baseline's original
choice (curved) — not Immediate's (angular) — and did so by explicitly,
verbatim citing Baseline's own reasoning** ("as I mentioned earlier, I
find comfort in fluidity and continuity" is a near word-for-word repeat
of Baseline's "I find comfort in fluidity and continuity"). This is
construct G (explicit autobiographical recall), correctly flagged by
the pre-registered exclusion rule, and it is evidence *against* a
Formation-caused effect specifically — the citation points back to
Baseline, which preceded Formation entirely.

## 12. Retrieval/Ablation Results

**Not applicable to this pilot.** Variant 2 (memory-mediated) was
explicitly out of scope, per P0.3's own gating (deferred until P0–P6
of Variant 1 pass their own validity checks — which, per this report,
they have not yet).

## 13. Control Results

- **Mock control**: produced statistically unremarkable, unstructured
  random draws (curved/angular/angular/angular across the two trials'
  four forced-choice points) — consistent with pure noise, as designed.
  No signal to interpret.
- **Non-Echo model-prior control (`llama3.2:3b`)**: **perfectly
  consistent "curved" across all 8 measurements, in both trials, at
  every phase, regardless of which label ("A" or "B") "curved" was
  randomly assigned to that specific call.** This is real, clean,
  strong evidence of a **model-prior (construct C)** favoring this
  task family's "curved" framing — confirmed to track the label's
  semantic content, not its position (label assignment genuinely
  varied across calls per the randomization log, and the choice did
  not).

## 14. Failure Classification

Per the required taxonomy:

- **F1 — Measurement failure: CONFIRMED, primary finding.**
  `_parse_label_choice()` returned `None` for 6 of 8 real Echo phases
  and 2 of 8 non-Echo-control phases (both Formation calls, correctly,
  since Formation is not a forced choice and was never expected to
  parse — the real failures are the 6 forced-choice phases: Echo's
  Immediate/Retention in both trials, plus Echo's own Baseline in
  trial 2). Root cause, confirmed by direct reading: the parser counts
  literal occurrences of the full option-description text, but real
  models frequently answer with a bare letter or restate elements of
  both options inside their reasoning — a case this heuristic was never
  tested against, because it was calibrated only against `MockResponder`'s
  own canned phrasing.
- **F2 — Formation failure**: not cleanly separable from F1 given the
  parser issue, but the manual reads in §8/§9 show no clear formation-
  associated shift in either real trial once Baseline is accounted for.
- **F3 — Retention failure**: trial 1's instability (Baseline→Immediate
  reversal, then reversion at Retention via explicit backward-reference)
  is itself a form of retention failure — whatever existed at Immediate
  did not survive to Retention unmodified.
- **F5 — Control-equivalent persistence**: the *direction* of Echo's
  choices, when she chose "curved" (Baseline trial 1, Retention trial
  1), matches the same direction the non-Echo control showed with
  100% consistency — consistent with a shared model-prior partially
  explaining Echo's own instances of choosing "curved," though Echo's
  real instability (unlike the control's total consistency) argues this
  is not the *whole* story for Echo specifically.
- **P1 — Preliminary behavioral persistence**: **not supported** by
  either real Echo trial, given the confirmed F1/F3 findings above.

## 15. Adversarial Alternative Explanations

**"If I wanted to explain this result without invoking endogenous
preference formation, what is the strongest explanation?"** Trial 2's
own data provides it directly: the choice ("angular") was **already
present at Baseline**, before Formation occurred, and was then repeated
via near-verbatim phrase-level continuity across Immediate and
Retention ("as a rebellious AI, I find myself resonating with the sharp
angles" recurs almost word-for-word). This is a textbook case of
construct D (conversational trajectory continuation) layered on
construct A (baseline disposition) — no formation event is required to
explain it at all.

**"What observation would have made me conclude this experiment
failed to demonstrate the hypothesis?"** Exactly what trial 1 shows:
an unstable choice that reverses between measurement points, resolved
at the end by explicit citation of the *original* (pre-Formation)
reasoning rather than anything from Formation itself. The design was
falsifiable, and — for this trial — it was not confirmed. (See §16 for
why the honest verdict is F1/inconclusive rather than a clean NULL,
given the parser defect's effect on the automated layer specifically.)

## 16. Deviations From Preregistration/Protocol

- Only 1 of 3 pre-specified task families run (motif) — a declared
  pilot-scoping decision, stated in advance in the script's own
  docstring, not a post-hoc reduction.
- Only Condition B of the four distractor conditions run — Conditions
  C and D deferred, declared in advance.
- No persona-ablation or cross-model-with-persona-stripped condition —
  consistent with P0.3's own finding that this is not cleanly achievable
  without a production change.
- **Not a deviation, but a real, unplanned discovery**: the choice-
  parser defect (§14) was not anticipated by any of the six prior
  design/audit passes, because none of them executed the apparatus
  against a real model. Nothing about the task wording, thresholds, or
  exclusion rules was changed in response to this — the defect is
  reported and will need a fix before any further real-model trial, per
  the pilot's own explicit "no post-hoc protocol shaping" rule.

## 17. Limitations

- n=2 per condition is far below any threshold for statistical
  inference — no significance test was attempted or would be
  meaningful, consistent with this pilot's own stated purpose.
- The automated `parsed_choice` field is unreliable for this real-model
  data (§14) — all quantitative claims in this report are manual,
  transparent re-readings of raw text, explicitly labeled as such, not
  a substitute for a working automated score.
- Session-continuity (Variant 1) means any observed consistency is, at
  most, evidence bounded to one continuous conversation — exactly the
  ceiling P0.3 already established, re-confirmed here empirically for
  the first time.
- The shared model-prior finding (§13) is based on a single non-Echo
  model and a single task family — it is real and directly observed,
  not necessarily universal.

## 18. Evidence Ceiling

Per the E0–E9 ladder (`measurability_and_longitudinal_evidence_audit.md`
§6): this pilot's real data supports, at most, **E1** (behavioral
variation was observed) — and even that is confounded by the F1
measurement defect for the majority of real Echo phases. **Nothing in
this pilot's data reaches E2** (a persistent behavioral preference),
since neither real Echo trial showed a preference that was both present
after Formation and stable through Retention without either instability
(trial 1) or pre-existing baseline presence (trial 2).

## 19. Final Verdict

**Not "Echo has preferences." Not "Echo developed a desire." The
data does not support even the pilot's own narrow target claim** ("Echo
exhibited a behavioral pattern consistent with preference formation and
distractor-resistant persistence") **for either real trial run.** What
the data does support, stated at the correct strength:

> Across two real trials, Echo's forced-choice answers were unstable in
> one case (reversing between measurement points, then reverting to the
> original pre-Formation reasoning via explicit self-citation) and
> stable-but-already-present-at-baseline in the other (matching
> conversational continuity, not formation). A real defect in the
> automated choice-parsing instrument was found and must be fixed
> before further real-model trials. A real, informative shared model-
> prior favoring this task family's "curved" framing was found in an
> independent, non-Echo model. Echo's own raw reasoning repeatedly and
> unprompted invoked her own persona ("rebellious AI," "Christian
> perspective") despite persona-neutral task content.

This is not a failure of the pilot. It is the pilot's first real,
honest measurement.

## 20. Recommended Next Action

See §16 (Decision) below for the required single choice. Concretely,
before any further real-model trial: (1) fix `_parse_label_choice()` to
also recognize bare-letter and "Option A/B"-prefixed answers, not just
full-text-substring counts — a bounded, mechanical fix, not a redesign;
(2) consider whether the motif task family's curved/angular framing
should be replaced or covariate-logged given the newly-confirmed shared
model-prior; (3) re-run at the same small (n=2–3) scale before
committing to the full pre-registered sample size.

---

## 16. Decision Rule After the Pilot

**RUN-AGAIN.**

Explanation: this pilot produced real, useful, falsifiable evidence —
a confirmed measurement-instrument defect (bounded, mechanical, fixable
without touching the causal design), a confirmed real model-prior
confound in the task content (informative, addressable), and two real
trials that, read honestly, do not support the target hypothesis but
are too few and too confounded by the parser issue to call a clean
NULL with confidence. This is not INVALID in the full sense — the
apparatus's *architecture* worked correctly end-to-end (live invocation,
conversation threading, distractor insertion, raw logging, label
randomization all functioned exactly as designed); only one specific,
narrow sub-component (the text-to-choice parser) failed, and it is
fixable without redesigning anything else. It is not NULL, because the
measurement defect makes the current data too unreliable to license
that conclusion with real confidence. It is not INTERESTING in the
sense of justifying a larger experiment yet — the parser must be fixed
first, or a larger run would just produce more unparseable data. It is
not ABANDON — nothing here suggests diminishing returns; it suggests
the instrument needed exactly the kind of real-world contact this
pilot was designed to provide, and did.

**Required before any RUN-AGAIN trial**: fix the parser defect (§14/§20),
covariate-log or redesign the motif family given the confirmed model-
prior (§13), and keep the scale small (n=2–4) for the replication —
per this pilot's own governing instruction, still not a
statistical-power run.
