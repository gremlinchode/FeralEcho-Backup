# FeralEcho: Autonomous Fruit Forensic Audit

**Observational only.** No autonomous loop, schedule, model selection, Ollama configuration, counter, learning state, or artifact was
paused, throttled, restarted, tuned, repaired, or otherwise altered to produce this document. Every number below is read directly from
the live, running system's own files and logs during the course of this investigation (2026-09-03/04), with exact commands and file
paths recorded in §12. Where evidence is thin, the classification is stated conservatively and marked `UNKNOWN` rather than inferred.
**Held-out protection re-confirmed at the end of this audit (see §12): no held-out manifest exists anywhere in the repository, no
held-out task was executed, referenced, or loaded.**

## 1. Executive Finding

**Mostly activity, with a small number of concrete, demonstrated fruit and one genuinely dormant, previously-load-bearing pipeline
found broken during this exact investigation.** The autonomous workload is real, large, and continuously running — dozens of distinct
background mechanisms, multiple real per-hour Ollama call volumes, gigabytes of accumulated state — and a handful of these mechanisms
demonstrably close the full causal chain this audit requires (autonomous trigger → output → persistence → reader → consumer → changed
downstream behavior). But the majority of the audited subsystems stop at ACTIVITY or SEED: real computation and real persistence, with
either no demonstrated reader, no demonstrated consumer, or no demonstrated behavioral consequence. One subsystem previously documented
as a genuine, trust-gated training-signal path (`RiverBrain.learn_from_council_rating()`) was found, during this investigation, to have
been silently non-functional for **at least 13 days** due to a cursor left stale by a log-rotation event — a real, current, previously
unreported defect, reported here per the mission's own instruction and **not repaired**. Per the mission's own explicit standard: this
is reported as a successful, honest result, not as a failure of the autonomy program or of this audit.

## 2. Subsystem Classifications

Each entry below answers, in compressed form, the ten required questions: (1) autonomous trigger, (2) code executed, (3) output
produced, (4) storage location, (5) reader, (6) consumer, (7) decision/action affected, (8) runtime-evidence demonstrability, (9)
cross-session/restart persistence, (10) competing explanations. "This session" means directly re-verified during this investigation
(2026-09-03/04, live repo/runtime state); citations to `CLAUDE.md Finding N` are prior, dated findings not independently re-run here
unless stated.

---

### Curiosity engine + curiosity garden — **ACTIVITY**, with narrow **POTENTIAL_FRUIT**

- **Trigger**: `curiosity_engine.py`'s WorldModel topic under-representation check; `dream_cycle()`, `seam_engine.observe()`, and
  `self_edit_manager.py`'s dissent-logging path also harvest questions via the same public API.
- **Code**: `garden_manager.harvest_question()` / `select_from_garden()` / `mark_question_asked()`.
- **Output**: real, natural-language questions with `category`, `resolution_score`, `status`, `parent_questions`/`children` lineage.
- **Storage**: `data/question_garden.jsonl` — **13,470 real lines**, re-confirmed this session (`wc -l`).
- **Reader**: `emergent_scheduler.py`'s `select_from_garden()` (topic-bias-weighted prompt selection), `claude_research.py`'s
  least-recently-asked picker, `echo_projects.py`'s `autonomous_generate_project()` (confirmed this session — see below).
- **Consumer / downstream effect**: (a) `emergent_scheduler`'s next autonomous reflection prompt is genuinely biased by garden
  content — this changes *which* prompt an autonomous cycle reflects on, a real, if soft, behavioral effect; (b) **`echo_projects`'s
  autonomous cycle uses a real garden entry as its literal build spec** — re-confirmed this session by directly invoking
  `autonomous_generate_project()`, which read a real philosophical question from the garden and used it, verbatim, as the project
  brief (see the `echo_projects` entry below for the full chain and where it terminates).
- **Evidence**: HIGH for "a real garden entry became a real downstream prompt" (directly observed this session); LOWER for "this
  measurably changed anything a person would notice," since the downstream consumers (a reflection's topic, a project's build brief)
  do not themselves demonstrably feed back into anything further outside their own subsystem (see `echo_projects`, `reflection cycle`
  below — both terminate at ACTIVITY one hop later).
- **Persistence**: yes — file-backed, survives restart, 13,470 lines is clearly multi-month accumulation.
- **Competing explanation**: the *volume* of garden entries (13,470) does not by itself indicate more "fruit" than a smaller garden
  would — most entries never resolve (`resolution_score` sampled this session shows `0.0` on 2 of the 3 most recent entries), and this
  audit does not equate persistence with use.

### Reflection cycle + reflection shards — **ACTIVITY**, one real but narrow **POTENTIAL_FRUIT** link (Global Workspace)

- **Trigger**: `ReflectionShardAutonomy`, 300s cadence, 35% chance/cycle (`observe()`); a 10th-observation meta-reflection pass.
- **Code**: `reflection_shard.py`'s `_generate_reflection()`/`_generate_meta_reflection()` — real model calls since Finding 78 (Phase
  B2), not template-quoting.
- **Output**: real generated text, `memory/reflection_shard.jsonl`.
- **Storage**: re-confirmed this session at **20,526 lines**, actively growing (a real, fresh entry from `2026-09-04T04:40:30` was
  read directly this session — see below for what that entry actually contained).
