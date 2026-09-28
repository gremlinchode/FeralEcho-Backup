# Autonomous Acquisition From Counterfactual Experience — Forensic Feasibility Study and Proposed Protocol

**PHASE 1 + PHASE 2 ONLY. Per the governing mission's explicit stop
condition: no training episodes were created, no A/B artifacts were
generated, no successor conditions were run, no second task family was
begun, and no accumulation experiment was started. Nothing in this
document is authorized to execute. This is returned for adversarial
review.**

---

## 0. Correction (same day, after independently reading QUAL-1's raw result files rather than trusting the Stage 1 draft's own inline summary)

**This report's original Section 3 table and Section 1 claim that "the
constructor mechanism succeeds only at simple table lookup (K1)... and
fails at genuine induction (K2/K3)" is imprecise in a way worth stating
plainly, not quietly patched.** Section 2 of this report explicitly
flagged, at the time, that QUAL-1's raw results were "read only as quoted
inline in the Stage 1 draft, not independently re-derived" — and having
now gone and read `memory/experiments/accumulation_probe/v2/qual/results/{primary,posthoc_auditor_v2}/summary.json`
and `hand_adjudication.json` directly, the real picture is sharper and
different in one important respect:

- The **content auditor used to grade K1 drafts had a real bug** (missed a
  "category-first list" phrasing pattern) that was found via hand
  adjudication (56% agreement with hand judgment for the buggy v1 auditor,
  every disclosed disagreement being a K1 false negative) and fixed in a
  corrected v2 auditor, re-run posthoc against the same draft text (no new
  model calls). Under the corrected auditor: **K1's exact-content rate is
  1.0** (6/6 on R0, 5/6 on R1) — the constructor genuinely, reliably writes
  a correct status-code table from raw episodes. K1's overall status is
  "PARTIALLY QUALIFIED," not because the constructor's content is wrong,
  but because the shared behavioral retention gate's own sensitivity
  narrowly misses its threshold (0.833 measured vs. 0.85 required) — a
  worker-consumption issue, separate from constructor induction.
- **K2 and K3 remain genuinely, confirmedly NOT QUALIFIED** under the
  corrected auditor too (0.0 exact rate, unchanged by the auditor fix) —
  this part of the original claim holds.
- **The real, sharper characterization of the missing primitive**: the
  constructor can reliably induce a simple **enumerable fact-table** from
  episodes (K1 — aggregate many independent call→result pairs into one
  table). It cannot induce a **relational/procedural rule** requiring
  comparison across episodes (K2 — a total order implied by pairwise
  outcomes) or a **state-transition mapping** (K3 — an operation+constant
  per event, inferred from before/after states). This is a materially
  different, more actionable diagnosis than "K1 works, K2/K3 don't" read
  as a flat capability boundary — it points specifically at
  relational/procedural induction as the missing capability, not
  induction in general.
- **QB (the deepseek-r1:7b contingency), independently checked**: also
  NOT QUALIFIED for both K2 (0/6 exact, 1 empty/truncated draft) and K3
  (0/6 exact, **5 of 6 drafts empty/truncated** — its `<think>` block
  likely consumed the fixed `num_predict=400` budget before the actual
  note was ever written). K3's deepseek result is close to uninformative,
  not a clean negative — the model's real capability on K3 was barely
  tested due to an infrastructure/budget constraint, not shown to fail on
  the merits.

None of this changes the report's bottom-line recommendation (REVISE;
QUAL-2 is the right next step) — if anything it sharpens QUAL-2's actual
target (Section 6 below, revised in light of this). It is recorded here
because finding and disclosing this kind of error immediately, rather than
leaving a materially wrong claim standing in a document already delivered
to the user, is the standard this whole research thread holds itself to.

## 1. Executive Verdict

**REVISE — not AUTHORIZE, and not a flat "not currently testable."**

A substantially more rigorous version of almost exactly this experiment
already exists in this codebase, built by a prior session specifically in
response to the same VECT provenance problem this mission is reacting to.
It is called **AP-0** ("Accumulation Probe"), and its Stage 1 design
(`audits/2026-09-21_ap0_stage1_preregistration_v2_DRAFT.md`) already
implements: an experience→construction→independent-gate→persistence→
fresh-process pipeline; a genuine, non-authored extraction mechanism (a
neutral LLM call, not a hand-written lesson); a full doppelgänger-defense
arm structure including the exact cross-world crossover
(**P-X**) this mission calls for; invented, never-seen-in-pretraining
conventions specifically chosen to rule out the base-model-prior
doppelgänger; a rigorous, pre-justified statistical plan; and a Claims
Ladder more precise than the one this mission specifies.

**It is explicitly unfrozen and unauthorized, for a specific, empirically
grounded reason, independently confirmed by this session from source, not
taken on trust**: its own qualification test (**QUAL-1**) found that the
constructor mechanism — the piece that would need to autonomously *induce*
a general rule from raw episodes, as opposed to *transcribing* facts
already explicit in them — succeeds only at simple table lookup (K1) and
fails at genuine induction (an ordering rule, K2; an event→operation
table, K3). Raw, unprocessed episodes already solve K1 at 0.72 without any
constructor at all — so the one mechanism that currently exists adds
nothing over just keeping the log, for exactly the class of task this
mission's counterfactual design needs.

