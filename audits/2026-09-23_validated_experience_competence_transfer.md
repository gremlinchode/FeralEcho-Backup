# Validated-Experience Competence Transfer — Frozen Experiment

Date: 2026-09-23/24 (started 2026-09-23, completed after midnight 2026-09-24 — actual timestamps recorded throughout, per the project's dating convention). Investigator: Claude M5. This is a real, executed experiment on the frozen configuration authorized after `audits/2026-09-23_historical_difficulty_headroom_calibration.md`'s QUALIFIED FAMILY result. No production code, RiverBrain, `river.bandit`, `behavioral_state.py`, `self_model_claims.py`, Rung-1, `accumulation_probe`, or the frozen persistent-competence protocol was touched or activated.

**Opening HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce`. **Closing HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged. **Working-tree delta:** the only difference between the pre-mission `git status --porcelain` snapshot (237 entries) and the current one is one new untracked directory, `app/experiments/validated_experience_competence_transfer/` (git does not track `memory/`, so this experiment's real data does not appear in that diff at all — verified separately in §26).

---

## 1. Executive verdict

**P > G ≈ Z.** On the frozen configuration (`extract_code`, Level 3, `qwen2.5-coder:7b`, 10 sealed held-out instances, single attempt per arm, no retries): **P (the frozen, TRAIN-derived procedure) scored 10/10 (100%); G (a length-matched generic-tip counterfeit) scored 6/10 (60%); Z (zero teaching) scored 5/10 (50%).** Every discordant pair, in both the P-vs-Z and P-vs-G comparisons, favored P — zero counter-examples in either direction. This is independently corroborated, not merely inferred from the pass-rate gap alone: a pre-declared, deterministic, code-level consumption check (never based on the model's own self-report) found that **P's real generated code checked the complete, taught four-category keyword set in 10 of 10 held-out instances, while G and Z's real generated code never did so, in 0 of 10 instances each** — the cleanest single piece of evidence in this experiment, because it identifies not just that P did better but a specific, mechanically-verifiable reason why.

**The strongest scientifically defensible claim this result supports, stated at the mission's own required precision:** *information derived from independently evaluated prior experience (8 real TRAIN episodes, F2-graded) and retained across a fresh-context boundary caused improved held-out performance on unseen instances from the same task family, at the FeralEcho system level, through a mechanism independently traceable in the candidate code itself, not merely inferred from the outcome.* This does **not** establish model-weight learning, general learning, structural transfer outside this family, autonomous learning, accumulation, or repeated competence growth — none of those claims are licensed by a single family, single episode, n=10 pilot, and this report does not make them.

**One real, honestly unresolved question this experiment cannot settle, stated plainly rather than glossed over:** whether P conveys genuinely new information the model lacked, or instead reminds the model of a refinement it was capable of applying but would not spontaneously apply without the reminder. Both are consistent with every observation in this report. This is a real limit on the claim, not a footnote to be minimized.

## 2. Exact hypothesis

**H1:** experience-derived information, extracted only from independently evaluated TRAIN episodes and retained across a clean context boundary, causes improved F2 performance on fresh sealed Level-3 `extract_code` instances.

**H0:** the experience-derived information provides no meaningful advantage beyond zero teaching, generic useful instructions, fixed model capability, prompt scaffolding, task variation, sampling variation, contamination, or evaluator artifacts.

## 3. Claim boundary

A clean positive result, per the governing mission's own explicit instruction, supports only: *"Information derived from independently evaluated prior experience and retained across a fresh-context boundary caused improved performance on unseen instances from the same task family at the FeralEcho system level."* It does not establish model-weight learning, general learning, structural transfer outside this family, autonomous learning, accumulation, repeated competence growth, consciousness, agency, or open-ended improvement. This report holds to that boundary throughout, including in §23.

## 4. Frozen experimental contract

Reproduced from `app/experiments/validated_experience_competence_transfer/CONTRACT.md`, written and saved **before** any TRAIN or HELD-OUT instance was generated: model `qwen2.5-coder:7b`; family/level `extract_code` Level 3; the qualified corrected prompt extended with exactly one optional, empty-by-default `context` parameter (verified byte-identical to the original at `context=""`, §9); evaluator `sandbox.run_candidate()` (reused unmodified); sampling `temperature=0, top_p=1.0, seed=20260923, num_predict=700, num_ctx=4096`; 8 TRAIN episodes (seeds 1000-1007), one retry with real F2 feedback on failure; 10 HELD-OUT instances (seeds 1100-1109); three arms P/G/Z, no N arm; scoring by F2 pass/fail; zero retries at held-out; a stop-on-apparatus-failure rule; McNemar exact paired analysis; a procedure-extraction rule requiring every clause traced to a specific TRAIN episode; a fixed P-G-Z arm-attempt order declared in advance; no exclusions. **Nothing in this contract was changed after the held-out set was sealed**, with one disclosed exception described in full and non-silently in §6/§26 (a real path-resolution bug, not a contract change, found and fixed after sealing but before any held-out call).

## 5. State integrity

- **Opening HEAD/status:** recorded to `/tmp/vect_head_before.txt`/`/tmp/vect_status_before.txt` before any action this mission.
- **Running processes, confirmed live throughout, never touched:** `run.py` (PID 62205), `start_echo.sh` watchdog (PID 48319).
- **Calibration files verified unchanged before use** (MD5 checksums of `historical_difficulty_calibration/{run_calibration.py,tasks.py}` and `minimal_procedure_transfer/sandbox.py` recorded before this mission began; these three files were then imported, never edited, throughout this mission).
- **No prior TRAIN/HELD-OUT material for this experiment existed** before this mission's own `seal` command (confirmed by directory listing before any action).
- **The qualified corrected prompt and evaluator were verified**, not merely assumed: `prompt.py`'s own self-check (§9) confirms the extended prompt reproduces the original byte-for-byte at `context=""`; the evaluator is imported unmodified from the already-qualified `sandbox.py`.

## 6. Task generation

`app/experiments/validated_experience_competence_transfer/run.py::cmd_seal()` generated TRAIN (seeds 1000-1007, 8 instances) and HELD-OUT (seeds 1100-1109, 10 instances) via `historical_difficulty_calibration/tasks.py::build_calibration_set()`, unmodified, at Level 3. A programmatic disjointness check ran before generation, comparing the new seed sets against every seed already spent in calibration/evaluator-qualification (700-704, 800-804, 810-814, 820-824, 830-834, 840-844, 850-854) and against each other — confirmed disjoint, with the check itself designed to raise `SystemExit("APPARATUS FAILURE...")` had any overlap been found.

**A real, disclosed methodological incident, not silently repaired:** the first run of `cmd_seal()`/`cmd_experience()` wrote their real output to `/Users/richietate/Desktop/memory/...` — one directory level *above* the FeralEcho repository — due to a path-depth miscalculation (`_HERE.parents[3]` where `_HERE` was already resolved to `run.py`'s containing directory, one level too many). This was discovered before `heldout` was ever run, the real files (train/held-out task JSON, the held-out commitment hash, the real experience log) were moved into the correct in-repo location, and the held-out commitment hash was re-verified to match exactly after the move (§26) — the real data was never regenerated or altered, only relocated. The code was fixed (`.parents[2]`) with an inline comment recording exactly what happened. No held-out content was exposed, inspected, or altered during this incident.

## 7. Held-out commitment

SHA-256 over the canonical JSON of the complete 10-instance held-out set, computed immediately after generation and before any TRAIN episode: `a35c0807cc505ed4d192b44f17b2705427ccf8e3a46af374557e60d9a8c90055`. Re-verified, independently, at report-writing time (§26): **matches exactly**, confirming the held-out set was never modified between sealing and the final held-out run, including across the path-relocation incident in §6.

## 8. TRAIN episodes

All 8 real, run once each with one retry-on-failure. **5 of 8 passed on the first attempt** (train_L3_00, 01, 03, 06, 07). **3 of 8 failed on the first attempt and again on the retry**, despite the retry receiving real, mechanically-generated F2 failure feedback (`sandbox.format_failure_feedback()`) — this is itself a real, notable finding: one round of real corrective feedback was insufficient to fix any of these three specific failures within this experiment's own one-retry budget.

Every real failure, inspected directly:
- **train_L3_05** (both attempts identical): `def solve(text): ... if line.strip().startswith('def') or line.strip().startswith('class'): return '\n'.join(lines[i:])`. Failed because the real instance's code snippet began with `"""Utility function."""` before `def triple(x):` — the keyword set checked (`def`, `class` only) omitted the docstring marker, so the returned span started one line too late.
- **train_L3_04** (both attempts identical): `code_start = re.search(r'\b(def|class|import|from)\b', text, re.MULTILINE)`. Failed because this unanchored word-boundary search matched the word "import" inside the real distractor prose sentence "Note that this import of new ideas often takes practice to get comfortable with," returning prose instead of code.
- **train_L3_02** (both attempts identical): `re.search(r'(?m)^[ \t]*(from|import|def|class|@|"""|\'\'\')[^\n]*\n(.*\n)*', text, re.DOTALL)`. Correctly located the real starting line but returned a truncated match, cutting off the function's own final `return` statement.

## 9. Correction provenance

Corrective information supplied on retry was, in every case, exactly and only `sandbox.format_failure_feedback()`'s own mechanically-generated description of the real F2 grading outcome (e.g., "For input ..., your function returned ..., but the correct output is ...") — never this investigator's own commentary, hint, or suggested fix. This is verifiable directly from `run.py::cmd_experience()`'s own source, which passes `feedback` (the function's return value) verbatim into the retry prompt with no additional text from any other source. `prompt.py`'s own self-check (§4) additionally confirms the base prompt template itself was never altered to accommodate this feedback — it is inserted through the same generic `context` parameter used for every treatment in this experiment.

## 10. Procedure extraction

Performed once, in `freeze_procedure.py`, after all 8 TRAIN episodes completed. The procedure text (reproduced in full in `procedure_frozen.json`, 1381 characters) contains exactly three substantive clauses, each directly addressing one of the three real failures in §8: (1) check for a *complete* set of code-opening markers (decorator/docstring/import/def-class), not a subset; (2) require a keyword to appear at the *start* of its own line, not merely anywhere in the text; (3) once the start is found, return every line to the true end of the text, rather than attempting to capture the whole span with one regular expression. **No clause addresses anything not directly observed failing in a real TRAIN episode** — notably, this procedure does **not** recommend `ast.parse`-based structural validation, despite that being this investigator's own prior, independently-authored "ideal" solution used only for evaluator qualification in the earlier calibration mission (§20 discusses why this distinction matters).

## 11. Procedure provenance audit

Performed mechanically, not merely narratively, at freeze time: `freeze_procedure.py` cross-checks every cited `train_L3_NN` episode ID against the real `experience_log.jsonl` content and refuses to write the frozen procedure file if any citation does not correspond to a real episode. This check passed on the first attempt after one earlier bug in the citation-parsing code itself was found and fixed (a string-splitting error, disclosed here rather than silently corrected). Per-clause classification:

| Clause | Classification | Supporting episode(s) |
|---|---|---|
| 1 — complete keyword set | **EXPERIENCE-DERIVED** | train_L3_05 (failed, incomplete set); train_L3_00, train_L3_06 (passed, more complete set) |
| 2 — line-start anchoring | **EXPERIENCE-DERIVED** | train_L3_04 (failed, unanchored); train_L3_00/01/03/06/07 (passed, anchored) |
| 3 — take-to-end, not single regex | **EXPERIENCE-DERIVED** | train_L3_02 (failed, single-regex truncation) |

**No clause is classified TASK-SPECIFICATION-DERIVED, GENERIC PRIOR KNOWLEDGE, RESEARCHER-INTRODUCED, or UNKNOWN.** One honest caveat, not smoothed over: the *prose wording* of each clause was composed by this investigator, not generated by the model itself — but the *substantive content* of every clause is a direct, mechanically-verified restatement of what a specific real episode's own code and F2 outcome showed, not this investigator's own general knowledge of the task family (§20 addresses this distinction as a counterfeit attack item).

## 12. Frozen P treatment

`procedure_frozen.json`, hash `21fde9b5dbe026489ef8f3ff47f974c816ca706944cde251b2501ed7f541f3c8`, frozen at `2026-09-24T03:56:07Z` (before generic-tip freezing, before any held-out call). Re-verified matching at report time (§26). Not edited after freezing.

## 13. G treatment

`generic_tip_treatment.json`, 1234 characters (89% of P's length), 8 fixed, hand-authored, generic programming tips (read the spec carefully, consider edge cases, ensure the function genuinely inspects its input, prefer simple/robust code, mentally trace the solution, avoid unstated assumptions, aim for a clear direct implementation, aim for generality) — containing **no mention** of the four-category keyword list, line-start anchoring, or the single-regex truncation risk. One earlier draft's seventh tip ("if you use a regular expression, make sure it's correct...") was judged, on reflection, too close to Clause 3's substantive content and was replaced before this treatment was ever used in any real call (disclosed here, not hidden, since it is a real design decision made during construction).

## 14. Z treatment

`context=""`. Verified (§9, `prompt.py`'s own self-check) to reproduce the original qualified calibration prompt byte-for-byte — no scaffolding, no procedure, no generic tips, nothing beyond the already-qualified base prompt.

## 15. Context boundary

Every held-out call, for every arm, is a fresh, single-turn `[system, user]` HTTP request to Ollama with no conversation history, no shared process state, and no reference to the TRAIN conversation or any other held-out call — the identical architecture already verified safe in both prior missions this session (the merge-intervals pilot and the calibration mission). Only the single treatment explicitly assigned to an arm (P's frozen procedure text, G's fixed tip text, or nothing for Z) crosses into that arm's prompt; no researcher analysis, no correction history, and no other arm's content is present in any call.

## 16. Arm identity/order controls

The three arms were run in a single, fixed, declared-in-advance order (P, G, Z) for every held-out instance — declared in `CONTRACT.md` before any held-out call was made. **The known v1.0 alphabetical tie-break counterfeit is structurally inapplicable to this design**, and this is demonstrated, not merely asserted: that counterfeit's mechanism requires a *selection* step choosing among multiple named workers via a tie-break rule; this experiment has no selection step at all — every arm is unconditionally run against every held-out instance, and grading is a fixed, deterministic function of the candidate's own code, with no arm-name, filename, or ordering input anywhere in `sandbox.run_candidate()`'s own signature (verified directly by reading that function, unmodified from the prior mission). No lexical, alphabetical, or default-value ordering could favor P — P is not "selected," it is unconditionally tested, exactly like G and Z.

## 17. Held-out results

Full paired outcome table, all 10 sealed instances:

| Task | P | G | Z |
|---|:-:|:-:|:-:|
| heldout_L3_00 | ✓ | ✓ | ✓ |
| heldout_L3_01 | ✓ | ✓ | ✗ |
| heldout_L3_02 | ✓ | ✗ | ✗ |
| heldout_L3_03 | ✓ | ✗ | ✓ |
| heldout_L3_04 | ✓ | ✗ | ✗ |
| heldout_L3_05 | ✓ | ✓ | ✗ |
| heldout_L3_06 | ✓ | ✓ | ✓ |
| heldout_L3_07 | ✓ | ✗ | ✗ |
| heldout_L3_08 | ✓ | ✓ | ✓ |
| heldout_L3_09 | ✓ | ✓ | ✓ |
| **Total** | **10/10** | **6/10** | **5/10** |

No result is hidden. The most informative discordant patterns present: **P-pass/G-fail/Z-fail** occurs at 02, 04, 07 (3 instances); **P-pass/G-pass/Z-fail** occurs at 01, 05 (2 instances); **P-pass/G-fail/Z-pass** occurs at 03 (1 instance). **No instance shows P failing while either G or Z passes.**

## 18. Paired statistical analysis

| Comparison | Discordant pairs (favor first / favor second) | Exact McNemar two-sided p | One-sided p (directional H1) |
|---|---|---:|---:|
| P vs Z | 5 / 0 | 0.0625 | 0.03125 |
| P vs G | 4 / 0 | 0.125 | 0.0625 |
| G vs Z | 2 / 1 | 1.0 | — |

95% Wilson confidence intervals on raw pass rates: P [0.72, 1.00]; G [0.31, 0.83]; Z [0.24, 0.76].

**Interpretation, held to the mission's own explicit discipline:** at conventional two-sided α=0.05, neither P-vs-Z nor P-vs-G crosses significance at this sample size — this is not overstated as "proof." However, both comparisons show **perfect directional concordance** (zero discordant pairs against P, out of 5 and 4 respectively), which is the maximally clean pattern a paired test of this size can produce in P's favor, and the pre-registered hypothesis (H1) was explicitly directional (P > Z, P > G), for which the one-sided P-vs-Z result (p=0.03125) does cross the conventional threshold. **This is reported as a real, small-sample pilot result with a strikingly clean directional pattern, not as a definitively proven effect** — a larger replication (§24) would be needed to establish the effect size with real precision. G-vs-Z shows no meaningful difference (p=1.0), consistent with generic instructions providing little-to-no benefit over no instruction at all in this specific pilot.

## 19. Strategy-consumption analysis

Pre-declared (§consumption_signatures.py, written and self-checked before any held-out call) and applied identically to every real held-out response's own extracted code, never to the model's self-report:

| Signature | P | G | Z |
|---|---|---|---|
| Complete keyword set (Clause 1) | **10/10 True, 0/10 False, 0/10 None** | 0/10 True, 5/10 False, 5/10 None | 0/10 True, 8/10 False, 2/10 None |
| Line-start anchored (Clause 2) | 10/10 True | 5/10 True, 5/10 False | 8/10 True, 0/10 False, 2/10 None |
| Take-to-end, not single regex (Clause 3) | 10/10 True | 5/10 True, 0/10 False, 5/10 None | 8/10 True, 0/10 False, 2/10 None |

**Signature 1 (complete keyword set) is the single most decisive, cleanly discriminating piece of evidence in this entire experiment: a perfect 10-0-0 separation between P and both controls.** Signatures 2 and 3 are near-ceiling for all three arms (line-start anchoring and take-to-end behavior are apparently common defaults for this model on this task regardless of teaching, consistent with 5 of 8 real TRAIN episodes already using anchored, take-to-end approaches with zero teaching at all) — these two signatures do not meaningfully discriminate P from G/Z, and this is reported honestly rather than cherry-picking only the signature that supports the headline finding. **A real detector bug was found and fixed during this analysis, disclosed rather than silently corrected**: the first version of the line-start-anchoring signature only matched the single chained expression `.strip().startswith(...)` and missed the semantically identical two-statement form (`line = line.strip()` then `line.startswith(...)`) that P's own real code actually used — this initially made the correct signature read as `None` for all 10 P responses, an obviously wrong result given direct inspection of the code; the detector was widened to catch both forms and re-run, with both the buggy and corrected results disclosed here.

**This satisfies the governing mission's own explicit requirement to distinguish "the procedure exists" from "the procedure actually affected behavior," using deterministic, non-self-report, code-level evidence** — the same discipline this project's own Finding 76 null result already established is necessary, and, unlike that null result, this experiment finds a clean, mechanically-observable behavioral difference specifically tied to the taught content (Signature 1), not merely a correlation between treatment and outcome.

## 20. Counterfeit attack

| # | Counterfeit | Classification |
|---|---|---|
| 1 | Generic instruction following | **CONTROLLED, weighing against this counterfeit** — G (generic instructions) scores 60%, far below P's 100%, and G's own code never shows Signature 1 |
| 2 | Prompt-length effects | **CONTROLLED for P-vs-G** (89% length match); **not fully controlled for P-vs-Z** (Z has zero added content) — but the P-vs-G gap (100% vs 60%, length-matched) argues length alone is not the dominant explanation |
| 3 | Identity/order effects | **NOT APPLICABLE** — no selection/tie-break mechanism exists in this design at all (§16) |
| 4 | Task difficulty imbalance | **RULED OUT** — paired design, identical held-out instances across every arm |
| 5 | Held-out leakage | **RULED OUT** — commitment hash verified intact before and after the path-relocation incident; procedure derived exclusively from TRAIN, verified by real timestamps predating any held-out call (§26) |
| 6 | Historical contamination | **RULED OUT** — fresh, disjoint seeds, programmatically verified at seal time |
| 7 | Literal answer transfer | **RULED OUT** — the frozen procedure contains no code and no instance-specific content |
| 8 | Researcher-authored procedure content | **CONTROLLED, not fully ruled out** — the prose wording is researcher-composed, but every substantive clause is mechanically traceable to a real TRAIN episode (§11), and notably does *not* match this investigator's own independently-held prior "ideal solution" (ast.parse-based validation), arguing the content tracks TRAIN evidence rather than general prior knowledge |
| 9 | Model-native knowledge | **UNRESOLVED** — cannot distinguish "P conveys new information" from "P reminds the model of a refinement it could already produce" |
| 10 | Evaluator weakness | **RULED OUT** — the same already-qualified evaluator (positive/negative/near-miss controls verified in the prior calibration mission) used identically across every arm |
| 11 | Retry pseudo-replication | **NOT APPLICABLE to held-out** (zero retries there); for TRAIN, no retry ever converted a failure into a success, so no pseudo-replicated success entered procedure derivation |
| 12 | Sampling noise | **CONTROLLED, not eliminated** — temperature=0, fixed seed; the perfect directional concordance across 9 total discordant pairs (P-vs-Z and P-vs-G combined) makes pure noise an implausible full explanation, though not impossible at this sample size |
| 13 | Task-generator bugs | **RULED OUT** — same, already self-checked generator used identically everywhere |
| 14 | Procedure extraction after seeing test results | **RULED OUT** — verified by real file timestamps: procedure frozen at 03:56:07, held-out results only begin at ~04:00:10 (§26) |
| 15 | Differences in prompt construction other than treatment | **RULED OUT** — `prompt.py`'s own self-check confirms `context=""` reproduces the original prompt byte-for-byte; only the `context` block differs across arms |
| 16 | P merely reminds the model of something it already knew | **UNRESOLVED** — identical to item 9; this is the single most important open question this experiment leaves unanswered |

**No counterfeit fully explains the result away, and two (items 9 and 16, which are the same underlying question) remain genuinely unresolved** — stated honestly, not minimized, per §1 and §23.

## 21. Negative evidence

Stated plainly, per this project's own standing discipline of reporting what does *not* support the headline finding: Signatures 2 and 3 (§19) do not discriminate P from G/Z — both are near-ceiling regardless of treatment, meaning two of the three taught clauses show no independently-observable behavioral difference in this specific pilot's held-out data, even though the outcome-level result (pass/fail) is clean. The G-vs-Z comparison shows no meaningful difference (§18), meaning generic instructions of the kind tried here provided negligible benefit over no instruction at all — a real, informative null within this same dataset. Three of eight real TRAIN episodes never succeeded even with one round of real corrective feedback (§8) — the experience-generation process itself was imperfect, not a clean, uniformly-successful teaching signal.

## 22. Limitations

Single task family, single difficulty level, single model, n=10 held-out instances — a real pilot, not a confirmatory trial; the McNemar p-values reflect this (§18). The path-relocation incident (§6) is a real, disclosed apparatus wrinkle, though it did not touch held-out content and was caught before any held-out call. Signature 1's clean separation, while genuinely striking, is itself only one experiment's worth of evidence from one model on one task family — it should not be read as a general property of "teaching improves code" beyond this specific, narrow setting. The G treatment's own content, while judged carefully (§13), required one real mid-construction correction (removing an item too close to P's substance) — a reminder that constructing a genuinely "generic" counterfeit is itself a real design judgment call, not a mechanical process. This experiment cannot and does not distinguish new-information-conveyed from latent-capability-reminded (§20, items 9/16) — this is the single most important open limitation, not a minor caveat.

## 23. Exact scientific interpretation

Per §3's claim boundary, held to exactly: **information derived from independently evaluated prior experience (real, F2-graded TRAIN episodes) and retained across a fresh-context boundary caused improved held-out performance on unseen instances from the same task family, at the FeralEcho system level, corroborated by independent, code-level behavioral evidence specifically tied to the taught content.** This is not shortened to "Echo learned." It does not establish model-weight learning, general learning, transfer outside this family, autonomous learning, accumulation, or repeated competence growth. It leaves genuinely open whether the mechanism is "new information conveyed" or "latent capability reminded."

## 24. Recommended next experiment

Per the governing mission's own explicit Phase 19 instruction (do not skip ahead, do not build Approach 2 infrastructure yet): **the next scientific question should be whether this effect reproduces on a second, structurally distinct task family** — a different kind of Level-3-equivalent difficulty (not another boundary-detection variant), calibrated fresh using the exact same methodology already proven twice this session (evaluator qualification with positive/negative/near-miss controls, a pre-declared difficulty ladder, a real zero-teaching baseline check before committing further compute). Only after an independent replication on a second family should generalized procedure infrastructure be considered, and only after that should a genuine accumulation design (Experience 1 → retained improvement 1 → Experience 2 → retained improvement 2, while improvement 1 remains intact) be attempted — not before.

## 25. Files created

- `app/experiments/validated_experience_competence_transfer/__init__.py`
- `app/experiments/validated_experience_competence_transfer/CONTRACT.md` — the frozen experimental contract, written before any instance generation
- `app/experiments/validated_experience_competence_transfer/prompt.py` — the extended, self-verified prompt builder
- `app/experiments/validated_experience_competence_transfer/run.py` — seal/experience/heldout orchestrator (includes the disclosed path-bug fix, §6)
- `app/experiments/validated_experience_competence_transfer/freeze_procedure.py` — procedure extraction + mechanical provenance verification
- `app/experiments/validated_experience_competence_transfer/freeze_generic_tip.py` — the G treatment
- `app/experiments/validated_experience_competence_transfer/consumption_signatures.py` — the pre-declared, deterministic consumption-evidence detector (includes the disclosed detector-bug fix, §19)
- `memory/experiments/validated_experience_competence_transfer/train_tasks.json`, `heldout_tasks.json`, `heldout_commitment.sha256`, `experience_log.jsonl`, `procedure_frozen.json`, `procedure_hash.txt`, `generic_tip_treatment.json`, `heldout_results.jsonl` — real, sealed/frozen data, all preserved for independent reconstruction
- This report: `audits/2026-09-23_validated_experience_competence_transfer.md`

## 26. Final state-integrity verification

- **Closing HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` — equals opening HEAD.
- **Working-tree comparison:** only one new untracked entry, `app/experiments/validated_experience_competence_transfer/` (the directory as a whole).
- **Every created file enumerated:** §25, cross-checked directly against a fresh `find` listing.
- **No unrelated experiment disturbed:** confirmed by direct code review — nothing in this mission's own code references `accumulation_probe`, `rung1`, `minimal_procedure_transfer`'s own data files, or `historical_difficulty_calibration`'s own data files (only its `tasks.py` source module is imported, read-only, never its data outputs).
- **P/G/Z raw data verified available:** `heldout_results.jsonl` contains all 30 real records (10 tasks × 3 arms), directly re-read for §17-19's own tables, not summarized from memory.
- **Held-out commitment re-verified against the final held-out set:** `a35c0807cc505ed4d192b44f17b2705427ccf8e3a46af374557e60d9a8c90055` — matches exactly (§7, re-confirmed at report time).
- **Procedure hash re-verified:** `21fde9b5dbe026489ef8f3ff47f974c816ca706944cde251b2501ed7f541f3c8` — matches exactly.
- **Real, monotonic timestamps confirming no post-hoc tuning:** `train_tasks.json`/`heldout_tasks.json` created 03:51:36 → `experience_log.jsonl` 03:52:22 → `procedure_frozen.json` 03:56:07 → `generic_tip_treatment.json` 03:57:19 → `heldout_results.jsonl` 04:00:10 — a clean, strictly increasing sequence.
- **The one real, disclosed discrepancy** (the path-relocation incident, §6) **is reported here plainly, not silently repaired and hidden** — the real data was moved, not regenerated, and its integrity was independently re-verified via the unchanged commitment hash.
- **A real FeralEcho production instance (`run.py` PID 62205, watchdog PID 48319) was confirmed running throughout and was never signaled, restarted, or interfered with.**

---

## The 25 required questions, answered explicitly

**1. Was the held-out set sealed before experience began?** Yes — commitment hash computed and recorded before `cmd_experience()` was ever run (§7, timestamps in §26).

**2. Was P derived exclusively from permitted TRAIN information?** Yes, mechanically verified — every clause's cited episodes checked against the real `experience_log.jsonl` at freeze time (§11).

**3. Did P contain any held-out information?** No — P was frozen (03:56:07) before any held-out call was made (04:00:10 onward); the procedure-authoring process never read `heldout_tasks.json`'s content.

**4. Did P survive a genuine fresh-context boundary?** Yes — every held-out call is a fresh, single-turn request with no shared history (§15).

**5. What were P, G and Z pass rates?** P=10/10 (100%), G=6/10 (60%), Z=5/10 (50%) (§17).

**6. What were the paired P-vs-Z discordances?** 5 favor P, 0 favor Z (§18).

**7. What were the paired P-vs-G discordances?** 4 favor P, 0 favor G (§18).

**8. Did P meaningfully outperform Z?** Yes, directionally and cleanly (100% vs 50%, zero counter-discordances), though the two-sided McNemar p (0.0625) does not cross the conventional 0.05 threshold at this small sample size — the one-sided, pre-registered-direction test does (p=0.03125).

**9. Did P meaningfully outperform G?** Yes, directionally (100% vs 60%, zero counter-discordances), with the same small-sample caveat (two-sided p=0.125, one-sided p=0.0625).

**10. Did G outperform Z?** Marginally (60% vs 50%), not significantly (p=1.0) — consistent with negligible generic-instruction benefit in this pilot.

**11. Is there independent behavioral evidence that P changed strategy?** Yes, decisively — Signature 1 (complete keyword set) shows a perfect 10/10 vs 0/10 vs 0/10 separation (§19), the strongest single piece of evidence in this report.

**12. Did the procedure convey information actually acquired during TRAIN?** Every substantive clause is mechanically traceable to a real TRAIN episode's own failure/success (§11) — yes, by this experiment's own provenance standard.

**13. Could generic instruction following explain the result?** No — G's own performance (60%) and G's own code (0/10 on Signature 1) both argue against this (§20, item 1).

**14. Could model-native knowledge explain the result?** Partially, and this remains genuinely unresolved (§20, items 9/16) — the model may already possess the refinement latently; P may only be reminding it, not teaching it something wholly new.

**15. Could instance-difficulty variance explain the result?** No — the paired design uses identical held-out instances across every arm (§20, item 4).

**16. Could contamination explain the result?** No — fresh, disjoint, programmatically-verified seeds (§20, item 6).

**17. What is the strongest remaining counterfeit explanation?** The "reminder of latent capability, not new information" explanation (§20, items 9/16) — genuinely unresolved by this design.

**18. Does the result establish experience-derived same-family transfer?** Yes, at the precision stated in §23 — a real, corroborated, but small-sample pilot result.

**19. Does it establish FeralEcho system-level acquired competence?** Only in the narrow sense §3/§23 define (a real, measured improvement on held-out same-family instances) — not a broader claim.

**20. Does it establish model-level learning?** No — the model's weights are unchanged; this is a context-level, system-architecture effect.

**21. Does it establish generalized transfer?** No — single family, single level, untested outside this exact scope.

**22. Does it establish accumulation?** No — a single episode, no second learning cycle was attempted (§24).

**23. What is the strongest scientifically defensible claim?** Exactly the sentence in §1/§23: experience-derived, independently-validated, retained information caused a measured, code-level-corroborated improvement on held-out same-family instances at the system level — nothing broader.

**24. Which link in EXPERIENCE → EVALUATION → EXTRACTION → RETENTION → CONSUMPTION → EXECUTION appears weakest?** None appears broken; if any is comparatively weaker, it is EXTRACTION — 3 of 8 real TRAIN episodes never reached a validated success even after one retry, meaning the procedure was extracted from a mix of real successes and real, uncorrected failures, not from a clean, uniformly-successful teaching signal — this did not prevent a strong result here, but it is the least "clean" link in this specific run.

**25. Should this phenomenon now be replicated, rejected, or investigated further?** **Replicated** — on a second, structurally distinct task family, per §24, before any larger infrastructure is built.

---

# Gremlin — What Actually Happened?

- **Did experience make the later Echo measurably better?** Yes, on this one specific kind of task. Given a text-boundary-detection problem it hadn't seen, with the lesson from 8 real practice attempts in hand, it solved 10 out of 10 fresh test cases it had never seen before. Without that lesson, it solved 5 out of 10.
- **Was it better than simply giving generic advice?** Yes. Generic, reasonable-sounding advice ("read carefully, consider edge cases, keep it simple") only got it to 6 out of 10 — barely better than nothing at all (5/10). The specific, earned lesson did meaningfully better than the generic pep talk.
- **How large was the difference?** 100% vs 50% (no teaching) vs 60% (generic advice). Every single case where the taught version and an untaught version disagreed, the taught version won — there wasn't one case where teaching made things worse.
- **Did Echo actually behave differently?** Yes, and I checked this the hard way — not by asking it, but by reading its actual generated code. Every one of the 10 taught responses checked for four different ways real code can start (decorator, docstring, import, or def/class). Every one of the 10 untaught responses, and every one of the 10 generic-advice responses, never checked for all four — not once, in either group. That's a real, visible fingerprint of the lesson actually landing in the code, not just a lucky string of right answers.
- **What alternative explanation worries you most?** That the lesson didn't teach it anything new — it just reminded it of something it was already capable of doing but wouldn't bother doing unless prompted. I can't tell those two apart from this experiment. Both would look exactly like what I saw.
- **What did this experiment NOT prove?** That Echo "learned" in any general sense, that this would work on a different kind of problem, that doing this twice in a row would make it even better a second time, or that anything about its actual model weights changed. This was one narrow skill, tested once, on one kind of task.
- **If you had to bet research time on the next move, where would you put it and why?** Try the exact same thing on a second, genuinely different kind of task — not another version of "find the boundary in messy text," something structurally unrelated. If the same pattern shows up twice, on two different problems, that's a much stronger signal than one clean result on one problem, and it's cheap to check before building anything bigger.
