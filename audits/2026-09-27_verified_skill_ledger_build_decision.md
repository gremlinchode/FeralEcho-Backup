# Verified Skill Ledger: Build Decision

**Status: decision document. No code written yet, no production changes.** Written under
explicit time pressure (Claude availability uncertain past ~Oct 1, Codex currently
unavailable) — this changes the calculus deliberately, per the governing mission's own
instruction, away from another pre-implementation probe and toward a real go/no-go call.

**One concrete, evidence-grounded revision was found while re-inspecting the architecture
against real data (§0) — stated precisely, not hidden, then built into the plan below.**
This is why the decision is REVISE THEN BUILD, not a clean BUILD — the revision is small,
specific, and immediately actionable, not a new open research question.

---

## 0. The single most important thing this re-inspection found

Re-reading `audits/2026-09-27_feralecho_learning_architecture_deep_dive.md`'s own schema
(`skill_ledger/<feature_key>.json` storing a single `code` field) against **real,
already-collected data** (zero new model calls) surfaced a concrete defect: **for K2-family
tasks, the "correct" code must read a world-specific convention (`procedure_text`) at
generation time — a single frozen `code` string cannot generalize across worlds by
construction**, because the exact tag names differ every time. Checked directly: all 4
real historical STEPWISE passes on `K2.T5` each contain a *different*, world-specific
`tag_priority` literal (`{'medaj':1,...}` for world 1, `{'fevar':1,...}` for world 2) —
proving the model already re-derives this per instance; a stored frozen function would
simply be the wrong world's answer on any new instance.

**The fix is small and immediately specifiable, not a new research question**: a "skill"
must be represented as a **verified code-transformation pattern** (in the automated
program-repair sense — a template plus its applicability condition), not a literal
function. Concretely, for this example: *"wherever a `tag_priority` dict is built via
ascending `enumerate()` over a listed priority order, the later sort key must reference
`tag_priority[tag]` directly, never negated"* — a rule that is instance-independent (it
never mentions a specific tag name) while the *dict itself* is still freshly derived per
instance, exactly as the model already does reliably. **This is one schema field change
(`skill = {applicability_pattern, transformation, ...}` instead of `skill = {code}`), not
an architecture rewrite** — named now, before any code is written, so the first
implementation gets it right the first time.

---

## 1. What is a skill, concretely