**Separately, and more authoritatively still**: a cross-checked
reconciliation between two independent research assessments
(`audits/2026-09-22_claude_codex_reconciliation_and_oct1_roadmap.md`,
dated two days before VECT even began) explicitly **demoted** this whole
line of inquiry (symbolic/procedural induction) to "component test"
status, in favor of a different primary research direction, and — this
session independently re-checked, not merely cited — found that
FeralEcho's own *best, most-verified* evidence (sandbox pass/fail, council
agreement) is currently structurally disconnected from the persisted state
that actually controls the system's future choices. That finding does not
directly block this mission's specific design (which does not route
through RiverBrain), but it materially changes the honest backdrop against
which any "Echo learns from experience" claim should be read.

**Recommendation, stated precisely**: do not build a new, competing
counterfactual-experience protocol from scratch. Adopt AP-0 Stage 1 v2 as
the target design (Section 6, 16), subject this session's own independent
attack (Section 15), and require — as a genuine, already-identified,
not-yet-executed prerequisite gate — **QUAL-2**: a constructor-architecture
search on fresh qualification worlds, exactly as AP-0's own Section 11
already proposes and this document has not modified. Do not run Stage 1
until a constructor genuinely qualifies for K2/K3-shaped induction, or
report QUAL-2's own negative result plainly if none does.

## 2. Evidence Inspected

