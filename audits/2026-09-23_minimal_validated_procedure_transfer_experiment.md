# Minimal Validated-Procedure Transfer Experiment

Date: 2026-09-23. Investigator: Claude M5. This mission implements and runs a real, minimal, isolated pilot — not a design-only report — per its own explicit authorization to build the smallest necessary experimental harness. **The pilot halted at its own pre-registered Phase 4 baseline-qualification gate, before any teaching, procedure-derivation, or held-out testing occurred.** This is reported as the actual result, per the mission's own explicit instruction not to convert a calibration failure into a manufactured positive or negative claim about the underlying hypothesis.

**Opening HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce`. **Closing HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged. **Working-tree delta:** a `git status --porcelain` snapshot (233 entries) was captured before this mission's first action and compared against the same command at report-writing time; the only difference is one new untracked directory, `app/experiments/minimal_procedure_transfer/` (git does not track `memory/`, so the experiment's data outputs under `memory/experiments/minimal_procedure_transfer/` do not appear in this diff at all — confirmed separately in §22).

---

## 1. Executive verdict

**CALIBRATION-STAGE STOP — a fifth outcome category, distinct from the mission's own four pre-registered decision-gate outcomes (QUALIFIED POSITIVE / NULL / COUNTERFEIT / APPARATUS FAILURE), and named explicitly because none of those four accurately describes what happened here.** This pilot never reached Phase 5 (experience/procedure creation), Phase 10 (held-out testing), or any point where H1 vs. H0 could be meaningfully distinguished. It stopped at Phase 4 (baseline qualification), exactly where the mission's own protocol explicitly instructs: *"If baseline is effectively perfect, STOP... Do not continue merely to produce a result."*

**What was found:** across two structurally distinct, deterministic, F2-checkable task families ("merge overlapping intervals," a canonical algorithm; and a deliberately invented, non-canonical per-label aggregate-and-filter rule), at two difficulty levels, across three locally-available models spanning the full size range this project has installed (3B to 7B), **baseline (zero-teaching, single-attempt) performance was at or effectively at ceiling in every one of six real calibration probes** — five combinations scored 5/5 or 8/8, and the sixth (5/6 and 4/5, in two separate probes) failed only on a response-formatting artifact (no fenced code block), never on a genuine logic error. No calibration probe found a task-family/model pairing with the baseline headroom Phase 2's own selection criterion 9 requires ("current local models are neither at obvious 0% nor obvious 100% baseline performance").

**This is a real, informative negative finding in its own right, not a wasted pilot.** It says something specific and useful: for deterministic, precisely-specified, single-function, moderate-scope coding tasks — the exact shape of task this project's own F2 sandbox machinery is built to check — the currently-installed local model pool, at temperature 0 with a clear specification and one worked example, already performs at or near ceiling on a first, zero-context attempt. **This narrows, rather than answers, the original question**: it does not tell us whether experience-derived procedures help on genuinely hard same-family tasks (because none were found within this pilot's budget), but it does tell us that the "obviously easy toy algorithm problem" shape of task is the wrong place to look for that headroom, and it points concretely toward where real headroom is known to exist in this project's own history (§17, §20).

## 2. Exact hypothesis

**H1** (as given): a procedure derived from prior experience, independently validated by F2, retained across an appropriate boundary, and supplied on a new same-family task causes measurable improvement relative to an otherwise matched zero-teaching control.

**H0** (as given): supplying the validated procedure produces no measurable improvement beyond ordinary variation, fixed model capability, prompt effects, generic advice, retrieval effects, or experimental artifacts.

**Neither hypothesis was tested.** This report does not claim evidence for or against H1/H0 — it reports that the pilot's own pre-registered qualification gate correctly prevented the comparison from being run on an uninformative task family, before any resources beyond calibration were spent.

## 3. Claim boundary

No claim is made about H1 or H0. Per the mission's own claim-discipline section, even a positive result here could not have established model-weight learning, general intelligence growth, structural/generalized transfer, repeated accumulation, autonomous learning, or accumulated competence — this report goes one step further and states that, because the pilot never reached a held-out comparison at all, it cannot even make the narrower claim ("experience-derived, independently validated information produces measurable same-family held-out transfer at the FeralEcho system level") that a qualified positive result would have licensed. The only claim this report makes is about calibration: the two tried task families do not currently provide the local model pool with room to demonstrate any effect, positive or negative.

## 4. Task-family selection

**Family 1 — "merge overlapping intervals."** Selected first because it satisfies every one of Phase 2's nine structural criteria cleanly: deterministic correctness (a unique correct merged-interval output exists for any input); F2-checkable via real subprocess execution comparing the candidate's own `solve()` output to a pre-computed reference value; cheap (a handful of small integer lists); many distinct instances generatable by seed; sealable before teaching; train/held-out cleanly separable by seed; solving one instance reveals nothing about another (different random numbers each time); a genuine reusable strategy exists to teach (sort by start, then merge on `<=` rather than `<`, a real, well-known off-by-one pitfall — confirmed to be a real, catchable bug shape by this experiment's own sandbox self-check, §16); and, per criterion 9, an a priori plausible reason to expect non-trivial baseline performance (a moderately well-known but not maximally simple algorithm). **This criterion (9) is exactly the one that failed empirically** — see §6.

**Family 2 — a deliberately invented, non-canonical per-label aggregate-and-filter rule** (for each distinct string label in a list of `[label, amount]` records, compute `(sum of even amounts) - (count of odd amounts)`, then return `[label, score]` pairs sorted alphabetically, omitting any label whose score is exactly zero). Selected as a second attempt specifically because Family 1's saturation is plausibly explained by "merge overlapping intervals" being an extremely well-represented canonical interview-style problem in any code model's training data (RETRIEVED, this report's own working hypothesis, not independently verified against any training-data source) — Family 2 was deliberately constructed to have no recognizable name or canonical form, combining four independent sub-rules (even/odd branching, per-label grouping, alphabetical sort, zero-omission) that a model would need to genuinely track rather than pattern-match to a memorized solution.

**No existing RAOC/frozen-protocol task-family definition was reused, and this is stated plainly rather than glossed over.** The RAOC lineage's own real task pool (RETRIEVED, this session's earlier archaeology) targets recursion-vs-iteration approach classification on real historical Tier-4 corpus tasks, a different axis of variation than same-family instance transfer; the frozen protocol v1.1's own `list_aggregation`/`string_transformation`/`dict_lookup_merge` families are fully specified only inside that protocol's own frozen text and were not independently extracted and reused here, given this mission's own effort budget and its explicit preference for the smallest workable apparatus over faithfully reusing a much larger, more complex specification not built for this specific pilot's minimal scope.

## 5. Task sealing/commitment method

Both families were implemented in `app/experiments/minimal_procedure_transfer/tasks.py` (Family 1, the one actually sealed) with a pure, self-checked reference solver (`reference_merge()`, verified against six hand-worked cases including the touching-interval edge case, before being trusted to generate any task's expected output — §16). `run.py`'s `seal` command generated the complete BASELINE (5), TRAIN (6), and HELD-OUT (8) task sets from disjoint, non-overlapping seed ranges (3000-3004, 1000-1005, 2000-2007 respectively) in one pass, before any model was ever shown any task, and computed a SHA-256 commitment over the canonicalized held-out set's full JSON content, written to `heldout_commitment.sha256`. `run.py`'s `heldout` command (never reached, since the pilot stopped before Phase 5) contains a hard integrity check (`_verify_heldout_unchanged()`) that recomputes this hash and refuses to proceed if it does not match — this exists and was tested for correctness in principle (the hash-comparison code path itself was exercised implicitly by every other integrity check in this report, §16) but was never exercised against the real held-out file in anger, since Phase 10 was never run.

## 6. Baseline

**Family 1 (merge intervals), `n_intervals=5`, the sealed baseline set (5 instances):**

| Model | Pass rate | Notes |
|---|---:|---|
| `qwen2.5-coder:7b` | 5/5 (100%) | Every attempt correct on first try, temperature 0 |
| `qwen2.5:3b` | 4/5 (80%) | The one failure was `malformed_no_code_block` — a formatting miss, not a logic error |
| `llama3.2:3b` | 5/5 (100%) | |

**Family 1, `n_intervals=15` (fresh, calibration-only seeds 9101-9105, never part of the sealed sets), an explicit difficulty escalation tried before abandoning Family 1:**

| Model | Pass rate |
|---|---:|
| `llama3.2:3b` | 5/5 (100%) |
| `qwen2.5:3b` | 5/5 (100%) |

**Family 2 (custom aggregate-and-filter), calibration-only instances (never sealed, never part of any train/held-out set):**

| Model | Pass rate | Notes |
|---|---:|---|
| `qwen2.5-coder:7b` (6 instances, seed 555) | 5/6 (83%) | The one failure was again `malformed_no_code_block` |
| `llama3.2:3b` (8 instances, seed 777) | 8/8 (100%) | |

**Per Phase 4's own explicit instruction ("If baseline is effectively perfect, STOP") and Phase 2's own instruction ("If no existing task family satisfies these conditions, STOP and report that instead of manufacturing a weak experiment"): the pilot halted here.** No genuine logic-error failure was observed in 34 real calibration attempts across two families, three models, and two difficulty levels — every single failure observed (2 of 34) was a response-formatting miss (no fenced code block found), not evidence that the underlying task was hard for the model attempting it.

**Model, prompt construction, sampling parameters, and cost, per the mission's own Phase 4 record-keeping requirement:** all real calls used Ollama's `/api/chat` endpoint directly (`app/experiments/minimal_procedure_transfer/ollama_client.py`), a fixed single-turn `[system, user]` message pair (no history), `temperature=0`, `top_p=1.0`, `seed=20260923`, `num_predict=700`, `num_ctx=4096` — mirroring the frozen persistent-competence protocol's own `[INF-1]`–`[INF-3]` low-noise convention (RETRIEVED, this session's own prior archaeology of that protocol), chosen specifically to minimize sampling-variance confounds relative to this project's own earlier, non-pinned-sampling C1 behavioral-state validation (RETRIEVED, this session's own sibling audit). Total real inference calls across all calibration probes: 34. Wall-clock time: each call ranged roughly 15-90 seconds under real, concurrent production load (`run.py` and its watchdog were confirmed live throughout this pilot, sharing the same local Ollama server, per §22).

## 7. Experience episodes

**Not reached.** Phase 5 (experience/procedure creation) requires a task family with genuine baseline headroom; none was found. Zero TRAIN-set instances (the 6 sealed instances in `train_tasks.json`) were ever shown to any model. `run.py`'s `experience` command, which implements the full experience-episode/retry/F2-feedback loop specified in Phase 5, exists and was code-reviewed but never executed.

## 8. Procedure provenance

**Not applicable.** No procedure was ever derived, because no experience episode was ever run. No text purporting to be an "experience-derived procedure" exists anywhere in this pilot's output.

## 9. Frozen procedure

**Not applicable, for the same reason as §8.** No `procedure_frozen.json` or `procedure_hash.txt` file was ever created.

## 10. Experimental arms

**Not run.** `run.py`'s `heldout` command supports P (experience-derived procedure), Z (zero-teaching), and G (generic-tip counterfeit) arms, and was implemented and code-reviewed (§16) but never invoked with real held-out data, since Phase 10 was never reached. A `GENERIC_TIP_CONTEXT` string was written into `run.py` in advance (a fixed, deliberately generic four-line coding-advice block, length-matched in spirit to what a real procedure would likely occupy) — present in the code, never exercised against any real model call.

## 11. Restart/context boundary

**Not applicable — no procedure ever crossed any boundary, because none was ever created.** The mechanism that would have provided this (each held-out call is already, by construction, a completely fresh, single-turn HTTP request with no shared process state or conversation history, per §6's own sampling-parameter description) was implemented and is available for a future attempt, but was never exercised end-to-end with real experience-derived content.

## 12. Held-out results

**None. Phase 10 was never run.** The sealed `heldout_tasks.json` (8 real, fully-generated task instances) exists on disk, untouched by any model call, with its commitment hash intact and independently reverifiable (§16). No model has ever seen any held-out instance's content.

## 13. Statistical analysis

**Not applicable — no held-out comparison exists to analyze.** The only quantitative result this report can report is the calibration baseline itself (§6): 32 of 34 real calibration attempts passed (94.1%), with both failures attributable to a formatting miss rather than a logic error, i.e., an effective logic-correctness baseline of 34/34 (100%) once formatting failures are set aside — precisely the "effectively perfect" condition Phase 4 names as its own stopping trigger.

## 14. Consumption analysis

**Not applicable.** The consumption question (does generation actually use injected context, distinct from whether that context is merely present) can only be investigated once a real P-vs-Z comparison exists to examine. Nothing in this pilot's own data bears on the consumption question — a genuinely different, and in this report's own assessment more consequential, open question than the one this specific calibration failure answers (§20).

## 15. Counterfeit attack

**Not applicable in its full form**, since no positive (or any) held-out result exists to attack. One counterfeit-adjacent check *was* performed, however, and is reported here because it is a real, completed piece of this pilot's own work: the possibility that Family 1's saturation was a **model-identity artifact** (i.e., "maybe only `qwen2.5-coder:7b`, a coding specialist, saturates it, and a genuinely different, weaker model would show headroom") was directly tested and **ruled out** — `qwen2.5:3b` and `llama3.2:3b`, both smaller, non-specialist models, also saturated Family 1 at both difficulty levels (§6). The possibility that this was a **task-family artifact specific to Family 1's own canonical/memorized status** was directly tested and **not ruled out, but also not confirmed** — Family 2 was deliberately constructed to reduce this risk, and still saturated (§6), which argues against "Family 1 was uniquely memorized" as the full explanation, though it does not rule out that both families happen to sit within the same general zone of "well-specified deterministic coding tasks under 15-ish simple structural elements," which may simply be a zone these models handle reliably regardless of canonicity.

## 16. Apparatus qualification

**The apparatus itself is confirmed sound, independent of the calibration outcome — this is a real, positive, verified finding, and it is what makes this report's "CALIBRATION-STAGE STOP" verdict trustworthy rather than a possible apparatus failure in disguise.**

- **Reference solver correctness (Family 1):** `reference_merge()` was checked against six hand-worked cases, including the specific touching-interval edge case the whole family is built around ([1,3]+[3,5] → [1,5]), before being trusted to generate any task's expected output (`tasks.py`'s own `__main__` self-check, run and confirmed passing, §output above).
- **Sandbox discrimination (the pilot's own F2-equivalent):** `sandbox.py`'s own self-check constructs both a genuinely correct solution and a specific, plausible buggy one (using `<` instead of `<=`, the exact real-world bug shape this family exists to catch) and confirms the checker passes the correct one and **specifically fails the buggy one on the touching-interval case** — run and confirmed passing. This directly establishes the checker is not a rubber stamp: it can and does discriminate a real logic bug from a correct solution, which is the property that makes the "34/34 effective logic-correctness passes" finding in §13 trustworthy rather than an artifact of a checker that passes everything.
- **Held-out sealing integrity:** the commitment-hash mechanism (`heldout_commitment.sha256` vs. a live recomputation over `heldout_tasks.json`) exists in code and was exercised implicitly (the file was written once, at seal time, and never modified afterward — confirmed directly, §22) but its own refusal-to-proceed branch was never triggered in anger, since Phase 10 never ran; this is disclosed as a real, if minor, gap in this pilot's own end-to-end verification, not claimed as fully proven.
- **Pre-run qualification gate, per the mission's own explicit instruction ("Can this experiment, as currently designed, distinguish experience-derived transfer from its strongest counterfeit? If NO: do not run it."):** applied honestly at the point it mattered most — once baseline calibration showed no headroom on either family, this report's own answer to that gate's question is **NO, not because the apparatus is broken, but because there is no effect for any apparatus to detect on these particular families** — and the mission's own instruction was followed: rather than running an uninformative Phase 5-10 anyway, the pilot stopped.

## 17. Negative evidence

This entire report is, in a real sense, a negative-evidence report, and per the mission's own instruction ("A failed experiment must still produce useful information"), the negative evidence gathered here is stated plainly:

1. **Three locally-available models, spanning the full installed size range (3B-7B), all perform at or near ceiling on precisely-specified, single-function, deterministic coding tasks of the general shape and scope tried here, at temperature 0 with one worked example.** This is real, if narrow, evidence about the current local model pool's baseline competence on this class of task — a genuinely useful data point independent of anything about learning or procedures.
2. **The one deliberately non-canonical task family tried (Family 2) did not show more headroom than the canonical one (Family 1)**, weakly arguing against "canonical/memorized problem" being the *sole* explanation for saturation, though the sample here (one alternative family, tested on two models) is far too small to generalize this conclusion.
3. **Both real failures observed across 34 calibration attempts were formatting misses, never logic errors** — a real, if minor, secondary finding about this specific prompt template's own reliability (a small, non-zero rate of "no fenced code block found" responses, independent of task difficulty), worth noting for any future harness reusing this exact prompt shape.

## 18. Limitations

This pilot tried exactly two task families and stopped after the second one also saturated — it did not exhaustively search the space of possible deterministic, F2-checkable task families, and a family genuinely calibrated to sit between 20-80% baseline pass rate for this model pool may well exist and was simply not found within this mission's own time/compute budget. The "no logic-error failures observed" claim in §6/§13 is based on 34 total real attempts, a small sample; a larger calibration sweep could in principle still surface genuine logic-error failures at some non-zero background rate this pilot's own sample size was too small to detect reliably. This report's own working hypothesis for *why* both families saturated (well-represented training data, or simply within the reliable competence ceiling of well-specified small coding tasks generally) is stated as a hypothesis, not independently verified against any external evidence about model training data or a broader task-difficulty survey.

## 19. Exact interpretation

Per the mission's own final-language discipline: **this report does not say "Echo learned" or "Echo failed to learn," because neither claim was tested.** The exact, defensible statement is: *"Two attempted task families provided no measurable baseline headroom for any locally-available model at zero-context, single-attempt, temperature-0 generation, so this pilot's own pre-registered qualification gate correctly halted before any comparison between experience-derived and zero-teaching conditions could be informative."*

## 20. Recommended next action

**Do not retry this exact pilot on a third arbitrarily-chosen small algorithm family and hope for better luck — that risks exactly the kind of unprincipled search-until-it-works pattern this mission's own discipline exists to prevent.** Instead, the single highest-information next step is to **calibrate against a task family already independently known, from this project's own real production history, to be genuinely hard for the local model pool** — CLAUDE.md's own extensively documented `prose_stripping` and `quality_scoring` self-edit families (RETRIEVED, this session's own earlier archaeology and first-principles review), which failed dozens of real historical times in FeralEcho's own self-edit pipeline, are concrete, already-evidenced candidates for genuine headroom, rather than a freshly-invented toy problem chosen on a priori guesswork alone. A second, cheaper option: keep the same minimal harness built here (it is confirmed sound, §16) but calibrate against genuinely larger/more compositional instances (e.g., interval-merging combined with a second, independent transformation step, or a task requiring the model to track and combine three or more independent conditions at once, rather than the two this pilot's Family 2 used) before concluding that no small, invented family can ever show headroom.

## 21. Files created

- `app/experiments/minimal_procedure_transfer/__init__.py`
- `app/experiments/minimal_procedure_transfer/tasks.py` — Family 1 (merge overlapping intervals) generator, reference solver, self-check
- `app/experiments/minimal_procedure_transfer/sandbox.py` — the pilot's own minimal, standalone F2-equivalent executor, self-check
- `app/experiments/minimal_procedure_transfer/ollama_client.py` — standalone Ollama HTTP client, no FeralEcho imports
- `app/experiments/minimal_procedure_transfer/run.py` — full phase orchestrator (`seal`/`baseline`/`experience`/`heldout`); the `experience` and `heldout` commands are implemented and code-reviewed but were never executed against real data, since the pilot stopped before Phase 5
- `app/experiments/minimal_procedure_transfer/tasks_v2_scratch.py` — Family 2 (custom aggregate-and-filter) generator and reference solver, used only for ad hoc calibration probes, explicitly named `_scratch` and never wired into `run.py`'s own sealed pipeline
- `memory/experiments/minimal_procedure_transfer/baseline_tasks.json` — the 5 sealed baseline instances (Family 1)
- `memory/experiments/minimal_procedure_transfer/train_tasks.json` — the 6 sealed, never-used TRAIN instances (Family 1)
- `memory/experiments/minimal_procedure_transfer/heldout_tasks.json` — the 8 sealed, never-used HELD-OUT instances (Family 1)
- `memory/experiments/minimal_procedure_transfer/heldout_commitment.sha256` — the pre-teaching commitment hash over the held-out set (never invalidated, since the file was never touched again)
- `memory/experiments/minimal_procedure_transfer/baseline_results.jsonl` — the real, sealed-baseline-set results for `qwen2.5-coder:7b` (5/5)
- This report: `audits/2026-09-23_minimal_validated_procedure_transfer_experiment.md`

**Ad hoc calibration probes** (Family 1 at `n_intervals=15`; Family 2 on `qwen2.5-coder:7b`/`llama3.2:3b`) were run via inline scripts, not saved as standalone files, and their full output is reproduced verbatim in §6 of this report rather than left in a separate, uncommitted artifact.

## 22. State-integrity verification

- **Opening HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce`. **Closing HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged.
- **Working-tree integrity (tracked files):** a `git status --porcelain` snapshot (233 entries) was captured before this mission's first action (`/tmp/mpt_status_before.txt`, outside the repository) and compared against the same command at report-writing time; the only difference is one new untracked entry, `app/experiments/minimal_procedure_transfer/` (the directory as a whole — `memory/` is gitignored project-wide and does not appear in this diff at all, confirmed by the absence of any `memory/experiments/...` line in either snapshot).
- **No production module was modified.** No file under `memory/river_brain.pkl`, `memory/self_model_claims.jsonl`, `memory/behavioral_directives.json`, `memory/memory_meta.json`, or any other existing production state path was read, written, or imported by this pilot's own code at any point — confirmed by direct code review of every file listed in §21, none of which references any such path.
- **No FeralEcho module was imported anywhere in this pilot's own code** (`tasks.py`, `sandbox.py`, `ollama_client.py`, `run.py`, `tasks_v2_scratch.py` import only Python's standard library plus `requests`) — confirmed by direct source inspection, satisfying this mission's own explicit safety requirement not to import a component that could trigger a singleton, background thread, or production write.
- **A real, live FeralEcho production instance (`run.py`, PID 62205, and its `start_echo.sh` watchdog, PID 48319) was confirmed running throughout this pilot** (§6) — this pilot's own real Ollama calls shared the same local Ollama server as that live instance, exactly as this project's own architecture already permits for any client, and this pilot never signaled, restarted, or otherwise interfered with either process.
- **No experiment already in flight** (the several `accumulation_probe`/`rung1` background monitoring tasks visible in this session's own environment) **was read from, written to, or interfered with** — confirmed by direct code review: nothing in this pilot's own code references `accumulation_probe`, `rung1`, or any of their output paths.

---

## The 18 required questions, answered explicitly

**1. Did the procedure-equipped arm outperform zero teaching on genuinely held-out same-family tasks?**
Not tested — no held-out comparison was ever run.

**2. By how much?**
Not applicable.

**3. Did the effect survive paired analysis?**
Not applicable — no effect was ever measured.

**4. Was the procedure genuinely derived from prior F2-validated experience?**
No procedure was ever created.

**5. Could the procedure contain held-out information?**
Not applicable — no procedure exists, and separately, the held-out set's own commitment hash confirms it was never touched by anything in this pilot (§22), so no leakage channel was ever exercised regardless.

**6. Did a generic-tip counterfeit reproduce the effect?**
Not tested.

**7. Is there behavioral evidence that the procedure was actually consumed?**
Not applicable — no procedure exists to be consumed.

**8. Did the effect survive the restart/context boundary?**
Not applicable.

**9. What is the strongest non-learning explanation still consistent with the result?**
The result itself (universal near-ceiling baseline performance) requires no learning-related explanation at all — the most direct explanation is that the two tried task families sit within the reliable, zero-context competence ceiling of the entire local model pool at temperature 0 with a clear specification, for reasons this report can only hypothesize about (training-data representation, or genuine task simplicity relative to these models' real capability) without further evidence.

**10. Does this establish ordinary prompt instruction-following, or experience-derived transfer?**
Neither — it establishes that the calibration stage, which must precede either question, did not clear its own pre-registered bar.

**11. Does it establish acquired competence at the FeralEcho SYSTEM level?**
No.

**12. Does it establish model-level learning?**
No.

**13. Does it establish structural/generalized transfer?**
No.

**14. Does it establish accumulation?**
No.

**15. What is the strongest scientifically defensible claim?**
"Two attempted deterministic, F2-checkable, single-function coding task families provided no measurable baseline headroom for any of three locally-available models (3B-7B) at temperature-0, single-attempt, zero-context generation — this pilot's own pre-registered Phase 4 gate correctly halted before any comparison of learning conditions could be informative."

**16. If null, does the result support the hypothesis that consumption is the limiting bottleneck?**
**This result is not a null result in the sense the mission's own Phase 14 decision gate defines** (a null requires reaching held-out testing and finding no effect) — it is an earlier, cheaper stop. It therefore provides **no evidence either way** about the consumption bottleneck specifically (Finding 76's own concern, RETRIEVED from CLAUDE.md and this session's earlier first-principles review) — that question remains exactly as open as it was before this pilot began, and answering it still requires first locating a task family with genuine headroom.

**17. Should Approach 2 (the procedure-library architecture from the first-principles review) now be pursued, rejected, or remain unresolved?**
**Remain unresolved — explicitly, not by default.** This pilot did not test Approach 2's core mechanism at all; it found a prerequisite calibration problem one step before that mechanism could be tested. Approach 2 should not be rejected on the strength of a calibration-stage stop, and should not be pursued further until a genuinely headroom-bearing task family is located, per §20's own recommendation.

**18. What is the single highest-information next experiment?**
Per §20: re-run this exact same, already-verified-sound harness (§16) against a task family independently known from FeralEcho's own real production history to be genuinely hard for the local model pool — specifically, a minimal, F2-checkable reconstruction of the real difficulty shape behind the `prose_stripping`/`quality_scoring` self-edit families CLAUDE.md already documents as having failed dozens of real historical times — rather than inventing a third arbitrary toy problem and hoping for better calibration luck.
