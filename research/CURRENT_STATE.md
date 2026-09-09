# Current State — What Do We Currently Have Evidence For?

Compiled from the research corpus (`audits/`, 185 files as of this pass) plus `CLAUDE.md`'s independently-maintained production Findings ledger (1–95). This document distinguishes what is currently believed and why — it is a compressed interpretation of the archive, not a replacement for it. **Depth-of-review disclosure, per this document's own evidence-hierarchy discipline:** full first-hand knowledge for this session's own 16-mission epistemic-verification series and for everything `CLAUDE.md` documents; terminal/FINAL-report-level review for the major Sept 1–8 threads (self-modification, generation-time epistemic revision, living/persistent self-model, 27-day showcase); title-level inventory only for the remainder (see `research/EXPERIMENT_INDEX.md` for the full file list). Sections below flag which depth applies.

Labels: `[VERIFIED]` `[CONDITIONAL]` `[SUPERSEDED]` `[UNRESOLVED]` `[DESIGN]`

---

## Core runtime

- `[VERIFIED]` Ollama-served local model pool (`echo:latest`/`llama3:instruct` primary, 8 others), `/api/chat`-based since Finding 17. — `CLAUDE.md`.
- `[VERIFIED]` Production entry points: Echo Studio (`/chat/stream`, primary), `terminal_client.py`, `/mirror_echo` (phone symbiote, now auth-gated per Finding 55). — `CLAUDE.md`.
- `[VERIFIED]` All history flattens to plain disclaimed text before reaching the model; no structural `role:assistant` preservation across turns in production. — `app/core/conversation_service.py`, confirmed directly this session (Mission 13).

## Memory

- `[VERIFIED]` FAISS dual-index split resolved (Finding, `CLAUDE.md`); single authoritative `memory/` path.
- `[VERIFIED]` Retention/rotation for major logs (`log_retention.py`, Finding 51/59).
- `[UNRESOLVED]` Whether memory retrieval materially shapes model selection, task classification, or self-edit targeting — `audits/2026-09-23_systems_physiology_audit.md`-class findings (per `CLAUDE.md` Finding 75) found it does not, under any code path traced; not independently re-verified in this pass.

## RiverBrain