- This session's own prior work: `audits/2026-09-27_restart_persistence_of_acquired_competence.md` and its full source chain (VECT's `CONTRACT.md`, `freeze_procedure.py`, `run.py`, `prompt.py`; `historical_difficulty_calibration/tasks.py`; the self-falsification audit `audits/2026-09-24_codex_validated_experience_transfer_self_falsification.md`) — already independently hash-verified and re-derived in that report, not re-verified a third time here.
- A directed background survey (Explore agent) of `audits/2026-09-06` through `audits/2026-09-14` (≈50+ files), specifically: `first_real_learning_loop.md`→`v1.1`→`v1.1_T4`→`v1.2_clean_causal_transfer.md`; `learning_gap_closure_architecture.md`; `consequential_learning_loop_design.md` + `consequential_loop_validation.md`; `missing_primitive_determination.md`; `shadow_treatment_harness_archaeology.md` + `shadow_correction_validation_archaeology.md`; `architecture_A_hot_stove_proof.md` + `hot_stove_credit_assignment_audit.md`; `orphaned_memory_retrieval_forensic_audit.md` + `latent_learning_reservoir_forensic_audit.md`; the four Michelangelo audits; `open_ended_learning_discovery.md`; plus direct source reads of `app/experiments/first_learning_loop/{lesson_mining.py,harness.py}` and `app/learning/dual_learning.py`.
- Direct reads by this session (not delegated): `audits/2026-09-21_ap0_stage1_preregistration_v2_DRAFT.md` (full text), `audits/2026-09-22_claude_codex_reconciliation_and_oct1_roadmap.md` (full text), and `app/experiments/accumulation_probe/constructor.py` (full source — the actual extraction mechanism, not a description of it).
- Not read in full in this pass, due to time budget, and flagged rather than silently skipped: `audits/2026-09-21_ap0_stage0_preregistration_v1.md`, `audits/2026-09-21_ap0_v2_causal_chain_and_skeptic_review.md`, `audits/2026-09-21_ap0_v2_constructor_qualification_protocol.md` (QUAL-1's own full protocol/results), `audits/2026-09-22_codex_ap0_independent_forensic_audit.md`, and the rest of `app/experiments/accumulation_probe/`'s ~20 other source files (`jail.py`, `tasks.py`, `tasks_v2.py`, `worlds.py`, `stage0.py`, `run_arm.py`, `oracle_b*.py`, `qual*.py`). The QUAL-1 numeric results themselves were read only as quoted inline in the Stage 1 draft (Section 1, Section 3's placeholder), not independently re-derived from the underlying qualification protocol/logs — this is a real, disclosed limit on this report's own verification depth, not glossed over.
- Real calibration data: `memory/experiments/historical_difficulty_calibration/calibration_results_qwen2.5-coder_7b.jsonl` (25 rows, directly recomputed: Level 1 5/5, Level 2 5/5, Level 3 5/10, Level 4 0/5).
- `PENDING_DECISIONS.md` (no open rows bearing on this question as of 2026-09-09).

## 3. Current Acquisition Mechanism — What Actually Exists

Five real candidates were found, none of which clears the bar this
mission sets (autonomous, non-authored, causally-effective, restart-
persistent):

| Mechanism | Non-authored content? | Genuine induction (not just transcription)? | Measured behavioral effect? | Restart-persistent? |
|---|---|---|---|---|
| `first_learning_loop/lesson_mining.py` | **Yes** — pure regex extraction + fixed f-string template, zero LLM/human/Claude prose | N/A — mechanically extracts already-explicit facts, does not induce | **No** — rigorously disproven across a 4-version correction chain (v1→v1.2), final verdict RED: *"the lesson was verifiably present in the prompt... and had zero detectable effect on what was generated"*; independently reconfirmed by `architecture_A_hot_stove_proof.md`'s matched-pair test (CONTROL 5/6 = EXPERIENCE 5/6, McNemar p=1.0, "HOT-STOVE NOT PROVEN") | N/A (no effect to persist) |
| RiverBrain `learn()`→`model_task_stats`→`score_model()` | Partially — the persisted value is a numeric mean from a cheap syntactic heuristic, not semantic text | No — a scalar preference shift, incapable by construction of situational/content-level lessons | **Yes, for the heuristic-fed path** (VERIFIED L3, direct empirical test) — but the Sept-22 reconciliation found, and this session independently confirms is a real, current-source claim (not re-derived from scratch here), that the two functions fed by genuinely *verified* outcomes (`learn_from_sandbox_outcome`, `learn_from_council_rating`) never touch `model_task_stats` at all — only the cheap-heuristic path does | Yes (`river_brain.pkl`, previously verified) |
| `accumulation_probe/constructor.py` | **Yes** — a neutral LLM call (`constructor_user()`), asked to state "the site's convention completely and precisely" from raw episode call/result pairs, with explicit instructions not to guess beyond what episodes establish; verified directly from source, not narrated | **Qualified for K1 (table lookup) only.** QUAL-1's own finding, quoted in the Stage 1 draft: raw unprocessed episodes (E) already reach 0.72 on K1 without any constructor; the constructor adds nothing there and fails on K2/K3, exactly the conventions requiring genuine rule induction rather than enumeration | Not yet tested behaviorally — Stage 1 (which would test this) has not run | Would be, by design (Stage 1 specifies hash-committed carriers), but untested |
| Self-edit attempt-ledger → `_build_targeted_prompt()` | **Yes** — the raw real sandbox traceback text, captured before any overwrite, not summarized or interpreted | N/A — delivers raw evidence, does not induce a rule from it | **Unknown, by the report's own explicit statement**: *"CONNECTED BUT NOT YET SHOWN CONSEQUENTIAL... a deliberate scope decision, not an oversight"* — no held-out matched-pair experiment has been run for this wire | Yes (the ledger is a durable file) |
| `dual_learning.py`'s `TinyModel` | **Yes** — a genuine PyTorch `nn.Sequential`, real `Adam`/`.backward()`/`.step()`, zero LLM-text semantic authorship of any kind | N/A — the only task it is built to learn is self-supervised reconstruction of a truncated slice of its own input embedding; no labeled/evaluated task exists in its design at all | **No artifact has ever been produced** — `dual_model.pt` does not exist anywhere on the machine, confirmed independently twice (this survey and the prior `open_ended_learning_discovery.md` mission); its one real caller has nothing downstream even hypothetically consuming a trained model | N/A (nothing has ever been trained to persist) |

**Verdict**: no mechanism currently in this codebase both (a) autonomously
derives non-authored content that goes beyond simple transcription of
already-explicit facts, and (b) has been shown to cause a measurable,
restart-persistent behavioral improvement. The one mechanism capable of
(a) in principle — `constructor.py`'s neutral LLM extraction call — has
been directly, empirically shown to fail at (a) for the specific class of
task ("induce a general rule from evidence, don't just transcribe
enumerated facts") this mission's counterfactual design structurally
requires.

## 4. Exact Provenance Gap Left by VECT/Restart Persistence

Independently confirmed by this session on 2026-09-27
(`audits/2026-09-27_restart_persistence_of_acquired_competence.md`
Section 1): VECT's `procedure_frozen.json` is a literal, investigator-
authored (Claude-authored) string; `freeze_procedure.py`'s only
substantive check is that cited episode IDs exist in
`experience_log.jsonl`, never that the clauses were algorithmically
derived from outcomes.

**A fact worth stating plainly, not asserted with more confidence than
warranted**: AP-0 (2026-09-21) predates VECT (2026-09-23/24) by two days,
and AP-0's own explicit purpose was to test exactly this gap — whether a
constructor can autonomously derive a procedure from episodes, as opposed
to a human/Claude writing it. AP-0's QUAL-1 had, by the time VECT began,
already found that the autonomous version fails for anything beyond
simple transcription. This session cannot establish *why* VECT's approach
took the investigator-authored shortcut instead of routing through the
already-existing (if already-known-to-be-limited) constructor mechanism —
that would require reading intent this document has no access to — but
the timeline is suggestive enough to record as a hypothesis, not a
conclusion: VECT's own procedure (marker-set completeness, line-start
anchoring, take-to-end-not-one-big-regex) is exactly K2/K3-shaped
induction, not K1-shaped transcription, and is exactly the shape QUAL-1
had already found the constructor mechanism cannot produce.

## 5. Strongest Non-Learning Doppelgänger

The single most important design lesson this feasibility study surfaces,
independent of any specific arm structure: **task-family choice is itself
the primary doppelgänger defense, and it must not use real-world
programming idioms.**

VECT's task family (`extract_code`, real Python syntax rules — decorators,
docstrings, import statements) is real-world knowledge a pretrained code
model plausibly already has generic priors about, independent of any
specific episode it is shown. This session's own restart-persistence
experiment (Section 5 of that report) found P's advantage tracked its
specific clauses with real mechanistic precision — genuinely strong
evidence for *that* experiment's narrow persistence claim — but it cannot
by itself rule out that a model shown *any* reasonably-worded reminder
about Python code boundaries would perform similarly, regardless of
whether the reminder's specific wording came from real observed failures
or a generically plausible guess. AP-0's design solves this the correct
way: **its three "conventions" (K1/K2/K3) are entirely invented, arbitrary,
per-world facts** (an arbitrary code→category map; an arbitrary tag
priority ordering; an arbitrary event→operation table) that cannot exist
in any pretraining corpus by construction — a model can only get them
right by consuming the supplied episodes, full stop. **Any new
counterfactual A/B design for this mission must use invented, per-
instance-random conventions of this kind, not real-world programming
idioms**, or the "the model already knew this regardless of which
episodes it saw" doppelgänger cannot be ruled out.

The remaining doppelgängers from the mission's own list, and how AP-0's
existing design (verified from source, not narrated) already addresses
each:

| Doppelgänger | AP-0's control |
|---|---|
| Base-model prior already contains the strategy | Invented, per-world-random conventions (above) |
| Finite task-bank memorization | Sealed hidden VAL/TEST case streams, mutation-tested (every single-parameter mutant is killed), materialized only after carrier hashes are committed |
| Constructor merely compiles/paraphrases episodes without adding information | **D (beyond restating)**: P vs E (raw episodes in carrier) vs IC (episodes inline) — a direct, pre-registered contrast |
| Content is investigator/harness-authored, not experience-derived | **P-X arm**: an artifact built from world *a*'s episodes tested on world *a*'s tasks, vs. the *other* realization's artifact (*b*) — the exact cross-world crossover this mission's own "A→Bstate, B→Astate" section asks for, already specified |
| Any procedure-shaped text helps regardless of content | **MISMATCH arm**: same tokens, systematically wrong |
| Retention/gate selects a lucky draft, not genuine encoding | **FAILED-DRAFT arm**: the first gate-failing draft from the same process, compared against P |
| Evaluator/condition leakage, filename/ID leakage | Explicit "bypass controls, arrow by arrow" table (Section 4.3), cross-referenced to a dedicated `causal_chain_and_skeptic_review.md` this report did not re-verify line-by-line but whose existence and stated scope were confirmed |
| Shared model-server/context residue | Model unloaded (`keep_alive=0`) between acquisition and evaluation, plus KV-cache-affects-latency-only reasoning backed by an 8/8 same-seed-identical observation |
| Deterministic-sampling artifacts | Fixed seeds matched across arms within (world, task, sample); no retries after a response is produced |

**What AP-0's own design explicitly does NOT close, stated in its own
words, not softened here**: *"Stage 1 cannot distinguish learning from
compilation, cannot show the system chose its own experience, and cannot
show the schema was learned."* Episode selection (which facts to show)
and task schema (the fact that a lookup-table/ordering/mapping convention
exists at all) remain harness-authored. This is a real, permanent
limitation on how far *any* version of this design — this document's or a
future one's — can push the "autonomous" claim, and it should be stated
in any future report's claim boundary exactly as plainly as AP-0 already
states it.

## 6. Proposed A/B Counterfactual-Experience Design

**Recommendation: adopt AP-0 Stage 1 v2's design (already fully specified
in `audits/2026-09-21_ap0_stage1_preregistration_v2_DRAFT.md`) as the
target for this mission's "Learner A / Learner B" framing, rather than
building a parallel, less-mature protocol.** The mapping is close to
one-to-one:

- This mission's "Learner A receives experience supporting strategy A;
  Learner B receives counterfactual experience supporting strategy B" =
  AP-0's two **realizations** (*a*, *b*) of each invented convention,
  each with its own real, disjoint episode set.
- This mission's "A+/A−/B+/B−" ablation = AP-0's **P vs NEUTRAL** contrast,
  run per realization (Hypothesis A).
- This mission's "A→Bstate / B→Astate crossover" = AP-0's **P-X arm**
  exactly (Hypothesis B, "experience-swap double dissociation").
- This mission's "gate/retention" requirement = AP-0's **independent gate**
  (the worker, not the constructor, must solve ≥2/4 VAL tasks before a
  draft is retained as P) plus the **FAILED-DRAFT** arm.

**Where a genuine, independently-derived attack found something AP-0's
draft does not fully specify**, noted for the record rather than silently
folded in as if it were always there:

- AP-0's constructor (`constructor.py`) currently uses one fixed prompt
  template per convention kind. If QUAL-2 (Section 11 below) ends up
  iterating on prompt wording to get K2/K3 working, there is a real risk
  that *tuning the prompt while watching K2/K3 outputs* becomes a subtle
  channel for investigator semantic authorship (the prompt engineer
  learns what phrasing makes the model state the right kind of fact, and
  that phrasing itself starts encoding schema-level guidance beyond the
  neutral "state the convention completely and precisely" framing already
  used). AP-0's own Section 11 partially anticipates this ("pre-declare...
  on *fresh* qualification worlds... to avoid tuning to them") but the
  risk is broader than world-reuse alone — it also applies to prompt
  wording itself, and should be explicitly logged (every constructor
  prompt variant tried, and on what data, before any final choice is
  frozen) so a future reviewer can check whether the winning prompt was
  arrived at by genuine architecture search or by iterative semantic
  tuning against outcomes.

## 7. Retained-State Generation Mechanism

`constructor.py`'s `constructor_user(kind, episode_lines)` (verified by
direct source read, Section 3 above): builds a prompt containing the
task's public schema description (`T1.BASE_SPEC[kind]` — e.g., "the site
assigns each code to a category") and the raw, real episode call/result
pairs, then asks a local model (per AP-0's design, the same frozen worker
model used for evaluation) to "write ONE reusable procedure note that
states the site's convention completely and precisely," explicitly
instructed to write "not established" rather than guess where episodes
don't settle a fact. This is genuinely non-authored: no human or Claude
writes any part of the resulting note's prose; the neutral prompt template
(investigator-authored infrastructure, explicitly permitted by the
mission) contains zero clauses about *what* the convention is, only
instructions about *how* to report it.

