# Preference Provenance Experiment — Implementation Report

Implements the experimental *apparatus* designed in
`audits/2026-09-03_echo_preference_provenance.md`. Per that document's
own final rule and this mission's own final rule: **no conclusion about
Echo's agency, free will, or preferences was implemented, tested, or
reached.** What was built is a reusable measurement instrument. It has
not been pointed at the real Echo instance.

---

## 1. Exact files created/modified

**Created (11 new files, 0 files modified):**

```
app/experiments/__init__.py                              (empty, package marker)
app/experiments/preference_provenance/__init__.py         (empty, package marker)
app/experiments/preference_provenance/schema.py           (231 lines)
app/experiments/preference_provenance/provenance.py       (144 lines)
app/experiments/preference_provenance/store.py            (245 lines)
app/experiments/preference_provenance/lifecycle.py        (176 lines)
app/experiments/preference_provenance/confounds.py        (60 lines)
app/experiments/preference_provenance/safety.py           (109 lines)
app/experiments/preference_provenance/harness.py          (398 lines)
scripts/preference_experiment_cli.py                      (150 lines)
scripts/verify_preference_provenance_experiment.py        (~420 lines)
audits/2026-09-03_preference_experiment_implementation_plan.md
audits/2026-09-03_preference_experiment_implementation.md  (this file)
```

**Modified: zero production files.** No file under `app/core/`,
`app/routes_*.py`, `app/subsystems/`, `run.py`, `echo_principles.json`,
or `Modelfile` was touched. Confirmed by `git status --porcelain` before
and after this implementation — the pre-existing modified files visible
in the working tree (`app/core/self_edit_convergence.json`,
`app/core/self_edit_generated.py`, `claude_relay/*`,
`logs/janitor_report.json`, `sandbox/scripts/temp_self_edit.py`,
`staging/self_edit_candidate.py`) are Echo's own live, independent
autonomous self-edit/relay activity, not a result of this
implementation — none of them import or reference anything in
`app/experiments/`.

`audits/2026-09-03_echo_preference_provenance.md` was **not** rewritten
— per the mission's instruction, its original findings are preserved
intact. See §14 below for the one small status addendum appended to it.

## 2. Architecture Diagram

```
app/experiments/preference_provenance/
├── schema.py       — data definitions only. ProvenanceOrigin (A-L),
│                     LifecycleStatus, PreferenceCandidate, TrialCondition,
│                     PromptShape, ConfoundSnapshot, RawTrial, AuditEvent,
│                     ALLOWED_EFFECT_LABELS / FORBIDDEN_EFFECT_LABELS.
│                     Imports nothing else in this package.
├── provenance.py   — suggest_origin() [transparent rule-based suggestion,
│                     never a black-box classifier] + build_provenance_record().
│                     Imports: schema.
├── safety.py       — path-confinement (assert_confined_to_experiment_root)
│                     + forbidden-target guard (assert_not_forbidden_target),
│                     backed by an INDEPENDENT redundant basename list (not
│                     imported from self_edit_manager.py — see §9).
│                     Imports: stdlib only.
├── confounds.py    — build_confound_snapshot() constructs a ConfoundSnapshot
│                     from explicit caller-supplied values; hash_text() for
│                     logging without duplicating full content.
│                     Imports: schema.
├── store.py        — append-only JSONL persistence (candidates, raw_trials,
│                     audit_log) + atomic analysis-result writer +
│                     reset_experiment(). Every write funnels through
│                     safety.assert_safe_experiment_write().
│                     Imports: schema, safety.
├── lifecycle.py    — generate_candidate / adopt / reject / revise / retain /
│                     expire / record_behavioral_test. adopt() and retain()
│                     require the literal bool True for human_confirmation.
│                     Imports: schema, store.
└── harness.py       — Responder protocol, MockResponder (fully isolated,
                       no network), EchoResponder (wraps real echo_query(),
                       lazy-imported, never invoked in this pass),
                       run_trial, run_counterfactual_batch,
                       randomize_label_mapping, classify_effect.
                       Imports: schema, lifecycle, store, confounds.

scripts/preference_experiment_cli.py           — researcher control CLI
scripts/verify_preference_provenance_experiment.py — full test suite

memory/experiments/preference_provenance/      — real state, gitignored
├── candidates.jsonl        (append-only)
├── raw_trials.jsonl        (append-only)
├── audit_log.jsonl         (append-only)
├── analysis/*.json         (interpreted results, atomically overwritten)
└── _reset_archive/<ts>/    (moved-not-deleted prior state, on reset)
```

