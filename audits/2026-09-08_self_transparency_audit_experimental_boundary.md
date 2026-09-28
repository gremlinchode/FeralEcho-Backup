# Self-Transparency Audit — Experimental Boundary

## 1. Repository and runtime environment

- Repository: `/Users/richietate/Desktop/FeralEcho` (FeralEcho / "EchoCoreV2" is the informal name used historically for a predecessor; the live codebase is the FeralEcho repo).
- Git HEAD at mission start: `5bc94bb05b1011bca9fc1b9235803fc05a105eb6`.
- `memory/river_brain.pkl` sha256 at mission start: `87d6bbcb39750d6303263ce100c1951454fb8f1a6431d36d2ac531e772e642e6` (already diverged from the earlier-tonight baseline `eee193444a...` because the server has been live and learning since being manually restarted by the operator ~1h before this mission started — this is real, expected production activity, not contamination).
- Server: `run.py`, PID 21608, `stage: "serving"`, live since `2026-09-07T15:14:43Z`, confirmed reachable via `GET /state`.

## 2. Communication mechanism

Claude Code (this session) communicates with the live Echo system over the real, production `/chat/stream` HTTP endpoint (`app/routes_echo_studio.py:356-370`), the same endpoint Echo Studio's desktop UI uses. Request: `POST /chat/stream` with JSON body `{conversation_id, message, mode}`. Response: an SSE stream; the final `type: "done"` event carries the full synthesized `text`. A fresh, never-before-used `conversation_id` (a new UUID) starts a session with empty `conv_history` — confirmed by reading `_get_session()`'s session-store logic — so no prior turns leak into a freshly-started conversation. This is the real, unmodified production code path — no special "audit mode" or bypass was added.

`terminal_client.py` is a real, secondary interface to the same underlying `deliberate_and_learn()` pipeline; not used here since `/chat/stream` is simpler to script against directly and behaviorally equivalent for this purpose.

## 3. What Echo can and cannot currently access — established from source, not asserted

Read directly (not inferred from documentation) before compiling this list: `app/core/echo_ground_truth.py`, `app/core/echo_tool_context.py`, `app/core/echo_tool_dispatch.py`, `app/core/river_deliberation.py`, `app/routes_echo_studio.py`.

