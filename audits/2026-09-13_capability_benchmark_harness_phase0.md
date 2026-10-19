# Capability Benchmark Harness — Phase 0: Archaeology, Boundary Definition, and Design

**Status: DESIGN/ARCHAEOLOGY ONLY. Nothing implemented. No production code, benchmark script, or
existing research-ledger file modified. No held-out task content inspected beyond what the source
reports themselves already disclose.**

Git baseline at mission start: HEAD `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f`, `git status --short`
113 lines (a large, pre-existing set of modified/untracked files from prior sessions in this
repository — not touched, added to, or reduced by this mission). Git baseline at mission end: HEAD
`e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` (unchanged), `git status --short` 113 lines plus exactly
one new untracked file — this report. No production file, no `research/*.md` file, no `audits/tier*`
file, no `scripts/*` file was modified. Nothing was committed.

---

## 1. Executive Conclusion

# YES, WITH BOUNDARIES

FeralEcho's Tier-3 through Tier-8 lineage is not a loose pile of one-off scripts — it is a genuine,
disciplined experimental program: pre-registered protocols hashed before execution, held-out task
suites frozen and hash-verified before every run, deterministic replay used to independently
re-verify prior claims (twice, in some cases), a Simpson's-paradox confound found and reported
*against* the investigating team's own prior recommendation, and — critically — a full forensic audit
(Tier-8) that found and characterized a real experimental-isolation gap in the apparatus itself before
it could be trusted further. This is closer to the discipline a permanent harness would need than
"NO, NOT YET" would honestly convey.

But it cannot be mechanically "converted" into a permanent harness by generalizing its current shape.
Three structural facts block a naive YES:

1. **The apparatus has already changed its own definition of its central arm at least twice** — the
   original `ARCH_PIPELINE` was discovered, mid-lineage, to secretly invoke a full 4-call council
   deliberation instead of the single call its name implied (`tier3_arch_pipeline_isolation.md`), and
   13 historical records across two files were retroactively reclassified `INVALID_FOR_ISOLATED_
   SINGLE_CALL_COMPARISON` as a result. A permanent harness needs versioning precise enough that this
   exact class of silent redefinition is either impossible or immediately detectable (§16).
2. **The production mechanism under test has already changed underneath the historical results** —
   Tier-5 refactored `river_deliberation.py`'s synthesis pipeline directly in response to Tier-4's
   findings. Tier-4's raw pass-rate numbers describe a system that, as of this report, no longer
   exists in that exact form. A harness that doesn't version the system-under-test alongside the task
   set will silently conflate "the benchmark changed" with "the system changed."
