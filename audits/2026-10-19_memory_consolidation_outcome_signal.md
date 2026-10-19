# Memory consolidation: outcome distinctions are not a retrieval key

Date: 2026-10-19. Read-only. One surface. No production edit, no new experiment root, no model output, no package install.

## Closed branches

The strategy-routing branch and the richer-experience-tail test remain closed. This pass did not retune, extend, replace, or re-run either of them.

Read-only hashes, unchanged from the close of those branches:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `app/experiments/persistent_routing/selector.py` | 5149 | `71f6f04fa522c78c49ea8eddeb67373335d8f6ea6b574c29220f0379fe0c6127` |
| `memory/experiments/persistent_routing/log_E_experience.jsonl` | 5486 | `4f5bb2377035a3ce94a1c21df6aa83e7f000e45a44e32eb296b01fa4968f0241` |
| `memory/experiments/strategy_characterization/stage1/log_stage1.jsonl` | 165572 | `7f9d9533cc05add8171eae632f3c9be7678233c2424ef7810858a64e1b4f826a` |
| `memory/experiments/richer_experience_20261019/log_E_experience_rich.jsonl` | 76571 | `547f17b3da8aecfa2b0e1dbeeba36db23990cf9f0dc0e6181e7e60e33aa7f7be` |
| `audits/2026-10-19_richer_experience_capture.md` | 10612 | `1b66ed539fb856bc6c33bbccbebe776369d55b730d37ea88b6ae2131d81ac71f` |

## Surface

Memory consolidation: retention and retrieval by embedding geometry.

Chosen first. Clear artifacts exist: `memory/consolidation_log.jsonl`, `memory/memory_journal_active.log`, `memory/memory_meta.json`, and the writers below. Self-model accuracy and the Liveness Ledger were not examined.

Live figures below are one stdlib JSON and line scan of those files. No application module was imported.

## Files and functions

- `app/maintenance/consolidation.py` — `ConsolidationRunner._should_run` (55–72), `run` (74–176), `_append_log` (187–192), `_update_self_model` (194–213).
- `app/maintenance/night_cycle.py` — `NightCycle._perform_reflection` (139–159), the only production caller of `ConsolidationRunner.run`.
- `app/core/memory_bridge.py` — `ACTIVE_JOURNAL` (39), `append_to_journal` (148–160), `trim_memory_journal` (178–206), `rebuild_vector_memory` (223–254), `log_interaction` (260–292), `log_dream_bridge` (298–350), `log_memory_edit_bridge` (355–358), `add_to_vector_memory` (364–386), `retrieve_relevant_memories` (410–477), `autonomous_prune_journal` (483–550).
- `app/lib/vector_memory.py` — `VectorMemory.search` (153–179). Returns `(text, inner-product score, meta)`. The index is L2-normalized, so the score is cosine. Search does not filter or rerank on any meta field.
- Readers of that retrieval: `app/core/conversation_service.py` `retrieve_memory_context` (78–177); `app/core/echo_ground_truth.py` `_build_memory` (560–600); `app/core/echo_optuna.py` `EchoOptuna._sample_prompt` (50–78); `app/core/curiosity_engine.py` `_find_existing_match` (88–113); `app/emergent_scheduler.py` `_prompt_recently_reflected` (342–355); `app/internet_tools/autonomous_fetch.py` `_is_duplicate` (134–143); `app/sync/echo_messaging.py` `_memory_search_fn` (538–548); `app/autonomous_awareness.py` `_load_waking_memories` (199–258) and `_sample_diverse_set` (270–293).
- Outcome writers beside this surface: `app/core/self_edit_manager.py` `append_to_journal("SELF_EDIT", ... | result: ...)` at 1988, 2052, 2063, 2187, 2204, 2232, 2279, 2325, 2333, 2358, 2690; `app/autonomous_loop.py` sandbox block (203–218); `app/core/autonomous_loop_with_optuna.py` `_run_sandbox_cycle` (84–98).
- `app/core/self_model_updater.py` `update` (91–138) replaces `memory_health` and sets `last_consolidation` to `None`.

## What non-coarse information is written

