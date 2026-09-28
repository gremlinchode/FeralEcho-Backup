# VRM Retrospective Feasibility Investigation

**Read-only. Nothing built. No production, RiverBrain, self-edit, council/routing, or model configuration touched.** The central question, exactly as posed: *without designing signatures around the answers, does FeralEcho's historical independently verified failure corpus contain recurring structural failure classes for which knowledge derived only from earlier failures could have prospectively repaired or improved genuinely later unseen failures?* Short answer up front, unpacked below: **the recurrence signal is real and substantial, but the corpus cannot test the "repaired" half of that question at all — the actual failing source code was never preserved, only its traceback.** That single fact caps everything else in this report.

## 1. Provenance freeze

- Git HEAD: `2fba42644c82b9f7096276f4dd338d615cf1bcce`. Working tree: 206 porcelain entries (the same pre-existing set from earlier in this session, unchanged by this investigation).
- Corpus used: `memory/self_edit_attempt_ledger.jsonl` — 1,325 rows, SHA-256 `361d83f368f0e8fbd088880386d4c197cb4a7a2ddc2d3c517fb0ca892f5efc5e`, mtime 2026-09-22T14:07:20 (still receiving real writes from the live, running self-edit loop; the file is append-only and was not modified by this investigation — confirmed by re-hashing after analysis, unchanged). Real F2-failure timestamp range: 2026-09-07T12:55:42 to 2026-09-20T20:something (881 rows), with one stray row on 09-22.
- Also inventoried, not used as primary evidence (reasons below): `memory/SELF_EDIT.log` (162,967 lines, 28.9MB, narrative one-liners), `memory/self_edit_outcomes.jsonl` (194 rows), `memory/apply_to_code_invocations.jsonl` (3,596 rows), `audits/recursive_learning_ground_truth/*` (Codex's own prior synthetic-worker experiment, dated 2026-09-17).
- **Outcomes independently verified vs. self-reported:** `initial_f2_outcome`/`retry_f2_outcome`/`final_f2_outcome` are real, kernel-sandboxed pass/fail booleans from F2 (the same mechanism this project's own Liveness Ledger and prior findings already treat as ground truth, not self-report). `fitness_score`/`production_score` are the AST-complexity heuristic (Finding 91's recalibrated version, per its own docstring) — a proxy, not independent verification; not used for signature analysis here, only cited for context.
- **Timestamp/order trustworthiness:** timestamps are ISO datetimes written at row-append time by the live process; the file is strictly append-only (confirmed: re-checking mid-investigation showed only new rows appended at the end, no reordering). Chronological analysis is trustworthy.

## 2. Corpus identification and classification

| Record type | Count | Classification | Why |
|---|---|---|---|
| `terminal_state == "staging_import_failed"` (real F2 sandbox failure) | 863 | **USABLE VERIFIED FAILURE** | Real kernel-sandboxed exception, with full traceback text, real timestamp, real retry linkage. |
| `terminal_state == "success"` | 15 | **USABLE VERIFIED SUCCESS** | Cleared F1→F2→fitness gate→deploy for real. |
| `terminal_state == "safety_blocked"` (318) / `"import_hallucination"` (96) | 414 | **PARTIAL EVIDENCE** | Real, independently-checked rejections, but at the F1 static-scan layer, before F2 ever runs — no sandbox execution occurred, `initial_f2_outcome` is null. Structurally a different failure class (caught before execution) and excluded from the F2-failure signature analysis below to avoid mixing static-scan rejections with runtime tracebacks. |
| `terminal_state == "rejected_not_improvement"` | 33 | **PARTIAL EVIDENCE** | Passed F1/F2 but rejected by the fitness gate (Finding 19) — a real outcome, but not a "failure" in the code-repair sense this study cares about. |
| Actual generated source code per attempt | **0 recoverable** | **UNUSABLE — does not exist** | Checked directly, not assumed: `self_edit_backups/` is named by timestamp (not trace_id) and retains only the 25 most recent *deployed* (successful) versions by design (Finding 30's retention policy) — never failing candidates. `staging/` is a transient scratch directory, already overwritten by unrelated later work (confirmed: it currently holds adversarial F1-bypass test files from a different investigation, not self-edit history). `app/core/self_edit_plans/` holds the input *plan* text (also timestamp-named, capped at 500 per Finding 58), not the generated code. `memory/SELF_EDIT.log`'s entries are truncated one-line summaries with no code and, checked directly, essentially no trace_id linkage (119 trace_id-shaped substrings in 163K lines, not systematically joinable). `memory/apply_to_code_invocations.jsonl` records only `before_len`/`after_len`/`changed`/`error` by design (Finding 31/69) — deliberately never the code text, for safety reasons unrelated to this study. **This is the single most consequential classification finding in this report.** |
| `audits/recursive_learning_ground_truth/*` | — | **UNUSABLE for this study's central question** | Read enough to classify, not analyzed further: Codex's own report already discloses these use "authored fixed workers, not live Echo inference" — a controlled synthetic demonstration of credit assignment, not organic historical production failures. Real and relevant to the *reconciliation*'s broader argument, but doesn't bear on whether FeralEcho's *actual* self-edit failures cluster usefully. |

## 3. Chronological firewall — and an honest disclosure of a lapse

**Split, frozen before any signature-vocabulary design:** DEVELOPMENT = 2026-09-07 through 09-14 (492 real F2 failures), PROSPECTIVE-SIMULATION = 09-15 through 09-19 (298), HOLDOUT = 09-20 and 09-22 (91). Chosen for roughly even mass across three periods with enough data in each, before looking at what any period's specific signatures were.

**Disclosed lapse, per the instruction to downgrade rather than pretend independence:** before setting up this split, I ran one exploratory query across the *entire* date range (an exception-class and undefined-name frequency count over all 881 failures at once) to get oriented. That means I already knew, before freezing the DEV-only signature list below, that names like `log_call`, `HealthMonitor`, and `self_edit_generated` recur heavily across the whole corpus. **This weakens the investigator-blindness claim for the specific finding "these particular names recur" — I cannot claim I discovered that fact only from DEV data.** What I did *not* do: hand-pick or adjust the extraction method after seeing which categories "worked," or peek at PROSPECTIVE/HOLDOUT content before freezing the DEV-derived list used for the coverage test in Section 4. The extraction rule itself (exception class + the single quoted identifier in a standard Python traceback's last line) is a fixed, generic parse of Python's own exception format, applied identically and mechanically to all three periods — not tuned per-period. Net effect: treat the *qualitative* observation "the corpus has a small recurring vocabulary of hallucinated names" as **investigator-contaminated, real but not blind**; treat the *quantitative* DEV→PROSPECTIVE→HOLDOUT coverage numbers below as **genuinely computed under a real chronological split with a fixed, generic, pre-committed extraction method**, which is a meaningfully weaker but still real form of evidence — not equivalent to a true pre-registered blind test.

## 4. Testing the core clustering assumption (DEV period only, frozen before checking PROSPECTIVE/HOLDOUT)

Signature = `(exception_class, quoted_identifier_or_None)`, extracted from the last line of the real traceback — generic, not hand-designed per category.

- **492 DEV failures → 113 distinct signatures.** Signatures occurring ≥2 times: **46**, covering **425/492 = 86.4%** of DEV failure mass. This is a strongly skewed, non-uniform distribution — most of the corpus's mass sits on a small number of recurring signatures, not spread evenly across hundreds of unique ones.
- **Top DEV signatures** (frozen list, in full): `('NameError','log_call')` 120, `('RuntimeError',None)` 50, `('NameError','HealthMonitor')` 40, `('NameError','self_edit_generated')` 25, `('NameError','log_call_with_timestamp')` 23, `('ImportError','HealthMonitor')` 15, `('NameError','run_code_generator')` 12, `('NameError','app')` 12, `('ImportError','Scheduler')` 9, `('NameError','CodeGenerator')` 8, `('AttributeError','str')` 7, `('NameError','dataclass')` 7, `('NameError','generate_and_modify_code')` 6, `('ModuleNotFoundError','app.self_edit_outcome_tracker')` 6, `('TypeError',None)` 5.
- **Are recurring signatures meaningful, or superficial?** Mixed, checked directly rather than assumed either way. `('RuntimeError', None)` (the single largest bucket without a parsed identifier, 97 occurrences corpus-wide) is *not* a grab-bag once actually read: every sampled instance is the identical message, `"[metal::load_device] No Metal device available. This typically occurs in headless, sandboxed, or virtualized macOS sessions..."` — a genuine, tightly homogeneous recurring failure that my generic identifier-parser simply didn't extract a quoted name from. This is a *structural/environmental* failure (self-edit-generated code attempting an MLX/Metal call inside a sandbox that can never have GPU access), not a code-logic bug — and it directly matches this project's own **Finding 23**, which already investigated and deliberately declined to fix the adjacent case (`app.mlx_handler` imports permanently failing F2) as an accepted structural dead end, not something to keep re-solving. A repair-content mechanism is the wrong shape of fix for this signature; the right fix is "recognize and stop attempting," which VRM as sketched doesn't distinguish from a genuine repairable bug — a real gap in the mechanism's own self-model, not just in this data.
- **Are signatures too coarse, causing incompatible repairs to collide?** Likely yes for `('TypeError', None)` and `('RuntimeError', None)` more broadly (not individually re-verified beyond the Metal case above) — a bare exception class with no identifier is a genuine risk bucket. Signatures *with* a parsed identifier (the large majority of DEV mass) are narrow and specific by construction (a `NameError` for `log_call` is a different, non-colliding signature from a `NameError` for `HealthMonitor`), so this risk is concentrated in the identifier-less minority, not the bulk of the recurring mass.
- **Too narrow, causing almost no reuse?** No — 86.4% coverage within DEV itself shows the opposite problem isn't dominant.
- **Stability over time, and does different-task-family sharing occur?** Not applicable to "different task families" — every single row in this ledger is `task_type: "coding"` (self-edit only; this corpus cannot speak to cross-family generalization at all, a real scope limit). Temporal stability is measured directly next.
- **Does task text leak into the signature?** No — the signature is derived purely from the traceback's exception class and identifier, never from the originating prompt/plan text.

## 5. VRM claims ladder — where this corpus lands

- **VRM-0** (human-defined signatures + human-defined transformations): fully testable in principle with this corpus's traceback data alone; not attempted here (would require actually writing transformations, out of scope for a feasibility study).
- **VRM-1** (frozen/human signature vocabulary + experience-selected transformations): the recognition half is what Sections 4 and 7 actually test. The *selection* half (choosing which of several candidate transformations to apply, informed by which one worked before) cannot be tested, because no transformation was ever recorded — see below.
- **VRM-2** (transformations generated from earlier experience, independently validated before retention): **not testable from this history.** Generating a transformation requires the failing source code; validating it requires re-running it through F2. Neither the input artifact nor a repair attempt's code exists anywhere in the historical record (Section 2). This is the load-bearing limitation of the entire study.
- **VRM-3 / VRM-4**: not reachable without VRM-2 first being real; not testable here.

**Highest level this corpus can actually test: between VRM-0 and VRM-1, on the *recognition* question only** — "would a signature, defined before a later failure occurred, have matched that later failure" — never "would a stored repair have fixed it," because no repair content was ever captured.

## 6. Static doppelgänger

**The strongest boring competitor: a human reads a week of DEV-period logs and writes a fixed blocklist/normalizer for the top ~10 recurring names** (`log_call`, `HealthMonitor`, `self_edit_generated`, `log_call_with_timestamp`, `run_code_generator`, `CodeGenerator`, `Scheduler`, `dataclass`, `generate_and_modify_code`, `app.self_edit_outcome_tracker`) — e.g., "strip any decorator/call referencing these names, or reject with a clear message before wasting an F2 cycle." Given how concentrated the top signatures are (the single largest, `log_call`, is 2.4x the size of the second-largest parseable one), this is a completely plausible one-day human engineering task, requiring no chronological learning step at all.

**Verdict: PARTIALLY SURVIVES.** I cannot rule this out without building and testing it, which isn't authorized here, so I'm not overclaiming a defeat. What *would* distinguish real experience-dependent learning from this static doppelgänger, stated precisely rather than left vague: (a) **temporal drift** — Section 7 below shows real coverage decay from DEV to HOLDOUT (86%→66%→47%), meaning a list frozen once from DEV data alone would measurably *stop working* as well over time; a genuinely learning system should re-derive or extend its list as new signatures emerge, and a fixed static list, by construction, cannot. This is the one piece of evidence in this study that a *static* list wouldn't fully explain on its own — but it argues for "the vocabulary needs to keep updating," not yet for "VRM's specific proposed mechanism is what should update it." (b) A genuinely novel signature never present in DEV but recurring within PROSPECTIVE or HOLDOUT (Section 7 finds real examples) is exactly the case a frozen static list, written once, would miss and a live-updating mechanism would eventually catch — this is the sharpest available discriminator, and it's real, not hypothetical, in this data.

## 7. Retrospective prospective simulation (recognition only — repair could not be tested, per Section 5)

Using *only* the 46 DEV-frozen recurring signatures (Section 4), checked against PROSPECTIVE and HOLDOUT without modification:

| Period | Failures | Distinct signatures | Mass matching a DEV-frozen signature | Genuinely novel signatures (never in DEV) |
|---|---|---|---|---|
| PROSPECTIVE (09-15..19) | 298 | 95 | **197/298 = 66.1%** | 72 distinct, 101 occurrences |
| HOLDOUT (09-20, 22) | 91 | 33 | **43/91 = 47.3%** | 23 distinct, 48 occurrences |

Answering the six numbered questions from Section 7 of the mission, honestly bounded by the missing-code limitation:
1. **Would the earlier library have recognized the signature using only information available at failure time?** For 66.1% of PROSPECTIVE and 47.3% of HOLDOUT mass, yes — the exact (exception class, identifier) pair had already recurred ≥2 times strictly before that period began.
2. **Would it have selected a transformation learned without access to this later case?** Cannot be answered — no transformation was ever recorded for any signature, DEV or otherwise.
3. **Would that transformation actually repair the later artifact?** Cannot be tested — the later artifact's source code doesn't exist.
4. **Does the repaired artifact pass the real independent evaluator?** Not reachable without (2) and (3).
5. **Would the same repair have been available to the frozen baseline?** N/A, same reason.
6. **Computational resources consumed, VRM vs. baseline?** Not measurable retrospectively without a running comparison; conceptually, a matched-signature short-circuit would cost strictly less than a full model retry, but this is a design property, not something observed in the historical data.

**Net honest answer to "prospective signal":** recognition-level prospective signal is real and substantial (roughly two-thirds of near-term later failure mass, decaying to under half further out) — but this study cannot say whether recognizing it would have translated into an actual repair, because that half of the mechanism has no historical trace to test against.

## 8. Causal ablations

- **CORRECT vs. EMPTY**: directly measurable as recognition coverage vs. 0% (an empty library recognizes nothing by definition) — the 66.1%/47.3% figures above *are* this comparison, for the recognition question only.
- **CORRECT vs. SHUFFLED**: **not meaningfully testable** — shuffling requires transformations to shuffle, and none exist in this data. A degenerate version (shuffling which *signature* a failure is checked against) would trivially show near-zero coverage and adds no real information.
- **STATIC** (Section 6): partially assessed qualitatively; not built or measured quantitatively here.
- **RETRY baseline**: directly measurable from real historical data, and reported for context: blind-retry self-repair rate is **1.8% (DEV), 2.7% (PROSPECTIVE), 1.1% (HOLDOUT)** — low and not improving over time on its own. This is the real frozen baseline any future repair mechanism would need to beat, and it's a weak baseline (consistent with this project's own prior findings that the self-edit loop doesn't show convergence).
- **STRONGER-MODEL baseline**: no existing historical evidence permits this comparison (self-edit has used one fixed model family throughout the observed window); correctly not attempted, per instruction.

**Conclusion: `correct > empty` is the only ablation this history can actually support (for recognition only), and even that comparison cannot be extended to `correct > shuffled` or to any repair-quality claim.**

## 9. Was the abstraction itself learned?

**No — and this needs to be stated plainly, not softened.** The signature representation used throughout this report (exception class + quoted identifier from a standard Python traceback) is **infrastructure-supplied** (Python's own exception-formatting convention) combined with **programmer-supplied** (my regex, applied by me as the investigator). Nothing in FeralEcho's existing history ever discovered, proposed, or represented this abstraction on its own. The *content* that recurs (which specific names get hallucinated) is a real property of the data, but the *category system* used to notice that recurrence was designed by a human reading the data, exactly the "manually invent categories" risk the mission warned against — I used the most generic, least-tuned extraction rule I could (Python's own exception grammar), not a category invented to make the corpus look good, but it is still an imposed abstraction, not a discovered one. **Narrowing the claim accordingly:** this study shows the corpus *contains* exploitable recurring structure at a level a simple, generic, non-tuned parse already surfaces — it does not show FeralEcho, or any mechanism within it, has ever generated this abstraction from experience itself.

## 10. Model-capability interaction

Conceptually, not run: `current 7B model + no VRM` (today's real 1.8-2.7% retry-repair rate) vs. `same model + accumulated VRM` (hypothetical, untested) vs. `stronger frozen model + no VRM` vs. `stronger frozen model + same VRM`. **A real, specific confound surfaced by this data, worth naming directly:** the dominant recurring failure content (`log_call`, `HealthMonitor`, `CodeGenerator`, `Scheduler` — all plausible-sounding, nonexistent helper names the model appears to be *inventing* as if this codebase should have them) looks exactly like the generic, well-known LLM failure mode of confidently hallucinating plausible infrastructure — not something specific to FeralEcho's architecture. A materially stronger frozen model might simply hallucinate these specific names far less often, shrinking the entire recurring-failure mass this study found, for reasons having nothing to do with any FeralEcho-side learning mechanism. **What future result would separate the two:** the same VRM mechanism (if built) applied against both the current model and a stronger frozen model, with the stronger model's *baseline* (no-VRM) failure rate measured first — if VRM's marginal gain over each model's own baseline is comparable, that argues for a real, model-independent mechanism effect; if VRM's gain shrinks to near-zero for the stronger model because the stronger model rarely produces these signatures at all in the first place, that argues the whole phenomenon was a symptom of the current model's specific weakness, not evidence of a generalizable learning mechanism. **Frozen-baseline value:** yes, clearly useful here specifically *because* of this confound — without keeping the current 7B model as a fixed comparison point, a future stronger-model swap could get all the credit that actually belongged to a repair mechanism, or vice versa.

## 11. Accumulation, not just one repair

The corpus supports evidence of *recurring recognizable classes* (46 in DEV alone), which is a necessary precondition for accumulation, but does **not** support evidence of the full chain the mission specifies (`experience A → retained repair A → experience B → retained repair B → both remain usable → performance benefits from A+B`), because no individual repair (A or B) was ever recorded as a retained, reusable artifact — only the raw failure signatures were. **Estimate of independent reusable repair classes plausibly available**, stated as an upper bound, not a demonstrated count: at most the ~46 DEV-recurring signatures, and realistically fewer once the identifier-less, genuinely-coarse buckets (`RuntimeError, None`, `TypeError, None`) are set aside or handled specially (the Metal case, Section 4). **A second, project-specific risk not present in a more static domain**: self-edit's own target file and prompts change over time as the system edits itself, so the space of "plausible hallucinated helper names" is plausibly non-stationary — Section 7's real coverage decay (86%→66%→47% dev-self/prospective/holdout) is at least consistent with this, though this study cannot cleanly separate "the vocabulary is genuinely drifting" from "the sample per period is just smaller and noisier." **If there aren't enough independent classes to matter**: 46 is a real, non-trivial number, but with unverifiable repair-success and measurable coverage decay, the realistic near-term accumulation story this corpus supports is "modest and requires ongoing maintenance," not "compounds indefinitely."

## 12. Attack VRM

| Explanation | Classification | Basis |
|---|---|---|
| Surface-form memorization (exact string reuse) | **CONTROLLED** | Signature is exception class + identifier, not raw error text or task text; genuinely different failure instances with the same identifier were confirmed to collapse correctly. |
| Task-family lookup | **NOT TESTABLE FROM EXISTING HISTORY** | Every row is `task_type: coding`; no cross-family data exists to test this against. |
| Future leakage | **CONTROLLED, with the disclosed caveat in Section 3** | The chronological split was enforced for the quantitative coverage test; the qualitative "these names recur" observation was investigator-contaminated before the split was designed, disclosed rather than hidden. |
| Taxonomy designed after seeing outcomes | **PARTIALLY NARROWS THE CLAIM** | The extraction *method* (parse Python's own exception grammar) was fixed and generic, not tuned per-category after seeing results — but see Section 3's disclosed lapse; not a clean pre-registration. |
| Hand-coded repair knowledge | **NOT APPLICABLE** | No repair knowledge of any kind was coded or tested here. |
| Evaluator leakage | **CONTROLLED** | F2's real kernel sandbox is unchanged and was not touched; this study only read existing outcomes, never re-ran or re-graded anything. |
| Repeated identical bugs (same exact code re-submitted) | **NOT TESTABLE FROM EXISTING HISTORY** | No source code preserved to check whether recurring signatures come from literally identical generated code or genuinely different code with the same underlying mistake. |
| Retry advantage / unequal compute | **CONTROLLED for the one measurement made (retry-repair rate)** | Retry-repair rate is reported as its own real, separate baseline (1.1-2.7%), not conflated with recognition coverage. |
| Selection bias (only easy bugs recur) | **NARROWS THE CLAIM** | Plausible and not ruled out — recurring signatures might be exactly the *shallowest* class of bug (a hallucinated name), while harder, more consequential bugs may be one-off and not amenable to this kind of signature matching at all. This study cannot distinguish "recurring because common" from "recurring because trivial." |
| Signatures encoding task identity | **KILLS CLAIM if true, but CONTROLLED here** | Checked directly: the signature extraction never touches the originating prompt/plan text, only the traceback. |
| Repair transformations already present in initialization | **NOT APPLICABLE** | No transformations exist in this study at all. |
| Stronger pretrained capability doing the real work | **NOT TESTABLE FROM EXISTING HISTORY, but a real, named, plausible confound** | Section 10 — the hallucinated-helper-name pattern looks like a generic LLM weakness, not a FeralEcho-specific one; this study cannot rule that out. |
| Retrospective cherry-picking | **PARTIALLY NARROWS THE CLAIM** | The DEV/PROSPECTIVE/HOLDOUT split, once fixed, was reported in full (all three periods' numbers shown, including the less favorable HOLDOUT decay) — no period was dropped because it looked worse. The pre-split exploratory peek (Section 3) is the honest caveat on this. |

## 13. VRM vs. the reconciled outcome-conditioned strategy-selection program

| | Strategy-selection program | VRM |
|---|---|---|
| Scientific value | Directly tests the reconciliation's own Level-3/4 claims-ladder question | Tests a narrower, different question (reusable repair content) not yet on that ladder |
| Implementation complexity | Small (a CPU bandit/classifier over a handful of existing strategies) | Larger even at VRM-1, and VRM-2/3 require capturing code artifacts that currently don't exist at all — a real, unbuilt data-capture step first |
| Dependence on local-model induction | Low (models are still just executing pre-existing fixed strategies) | High at VRM-2/3 (a model must still propose plausible transformations, even if a symbolic search handles some cases — same induction risk AP-0 already found weak) |
| Causal clarity | High — the reconciliation's own design (Part IX) already specifies the exact controls needed | Currently lower — this study shows recognition works, but the repair half is entirely untested |
| Sample efficiency | Reasonable — reuses real, already-accumulating production outcomes | Would need a new logging change before any real sample accumulates for the repair half |
| Accumulation potential | Real but bounded (better use of existing strategies, not new capability) | Higher ceiling *if* VRM-2/3 turn out feasible, but that's unverified | 
| Static-doppelgänger susceptibility | Real (a hand-written routing rule is an explicit named control already) | Real, and shown here to be a live, plausible risk (Section 6), not just a hypothetical |
| Suitability for the remaining pre-October-1 window | Already scoped and ready to freeze | Not ready — the missing-code gap alone means VRM-2/3 can't be attempted in this window regardless of appetite |

**Choice: C — a component experiment**, not abandoned, not promoted above strategy selection, not pursued as an equal-weight parallel program given the remaining time. Not **E**: nothing in this study shows VRM is currently strong enough to displace the already-reconciled primary program, and the missing-code gap is a real, unresolved blocker, not a minor implementation detail. Not **A**: the recognition-level clustering result is real and interesting enough that dropping it entirely would waste a genuine, freshly-confirmed finding. Not **B** (idea-only, no action): there is one small, concrete, low-cost next step worth taking now (below) that isn't full VRM.

## What I'd actually recommend, if a next step is warranted

Not VRM itself. **Start recording the actual generated source code (and, on retry, the retry's code) alongside the existing traceback in `self_edit_attempt_ledger.jsonl` or a sibling file, going forward.** This is a logging change, not a learning mechanism — it creates no new autonomous behavior, touches no production decision path, and is reversible by simply not consuming the new field. Without it, no future VRM feasibility study (this one included) can ever test the actual repair-validity question, only the recognition question this report already answered as far as it can go.

---

### VRM FEASIBILITY
MODERATE

### HISTORICAL VERIFIED FAILURE COUNT
881 real, kernel-sandboxed F2 failures (`terminal_state == "staging_import_failed"`), 2026-09-07 to 2026-09-20, all `task_type: coding`. (A further 414 rows are real but pre-F2 static-scan rejections, classified separately as PARTIAL EVIDENCE, not counted here.)

### RECURRING STRUCTURAL FAILURE MASS
86.4% of DEV-period mass matches a signature recurring ≥2 times within DEV itself; 66.1% of PROSPECTIVE mass and 47.3% of HOLDOUT mass matches a signature already recurring in the strictly earlier DEV period (recognition-level coverage only — repair success is NOT ESTIMABLE, no historical code artifacts exist to test it).

### HIGHEST VRM LEVEL CURRENT HISTORY COULD TEST
VRM-0/VRM-1 boundary, recognition only — VRM-2 and above are blocked by the total absence of preserved source code for any historical attempt.

### PROSPECTIVE SIGNAL
Real and substantial for recognition (two-thirds of near-term later failures, decaying to under half further out, would have matched an already-known signature) — but this cannot be extended to "would have been repaired," because no repair content was ever recorded to test.

### STATIC DOPPELGÄNGER
PARTIALLY SURVIVES — a human-written list of the top ~10 recurring names is entirely plausible and not ruled out; the one piece of evidence against it is measured temporal coverage decay, which argues a fixed list would need to keep being updated, not that VRM's specific mechanism is what must do the updating.

### ABSTRACTION ORIGIN
Infrastructure-supplied (Python's own exception format) plus programmer-supplied (the extraction regex, applied by the investigator) — not experience-generated. Nothing in FeralEcho's history has ever produced this abstraction on its own.

### STRONGEST CLAIM CURRENT EVIDENCE COULD SUPPORT
FeralEcho's real self-edit failure history contains a small, genuinely recurring, temporally-decaying set of failure signatures whose *recognition* (not repair) could plausibly have been anticipated from strictly earlier data.

### STRONGEST REASON VRM MAY FAIL
No historical mechanism has ever preserved the actual failing (or retried) source code, so the entire repair-generation-and-validation half of VRM — the part that would distinguish it from a static lookup table — has zero historical evidence either for or against it, and building it would require a real generation/validation pipeline whose central induction step (proposing a correct transformation) is exactly the class of task AP-0 already found local models perform poorly at.

### RELATION TO STRATEGY-SELECTION PROGRAM
C — a component experiment. VRM's recognition half is real and cheap to keep exploring, but it is not ready to compete with, replace, or run as an equal-weight parallel to the already-reconciled outcome-conditioned strategy-selection program in the time remaining, given the unresolved missing-code gap.

### NEXT EXPERIMENT IF WARRANTED
Not an experiment: a minimal, reversible logging addition — capture the actual generated (and retried) source code per self-edit attempt going forward, alongside the existing traceback — so a future retrospective study can test VRM-2's repair-validity question, which this one could not.

### IMPLEMENTATION AUTHORIZATION
NOT AUTHORIZED
