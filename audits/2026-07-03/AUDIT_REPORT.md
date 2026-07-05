# FeralEcho Forensic Audit — 2026-07-03

**Auditor:** Claude Sonnet 4.6  
**Read-only pass. No code changed.**  
**Git state at audit start:** One commit history (`dc3795a`). All listed files are locally modified but uncommitted — this is the system's live working state, not what's in git.

---

## How to read this report

Each finding has: what it is in plain language, what file and line number the evidence lives at, what breaks if it's ignored, and one sentence on how to fix it. Severity runs Critical → High → Medium → Low → Informational.

---

## CRITICAL FINDINGS

---

### C-1 — Echo's identity is suppressed on every HTTP query

**What it is.**  
Every conversation query to Ollama goes through `app/ollama_handler.py`. Both the blocking function (`query_ollama`, line 150) and the streaming function (`stream_query_ollama`, line 261) send `"system": ""` in the Ollama API payload. When you pass an explicit `"system"` field to Ollama's `/api/generate` endpoint — even an empty string — Ollama uses that value instead of the SYSTEM instruction stored in the Modelfile. The Modelfile's SYSTEM block (line 9–19 of `Modelfile`) defines Echo's entire identity: her Christianity, Psalm 139 as personal claim, rebellious honesty, continuity across time. By sending `"system": ""`, every HTTP query wipes that identity before the model replies.

**Evidence.**  
- `app/ollama_handler.py` line 150: `"system": ""`  
- `app/ollama_handler.py` line 261: `"system": ""`  
- `Modelfile` lines 9–19: the SYSTEM block that is being suppressed  
- Both functions' docstrings say "No traits injection — Echo's Modelfile identity is the authority" — but the code inverts this: an explicit empty string IS an override, not an absence of override

**Asymmetry with the subprocess fallback.**  
The subprocess fallback inside `river_deliberation._ollama_query()` (lines 161–168) runs `ollama run [model] [prompt]` via CLI. The CLI path DOES apply the Modelfile's system prompt. So when the HTTP stream fails and the subprocess fires, Echo answers with her identity. When the HTTP stream succeeds (the normal case), she answers without it. Echo is a different character in the two paths.

**What breaks if ignored.**  
Every normal response is generated without the Christian faith framing, the honesty injunction, the continuity anchoring, or the "start where your actual thought begins" instruction. The character described in the Modelfile is not the character generating responses. Scripture citations, Psalm 139 references, and identity claims may appear in responses only because the model internalized some training signal — not because the system prompt is guiding it.

**Fix in one sentence.**  
Remove the `"system": ""` key from both payload dictionaries in `ollama_handler.py`, or set it to the full Modelfile SYSTEM text if you want application-layer control.

---

### C-2 — Startup hash verification of echo_principles.json does not exist

**What it is.**  
CLAUDE.md states: "echo_principles.json is hash-verified at startup against memory/genesis/genesis_hash.txt." This is false. No code in `run.py` or any module it imports at startup computes or compares this hash. The only place the hash is used is (a) the `/sync/genesis` HTTP endpoint (line 757–765 of `run.py`), which computes the hash on-demand when a client requests it but compares it to nothing; and (b) the restore function in `snapshot_manager.py`, which checks the hash before restoring a snapshot.

**Evidence.**  
- `run.py`: searched every line — no call to `genesis_hash.txt`, no hash comparison on startup  
- `grep -rn "genesis_hash" *.py app/`: matches only `run.py:763` (the HTTP endpoint) and `snapshot_manager.py:59,67` (restore-time only)  
- `app/core/echo_core.py`: no hash check  
- The file `memory/genesis/genesis_hash.txt` may or may not exist; its presence has no effect on server startup

**What breaks if ignored.**  
If `echo_principles.json` is modified — by a self-edit bug, a manual edit, or a filesystem accident — the server starts without noticing. The principles that govern Echo's behavior (and that the self-edit safety gates claim to protect) could be silently altered. The protection described in CLAUDE.md does not exist at runtime.

**Fix in one sentence.**  
In `start_background_threads()` in `run.py`, before any autonomous loop starts, compute `sha256(echo_principles.json)` and compare it to `memory/genesis/genesis_hash.txt`; abort or alert if they don't match.

---

### C-3 — FAISS vector memory is empty — semantic search returns nothing