- **Reader**: **A directly-observed anomaly, worth stating plainly**: the newest entry in `reflection_shard.jsonl` sampled this
  session was not an ordinary self-reflection at all — it was a full self-edit *planning* prompt/response pair (the real
  `plan_code_logic()` output for a `response_shortening` cycle, including the real "attempted 58 times before" convergence note and
  the real code-quality guidance block, ending in a genuine 8-step numbered plan). This means `reflection_shard.jsonl` is, in
  practice, a shared log destination for at least two structurally different producers (ordinary autonomous reflection, and
  self-edit's own planning step) — not investigated further in this pass, flagged as a real, current observation rather than
  something this audit had a prior basis to expect.
- **Consumer / downstream effect**: since Finding 78 (Phase B2), a meta-synthesis publishes a real `reflection.meta_synthesis` Global
  Workspace event. **Directly re-confirmed this session**: the last 500 `workspace_log.jsonl` events include 16 real `reflection_shard`
  entries, and a real `workspace.consumed` event (`source: river_deliberation`, `summary: "exploration_bias=0.001 (from cache)"`) was
  observed at `2026-09-04T04:40:45` — proving the Global Workspace's consumption path is genuinely live, right now, not merely wired.
  But that consumed event's *own* source in this specific instance was `river_deliberation`/`world_model`, not `reflection_shard` —
  this session did not directly observe a `reflection.meta_synthesis` event itself being consumed and changing a later decision (only
  that the general consumption mechanism is alive, and that `reflection_shard` is one of several sources reaching wide broadcast).
- **Evidence**: MEDIUM. The write→broadcast half of the chain is demonstrated live; the broadcast→consumed-and-changed-a-decision half
  is demonstrated live for the mechanism in general, but not specifically traced end-to-end for a `reflection_shard`-originated event
  in this session's observation window.
- **Persistence**: yes, file-backed.
- **Competing explanation**: a person reading `self_edit_apply_to_code`-style dashboards would see "reflection shard: 20,526 entries,
  growing" and reasonably assume rich accumulated self-knowledge; the direct sample this session shows at least one entry that is not
  reflection at all, undermining a naive read of that line count as "20,526 genuine reflections."

### Planning (self-edit's `plan_code_logic()`) — **ACTIVITY**, real internal **FRUIT** confined to the self-edit loop itself

- **Trigger**: every self-edit cycle (Optuna dry-run trials, ~10/hour; the ≤1/hour real production attempt).
- **Code**: `self_edit_manager.py`'s `plan_code_logic()` — reads live convergence state, live AST module inventory, live code-quality
  guidance, and (Finding 32) an explicit before/after example.
- **Output**: a real, numbered step plan — directly observed this session (the 8-step plan quoted above).
- **Storage**: `app/core/self_edit_plans/` (capped at 500, Finding 58), and incidentally `reflection_shard.jsonl` (see above).
- **Reader/consumer**: `generate_code_from_plan()` — the plan is the literal prompt for the next real generation call.
- **Decision/action affected**: real — the plan text directly determines what candidate code gets generated, which then goes through
  F1/F2 and (rarely) deployment. This is a genuine, demonstrated, tight causal chain, but it is entirely **internal to the self-edit
  loop** — it does not reach outside that loop into any other subsystem's behavior.
- **Evidence**: HIGH (the literal plan text and the literal downstream candidate are both directly inspectable and causally linked by
  construction — `generate_code_from_plan()` has no other prompt source).
- **Persistence**: yes.
- **Competing explanation**: none of significance — this is a genuinely real, if narrow, closed loop; see the "self-editing" entry
  below for why its *ultimate* output (a deployed, quality-improving change) remains weak/uncertain.

### echo_projects — **ACTIVITY** (0/61 end-to-end success, re-confirmed this session)

- **Trigger**: `!project` (manual) and, since Finding 85, an autonomous 6h-cadence loop gated by `should_run_cycle`.
- **Code**: `council_generate_project()` → `_council_review_project()` → per-file `echo_query()` → F1 → F2.
- **Output**: multi-file Python projects + a human-readable `_report.md`.
- **Storage**: `sandbox/echo_projects/` — **61 real project directories**, at the 60-directory retention cap (Finding 85), re-confirmed
  this session.
- **Reader**: a human, if they choose to open a report; **no automated reader of the *generated code* itself exists anywhere** — the
  pipeline's own design explicitly never promotes anything into a trusted or loaded state (Finding 83's own stated invariant, and this
  session confirmed, via direct grep, no importer of anything under `sandbox/echo_projects/` exists anywhere in `app/` or `run.py`).
- **Consumer / downstream effect**: **none demonstrated on the generated code itself.** The one real, demonstrated downstream effect is
  upstream of the code: a real curiosity-garden question genuinely becomes a real project spec (see "curiosity" above) — that is a real
  input-side effect, not an output-side one.
- **Evidence, re-measured directly this session, not carried forward from a prior count**: of 61 real reports, **48 fail F1** entirely
  (never reach F2); of the 13 that reach F2, **13/13 fail** (`grep` count, not estimated). **0/61 have ever produced a working,
  F2-passing multi-file project.** The most recent autonomous cycle (`echo_projects_autonomy_state.json`, `last_run_utc:
  2026-09-04T00:48:46`) recorded `last_status: "f1_failed"` — consistent with, not contradicting, the historical rate.
- **Persistence**: yes, capped and pruned.
- **Competing explanation**: this is real, repeated, non-trivial computation (multi-model council planning + generation + council
  review) producing consistently non-functional output — this reads as a demonstrated capability ceiling for this pipeline's current
  design/model pool, not as "nearly working" or "one bug away." Classified `ACTIVITY`, not `DEAD`, because it runs on schedule as
  designed and does produce real, if useless-to-date, artifacts — and not `SEED`, because a seed implies latent future value, and 0/61
  gives no positive evidence supporting that framing over "this reliably fails."

### Knowledge acquisition (daily code-scan + internet fetch) — **mixed: fixed dedup is real POTENTIAL_FRUIT; internet fetch is ACTIVITY**

- **Trigger**: `autonomous_awareness.py`'s daily code-scan; `autonomous_loop.py`'s ~9-source internet fetch (Reddit removed, Finding
  59).
- **Code / output / storage**: `analyze_python_code()` → `memory/memory_meta.json` (`role="code_analysis"`); fetch results also land
  in the same FAISS-backed store.
- **Re-verified this session, a genuinely positive, current finding**: `memory_meta.json` currently holds **123,793 total entries**,
  of which **59,910 (48.4%) are `code_analysis`** — the historical contamination Finding 30/41's staging/-scan bug produced is still
  present in full, unpurged, exactly as the (parked, unexecuted-by-this-session) remediation plan intended. But **the fix is live and
  working**: `memory/code_scan_hash_cache.json` exists, tracks 472 real files, and a direct scan of `memory_meta.json`'s own timestamps
  found **zero new `code_analysis` entries added in the last 24 hours** — the daily scan is still running (the cache file's own mtime
  is from today) but is now correctly skipping unchanged files instead of re-logging them. `app/core/memory_bridge.py`'s
  `retrieve_relevant_memories()` was also directly confirmed, by reading its live source, to unconditionally exclude
  `code_analysis`/`self_model_reflection` from every retrieval regardless of `source_filter` (`_ALWAYS_EXCLUDED_MEMORY_CATEGORIES`).
- **Reader/consumer**: the exclusion means this content is now demonstrably **not** reachable via `retrieve_relevant_memories()` —
  a real, verified negative (a bug closed), which this audit records as a positive finding about system hygiene, not as fruit in the
  sense the mission defines it (nothing here changes a downstream *decision*; it prevents a downstream *contamination*).
