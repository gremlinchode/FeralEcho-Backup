# Echo Learning Causal Architecture (P2-CAUSAL-AUTOPSY)

Read-only, no live experiment, no mutation. Every mechanism traced through the mandated sequence:

```
EXP (experience) → OBS (observation/extraction) → STATE (state change) → PERSIST (persistence)
→ RELOAD (reload behavior) → READ (read path) → GEN (generation-path reach) → BEHAVIOR (actual influence)
```

A break anywhere in this chain means everything downstream of the break is inert, regardless of how
real or sophisticated the upstream machinery is. This document marks the exact link that breaks, per
mechanism, where one exists.

---

## 1. FAISS memory write/retrieve (`memory_bridge.py`, `vector_memory.py`)

```
EXP: any conversational turn, dream cycle, curiosity/fetch content
  ↓ OBS: 384-dim sentence embedding + raw text + metadata (textual/statistical, no fine-tuning)
  ↓ STATE: new vector appended to in-memory FAISS index; new {text,meta} entry keyed by UUID
  ↓ PERSIST: memory/faiss.index + memory/memory_meta.json, atomic rewrite EVERY write (confirmed:
             123,567 meta entries this session, up from 123,543 at the last check — live growth)
  ↓ RELOAD: VectorMemory.__init__() at process/import startup — confirmed exercised (fresh count
            cross-checked against liveness-ledger's independent reader)
  ↓ READ: retrieve_relevant_memories(), 10+ real call sites re-confirmed this session
  ↓ GEN: _memory_search_fn → retrieve_memory_context() → build_context_system_note() →
         system_context → echo_query(system=...) → deliberate_and_learn(system=...) →
         _ollama_query(..., system=...) → real /api/chat call — traced fresh, unbroken, this session
  ↓ BEHAVIOR: real text genuinely present in the model's input on every real conversational request
```

**No break in this chain.** This is the single mechanism in the entire codebase confirmed to carry
genuinely new, semantically-retrieved (not exact-wording-dependent) content all the way to a live
generation call. Classification: **B** (persistent information retrieval — the retrieved content is
re-presented verbatim or near-verbatim; this is not the same claim as C, persistent behavioral
learning, since nothing about *how* the model reasons over that content is itself altered).

---

## 2. RiverBrain `learn()` → `model_task_stats` → council/model selection

```
EXP: any real conversational turn scored by _score_response_quality()
  ↓ OBS: 13-dim feature vector (regex/AST heuristics, no LLM judge)
  ↓ STATE: scaler updated, classifier updated, model_task_stats[model][task_type] updated
  ↓ PERSIST: memory/river_brain.pkl, unconditional per-call save path
  ↓ RELOAD: RiverBrain.load() at process init — confirmed exercised at server boot
  ↓ READ: score_model(model, task_type) — 4 real call sites re-confirmed fresh this session
  ↓ GEN: _select_council() (river_deliberation.py:524) is called inside deliberate_and_learn()
         on every real, non-bypass conversation
  ↓ BEHAVIOR: changes WHICH models are consulted / how they're weighted -- never WHAT they say
```

**No break in the write/persist/reload/read chain — but the chain terminates at SELECTION, not
CONTENT.** This is a real, confirmed, restart-durable, session-independent learning signal — but its
downstream effect is entirely about *which model gets asked*, never about the content any model
produces. Classification: **C**, with the explicit caveat that "C" here means persistent behavioral
change in a routing/selection sense, not a change to what any individual model says.

---

## 3. RiverBrain `learn_from_sandbox_outcome()` / `learn_from_rating()` → dead end at the classifier

```
EXP: a coding-verification outcome / a human 1-5 terminal rating
  ↓ OBS: feature vector extraction (real)
  ↓ STATE: scaler + classifier updated; model_task_stats is NOT updated (CORRECTED this session —
           see hollow-writes doc item 3; the prior audit's claim that learn_from_sandbox_outcome()
           updates model_task_stats was checked directly and found inaccurate)
  ↓ PERSIST: memory/river_brain.pkl (classifier/scaler portion)
  ↓ RELOAD: same load path
  ↓ READ: predict_one() — confirmed, fresh, the ONLY call site anywhere in the repo, immediately
          inside learn() itself (a different function), feeding only accuracy_trackers
  ✗ BREAK HERE: accuracy_trackers feeds only a WARNING-tier drift-notice log line, never a decision
  ↓ GEN: none reached
  ↓ BEHAVIOR: none confirmed
```