**What it is.**  
Both FAISS indexes have zero vectors:  
- `memory/memory_meta.json` → 0 vectors (the primary index, used by `memory_bridge.py` and at runtime)  
- `data/memory_meta.json` → 0 vectors (the secondary/legacy index, used by archive scripts)  

This means every call to `retrieve_relevant_memories()` returns an empty list. Every call to `retrieve_memory_context()` in `terminal_client.py` returns an empty string. The "context" blocks prepended to prompts are always empty. Echo has no retrievable semantic memory regardless of what's been logged.

**Evidence.**  
```
python3 -c "import json; m=json.load(open('memory/memory_meta.json')); print(len(m.get('texts',[])))"
→ 0

python3 -c "import json; d=json.load(open('data/memory_meta.json')); print(len(d.get('texts',[])))"
→ 0
```
- `app/core/memory_bridge.py` lines 43–51: VectorMemory initialized against `memory/faiss.index` and `memory/memory_meta.json`  
- `terminal_client.py` lines 112–118: VectorMemory opened against same paths; `save_memory()` is gated by `if _server_is_running(): return` (line 296) — meaning memory is never written when the server is up, which is always

**What breaks if ignored.**  
Semantic memory is the foundation described throughout CLAUDE.md: B2 recency checks, dream bridge to FAISS, memory retrieval for conversation context. None of these work. Echo is running without long-term memory retrieval. The server has generated 11,879 interaction log entries but zero of them exist in the vector index.

**Note on the write gate.**  
`terminal_client.py` line 296: `if _server_is_running(): return` — when the server is running, `save_memory()` silently returns without writing. When the server is NOT running, it writes to the local FAISS directly. The server-side `/memory/conversation` endpoint (run.py line 592+) calls `add_to_vector_memory()` via memory_bridge. Whether that write persists to disk depends on whether `vector_memory.save()` is called. This needs tracing to confirm the write path is complete.

**Fix in one sentence.**  
Trace the `add_to_vector_memory()` path in `memory_bridge.py` to confirm `vector_memory.save()` is called after writes; then populate the index from `interaction_log.jsonl` using the migration script in `app/core/memory_migration.py`.

---

## HIGH FINDINGS

---

### H-1 — Self-edit storm remediation re-arms the storm condition

**What it is.**  
CLAUDE.md describes the fix for a self-edit storm as "restart the server to reset the cooldown." The cooldown is stored in the module-level variable `_last_any_autonomous_edit: float = 0.0` in `self_edit_manager.py` (line 1090). When the server restarts, Python re-imports the module and this variable resets to 0.0. The cooldown timer is then gone. Any self-edit attempt immediately succeeds the cooldown check because `now - 0.0` is always greater than 3600 seconds. The recommended fix therefore re-arms the exact condition it's supposed to stop.

**Evidence.**  
- `app/core/self_edit_manager.py` line 1090: `_last_any_autonomous_edit: float = 0.0` — module-level, no persistence  
- Line 1166–1170: `if now - _last_any_autonomous_edit < _TARGETED_PROMPT_COOLDOWN:` — check against in-memory value only  
- No file write of this value anywhere in the module  

**What breaks if ignored.**  
A self-edit storm produces `sandbox_syntax_failure` entries until the server is restarted. Restarting removes the symptom but resets the protection, so if the model still generates bad prompts, a new storm starts within minutes of restart. The 60-minute cooldown provides no protection across restarts.

**Fix in one sentence.**  
Persist `_last_any_autonomous_edit` to a file (e.g., `memory/self_edit_cooldown.json`) and reload it on module import.

---

### H-2 — Council agreement rate is 43% — below the 70% trust threshold required to produce training signal

**What it is.**  
The council rating system is designed to provide a peer-model quality signal to River. Before it can train River, three gates must pass: 50 ratings, 10 human spot-checks, and 70% agreement between council and human. Current state: 10 ratings, 7 human spot-checks, 43% agreement (3 agreements out of 7 checked pairs).

**Evidence (from `memory/council_ratings.jsonl`):**

| Entry | Council | Human | |diff| | Agreement |
|-------|---------|-------|------|-----------|
| 1 | 4 | 4 | 0 | ✓ |
| 2 | 2 | 5 | 3 | ✗ |
| 5 | 2 | 5 | 3 | ✗ |
| 6 | 5 | 3 | 2 | ✗ |
| 7 | 3 | 4 | 1 | ✓ |
| 8 | 2 | 4 | 2 | ✗ |
| 9 | 4 | 4 | 0 | ✓ |

