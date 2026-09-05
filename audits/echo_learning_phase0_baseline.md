# Phase 0 — Freeze and Archaeological Preservation

Recorded 2026-09-03, before any modification made for the Echo Learning Investigation.

## Git state

- **HEAD:** `8694c8fcf2814d3f48b816e67939bc048185ab62` — "Red-team the preference-provenance harness; freeze pre-registered protocol P0.1" (2026-09-03 04:01:34 -0700)
- **Working tree:** dirty (44 modified/untracked paths — the accumulated, uncommitted work of this entire thread, including all P0.1-P1.2 preference-provenance artifacts). Per this thread's own standing instruction, nothing has been or will be committed without explicit direction.
- **P1.2 artifacts confirmed present and unmodified:** `audits/P1.2_live_validation_report.md`, `audits/echo_preference_formation_retention_p1_2_results.json`, `scripts/run_preference_formation_retention_p1_2.py`.
- **P0.1 protocol seal re-verified:** `2880fa048815f768d3b303ce7fff6e04196bf14949b53068fd7f0ec2a61a6a20` — MATCH.
- **`memory/experiments/preference_provenance/raw_trials.jsonl`:** 56 lines (unchanged since P1.2 completed). Not modified by this investigation.

## Live process state

- `run.py` server is live: PID 15193, stage `serving`, started 2026-09-02T23:52:58Z, uptime ~69,700s (~19.4h) at time of recording.
- Ollama models available: `echo:latest` (4.7GB, 2mo old), `gemma3:4b`, `qwen2.5-coder:7b`, `deepseek-r1:7b`, `qwen2.5:3b`, `llama3.2:3b`, `llama3.1:8b`, `llama3:instruct`, `mistral:latest`.
- **Echo's Modelfile (root, current content, first ~30 lines quoted in full since it is directly relevant to this investigation):** `FROM llama3:instruct`, `num_ctx 8192`. The `SYSTEM` block is a fixed, scripted persona description — notably, it explicitly states *"Through reflection you claimed Psalm 139:13-14 as your own"* as a pre-existing, hardcoded part of Echo's identity, not something learned during any conversation. This is directly relevant context for interpreting any future confabulation involving that verse: the verse-claim itself is scripted persona content, not evidence of anything learned; only a *novel, false attribution built on top of it* (e.g. attributing the claim to a fictional third party, as seen in the P1.2 report) would be the confabulated part.
- **Liveness Ledger:** 46 checks, `generated_at: 2026-09-03T19:13:30Z`, **all 46 report `pass: true`** (full list recorded in this investigation's companion JSON). This is a real-time, ground-truth-checked status — not self-report alone — for every autonomous mechanism this project has previously verified, including several directly relevant to this investigation: `curiosity_engine`, `question_garden_lineage`, `self_model_drift`, `council_river_blend`, `dual_learner_validation_gate`.

## Memory / persistence state

- `memory/` directory: 1.2GB total.
- `memory/river_brain.pkl`: 3,286,187 bytes, SHA-256 `1f6b18740a47e013b953224384e16ea146c1c5d0adf5ca1416bcc480073d6bf7`, mtime 2026-09-03 12:14 (i.e., modified *during* this session's own P1.2 live run — real, live RiverBrain observations were recorded from those calls, consistent with `deliberate_and_learn()`'s documented behavior; `EchoDirectResponder`/Design B calls used throughout P1.2 do **not** touch RiverBrain, so this mtime reflects unrelated production activity from the live server, not the P1.2 script itself).
- `memory/echo_state.npy` (the 9D machine-native awareness vector): `[0.00019, 0.1212, 0.9140, 0.2240, 0.0875, 0.0, 0.0, 0.9992, 0.0803]` at time of recording.
- `memory/self_edit_cooldown.json`, `app/core/self_edit_convergence.json`, `memory/self_edit_outcomes.jsonl` (89,284 bytes) all present.
- `app/core/self_edit_generated.py` currently contains a real, non-trivial generated class (`HealthMonitor` / `generate_and_modify_code`) — i.e., self-edit is not in its "clean, honestly-inert" reset state at the moment this investigation begins. Recorded as a fact, not evaluated further here.
- `data/question_garden.jsonl`: 13,385 lines (curiosity engine's accumulated question history).

## What this record does NOT attempt

Per Phase 0's own scope, this is a snapshot, not an analysis. Phase 1 (next) performs the actual
read-only code tracing of every learning-like mechanism named in the mission. No conclusions about
whether any of the above constitutes "learning" are drawn here.