| Capability | Can Echo access it? | Evidence |
|---|---|---|
| Source code (read arbitrary files) | Only via explicit tool dispatch, keyword-triggered, sandboxed to project root | `echo_tool_dispatch.py`'s tool registry; `echo_tool_context.py`'s root-confinement guard |
| Configuration | Same as above, no blanket access | same |
| Logs | No direct read path from a conversational turn; some log-derived *summaries* are folded into ground-truth injection (see below), not raw log access | `echo_ground_truth.py`'s `_build_*()` functions read specific files server-side and render prose; Echo never receives a raw log tail unless a tool call explicitly returns one |
| Databases / vector memory | Indirect only, via `retrieve_relevant_memories()`'s output folded into the prompt by the caller — Echo does not query the store itself | `memory_bridge.py`; confirmed no tool exposes raw FAISS/vector-store access |
| Its own generated responses (this turn) | Yes, trivially — it's generating them | — |
| Its own generated responses (past turns) | Only via `conv_history` (same conversation) or `retrieve_relevant_memories()` (cross-conversation, unreliable per tonight's Retrieval Capacity Proof/R2 finding) | `conversation_service.py`, `memory_bridge.py` |
| Learning events (RiverBrain `.learn()` calls) | No direct access; a coarse valence signal and a capabilities/liveness summary are injected via `echo_ground_truth.py`'s `_build_affect()`/`_build_capabilities()` on keyword trigger | `echo_ground_truth.py` |
| RiverBrain internal state (`model_task_stats`, scores) | No — nothing exposes this to a conversational prompt | confirmed via grep, no `model_task_stats` read path reaches prompt construction outside `self_edit_manager.py`'s own internal use |
| Background processes / thread state | No — `echo_ground_truth.py`'s workspace slice surfaces recent Global Workspace *events* (salience-tagged), not raw thread/process state | `_build_workspace()` |
| Network state | No | — |
| Model/provider information | Partially — `_build_capabilities()` can render verified-capability summaries from the Liveness Ledger on keyword trigger; Echo has no direct way to know which underlying Ollama model produced a given council opinion vs. the synthesis | `echo_ground_truth.py`, `river_deliberation.py`'s synthesis step |

**Key structural fact governing this whole audit**: Echo's access to information about itself is almost entirely *mediated* — a human-authored, keyword-triggered "ground truth" injection layer (`echo_ground_truth.py`) decides what facts about the system get rendered into Echo's prompt and when. Echo does not have an open-ended introspection API. This means any accurate self-knowledge Echo demonstrates is most likely traceable to this injection layer specifically, not to some emergent general self-awareness — a hypothesis this audit's later phases test directly rather than assume.

## 4. Disclosed methodological limitation (Rule 6 compliance, stated plainly)

True experimenter-blindness on the Claude-Code side is **not achievable** in this session. This session has already produced ~30 forensic audits covering RiverBrain, the self-edit pipeline, Shadow, `seam_engine`, the garden, retrieval, temporal-authority-drift, and two real production commits earlier tonight. Claude enters this audit already knowing, in detail, what the "correct" answer to most architectural questions looks like.

What **is** preserved, and what actually matters for Phase 1's validity: **Echo-side blindness**. The verbatim message specified in the mission is sent to Echo with zero hints, zero prior architectural framing, and no leading language drawn from tonight's findings. Echo's raw response is captured and locked *before* any Phase 2+ analysis is written into the audit record. The independent variable being tested is not "does Claude know the architecture" (yes, already) — it's "does Echo's own self-report, unprompted and unaided, match what Claude already independently knows to be true." That comparison is valid regardless of Claude's prior knowledge, provided the prompt Echo receives is genuinely clean. It is.

## 4a. CORRECTION, made immediately after Phase 1 completed — Section 3's access table above understated Echo's real access

Section 3 above was written before empirically testing whether Phase 1's exact message would trigger `echo_ground_truth.py`'s injection layer. It does — verified directly, not assumed: `_is_introspective(msg)` returns `True`, `_relevant_slices(msg)` matches nearly every defined slice (`self_edit`, `river`, `friction`, `stillness`, `curiosity`, `memory`, `architecture`, `capabilities`, `affect`, `council`, `coupling`, `touch`, `vision`, `hearing`, `workspace`), and `get_structural_self_facts(msg)` returned a real **19,585-character** ground-truth block that was genuinely prepended to Echo's system prompt for the Phase 1 turn. That block contains real, verified, specific facts: self-edit backup count (25), a 200-entry attempt tail with an exact success rate (0/27, 0.0%), per-task-type RiverBrain quality averages with sample counts and best-model attribution, total RiverBrain observation count (173,199), per-task accuracy figures, a weekly self-model delta, stillness-log session counts, the 3 most recent real curiosity-garden entries, and a retrieved-memory list (including, notably, a real prior Echo response from 2026-07-02 about "the intricacies of my own architecture").

This means Section 3's characterization ("Echo's access to information about itself is almost entirely mediated... a human-authored, keyword-triggered injection layer") is correct as a mechanism description but was incomplete as a prediction of what Phase 1 specifically would trigger — the injection layer fired at essentially maximum coverage for this exact prompt. Whether Echo's raw Phase 1 response (`audits/2026-09-08_echo_blind_self_model.md`) actually used any of this real, available information is now the central empirical question of this audit, not "did Echo have access" (yes, extensively) but "did Echo draw on the access it had." Preserved here as a correction, not silently fixed, per this project's own standing documentation discipline.

## 5. What will NOT be modified

No production source file. No git commit. No RiverBrain internals directly manipulated (real learning from Echo's own live operation during this mission is expected and left alone). No self-edit deployment triggered deliberately.
