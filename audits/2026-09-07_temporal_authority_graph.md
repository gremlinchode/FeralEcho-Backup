# Echo's Temporal Authority Graph

Forensic archaeology mission, building on and re-verifying `audits/2026-09-07_consequence_authority_map.md` and `audits/2026-09-07_authority_boundary_deliberateness.md`. Every load-bearing claim below was re-checked directly against current source and real git history in this pass — prior-report claims are cited as such, not assumed.

## 1. Executive Finding

FeralEcho's authority architecture is not a single design — it is a sequence of independent, well-reasoned decisions made on different days, each correct in its own local context, that were never required to check themselves against decisions made on other days. Where a decision-maker had the full picture at write time (RiverBrain's Finding 10, the fitness gate's Finding 19), authority is genuinely deliberate and works. Where a decision was made about one class of thing (a duplicate-question filter, a task-type dispatch table) and a *later*, unrelated addition silently started passing through it, the old decision keeps governing the new producer with nobody having evaluated whether it should. This mission finds this is not a one-off (`seam_engine`) — it is a **recurring, git-provable pattern** that has independently occurred at least twice more, in a structurally identical shape, in this codebase's own history — and in one of those repeat cases, the project caught and fixed it, then let the identical failure mode recur a second time before catching it again.

## 2. Methodology

Direct `git log -S`/`-G`/`show` archaeology against the real commit history (HEAD `c5bf2e5f8913e35a1ded9af8afe68e247651e26d`, 200+ commits), direct source reads of every function cited, and cross-reference against CLAUDE.md's own dated Findings index. No claim below is carried forward from a prior audit without being independently re-derived here. Temporary analysis was done via ad hoc `git log`/`python3 -c` one-liners in the shell — no standalone script files were created; none were needed.

## 3. Safety Verification

- `run.py`/watchdog: confirmed not running before starting (`ps aux`), port 5000 confirmed unbound (`lsof -ti :5000` → empty).
- Git HEAD: `c5bf2e5f8913e35a1ded9af8afe68e247651e26d` — confirmed identical at start; this mission made zero commits, zero amends.
- `river_brain.pkl` sha256: `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` — unchanged (this mission never touched it; RiverBrain was never imported or called).
- No production source modified. No self-edit run. No RiverBrain learning calls. Only this report file was created.

## 4. Authority Graph — The Eight Known Mechanisms, Re-Verified

| Producer | Intermediary | Consumer | Decision | Mutation | Authority | Created | Evidence |
|---|---|---|---|---|---|---|---|
| `RiverBrain.learn()` | `model_task_stats[model][task_type]` dict | `score_model()` (`echo_model_orchestrator.py:995`) | `rank_models()`'s sort by `combined[model]` (line ~1220) | Council ranking order changes | **YES** | `score_model()` existed since day one (`44e7a8e`, 2026-06-28) but returned an identical synthetic-probe value for every model; Finding 10 (2026-07-08) rewired it to real per-`(model,task_type)` history. Re-verified: `score_model` function body dates from the initial commit; its *authority* dates from Finding 10's rewrite. |
| Same `model_task_stats` | Same | `_select_council()` (`river_deliberation.py:532-558`) | Own docstring: ranks by `score_model()`, applies boosts, takes top N | Actual council membership changes | **YES** | Second independent consumer, same Finding 10 fix. |
| `council_rater.rate_one_entry()` | `is_council_trusted()` gate (`council_rater.py:525`) | `learn_from_council_rating()` (`echo_model_orchestrator.py:936`) | `_blend_council_and_quality()` computes a blended label, written into `model_task_stats` | Same downstream authority as the row above, now fed by a second real producer | **YES** | Finding 67 (2026-07-22) — confirmed live: `council_rater.py:300` calls it, gated at line 297 by `is_council_trusted()`, itself flipped by `_check_and_set_trust()`'s compound threshold comparison (`council_rater.py:530`). |
| `_score_response_quality(code, "coding")` × 2 (candidate, production) | none — direct comparison | `execute_self_edit()` | `if candidate_quality < current_quality:` (`self_edit_manager.py:2179`) | Deploy vs. reject-not-improvement | **YES** | Finding 19 narrates "fixed 2026-07-10," but `git log -S "candidate_quality"` against this exact code resolves only to commit `3e24186` (**2026-07-12**), not 07-10 — see §13 for this discrepancy, kept separate from the drift findings below since it does not involve a later-arriving producer. |
| `update_question_quality()` | `entry["resolution_score"]`, monotonic (`min(5.0, cur + q*0.5)`) | `select_from_garden()` | `weight += max(0, 5 - resolution)` then `random.choices(..., weights=weights)` | Which garden question gets asked next | **YES, one-directional** | `select_from_garden()` dates to `44e7a8e` (day one); re-verified `resolution_score` can only rise, confirmed at `garden_manager.py:245-247`. |
| `self_edit_attempt_ledger.record_attempt()` | own file, own lock | **none** | — | — | **NO** | Built tonight, commit `c5bf2e5`. `grep -rn "record_attempt(" app/ run.py` outside the module's own two files: zero hits, re-confirmed. |
| `check_and_correct()` → `corrected_task` | `shadow_corrections.log` | `night_cycle.py:182` reads `corrected`, feeds one `logging.warning()` | none | none | **NO** | Confirmed by direct read: `night_cycle.py:175-186`, the entire consumption is a log line. `propose()` (the call that would grant authority) is not called anywhere in `check_and_correct()` — confirmed by reading the full function body. |
| `seam_engine.observe()` | `_is_near_duplicate()` (`garden_manager.py:125-155`) | `harvest_question()` | Jaccard overlap ≥ 0.7 against ALL active entries, regardless of `category`/`source` | Garden entry created or silently dropped | **NO (see §7 — temporal drift)** | 754 real detections, 78 `first_ever`, 2 survive (re-counted directly from `memory/seam_log.jsonl` and `data/question_garden.jsonl` this pass — matches prior counts exactly). |
| `retrieve_relevant_memories()` | FAISS cosine search | 9 real call sites system-wide (`echo_ground_truth.py`, `emergent_scheduler.py`, `curiosity_engine.py`, etc.) — but zero in `self_edit_manager.py` | Top-k by cosine score, no relevance filter | Prompt content varies | **PARTIAL** | Re-confirmed `grep -c "retrieve_relevant_memories(" app/core/self_edit_manager.py` → 0. Read where it *is* consumed; the read is real, but per tonight's Retrieval Capacity Proof, cosine rank doesn't track causal relevance. |

