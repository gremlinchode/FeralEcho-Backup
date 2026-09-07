# FeralEcho Forensic Mission: Initial-Generation Influence Audit

## 1. Executive Verdict

**INITIAL-INFLUENCE PATHWAY DEAD-ENDED.**

The specific causal information behind a recurring failure (e.g., the exact
error text "NameError: name 'functools' is not defined") is never captured
into any structured, retrievable record, and even where a partially-relevant
mechanism exists and does fire (the convergence note), it structurally
cannot carry that information. The break is not subtle, contested, or
probabilistic — it is a **structural absence of a read path**, verified
directly against source, at least as strong a form of evidence as the
Architecture A experiment's own null result, and fully consistent with it.

This is not "Architecture A failed to prove learning." This is "the
information Architecture A would need to inject at initial generation
literally has nowhere to come from between one independent self-edit cycle
and the next, for the `functools` failure family specifically."

## 2. Safety Invariants

| Check | Before | After |
|---|---|---|
| `run.py` / watchdog process | not running | not running |
| Port 5000 | unbound | unbound |
| Ollama reachable | yes (`echo:latest` etc. listed) | not re-queried (no model calls made this mission) |
| Git HEAD | `2cf2d95009943797db5ec41fea9b4021634fd5e6` | unchanged |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` | unchanged (not touched) |
| `interaction_log.jsonl` line count | 13,324 | unchanged (read-only access) |
| Production source modified | — | **none** |
| Experiment artifacts created | — | **none** — this mission concluded, on source evidence alone, that a new black-box experiment was not justified (see §10); the only new file is this report |

This mission made **zero model calls** and **zero writes anywhere** — it is a
pure static/historical-data forensic trace, per its own Phase 7 gate.

## 3. Actual Initial-Generation Call Graph

Traced directly from `app/core/self_edit_manager.py` (current source, not
assumed from prior audits — line numbers below are fresh reads):

```text
perform_self_edit(prompt=None, ...)                         [line 2760]
  ↓ (no explicit prompt → build one for a fresh, independent cycle)
  target_task_type = SelfModelUpdater().get_weak_task_type()  [line 2792, empirical signal, primary]
    or shadow_self_model.json fallback                        [line 2800-2808]
    or "coding"                                                [line 2811]
  ↓
  prompt = _build_targeted_prompt(target_task_type, creativity) [line 2813 → def at 2718]
    - base sentence (fixed)
    - Focus: domain_sentence (fixed, keyed by creativity bucket)
    - convergence_sentence  (only if non_convergent_streak>=2 for a keyword-matched family — currently 0 for all 4 families, per Hot Stove audit; ALWAYS empty right now)
    - outcome_sentence (_recent_outcome_note: direction-only quality delta, e.g. "be conservative" — no error text)
  ↓
execute_self_edit(prompt, ...)                                [line 1854]
  ↓
plan_code_logic(prompt, mastery_note, trace_id)                [line 1535]
  plan_prompt = PLAN_OUTPUT_RULES
              + _build_live_self_edit_inventory() + _build_module_inventory()  [module/function inventory, not failure-specific]
              + _build_convergence_note(prompt)     [line 1174 → only fires for 3 keyword-matched families; carries FUNCTION NAMES only, never error text]
              + mastery_block (advise_before_edit(), generic code-quality tips, static, not failure-specific)
              + _recent_experiment_note()            [line 1508 → tail of interaction_log.jsonl, but ONLY task_type=="autonomous_experiment" entries]
              + "Task: {prompt}"
  plan = echo_query(plan_prompt, task_type="coding", trace_id=trace_id)
  ↓
generate_code_from_plan(plan, ...)                             [line 1784]
  code_prompt = CODE_OUTPUT_RULES + current file contents + plan text
  model_name, _ = choose_model(code_prompt, task_type="self_edit_coding")
  code = echo_query(code_prompt, task_type="coding", trace_id=trace_id)
  ↓ (candidate code)
