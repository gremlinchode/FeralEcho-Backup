# Phase 3: Architectural Intent & Data Flow Reconstruction (raw notes)

Reconstructed from the dependency graph (Phase 2) + direct reads (Phase 2.5), not from any
pre-existing documentation.

## Primary conversational flow (reconstructed from imports + route wiring)
Two real client entry points converge on one backend function chain:
  terminal_client.py  \
                        --> app/core/echo_model_orchestrator.py: echo_query()
  routes_echo_studio.py/                (imports river_deliberation, memory_bridge,
   chat_stream()      /                  echo_ground_truth, echo_tool_context)
                                          --> app/core/river_deliberation.py: deliberate_and_learn()
                                              --> app/ollama_handler.py: stream_query_ollama()/
                                                  query_ollama() --> Ollama HTTP API
[VERIFIED at the import-graph level: echo_model_orchestrator.py has 19 inbound importers and is
imported by river_deliberation.py's own dependents; ollama_handler.py was not itself deeply
re-read this pass but is referenced pervasively in source comments across the reviewed files.]

A third, separate entry point exists: run.py's `/mirror_echo` route (POST, gated behind
`_secret_ok()` per direct code read) -- a distinct code path from the two above, used by the
"thunderhead.py"/phone-symbiote reference client. [VERIFIED via grep at Phase 1]

A fourth, genuinely standalone Flask app exists at root: echo_json_server.py, binding the SAME
port 5000 as run.py (`app.run(debug=True, port=5000)` vs run.py's
`app.run(host="0.0.0.0", port=5000, ...)`), with its own separate route set. Not started by
run.py or any autonomous loop (no cross-reference found). A real, live conflict risk IF ever run
concurrently with run.py -- but nothing in the codebase does so automatically. [VERIFIED both
bind port 5000 via direct grep; NOT verified whether anything on the live host actually starts
this process, since that's outside static-audit scope.]

## Autonomous background flow
Multiple independent, uncoordinated timer loops exist (confirmed via `__main__`/thread-start
inspection across app/autonomous_loop.py, app/emergent_scheduler.py,
app/core/autonomous_loop_with_optuna.py, app/core/echo_model_guided_orchestrator.py,
app/maintenance/night_cycle.py) -- each imports from the shared hub modules
(echo_model_orchestrator.py, memory_bridge.py) rather than from each other, consistent with a
"fan-out from shared core, independent scheduling per loop" architecture rather than one
orchestrated pipeline. `app/core/autonomy_coordinator.py` (8 inbound importers) is a real,
shared throttle/stillness-check gate several -- but NOT ALL -- of these loops route through
(confirmed by import graph; exhaustive verification of which specific loops call
`should_run_cycle()` at their own top was not independently re-derived line-by-line for every
loop in this pass, time-boxed).

`app/core/scheduler.py` -- a well-designed, DIFFERENT "single dispatcher thread instead of N
independent while-True loops" mechanism -- exists, is clean, is documented as solving exactly the
architectural problem described above, and has ZERO real callers (confirmed Phase 2). This is a
genuinely interesting architectural fact: the codebase diagnosed its own "too many uncoordinated
timers" problem accurately enough to build a real, sound fix for it, and then never adopted the
fix anywhere. [VERIFIED]

## Self-edit flow (reconstructed, not narrated)
self_edit_manager.py (LOGIC_PLAN_DIR / SELF_EDIT_FILE / STAGING_DIR path constants, all anchored
via `_PROJECT_ROOT` derived from `__file__` -- confirmed this anchoring is real and NOT
relative/cwd-dependent by direct read of the constant definitions) drives:
  plan_code_logic() --> generate_code_from_plan() --> F1 scan --> F2 sandbox test -->
  save_code() (F3 re-scan) --> importlib.util.spec_from_file_location() dynamic load into the
  running process.
self_edit_generated.py is the one file that gets hot-loaded this way -- confirmed via
`SELF_EDIT_FILE` constant + `importlib.util` usage (Phase 2). Everything else in
EDIT_FORBIDDEN_TARGETS is excluded from autonomous write by the frozenset check.

## Memory / vector flow (reconstructed)
app/lib/vector_memory.py (VectorMemory class, FAISS IndexFlatIP) is the low-level persistence
primitive; app/core/memory_bridge.py (24 inbound importers -- the single highest fan-in module in
the entire scanned graph) is the shared write/retrieve API almost every other subsystem goes
through. app/core/memory_write_validator.py sits in front of memory_bridge's actual FAISS commit
path (confirmed via its own inbound-importer list: memory_bridge.py + dual_learning.py both
import it) -- a real, structurally-enforced validation gate, not merely a convention other code
happens to follow.

## Failure recovery / offline capability (reconstructed, partial)
- app/core/snapshot_manager.py (7 inbound importers) does real sha256-verified artifact backups
  (confirmed the module exists and is imported by council_rater.py, dmn_guardian.py,
  introspection_channel.py, liveness_ledger.py, self_edit_manager.py -- a real, broadly-consumed
  subsystem, not an isolated one).
- app/core/crash_awareness.py (4 inbound importers, including app/mlx_handler.py and
  scripts/verify_liveness_ledger.py) -- confirmed real: reads live macOS `.ips` crash reports AND
  a watchdog log for SIGABRT lines, to temporarily exclude MLX models from the council pool after
  a real detected crash cluster. This is genuine environmental self-protection logic, not merely
  narrated -- independently confirmed present via the import graph and direct function-name
  greps (`_evaluate_crash_window`, `list_mlx_models`).
- Offline LLM operation: the whole system's design center is a LOCAL Ollama server plus optional
  MLX models -- no cloud LLM dependency for the primary conversational path (confirmed: only
  `app/internet_tools/claude_research.py` makes an outbound Anthropic API call, rate-limited,
  and it is one optional autonomous-curiosity subsystem, not on the primary chat path per the
  import graph -- echo_model_orchestrator.py does not import claude_research.py).

## Honest gaps in this reconstruction (time-boxed, not exhaustively re-derived)
- Exact behavior of `ollama_handler.py`'s streaming/chat-message-building logic was NOT
  independently re-read line-by-line this pass (relied on grep + import-graph evidence only).
- The precise runtime behavior of `river_deliberation.py`'s council-selection algorithm
  (`_select_council`, exploration bias, tag-boosts) was NOT independently re-verified against
  live data (no live process available for a static audit) -- treat any claim about its actual
  selection outcomes as [HYPOTHESIS], not [VERIFIED].
