# VSL Integration Readiness — Operation Skillforge

**Branch `vsl-implementation`, `main` untouched throughout.** This document is the
governing record for the 2026-09-28 integration-readiness mission: turning the
experimental Verified Skill Ledger (5 prior commits, ending `02632bb`, qualified AC-1
on Checkpoint 7) into a real, bounded, reversible FeralEcho subsystem, without
inflating the underlying scientific claims or weakening any safety gate.

## Phase 0 — ground truth, re-confirmed directly, not assumed

- Branch: `vsl-implementation`. Pre-mission HEAD: `02632bb083d0b2c210ed584f6927dbe8b4a6facb`.
- `main`: `2fba42644c82b9f7096276f4dd338d615cf1bcce`, untouched.
- Working tree: clean for VSL scope at mission start.
- `verify_diff_extract.py`: 15/15, re-confirmed.
- Governing docs re-read directly: the architecture deep dive, the build decision (§8's
  accumulation metric, §11/§12's KEEP/MODIFY/RETIRE precedent and reusable-core
  structure), both prospective protocols and their RESULTS sections, `NEXT_ACTION.md`.
- The real Echo execution architecture was inspected directly from source (not from
  README prose) — see Phase 2 below.

## Phase 2 — the real Echo loop, and exactly where VSL attaches

**Chosen integration point: `app/core/echo_projects.py`, not `self_edit_manager.py`.**
Both were inspected directly before deciding. `self_edit_manager.py` — the more
obviously analogous production loop (generate candidate → F1/F2/F3 → fitness-gate →
`save_code()`) — currently carries **204 lines of pre-existing, uncommitted changes
from a separate, unrelated research thread** (confirmed via `git diff --stat`), whose
content and intent are unknown to this mission. Modifying a dirty, 204-line-changed
safety-critical file blind, without understanding what the other thread is already
mid-way through changing, was judged too risky for a narrow, reversible integration —
a real engineering judgment call, not an oversight. `app/core/echo_projects.py` was
confirmed clean (`git status --porcelain` empty for that file at mission start) and is
already, by its own design, a sandboxed, never-auto-loaded, F1/F2-gated code-generation
space with zero promotion path into anything trusted (Liveness Ledger checks
`echo_projects_isolation`/`echo_projects_no_escalation` already enforce this structurally)
— a close-to-ideal match for VSL's own safety posture, requiring no new sandboxing to
be built.

Mapped against the mission's own loop shape, using real code:

