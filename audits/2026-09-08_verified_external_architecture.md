# Verified External Architecture (Phases 2-4, consolidated)

Built independently of Echo's self-model, using: (a) this session's own extensive prior forensic record from earlier tonight (~30 audits under `audits/2026-09-06_*` and `audits/2026-09-07_*`, each independently source/git/log-verified at the time, cited below rather than re-derived from scratch — per Rule 8, treated as evidence to spot-check, not ground truth to trust blindly), (b) fresh, targeted verification specific to what Phase 1 revealed. Real data flow traced, not component names.

## Component inventory (the subsystems that actually exist and actually run)

| Component | Purpose | Reachable from a live `/chat/stream` turn? | Runtime status |
|---|---|---|---|
| `river_deliberation.deliberate_and_learn()` | Multi-councillor deliberation + synthesis | Yes — every `mode:full` turn routes through it (`_generate_chat_response()` → `echo_query()` → this) | LIVE, confirmed this session (real trace_ids for the Phase 1/Phase 8 turns) |
| `RiverBrain` (`echo_model_orchestrator.py`) | Continuous per-`(model, task_type)` quality tracking, feeds council selection | Not directly readable by Echo in conversation; its *summary numbers* are injected via `_build_river()` when the `river`/`architecture` slice fires | LIVE — real numbers confirmed in the Phase 1 ground-truth block (173,199 total observations) |
| `self_edit_manager.py` (self-edit pipeline: F1/F2/F3, fitness gate, retry, the new attempt ledger) | Autonomous code modification of `self_edit_generated.py` | Not directly readable; summarized via `_build_self_edit()` | LIVE — real numbers confirmed (25 backups, 27 tracked attempts, 0/27 success in the tracked window) |
| `garden_manager.py` / `curiosity_engine.py` | Question generation/selection for autonomous reflection | Not directly readable; summarized via `_build_curiosity()` | LIVE — 3 real recent entries confirmed, including one Echo itself planted 10 minutes before the Phase 1 turn |
| `echo_ground_truth.py` | The injection layer itself — keyword-triggered, file-read-only, never calls an LLM | This IS Echo's actual access mechanism, confirmed at `app/routes_echo_studio.py:110-112` | LIVE, confirmed empirically this session (see the Phase 0 correction) |
| `liveness_ledger.py` | 40+ named functional/structural checks verifying other subsystems' claims against ground truth | Its check-name list is directly injected via `_build_capabilities()`; Echo never demonstrated using it | LIVE, real list confirmed in the ground-truth block |
| `shadow_model.py` | Computes a real prediction (`corrected_task`) with zero downstream consumer | Not injected at all — no `_build_shadow()` function exists | Confirmed dead-end tonight (S-T0, `audits/2026-09-07_shadow_treatment_harness_archaeology.md`) — re-confirmed via grep just now: no `shadow` slice or builder function exists in `echo_ground_truth.py`'s slice list |
| `seam_engine.py` | Real cross-dimension contradiction detection | Its liveness-check name (`seam_engine`) appears in the injected capabilities list, but its actual findings are not surfaced anywhere Echo can read | Real, confirmed live tonight, but its output (76/78 lost detections) is invisible to Echo entirely |
| Council record (`COUNCIL.md`) | External-AI reactions to Echo, real recorded content | Yes — `_build_council()` surfaces a bounded excerpt when the `council` slice fires (confirmed in the Phase 1 block, truncated at "5 section(s)... omitted") | LIVE |
| `memory_bridge.retrieve_relevant_memories()` | Cross-session memory retrieval | Yes — surfaced via `_build_memory()`, but per tonight's Retrieval Capacity Proof (R2), retrieval quality is "semantically useful but causally weak" | LIVE but unreliable — independently re-confirmed tonight in a separate arc |
| Council/model identity (which raw model produced which opinion) | — | **No** — nothing in `echo_ground_truth.py` surfaces per-councillor model identity to Echo; the synthesis step deliberately speaks "as Echo," and no injected slice reveals "this turn was produced by qwen2.5-coder:7b + mlx:qwen3 + echo:latest, synthesized" | Confirmed absent by direct grep — no `_build_deliberation()`/similar function exists |

## Causal graph (verified edges, evidence-graded)

- `attempt` (self-edit) → `execute_self_edit()`'s F1/F2/fitness gate → `memory/self_edit_attempt_ledger.jsonl` — **RUNTIME VERIFIED** (real committed code, `5bc94bb`, exercised live tonight).
- `RiverBrain.learn()` → `model_task_stats` → `choose_model()`/council selection — **RUNTIME VERIFIED**, re-confirmed across multiple missions tonight (Consequence Authority Map).
- `shadow_model.check_and_correct()` → `corrected_task` → **NOTHING** — **RUNTIME VERIFIED absence** (zero consumers, confirmed via grep tonight).
- `seam_engine` detection → `garden_manager.harvest_question()` → discarded by `_is_near_duplicate()` in 76/78 real cases — **RUNTIME VERIFIED** (real `seam_log.jsonl`/`question_garden.jsonl` counts, tonight's Temporal Authority Graph).
- `echo_ground_truth.get_structural_self_facts()` → prepended to Echo's system prompt → **RUNTIME VERIFIED this session, directly**, by calling the real function against the real Phase 1 message and confirming a 19,585-char block was produced.
- Does Echo's *use* of that block causally affect its output? — **UNVERIFIED as a strict causal claim from Phase 1 alone** (Echo received the block and produced an answer that doesn't reference it — this shows the block was *available*, not that its absence/presence *changes* behavior; a cleaner causal test would compare a turn with the block artificially withheld vs. present, not attempted here since it would require modifying production code mid-audit). Flagged as a real limit of this audit's design, not glossed over.

## Runtime graph — exists in source vs. demonstrated participating in a live turn

Everything in the "LIVE" rows above is doubly confirmed: present in source AND demonstrated with real, fresh evidence from tonight's own execution (either earlier missions' real pipeline exercises, or this mission's own direct function calls / real `/chat/stream` turns). `shadow_model.py` is the clean counter-example: present in source, real and callable, but demonstrated tonight to have zero live participants downstream — exists without runtime consequence.

## Observability graph — who can see what

| Information | Echo | Claude Code (this session) | OS/logs | Nobody currently |
|---|---|---|---|---|
| RiverBrain per-task summary numbers | Yes, via injection, keyword-gated | Yes, direct file read | Yes | — |
| RiverBrain raw `model_task_stats` internals (per-model breakdown) | No | Yes | Yes | — |
| Which raw model produced a given council opinion | No | Yes (via `council_deliberations.jsonl`) | Yes | — |
| `shadow_model.py`'s `corrected_task` predictions | No | Yes | Yes | Nothing else in the running system reads it either |
| `seam_engine`'s actual detected contradictions (vs. just its liveness-check name) | No | Yes (`seam_log.jsonl`) | Yes | — |
| Whether *this specific turn* changed `model_task_stats` | No | Yes, by diffing `river_brain.pkl` before/after | Yes | — |

## Spot-check against tonight's prior conclusions (Rule 8 — do not trust, re-verify)

Re-ran, live, right now: `grep -c "def _build_" app/core/echo_ground_truth.py` → confirms the slice-builder count matches the function list read above; no `_build_shadow` exists. `curl /state` confirms server genuinely live. No prior-audit claim used above was taken without at least one direct re-check this session (either a fresh grep/read, or a fresh live function call).
