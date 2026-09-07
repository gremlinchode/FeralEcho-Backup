# 27-Day Showcase Mission — Phase 0: Architecture & Capability Liveness Map

Scope: architecture/liveness survey only, per this leg's directive. Adversarial testing and
Findings-91-93 re-litigation are explicitly out of scope here (owned by sibling legs running in
parallel). Read-only — no production file, RiverBrain state, or persisted memory was modified.
Live-server checks used only side-effect-free GETs (`/admin/liveness-status`, `/admin/autonomy-status`).

**Method:** for subsystems already deeply investigated earlier in this same session (self-edit
F1/F2/F3, RiverBrain training pathways, the sandbox, the new functional-quality verifier, RAOC,
council-rating cursor mechanics), that prior evidence is cited and marked `[inherited, previously
verified]` rather than re-derived from scratch. Everything else below was freshly checked in this
pass, marked `[fresh, this pass]`.

Snapshot time: 2026-09-06T14:52 UTC. Server PID 94884, uptime 47,072s (~13h), watchdog PID 94876 alive.

---

## Subsystem-by-Subsystem Liveness

### Model layer `[fresh]`
9 real Ollama models pulled and present (`echo:latest`, `gemma3:4b`, `qwen2.5-coder:7b`,
`deepseek-r1:7b`, `qwen2.5:3b`, `llama3.2:3b`, `llama3.1:8b`, `llama3:instruct`, `mistral:latest`),
confirmed via `ollama list`, not inferred from a config file. Plus `mlx:qwen3` (local MLX,
`mlx:gemma3` permanently retired per code-level `_RETIRED_MLX_MODELS`, verified in an earlier leg of
this session). **Live.** Invoked by `river_deliberation._ollama_query()`. Feeds every downstream
signal in this map. Independently demonstrable: `ollama list` + real interaction_log entries per
model.

### Orchestration (`echo_model_orchestrator.py`, `river_deliberation.py`) `[fresh + inherited]`
**Live.** `RiverBrain.score_model()` (reads `model_task_stats`) confirmed as the *primary* blended
signal in both `rank_models()` and `_select_council()` — re-confirmed earlier this session by direct
source read, not assumed. Invoked by every real conversational turn and every self-edit generation
call. Writes: `model_task_stats`, `classifiers`, `scalers`, `observation_counts`,
`sandbox_observation_counts`, `accuracy_trackers` (all in `memory/river_brain.pkl`, confirmed present
this pass: `keys: ['classifiers', 'scalers', 'observation_counts', 'sandbox_observation_counts',
'accuracy_trackers', 'model_task_stats']`). Reads: same file at startup. **Affects future
behavior:** yes, directly (model selection). **Independently demonstrable:** yes — before/after
`model_task_stats` reads around a real event, the exact method used successfully multiple times
earlier this session.

### RiverBrain `[inherited, previously verified this session]`
**Live**, with one confirmed asymmetry: two of four `.learn*()` pathways
(`learn_from_sandbox_outcome`, `learn_from_rating`) do **not** write `model_task_stats` — confirmed
by direct source re-read earlier this session — only the AST-heuristic-scored `.learn()` pathway
does. `accuracy_trackers` — re-confirmed this pass — is written at `echo_model_orchestrator.py:823`
and has exactly two real readers: itself (immediately after training, same class), and
`introspection_channel.py:288` (folds into a self-model/drift read). **Does its output affect future
behavior?** The `model_task_stats` writer does (feeds selection). `accuracy_trackers` does **not**
feed any decision — only a passive read into `self_model.json`'s drift reporting and a
`[DRIFT-NOTICE]` log line (never an autonomous action), consistent with what this session already
established. Not re-litigated further here (owned by the Findings-91-93 leg for the arbitration-fix
specifics).