F1 static scan → F2 sandbox test → fitness gate → deploy/reject
```

`echo_query()` (`app/core/echo_model_orchestrator.py:1367`) itself performs
**no memory retrieval of any kind** — confirmed by grep: zero references to
`retrieve_relevant_memories`/`retrieve_memory_context`/`memory_bridge` inside
`echo_model_orchestrator.py`. Whatever context reaches a model call has to be
assembled by the caller (here, `self_edit_manager.py`) before the call.
`task_type="coding"` is not in `river_deliberation.py`'s `DIRECT_ECHO_TASKS`
set (confirmed via grep, line 294 region) — self-edit generation goes
through full multi-councillor deliberation + synthesis, not a single-model
bypass. (This makes downstream-collapse a theoretically live risk layer, but
moot here — see §7.)

**Determinism / state-mutation notes per stage**: `_build_targeted_prompt`
and `plan_code_logic`'s context-assembly are deterministic given current
state (no randomness); `echo_query()` itself is not (real model sampling,
council composition); `generate_code_from_plan` mutates `RiverBrain` state
via `.learn(model_name, "self_edit_coding", code)` (line 1842) — an aggregate
signal, not failure-signature-specific.

## 4. Experience Inventory

| Experience source | Contains relevant `functools` experience? | Reachable during initial generation? | Retrieved? | Prompt-visible? | Consequential? |
|---|---:|---:|---:|---:|---:|
| `memory/SELF_EDIT.log` raw failure text | **Yes** — 76 verbatim occurrences | Technically on disk, yes | **No** — zero call sites reading its raw text anywhere in the initial-gen path (only `backfill_convergence_from_log()` parses `[LOAD_AUDIT]` lines for function names, never error text) | No | No |
| `self_edit_convergence.json` (`all_names_seen`) | No — function names only, never error text | Yes, via `_build_convergence_note()` | Yes, but only for 3 keyword-matched families (`prose_stripping`, `response_shortening`, `quality_scoring`); `functools` bug isn't family-specific | Yes, when it fires | Only nudges "don't reinvent a named function" — carries no causal information about *why* a candidate failed |
| `self_edit_outcome_tracker.py` (quality delta) | No — direction only (`+`/`-`/none) | Yes, via `_recent_outcome_note()` | Yes | Yes | Weak — "be conservative" / "continue in that direction," no specificity |
| `execute_self_edit()`'s local `clean_error`/`retry_prompt` | **Yes**, within one retry | Only within the *same* `execute_self_edit()` call (Hot Stove audit, `self_edit_manager.py:1999-2015`) | N/A across cycles — local variables, never persisted | Only inside that one retry's own prompt | Proven, empirically, to produce **no measurable behavioral difference even when explicitly injected** (Architecture A: 5/6 vs 5/6) |
| `retrieve_relevant_memories()` (general vector memory) | Possibly, if a functools-related memory entry exists | **No — imported but never called anywhere in `self_edit_manager.py`** (confirmed: `grep -n "retrieve_relevant_memories(" app/core/self_edit_manager.py` returns zero hits, despite being imported at line 19) | No | No | No |
| `RiverBrain.model_task_stats["self_edit_coding"]` | No — one aggregate AST-heuristic float per model | Yes, via `choose_model()` | Yes | Indirectly (via model ranking, not prompt text) | Only ever chooses *which model* generates next — cannot make any model avoid a specific bug |
| `interaction_log.jsonl` (`task_type="coding"` entries) | Possibly, in raw response text | Technically on disk | Only for `task_type=="autonomous_experiment"` entries via `_recent_experiment_note()` — `"coding"` entries (where self-edit generations actually land) are never read back | No | No |
| Garden / `harvest_question()` | No — Hot Stove audit already confirmed zero of the 5 real call sites are triggered by ordinary self-edit/sandbox failure | N/A | N/A | N/A | N/A |
| `dissent_log.jsonl` | No — scoped to `propose_core_edit()`'s protected-file council reviews only, unrelated to generation failures | No | No | No | No |

## 5. `functools` Forensic Reconstruction

76 real occurrences, `memory/SELF_EDIT.log`, span **2026-07-15T20:32:09 →
2026-09-01T05:01:24** (~48 days) — not a single burst, genuinely recurring
across independent cycles over time.

Two concrete, directly-read examples, confirming *structural* not *lexical*
recurrence (different specific misuse of the same missing import, in
different candidate files):

```text
2026-07-15T20:32:23 — staging/self_edit_candidate_b87cba8e73a349a6988a1db1b5d9942c.py
  @log_call
   → @functools.wraps(func)
  NameError: name 'functools' is not defined. Did you forget to import 'functools'?

2026-08-02T23:42:38 — staging/self_edit_candidate_380470164090457c921f64b4f30db510.py
  @functools.lru_cache(None)
  NameError: name 'functools' is not defined. Did you forget to import 'functools'?
```

Both prompts read `"Autonomous self-edit targeting 'coding' task
performance..."` — the generic, non-family-specific Focus text, not one of
the three convergence-tracked families. This is consistent with §3/§4: this
failure class sits entirely outside the one existing mechanism
(`_build_convergence_note`) capable of carrying *any* cross-cycle
information, because its keyword gate (`prose`, `shorten`/`length`/
`concise`/`trim`/`truncat`, `quality`/`score`/`eval`) never matches a bug
about a missing stdlib import.

At the time of each of these 76 occurrences, no prior `functools` failure
had been transformed into any durable, retrievable, signature-keyed
artifact — because §4 establishes no such artifact-creation mechanism exists
anywhere in this pipeline. There is nothing to retrieve, so no later
generation could have retrieved it, regardless of whether retrieval
machinery existed (it doesn't, either — see the `retrieve_relevant_memories`
dead-import finding).