**A ninth row worth adding**, discovered in this pass (§8): `TASK_TYPE_MAP` (two independent copies, `echo_model_orchestrator.py:717` and `echo_quality_scorer.py:495`) → consumed by `_extract_quality_features_v2()` to compute `task_type_id`, which feeds the RiverBrain quality-scoring path above. This is authoritative (it changes a real feature value fed into scoring), but its authority has drifted at least twice — see §7.

## 5. Authority Timeline (git-verified, no fabricated dates)

```text
2026-06-28  44e7a8e   Initial commit. select_from_garden() weighting, score_model()
                       (unauthoritative synthetic form), harvest_question(),
                       retrieve_relevant_memories() (never wired into self-edit),
                       echo_quality_scorer.py all present from day one.
2026-07-03  (comment)  Shadow model's propose() removal decided — dated in the
                       in-code comment, two days before the commit lands.
2026-07-05  ea81132    "shadow model disconnection" — Shadow's non-authority
                       becomes an explicit, committed decision.
2026-07-08  (Finding10) score_model() rewired to real model_task_stats; RiverBrain
                       authority over council selection begins here.
2026-07-10  (Finding19) Fitness-gate comparison narrated as added (see §13 —
                       the exact code's earliest commit is 07-12, not 07-10).
2026-07-12  3e24186    Busy commit: adds _is_near_duplicate() to the garden
                       (general dedup, no seam awareness — could not have any,
                       seam_engine does not exist yet), AND the current
                       candidate_quality < current_quality gate text.
2026-07-16  47ccbcd    "self_edit_coding": 5 added to echo_model_orchestrator.py's
                       TASK_TYPE_MAP. echo_quality_scorer.py's separate copy is
                       NOT updated in this commit — drift begins.
2026-07-16  0c8e903    seam_engine.py introduced — 4 days after the duplicate
                       filter (3e24186) it will silently lose 76/78 detections to.
2026-07-22  (Finding67) learn_from_council_rating() wired into rate_one_entry(),
                       gated on is_council_trusted() (itself set by a compound
                       threshold comparison, council_rater.py's own second real
                       authority-by-comparison instance).
2026-07-23  6d98e18    echo_projects_coding added to BOTH TASK_TYPE_MAP copies —
                       and self_edit_coding, still missing from the scorer's
                       copy since 07-16, is finally added in the SAME commit.
                       7 real days of silent mis-scoring closed in one pass.
2026-09-06/07 (tonight) Attempt ledger built (c5bf2e5) — deliberately non-authoritative,
                       same posture as Shadow, by explicit choice.
```

