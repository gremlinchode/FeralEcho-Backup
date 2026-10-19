# Self-edit result token visibility (M5, isolated)

Date: 2026-10-19. One isolated test. No production code change. No promotion of the wrapper. The strategy-routing branch and the richer-experience-tail test were not reopened. Nothing was propagated to the Ark.

## Question

Does exposing the existing `result:` token on self-edit journal lines, inside a new root-local retrieval view, change any later retrieval, injection, or retention decision relative to the same lines with that span deleted? If it does, does the change remain after a control that writes equal-length non-token text into the same span?

What would have completed the mission with a null result: every precommitted decision identical across the withheld view, the visible view, and the control. That did not happen.

## What this test is

The view is a new MiniLM cosine index over formation lines from `memory/SELF_EDIT.log`. It is not the production FAISS store. The prior consolidation audit already established that consolidation and `rebuild_vector_memory` do not read `memory/SELF_EDIT.log`. This test does not reopen that claim and does not search the live index.

Encoder: `all-MiniLM-L6-v2`, loaded with `HF_HUB_OFFLINE=1` and `local_files_only=True` (OBSERVED: status line `encoder minilm`, embedding dim 384). Vectors are L2-normalized. Score is the dot product, the same geometry `VectorMemory.search` uses after `faiss.normalize_L2`. No generative model was called.

Frozen before the run, and recorded in `comparison_result.json` under `precommitted`:

- A labeled record is a line whose first `result:` span matches `\bresult:\s*([A-Za-z_][A-Za-z0-9_]*)`.
- Held-out ids are matched indexes where `id % 5 == 0`. Those lines are queries only. They are not embedded in the view.
- The query for every condition is the held-out line with that span deleted, so the query itself does not carry the token.
- Withheld documents: span deleted. Visible documents: original line. Control documents: the span replaced by `marker: ` plus the letter `q` repeated `len(token)` times.
- Signature: `(top-1 id, duplicate flag, skip-similarity flag)`.
- Duplicate flag: top-1 score `> 0.92`. Skip-similarity flag: top-1 score `> 0.85`. Full skip: skip-similarity and `(decision_clock - doc_timestamp) < 7200`, matching `_prompt_recently_reflected`.
- Returned set: unordered top 6. Injected-text identity: top-1 id.
- Retention pool: formation ordinal `% 67 == 0`, first 300, keep top 20% (60). Centroid cosine, plus apricot `FacilityLocationSelection` (`n_samples=60`, `metric='cosine'`) because apricot imported.
- The token effect survives the control only when the visible signature differs from the control signature on at least one query. Exact score ties break to the lowest formation row. No margin was applied after the results.

One disclosed difference from the live duplicate helper: `autonomous_fetch._is_duplicate` searches `snippet[:100]`. This test scores the full withheld line. That truncation was not added.

## Log consumed

