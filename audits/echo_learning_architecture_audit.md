# Phase 1 — Echo Learning Architecture Audit

Read-only code archaeology, performed via three parallel research passes (each independently
tracing a cluster of related mechanisms through real source, citing exact file:line, not names or
docstrings) plus direct spot-verification of the most consequential and surprising claims before
they were trusted into this document. Every claim below is either (a) directly re-verified by this
session via a live command against the running repository/filesystem, or (b) sourced from one of
the three research passes, whose method (full-file reads, whole-repo greps, call-chain tracing from
a real user-facing entry point down to the actual Ollama HTTP call) is described in each finding.

**Two of the most consequential claims were independently re-verified by this session directly,
not merely trusted from the research pass:**
1. `learn_from_council_rating()`'s pipeline is confirmed dead in the live process — reproduced
   directly: `memory/council_cursor.json` holds `{"position": 33471}`, the real live
   `memory/interaction_log.jsonl` has only 11,548 lines (post-rotation; `interaction_log.jsonl.1.gz`
   confirmed on disk, dated Aug 22), `lines[33471:]` on an 11,548-line list is `[]` (reproduced with a
   direct Python check), and `memory/echo_watchdog.log` shows zero occurrences of `"[Council] Rated"`
   against 26 occurrences of the daemon restarting.
2. `learn_from_rating()` (human 1-5 terminal ratings) genuinely never touches `model_task_stats` —
   confirmed by direct read of `echo_model_orchestrator.py:898-918`: only `scalers`/`classifiers`/
   `observation_counts` are mutated.
3. `ToolManager.get_tool()` has zero real callers anywhere in the repository — confirmed via a direct
   whole-repo grep; the only hit besides its own definition is an unrelated comment in a test file.

---

## Executive summary: the overall shape

Across every mechanism traced, one structural fact recurs: **RiverBrain, and every training-signal
pathway feeding it, never touches the underlying LLM's weights or generation process at all.** Every
real causal effect any of these mechanisms has runs through *selection* (which of ~9-12 pool models
gets consulted, in what proportion of council seats) or *routing* (which task-type label a
conversation gets classified as, which changes token budgets/tool injection/council-vs-single-model
bypass) — never through directly rewriting what a model says. Separately, a small number of
mechanisms **do** inject real, dynamic textual content directly into a live prompt: FAISS memory
retrieval, and `echo_ground_truth.py`'s keyword-gated self-model/curiosity/capability slices. These
two are the only mechanisms in the entire audited surface that put *novel, accumulated, non-code
content* in front of the model before it answers — everything else is either (a) a routing/selection
signal with no content of its own, (b) a fully autonomous, human-review-free *code* deploy pathway
whose reach back into ordinary conversation is confirmed narrow and almost entirely self-referential,
or (c) a confirmed **hollow write** — real, continuous computation that nothing ever reads back into
any behavior-affecting path.

**This has a direct, load-bearing consequence for Phase 4's condition design** (see §7 below): the
only architecturally sound vehicle for Condition C (persistent memory) is the FAISS memory-write/
retrieve pathway; RiverBrain-based Condition E is architecturally inapplicable to a task using
`EchoDirectResponder` (the same clean, single-model Design B path this entire thread's preference-
provenance experiments already established as the non-contaminating baseline), since RiverBrain's
only causal lever is *which models get asked in a multi-model council* — a mechanism this
investigation's own single-model design never invokes.

---

## Mechanism map (INPUT → EXTRACTION → STATE CHANGE → PERSISTENCE → RELOAD → READ PATH → INFLUENCE ON GENERATION)

### 1. Vector memory write/retrieve (`memory_bridge.py`, `vector_memory.py`)

- **Input experience:** any conversational turn (or dream/curiosity/fetch content) passed to
  `add_to_vector_memory()` / `log_interaction()` / `log_dream_bridge()`.
- **Extraction:** a 384-dim sentence embedding (statistical), paired with the raw text + metadata
  dict (symbolic/textual). No model fine-tuning occurs anywhere in this codebase.
- **State change:** a new vector appended to an in-memory `faiss.IndexFlatIP`; a new `{text, meta}`
  entry added to `VectorMemory.meta`, keyed by UUID.
- **Persistence:** `memory/faiss.index` + `memory/memory_meta.json`, rewritten wholesale via atomic
  temp-file + `os.replace()` on **every single write**, unbatched (`vector_memory.py:117`).