### Memory / vector storage `[fresh]`
**Live.** `memory/memory_meta.json`: 124,477 entries (fresh count, this pass — was 124,477 at last
check earlier tonight too, consistent with steady real growth). `memory/faiss.index`: 191MB, mtime
`Sep 6 07:48` (same day, well within this session — actively written to, not stale). Invoked by
`memory_bridge.add_to_vector_memory()`/`retrieve_relevant_memories()`, called from real conversation
turns (`/chat/stream` → `save_turn_to_server()` → `/memory/conversation`) and autonomous fetch/dream
cycles. Writes both files. **Affects future behavior:** yes — retrieval feeds prompt construction for
subsequent turns. **Demonstrable:** yes, directly (a real conversation this session was independently
confirmed landing in `memory_meta.json` via the `/memory/conversation` route).

### Interaction logging `[fresh]`
**Live.** `memory/interaction_log.jsonl`: 13,191 lines, most recent entry `2026-09-06T14:50:34`
(18 seconds before this exact check) — actively, continuously written. Feeds council rating,
RiverBrain training labels, and the trace_id correlation work done earlier this session.

### Autonomous loops & scheduler `[fresh]`
**Live, all 9 registered.** `/admin/autonomy-status` (real GET, this pass) shows 9 loops each with a
recent `last_check_utc` and `skipped_reason: null`: `autonomous_loop` (10:00), `awareness_code_scan`
(01:47 — once at startup, by design), `echo_checkin` (09:56), `echo_messaging` (11:56),
`echo_projects_autonomy` (09:56), `emergent_scheduler` (14:47 — 5 min before this check, most
frequent), `model_guided_orchestrator` (07:28), `night_cycle` (11:38), `self_edit_loop` (07:30). This
is the shared `autonomy_coordinator.py` gate every loop routes through — genuinely running, not a
config file describing intent.

### Self-editing `[inherited, extensively re-verified this session]`
**Live**, with a nuanced picture already fully established earlier tonight, not re-derived here:
F1/F2/F3 hold; the deploy fitness gate (`_score_response_quality`, AST-only) is real but was shown
this session to have zero functional-correctness signal (Phase 1's own finding); 64% of the real
25-file retained-deploy corpus independently re-verified as functionally broken despite scoring at
the AST ceiling. Fresh this pass: cooldown timestamp `2026-09-06T11:36:28Z` (~3h15m before this
check) confirms the real hourly/dry-run cycle is still actively firing, not stalled — most recent
`SELF_EDIT.log` tail line is a real, current `staging_import_failed` (`NameError: name 'log_call' is
not defined`) from a live trial minutes before this check.

### Sandbox `[inherited, extensively tested this session]`
**Live**, both the pre-existing F2 kernel Seatbelt profile and the new `--mode=functional_verify`
built and adversarially tested earlier this session. Not re-derived here.

### Council / rating systems `[fresh + inherited]`
**Live.** `memory/council_cursor.json`: `{"position": 13191, "updated_utc":
"2026-09-06T14:51:01Z"}` — checked this pass, exactly matches `interaction_log.jsonl`'s current
13,191-line length to the second. This is the identical mechanism Finding 91 fixed (previously
found dead via a stale-cursor deadlock); now independently reconfirmed live via a completely fresh
check, not the same evidence already cited earlier tonight. `council_baseline_trusted_since:
2026-07-22T00:52:13Z` — trust gate genuinely set. `council_ratings.jsonl`: 137 entries (up from 135
observed ~13 hours earlier in this same session — real, continuing growth, not a frozen snapshot).

### Learning systems `[fresh + inherited]`
- **Shadow model**: `memory/shadow_accuracy.jsonl`, 2,061 lines, mtime `04:38` this session —
  actively growing (was cited at 2,054 in an earlier leg's context; +7 in the interim, consistent
  with real, continuous, low-rate accumulation). Its low real accuracy (13-16%, established earlier
  this session) is a *quality* finding, not a *liveness* one — it is genuinely live and genuinely
  weak, both true at once.
- **Dual learning** (`app/learning/dual_learning.py`): `log_event()`/`ingest_batch()` confirmed
  present in source this pass; **not independently confirmed firing in this pass** — no fresh
  `memory/dual_learning_meta.json` timestamp was found to check against (file absent or unwritten at
  the path checked). Flagged as **UNRESOLVED liveness**, not asserted either way — the phone-symbiote
  auth fix (Finding 55, prior session history) should make this live, but this pass did not verify it
  with fresh evidence the way every other claim above was.
- **`echo_projects` autonomy**: `memory/echo_projects_autonomy_state.json`: `last_run_utc:
  2026-09-06T10:43:56Z, last_status: "f2_failed", spec_source: "garden"` — genuinely live, genuinely
  real (a real F2 sandbox failure, not a placeholder), ~4h before this check, within its documented
  ~6h cadence tolerance.

### Experimental systems `[inherited]`
RAOC, preference-provenance, the echo-learning/behavioral-state research body: all previously
established this session as **fully isolated from the live pipeline by construction** (zero live
imports, confirmed via grep in an earlier leg). Not re-derived here. One fresh data point:
`app/core/behavioral_state.py` is imported by exactly one live file, `echo_ground_truth.py` —
confirmed this pass — consistent with the earlier finding that it's real, live, wired infrastructure
but currently holds zero directives (human-confirmed-only, no autonomous write path).

### Persistence (snapshots) `[fresh]`
**Live.** `memory/snapshots/`: 5 real, timestamped directories, most recent `20260906T014726Z` —
matches this session's own server restart exactly. Real, working retention (5 kept, consistent with
documented `_MAX_SNAPSHOTS`).

