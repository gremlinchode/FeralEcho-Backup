# P3.1-IMPLEMENT-C1 — Implementation Report

**This is an architectural intervention, not an experiment. No claim is made anywhere in this document
that Echo has learned anything. No live model was called. The frozen P3 behavioral experiment protocol
was not run and was not altered.**

## Exact files changed

| File | Type | Change |
|---|---|---|
| `app/core/behavioral_state.py` | **New** | The entire Candidate 1 mechanism: state schema, human-confirmed mutation, deterministic read, provenance/audit logging, backup/rollback. |
| `scripts/verify_behavioral_state.py` | **New** | 49-case test suite proving every required property, including a full re-run of every sibling experiment's own test suite. |
| `app/core/echo_ground_truth.py` | **Modified, additive only** | One new constant comment block, one new `_build_behavioral()` function, one new independent `behavioral_matches` check plus one new dispatch branch inside `get_structural_self_facts()`. Zero existing slice's logic was altered. SHA-256:
`a0805b45d02075276332c7b758610212ba1e14502ba907395df00cf1d706279d` → `6b487e1ce9c61d4f68ea0f85a04df5eeedd54bdad5cdaca26dff60fa3692f4ef`. |
| `scripts/verify_preference_provenance_experiment.py` | Modified, unrelated one-line fix | Same recurring, benign isolation-exclusion-list maintenance pattern already documented several times earlier in this project's history — a new test script (`verify_p3_causal_learning_apparatus.py`, created in the prior P3 design mission) had never been added to this check's exclusion list; fixed identically to every prior occurrence. |

**Nothing else was touched.** `Modelfile`, `memory/task_type_classifier.pkl`,
`app/core/self_edit_manager.py`, `app/core/river_deliberation.py`, `app/core/memory_bridge.py`,
`app/core/echo_core.py`, `app/core/introspection_channel.py`, `app/core/self_model_updater.py`,
`app/subsystems/reflection_shard.py`, `app/core/echo_model_orchestrator.py`, and every file belonging
to P1, P1.2, the Learning Investigation, or P2/P3's own deliverables were not modified.

## Exact causal path, with source-level evidence per edge

```
EXPERIENCE
  → explicit proposed directive
       app/core/behavioral_state.py: propose_and_confirm_directive(trigger_keywords, directive_text,
       provenance, human_confirmed) — the ONLY function that creates new state. No other entry
       point exists.
  → HUMAN APPROVAL
       propose_and_confirm_directive(): "if human_confirmed is not True: raise BehavioralStateError(...)"
       — a literal identity check against the bool True (mirroring the sibling preference-provenance
       package's EchoDirectResponder(acknowledge_live_model_call=True) convention), not merely a
       truthy check. Proven by test: "propose_and_confirm_directive refuses a truthy-but-not-True
       value" (passed `human_confirmed=1`, correctly refused).
  → DERIVED STATE
       propose_and_confirm_directive()'s own signature has exactly four parameters
       (trigger_keywords, directive_text, provenance, human_confirmed) — no parameter for a raw/
       original/verbatim exchange exists to be passed in the first place. Proven by test:
       "the function signature itself has no parameter for the original exchange" (introspected via
       inspect.signature()) and "the original verbatim teaching exchange never appears anywhere in
       the persisted state file" (a real 200-char verbatim exchange string was constructed and
       confirmed absent from the on-disk JSON dump after a real mutation).
  → PERSIST
       behavioral_state._atomic_write_json(): temp-file + os.replace(), the same convention already
       established throughout this codebase. Proven by test: state correctly readable via a fresh
       load_state() call immediately after every mutation.
  → RESTART
       load_state() performs a fresh disk read with no module-level cache. Proven by test: the test
       suite explicitly deletes and re-imports the module (`del bs; importlib.invalidate_caches();
       import app.core.behavioral_state as bs`) between mutation and read, simulating a fresh process,
       and confirms the directive count and content survive intact.
  → DETERMINISTIC READ
       get_matching_directives(): "if any(kw in lowered for kw in directive['trigger_keywords'])" —
       exact lowercased substring match only. Proven by test: 5 repeated identical calls return
       byte-identical results; an unrelated prompt returns zero matches; multiple matching directives
       are returned in deterministic creation order (not similarity-ranked).
  → EXISTING GENERATION SLICE
       app/core/echo_ground_truth.py's get_structural_self_facts(): a new, independent
       `behavioral_matches = behavioral_state.get_matching_directives(prompt)` check, added to
       `slices` when non-empty, dispatched through the SAME sections-list/system_note()-wrapping
       mechanism every other slice already uses (_build_capabilities(), _build_affect(), etc.).
       Proven by test: a real matching prompt's rendered ground-truth block includes the directive
       text; a non-matching, non-introspective prompt returns an unchanged empty string; a purely
       introspective prompt with no directive match never mentions behavioral directives at all,
       and its own pre-existing slice content is unaffected.
  → BEHAVIOR
       The rendered directive text becomes literal system-prompt content via the same
       system_note()-wrapped, disclaimed injection every other ground-truth slice already uses —
       this is where this implementation's causal reach ends. No live model was called to confirm
       the model actually follows the injected directive; that would be a live experiment, explicitly
       out of scope for this mission (NO_EXPERIMENT=1, LIVE_MODEL=0).
```