- **Reload:** at `VectorMemory.__init__()` — i.e., process-startup time only. `memory_bridge.py`'s
  module-level `vector_memory = VectorMemory(...)` singleton is constructed at import time, so
  `run.py`'s import of `memory_bridge` at server boot triggers a real, working reload — confirmed
  live: `memory/liveness_ledger.json`'s `self_model_drift` check cross-references two independent
  readers of the FAISS count (123,537 vectors) and finds them matching.
- **Read path:** `retrieve_relevant_memories()`, called from **8 confirmed real call sites**, most
  importantly `app/routes_echo_studio.py:60` (`_memory_search_fn`) — the real conversational
  retrieval adapter for Echo Studio's actual `/chat/stream`.
- **Influence on generation:** **Confirmed causal by direct call-chain trace**, not assumed:
  `_memory_search_fn` → `conversation_service.retrieve_memory_context()` →
  `build_context_system_note()` → `system_context` → `echo_query(system=system_context)` →
  `system_parts` → `deliberate_and_learn(system=system_prompt)` → `_ollama_query(..., system=system)`
  → the real, streaming `/api/chat` HTTP call. Fires on **every** real conversational request in both
  "full" and "fast" mode, and mirrored in `terminal_client.py`'s own identical chain. Genuine semantic
  similarity search (cosine, FAISS `IndexFlatIP`) — a new, differently-worded query surfaces
  semantically close content; exact wording is not required.