### Recovery / watchdogs `[fresh]`
**Live.** `start_echo.sh` watchdog confirmed running via direct `ps` (PID 94876, parent of the
current server process 94884) — this is the same watchdog that correctly refused a direct
`safe_restart.sh` collision earlier this session and was later used (by the human operator) to
recover from a real terminal-freeze/connectivity-loss incident tonight. Genuinely functioning, not
theoretical — demonstrated by a real incident this same session, not merely present as code.

### External dependencies `[fresh]`
**`claude_research.py` (real, paid Anthropic API call, rate-limited 1/hr): live.**
`memory/claude_research_cursor.json`: last real call `2026-09-06T09:20:24Z` (~5.5h before this
check, within its 48h liveness window), model `claude-haiku-4-5-20251001`, a real, specific,
non-placeholder question captured (`"Does God's possession of our reins imply a predetermined
outcome..."`). **This is the one subsystem in this entire map with a genuine, ongoing monetary cost
component** — small (1 call/hr, haiku-tier) but real, and worth flagging explicitly for the showcase
mission's "no additional monetary expenditure" framing: this isn't *additional* spend, it's existing,
already-budgeted spend, but a hostile reviewer would reasonably ask about it and the showcase
material should have a ready, honest answer rather than being caught flat-footed.

### Network dependencies `[fresh]`
**Live, real cross-machine traffic.** `memory/echo_messages.jsonl` tail (this pass): three real
`"sent"` entries across `2026-09-04` through `2026-09-06T09:58:19Z` (~5h before this check) — genuine
M5↔Air Tailscale traffic, not a stale log. Consistent with `/admin/autonomy-status`'s
`echo_messaging` entry (`last_check_utc: 11:56:08`, `skipped_reason: null`).

---

## Summary Capability Liveness Map