## State schema

```json
{
  "version": 1,
  "directives": [
    {
      "id": "<uuid4>",
      "trigger_keywords": ["<lowercased keyword>", "..."],
      "directive_text": "<derived, distilled instruction, max 300 chars>",
      "provenance": {"...": "caller-supplied, required, non-empty"},
      "created_at": "<unix timestamp>"
    }
  ]
}
```

Stored at `memory/behavioral_directives.json` — a new, dedicated path, never overlapping with any
existing production file or any sibling experiment's own state root.

## Mutation path

`propose_and_confirm_directive()` (create), `delete_directive()` (remove), `rollback_to_backup()`
(restore). All three require the identical explicit `human_confirmed=True` check and refuse
outright (raising `BehavioralStateError`, never silently no-oping) otherwise. **No autonomous
mutation path exists anywhere in this codebase** — this module is not imported by `run.py`, any
autonomous loop, or the self-edit pipeline (confirmed: `grep -rn "behavioral_state" --include="*.py" .`
finds only `app/core/behavioral_state.py` itself, `app/core/echo_ground_truth.py`'s new read-only
import, and this implementation's own test/audit files — zero autonomous-loop call sites).

## Read path

`get_matching_directives(prompt)` — deterministic, bounded, lowercased substring match. Called from
exactly one place: `echo_ground_truth.py`'s `get_structural_self_facts()`. Every real match is logged;
non-matches are not logged (to avoid unbounded audit-log growth on ordinary prompts that never touch
this mechanism at all).

## Provenance path

Every mutation (`propose_and_confirm`, `delete`, `rollback`) and every real read-match is appended to
`memory/behavioral_directives_audit.jsonl` — a separate file from the state store itself, mirroring
the Dissent Log's own established append-only convention. Read-match entries record a SHA-256 hash of
the prompt, never the prompt text itself (mission requirement: "not silently log conversations into
behavioral state").

## Rollback path

Before every mutation, the current on-disk state (if any) is copied to a timestamped file under
`memory/behavioral_directives_backups/`, pruned to the most recent 10. `rollback_to_backup()` restores
any retained backup, itself requiring the same explicit human confirmation as any other mutation.
`delete_directive()` provides a lighter-weight, single-directive removal path for the common case.

## Tests / results

`scripts/verify_behavioral_state.py`: **49/49 passing.** Covers, with a dedicated test for each:
mutation refusal without human confirmation (both `False` and a truthy-but-not-`True` value); the
raw teaching exchange's absence from persisted state (both content-based and signature-based checks);
persistence across a simulated restart (module re-import + fresh disk read); deterministic lookup
(repeated-call stability, unrelated-input rejection, multi-match creation-order); FAISS and RiverBrain
never consulted (proven by *poisoning* `memory_bridge.retrieve_relevant_memories` and
`RiverBrain.score_model` to raise if called, then confirming a full read/write cycle completes
without either exception firing); provenance surviving restart; rollback (both direct restore and the
lighter delete path, each independently confirmed to require human confirmation); every stated bound
(directive count, keywords-per-directive, directive-text length, non-empty provenance, backup
retention count); the absence of any accidental write from 20 repeated read-only calls (both mtime and
backup-count checked); the `echo_ground_truth.py` integration end-to-end; and a full re-run of every
sibling test suite this project already has, confirming zero regressions.

## Regressions

**None found.** All four sibling test suites pass at their existing counts:
`verify_preference_provenance_experiment.py` 105/105, `verify_choice_parser_benchmark.py` 58/58 (+1
documented exemption, unchanged), `verify_learning_investigation_harness.py` 58/58,
`verify_p3_causal_learning_apparatus.py` 35/35. One benign, expected, already-precedented maintenance
fix was required (the isolation-exclusion-list gap, see "Exact files changed" above) — not a
regression caused by this implementation, but a pre-existing gap from the prior P3 mission that this
session's own full-suite re-run happened to be the first to surface.

## Remaining confounds (named explicitly, not glossed over)

- **This implementation does not, and cannot, prove the injected directive text actually changes
  model output** — no live call was made under this mission's own constraints. The causal chain
  traced above ends at "the directive becomes literal system-prompt content"; whether a live model
  reliably follows it is an entirely separate, future, explicitly-out-of-scope question.
- **The "is this genuinely different from FAISS-style retrieval" tension named in
  `p3_1_l2_mechanism_design.md` still applies here in full**: this mechanism still works by placing
  *some* text in context for a frozen-weight model to read. What is architecturally different — a
  derived, non-verbatim directive; a deterministic, bounded lookup instead of a similarity search; an
  explicit, human-confirmed provenance chain instead of implicit automatic logging — is real and
  verified by the tests above, but this implementation does not resolve, and does not claim to
  resolve, the deeper philosophical question of whether "text read in context" can ever be
  categorically distinct from L1. That question is out of scope for a controlled implementation pass.
- **No mechanism exists yet for reviewing WHETHER a proposed distillation is a faithful, non-
  misleading summary of whatever real experience motivated it** — `provenance` is a free-form dict the
  caller supplies; this implementation does not validate that the `directive_text` is a *correct*
  distillation of anything, only that a human explicitly confirmed the mutation. This is a real,
  named gap for whoever uses this mechanism, not a defect in what was asked to be built.

## Does the implementation match Candidate 1 exactly?

**Yes**, checked point-by-point against `audits/p3_1_l2_mechanism_design.md`'s own description: a
small, bounded (20 directives, 5 keywords each, 300-char directive text), human-readable JSON store;
mutation via a dedicated, narrow, human-confirmation-gated function, never automatic logging; read via
deterministic keyword match, never similarity search; injection through the already-proven
`echo_ground_truth.py` slice mechanism, requiring no new generation/read path; explicit provenance per
mutation; rollback reusing the same small-file-snapshot spirit as `snapshot_manager.py`'s own
established pattern (a fresh, standalone reimplementation, not an import, per this mission's own
constraint against modifying existing memory architecture).

## Git diff / status (final)

```
 M app/core/echo_ground_truth.py
 M scripts/verify_preference_provenance_experiment.py
?? app/core/behavioral_state.py
?? audits/echo0_baseline.json
?? audits/echo0_baseline.md
?? audits/p3_1_c1_implementation.json
?? audits/p3_1_c1_implementation.md
?? scripts/verify_behavioral_state.py
```

(Every other modified/untracked path visible in a full `git status` predates this mission and was
verified untouched by it — see `audits/echo0_baseline.md`'s post-implementation appendix for the exact
production-state hash comparisons.)

## Confirmation: no live model call occurred

**Confirmed.** No file created or modified in this implementation imports or calls
`river_deliberation._ollama_query()`, `EchoDirectResponder`, `stream_query_ollama`, or any other
live-inference path. The test suite's own FAISS/RiverBrain-poisoning tests independently confirm, at
runtime, that this mechanism's real code path touches neither subsystem. Nothing in this session
started, restarted, or signaled the live `run.py` production process (PID 15193, confirmed still
running throughout, per the baseline).

**Stopping per `STOP_AFTER=IMPLEMENTATION+TESTS`.**