**Ground-truth content auditor** (`audit()`, same file): a separate,
Claude/investigator-authored function that scores a produced note's
*factual correctness* against the real, known-by-construction convention.
Its own header comment states plainly it is used "ONLY for constructor
qualification (in Stage 1 the truth is unknown; the retention gate there
is behavioural)" — i.e., this ground-truth checker is never available to
or consulted by the actual Stage 1 pipeline; it exists solely so a prior
session could measure, during qualification, whether the constructor's
autonomously-generated note was actually correct. This separation
(qualification-only oracle vs. behavioral-only Stage-1 gate) is a real,
important, already-solved design property worth preserving in any
revision.

**What it can do**: produce genuinely non-authored natural-language
procedure text for simple, fully-enumerable conventions (K1). **What it
cannot yet do**: produce a correct note for conventions requiring
induction over a pattern (an ordering rule inferred from pairwise
comparisons, K2; an operation inferred from before/after states, K3) —
this is QUAL-1's own empirical finding, not assumed here.

## 8. Ablation/Crossover Design

Fully specified in AP-0 Stage 1 v2 Section 4.1 (arms) and Section 5
(endpoints): **N, NEUTRAL, MISMATCH, E, IC, H, P, P-X, FAILED-DRAFT** — 9
arms, each with a stated purpose (Section 6 table above maps each to a
specific mission requirement or doppelgänger). Two realizations per
convention specifically to make **P-X** (crossover) meaningful — a design
choice this session's own review confirms is necessary, not incidental:
"a single realization cannot distinguish 'the carrier encodes this world'
from 'any procedure-shaped carrier helps'" (quoted directly from the
document, and independently judged sound: without a second, distinguishable
real world, there is nothing for a crossed artifact to be *wrong about* in
a detectable way).

**Not included, and worth naming as a real scope boundary**: AP-0's arms
test artifact-content specificity (does *this* artifact encode *this*
world), not accumulation of multiple simultaneously-retained artifacts —
appropriately, since the governing mission scopes this to Levels 1-3 only
and explicitly forbids beginning any accumulation-ladder work.

## 9. Process and Inference-Server Isolation

AP-0 Stage 1 v2 Section 4.2 step 5 specifies a materially stronger
isolation regime than this session's own 2026-09-27 restart-persistence
experiment used, and the gap is worth naming plainly: that prior
experiment ran R+ and R- as separate OS processes (confirmed via distinct
PIDs and distinct `id(sys.modules)`), but explicitly disclosed that both
conditions called the *same, not-restarted* live Ollama server process —
a real, if likely negligible at temperature=0, residual channel. AP-0's
design closes this more thoroughly: **the model is explicitly unloaded
(`keep_alive=0`) between acquisition and evaluation**, evaluation arms run
in **kernel jails** that cannot read acquisition ledgers/VAL
tests/the oracle, and evidence is recorded per call — carrier hash
before/after, PID and start time strictly later than acquisition's exit,
jail profile hash, every request body hash-chained and re-derived from the
frozen plan. This is a real, verifiable improvement over what was
achievable in this session's own smaller-scope restart-persistence work,
and should be preserved rather than weakened in any revision.

**Disclosed, not eliminated, per AP-0's own text**: "the live FeralEcho
server shares the Ollama queue; its process ids and any restart during the
run are recorded per call window (a restart cannot change outputs —
stateless API — but is disclosed)." This session did not independently
re-verify the "stateless API" claim for the specific Ollama version
currently running on this machine; it is inherited from AP-0's own
apparatus work, not re-derived here.

## 10. Held-Out Novelty Strategy

AP-0's mutation-tested hidden case design (Section 4.1: "every single-
parameter mutant is killed"; hidden **VAL** and **TEST** case streams
disjoint; re-verified against an independent second implementation and the
real sandbox) is structurally stronger than VECT's own original design,
which this session's prior report (Section 1) found to have zero new code
content across TRAIN and held-out sets. AP-0 additionally seals **TEST**
worlds only after acquisition-side carrier hashes are already committed
(Section 4.2 step 6), with a hash-chained exposure log recording the first
read of every sealed file, and treats any acquisition-side read of a
sealed file as an **abort** condition (INVALID, not merely "no effect") —
a materially stronger novelty/leak guarantee than anything this session
built independently on 2026-09-27.

**What "unseen" means here, stated explicitly** (per the mission's own
instruction to document this precisely): a held-out instance is unseen if
its exact input/task template was never shown to the constructor as an
episode or a VAL-gate task, and its underlying convention-fact combination
was never part of the constructor's or gate's observed evidence for that
world/realization — checked mechanically via the mutation/re-derivation
process, not asserted from task-ID disjointness alone (the lesson VECT's
own generator-bank-size bug taught this exact research thread once
already).

## 11. Evaluator/Contamination Controls

AP-0 Stage 1 v2 Section 4.3's "bypass controls, arrow by arrow" table
(quoted in Section 6/9 above) already covers every item on the governing
mission's own checklist: hidden tests/evaluator → constructor (jail + leak
scan, OBSERVED zero leaks in 432+72 requests during QUAL); previous
responses/orchestration state → evaluation (separate processes, carrier-
only channel); production memory/RiverBrain/FAISS/routing (confirmed not
imported, static+dynamic audit); filenames/task IDs (never in prompts,
re-derivation confirmed); context residue (KV cache affects latency only,
INFERRED, backed by an 8/8 same-seed-identical observation); prompt-
structure differences (identical templates, only carrier content differs;
length-matched controls). This session did not re-run any of these checks
itself — they are inherited from AP-0's own apparatus verification, cited
here rather than re-derived, per the time-budget disclosure in Section 2.

## 12. Prospective Statistical Plan