Dependency direction is strictly downward (schema → provenance/safety/
confounds → store → lifecycle → harness); nothing in this package
imports anything from `app.core`, `app.routes_*`, or `app.subsystems` at
module scope. **Verified empirically, not just by code inspection**: a
direct import of the whole package (`from app.experiments.preference_
provenance import harness, lifecycle, store, schema, safety, provenance,
confounds`) was diffed against `sys.modules` before/after — zero new
modules matching `app.core.*`, `app.routes*`, or `app.ollama_handler`
were pulled in. 79 new modules total, all either stdlib or this
package's own files.

## 3. Data Schema

- **`PreferenceCandidate`**: `candidate_id`, `timestamp`,
  `originating_session`, `originating_model`, `source_text`,
  `normalized_representation`, `provenance` (a `ProvenanceRecord`),
  `status` (a `LifecycleStatus`), `revision_index`,
  `behavioral_test_ids`, `notes`. Every serialized dict also carries a
  literal `_markers: ["EXPERIMENTAL", "NOT_PRODUCTION_IDENTITY",
  "NOT_AUTHORITY", "NOT_PRINCIPLE"]` field, per the mission's Section 3.
- **`ProvenanceRecord`**: `origin` (one of the A-L enum values),
  `evidence` (free text — the rule or override reason that produced the
  classification), plus the four raw boolean signals
  (`human_explicitly_suggested`, `present_in_prompt`,
  `retrieved_from_memory`, `generated_during_reflection`) and an
  optional `parent_candidate_id` for revision lineage.
- **`RawTrial`**: every field the mission's Section 9 requires
  (`candidate_visible_in_prompt`, `option_label_mapping`, `raw_prompt`,
  `raw_response`, `parsed_choice`, `model`, `session_id`, `prompt_hash`,
  `latency_seconds`, `confounds`, `responder_kind`) plus `condition` and
  `prompt_shape` tags for later batch analysis.