- **Internet fetch** (Wikipedia, arXiv, BBC, NPR, Guardian, StackOverflow, HN, This Day History, optional NASA): real content lands in
  the same memory store and is eligible for ordinary retrieval and dream-cycle sampling; no evidence was sought or found this session
  of any specific fetched article changing a specific later decision — classified `ACTIVITY` on the same basis as most memory writes
  in this audit (real, persisted, no demonstrated consumer-driven behavior change traced).
- **Persistence**: yes.
- **Competing explanation**: none — this is a case where the mission's own re-verification requirement caught a real, positive,
  previously-uncertain state change (the fix holding) that a stale prior document could easily have mischaracterized as still-broken.

### Self-editing (the full pipeline: Optuna trials → F1/F2 → deploy → outcome → reflection) — **ACTIVITY with a real, narrow, weak POTENTIAL_FRUIT loop**

- **Trigger**: hourly `AutonomousSelfEdit` thread + Optuna dry-run trials (~10/hour).
- **Code**: `self_edit_manager.py`'s full pipeline, `self_edit_outcome_tracker.py`.
- **Output/storage**: `memory/self_edit_outcomes.jsonl` — **179 real evaluated records**, re-confirmed this session.
- **Directly sampled this session, real and current, not carried forward**: the 3 most recent real outcome deltas are `+0.135`,
  `-1.471`, and `null` (post-window never resolved). This is a real, mixed, and — in the most recent resolved case — **negative**
  result: a real deployed self-edit made measured quality *worse*. This is exactly the "weak/uncertain quality improvement" prior
  characterization, re-confirmed with fresher and, if anything, less favorable data than before.
- **A second, directly-observed current signal, not previously documented at this level of freshness**: `self_edit_convergence.json`
  (live, git-modified during this exact session, confirmed via `git diff --stat`) shows `response_shortening` now at **58 near-duplicate
  function names** (`shorten_code`, `shorten_code_generation`, ...`v19`, `refactorshortencodegeneration`...) — the same
  non-convergent-reimplementation pattern Finding 32 first found for `prose_stripping` (95 cycles) is now clearly present, at
  comparable scale, in a second family. `quality_scoring` (paused per Finding 52) still carries 8 accumulated names despite the pause.
- **Closed-loop check (the mission's own explicit standard — do not conflate individual real subsystems existing with the loop actually
  closing)**: self-edit → outcome → RiverBrain's `self_edit_coding`/`echo_projects_coding` buckets (confirmed genuinely fed — see
  RiverBrain/model_task_stats below) is a **real, demonstrated, closed loop** for the narrow question "does the model-scoring signal
  update from real self-edit activity" — yes, confirmed. Self-edit → outcome → **self-model retargeting** (a genuinely improved next
  target, not just a logged delta) is **not independently demonstrated this session** — `_build_targeted_prompt()`'s convergence-aware
  framing (Finding 16/32) is real and does change the *prompt text*, but this audit found no direct evidence this session that it
  measurably changes *deployment success rate* over time, and the recent -1.471 delta plus the still-growing 58-name
  `response_shortening` family are direct evidence *against* the loop reliably improving outcomes, even though the mechanics of the
  loop are all real and independently verifiable.
- **Evidence**: HIGH for "the loop runs, logs, and updates RiverBrain for real"; LOW/MIXED for "the loop demonstrably improves
  anything," and the most recent real data point is a negative one.
