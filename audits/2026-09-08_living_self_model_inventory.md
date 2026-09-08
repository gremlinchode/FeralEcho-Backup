# Living Self-Model — Inventory (Phase 1)

Investigated whether the existing architecture has enough observability to support a living epistemic model. Re-verified every claim against current source, not assumed from prior audits.

## What already exists, traced precisely

| Component | Exists | Writer | Reader | Survives session? | Survives restart? | Independently verified? |
|---|---|---|---|---|---|---|
| `self_model.json` | Yes, real, 318 lines | `SelfModelUpdater.update()` (`app/core/self_model_updater.py:91`), on its own 130s daemon loop | `echo_ground_truth.py`'s `_build_river`/`_build_capabilities`/`_build_affect`/etc. (real, confirmed) | Yes | Yes (disk file) | Partially — background telemetry only, no conversational input path |
| `self_knowledge_verification.py` | Yes, real | Nothing (it's stateless) | `routes_echo_studio.py:250` (one call site) | No — no persistence at all | N/A | Yes, this IS the verifier |
| `EDIT_FORBIDDEN_TARGETS` (`self_edit_manager.py:70`) | Real, protects `self_model_updater.py` already | N/A | N/A | N/A | N/A | N/A — confirmed `self_knowledge_verification.py` was NOT on this list before this mission (a real, previously-undocumented gap; closed in Phase 5 below) |
| Conversational corrections | Exist as ordinary transcript | `interaction_log.jsonl`/`council_deliberations.jsonl` | Nothing that feeds `self_model.json` | No — see Phase 2 | N/A | No — never independently checked, just logged |

## What can currently be observed / verified / persisted / retrieved (as of baseline)

1. **Observed**: yes — introspection_state.json, raw logs, real file/pickle state.
2. **Verified**: yes, narrowly — 4 specific claim shapes in `self_knowledge_verification.py`.
3. **Persisted**: yes for background telemetry (`self_model.json`); NO for a conversational claim/correction/verification verdict.
4. **Retrieved by Echo**: yes, `self_model.json`'s fields, via `echo_ground_truth.py`'s keyword-triggered slices.
5. **Triggers a self-model update**: only `SelfModelUpdater`'s own 130s timer and post-scan hooks — never a conversational event.
6. **Architectural changes auto-detected**: none currently — no observer exists.
7. **Invisible to the current system**: whether a specific self-claim was ever independently checked and what the verdict was — this exact gap is what this mission's implementation (Phase 4 onward) closes.

Full detail on the correction-path break is in `2026-09-08_self_model_correction_path.md` (mirrors Phase 2 of the prior Persistent Self-Model design, re-verified here).