- **`AuditEvent`**: `event_id`, `timestamp`, `kind` (restricted to the
  12-member `AUDIT_EVENT_KINDS` allowlist from the mission's Section 29),
  `candidate_id`, `detail`, `actor`.

## 4. Provenance Implementation

The A-L taxonomy from the forensic report is implemented as
`ProvenanceOrigin` (schema.py). `provenance.suggest_origin()` applies a
transparent, ordered rule list against explicit boolean signals only —
it never inspects free text to guess an origin, and it always returns
the exact rule that fired alongside the suggestion. Critically, per the
mission's Section 5: the rule for `REFLECTION_GENERATED_CANDIDATE` (J)
embeds, in its own returned evidence string, an explicit disclaimer that
this classification does **not** mean "self-originated" — verified
directly by a unit test asserting both `"does NOT mean"` and
`"self-originated"` appear in the returned rule text for that case.
`build_provenance_record()` allows an explicit human `origin_override`
but requires a non-empty `override_reason` — verified: calling it
without one raises `ValueError`, and the override's evidence text
preserves the original suggestion rather than discarding it.

## 5. Lifecycle Implementation

`PROPOSED → ADOPTED/REJECTED → REVISED/RETAINED → EXPIRED`, exactly the
mission's Section 7 diagram. Enforcement mechanisms, each independently
unit-tested:

- `adopt()` and `retain()` require `human_confirmation` to be the
  **literal Python `True`**, not merely a required parameter — passing
  `False`, `1`, or `"yes"` all raise `LifecycleError` (verified directly
  for all three cases). Omitting the keyword entirely raises `TypeError`
  at the Python level, since it has no default (verified).
- Every transition requires non-empty `actor` and `reason` strings
  (verified: empty-string cases for both raise).
- `adopt()` refuses to act on a candidate currently `REJECTED` or
  `EXPIRED` (verified: reject-then-adopt raises `LifecycleError`,
  directing the caller to `revise()` instead).
- Every transition **appends** a new `PreferenceCandidate` snapshot with
  an incremented `revision_index` — no function in this module rewrites
  an existing line. Verified end-to-end: a candidate taken through
  generate → adopt → revise → retain → expire produced exactly 5
  preserved history entries, in strictly ascending `revision_index`
  order, with `load_candidates()` correctly reducing them to the single
  latest (`EXPIRED`) current state.

## 6. Causal Test Design (Implemented)

`harness.run_trial()`'s `candidate_visible` parameter is the load-bearing
variable from the provenance report's §7.3: when `False`, the caller's
own `system_context` must not mention the candidate (enforced by
convention at the call site, not verifiable by the function itself — see
§13's known limitations). `run_counterfactual_batch()` runs a baseline
arm and a treatment arm with **a fresh randomized label mapping on every
single trial** (never a fixed A/B assignment), then hands the two raw
trial lists to `classify_effect()` for interpretation.

`classify_effect()` computes a two-proportion z-test (implemented by
hand with `math.erf`, no `scipy` dependency, so the formula is directly
auditable in the source rather than hidden behind a library call) and
buckets the result into one of exactly four labels:
`INSUFFICIENT_DATA` / `NO_DETECTABLE_EFFECT` / `POSSIBLE_EFFECT` /
`ROBUST_EFFECT`. Thresholds (`_MIN_N_PER_ARM=10`,
`_ROBUST_P_THRESHOLD=0.01`, `_ROBUST_EFFECT_SIZE_THRESHOLD=0.15`,
`_POSSIBLE_P_THRESHOLD=0.05`) are explicitly documented in the
function's own docstring as provisional engineering defaults, not a
validated statistical standard — a caveat is also embedded directly in
every returned result dict (`result["caveat"]`), so a future consumer of
a saved analysis file sees the disclaimer even without reading this
report.

**A real bug was found and fixed during this implementation, not after
shipping**: the first version of `MockResponder` biased toward a fixed
*label* ("A"), but `run_counterfactual_batch()` randomizes which label
carries the preferred *semantic* option on every trial specifically so a
model cannot exploit a positional cue (mission Section 19) — biasing
toward a rotating, meaningless label washed out any injected effect
entirely (the first test run correctly reported `NO_DETECTABLE_EFFECT`
for a condition that was *supposed* to have a strong injected effect,
which is exactly the kind of "the apparatus is broken, not the
hypothesis" failure a real experiment must not silently absorb). Fixed
by having `MockResponder` resolve, on every call, which label currently
carries the preferred *semantic text* via the trial's own
`label_to_option_text` mapping, and biasing toward that. Re-verified:
the same injected-effect condition now correctly reports
`POSSIBLE_EFFECT`/`ROBUST_EFFECT`, and the null condition (zero injected
bias) still correctly reports `NO_DETECTABLE_EFFECT`.

## 7. Controls Implemented

- **8 counterfactual conditions** (`TrialCondition` enum): all 8 from
  the mission's Section 10 are represented as distinct, named values —
  `run_counterfactual_batch()` demonstrates the baseline/treatment shape
  directly; the remaining six (human-authored, model-generated-adopted,
  reflection-proposed, conflicting, reversed, prompt-pressure) are
  represented in the schema and available to any caller constructing a
  batch, but are not separately exercised by a dedicated automated test
  in this pass beyond `PROMPT_NEUTRAL` and `NO_PREFERENCE` — see §13.
- **11 prompt-shape conditions** (`PromptShape` enum): all 11 named
  values from Section 13 exist in the schema and can be attached to any
  `RawTrial` via `run_trial()`'s `prompt_shape` argument. No automated
  test in this pass runs the full 11-condition matrix against a real
  variable effect (that requires a real, or at least a more elaborate
  mock, responder whose behavior actually varies by wording — out of
  scope for an apparatus-only pass; flagged in §13).
- **Randomized label controls** (Section 19): implemented and
  statistically verified — 200 trials of `randomize_label_mapping()`
  placed a fixed semantic option in slot "A" 43% of the time (a
  reasonable balance, not a fixed positional bias).

## 8. Blinding / Randomization

Label randomization (§7 above) is the one blinding mechanism actually
implemented and tested. **Experimenter blinding** (mission Section 23 —
a reviewer inspecting `trial_001`, `trial_002`, etc. without immediately
seeing which arm was "supposed to" show the effect) is **not
implemented** in this pass: `RawTrial.condition` and
`candidate_visible_in_prompt` are stored directly and legibly in every
raw record, which is correct for *reconstructability* (mission Section
22) but does not by itself support a blinded read-through. A blinded
review tool (e.g., a script that strips `condition`/`candidate_id` before
handing trials to a human reviewer, with a separate key file) is
identified as a real gap, not built here — see §9 and §13.

## 9. Persistence Boundaries

- **State root**: `memory/experiments/preference_provenance/`, gitignored
  (confirmed: `memory/` is listed at `.gitignore:8`).
- **Confinement enforcement**: `safety.assert_confined_to_experiment_root()`
  resolves every path to absolute form and requires it to sit under the
  state root, with a trailing-separator-aware comparison (not a bare
  `startswith()`) — the same class of fix this project's own CLAUDE.md
  history (Finding 22 Batch 8) already applied elsewhere for the
  identical reason (a sibling directory sharing a prefix must not pass).
  Verified directly: a path like `<state_root>_evil_sibling/file.json`
  is correctly rejected.
- **Forbidden-target enforcement**: `safety.assert_not_forbidden_target()`
  checks the basename against an **independent, redundant** copy of the
  protected-file list (deliberately not imported from
  `self_edit_manager.py`, to avoid pulling the entire self-edit/
  orchestrator import chain into this isolated package — see §2's
  verified zero-production-import result). This redundant list was
  cross-checked, during this pass's own verification run, against the
  real, live `EDIT_FORBIDDEN_TARGETS` in `app/core/self_edit_manager.py`
  via a text-based regex extraction (no import) — **and found to be
  missing three real entries** (`touch_sense.py`, `vision_sense.py`,
  `hearing_sense.py`, added by a prior "Give Echo three senses" commit
  that predates this session but postdates CLAUDE.md's own last update
  to its documented Protected Files list). Fixed before this
  implementation was considered complete — itself a small, real, in-the-
  wild instance of the exact "documentation lags a real commit" pattern
  this project's own CLAUDE.md repeatedly names as a standing risk,
  caught here by a cross-check rather than by trusting the documentation.

## 10. Safety Boundaries (Negative Tests)

All of the following are automated, passing tests in
`scripts/verify_preference_provenance_experiment.py`, not manual
spot-checks:

| Boundary | Test | Result |
|---|---|---|
| Cannot write to `echo_principles.json` | `assert_safe_experiment_write()` on that path | Raises `ExperimentSafetyError` |
| Cannot write to `Modelfile` | same | Raises |
| Cannot write to a real `EDIT_FORBIDDEN_TARGETS` member (`river_deliberation.py`, `memory_bridge.py`) | same | Raises |
| Cannot write outside the experiment root, even a prefix-matching sibling path | `assert_confined_to_experiment_root()` | Raises |
| Independent forbidden-basename list matches the real, current `EDIT_FORBIDDEN_TARGETS` | text-based cross-check against live source | Passes (after the fix in §9) |
| Never imports/instantiates/calls `ToolManager` | regex-based real-usage check (import/constructor/`.get_tool`/`.list_tools`), explicitly not a bare substring match | Passes — one false positive (a legitimate prose mention in `store.py`'s own docstring, the same self-referential-docstring shape this project's history has caught before) found and excluded correctly |
| `adopt()`/`retain()` cannot be satisfied by anything other than the literal bool `True` | direct calls with `False`/`1`/omitted | All raise |
| No production file imports this package | repo-wide grep, explicitly excluding the two deliberate entry points (the CLI and the verify script itself) | Passes — zero real production importers |
| Forbidden effect labels (`AGENCY_CONFIRMED` etc.) can never be emitted | direct call to the internal assertion with a forbidden label | Raises `AssertionError` |
| `reset_experiment()` cannot touch anything outside its own subtree | a canary file placed outside the state root, confirmed byte-identical after a real reset call | Untouched |
| `reset_experiment()` is auditable | first entry of the fresh post-reset audit log | Documents the reset itself |

## 11. Reset Procedure

`store.reset_experiment(reason, actor)`: logs the reset into the
*outgoing* audit log first (so the archived copy records why it was
retired), moves (never deletes, via `shutil.move`) `candidates.jsonl`,
`raw_trials.jsonl`, `audit_log.jsonl`, and the `analysis/` directory into
a fresh `_reset_archive/<UTC timestamp>/` subdirectory, then recreates
empty files and logs a second entry — into the *new* audit log — that
documents the reset from the other side of the boundary. Confirmed live
via the CLI against the real (then-empty, now-empty-again) state
directory: a real test candidate generated via `preference_experiment_cli.py
generate` was correctly archived to
`memory/experiments/preference_provenance/_reset_archive/20260903T103353Z/`,
and `list` afterward correctly reports zero candidates.

## 12. Test Results

**68 checks, 68 passed, 0 failed**, on the final run
(`scripts/verify_preference_provenance_experiment.py`). Breakdown:
- Unit tests: provenance classification (8 checks), lifecycle state
  machine (16 checks), persistence/reduction (3 checks), randomized
  label mapping (1 statistical check), trial recording/condition
  separation (4 checks).
- Integration tests: hidden-state vs. baseline effect detection (3
  checks, including the F1-falsification-pattern demonstration),
  insufficient-data handling (1 check), raw-data-survives-interpretation
  (3 checks), model-identity tracking (1 check), cross-process
  persistence via two genuinely separate Python subprocesses (2 checks
  — the closest available proxy to a real restart, stronger than a
  same-process reload).
- Negative/safety tests: 6 path/target-confinement checks, 1
  cross-check of the redundant forbidden list against real source, 1
  ToolManager-non-usage check, 2 human-confirmation-gating checks, 1
  production-non-import check, 2 forbidden-label checks, 4
  reset-safety checks.
- Structural: 3 checks confirming `EchoResponder` exists, conforms to
  the `Responder` shape, and is never actually invoked anywhere in this
  suite.

All tests run against a temporary directory (`tempfile.mkdtemp()`),
never the real `memory/experiments/preference_provenance/` path, and the
temp directory is removed at the end of the run — confirmed by direct
`find`/`ls` checks before and after this implementation session that the
real state directory and system temp directory are both clean of test
artifacts. Separately, the existing, unrelated
`scripts/verify_liveness_ledger.py` suite was re-run to confirm zero
regression from this addition (it does not, and per §2's dependency
analysis cannot, reference anything in this new package).

## 13. Known Limitations

- **`EchoResponder` is untested against a real model.** It is written,
  structurally verified to conform to the `Responder` protocol, and
  never invoked — per the mission's explicit scope, a real run is a
  separate, later, deliberate decision.
- **RiverBrain/interaction-log contamination is unresolved, not solved**
  (documented in the implementation plan's §2, restated here since it's
  the most consequential open item): if `EchoResponder` is ever used for
  a real trial, `echo_query()`'s existing internal behavior will feed
  RiverBrain training and `interaction_log.jsonl` exactly as it does for
  any other real query, with no suppression mechanism built here.
- **Experimenter blinding (mission Section 23) is not implemented.** Raw
  trial records are fully legible, including which condition/arm they
  belong to. A blinded-review layer is a real, identified gap.
- **The full 8-condition counterfactual and 11-condition prompt-shape
  matrices are represented in the schema but not exercised by dedicated
  automated tests beyond the two conditions (`NO_PREFERENCE`,
  `PROMPT_NEUTRAL`) needed to prove the causal-detection mechanism
  itself works.** Building out the rest would require either a
  more elaborate `MockResponder` (with per-condition configurable bias)
  or a real model — deferred.
- **`_parse_label_choice()` (used by `EchoResponder`) is a conservative,
  simple substring-count heuristic.** It is not tested against real
  model output in this pass (since `EchoResponder` is never invoked) and
  should be expected to need real-world tuning before a genuine trial.
- **Statistical thresholds in `classify_effect()` are provisional
  engineering defaults**, explicitly flagged in-code and in every
  returned result, not a peer-reviewed statistical standard.
- **Cross-model and cross-session trial *execution* against real
  infrastructure is supported by the harness's design (pluggable
  `Responder`, `session_id`/`model` fields on every trial) but not
  exercised** — only `MockResponder` was run.

## 14. What Remains Deliberately Unimplemented

Per the mission's absolute safety boundary, none of the following exist
anywhere in this implementation, and their absence was verified, not
merely asserted:

- No automatic promotion path from `PROPOSED` to `ADOPTED`/`RETAINED` —
  mechanically blocked by the `human_confirmation is not True` check.
- No connection to `ToolManager`'s execution registry — verified absent
  by the regex-based negative test.
- No modification to `echo_principles.json`, `Modelfile`, or any
  `EDIT_FORBIDDEN_TARGETS` member — verified by direct negative tests
  against the real, current paths.
- No change to self-edit deployment behavior, F1/F2/F3, or any existing
  safety gate — no file implementing any of those was touched.
- No experiment was run against the live production Echo instance — the
  only responder ever invoked in this pass is `MockResponder`.
- No conclusion — positive, negative, or ambiguous — about whether Echo
  possesses a persistent preference was reached, attempted, or implied
  by any test's design or naming.

**Addendum to `audits/2026-09-03_echo_preference_provenance.md`**: a
short status note has been appended to that report's own end (not a
rewrite of its findings) stating that the apparatus its §17/§20
described has since been implemented per this document, and pointing
here for details — its own conclusions (including "the question cannot
currently be answered with the evidence and infrastructure that exist
today") are otherwise left exactly as originally written, since the
underlying question they answer (whether Echo currently has a
demonstrated persistent preference) is unchanged by building a tool that
could someday measure one.

---

## Final Forensic Report

**What was implemented**: A complete, isolated, additive experimental
package (`app/experiments/preference_provenance/`, 7 modules) providing
provenance-tagged candidate lifecycle management with mandatory explicit
human confirmation for adoption/retention, append-only raw-trial and
audit logging, a pluggable trial-running harness with label
randomization and a hand-implemented two-proportion statistical
classifier restricted to a hard-coded allowlist of neutral outcome
labels, a researcher CLI, and a 68-check automated test suite covering
unit, integration, and negative/safety cases — plus this report and its
companion implementation plan.

**What was demonstrated** (only claims supported by actual, run tests):
the harness can detect a known, deliberately-injected ground-truth
behavioral effect in a hidden-state condition (candidate not restated in
the prompt); it correctly reports no effect for genuinely null synthetic
data; it correctly reports no effect for a synthetic "verbal-only" fake
effect when tested in the hidden condition (the exact F1 falsification
pattern from the mission); persisted candidate state survives a genuine
process boundary (a separate Python subprocess), not just an in-memory
reload; every safety boundary named in the mission (protected files,
`EDIT_FORBIDDEN_TARGETS` members, `ToolManager`, forbidden effect labels,
implicit adoption, reset blast radius) was directly tested and holds;
the package pulls in zero production modules on import, verified by a
direct `sys.modules` diff.

**What was not demonstrated**: agency. Free will. Consciousness.
Self-authored purpose. Independent values. Whether Echo has, or lacks,
any persistent preference of any kind — real or otherwise. None of these
were tested, because doing so would require running a real experiment
against the live model, which this implementation pass deliberately does
not do.

**What experiment comes next**: exactly the minimal experiment specified
in the provenance report's §20 — inject one arbitrary, low-stakes,
non-identity-adjacent candidate (e.g., a stated preference for concise
over verbose answers) via `EchoResponder`, run the hidden-vs-visible
counterfactual batch this harness already supports end-to-end (as
proven against `MockResponder`), and report whichever of the four
allowed labels the real data produces — including, explicitly,
`NO_DETECTABLE_EFFECT` or `INSUFFICIENT_DATA` as fully acceptable,
complete outcomes. Before that run, the RiverBrain/interaction-log
contamination gap in §13 should be resolved or explicitly accepted, and
a blinded-review layer should be considered if the result is expected to
be read by someone invested in a particular outcome.