## 6. Reconstructing the Comparison-Holds-Authority Pattern

The prior audit's finding — "authority resides in the `<` comparison, not either score alone" — **generalizes**. A second, independent instance exists: `council_rater._check_and_set_trust()` computes a compound comparison (`total_rated >= 50`, `spot_checks_completed >= 10`, `agreement_rate >= 0.70`, confirmed by reading `is_council_trusted()`/`_check_and_set_trust()` at `council_rater.py:525-530`) that flips `council_baseline_trusted_since` from unset to set. Neither `agreement_rate` nor either raw count has any power alone — the compound `>=` comparison is what actually grants `learn_from_council_rating()` the right to run. Two real, independently-discovered cases in one codebase is enough to treat "authority attaches to a comparison operator, not a scalar" as a real architectural pattern here, not a one-off observation about the fitness gate specifically.

## 7. Temporal Authority Drift — The Core Investigation

Applying the mission's five-way test (A: genuine drift / B: ordinary bug / C: deliberate constraint / D: pure absence / E: deliberate withholding) to every candidate found:

### 7.1 `seam_engine` → garden duplicate filter (re-confirmed, Category A)

- **Chronology, git-verified**: `_is_near_duplicate()` added in `3e24186` (2026-07-12 22:17:15 -0700). `seam_engine.py` added in `0c8e903` (**2026-07-16**, not 07-18 as the immediately-prior audit's own body text still states — corrected here). **Gap: 4 days**, not six.
- `_is_near_duplicate()`'s own docstring (read in full this pass, `garden_manager.py:125-142`) explains its purpose precisely: stopping *lexically similar but differently-worded* questions from accumulating, citing "Who am I?" vs "Who am I, really?" as the motivating example — a real, well-reasoned, self-contained decision about general garden content quality.
- The function iterates over **every** `status == "active"` entry with zero regard for `category` or `source` — confirmed by direct read of the loop (`garden_manager.py:146-154`), even though `seam_engine.py:250,264` passes both `category="seam"` and `source="seam_engine"` at the call site — the data needed to exempt seam-sourced content exists on every entry, and is simply never consulted by this function.
- **Category: A (genuine temporal authority drift) — high confidence.** The filter's author (per commit `3e24186`'s own message and diff) could not have evaluated seam-specific behavior, because seam attribution did not exist. This is not Category B (the filter works exactly as designed for its actual purpose) or Category C (nobody decided seam questions specifically should be filtered this way — no evidence that decision was ever made).
- **Revalidation**: none found. `git log --all -- app/core/garden_manager.py` shows no commit since `3e24186` touches `_is_near_duplicate()`'s body or adds a category-aware exemption.

### 7.2 `TASK_TYPE_MAP` drift — a second, independently git-verified case, and a recurring one (Category A)

This is the most important new finding of this mission. Two separate, independently-maintained copies of the same dispatch dictionary exist:

- `echo_model_orchestrator.py:717` — the canonical map, read by `RiverBrain.learn()` and the model-selection path.
- `echo_quality_scorer.py:495` — a second, separately-hardcoded copy, read by `_extract_quality_features_v2()` to compute `task_type_id`, one of the real features feeding the quality score that RiverBrain trains on (a direct upstream input to the AUTHORITATIVE row 1 of §4).

Both currently read `{"general": 0, "coding": 1, "creative": 2, "personal": 3, "reasoning": 4, "self_edit_coding": 5, "echo_projects_coding": 6}` — identical, in sync, as of `HEAD`. But the git history shows this was **not always true**, and the gap was not hypothetical — it produced real, silently-wrong feature values for a real span of days:

```text
2026-07-16  47ccbcd   "self_edit_coding": 5 added to the CANONICAL map only.
                       echo_quality_scorer.py's copy is untouched — it has no
                       entry for self_edit_coding, so
                       TASK_TYPE_MAP.get(task_type, 0) silently returns 0
                       (the same code as "general") for every real self-edit-
                       coding quality-scoring call in this window.
2026-07-23  6d98e18   Both self_edit_coding AND the newly-needed
                       echo_projects_coding are added to the scorer's copy,
                       in the same commit — the older, 7-day-old gap only
                       gets closed because a fresh producer (echo_projects_
                       coding) forced a fresh audit of the same file.
```