| Stage | Real mechanism |
|---|---|
| task/input | `spec` (from the `!project` command, or `autonomous_generate_project()`'s curiosity-garden pick) |
| task classification | `task_type="general"` for planning, `task_type="echo_projects_coding"` for per-file generation (a dedicated RiverBrain bucket, kept separate per Finding 85) |
| model/council selection | `rank_models(task_type="coding")` (review), `deliberate_and_learn()` (planning), `echo_query()` (per-file generation) |
| generation/execution | `echo_query()`, one call per planned file |
| evaluation/reward | F1 (`scan_for_unsafe_operations`, safety only) + F2 (real kernel sandbox, "does it run") + an advisory, non-gating council review — **no correctness oracle exists at this integration point**, stated plainly below as a real, disclosed limitation |
| memory/state update | `_write_autonomy_state()`, `interaction_log.jsonl` via `echo_query()`'s own source tag |
| future task behavior | none today beyond RiverBrain's own generic per-model quality scoring — this is the real gap VSL's `applications.jsonl` now starts to fill, narrowly |

**VSL's own attach points, using this map directly:**
- **Acquisition** (where a verified failure/success pair originates): unchanged, still
  the experimental harness only (`app/experiments/skill_ledger/`) — production
  `echo_projects.py` does not yet feed new acquisition candidates back into VSL; it is
  a *consumer* of already-qualified skills, not yet a *source* of new ones. Stated as a
  real scope boundary, not solved in this pass.
- **Candidate generation**: `echo_query()`, already real, unmodified.
- **Verification authorizing learning**: unchanged — still the K2 harness's real hidden
  tests (`full_oracle` strength, per `runtime.py`'s own vocabulary). `echo_projects.py`'s
  own F1/F2 verdict is a *weaker*, safety-only signal (`f1_f2_safety_only`), never
  conflated with the stronger one (see `runtime.record_outcome()`'s explicit strength
  labeling and `evaluate_degradation()`'s exclusion of weak-signal evidence).
- **Skill qualification**: unchanged, still the experimental harness's
  `extract_transformation()`/prospective-transfer-test pipeline.
- **Retrieval**: `runtime.consult()`, called once per top-level function per generated
  file, before F1.
- **Consumption**: `matcher.apply_skill()` (unmodified core logic), gated by
  `VSL_ENABLED`/`VSL_MODE` and `effective_lifecycle() == "ACTIVE"`.
- **Feedback**: `runtime.record_outcome()` → `applications.jsonl` → (separately,
  explicitly invoked, never automatic) `runtime.evaluate_degradation()`.

## Phase 3/4 — production boundary and the preserved skill contract

`app/core/skill_ledger/` exposes: `matcher.{extract_transformation, apply_skill}`,
`schemas.Skill` (with `promote_to_verified/qualified/active`, `mark_degraded`,
`quarantine`, `retire`, `supersede`), `runtime.{consult, record_outcome,
evaluate_degradation, is_enabled, get_mode}`, `echo_adapter.{consult_file,
record_final_verdict}`. The `{precondition, transformation}` contract is byte-for-byte
unchanged from the experimental schema (verified directly: real Skill A/B files
recompute identical content hashes under the new schema — see Integration Commit 1's
message for the exact hashes). No frozen-answer storage, no natural-language lesson as
the authoritative mechanism, no embedding-based applicability, no model-confidence
gate anywhere in the consumption path — `apply_skill()` is a pure, deterministic AST
operation; a match is structural or it doesn't happen.

**THE LEDGER DOES NOT VERIFY ITSELF.** No function anywhere in `app/core/skill_ledger/`
computes a pass/fail verdict — `record_outcome()` only ever records one an external
caller already produced, and lifecycle promotion functions require a `evidence` string
naming a real, external fact (never a self-referential claim).

## Phase 5 — safety boundary

Unchanged, by design: F1 and F2 remain the *only* authority over what code actually
gets staged and executed, running identically whether or not VSL touched the code
first (verified directly: VSL runs *before* F1 in `generate_project()`, not instead of
it or after it in a way that could skip it). A VSL-introduced defect is caught by the
exact same real gates as a model-hallucinated one — no new trust boundary was created.
`consult_file()`/`consult()` themselves fail closed on any exception (a matcher crash
is treated as "no match", never propagated to break generation). Disabling
(`VSL_ENABLED` unset or anything but `"true"`) restores pre-integration behavior
exactly — verified directly (Integration Commit 4, checks 17-18).

## Phase 6 — lifecycle (built, see Integration Commit 1)

`CANDIDATE → VERIFIED → QUALIFIED → ACTIVE → DEGRADED → QUARANTINED → RETIRED /
SUPERSEDED`, additive to the legacy `status`/`held_out_verdict` fields (never
replacing them), with `effective_lifecycle()` deriving a value for any skill —
legacy or new — without requiring old files to be rewritten. Every transition is
write-once/versioned and requires a real evidence string.

## Phase 7 — conflicts (documented in `runtime.consult()`'s own docstring, not a
separate mechanism)

Deterministic, fixed-order (sorted `feature_key`), first-structural-match-wins;
never composes two skills within one `consult()` call; no specificity/outcome-stat/
recency-based tiebreak exists yet (explicit, accepted limitation — irrelevant with
exactly one real ACTIVE skill today, revisit once a second one is promoted).
`echo_adapter.consult_file()` *does* allow different skills to apply to *different*
functions within the same file across repeated `consult()` calls — composition across
functions, never within one match.

## Phase 8 — outcome attribution (built, see Integration Commit 2/3)

Every application is traceable to `task_id`/`feature_key`/`version`/mode/
`verifier_strength`/`verifier_result`/code hashes, via `applications.jsonl` — verified
directly (Integration Commit 4, check 13).

## Phase 9 — RiverBrain: NOT integrated, reasoned explicitly, not by default

Checked against every question the mission poses, using real code and real data
(RiverBrain's `model_task_stats` structure, VSL's own `outcome_stats` shape):

- **Do they measure the same thing?** No. RiverBrain tracks *model* reliability per
  task type (which model tends to produce good code for "coding" tasks); VSL tracks
  *skill* reliability (does this one specific code transformation help). There is no
  natural single bucket — merging them would conflate two different questions.
- **Would VSL's outcome signal be strong enough to feed RiverBrain safely?** No, not
  yet. The one wired integration point (`echo_projects.py`) only ever produces
  `f1_f2_safety_only`-strength verdicts (no correctness oracle exists there) — weaker
  than what already feeds RiverBrain's real quality scores (`echo_quality_scorer.py`'s
  AST-based checks). Feeding a weaker, safety-only signal into a more rigorously
  grounded score would dilute it, not strengthen it.
- **Circular reinforcement risk?** Real and unaddressed if built today: `consult()`'s
  conflict policy (Phase 7) does not currently weight by a skill's own success stats,
  so VSL is not self-reinforcing *today* — but a future "prefer higher-success skills"
  improvement (already flagged as accepted future work) would need to solve the exact
  same anti-self-reinforcement problem RiverBrain integration would introduce, so
  designing either in isolation right now, with almost no real application volume to
  calibrate against, would mean guessing at a safeguard rather than deriving one from
  evidence.

**Decision: keep fully separate.** Revisit only once VSL accumulates enough real,
`full_oracle`-strength outcome volume (a stronger verifier than the one integration
point currently wired) to be credible, non-diluting evidence — not attempted in this
pass.

## Phase 10 — FAISS: NOT integrated, reasoned explicitly

FAISS/embedding retrieval is explicitly disallowed as the *sole* applicability
mechanism by this project's own architecture (Phase 4's contract, already honored: all
matching is structural/AST-based). A *safe*, propose-only role (retrieve
semantically-similar past skill-application records as human-review context) was
considered and explicitly not built: with exactly 1-2 real skills in the ledger today,
a linear scan over ACTIVE skills (what `consult()` already does) is strictly simpler
and equally correct — there is no real retrieval problem yet for FAISS to solve.
**Decision: no role for FAISS in VSL at this scale.** Revisit only if/when the skill
count grows large enough that linear precondition-matching becomes a genuine
performance concern, and even then, FAISS would only ever *pre-filter candidates for
the structural matcher to verify* — never replace the structural decision itself.

