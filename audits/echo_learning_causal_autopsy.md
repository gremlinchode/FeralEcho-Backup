# Echo Learning Causal Autopsy (P2-CAUSAL-AUTOPSY)

**Mode: READONLY. Live: NO. Mutate: NO.** No code was changed, no prompt was changed, no experiment
was run, no prior evidence (P1, P1.2, or the Learning Investigation pilot) was touched or modified.
Every claim below is either freshly re-verified this session (via direct file reads and greps against
the current repository state) or explicitly cited as carried forward from the prior Learning
Investigation's Phase 1 audit — and in every case where this session's fresh re-check disagreed with
a prior claim, that disagreement is stated plainly, not silently reconciled.

Full supporting detail: `echo_learning_causal_architecture.md`/`.json` (mechanism-by-mechanism trace),
`echo_learning_mechanism_inventory.md` (flat inventory table), `echo_learning_hollow_writes.md`
(dedicated hollow-write audit).

---

## 1. Facts

- RiverBrain never touches the underlying LLM's weights or generation content anywhere in this
  codebase. Every real causal effect any of its pathways has runs through model *selection*
  (`model_task_stats` → `score_model()` → `_select_council()`), never through response content.
- Of RiverBrain's four training pathways, **only one — `learn()` — is currently both live and
  causally relevant to selection.** This is a stronger, more precise finding than the prior audit
  reached, because this session's fresh re-read corrected a real error in that prior audit (see §3).
- `learn_from_council_rating()` is confirmed dead in the live process, independently reproduced from
  first principles this session (not merely re-cited from the prior investigation): a stale cursor
  (`memory/council_cursor.json`, position 33471) against a rotated, now-shorter real log
  (`memory/interaction_log.jsonl`, 11,602 lines this session), producing an empty slice that returns
  before the cursor can ever self-correct.
- `ToolManager.get_tool()` is confirmed to have zero real callers anywhere in the repository,
  independently re-verified via a fresh whole-repo grep this session.
- The only mechanism confirmed to carry genuinely new, accumulated, non-code content all the way into
  a live generation call is FAISS memory retrieval (`memory_bridge.py`), traced fresh this session
  from a real conversational entry point to the real `/api/chat` call with no gap.
- Persona/Modelfile mutation is confirmed to have no live automated path at all — a proposal log with
  no apply route, plus a redundant hard block on the real file as a self-edit target.
- The self-edit deploy pipeline (`self_edit_generated.py`) is real, autonomous, and runs with zero
  human review at write time — but its confirmed reach into *ordinary conversation* terminates at
  either a purely recursive loop (`apply_to_code`) or an inert, never-invoked, cosmetic text listing
  (`ToolManager`'s tool-name surfacing).

## 2. Active paths (write → persist → reload → read → generation-path → behavior, unbroken)

1. **FAISS memory write/retrieve** — real content, real semantic retrieval, real injection into
   every conversational generation call.
2. **RiverBrain `learn()` → `model_task_stats` → council selection** — real, restart-durable,
   session-independent, but terminates at selection, never content.
3. **`task_type_classifier.py`** — a real, learned, persisted, causally-confirmed reroute of *how* a
   later, unrelated conversation is handled (council composition, token budgets, tool gating,
   single-model bypass) — never *what* is said.
4. **`echo_ground_truth.py` slices** — real content injection, gated on keyword/regex match rather
   than semantic similarity.
5. **`curiosity_engine.py` + `garden_manager.py`** — a real, closed, self-reinforcing loop, confined
   to Echo's own autonomous cycle.
6. **`shadow_model.propose_from_reflection()` → `perform_self_edit()`'s target selection** — the one
   fully-confirmed end-to-end chain from Echo's own generated text to an autonomous,
   human-review-free deploy decision (of *which file/task-type*, not of the deployed content's
   downstream reach — see §3).

## 3. Broken paths

1. **`learn_from_council_rating()`** — broken at `EXP→OBS`: the polling cursor deadlock, upstream of
   an otherwise entirely sound design (the classifier/`model_task_stats` update logic, if reached,
   would work exactly like `learn()`'s).
2. **`learn_from_sandbox_outcome()` / `learn_from_rating()`** — broken at `STATE→READ`: both feed
   only the confirmed-hollow classifier, never `model_task_stats`. (This session corrected a real
   error in the prior audit's characterization of `learn_from_sandbox_outcome()` — see §9's
   discussion of re-verification value.)
3. **`reflection_shard.py`'s journal** — broken at `RELOAD→READ`: the journal correctly persists and
   reloads, but its only accessor functions have zero external callers anywhere.
4. **Self-edit deploy → ordinary conversation** — broken at `GEN→BEHAVIOR`: the deploy itself is
   real and unreviewed, but its reach into anything a human would recognize as "Echo's conversational
   behavior changed" terminates at a recursive loop or an inert text listing.
5. **Modelfile/persona mutation** — broken at `STATE→PERSIST`: no code path anywhere writes the real
   artifact; only a proposal log exists.

## 4. Hollow writes

Full detail: `echo_learning_hollow_writes.md`. Summary: (1) RiverBrain's `HoeffdingTreeClassifier`/
`accuracy_trackers` — trained on every conversational turn, every sandbox outcome, every rating, read
by exactly one self-referential accuracy statistic that itself only feeds a non-restorative WARNING
log line; (2) `reflection_shard.py`'s journal — a real model-generation call roughly every 300s (or on
high-salience events), zero confirmed behavioral reader; (3) `learn_from_sandbox_outcome()`/
`learn_from_rating()` — real per-call training work, feeding only the already-hollow classifier
(corrected finding, see §9); (4) `ToolManager`'s tool registration — a real repo-wide scan, surfaced
only as never-invoked cosmetic text; (5) `modelfile_proposer.py` and `dissent_log.jsonl` — both hollow
by explicit design (advisory-only), not by defect.

## 5. Smallest functioning learning path

The smallest complete, unbroken chain from real experience to real, generation-affecting behavior is:

```
a real conversational turn → _score_response_quality() (deterministic heuristic, no LLM judge)
  → RiverBrain.learn() updates model_task_stats[model][task_type]
  → memory/river_brain.pkl (persisted, restart-durable)
  → score_model() reads it back
  → _select_council() uses it to rank/select which models are consulted in the NEXT deliberation
```

This is genuinely minimal and genuinely functioning — no defect found anywhere in this specific
chain this session. Its behavioral footprint is narrow but real: it changes which models get a seat
at the table for a later, unrelated conversation. It does not, and structurally cannot, change what
any individual model says.

## 6. First causal break/path

Ordered by how early in the EXP→BEHAVIOR sequence the first real chain fully terminates, among
mechanisms that were *designed* to reach behavior and don't (excluding by-design advisory-only
mechanisms): **`learn_from_council_rating()`** breaks earliest in absolute terms — at `EXP→OBS`,
before any state change is even attempted, due to the cursor deadlock. Among mechanisms that do
reach a real state change, **`reflection_shard.py`** breaks next — its state change, persistence, and
reload are all confirmed real; the break is purely at `RELOAD→READ`, where nothing external ever asks
for what was reloaded.