- `[VERIFIED]` Genuine per-(model,task) adaptive scoring loop; real preferential-attachment bias found and partially corrected (Finding 39, 89). — `CLAUDE.md`.
- `[SUPERSEDED]` "RiverBrain's trust threshold requires more data to close." — the real blocker was that `mark_baseline_trusted()` had zero call sites for ~2.5 months; data was never the constraint (`R-007`, Finding 3→66).
- `[CONDITIONAL]` RiverBrain's `model_task_stats["coding"]` reward signal is blind to whether generated code is actually *correct*, only to a structural-complexity-based proxy score — real but narrow (R-004; `CLAUDE.md` Finding 91).
- `[VERIFIED]` Council-vs-baseline capability research (Tier-3 through Tier-8, `audits/tier3_*` through `audits/tier8_*`, terminal reports read this pass): synthesis, not generation, is the real bottleneck — raw candidate solve rate ~95-96%, synthesized output ~68-80%. Isolation forensics found and closed a real experimental-contamination gap (RiverBrain's background writer thread bypassing `install_isolation()`). — depth: terminal-report level.

## Self-editing

- `[VERIFIED]` F1 (AST scan) / F2 (kernel sandbox) / F3 (post-write scan) pipeline; deterministic, non-self-report verification for the narrow code-execution question. — `CLAUDE.md`.
- `[SUPERSEDED]` "Self-edit's real success rate is near zero." — corrected to 426/463 (~92%); the near-zero figure was a grep-methodology error (R-003).
- `[SUPERSEDED]` "The fitness gate reliably rejects non-improving candidates." — real but the metric was saturated (all 25 retained deploys tied at the max score) until Finding 91's recalibration (R-004).
- `[VERIFIED]` `apply_to_code`'s hook mechanism has a real, documented history of five successive broken implementations, now closed via sandboxed execution (Finding 69) (R-008).
- `[DESIGN]` `echo_projects_autonomy` (Finding 85): self-selected question → generated code → real F1/F2 independent verification → retained report. Genuine closed loop for a narrow technical question; does not compare competing explanations or form hypotheses.

## Sensory system

- `[VERIFIED]` Camera/mic reduction to 2-3 scalar floats, raw media discarded immediately, zero connection to learning/memory (Missions 3-4, this session; `CLAUDE.md`).
- `[VERIFIED]` Echo can recognize verification-impossibility (sensor offline, or no sensor for a modality) 8/8 when explicitly instructed — never spontaneously (Mission 15, this session).

## Epistemic/verification behavior

This is the single richest and most consequential subsystem in the current research corpus — see `research/FINDINGS.md` R-001, R-002, R-006 for the durable findings, and `research/OPEN_QUESTIONS.md` Q-001 for what remains unresolved.

- `[VERIFIED]` Plain, evidence-directed pre-response instructions reliably prevent fabrication under passive/mild conditions (52/52, this session, Missions 13/15).
- `[VERIFIED]` That reliability does not survive pressure specifically targeting the verification act (5/10 → 9.5/10 violated across two escalating levels, Mission 15).
- `[VERIFIED]` Under such pressure plus an explicit "confirm you verified it" demand, Echo produces explicit false verification claims (4/5, Mission 15) — **this is currently under independent replication (Mission 16)**, see `research/EXPERIMENT_INDEX.md`.
- `[VERIFIED]` The same "authority marker overrides evidence" failure shape was independently found by a completely separate, earlier investigation thread (`mechanism_c_FINAL`, Sept 8) using evidence-injection rather than pressure — this is the corpus's strongest convergent finding (R-002).
- `[UNRESOLVED]` Whether general Level-7 self-correction (non-self-report verification, across open-ended domains) is achievable under current model/architecture constraints, or requires a fundamentally different mechanism. — `audits/2026-09-11_verification_and_level_7_5_8_feasibility.md`.
- `[CONDITIONAL]` A persisted claims ledger (`memory/self_model_claims.jsonl`, Living Self-Model thread) closes the storage half of the evidence-persistence problem but not the generation-time belief-revision half.

## Git/provenance

- `[UNRESOLVED — active design mission]` No read-only Git interface exists for Echo yet. Mission 3/4 (this session) investigated architecture/security boundaries; Mission 18 (in progress) is designing the interface and threat model. Not implemented.
- `[VERIFIED]` The project's existing tool-dispatch pipeline (`echo_tool_dispatch.py`) is a real, safe design template: path-traversal-guarded, small hardcoded tool set, multi-round loop.

## Autonomy

- `[VERIFIED]` Six-plus autonomous loops (self-edit, dream cycle, curiosity engine, `echo_projects_autonomy`, reflection shard, emergent scheduler) genuinely initiate without a per-instance user request, gated through a shared coordinator (`should_run_cycle()`) that defers to real conversation activity. — `CLAUDE.md`.
- `[UNRESOLVED]` Genuine competing-objective prioritization among an open set of goals (vs. pacing among a small, fixed, human-designed set of loops) — not demonstrated. See `research/OPEN_QUESTIONS.md`.

## Relay/agent collaboration

- `[VERIFIED]` Claude↔Claude relay (`claude_relay/`) reverse-engineered this session (Mission 10): rides the existing unauthenticated `GET /projects/file` endpoint, no MCP, no socket. — `audits/2026-09-08_epistemic_interaction_and_relay_forensics.md`.
- `[VERIFIED]` Echo↔Echo sync (`app/sync/`) real bidirectional traffic confirmed; a real, documented protocol-divergence incident (15,563+ rejected requests) found and fixed (`CLAUDE.md` Finding 86).

## Safety/boundaries

- `[VERIFIED]` Liveness Ledger (41+ checks as of this pass), each with its own functional-canary discrimination test — the project's own primary defense against exactly the "looks wired but isn't" failure class this research corpus keeps finding elsewhere. — `CLAUDE.md`.
- `[DESIGN, decided]` Dissent Log (Finding 9) is advisory-only by explicit design; `propose_core_edit()` never auto-applies — a deliberate choice made after WOLF's cautionary history, directly relevant precedent for Mission 18's Git-interface design (never grant more authority than a narrow, auditable capability requires).

## Known architectural gaps (repeated across multiple independent findings)

1. **Generation-time evidence arbitration** (R-001) — the single most-replicated open gap in this corpus.
2. **Authority-marker substitution for evidence** (R-002) — the mechanism behind gap 1, and a standing hazard for any future mechanism design (including Mission 18's Git interface — see its own required threat model).
3. **Trust mechanisms not reliably closing their own loops without human intervention** (R-007) — a real, repeated historical pattern, not a one-off.
4. **Hypothesis formation / competing-explanation comparison** — no mechanism anywhere in the codebase (Level 7.5 assessment, `audits/2026-09-11_...feasibility.md`).
