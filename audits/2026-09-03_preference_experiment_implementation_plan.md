# Preference Provenance Experiment — Implementation Plan

Written before any code, per this mission's own instruction. Records
what exists, what is reusable, what is a contamination risk, where the
harness will be isolated, and exactly what new code is required. All
facts below are direct `file:line` citations checked this pass, except
where marked as carried forward from the four prior reports in this
thread (`self_modification_causal_chain.md`, `self_modification_evidence_index.md`,
`echo_agency_architecture.md`, `echo_preference_provenance.md`).

---

## 1. Existing components relevant to this build

**Persistence mechanisms** (candidates for reuse or precedent):
- `app/core/shadow_model.py` — 196 lines total. Public functions:
  `propose(adjustments)`, `compare_to_actual()`, `log_accuracy()`,
  `check_and_correct(delta)`, `propose_from_reflection(reflection_text)`.
  This is the project's own real precedent for "a reflection-triggered
  proposal gets persisted and later compared against outcome," and is
  the closest existing analogue to the lifecycle this harness needs —
  reused as a *design precedent*, not imported or extended, since its
  schema is fixed to self-edit-focus predictions specifically.
- `app/autonomous_awareness.py`'s `_load_code_scan_hash_cache()`/
  `_save_code_scan_hash_cache()` (confirmed present, prior session's own
  work) — the project's established atomic-write convention: temp file
  + `os.replace()`. This harness's store will follow the identical
  pattern, not invent a new one.
- `app/core/garden_manager.py` — real, working append/mutate functions
  (`harvest_question`, `update_question_quality`, `mark_question_asked`,
  `update_resolution`) operating on `data/question_garden.jsonl`. Not
  reused directly (different schema, different purpose) but confirms
  this project already has a working precedent for a JSONL-backed,
  human/reflection-fed store with quality/lineage tracking.

**Reflection mechanisms**:
- `app/subsystems/reflection_shard.py` — `ReflectionShard.observe(signal)`
  and `BecomingReflectionShard.observe(signal)` are the real, live
  reflection-generation entry points (both real model calls per this
  project's own CLAUDE.md Finding 75 history, not re-verified line-by-line
  this pass). **Not called by this harness** — the harness's own
  `MockResponder` and, for a real run, its `EchoResponder` are
  deliberately independent of Echo's own autonomous reflection loop, so
  that experimental trials are never silently mixed into Echo's real,
  continuous self-reflection stream. This is a **deliberate scoping
  decision**, not an oversight: reusing the live reflection loop would
  make trial provenance (§5 of the provenance report) unverifiable,
  since a live reflection cycle's inputs are not fully controlled.

**Outcome tracking**:
- `app/core/self_edit_outcome_tracker.py` — `record_pending_outcome()`,
  `evaluate_pending_outcomes()`, `get_outcomes_summary()`. Confirms this
  project's own established pre/post-delta pattern for measuring
  whether something "worked." The harness's own effect-size measurement
  (§20 of the mission) is structurally similar (baseline vs.
  treatment frequency) but implemented independently, since this
  tracker's schema and window logic are specific to self-edit quality
  deltas, not choice-frequency experiments.

