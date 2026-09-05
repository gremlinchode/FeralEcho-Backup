# Echo Learning — Hollow Write Audit (P2-CAUSAL-AUTOPSY)

Read-only. A "hollow write" here means: real, continuous, sometimes computationally expensive state
change that is genuinely persisted to disk and correctly reloaded across restarts, but for which no
reader anywhere in the current codebase converts that state into any behavior-affecting decision.
Every entry below was independently re-confirmed this session via a fresh whole-repo grep for the
mechanism's own accessor/consumer functions — not carried forward from a prior audit's conclusion
without re-checking.

---

## 1. `reflection_shard.py`'s `reflection_journal.jsonl`

**The write is real.** `BecomingReflectionShard.observe()` produces genuine, live, model-generated
text (not a template — independently confirmed by the project's own `reflection_shard_generation`
liveness check, which measures real pairwise distinctness against the last 20 entries). It runs on
its own 300s autonomy loop and, since a later phase, also fires when a high-salience Global Workspace
event crosses a wide-broadcast threshold.

**The read is confirmed absent.** `EchoCore.recall_reflections()` and `EchoCore.observe_reflection()`
are this journal's only public accessors. A fresh, whole-repository grep this session
(`grep -rn "recall_reflections\|observe_reflection\b"`) returns exactly two lines — both the
definitions themselves, in `echo_core.py`. No other file in the repository calls either method.
Separately, `reflection_shard.py` itself was grepped for any reference to `memory_bridge` or
`add_to_vector_memory` — none found — confirming this journal has no path into the FAISS store
either, and therefore no path into mechanism #1 of the inventory (the one confirmed-causal, real
generation-influencing pathway in the entire codebase).

**One narrow, content-free side effect exists, not a real read path**: meta-reflection synthesis
publishes a Global Workspace event, but with `salience` left at its default `None` — per the
workspace's own documented fail-closed rule, this never qualifies as `wide_broadcast`, so
`echo_ground_truth.py`'s workspace slice never surfaces it either.

**Verdict: confirmed hollow.** Real, continuous, live computation with zero confirmed behavioral
consequence anywhere in the current codebase.

---

## 2. RiverBrain's `HoeffdingTreeClassifier` / `accuracy_trackers`

**The write is real and continuous.** All four training pathways (`learn()`,
`learn_from_sandbox_outcome()`, `learn_from_rating()`, `learn_from_council_rating()`) feed this
classifier on every call, whether or not that specific call also touches `model_task_stats`.

**The read is confirmed to be exactly one call site, feeding only itself.** Fresh grep this session
for `predict_one`/`.classifiers\b` across the whole repository finds a single non-definition call
site: inside `learn()` itself, immediately followed by `accuracy_trackers[task_type].update(label,
pred)`. `accuracy_trackers`' own only consumer, in turn, is `introspection_channel.py`'s PageHinkley
drift detector, which — by explicit, documented design — only ever produces a `[DRIFT-NOTICE]`
WARNING-tier log line (`raise_drift_notice()`, deliberately not `raise_restore_alert()`), never an
autonomous action.

**Verdict: confirmed hollow.** The classifier predicts on a sample it is about to be trained on,
purely to produce a self-referential accuracy statistic that itself only feeds a notification, never
a decision.

---

## 3. RiverBrain's `learn_from_sandbox_outcome()` and `learn_from_rating()`, specifically with
   respect to `model_task_stats`

**Correction to the prior Learning Investigation's Phase 1 audit, produced by this session's own
re-verification (as the mission explicitly required — "do not assume prior findings").** The prior
audit's report characterized `learn_from_sandbox_outcome()` as updating "the same triad" as `learn()`
(scaler, classifier, **and** `model_task_stats`). A fresh, direct read of
`echo_model_orchestrator.py:870-880` this session shows this is not accurate: the function updates
`scalers`, `classifiers`, and a *separate* counter, `sandbox_observation_counts` — it never touches
`self.model_task_stats` at all. `learn_from_rating()` was already correctly identified in the prior
audit as not writing `model_task_stats`; re-confirmed here by direct re-read, unchanged.

**Consequence:** since `score_model()` (the one function that actually influences model/council
selection) reads only `model_task_stats`, **both of these training pathways are hollow with respect
to selection**, not merely "narrower than `learn()`." They still feed the confirmed-hollow classifier
(item 2 above), so their real behavioral footprint — across two independent hollow layers — is zero.
Of RiverBrain's four training pathways, this leaves **exactly one** (`learn()`) as the sole currently
firing, causally-relevant-to-selection writer, since `learn_from_council_rating()` (the other
`model_task_stats` writer) is separately confirmed dead (item 4 below).

---

## 4. RiverBrain's `learn_from_council_rating()` pipeline (peer-council rating blend)