- **Producer existed at constraint-creation time? No** — `self_edit_coding` (the new producer) postdates the scorer's last edit to its own `TASK_TYPE_MAP` copy (last touched at `3e24186`, 2026-07-12) by 4 days.
- **Was it ever explicitly considered? No** — commit `47ccbcd`'s diff (confirmed by direct `git show`) touches only `echo_model_orchestrator.py`; `echo_quality_scorer.py` is untouched in that commit.
- **Revalidated? Yes, but only as a side effect** — commit `6d98e18`'s own message is about `echo_projects` autonomy, not about auditing the scorer's map; CLAUDE.md's Finding 85 (read this session) confirms this directly: *"echo_quality_scorer.py has its own second, independently-drifted local TASK_TYPE_MAP copy — its own comment already admits it drifted once for 'reasoning' and was patched, but it was still missing 'self_edit_coding' entirely."*
- **This sentence is the single most important piece of evidence in this whole report**: this project's own comment, written by an earlier session, already documents that this exact failure mode (a duplicated dispatch table silently missing a newer producer) had happened **once before**, for `"reasoning"`, was caught and patched — and then the *identical* failure mode recurred, undetected, for `self_edit_coding`, until a third, unrelated producer's addition accidentally surfaced it again.
- **Category: A (genuine temporal authority drift), high confidence, and — uniquely among everything in this report — self-documented as a recurring pattern by the project's own prior comments**, not just discovered by this investigation.
- **Test coverage**: none. `grep -rln "TASK_TYPE_MAP" scripts/verify_*.py` returns zero files. No liveness check or verification script would catch a third recurrence if a fourth task type is ever added to one map and not the other.

### 7.3 Fitness gate date discrepancy — checked, does NOT qualify as drift (Category: not applicable)

Investigated because the exact commit date (`3e24186`, 2026-07-12) didn't match Finding 19's narrated "fixed 2026-07-10" — but `git log -G "candidate_quality"` (regex, catching renames/reformatting, not just the exact literal string) also resolves only to `3e24186` as the earliest touch. No evidence of an earlier, differently-named version of this same gate. **Interpretation, Medium confidence**: most likely explained by this project's own repeatedly-documented "doc lags commit" pattern (CLAUDE.md itself calls this out as a recurring, self-acknowledged gap multiple times) rather than any drift in the gate's actual authority — the gate has had one producer (self-edit quality comparison) since it was written, with no second producer ever arriving later to collide with it. Recorded here as a discrepancy worth knowing, not as a drift finding — it fails the mission's own Category-A bar because there's no second, later-arriving producer involved.

### 7.4 Searched, not found: other candidates

Checked and ruled out as genuine drift (Category B/D, or simply not present):
- `memory_write_validator.py`'s `_ALWAYS_EXCLUDED_MEMORY_CATEGORIES` — confirmed (via CLAUDE.md's own `code_analysis_retrieval_exclusion` liveness-check comment, read this session) that this set was *extended* deliberately when `self_model_reflection` was identified as a second contaminating category, with an explicit dated comment — this is the *opposite* of drift: a case where revalidation genuinely happened.
- `_FOCUS_FAMILY_BY_CREATIVITY` (self-edit family selection) — families are commented out (not silently ignored) when retired (`prose_stripping`, `quality_scoring`), each with a dated Finding citing the reason. Deliberate, not accidental.
- RiverBrain's `_RETIRED_MODELS`/`crash_awareness.py`'s avoidance set — both are allowlist/denylist-shaped mechanisms, but both are actively, deliberately maintained per dated Findings (39, 51) with no evidence of a later producer silently colliding.

## 8. Authority Blast-Radius Ranking

| Rank | Mechanism | Producers affected | Severity | Silent? | Would a test catch it? |
|---|---|---|---|---|---|
| 1 | `TASK_TYPE_MAP` duplication | Any RiverBrain-scored task type added to one map and not the other — 2 confirmed real occurrences (`reasoning`, `self_edit_coding`), structurally open to a 3rd/4th | High — corrupts a real ML feature feeding the system's one clearly-working continuous-authority mechanism | Yes — `TASK_TYPE_MAP.get(task_type, 0)` fails silently to a default, no exception, no log line | No — zero test coverage found |
| 2 | Garden `_is_near_duplicate()` | Currently only `seam_engine` (2 sources total: `general`-sourced organic questions, and `seam`-sourced) but structurally open to any *future* `harvest_question()` caller too, since the filter is category/source-blind by construction | High for the affected producer (97.4% loss) but narrow in current blast radius (1 known victim) | Yes — `logging.debug()` only, no warning, no metric | Partially — `_evaluate_seam_engine`'s liveness check tests `check_pair()`'s own discrimination, never touches `harvest_question()` or the filter, so no |
| 3 | Fitness-gate date discrepancy | None — investigated and ruled not a blast-radius case (§7.3) | N/A | N/A | N/A |

