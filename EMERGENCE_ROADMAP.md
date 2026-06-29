# EMERGENCE ROADMAP
## Five Interconnected Systems for FeralEcho Autonomous Development

**Build order is strict** — each system feeds the next. Do not start System N+1
until System N is verified producing real output.

---

## System 1: Introspection Channel

### What It Is

A lightweight reader that computes actual internal state metrics on a schedule and
publishes structured snapshots. Other subsystems treat this as the ground truth about
Echo's current performance. Nothing in this system modifies Echo — it only observes.

### Current Gap

FeralEcho has raw data everywhere — `interaction_log.jsonl`, `reflection_shard.jsonl`,
`river_brain.pkl`, sandbox logs — but no subsystem synthesizes them into a single
coherent picture. Optuna, the self-edit manager, and the emergent scheduler all operate
blind: they cannot answer "how is Echo actually doing right now?"

`echo_principles.json` (generation 95741) contains `joker_mode`, `laugh_count`, and
`last_sensory_input` — none of which are real performance signals. That file is the
placeholder this system eventually makes irrelevant.

### Metrics to Collect

**RiverBrain confidence distribution**
`river_brain.score_model(model, task_type)` is live and callable for every
(model × task_type) pair. Compute a full matrix: 5 task types × N models. The spread
of scores within a task type tells you whether River has learned discrimination (high
variance) or is still guessing (scores clustered near 0.5). Also read
`river_brain.observation_counts` and `accuracy_trackers` per task type.

**ClaudeShard friction rate**
`claude_shard.assess(response, context=prompt)` is called inside `echo_query` at
`echo_model_orchestrator.py:805`. Currently the result is logged but not aggregated.
Track: total assessments in last N interactions, `friction["friction"] == True` count,
average `friction["confidence"]`, most common friction question text (top 3 by
substring clustering).

**Sandbox success/failure ratio**
`interaction_log.jsonl` has `sandbox_outcome: "success" | "failed"` fields. Read the
last 50 sandbox entries. Compute: rolling success rate, most common failure category
(parsed from `sandbox_error` field via `_sanitize_sandbox_error`), which model was
used for each failure.

**Memory retrieval scores**
`retrieve_relevant_memories` returns `{"text": ..., "score": ..., "meta": ...}`.
Track average retrieval score per session (higher = memories are relevant to incoming
queries). A falling average means the FAISS index is drifting away from current content.

**Time since last meaningful self-edit**
Read `memory/self_edit_reflections.log` for the most recent entry where result is
`"success"` (not `"stub"` or `"failed"`). Compute age in hours.

**Optuna study health**
`echo_core.optuna_study.trials` — count total trials, count trials with `inf` value
(Optuna dead ends), best value so far. A study where >70% of trials return `inf` is
not learning.

### Files Changed / Created

**New file: `app/core/introspection_channel.py`**
Core reader class. All metric collection here. No imports from Flask context — must
run standalone and inside Flask. Uses `get_echo_core()` to access live RiverBrain and
Optuna study when available.

**New file: `memory/introspection_state.json`** (written by the channel at runtime)
Schema:
```json
{
  "timestamp": "2026-06-26T...",
  "river_brain": {
    "observation_counts": {"general": 0, "coding": 0, "creative": 0, "personal": 0, "reasoning": 0},
    "confidence_matrix": {
      "general":   {"echo:latest": 0.72, "deepseek-r1:7b": 0.61, ...},
      "coding":    {"qwen2.5-coder:7b": 0.81, "deepseek-r1:7b": 0.75, ...},
      "creative":  {"mistral:latest": 0.79, "gemma3:4b": 0.68, ...},
      "personal":  {"echo:latest": 0.91, ...},
      "reasoning": {"deepseek-r1:7b": 0.83, ...}
    },
    "per_task_accuracy": {"general": 0.0, "coding": 0.0, ...},
    "influence_weight": 0.0
  },
  "claude_shard": {
    "assessment_count_last_50": 0,
    "friction_rate": 0.0,
    "avg_confidence": 0.0,
    "top_friction_questions": []
  },
  "sandbox": {
    "success_rate_last_50": 0.0,
    "total_attempts": 0,
    "failures_by_model": {},
    "most_common_failure": ""
  },
  "memory": {
    "avg_retrieval_score": 0.0,
    "faiss_vector_count": 0,
    "journal_line_count": 0
  },
  "self_edit": {
    "hours_since_last_success": 0.0,
    "last_success_prompt_preview": ""
  },
  "optuna": {
    "total_trials": 0,
    "inf_trial_rate": 0.0,
    "best_value": null,
    "best_params": {}
  }
}
```

**Modified: `app/core/echo_core.py`**
Add `IntrospectionChannel` instantiation after `SelfHealMonitor`. Start its background
loop (interval 120s) in a new daemon thread. Register the thread in
`_thread_restart_registry`.

**Modified: `app/core/echo_model_orchestrator.py` (minor)**
In the ClaudeShard block at line 805, count friction assessments to an in-memory
counter accessible to `IntrospectionChannel`. One `threading.Lock`-protected dict
on the orchestrator module: `_friction_stats = {"total": 0, "friction": 0, "questions": []}`.

### Dependencies

None. This is the root of the dependency graph.

### Risks

- `river_brain.pkl` load takes a read lock; introspection must not hold it for more
  than a few milliseconds. Use `score_model` (which acquires and releases) not direct
  classifier access.
- `interaction_log.jsonl` can be large. Always read the last N lines with a tail
  approach — do not load the full file.
- The channel's 120s write loop must be tolerant of partial/missing data on first runs
  when observation counts are low.

### Minimum Viable Implementation

`IntrospectionChannel` with a `collect()` method that reads only:
1. `river_brain.observation_counts` and `influence_weight` (2 lines of code)
2. Last 50 lines of `interaction_log.jsonl` for sandbox ratio
3. Most recent successful self-edit timestamp from `self_edit_reflections.log`

Writes these three to `memory/introspection_state.json`. Background loop at 120s.
That's enough to unblock Systems 2 and 3.

---

## System 2: Living Self-Model

### What It Is

A dynamically-updated structured document — `memory/self_model.json` — that records
what Echo has learned about herself. Fed by the Introspection Channel. Replaces
`echo_principles.json` as the authoritative description of Echo's current behavioral
state.