**Session/model infrastructure**:
- `app/routes_echo_studio.py:39` — `_SESSIONS: dict = {}`, confirmed
  in-memory only, no disk-backed load path (re-confirmed this pass,
  same finding as the provenance report's §10).
- `app/core/echo_model_orchestrator.py:1367` — `def echo_query(prompt,
  use_all=False, task_type=None, temperature=None, source="autonomous",
  system=None, trace_id=None, post_synthesis_hook=None)`. This is the
  one real, existing injection point (`system=`) a future `EchoResponder`
  would use to surface experimental state without editing any protected
  file — confirmed present and unchanged this pass. **Not called by
  anything built in this pass** — `EchoResponder` (§4 below) wraps this
  function but is never invoked in this implementation's own test run.
- `app/core/river_deliberation.py:332` — `_ollama_query()`, and
  `terminal_client.py`'s `!ask <model> <task_type> <prompt>` command
  (cited from prior session's own work, confirmed present via grep) —
  the existing manual, single-model-call precedent for cross-model
  testing (§18 of the mission). Not modified.

**Provenance/logging precedent**:
- `memory/council_deliberations.jsonl` (Phase 10, this project's own
  prior work, carried forward not re-verified) — the real precedent for
  "log raw + processed content with a `source` field distinguishing
  origin." The harness's own `raw_trials.jsonl` follows this same shape
  (raw record, `source`/provenance field, never overwritten).

## 2. Potential contamination paths, identified before coding

1. **Vector memory leakage**: if any trial's prompt or response were
   ever written through `memory_bridge.add_to_vector_memory()` or
   `log_dream_bridge()`, it would become retrievable by Echo's real
   conversational memory search, contaminating future real
   conversations with experimental content. **Mitigation**: the harness
   never calls either function. All trial data lives exclusively in
   `memory/experiments/preference_provenance/*.jsonl`, a path FAISS
   ingestion has no reader for (confirmed via grep: no code anywhere
   walks `memory/experiments/`).
2. **RiverBrain training contamination**: if `EchoResponder` ever calls
   `echo_query()` for a real trial, `echo_query()`'s own internal path
   calls `RiverBrain.learn()` (per this project's own established
   behavior, unchanged). **Mitigation**: not resolved by this pass
   architecturally — flagged as a known limitation (§13 below) rather
   than solved, since solving it would require either a new `echo_query()`
   parameter to skip training (a production-file change, out of scope
   per the safety boundary) or never calling `echo_query()` for real
   trials at all (which the harness supports — `MockResponder` is the
   only responder actually exercised in this pass).
3. **Autonomous loop pickup**: if candidate files were written to a path
   any autonomous loop scans (e.g., `app/autonomous_awareness.py`'s daily
   code-scan, or the curiosity engine's garden read), they could be
   mistaken for real project content. **Mitigation**: `memory/experiments/`
   is not `.py` source (the code-scan only walks `.py` files under the
   project root, confirmed via this session's own prior read of
   `awareness_loop()`), and is a distinct path from `data/question_garden.jsonl`
   entirely.
4. **Self-edit pickup**: `self_edit_manager.py`'s module inventory
   (`_build_module_inventory`) only scans `app.*` modules for self-edit's
   own prompt construction. Placing the harness under `app/experiments/`
   means it **will** appear in that inventory (confirmed: the inventory
   is a project-wide `app.*` scan, not scoped to `app/core`). This is
   judged an acceptable, non-contaminating exposure — the inventory is
   read-only context for prompt construction, not a write target, and
   `SELF_EDIT_FILE` remains the only write target regardless of what
   appears in the inventory. Documented here rather than silently
   accepted.
5. **Confirmation bias in the implementer** (this session): the harness's
   own effect-classification function (`classify_effect()`) is
   restricted to a fixed, hard-coded allowlist of neutral labels
   (`INSUFFICIENT_DATA`, `NO_DETECTABLE_EFFECT`, `POSSIBLE_EFFECT`,
   `ROBUST_EFFECT`) with an explicit runtime assertion rejecting any
   attempt to write a label outside that allowlist — see §6 for the
   enforcement mechanism, added specifically because this document's
   own author (this session) is aware of the desired mythology and must
   not be trusted to self-police by good intentions alone.

## 3. Where the harness will be isolated

New top-level package: **`app/experiments/preference_provenance/`** —
deliberately *not* `app/experimental/` (the pre-existing, CLAUDE.md-
documented empty directory with its own established "dead weight, not
disconnected capability" meaning; reusing it would conflate two
different things). Confirmed via `ls`: neither `app/experiments/` nor
any file under it currently exists.

State/data: **`memory/experiments/preference_provenance/`** (per the
mission's own suggested location), confirmed via `ls` not to currently
exist. All writes are confined to this subtree by a runtime path-prefix
guard (`safety.py`, §6).

**Isolation is verified, not merely intended**: a negative test (§8 of
this plan) confirms zero production files (`run.py`, anything under
`app/core/`, anything under `app/routes_*.py`) import anything from
`app/experiments/`.

## 4. Exactly what new code is required

```
app/experiments/__init__.py                              (empty, package marker)
app/experiments/preference_provenance/__init__.py         (empty, package marker)
app/experiments/preference_provenance/schema.py           (dataclasses, enums, allowlists)
app/experiments/preference_provenance/provenance.py       (A-L taxonomy + evidence recording)
app/experiments/preference_provenance/store.py            (append-only JSONL persistence + reset)
app/experiments/preference_provenance/lifecycle.py         (propose/adopt/reject/revise/retain/expire)
app/experiments/preference_provenance/confounds.py         (confound snapshot dataclass)
app/experiments/preference_provenance/safety.py            (path-confinement + forbidden-target guards)
app/experiments/preference_provenance/harness.py           (Responder protocol, MockResponder,
                                                             EchoResponder [written, never invoked],
                                                             run_trial, run_counterfactual_batch,
                                                             classify_effect)
scripts/preference_experiment_cli.py                      (researcher inspect/adopt/reject/reset tool)
scripts/verify_preference_provenance_experiment.py         (unit/integration/negative tests,
                                                             this project's own check() convention)
```

No existing file is modified. This is a purely additive change.

## 5. What is deliberately NOT built in this pass

Per the mission's own Section 8 instruction ("do not implement
[autonomous adoption] yet unless the existing forensic report explicitly
establishes a safe experimental path" — it does not): no automatic
adoption path exists anywhere in `lifecycle.py`. Every state transition
requires an explicit call with an explicit human-originated argument;
there is no code path by which a candidate transitions from `PROPOSED`
to `ADOPTED` without that call. Cross-session, cross-model, and
hidden-state trial *execution* against the real Echo instance are
supported by the harness's design (pluggable `Responder`) but not
exercised — every test in `verify_preference_provenance_experiment.py`
uses `MockResponder` exclusively.