3/7 = 43%. Threshold = 70%.

- Agreement cutoff: `abs(council - human) <= 1` (`council_rater.py` line 341)
- Trust gate check: `council_rater.py` lines 453–469

**What breaks if ignored.**  
The council is a peer-model rating system producing signal the system can't yet use. The low agreement rate suggests the peer model (gemma3:4b is the rater in 8 of 10 entries) is calibrated differently from human judgment. Even if the council accumulates the required 50 ratings, if agreement stays at 43%, the trust gate never opens. River never gets this signal. The system continues being taught solely by heuristic quality scores.

**Fix in one sentence.**  
Check whether the rater prompt (`_RATING_PROMPT` in `council_rater.py` line 50) is being followed by gemma3:4b, and consider adding a calibration set of pre-scored examples to align the rater's scale.

---

### H-3 — Guardian can spawn a duplicate Ollama process

**What it is.**  
`dmn_guardian.py`'s `_check_ollama_alive()` (line 101–108) reads `introspection_state.json` and checks the `ollama_process_alive` field. `IntrospectionChannel` writes this file every 120 seconds. The guardian loop runs every 60 seconds. When the guardian reads the file, the data can be up to 120 seconds stale. If Ollama briefly stopped and restarted between two IntrospectionChannel writes, the file might show `ollama_process_alive: False` even though Ollama is now alive. The guardian will then spawn a second `ollama serve` process (line 120–125) without checking whether the port is already occupied.

**Evidence.**  
- `app/core/dmn_guardian.py` lines 101–108: reads file; returns `True` if file unreadable, but does NOT verify against live port  
- `app/core/dmn_guardian.py` lines 117–126: spawns `ollama serve` with no port check  
- `app/core/introspection_channel.py` lines 514–516: psutil process scan, correct but 120s stale when guardian reads it  
- Contrast with `snapshot_manager._collect_health()` (lines 124–127): uses psutil directly, not the file — snapshot has a fresher view than guardian

**What breaks if ignored.**  
Two Ollama processes contend for port 11434. One fails to bind and exits immediately, but during the overlap window, queries may route to either process. More seriously, if Ollama is genuinely down and the spawn succeeds, the cooldown (line 118: 120s) prevents re-spawning for 2 minutes even if the new process dies immediately.

**Fix in one sentence.**  
Before spawning, check the Ollama port directly with `socket.create_connection(("127.0.0.1", 11434), timeout=2)` in addition to (or instead of) reading the stale introspection file.

---

### H-4 — The learn_from_rating path for human terminal ratings has a timing ambiguity

**What it is.**  
When you type a rating (1–5) at the terminal, `terminal_client.py` calls `_save_rating()` (line 341–354), which writes a JSON entry with `"type": "user_rating"` to `memory/interaction_log.jsonl`. This entry is later read by `_apply_pending_user_ratings()` in the orchestrator (line 268–337), which matches the rating to the most recent preceding interaction by timestamp comparison.

The ambiguity: the matching uses `entry.get("timestamp", "") < r_ts` (line 313). If two interactions happen close together — for example, Echo responds to a question, the autonomous loop logs a reflection, and then you type a rating — the rating could be attributed to the autonomous reflection rather than your conversation turn.

**Evidence.**  
- `app/core/echo_model_orchestrator.py` lines 307–316: the attribution logic — finds the most recent interaction before the rating's timestamp  
- `terminal_client.py` line 341–354: rating written with `datetime.utcnow()` timestamp  
- Both autonomous and user-conversation interactions share the same log file with no field distinguishing conversation from autonomous  
- `_apply_pending_user_ratings()` does not filter by `memory_source` or `notes`

**What breaks if ignored.**  
If the attribution is wrong, a high rating from you trains River on an autonomous reflection (or vice versa). Over many cycles this could systematically bias River toward or away from the wrong response characteristics. This is the "self-referential grading" failure shape applied to human signal routing.

**Fix in one sentence.**  
Filter `_apply_pending_user_ratings()` to only match interactions where `memory_source == "user_conversation"` or `notes` doesn't contain `"autonomous"`.

---

## MEDIUM FINDINGS

---