The consolidation event itself is coarse. Every one of 2915 rows in `memory/consolidation_log.jsonl` (455837 bytes) has the same six keys: `started_at`, `entries_before`, `entries_after`, `pruned_count`, `faiss_vectors_after`, `error`. Zero rows failed to parse. The skip path in `run` returns before `_append_log`, so a skipped cycle is not in this file. The last row is `2026-10-19T14:26:19.142716+00:00`, with `entries_before` 0, `entries_after` 0, `pruned_count` 0, `faiss_vectors_after` 144500, `error` null.

The store that later retrieval actually ranks does retain non-coarse text. `memory/memory_meta.json` held 144521 items at this read. `empty_meta` was 0. Meta-key counts:

| Key | Items |
|---|---:|
| timestamp | 144489 |
| role | 122766 |
| memory_source | 120805 |
| validation_warning | 21045 |
| type | 17117 |
| prompt | 16560 |
| source | 16560 |
| task_type | 6935 |
| retention | 6935 |
| backfill | 3791 |
| sync_ts | 2456 |
| is_thought_provoking | 1562 |
| migration_ts | 231 |
| migrated_from_legacy_self_model_tag | 212 |
| migrated_from_legacy_backfill_burst | 19 |
| seed_ids | 10 |

A key-name scan for pass, fail, error, outcome, quality, prior, result, tail, strategy, and oracle returned no key. Pass/fail, error type, and prior-attempt result are not fields in this store.

`validation_warning: true` is present on 21045 items. `log_dream_bridge` writes it when the validator blocks a dream (lines 328–341). The docstring says retrieval callers may filter on it. A search of Python sources finds the name only at that write.

Roles that carry a sandbox outcome as text, not as a boolean: `sandbox_run` 316, `sandbox_failure` 1. Sources are dominated by `code_analysis` (60567), `autonomous` (47717), untagged (23716), and `user_conversation` (6948).

Writers that already know an outcome, and what they store:

- `append_to_journal` sends tag `MEMORY` to `memory/memory_journal_active.log` and every other tag to `memory/{tag}.log` (lines 151–152). A search of Python sources finds no caller that passes the tag `MEMORY`. Production self-edit lines use `SELF_EDIT`.
- `memory/SELF_EDIT.log` (33007897 bytes) contains 25623 `result:` tokens: success 6485, safety_blocked 5912, staging_import_failed 5134, dry_run_staged 4795, load_failed 1131, rejected_meaningless_prompt 996, import_hallucination 736, invalid_syntax 344, rejected_not_improvement 83, proposed_core_edit_for_review 5, load_blocked 1, and one unparsed token. `log_memory_edit_bridge` also appends to that same tag and does not call `add_to_vector_memory`.
- `app/autonomous_loop.py` reads `result["success"]`. On baseline success it writes nothing to memory (comment at 213–215). On baseline failure it calls `log_dream_bridge` with the output string and `role: sandbox_failure`. The boolean is not a field.
- `app/core/autonomous_loop_with_optuna.py` logs `Sandbox run: {script} | Result: {output}` for both success and failure, with `role: sandbox_run` and `memory_source: autonomous`. The boolean is not a field.
- `rebuild_vector_memory` adds a new active-journal line as `MemoryItem(uuid, text, {})` (line 249). Any line that reached this path would be embedded as text with empty meta. Dedup is SHA-256 of the stripped text.

`ConsolidationRunner`'s class docstring still says prune keeps entries by cosine similarity to a centroid. `autonomous_prune_journal` uses apricot `FacilityLocationSelection` with metric `cosine`, and uses the centroid only if that import fails (lines 519–540).

## Is that information read by a later decision, retrieval, or evaluation

Outcome class is not read. No function in the consolidation or retrieval path above loads `passed`, an error type, a prior-attempt result, `oracle_outcome`, `output_tail`, or `error_tail`.

What those functions do read:

- `VectorMemory.search` ranks by cosine of the embedded text and returns the stored meta untouched.
- `retrieve_relevant_memories` drops a hit whose `role` or `memory_source` is in `{code_analysis, self_model_reflection}` (lines 459–463). If `source_filter` is set, it returns only `meta["memory_source"] == source_filter` and does not pad (lines 464–473). The docstring at 417–418 still says it falls back to an unfiltered set. The body does not.
- `retrieve_memory_context` reads `timestamp` (drop newer than 30 minutes), `memory_source` (prefer `user_conversation`, else an explicit source that is not empty and not `autonomous`), and `role` only to label the injected line. Provenance records source, role, timestamp, and a text hash.
- `_build_memory` keeps `memory_source == user_conversation` and injects text, role, and timestamp.
- `EchoOptuna._sample_prompt` drops `memory_source == autonomous` and uses the remaining text as a trial prompt.
- `_find_existing_match` reads `timestamp` and skips a topic reflected within one hour.
- `_prompt_recently_reflected` returns true when score > 0.85 and the timestamp is within two hours. That return changes which prompt is selected.
- `_is_duplicate` returns true when score > 0.92. That return skips a fetch.
- `_memory_search_fn` forwards text, score, and meta into chat prompt assembly.
- Dream sampling reads `memory_meta.json` directly, excludes role or source in `{dream, code_analysis, self_model_reflection}` and `memory_source == dream_v2`, then samples by `memory_source` bucket. Timestamp is a new-memory throttle only.

`validation_warning` has no reader. `retention` has no Python read of that key. `last_pruned_count` is written by `_update_self_model` and has no reader. The other stored keys (`type`, `prompt`, `source`, `task_type`, migration flags) were not traced to a branch in the functions listed above.

`last_consolidation` is read, by the consolidation gate only (`_should_run`, lines 63–70). A missing or falsy value returns true, so the cycle runs. Live `memory/self_model.json` `memory_health` is exactly `faiss_vector_count` 144521, `journal_line_count` 4894, `last_consolidation` null. `last_pruned_count` is absent. `self_model_updater.update` rebuilds `memory_health` and assigns `last_consolidation: None` (lines 111–118), so the timestamp consolidation writes does not survive the next self-model update. All 2915 logged cycles are non-skip rows. That is consistent with a cleared timestamp. This pass did not separately prove that the updater is the cause of every cycle running.

## Does any artifact show an outcome-class read changing an action or a recorded assessment

No. There is no stored outcome-class field for a later decision to read, and none of the consumers above branch on one.

Actions that do change on this surface use cosine score, `role`, `memory_source`, and `timestamp`. Those reads change which text is injected, which prompt is skipped, which fetch is treated as a duplicate, and which memories a dream samples. They do not change on pass versus fail, error type, or a prior attempt's result.

The consolidation summary is logged and copied into three `memory_health` fields. Night cycle prints the counts (lines 152–156) and does not branch a learning or retention decision on them. The geometry prune has never selected among journal lines in the recorded log: `nonzero` cycles with `entries_before`, `entries_after`, or `pruned_count` above zero: 0 of 2915. `max_entries_before` is 0. `max_pruned_count` is 0. `memory/memory_journal_active.log` is 0 bytes, and its mtime matches the consolidation log.

## Where the outcome signal is dropped

1. Self-edit `result:` lines are appended under tag `SELF_EDIT`. That path writes `memory/SELF_EDIT.log`. It does not write `memory/memory_journal_active.log`, and those call sites do not add a FAISS item.
2. The active journal, the only file `trim_memory_journal`, `autonomous_prune_journal`, and `rebuild_vector_memory` read, is empty on every recorded cycle. Facility-location retention has had no lines to rank.
3. If a line did reach `rebuild_vector_memory`, the new item's meta would be `{}`. The outcome token would remain inside the text only if the line text contained it.
4. The sandbox success boolean is not written. Baseline success is omitted. Baseline failure and the optuna-loop run are free text plus `role` and `memory_source: autonomous`. Prompt paths that exclude `autonomous` drop them by source.
5. `validation_warning` is written 21045 times and is not read.

## Single most important unused signal

The self-edit `result:` token.

It is already a labeled outcome: success, safety_blocked, staging_import_failed, dry_run_staged, load_failed, rejected_meaningless_prompt, import_hallucination, invalid_syntax, rejected_not_improvement, and the smaller tokens above. 25623 of those lines sit in `memory/SELF_EDIT.log`. Consolidation's geometry never opens that file. Retrieval has no meta key for the token. No examined decision, retrieval, or evaluation reads it.

The sandbox `result["success"]` boolean is the same kind of drop, at a smaller scale: computed next to a memory write, then either omitted or dissolved into an undifferentiated result string.

This surface retains non-coarse text and uses embedding geometry, source, role, and time. It drops outcome class. That is a complete finding for this pass.