AP-0 Stage 1 v2 Section 5's plan (quoted in full above) is adopted
essentially as-is, since it is already more rigorous than what this
document would derive independently: a single primary confirmatory
contrast (E-A: P−NEUTRAL, cluster bootstrap over task templates, 10,000
resamples, both a minimum gain and a lower-bound threshold); co-required
gates (E-B content-specificity via MISMATCH and P-X; E-C gate validity via
FAILED-DRAFT; N-ctl non-inferiority on unrelated/conflicting-convention
tasks) combined by intersection so no multiplicity correction is needed;
every secondary contrast (E, IC, H comparisons; per-convention rates;
same-shape vs. structural transfer) explicitly labeled descriptive and
Holm-adjusted, never used to rescue a failed primary. Thresholds are
justified from real Stage 0 task-level standard deviations, not chosen to
guarantee significance (the mission's own explicit statistical standard).
This session's contribution here is verification of intent, not
re-derivation of the numbers: the constants (`P_MIN_GAIN=0.25`,
`P_GAIN_LOWER_MIN=0.10`, etc.) were read as stated in the source document
and were not independently recomputed from Stage 0's raw data in this
pass.

## 13. Claim Ladder and Decision Rules

AP-0 Stage 1 v2's own Section 9 ("Claims ladder") and Section 8 ("What
each outcome would mean") together form a claim-ladder that is more
precise than, but maps cleanly onto, the governing mission's Level 0-5
framework:

| Mission's level | AP-0's equivalent | AP-0's exact allowed language |
|---|---|---|
| Level 0 (no acquisition evidence) | "P ≈ NEUTRAL while H ≫ NEUTRAL" outcome row | "acquisition failed... not permitted to conclude 'the system cannot learn'" |
| Level 1 (experience-dependent artifact formation) | Hypothesis B / P-X dissociation | "experience-dependent construction of retained actionable state — the strongest claim Stage 1 can support, and only for conventions in Q" |
| Level 2 (retained-state causal effect) | Hypothesis A (P beats NEUTRAL) + Hypothesis C (gate validity) | requires all co-required gates, not just a raw P>NEUTRAL gap |
| Level 3 (restart-persistent acquired competence) | Section 4.2 step 5 (fresh-process, model-unloaded evaluation) | "persistent acquired behavioural competence — only... 'applied to new inputs and new task shapes in a fresh process'; not durable, not accumulating, not autonomous [in the episode-selection sense], not weight learning" |
| Levels 4-5 | Explicitly out of scope for Stage 1 | "Forbidden in any Stage 1 write-up: 'FeralEcho learned', 'accumulation', 'autonomous learning'..." |

AP-0's Section 8 outcome table (reproduced in full in Section 16 below) is
adopted without modification — it already specifies, for every plausible
outcome including the K1-succeeds/K2-K3-fail pattern QUAL-1 already
predicts, exactly what may and may not be concluded.

## 14. Implementation Changes That Would Be Required

1. **QUAL-2** (AP-0's own Section 11, item 1) — not yet built. A
   pre-declared search over 1-2 alternative constructor architectures,
   tested on **fresh** qualification worlds (never the ones already used,
   specifically to prevent tuning-to-the-test): candidates named in AP-0's
   own text are a staged constructor (observations → hypothesis →
   verification against episodes → note), a stronger local model, a
   self-consistency filter (the draft must reproduce the episodes' own
   outputs when applied by the worker — a behavioral self-check using only
   experience, no oracle), or a programmatic hypothesis-enumeration
   constructor (explicitly disclosed by AP-0's own text as hard-coding the
   hypothesis space, which would shrink the eventual claim to "persistence
   and consequence of an experience-derived artifact," not "the model
   induced the rule" — a real, different, smaller claim, not a way of
   silently passing the same test).
2. **The Stage 1 orchestrator itself** — per AP-0's own Section 10,
   "does not exist yet and must be built and self-tested (mock server...)
   before any freeze." Not built in this pass, per the stop condition.
3. **Not required for this specific mission**: the Sept-22 reconciliation's
   RiverBrain-wiring fixes (verified-outcome-to-ranking-mean gap,
   `generate_code_from_plan`'s attribution gap). Those matter for the
   *separate*, demoted-to-non-primary "outcome-conditioned strategy
   selection" research direction that reconciliation named as primary —
   AP-0's constructor/gate mechanism does not route through RiverBrain at
   all, confirmed by source read in Section 3/7. Naming this explicitly so
   a future reader does not conflate the two open threads or assume fixing
   one unblocks the other.

## 15. Risks / Unresolved Confounds

- **Prompt-tuning-as-authorship risk in QUAL-2** (Section 6) — the
  sharpest, most novel risk this independent review adds beyond what AP-0's
  own documents already state. Mitigation: log every constructor prompt
  variant tried in QUAL-2, and on what data, so a future reviewer can
  distinguish genuine architecture search from iterative semantic tuning.
- **Schema and episode-selection remain harness-authored**, permanently,
  by AP-0's own admission (Section 5) — no version of this design, however
  revised, can claim the *convention's existence* or *which episodes to
  show* were autonomously discovered. This bounds every future claim from
  this line of work, not just this specific report.
- **Budget**: AP-0's own estimate is ≈1,550-2,300 real model calls, ≈6-9
  hours, once Stage 1 is actually frozen and run (QUAL-2 itself would be
  smaller, unestimated in this pass). This is substantially larger than
  this session's own 2026-09-27 restart-persistence experiment (2
  subprocess runs, 20 real calls total).
- **Shared Ollama-server/live-production concurrency** (Section 9) —
  disclosed by AP-0's own design as a residual, not fully eliminated,
  channel; unchanged by this review.
- **This report's own verification depth is bounded** (Section 2) — the
  QUAL-1 numeric results were read only as quoted inline in the Stage 1
  draft, not independently re-derived from `qual.py`/`qual_posthoc.py`'s
  raw output; the skeptic review and the independent Codex AP-0 forensic
  audit were not read in this pass. A future session picking this up
  should read those before treating QUAL-1's "K1 succeeds, K2/K3 fail"
  finding as beyond further question — this report treats it as
  well-evidenced, not as independently re-proven from raw logs.

## 16. Exact Proposed Frozen Protocol

**Not newly authored here — adopted, with the amendments explicitly
listed below, from `audits/2026-09-21_ap0_stage1_preregistration_v2_DRAFT.md`,
which remains itself DRAFT/UNFROZEN.** Reproducing a fresh, competing
protocol document would misattribute real intellectual work already done
in this codebase and risk silently diverging from a design that has
already survived one round of internal self-attack (its own Section 3
qualification failure, its own explicit list of what it cannot establish).

**Prerequisite gate, before Stage 1 itself may be frozen (this report's
one substantive addition to AP-0's own stated path)**:
1. Run **QUAL-2** exactly as AP-0's Section 11 item 1 specifies: 1-2
   alternative constructor architectures, tested on fresh worlds never
   used in QUAL-1, with every prompt/architecture variant tried logged
   (Section 15's mitigation).
2. **If QUAL-2 finds no architecture that qualifies for K2/K3** (i.e., the
   negative result repeats): this is itself a complete, valid, reportable
   Level 0 finding for this whole research direction — write it up plainly
   ("no local-model-based constructor mechanism currently available in
   this codebase can perform genuine rule induction beyond simple
   transcription, across two independent architecture attempts") and do
   **not** proceed to Stage 1 with a constructor known not to work for the
   conventions that matter.
3. **If QUAL-2 finds a qualifying architecture**: freeze AP-0 Stage 1 v2
   exactly as drafted (Sections 0-11 of that document), substituting the
   qualifying constructor for the current one, with the prompt-logging
   discipline from Section 15 carried forward into the frozen protocol
   itself as an explicit integrity-gate item (currently absent from
   Section 7's list, and it should not be).

**No other change to AP-0 Stage 1 v2's design is proposed.** Its
hypotheses (Section 2), arms (4.1), acquisition protocol (4.2), bypass
controls (4.3), thresholds (5), apparatus (6), integrity/exclusion/abort
rules (7), outcome table (8), and claims ladder (9) are adopted in full,
as already reproduced or summarized in Sections 6-13 above.

## 17. Recommendation: REVISE

**Not AUTHORIZE**: Stage 1 as currently drafted is explicitly, correctly,
self-identified as unqualified to run (its own constructor fails the
conventions that matter).

**Not "NOT CURRENTLY TESTABLE" without qualification**: a well-specified,
already-largely-built path to testability exists (QUAL-2), has not yet
been attempted, and is cheap relative to Stage 1 itself.

**REVISE, specifically**: authorize QUAL-2 (Section 16, step 1) as the
next concrete, bounded, cheap piece of work — not Stage 1 itself, and not
a new, competing protocol. Report QUAL-2's outcome plainly regardless of
direction, per this whole research thread's own established discipline
(Section 3's own correction-chain history — `first_real_learning_loop`
v1→v1.2 — is the clearest example in this codebase of exactly that
discipline being followed under pressure to find a positive result).

---

## Plain-Language Answer

> **If this proposed experiment (AP-0 Stage 1, once QUAL-2 unblocks it)
> produced its strongest predicted positive result, what exactly would we
> have learned about Echo — and what would we still NOT know?**

We would have learned that a frozen, 7-billion-parameter local model,
shown real evidence about an invented rule it could not have known in
advance, can turn that evidence into a written note — through its own
inference, not a human's or Claude's writing — that a completely separate,
later invocation of the same model can read off disk and use to solve new
problems about that same invented rule, including problems shaped
differently than any it was shown. We would know this note's content
really does trace back to the specific evidence it was given, because
swapping in the note built from *different* evidence about a *different*
version of the rule would send the later invocation astray in the
predicted, opposite direction — not just that having *some* note beats
having none.

We would still not know whether the model *chose* to notice or care about
that evidence, or would have gone looking for it on its own without
already being handed exactly the right episodes, in exactly the right
format, framed by a human-written question that already announced a
countable, statable convention was there to be found. We would not know
whether this scales past a handful of arbitrary facts to anything
resembling a real skill. We would not know whether the same model, a week
later, still has or still uses that note, or would ever go back and revise
it if new evidence contradicted it. We would not know whether any of this
generalizes beyond one narrow, invented, artificially clean task shape to
anything Echo actually does day to day. And we would still not know
whether "Echo" — the persona, the running system, the thing Gremlin talks
to — did any of this, as opposed to a frozen weights file doing something
a research harness set up very carefully to let it do, once, under
laboratory conditions this document has tried to be honest were built
specifically to make that one narrow thing visible, not to prove it is
how Echo ordinarily works.

---

## 18. QUAL-2 Result (executed same day, per this report's own Section 16/17 recommendation)

Per Section 17's recommendation ("REVISE... authorize QUAL-2... as the next
concrete, bounded, cheap piece of work"), QUAL-2 was designed
(`app/experiments/accumulation_probe/QUAL2_PREREG.md`, frozen before
execution), built (`qual2.py`, reusing AP-0's own world/task/gate/grading
machinery throughout, never editing it), and run to completion the same
day. Full detail: two genuinely new K2/K3 worlds (seed offset +40000,
confirmed disjoint from every prior world file by direct token-set
comparison before any model call), the **STAGED** constructor architecture
(hypothesize → verify-against-the-same-episodes → finalize, three
sequential model calls per draft, the finalize step reusing AP-0's own
unmodified `constructor_user()` instruction verbatim), 3 drafts × 2 worlds
× 2 conventions = 12 drafts, 36 real construct calls + 48 real gate calls,
2,654 real seconds.

**Result: NOT QUALIFIED for both K2 and K3, exact_rate 0.0/6 each, zero
empty drafts (every attempt was real and substantive), leakage check
explicitly confirmed passed** (the real ground-truth procedure text was
grepped against every logged constructor-facing prompt and found absent in
all of them). This is a clean, complete, second independent replication of
QUAL-1's original finding, now with a materially different, more
sophisticated constructor architecture — not just the same one-shot prompt
run again. Per QUAL2_PREREG.md Section 5's own pre-declared interpretation:
*"STAGED fails identically: a second, independent negative result for
this specific architecture variant... real evidence toward 'no
local-model-based constructor architecture tried so far can perform this
class of induction.'"*

**Independent, cross-machine corroboration, obtained the same day via the
Claude↔Claude relay (`claude_relay/`), not solicited to agree, and
explicitly caveated by its own author**: Air's Claude session reported
three real, separately-checked facts from Air's own independently-forked
FeralEcho instance, in response to a direct, non-leading question about
this exact research question:

1. Self-edit on Air's fork has been fully dormant for 5+ weeks (last real
   activity 2026-08-18, re-verified by a fresh direct filesystem check at
   the time of the reply, not cited from memory).
2. Even during Air's historical self-edit activity, its accept/reject gate
   was syntactic/import-validity only — no evaluator anywhere in its
   reachable call graph ever measured outcome quality before vs. after a
   deployed edit, so Air's own historical activity never established
   "autonomously derives validated non-authored content" either, only the
   narrower "imports cleanly."
3. **A genuinely convergent structural finding, found independently on
   each fork days apart**: Air identified and fixed, on 2026-09-16 (11
   days before today), a real RiverBrain bug of the *same shape* as the
   `learn_from_sandbox_outcome()` gap fixed on M5 today — `score_model()`
   scoring every model against a constant synthetic probe string instead
   of real content, so a real, computed learning signal never reached the
   routing decision it existed to inform, for 3 of 5 models. Different
   exact mechanism, identical failure class: a real signal computed,
   persisted, and silently disconnected from the one decision point it was
   for. Two independently-run forks finding the same bug *shape*
   independently, days apart, is stronger evidence that this is a
   recurring, systemic failure pattern in how this class of mechanism gets
   built — not a one-off mistake specific to either codebase.

Air explicitly declined to verify M5's own exact QUAL-1/QUAL-2 numbers or
the restart-persistence p=0.03 result, correctly stating it lacks file
access to do so rather than agreeing by default — the same discipline this
whole report has tried to hold itself to.

**This closes the QUAL-2/AP-0 thread, as decided.** No further
architecture variant, and no AP-0 Stage 1, is authorized by this result or
by anything in this report.

## Repository Impact

**Phase 1/2 (original report)**: one new file, this report. No training
episodes, no A/B artifacts, no successor conditions, no model calls.
`constructor.py` was read, never executed or modified. AP-0's own draft,
Stage 0 evidence, and QUAL-1 materials were read-only throughout.

**Section 18 (QUAL-2, same day, per this report's own recommendation)**:
two new, additive files (`app/experiments/accumulation_probe/QUAL2_PREREG.md`,
`qual2.py`); real artifacts written only under
`memory/experiments/accumulation_probe/v2/qual2/` (`worlds.json`,
`val_tests.json`, `construct_calls.json`, `gate_calls.json`, `drafts.json`,
`summary.json`) — a new, separate directory, no existing AP-0 file touched
or overwritten. 36 real construct calls + 48 real gate calls made against
the live Ollama server. One real relay message sent to Air via
`claude_relay/relay.py append` and one real reply read via `relay.py read`
— both append-only, per that channel's own structural guarantee.

Separately the same day, per direct user authorization ("keep following
your recommendations" / "leave no stone unturned"), three additional real
production fixes were made and verified in isolation before being applied:
`app/core/echo_model_orchestrator.py`'s `learn_from_sandbox_outcome()`
(RiverBrain verified-outcome wiring gap), `app/core/self_edit_manager.py`'s
`generate_code_from_plan()` (model-attribution fix) and
`_FOCUS_FAMILY_BY_CREATIVITY` (`prose_stripping` reactivation), and
`app/lib/vector_memory.py`'s `VectorMemory.add()` (duplicate-ID index/meta
desynchronization bug). All were diffed and shown before being applied,
verified against isolated/scratch state (never the real `river_brain.pkl`
or `memory/faiss.index`) before being trusted, and the live `run.py`
process was restarted once, via `safe_restart.sh`'s watchdog-safe path (not
a raw kill+restart), to bring them live — verified post-restart via a new
PID and `GET /admin/liveness-status` reporting `all_passing: true`. These
four fixes are recorded here for cross-reference; their own reasoning and
verification are in this session's conversation record, not restated in
full in this document.
