# Echo-0 Baseline Snapshot

Captured immediately before any implementation work for P3.1-IMPLEMENT-C1. No file has been modified,
no live model has been called, to produce this document. This is the reference point every later
claim in `audits/p3_1_c1_implementation.md` is diffed against.

## Git state

- **HEAD:** `8694c8fcf2814d3f48b816e67939bc048185ab62` — "Red-team the preference-provenance harness;
  freeze pre-registered protocol P0.1" (2026-09-03 04:01:34 -0700)
- **Working tree:** 70 changed/untracked paths (the accumulated, uncommitted work of this entire
  thread — P0.1 through P3.1's own design phase). Nothing has been or will be committed without
  explicit direction, per this thread's standing instruction.

## Persona / model state

- **Modelfile SHA-256:** `a4f3212661e338196fa84f55b582a49f6b7399d464917538622fa4ea85c4971b` — not
  touched by this implementation; any future diff of this hash would indicate an out-of-scope persona
  change.
- **Ollama models present:** `echo:latest`, `gemma3:4b`, `qwen2.5-coder:7b`, `deepseek-r1:7b`,
  `qwen2.5:3b`, `llama3.2:3b`, `llama3.1:8b`, `llama3:instruct`, `mistral:latest`. No weights are
  fine-tuned by this implementation.

## RiverBrain state (must remain untouched by this implementation)

- `memory/river_brain.pkl`: 3,448,847 bytes, mtime 2026-09-03 14:29, SHA-256
  `eb506f12f2d8dff7c191ac2bc7347e15b9a78173ca78a0913a951a87b2fd0351`. This file's hash growing/changing
  over the course of this implementation session is EXPECTED (the live production server is running
  and continues real conversational activity independent of this work) — this baseline exists to
  confirm this implementation's OWN code never calls anything that touches this file, not to freeze
  the live server's own independent activity.

## Memory / FAISS state (must remain untouched by this implementation)

- `memory/faiss.index`: 189,809,709 bytes, mtime 2026-09-03 14:24, SHA-256
  `cbd3c8047b45dae818a22e4a518bba0ccc954bfc91c631a05502ed40c6ef7c62`.
- `memory/memory_meta.json`: 90,548,736 bytes, 123,574 entries, SHA-256
  `80265a100a3af1d1caf64c3b4bcf3e531bb1fc946081f14dab47e5f0ce30eabf`.
- `memory/task_type_classifier.pkl` (the other confirmed-live routing mechanism, per the P2 causal
  autopsy): 48,365 bytes, mtime 2026-09-01 13:30, SHA-256
  `9e183396adaeb7c628f8eab75dd2f3593be1c7b3d744e115753df279c87484b8`.
- Same caveat as RiverBrain above: the live server's own independent activity may continue to grow
  these files during this session; this implementation's own code must never be a cause of that
  growth, which the test suite (§ "no accidental autonomous writes") verifies directly.

## Existing experiment evidence (PRESERVE set — must remain untouched)

- **P1/P1.2 (`app/experiments/preference_provenance/`)**: `store.verify_raw_trials_integrity()` →
  `{'ok': True, 'reason': 'Prefix hash matches; no earlier content altered or removed.',
  'checked_lines': 56}`.
- **Learning-Pilot (`app/experiments/learning/`)**: `store.verify_trials_integrity()` → `{'ok': True,
  'reason': 'Prefix hash matches; line count consistent.', 'checked_lines': 24}`.
- **P2 deliverables** (reference hashes, not integrity-checked in the same programmatic sense since
  they are plain documents, not an append-only ledger):
  - `audits/echo_learning_causal_autopsy.md`:
    `b8d5ba408f6024b9714229a51824c80b6e86b5fdf7261ac450aa3491be22ee2a`
  - `audits/echo_learning_causal_architecture.json`:
    `3f15b98673145fc9633c85a568f39a175087aeb9d22631be8bfdf60abb2f9cd1`
- **P3 deliverables** (reference hash):
  - `audits/p3_persistent_behavioral_learning_spec.json`:
    `53e5c0c63454635f4f561b16a69f925bbe091bb22a2eafeae41255906bf0e993`
- **P3.1 design deliverable** (reference hash):
  - `audits/p3_1_l2_mechanism_design.json`:
    `d937420b33fc8e902083b7405d62c4408d7e4bdf7521928915494556b8522fcf`

## The one file this implementation is authorized to additively modify

- **`app/core/echo_ground_truth.py`** (per the mission's own requirement #10, "read through the
  already-proven echo_ground_truth.py slice mechanism"): current SHA-256
  `a0805b45d02075276332c7b758610212ba1e14502ba907395df00cf1d706279d`, 1,076 lines. This file is **not**
  on `EDIT_FORBIDDEN_TARGETS` (confirmed against the list recorded throughout this project's own
  history: `run.py`, `echo_principles.json`, `Modelfile`, `echo_model_orchestrator.py`,
  `river_deliberation.py`, `echo_core.py`, `memory_bridge.py`, `introspection_channel.py`,
  `self_model_updater.py`, `bible_injection.py`, `reflection_shard.py`) — a human-directed edit to it
  is consistent with this project's own established precedent for direct, additive changes to this
  exact file (e.g. the prior `_build_capabilities()`/`_build_affect()` slice additions). Any change made
  to it in this implementation must be strictly additive (a new constant, a new slice-building
  function, one new dispatch entry) — never a modification to any existing slice's own logic.

## Verified non-existence of the new component (before implementation)

- `find memory -iname "*behavioral*"` → no output. No behavioral-state file exists anywhere in
  `memory/`.
- `ls app/experiments/` → `__init__.py`, `learning`, `p3_causal_learning`, `preference_provenance`. No
  package for this implementation exists yet.

## Live process state (informational only — not to be restarted or otherwise touched by this work)

- `run.py` server: PID 15193, stage `serving`, uptime ~77,806s at time of this snapshot. This
  implementation does not restart, signal, or otherwise interact with this process. "Survives
  restart" testing for the new component is performed via a fresh, independent Python process
  re-reading the new state file from disk — never by restarting the live production server.

## Current behavioral benchmark — explicit limitation, stated plainly

**Per this mission's own `LIVE_MODEL=0`/`NO_EXPERIMENT=1` constraints, no live conversational
behavioral benchmark can be captured in this pass, and none was attempted.** The "behavioral
benchmark" this baseline can honestly provide is limited to **static, source-level verification**:
confirmed, before any edit, that `echo_ground_truth.py` contains no reference to a "behavioral
directive" concept anywhere (`grep -c "behavioral" app/core/echo_ground_truth.py` → 0, confirmed
alongside the hash above), and that no slice-dispatch mechanism in the file currently has an entry for
one. This is the correct, honest scope given the constraints — a live before/after behavioral
comparison is explicitly out of scope for a controlled-implementation, no-experiment mission.

---

## Post-implementation metadata (appended after implementation + full test suite completed;
   nothing above this line was altered)