## Phase 11 — component triage

| Component | Verdict | Reasoning |
|---|---|---|
| `app/core/skill_ledger/*` (new) | **KEEP** | The production core, this pass. |
| `app/experiments/skill_ledger/*` | **KEEP, unmodified in logic** | Scientific reference implementation, preserved byte-for-byte (Phase 1). |
| `app/core/echo_projects.py` | **MODIFY (this pass)** | One narrow, disclosed, tested hook. |
| RiverBrain (`model_task_stats`) | **KEEP, unmodified** | Real, demonstrated acquired-competence mechanism; not merged with VSL — see Phase 9. |
| FAISS / vector memory | **KEEP, unmodified, out of scope** | Correctly scoped to contextual retrieval already; not integrated — see Phase 10. |
| Council / routing (`river_deliberation.py`) | **KEEP, unmodified** | Already correctly used by `echo_projects.py`'s own generation calls; VSL adds nothing here. |
| Oracle/evaluator infra (`accumulation_probe.oracle_runner`) | **KEEP, reused directly** | The literal meaning of `runtime.py`'s `"full_oracle"` strength label; not reachable from `echo_projects.py`'s own domain today — a real, disclosed gap (see Known Risks). |
| Replay/substitution machinery (TRUE/SHAM pattern) | **KEEP, reused directly** | `prospective_transfer.py`/`accumulation.py` already reuse this design verbatim. |
| `self_edit_attempt_ledger.py` | **NOT integrated (deliberate)** | Currently dirty (unrelated, uncommitted, in-flight thread) — VSL built its own separate `applications.jsonl` rather than risk touching this file blind. A real, disclosed tension: the mission's own Phase 8 says "do not create a parallel attribution universe if Echo already has suitable identifiers" — weighed against the real risk of modifying an unstable file, and the safer choice was made. Flag for a future consolidation pass once that thread's own work lands. |
| `self_edit_manager.py` | **KEEP, unmodified, not integrated** | The natural next VSL integration target once its own current unrelated changes are committed/stabilized — not touched blind in this pass (see Phase 2). |
| Restart harnesses (`restart_persistence_transfer`'s PID convention) | **KEEP, reused directly** | Every fresh-process check in this project's VSL work (historical and production) uses this exact evidence standard. |
| Task classifier, self-model claims, drift detectors | **KEEP, unmodified, out of scope** | Not touched, not inspected deeply enough by this pass to recommend anything beyond "no change". |
| `persistent_routing`, G3/belief-revision harnesses | **RESEARCH-ONLY, unchanged** | Explicit prior null results / STOP-list items (this mission's own explicit instruction: do not reopen). |
| `first_learning_loop`'s mining half | **RESEARCH-ONLY, unchanged** | Already correctly scoped this way by the original build-decision memo. |

**Nothing was retired in this pass.** No component was deleted or deprecated based on
this integration alone — a full retirement audit of any of the above is out of scope
here.

## Phase 21 — adversarial integration review

A genuinely independent, fresh (non-fork) agent reviewed this integration end to end
per `.claude/skills/feral-independent-review/references/reviewer-checklist.md`,
including running its own experiments against the real code rather than trusting this
document's own framing. **It found one real, safety-critical defect and two real,
lower-severity gaps — all three confirmed independently by direct re-reproduction
before being fixed, and all three are now closed, with dedicated regression coverage.**
This section is the "Known Risks" disclosure the earlier draft of this document cited
but never wrote — a real, embarrassing gap in its own right, flagged by the same review
and closed here.

### Finding 1 (SAFETY-CRITICAL, FIXED): `matcher._rehydrate()`'s `eval()` was a real
sandbox escape

`_rehydrate()` reconstructed a transformation's AST via
`eval(hydrated, {"__builtins__": {}}, vars(ast))`. This was safe *only* for content
`extract_transformation()` itself produced — but `apply_skill()` (the real production
entry point) reads `transformation` from `Skill.load()`/`load_latest()`, which perform
**zero content validation**. `{"__builtins__": {}}` blocks bare-name builtin lookups
but not the standard attribute-chain escape
(`().__class__.__base__.__subclasses__()...`), which needs no builtins at all.
**Independently reproduced before fixing**: a hand-crafted `transformation` string
wrote a real marker file to disk purely as a side effect of computing `_rehydrate()`'s
return value — the exploit ran regardless of what the function returned, meaning F1/F2
never got a chance to matter; they never see the exploit because it never appears in
any returned code string.

This bug predates this integration (it was in the original experimental
`diff_extract.py`, where it was research-grade code with no autonomous trigger and no
persistent, disk-loaded, attacker-reachable skill files). What this integration
changed is the blast radius: it wired the identical code into a path reachable by an
unattended autonomous loop and persistent on-disk skill files that are never
re-validated on load. **This is exactly the class of gap this project's own culture
treats as unacceptable to leave undisclosed** (contrast with F1/F2's own honestly-named
"known residual gap" — third-party C extensions — which is disclosed *and* has no
simple fix; this one had a real, single-file fix and was undisclosed).

**Fixed**: `_rehydrate()` no longer calls `eval()`/`exec()` at all.
`ast.parse(hydrated, mode="eval")` produces an inert parse tree (parsing text is not
executing it), and a new `_validate_and_build()` walks that tree, constructing a real
object only for a small allowed shape (a call to a genuine `ast.*` class name, keyword
arguments, list literals, primitive constants) — anything else (attribute access,
subscripting, comprehensions, arbitrary names/calls) is rejected *before* a single real
object is built, closing the code-execution path entirely rather than trying to
enumerate more forbidden patterns. Verified: the exact exploit string, replayed against
both `_rehydrate()` directly and the real `apply_skill()` entry point, is now a clean,
honest `None` with zero side effects; every legitimate case (including a
negative-number literal, which needed explicit handling since Python's own parser
reads `-5` as `UnaryOp(USub, Constant(5))`, not a single negative `Constant`) still
reconstructs correctly, confirmed against the full historical 15/15 suite plus two new
dedicated regression checks.

**Practical exploitability before this fix, stated precisely, not overstated**: LOW —
nothing in the currently-wired automated pipeline writes attacker-influenceable content
into a skill's `transformation` field (`extract_transformation()`, the only writer,
always derives it from real `ast.dump()` output on parsed nodes). The vector required a
hand-edited or otherwise-corrupted skill JSON file. But it was real, demonstrated, and
undisclosed — fixed regardless of low current exploitability, not left as an accepted
risk.

### Finding 2 (FIXED): the documented "fails closed on any exception" contract was
false for skill-loading

`echo_adapter.py`'s own docstring claimed matcher exceptions are the only failure mode
guarded against; in fact `_list_active_feature_keys()` and the `Skill.load_latest()`
call inside `consult()`'s loop had no exception handling at all — a missing key or
malformed JSON raised straight out of `runtime.consult()`/`echo_adapter.consult_file()`.
`echo_projects.generate_project()` has no try/except around its own `consult_file()`
call site, so this would have propagated out of `generate_project()` entirely.
**Mitigating factor, confirmed directly**: both real callers of `generate_project()`
(`autonomous_generate_project()`, `terminal_client.request_project_generation()`) do
wrap it broadly, so this would not have crashed the server process — it would have
silently disabled the entire `echo_projects` generation feature (not just VSL) on every
call, the instant one skill file became corrupted, rather than VSL degrading
gracefully to "as if it weren't there."

**Fixed**: both `_list_active_feature_keys()` and `consult()`'s per-candidate
`Skill.load_latest()` call are now wrapped in try/except, degrading to "skip this
key"/"no match" — matching the fail-closed contract already applied to matcher
exceptions. Verified with a real corrupted skill file (valid JSON, missing required
keys) against `consult()`'s actual default (no explicit `feature_keys`) code path —
the one `echo_adapter.py` uses in production, and the one the original 24-check suite
never actually exercised (see Finding 2b).

### Finding 2b (FIXED): a test-isolation gap that let Finding 2 go uncaught

`runtime.py` originally did `from .schemas import SKILLS_DIR` — a copied name binding.
Monkeypatching `schemas.SKILLS_DIR` (the pattern this codebase's own historical
serialization test already establishes, and the pattern the original integration test
suite used) silently did **not** affect `runtime.SKILLS_DIR`, which
`_list_active_feature_keys()` actually reads. The original 24-check suite never
noticed, because every one of its "isolated scratch root" checks supplied an explicit
`feature_keys=` list — bypassing `_list_active_feature_keys()` entirely, and with it,
the one code path that actually uses the module-level `SKILLS_DIR` binding in
production. **Fixed**: `runtime.py` now does `from . import schemas` and references
`schemas.SKILLS_DIR` throughout, so a monkeypatch on the schemas module genuinely takes
effect everywhere. A new dedicated check confirms `runtime.schemas.SKILLS_DIR is
schemas.SKILLS_DIR` and that the corrupted-store scenario above is caught via
`consult()`'s real default code path, not just the explicit-`feature_keys` shortcut.

### Finding 3 (FIXED): lifecycle promotion order was enforced at exactly one step

Only `promote_to_active()` checked the skill's current `effective_lifecycle()`;
`promote_to_verified()`/`promote_to_qualified()`/`mark_degraded()` were callable from
any state at all — demonstrated live: a fresh `CANDIDATE` skill could jump straight to
`QUALIFIED` with a trivial evidence string, and a `RETIRED` skill could be silently
re-qualified. **The real production Skill A's own migration (this same integration
pass) exhibits a benign instance of exactly this gap**: v1 was already
effectively `QUALIFIED` (via legacy `status`/`held_out_verdict` fields) before
`promote_to_verified()` was called on it, moving it "backward" to `VERIFIED` in its own
recorded provenance, then forward again — harmless in this specific case (every
evidence string cited is genuine and real, and the final `ACTIVE` promotion was
correctly gated on `QUALIFIED`), but it proves the documented sequencing was decorative
outside the one enforced step. **Not retroactively corrected** — Skill A's real
v1-v4 files are left exactly as they are, per this project's own write-once,
never-rewrite-history discipline; this note is the disclosure instead.