- **Persistence**: yes, all file-backed and restart-surviving.
- **Competing explanation**: a system that safely, repeatedly rejects most of its own output (Finding 19's fitness gate) while still
  producing near-duplicate attempts at high volume is arguably *demonstrating the safety gate working as intended*, not demonstrating
  learning failure — both readings are consistent with the same data; this audit does not adjudicate between them, only reports both.

### RiverBrain / `model_task_stats` / council deliberation — **FRUIT** (routing signal), **DEAD** (one specific consumer)

- **Trigger**: every real council deliberation, self-edit attempt, and echo_projects generation.
- **Code**: `RiverBrain.learn()` (`echo_model_orchestrator.py`), read by `_select_council()`/`choose_model()`'s exploration-floor logic.
- **Output/storage**: `memory/river_brain.pkl`.
- **Directly re-verified this session, via the real, live `get_river_brain()` singleton (not an isolated unpickle)**: `model_task_stats`
  holds real, large, differentiated per-(model, task_type) statistics across **12 models** — e.g. `echo:latest`: `coding` n=49,139
  mean=0.594, `personal` n=43,460 mean=0.657, `self_edit_coding` n=7,908 mean=0.854, `echo_projects_coding` n=1,282 mean=0.836;
  `qwen2.5-coder:7b`: `coding` n=9,932 mean=0.647. This is unambiguously real, live, continuously-updated state, directly contradicting
  any characterization of `model_task_stats` as dead — **it is a confirmed real reader/consumer, separate from the dormant
  `learn_from_council_rating()` path below.**
- **Reader/consumer/decision affected**: `_select_council()`'s exploration floor (Finding 10) and `TAG_SCORE_BOOST` (Finding 39) read
  this data to influence which models are selected for a council — a real, demonstrated routing effect (see "routing adaptation"
  below for the one disclosed limitation).
- **Evidence**: HIGH — directly read from the live production singleton this session, not inferred.
- **A separate, real, currently-broken path found this session — `RiverBrain.learn_from_council_rating()`**: wired since Finding 67
  (2026-07-22), gated on `is_council_trusted()` (confirmed true — `snapshot_baseline.json`'s `council_baseline_trusted_since:
  2026-07-22T00:52:13`). **This session traced the actual mechanism end to end and found it has been silently non-functional since
  approximately 2026-08-22 — over 13 days as of this writing:**
  1. `memory/council_cursor.json` reads `{"position": 33471, "updated_utc": "2026-07-26T14:15:33"}` — unchanged for 5+ weeks.
  2. `memory/interaction_log.jsonl` was rotated (gzip+truncate, Finding 51's `log_retention.py`) on **2026-08-22** — confirmed directly:
     `memory/interaction_log.jsonl.1.gz` exists with that exact mtime, and the *current* live file's first entry timestamp is
     `2026-08-22T17:55:41` (i.e., the live file is younger than the rotation).
  3. The current live file has **11,970 lines** — less than the stale cursor's `33471`. `council_rater.py`'s `_poll_and_rate()` reads
     `lines[cursor:]`; since `11970 < 33471`, this slice is **empty on every single poll cycle**, and the function returns before ever
     reaching `_save_cursor()` — a silent, no-exception stall (confirmed: zero `[Council] Loop error` or `_poll_and_rate error` lines
     anywhere in `echo_watchdog.log`, and the `CouncilRater` thread is confirmed alive and restarting normally across every server
     restart — 14 real "Background rater started" lines observed, most recently for the current live process).
  4. `memory/council_ratings.jsonl` has grown by only **17 entries** since council trust was set on 2026-07-22 (116 → 133,
     re-confirmed via `wc -l`) — consistent with the rater having functioned normally for ~4 days after trust was set, then stalling
     at the rotation.
  - **This is a real, current, previously-unreported defect: the log-rotation mechanism (Finding 51, a genuine, independently-verified
    fix) and the council-rating cursor mechanism (Finding 67) are mutually incompatible, and nothing in this codebase reconciles a
    line-position cursor against a file that can be silently reset out from under it.** Reported here per the mission's explicit
    instruction; **not repaired**.
  - **Classification: `learn_from_council_rating()`'s actual training-signal contribution is `DEAD`, right now, as of this
    investigation** — not merely dormant-by-low-volume, but structurally unable to advance until either the file regrows past
    33,471 lines (implausible before the next rotation at current growth rates) or a human/future session intervenes. The routing
    signal `model_task_stats` feeds (via `learn()`, not `learn_from_council_rating()`) is unaffected by this and remains genuinely
    live, per above.
- **Persistence**: `river_brain.pkl` is real and persists across restarts; `council_cursor.json` also persists, which is precisely why
  its staleness is durable rather than self-correcting.
- **Competing explanation**: it is possible the interaction_log's post-rotation growth rate will eventually exceed 33,471 lines again
  (at ~53 entries/hour observed this session, that would take roughly 26 more days from the rotation, i.e. around 2026-09-17) — at
  which point the cursor would suddenly "unstick" on its own without any code change, `new_lines` would become non-empty, and rating
  would silently resume. This audit does not know whether that has already been anticipated or is coincidental; it is stated as a
  plausible, if slow, self-resolution path, not a repair.

### Self-model updates + shadow self-model/accuracy — **FRUIT** (shadow-model tracking), **ACTIVITY** (self_model.json itself)

- **Trigger**: `SelfModelUpdater`'s fixed 130s timer; `emergent_scheduler.py`'s reflection cycle calling `propose_from_reflection()`.
- **Output/storage**: `memory/self_model.json`, `memory/shadow_self_model.json`, `memory/shadow_accuracy.jsonl`.
- **Re-confirmed this session, both genuinely live, not stale documentation**: `self_model.json`'s `last_updated` reads
  `2026-09-04T04:38:43` — minutes old relative to this check. `shadow_accuracy.jsonl` has **2,035 real lines**, with the newest entry
  (`2026-09-04T04:34:59`) showing a real, non-trivial comparison: `shadow_focus: "personal"` vs. `real_focus: "coding"`,
  `focus_matches: false`, a real per-task `quality_delta_from_shadow`. **This directly confirms Finding 35's own retraction (the
  "shadow_model.propose() has zero callers" claim was wrong) remains correct today — the mechanism is genuinely, continuously live.**
- **Reader/consumer/decision affected**: `self_model.json`'s content is read by `echo_ground_truth.py`'s various `_build_*()` slices
  (capabilities, affect, coupling, workspace, council) for prompt grounding — a real, demonstrated read path into what a live
  conversation sees. The *shadow* comparison itself (predicted focus vs. real focus) is logged but this audit found no evidence this
  session that a mismatch (like the one just observed) itself triggers any corrective action anywhere — it is compared and recorded,
  not (yet) acted on.
- **Evidence**: HIGH for "both files are genuinely live and growing"; MEDIUM/LOW for "the shadow-accuracy comparison changes anything"
  beyond its own log.
- **Persistence**: yes.
- **Competing explanation**: a system that accurately logs its own prediction misses (as this one does, honestly, right now — a
  `false` match logged plainly) is a real, if narrow, metacognitive capability worth distinguishing from a system that either doesn't
  check or doesn't record its misses; this audit classifies the *tracking* as real, while being explicit that tracking alone is not
  the same as correction.

### Global Workspace (publish/consume) — **FRUIT** (river_deliberation's exploration-bias consumption, directly observed live)

- **Trigger**: any of 6+ real publishers (`world_model`, `emergent_loop`, `river_deliberation`, `reflection_shard`, `echo_optuna`,
  `seam_engine`, `self_edit_manager`'s dissent path, `dream_cycle`).
- **Output/storage**: `memory/workspace_log.jsonl`.
- **Re-confirmed this session, directly, not from documentation**: the last 500 events span **6 distinct real sources**
  (`emergent_loop` 326, `echo_optuna` 88, `world_model` 35, `river_deliberation` 34, `reflection_shard` 16, `seam_engine` 1) —
  genuine multi-subsystem diversity, matching the `global_workspace` Liveness Ledger check's own standard. A real
  `"type": "workspace.consumed", "source": "river_deliberation", "summary": "exploration_bias=0.001 (from cache)"` event was directly
  observed at `2026-09-04T04:40:45` — proof the consumption side is live right now, not merely wired since Phase 4.
- **Reader/consumer/decision affected**: `river_deliberation.py`'s `exploration_bias` (Finding 80's valence-adjusted version) is a real
  input to a real Bernoulli gate controlling whether a council swap happens — this is a genuine, if probabilistically small
  (`0.001` observed), causal input to council composition.
- **Evidence**: HIGH — the specific event, its timestamp, and its causal target (`exploration_bias`) were all directly read this
  session from the live log, not reconstructed from design documents.
- **Persistence**: yes.
- **Competing explanation**: a `0.001` probability is a real but extremely faint causal lever — this audit classifies the mechanism as
  `FRUIT` because the definition requires only a demonstrated changed downstream decision path, not a large one, but flags plainly that
  its practical magnitude, right now, is small.

### Behavioral-state persistence (`app/core/behavioral_state.py`) — human-directed only; **no autonomous-originated instance found**

- **Trigger**: **by explicit design, human-confirmation only** — every mutating function (`propose_and_confirm_directive`,
  `delete_directive`, `rollback_to_backup`) hard-requires the literal `human_confirmed=True`, raising `BehavioralStateError` otherwise.
  The module's own header states plainly: *"THIS IS NOT A LEARNING MECHANISM... No autonomous mutation exists anywhere in this file."*
- **This audit's specific job here — distinct from prior human-directed demonstrations — was to search for an AUTONOMOUS-originated
  path. None was found.** `echo_ground_truth.py` is the module's only real caller in the live app, and it calls only
  `get_matching_directives(prompt)` — a pure read.
- **Output/storage**: `memory/behavioral_directives.json`. **Current live state, checked directly this session: `{"directives": [],
  "version": 1}` — empty.** The audit log (`behavioral_directives_audit.jsonl`) shows one real directive (id `8722f4d4...`) was
  created, matched a prompt twice (`read_match`), then deleted — all with `human_confirmed: true` — timestamped consistent with a
  same-day validation exercise, not a standing production directive.
- **Reader/consumer**: `get_matching_directives()` is wired into prompt construction — a real, demonstrated read path, exercised twice
  (per the audit log) before being cleared.
- **Evidence**: HIGH that the mechanism is real, functional, and (per its own design) exclusively human-gated; the specific autonomous
  instance this audit was asked to look for does not exist, and the module's own source makes clear why it structurally cannot.
- **Classification, per the audit's own autonomous-vs-directed rule**: this subsystem is **excluded from any autonomous-fruit claim**
  regardless of how effective it is, because the causal signal (the directive's content and its very existence) originates from a
  human, not from an autonomous subsystem. Its demonstrated read-path effectiveness is real but attributable to the human who
  confirmed the directive, not to autonomy.

### Memory / FAISS retrieval — **ACTIVITY** at scale, with a real, current, demonstrated **hygiene fix** (see knowledge acquisition)

- **Trigger**: every real conversational turn (`retrieve_relevant_memories()`), dream cycles, curiosity/seam question harvesting.
- **Output/storage**: `memory/memory_meta.json` + `memory/faiss.index` — **123,793 total entries**, re-confirmed this session.
- **Reader/consumer**: real — this is the actual similarity-search backing real conversational grounding and the dream cycle's
  material sampling.
- **Decision/action affected**: real for the *conversational grounding* case (a retrieved memory genuinely becomes part of a real
  prompt) — but the memory-ablation experiment this project already ran (`audits/2026-07-23_memory_ablation_experiment.md`,
  not re-run this session) found the measured effect on response embedding-distance was statistically indistinguishable from the
  system's own sampling noise floor for the `personal`/direct-response path specifically — a prior, not-contradicted-this-session
  finding that "retrieval happens" does not by itself establish "retrieval demonstrably changes the response" at the tested
  granularity. **A follow-up attempt exists, checked this session**: `scripts/memory_ablation_results_nonpersonal_2026-09-03.json`
  (stratified across `coding`/`creative`/`reasoning`/`general`, the exact gap the original experiment's own text flagged as
  untested) contains only 5 real prompt/metadata pairs and **no computed distance values for any of them, and an empty
  `noise_floor` list** — read directly, not assumed complete. This looks like an interrupted or not-yet-finished run, not a
  completed result contradicting or confirming the original `personal`-path finding. Recorded here as an unresolved, in-progress
  artifact, not double-counted as new evidence either way.
- **Evidence**: HIGH for "retrieval is real, live, and large-scale"; the prior ablation result (not independently re-run here, cited
  as context, not re-verified) is the relevant caution against assuming retrieval implies causal influence.
- **Persistence**: yes.
- **Competing explanation**: 48.4% of this entire store being `code_analysis` (see above) is itself evidence that *scale* of a memory
  store is not evidence of *quality* or *use* — the single largest category by volume is confirmed excluded from retrieval entirely.

### Routing adaptation — **ACTIVITY**, with one real, disclosed structural limitation re-confirmed this session

- **Trigger**: every real council selection (`_select_council()`) and self-edit model choice (`choose_model()`).
- **Reader/consumer**: `_select_council()`'s exploration floor and `TAG_SCORE_BOOST` genuinely read `model_task_stats` (see RiverBrain
  above) — a real, demonstrated routing effect on *council composition*.
- **A specific, previously-disclosed limitation, spot-checked this session rather than re-derived from scratch**: Finding 44's own
  text states `choose_model()`'s *primary* ranking still comes from a separate mechanism (`rank_models()`, reflection-log-based) that
  never reads `model_task_stats` at all — meaning the richest, most-fed signal in the system (49,139 real `coding` observations for
  `echo:latest` alone) demonstrably does **not** drive the single most consequential routing decision (which model gets chosen first)
  for self-edit's own code generation. This session did not re-derive this from source but did confirm the underlying data
  (`model_task_stats`) that would need to be read is genuinely rich, sharpening rather than resolving the gap.
- **Evidence**: MEDIUM — the exploration-floor/tag-boost effect is real and demonstrated; the "primary ranking ignores the richest
  signal" limitation is a real, disclosed, structural gap, not fully re-verified against current source this session.
- **Competing explanation**: none of significance.

### Autonomous background loops + scheduling — **ACTIVITY** at real, substantial, currently-measured volume

- **Trigger/code**: `emergent_loop`, `AutonomousSelfEdit`, `model_guided_autonomous_loop`, `ReflectionShardAutonomy`,
  `EchoProjectsAutonomy`, `autonomous_loop` (fetch), `DMN Guardian`, `night_cycle`.
- **Directly measured this session, not estimated**: 53 real `interaction_log.jsonl` entries in the last observed hour (a mixed
  proxy for conversational + autonomous LLM call volume, since both write to the same log); real, live `[DELIBERATION]` log lines
  observed for `AutonomousSelfEdit` and `model_guided_autonomous_loop` running full 3-councillor-plus-synthesis cycles within the
  same ~5-minute observation window; `qwen2.5-coder:7b` resident in `ollama ps` with an actively-refreshing keep-alive countdown at
  the moment of this check.
- **Decision/action affected**: each individual loop's own real effects are covered under its own entry above (self-edit, curiosity,
  reflection, echo_projects). This entry exists specifically to record that the aggregate *cadence and concurrency* is real and
  substantial, which is directly relevant to §5/§10/§11 below.
- **Evidence**: HIGH — directly observed, live, this session.
- **Competing explanation**: none.

### Metacognitive outputs (`echo_ground_truth.py`'s self-report slices) — **FRUIT** (grounds real conversational output)

- **Trigger**: keyword-gated per real user/conversational prompt (capabilities, affect, coupling, workspace, council slices).
- **Output**: real, computed-and-rendered text folded into real system prompts.
- **Consumer/decision affected**: this directly changes what a real conversation's system prompt contains, which is as close to
  "changed downstream behavior" as a text-generation system has — **but this is triggered by, and serves, a real user-facing
  conversational turn**, not an autonomous cycle. Per the audit's own autonomous-vs-directed rule, the *grounding accuracy* (does the
  rendered valence direction match the real signed state) is a real, demonstrated, self-consistent effect, but its trigger is the
  conversational request pipeline, not autonomy — recorded here as `FRUIT` for the conversational path specifically, explicitly not
  claimed as autonomous fruit.

### Error correction (Dissent Log, crash_awareness/MLX avoidance) — **split**: Dissent Log effectively unused; crash avoidance is real **FRUIT**

- **Dissent Log** (`memory/dissent_log.jsonl`): **exactly 1 real entry, ever**, dated 2026-07-17 — re-confirmed this session
  (`wc -l` = 1). By design this is human-invoked-only (`!propose`), so a single historical validation call is the expected shape, not
  a new finding — but it means this mechanism has produced **zero** real autonomous or even repeated human-directed activity in the
  ~7 weeks since. Classification: **effectively unused**, not dead (it would work if invoked), not fruit (it has affected nothing).
- **Crash avoidance** (`app/core/crash_awareness.py`, Findings 51/73): re-confirmed this session — `"MLX-AVOIDANCE"` appears **14 times**
  in the live watchdog log, a real, recurring, autonomous-originated pattern: a real crash cluster is detected → `mlx:*` models are
  genuinely excluded from the live `MODEL_POOL` for a cooldown window → this demonstrably changes real council composition for that
  window (fewer real candidate models). This is a clean, autonomous-originated, closed causal chain: **trigger (real crash) → output
  (avoidance decision) → consumer (`list_mlx_models()`, read by every real council selection) → demonstrated behavioral change (MLX
  models absent from real councils during the window)**. Classified `FRUIT`.

### Question of "goal persistence" — **DEAD** (the one candidate artifact found is inert)

- The only file-system artifact matching "goals" outside the curiosity garden (already covered above) is a root-level `goals.txt`
  (*"Master the art of coding / Learn machine learning / Write a novel"*). Re-confirmed this session: **zero** references to this
  filename anywhere in `app/` or `run.py` (`grep -rl` returns nothing), and its git history shows a single commit from **2026-07-04**,
  two months stale. Classified `DEAD` — a static, orphaned artifact, not a live goal-persistence mechanism. The curiosity garden (see
  above) is this project's actual, real, functioning analogue of persisted "things to pursue," and is classified there instead.

---

## 3. Causal-Chain Evidence

| Autonomous producer | Output | Reader | Consumer | Downstream consequence | Evidence |
|---|---|---|---|---|---|
| `crash_awareness.py` (real crash detection) | avoidance decision, cooldown window | `list_mlx_models()` | every real council selection during the window | MLX models genuinely absent from real councils | **HIGH** (14 real log occurrences) |
| `river_deliberation.py` (world-surprise consumption) | `exploration_bias` value | Bernoulli gate in `_select_council()` | council-swap decision | real, small (`p=0.001` observed) chance of an extra council slot swap | **HIGH** (directly observed live `workspace.consumed` event, 2026-09-04T04:40:45) |
| curiosity garden (`garden_manager`) | a real harvested question | `echo_projects.autonomous_generate_project()` | the autonomous project-generation cycle | a real project spec (verbatim garden text) | **HIGH** (directly traced this session) |
| curiosity garden / seam_engine / dream_cycle | harvested questions | `emergent_scheduler.select_from_garden()` | next autonomous reflection prompt selection | which topic gets reflected on next | **MEDIUM** (mechanism confirmed live; magnitude of behavioral change not independently measured this session) |
| self-edit's `plan_code_logic()` | a real numbered plan | `generate_code_from_plan()` | next candidate-code generation | the literal candidate code generated | **HIGH** (direct causal link by construction, confirmed live sample) |
| self-edit outcomes / echo_projects | quality deltas | `RiverBrain.learn()` | `model_task_stats` | real, large, per-model/task scoring state | **HIGH** (directly read from live singleton: 12 models, up to 49,139 obs/bucket) |
| `model_task_stats` | scoring state | `_select_council()` exploration floor, `TAG_SCORE_BOOST` | council composition | real influence on which models are selected | **HIGH** (mechanism re-confirmed; `choose_model()`'s *primary* rank still bypasses it — see routing adaptation) |
| council ratings (`council_rater.py`) | a per-entry rating | `RiverBrain.learn_from_council_rating()` | `model_task_stats` (blended) | **NONE currently** — pipeline stalled since ~2026-08-22 | **HIGH confidence this is currently non-functional** (cursor/rotation mismatch directly traced) |
| `echo_projects` council-generated code | multi-file project | (none — no importer exists) | — | none | **NONE** (0/61 F2-passing, directly re-measured) |
| `reflection_shard.py` meta-synthesis | `reflection.meta_synthesis` event | Global Workspace wide-broadcast | `reflection_shard.observe()`, curiosity topic-bias (per Finding 78/CLAUDE.md) | plausible, not directly re-traced end-to-end this session | **MEDIUM** (write+broadcast confirmed; this session's one directly-observed consumption event was from a different source) |
| `behavioral_state.py` directives | a matched directive's text | `echo_ground_truth.py` prompt construction | real conversational system prompt | real, but **human-originated**, excluded from autonomous-fruit tally | **HIGH** (mechanism real; currently zero live directives) |
| daily code-scan | `code_analysis` memory entries | `retrieve_relevant_memories()` | — (now excluded) | prevented, not caused, a downstream effect | **HIGH** (exclusion + zero-new-in-24h both directly confirmed) |

## 4. Quantitative Activity

| Subsystem | Activity (this session's direct evidence) | Unique outputs | Persisted | Read | Consumer | Demonstrated behavioral effect | Classification | Confidence |
|---|---|---|---|---|---|---|---|---|
| Curiosity garden | growing | 13,470 entries | Yes | Yes (3 real readers) | `emergent_scheduler`, `echo_projects` | Prompt/topic selection changes | POTENTIAL_FRUIT | HIGH |
| Reflection shards | growing, ~300s/35% cadence | 20,526 entries | Yes | Global Workspace (confirmed live) | `river_deliberation` (workspace, general) | Plausible, not end-to-end traced this session | ACTIVITY / narrow POTENTIAL_FRUIT | MEDIUM |
| Self-edit planning | ≤1 real deploy/hr + ~10 dry-run/hr | plan text per cycle | Yes (capped 500) | `generate_code_from_plan()` | self-edit pipeline itself | Determines candidate code | FRUIT (internal only) | HIGH |
| echo_projects | 6h autonomous cadence + manual | 61 project dirs | Yes (capped 60) | human (report), no code importer | none | 0/61 F2 pass | ACTIVITY | HIGH |
| Knowledge acquisition (code-scan) | daily | 0 new in last 24h (post-fix) | Yes (59,910 historical, frozen) | excluded from retrieval | — | Prevented contamination | POTENTIAL_FRUIT (hygiene) | HIGH |
| Self-editing outcomes | 179 real evaluated records | mixed quality deltas | Yes | `self_edit_outcome_tracker`, RiverBrain | model scoring | Real but weak/mixed (+0.135, -1.471, null recent) | POTENTIAL_FRUIT | HIGH |
| RiverBrain `model_task_stats` | continuous | 12 models × up to 7 task buckets | Yes | `_select_council()`, `TAG_SCORE_BOOST` | council composition | Real, demonstrated | FRUIT | HIGH |
| `learn_from_council_rating` | **0 effective since ~2026-08-22** | 17 ratings since trust (2026-07-22), then stall | Yes (stale cursor) | — (structurally blocked) | — | None currently | DEAD (currently) | HIGH |
| Self-model / shadow model | continuous, minutes-fresh | 2,035 shadow-accuracy records | Yes | `echo_ground_truth` | real conversational prompts | Real read path; mismatch logged, not acted on | FRUIT (self_model read) / ACTIVITY (shadow comparison) | HIGH |
| Global Workspace | continuous | 6 distinct real sources / 500-event window | Yes | `river_deliberation` (confirmed live) | `exploration_bias` gate | Real, small magnitude | FRUIT | HIGH |
| Behavioral-state directives | human-gated only | 0 live directives (1 created+deleted today) | Yes | `echo_ground_truth` | real prompts, when a directive exists | Real, but human-originated | EXCLUDED from autonomous tally | HIGH |
| Memory/FAISS retrieval | continuous, large | 123,793 total entries (48.4% code_analysis) | Yes | real conversational retrieval | real prompt construction | Real for grounding; magnitude questioned by prior ablation result | ACTIVITY | MEDIUM |
| Dissent Log | dormant | 1 entry (2026-07-17) | Yes | human review only | human | None since single historical use | ACTIVITY (effectively unused) | HIGH |
| Crash avoidance | recurring | 14 log occurrences | Yes | `list_mlx_models()` | council composition | Real, demonstrated | FRUIT | HIGH |
| Goal persistence (`goals.txt`) | none | 3 static lines | Yes (inert) | none | none | None | DEAD | HIGH |

## 5. Resource Cost

Framed explicitly as *resource cost vs. demonstrated downstream fruit* — not as evidence the cost is unjustified; several real,
demonstrated fruit items above (crash avoidance, exploration-bias consumption, curiosity→project spec) exist alongside this cost, and
this section does not net them against each other.

- **Ollama call volume**: 53 real `interaction_log.jsonl` entries in one directly-observed hour (mixed autonomous + conversational);
  real, live multi-councillor deliberations (3 councillors + synthesis, ~2-4 minutes wall-clock each) were directly observed for both
  `AutonomousSelfEdit` and `model_guided_autonomous_loop` within the same ~5-minute window — i.e., **concurrent** real inference
  demand from at least two autonomous loops simultaneously, consistent with the contention this project's own prior Tier-3 preflight
  investigations repeatedly measured.
- **Model residency / GPU**: `qwen2.5-coder:7b` (5.0GB) resident and 100% GPU-utilized at the moment of this check, with an
  actively-refreshing (not idle) keep-alive countdown.
- **Memory pressure**: `vm.swapusage` reads **5.6GB of 7.0GB swap used** (encrypted) at the time of this check — real, current
  pressure, consistent with this project's own repeatedly-documented history of Ollama-queue contention.
- **Disk**: `memory/` totals **1.2GB** (down from Finding 30's 2.0GB baseline after historical cleanup, but growing again from ongoing
  activity); `memory/memory_meta.json` alone backs 123,793 vector entries, 48.4% of which are confirmed excluded from any real use.
- **CPU**: at the instant sampled, the production `run.py` process itself showed near-zero CPU (I/O-wait-dominated, consistent with
  waiting on Ollama), while `llama-server` (Ollama's own inference process) was the actual compute consumer.
- **Wall-clock inference time**: individual real council cycles observed this session took roughly 2-4 minutes end-to-end
  (3 councillor queries + synthesis), matching this project's own prior-documented per-cycle timings.

## 6. Strongest Demonstrated Autonomous Fruit

**Crash avoidance (`crash_awareness.py`).** This is the cleanest, most defensible FRUIT in this audit: the trigger (a real native
crash) originates entirely from the system's own operating conditions, not from any user action; the output (an avoidance decision)
is autonomously computed; the consumer (`list_mlx_models()`) is read by every real council selection; and the behavioral change
(MLX models genuinely absent from real councils during the cooldown) is directly, repeatedly observed (14 real log occurrences) —
every link in the required chain is independently verifiable, and none of it depends on a human having supplied the causal signal.

**Runner-up**: `RiverBrain.learn()`'s feeding of `model_task_stats`, which is real, large-scale, continuously live, and does
demonstrably influence council composition via the exploration floor and tag-boost — weakened only by the disclosed, unresolved fact
that the system's *primary* model-ranking mechanism doesn't read this same signal.

## 7. Largest Activity-Without-Fruit Subsystem

**`echo_projects`.** By computation volume (61 real multi-file generation cycles, each involving a real council-planning
deliberation, N real per-file generations, and a real 3-model council review — a materially larger per-cycle compute footprint than
almost anything else audited) and by the cleanliness of its null result (0/61 ever reaching a working end state, with **no** automated
reader of the generated code existing anywhere), this is the largest confirmed gap between resource expenditure and demonstrated
downstream value in this audit. It is not classified `DEAD` (it runs on schedule, exactly as designed, and does produce real,
human-readable artifacts) — but its practical yield, measured honestly against 61 real attempts, is zero.

## 8. Dead/Dormant Paths

- **`RiverBrain.learn_from_council_rating()`** — currently non-functional (see §2, §3), due to a stale line-position cursor left
  behind by a log-rotation event on 2026-08-22. Real, previously-functioning (17 ratings between 2026-07-22 and the stall), now dead
  in practice until either the file regrows past the stale cursor's position or a future session intervenes.
- **Dissent Log** — functional but effectively unused: 1 entry, ever, from 2026-07-17.
- **`goals.txt`** — orphaned, unreferenced, two months stale.
- **`echo_projects`'s generated code** — no automated reader exists anywhere; the pipeline's own design (Finding 83) makes this
  permanent by intent, not an oversight.

## 9. Important Unknowns

- Whether `reflection.meta_synthesis`'s specific Global Workspace events (as opposed to the mechanism in general, which this session
  directly confirmed live) have themselves been consumed and changed a specific downstream decision — plausible per CLAUDE.md's own
  Finding 78/6, not independently re-traced end-to-end this session. **Marked UNKNOWN, not assumed.**
- Whether the interaction-log growth rate will in fact carry `council_cursor.json`'s stale position back into range before the next
  rotation (estimated ~2026-09-17 at the observed ~53/hour rate) — a plausible but unverified self-resolution path, stated as a
  possibility, not a prediction this audit stands behind.
- The exact reason `reflection_shard.jsonl` contains at least one self-edit-planning-shaped entry rather than only ordinary
  reflections — observed directly this session, not investigated to root cause (out of scope; flagged per the mission's "report,
  don't silently repair" instruction, though this is closer to "noticed, not explained" than "found broken").
- The prior memory-ablation experiment's conclusion (retrieval effect indistinguishable from noise floor for the `personal` path) was
  cited, not re-run, this session — its applicability to the multi-councillor `coding`/`creative`/`reasoning` paths remains untested;
  a follow-up attempt exists on disk (`scripts/memory_ablation_results_nonpersonal_2026-09-03.json`) but its results file contains no
  computed distances (see §2, memory/FAISS retrieval) — genuinely unresolved, not merely uncited.
- Whether `echo_projects`'s 0/61 result reflects a genuine, stable capability ceiling for the current model pool, or would improve
  materially with a different model pool or prompt design — this audit observed the *rate*, not the *cause* of each individual F1/F2
  failure in aggregate (a small sample of individual failure reasons was read directly, e.g. syntax errors in generated files, but a
  full failure-mode taxonomy across all 61 was not built).

## 10. Resource-vs-Fruit Assessment

The autonomous workload's resource cost (real, continuous, multi-loop Ollama demand; measurable swap pressure; gigabyte-scale
persisted state) is **not small**, and a meaningful share of it — most visibly `echo_projects`'s 61 real, expensive, 0%-successful
generation cycles, and the 48.4% of the entire memory store that is confirmed-excluded `code_analysis` content — demonstrably produces
no downstream behavioral consequence by this audit's required standard. At the same time, a real, if smaller, set of mechanisms
(crash avoidance, the RiverBrain `model_task_stats` routing signal, the Global Workspace's exploration-bias consumption, the
curiosity-garden→project-spec link) clear the full causal-chain bar this audit set, and do so with direct, current, repeatable
evidence rather than inference. Per the mission's own standard, this is reported plainly as a mixed picture, not rounded toward either
extreme.

## 11. Tier-3 Operating Recommendation

# THROTTLE_FOR_EXPERIMENT

Reasoning, stated against the four defined options: `PRESERVE_AUTONOMY` would require strong evidence of meaningful downstream
effects broadly across the workload — not supported; most of the largest-volume mechanisms (`echo_projects`, the bulk of daily
memory writes, the now-confirmed-dormant council-rating path) show weak-to-zero demonstrated effect. `SAFE_TO_PAUSE_FOR_EXPERIMENT`
would require little/no demonstrated fruit relative to cost — too strong a claim given the real, repeatable, autonomous-originated
fruit this audit did confirm (crash avoidance changing real council composition; the RiverBrain routing signal; the Global Workspace
consumption path), each of which this document explicitly declines to inflate but also cannot honestly describe as absent.
`INCONCLUSIVE` would understate what this audit actually established — the evidence is not thin, it is mixed and, in several places,
concrete in both directions. **`THROTTLE_FOR_EXPERIMENT`** best matches what was found: real effects exist and would very likely
survive a reduced cadence (crash avoidance and the RiverBrain signal do not depend on high-frequency polling to remain meaningful; the
council-rating path is already non-functional regardless of throttling), while the workload's dominant resource costs
(`echo_projects`'s expensive, 0%-successful cycles; the continuous multi-loop Ollama contention this project has repeatedly measured
elsewhere) are exactly the kind of load a Tier-3 measurement window would most benefit from reducing, without plausibly destroying any
of the fruit this audit actually confirmed. **This is a recommendation only; no production behavior was changed to produce it.**

## 12. Evidence Trail

All commands were run read-only, directly against the live repository and runtime state, during this investigation
(2026-09-03/04). Representative commands (full session commands are reproduced in the companion JSON's `evidence_commands` field):

- `wc -l memory/interaction_log.jsonl memory/council_ratings.jsonl data/question_garden.jsonl memory/reflection_shard.jsonl memory/dissent_log.jsonl memory/shadow_accuracy.jsonl audits/tier3_apparatus/dev_sanity_results.jsonl`
- `cat memory/council_cursor.json memory/snapshot_baseline.json memory/echo_projects_autonomy_state.json`
- direct `get_river_brain()` call (via `app.core.echo_model_orchestrator`) inspecting the live `model_task_stats` singleton
- `grep -c "MLX-AVOIDANCE" / "\[Council\] Background rater started" / "\[Council\] Loop error"` against `memory/echo_watchdog.log`
- `grep -l "BLOCKED" / grep -l "^# F2"` across all 61 `sandbox/echo_projects/*/_report.md` files
- `python3 -c` inline scripts computing `memory_meta.json`'s total/`code_analysis` split and 24h-recency check
- `ps aux`, `ollama ps`, `sysctl vm.swapusage`, `du -sh memory/`
- `find . -iname "*held_out*"` (zero results); `git status --porcelain` / `git diff --stat` for production-file change provenance
- `grep -rln "goals.txt"` (zero results); `git log -1 -- goals.txt`

**Held-out protection, final re-confirmation**: `find . -iname "*held_out*"` returns nothing anywhere in the repository. No held-out
task ID appears in any file read or command run during this audit. `audits/capability_pilot/task_suite.json`'s hash was not
re-touched by this objective (see the companion Objective 1 report for its own independent re-verification). Nothing in this audit
executed, referenced, or loaded any held-out task.