**A skill is a verified code-transformation pattern**: a pre-condition (a mechanical,
AST-checkable pattern describing *when* the transformation applies — e.g., "a sort key
references a dict built via ascending enumerate over a listed order, with no negation on
that term") plus a transformation (the specific rewrite that fixes it). It is **not**
natural language, not a frozen function, not a general belief. It is produced by
search-and-verify (candidates generated, oracle-graded, the *difference* between a
passing and failing candidate on the same feature key mechanically diffed into a
transformation pattern), never by asking the model to explain itself.

## 2. Complete learning loop, traced through one real, mechanically realistic example

`task failure` (K2.T5, DIRECT, tag-priority-direction bug, already real and on disk) →
`variation` (resample the SAME task N=4 times, mixing strategies/temperatures — already
proven cheap: real historical data shows this exact resampling already produces a passing
candidate ~33% of the time for this family, **zero new calls needed to prove this step
works**, see §0's sibling check below) → `execution+verification` (`oracle_runner.grade()`,
already proven infrastructure) → `skill qualification` (diff the passing candidate against
a matched failing one on the *same feature key* to extract the transformation pattern,
confirm the pattern doesn't reference any instance-specific literal) → `ledger write`
(hash-then-freeze, `persistent_routing`'s own proven convention) → `process termination` →
`restart` (`restart_persistence_transfer`'s own proven distinct-PID design, reused
verbatim) → `fresh related task` (a genuinely new world, same feature key, verified
disjoint via the token-overlap check already proven three times in this codebase) →
`skill retrieval` (lookup by feature key) → `skill consumption` (apply the transformation
to the freshly-generated candidate before grading, or bias the generation prompt with the
pattern) → `behavioral advantage` (measured pass-rate delta vs. a no-skill control) →
`counterfactual removal` (`replay.py`'s own TRUE/SHAM substitution design, generalized
from selector state to skill-file presence/absence) → `advantage disappears` (the actual
falsification test). **Skill A → Skill B**: if a second, independently-discovered skill
(e.g., a `K2.T2` field-projection fix) can be looked up and applied *within the same
generation attempt* as Skill A (both patterns matching different parts of the same
candidate), that is the concrete, checkable version of "A+B enable something neither
alone would" — composability at the level of independently-applicable patches, not a
vague synergy claim.

## 3. Why this is not "just RAG with executable snippets"

**Honestly conceded**: at Stage 2 (one skill, one reuse), this *is* a form of verified
procedural memory — retrieval of a validated artifact. **What would make it more than
that**: (a) the held-out generalization gate (§2) — plain RAG never checks whether a
retrieved snippet is *provably* keyed correctly, it just returns nearest-neighbor matches;
(b) the causal-substitution test (§2's last step) — RAG systems essentially never verify
that removing the retrieved content actually removes the benefit; (c) §8's accumulation
mechanism — a pattern that composes with other patterns inside one generation attempt is
a genuinely different causal structure than independently retrieving two separate
documents. **This is won by behavior, not terminology**: if Stage 5/6 (below) fail, this
*is* just RAG, and should be called that plainly, not defended semantically.

## 4. Why this is not brute-force search

**Acquisition cost** (finding the pattern the first time) vs. **post-acquisition
capability** (using it later) are measured separately, explicitly: the accumulation
metric (§9) is *reduction in search cost* — specifically, the number of new candidates
that must be generated for a fresh instance of an already-solved feature key **should
drop toward 1** (apply the known pattern directly) from whatever N was needed at
discovery time. If it never drops, this is brute-force search wearing a ledger, and the
architecture has failed on its own terms — a real, falsifiable claim, not asserted away.

## 5. Why this is not prompt engineering

**Counterfactual, specified precisely**: same model, same task, same reasonable base
prompt, same generation budget — with the skill pattern available for lookup vs. with the
skill file removed (not "never built," *removed after being built*, mirroring `replay.py`'s
own SHAM design). A held-out pass-rate difference attributable to the file's
presence/absence, not to a better-written prompt, is the actual, already-proven-feasible
test (`restart_persistence_transfer` already ran exactly this shape of comparison, R+
vs. R-, successfully).

## 6. Structural comparison to RiverBrain

RiverBrain: experience → verified outcome → bounded numeric state update → persistence
→ explicit consumer (fitness gate) → behavioral consequence. **Verified Skill Ledger**:
experience → verified outcome **→ a diffed, mechanically-extracted transformation
pattern (open-ended in content, but bounded in *shape*: precondition + rewrite, always)**
→ persistence (identical hash-then-freeze convention) → explicit consumer (a lookup at
generation time) → behavioral consequence. **Shared principle**: grounded update (never
model self-report), explicit pre-wired consumer, bounded representation *shape* even
though not bounded *content* the way a running mean is. **Where VSL adds real, new
risk RiverBrain never carried**: RiverBrain's state can never be "wrong" in a way that
actively breaks something — a bad running mean just biases a choice; a bad
transformation pattern, mis-applied, could actively **introduce** a new bug into
otherwise-correct code. This is a genuinely new risk class, and the mitigation is
explicit: a skill is applied only as a *candidate* that itself gets re-graded by the
oracle before being accepted, never applied blind.

## 7. Every persistent mutable component, with a specified consumer (Part VII's own rule)

| State | Producer | Update rule | Storage | Consumer | Behavioral consequence |
|---|---|---|---|---|---|
| Skill file | search-and-verify + diff extraction | write-once, hash-frozen | `skill_ledger/<feature_key>.json` | generation-time lookup | pattern applied to a fresh candidate before grading |
| Skill stats | every reuse attempt | RiverBrain's own incremental-mean formula, reused verbatim | `skill_stats.pkl` | staleness check (§ Forgetting) | flags a skill for re-validation if its recent success rate drops |
| Provenance log | every ledger write/consumption | append-only | `skill_ledger/provenance.jsonl` | human/audit review, future forensic mining | none automatic — deliberately observational, matching this project's own Global Workspace precedent |

No component above lacks a named consumer; none is added speculatively.

## 8. Accumulation — the specified metric and the two thresholds

**Primary metric**: mean candidates-needed-to-reach-a-pass for fresh instances of an
already-solved feature key, before vs. after a skill exists for that key. **One learned
skill** = a single validated ledger entry with a passing held-out test. **Accumulated
competence growth** = this metric trending down across multiple independently-acquired
skills over real time, *and* at least one observed case of two skills composing within a
single generation attempt (§2's Skill A + Skill B check). Both are directly measurable
with infrastructure already specified — no new measurement invention required.

## 9. Must weights eventually change?

**Phase I (this build): no.** Search-and-verify + a transformation-pattern ledger
requires zero weight access — the frozen model only needs to *vary*, never to *correctly
explain*, sidestepping the one capability (verbal causal inference) this arc has
repeatedly, directly falsified. **Phase II (later, conditional): plausible, not needed
now.** If Phase I's skill library grows to enough validated (precondition, rewrite) pairs
that they could constitute real supervised fine-tuning data for a small local model, that
becomes a legitimate, evidence-justified next step — but only after Phase I proves the
patterns themselves are real and reusable, not before. Committing to Phase II now would
mean building genuinely new (untested-in-this-codebase) training/rollback infrastructure
before confirming Phase I's simpler mechanism produces anything worth consolidating.

## 10. Hardware reality

Everything in Phase I runs on the M5 today: local Ollama inference (already running),
flat JSON/pickle files (negligible storage), the existing kernel-sandboxed oracle (already
proven cost — seconds per grade). Verification cost scales with the number of candidates
sampled per failure (4–8, matching this session's own established repeat-count
convention) — no new compute category. **No component of Phase I depends on Claude
existing after this build session** — the resulting harness is plain Python, runnable via
`python3 -B -m app.experiments.skill_ledger.run`, exactly like every other experiment
package this session built.

## 11. KEEP / MODIFY / RETIRE

| Component | Verdict | Why |
|---|---|---|
| `oracle_runner.grade()` / `sandbox.run_candidate()` | **KEEP, verbatim** | Proven across 6+ experiments; the verifier this whole architecture depends on. |
| `replay.py` (TRUE/SHAM substitution) | **KEEP, generalize** | Reuse its exact design for skill-file presence/absence substitution. |
| `restart_persistence_transfer`'s process-boundary design | **KEEP, verbatim** | Directly reusable for Stage 3. |
| RiverBrain `model_task_stats` | **KEEP, unmodified** | The one demonstrated acquired-competence mechanism in the project; VSL's skill-stats reuses its update math, never its buckets. |
| FAISS / vector memory | **KEEP, out of scope** | Already correctly scoped to contextual retrieval, never claimed as learning; no change needed or proposed. |
| Council / routing (production) | **KEEP, unmodified** | Not touched by this build. |
| `persistent_routing` (this session's experiment) | **RETIRE as a load-bearing mechanism, KEEP as documented negative evidence** | Its own null result is exactly what motivated this redesign — do not resurrect its selector shape for VSL's consumer (§6 already explains why: it's a SELECTION-only mechanism with no VARIATION step). |
| `self_edit_manager.py`'s fitness gate | **MODIFY, additively** | A skill-ledger lookup can feed a candidate into the *existing* gate; the gate itself is untouched. |
| `self_model_claims.py` / drift detectors | **KEEP, unmodified** | Orthogonal monitoring machinery, not part of this loop. |
| `first_learning_loop`'s mining half | **RESEARCH-ONLY, reusable input** | Its mechanically-verified extraction (not its fixed template) is a legitimate future input to feature-key discovery — not built into Phase I. |
| G3 / belief-revision harnesses | **RETIRE as learning mechanisms, KEEP as diagnostic tools** | Already the prior synthesis's own STOP-list item; unchanged here. |
| `attempt_ledger_test` / `provenance_f2_verification` | **KEEP as verification patterns** | Their hash-diff and joinability-check techniques are directly reusable for VSL's own integrity tests. |

---

## 12. Implementation architecture

- **New package**: `app/experiments/skill_ledger/` (experimental status first, exactly
  matching every other package this session built).
  - `common.py` — reused `seed_for`/`write_json_new`/hash helpers, new disjoint namespace.
  - `tasks.py` — thin wrapper, re-imports `strategy_characterization.tasks` and
    `accumulation_probe` verbatim (no duplication).
  - `variation.py` — samples N candidates per failure (reuses the exact `OC2`/generation
    call shape already proven in `strategy_characterization`/`g3_micro_probe`).
  - `diff_extract.py` — AST-level diff between a passing and a matched failing candidate
    on the same feature key; produces a `{precondition, transformation}` record. **This
    is the one genuinely new piece of logic in the whole architecture** — everything else
    is reused.
  - `ledger.py` — `Skill` class: `load()`, `content_hash()`, `save()` (write-once,
    matching `Selector.save()`'s exact contract), `applies_to(candidate_ast)`,
    `apply(candidate_code)`.
  - `verifier.py` — thin wrapper around `oracle_runner.grade()`, unmodified underneath.
  - `harness.py` — the phased CLI (`build`, `acquire`, `restart-check`, `transfer-check`,
    `substitution-check`), mirroring `persistent_routing/harness.py`'s own multi-phase
    shape exactly.
  - `PROTOCOL.md` — frozen before Phase 2 of the implementation order below.
- **Schema** (revised per §0):
  ```json
  {
    "feature_key": "K2.T5.tag_priority_direction",
    "precondition_ast_pattern": "...",
    "transformation": "...",
    "provenance": {"source_failure_id": "...", "candidate_hash": "...", "oracle_verdict": "PASS",
                    "held_out_verdict": null, "created_at": "..."},
    "content_hash": "..."
  }
  ```
  `held_out_verdict` starts `null` and is filled only after Stage 4 passes — a skill is
  **not** eligible for consumption until this field is set, enforced in code, not by
  convention.
- **Tests**: `verify_skill_ledger.py`, matching `verify_replay.py`/`verify_seam_engine.py`'s
  own synthetic-discrimination-case convention, written *before* any real skill is
  trusted.

## 13. Minimum viable learning kernel — named exactly

**Must implement now**: `variation.py` (N=4 resampling, reusing proven generation code),
`diff_extract.py` (the one new component), `ledger.py`'s write-once/load/apply, the
restart-boundary harness shape (copied near-verbatim from
`restart_persistence_transfer`), and the substitution check (copied near-verbatim from
`replay.py`'s design, applied to skill-file presence). **Can wait**: multi-skill
composition (§2's Skill A+B check — real, but only meaningful once ≥2 skills exist),
skill staleness/forgetting (§7's stats-based flag — only matters after real reuse volume
accumulates), any UI/dashboard surfacing.

## 14. First end-to-end demonstration — phases A–F, as specified by the mission, unchanged

Adopted directly: Phase A (baseline pass rate on K2.T5 fresh worlds, no skill) → Phase B
(search-and-verify produces one real skill, diff-extracted, `held_out_verdict: null`) →
Phase C (real OS-process restart, `restart_persistence_transfer`'s exact evidence
standard) → Phase D (fresh, disjoint K2.T5 worlds; skill retrieved and applied; measure
pass rate, candidates-needed, latency) → Phase E (substitution: identical run with the
skill file removed, per `replay.py`'s own design) → Phase F (only if A–E all pass:
introduce a second feature key, e.g. `K2.T2`'s field-projection bug, and check whether
solving it is any cheaper/different given Skill A already exists — the real accumulation
check, not assumed).

## 15. Final red-team pass

- **Retrieval masquerading as learning**: addressed in §3 — conceded honestly as the
  Stage-2 starting point; the held-out and substitution gates are what would distinguish
  it, and neither has ever successfully fired in this codebase before. **This is the
  single largest testable-not-fatal risk carried into implementation.**
- **Instance memorization / false generalization**: directly mitigated by §0's own fix —
  a transformation pattern that never references an instance-specific literal is
  mechanically checkable (a real AST-level assertion, not a promise).
- **Verifier leakage, task leakage**: low risk, inherited from already-hardened oracle
  infrastructure; must be re-confirmed for this specific reuse, not assumed.
- **Hand-authored skill semantics / Claude secretly supplying the abstraction**: a real
  risk specific to *this build session* — since a Claude session is writing
  `diff_extract.py`, there's a real chance the diffing logic is tuned, even
  unconsciously, toward the exact three bug families already characterized this session.
  **Mitigation, stated plainly**: `diff_extract.py` must be a generic AST-diff, with no
  bug-family-specific logic anywhere in it — verified by testing it against a
  held-out bug family *not* used to design it, per its own test suite.
- **Compute inequality between skill-present and skill-absent conditions**: must be
  matched exactly (same candidate budget) in every comparison, mirroring VECT's own
  already-established discipline.
- **Poisoning / stale skills**: addressed by §7's stats-based staleness flag; not solved
  for Phase I in full (a real, disclosed, deferred risk, not a blocker for the MVK).

**Fatal-before-implementation vs. testable-during-implementation**: nothing found rises to
fatal. The held-out generalization gate never having fired before is the single most
serious concern, but it is *exactly* what Stage 4/Phase D is designed to test — deferring
implementation until that's separately proven would mean running yet another
pre-implementation probe, which the mission explicitly asks not to default into.

---

## 16. Decision

# REVISE THEN BUILD

**The revision** (§0, already fully specified, not open-ended): represent a skill as a
verified `{precondition, transformation}` pattern, never a frozen code string — required
because K2-family tasks embed instance-specific data in-prompt by design, so literal code
reuse is structurally impossible, a fact directly confirmed from already-collected data at
zero additional cost. **This is a schema correction, not a new research program** — fully
specified in §12, ready to implement immediately.

No fatal architectural flaw was found. The largest real risk (the held-out generalization
gate has never fired successfully in this codebase) is exactly what the Minimum Viable
Learning Kernel is built to test directly, not something requiring a separate probe first
— consistent with the mission's own explicit time-pressure instruction to move rigor into
the integrated build rather than defer it into another isolated pre-check.

---

## 17. Implementation order

**Checkpoint 0**: confirm working tree is clean/committed as-is; no changes to any
existing file. (Already satisfied — this document and its predecessors are new files
only.)

**Checkpoint 1** (§13's MVK, part 1): `app/experiments/skill_ledger/` package skeleton —
`common.py`, `tasks.py` (thin reuse wrappers), `ledger.py` (schema from §12, `Skill`
class). No search/diff logic yet. Runnable, testable in isolation.

**Checkpoint 2**: `variation.py` — N=4 resampling on one real, already-characterized
failure (K2.T5). Reuses the exact generation call shape from `g3_micro_probe`/
`strategy_characterization`. Verify against **already-collected data first** (§0's own
check) before spending any new calls — confirm the expected ~33% hit rate is what a
literal re-query would also produce.

**Checkpoint 3**: `diff_extract.py` — the one new component. Built and unit-tested
against synthetic, hand-constructed pass/fail code pairs *before* being pointed at real
data, matching `verify_replay.py`'s own precedent.

**Checkpoint 4**: Phase A+B of §14 — real baseline measurement, real skill acquisition,
`held_out_verdict: null`.

**Checkpoint 5**: Phase C+D — restart (reusing `restart_persistence_transfer`'s design
verbatim) + fresh, disjoint held-out worlds. **This is the actual go/no-go gate for the
whole architecture** — if the pattern doesn't transfer here, stop and report a clean
negative, exactly as `persistent_routing` did.

**Checkpoint 6**: Phase E (substitution, reusing `replay.py`'s design).

**Checkpoint 7** (only if 1–6 all pass): Phase F (second feature key, accumulation
check).

Each checkpoint is independently committable and leaves the repository fully runnable —
no checkpoint depends on a later one to be in a working state.

### Time-prioritized cut lines

- **If only 1 hour remains**: Checkpoint 1 only — the schema and package skeleton, fully
  documented, so a future session (Claude or otherwise) can pick up immediately with zero
  reconstruction cost.
- **If only 4 hours remain**: Checkpoints 1–3 — skeleton + variation + the diff-extraction
  logic, unit-tested on synthetic cases. No real skill yet, but the one genuinely new
  piece of machinery is built and proven correct in isolation.
- **If a full working day remains**: Checkpoints 1–5 — through the actual go/no-go gate
  (does a skill transfer to a fresh, disjoint world after a real restart). This is the
  single most information-dense stopping point: a full day gets a real answer to the
  architecture's central claim.
- **If through September 30 remains**: Checkpoints 1–7, plus this document's own
  succession requirements (below) fully satisfied regardless of how far the build gets.

### Succession requirements (satisfied at every checkpoint, not deferred to the end)

Each checkpoint commit includes: what was built, exact run/test commands, current status
against §14's phases, known limitations, and a `NEXT_ACTION.md` file stating precisely
what checkpoint comes next and why — so Gremlin, ChatGPT, or a future coding agent can
continue with no Claude-specific knowledge required, matching this whole session's own
established provenance discipline.