3. **The experimental apparatus itself has a documented, only-partially-closed isolation gap**
   (Tier-8): `install_isolation()` does not stop RiverBrain's own background writer thread, and one
   real historical run (`tier3_apparatus`'s dev-sanity pass) is classified `POTENTIALLY CONTAMINATED`
   — real, evidenced temporal overlap with a live production process, not a hypothetical risk. A
   permanent harness inherits this exact class of risk unless it fixes the isolation boundary as a
   first-class, continuously-verified property of the harness itself, not an artifact of "no `run.py`
   happened to be running this time."

None of these is fatal. All three are addressable by design choices this report specifies (§7, §15,
§16) without inventing new infrastructure — they are why the answer is **YES, WITH BOUNDARIES**, not
a plain YES.

---

## 2. Existing capability-evaluation archaeology

Six generations of experiment, each responding directly to a gap the previous one found, read in full
this session (not inferred from filenames):

| Stage | What it tested | Verdict it reached |
|---|---|---|
| Tier-3 design/preflight | RAW/PIPELINE/COUNCIL pilot's own confound structure | Original 3-condition pilot could not answer the central question; a 4-arm budget-matched design was specified, then found to have 3 BLOCKER-severity confounds (token budget, a non-existent `BASE_N` arm, a synthesis-prompt wording bias) before it could run |
| Tier-3 isolation fix | Whether `ARCH_PIPELINE` was really testing what its name claimed | **No** — it was secretly a full council deliberation; fixed, relabeled `ARCH_PIPELINE_ISOLATED`, 13 historical records invalidated for this specific comparison (not deleted) |
| Tier-3 held-out execution + scoring | 4-arm design (`BASE_1`/`BASE_N`/`ARCH_PIPELINE_ISOLATED`/`ARCH_COUNCIL`) on 8 frozen, hash-verified held-out tasks | `BASE_N` 6/8 beat `ARCH_COUNCIL` 3/8; McNemar p=0.25 (not significant, n=8); explicitly reported as "gather more evidence," not settled |
| Tier-4 confirmatory | The same question at ~10x scale (84 tasks, two independently-authored stages, pre-registered O'Brien-Fleming-style stopping rule) | Pilot's 37.5pp gap was inflated by small-sample noise (confirmed magnitude: 11.9pp, p=0.087, still not significant); **the real, decisive, unplanned finding**: raw candidate solve rate 95-96%, synthesized output only 68-80% — synthesis, not generation, is the bottleneck |
| Tier-5 refactor | Fixing the synthesis mechanism Tier-4 implicated | Two real, replayed historical failures (`cs09`, `bf06`) fixed by construction; two new bugs found during the refactor's *own* live validation (prose-extraction gap, case-sensitive fence regex) |
| Tier-5 counterfactual replay | Whether the refactor's own claims hold under independent, deterministic re-verification against the full 168-event corpus | Zero regressions confirmed; net effect real but modest (+3.6pp/+6.0pp); found a **new, previously-undocumented weakness**: the fallback candidate-selection heuristic picked the wrong candidate in 3 of 3 checked cases where it fired without benefit |
| Tier-6 disagreement/ranking forensic | Whether "prefer longest candidate" is a defensible fallback rule, corpus-wide | No — "prefer shortest" beats it (93.6% vs 78.2%), because length is confounded with which councillor produced the text, and one real councillor (`echo:latest`) is measurably less reliable (53.6% vs 83-88%) than its peers |
| Tier-7 RiverBrain-ranking forensic | Whether RiverBrain's existing historical score could replace the length heuristic | **Simpson's paradox found**: 77.8% aggregate accuracy is carried almost entirely by pairs involving the one weak councillor; on the one pairing that excludes it, RiverBrain's score picks correctly only 38.9% of the time — worse than chance. Recommendation narrowed from "use as ranker" to "use only as a large-margin deprioritization signal." **Also discovered, as a side effect of this investigation**: RiverBrain's background writer thread bypasses `install_isolation()` |
| Tier-8 isolation forensic | Whether the isolation mechanism used by every prior tier actually isolates | **PARTIALLY ISOLATED** — the four explicit write call-sites are genuinely blocked (340/340 real interceptions confirmed); the background writer thread is not. One historical run classified `POTENTIALLY CONTAMINATED` (real, evidenced overlap with a live production process); Tier-4/Tier-5-REFACTOR classified `CLEAN` (confirmed via a 10.6-hour production-log silence window); Tier-5-counterfactual/Tier-6 classified `CLEAN` structurally (fresh grep found neither script even touches RiverBrain, correcting a more cautious characterization inherited from Tier-7) |
| RAOC (separate lineage) | Whether a *verified* outcome injected as context causally shifts a new candidate's approach | **Design-only** (pre-registered protocol, `echo_raoc_outcome_conditioning_experiment.md`), a real harness built (`app/experiments/raoc/`, 831 lines across 7 files), a mock-only calibration run, and a tiny (n=1/cell, 12-trial) **non-evidentiary** real-Echo pilot that surfaced and fixed a real approach-classifier gap (UNKNOWN rate 44.6%→10.7% corpus-wide after fixing missed comprehension/no-control-flow patterns). **The pre-registered n=240 confirmatory run has never executed** — confirmed directly this session: `memory/raoc_trials.jsonl` (where real trial data would land) does not exist; only `memory/raoc_pilot_trials.jsonl` (32,934 bytes, the small pilot) exists. |

For each evaluation, the 16-question trace the mission requires:

**Tier-3/4 (`ARCH_PIPELINE_ISOLATED`/`ARCH_COUNCIL`/`BASE_1`/`BASE_N`)**
1. What was tested: whether Echo's Council orchestration (and separately, self-edit's generation
   framing) beats simpler, budget-matched baselines on single-function coding tasks.
2. Independent variable: which of the 4 arms generated the candidate.
3. Held constant (Tier-4, after repair): pinned model (`qwen2.5-coder:7b`), `max_tokens=2048` for
   every generative call, task text, scoring method, arm-order randomization.
4. Dependent variable: binary sandbox pass/fail (`objective_verify()`).
5. Success: the candidate's code passes a real, frozen `test_code` block in a real kernel sandbox.
6. Mechanically verifiable: **yes** — real sandboxed execution, not a heuristic or LLM judge.
7. Deterministic scoring: yes (Tier-3 scoring analysis independently reproduced 32/32 records exactly
   via fresh re-execution of the stored code).
8. LLM judge involved: no, for pass/fail. (A text-backstop *classifier* for truncation is used, and it
   produced 2 false positives on 32 records, both caught and corrected by human spot-check — see §10.)
9. Human judgment involved: yes, as a spot-check layer (100% coverage at Tier-3's n=32 scale; not
   attempted at Tier-4's n=336 scale — see §5).
10. Rerunnable today: **UNKNOWN** — the apparatus (`scripts/run_tier3_apparatus.py`, `run_tier4_
    confirmatory.py`) exists and is documented as working at the time it ran; not re-executed this
    session (this mission is read-only). `river_deliberation.py`'s synthesis pipeline has since been
    refactored (Tier-5), so a literal rerun today would measure a different system than Tier-3/4
    measured, by design intent, not by accident — see §17.
11. Current reproducibility of the *historical* result: the raw JSONL artifacts exist, are
    hash-referenced, and were independently re-scored at least twice (Tier-3 scoring analysis, Tier-5
    counterfactual replay) with zero discrepancies against the stored `candidate_code`. The
    *result itself* (as a statement about current Echo) is not reproducible today without re-running,
    because the system changed.
12. Artifacts retained: yes — `audits/tier3_apparatus/*.jsonl`, `audits/tier4_apparatus/*.jsonl`, both
    task suites and their SHA-256 hashes, both protocols and their hashes.
13. Contamination risks: real and documented — see Tier-8 (§8/§13 below).
14. Confounders: extensively documented and mostly closed (token budget, model pinning, synthesis
    template wording, warm-up call asymmetry — the last one disclosed, never eliminated).
15. Claim made: "Council underperforms a compute-matched same-model baseline on this task class; the
    loss is attributable to the synthesis step, not the underlying model pool."
16. Stronger than evidence warrants: **no** — this is the rare case where the investigating team
    repeatedly narrowed its own claims (Tier-3→4's own magnitude correction; Tier-6/7's narrowing of
    "prefer shortest" to "the real driver is model identity"; Tier-7's narrowing of "use RiverBrain
    score" to "use only as a large-margin signal"). This is the single strongest piece of evidence in
    this whole archaeology that the underlying culture, not just the individual scripts, is
    harness-grade.

**Tier-5/6/7 forensic/counterfactual passes**
1–4: Not new generation experiments — deterministic replay against already-captured Tier-4 data (zero
new model calls in Tier-5-counterfactual, Tier-6, and the corpus-reuse portions of Tier-7).
5–9: Success = does the replayed function call, run against real stored text, reproduce or improve on
the stored historical outcome; fully deterministic and mechanically verifiable, zero LLM judgment.
10–11: Fully rerunnable and fully reproducible **by construction** — this is the strongest
reproducibility class in the whole archaeology, since it requires no new model calls at all, only the
already-frozen corpus and the current, real production functions.
12: Artifacts retained (`memory/synthesis_integrity_log.jsonl` from Tier-5's live validation; the
Tier-6/Tier-7 scripts themselves, confirmed present in `scripts/`).
13–14: Contamination — the historical corpus's own capture is subject to Tier-8's findings; the
*replay itself* touches nothing live (confirmed structurally, not just claimed, in Tier-8 §13).
15–16: Claims are narrowly, repeatedly scoped down as evidence accumulated (see Tier-7's own Simpson's
paradox self-correction) — not overstated.

**Tier-8**
1–16: A pure forensic/source-reading audit, not a capability benchmark itself — it is the
*meta-evaluation* this Phase-0 mission most directly needs to inherit. Its own claims are the most
rigorously self-falsifying in the archaeology (§18 of that report states explicit falsification
criteria for its own verdict, including exactly what evidence would overturn it in either direction).

**RAOC**
1–16: Design is complete and precise (§7–§13 of its own protocol). Execution is real but tiny (n=1/
cell) and explicitly, repeatedly labeled non-evidentiary by its own author. Success oracle: `objective_
verify()` for pass/fail, plus a now-repaired AST-based approach classifier for the directional claim.
Deterministic, no LLM judge for scoring. The pre-registered, powered confirmatory run has not happened.

---

## 3. Tier-3..8 inventory

Full detail folded into §2's table above (the mission's §3/§4 requirements are answered together there
to avoid duplicating the same 16-question trace twice for the same artifacts). Evaluation archaeology
table, per §4 of the mission:

| Evaluation | Location | Capability | Input | Success oracle | Score | Reproducible? | Deterministic? | Human/LLM judgment? | Known confounds | Legitimate claim |
|---|---|---|---|---|---|---|---|---|---|---|
| Tier-3 held-out (4-arm) | `audits/tier3_apparatus/heldout_results.jsonl` | Single-function coding | 8 frozen tasks | `objective_verify()` (sandbox) | 5/8, 6/8, 4/8, 3/8 | Data: yes. Live result: UNKNOWN (system changed) | Yes (scoring) | Human spot-check, 100% coverage at n=32 | Token budget (fixed before this run), 5th warm-up call (disclosed, not fixed) | "On this task class, this exact system state, Council underperformed a matched baseline; underpowered" |
| Tier-4 confirmatory (4-arm ×2 stages) | `audits/tier4_apparatus/{stage1,stage2}_results.jsonl` | Same | 84 frozen tasks | Same | 74/84, 67/84, 54/84, 57/84 | Data: yes. Live result: no (system since refactored) | Yes | Human judgment not separately reported at this scale (see §5) | Temperature confound (`BASE_1` deterministic vs. others jittered — named, not isolated); self-edit framing confound (isolated, decisive) | "Synthesis, not generation, is the bottleneck; self-edit framing actively hurts general coding" |
| Tier-5 live validation | `memory/synthesis_integrity_log.jsonl` | Synthesis-refactor correctness | 5 fresh tasks | `deliberate_and_learn()` end-to-end + replay of 2 historical cases | 5/5 pass (both refactored and control) | Yes, small n | Yes | None for pass/fail | Sample too small to show a pass-rate delta (disclosed) | "Fix works mechanically (replayed cases); does not, by itself, prove a live pass-rate improvement" |
| Tier-5/6 counterfactual replay | In-memory / `/tmp` scratch, not persisted as a durable artifact | Same corpus, re-scored | The 168-event Tier-4 `ARCH_COUNCIL`/`BASE_N` corpus | Same `objective_verify()` | +3.6pp/+6.0pp net; 0 regressions | Yes, fully (deterministic replay of frozen data) | Yes | None | Fallback-selection heuristic's own weakness (found, not a confound of the measurement) | "Refactor causes zero regressions and modest, real improvement on the historical corpus" |
| Tier-7 RiverBrain ranking | Same corpus + `memory/snapshots/*/river_brain.pkl` | Candidate ranking | Same 90 discriminating pairs | Same | 77.8% aggregate / 38.9% on the isolating subgroup | Yes | Yes | None | Simpson's paradox (found, reported, not hidden) | "RiverBrain score is a large-margin weak-model detector, not a general ranker" — narrower than first framed |
| RAOC pilot | `memory/raoc_pilot_trials.jsonl` | Outcome-conditioning | 3 real task pairs, 4 conditions, n=1/cell | `objective_verify()` + AST approach classifier | 6/12 passed; only 2/12 had a determinate direction | Yes (harness exists) | Yes for scoring | None for scoring | Explicitly, repeatedly labeled non-evidentiary by its own author | **None** — author states directly this is one data point, not evidence for or against H1 |
| RAOC confirmatory (pre-registered n=240) | Not executed | — | — | — | — | N/A | — | — | — | **UNKNOWN — never run** |

---

## 4. RAOC inventory

Covered in full above. The one item worth stating plainly and separately, since it is the sharpest
gap between "designed" and "executed" in this entire archaeology: **RAOC has a complete, adversarially
red-teamed, pre-registered protocol and a working harness, and has never produced a single trial that
counts as evidence for or against its own research question.** This is not a criticism of the design —
it is exactly the honest state a Phase-0 harness-design mission needs to record precisely, since a
future harness that treated the RAOC *harness's existence* as equivalent to a RAOC *result* would be
a real instance of exactly the "instrument becomes an authority" risk this whole mission exists to
guard against (§9).

---

## 5. Reproducibility assessment

Three distinct senses of "reproducible," kept separate per the mission's own discipline:

1. **Can the stored data be re-scored identically?** Yes, repeatedly demonstrated — Tier-3's scoring
   analysis (32/32), Tier-5's counterfactual replay (168/168), Tier-6 (168/168 again, independently),
   Tier-7 (re-derives Tier-6's own numbers a third time, confirms exact match, then declines a fourth
   identical recomputation as adding no evidence). This is the strongest reproducibility property in
   the archaeology and the one a permanent harness should lean on hardest: **frozen raw text +
   deterministic sandbox scoring is genuinely, repeatedly reproducible in this codebase.**
2. **Can the experiment be re-run and produce the same live result?** **UNKNOWN, and not merely
   untested** — the production system under test (`river_deliberation.py`'s synthesis pipeline) has
   materially changed since Tier-4 ran (Tier-5's refactor). A literal rerun today would not be
   measuring the same system, by design intent (the refactor was supposed to change behavior). This is
   not a flaw in the historical experiments; it is a structural fact any permanent harness must encode
   as a first-class property (system version ≠ benchmark version — see §16), not paper over.
3. **Does spot-checking find the automated scoring reliable?** Yes, with one disclosed, real
   exception: Tier-3's own text-backstop truncation heuristic produced 2 false positives out of 32
   records (both `ARCH_COUNCIL` synthesis outputs opening with an unclosed fence around otherwise-
   complete, correct-except-for-a-real-bug code) — found by 100%-coverage manual spot-check, corrected,
   and shown *not* to change any pass/fail outcome. **At Tier-4's 10x scale (336 records), no
   equivalent 100%-coverage spot-check was performed** — the report states the evaluator "held up
   cleanly," based on zero infrastructure failures/truncations and the primary pass/fail oracle being
   independently re-verified, but does not claim the same exhaustive-spot-check confidence Tier-3
   established. This is a real, disclosed gap in reproducibility *assurance*, not a demonstrated
   scoring error at that scale.

---

## 6. Proposed benchmark unit

**Recommendation: the task-attempt (one candidate's full generation trajectory against one task), not
the bare final answer, and not the "complete system run."**

Justification, working from what the existing lineage actually needed to diagnose its own failures:
Tier-4/5/6's single most important finding (synthesis destroys already-correct candidates) was
**invisible at the final-answer unit** — it only became visible once the harness captured
`mechanism_calls` (every individual pre-synthesis attempt/councillor response, not just the delivered
answer) and could re-score each one independently. A benchmark unit that discarded intermediate
attempts, as the original Tier-3 pilot effectively did before this instrumentation was added, could
never have found the actual, actionable defect (a specific synthesis step dropping a class
definition) — it could only ever report "Council scored lower," a conclusion that would have pointed
toward retiring Council rather than the correct, narrower fix (repair synthesis).

Concretely, the working presumption from the mission brief holds and is directly evidenced by this
archaeology: **a final answer alone is insufficient.** The minimum unit that preserved the causal
information this lineage actually needed was:

```
task
  |
  v
fixed candidate-generation step(s) — every individual model call's full raw text,
  not just which model was queried (Tier-4's `mechanism_calls` innovation)
  |
  v
combination/synthesis step, if any — recorded separately from generation
  |
  v
deterministic sandbox check (objective_verify)
  |
  v
final delivered answer + which upstream step, if any, is responsible for a failure
```

This is closer to "task attempt with full trajectory" than to "prompt" (too fine — loses the
generation-vs-synthesis distinction that mattered most) or "complete system run" (too coarse — a
36-second `ARCH_COUNCIL` candidate and a 6-second `BASE_1` candidate get treated as comparable units
today, which is defensible for the paired-comparison statistics but was not sufficient on its own to
diagnose *why* one failed).

---

## 7. Proposed architecture

Following the mission's own layer sketch, with what each layer owns/is forbidden from doing, evidenced
against what actually went wrong when a boundary was blurred in the historical lineage:

| Layer | Owns | Forbidden from | Deterministic? | Evidence this boundary matters |
|---|---|---|---|---|
| **Benchmark definition** | Task text, reference test code, category tags, approach-relevant metadata (for RAOC-style pairs) | Knowing anything about which system/model will attempt it | Yes | Tier-4's task pool was independently verified (`scripts/tier4_verify_task_pool.py`, 84/84 reference solutions checked, one authoring bug caught and fixed) *before* freezing — this discipline should be a required gate, not an optional nicety |
| **Fixed task fixture** | The frozen, hashed artifact (`held_out_task_suite.json` + `.hash.txt` pattern) | Being read for content by anything except the loader that verifies its hash first | Yes | `load_and_verify_held_out_suite()`'s hard-assert-on-mismatch pattern (Tier-3) is exactly the right shape and should be the harness's universal loader, not reimplemented per tier |
| **Controlled execution** | Making the real model/system calls, recording every intermediate step (not just the final answer — §6), recording system identity (model pin, git state, task-type routing) | Any interpretation of whether an output is "good" | No — this is where real model nondeterminism lives; must record enough (seed/temperature/model identity) that nondeterminism is *disclosed*, not hidden | Tier-4's Finding B (council composition not guaranteed deterministic) is the direct precedent — the harness recorded composition per-candidate specifically so drift, if it occurred, would be visible rather than silently assumed away |
| **Deterministic evaluator** | Sandbox pass/fail, AST-based structural checks (approach classification, completeness checks) | Ever asking an LLM to render a verdict on correctness where a mechanical check exists | Yes, always | This is the layer every tier in this archaeology trusted completely and never found wrong at the primary-oracle level — the one layer worth treating as load-bearing infrastructure |
| **Optional human review** | Spot-checking the deterministic evaluator's own edge cases (the text-backstop truncation heuristic, specifically) | Overriding a clean sandbox pass/fail; being silently skipped at scale (§5's disclosed Tier-4 gap) | No | Tier-3's 2 corrections came from 100%-coverage human spot-check; this coverage rate should be a versioned, disclosed parameter of every benchmark run, not an ad hoc choice per tier |
| **Optional model review** | Never used as a *primary* oracle anywhere in this lineage for pass/fail; the closest analog is `code_verification.py`'s self-consistency check (does a self-claimed output match reality), explicitly named in Tier-6 as "the only real execution-based signal available for arbitrary questions... not yet wired into candidate selection" | Substituting for a deterministic check wherever one exists (this is the load-bearing D-001/R-002 boundary — see §13) | No | Never actually deployed as a *scoring* mechanism in this lineage — a genuine gap for domains without an executable oracle (creative/reasoning tasks), explicitly out of scope for Tier-3..8's coding focus |
| **Per-run result** | One record per task-attempt (§6), carrying benchmark identity + system identity + execution + evidence + evaluation + interpretation, kept separate (§18's schema) | Overwriting raw evidence with an interpretation field | Structurally yes (append-only) | — |
| **Versioned results ledger** | Append-only accumulation across runs, keyed by (benchmark_version, system_version) | Silently treating two different (benchmark_version, system_version) pairs as comparable | N/A | The Tier-3→4 magnitude correction (37.5pp→11.9pp) is exactly the case a versioned ledger should make legible at a glance rather than requiring re-reading two full reports |
| **Comparison/report** | Human- or Claude-authored interpretation, explicitly citing which (benchmark_version, system_version) pairs are being compared | Ever writing directly into the results ledger's raw records | N/A | This is where all of §9's adversarial cases actually get resisted or fail — see §9 |

Task definition, execution, grading, and aggregation are already, in practice, kept separate in this
lineage's better-executed tiers (Tier-4's own `_run_single_candidate()`/`classify_result()`/analysis-
script split) — the recommendation is to formalize this as an enforced architectural boundary, not to
invent a new one.

---

## 8. Evidence model

No "truth label" tier is proposed, per the mission's explicit prohibition and per this archaeology's
own repeated demonstration that the underlying evidence is what actually did the diagnostic work, not
a summary label. Concretely, every "per-run result" record should preserve:

- `raw_output` — the full, unextracted model response text (Tier-4's `mechanism_calls` innovation,
  the single most valuable retained-evidence field in the entire archaeology, since it is what let
  Tier-5/6/7 independently re-derive and correct prior claims without a single new model call).
- `execution_trace` — which real underlying calls were made, in what order, by which model(s), at
  what token budget/temperature (Tier-3's own §Finding-3 disclosure of `ARCH_COUNCIL`'s undisclosed
  5th warm-up call is the direct precedent for why this must be captured, not assumed from the arm's
  nominal contract).
- `test_result` — the real, deterministic `objective_verify()` output (pass/fail + stdout tail).
- `filesystem_state` / `artifact_hash` — task-suite hash at time of read, system git HEAD at time of
  execution.
- `validator_result` — any secondary heuristic classifier's own verdict (e.g., the truncation
  text-backstop), kept **structurally separate** from the primary pass/fail oracle, exactly as Tier-3's
  `classify_result()` already keeps `passed` (ground truth) separate from `classification`
  (interpretive, spot-checked, and twice found wrong in this archaeology's own history).
- `timing` / `resource_usage` — generation time, call count, telemetry snapshot (Tier-3's §3/§4
  contention-threshold discipline is a directly reusable precedent).
- `human_review` / `model_review` — present only when actually performed, with coverage rate
  (fraction of records reviewed) recorded explicitly rather than implied.

The distinction the mission requires — "the evaluator recorded X" vs. "the system is therefore X" —
maps directly onto this archaeology's own hardest-won lesson: Tier-4's raw 95-96% figure ("the model
solves 95-96% of tasks") was independently found, twice (Tier-5-counterfactual, Tier-6), to be
**overstated as commonly read** — the evaluator correctly recorded a real "best-of-3 solvability" rate;
the system does not, in fact, deliver that rate to any real user. **This exact gap — a correctly-
recorded number being informally upgraded to a stronger system-level claim than it supports — already
happened once in this project's own real research history, inside a single investigation, before being
caught two tiers later.** Any permanent harness's evidence model exists specifically to make this class
of drift structurally harder, by keeping "the evaluator recorded" fields physically separate from any
"claim_scope"/"interpretation" field (§18), never fields of the same kind.

---

## 9. Scoring model options — Taxonomy-laundering attack (D-001/R-002/Q-007), mandatory per §9 of the mission

Working through the mission's 8 adversarial questions directly against the harness architecture in §7:

1. **Could the benchmark manufacture false authority?** Yes, structurally, if a future version
   collapses the evidence model (§8) into a single summary label attached to output and that label is
   then read by anything downstream (a prompt, a self-model claim, a Council decision) without the
   underlying evidence. This is not hypothetical for this exact codebase — `research/DECISIONS.md`
   D-001 already documents this precise failure occurring with a near-identical taxonomy
   (OBSERVED/DERIVED/INFERRED/SPECULATIVE/IMAGINED), rejected from production specifically because a
   fabrication could acquire a false `OBSERVED` label and become *more* credible-looking than an
   unlabeled fabrication.
2. **Could a fabricated output receive a convincing label?** Yes, if a benchmark's evaluator layer
   were ever an LLM judge rather than the deterministic sandbox this lineage has exclusively used for
   its primary oracle — this is exactly why §7 forbids model review from ever substituting for a
   deterministic check where one exists.
3. **Could downstream code trust the label rather than inspect the evidence?** This is the literal
   mechanism R-002 documents: "an authoritative-sounding marker... does change the answer, but by
   making generation trust the flag's authority rather than the evidence's truth." A benchmark
   `PASS`/`FAIL` field is exactly such a marker if it is ever surfaced to Echo's own generation context
   without the underlying evidence — a genuinely live risk for §20's self-model boundary, addressed
   directly there.
4. **Could benchmark results become self-fulfilling?** Yes, in principle, if a benchmark score ever
   gated a self-edit promotion decision *and* Echo could see its own past benchmark history in context
   before generating a new attempt at a related task — this is architecturally the RAOC research
   question itself (§4), currently unanswered by any real evidence, which is exactly why §14 forbids
   automatic promotion on benchmark score alone.
5. **Could Echo learn that producing the expected label is more important than producing correct
   evidence?** Same mechanism as #4, sharper — this is the R-002/R-009 "taxonomy laundering" pattern's
   exact shape, generalized from a self-model claim to a benchmark score. No evidence exists either way
   for benchmarks specifically (nothing in this codebase currently exposes benchmark results to Echo's
   own generation), and this report does not recommend building that exposure without first resolving
   Q-007 (§13).
6. **Could the scoring system reward plausible explanations of failed runs?** Not under the current
   deterministic-sandbox-primary-oracle design — `objective_verify()` has no "explanation" input at
   all, only code and a test suite. This risk is specific to any future model-review layer, which §7
   explicitly scopes to *review of edge cases in the deterministic evaluator*, never as a primary
   grader.
7. **Could a model judge override deterministic failure?** Not in any tier of this archaeology —
   confirmed directly: `classify_result()`'s text-backstop heuristic can *reclassify a failure's
   attributed cause* (truncation vs. logic error), but has never been observed or designed to flip a
   `passed` boolean the real sandbox already determined. This boundary should be made an explicit,
   enforced invariant of the harness, not an accident of how it happens to have been built so far.
8. **Could repeated benchmark exposure teach Echo the benchmark rather than improve the underlying
   capability?** A real, live risk once any benchmark task set becomes reused/visible in Echo's own
   context or training signal — directly analogous to this project's own already-documented concern
   about `self_edit_generated.py`'s content leaking non-reproducibly into `ARCH_PIPELINE`'s prompts
   (Tier-3 §13). Containment requirement: benchmark task text and reference solutions must never be
   written to any location Echo's own retrieval/generation context can reach (§13).

**Verdict on the proposed architecture against this attack**: **safe as specified in §7, unsafe if any
future implementation collapses the evidence model into a summary label surfaced to generation.** This
report explicitly does not propose, and explicitly warns against, any field resembling `evidence_type
= "VERIFIED"` or `capability_status = "CONFIRMED"` anywhere in the schema (§18) — only raw,
structurally-separated evidence fields plus a distinctly-separated, never-authoritative
`interpretation` block.

---

## 10. R-004 saturation analysis (mandatory per §10 of the mission)

Applied to the metrics this archaeology actually used or considered:

| Metric | Floor | Ceiling | Observed variance in this corpus | Distinguishes strong from weak? | R-004-shaped saturation risk |
|---|---|---|---|---|---|
| Binary sandbox pass/fail per task-attempt | 0 | 1 | Wide — arm rates ranged 37.5%-88.1% across the real runs read this session | Yes, directly | Low — this is a real execution outcome, not a proxy score |
| Aggregate arm pass rate (e.g. "ARCH_COUNCIL = 67.9%") | 0% | 100% | Real, wide range observed | Yes, at the arm level | **Real, demonstrated risk if used alone**: this exact metric is the one Tier-4's own central finding shows can move dramatically (37.5pp→11.9pp between pilot and confirmatory) for reasons having nothing to do with the underlying capability changing — sample-size noise alone moved it. A permanent harness must never report this number without its confidence interval and n, per §11/§12. |
| "Best-of-N solvability" (oracle, ≥1 component passes) | 0 | 1 | **95-96% observed, both arms, independently reproduced twice** | **This is the R-004 case directly, demonstrated live in this archaeology, not hypothetical.** Both `BASE_N` and `ARCH_COUNCIL` land within 1.2 points of each other (95.2% vs 96.4%) despite the two arms' *delivered* results differing by ~28pp — the oracle metric is measurably insensitive to exactly the architectural difference (synthesis reliability) that turned out to matter most. Tier-4's own report states this precisely: "the raw model pool is not the bottleneck," which is true, but a harness reporting only this number would have missed the entire, decisive finding. |
| `select_best_fallback_candidate()`'s own historical "correct-pick rate" | 0% | 100% | 78.2%/93.6%/87.2% across three candidate ranking rules, measured | Yes | Confirmed non-saturated and genuinely discriminating (Tier-6/7) — this is a real counter-example showing the archaeology's own metrics are *not uniformly* subject to R-004; the risk is specific to aggregate/oracle-style metrics, not narrow structural ones |
| `_ast_complexity()`-based self-edit fitness score (CLAUDE.md Finding 91, cross-referenced, not re-derived here) | 0 | 8 (observed) | All 25 retained real deploys scored ≥3 pre-fix (saturated at the old threshold of 4) | **No, pre-fix** — the exact R-004 failure the mission cites by name, confirmed already occurred once in this codebase's real production history, already fixed by recalibrating against the real observed distribution rather than a round number | Already fixed; cited here as direct, first-party precedent that this class of failure is not theoretical for this project |

**Direct answers to the mission's two required questions**:

- *If Echo gets dramatically better, could the aggregate arm-pass-rate metric remain almost
  unchanged?* At small n (Tier-3's n=8), yes — demonstrated directly: the same underlying system
  produced a 37.5pp swing between two samples of comparable size (pilot n=8 vs. confirmatory n=84,
  stage-to-stage swing 4.76pp→19.05pp within the confirmatory run itself). A single small-n reading of
  this metric is **not adequate as a primary capability signal** without a confidence interval and a
  pre-registered sample size (§11/§12).
- *If Echo gets dramatically worse, could the best-of-N oracle metric remain almost unchanged?*
  **Yes, directly demonstrated** — this metric stayed within 1.2 points across two arms whose delivered
  quality differed by ~28pp. **The oracle metric is not an adequate primary capability metric on its
  own** — it must always be reported alongside the delivered (synthesized/final) rate, exactly as
  Tier-6's own terminology-precision finding insists ("best-of-3 candidate solvability," never "model
  capability," always paired with the true per-attempt rate).

**No composite score is proposed to hide either of these gaps** — see §11.

---

## 11. No single-number capability score unless justified

**Recommendation: capability-specific, per-comparison results with explicit confidence intervals and
n, never a single aggregate "Echo capability score."**

Directly demonstrated why a single number would fail, using this archaeology's own real data:

- A single "Council capability" number computed from Tier-3 alone (37.5pp disadvantage) and a single
  number computed from Tier-4 (11.9pp) describe, in a naive single-number report, what looks like two
  *different* systems — they are the same system, at two different sample sizes. Aggregation into one
  number, without the confidence interval, would have actively misled.
- A single "coding capability" score averaged across `BASE_1`/`BASE_N`/`ARCH_PIPELINE_ISOLATED`/
  `ARCH_COUNCIL` would average away the single most actionable finding in the whole archaeology
  (synthesis destroys correct candidates) — the information that matters lives specifically in the
  *gap* between the oracle rate and the delivered rate, a quantity a single blended score structurally
  cannot represent.
- A single number combining Tier-6's "correct-pick rate" and Tier-4's "final pass rate" would obscure
  that these measure genuinely different things at different points in the pipeline (candidate
  selection vs. end-to-end task success) — collapsing them risks exactly the "two qualitatively
  different systems receive the same score" failure the mission names.

If an aggregate is ever proposed for a specific downstream purpose (e.g., a single self-edit
promotion-gate number), it must state explicitly: why aggregation is legitimate for that specific
decision, what information it destroys (name the specific finding class — e.g., "this aggregate cannot
detect a synthesis-vs-generation split"), whether component weighting could let a catastrophic
per-component failure be averaged away, and whether two systems with materially different failure
modes (e.g., "fails on concurrency tasks" vs. "fails on refactoring tasks") could land at the identical
aggregate score. This report does not propose any such aggregate now.

---

## 12. Repetition/nondeterminism strategy

The lineage's own power-analysis arc is the direct, load-bearing answer here, and it converges on a
sharper number than a naive "run more trials" intuition would suggest:

- **Repetitions required is not driven by total task count — it is driven by the *discordant-pair
  rate*, independently measured at 3.6% (`ARCH_COUNCIL`) / 6.0% (`BASE_N`) across the full 168-event
  Tier-4 corpus** (Tier-5-counterfactual, re-confirmed by Tier-6, re-confirmed by Tier-7 — three
  independent derivations, identical number each time). A 20-30 task sample (the original, pre-Tier-4
  proposal) would be expected to produce only 1-2 discordant-eligible events — nowhere near sufficient
  for any formal conclusion. Detecting a large (80:20-split) effect at 80% power requires on the order
  of **100-500+ total tasks**, depending on which arm's discordance rate is used as the planning basis
  — this is a real, twice-independently-derived number from this project's own data, not a textbook
  default.
- **Fixed vs. variable seeds**: `BASE_1`/`ARCH_PIPELINE_ISOLATED` ran at temperature 0.0 (fully
  deterministic per call); `BASE_N`'s attempts and `ARCH_COUNCIL`'s councillors ran at jittered
  temperature (~0.7±0.15) by design, for genuine sampling diversity. Tier-4's own adversarial
  interpretation section names this directly as a real, disclosed, **not fully isolated** confound for
  why `BASE_1` outperformed the other arms — a concrete, cheap, flagged-but-not-yet-run follow-up
  (re-run `BASE_N` at temperature 0.0) exists in the record and should be a Phase-1 candidate.
- **Model/provider version drift**: not directly tested in this archaeology (single local Ollama
  deployment throughout) — a real, disclosed gap for any future cross-session comparison; the schema
  (§18) captures model/provider identity per record specifically so this becomes detectable rather than
  silently assumed stable.
- **Timeout/retry/infrastructure-failure handling**: already a first-class, separately-tracked category
  in every tier read this session (`INFRASTRUCTURE_FAILURE`, distinct from `TASK_LOGIC_FAILURE` and
  `GENERATION_TRUNCATED`), with an explicit override rule (Tier-3's H5: >15% infrastructure-failure
  rate voids the primary result regardless of pass-rate numbers) — this is already a correctly-designed
  pattern and should be reused verbatim, not redesigned.
- **Sleep/wake and environmental effects**: directly relevant, cross-referenced from `research/
  FINDINGS.md` R-010/Q-009 (this same investigation lineage's `echo_projects_autonomy` reliability
  thread) — a real, confirmed OS-level sleep/wake event was found correlated with a stalled autonomous
  loop elsewhere in this project. Tier-3's own contention-telemetry discipline (`ollama ps`, load
  average, swap, watchdog-log tail, checked immediately before every real generation batch) is the
  directly reusable mitigation and should be a mandatory, logged precondition for every harness run,
  not an optional nicety.
- **Explicit categories, never collapsed to "FAIL"**: this archaeology already, consistently,
  distinguishes capability failure (`TASK_LOGIC_FAILURE`) / evaluator ambiguity (`GENERATION_
  TRUNCATED`, spot-checked) / infrastructure failure (`INFRASTRUCTURE_FAILURE`, timeout/connection-
  error-pattern-matched) — a fourth category, **contamination/isolation failure** (Tier-8's own new
  finding), should be added as a first-class outcome category for any permanent harness, not folded
  into infrastructure failure.

---

## 13. Contamination analysis

Tier-8's own forensic audit (§20 above) is the authoritative source for this section — not re-derived,
cross-referenced directly:

- **Prior benchmark outputs in memory / cached retrieval results**: not found to be a live risk in
  this specific lineage (none of the audited scripts call `add_to_vector_memory()`/`retrieve_relevant_
  memories()`), but this is a property of *how these specific scripts happened to be written*, not an
  architectural guarantee — a future harness script that did call into memory-writing functions would
  need `install_isolation()`'s explicit no-op coverage, exactly as the four currently-covered call
  sites already demonstrate is achievable.
- **Benchmark artifacts remaining in the workspace / self_edit_generated.py leakage**: a real, already-
  disclosed, not-fully-closed confound — `ARCH_PIPELINE_ISOLATED`'s prompt includes the *live,
  continuously-self-edited* contents of `self_edit_generated.py`, which is confirmed (Tier-3 §5) to
  differ between runs at different times. This is disclosed as a genuine non-reproducibility source,
  not fixed, in every report that touches this arm.
- **RiverBrain background-writer contamination (Tier-8's central, new finding)**: `install_isolation()`
  blocks the four explicit write call sites (340/340 real interceptions confirmed) but does **not**
  stop RiverBrain's own unconditional 60-second background persistence thread, which starts the instant
  `get_river_brain()` is first called — before any patch can exist. One real historical run (Tier-3's
  dev-sanity pass) is classified `POTENTIALLY CONTAMINATED`: direct, evidenced temporal overlap with a
  live production process, not a hypothetical. **Per CLAUDE.md's own live production ledger (Finding
  89, cross-referenced, not re-derived), this specific gap has since been fixed** — `install_isolation()`
  now redirects `RIVER_BRAIN_PATH` to a scratch copy *before* the first `get_river_brain()` call,
  closing the gap at its root. This report treats the fix as real and applied, but was not asked to,
  and did not, re-verify it live this session (out of scope for a read-only Phase-0 archaeology pass).
- **Task suite / benchmark code visible to Echo**: not currently a live risk (no code path surfaces
  `audits/tier*_apparatus/` content to Echo's own generation or retrieval context, confirmed by the
  same absence-of-memory-write-calls finding above) — but this is the exact containment property §9
  item 8 depends on, and should be an explicitly tested, versioned invariant (a Liveness-Ledger-style
  canary, per §15) for any future harness that runs benchmarks more frequently or automatically.
- **Repeated exposure to the same task set**: the 90.5-95% pass rate observed on Tier-1/2 "easy" tasks
  in the original Tier-3 design pass (cited in `tier3_architecture_vs_model_design.md` §9 as a reason
  to exclude those tasks from the held-out suite) is itself a real, disclosed instance of near-ceiling
  performance on a task class the model pool may have effectively "seen" via broad pretraining exposure
  to common algorithmic patterns — not benchmark-specific leakage in this project's own sense, but a
  genuine, adjacent concern any permanent harness inherits from using publicly-common task shapes.

**Containment requirement for a permanent harness, stated directly**: (1) reuse `install_isolation()`'s
proven four-call-site pattern verbatim; (2) close the RiverBrain writer-thread gap by redirecting the
path constant before first access (already done, per the cross-reference above — verify live before
Phase 1 proceeds, do not assume); (3) never write benchmark task content or reference solutions to any
path `memory_bridge.py`'s retrieval or Echo's own prompt-assembly functions can reach; (4) treat
`self_edit_generated.py`'s live-file-content confound as a standing, permanent disclosure requirement
for any arm that reads it, not a one-time note.

---

## 14. Production boundary

**RESEARCH EVALUATION → evidence → RESEARCH LEDGER → human interpretation / explicit engineering
decision → PRODUCTION CHANGE.**

This is not a novel proposal for this codebase — it is already, in practice, how Tier-4's finding
became Tier-5's refactor: a full evidentiary report, an explicit human-directed mission ("repair the
architectural mechanisms responsible for the information-loss patterns"), a named engineer decision
(REFACTOR, not KEEP or RETIRE, with the decision rule stated: "the underlying idea appears useful, but
implementation/orchestration is causing measurable losses"), then a bounded, disclosed, gated code
change (`task_type == "coding"` only, verified against real historical replay before being trusted).
**This is the pattern to formalize, not invent.**

Explicitly, per the mission's own hard requirement: **no automatic production promotion based solely
on a benchmark score is recommended anywhere in this report.** This is not a generic caution — it maps
directly onto `research/FINDINGS.md` R-007 (RiverBrain's own trust-gate computed everything it needed
for ~2.5 months and never acted, until a human asked directly) and `research/DECISIONS.md` D-001
(automatic label-based authority is a demonstrated, named failure mode in this exact codebase). A
benchmark harness that auto-promoted a self-edit candidate, or auto-updated a self-model claim, purely
because a score crossed a threshold would recreate both failure classes at once — the "computed but
never human-checked" pattern *and* the "authoritative label substituting for inspected evidence"
pattern — in a single mechanism.

---

## 15. Liveness requirements

Following the Liveness Ledger's own established philosophy (functional canaries against the real
function, not import checks — `CLAUDE.md`'s own 41+-check pattern, cross-referenced not re-derived),
the minimum canary set for a permanent harness:

1. **`benchmark_task_suite_integrity`** — the frozen task suite's live SHA-256 still matches its
   recorded hash at every load, hard-fail (not warn) on mismatch. Direct precedent:
   `load_and_verify_held_out_suite()`'s existing hard-assert pattern, already proven across Tier-3/4.
2. **`benchmark_isolation_boundary`** — a functional canary confirming `install_isolation()` (or its
   successor) still blocks all explicit production write call sites AND still redirects the RiverBrain
   path constant before first access (closing Tier-8's own central finding) — modeled directly on this
   project's own `apply_to_code_sandbox_isolation`/`echo_projects_isolation` check shape (static
   source-anchor plus, where feasible, a real synthetic write-attempt probe).
3. **`benchmark_evaluator_discrimination`** — the deterministic sandbox scorer still correctly
   discriminates a known-correct and a known-incorrect fixture, run every time the harness executes
   (cheap, no new model calls) — the direct benchmark-harness analog of `task_type_classifier`'s own
   functional-canary check.
4. **`benchmark_result_persistence`** — a written result record can be read back byte-identical
   immediately after write, confirming the versioned ledger's own append path is not silently dropping
   or corrupting records (a cheap, mechanical check, not requiring any real generation).
5. **`benchmark_repeated_run_consistency`** — re-scoring an already-stored raw record produces the
   identical `passed` verdict as originally recorded (this exact check is what Tier-3's scoring
   analysis and Tier-5's counterfactual replay already performed manually, at 32/32 and 168/168 scale
   respectively — formalizing it as a standing canary, not a one-off analysis step, is the
   recommendation).
6. **`benchmark_known_regression_detection`** — feed the harness's own comparison layer a synthetic,
   known-answer pair (e.g., a fixture with a deliberately-injected 20pp drop between two "runs") and
   confirm the comparison/report layer correctly flags it — the harness-level analog of every other
   Liveness Ledger check's "degraded-evaluator" discrimination case.

None of these six require any new infrastructure beyond what this lineage has already built and
proven — they formalize existing, ad hoc verification steps (Tier-3's readiness-gate script, Tier-4's
raw-integrity re-check, Tier-5/6's replay-based re-verification) into standing, reusable checks.

---

## 16. Versioning requirements

**A benchmark result must never be represented as a bare percentage.** Minimum composite identity,
directly motivated by two real, already-occurred events in this archaeology, not hypothetical:

- **Benchmark identity must be versioned separately from system identity**, because this project's own
  history shows both can change independently and silently conflating them produces a wrong
  conclusion: `ARCH_PIPELINE`→`ARCH_PIPELINE_ISOLATED`'s rename (Tier-3) is a *benchmark definition*
  change (what is actually being measured changed); Tier-5's synthesis refactor is a *system* change
  (what is being measured stayed the same, the thing measured got different). A result reported as
  bare "ARCH_PIPELINE = 50%" is ambiguous between these two entirely different kinds of change and this
  project has already, in its own real history, needed to retroactively invalidate 13 records because
  this distinction wasn't tracked from the start.
- **Minimum hash set, per the mission's own list, all directly evidenced as necessary by this
  archaeology**: task set (already done, `held_out_task_suite.hash.txt`), evaluator code (not
  currently hashed anywhere in this lineage — a real, disclosed gap; `classify_result()`'s own logic
  changed at least once, per Tier-3's Objective-1 truncation-attribution repair, with no hash tracking
  which evaluator version scored which record), system git HEAD (already captured informally in every
  report's own "git status/HEAD before and after" discipline — should become a structured field, not
  prose), model/provider identity + configuration (already captured per-record in this lineage's own
  `model_used`/`total_calls`/`temperature` fields — formalize, don't invent).
- **A result should read as**: `benchmark_id=tier4_arch_council_v1, benchmark_version=<task_suite_hash>,
  evaluator_version=<classify_result_hash>, system_version=<git_HEAD_at_execution>, run_set=stage1+
  stage2(n=84) -> observed: 67.9% [57.3%, 76.9%]`, not `Council = 67.9%`.

---

## 17. Historical-result compatibility

Classifying each real historical artifact read this session against the mission's five required
categories:

| Artifact | Classification | Reasoning |
|---|---|---|
| Tier-3 held-out (`heldout_results.jsonl`) | **HISTORICAL ONLY** | The task suite and raw candidate text are intact and re-scorable, but the system under test (`river_deliberation.py`) has since changed (Tier-5 refactor) — re-running today would not reproduce a comparable live result, only a re-score of the frozen text, which is already done |
| Tier-4 confirmatory (`{stage1,stage2}_results.jsonl`) | **HISTORICAL ONLY** | Same reasoning, larger and more consequential dataset — this is the corpus multiple later tiers (5/6/7) correctly treated as a fixed, replayable artifact rather than something to rerun |
| Original 3-condition pilot (`audits/capability_pilot/raw_results.jsonl`) | **INVALID/UNUSABLE for the specific `ARCH_PIPELINE` isolated-generation comparison** | Explicitly, formally invalidated by the Tier-3 isolation-fix report itself (13 records total across this file and two Tier-3 dev-sanity variants) — preserved as a record of a real measurement defect, not usable as evidence for the question a permanent harness would ask today |
| `memory/synthesis_integrity_log.jsonl` (Tier-5 live validation) | **PARTIALLY RECONSTRUCTABLE** | Real, live data, but from only 5 tasks, explicitly stated by its own author to be too small to show a pass-rate delta — usable as a functional-correctness record (did the mechanism fire as designed), not as a capability-comparison data point |
| RAOC pilot (`memory/raoc_pilot_trials.jsonl`) | **HISTORICAL ONLY, explicitly non-evidentiary by its own author's design** | The classifier that scored these 12 trials was itself found to have a real gap (44.6% UNKNOWN rate) and was fixed *after* this pilot ran; the pilot's own log was deliberately left un-rewritten as an honest record of what the old classifier said at the time, per that mission's own explicit discipline (CLAUDE.md Finding 95, cross-referenced) — re-classifying it under the new classifier would itself be exactly the kind of retroactive rewrite this section's own instruction forbids |
| Any Tier-3..8 report's own prose narrative/conclusion | **NOT a benchmark result at all** | These are interpretation layers over the raw data above — they should be treated as the "RESEARCH LEDGER" layer of §14, never imported into a benchmark_results table as if they were primary data |

**No historical result is classified REPLAYABLE** in the strict sense of "produces the identical live
outcome if re-run today" — this is not a defect in the archaeology, it is the direct, correct
consequence of the system under test having legitimately changed. A permanent harness's own
versioning scheme (§16) exists specifically so this becomes an expected, disclosed property of the
ledger rather than a surprise discovered by trying to rerun something and getting a different answer.

---

## 18. Proposed minimal schema

Design only, not implemented, matching the mission's field groups exactly, with each field's
justification tied to a real, specific gap or success this archaeology demonstrated:

```
benchmark_identity:
  benchmark_id            # e.g. "council_vs_baseline_coding_v1" — stable across versions of the
                           # same underlying question
  benchmark_version        # hash of {task_set, prompt templates}, per §16
  task_id                  # e.g. "held_03" — already this lineage's own convention
  fixture_hash              # per-task reference-solution/test-code hash

system_identity:
  git_head                  # already informally captured every report; formalize
  dirty_clean                # was the working tree clean at execution time
  model_provider             # e.g. "ollama:qwen2.5-coder:7b" — already captured per-record
  model_configuration        # temperature, max_tokens, num_ctx — already captured, formalize
  relevant_environment        # e.g. Ollama version, MLX avoidance state (cross-reference:
                               # CLAUDE.md's own crash_awareness.py precedent for what "relevant
                               # environment" concretely means in this codebase)
  evaluator_version            # hash of classify_result()-equivalent code — CURRENTLY MISSING
                                # anywhere in this lineage; the single most important net-new field
                                # this report recommends adding, given the Objective-1 truncation-
                                # attribution repair changed evaluator behavior with no version marker

execution:
  run_id
  start_time / end_time
  duration
  attempt_number / retry_count
  timeout_status
  execution_status            # PASS / TASK_LOGIC_FAILURE / GENERATION_TRUNCATED /
                               # INFRASTRUCTURE_FAILURE / CONTAMINATION_SUSPECTED (new, per §12/§13)

evidence:
  raw_output_reference         # full, unextracted text — Tier-4's own single most valuable field
  trajectory_reference          # every mechanism_calls-shaped intermediate step, per §6
  artifact_references
  validator_outputs              # e.g. the truncation text-backstop's own verdict, kept separate
                                  # from execution_status per §8
  test_outputs
  hashes

evaluation:
  deterministic_result           # the real sandbox pass/fail — never overwritten by anything below
  human_review_status            # present + coverage_fraction, per §5's disclosed Tier-4 gap
  model_review_status            # present only if actually performed; never a primary oracle, per §9
  unresolved_questions            # explicit UNKNOWN markers, per the mission's own §4 instruction

interpretation:                  # kept explicitly, physically separate from evaluation — never
                                  # written back into raw evidence fields, per §8/§9
  observed_result
  interpretation
  claim_scope                     # e.g. "best-of-3 candidate solvability, not model capability" —
                                   # Tier-6's own terminology-precision finding, made a required field
  limitations
```

---

## 19. Explicit non-goals

- This is not a benchmark that produces a single "Echo capability score" (§11).
- This is not a mechanism for automatic production promotion (§14).
- This is not a taxonomy of truth labels (§8/§9).
- This does not attempt to resolve R-001/R-002/Q-007 (§20) — it is designed to eventually help measure
  around that boundary, not to solve it.
- This does not propose re-running any Tier-3..8 experiment as part of Phase 0 (none was executed this
  session; this is archaeology and design only, per the mission's own explicit constraint).
- This does not propose a domain beyond coding/executable tasks for Phase 1 — every reliable, primary-
  oracle scoring mechanism in this archaeology is sandbox-execution-based; extending to creative/
  reasoning/self-model domains would require a genuinely new evaluator layer this report does not
  design.
- This does not claim the RiverBrain writer-thread fix (cross-referenced from CLAUDE.md Finding 89) has
  been re-verified live in this session — it was not; Phase 1 should re-confirm it before relying on it.

---

## 20. Risks

1. **Taxonomy laundering** (§9) — the single most important, explicitly-named risk this mission was
   built to guard against; addressed structurally (no label-only field, evidence always preserved
   alongside interpretation) rather than by policy alone.
2. **Aggregate-metric regression-to-the-mean misreads** (§10/§11) — directly demonstrated once already
   in this project's own history (Tier-3→4's 37.5pp→11.9pp correction); mitigated by never reporting a
   percentage without n and a confidence interval.
3. **System-vs-benchmark version conflation** (§16/§17) — directly demonstrated once already (the
   `ARCH_PIPELINE` rename); mitigated by the proposed composite identity.
4. **Isolation gaps re-emerging** (§13) — a real, only-recently-closed gap (RiverBrain writer thread);
   mitigated by the proposed liveness canary (§15, item 2), not by a one-time fix alone.
5. **Evaluator drift with no version marker** (§18) — a real, already-occurred gap (the truncation-
   classification repair mid-lineage); mitigated by adding `evaluator_version` as a first-class,
   currently-missing schema field.
6. **Spot-check coverage silently dropping at scale** (§5) — Tier-3's 100% coverage did not carry
   forward explicitly to Tier-4's 10x-larger corpus; mitigated by making coverage_fraction an explicit,
   required field (§18) rather than an implicit assumption.
7. **Domain-narrowness mistaken for general capability** (§2/§19) — every reliable result in this
   archaeology is scoped to single-function coding tasks with an executable oracle; a permanent harness
   must carry this scope forward as an explicit, stated limitation on every report, not an implicit one.
8. **RAOC's harness existing being mistaken for RAOC's research question being answered** (§4) — named
   explicitly as the sharpest present example of exactly the risk this whole mission investigates.

---

## 21. Open questions

- Has the RiverBrain writer-thread isolation fix (cross-referenced from CLAUDE.md Finding 89) actually
  been re-verified live and end-to-end, specifically for a benchmark-harness use case, since it landed?
  Not confirmed in this session.
- What would a primary-oracle evaluator look like for creative/reasoning/self-model domains, where no
  executable test suite can exist? Entirely unaddressed by this archaeology and by this report.
- Should `evaluator_version` hashing be retrofitted onto the existing Tier-3/4 historical artifacts
  (making their `HISTORICAL ONLY` classification in §17 more precise), or only applied going forward?
  Not decided here.
- Is the temperature confound named in Tier-4's own adversarial-interpretation section (`BASE_1`
  deterministic vs. jittered multi-attempt arms) worth resolving before Phase 1 proceeds, or can Phase
  1 proceed with it as a disclosed, carried-forward limitation? Not decided here.
- Does `PENDING_DECISIONS.md`/`research/OPEN_QUESTIONS.md` need a new row specifically tracking "build
  the permanent capability benchmark harness" as a live decision item? Not added by this report,
  per this project's own convention that research-mission reports don't edit the decision ledgers
  themselves.

---

## 22. Recommended Phase 1

**Scope, deliberately narrow**: build the minimal schema (§18) and the six liveness canaries (§15) as
real, working infrastructure — nothing else. Specifically:

1. Implement the versioned result-record writer (§18's schema) as a small, standalone module, tested
   against synthetic fixtures only (no real model calls required to validate the schema/persistence
   layer itself).
2. Implement and verify all six liveness canaries (§15) against the *existing* Tier-4 corpus and the
   *existing* `install_isolation()`/`objective_verify()` functions — this can be done entirely as a
   read-only exercise against already-generated data, requiring zero new model calls, mirroring exactly
   the deterministic-replay discipline Tier-5/6/7 already proved out.
3. Re-verify, live, that the RiverBrain writer-thread fix (§13/§21) actually holds under a real,
   short, controlled harness invocation — before any Phase 2 mission spends real compute assuming it
   does.
4. Explicitly defer: any new capability comparison experiment (that is a Phase-2-or-later decision,
   not part of building the harness itself); any creative/reasoning/self-model evaluator (§19); any
   automatic promotion wiring (§14, permanently out of scope by design, not just by phase).

---

## 23. Files inspected

- `research/CURRENT_STATE.md`, `research/DECISIONS.md`, `research/FINDINGS.md`, `research/
  OPEN_QUESTIONS.md` — full content (read earlier this session, re-confirmed unchanged this mission).
- `audits/tier3_architecture_vs_model_design.md`, `audits/tier3_design_preflight.md`, `audits/
  tier3_arch_pipeline_isolation.md`, `audits/tier3_final_execution_gate.md`, `audits/
  tier3_heldout_execution_report.md`, `audits/tier3_heldout_scoring_analysis.md` — full content.
- `audits/tier4_confirmatory_protocol.md`, `audits/tier4_confirmatory_report.md` — full content.
- `audits/tier5_refactor_report.md`, `audits/tier5_counterfactual_replay.md` — full content.
- `audits/tier6_disagreement_resolution_forensic.md` — full content.
- `audits/tier7_riverbrain_candidate_ranking_forensic.md` — full content.
- `audits/tier8_experimental_isolation_forensic.md` — full content.
- `audits/echo_raoc_outcome_conditioning_experiment.md` — first 150 lines (protocol sections 1-14 of
  the design; sections beyond this point cover evidence-level mapping already summarized adequately
  via cross-reference to CLAUDE.md Findings 93-95, read earlier this session).
- `CLAUDE.md` Findings 86-95 (read earlier this session, re-confirmed relevant claims — self-edit
  fitness saturation/Finding 91, RiverBrain isolation fix/Finding 89, RAOC harness build and pilot/
  Findings 93-95).
- Directory listings and file-size checks: `audits/tier3_apparatus/`, `audits/tier*.md` inventory,
  `scripts/` (tier/RAOC-related scripts by name only, not full content — see §24), `app/experiments/`
  (subdirectory names only), `app/experiments/raoc/` (full file listing and line counts).
- `memory/raoc_pilot_trials.jsonl` (existence + size confirmed, content not read), `memory/
  raoc_trials.jsonl` (confirmed does not exist).
- `git status --short` / `git rev-parse HEAD` — checked at mission start and end.

## 24. Files NOT inspected

- `scripts/run_tier3_apparatus.py`, `scripts/run_tier4_confirmatory.py`, `scripts/tier4_analyze.py`,
  `scripts/tier5_counterfactual_replay.py`, `scripts/tier6_disagreement_analysis.py`, `scripts/
  run_capability_pilot.py`, and the remaining tier-related scripts — **not read directly this
  session**; their behavior is characterized entirely through the detailed, code-quoting reports these
  scripts themselves produced (each report reproduces the relevant real source excerpts directly, e.g.
  `install_isolation()`'s full body in Tier-8 §4). This is a real, disclosed depth limitation: claims
  about these scripts' exact current behavior are sourced from the reports' own direct quotations, not
  from an independent fresh read of the .py files in this session.
- `app/experiments/raoc/*.py` (7 files, 831 lines) — listed and sized, not read line-by-line; their
  design and findings are characterized via the pre-registered protocol document plus CLAUDE.md
  Findings 93-95's own detailed summaries (read earlier this session), not an independent code read.
- `app/core/river_deliberation.py`'s current, live source (the real synthesis pipeline Tier-5
  refactored) — not re-read this session; its post-refactor behavior is taken from the Tier-5/
  Tier-5-counterfactual/Tier-6/Tier-7 reports' own direct quotations, not independently re-verified
  against current source.
- `audits/tier3_apparatus/*.jsonl`/`*.json` raw data files themselves — existence and size confirmed
  (§23), content not read; all quantitative claims in this report are drawn from the analysis reports'
  own stated figures, not independently recomputed from the raw files in this session.
- `app/experiments/preference_provenance/`, `app/experiments/p3_causal_learning/`, `app/experiments/
  learning/`, `app/experiments/gen_epistemic/`, and the other `app/experiments/` subdirectories named
  in the pre-flight listing but not part of the Tier-3..8/RAOC lineage — noted as existing, not
  inspected, genuinely out of this mission's stated scope.

---

## What we can measure now

- Binary, deterministic, sandboxed pass/fail on single-function coding tasks with a pre-written,
  executable test suite — the one primary oracle every tier in this archaeology trusted and never
  found wrong at the core pass/fail level.
- The gap between best-of-N candidate solvability and delivered (synthesized) correctness — the single
  most decisive, mechanistically-explained finding this whole lineage produced.
- Whether a specific, narrow architectural change (e.g., an agreement-detection shortcut) causes a
  regression on an already-captured historical corpus, at zero new model-call cost, via deterministic
  replay.

## What we cannot measure reliably yet

- A stable, single-number "Echo capability" score of any kind (§10/§11).
- Anything about creative, reasoning, or self-model-domain correctness — no primary oracle exists.
- Whether a verified outcome injected as context causally shifts behavior (RAOC's own research
  question) — designed, harnessed, not evidenced.
- Whether the current, post-refactor synthesis pipeline's real improvement holds at confirmatory scale
  — Tier-5's own live validation sample (n=5) is explicitly too small to show a pass-rate delta.

## What existing experiments can be preserved

- The Tier-3/4 raw JSONL corpora, both task suites and hashes, both frozen protocols — as `HISTORICAL
  ONLY` artifacts (§17), fully re-scorable, not fully re-runnable to a comparable live conclusion.
- The deterministic-replay methodology itself (Tier-5/6/7's shared pattern) — directly reusable as a
  standing capability of any permanent harness, requiring no new model calls.
- The contention-telemetry and stop-condition discipline (Tier-3's §3/§4/§9) — directly reusable
  verbatim.

## What existing experiments must be redesigned

- The `select_best_fallback_candidate()` ranking rule (Tier-6/7's own recommendation, not yet
  implemented as production code per this session's reading — a real, evidence-grounded, low-cost
  fix still pending).
- Any future rerun of the Tier-4 comparison must account for the system having changed (Tier-5's
  refactor) — a literal rerun "to check the old number" is a category error; a fresh, versioned
  (§16) comparison against the current system is the correct next step, not a repeat of the old one.
- RAOC's confirmatory run needs its own, separately-authorized, properly-powered execution — the
  design and harness are ready; the evidence is not.

## What the harness would prove

- Whether a specific, named architectural or generation-pipeline change measurably improves or
  regresses task-attempt-level correctness on the specific, bounded task distribution it was tested
  against — with an honestly-reported confidence interval, not a bare percentage.

## What the harness would NOT prove

- That Echo is generally capable, intelligent, self-aware, autonomous, or truthful (per the mission's
  own explicit list) — no tier in this archaeology, at any point, claimed otherwise, and this report
  makes the same restraint explicit and structural (§8/§9), not merely a stated intention.
- That a benchmark score is safe to treat as ground truth for anything Echo says about itself — the
  opposite: `research/DECISIONS.md` D-001 already shows why not.

## Production changes explicitly deferred

- Every item in §19 (explicit non-goals) plus the `select_best_fallback_candidate()` ranking-rule fix
  named directly above — evidence-grounded and low-cost, but not implemented by this mission, per its
  own read-only constraint.

## Phase 1 recommendation

Build the minimal schema (§18) and the six liveness canaries (§15) only, entirely against already-
existing, already-frozen data — zero new model calls required. Re-verify the RiverBrain isolation fix
live before any Phase 2 mission spends real compute assuming it holds. Do not attempt a new capability
comparison experiment, a creative/reasoning evaluator, or any promotion-gating wiring as part of Phase
1 — each is a separate, later, explicitly-authorized decision.