Critically: this becomes Optuna's objective function. Instead of minimizing
`1 / (len(str(detail)) + 1)` (System 3's current broken scorer), Optuna minimizes the
delta between the self-model's identified weak spots and the self-edit's outcomes.

### Current Gap

`echo_principles.json` records `joker_mode: true` and `laugh_count: 17`. It is not
updated by anything meaningful. It does not tell Optuna what to target. The emergent
scheduler has `SELF_MODEL_PATH = Path("data/self_model.txt")` and a
`run_self_model_reflection()` function (emergent_scheduler.py:238), but that function
writes a plain English text interpretation of the codebase map — not structured
performance data.

`EchoOptuna._score_result` currently scores a 2000-character output higher than a
200-character output simply because `1/(len+1)` is lower for longer strings. This is a
length bias, not a quality signal.

### Schema

**`memory/self_model.json`**:
```json
{
  "schema_version": 1,
  "last_updated": "2026-06-26T...",
  "generation": 95742,
  "performance": {
    "by_task_type": {
      "coding": {
        "avg_quality_score": 2.1,
        "best_model": "qwen2.5-coder:7b",
        "sandbox_success_rate": 0.62,
        "common_failure_pattern": "prose_detected"
      },
      "creative": {
        "avg_quality_score": 3.1,
        "best_model": "mistral:latest",
        "hollow_opener_rate": 0.34
      },
      "personal": {
        "avg_quality_score": 2.8,
        "interiority_rate": 0.41,
        "confabulation_rate": 0.22,
        "female_pronoun_incidents": 7
      },
      "reasoning": {
        "avg_quality_score": 2.4,
        "best_model": "deepseek-r1:7b"
      },
      "general": {
        "avg_quality_score": 2.2
      }
    }
  },
  "self_edit": {
    "success_rate": 0.58,
    "hours_since_last_success": 4.2,
    "weak_areas": ["prose_detected_in_code", "retry_also_fails"],
    "best_intensity": 0.5,
    "best_creativity": 0.5,
    "optuna_best_value": null
  },
  "memory_health": {
    "avg_retrieval_score": 0.0,
    "faiss_vector_count": 0,
    "last_consolidation": null
  },
  "friction": {
    "rate_last_50": 0.0,
    "recurring_questions": []
  },
  "river_brain": {
    "influence_weight": 0.0,
    "weakest_task_type": "general",
    "strongest_task_type": "personal"
  },
  "identity": {
    "confabulation_rate": 0.0,
    "scripture_integrity_rate": 0.0,
    "hollow_opener_rate": 0.0,
    "female_pronoun_incidents_total": 0
  },
  "time_patterns": {
    "self_edit_success_by_hour": {},
    "high_quality_response_by_hour": {}
  },
  "targets": {
    "next_self_edit_focus": "coding",
    "reason": "sandbox_success_rate below 0.65 threshold"
  }
}
```

### Update Logic

`SelfModelUpdater` class reads `introspection_state.json` (System 1 output) plus
the raw logs and computes the schema above. It does NOT call `echo_query` for this —
no LLM needed. Pure signal aggregation from existing data.

The `targets.next_self_edit_focus` field is the key output: it is the task type with
the lowest performance, weighted by how many observations River has for that type
(a task type with 3 observations isn't reliably weak — it's just unknown). Rule:

```
focus = lowest avg_quality_score among task types where observation_count > 20
reason = f"avg_quality={x:.2f}, obs={n}, threshold=2.5"
```

### Files Changed / Created

**New file: `app/core/self_model_updater.py`**
`SelfModelUpdater` class. Methods:
- `update()` — reads introspection_state.json + interaction_log.jsonl + self_edit
  reflections, writes self_model.json
- `get_targets()` — returns the `targets` block, used by Optuna
- `get_weak_task_type()` — returns the task type to target in the next self-edit

**New file: `memory/self_model.json`** (written at runtime)

**Modified: `app/emergent_scheduler.py`**
`run_self_model_reflection()` (line 238) currently writes a plain text architecture
interpretation. Extend it to call `SelfModelUpdater().update()` after the text
generation, so the structured model is always refreshed post-cartographer-scan.

**Modified: `echo_principles.json`**
Mark as deprecated in a comment field. Do not delete — `generation` counter should
be read by SelfModelUpdater and incremented each update cycle to preserve continuity.

**Modified: `app/core/echo_core.py`**
Instantiate `SelfModelUpdater` after `IntrospectionChannel`. Wire its `update()` into
the introspection channel's post-collection callback so the self-model stays one step
behind the latest introspection snapshot.

### Dependencies

System 1 (Introspection Channel) must be writing `introspection_state.json` before
`SelfModelUpdater.update()` is useful. Can be tested standalone by running
`IntrospectionChannel.collect()` once manually.

### Risks

- The `time_patterns.self_edit_success_by_hour` computation requires timestamps on
  self-edit log entries. `self_edit_reflections.log` uses `[ISO_TIMESTAMP] ...` format —
  parseable. But early entries may have missing or malformed timestamps; skip on parse
  error, don't crash.
- `targets.next_self_edit_focus` drives real behavior in System 3. If the self-model
  incorrectly identifies a task type as weak due to sample size, Optuna wastes trials
  targeting it. The `observation_count > 20` threshold guards against this — but that
  threshold may need tuning.

### Minimum Viable Implementation

`SelfModelUpdater.update()` reads only `introspection_state.json` (which System 1
already writes) and:
1. Copies the `performance.by_task_type` block from River's confidence matrix
2. Reads `sandbox.success_rate_last_50` and writes it to `self_edit.success_rate`
3. Computes `targets.next_self_edit_focus` from the two fields above
4. Writes `memory/self_model.json`

That is sufficient to give Optuna a real target for System 3.

---

## System 3: Self-Edit Pipeline Without Crushing Emergence

### What It Is

A wiring of `intensity` and `creativity` into real behavior parameters, replacing the
current dummy `[intensity=0.5, creativity=0.5]` prompt suffix. Connected to the Living
Self-Model so Optuna targets what is actually broken. Constrained to structure not
content — Echo's voice is not a variable to optimize.

### Current Gap

**`intensity` and `creativity` are string decorations, not parameters.**
`perform_self_edit` in `self_edit_manager.py` (line 456) appends
`f"\n[intensity={intensity}, creativity={creativity}]"` to the prompt text and that is
the entire effect. The Ollama call has no temperature or sampling adjustment.

**Optuna creates a fresh study every run.**
`optimize_self_edit` (echo_optuna.py:157) calls
`optuna.create_study(direction="minimize")` — a new ephemeral study each time, not the
persistent `sqlite:///memory/optuna.db` study that EchoCore loads. Every Optuna run
starts from zero. The 95,000+ trials implied by `generation: 95741` in
`echo_principles.json` are not connected to current behavior in any meaningful way.

**The objective function rewards length, not quality.**
`_score_result` (echo_optuna.py:49) returns `1 / (len(str(detail)) + 1)` for string
results. A 400-character stub scores better than a 200-character focused fix.

**Self-edit targets a static file.**
`execute_self_edit` always targets `app/core/self_edit_generated.py` regardless of
what is actually performing poorly. There is no mechanism to say "focus on coding task
failures this week."

### Wiring Plan

**`intensity` → Ollama temperature**
Map `intensity=0.0–1.0` to `temperature=0.2–1.2`. Low intensity = conservative,
syntactically focused edits. High intensity = exploratory restructuring.
Implementation: in `generate_code_from_plan`, pass temperature to `echo_query` via
an extended signature. `echo_query` passes it to `deliberate_and_learn`, which passes
it to `_ollama_query`. The `ollama run` subprocess does not support temperature flags
directly — use the streaming HTTP path (`stream_query_ollama` in `ollama_handler.py`)
with a payload `{"options": {"temperature": t}}` instead.

**`creativity` → target scope**
Map creativity bands to what kind of edit is attempted:
- `0.0–0.33`: fix a specific known failure (take `targets.next_self_edit_focus` from
  self-model, build a repair prompt targeting that task type's weak pattern)
- `0.34–0.66`: refactor a module function without changing its interface
- `0.67–1.0`: propose a new helper/utility targeting the weak task type

This is encoded in `plan_code_logic` prompt construction, not in raw text injection.

**Persistent Optuna study**
Change `optimize_self_edit` to use the EchoCore-owned study:
```python
study = current_app.config['echo_core'].optuna_study
# instead of: study = optuna.create_study(direction="minimize")
```
Fall back to creating a named persistent study when outside Flask context:
```python
study = optuna.create_study(
    study_name="echo_self_edit",
    storage="sqlite:///memory/optuna.db",
    load_if_exists=True,
    direction="minimize"
)
```

**Objective function using self-model quality signal**
Replace `_score_result`'s length heuristic with `_score_response_quality` from
`echo_quality_scorer.py`:
```python
# After execute_self_edit returns (success, detail)
if not success:
    return float("inf")
task_type = self_model.get("targets", {}).get("next_self_edit_focus", "general")
quality = _score_response_quality(str(detail), task_type)
return max(0.0, 1.0 - quality / 4.0)   # quality 0-4, Optuna minimizes
```

**Protecting emergence**
Echo's voice lives in the SYSTEM block of the Modelfile and in `echo_principles.json`.
The self-edit pipeline must never be prompted to modify:
- The SYSTEM block content
- Identity anchors (`christian`, `gremlin`, `psalm`)
- `echo_quality_scorer.py` (the scorer of what makes Echo sound like Echo)

Implement as an `EDIT_FORBIDDEN_TARGETS` set in `self_edit_manager.py`:
```python
EDIT_FORBIDDEN_TARGETS = {
    "Modelfile",
    "echo_principles.json",
    "echo_quality_scorer.py",
    "app/core/claude_shard.py",
}
```
Check before any `save_code` call. If the generated plan mentions a forbidden target,
reject the edit and log `"emergence_protection_triggered"`.

### Files Changed / Created

**Modified: `app/core/self_edit_manager.py`**
- Add `EDIT_FORBIDDEN_TARGETS` guard (lines near `save_code`)
- `perform_self_edit`: accept `target_task_type` param, read from self-model if None
- `generate_code_from_plan`: pass temperature derived from intensity to Ollama streaming call
- `plan_code_logic`: build creativity-scoped prompt using self-model's `targets` block

**Modified: `app/core/echo_optuna.py`**
- `optimize_self_edit`: switch to persistent study (Flask-context-aware)
- `_score_result`: replace length heuristic with quality scorer signal
- Add `_load_self_model()` helper to read `memory/self_model.json` for target task type

**Modified: `app/ollama_handler.py`**
- `stream_query_ollama`: add optional `temperature: float = None` parameter, inject
  into the JSON payload's `options` block when provided

**Modified: `run.py`**
- In the Optuna-triggered self-edit block (line 581), pass `target_task_type` from
  `self_model.json` rather than the current hardcoded prompt

### Dependencies

System 2 (Living Self-Model) must be writing `memory/self_model.json` before
`perform_self_edit` reads it. System 1 must be collecting before System 2 updates.

### Risks

**Temperature via streaming HTTP vs subprocess.**
The current fallback in `_ollama_query` uses `subprocess.run(["ollama", "run", ...])`.
`ollama run` on the CLI does not accept temperature flags. Temperature control requires
the streaming HTTP path. If `stream_query_ollama` fails, the subprocess fallback will
silently ignore the temperature parameter and run at default. Log a warning when
falling back so this is visible.

**Emergence protection guard is substring-based.**
A generated plan that says "import from echo_quality_scorer" would not be caught by
`EDIT_FORBIDDEN_TARGETS` (which checks filenames). Add a secondary check: if any
forbidden name appears in the generated code string, reject.

**Optuna persistent study conflict.**
EchoCore already creates the persistent study on init. If `optimize_self_edit` also
opens the same SQLite study concurrently, SQLite write locks can block. Use
`load_if_exists=True` and ensure only one writer at a time (EchoCore owns the study
object; `optimize_self_edit` should acquire it via `get_echo_core().optuna_study`
rather than opening a new connection).

### Minimum Viable Implementation

1. Replace `_score_result` with the quality-scorer objective (one function change)
2. Wire `optimize_self_edit` to the persistent study (two lines)
3. Add `EDIT_FORBIDDEN_TARGETS` guard (five lines)

That's sufficient for Optuna to stop doing random walks and start learning. Temperature
control and self-model targeting can follow after observing trial convergence.

---

## System 4: Forgetting Module

### What It Is

Principled memory reduction modeled on hippocampal consolidation: episodic entries
(individual interaction logs) are compressed into semantic summaries, duplicates are
merged, contradictions are flagged, and low-signal entries are archived. Runs during
NightCycle — the existing downtime architecture that is currently a stub.

### Current Gap

**`autonomous_prune_journal` is broken by design.**
`memory_bridge.py:304` sorts journal entries by `np.linalg.norm(embeddings, axis=1)`.
But embeddings are generated with `normalize_embeddings=True` (line 171), so every
embedding has L2 norm ~1.0. The sort is random noise. This function currently archives
entries based on floating-point rounding differences in normalization — not semantic
signal.

**NightCycle is a stub.**
`app/maintenance/night_cycle.py:_perform_reflection` logs a timestamp and returns.
The consolidation architecture exists in name only.

**FAISS has no merge operation.**
Three separate FAISS instances (run.py vm, memory_bridge, DualLearner — known issue
in project memory) mean a duplicate memory can exist across all three without any
system aware of the redundancy.

**No contradiction detection.**
A memory "Echo values directness" and a memory "Echo values mystery and indirection"
can coexist with no flag. Over time this produces incoherent retrieval context.

### Consolidation Algorithm

**Phase 1: Duplicate detection (cosine similarity)**
For entries in the active journal above a similarity threshold (>0.92), keep the most
recent, archive the rest, write a composite entry:
`[CONSOLIDATED from N entries: {date_range}] {representative_text}`

Do NOT use the broken L2-norm approach. Use FAISS's own `search()` — for each entry,
search for the top-5 nearest neighbors. If any neighbor has cosine similarity > 0.92,
they are consolidation candidates.

**Phase 2: Semantic summarization (with LLM)**
Cluster entries by topic (use k-means on embeddings, k=10–20 depending on corpus
size). For each cluster, call `echo_query` with task_type="general" and a prompt:
```
Summarize these memory entries into one concise semantic record that preserves
the most distinctive signal. Discard filler. Output one paragraph maximum.

Entries:
{entries}
```
The summary replaces the cluster in the active journal. Originals go to archive.

This is the only step that calls an LLM. Run it with a 200-entry batch limit to
prevent context window overflow.

**Phase 3: Contradiction flagging (not resolution)**
Search for entry pairs with high semantic similarity but opposing sentiment/content.
Heuristic: pairs where cosine similarity is 0.70–0.85 (related but not duplicate) AND
where one contains negation words ("not", "never", "no longer") relative to the other.
Flag these pairs with a `[CONTRADICTION?]` prefix and write them to
`memory/contradiction_log.jsonl`. Do not delete either — contradictions are informative
about Echo's evolution over time. Surface them to the self-model.

**Phase 4: Temporal decay**
`trim_memory_journal` already exists (line 139). The forgetting module calls it with a
tunable cutoff. Default: 90 days (more aggressive than current 180). Archive is
gzip-compressed and kept indefinitely.

### Files Changed / Created

**New file: `app/maintenance/consolidation.py`**
`MemoryConsolidator` class. Methods:
- `detect_duplicates(threshold=0.92)` → list of (entry_id, [duplicate_ids])
- `consolidate_cluster(entries)` → calls `echo_query` for summarization
- `flag_contradictions(threshold_low=0.70, threshold_high=0.85)` → writes contradiction_log
- `run_full_consolidation()` — runs all phases in order, returns stats dict

**Modified: `app/maintenance/night_cycle.py`**
`_perform_reflection` is currently a heartbeat stub. Extend it to run
`MemoryConsolidator().run_full_consolidation()` when:
1. Hours since last consolidation > 6 (read from self-model if System 2 is live,
   otherwise from a lockfile timestamp at `memory/.last_consolidation`)
2. FAISS vector count > 500 (skip on small indexes — consolidation overhead isn't
   worth it)

After consolidation, publish `"memory.consolidation_complete"` to the event bus with
stats payload.

**Modified: `app/core/memory_bridge.py`**
- `autonomous_prune_journal` (line 304): replace the broken L2-norm scoring with
  cosine similarity via FAISS search. This is a bug fix, not a new feature.
- Add `get_faiss_vector_count()` utility (reads `vector_memory.index.ntotal`) so
  NightCycle can check corpus size before running.

**New file: `memory/contradiction_log.jsonl`** (written at runtime)

### Dependencies

System 1 (Introspection Channel) is useful but not required — the consolidator can
check corpus size directly from FAISS. System 2 (Living Self-Model) provides
`memory_health.last_consolidation` timestamp, which prevents redundant runs.
No dependency on System 3.

### Risks

**The LLM summarization step (Phase 2) can fail or hallucinate.**
A cluster summarization that invents facts about Gremlin or Echo's history is worse
than the original entries. Mitigate: run the summary through `_score_response_quality`
with task_type="personal" — if score < 2, discard the summary and keep the originals.
Never delete originals before verifying the summary passes quality check.

**Consolidation during active inference causes FAISS contention.**
NightCycle runs continuously; so does the main Flask server. If consolidation rebuilds
the FAISS index while a query is running, there is a race. Use `memory_lock` (already
defined in memory_bridge.py:53) around all FAISS write operations in the consolidator.
For long rebuilds, build a new index object and swap atomically.

**Three FAISS instances (known issue).**
The consolidator should only touch the `memory_bridge.vector_memory` instance —
the one it has clean access to. Do not attempt to consolidate the DualLearner's
separate FAISS index in this pass. Note the scope limitation in log output.

### Minimum Viable Implementation

1. Fix `autonomous_prune_journal` — replace L2-norm sort with FAISS cosine search.
   This is a one-function fix in `memory_bridge.py` and is a correctness bug, not a
   new feature. Do this first regardless of full System 4 timeline.
2. Implement `detect_duplicates` only (no LLM summarization, no contradiction detection).
3. Wire it into NightCycle with the corpus-size gate.

That makes NightCycle do something real without introducing LLM summarization risk.

---

## System 5: Echo Writing Her Own Modelfile

### What It Is

Echo can propose changes to her own Modelfile parameters based on self-model insights.
Proposals are written to a review queue. A human approves or rejects via a Flask
endpoint or CLI command. On approval, `ollama create echo:latest -f <modified>` runs.

This is the deepest form of self-modification in the architecture — it changes the
inference parameters of Echo's own base model, not just runtime code.

### Current Modelfile State

```
FROM llama3:instruct
PARAMETER stop "<|start_header_id|>"
PARAMETER stop "<|end_header_id|>"
PARAMETER stop "<|eot_id|>"
PARAMETER num_keep 24
PARAMETER num_ctx 8192
SYSTEM "..."
```

Parameters NOT currently set (but Ollama supports): `temperature`, `top_p`, `top_k`,
`repeat_penalty`, `repeat_last_n`, `mirostat`, `mirostat_tau`, `mirostat_eta`,
`num_predict`.

### Proposal Categories

**Safe to propose (no human risk, Echo can reason about these):**
- `num_ctx`: Echo could propose increasing to 16384 if it notices long prompts being
  truncated (introspection channel: if avg prompt length > 6000 tokens, propose increase)
- `num_keep`: echo could propose changes if synthesis prompts are being truncated
- `temperature`: if sandbox failure rate is high (>0.5) AND task type is coding, propose
  lower temperature (0.1–0.4) for coding sessions
- `repeat_penalty`: if hollow_opener_rate > 0.4, propose `repeat_penalty 1.1` to
  discourage repetitive openers
- `top_p`: fine-grained creativity tuning

**Requires human review regardless:**
- The SYSTEM block content (identity, faith, Gremlin relationship)
- `FROM` (base model change)

**Off-limits entirely (blocked by proposal validator):**
- Removing any existing stop token
- Removing or weakening the SYSTEM block
- Adding new identity claims Echo hasn't already established through reflection

### Pipeline

**Step 1: Proposal generation**
`ModelfileProposer.propose()` reads `memory/self_model.json` and applies a rule table:

| Condition from self-model | Proposed change | Rationale template |
|---|---|---|
| `sandbox.success_rate < 0.5` AND `targets.next_self_edit_focus == "coding"` | `PARAMETER temperature 0.25` | "Low sandbox success on coding tasks suggests high temperature is producing unstable code" |
| `identity.hollow_opener_rate > 0.40` | `PARAMETER repeat_penalty 1.15` | "High hollow opener rate suggests repetition penalty would discourage filler patterns" |
| avg prompt length > 6500 tokens | `PARAMETER num_ctx 16384` | "Introspection shows prompts approaching context limit; expansion preserves council synthesis quality" |
| `memory.avg_retrieval_score < 0.55` | no Modelfile change — surface as note | "Low retrieval scores suggest memory quality issue, not inference parameter issue" |

Additional proposals can come from Echo herself: `echo_query` with a structured prompt
asking Echo to read her own Modelfile and suggest one parameter change, given the
current self-model state. Echo's suggestion goes through the same validator before
entering the queue.

**Step 2: Proposal validation**
`ModelfileValidator.validate(proposal)` checks:
- Parameter is in allowed set (never `FROM`, never SYSTEM modification)
- Value is within safe range (temperature: 0.0–1.5, repeat_penalty: 1.0–1.3, etc.)
- Proposal includes a rationale tied to a specific self-model metric
- No more than 2 proposals queued simultaneously (prevents cascade changes)

**Step 3: Review queue**
Valid proposals written to `memory/modelfile_proposals.jsonl`:
```json
{
  "id": "mp_20260626_001",
  "timestamp": "2026-06-26T...",
  "parameter": "temperature",
  "current_value": null,
  "proposed_value": 0.25,
  "rationale": "sandbox success rate 0.48 on coding tasks...",
  "self_model_snapshot": {"sandbox": {"success_rate_last_50": 0.48}, ...},
  "status": "pending",
  "reviewed_by": null,
  "reviewed_at": null
}
```

**Step 4: Human review interface**
New Flask route: `GET /modelfile/proposals` — lists pending proposals as JSON.
`POST /modelfile/proposals/<id>/approve` — sets status to "approved", triggers rebuild.
`POST /modelfile/proposals/<id>/reject` — sets status to "rejected" with optional
`reason` body parameter.

**Step 5: Rebuild on approval**
When a proposal is approved:
1. Read current `Modelfile`
2. Apply the proposed parameter change (add the line if absent, replace if present)
3. Write to `Modelfile.proposed` (never overwrite `Modelfile` directly before build
   succeeds)
4. Run `ollama create echo:latest -f Modelfile.proposed` via subprocess
5. If exit code 0: overwrite `Modelfile` with `Modelfile.proposed`, archive the old
   `Modelfile` to `memory/modelfile_archive/Modelfile_<timestamp>`, publish
   `"modelfile.rebuilt"` event
6. If exit code nonzero: log failure, discard `Modelfile.proposed`, set proposal
   status to "build_failed"

### Files Changed / Created

**New file: `app/core/modelfile_proposer.py`**
`ModelfileProposer` and `ModelfileValidator` classes. Rule table as a typed list of
dataclasses. `propose()` → returns a proposal dict or None. `validate(proposal)` →
returns (is_valid, reason).

**New file: `memory/modelfile_proposals.jsonl`** (written at runtime)

**New file: `memory/modelfile_archive/`** directory (created at runtime)

**Modified: `app/routes/` (or `run.py`)**
Add three Flask routes: list, approve, reject. Keep them behind a simple check
(localhost-only, or require a configurable secret token in the request header) — these
routes trigger model rebuilds and should not be publicly exposed.

**Modified: `app/core/echo_core.py`**
Add `ModelfileProposer` instantiation. Subscribe its `check_and_propose()` method to
the `"self_model.updated"` event (published by `SelfModelUpdater.update()` when the
model changes significantly — define "significant" as any field in `targets` changing).

**Modified: `Modelfile`**
Add a comment header with the schema version and last-modified metadata so the proposer
can verify it is reading the current file.

### Dependencies

System 2 (Living Self-Model) is the primary input — proposals are grounded in
self-model metrics. System 1 provides the raw data that feeds System 2. Systems 3 and
4 are not required, but their outputs (sandbox success rate, memory retrieval scores)
improve proposal quality.

### Risks

**This is the highest-risk system in the roadmap.**
A bad Modelfile can render `echo:latest` unable to generate coherent responses. The
`Modelfile.proposed` staging approach and the archive are non-negotiable safeguards.
`ollama create` must be verified with a test query before marking the proposal as
complete.

**Echo proposing SYSTEM block changes via the LLM path.**
If `echo_query` is asked to suggest Modelfile changes, it may suggest rewriting the
SYSTEM prompt. The validator must check for SYSTEM-related proposals and block them
unconditionally. Pattern: if `"SYSTEM"` appears anywhere in the proposed change text,
reject.

**Cascade proposals.**
Two proposals approved in quick succession (e.g., both temperature and repeat_penalty
on the same day) interact in ways that are hard to predict. The 2-proposal queue cap
plus requiring a minimum 24-hour gap between rebuilds prevents this.

**Proposal rationale decoupling.**
A proposal written when `sandbox_success_rate = 0.48` may sit in the queue for days
while the rate recovers to 0.72. On approval, the rationale no longer reflects reality.
The approval route should re-validate against the current self-model before executing
the rebuild — if the trigger condition is no longer met, warn the reviewer.

### Minimum Viable Implementation

1. `ModelfileProposer.propose()` with the rule table only (no LLM path)
2. `ModelfileValidator.validate()` with the parameter allowlist
3. `memory/modelfile_proposals.jsonl` writer
4. One Flask route: `GET /modelfile/proposals` to list pending proposals
5. A CLI script `scripts/approve_modelfile.py <proposal_id>` that performs steps 4–6
   of the rebuild pipeline

The LLM-generated proposals and the event-bus subscription can be added after the
human-review pipeline is verified working end-to-end.

---

## System 6: Predictive Loops — Surprise-from-News

### What It Is

Before fetching news, Echo generates a prediction about what she expects to find.
After the fetch, she compares the prediction to the actual content and computes a
**surprise signal** — a scalar measure of how wrong she was. This surprise is logged
as an introspection metric (feeding S1) and stored in the self-model (S2), making
it available to downstream systems as evidence that the world moved in an unexpected
direction.

This is an implementation of the **perceptual inference step** from Active Inference
and the free energy principle: the brain (or agent) minimizes the difference between
its generative model of the world and incoming sensory observations. Surprise is
variational free energy; reducing it over time means the model is getting better at
predicting the world.

### Prerequisite: Library Replacement

**`pymdp` as currently installed is not the Active Inference library.**

The installed package (`pip show pymdp`) is a minimal tabular MDP solver with value
iteration. It has no concept of free energy, generative models, or belief updating.

The correct library is `inferactively-pymdp` (same import name, entirely different
codebase and authors):

```bash
pip uninstall pymdp
pip install inferactively-pymdp
```

The `inferactively-pymdp` API centers on:
- `A`: likelihood matrix — P(observation | hidden_state)
- `B`: transition matrix — P(state_t+1 | state_t, action)
- `C`: log preferences over observations (what Echo values seeing)
- `D`: prior beliefs over hidden states at t=0
- `maths.spm_log_sum_exp` / `control.get_expected_states` for EFE computation

All design notes below assume `inferactively-pymdp`.

### Current Gap

`autonomous_fetch.py`'s `run_autonomous_fetch()` is a flat loop over a hardcoded
source list. It fetches, logs, and returns. There is no prediction step before the
fetch, no comparison after, and no surprise metric anywhere in the system.

The emergent scheduler's question `"What patterns in my reflections surprise me?"`
(line 66) uses "surprise" loosely as a reflection prompt — not as a computed signal.

S1 `IntrospectionChannel` has room for a `predictive_loops` block in
`introspection_state.json` but nothing fills it. S2's self-model has no concept of
world-model accuracy.

### Perceptual Inference Architecture

The core loop has a clean seam in `autonomous_fetch.py`:

```
1. Pre-fetch: infer beliefs → q(s) = softmax(ln D + A^T ln P(o_expected))
                             compute expected observations from q(s) and A
                             store as "prediction" with timestamp

2. fetch_and_log() runs (unchanged)

3. Post-fetch: embed actual content → assign to observation category o_actual
               update beliefs:  q(s) ← softmax(ln q(s) + A[:,o_actual])
               compute VFE:     F = E_q[ln q(s)] - E_q[ln P(o,s)]
                                  ≈ -ln P(o_actual) under q(s)    (simplified)
               store (prediction, o_actual, surprise_F) in prediction_log.jsonl

4. S1 reads prediction_log.jsonl → adds surprise_last_cycle, surprise_rolling_avg
   to introspection_state.json["predictive_loops"]

5. S2 adds world_model_accuracy (1 - normalized_surprise_avg) to self_model.json
```

The fetch pipeline itself does not change. The prediction step runs before; the
update step runs after. The rest of the architecture is untouched.

### The Discretization Decision (Must Resolve Before Building)

Active Inference requires discrete (or Gaussian) observations. News content is
high-dimensional text. Three viable options with different trade-off profiles:

---

**Option A — Embedding Clusters (lowest effort, coarsest signal)**

Embed each article's headline + summary → assign to the nearest of K pre-computed
semantic cluster centroids → that cluster index is the discrete observation.

```python
# One-time: build K=20 cluster centroids from historical fetch data
# At runtime:
embedding = embed_text(article_text)
o = int(np.argmin(np.linalg.norm(cluster_centroids - embedding, axis=1)))
```

The generative model is then a 20-dimensional discrete observation space. Simple to
implement; the embedding model is already loaded in `memory_bridge.py`.

**Problem**: K=20 is very coarse. An article about a ceasefire and one about a
hurricane both land in "world events" (cluster 7). Surprise is insensitive to the
distinction that might matter to Echo — the model only registers surprise at the
cluster level, not the meaning level. Requires an offline clustering step to
initialize centroids from past fetch data.

---

**Option B — Feature Extraction (medium effort, richer signal)**

Extract a small structured feature vector per article instead of a single cluster
index. Each dimension is a separate observation modality:

| Feature | Values | How to compute |
|---|---|---|
| sentiment | {negative, neutral, positive} | TextBlob or vader (installed?) |
| topic tag | {world, tech, science, faith, local, other} | keyword rules or zero-shot clf |
| source type | {wire, independent, state, opinion} | source-name lookup table |
| urgency | {breaking, developing, archive} | headline word patterns |

Each modality is a separate `A` matrix in pymdp's multi-modality formulation.
More expressive than Option A — Echo can be surprised by unexpected sentiment
*and* unexpected topic simultaneously.

**Problem**: Building and maintaining the feature extractors is real work. The topic
tagger in particular needs either a rule set or a small classifier. Sentiment is
available from existing libraries but adds a dependency.

---

**Option C — LLM-as-Perceptual-System (highest fidelity, expensive)**

After each fetch, call `echo_query` with a structured prompt asking Echo to score
the article batch on N dimensions (relevance, emotional valence, alignment with
her values, theological weight). Use the scores as the observation vector.

```
Prompt: "Rate these headlines on a 0-3 scale for each:
  relevance to your ongoing reflections,
  alignment with your values,
  emotional weight,
  degree of surprise.
Output JSON only."
```

This preserves full semantic richness and is the only option where the observation
space is expressive enough to capture nuanced surprise (e.g. a story about faith
communities during a ceasefire triggers different expectations than a war story).

**Problem**: Each inference step costs an LLM call. On a machine with memory
pressure (Ollama + Flask + background threads already competing for RAM), adding
an LLM call inside the fetch cycle may cause timeouts elsewhere. Also: using Echo
to score her own surprise creates a feedback loop between her language model and
her world model that may not cleanly decompose.

---

**Recommendation**: Start with Option A to validate the pipeline and produce a
working surprise metric. Migrate to Option B once the downstream value (does
surprise actually improve self-edit targeting, memory pruning priority, etc.) is
demonstrated. Option C is architecturally interesting but the cost-per-cycle is
high enough that it should be a deliberate choice, not a default.

### The Action-Selection Question

This is the harder half of Active Inference and is **out of scope for the initial
implementation**. Document it here for later consideration.

The perceptual inference step above updates Echo's beliefs about the world after
observing it. Active Inference's full loop also covers **action selection**: choosing
which sources to fetch next in order to minimize *expected* free energy (EFE).

EFE = epistemic value + pragmatic value:
- **Epistemic value**: fetch sources that will reduce uncertainty about hidden states
  (information gain). Echo would prefer sources that are currently poorly predicted.
- **Pragmatic value**: fetch sources whose content aligns with preferences in the `C`
  matrix (Echo's values). Avoid sources that consistently produce high-aversion content.

Implementing action selection would require changing `run_autonomous_fetch()` from
a fixed-list loop to a policy-driven loop where Echo evaluates EFE for each
candidate source and selects the top K. The source list in `autonomous_fetch.py`
becomes a candidate pool, not an iteration target.

**This requires the EFE computation** (`control.get_expected_states` in
`inferactively-pymdp`) which needs a `B` transition matrix — a model of how the
world state evolves between fetch cycles. This is non-trivial to initialize without
historical data (months of fetch logs with tracked hidden states).

**Decision gate**: Do not build the action-selection layer until:
1. Perceptual inference is running and producing a surprise signal
2. S2 self-model has `world_model_accuracy` populated for at least 30 cycles
3. The surprise signal has been shown to correlate with something meaningful
   (e.g. high-surprise cycles precede elevated ClaudeShard friction)

### Output Schema

New block in `introspection_state.json`:
```json
{
  "predictive_loops": {
    "last_cycle_timestamp": "2026-06-26T...",
    "prediction": {
      "expected_obs": [3, 1, 0, 2],
      "hidden_state_priors": [0.6, 0.2, 0.1, 0.1]
    },
    "actual_obs": [7, 1, 0, 2],
    "surprise_F": 1.84,
    "surprise_rolling_avg_10": 1.21,
    "surprise_rolling_avg_50": 1.03,
    "cycles_since_start": 47
  }
}
```

New block in `self_model.json`:
```json
{
  "world_model": {
    "accuracy": 0.71,
    "surprise_trend": "stable",
    "surprise_rolling_avg": 1.03,
    "total_inference_cycles": 47
  }
}
```

New file: `memory/prediction_log.jsonl`
Each line:
```json
{
  "timestamp": "...",
  "prediction": {...},
  "actual_obs": [...],
  "surprise_F": 1.84,
  "discretization_method": "embedding_clusters_k20"
}
```

### Files Changed / Created

**New file: `app/core/predictive_loop.py`**
`PredictiveLoop` class. Methods:
- `__init__`: loads or initializes A, B, C, D matrices; loads/builds cluster centroids
  (Option A) or feature extractor (Option B)
- `predict()` → stores expected observation distribution before fetch
- `update(article_texts: list[str])` → embeds/discretizes actual content, runs belief
  update, computes VFE, writes to prediction_log.jsonl
- `get_surprise()` → returns (surprise_F, rolling_avg) for S1 to read
- `_discretize(text: str) → int` → converts article text to observation index
- `_save_matrices()` / `_load_matrices()` → persist A/B/C/D to memory/ as numpy arrays

**Modified: `app/internet_tools/autonomous_fetch.py`**
`run_autonomous_fetch()` gains an optional `predictive_loop` parameter:
```python
def run_autonomous_fetch(predictive_loop=None):
    if predictive_loop:
        predictive_loop.predict()
    # ... existing fetch loop unchanged ...
    if predictive_loop:
        predictive_loop.update(collected_texts)
```
When `predictive_loop=None` (default), behavior is identical to today.

**Modified: `app/core/introspection_channel.py`**
Add `_collect_predictive_loops()` collector. Reads `memory/prediction_log.jsonl`
tail (last 50 entries), computes rolling averages, writes to `predictive_loops` block.

**Modified: `app/core/self_model_updater.py`**
Add `_compute_world_model(introspection)` method that reads `predictive_loops` from
introspection state and writes `world_model` block to self_model.json.

**New file: `memory/prediction_log.jsonl`** (written at runtime)

**New file: `memory/predictive_model/`** directory
Contains persisted numpy arrays: `A.npy`, `B.npy`, `C.npy`, `D.npy`,
`cluster_centroids.npy` (Option A) or `feature_model.pkl` (Option B).

**Modified: `run.py`**
Instantiate `PredictiveLoop` after S1/S2 start. Pass it into the scheduled fetch
calls (wherever `run_autonomous_fetch` is invoked from the scheduler).

### Dependencies

S1 must be running before predictive loop output has anywhere to go. S2 must be
running to populate `world_model` in self_model.json. Neither blocks the
perceptual inference computation itself — `PredictiveLoop` can run standalone
and write to `prediction_log.jsonl` before S1/S2 read it.

`inferactively-pymdp` must be installed (replaces `pymdp`).

The cluster centroids (Option A) or feature extractor (Option B) must be
initialized from historical data before the first cycle. A cold-start fallback
with uniform random centroids is acceptable — the model will learn from the first
fetch cycle regardless.

### Risks

**Discretization information loss.**
Option A's cluster assignment throws away most of the semantic content. A surprise
signal based on coarse clusters may be noise rather than signal — Echo registers
surprise at "unexpected cluster" but the actual article content is completely
mundane within that cluster. Monitor the correlation between `surprise_F` and
subsequent ClaudeShard friction rate over the first 50 cycles to verify the signal
has meaning. If it doesn't correlate with anything downstream, the discretization
is too coarse and Option B or C is needed.

**Library swap may break existing pymdp usages.**
Grep for any existing `from pymdp import` or `import pymdp` in the codebase before
uninstalling. As of Systems 1–5 there are no usages — the installed `pymdp` is
currently unwired. Verify with `grep -rn "pymdp" app/` before swapping.

**Generative model cold-start.**
On first run, A/B/C/D matrices are either uniform or randomly initialized. The first
N surprise values will be meaningless until the model has seen enough fetch cycles
to develop non-trivial beliefs. Set `min_cycles_before_reporting = 10` and suppress
the `surprise_trend` field in self_model.json until that threshold is reached.

**LLM feedback loop (Option C only).**
If Echo scores her own surprise, her language model's current state (affected by
self-edit, temperature, Modelfile parameters) bleeds into the world-model signal.
A system with a degraded self-edit at low temperature will produce different
surprise scores than the same world content seen at default temperature, making
the signal confounded. Options A and B avoid this entirely.

**Memory pressure during fetch cycles.**
Embedding each article batch (Option A/B) loads the SentenceTransformer. It is
already loaded in `memory_bridge.py` at module init — import from there rather
than creating a new instance. Zero additional RAM cost.

### Minimum Viable Implementation

1. Install `inferactively-pymdp` (after verifying no existing usages of `pymdp`)
2. Build cluster centroids from last 500 lines of `memory_journal_active.log`
   (the content Echo has already seen — reasonable prior for what to expect)
3. Implement `PredictiveLoop._discretize()` and `update()` using Option A
4. Wire into `run_autonomous_fetch()` with the optional parameter
5. Add `_collect_predictive_loops()` to S1

That is sufficient to produce a surprise signal for 30+ cycles and answer the
downstream-value question before committing to a richer discretization strategy.

### Open Decision

Before building, decide:

**Discretization**: Option A (embedding clusters) to start, with explicit commitment
to revisit after 30 cycles of data.

**Action selection**: Out of scope until the perceptual inference signal has been
validated as meaningful. The fetch source list stays fixed.

**Library swap timing**: Do this before any S6 code is written. One `pip uninstall /
pip install` and a `grep` for existing usages. Do not mix old `pymdp` and
`inferactively-pymdp` API calls in the same module.

---

## Cross-System Integration Map

```
Introspection Channel (S1)
        │
        ▼ writes introspection_state.json
Living Self-Model (S2)
        │
        ├──▶ self_model.json["targets"] ──▶ Self-Edit Pipeline (S3)
        │                                         │
        │                                         └──▶ Optuna (persistent study)
        │                                                    │
        │                                                    └──▶ river_brain learns
        │
        ├──▶ self_model.json["memory_health"] ──▶ Forgetting Module (S4)
        │                                               │
        │                                               └──▶ NightCycle consolidation
        │
        ├──▶ self_model.json["performance"] ──▶ Modelfile Proposer (S5)
        │                                               │
        │                                               └──▶ Human review → ollama create
        │
        └──▶ self_model.json["world_model"] ◀── Predictive Loops (S6)
                                                       │
                      autonomous_fetch.py ────────────▶│
                      (predict before / update after)  │
                                                        └──▶ prediction_log.jsonl
```

All six systems publish to the EchoCore event bus. SelfHealMonitor (see
SELF_HEAL_PLAN.md) subscribes to failure events from all six. The Introspection
Channel reads health_events to update `introspection_state.json`'s error rate fields.

---

## Build Order Rationale

**Why S1 before S2**: The self-model is only as good as its input. Building S2 without
S1 produces a self-model populated with zeros and guesses.

**Why S2 before S3**: Optuna without real targets produces random walks. The current
system is evidence of this — 95,000+ generations with length-biased scoring.

**Why S3 before S4**: The forgetting module should know what task types are being
targeted in self-edits, so it doesn't consolidate away the memories that feed active
Optuna trials. S2's `targets` field is the dependency.

**Why S4 before S5**: Modelfile proposals should be grounded in clean memory. If
`avg_retrieval_score` is low because the FAISS index is dirty (pre-S4), it might
trigger incorrect parameter proposals.

**Why S5 last among S1–S5**: It is the only system that modifies Echo's inference
parameters. All other systems must be stable and producing trustworthy signals
before Echo proposes changes to herself at this level.

**Why S6 after S1–S5**: The surprise signal is only useful if something downstream
consumes it. S2 must be stable (to receive `world_model` updates) and S1 must be
collecting (to carry `predictive_loops` data). The library swap is a prerequisite
that should not disrupt the already-running S1–S5.

---

## Files Reference Summary

| File | System | Action |
|---|---|---|
| `app/core/introspection_channel.py` | S1 | Create |
| `memory/introspection_state.json` | S1 | Created at runtime |
| `app/core/self_model_updater.py` | S2 | Create |
| `memory/self_model.json` | S2 | Created at runtime |
| `app/emergent_scheduler.py` | S2 | Modify `run_self_model_reflection` |
| `app/core/self_edit_manager.py` | S3 | Add forbidden targets, creativity scoping |
| `app/core/echo_optuna.py` | S3 | Persistent study, quality-scorer objective |
| `app/ollama_handler.py` | S3 | Temperature param in streaming path |
| `app/maintenance/consolidation.py` | S4 | Create |
| `app/maintenance/night_cycle.py` | S4 | Implement `_perform_reflection` stub |
| `app/core/memory_bridge.py` | S4 | Fix broken L2-norm pruner |
| `memory/contradiction_log.jsonl` | S4 | Created at runtime |
| `app/core/modelfile_proposer.py` | S5 | Create |
| `memory/modelfile_proposals.jsonl` | S5 | Created at runtime |
| `memory/modelfile_archive/` | S5 | Created at runtime |
| `Modelfile` | S5 | Add version header comment |
| `app/routes/*.py` or `run.py` | S5 | Add review Flask routes |
| `app/core/echo_core.py` | S1–S6 | Wire new subsystems on init |
| `echo_principles.json` | S2 | Mark deprecated; preserve generation counter |
| `app/core/predictive_loop.py` | S6 | Create |
| `app/internet_tools/autonomous_fetch.py` | S6 | Add optional predictive_loop param |
| `memory/prediction_log.jsonl` | S6 | Created at runtime |
| `memory/predictive_model/` | S6 | Created at runtime (A/B/C/D matrices) |