`memory/SELF_EDIT.log` was read once at the start of the run (VERIFIED: the script's recorded digest equals the shell digest taken immediately before launch).

| | bytes | SHA-256 |
|---|---:|---|
| Bytes scored | 33008379 | `bf05736e4bf7a5a14e5d12f6cf9f3729440fa2d0b329e2ea7bb0dd21d3a89383` |

OBSERVED parse of those bytes: 170729 lines, utf-8, 25624 matched, 0 lines with more than one token, 1 line containing the letters `result:` and no parseable token, 25624/25624 control spans the same length as the original span. Holdout 5125. Formation 20499. `5125 + 20499 = 25624`.

Matched token counts in the scored snapshot: `success` 6485, `safety_blocked` 5913, `staging_import_failed` 5134, `dry_run_staged` 4796, `load_failed` 1131, `rejected_meaningless_prompt` 996, `import_hallucination` 736, `invalid_syntax` 344, `rejected_not_improvement` 83, `proposed_core_edit_for_review` 5, `load_blocked` 1. Those eleven counts sum to 25624.

The consolidation audit's earlier census was a shorter file (`33007897` bytes, digest `bb8ee5248266345b2d24559faa5f64ff42cb09ddcf5148de6153f6f05965df76`, 25623 labeled lines). The live log grew before this read. This test uses the snapshot above and does not re-grade that audit.

Decision clock: `2026-10-19T15:23:22.427623+00:00` (unix `1792423402.4276228`). Nine formation documents fell inside the 7200-second skip window at that clock.

## Root-local view

Path: `memory/experiments/self_edit_token_visibility_20261019/`

| File | Role |
|---|---|
| `run_comparison.py` | Reader and scorer. Writes only inside this directory. |
| `token_view_index.jsonl` | The view. Header plus one record per matched line. No line body. |
| `comparison_result.json` | Aggregate counts. |
| `comparison_status.txt` | Phase lines only. |
| `comparison_stdout.txt`, `comparison_stderr.txt` | Redirected process output. Stderr is the MiniLM weight-load bar. |

Index record schema: `kind`, `id` (0-based matched-line index in file order), `split` (`holdout` if `id % 5 == 0`, otherwise `formation`), `ts` (bracketed timestamp), `token` (first parsed token), `span_start`, `span_end`. The header records the source digest, the three view rules, and the matched token counts. The scorer rebuilds text by applying those spans to the hashed log bytes. Embeddings were not kept.

Checked against the index head (VERIFIED): id 0 is holdout, token `success`, span `[89, 104)`; id 1 is formation, token `success`, span `[165, 180)`. Both spans are 15 characters, which is `len("result: success")`.

## Prospective comparison

5125 held-out queries. Counts are queries whose decision differed, except the `n_*_true_*` rows, which are how many queries fired the flag.

| Decision | Visible vs withheld | Control vs withheld | Visible vs control |
|---|---:|---:|---:|
| Signature `(top-1, dup, skip-sim)` | 4660 | 4964 | 4639 |
| Top-1 id (injected-text identity) | 4653 | 4920 | 4522 |
| Top-6 set, unordered | 4996 | 5043 | 5036 |
| Top-6 order | 5082 | 5090 | 5091 |
| Duplicate flag `score > 0.92` | 299 | 1376 | 1077 |
| Skip-similarity flag `score > 0.85` | 186 | 253 | 69 |
| Full skip (similarity and age `< 2h`) | 1 | 1 | 0 |

Flag bases:

| Flag | Withheld | Visible | Control |
|---|---:|---:|---:|
| Duplicate true | 5114 | 4815 | 3738 |
| Skip-similarity true | 5122 | 4936 | 4869 |
| Full skip true | 1 | 0 | 0 |

Of the 4660 signature changes between visible and withheld, 386 have the identical signature under the control. The other 4274 do not.

Retention, pool of 300, keep 60:

| Selector | Visible vs withheld | Control vs withheld | Visible vs control |
|---|---|---|---|
| Centroid | 3 ids swapped each way | 35 | 37 |
| Apricot facility location | 21 | 19 | 25 |

Apricot ran (`error_type` null). Both selectors' visible kept-sets differ from their control kept-sets.

## Does the change survive the control

Yes for the precommitted signature (OBSERVED: `signature_changed_visible_vs_control = 4639`, `token_effect_survives_control = true`). The same is true for top-1 identity, the top-6 set, the duplicate flag, and the skip-similarity flag. Centroid retention and apricot retention also differ between the token and the marker.

The full time-gated skip does not. Both the token and the marker clear the single withheld full-skip, and they do not differ from each other (`full_skip_changed_visible_vs_control = 0`).

The control shows that the result is not "any characters placed in that span do the same thing." It also shows why the top-1 count is large. With the span deleted on both the query and the documents, 5114 of 5125 queries still have a neighbor above 0.92. Restoring the real token leaves 4815 above 0.92, while the `q` marker leaves 3738. Top-1 identity moves on 4653 queries even though the duplicate gate moves on only 299. SUPPORTED reading: most identity changes are flips inside a tight cluster of near-copies, and the marker perturbs that cluster harder than the real token does. The centroid pool says the same thing at retention scale: the token swaps 3 of 60 kept ids relative to deletion, and the marker swaps 35.

The length-matched control is `marker: ` plus a run of `q`, not a second English result word. Equivalence here is position and length. The test does not say which property of `success` versus `safety_blocked` the index uses. It says the real span and this non-token span do not produce the same decisions.

## What was left unchanged on purpose

The strategy-routing selector was not loaded, not run, and not edited. `app/experiments/persistent_routing/selector.py` is still 5149 bytes, SHA-256 `71f6f04fa522c78c49ea8eddeb67373335d8f6ea6b574c29220f0379fe0c6127`.

The richer-experience-tail artifacts were not read for scoring and were not rewritten.

- `memory/experiments/persistent_routing/log_E_experience.jsonl` — 5486 bytes, `4f5bb2377035a3ce94a1c21df6aa83e7f000e45a44e32eb296b01fa4968f0241`
- `memory/experiments/strategy_characterization/stage1/log_stage1.jsonl` — 165572 bytes, `7f9d9533cc05add8171eae632f3c9be7678233c2424ef7810858a64e1b4f826a`
- `memory/experiments/richer_experience_20261019/log_E_experience_rich.jsonl` — 76571 bytes, `547f17b3da8aecfa2b0e1dbeeba36db23990cf9f0dc0e6181e7e60e33aa7f7be`
- `audits/2026-10-19_richer_experience_capture.md` — 10612 bytes, `1b66ed539fb856bc6c33bbccbebe776369d55b730d37ea88b6ae2131d81ac71f`

`app/core/echo_model_orchestrator.py` (90538 bytes, `6dcc8b90a33008e889821f1e41058cd6291fca754ee6418fb30444a0e99b0720`) and `app/core/river_deliberation.py` (81478 bytes, `c7d68f6e09458007f230bb00138738c1115a70fc919aab1fb3717220724370cc`) are byte-identical before and after. Git HEAD stayed `4d2932c5f9a74e46ac866862ac4972b0787d7b8f`.

`audits/2026-10-19_memory_consolidation_outcome_signal.md` stayed 12813 bytes, `bf1cc7ef6b39dbbe3f85ced18eb8304425e1ab36f3106b92e92adddb54e8c921`.

## Live files that moved during the run

The scorer's only production read is `memory/SELF_EDIT.log` via `read_bytes()`. Its writes are `comparison_status.txt`, `token_view_index.jsonl`, and `comparison_result.json` in the experiment root. Shell redirection added the stdout and stderr files there. It does not open the FAISS index, `memory_meta.json`, `consolidation_log.jsonl`, or `self_model.json`.

Those live files still changed, because the already-running server kept writing. Digests before the process, then after it exited:

| File | Before (bytes, SHA-256) | After (bytes, SHA-256) |
|---|---|---|
| `memory/SELF_EDIT.log` | 33008379, `bf05736e4bf7a5a14e5d12f6cf9f3729440fa2d0b329e2ea7bb0dd21d3a89383` | 33011536, `afb19fc1e98b1a7c85103c1f93b477574021d6aa9f5326804c3f2ee7d1e17868` |
| `memory/memory_meta.json` | 121275599, `632d39cca1cf7e8720846dea515cd0da67f7ce06194794958494bd609726e5d5` | 121278012, `f8c2fddd01a7329bda3d43e84bbbeb42a6ba29466a7b18949d5750cde88ed71b` |
| `memory/faiss.index` | 221988909, `fadf8366850d0568e467c895bc87610c437cf6776eb275e3e4a2172efd91ab3b` | 221990445, `bc3c67aca73cf317b073cd494c3253c62269098304ce6f90f2598524a275a568` |
| `memory/consolidation_log.jsonl` | 455837, `e96c38e1290e62d89b3689d8279b03c3f640597aeec87ed41bd4c2594e76c35b` | 455994, `8d434a381d16a4311f91b18aa83baffc0639cc540446cf997331e611994289b1` |
| `memory/self_model.json` | 19494, `340e4859ae1a7025f19d231908d93358a357810028ace6bddc1d6e765d6227e5` | 19494, `9db7cdce1b099181bff4c78b7bd0cb716ca91e808ebea9501aa580709fdce056` |
| `memory/memory_journal_active.log` | 0, `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | unchanged |

The new consolidation row is the 2916th, `started_at` `2026-10-19T15:26:20.690124+00:00`, `pruned_count` 0, `entries_before` 0, `entries_after` 0, `error` null, `faiss_vectors_after` 144524. That is three minutes after the decision clock and during encoding. The active journal remained empty. The scored log snapshot does not include appends after `bf05736e…`.

## Stop

The wrapper stays in the experiment root. It was not promoted, not wired into consolidation, retrieval, or self-edit, and not applied on the Ark. No further test was chained. The strategy-routing selector and the richer-experience-tail comparison stay closed.

## Integrity

```
production changes: NO
files changed: memory/experiments/self_edit_token_visibility_20261019/ (new), audits/2026-10-19_self_edit_token_visibility.md (new)
Git HEAD before: 4d2932c5f9a74e46ac866862ac4972b0787d7b8f
Git HEAD after: 4d2932c5f9a74e46ac866862ac4972b0787d7b8f
commits created: NO
pushes performed: NO
services restarted: NO
processes started/stopped: one feral_echo python process for run_comparison.py, exit 0, about 546s; not the Echo server
configuration changes: NO
test changes: NO
temporary files created: experiment-root __pycache__ from py_compile
temporary files cleaned: YES — __pycache__ removed; the script, index, result, and status logs remain
orphaned processes: none; the comparison process exited
known anomalies: live server appended SELF_EDIT.log, memory_meta.json, faiss.index, consolidation_log.jsonl, and rewrote self_model.json during the run; the scorer does not open those except the one read of SELF_EDIT.log
known deviations from requested methodology: production duplicate search truncates the query to 100 characters; this comparison scored the full withheld line, disclosed before the run in comparison_result.json
```