**Fixed**: `promote_to_verified()` now requires `CANDIDATE`, `promote_to_qualified()`
now requires `VERIFIED`, `mark_degraded()` now requires `ACTIVE` — each raises
`ValueError` otherwise, mirroring `promote_to_active()`'s own pre-existing pattern.
`quarantine()`/`retire()`/`supersede()` remain deliberately unguarded (callable from
any state), since a safety-relevant removal should never itself be blocked. Verified
directly: a CANDIDATE→QUALIFIED skip is rejected, re-qualifying a QUARANTINED skill is
rejected, and — a genuine, adjacent discovery made while writing this specific
test — a **stale in-memory `Skill` object** (e.g., a `v4` reference held after the real
skill was quarantined to `v5` by a different code path) attempting a further
transition is independently caught by the write-once persistence layer itself
(`FileExistsError` on the version collision), not by the new lifecycle guard (which
only inspects the in-memory object's own fields, not a fresh disk read) — a real,
accepted limitation, disclosed rather than silently relied upon: callers should always
operate on a freshly-loaded `Skill` object, not a stale reference, though the
write-once layer provides a real backstop against silent corruption either way.

### What held up genuinely well under adversarial attack, per the reviewer's own
report

The additive, disable-by-default design; F1/F2 running after VSL for the *returned
code string* specifically; the shadow/active mode separation (shadow's proposed patch
cannot reach the staged file or report); the quarantine-exclusion mechanism (once
fixed, confirmed immediate, no restart); the conflict policy (confirmed deterministic
under a real two-matching-skills scenario); the hash-preservation of legacy skill
files; the `_pattern_for()` field-naming consistency between `runtime.py` and
`matcher.apply_skill()`; and the Phase 9/10 decision discipline (not integrating
RiverBrain/FAISS) — all confirmed correct under direct, adversarial testing, not just
reading.

### Post-fix status

All 3 findings fixed, each with dedicated regression coverage (not just re-confirmed
manually) in `scripts/verify_skill_ledger_integration.py`, now 34/34 passing (up from
24/24 pre-review). The historical 15/15 experimental suite is unaffected. The real
production Skill A remains cleanly `ACTIVE` at v4 — untouched by any of this session's
fixes or their tests.