**Break point: STATE→READ.** The state genuinely changes and persists, but the one thing that reads
it (the classifier's predictions) has no path forward into generation or selection. Classification:
**U** — real computation, confirmed zero behavioral consequence, not confidently "dead" in the sense
of item 4 (nothing is broken here; it was simply never wired to anything that matters).

---

## 4. RiverBrain `learn_from_council_rating()` → confirmed dead

```
EXP: a real peer-council rating, gated on is_council_trusted() (genuinely set: 2026-07-22T00:52:13Z)
  ↓ OBS: council_rater.py's rate_one_entry(), real per-model APPROVE/REJECT-style scoring
  ↓ STATE: would update scaler/classifier/model_task_stats (same as #2) — DESIGN IS SOUND
  ↓ PERSIST: would write memory/river_brain.pkl
✗ BREAK HERE, upstream of STATE: _poll_and_rate() never reaches rate_one_entry() at all
  ↓ Root cause, re-confirmed fresh this session: memory/council_cursor.json position=33471,
    real live interaction_log.jsonl at 11,602 lines (post-rotation), lines[33471:] reproduces to
    length 0, and _poll_and_rate() (council_rater.py:591-592) returns 0 BEFORE _save_cursor()
    (line 625) ever executes -- a self-perpetuating deadlock until the real file naturally regrows
    past the stale cursor.
  ↓ RELOAD/READ/GEN/BEHAVIOR: all unreachable, confirmed by the same root-cause trace
```

**Break point: EXP→OBS, specifically the polling loop's own cursor logic, upstream of any of the
mechanisms that are otherwise sound.** Classification: **C when live, DEAD in the current process** —
this is the one mechanism in the whole audit where the entire downstream chain (state change,
persistence, reload, read, generation-path relevance) is real and would work, and the actual failure
is a single, narrow, freshly-reproduced bug far upstream.

---

## 5. `reflection_shard.py` → confirmed hollow

```
EXP: 300s autonomy tick, or a high-salience Global Workspace event
  ↓ OBS: real, live model generation (confirmed non-templated via the project's own liveness check)
  ↓ STATE: in-memory journal + self-model dict updated
  ↓ PERSIST: memory/reflection_journal.jsonl, real, reloaded correctly at EchoCore init
  ↓ RELOAD: _load_from_disk() at EchoCore init — confirmed real
✗ BREAK HERE: recall_reflections()/observe_reflection() (the only accessors) have ZERO external
  callers anywhere in the codebase (fresh whole-repo grep, this session) -- confirmed, not assumed.
  reflection_shard.py itself never imports memory_bridge or calls add_to_vector_memory (fresh grep).
  ↓ GEN/BEHAVIOR: unreachable
```

**Break point: RELOAD→READ.** Everything up to and including a correct reload is real; nothing reads
the reloaded state back into any decision. Classification: **U** (real accumulation, zero confirmed
behavioral consequence — precisely the "hollow write, no reader" pattern this project's own history
has repeatedly found in other subsystems).

---

## 6. `task_type_classifier.py` → confirmed causal routing change

```
EXP: any real user_conversation-sourced turn passing is_trustworthy_training_example()
  ↓ OBS: BagOfWords feature extraction
  ↓ STATE: learned NB weights updated
  ↓ PERSIST: memory/task_type_classifier.pkl, confirmed mtime Sep 1 this session (recently active)
  ↓ RELOAD: TaskTypeClassifier.load() at process init
  ↓ READ: detect_task_type() -- tried BEFORE the keyword ladder; real call sites re-confirmed fresh:
          run.py:556, self_edit_manager.py:1855, echo_model_orchestrator.py:612
  ↓ GEN: the returned task_type label drives council composition, per-task token budgets,
         tool-list gating, and the DIRECT_ECHO_TASKS single-model bypass
  ↓ BEHAVIOR: real, confirmed reroute of how a LATER, UNRELATED conversation is handled
```

**No break.** This is the one mechanism confirmed to change *routing* for later conversations based
on accumulated, persisted, learned state — but it never changes response *content* directly.
Classification: **C** (routing-level persistent behavioral change).

---

## 7. Self-edit deploy (`self_edit_generated.py`) → confirmed narrow reach

```
EXP: Echo's own autonomously-generated reflection text (via shadow_model.propose_from_reflection())
  ↓ OBS: keyword-count heuristic over real generated text
  ↓ STATE: shadow_self_model.json's targets.next_self_edit_focus
  ↓ PERSIST: real file, read fresh each call
  ↓ RELOAD: N/A (re-read fresh)
  ↓ READ: perform_self_edit() checks this field FIRST -- confirmed fresh
  ↓ GEN (of the deploy pipeline itself): F1/F2/F3 safety gates + a real quality fitness gate,
         ZERO human review -- a full, unreviewed file overwrite of self_edit_generated.py
✗ BREAK HERE, for reach into ORDINARY CONVERSATION specifically: the deployed file's current content
  (re-confirmed by direct cat this session -- HealthMonitor/log_call/generate_and_modify_code/
  get_shortened_code/run_code_generator, no apply_to_code) has exactly two confirmed channels back
  into anything outside itself:
    (a) apply_to_code, IF deployed (currently not) -- purely recursive, only ever transforms
        FUTURE self-edit candidates, never a conversational response
    (b) ToolManager's scan of app/core (run.py:1285, re-confirmed) registers the file's top-level
        function NAMES as literal text in a "TOOL-LIST" system note for coding/reasoning-tagged
        conversations (echo_model_orchestrator.py:1503-1516, re-confirmed) -- but
        ToolManager.get_tool() has ZERO real callers anywhere (re-confirmed fresh, whole-repo grep),
        so the function is NEVER actually invoked. Text only, no execution.
  ↓ BEHAVIOR beyond the self-edit subsystem itself: none confirmed beyond the cosmetic tool-name text
```

**Break point: GEN→BEHAVIOR, specifically for the "ordinary conversation" claim.** The deploy
mechanism itself is real, autonomous, and unreviewed (a genuine, if narrow, C-classification event
for the self-edit subsystem's own future behavior) — but its reach into anything a human would
recognize as "Echo's conversational behavior changed because of a self-edit" is confirmed to
terminate at either a purely recursive loop or an inert text listing. Classification:
**C for the self-edit subsystem itself; effectively A (no confirmed lasting conversational change)
for ordinary conversation.**

---

## 8. Persona/Modelfile mutation → confirmed structurally impossible

```
EXP: any conclusion Echo reaches, any human GET request to the proposal endpoint
  ↓ OBS: modelfile_proposer.py renders a candidate Modelfile
  ↓ STATE: a proposal object
  ↓ PERSIST: memory/modelfile_proposals.jsonl (log only)
✗ BREAK HERE: no code path anywhere applies a proposal to the real Modelfile. No POST/apply route
  exists in run.py. Modelfile is additionally a protected self-edit target as a second, independent
  guarantee.
  ↓ RELOAD/READ/GEN/BEHAVIOR: unreachable by construction
```

**Break point: STATE→PERSIST, in the sense that the only "persistence" that exists is a proposal log,
never the real artifact.** Classification: **N/A** — this is not a partially-working mechanism, it is
confirmed to have no live path at all, by design.

---

## Classification summary

| Mechanism | Class | Break point (if any) |
|---|---|---|
| FAISS memory write/retrieve | B | none |
| RiverBrain `learn()` → `model_task_stats` → selection | C (selection-only) | none in the chain; terminates at selection, not content |
| `learn_from_sandbox_outcome()`/`learn_from_rating()` | U | READ (classifier's prediction has no forward path) |
| `learn_from_council_rating()` | C when live / confirmed DEAD now | EXP→OBS (cursor bug, upstream of otherwise-sound machinery) |
| `reflection_shard.py` journal | U | RELOAD→READ (no external accessor callers) |
| `task_type_classifier.py` | C (routing) | none |
| Self-edit deploy → conversation | C (subsystem-internal) / effectively A (conversational reach) | GEN→BEHAVIOR (narrow, self-referential or cosmetic-only channels) |
| Modelfile/persona mutation | N/A | STATE→PERSIST (no real apply path exists) |
| `curiosity_engine`/`garden_manager` | C (autonomous-loop-internal) | none within its own loop |
| `echo_ground_truth.py` slices | B (gated) | none, but gated on keyword match, not semantic |
| `self_model.json` → `get_weak_task_type()` | C (self-edit-subsystem only) | none within that scope |