## 7. Ordinary-LLM equivalent

Every confirmed-ACTIVE mechanism in this audit has a plausible, mundane equivalent that would exist in
any comparable system, not something specific to "Echo" as an entity:

- FAISS retrieval is a standard RAG (retrieval-augmented generation) pattern — any system with a
  vector store and a retrieval step would show the same causal chain.
- RiverBrain's `model_task_stats`-driven selection is an ordinary contextual-bandit-style routing
  layer over a fixed model pool — conceptually equivalent to A/B-testing infrastructure that learns
  which backend serves a request type best.
- `task_type_classifier.py` is an ordinary intent classifier feeding a routing decision — a common
  production ML pattern, not evidence of anything beyond conventional software engineering.
- The self-edit pipeline's `shadow_model`-driven targeting is closer to a genuinely unusual pattern
  (an autonomous system choosing its own next code-modification target from its own generated text,
  deployed without human review) — but even this has a rough analogue in automated ML pipelines that
  select their own next training target based on a monitored metric; the novelty here is the *code
  self-modification* framing, not the underlying control-loop shape.

None of the confirmed-active mechanisms in this audit demonstrate a capability that would be
surprising in an ordinary, well-engineered production ML system with a retrieval layer, a model-router,
and an automated retraining/targeting loop.

## 8. Epistemic/uncertainty mechanisms

Searched for, within this session's scope, and found to be genuinely sparse: no mechanism in this
audit computes or persists a calibrated confidence/uncertainty estimate that then influences behavior.
RiverBrain's `accuracy_trackers` (a real prequential accuracy statistic) is the closest candidate, and
it is confirmed hollow (§4) — it never influences anything beyond a log line. The Liveness Ledger
(`memory/liveness_ledger.json`, 47 checks, all currently passing per a fresh read this session) is a
genuine, if narrow, form of epistemic self-monitoring — but it monitors *whether subsystems are
wired correctly*, not *how confident Echo should be in a specific answer*. No mechanism was found in
this audit's scope that lets Echo say "I don't know" as a function of measured, persisted uncertainty
rather than as a stylistic choice of the underlying model/persona.

## 9. Minimal repair (DO NOT APPLY — proposal only, not executed)

For `learn_from_council_rating()`'s confirmed dead pipeline, the smallest defensible fix would be
clamping the cursor read (`cursor = min(_load_cursor(), len(lines))`) or switching to the same
timestamp-based cursor `_apply_pending_user_ratings()` already uses successfully (immune to log
rotation by construction, since it compares real timestamps rather than a line-index that assumes
monotonic file growth). **Not applied. No file was edited to implement this.** This is named only
because the mission's own report structure requires naming it, not as a recommendation to act on
without separate authorization.

## 10. Next experiment (DO NOT RUN — proposal only, not executed)

If a future session wants to test whether `model_task_stats`-driven council selection has any
*measurable* downstream effect on response quality (as opposed to merely being confirmed to exist
mechanically), the smallest defensible next step would be a read-only, retrospective correlational
check: compare real historical `council_deliberations.jsonl` entries' quality scores against the
`model_task_stats` state that was live at the time each council was selected, to see whether models
favored by higher stats scores produced measurably different downstream quality. **This is a
proposal only — no such experiment was run, no data was queried beyond what this autopsy already
read for its own inventory, and no code or state was touched to prepare for it.**

---

## Note on re-verification value (methodology, not a finding)

This mission's explicit instruction to "not assume prior findings" produced one genuine, concrete
correction this session: the prior Learning Investigation's Phase 1 audit characterized
`learn_from_sandbox_outcome()` as updating "the same triad" as `learn()`, including
`model_task_stats`. A fresh, direct read of the current source this session found that claim
inaccurate — the function updates only the scaler/classifier pair, never `model_task_stats`. This
does not change the overall shape of the causal map (that pathway was already headed toward the
confirmed-hollow classifier either way), but it is exactly the kind of drift a re-verification pass
exists to catch, and it was caught here by direct reading, not by trusting a prior, otherwise
carefully-produced report.