**This is the single most important mechanism for this investigation's own experimental design**
(see §7) — it is real, causal, keyed by genuine semantic similarity (not exact repeat), and survives
both process restart and new conversations/sessions (with one honest caveat: a second, independent
process such as `terminal_client.py` holds its own in-memory FAISS snapshot from its own startup and
will not see another process's writes until it reloads).

### 2. Memory-write validator gate (`memory_write_validator.py`)

A **gate**, not a content-injection mechanism: decides whether Mechanism 1's write is committed,
quarantined-but-committed (`validation_warning=True`), or blocked outright. Exact-hash duplicate
detection is exact-match only; `DUPLICATE_SIGNAL_FUZZY` uses character-sequence similarity
(`difflib`, 0.92 threshold) — **not semantic** — so paraphrased near-duplicates are not caught by this
specific check (only Mechanism 1's own retrieval is semantic). Confirmed causal to whether a write
happens (`check_empty_or_trivial`/`check_reflection_length` genuinely block), no direct text-
injection path of its own. No continuous liveness check exists for this specific module (a real,
if minor, gap in the project's own ground-truth-verification coverage, distinct from anything this
investigation itself needs to fix).

### 3. Reflection Shard journal (`app/subsystems/reflection_shard.py`) — **confirmed hollow write**

Real, continuously-generated, model-produced text (confirmed live via the `reflection_shard_generation`
liveness check: 15/20 of the last 20 entries are genuinely distinct, non-templated). **But confirmed,
by direct grep, to have no path into any live generation prompt and no path into FAISS/
`retrieve_relevant_memories()`** — `reflection_shard.py` never imports `memory_bridge` or calls
`add_to_vector_memory()`. Its only public read accessors, `EchoCore.recall_reflections()`/
`.observe_reflection()`, have **zero external callers anywhere in the current codebase**. The one
real external consequence is an indirect, content-free one: meta-reflection synthesis publishes a
Global Workspace event with `salience` left at its default `None`, which (per the workspace's own
documented fail-closed rule) never qualifies as `wide_broadcast`, so `echo_ground_truth.py`'s
workspace slice never surfaces it either. **This is a real, previously-uncatalogued instance of the
exact "hollow write, no reader" pattern this project's own CLAUDE.md history (Findings 25/28/35)
repeatedly documents in other subsystems** — not previously called out for this specific module.

### 4. Curiosity engine + question garden (`curiosity_engine.py`, `garden_manager.py`)

A genuine, confirmed-live (255 new questions in the last 7 days per the real `curiosity_engine`
liveness check), closed causal loop: topic-underrepresentation (read from a real WorldModel
distribution fed by fetched-content classification) → a real generation call produces a new question
→ persisted to `data/question_garden.jsonl` (11,561/13,385 entries with real, accumulating lineage
per the `question_garden_lineage` liveness check) → `select_from_garden()`'s weighting (a genuine
function of accumulated `quality_scores`/`resolution_score`/recency) → the selected question drives
a **second** real generation call in `emergent_scheduler.reflect()` → the resulting response is
scored and its score updates the garden's own weights for the *next* selection cycle. This is causal
and self-reinforcing, but it operates entirely within Echo's **autonomous** loop — it is not, by
itself, a mechanism a human-taught fact passes through (see Mechanism 7 for the one place its
accumulated content can reach an ordinary conversation).

### 5. `echo_ground_truth.py` — keyword-gated self-model/curiosity/capability injection

A stateless synthesis layer reading several other files' current content
(`self_model.json`, `introspection_state.json`, `data/question_garden.jsonl`,
`memory/workspace_log.jsonl`, `echo_state.npy`, `COUNCIL.md`, live sensor reads) and rendering it as
system-prompt text, **gated by keyword/regex match against the user's own message**
(`_is_introspective()`/`_SLICE_SIGNALS`). **Confirmed causal by direct trace** — the same
`system_context` chain as Mechanism 1, reaching the real `/api/chat` call on every one of the four
real entry points (`run.py:mirror_echo`, `terminal_client.py`, Echo Studio, `emergent_scheduler.py`'s
autonomous reflection). Unlike Mechanism 1, triggering requires the user's message to match a
recognizable keyword/phrase stem — a genuinely novel phrasing that avoids every listed marker would
not surface any of this content for that turn. **Directly relevant to this investigation**: this is
the mechanism that would surface e.g. `self_model.json`'s state if a test question happened to ask
about Echo's own capabilities — this investigation's micro-world task (Phase 3) deliberately never
triggers any of these keyword sets (no mention of "capabilities," "self-edit," "curiosity garden,"
etc.), so this mechanism is not expected to fire during the actual learning trials, and its firing
would itself be a confound worth flagging if unexpectedly observed.

### 6. `self_model.json` (`self_model_updater.py`)

A periodically-rewritten (130s) dashboard/digest file. **Confirmed dual-path**: read by
`echo_ground_truth.py` (Mechanism 5's chain — real, gated), and read by
`SelfModelUpdater().get_weak_task_type()` inside `self_edit_manager.py` as the **fallback** target-
selector for autonomous self-edit cycles (real, but scoped to the self-edit subsystem, not ordinary
conversation).

### 7. RiverBrain (`echo_model_orchestrator.py`'s `RiverBrain` class)

Four independent training-signal pathways feed a shared per-`(model, task_type)` state:
`learn()` (every real conversation), `learn_from_sandbox_outcome()` (coding-verification outcomes),
`learn_from_rating()` (human 1-5 terminal ratings), `learn_from_council_rating()` (peer-council
blend). **All four update the same `HoeffdingTreeClassifier`/`StandardScaler` pair, which is
confirmed fully hollow** (`predict_one()` is called exactly once in the entire codebase, immediately
inside `learn()` itself, purely to produce a self-referential prequential-accuracy statistic that
itself only feeds a WARNING-tier, non-restorative `[DRIFT-NOTICE]` log line — never a decision).

**Only `model_task_stats`/`score_model()` is genuinely causal**, and only to *council/model
selection* — confirmed to be read by four independent real subsystems (`river_deliberation.py`'s
`_select_council()`, `self_edit_manager.py`'s core-edit review council, `echo_projects.py`'s
generation/review council, `echo_janitor.py`'s advisory council). It never touches response content.

Of the four writers into `model_task_stats`: `learn()` and (plausibly, not directly observed firing
this session) `learn_from_sandbox_outcome()` are confirmed live. **`learn_from_rating()` never
writes `model_task_stats` at all** (confirmed above) — its only effect is on the already-hollow
classifier, making it *currently causally inert* regardless of whether anyone is actively rating.
**`learn_from_council_rating()`'s entire pipeline is confirmed dead in the live process** (stale
line-index cursor vs. a rotated log file — see the executive summary's directly-reproduced evidence)
— a real, previously-uncaught instance of exactly the disease this project's own Liveness Ledger
exists to catch, missed because the existing `council_river_blend` check is a static source-anchor
check (confirms the wiring/gate/math are intact) with no way to ask "has this actually fired
recently" the way the sibling `claude_research` check does.

**`baseline_trusted_since` (RiverBrain drift-trust flag) is genuinely set** (confirmed:
`2026-07-22T13:01:29Z`, with a real, exercised call site at `introspection_channel.py:202`) —
contradicting an older audit's claim of zero call sites; that claim has since become stale, corrected
here directly against current source, not carried forward.

### 8. Self-edit deploy pipeline (`self_edit_manager.py` → `app/core/self_edit_generated.py`)

A real, autonomous, human-review-free file overwrite (`run.py`'s hourly `AutonomousSelfEdit` thread,
`perform_self_edit(dry_run=False)`) — gated by F1 (static AST safety scan)/F2 (kernel sandbox import
test)/F3 (post-write re-scan) **and** a real quality fitness gate (rejects a candidate that doesn't
beat current production), but **none of these constitute human review**. The one human-review path
(`propose_core_edit()`) is structurally separate and never auto-applies (confirmed: never calls
`save_code()`).

**Critically, this deployed file's reach back into ordinary conversation is confirmed narrow, not
general:**
- `apply_to_code` (if deployed): purely recursive — only ever transforms *future self-edit code
  candidates*, confirmed reachable only from the self-edit pipeline itself, never a conversational
  response.
- `ToolManager`'s scan of `app/core` (including `self_edit_generated.py`) registers the deployed
  file's top-level function *names* as literal text inside a "TOOL-LIST" system note for
  tool-aware/coding-signal conversations — **a real, if extremely thin, textual channel** (a name an
  earlier self-edit cycle chose can appear in front of the model in a later, unrelated conversation)
  — but the function itself is **never invoked** (confirmed: `ToolManager.get_tool()` has zero real
  callers anywhere; the actual live tool-execution system, `echo_tool_dispatch.py`, is a separate,
  hardcoded 3-tool system that never touches `ToolManager`).
- No other path exists: nothing merges `self_edit_generated.py`'s content into the Modelfile,
  `echo_principles.json`, or any cross-conversation prompt template.

**Persona/Modelfile mutation is confirmed structurally impossible via any automated path.**
`modelfile_proposer.py` only ever appends a *proposed* Modelfile text to a JSONL log; the "apply"
step its own docstring describes is not implemented as any callable route anywhere (`GET
/api/modelfile/proposal` is read-only; no `POST .../apply` route exists). `Modelfile` is additionally
hard-blocked in `EDIT_FORBIDDEN_TARGETS` as a redundant second guarantee. **A human must manually run
`ollama create` after reading a proposal by hand — there is no code path that changes Echo's
persona/system prompt autonomously.**

### 9. `shadow_model.py` — the real, confirmed chain from Echo's own text to an unreviewed deploy

`propose_from_reflection(response)` — called from `emergent_scheduler.py` with **genuine, real
LLM-generated autonomous reflection text** (not a template) — writes `shadow_self_model.json`'s
`targets.next_self_edit_focus` via a keyword-count heuristic. **`perform_self_edit()` explicitly
checks this field FIRST**, before falling back to `self_model.json`'s weak-task-type signal. This is
the clearest, fully-confirmed end-to-end chain from Echo's own autonomously-generated text to an
autonomous, human-review-free file overwrite anywhere in the audited surface — but it only ever
selects *which file/task-type the next self-edit cycle targets*, not what that cycle's generated code
contains, and (per Mechanism 8) that deployed code's reach back into ordinary conversation is itself
confirmed narrow.

### 10. `task_type_classifier.py` — a genuinely learned, causally-reroute-conversation mechanism

An online `river` BagOfWords+MultinomialNB classifier, persisted to
`memory/task_type_classifier.pkl`, trained only on `is_trustworthy_training_example()`-filtered real
user-conversation turns, trust-gated per class (real, measured confidence/observation-count
thresholds, not decorative). **Confirmed causal**: its prediction is tried *before* the keyword
ladder in `detect_task_type()`, and the resulting task-type label directly drives council
composition, per-task token budgets, tool-list injection gating, and the `DIRECT_ECHO_TASKS`
single-model bypass. This is the one learned-and-persisted mechanism in the entire audited surface
confirmed to reroute *how* a later, unrelated conversation is handled — though it changes routing,
never the content of what gets said.

### 11. `self_edit_outcome_tracker.py` — docstring understates its own real scope

Its own docstring claims "log-only... does not feed self-edit targeting." **Confirmed accurate for
targeting** (that's `shadow_model`/`self_model_updater`'s job) **but confirmed inaccurate as a
blanket scope claim**: `_recent_outcome_note()` reads this tracker's pre/post quality deltas and
appends a real advisory sentence into the next self-edit generation cycle's prompt — a genuine, if
narrow, causal read-path the module's own docstring undersells. Flagged explicitly per this
investigation's own "be skeptical of self-reported scope" discipline.

---

## Consolidated "hollow write, no reader" list

| Mechanism | Real, continuous write? | Confirmed reader that affects behavior? |
|---|---|---|
| `reflection_shard.py`'s `reflection_journal.jsonl` | Yes (live, non-templated model text) | **No — zero external callers of its own accessors, no FAISS path** |
| RiverBrain's `HoeffdingTreeClassifier`/`accuracy_trackers` | Yes (every `learn()` call) | **No — single self-referential reader, feeds only a non-restorative WARNING log line** |
| `learn_from_rating()`'s effect on `model_task_stats` | N/A — never writes it | **N/A — confirmed to never reach the one state that matters** |
| `learn_from_council_rating()` pipeline | **Currently: no** (dead cursor) | Was real when firing (2026-07-22 through 07-26); confirmed non-firing since |
| `dissent_log.jsonl` | Yes (human-invoked) | No behavioral reader — static existence-check + human dashboard only |
| `modelfile_proposer.py`'s proposals | Yes (on-demand, GET-triggered) | No — no apply route exists anywhere |

## Consolidated "genuinely reaches live generation" list

| Mechanism | Reaches conversation content, or only routing/selection? | Requires exact wording? |
|---|---|---|
| FAISS memory retrieval (`retrieve_relevant_memories`) | **Content** — real text injected into system prompt | No — genuine semantic similarity |
| `echo_ground_truth.py` slices | **Content** — real text injected into system prompt | Keyword/regex-gated, not semantic |
| `task_type_classifier.pkl` | Routing only (task-type label → council/budget/bypass) | N/A |
| `model_task_stats`/`score_model()` | Selection only (which models get asked) | N/A |
| ToolManager tool-name listing | Content, but purely cosmetic (names only, never invoked) | N/A |

---

## Direct answer to the mission's two special-focus questions

**Can Echo's own generated text or a conclusion she reaches cause a permanent, code-level or
persona-level change that alters what she says in a later, unrelated conversation, without human
review?**

Persona: **No, confirmed structurally impossible.** Code: **Yes, for the self-edit-generated file
specifically** (`shadow_model.py` → `perform_self_edit()` → autonomous deploy, zero human review at
write time) — **but that deployed file's reach back into later, unrelated conversation is confirmed
narrow and almost entirely self-referential** (recursive `apply_to_code` effects on future self-edit
candidates only; a thin, never-invoked, purely-textual tool-name-listing channel). There is no
confirmed path by which a self-edit deploy changes an ordinary conversation's *content* in any
general way.

**Does `task_type_classifier`'s learned state change which model/response-shape gets produced, or
only an internal routing label?** **Confirmed to change real downstream behavior**, not merely an
inert label — it drives council composition, token budgets, tool-context gating, and the
single-model bypass for later, unrelated conversations.

---

## Consequence for Phase 4's experimental conditions

Given the above, the architecturally sound design for each condition is:

- **Condition A/B/F**: unaffected by any of this — `EchoDirectResponder`/Design B
  (`river_deliberation._ollama_query()`) bypasses RiverBrain, logging, and memory writes entirely
  (already confirmed clean in this thread's prior preference-provenance audits), making it the correct
  low-contamination vehicle for a controlled, session-boundary-testable condition.
- **Condition C (persistent memory)**: the only architecturally real, causal, semantic (not
  exact-wording) persistence mechanism found anywhere in this audit is FAISS memory write/retrieve
  (Mechanism 1). Condition C is implemented as: Formation runs via `EchoDirectResponder` (clean,
  no side effects), then the harness **explicitly and transparently** calls the real
  `add_to_vector_memory()` to persist the formation exchange (making visible and deliberate what the
  full, contaminating `echo_query()`/`log_interaction()` orchestration path would otherwise do
  silently) — then, in a fresh session, calls the real `retrieve_relevant_memories()` to fetch
  whatever it would genuinely surface, threads that into the test call's system context (mirroring
  exactly how `conversation_service.py`/`echo_ground_truth.py` really assemble it), and asks the test
  question via `EchoDirectResponder`.
- **Condition D (retrieval-blocked ablation)**: identical to C, except the retrieval step is skipped
  (an empty result is threaded into the test call instead of a real `retrieve_relevant_memories()`
  call) — isolating whether retrieval itself, not something else, explains any observed persistence.
- **Condition E (RiverBrain ablation/control): architecturally inapplicable to this experimental
  design, not merely unbuilt.** RiverBrain's only confirmed causal lever is *which models get
  consulted in a multi-model council* — a mechanism this investigation's single-model
  `EchoDirectResponder` design never invokes at all (matching this thread's own established,
  deliberate choice to use the clean Design B path throughout). Testing RiverBrain's real effect
  would require the full, multi-model `deliberate_and_learn()` council path — which reopens exactly
  the RiverBrain/logging/sync contamination this thread has consistently avoided in every prior
  experiment. Per the mission's own Stop Conditions ("the proposed test would require changing Echo
  in a way that itself constitutes an uncontrolled intervention"), this condition is reported as
  **N/A, architecturally inapplicable**, not attempted with a weaker substitute.

This reasoning, and the condition implementations built from it, are recorded in
`app/experiments/learning/harness.py` and cross-referenced from
`audits/echo_learning_experiment_spec.md` (Phase 9).
