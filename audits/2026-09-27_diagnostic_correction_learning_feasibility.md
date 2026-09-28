# Feasibility Assessment: Can Echo Learn a Correction From Its Own Failure?

**Read-only. No model calls, no code changes, no permanent learned rules, no new
experimental outcomes.** Everything below is grounded in direct reads of existing
artifacts in this repository — cited by path — not inherited from the mission prompt's
own framing.

---

## 1. Current ground truth — re-derived from primary artifacts

Three prior lines of work in this exact codebase bear directly on this question, and
none of them were assumed from memory — each was re-opened and checked:

- **`app/experiments/validated_experience_competence_transfer/` ("VECT")** and its
  independent self-falsification review
  (`audits/2026-09-24_codex_validated_experience_transfer_self_falsification.md`): a real
  procedure artifact P produced a genuine, measured advantage (P=10/10, G=6/10, Z=5/10 on
  a held-out panel) — **but P's text is investigator-authored** (`freeze_procedure.py`'s
  `PROCEDURE_TEXT` is a literal string Claude wrote; the script's only substantive check
  is that cited episode IDs exist in the log, never an algorithmic derivation from the
  data). Also confirmed: **the original "unseen instances" claim was too strong** — TRAIN
  and the original held-out set shared all 4 underlying code bodies (a 4-entry fixed
  generator bank, guaranteed to recur by pigeonhole across 8 draws). This is the exact
  "duplicated code bodies" mistake Section 6 of this mission warns not to repeat.