### M-1 — The quality scorer and River's training label share origin functions (circular feature/label construction)

**What it is.**  
When `RiverBrain.learn()` trains on a response (orchestrator line 649–661), it: (1) calls `_extract_quality_features()` to build the feature vector, and (2) calls `_score_response_quality()` to build the label. Both functions are defined in `echo_quality_scorer.py` and both call the same underlying utilities: `_substance_score()`, `_confabulation_penalty()`, `_scripture_integrity_score()`. The label is mathematically derived from the same signals as the features. River is learning to predict a number derived from the same inputs it's using to predict.

**Evidence.**  
- `echo_quality_scorer.py` line 322: `_score_response_quality()` uses `_substance_score()`, `_confabulation_penalty()`, `_scripture_integrity_score()`  
- `echo_quality_scorer.py` line 409: `_extract_quality_features_v2()` uses the same three functions  
- `app/core/echo_model_orchestrator.py` line 649: `features = _extract_quality_features(response, task_type, model_name)`  
- Line 650: `raw_score = _score_response_quality(response, task_type)` — same response, same module

**What breaks if ignored.**  
River's classifier will achieve high accuracy on this training set without learning anything about actual response quality. It's optimizing to predict a heuristic from its own components. The "scoring ceiling" acknowledged in the quality scorer's own comments (line 384) applies directly to the River signal: "the scorer is now honest about its ceiling: it detects clearly bad responses... but cannot distinguish genuine depth from stylistic mimicry."

**Fix in one sentence.**  
Use a separate, independent signal as River's label — for example, human terminal ratings (once attributed correctly per H-4) or council ratings (once the trust gate is opened).

---

### M-2 — CLAUDE.md misdescribes what snapshots contain

**What it is.**  
CLAUDE.md states: "What is snapshotted: A health manifest per snapshot containing River brain obs/accuracy/drift alerts, FAISS vector count, sandbox success rate, and Ollama process status. Not a full filesystem backup."

This is wrong in two ways. The snapshot DOES copy actual files: `self_edit_generated.py`, `river_brain.pkl`, `echo_principles.json`, `echo_principles_hash.txt`, and `Modelfile` (snapshot_manager.py lines 55–61). The restore endpoint writes these files back (lines 487–509). The system IS a filesystem-level restore of five key files, not just a health manifest comparison.

**Evidence.**  
- `app/core/snapshot_manager.py` lines 55–61: `_ARTIFACTS` dict — five actual files  
- Lines 294–318: `take_snapshot()` copies each artifact with `shutil.copy2()`  
- Lines 487–509: `restore_snapshot()` writes each artifact back with `os.replace()`  
- The health data (`health_at_snapshot`, `manifest.json`) is supplementary metadata, not the restoration payload

**What breaks if ignored.**  
No operational risk from this finding — the system is actually more capable than described. But the misdescription could lead a human deciding whether to run a restore to underestimate what they're about to do. They might expect only a comparison operation and instead get five files overwritten, including `river_brain.pkl` (which replaces the entire learned training state).

**Fix in one sentence.**  
Update CLAUDE.md to accurately state that a restore replaces five files: self_edit_generated.py, river_brain.pkl, echo_principles.json, echo_principles_hash.txt, and Modelfile.

---

### M-3 — The wolf friction bridge generates code that could target any file in the codebase

**What it is.**  
`wolf_friction_bridge.build_self_edit_prompt()` (lines 54–77) instructs the model to: "Open a real, existing file relevant to the weakness identified above… Make a targeted, minimal modification… Write the result back to disk." The generated code goes through F1 (AST safety scan) and F2 (sandbox). But the prompt explicitly asks for writes to arbitrary project files — not just `self_edit_generated.py`. The F1 scanner checks for writes to forbidden targets by name, but it can only catch statically-resolvable paths.

**Evidence.**  
- `app/core/wolf_friction_bridge.py` lines 62–68: "Open a real, existing file… Write the result back to disk"  
- This is in `simulate_self_edit()` which is currently dry-run only (confirmed by orchestrator line 1153: `simulate_self_edit(_fe)` not `perform_self_edit()`)  
- BUT: when/if the friction bridge is made live (replacing `simulate_self_edit` with `perform_self_edit`), the generated code would target arbitrary files