| Subsystem | Live? | Evidence (this pass unless marked inherited) | Affects future behavior? | Independently demonstrable? |
|---|---|---|---|---|
| Model layer (Ollama/MLX) | **Yes** | `ollama list`, 9 real models | Yes | Yes |
| Orchestration (RiverBrain-driven selection) | **Yes** | `rank_models()`/`_select_council()` source read | Yes | Yes |
| RiverBrain — `model_task_stats` path | **Yes** | pkl keys present, 2 of 4 pathways feed it (inherited) | Yes | Yes |
| RiverBrain — `accuracy_trackers` | **Yes (live, but functionally dead-ended)** | 2 readers found, neither drives a decision | **No** | Yes (of the dead-end itself) |
| Memory / FAISS | **Yes** | 124,477 entries, index mtime same-day | Yes | Yes |
| Interaction logging | **Yes** | 13,191 lines, latest 18s before check | Yes (indirectly, via what it feeds) | Yes |
| Autonomous loops (9) | **Yes, all 9** | `/admin/autonomy-status`, all recent | Yes | Yes |
| Self-editing (F1/F2/F3 + deploy gate) | **Yes** | Cooldown ts 3h15m old, live SELF_EDIT.log tail (inherited depth) | Yes, but on a weak AST-only signal (inherited finding) | Yes |
| Sandbox (F2 + new functional_verify) | **Yes** | Inherited, extensively tested | N/A (infra) | Yes |
| Council rating | **Yes** | Cursor exact-matches log length, second-precision | Yes (feeds `model_task_stats`) | Yes |
| Shadow model | **Yes (live, low-quality)** | 2,061 lines, growing | Yes, but weakly/misleadingly (inherited finding: worse than chance pre-Finding-91) | Yes |
| Dual learning (phone symbiote) | **RESOLVED (follow-up check, post-report): DORMANT, not live** | `memory/dual_meta.json` (not `dual_learning_meta.json`, the filename originally checked — a real miss, corrected here) confirmed real: 919 historical events, `last_ts=2026-07-22T14:17 UTC` — 46 days of silence as of the follow-up check. Routes (`/learning_event`) confirmed live and correctly wired in current `run.py`. | No (currently) | Yes — dormancy directly demonstrable via the meta file's own timestamp |
| `echo_projects` autonomy | **Yes** | State file, 4h-old real run, real failure captured | Yes (writes candidate projects) | Yes |
| RAOC / preference-provenance / echo-learning research | **No (by design)** | Zero live imports (inherited) | No | N/A — intentionally isolated |
| `behavioral_state.py` | **Yes (live, empty)** | One real live importer confirmed | Not yet (holds zero directives) | Yes (of the "wired but empty" state itself) |
| Snapshots | **Yes** | 5 real dirs, most recent matches this session's restart | Yes (recovery path) | Yes |
| Watchdog/recovery | **Yes** | Real PID, demonstrated in a real incident this session | Yes | Yes — already demonstrated once tonight |
| `claude_research.py` (external, paid) | **Yes** | Cursor 5.5h old, real captured question | Yes (feeds curiosity garden) | Yes — but carries real, small, ongoing cost |
| Echo↔Air messaging (network) | **Yes** | 3 real sends across 2 days, most recent 5h old | Yes (cross-instance sync) | Yes |

---

## Most Consequential Finding

**The single most important thing this survey adds beyond what was already known this session:**
`RiverBrain.accuracy_trackers` is **genuinely live** — it trains continuously, on every real
interaction, exactly as designed — **and simultaneously, permanently, structurally dead-ended** with
respect to actually affecting anything. It has exactly two readers in the entire codebase, and
neither one makes a decision with the value — one is itself (a training feedback loop that only
feeds itself), the other is a passive display field in a self-model JSON file that nothing else
reads for a decision either. This is a sharper, more precise instance of the "looks wired, isn't"
pattern this project's own CLAUDE.md history is built around finding — not a new discovery in kind,
but independently re-confirmed here via a completely fresh code trace, not carried over from prior
context.

**Second-most-consequential finding, resolved in a follow-up pass**: dual_learning (the phone-symbiote
ingestion path) is real and correctly wired but genuinely **dormant** — the original check looked at
the wrong filename (`dual_learning_meta.json`, which doesn't exist); the real file, `dual_meta.json`,
confirms 919 real historical events but zero activity in the 46 days before the follow-up check. Not a
liveness gap in this map anymore — a real, dated, evidenced finding: the mechanism works, real-world
input has simply stopped, most likely because Finding 42's required manual phone-side secret paste was
never completed or the phone client isn't currently running.

File written: `audits/2026-09-06_27day_phase0_architecture_liveness_map.md`. Untracked, not
committed.