- **`app/experiments/restart_persistence_transfer/`**
  (`audits/2026-09-27_restart_persistence_of_acquired_competence.md`): fixed the code-body
  duplication problem (4 genuinely new snippets, verified disjoint via
  `new_heldout_tasks.py::_verify_disjoint_from_vect()`, an in-process monkeypatch of the
  generator's bank rather than an on-disk edit) and demonstrated P surviving a genuine OS
  process restart (distinct PIDs, distinct `id(sys.modules)`) with a measured, mechanistically-traced
  advantage (9/10 vs 4/10) on the new content. **This is real, rigorous restart-persistence
  evidence — but it persists the same investigator-authored artifact**, and explicitly did
  not attempt to close the acquisition-provenance gap (its own §10 names exactly this as
  the next step, matching this new mission almost verbatim).
- **`app/experiments/first_learning_loop/lesson_mining.py`**: a real, mechanical (non-LLM)
  extraction of historical `NameError` failure→retry-success patterns from
  `memory/echo_watchdog.log` — genuinely automated, but its output "lesson" is a **fixed,
  investigator-authored sentence template**, filled with mined facts (an undefined name,
  an occurrence count), not a model-generated inference. Its own recorded transfer test
  produced a byte-identical control/experience code pair — no measurable advantage in that
  instance.
- **`app/experiments/architecture_a_hot_stove_proof/`**: a real null result — 6 control vs
  6 experience trials, 5/6 retry-success in *both* conditions, on production's own
  self-edit sandbox/importability path, with a failure-derived diagnostic injected. No
  observed advantage.

**The single decisive fact this feasibility assessment rests on**: across every one of
these prior experiments, in every case where a real, measured, causally-traced advantage
was found, **the candidate correction/procedure was authored by a human or Claude, not
derived by Echo (or any model, in an equivalent role) from its own diagnostic evidence.**
Gate G3, below, has never been attempted anywhere in this codebase.

**Diagnostic infrastructure, re-derived directly, not assumed:**
- `app/experiments/accumulation_probe/oracle_runner.py::grade()` (used by
  `strategy_characterization` and `persistent_routing`) returns `output_tail`/`error_tail`
  — the real grader's own `FAIL <args> <actual> <expected>` line, or a real exception
  tail on crash. Genuine, minimally-interpreted consequence evidence.
- `app/experiments/minimal_procedure_transfer/sandbox.py::format_failure_feedback()`
  (used by VECT's own TRAIN-phase retries) is the closer analog to what this mission calls
  "raw consequence evidence": for a wrong-output failure, it reports exactly
  `"For input {input}, your function returned {got!r}, but the correct output is {expected!r}."`
  — real values, no interpretation, no naming of the underlying mistake.
- `app/core/persistent_routing/selector.py::extract_sanitized_outcome()` explicitly
  discards everything except the boolean `passed` — confirmed directly, unchanged, and
  named correctly in this mission's own framing as the architecture *not* to change yet.
- **Nothing in this codebase currently asks a model to look at its own real diagnostic
  evidence and produce a candidate rule.** This is the one genuinely missing piece, not a
  missing family of pieces.

---

## 2. The exact target claim, restated precisely

Per Section 2: this experiment must **not** be satisfied by diagnostic text existing,
Claude authoring a correction, a better prompt improving performance, or RAG retrieving a
previously-authored rule. The claim requires, in one causal chain: Echo (or an equivalent
model acting as "the learner," never the investigator) produces a failing attempt →
independently generated diagnostic evidence from *that specific attempt's* real
consequence → the learner itself (not the investigator) derives a candidate
correction/generalization from that evidence → the candidate is independently validated
(not assumed correct) → only validated content is retained, with full provenance → the
retained artifact survives a genuine restart boundary → on a later, genuinely unseen case,
the learner is not told which stored correction to use → held-out performance improves
because of the retained artifact → removing/substituting that artifact removes the
advantage.

---

## 3. Gate-by-gate assessment (G0–G10)

| Gate | Status in this codebase | Evidence |
|---|---|---|
| **G0 — Action without the lesson** | **Trivially feasible, already the norm.** | Every K2/K3/`extract_code`-family task generator in this codebase produces fresh instances with no answer leaked into the prompt. |
| **G1 — Independent consequence** | **Already exists, reusable unmodified.** | `oracle_runner.grade()` and `sandbox.run_candidate()` are both real, sandboxed, already-qualified evaluators. |
| **G2 — Diagnostic evidence** | **Already exists, reusable unmodified.** | `output_tail`/`error_tail` and `format_failure_feedback()`, both genuine per-attempt consequence text, both already minimally-interpreted (Section 4 below). |
| **G3 — Candidate inference by the learner itself** | **The one genuine gap. Never attempted.** | Every prior "P" in this codebase (VECT, restart-persistence) is investigator-authored; `lesson_mining.py`'s automated extraction still ends in a fixed authored template. No code path anywhere asks a model to generate a candidate rule from its own real failure evidence. |
| **G4 — Independent validation of the candidate** | **Design pattern exists, reusable with adaptation.** | VECT's P/G/Z arm structure and `sandbox.run_candidate()` are directly reusable for testing a candidate (whatever G3 produces) against fresh instances — the mechanism is proven; only the *source* of the tested text (model-derived vs. investigator-authored) would change. |
| **G5 — Retention only if validated** | **Directly reusable.** | `persistent_routing/selector.py`'s content-hashed, provenance-logged `update()`/`save()` pattern and `freeze_procedure.py`'s hash-then-freeze convention are both real, proven templates — repointed at a candidate's *validation outcome* rather than an unconditional freeze. |
| **G6 — Restart persistence** | **Demonstrated, directly reusable.** | `restart_persistence_transfer`'s genuine-OS-process, distinct-PID, hash-verified-recovery design is a proven, real template for exactly this gate. |
| **G7 — Later autonomous use, not told which correction** | **Trivial for one candidate; a real open design question for more than one.** | With exactly one retained candidate (the minimal first experiment), "use" reduces to "is it present or absent" — no selection problem. Selecting among multiple retained candidates is real future complexity, correctly out of scope per Section 17/G10. |
| **G8 — Held-out improvement, causally attributable to state** | **Design pattern exists.** | VECT's and restart-persistence's own contamination checklists (18+ named channels, each with a stated control) are directly reusable, not to be re-derived from scratch. |
| **G9 — Causal removal/substitution** | **A stronger template exists than either VECT precedent used.** | `persistent_routing/replay.py`'s TRUE/SHAM-reversed, same-starting-state substitution (independently verified 10/10 before trust) is a *more rigorous* causal design than restart-persistence's own R+/R- between-groups comparison — this experiment should borrow `replay.py`'s shape (same acquired state, artifact swapped/removed) rather than repeat the weaker two-independent-conditions pattern. |
| **G10 — Accumulation** | **Correctly out of scope**, per the mission's own instruction. Not assessed further. |

**The table's own shape is the finding**: seven of nine testable gates (G0, G1, G2, G4,
G5, G6, G9) already have a directly reusable, previously-validated template in this
codebase. **G3 is the only gate with zero prior art anywhere.** This changes what
"feasibility" means here — the risk is not "do we have the infrastructure," it's "does
the one missing generation step actually produce anything worth putting that
infrastructure around."

---

## 4. What information current sanitization destroys, precisely

Direct comparison of `output_tail`'s FAIL line against `extract_sanitized_outcome()`'s
output: the former carries the *specific wrong value*, the *specific expected value*, and
the *specific input* that triggered the mismatch; the latter reduces all of that to one
bit. `format_failure_feedback()` is the correct model for what G3's input should look
like: **real values, zero naming of the underlying mistake** ("your function returned X,
expected Y" — never "you forgot to extract only the name field"). This satisfies Section
7's own instruction precisely: it is the least-interpreted diagnostic evidence that still
reflects the actual consequence. **Using the forensic-mining pass's own already-written
prose characterization of the T2/T5 bug ("returns too much of the input structure") as
input to Echo would leak the answer** — Section 6's own explicit prohibition. The correct
input is the raw `(args, actual, expected)` triple alone, exactly as `output_tail`/
`format_failure_feedback()` already produce it, never the investigator's own diagnosis of
it.

---

## 5. Operationalizing "autonomous candidate inference" (Section 8)

Adopting the mission's own five-part definition directly, with one addition grounded in
what this codebase's evidence shows is actually at risk: a sixth check —

6. **The candidate must not be recoverable by simple string operations on the
   diagnostic text or the task description alone** (e.g., "return `expected`" or a
   verbatim echo of the FAIL line is not an inference). This closes a real, concrete
   failure mode this codebase has already exhibited once: `lesson_mining.py`'s "lesson"
   is effectively a template fill from mined facts, not a generalization — a mechanical
   check (e.g., normalized-string containment/edit-distance between the candidate and the
   diagnostic text) should flag and exclude degenerate candidates of that shape before
   they ever reach validation, per this codebase's own precedent of catching exactly this
   pattern once already.

---

## 6. Proposed experimental arms

**A — frozen/no-learning control**: baseline pass rate with no persistent artifact
available, ever. **B — scalar-feedback control**: the exact current
`extract_sanitized_outcome()`-shaped signal (pass/fail only) available across a retry, no
diagnostic text. **C — diagnostic-experience condition**: the learner receives real
`output_tail`/`format_failure_feedback()`-shaped evidence from its *own* failed attempt
and is asked, in a separate, logged call, to propose a candidate correction — the
investigator never authors or edits that candidate's content.

**D — investigator-authored correction, as a ceiling, not a fourth arm to add by
default**: given the mission's own explicit "do not add Arm D automatically," and given
that VECT's own P *already is* exactly this ceiling (a real, already-measured 10/10
result under investigator authorship, on the same general task family) — **Arm D is not
scientifically necessary to re-run**; VECT's existing result already serves as the
ceiling reference, re-derivable by citation rather than by re-generating it. Recommend
omitting a fresh Arm D.

---

## 7. Candidate-generation provenance design

Per Section 5's explicit requirement, every candidate record should carry: the exact
failed attempt (full prompt + raw response + code_hash); the exact diagnostic evidence
shown to the learner (verbatim `output_tail`/feedback string); the exact prompt/context
given to the learner when asked to propose a candidate (so no accidental extra context
leaked in); the candidate's own raw output verbatim; a timestamp; content hashes of both
the evidence and the candidate; the parent episode's ID; and an explicit boolean field
`human_or_claude_authored_content: false` by construction (never set retroactively) —
mirroring `persistent_routing/provenance.py`'s existing E/U/D record shape, extended with
these fields rather than inventing a new logging convention. **A bad or empty candidate is
retained in the log exactly as a good one would be** — this matches
`seam_engine.py`'s and `dissent_log`'s own established "log the negative case too"
discipline already present elsewhere in this codebase.

---

## 8. Validation-before-retention design

**Candidate → fresh validation opportunity → retain/reject/uncertain**, sized the same
way `strategy_characterization`'s own Q4 split-sample correction was sized: a small,
disclosed-as-rough number of fresh instances (not the training instance, not the
contaminated 216 K2 outputs per Section 6's explicit prohibition) — recommend n≥5 fresh,
freshly-drawn instances of the *same specific failure-prone task template* (e.g., K2's
T2/T5-shaped tasks specifically, since those are where a real, replicated bug pattern is
already known to exist from the forensic pass, used here only to *pick the task family to
study*, never to hand the answer to the learner). **Support** = candidate materially
raises pass rate on those fresh instances versus Arm B's own baseline on the same
instances; **falsification** = it does not, or moves it the wrong direction (a real,
useful negative — "my hypothesis was wrong" is itself a retained, logged outcome, not
discarded). Track a confidence value (e.g., a Beta-parameterized running estimate,
mirroring `persistent_routing/selector.py`'s own running-mean update shape) rather than a
binary flag, so contradictory later evidence can revise confidence downward rather than
requiring a hard delete.

---

## 9. Novelty / held-out-transfer design (Levels 1–3)

Level 1 (repair) and Level 2 (near transfer) are cheap, direct reuses of the fresh
K2-world-generation machinery `strategy_characterization`/`persistent_routing` already
use (fresh worlds, same task template). **Level 3 (structural transfer) must not repeat
VECT's own already-identified mistake** — novelty must be defined mechanically, *before*
generation, the same way `restart_persistence_transfer/new_heldout_tasks.py`'s
`_verify_disjoint_from_vect()` already does it: a programmatic check (not eyeballing) that
the held-out task's underlying content (not just its surface prose) is disjoint from
every instance the candidate was validated against. For K2-family tasks this is more
tractable than VECT's fixed 4-snippet code bank was — K2's worlds are freshly, randomly
generated per seed offset (confirmed disjoint via direct token-overlap check, the exact
technique already used to freeze `strategy_characterization`'s own `SEED_OFFSET=120000`),
so genuine novel-content held-out instances are cheap to produce here, unlike VECT's
fixed-bank constraint.

---

## 10. Baseline control

Directly reusable: `restart_persistence_transfer`'s own R+/R- design (a fresh process
with the artifact available vs. an otherwise-identical fresh process from which it is
withheld, both receiving the identical task and prompt shape otherwise) is already a
proven baseline-control template — apply it here with the candidate in place of P.

---

## 11. Restart boundary

Directly reusable: `restart_persistence_transfer`'s own process-boundary evidence
standard (distinct PIDs, distinct `id(sys.modules)`, file-age-gap evidence for the
originating process) is already a validated, sufficient bar for this claim — no new
mechanism needed.

---

## 12. Causal removal/substitution intervention

**Recommend `persistent_routing/replay.py`'s design over restart-persistence's own R+/R-
shape for this specific gate.** R+/R- is a between-groups comparison (two separately-run
conditions); it does not prove the *same* acquired state, with only the artifact swapped,
produces the difference — a real, if minor, gap the restart-persistence report itself did
not need to close (it wasn't testing a state-substitution claim, only persistence).
`replay.py`'s TRUE/SHAM mechanism — same starting checkpoint, only the outcome/artifact
substituted, independently verified before trust — is exactly the intervention Section 13
asks for, and it already exists, proven, in this exact codebase.

---

## 13. Non-learning doppelgängers and controls

| Doppelgänger | Control/evidence needed |
|---|---|
| Base-model competence alone explains the held-out result | Compare against Arm A/B's own baseline on the identical fresh instances — already part of the design. |
| Prompt/context carryover | Each generation call is a fresh, single-turn request, matching every prior experiment's own convention (`ollama_client.py`'s stateless request shape) — verified structurally, not assumed. |
| Copying diagnostic text as the "candidate" | Section 5's sixth check (string-containment/edit-distance against the diagnostic) — new, proposed above. |
| Investigator/Claude-authored lesson | Provenance record's `human_or_claude_authored_content` field, set only by construction, checked before any candidate is used. |
| Contaminated validation tasks (VECT's own historical mistake) | Mechanical disjointness check, per Section 9 above, before any validation instance is trusted. |
| Duplicated underlying code/world content | Same disjointness check, applied to K2 world realizations, not just surface task text. |
| Memorization of the failed instance itself | Held-out instances must be genuinely different task/world draws, never the training instance re-shown. |
| RAG retrieval mistaken for acquisition | This design has no retrieval step to conflate with acquisition — the candidate is read from one hash-verified file, not searched for among many; flagged as a real risk only if a future, richer version adds multi-candidate storage (G7's noted complexity). |
| Grader/expected-answer leakage | `oracle_runner.grade()`/`sandbox.run_candidate()` both take no arm/condition parameter and never place `expected` in a generation prompt — already independently confirmed for the reused evaluators. |
| Stochastic generation | Multiple fresh validation instances (Section 8), not a single trial, before retention. |
| Hand-selection of favorable candidates | Every candidate logged regardless of quality (Section 7); no filtering before logging. |
| Post-hoc interpretation | The candidate's own raw text is the artifact — no investigator rewording permitted after generation, per the mission's own explicit rule. |
| Hidden state surviving a "fake" restart | `restart_persistence_transfer`'s distinct-PID/`id(sys.modules)` evidence standard, reused unmodified. |
| Selecting only failures whose fix is obvious from the diagnostic alone | A real, hard-to-fully-eliminate risk — mitigated, not solved, by using the *raw* value-only diagnostic (Section 4) rather than a richer error message, and by requiring the candidate to pass Section 5's inference-vs-echo check. |

---

## 14. Pre-registered interpretation matrix (D0–D5)

Adopted directly as specified in the mission (Section 16) — no changes proposed. One
addition: **a candidate that fails Section 5's "not recoverable by string operations"
check should be excluded from the D0–D5 classification entirely** (treated as "no genuine
candidate was produced this trial," a distinct, honestly-reported outcome, not folded into
D0 — D0 specifically means "a genuine candidate existed but performed no better than
scalar feedback," which is a different, more informative finding than "no genuine
candidate was ever produced").

---

## 15. Feasibility using current components

**No missing component makes this experiment structurally invalid.** Every gate except
G3 has a directly reusable, previously-validated template already in this codebase
(Section 3's table). G3 requires exactly one new piece: a generation call that presents
the learner with real, un-interpreted diagnostic evidence from its own failed attempt and
asks it to propose a candidate correction, logged with the provenance fields in Section 7
— a small, well-scoped addition, not an architectural rewrite.

## 16. Minimum missing machinery

One new module (by analogy to every prior experiment package in this codebase): a
`candidate_inference.py`-shaped file implementing the G3 prompt/call/logging step
described above, plus Section 5's mechanical degeneracy check. No change to
`extract_sanitized_outcome()`, `oracle_runner.py`, or any production Echo file is needed
or proposed.

## 17. Estimated cost of a future full experiment

Rough order of magnitude, following this research arc's own established cost-discipline
(explicit estimates before execution, per `strategy_characterization`'s own precedent):
~10-20 TRAIN/failure-inducing attempts (to generate real failures worth deriving
candidates from) + 1 candidate-inference call per genuine failure + Section 8's ~5+ fresh
validation instances per candidate + Section 9's ~10 structurally-novel held-out instances
+ restart-boundary and substitution re-runs of the held-out panel (2-3x that panel size,
matching `restart_persistence_transfer`'s own shape) — very roughly 60-120 real model
calls for a first, appropriately-scoped pass, an order of magnitude cheaper than
`strategy_characterization`'s own 216-call Stage 1, since this design has fewer arms and
does not need a full factorial task/strategy/world/repeat grid.

## 18. Is a full experiment scientifically justified now?

**Not yet, and not for a large-design reason — for the same small-design reason this
research arc has repeatedly and correctly applied before committing to an expensive
frozen protocol** (`strategy_characterization`'s own Phase-0 smoke test before its
216-call Stage 1; QUAL-2's own deliberately reduced scope before a larger run). **G3 has
never been empirically observed even once in this codebase.** Freezing the full G4–G9
protocol now would mean designing validation, retention, restart, and substitution
machinery around a generation step whose actual output shape — genuinely inferential vs.
degenerate-echo vs. vacuous — is completely unknown. Section 9's own "mechanical or
blinded method for determining whether a candidate is specific enough to test" cannot be
properly calibrated without having seen at least a handful of real candidate outputs
first.

**Recommend a small, separately-authorizable G3-only feasibility probe before freezing
the full protocol**: a handful of real failures (reusing K2's T2/T5-shaped tasks, since a
real, replicated bug family is already known to exist there from the forensic-mining
pass, used only to select *which task family to probe*, never to hand the learner the
diagnosis) → real diagnostic evidence shown → the learner asked to propose a candidate →
Section 5's degeneracy check applied → results reported plainly, with zero validation,
retention, or restart machinery built around them yet. This is cheap (single-digit real
calls), directly answers the one open empirical question, and matches this whole
project's own repeated practice of gating an expensive design behind a cheap
feasibility check.

## 19. Single strongest reason this design could still fool us

**A "genuinely inferential" candidate could still be produced by the model
reconstructing the fix from ordinary programming knowledge triggered by the task
description alone, not from the specific diagnostic evidence shown** — exactly the
doppelgänger the VECT self-falsification review named for its own P ("the lesson could be
constructed from the task schema and ordinary programming knowledge... matching clauses
to real experience does not establish that the experience was necessary"). **The
proposed design does not yet fully close this gap**, and should not claim to: the
strongest available mitigation, not a complete one, is an experience-necessity
counterfactual — regenerate the same task *without* showing the failure/diagnostic at all
(a fresh, cold attempt) and check whether the model spontaneously proposes the same
"candidate" unprompted. If it does, the diagnostic evidence was not load-bearing for that
specific inference, and the result should be reported as such, not smoothed over.

---

## 20. Recommendation

**NOT READY — INVESTIGATE/REPAIR FIRST.**

Not because of missing infrastructure — Section 3's table shows seven of nine testable
gates already have directly reusable, validated templates in this codebase. The one real
gap (G3) is narrow and specific: no code path anywhere has ever asked a model to derive a
candidate correction from its own real failure evidence, so nothing is known yet about
what that step actually produces. The repair needed is small and cheap: a standalone G3
feasibility probe (Section 18), not a broad architectural investigation, before any full
protocol is frozen.

---

## Stop-condition sentence, addressed directly

**"This design can distinguish Echo learning a correction from its own diagnostic
experience from Echo merely being shown enough information to solve the next task."**

**Partially defensible, not fully, and the gap is named precisely, not glossed over.**
The *infrastructure* half of that sentence is defensible now: the reused
validation/retention/restart/substitution machinery (Sections 6–12) is adequate,
previously proven, and correctly designed to attribute any observed advantage to the
retained artifact rather than to prompt, history, or process-boundary artifacts. The
*candidate-quality* half is not yet defensible, for the concrete reason in Section 19: a
genuinely novel-sounding candidate could still be reconstructed from ordinary task-level
knowledge rather than from the specific diagnostic evidence shown, and this design does
not yet include a component that would catch that specific failure mode with confidence —
only a partial mitigation (the cold-regeneration counterfactual) is proposed, not yet
built or tested. Until the small G3 feasibility probe in Section 18 is run and at least
gives a first real look at what a candidate looks like, freezing the full protocol would
mean committing expensive, carefully-designed machinery around a step whose basic
behavior remains completely unobserved.

Returned for adversarial review. No experiment executed, no code modified, no production
Echo changed, no permanent learned rule created.