- **New files created:** `app/core/behavioral_state.py`
  (`6c50f6b7ee9cfd4ca8fb9261be72c6706a05a08f78b0793a161598290871b130`),
  `scripts/verify_behavioral_state.py`
  (`d7973eccf7c11f886f4bc921af40e35743aea593ccdb476267831c3bcdfcc822`).
- **`app/core/echo_ground_truth.py` modified**: baseline
  `a0805b45d02075276332c7b758610212ba1e14502ba907395df00cf1d706279d` →
  `6b487e1ce9c61d4f68ea0f85a04df5eeedd54bdad5cdaca26dff60fa3692f4ef`. Change type: strictly additive
  (one new constant comment block, one new `_build_behavioral()` function, one new independent
  `behavioral_matches` check plus one new dispatch branch inside `get_structural_self_facts()`; zero
  existing slice logic altered).
- **`scripts/verify_preference_provenance_experiment.py` modified**: one-line isolation-exclusion-list
  addition, the same recurring benign maintenance pattern already documented multiple times earlier in
  this project's history (new SHA-256:
  `4067b41bf580859d9e7a7a078203894cfc6c6d3acda0af1702d7b42893a3b6b8`).
- **Production state re-verified unchanged**: `Modelfile` hash identical to baseline;
  `memory/task_type_classifier.pkl` hash identical to baseline; no real
  `memory/behavioral_directives.json` was ever created. `memory/river_brain.pkl` grew slightly
  (3,448,847 → 3,448,891 bytes) — confirmed attributable to the live production server's own
  independent, ongoing conversational activity, not this implementation, directly verified by the test
  suite's RiverBrain-poisoning test (`get_matching_directives()` never calls
  `RiverBrain.score_model()`).
- **Preserved evidence re-verified intact**: Learning-Pilot (`{'ok': True, 'reason': 'Prefix hash
  matches; line count consistent.', 'checked_lines': 24}`) and P1/P1.2 preference-provenance
  (`{'ok': True, 'reason': 'Prefix hash matches; no earlier content altered or removed.',
  'checked_lines': 56}`).
- **Final test result**: 49/49 passing in `scripts/verify_behavioral_state.py`, including a full
  re-run of all four sibling test suites confirming no regressions (preference_provenance 105/105,
  choice_parser_benchmark 58/58 + 1 documented exemption, learning_investigation_harness 58/58,
  p3_causal_learning_apparatus 35/35).