## 9. Silent Authority Loss — Pipeline Trace

Applying `GENERATED → PERSISTED? → READ? → TRANSFORMED? → FILTERED? → RANKED? → DECIDED? → MUTATED? → OBSERVABLE CONSEQUENCE?` to the two drift cases:

- **`seam_engine`**: GENERATED (yes, `check_pair()`) → PERSISTED (yes, `seam_log.jsonl`, every cycle) → READ (yes, by `observe()` itself for the `first_ever` decision) → **FILTERED (first loss point: `_is_near_duplicate()`, 76/78)** → RANKED (only for the 2 survivors, via `select_from_garden()`) → DECIDED/MUTATED/OBSERVABLE (only for those 2). First loss point is the FILTERED stage, precisely as the prior audit found — re-confirmed, not merely repeated.
- **`self_edit_coding` quality scoring, 2026-07-16 to 2026-07-23**: GENERATED (a real self-edit-coding response) → **TRANSFORMED (first loss point: `_extract_quality_features_v2()`'s `TASK_TYPE_MAP.get(task_type, 0)` silently substitutes the wrong feature value)** → the resulting (wrong) feature still flows all the way through to DECIDED/MUTATED (RiverBrain still learns from it, just from corrupted input) — this is a case where authority was never *lost*, it was *silently misdirected*, a more dangerous shape than seam_engine's clean drop, since nothing downstream had any way to detect the corruption.

## 10. Provenance Analysis

| Mechanism | Classification | Evidence |
|---|---|---|
| `_is_near_duplicate()` | **Provenance-agnostic** | Loop body reads only `e["question"]`; `category`/`source` fields exist on every entry (confirmed present in `harvest_question()`'s own entry-construction, `garden_manager.py:188+`) and are never read by this function. |
| `echo_quality_scorer.py`'s `TASK_TYPE_MAP` lookup | **Provenance-agnostic, with a silent default** | `.get(task_type, 0)` — worse than pure agnosticism, since an unrecognized producer doesn't get rejected or flagged, it gets *reclassified* as `"general"` (id 0) without anyone knowing. |
| `select_from_garden()`'s weighting | **Provenance-aware, partially** | Reads `entry.get("source") == "human"` for a real bonus term (confirmed in the function body) — so the mechanism *can* discriminate by provenance, it simply was never extended to discriminate `seam` specifically the way it already does for `human`. |
| RiverBrain's `model_task_stats` | **Provenance-aware by construction** | Keyed by `(model_name, task_type)` — provenance (which model, which task type) is the literal index structure, not an afterthought. |
| Attempt ledger | **N/A — provenance-destroying is moot, since nothing consumes it** | — |

## 11. Test Coverage Analysis

Distinguishing "this exists" tests from "this changes the system" tests, per the mission's own framing:

- `scripts/verify_seam_engine.py` and the liveness ledger's `_evaluate_seam_engine` (`liveness_ledger.py:1338`) — **exists-tests**: they prove `check_pair()`'s correlation math still discriminates correctly. Neither calls `harvest_question()`, neither checks whether a `first_ever` seam actually reaches the garden. A silent regression from "2/78 survive" to "0/78 survive" would pass both checks unchanged.
- `TASK_TYPE_MAP` — **zero coverage of any kind**. No test asserts the two copies match, no test asserts every key in one exists in the other. This is the more consequential gap: the seam_engine loss is at least *logged* (`logging.debug`); a `TASK_TYPE_MAP` drift produces no log line, no exception, nothing — pure silent misclassification.
- RiverBrain/fitness-gate/council-blend — real functional canaries exist in `liveness_ledger.py` (`_evaluate_apply_to_code`-style patterns) confirming these paths fire and produce non-trivial output; these are genuinely closer to "changes the system" tests, though none specifically assert that a *changed* `model_task_stats` value produces a *different* selection outcome end-to-end.

## 12. Confidence-Rated Findings Summary

| Finding | Evidence | Interpretation | Confidence |
|---|---|---|---|
| `seam_engine` loss is temporal drift, not a bug | `3e24186` (07-12) predates `0c8e903` (07-16) by 4 days, confirmed via `git log --diff-filter=A` | Filter author could not have considered seam attribution | **High** |
| `TASK_TYPE_MAP` drift is a recurring pattern, not a one-off | `47ccbcd` (07-16) touches only the canonical map; `6d98e18` (07-23) fixes both copies at once; CLAUDE.md's own Finding 85 comment states this happened once before for `"reasoning"` | Duplicated dispatch tables are a structurally recurring failure shape in this codebase specifically | **High** |
| Fitness-gate's real introduction commit is 07-12, not Finding 19's narrated 07-10 | `git log -S`/`-G` on the exact code, both resolve only to `3e24186` | Most likely a doc-lags-commit artifact, not evidence of a second producer colliding | **Medium** — intent not fully recoverable from repository evidence alone |
| Authority-by-comparison generalizes beyond the fitness gate | `council_rater.py:525-530`'s `is_council_trusted()`/`_check_and_set_trust()` is a second, independent instance | A real, if small, architectural pattern: at least two gates in this codebase grant authority via a compound comparison, not a stored scalar | **High** |
| No test would catch a `TASK_TYPE_MAP` divergence | `grep -rln "TASK_TYPE_MAP" scripts/verify_*.py` → zero | This is the largest un-guarded blast radius found in this pass | **High** |

## 13. Final Conclusions

**A. How many authority boundaries are genuinely deliberate?** 6 of the 9 rows in §4 (RiverBrain ×2 read paths counted once as one deliberate decision, council-blend, fitness gate, garden weighting, and — new this pass — the trust-threshold gate) are DELIBERATE-WIRED, each with a dated Finding or, for garden weighting, dated to original day-one authorship.

**B. How many are deliberately withheld?** 2 — Shadow's `corrected_task`, tonight's attempt ledger. Both have an explicit, quoted rationale in-repo.

**C. How many are unfinished/pure absence?** 1 — `retrieve_relevant_memories` in `self_edit_manager.py`, confirmed still untouched since the initial commit.

**D. How many represent temporal authority drift?** 2, both git-provable: `seam_engine` vs. the garden duplicate filter, and `TASK_TYPE_MAP`'s two-copy divergence (which has independently recurred twice, per the project's own prior comment).

**E. How many other accidental authority failures exist?** None found beyond D and C above after the Section 7.4 search — several plausible candidates were checked and ruled out as deliberate/maintained, not accidental.

**F. Which generic constraints have the largest authority blast radius?** `TASK_TYPE_MAP`'s duplication — it has already silently corrupted real training-feature data twice and has no structural protection against a third recurrence, versus `seam_engine`'s constraint which currently has exactly one known victim.

**G. Which producers are most vulnerable to provenance-blind decisions?** Any future `harvest_question()` caller that isn't `category="general"`-shaped (the filter has no allowlist, it will silently apply to whatever comes next); any future `TASK_TYPE_MAP` key added to only one of the two copies.

**H. Where does Echo currently detect information it cannot convert into consequence?** Shadow's `corrected_task` (deliberately) and the attempt ledger (deliberately) — both by design, not failure. `seam_engine`'s 76 lost detections are the one case where detection genuinely happens and consequence is genuinely, unintentionally lost.

**I. Where does Echo currently possess consequence authority that was deliberately granted?** RiverBrain's `model_task_stats` (two read paths, one shared write path from two producers), the self-edit fitness gate, the garden's resolution weighting, and the council-trust threshold gate.

**J. Which authority boundaries should be revalidated because the architecture has evolved since their creation?** `_is_near_duplicate()` (predates its one known victim by 4 days, never revisited since) and `echo_quality_scorer.py`'s `TASK_TYPE_MAP` copy (has drifted twice already, structurally guaranteed to drift a third time absent either a sync mechanism or a test).

## 14. Recommended Next Forensic Missions

Not a recommendation to build anything — per this whole investigation's standing discipline, these are proposed *next questions*, not proposed fixes:

1. A targeted, narrow investigation into whether any *other* duplicated dispatch table or allowlist/denylist pair exists elsewhere in the codebase with the same "two independently-maintained copies" shape as `TASK_TYPE_MAP` — this pass searched specifically for filters-that-predate-producers and found this case opportunistically while validating a different lead; a dedicated grep-and-verify pass for "same dict literal defined in two files" specifically might find more.
2. Whether a cheap, purely-observational liveness check (in the same spirit as this session's own attempt ledger — computed and logged, deliberately not given authority) could detect a future `TASK_TYPE_MAP` divergence the moment it happens, rather than waiting for an unrelated audit to stumble onto it 7 days later a third time.