**Not a hollow write in the "no reader" sense — a dead write, confirmed via a different mechanism.**
Unlike items 1-3 above, this pathway's design is structurally sound and, when it fires, is genuinely
read by `score_model()` exactly like `learn()`. The problem is that it is **not firing at all**,
independently reproduced fresh this session:

```
memory/council_cursor.json: {"position": 33471, ...}
memory/interaction_log.jsonl: 11602 lines (real, live count, this session)
lines[33471:] on an 11602-line list: length 0
grep -c "[Council] Rated" memory/echo_watchdog.log: 0
memory/council_ratings.jsonl: last modified Jul 28, unchanged
```

Root cause, re-confirmed by direct read of `council_rater.py:574-630`'s current source this session:
`_poll_and_rate()` slices `lines[cursor:]`; if that slice is empty, it returns `0` at line 591-592 —
**before** `_save_cursor(len(lines))` at line 625 ever executes. Since the real log
(`memory/interaction_log.jsonl`) was rotated (a real rotation artifact,
`interaction_log.jsonl.1.gz`, confirmed on disk, dated Aug 22) and now sits far shorter than the
stale cursor, this condition can never self-correct until the live file naturally grows past 33,471
lines again — a slow, real-time-dependent recovery, not a structural fix.

**Verdict: confirmed dead, not hollow.** The mechanism would be genuinely causal if it fired; it does
not currently fire, and nothing in the codebase detects or corrects this on its own.

---

## 5. `ToolManager.get_tool()`

**Re-confirmed, fresh, this session, exactly as the mission required rather than assumed.** A
whole-repository grep for `.get_tool(` finds only the method's own definition and one unrelated
comment (in `scripts/verify_preference_provenance_experiment.py`, describing a different check's
shape in prose). **Zero real callers exist anywhere.** `ToolManager`'s `tools` dict is populated by
`discover_and_register_tools()` (a real scan of `app/core`, confirmed still wired at `run.py:1285`
this session) and its contents are surfaced as **text only** — a comma-joined list of function names
injected into a "TOOL-LIST" system note for `coding`/`reasoning`-tagged conversations
(`echo_model_orchestrator.py:1503-1516`, re-confirmed fresh) — but the functions themselves are never
invoked by anything.

**Verdict: confirmed hollow for invocation, real (but purely cosmetic) for text-surfacing.** A
function name an earlier self-edit cycle happened to choose can genuinely appear in front of the
model in a later, unrelated conversation — but it is never executed, so this is not a behavioral
learning channel in any meaningful sense; it is closer to an incidental, unreviewed piece of prompt
content.

---

## 6. `modelfile_proposer.py`

**The write is real** (a proposal is genuinely rendered and appended to
`memory/modelfile_proposals.jsonl` on a `GET` request). **The read is confirmed to loop back to the
same GET route only** — no apply route exists anywhere in `run.py`, and the real `Modelfile` is a
protected self-edit target as a second, independent guarantee.

**Verdict: confirmed hollow, by design, for autonomous persona mutation.** This is a deliberate,
human-in-the-loop-only workflow, not a defect — but it is, mechanically, a write with no automated
reader, and belongs in this inventory for completeness.

---

## 7. `dissent_log.jsonl` (`propose_core_edit()`)

**The write is real** (a genuine multi-model council vote, human-triggered via `!propose`). **The
read is confirmed to be a static source-anchor liveness check plus a human-facing dashboard view
only** — `propose_core_edit()` never calls `save_code()`, confirmed by the absence of that call
anywhere in the function's body.

**Verdict: hollow by design** — this is an advisory log that intentionally never gates a write, not a
mechanism that was supposed to be causal and silently isn't.

---

## Summary: hollow-write mechanisms ranked by how much real computation they consume for zero
   confirmed behavioral return

| Mechanism | Real ongoing cost | Confirmed behavioral return |
|---|---|---|
| RiverBrain classifier/accuracy_trackers | Trained on every conversational turn, every sandbox outcome, every rating | A WARNING log line, never a decision |
| `reflection_shard.py` journal | A real model-generation call every ~300s (or on high-salience events) | None confirmed |
| `learn_from_sandbox_outcome()`/`learn_from_rating()` | Real feature extraction + classifier training per call | None confirmed (feeds only the already-hollow classifier) |
| `ToolManager` registration | A repo-wide file scan every ~1800s (or at startup) | Cosmetic text only, no invocation |
| `modelfile_proposer.py` | On-demand only, cheap | A human-facing log entry, no autonomous effect |
| `dissent_log.jsonl` | On-demand only (human-invoked), cheap | Advisory only, by design |

None of these findings imply any of these mechanisms are broken relative to their own documented
intent (the last two are explicitly designed to be advisory-only) — they are reported here precisely
because "real write, no behavioral reader" is the specific pattern this project's own history
(CLAUDE.md's Findings 25/28/35) has repeatedly found and re-found, and this autopsy's mandate was to
verify rather than assume that the previously-identified instances still hold, and to check for
others.