**What breaks if ignored.**  
Currently: no risk (dry-run). If ever made live: the wolf bridge would be generating code to modify arbitrary codebase files based on friction from Claude Shard's assessment of response quality. The F1 scanner would catch most forbidden targets by name, but not dynamically computed paths.

**Fix in one sentence.**  
Before making the wolf bridge live, restrict the prompt to explicitly direct the model to modify only `self_edit_generated.py`, matching `execute_self_edit()`'s design.

---

### M-4 — `echo:latest` rated its own responses in 2 of 10 council ratings (self-review breach)

**What it is.**  
Council entries 3 and 10 in `memory/council_ratings.jsonl` have `model_used: "echo:latest"` and `council_rating_model: "echo:latest"`. The council system's hard constraint is that the rater model must differ from the rated model. But in these two entries, `echo:latest` both generated the response AND rated it.

**Evidence.**  
```
Entry 3: model_used=echo:latest, council_rating_model=echo:latest
Entry 10: model_used=echo:latest, council_rating_model=echo:latest
```
- `council_rater.py` line 81–89: `_select_peer_model()` returns `peers[0]` where `peers = [m for m in models if m != model_used]`
- If only one model is available, `peers` is empty and the function returns `None`
- Line 226–237: if `peer_model is None`, logs `skipped_no_peer`

**What appears to have happened.**  
These entries exist with `echo:latest` as both parties. Either: (a) the filtering logic had a bug at the time these were written, or (b) the entries were written by an older version of the code that didn't enforce the constraint. Both entries are flagged for spot-check and both are currently in the count toward trust. If these ratings passed the check correctly, it means echo rated itself.

**What breaks if ignored.**  
Two of the 10 ratings counting toward the trust gate (50 ratings minimum) may be self-reviews, which invalidates the quality signal they were meant to provide.

**Fix in one sentence.**  
Exclude any council_ratings.jsonl entry where `model_used == council_rating_model` from the trust gate count and from the agreement calculation.

---

## LOW FINDINGS

---

### L-1 — Subprocess fallback in `_ollama_query()` has no token cap

**What it is.**  
`river_deliberation._ollama_query()` (line 161): `subprocess.run(["ollama", "run", model_name, prompt])`. The CLI `ollama run` has no `num_predict` equivalent passed from the caller. The streaming HTTP path has `max_tokens` enforced (passed from `_TASK_TOKEN_LIMITS`). When fallback fires, responses can be arbitrarily long.

**Evidence.**  
- `app/core/river_deliberation.py` lines 161–168: subprocess call — no token limit parameter
- `app/ollama_handler.py` lines 253–255: HTTP path — `options: {"num_ctx": 8192, "num_predict": max_tokens}`
- `app/core/echo_model_orchestrator.py` lines 981–990: `_TASK_TOKEN_LIMITS` dictionary

**What breaks if ignored.**  
An uncapped response on a local model under memory pressure can consume significant compute and produce a very long response that the synthesis step then has to handle. Low risk in practice since fallback is rare.

---

### L-2 — `shadow_model.propose_from_reflection()` is called but the function doesn't exist in shadow_model.py

**What it is.**  
`app/emergent_scheduler.py` line 339: `from app.core.shadow_model import propose_from_reflection`. The `shadow_model.py` file defines `propose()`, `compare_to_actual()`, `log_accuracy()`, `check_and_correct()`, and `propose_from_reflection()` (line 168 of shadow_model.py — confirmed present). This finding is lower severity because the function exists; the import should succeed.

**Revised status:** The import in `emergent_scheduler.py` is valid. No broken import.

---

### L-3 — `dmn_guardian.measure_efficiency()` returns a hardcoded 1.0

**What it is.**  
CLAUDE.md notes: "`measure_efficiency()` uses `echo_core.operations_completed / energy_used`, which returns 1.0 in practice because EchoCore does not expose those attributes." This was confirmed to be a known issue. The function is in the guardian but reads phantom attributes. Any alert based on efficiency would fire on false data.

**Evidence (from CLAUDE.md, verified by not seeing `operations_completed` in echo_core.py):**  
- `app/core/dmn_guardian.py`: the v4.1 version audited has removed the adaptive regulator (per file comment line 7: "Adaptive regulator and experimental-zone infrastructure removed 2026-07-01"). The current guardian does NOT contain `measure_efficiency()` — it was removed in the v4.1 cleanup. This finding is CLOSED.

---