## 6. Storage → Retrieval → Exposure → Influence → Consequence Matrix

Scored specifically for the `functools` NameError signature, at the
**initial-generation** boundary (not retry, which Architecture A already
tested):

| Layer | Score | Evidence |
|---|---|---|
| STORAGE | **PARTIAL** | Raw text exists in `SELF_EDIT.log` (unstructured, not signature-keyed); zero structured record with a queryable error-signature field anywhere |
| RETRIEVAL | **FAIL** | No code path in the initial-generation call graph reads `SELF_EDIT.log`'s raw failure text, `interaction_log.jsonl`'s `coding`-tagged entries, or calls `retrieve_relevant_memories()` (imported, never called) |
| EXPOSURE | **FAIL** (consequence of Retrieval failure) | Neither `plan_code_logic()`'s prompt nor `generate_code_from_plan()`'s prompt ever contains the string "functools" or any specific historical error text for a fresh, independent cycle |
| INFLUENCE | **N/A** | Nothing is exposed, so there is nothing whose influence could be measured, at this boundary |
| CONSEQUENCE | **N/A** | Same |

Contrast with the **retry** boundary (already measured empirically by
Architecture A, not re-tested here): STORAGE partial (local var), RETRIEVAL
trivial (same call frame), EXPOSURE yes (injected into retry prompt),
INFLUENCE **measured null** (CONTROL 5/6 = EXPERIENCE 5/6), CONSEQUENCE null.

The two boundaries fail at *different* layers — retry fails at INFLUENCE
(exposure happens, nothing changes), initial-generation fails earlier, at
RETRIEVAL (exposure never happens at all). This is the report's central
finding: Architecture A tested the *later, already-broken-in-a-different-way*
boundary; the *first* break, in causal order, is upstream of that.

## 7. First Causal Break

**Earliest evidence-backed point where prior experience could affect
initial generation but does not:**

```text
failure occurs, real specific error text generated
  (SELF_EDIT.log's F2-sandbox traceback capture — this part works)
      ↓
diagnosis exists in this form: raw traceback text, sanitized by
  _sanitize_sandbox_error() (self_edit_manager.py:1427) — but only
  ever consumed within the SAME execute_self_edit() call's own retry
      ↓
██ BREAK ██  nothing converts this into a structured, signature-keyed,
             cross-cycle-retrievable record. No code writes such a record.
             No code reads SELF_EDIT.log's raw text for this purpose.
             retrieve_relevant_memories() is imported but never called
             in this file.
      ↓
later, independent perform_self_edit() cycle
  → _build_targeted_prompt() / plan_code_logic() / generate_code_from_plan()
  → none of these three functions' prompt-assembly can possibly contain
    the functools-specific information, because nothing supplies it to them
```

This is ranked #1 (most confident, most evidence) because it is not inferred
from output behavior — it is a direct, positive absence-of-code-path
finding: `grep -n "retrieve_relevant_memories(" app/core/self_edit_manager.py`
returns **zero matches** despite the function being imported at line 19, and
`_SELF_EDIT_LOG_FILE`'s only reader (`backfill_convergence_from_log`)
extracts function names via a regex (`_LOAD_AUDIT_RE`, line 1206-1208) that
structurally cannot capture error text — it only matches `[LOAD_AUDIT] ...
defines N callables: [...]` lines, a different log line shape entirely from
the traceback lines carrying "NameError: name 'functools'...".

A second-ranked, secondary break exists one layer downstream even if the
first were fixed: `_build_convergence_note()`'s 3-family keyword gate would
still exclude a `functools`-import bug from ever qualifying for the one
mechanism that *does* propagate cross-cycle information — so fixing #1 alone
(adding a way to capture the signature) would still need a second fix (a way
to *route* it into a prompt) to have any effect.

## 8. Existing Mechanisms — Liveness Standard

| Mechanism | Defined? | Called (in initial-gen path)? | Data produced? | Data propagated? | Reaches generation? | Can alter generation? |
|---|---|---|---|---|---|---|
| `retrieve_relevant_memories()` | Yes | **No** | — | — | No | No |
| `_build_convergence_note()` | Yes | Yes | Yes (names, 3 families) | Yes | Yes | Weakly, only "don't rename" — irrelevant to `functools` |
| `_recent_outcome_note()` | Yes | Yes | Yes (delta direction) | Yes | Yes | Weakly, generic conservatism nudge only |
| `_recent_experiment_note()` | Yes | Yes | Yes, but only `autonomous_experiment` entries | Yes (for that task_type only) | Yes | No, for `functools` (wrong task_type filter) |
| SELF_EDIT.log raw-text reader | **Not defined at all** | — | — | — | — | — |
| `execute_self_edit()`'s retry `clean_error` | Yes | Only within-call | Yes | **No** (local var) | Only within same retry | Measured: no (Architecture A) |
| `RiverBrain.model_task_stats["self_edit_coding"]` | Yes | Yes | Yes (aggregate float) | Yes | Yes | Only which model, not what bug to avoid |

