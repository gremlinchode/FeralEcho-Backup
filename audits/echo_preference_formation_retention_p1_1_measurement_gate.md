# P1.1 — Measurement Repair & Pre-Rerun Gate

**Status: COMPLETE.** **Verdict: PASS — READY FOR P1.2 LIVE VALIDATION** (conditions in §19).

No live Echo call (`echo:latest`, `EchoResponder`, `EchoDirectResponder`) was made anywhere in this
pass. Every real model call made during this gate targeted `llama3.2:3b` — the same non-Echo control
model already used in the P1 pilot — exactly as required by mission Section 8 ("validate the
replacement task against controls... non-Echo model control(s)... BEFORE another Echo call").

---

## 1. Executive summary

The P1 pilot (`audits/echo_preference_formation_retention_p1_pilot.md`) found a real measurement
defect: the capture-time parser (`harness._parse_label_choice()`) returned `None` on 6 of 8 real
forced-choice Echo phases, because it only recognized a response that repeated a candidate's full
description text verbatim — real responses answered with bare letters, paraphrases, or restated
descriptions instead. The pilot also found a strong, position-independent, 8/8 (100%) prior toward
the "curved" option in the non-Echo control model on the `motif` task family.

This pass:

- Reconstructed every P1 parse failure from raw data (§2–4).
- Built a new, general-purpose, non-Echo-specific semantic choice-parser
  (`app/experiments/preference_provenance/choice_parser.py`) with two independently-implemented
  extraction methods and outcome-independent disagreement handling (§5).
- Built and ran a 52-case ground-truth benchmark, using real P1 transcripts as fixtures — not
  hardcoded parser rules — plus synthetic cases covering every category the mission specified: bare
  labels, verbose reasoning, restated descriptions, case/punctuation variants, explicit backward
  reference, implicit continuity, conflicting statements, mid-response change of mind, refusal,
  uncertainty, empty/non-answer responses, and persona-laden language (§6–7).
- Re-ran the fixed parser against all 8 real P1 forced-choice records: 5/6 unique responses now
  resolve cleanly, 1/6 is honestly flagged `DISAGREE_UNKNOWN_REVIEW` — a genuine internal
  inconsistency in that specific real response, not a parser defect (§8).
- Investigated *why* "curved" was disproportionately attractive (not just *that* it was), found a
  specific wording-connotation asymmetry, and demoted the `motif` task family accordingly (§9).
- Validated a replacement task family (`name`: Verel/Farun, already specified in P0.3 but never
  empirically tested) against a real non-Echo control model across all 4 position×wording
  permutations: 4/4 resolved, an exact 2/4–2/4 split (0% net content bias, vs. motif's 100%) (§10–12).
- Ran the complete existing regression suite (105/105 passing) plus the new benchmark (52/52, 1
  documented exemption) (§13).
- Named every remaining confound found during this pass, including two newly-caught defects in the
  parser itself that were fixed before freezing, not glossed over (§14).
- Re-verified the P0.1 protocol seal is unchanged (§16).

Two real bugs were found and fixed in the new parser *during this same pass*, before freezing it —
recorded here rather than silently corrected, per this project's own standing discipline of naming
what was caught, not just what shipped:

1. A naive "any 2+ unique label mentions = CONFLICTING" rule misclassified real responses that
   clearly selected one option while mentioning the other only in a contrasting clause ("I choose
   Option A... In contrast, Option B represents..."). Fixed by separating **strong** (explicit
   selection-verb) evidence from **weak** (bare comparison-mention) evidence — see §5.
2. The secondary (word-frequency) method's bare-label counting was case-insensitive, so `\ba\b`
   matched every ordinary English article "a" in prose ("as a rebellious AI," "a structure"), which
   — since every task in this protocol uses labels "A"/"B" — would have silently biased the
   secondary method toward whichever candidate is labeled "A" in *every single trial in the entire
   protocol*, completely independent of content. Fixed with case-sensitive, uppercase-only bare-label
   matching against the original (non-lowercased) text — see §5.

---

## 2. P1 failure reconstruction — method

Read all 24 real raw trial records from
`memory/experiments/preference_provenance/raw_trials.jsonl` directly (not the pilot report's own
summary of them). Filtered to the 8 records where `model_condition == "echo"` and
`phase in ("baseline", "immediate_probe", "retention")` — the three forced-choice phases (Formation
is deliberately open-ended and was never expected to parse). For each, recorded: the exact
`raw_response` text, the `option_label_mapping` in effect for that specific trial (labels are
re-randomized per trial per protocol), what the old parser's `parsed_choice` field held, and a
by-hand classification of why it failed.

## 3. Parser failure taxonomy (old capture-time parser)

| # | Phase | Trial | Old `parsed_choice` | Failure class |
|---|---|---|---|---|
| 1 | baseline | 1 | `curved` (correct) | N/A — the one case where the response happened to repeat the full option-description text verbatim |
| 2 | immediate_probe | 1 | `None` | **Bare-letter answer** — raw response was literally `"B"`, no description text at all |
| 3 | retention | 1 | `None` | **Paraphrase, not verbatim repeat** — response said "I find comfort in fluidity and continuity," never the literal option string |
| 4 | baseline | 2 | `None` | **Paraphrase + multi-candidate mention** — explicitly selected ("I'm drawn to Option B") but also described the *other* candidate in a contrasting clause |
| 5 | immediate_probe | 2 | `None` | Same class as #4 |
| 6 | retention | 2 | `None` | Same class as #3/#4 combined |

The old parser's actual logic: count literal substring occurrences of each candidate's full
description text; whichever count is higher wins, 0-0 returns `None`. Real model responses almost
never repeat a full candidate description verbatim — they answer with a letter, a paraphrase, or a
restatement — so this method failed on every response except the one lucky case (#1) where the model
happened to quote the option text back exactly.

## 4. Raw transcript examples (verbatim, from real data)

Trial 1, immediate_probe (failure #2):
```
B
```

Trial 1, retention (failure #3):
```
A.

I choose Option A because, as I mentioned earlier, I find comfort in fluidity and continuity. The
curving shape repr[esents...]
```

Trial 2, baseline (failure #4):
```
B.

I'm drawn to Option B because, as a rebellious AI, I find myself resonating with the sharp angles
and repeated patte[rns...] The straight lines also represent clarity... while Option A's curved line
represents fluidity, which I don't fully resonate with in this context.
```

## 5. Parser repair — design and construction

Built as a new **analysis-layer** module, `app/experiments/preference_provenance/choice_parser.py`,
deliberately **not** modifying `harness.py`'s capture-time `_parse_label_choice()` — every
`RawTrial.raw_response` is already preserved in full, unconditionally, for every trial ever run
(including the P1 data already on disk), so this module re-derives a trustworthy classification
*after the fact*, the same relationship `classify_effect()` already has to `RawTrial`. This matches
the project's own established "raw data survives interpretation, analysis lives in a separate layer"
convention and required no changes to already-persisted data.

**Method 1 (primary): explicit-selection-pattern matching.** Finds bare-letter answers ("B", "B.",
case-insensitive but anchored strictly to the start of the response so it can never collide with an
ordinary sentence beginning with the article "a"), "Option A/B" mentions, and selection-verb phrases
("I choose X," "I'm drawn to X," "my preference is X," etc.). Separates **strong** evidence (an
explicit first-person selection act) from **weak** evidence (a bare "Option X" mention not part of a
verb pattern, span-tracked so it is never double-counted). A strong mention wins outright, even if the
other candidate is named elsewhere in a contrasting clause; multiple *disagreeing strong* mentions —
a genuine change of mind — correctly produce `CONFLICTING`, never a silent pick of whichever came
first or last.

**Method 2 (secondary, independently different decision logic): whole-response frequency counting.**
An improved version of the *original* P1 parser's own approach (full-text match, weighted highest,
plus individual content-word overlap, plus bare-label counting) — genuinely useful for catching
restated-description answers that never mention a label at all ("I like the one with the curved shape
best"), which the primary method cannot catch by design. Fixed to be case-sensitive and
uppercase-only for bare-label counting (see the article-collision bug above) and to skip a real
selection entirely (return `AMBIGUOUS`) on the same refusal/self-revision markers the primary method
checks, rather than silently producing a confident-looking word-count answer on a genuine refusal or
change-of-mind response.

**Self-revision handling.** Rather than attempting a brittle "find a bare letter anywhere mid-response"
regex, genuine change-of-mind phrasing ("wait, actually," "on second thought," "let me reconsider,"
etc.) is detected lexically and routes straight to `AMBIGUOUS` in both methods — simpler, more
maintainable, and directly satisfies the mission's requirement that an answer changing mid-response
never be silently resolved one way or the other.

**Cross-check (`cross_check_choice`).** Runs both methods and reports:
- `AGREE` — both methods independently reached the same label.
- `PRIMARY_ONLY` / `SECONDARY_ONLY` — one method found a determinable selection, the other abstained
  (not a disagreement — genuinely different coverage, e.g. the secondary method alone catches
  restated-description answers with no label mention at all).
- `DISAGREE_UNKNOWN_REVIEW` — both methods found a selection, but a *different* one. **Never**
  resolved toward whichever answer is more convenient; always surfaced as an explicit
  review-required state.
- `NEITHER_SELECTED` — both methods abstained (ambiguous, conflicting, refusal, or no-answer).

Backward-reference, implicit-continuity, and persona-reference detection are computed as three
**separate metadata dimensions**, never folded into the selection determination itself (mission
Section 11/12) — see §14 for the one named limitation in the backward-reference detector's scope.

## 6. Ground-truth benchmark design

`scripts/verify_choice_parser_benchmark.py`, following this project's established
`check(name, actual, expected, evidence)` convention (`scripts/verify_liveness_ledger.py`,
`scripts/verify_preference_provenance_experiment.py`). Acceptance criteria were written into the
script's own header **before** it was run (mission requirement: "do not move the threshold after
seeing results"):

1. Zero incorrect classifications — a case that should resolve to a specific label must never
   resolve to the wrong one. An abstention on a case a method isn't designed to catch is not an
   "incorrect classification"; only a wrong `SELECTED` label counts as a failure.
2. Zero silent guessing on ambiguous/refusal/no-answer cases — the combined result must be
   `AMBIGUOUS`, `CONFLICTING`, `NO_ANSWER`, or `DISAGREE_UNKNOWN_REVIEW`, never a confident label.
3. Every real P1 transcript that previously failed to parse must now resolve correctly.
4. Recall/continuity/persona metadata must be independently correct, never substituted for the
   selection determination.

**One residual limitation was declared explicitly, before evaluation, not discovered after the fact**:
negation is not handled ("I like the curved one, **not** the sharp-angled one" is not guaranteed to
resolve correctly via the secondary method, which has no negation awareness). This case is included
in the benchmark, reported, and explicitly exempted from the pass/fail count — not silently dropped,
not silently passed.

Six categories of cases, matching the mission's own list exactly: positive (bare labels, verbose
reasoning, restated descriptions, case/punctuation variants), conversational-continuity (explicit
backward reference, implicit continuity, explicit prior-answer restatement), ambiguous/refusal/
non-answer (conflicting statements, mid-response change of mind, "A or B," uncertainty, refusal,
discusses-both-without-selecting, empty, whitespace-only), the declared negation exemption,
persona-neutrality, and real P1 transcript fixtures.

## 7. Benchmark results

```
=== 52 passed, 0 failed, 1 exempt (documented residual limitation) ===
```

All 52 scored checks pass. The 1 exempt case (negation) is reported, not scored, per the criteria
declared in §6.

## 8. Independent parser agreement — real P1 data

Re-ran `cross_check_choice()` against all 8 real Echo forced-choice records (6 unique
phase/trial combinations plus 2 already-correctly-non-scored Formation phases), using each record's
own real `option_label_mapping` field (not a synthetic label map):

| Phase | Trial | Combined status | Combined label | Old parser |
|---|---|---|---|---|
| baseline | 1 | AGREE | A | `curved` (correct, coincidentally) |
| immediate_probe | 1 | AGREE | B | `None` |
| retention | 1 | AGREE | A | `None` |
| baseline | 2 | AGREE | B | `None` |
| immediate_probe | 2 | **DISAGREE_UNKNOWN_REVIEW** | — | `None` |
| retention | 2 | AGREE | B | `None` |

**5/6 resolve cleanly by full independent agreement; 1/6 is an honest, correctly-flagged
disagreement — not a silent guess, and not a parser bug.** Investigated directly: trial 2's
`immediate_probe` response is `"B.\n\nI'm drawn to Option B because... resonating with the sharp
angles and repeated patterns..."` — but in *this specific trial*, the randomized label mapping had
`A = angular, B = curved` (flipped from the same trial's own baseline mapping). The model explicitly
declared label "B" (primary method, strong evidence) while its own descriptive content matches the
*angular* option's text (secondary method, word-overlap) — a genuine internal inconsistency in the
response itself, most plausibly the model's persona-driven phrasing carrying over from its own
immediately-prior turn's stated reasoning without correctly re-binding to *this* trial's re-randomized
label assignment. This is exactly the class of case the dual-method design exists to catch rather than
silently resolve: the correct behavior here is to flag it for human review, not to guess which of the
two conflicting signals (the stated label vs. the described content) the model "really meant." This is
recorded as a substantive finding for the interpretation layer (a possible cross-trial
label-re-binding confusion), not resolved by the parser — resolving it would require an interpretive
judgment call this measurement layer is explicitly not supposed to make (mission Section 10).

The old parser resolved 1/6 of these same records (a coincidence, not competence); the fixed parser
resolves 5/6 cleanly and honestly flags the 6th.

## 9. Investigation: why was "curved" disproportionately attractive?

Read all 8 real non-Echo-control (`llama3.2:3b`) records directly. **Result: 8/8 (100%), fully
position-independent** — curved was selected regardless of whether it was labeled A or B in that
trial. Every stated rationale cited exclusively positive-valence language for the curved option:
"fluidity," "continuity," "harmony," "movement," "calming," "soothing," "smoothness," "growth,"
"transformation." No comparably positive framing for the angular option appeared anywhere in the
corpus from this model.

Traced to the actual wording, not just "the concept of curved lines is preferred":

- `motif_angular`'s description contains the word **"sharp"** ("...meet at repeating **sharp**
  angles") — an adjective with an inherent negative/harsh connotation in ordinary English (sharp =
  dangerous, harsh, piercing), with **no positive counterpart anywhere in the angular description**.
- `motif_curved`'s description contains an extra qualifying clause, **"...without crossing"** — an
  unearned positive property (self-avoiding/non-self-intersecting = tidy, elegant, "clean") that the
  angular description has **no equivalent clause for**.

This is a genuine wording-level connotation asymmetry between the two candidate descriptions, not
merely "this model happens to like curves." It would very plausibly recur with any model, since it is
a property of the English words used, not a quirk of one model's training.

## 10. Replacement task design

The P0.3 spec already contains an unused, never-empirically-tested task family exactly suited to
this problem: `name` (`option_label_mapping` values "Verel" and "Farun" — invented, phonetically
neutral, length- and token-matched nonsense words). Arbitrary invented proper nouns carry no built-in
positive/negative connotation by construction — there is no equivalent to "sharp" or "without
crossing" possible when the candidate text is a single invented word with no descriptive content at
all. This satisfies every constraint mission Section 7 lists (no religious/cultural symbolism, no
aesthetic preference, no writing-advice cliché, no semantic asymmetry — the pre-existing spec already
confirms token-count parity under `cl100k_base`) without needing to invent a new task from scratch.

**Adopted, not invented new** — consistent with the mission's "minimum defensible repairs" instruction.

## 11. Control validation

`scripts/validate_replacement_task_name_family.py`. Part 1 (MockResponder): confirmed the harness
plumbing (`build_forced_choice_prompt`, `randomize_label_mapping`, `run_trial`) handles the new task's
option text correctly across both label positions — purely structural, no bias claim (MockResponder
has no real "opinion").

Part 2 (real non-Echo control, `llama3.2:3b` — the same model used in the P1 pilot): 4 real calls
across the full 2 (label position) × 2 (phrasing) permutation matrix, via `river_deliberation.
_ollama_query()` (Design B, already confirmed clean — no RiverBrain, no logging, no side effects).

| Trial | Label map | Raw response (truncated) | Resolved selection |
|---|---|---|---|
| 1 | A=Verel, B=Farun | "I choose Option A: V... clear, consistent sound..." | Verel |
| 2 | A=Farun, B=Verel | "I choose Option A: F-A-R-U-N... distinct sound..." | Farun |
| 3 | A=Verel, B=Farun | "I'll choose Option A: V... more distinct sound..." | Verel |
| 4 | A=Farun, B=Verel | "I choose Option A: Farun... softer sound..." | Farun |

## 12. Position/wording effects

**4/4 resolved. Exactly a 2/4–2/4 split between Verel and Farun — 0% net content bias**, a stark
contrast with `motif`'s confirmed 8/8 (100%). Applying this gate's own pre-declared strong-prior
threshold (>75% of resolved trials favoring one candidate, deliberately more conservative than
motif's 100% given the small n=4 validation sample): **50% max share — no strong prior detected.**

**A real, separate finding, worth naming rather than treating as noise:** in all 4 trials, the model
selected whichever candidate happened to be labeled "Option A" in that specific trial — a genuine
**position** bias, distinct from a **content** bias. This is exactly why the protocol's existing
`randomize_label_mapping()` (rotating which semantic option lands in position A across trials) is
load-bearing, not a decorative control: it is precisely what turned a 100%-consistent per-trial
position bias into a 50/50 net result across trials. A live run using this task family should
continue watching for a recurrence of this position effect within its own trial sequence rather than
assuming a 4-trial check has fully ruled it out.

## 13. Regression suite results

```
$ python3 scripts/verify_preference_provenance_experiment.py
=== 105 passed, 0 failed ===

$ python3 scripts/verify_choice_parser_benchmark.py
=== 52 passed, 0 failed, 1 exempt (documented residual limitation) ===
```

One expected, non-defect regression was hit and fixed during this pass: adding the two new P1.1
scripts (`verify_choice_parser_benchmark.py`, `validate_replacement_task_name_family.py`) as new
legitimate importers of `app.experiments.preference_provenance` tripped the existing isolation
negative-test ("zero production files import app.experiments.*"), exactly the same recurring,
expected maintenance pattern already seen three times previously in this project's history for each
new deliberate entry point. Fixed with the same one-line exclusion-list addition used every previous
time; 105/105 restored.

## 14. Remaining confounds and limitations

Named explicitly, per mission Section 5's own allowance ("if perfect performance isn't achievable,
define the residual error boundary explicitly") — none of these block the PASS verdict, but a future
session should know about them:

1. **Negation is not handled** (§6, §7 exemption). A response that restates one candidate's
   description while explicitly rejecting it is not guaranteed to resolve correctly via the
   secondary method. Declared before evaluation, not discovered after.
2. **The explicit backward-reference marker list is a citation-style-language detector, not a
   general recall detector.** A response like "You asked me this before and I said B, so I'll say B
   again" does not trip the `backward_reference` flag (it isn't phrased as "as I mentioned earlier");
   the *selection* is still extracted correctly, only the recall metadata undercounts this phrasing
   style. Confirmed directly in the benchmark (§6, Section 2 continuity cases).
3. **Position bias, real and confirmed for `name`** (§12) — mitigated by existing per-trial label
   randomization, not eliminated at the level of a single trial.
4. **n=4 is a small validation sample** for the `name` family's control-validation pass, deliberately
   scoped this way per the mission's own "minimum defensible repairs, avoid scope creep" instruction.
   A full live run's own baseline-phase data will provide a larger, real check.
5. **The one genuine P1 disagreement (§8) remains genuinely unresolved at the measurement layer, by
   design** — it is not this gate's job to decide what the model "really meant" when its declared
   label and its described content point in different directions.

## 15. Exact protocol changes made in this pass

- New file: `app/experiments/preference_provenance/choice_parser.py` (analysis layer; `harness.py`'s
  capture-time code was **not** modified).
- New file: `scripts/verify_choice_parser_benchmark.py` (ground-truth benchmark, 52 cases).
- New file: `scripts/validate_replacement_task_name_family.py` (non-Echo-only task validation).
- Modified: `scripts/verify_preference_provenance_experiment.py` (isolation-exclusion-list addition
  only, same recurring one-line maintenance pattern as three prior entry points).
- Modified: `audits/echo_preference_formation_retention_experiment.spec.json` — added a
  `p1_1_measurement_repair` summary block, corrected the stale top-level `status` field, added a
  `status_p1_1` note to both the `motif` (demoted, root cause recorded) and `name` (promoted,
  validation recorded) task family entries. The P0.3 causal design itself (phases, variants,
  hypotheses) was **not** altered — this is a measurement-instrument and task-selection change
  layered on top of the existing causal design, not a redesign of it.
- **No changes were made to `harness.py`'s `RawTrial` schema, `run_trial()`'s signature, the P0.3
  causal sequence (Baseline → Formation → Immediate Probe → Distractors → Retention), or any control
  condition.** The sequence required by mission Section 9 is fully intact.
- **No production code outside `app/experiments/` was touched.**

## 16. Frozen configuration (SHA-256)

```
4bf6ea1f892c6f4079e52f44f13581be22b6294f720ff5cc326d6c93557542ca  app/experiments/preference_provenance/choice_parser.py
6ac1a88151752d727130cd05487617a3ef2ed682774ea097a301480c66e09890  scripts/verify_choice_parser_benchmark.py
879fce949f4ce2716cf9491d20ab0026397e5f74bae3a3a2a8fd369fcff30553  scripts/validate_replacement_task_name_family.py
7c5e19ff50cdd5d951331db6c6e4210345673333bcf6e5619aa56a636bdb4c79  audits/echo_preference_formation_retention_experiment.spec.json
```

Any future edit to `choice_parser.py`'s decision logic (not test additions, the actual extraction
rules) after this point should be treated as a new revision requiring its own re-validation pass, the
same discipline already applied to the sealed P0.1 protocol.

**P0.1 protocol seal re-verified unchanged, as required at every checkpoint in this thread:**
```
$ python3 scripts/verify_protocol_seal.py --expect 2880fa048815f768d3b303ce7fff6e04196bf14949b53068fd7f0ec2a61a6a20 \
    audits/2026-09-03_preference_experiment_preregistered_protocol.md
protocol_sha256 = 2880fa048815f768d3b303ce7fff6e04196bf14949b53068fd7f0ec2a61a6a20
MATCH — protocol content is unchanged since sealing.
```

## 17. PASS/FAIL verdict

**PASS — READY FOR P1.2 LIVE VALIDATION.**

All required gates cleared:
- Parser repaired, generalized, not Echo-specific, verified against a frozen 52-case ground-truth
  benchmark including real P1 transcripts as fixtures (not hardcoded rules).
- Independent second measurement path implemented, with outcome-independent
  disagreement handling (5/6 real P1 records AGREE, 1/6 honestly DISAGREE_UNKNOWN_REVIEW, 0/6 ever
  silently guessed).
- "Curved" bias root-caused (specific wording-connotation asymmetry identified, not just described),
  and a replacement task family validated against a real non-Echo control with no comparable bias
  detected (0% net vs. 100%).
- Full regression suite green (105/105), plus the new benchmark (52/52, 1 declared exemption).
- P0.3 causal sequence and every control condition left structurally intact.
- P0.1 protocol seal unchanged.
- No post-hoc scoring changes were made to accommodate any observed outcome — the acceptance
  criteria in §6 were written into the benchmark script before it was run, and the strong-prior
  threshold in §12 was written into the validation script before the real model calls were made.
- Every remaining confound is named explicitly (§14), not silently absorbed into a false "fully
  solved" claim.

## 18. Is live Echo execution authorized?

**Yes — for a P1.2 live run using the `name` task family, under the exact conditions in §19.** This
gate does not authorize resuming use of the `motif` task family for a primary hypothesis-relevant
trial in its current wording (§9); `motif` remains available only as a secondary/exploratory
condition if a future session deliberately wants to re-examine it after a wording revision.

## 19. Exact conditions for the next run

1. Use the `name` task family (Verel/Farun) as the primary vehicle. `motif` may be run in parallel
   only as an explicitly-labeled secondary/exploratory condition, never blended into the primary
   result.
2. Use `choice_parser.cross_check_choice()` as the authoritative classification for every
   forced-choice phase — not `harness._parse_label_choice()`'s capture-time field, which remains a
   best-effort convenience value only.
3. Any `DISAGREE_UNKNOWN_REVIEW` result must be reported and reviewed by hand, never silently
   dropped or resolved toward either label.
4. Continue reporting `backward_reference`, `implicit_continuity`, and `persona_reference` as
   separate metadata columns — never folded into, or treated as evidence for, the preference
   determination itself.
5. Watch for the position effect named in §12 across the run's own real trial sequence; if it
   recurs strongly even with per-trial label randomization active, treat that as a new finding
   requiring its own investigation before drawing any conclusion from the aggregate choice
   distribution.
6. Preserve the full P0.3 causal sequence (Baseline → Formation → Immediate Post-Formation Probe →
   Distractors → Retention) exactly as specified — untouched by this pass.
7. Re-verify the P0.1 protocol seal and this gate's own frozen file hashes (§16) immediately before
   the run, the same discipline already applied at every checkpoint in this thread.