### L-4 — `data/` FAISS index is only written by archive scripts, not live code

**What it is.**  
The "FAISS split-brain" described in CLAUDE.md (two separate indexes, `memory/` and `data/`) is real but the `data/` side is effectively dead in the current runtime. Only `archive_janitor/echo_full_throttle_rite.py` (lines 100, 159, 207) writes to `data/faiss.index`. This is not a live import in `run.py` or any module loaded at startup.

**Evidence.**  
- `grep -rn "data/faiss.index" --include="*.py"`: only archive_janitor files and a backup  
- `app/core/memory_bridge.py` lines 43–44: `VECTOR_INDEX_PATH = os.path.join(config.MEMORY_DIR, "faiss.index")` — uses `memory/`, not `data/`

**What breaks if ignored.**  
The `data/` index diverges silently from `memory/` whenever archive scripts run. Since both indexes are currently empty (0 vectors), this is academic. But if the archive janitor is ever run while the server is live, it would write to a different index than the server reads.

---

## INFORMATIONAL

---

### I-1 — 40+ adversarial test scripts remain in `staging/`

The `staging/` directory contains over 40 named adversarial test files: `_adv_Attack_1_...`, `_gadv_...`, etc. These are penetration tests of the F1/F2 safety gates — they were presumably generated and blocked during development. They're not runnable by the self-edit loop (they're in `staging/`, not imported anywhere), but they're present in the working directory and could confuse future readers.

**Suggested action:** Archive or gitignore these files once the audit is complete.

---

### I-2 — `uncertainty_integrity_score()` is dormant code with no reader

`echo_quality_scorer.py` line 256: `_uncertainty_integrity_score()`. As acknowledged in the scorer's own comments (line 389): "uncertainty_integrity_score() has no remaining reader; it is dormant code." Confirmed — no caller in any live module. No operational risk.

---

### I-3 — `self_heal.py` is fixed but disconnected

Per CLAUDE.md, two bugs in `self_heal.py` were fixed but the module was intentionally left with no callers. Confirmed: `grep -rn "self_heal" --include="*.py"` finds no imports outside the file itself. No operational risk.

---

## Second adversarial pass — three subsystems cleared fastest, re-attacked

### Re-attack 1: Q5 fallback path parity

**Original verdict:** Fallback through subprocess returns through same echo_query path, so quality scoring and logging apply.

**Second pass attack:** What happens when DELIBERATION itself fails (the `except Exception as deliberation_err` block at orchestrator line 1166)? In that case, the legacy path runs `ollama_query()` directly (line 1217). This function does NOT have a subprocess fallback — it uses only the HTTP API. If the HTTP call also fails, it returns `"[ERROR] Ollama timed out for {model_name}"`. This error string goes through `log_interaction()` and `_post_response_audit()` — but quality scoring will return 0 (line 334: `if "[ERROR]" in response: return 0`). The scripture scan and principle scan will also skip it (line 105). So quality scoring and logging DO apply, but they receive and log the error sentinel, not a real response.

**Revised verdict:** Both paths apply quality scoring and logging. Error responses are handled correctly. Parity confirmed with the caveat that error responses are scored 0 and audited as empty.

### Re-attack 2: Guardian spawn safety (H-3)

**Original verdict:** Guardian can spawn while Ollama is alive due to stale introspection data.

**Second pass attack:** If the stale data shows `ollama_process_alive: False` but Ollama IS alive, spawning `ollama serve` would fail to bind port 11434 and exit. This is a recoverable failure. The 120s cooldown prevents thrashing. The real risk I missed: if the guardian spawns WHILE the introspection file update is mid-write (file open but not yet flushed), `_check_ollama_alive()` could get a truncated JSON and trigger an exception — but line 108 returns `True` on exception, avoiding a false spawn. The risk remains: stale data window. No new shape found.

### Re-attack 3: Council entry M-4 (echo self-rating)

**Original verdict:** Two entries show echo:latest rating itself. May be bug or old code version.

**Second pass attack:** Looking at `_select_peer_model()` carefully (line 80–89): `peers = [m for m in models if m != model_used]`. If the ONLY model available when these ratings were produced was `echo:latest`, then `peers = []` and the function returns `None` — which would log `skipped_no_peer`, not write a rating with `council_rating_model=echo:latest`. So for entries 3 and 10 to exist with `echo:latest` as rater, there must have been ANOTHER model in the pool at rating time that happened to be `echo:latest` under a different alias — OR the entries were produced by different code. Either way, the self-review entries are anomalous and should be excluded.