## 9. If an Experiment Was Justified

**Not run.** See §10.

## 10. Why No Experiment Was Justified

Phase 7 requires determining whether the source trace already justifies a
causal test before running one. It does not, here, for a specific reason:
the finding in §7 is a **structural absence**, not a probabilistic or
contested one. `grep`-confirmed absence of any call site is a stronger,
cheaper, and more certain form of evidence than a black-box behavioral test
could produce — a matched-pair experiment could at best show "no measurable
difference," which is exactly what direct code reading already
demonstrates *and explains the mechanism of*, without the residual
uncertainty (sample noise, model-selection variance, evaluator blind spots)
that any such experiment would carry.

Running a new causal test here would also duplicate, at a *strictly weaker*
evidentiary boundary, what Architecture A's real, already-completed
experiment established for the retry case: that even explicit, verbatim
injection of the causal hypothesis produces no measurable behavioral change
(CONTROL 5/6, EXPERIENCE 5/6, the one EXPERIENCE failure reproducing the
exact injected-against error). If explicit injection at the *easier* retry
boundary already shows zero effect, and the initial-generation boundary
additionally lacks any exposure pathway at all (a strictly harder
precondition to clear), a new experiment could not plausibly find a
*positive* result — it could only confirm the null a second time, at a
boundary where the null is already explained by an absent read path rather
than needing to be inferred from behavior. This satisfies the mission's own
Phase 7 gate ("do not automatically run another experiment... first
determine whether the architecture trace supports one") in the negative
direction and Phase 0/14's "no bottleneck found... must remain a valid
conclusion" framing, applied here as "a specific, evidenced bottleneck was
found by trace, and does not require re-discovery by trial."

## 11. Classification

**RETRIEVAL FAILURE** (primary) — the most precise single label. Storage
exists in unstructured form (raw log text); nothing retrieves it for reuse
in a later, independent initial-generation cycle. `retrieve_relevant_memories()`
being imported-but-never-called in the exact file that would need it is the
clearest single piece of evidence for this classification.

**Secondary, distinct boundary — DECISION-AUTHORITY FAILURE**: even where
something *is* retrieved and reaches the prompt (`_build_convergence_note`'s
function-name list, `_recent_outcome_note`'s delta direction), neither
carries authority over the specific behavior that would need to change
(avoid using a stdlib module without importing it) — they are structurally
incapable of representing that class of information, regardless of whether
retrieval improved.

**Not reached, so not classified here**: GENERATION-INFLUENCE FAILURE and
DOWNSTREAM-COLLAPSE FAILURE both presuppose that exposure happens first.
Exposure does not happen for this signature at this boundary, so these two
layers cannot be evaluated from evidence — noted as genuinely unknown rather
than assumed innocent (self-edit generation does route through full council
deliberation + synthesis for `task_type="coding"`, so a downstream-collapse
risk is structurally *possible* in principle; it simply isn't the
operative failure here, because nothing survives to synthesis to be
collapsed).

**MEMORY FAILURE and CREDIT-ASSIGNMENT FAILURE**: explicitly **not** the
right label here, and worth stating plainly to avoid conflation with the
Hot Stove audit's Classification D (episodic credit assignment). The
*attribution itself* is not the missing piece — `_sanitize_sandbox_error()`
already produces a correct, specific causal string ("NameError: name
'functools' is not defined") at the moment of failure. The problem is purely
that this correct attribution has no path out of the call frame that
produced it.

## 12. Recommendation

**Investigate a different boundary is not needed — the recommendation is to
repair the specifically-identified dead pathway, but only as a future,
separately-authorized decision, not in this mission (Phase 14 forbids it
here).**

Concretely, for whoever authorizes the next step: the minimal repair implied
by this trace is narrower than Architecture A's original design and
addresses the actual break identified in §7 — persist
`_sanitize_sandbox_error()`'s output (already computed, already correct)
into a structured, signature-keyed record at the point of failure (not
retry-scoped), and give `_build_targeted_prompt()` or `plan_code_logic()` a
narrow, signature-matched (not keyword-family-matched) read of that record
before a fresh cycle's Focus text is assembled. This is explicitly a
*design* recommendation for a future mission, not an implementation
performed here.

---

**One sentence**: *The specific causal information behind FeralEcho's
recurring self-edit failures is correctly generated at the moment of
failure and then has no path out of the call frame that generated it — not
because retrieval is weak, but because nothing was ever built to retrieve
it.*