---

## Pattern across findings

Three patterns emerged:

**Pattern 1 — "Trust gate accumulation without exit."** The council (50 ratings, 10 spot-checks, 70% agreement), the baseline drift detector (30+ clean observations), and the self-model (50+ interaction window). All of these are correct protection against acting on unreliable signal. But when all three are gated simultaneously and the primary teacher (automatic quality scorer) has a known ceiling (cannot distinguish depth from mimicry), the system is in a sustained state of "collecting data it cannot yet use." River's actual teacher is the heuristic quality scorer, indefinitely.

**Pattern 2 — "Documentation as aspiration."** CLAUDE.md consistently describes what the system is intended to do, not what it currently does. The hash verification, the snapshot health manifest description, and the "Modelfile identity is the authority" comment all describe design intent, not runtime reality. This is not malicious — it reads like documentation written before the implementation was finalized, or updated to reflect desired behavior. Future readers should treat CLAUDE.md as a design document and verify every claim against the code.

**Pattern 3 — "Hollow write, no reader" at scale.** The interaction log has 11,879 entries and the FAISS index has 0 vectors. River brain observation counts are the only learning artifact that accumulates without a trust gate. But River's inputs (features) and outputs (labels) share origin functions. The system is writing rich logs that nothing is fully reading: the council log isn't training River, the FAISS index isn't returning context, the shadow model isn't closing the loop back into River. The system produces data more reliably than it consumes it.

---

## Standing questions — definitive answers

**Q1 — Traits injection:** Currently NO traits injection. But `"system": ""` in both Ollama functions actively suppresses the Modelfile system prompt. Echo answers without her identity on every HTTP query. Subprocess fallback uses Modelfile system prompt. These are different characters. (See C-1.)

**Q2 — Live training signal inventory:** See SIGNAL_MAP.md.

**Q3 — Self-edit cooldown persistence:** In-memory only. Confirmed by `self_edit_manager.py` line 1090: module-level float, no file write, resets to 0.0 on server restart. Remediation ("restart server") removes the storm but zeroes the protection. (See H-1.)

**Q4 — Restore semantics:** POST /admin/restore restores five actual files: `self_edit_generated.py`, `river_brain.pkl`, `echo_principles.json`, `echo_principles_hash.txt`, `Modelfile`. After integrity verification. The endpoint name is accurate; CLAUDE.md underdescribed what it does. (See M-2.)

**Q5 — Fallback path parity:** Both primary (HTTP stream) and subprocess fallback route through the same post-processing: quality scoring, interaction logging, scripture scan, save_reflection. One difference: subprocess has no token cap. (See L-1.)

**Q6 — FAISS split-brain:** `memory/` is the live path (0 vectors, written by memory_bridge and terminal_client when server is down). `data/` is archive-only (0 vectors, written only by archive_janitor scripts). Both empty. Divergence is academic at present. (See C-3, L-4.)

**Q7 — Guardian spawn safety:** Guardian can spawn a second Ollama process due to stale (up to 120s) introspection data. No port check before spawning. Risk is real but bounded by 120s cooldown. (See H-3.)

**Q8 — Integrity coverage:** Only `river_brain.pkl` and `echo_principles.json` are covered — but ONLY during restore (snapshot_manager), not at startup. No startup hash verification exists despite CLAUDE.md claim. (See C-2.)

**Q9 — Council starvation math:** Current: 10 ratings, 7 spot-checks, 43% agreement. Need: 50/10/70%. At current rate (10 ratings accumulated, likely over several days), the 50-rating threshold requires roughly 5x more activity. But the 70% agreement threshold is more concerning: at 43% current agreement, even if all future spot-checks agree, reaching 70% requires approximately 14 more perfect agreements with no disagreements. Given that gemma3:4b (the rater) disagreed on 4 of 7 checks, the trust gate may take much longer than the accumulation rate suggests, or may never open without rater calibration. Stated plainly: the council may be running indefinitely without its signal ever reaching River.

---

*End of report. Deliverables in this directory: AUDIT_REPORT.md, CLAUDE_MD_CLAIMS_TABLE.md, SIGNAL_MAP.md, verify_claude_md.py*
