# RiverBrain Independent-Outcome Reward Wire — Design Audit

Date: 2026-09-23. Investigator: Claude M5. Method: read-only, adversarial forensic design audit. No connection was built. No experiment was run. No persistent state was written by this mission's own actions.

**Central question:** can FeralEcho's existing independent outcome signals be connected to an existing persistent behavioral consumer in a way that creates a falsifiable experiment for retained learning — and, if so, what would success actually establish? This report does not assume the answer is yes.

**Opening HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce`. **Closing HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged. **Working-tree delta:** a `git status --porcelain` snapshot (231 entries) was captured before this mission's first read and diffed against the same command at report-writing time; the only difference is this report's own new, untracked path. One read-only inspection of the live `memory/river_brain.pkl` was performed via a bare, isolated `pickle.load()` in a fresh `python3 -I -B` subprocess, never through `get_river_brain()` and never importing `echo_model_orchestrator` — the file's mtime and byte size were captured before and after and are bit-for-bit identical (`1790197762 4702634`, both times), confirmed in §23.

---

## 1. Executive verdict

**The "broken reward wire" diagnosis is CONFIRMED, and this mission's own direct re-derivation from current source sharpens it into an exact, quantified statement rather than a qualitative one.** `learn_from_sandbox_outcome()` and `learn_from_rating()` genuinely never write `model_task_stats` — confirmed by reading both method bodies in full, this mission, independent of any prior report's characterization (§4, §5, §6). The one signal that both writes `model_task_stats` and originates from something other than a response scoring its own text — `learn_from_council_rating()` — is real, live, and has genuinely fired in production, but at a scale that makes it a rounding error against the dominant path: **70 real council-vetted observations against 207,554 total real observations across all of `model_task_stats`, roughly 0.034%** (OBSERVED, direct, safe read of the live pickle, §7). The dominant path, `learn()`, trains on a label derived from `_score_response_quality()` scoring the *same response text* whose producing model is being credited — a self-referential evaluator, not an independent one (§7).

**`score_model()` does causally affect real production model selection**, and this is not merely inferred — it is a direct, deterministic arithmetic fact readable straight from `rank_models()`'s source: `combined[model] = (legacy_weight * legacy_score) + (river_weight * river_score)`, where `river_score` is `score_model()`'s return value, `river_weight` is `RiverBrain.influence_weight` (a real, computed property currently near its 0.65 ceiling given the live observation volume, §8), and `ranked = sorted(combined.items(), ...)` directly determines `choose_model()`'s selection order (§8). No separate empirical ablation is required to establish this specific causal link — it is a deterministic computation, not a statistical inference — though no live experiment has ever measured *how much* real production selection frequency shifts as a result, at scale.

**A real, independent, high-volume evaluator already exists and is already computed — real sandbox executions, 16,208 of them for the `coding` task type alone (OBSERVED, live pickle read, §7)** — and it is discarded at exactly the point the earlier diagnosis identified: trained into a separate scaler/classifier pair and a separate counter (`sandbox_observation_counts`) that nothing downstream of `learn_from_sandbox_outcome()` ever reads into `model_task_stats`. This is the single most concrete, quantified confirmation this mission can offer: **16,208 real, independent, discarded observations sitting one method-boundary away from the exact statistic `score_model()` reads.**

**The naive fix ("just make these methods also update `model_task_stats`") is not scientifically defensible without repair, for reasons this mission independently reconstructs and finds are real, not merely inherited (§11):** the two sandbox-outcome producers (self-edit's F2 import-execution gate and conversational code-verification's claimed-output check) test qualitatively different things under one label; `learn_from_rating()`'s human ratings are sparse, correctness-conflated-with-preference, and arrive asynchronously from the response's own generation context; and the same `_MEAN_EFFECTIVE_WINDOW=200` EMA mechanics already identified as a real, unfixed ceiling for interpreting any staged-vs-continuous accumulation claim apply identically to any new writer of the same field.

**Verdict on the central question: PARTIAL YES, WITH A REQUIRED, EXPLICITLY-NAMED NEW COMPONENT.** FeralEcho's existing pieces — the independent sandbox oracle, the frozen persistent-competence protocol's already-adversarially-hardened counterfeit-learner defenses, the causal `score_model()`→`rank_models()` chain, and `behavioral_state.py`'s proven restart-isolation methodology — can, in principle, be recombined into a falsifiable routing-learning experiment (§18) with almost no new architecture. But that experiment would test **routing/policy learning among fixed models, not capability acquisition** (§14), and it requires one genuinely new, currently-nonexistent piece: an isolated, freshly-initialized statistic path (not live `model_task_stats` itself) that a real experiment can populate, restart, and measure without contaminating or being contaminated by the live production pickle's continuous background writer thread (§16). Building that isolation layer is smaller than building a new learning architecture, but it is not nothing, and it is named explicitly per this mission's own instruction rather than glossed over as pure recombination.

## 2. Scope and state integrity

No RiverBrain, `model_task_stats`, `learn_from_sandbox_outcome()`, `learn_from_rating()`, `score_model()`, sandbox machinery, `behavioral_state.py`, `self_model_claims.py`, prompt, configuration, persistent state, Rung-1, `accumulation_probe`, AP-0, E5-mini, frozen-protocol artifact, test, or Git state was modified. No production process was started, stopped, or restarted. No experiment was run that wrote persistent state. `river.bandit` was not activated. Nothing was connected. Nothing was "fixed." The one read of live production state (`memory/river_brain.pkl`) was performed with the explicit safety discipline this project's own prior Tier-7/Tier-8 forensic work already established as safe (a bare, isolated `pickle.load()`, never through the class's own loader or the module-level singleton accessor) — full accounting in §23.

## 3. Artifacts/source inspected

- `app/core/echo_model_orchestrator.py` — the complete `RiverBrain` class (lines 758–1148, read in full: `__init__`, `_init_classifiers`, `influence_weight`, `learn`, `learn_from_sandbox_outcome`, `learn_from_rating`, `learn_from_council_rating`, `score_model`, `observations_for`, `is_well_observed`, `entropy_of_predictions`, `_writer_loop`, `_do_save`, `save`, `shutdown`, `load`), plus `rank_models()` and the opening of `choose_model()` (lines 1153–1227)
- A repo-wide grep census of every reference to `model_task_stats` and every caller of `learn`/`learn_from_sandbox_outcome`/`learn_from_rating`/`learn_from_council_rating`/`get_river_brain()` (excluding `.claude/worktrees/`, a stale agent worktree copy of the repo, and `__pycache__`)
- `app/core/council_rater.py` lines 270–312 (`rate_one_entry()`'s `is_council_trusted()` gate and its `learn_from_council_rating()` call site, with the module's own extensive design-history comments)
- `app/core/self_edit_manager.py` lines 2070–2095 (the F2 sandbox-outcome call site, its own comment explaining why the interim result is deliberately not saved to the reflection log at this point, and the exact success criterion this call site tests)
- A live, read-only inspection of `memory/river_brain.pkl`'s real `model_task_stats`, `sandbox_observation_counts`, and `observation_counts` fields, performed via a bare `pickle.load()` in an isolated `python3 -I -B` subprocess (§23)
- This session's own three immediately-prior missions (`2026-09-23_feralecho_second_pass_deep_research_archaeology.md`, `2026-09-23_self_model_claims_adversarial_learning_audit.md`, `2026-09-23_behavioral_state_forensic_infrastructure_audit.md`), consulted for the frozen persistent-competence protocol lineage's own already-adversarially-hardened content (the v1.0 tie-break counterfeit, the v1.1 fixes, the QUAL-4 null/positive-control battery, and `behavioral_state.py`'s own proven restart-isolation methodology) — every fact drawn from these is marked RETRIEVED, not re-derived a fourth time from the frozen protocol's own primary text in this pass, per this mission's effort budget; where a claim from these prior reports is load-bearing for this mission's own new conclusions, it is flagged as such

## 4. Sandbox-outcome data-flow reconstruction

```
REAL SANDBOX EXECUTION
  │  (OBSERVED — two real, distinct producers, not one:
  │   (a) self_edit_manager.py's F2 import/execution gate — tests whether
  │       staged candidate code imports and runs cleanly (SANDBOX_OK),
  │       NOT whether it is functionally correct against any expected
  │       output; (b) routes_echo_studio.py's code_verification.py path —
  │       actually runs the response's own claimed print-output example
  │       and compares it against real execution, a genuine
  │       correctness-shaped check, narrower in scope, RETRIEVED from
  │       this session's own sibling self_model_claims audit's direct
  │       source read of this exact call site)
  ▼
SANDBOX VERDICT (bool success, code, error)
  ▼
river.learn_from_sandbox_outcome(model_name, success, code, error)
  │  (OBSERVED, direct source read, echo_model_orchestrator.py:870-896)
  ▼
  task_type FORCED to "coding" (hardcoded, line 871 — regardless of
  whether the originating call was self-edit's own "self_edit_coding"
  bucket or an ordinary conversational "coding" request; see §11 for why
  this is a real confound, not a simplification)
  ▼
  IF RIVER_AVAILABLE:
    features = _extract_quality_features(train_text, "coding", model_name)
    self.scalers["coding"].learn_one(features)
    self.classifiers["coding"].learn_one(scaled, quality_score)
    self.sandbox_observation_counts["coding"] += 1   ◄── TERMINATES HERE
  │  (OBSERVED — this is the exact, precise point at which the signal
  │   stops. No line anywhere in this method touches
  │   self.model_task_stats. Confirmed by reading the complete method
  │   body, not by absence-of-a-keyword search alone.)
  ▼
  [IF success: also logs to interaction_log.jsonl, quality_score=1,
   notes="sandbox_feedback" — a real, but separate, persisted trace of
   the outcome, itself never read back into model_task_stats by anything
   this mission found]
  ▼
  ✗ model_task_stats — NEVER REACHED
  ✗ score_model() — NEVER SEES THIS SIGNAL
  ✗ routing/model selection — UNAFFECTED BY REAL SANDBOX OUTCOMES
  ✗ observable behavior — UNAFFECTED
```

**Precise localization, OBSERVED this mission by reading the complete method body:** the signal terminates at `echo_model_orchestrator.py:880`, `self.sandbox_observation_counts[task_type] += 1` — the last stateful write in `learn_from_sandbox_outcome()`. The classifier/scaler trained here (`self.classifiers["coding"]`) is the same object `learn()` also trains, but `score_model()` never queries the classifier at all — it reads only `model_task_stats`'s `mean` field (§7) — so even the classifier-level training this method performs has no path to the consumed statistic either. **This mission's own direct re-derivation confirms the earlier "broken reward wire" characterization exactly, with one refinement the earlier characterization did not make explicit: there are two distinct real sandbox-outcome producers feeding this one shared, disconnected pipe, and they test qualitatively different things (§5's Mission-5-style attack, and §11).**

## 5. Human-rating data-flow reconstruction

```
HUMAN RATING (1-5, e.g. terminal_client.py's bare-digit rating prompt)
  ▼
river.learn_from_rating(model_name, task_type, response_preview, user_rating)
  │  (OBSERVED, echo_model_orchestrator.py:898-918)
  ▼
  IF user_rating == 3: return immediately (neutral ratings skipped)
  ▼
  label = 1 if user_rating >= 4 else 0
  features = _extract_quality_features(response_preview, task_type, model_name)
  self.scalers[task_type].learn_one(features)
  for _ in range(3):
      self.classifiers[task_type].learn_one(scaled, label)     ◄── 3x-weighted
  self.observation_counts[task_type] += 3                       ◄── TERMINATES HERE
  │  (OBSERVED — the complete method body contains no reference to
  │   self.model_task_stats anywhere. This mission independently confirms
  │   this by reading the function in full, not merely by grep.)
  ▼
  ✗ model_task_stats — NEVER REACHED
  ✗ score_model() — NEVER SEES THIS SIGNAL
  ✗ routing/model selection — UNAFFECTED BY REAL HUMAN RATINGS
```

**A real, secondary effect worth naming, distinct from the main disconnection finding:** `observation_counts[task_type] += 3` **does** feed `RiverBrain.influence_weight` (§8's property, which reads `self.observation_counts`) — so a human rating, while never touching `model_task_stats`'s `mean`/`count` fields, does slightly raise the *overall confidence weight* `rank_models()` assigns to RiverBrain's contribution generally, for that task type, across *every* model — an indirect, diffuse, model-identity-blind effect, not a targeted "this model earned more trust" effect. This is a real, if minor, secondary path this mission's own direct trace surfaces that neither prior report in this session's own lineage had explicitly separated out.

## 6. Current `model_task_stats` writer/reader census

**Every writer, exhaustively enumerated by direct source read of the two methods that touch this field (OBSERVED):**

1. `RiverBrain.learn()` — `echo_model_orchestrator.py:828-862`. The dominant path (§7).
2. `RiverBrain.learn_from_council_rating()` — `echo_model_orchestrator.py:958-979`. Real, live, low-volume (§7).
3. `RiverBrain.load()` — `echo_model_orchestrator.py:1138`, a bulk restore from the persisted pickle at process start; not a new-observation write, a rehydration of prior state.

**No third writer exists.** `learn_from_sandbox_outcome()` and `learn_from_rating()` are confirmed, by reading their complete bodies (§4, §5), to never appear among these three.

**Every reader, exhaustively enumerated (OBSERVED):**

1. `RiverBrain.score_model()` — `echo_model_orchestrator.py:1007`, the sole real behavioral consumer (§8).
2. `RiverBrain.observations_for()` — `echo_model_orchestrator.py:1016`, a thin wrapper reporting the count only, itself called by `is_well_observed()` and, per this project's own well-documented "fair-sample exploration" mechanism (RETRIEVED from this session's prior archaeology, not re-verified this mission), by council-selection exploration logic.
3. `RiverBrain._do_save()` — `echo_model_orchestrator.py:1067`, serializes the full dict into the pickle snapshot; a persistence path, not a behavioral consumer.
4. `self_model_updater.py:601`'s own comment (`"reads model_task_stats, prompt assembly, or any decision from it"`) — this line, read directly this mission, is itself a **negative-evidence comment**, stating that this specific module deliberately does *not* read `model_task_stats` for the decision it's documenting (the exact sentence fragment reads as a denial, in context) — flagged here because a naive keyword grep would have miscounted it as a fourth reader; direct reading of the surrounding context is required to correctly classify it as a non-reader.

**Dead writes / write-only state / shadow statistics / duplicated state:** none found among the three real writers above — all three feed the identical, single `model_task_stats` structure, with no parallel shadow copy found anywhere in `echo_model_orchestrator.py` itself. (This is a materially different finding from `self_model_claims.py`'s own confirmed write-only-orphan bug, this session's sibling audit — `model_task_stats` itself has no analogous internal orphaning; the orphaning problem here is external, at the method-boundary level, not internal to the data structure.)

**Stale aliases / conditional consumers / unreachable consumers:** `score_model()` is unconditionally reachable from `rank_models()` for every real council-selection or `choose_model()` call (§8) — unlike `self_model_claims.py`'s or `behavioral_state.py`'s own consumers, this one is *not* gated behind any introspection or topic check, a real, positive structural difference this mission's own comparison to the two sibling mechanisms surfaces.

**Reset/reinitialization paths:** `RiverBrain.__init__()` always creates a fresh `defaultdict(dict)`; `load()` (§7) merges the persisted pickle's `model_task_stats` on top of that fresh dict rather than replacing the whole object — a real, if minor, distinction from a hard reset, since any task-type key present in a fresh `_init_classifiers()` pass but absent from the pickle would simply not appear until a first real observation, no corruption risk found.

**Background-thread writers / singleton contamination / race conditions:** the writer thread (`_writer_loop`/`_do_save()`, §7) is real, confirmed live via this mission's own direct source read, unconditionally started in `__init__()`, and persists the *entire* `model_task_stats` dict on its own ~60-second-or-queue-triggered cadence, independent of which of the three writer methods most recently mutated it. This is the exact mechanism this project's own prior Tier-8 forensic work (RETRIEVED, this session's archaeology mission) already found requires a path-redirect-before-first-access isolation pattern for any experiment sharing a process with a live `get_river_brain()` call — **this mission's own direct re-read of `__init__()`/`_writer_loop()`/`_do_save()` confirms this risk is still exactly as described, unchanged in current source** (§16).

**Multiple sources writing semantically incompatible values into the same statistic:** yes, a real finding, distinct from the missing-writer problem — `learn()`'s `normalized_score` (a static, self-scored 0-4 heuristic divided by 4) and `learn_from_council_rating()`'s `blended` value (a 30/70 mix of a peer model's 1-5 rating and the same static heuristic) are both written into the identical `stats["mean"]` field via the identical EMA update rule, meaning the resulting `mean` is a rolling average of two evidentially different signal types with no field distinguishing which contributed how much to any given value — mitigated only partially by the additive `council_vetted_count` provenance counter (§7), which tracks *how many* observations were council-vetted but not *what the mean would be if computed from only one signal type or the other*.

## 7. Current dominant evaluator analysis

**EVENT → evaluator → update → persistence → `model_task_stats` → `score_model()` → routing consequence, for `learn()` specifically (OBSERVED, complete method read, `echo_model_orchestrator.py:808-868`):**

- **EVENT:** any real model response, from any task type, any real production call site (council deliberation, direct-response, self-edit code generation, `echo_projects` generation — every one of the more than a dozen real `get_river_brain().learn(...)` call sites this mission's own repo-wide grep found, §3).
- **Evaluator:** `_score_response_quality(response, task_type)` — a static, deterministic function scoring the response text itself: for `task_type == "coding"`/`"self_edit_coding"`/`"echo_projects_coding"`, an AST-complexity-branch-count heuristic (RETRIEVED, this project's own extensively-documented Finding 91 recalibration of exactly this function, this session's prior archaeology mission — not independently re-read line-by-line this mission, since the relevant fact for this audit is only that the label fed into `learn()` derives from scoring the response's own text, which this mission's own direct read of `learn()`'s call to this function, line 815, confirms structurally regardless of the heuristic's exact internal threshold). **This is self-referential by construction: the text being credited to a model is the same text the evaluator scores.**
- **Update:** `label = 1 if raw_score >= 3 else 0`; the classifier/scaler are trained on this label; `stats["mean"]` moves toward `normalized_score = raw_score/4.0` via the EMA update, capped at `_MEAN_EFFECTIVE_WINDOW=200` (OBSERVED, exact source lines 816, 844, 861-862).
- **Persistence:** the background writer thread, unconditionally (§6).
- **`model_task_stats`:** written directly, every call.
- **`score_model()` → routing consequence:** direct, deterministic (§8).

**Quantified, this mission, via the live pickle (OBSERVED, REPRODUCED — a safe, isolated, non-mutating read, §23):**

| Model | `coding` count | `coding` mean | `council_vetted_count` |
|---|---:|---:|---:|
| `echo:latest` | 63,071 | 0.5622 | 24 |
| `mlx:qwen3` | 22,365 | 0.5442 | 4 |
| `qwen2.5-coder:7b` | 15,416 | 0.5112 | 1 |
| `qwen2.5:3b` | 11,033 | 0.5124 | 3 |
| `llama3.2:3b` | 5,026 | 0.5771 | 0 |
| `llama3:instruct` | 4,565 | 0.5407 | 4 |
| `mistral:latest` | 2,711 | 0.5972 | 0 |
| `llama3.1:8b` | 1,288 | 0.5887 | 0 |
| `deepseek-r1:7b` | 201 | 0.4900 | 0 |
| `gemma3:4b` | 200 | 0.5162 | 0 |
| `mlx:gemma3` | 73 | 0.5205 | 0 |
| `vicuna:latest` | 7 | 0.2857 | 0 |

**Total real observations across all of `model_task_stats` (every task type, every model): 207,554. Total `council_vetted_count` across every entry: 70 — approximately 0.034%.** `sandbox_observation_counts["coding"] = 16,208` — real, substantial, and entirely disjoint from every number in the table above (OBSERVED, live pickle, §23).

**Answering the mission's own quantification checklist directly:**
- Whether evaluation is independent: **no, for the dominant `learn()` path** — the evaluator scores the exact text being credited.
- Whether model output participates in grading itself: **yes, directly**, for `learn()`.
- Whether peer/council output participates: **yes, but only for the 70-observation `learn_from_council_rating()` path**, itself still blended 70% with the same self-referential heuristic (§7's blend formula, RETRIEVED from this mission's own direct source read of `learn_from_council_rating()`, §3).
- Whether humans participate: **no, not in anything that reaches `model_task_stats`** — `learn_from_rating()` is confirmed terminated before it (§5).
- Whether sandbox execution participates: **no, not in anything that reaches `model_task_stats`** — confirmed terminated before it (§4), despite being the single largest-volume genuinely independent signal this mission found (16,208 real observations).
- Relative observation volume: **the self-referential `learn()` path outnumbers the one genuinely council-vetted path by roughly 2,965 to 1** (207,554 total minus 70 council-vetted, divided by 70).

## 8. `score_model()` behavioral-consequence analysis

**Reconstructed directly from source, not inferred (OBSERVED, `rank_models()`, `echo_model_orchestrator.py:1153-1196`):**

```python
river_score = get_river_brain().score_model(model, task_type)
legacy_score = legacy_norm.get(model, 0.0)
combined[model] = (legacy_weight * legacy_score) + (river_weight * river_score)
ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)
```

`river_weight` is `RiverBrain.influence_weight` — a real, computed property (`echo_model_orchestrator.py:796-806`) whose formula, applied to this mission's own directly-observed live `observation_counts` (`coding=127,468`, `personal=63,556`, others smaller, §7), yields a `weighted_obs` value in the tens of thousands — meaning `1 - math.exp(-weighted_obs/100.0)` is, to any practically representable precision, `1.0`, pinning `influence_weight` at its hard ceiling of `0.65` (OBSERVED, direct arithmetic from the formula against the live counts; not independently re-measured by calling the live property itself, since doing so would require importing the module — this is a direct hand-computation from the formula and the observed counts, labeled OBSERVED for the formula and counts, INFERRED for the resulting weight's exact current value). **This means RiverBrain's `score_model()` output currently dominates `rank_models()`'s combined score for well-observed task types, at roughly a 65/35 weighting against the legacy reflection-based score.**

`choose_model()` (lines 1212–1227+) then iterates `ranked = rank_models(task_type)` and selects the first entry present in `candidates` — a direct, deterministic control-flow dependency on `rank_models()`'s sort order, which in turn directly depends on `score_model()`'s value.

**"Score changes" vs. "behavior changes," per the mission's own explicit separation:** this is not a case requiring an empirical ablation to distinguish the two — the code is a deterministic sort, and a sort key that includes a term is definitionally capable of changing the sort's outcome. **This mission finds no historical A/B test or ablation that measures the *magnitude* of this effect at real production scale** (e.g., "how often does changing one model's `score_model()` value actually flip which model gets selected, in real historical traffic") — that specific quantitative question remains UNKNOWN, distinct from the qualitative causal-mechanism question, which is definitionally answered by the source code itself.

**Does `score_model()` causally affect council participation, synthesis, or task routing beyond `choose_model()`/`rank_models()`?** RETRIEVED, not independently re-verified this mission beyond the one call site read here — this session's prior archaeology mission (Tier-7 citation) states `_select_council()` in `river_deliberation.py` also consumes `score_model()`, with an additional tag-boost and exploration-floor mechanism layered on top; this mission did not re-read `river_deliberation.py`'s own source to independently confirm that specific claim, and flags it as RETRIEVED accordingly.

## 9. Independent-evaluator attack

**Sandbox outcomes:**

- **Is verdict deterministic?** For self-edit's F2 gate: yes, a real subprocess execution with a fixed pass/fail signal (`SANDBOX_OK` or not). For code-verification's conversational path: RETRIEVED from this session's own sibling `self_model_claims.py` audit's direct source read — a real sandboxed execution comparing claimed output to actual output, deterministic given fixed code and fixed test input.
- **Can model text influence the evaluator other than through the artifact being tested?** Not found for either path — both execute the code artifact itself and observe real process behavior, not a re-parse of the model's own prose claims about what the code does.
- **Is expected output hidden?** For F2: there is no "expected output" concept at all — the test is import/execution cleanliness, not correctness against a reference. For code-verification: the "expected output" is the model's *own claimed* output in the same response, re-derived by actually running the code — a real check, but the reference the model is being checked against is self-supplied, not an independently authored, hidden oracle answer (a genuine, if narrower, independence gap relative to a true held-out test, distinct from the frozen persistent-competence protocol's own hidden-oracle design, which does use genuinely hidden, orchestrator-only expected outputs, RETRIEVED, this session's own prior archaeology).
- **Can evaluator leakage occur?** Not found for either real path in this codebase, at the mechanism level examined here — a full exploit battery of the kind the frozen protocol's own `[QUAL-2]` specifies (canary files, `os.walk` probes, symlink attacks, etc., RETRIEVED) was not independently re-run against these two production sandbox paths this mission; this is a real, disclosed limitation (§22), not a confirmed clean bill of health.
- **Is there an exploitable success criterion?** For F2 specifically: yes, in a narrow, already-documented sense (RETRIEVED, this project's own Finding 41-C precedent, not re-verified this mission) — a candidate that merely imports cleanly without doing anything meaningful would still register `success=True`.
- **Does the evaluator test correctness or merely execution?** **This is the single most important independence-attack finding of this section, and it differs between the two real producers**: F2 tests *execution cleanliness only* — a real, meaningful, but narrower signal than correctness. Code-verification tests a real, if self-referentially-scoped, *correctness* claim. Both currently feed the identical `learn_from_sandbox_outcome()` method with a single `success: bool`, collapsing this real distinction into one indistinguishable signal type before it is even discarded (§4, §11).
- **What task families can it validly evaluate?** F2: any self-edit-generated Python module. Code-verification: only conversational responses containing a fenced code block plus a claimed, checkable output — RETRIEVED, this session's sibling audit, a narrow subset of real coding-task responses.
- **What known evaluator attacks exist?** RETRIEVED, this project's own well-documented Finding 41-C (aliased-import bypasses of F1's static scanner, since partially closed) — relevant context, not independently re-tested this mission against F2's real current source.

**Human ratings:**

- **What exactly is rated?** A single 1-5 integer, per `learn_from_rating()`'s signature — no structured rubric, no per-dimension breakdown; whatever a human operator felt about one response as a whole.
- **Who supplies the rating?** RETRIEVED, this project's own well-documented terminal-client bare-digit rating convention — a single human operator (Gremlin, per this project's extensive prior documentation), not a panel, not blinded to which model produced the response.
- **Is the rating tied to the correct model/task instance?** Structurally yes — `learn_from_rating()`'s signature requires `model_name`/`task_type`/`response_preview` supplied together at the call site; this mission did not independently trace the calling convention all the way from the terminal client's own rating-capture code to confirm no identity-mixup is possible there, and flags this as UNKNOWN rather than assumed.
- **Can selection bias contaminate it?** Yes, plausibly — a single human rater who knows (or can infer) which model produced a response before rating it is not a blinded evaluator, and this mission found no blinding mechanism anywhere in the rating capture path.
- **Is it sparse?** Yes, self-evidently, relative to `learn()`'s 207,554-observation dominant path — this mission did not locate a live count of real human ratings specifically (as opposed to council ratings), but given `learn_from_rating()` never reaches `model_task_stats` at all (§5), this count is, for the purpose of this audit's central question, moot until reconnected.
- **Can human preference substitute for correctness?** Yes, structurally — a 1-5 rating is a preference/satisfaction signal, not a verified-correctness signal, and nothing in `learn_from_rating()`'s own code distinguishes "the human liked this" from "the human verified this was factually/functionally correct."
- **Is provenance preserved?** Not beyond the plain function-call arguments — no separate audit log analogous to `behavioral_state.py`'s or `self_model_claims.py`'s own append-only provenance records was found for this specific signal.

**The mission's own explicit caution — "do not treat 'human' as automatically equivalent to 'independent correctness evaluator'" — is directly borne out by this attack: human ratings are real and genuinely human-sourced, but they are a preference signal, not a verified-outcome signal, and conflating the two would be a real, avoidable design error in any reconnection.**

## 10. Broken-wire localization

Precisely, per §4/§5's exact source-line citations: the sandbox-outcome wire breaks at `echo_model_orchestrator.py:880` (the last line of `learn_from_sandbox_outcome()` that writes any persistent state, `self.sandbox_observation_counts[task_type] += 1`); the human-rating wire breaks at `echo_model_orchestrator.py:914` (`self.observation_counts[task_type] += 3`, the last stateful write in `learn_from_rating()`). **Both breaks are at the exact method boundary — neither signal is lost somewhere upstream (in event capture, in feature extraction, or in classifier training) nor somewhere downstream (in `score_model()` failing to read a value that was written) — the methods themselves simply never contain a line writing to `self.model_task_stats`.** This is a materially more precise statement than "the reward wire is broken" — it is broken at one exact, identifiable, two-line location per signal, both confirmed this mission by reading the complete function bodies, not by keyword absence alone.

## 11. Naive-reconnection failure analysis

**The naive proposal: "just make `learn_from_sandbox_outcome()` and/or `learn_from_rating()` update `model_task_stats`."** Constructing the strongest failure case, per the mission's own checklist:

- **Incompatible reward scales:** real — `learn()`'s `normalized_score` is a continuous `raw_score/4.0` value; a naive sandbox-outcome connection would most likely use a binary `1.0`/`0.0`, and a naive rating connection a `user_rating/5.0` — three different scales blended via the identical EMA formula into one `mean` field would produce a statistic whose numeric meaning silently shifts depending on which signal type happened to update it most recently, with no field distinguishing the contribution (the same problem already real for the existing `learn()`/`learn_from_council_rating()` pair, §6, now tripled).
- **Task-type confounding:** real and already demonstrated in current source — `learn_from_sandbox_outcome()` hardcodes `task_type = "coding"` (line 871) regardless of whether the originating call came from self-edit's own `"self_edit_coding"` bucket or an ordinary conversational `"coding"` request; naively connecting this to `model_task_stats` would write self-edit-generation outcomes into the same bucket ordinary conversational coding-help routing reads from, exactly the cross-contamination this project's own well-documented Finding 35 (RETRIEVED) already fixed once for `learn()`'s own three separate coding buckets — a naive reconnection would reintroduce a version of that already-fixed problem for this new signal.
- **Model-selection confounding:** real — a model that is selected more often (because it already scores well) will accumulate more sandbox/rating observations, and if those new observations are noisier or systematically differently-distributed than the observations that produced its current score, the update dynamics differ per model in a way that isn't a fair, symmetric comparison.
- **Survivorship/selection bias:** real — a model rarely selected (§6's `is_well_observed()`/exploration-floor mechanism aside) accumulates independent-outcome observations more slowly, meaning any new statistic built from these signals inherits the same cold-start asymmetry `_MIN_MODEL_OBSERVATIONS=5` already exists to paper over for the dominant path.
- **Lack of counterfactual outcomes:** real, and directly relevant to any claim about "would a different model have done better" — nothing in either sandbox-outcome producer tests what a *different* model would have produced on the same task; this is a single-arm observation, not a comparative trial, for every real historical sandbox/rating event.
- **Repeated observations of the same task:** plausible, not directly measured this mission — self-edit's retry mechanism (RETRIEVED, this project's own well-documented Finding 22 Batch 4 retry-then-succeed pattern) means a single logical attempt can generate more than one real sandbox-outcome call, a form of pseudo-replication if naively treated as independent evidence.
- **Model identity imbalance:** confirmed directly in this mission's own live-pickle read (§7) — `echo:latest` (63,071 `coding` observations) versus `vicuna:latest` (7) is an enormous imbalance that any new writer would inherit rather than correct.
- **Simpson's paradox:** directly relevant and already independently demonstrated in this exact statistic for a *different* signal — this session's prior archaeology mission (RETRIEVED, Tier-7 citation) found RiverBrain's own historical score discriminates candidates at 77.8% overall but only 38.9% (worse than chance) once one confounding model is excluded from the comparison; a naive new writer inherits the same risk of an aggregate figure masking a reversed subgroup effect, without any new safeguard against it.
- **Catastrophic overwriting / stale statistics:** the EMA cap (`_MEAN_EFFECTIVE_WINDOW=200`, §7) already means a model's score reflects roughly its last 200 observations once past that threshold — a naive new writer competing for the same 200-observation window as the existing dominant `learn()` path would dilute, not cleanly add to, whatever independent signal it's meant to contribute, at exactly the volume ratio this mission quantified (207,554 self-scored vs. a currently-nonexistent count of naively-added independent observations).
- **Contamination from the existing self-referential writer:** real, and the single most important item on this list for the mission's central question — because `learn()` already writes the identical field at high volume, any naive new writer to the same field cannot be cleanly attributed after the fact; the two signal types are mixed in one number, at one file's granularity, with only the low-fidelity `council_vetted_count`-style provenance counter (§6) available to even estimate the mixing ratio.
- **Temporal leakage:** not directly assessed as a distinct risk beyond what's already covered above — this mission did not find a specific temporal-ordering vulnerability unique to a naive reconnection, beyond the general staleness/EMA concerns already listed.
- **Reward hacking / evaluator exploitation:** real, per §9's own findings — F2's execution-only success criterion is a real, if narrow, exploitable surface; naively wiring its raw pass/fail into a reward statistic without first closing that gap would reward "imports cleanly" as if it meant "is a good coding response," a real category error.
- **Inability to distinguish routing improvement from capability acquisition:** the single most conceptually important item, addressed fully in §14 below — a naive reconnection, even if executed flawlessly on every item above, would still only ever be capable of showing that FeralEcho got better at *choosing among its fixed models*, never that any underlying model became more capable.

**Which existing v1.1 defenses would catch which of the above (RETRIEVED, this session's own prior sibling reports, §16 below expands this fully):** the frozen persistent-competence protocol v1.1's null-effect calibration and hand-typed-carrier positive control (`[QUAL-4]`) is specifically designed to catch exactly the "apparent improvement from a fixed/counterfeit signal" family of failures named here; its `EMPTY`/`NEUTRAL`/`POISON` context-ablation arms are designed to catch reward-hacking/evaluator-exploitation-shaped failures; neither, as originally designed, was built with the specific "three incompatible scales blended into one EMA field" failure mode in mind, since that protocol's own carrier design (§16's citation) deliberately avoids ever blending signal types into RiverBrain's own field in the first place — a real, positive design choice this mission's own analysis retroactively validates.

## 12. `river.bandit` comparison

**Current status, re-confirmed from source this mission (OBSERVED, direct grep, `grep -rl "river.bandit\|river\.bandit\|from river import bandit\|import bandit" --include="*.py" .` across the live repository, excluding the stale `.claude/worktrees/` copy): zero real code references anywhere.** The only match found is inside `audits/python_learning_capability_gap/probes.py` — itself a research artifact from a prior audit's own capability probe, not production code, and not an import of the module. **`river.bandit` remains fully dormant, unchanged from every prior confirmation across this session's research history.**

**Comparison, DESIGN ONLY, per the mission's explicit evaluation criteria:**

| Criterion | A. Direct `model_task_stats` update | B. `river.bandit` | C. Fresh isolated experimental statistic |
|---|---|---|---|
| Causal interpretability | **Weak** — a shared field already mixing at least two signal types (§6), any addition worsens this | **Moderate** — a bandit's `update(arm, context, reward)`/`pull(arms, context)` API is a cleaner, purpose-built shape for exactly this kind of decision, but still shares the model pool's live selection history if wired into production | **Strongest** — a fresh field, populated only by the new signal, has no pre-existing contamination to interpret around |
| Reset/isolation | **Worst** — cannot be isolated without also isolating the entire, already-contaminated live `model_task_stats` structure | **Moderate** — a bandit object instantiated fresh has clean state, but if fed from the live production selection stream it inherits the same non-counterfactual-outcome problem named in §11 | **Best** — purpose-built for isolation from the start |
| Counterfactual requirements | Same underlying weakness in all three — none of FeralEcho's real production traffic includes a counterfactual ("what would model B have done") without an explicit held-out design (§18) | Same | Same |
| Online learning properties | Already real and live (the EMA mechanism) | Real and more principled (this project's own prior python-capability-gap audit, RETRIEVED, already names `river.bandit`'s `LinUCBDisjoint`/`ThompsonSampling`/`EpsilonGreedy` as architecturally well-matched to RiverBrain's own per-(model,task_type) structure) | Would need to be built fresh, but can be built exactly to the frozen protocol's own already-specified `[CAR-1]`/`[CAR-2]` cumulative-mean shape (RETRIEVED) — no new statistical machinery required |
| Reproducibility | Weak — the live pickle's own writer thread makes exact reproduction of a given historical state difficult (§16) | Same weakness if wired live; strong if run offline against a frozen replay log | **Strongest** — a fresh file with no background writer, following `behavioral_state.py`'s own already-proven no-cache, no-singleton architecture (RETRIEVED, this session's sibling audit) |
| Restart persistence | Real, but entangled with RiverBrain's own singleton/writer-thread risk (§16) | Not inherently — `river.bandit`'s own policy objects have no persistence layer of their own in this codebase; would need to be added | Can be built to `behavioral_state.py`'s exact proven pattern (atomic write, fresh read, no cache) |
| Evaluator compatibility | Compatible with any evaluator, but inherits all of §11's contamination risk | Compatible; this project's own prior audit (RETRIEVED) already sketches a concrete offline-replay experiment using real historical `(model, task_type, outcome)` logs | Fully compatible by construction — a fresh statistic can be shaped around whatever evaluator is chosen |
| Contamination risk | **Highest** — directly shares the field the dominant self-referential path already writes | **Moderate**, only if connected to live production state; **low** if run as an offline replay (this project's own prior audit's own recommended first step, RETRIEVED) | **Lowest** — isolated by construction |
| Ability to support held-out tests | Poor — no existing mechanism separates "training" observations from "held-out" ones within `model_task_stats` | Better — a bandit's own exploration/exploitation split is conceptually closer to a train/held-out distinction, though not identical | **Best** — a fresh statistic can be explicitly partitioned to match the frozen protocol's own already-designed E2/E3/E5 scheme (RETRIEVED) |
| Ability to distinguish routing adaptation from competence acquisition | **None of the three options change this** — this is a question about what claim the experiment tests, not which statistic implementation is used (§14) | Same | Same |

**Verdict, DESIGN ONLY, not activated: a fresh, isolated experimental statistic (option C) is scientifically preferable to both A and B for a first, cleanly-falsifiable experiment specifically because it inherits none of `model_task_stats`'s existing contamination and requires no new dependency activation risk.** `river.bandit` (option B) is a real, well-matched, already-installed piece of dormant capability that this mission agrees, per the prior python-capability-gap audit's own recommendation (RETRIEVED), is worth a *separate*, later offline-replay experiment against real historical logs — but it is not the minimum, lowest-risk first step for the specific falsifiable-routing-learning question this mission's Mission 13 designs (§18), and this mission does not recommend activating it now.

## 13. Claim ladder

| Level | What it licenses saying | Additional evidence required beyond the level below |
|---|---|---|
| **0 — Storage** | "An outcome was recorded somewhere." | A log line or persisted record exists — already true today for sandbox outcomes (`interaction_log.jsonl`'s `sandbox_feedback` notes, §4) and ratings. |
| **1 — Persistent state** | "The outcome's record survives restart." | The persisted artifact reloads correctly after a process restart — already true for `model_task_stats` itself (§7's `load()`), not yet true for a connected independent-outcome signal specifically, since none exists. |
| **2 — Behaviorally consequential persistent state** | "The persisted state is read by something that makes a real decision." | A real, unconditionally-reachable consumer reads the field and its value provably affects a decision's outcome — already true for `model_task_stats` as a whole (§8), via the existing self-referential `learn()` path; not yet true for an independent-outcome-derived value specifically. |
| **3 — Experience-dependent policy adaptation** | "The same input is routed differently after new evidence than it would have been before." | A real, controlled, before/after comparison on the actual production decision path, holding the input fixed — not currently demonstrated for any signal in `model_task_stats`, per this mission's own §8 finding that no historical ablation exists at this granularity. |
| **4 — Improved routing/selection** | "The changed decision is measurably better by an independent outcome measure, not merely different." | An independent evaluator scores the outcome of the *new* routing choice against a frozen baseline choice, on held-out tasks — not demonstrated for `model_task_stats` at all; this is exactly what §18's minimum falsifiable experiment is designed to test. |
| **5 — Held-out transfer** | "The improved routing generalizes to task instances structurally distinct from the ones that produced the routing evidence." | The frozen protocol's own already-designed E3 (surface-changed)/E5 (structurally novel) held-out cells (RETRIEVED), reused rather than reinvented — not run for RiverBrain's own statistic at any point in this project's history. |
| **6 — Acquired competence** | "An underlying model itself became more capable at the task." | **Structurally unreachable via RiverBrain's own architecture, per §14** — RiverBrain never modifies model weights; it can only ever change *which already-fixed model is chosen*. Reaching this level would require evidence about the model itself, not about RiverBrain. |
| **7 — Repeated accumulation** | "A second, independent learning episode adds further, non-interfering improvement on top of the first." | The frozen protocol's own already-designed `[LONG-1]`–`[LONG-8]` longitudinal battery (RETRIEVED) — retention testing, family-coverage controls, permutation-based trend tests — never run for any FeralEcho mechanism to date. |
| **8 — Accumulated competence** | "Improvement compounds across many independent episodes into a durable, general capability gain." | Everything above, sustained across many real episodes, with the Level-6 barrier already noted meaning this level is, for RiverBrain specifically, capped at "accumulated *routing* competence," never general capability, unless the underlying model pool itself changes. |

**A naive reconnection, even if it succeeded perfectly, would license claims up to Level 4 or 5 at best** — and only after the specific failure modes in §11 are closed and the isolation gap in §16 is resolved. **It cannot, even in principle, license Level 6 or above**, per §14's own direct argument. This is stated plainly per the mission's own explicit instruction not to inflate improved routing into capability acquisition.

## 14. Routing-learning vs. capability-acquisition analysis

**Recovering the frozen protocol's own original distinction (RETRIEVED, this session's prior archaeology mission's direct read of `audits/2026-09-20_persistent_competence_frozen_protocol_v1_1.md` §1):** `[SCOPE-4]` defines **CLAIM R — ROUTING LEARNING**: "experience improves the selection among the already-capable frozen workers." `[SCOPE-5]` defines **CLAIM C — CAPABILITY ACQUISITION**: "experience produces a reusable performance improvement of a *fixed* worker... through a within-worker mechanism... not explainable by switching to an already-superior pretrained worker." `[SCOPE-2]` states plainly: "the workers are frozen. Model weights MUST NOT change." `[SCOPE-6]` states: "a routing result MUST NOT be labeled capability acquisition."

**Applying this distinction directly to RiverBrain: connecting independent outcomes to `model_task_stats` would test A (routing learning) only, never B (capability acquisition), and this is not a limitation of the *connection design* — it is a structural fact about what RiverBrain, as an architecture, is capable of representing at all.** `model_task_stats` is keyed by `(model_name, task_type)`; every model's underlying weights are, by this project's own architecture, never touched by anything RiverBrain does — RiverBrain only ever decides *which already-fixed model to call*. There is no mechanism anywhere in `RiverBrain`'s class body, read in full this mission, that could cause an underlying model to become better at anything; the only thing that can change is which model gets *selected* more often for a given task type.

**Can RiverBrain ever demonstrate capability acquisition while the underlying candidate models remain fixed? No, not even in principle**, per this direct architectural analysis. Any observed improvement in real, held-out task outcomes attributable to a RiverBrain-mediated routing change is, by construction, fully and completely explained by "FeralEcho got better at choosing which already-capable model to call" — which is precisely `[SCOPE-6]`'s own named failure mode to guard against mislabeling.

**What RiverBrain CAN legitimately demonstrate, and why this is still scientifically useful:** genuine, independently-evaluated, restart-surviving, held-out-transferring **routing/policy learning** — a real, non-trivial claim in its own right, and one this project's own prior archaeology already found partial, narrow, real evidence for (RiverBrain's live-data-confirmed detection of one specific unreliable model, `echo:latest` in a particular disagreement-shaped comparison, RETRIEVED, this session's prior archaeology's Tier-7 citation). A cleanly-demonstrated routing-learning result would be genuinely valuable: it would show FeralEcho can learn, from real independent outcomes, which of its already-installed tools is the right one to reach for — a real, practically useful property for a multi-model system, entirely independent of whether any underlying model ever gets smarter. **This mission explicitly does not dismiss this as a lesser goal merely because it isn't capability acquisition, per the mission's own instruction.**

## 15. Counterfeit-learner attack

**Recovering the known v1.0 exploit and its v1.1 fix (RETRIEVED, this session's own prior archaeology mission's direct read of `audits/2026-09-20_persistent_competence_protocol_v1_blind_review.md` and `_frozen_protocol_v1_1.md` §8):** v1.0's tie-breaking used alphabetical/identity ordering among a small worker set, which — proven via a real synthetic simulation cited in the prior blind review — made the baseline arm deterministically pick one specific worker and the transplant-recipient arm win every tie regardless of content, reproducing an apparently-real "learning" result (0.877 vs. 0.869 pass rate) from a completely fixed, non-learning policy. v1.1's fix (`[TIE-1]`/`[TIE-2]`, RETRIEVED, this session's own prior direct read) replaces this with an HMAC-keyed, non-identity-ordered draw, plus a dedicated `[QUAL-4]` battery specifically testing identity-bias, best/worst neutrality, key independence, and — most relevant here — a **null-effect calibration** run on synthetic ledgers with statistically identical workers, checking that the full experimental pipeline's false-positive rate for a "learning" verdict stays below a pre-registered threshold, "repeated with a hand-typed carrier" specifically to catch a counterfeit.

**Could a proposed independent-outcome→RiverBrain connection produce apparent improvement while no meaningful learning occurred? Yes, and this mission constructs three concrete counterfeits, per the mission's own required list:**

1. **Fixed policy / identity effect:** if the experiment's held-out task set happens to favor whichever model was already dominant in the live pickle before any new independent-outcome signal was ever added (§7's table shows `echo:latest` already holding 63,071 real `coding` observations and the highest mean among the high-volume models), then *any* routing policy that simply keeps selecting the already-dominant model — with or without a genuinely new independent signal — would appear to "improve" outcomes, because the pre-existing imbalance already favors it. **The frozen protocol's own `[QUAL-4]`(d) null-effect calibration and its "repeat with a hand-typed carrier" requirement (RETRIEVED) is specifically designed to catch exactly this counterfeit** — a hand-typed carrier that simply encodes "always prefer the already-dominant model" would need to be shown to *not* pass the same statistical test a genuine connection would need to pass.
2. **Selection-frequency imbalance:** because `_MIN_MODEL_OBSERVATIONS=5` (§7) already gates `score_model()` to a neutral 0.5 for under-observed models, and because a model selected more often accumulates more of whatever new independent-outcome signal is added faster, a purely mechanical volume effect (not a quality signal at all) could produce an apparent score improvement for already-favored models simply because they get more chances to accumulate the new signal. **The frozen protocol's forced-exploration design (`[CAR-9]`, RETRIEVED — "every worker in E receives exactly all N_TRAIN tasks per trained capability... forced exploration; no selector-driven allocation") is specifically built to neutralize this exact counterfeit**, by construction removing the selection-frequency confound from the experience-generation phase.
3. **Task-distribution artifact:** if the held-out test set's task-type distribution differs even slightly from the distribution that generated the independent-outcome training signal (e.g., more `self_edit_coding`-shaped tasks in training than in the held-out set, given §11's already-confirmed task-type-hardcoding confound in `learn_from_sandbox_outcome()`), an apparent improvement could reflect a distributional match rather than genuine learned discrimination. **The frozen protocol's `[PART-2]` structural-novelty requirement and its family-coverage controls (`[LONG-8]`, RETRIEVED) are designed to catch this**, by requiring held-out cells to be drawn from genuinely distinct template families and approach-buckets, not merely a random split of the same distribution.

**Any counterfeit the frozen protocol would NOT catch, stated plainly rather than assumed away:** the frozen protocol's entire battery is designed around its own fresh, purpose-built carrier architecture (§16 below) — it does not, and was never designed to, test a scenario where the *experimental* signal is blended into the *already-contaminated, already-massively-imbalanced* live `model_task_stats` structure itself, exactly the naive-reconnection scenario §11 already argues against. **If a future experiment naively wired a new signal directly into the live pickle rather than building a fresh, isolated carrier, the frozen protocol's own existing defenses would not automatically apply to it** — they were designed for, and verified against, a fresh-carrier architecture, and this mission finds no evidence they would generalize to a shared, pre-existing, already-imbalanced statistic without re-verification.

## 16. Isolation/restart qualification

**Independently re-checked against current source this mission (OBSERVED, not retrieved from any prior report's own conclusion, though the underlying risk class was first named by this project's own prior Tier-8 work):** `RiverBrain.__init__()` (`echo_model_orchestrator.py:759-781`) unconditionally starts a background daemon thread (`_writer_thread`, `target=self._writer_loop`) the moment any code constructs a `RiverBrain` instance — including via `get_river_brain()`'s own module-level singleton accessor (not independently re-read this mission, but its existence is implied by the many `get_river_brain()` call sites already confirmed, §3). This thread calls `_do_save()` on its own ~60-second-or-queue-triggered cadence (`_writer_loop`, lines 1031-1056), which serializes the *entire live* `model_task_stats` (and every other tracked field) to `memory/river_brain.pkl` — the same file this mission's own read-only inspection (§23) targeted, confirmed via `fcntl.flock()`-guarded exclusive access and a "refuse to overwrite a richer pkl" guard comparing total `observation_counts` (lines 1074-1082).

**Can a future experiment cleanly:**
- **Initialize baseline state?** Yes, trivially — a fresh `RiverBrain()` instance, per `__init__()`, always starts with empty `model_task_stats`.
- **Isolate experimental state?** **Not automatically** — the moment any code path calls `get_river_brain()` (whether directly or via any of the more than a dozen real call sites this mission's own §3 census found), a background writer thread targeting the *real, shared* `memory/river_brain.pkl` path starts, unconditionally, per `__init__()`'s own unconditional `self._writer_thread.start()` call.
- **Prevent background writes?** **Not without an explicit, pre-existing redirect** — this mission's own direct source read confirms `RIVER_BRAIN_PATH` (referenced as a bare global inside `_do_save()`/`load()`, not captured into any per-instance local) is the only thing standing between an experimental instance's writer thread and the live production file. This is the exact mechanism this project's own prior Tier-8 forensic work (RETRIEVED) already found and fixed once, via a redirect-before-first-`get_river_brain()`-call pattern in `scripts/run_capability_pilot.py` (RETRIEVED, cited by name at `app/experiments/architecture_a_hot_stove_proof/harness.py`'s own comment referencing exactly this class, per this mission's own §3 grep) — **this mission's own direct re-read of `__init__`/`_writer_loop`/`_do_save` confirms the underlying risk this fix addresses is unchanged in current source**, meaning the fix pattern itself (not yet independently re-verified this mission to still be correctly applied everywhere it needs to be) remains the correct, already-proven mitigation.
- **Snapshot state, restart process, reload only intended state?** Yes, in principle, following `behavioral_state.py`'s own already-proven separate-subprocess methodology (RETRIEVED, this session's own sibling audit, §4 of that report) — a fresh, redirected `RIVER_BRAIN_PATH` per experimental arm, in its own subprocess, would achieve this cleanly.
- **Verify no external writer contaminated it?** Yes, in principle, via the same hash/mtime-comparison discipline this mission's own §23 integrity check and this session's own prior Tier-7/Tier-8 work already establish as a working pattern.
- **Compare treated vs. control state?** Yes, in principle, given the above.

**Verdict: clean isolation is currently possible, but only via an already-proven, external redirect pattern that must be correctly and separately applied by any new experiment — it is not automatic, and the underlying background-writer-thread architecture that makes this necessary is confirmed, this mission, to be unchanged in current source.** This is a real prerequisite, not a blocking impossibility — consistent with this mission's own instruction that "if clean isolation is currently impossible, that becomes a prerequisite and may supersede the reward-wire work": **it is possible, but the isolation step itself is a real, separate piece of required engineering discipline for any future experiment touching RiverBrain, and this mission recommends it be treated as a mandatory, independently-verified precondition (§17, §19), not an assumed-safe afterthought.**

## 17. Minimum safe connection design — DESIGN ONLY

Per the mission's own explicit preference for the smallest possible change, and per §12's own verdict that a fresh, isolated statistic is scientifically preferable to a direct `model_task_stats` write:

- **Exact conceptual writer:** a new, standalone function — not a modification to `learn_from_sandbox_outcome()` or `learn_from_rating()` themselves, and not a new method on the live `RiverBrain` class — that accepts an already-computed independent-outcome tuple `(model_name, task_type, outcome: float in [0,1], provenance: dict)` and writes it to a fresh persistent artifact.
- **REQUIRED CHANGE:** the fresh artifact's own persistence layer, built to `behavioral_state.py`'s own already-proven shape (§9/§12 of this session's sibling audit, RETRIEVED): atomic write-to-temp-then-`os.replace`, no in-process cache, fresh disk read on every call, no background thread, no module-level singleton.
- **Exact state/statistic receiving the signal:** a per-`(model_name, task_type)` record, structurally identical to the frozen protocol's own already-specified `[CAR-1]` shape (RETRIEVED): `{worker_id, capability_id, count, mean, last_updated_utc, provenance}`.
- **Update rule:** the frozen protocol's own already-specified `[CAR-2]` exact, uncapped cumulative mean (`count += 1; mean += (x - mean)/count`) — REQUIRED CHANGE, and deliberately **not** RiverBrain's own `_MEAN_EFFECTIVE_WINDOW=200` EMA formula, per the frozen protocol's own explicit design rationale (RETRIEVED) that an uncapped mean is more interpretable for a fresh, small-sample experimental statistic than a windowed one.
- **Reward scale:** REQUIRED CHANGE — a single, fixed `[0,1]` scale for every signal type feeding this new statistic, with the F2-execution-only and code-verification-correctness-check signals (§9's own finding that they test different things) kept in **separate** fields/statistics rather than blended, at least until a dedicated design pass explicitly decides whether and how to combine them.
- **Provenance record:** REQUIRED CHANGE — every write carries a non-optional `provenance` dict naming the exact originating evaluator (e.g., `"self_edit_f2_import_execution"` vs. `"conversational_code_verification_output_match"` vs. `"human_rating"`), following `behavioral_state.py`'s own already-proven required-provenance convention (RETRIEVED).
- **Task-family keying:** REQUIRED CHANGE — a task-type key that does **not** collapse self-edit-generation and ordinary conversational coding into one bucket, correcting the exact confound §11 identifies as already live in `learn_from_sandbox_outcome()`'s own current hardcoding.
- **Model identity keying:** REQUIRED CHANGE — keyed by real model identity, matching RiverBrain's own existing convention, so any future comparison against `model_task_stats` remains meaningful.
- **Persistence behavior:** REQUIRED CHANGE, per the shape above.
- **Restart behavior:** REQUIRED CHANGE, per the shape above — no cache means restart survival is automatic and requires no separate mechanism.
- **Contamination defenses:** REQUIRED CHANGE — this new artifact must live at a path that is never touched by `RiverBrain`'s own writer thread and never read by `score_model()` or any other live production consumer, closing exactly the isolation gap §16 identifies. **EXPERIMENT-ONLY CHANGE**, additionally: for the duration of any experimental run specifically, the redirect-before-first-access pattern (§16, RETRIEVED from Tier-8) applied to the *live* `RIVER_BRAIN_PATH` as well, so that any code path the experiment happens to also exercise (e.g., a real generation call that incidentally also triggers `learn()`) cannot write into the live production pickle mid-experiment.
- **Rollback mechanism:** OPTIONAL CHANGE — `behavioral_state.py`'s own already-proven pre-mutation backup pattern (`_backup_current_state_before_mutation()`, RETRIEVED) could be reused directly for this fresh artifact, at low cost, though a fresh experimental statistic with no live production consumer has lower rollback stakes than a mechanism already wired into production.
- **Audit logging:** REQUIRED CHANGE — a separate, append-only log of every write, mirroring `behavioral_state.py`'s own `_append_audit()` pattern (RETRIEVED), for the same reason: honest, inspectable provenance.
- **Feature flag / isolation requirement:** REQUIRED CHANGE — this fresh statistic must have **no consumer wired into any live production decision path** for as long as it remains an experimental artifact; **NOT RECOMMENDED**, explicitly: wiring this fresh statistic into `rank_models()`/`choose_model()` before the experiment in §18 has actually run and been independently reviewed, per this project's own established report-then-pause discipline (RETRIEVED, this project's own extensive prior documentation of this norm).

**No code is presented here, and no pseudocode is offered that could be mistaken for an implementation** — every element above is a design requirement, stated in prose, citing an already-proven pattern by name where one exists.

## 18. Minimum falsifiable experiment — DESIGN ONLY

**BASELINE:** the fixed, cold-start static-worker comparison the frozen protocol v1.1 already specifies (`[ARM-1]`/`[ARM-12]`, RETRIEVED) — reused directly, not reinvented.

**EXPERIENCE:** real F2 sandbox executions (self-edit's own already-live pipeline) and/or real code-verification executions (routes_echo_studio.py's own already-live pipeline), kept in **separate** experimental arms per §17's own separation requirement, on a fixed, narrow task family — the frozen protocol's own already-designed `list_aggregation`/`string_transformation`/`dict_lookup_merge` families (RETRIEVED), reused by citation.

**INDEPENDENT OUTCOME:** the real, deterministic sandbox verdict itself — already the most independent signal this mission's own §9 attack found, with the frozen protocol's own already-specified hidden-oracle/grader-manifest-hash discipline (`[ORC-1]`–`[ORC-4]`, RETRIEVED) layered on top to close the specific gap §9 found in the *current* production sandbox paths (self-supplied "expected output" for code-verification; no correctness check at all for F2).

**RETAINED CHANGE:** §17's own fresh, isolated statistic — never the live `model_task_stats`.

**RESTART:** `behavioral_state.py`'s own already-proven separate-subprocess methodology (RETRIEVED, this session's sibling audit's own §4), reused verbatim as a testing pattern.

**HELD-OUT TEST:** the frozen protocol's own already-designed E2 (same family, new task)/E3 (surface-changed)/E5 (structurally novel) partitions (RETRIEVED), reused by citation.

**INDEPENDENT MEASUREMENT:** the frozen protocol's own already-specified paired McNemar/permutation statistical machinery (`[HYP-R1]`–`[HYP-R6]`, `[STAT-*]`, RETRIEVED), reused rather than reinvented, adjudicating **Track R (routing learning) only**, per §14's own architectural argument that Track C (capability acquisition) is unreachable for a RiverBrain-shaped mechanism regardless of experiment design.

**SECOND EXPERIENCE → SECOND RETAINED CHANGE → SECOND RESTART → SECOND HELD-OUT TEST, per the mission's own explicit requirement:** a second, independent batch of real sandbox/rating experience, fed through the identical isolated-statistic pipeline, followed by a second restart and a second held-out measurement on a *fresh* held-out cell (never previously exposed, per the frozen protocol's own `[PART-4]`/`[PART-5]` commit-reveal/sealing discipline, RETRIEVED) — **this second cycle is what distinguishes adaptation (Level 3-4 on §13's ladder) from the beginning of an accumulation claim (Level 7)**, exactly per the mission's own stated reasoning, and this mission fully agrees with that reasoning: a single before/after measurement, however clean, cannot show whether an effect is durable or a one-time treatment effect.

**Distinguishing H1 from H0, per the mission's own explicit list, using the frozen protocol's own already-designed defenses (RETRIEVED, cited by name, not reproduced in full here):** fixed capability → the frozen protocol's own `[ARM-1]`/`[ARM-12]` static-worker baselines. Routing bias → `[ARM-13]`'s fixed-worker invariance control. Retrieval/context → not directly applicable to a routing-only (Track R) design, since Track R's own `[EVALM-1]` explicitly excludes context-block injection from the routing-mode prompt. Evaluator leakage → `[QUAL-2]`'s sandbox exploit battery, reused directly, and this mission's own §9 attack's specific findings about F2/code-verification's current gaps should be closed *before* reuse, not assumed already closed. Selection effects → `[CAR-9]`'s forced-exploration design. Identity effects → `[TIE-1]`/`[TIE-2]`'s HMAC-keyed tie-break. Sampling variance → the frozen protocol's own `[INF-3]` fixed temperature/seed requirements (RETRIEVED) — a real, disclosed gap the C1 behavioral-state validation itself did not observe (this session's sibling audit, §4/§8), and one this design explicitly requires rather than omits. The known v1.0 counterfeit learner → already fixed in v1.1, reused rather than rebuilt.

**This experiment is specified but not run, per this mission's explicit scope.**

## 19. Negative-result interpretation matrix

Pre-registered, per the mission's own instruction:

| Observed failure | What it falsifies | What weaker claims survive |
|---|---|---|
| Independent reward updates the fresh statistic but routing does not change when the statistic is consulted | Level 3 (experience-dependent policy adaptation) | Level 1-2 still hold (persistence, and the statistic is technically readable) — the failure is specifically in the consumer's sensitivity to the new signal, a design/wiring question, not evidence against the signal's own validity |
| Routing changes but held-out outcome does not improve | Level 4 (improved routing/selection) | Level 3 survives — the system genuinely adapted its choices, just not in a way that helped on held-out tasks; this is real, useful negative evidence about whether the training signal generalizes |
| Held-out improvement disappears after restart | Level 1 (persistent state) itself, retroactively | Nothing above Level 0 survives cleanly — this would indicate the isolation/persistence layer (§17) has a real bug, and per §16's own findings, this is exactly the class of failure the RiverBrain-adjacent writer-thread risk could produce if isolation was not correctly applied |
| Improvement occurs equally in an EMPTY/no-signal control | Levels 3-4 entirely | Only Level 0-1 survive — this is the frozen protocol's own `[HYP-C2]`-shaped finding (RETRIEVED) and would indicate the effect is a fixed-capability or prompt-formatting artifact, not the independent signal |
| A POISON (deliberately wrong) version of the signal performs equally well or better | Levels 3-4 entirely, and specifically implicates the evaluator | Nothing survives above Level 1 — per the frozen protocol's own `[HYP-R3]`/`[HYP-C3]` (RETRIEVED), this is explicitly load-bearing: "failure prohibits every label above CARRIER-CONTROLLED BEHAVIOR" |
| One of §15's three constructed counterfeits (fixed-policy, selection-frequency, task-distribution) passes the full experimental battery | The specific claim the passing counterfeit targets — e.g., a fixed-policy counterfeit passing falsifies any claim that the *independent signal itself* (rather than a pre-existing imbalance) drove the result | Whatever level the counterfeit itself would have reached under H0 remains a real, separate finding about the apparatus's own discriminating power, worth reporting even though it falsifies the original claim |
| The first cycle shows real improvement but the second cycle shows no additional, non-interfering gain | Level 7 (repeated accumulation) | Levels 3-4 (and possibly 5, if held-out transfer held for the first cycle) survive fully — this is real, valuable evidence that FeralEcho can adapt once but does not compound adaptation, a materially different and still useful finding |
| Performance improves only on tasks structurally identical (not merely same-family) to the training experience | Level 5 (held-out transfer) | Level 4 survives — the routing genuinely improved measured performance, just without generalizing beyond near-exact repetition; this is a real, common, and informative failure mode distinguishing genuine discrimination from memorization-adjacent overfitting |
| The effect vanishes under identity randomization (the HMAC tie-break's own `[QUAL-4]`(a) discrimination test) | The entire experimental apparatus itself | This would mean the experiment's own construction, not the underlying hypothesis, is untrustworthy — per this mission's own methodological discipline, this result would need to be reported and the apparatus repaired before any substantive claim, positive or negative, could be drawn from the same run |

**Per the mission's own instruction: a failed experiment must still produce useful information — every row above names a real, retained, weaker claim, not a blanket "nothing was learned."**

## 20. Comparison with Rung-1

**Without altering Rung-1, and drawing only on this session's own carried-forward context of Rung-1's current scope (a hidden-test evaluator gate for self-edit candidates, per this session's own prior seven-day research-debt audit — RETRIEVED, not independently re-verified this mission by re-reading Rung-1's own source, per this mission's strict scope prohibiting Rung-1 modification and this report's own budget prioritizing the reward-wire question itself):**

- **Does the proposed reward-wire experiment duplicate Rung-1?** No — Rung-1's hidden-test evaluator gate, as characterized, is about whether a *single self-edit candidate* clears a quality bar before deployment; the reward-wire experiment in §18 is about whether *routing among already-installed models* improves given independent outcomes, a different question about a different decision.
- **Does it complement Rung-1?** Yes, directly — Rung-1's own hidden-test gate is itself a genuinely independent evaluator (per this session's own carried-forward context), and per §9/§18's own design, the exact same evaluator machinery Rung-1 is already building could, in principle, supply the "independent outcome" half of §18's experiment for the `self_edit_coding` task family specifically, once Rung-1's own gate is itself qualified and stable — a real, concrete point of potential future reuse, not pursued or connected in this mission.
- **Should it precede Rung-1?** No — Rung-1 is already active (per this session's carried-forward context) and targets a narrower, cheaper, more immediately actionable question (does this one candidate pass a quality bar); §18's design is a larger, more expensive undertaking that should not be prioritized ahead of an already-in-flight, narrower effort.
- **Should it follow Rung-1?** Plausibly yes, and this mission's own recommendation (§21) reflects this — once Rung-1's own evaluator is qualified, it becomes a stronger, ready-made independent-outcome source for exactly the kind of experiment §18 designs, making "finish qualifying Rung-1's own evaluator first" a real, concrete prerequisite worth stating rather than a vague deferral.
- **Does it expose a flaw in Rung-1's current design?** Not directly — this mission did not re-read Rung-1's own source deeply enough to make this claim with confidence, and per this mission's own strict scope (no Rung-1 modification, and by extension no deep re-audit of Rung-1 itself), this question is left as UNKNOWN rather than answered from insufficient evidence. One indirect, worth-naming observation: if Rung-1's own evaluator shares any of §9's found gaps (self-supplied "expected output," execution-only success criteria), those same gaps would need independent verification before Rung-1's evaluator could safely supply the "independent outcome" half of any future reward-wire experiment — a real, stated dependency, not a confirmed flaw.

**This mission does not recommend replacing or altering the current Rung-1 roadmap.** The evidence gathered here argues for treating §18's design as a distinct, later, complementary research track, not a substitute for or a correction to Rung-1's own narrower, already-in-flight work.

## 21. Ranked next three research actions

1. **A design-only, read-only pass verifying that Rung-1's own hidden-test evaluator meets the same independence bar this mission's §9 attack applied to F2/code-verification — before any future work treats it as a ready-made "independent outcome" source for a reward-wire experiment.**
   - *Exact question:* does Rung-1's evaluator hide expected outputs from the candidate, avoid the execution-only/correctness-conflation gap §9 found in F2, and pass an exploit battery structurally equivalent to `[QUAL-2]`?
   - *Cost:* low — read-only source inspection, no live run required.
   - *Risk:* very low.
   - *Code changes required:* none.
   - *Prerequisite:* none beyond read access to Rung-1's own current source (explicitly not modified by this action).
   - *Positive interpretation (evaluator meets the bar):* Rung-1's evaluator becomes a genuinely ready-made independent-outcome source for §18's design, meaningfully de-risking that larger effort.
   - *Negative interpretation:* identifies a specific, fixable gap in Rung-1's own evaluator before it's ever relied upon for anything beyond its own current, narrower purpose — valuable regardless of whether §18 is ever built.
   - *Claim level advanced:* none directly, but it is a direct prerequisite for advancing to Level 3-4 in §18's design safely.
   - *Reason it outranks the next action:* cheapest, most directly actionable, and reduces risk for every subsequent action on this list.

2. **A design-only pass specifying and independently reviewing the isolation-redirect implementation §16/§17 require, verified empirically against the real `memory/river_brain.pkl` (the exact "confirm zero bytes landed in the live file" methodology this project's own prior Tier-8 work already proved out) — before any experimental writer of any kind is built.**
   - *Exact question:* does the already-proven redirect pattern, applied to a *new* experimental artifact rather than RiverBrain's own state, actually prevent any write to the live production pickle, verified empirically rather than assumed from reading the patch?
   - *Cost:* low-moderate — requires writing a small, throwaway isolation-verification script (not the experiment itself), run and then discarded.
   - *Risk:* low, provided the verification script itself is never run against the live process while `run.py` is live (per this project's own established `safe_restart.sh`-era discipline, RETRIEVED).
   - *Code changes required:* none to production; a scratch verification script only, outside this report's own current scope to write.
   - *Prerequisite:* none.
   - *Positive interpretation:* isolation is confirmed clean, clearing the single prerequisite §16 names as potentially superseding the reward-wire work.
   - *Negative interpretation:* isolation is confirmed leaky in some new way, which would be a genuinely important, standalone finding — and would supersede any further reward-wire design work until closed, exactly per this mission's own instruction that a broken isolation prerequisite may outrank the reward-wire work itself.
   - *Claim level advanced:* none directly, but is the direct prerequisite for any experiment in §18 to produce trustworthy evidence at all.
   - *Reason it outranks the next action:* it is the one item on this list explicitly named by the mission itself as potentially superseding everything else, and it is cheap and low-risk relative to that stakes level.

3. **Build and adversarially review (not implement into production) a fully-specified, frozen protocol for §18's Track-R-only reward-wire experiment, explicitly scoped to routing learning, explicitly excluding any capability-acquisition claim per §14, and explicitly reusing the frozen persistent-competence protocol v1.1's own already-hardened machinery by citation rather than reinvention.**
   - *Exact question:* can a genuinely independent outcome, connected to a fresh, isolated, restart-surviving statistic, produce a measurable, held-out, twice-replicated routing-learning effect that survives the counterfeit-learner battery in §15?
   - *Cost:* moderate — a real design/write-up effort, comparable in scope to the frozen protocol's own v1.0→v1.1 lineage (RETRIEVED, this session's own prior archaeology), but still no implementation.
   - *Risk:* low as a design exercise; the risk shifts to moderate only once implementation is considered, and this mission does not recommend implementation yet.
   - *Code changes required:* none for the design phase.
   - *Prerequisite:* actions 1 and 2 above, both completed first.
   - *Positive interpretation:* a genuinely reviewable, frozen design ready for the same adversarial-review/blind-review cycle this session's own archaeology already found this project is capable of producing and has, historically, found real, load-bearing flaws through (the v1.0 tie-break exploit itself being the clearest precedent).
   - *Negative interpretation:* a design pass that concludes the experiment cannot be specified cleanly without solving a further prerequisite — itself a valuable, falsifiable finding.
   - *Claim level advanced:* directly targets Levels 3-5 on §13's ladder, explicitly stopping short of Level 6, per §14.
   - *Reason it outranks "do nothing":* the component inventory this session's own prior sibling audit already established (§14/§15 of `2026-09-23_behavioral_state_forensic_infrastructure_audit.md`, RETRIEVED) found this to be the single most repeatedly-confirmed, load-bearing missing link across every mechanism surveyed this research arc — a real, high-information-value gap worth designing toward, not merely noting again.

**"Do nothing / continue current Rung-1 unchanged" was considered explicitly, per the mission's own instruction, and is not recommended as the top-ranked action** — but it is a legitimate fallback if action 1 above finds Rung-1's own evaluator does not yet meet the independence bar needed to support any of this: in that case, the correct next step becomes closing that gap within Rung-1's own existing scope, not building a new, parallel experiment on top of an evaluator not yet proven trustworthy for this purpose.

## 22. Limitations

This mission did not independently re-run a full exploit battery (structurally equivalent to `[QUAL-2]`) against either real production sandbox path (F2, code-verification) — §9's finding that neither shows an obvious leakage vector is based on direct source reading of the relevant call sites and this project's own prior documentation, not a fresh, adversarial live-fire test. This mission did not independently re-verify `river_deliberation.py`'s own `_select_council()` consumption of `score_model()` beyond citing this session's own prior archaeology's characterization of it (§8) — a full independent re-read of that file was out of this mission's own effort budget. This mission's `influence_weight` calculation (§8) is a hand-computation from the live-observed `observation_counts` against the documented formula, not a direct call to the live property itself (which would have required importing the module) — labeled INFERRED for the resulting numeric value accordingly. This mission did not independently trace the terminal client's own rating-capture code end-to-end to confirm `learn_from_rating()`'s model/task-instance binding is never mixed up (§9) — flagged as UNKNOWN rather than assumed. The frozen persistent-competence protocol v1.1's own full statistical machinery (§15 of its own text, per this session's prior archaeology's own disclosed partial-read limitation) was not independently re-read in this mission either — every citation to it here is RETRIEVED from that prior mission's own already-partial read, one further remove from this mission's own direct verification, and a reader relying on this report's own characterization of the frozen protocol's exact statistical thresholds should treat those specific claims as twice-retrieved, not independently confirmed.

## 23. Final state-integrity/provenance block

- **Opening HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce`. **Closing HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` — unchanged.
- **Working-tree integrity:** a `git status --porcelain` snapshot (231 entries) was captured before this mission's first read (`/tmp/rb_audit_status_before.txt`, outside the repository) and compared against the same command at report-writing time; the only difference is this report's own new, untracked path.
- **Files created by this mission:** exactly one — `audits/2026-09-23_riverbrain_independent_outcome_reward_wire_design_audit.md`.
- **Live production state read, not modified:** `memory/river_brain.pkl` was read exactly once, via a bare `pickle.load()` in an isolated `python3 -I -B` subprocess (no `app.*` import, no `get_river_brain()` call, no class instantiation, no writer thread ever started by this mission's own actions). File mtime and byte size were captured before and after this read: `1790197762 4702634`, identical both times — confirming zero mutation.
- **No RiverBrain, `model_task_stats`, `learn_from_sandbox_outcome()`, `learn_from_rating()`, `score_model()`, sandbox machinery, `behavioral_state.py`, `self_model_claims.py`, prompt, configuration, persistent state, Rung-1, `accumulation_probe`, AP-0, E5-mini, frozen-protocol artifact, test, or Git state was modified.** No production process was started, stopped, or restarted. `river.bandit` was not activated. Nothing was connected. Nothing was implemented.

---

## The 24 required questions, answered explicitly

**1. Does real sandbox outcome currently affect `model_task_stats`?**
No — confirmed by reading `learn_from_sandbox_outcome()`'s complete body; it terminates at `self.sandbox_observation_counts[task_type] += 1` and never touches `model_task_stats` (§4).

**2. Does human rating currently affect `model_task_stats`?**
No — confirmed by reading `learn_from_rating()`'s complete body; it terminates at `self.observation_counts[task_type] += 3` and never touches `model_task_stats` (§5).

**3. If not, where exactly does each signal terminate?**
Sandbox: `echo_model_orchestrator.py:880`. Human rating: `echo_model_orchestrator.py:914`. Both are the last stateful writes in their respective methods (§10).

**4. What currently supplies most updates to `model_task_stats`?**
`learn()`, which scores a response's own text via `_score_response_quality()` and credits the result to the producing model — 207,554 real total observations, of which only 70 (≈0.034%) came from the one genuinely council-vetted alternative path (§7).

**5. Is that dominant evaluator independent?**
No — it is self-referential by construction: the text credited to a model is the same text the evaluator scores (§7).

**6. Does `score_model()` causally affect real production behavior?**
Yes, directly and deterministically — `rank_models()`'s combined score includes `score_model()`'s output as an addend in a weighted sum that is then sorted, and `choose_model()` selects from that sorted order (§8). No empirical ablation is needed to establish this mechanism; it is a direct property of the deterministic code.

**7. Is the "broken reward wire" diagnosis confirmed, falsified, or materially revised?**
**Confirmed, and sharpened into an exact, quantified, two-signal-type statement** rather than a single generic claim: two distinct real signal producers (F2 execution-cleanliness, code-verification correctness-checking) both feed one shared, disconnected method, and a real, high-volume genuinely independent signal (16,208 real sandbox observations) is confirmed discarded at an exact, named line (§4, §11).

**8. What is the minimum safe design for reconnecting it?**
Not a direct write to `model_task_stats` — a fresh, isolated statistic, built to `behavioral_state.py`'s own already-proven persistence shape, with separated reward scales per signal type, corrected task-family keying, mandatory provenance, and no live production consumer until independently reviewed (§17).

**9. Should sandbox outcome and human rating feed the same statistic?**
Not without a dedicated design decision — §11/§17 both find that blending qualitatively different signal types (execution-cleanliness vs. correctness vs. human preference) into one field without a distinguishing mechanism is a real, avoidable source of contamination, exactly the problem already partially present in `model_task_stats` itself (`learn()` vs. `learn_from_council_rating()`).

**10. Is `river.bandit` preferable to direct `model_task_stats` updates?**
Yes, comparatively, per §12 — but a fresh, isolated experimental statistic (§17's own design) is preferable to both for a first, cleanly-falsifiable experiment; `river.bandit` remains a real, separately-worthwhile, still-dormant candidate for a later, distinct offline-replay experiment (RETRIEVED, this project's own prior python-capability-gap audit).

**11. Can RiverBrain ever demonstrate capability acquisition while its underlying models remain fixed?**
No, not even in principle — this is a structural, architectural fact, not a design limitation fixable by a better connection (§14).

**12. What CAN RiverBrain legitimately learn?**
Which of its already-fixed, already-installed models to select for a given task type, given real, independent evidence — genuine routing/policy learning, a real and independently valuable claim in its own right (§14).

**13. What is the strongest claim a successful reconnection experiment could establish?**
A cleanly demonstrated, held-out, twice-replicated instance of Level 4-5 on §13's ladder: experience-dependent, independently-evaluated, transfer-tested routing improvement among fixed models — never capability acquisition (§13, §14, §18).

**14. What additional evidence would be required for held-out transfer?**
The frozen protocol's own already-designed E3 (surface-changed)/E5 (structurally novel) held-out cells, applied to the fresh experimental statistic §17 designs, not the live `model_task_stats` (§18).

**15. What additional evidence would be required for accumulated competence?**
A second, independent learning episode with its own fresh held-out measurement, per §18's explicit second-cycle requirement, following the frozen protocol's own already-designed `[LONG-1]`–`[LONG-8]` retention/family-coverage/permutation-trend battery (§18) — and even then, per §14, this would cap at accumulated *routing* competence, never general capability.

**16. Can current RiverBrain state be cleanly isolated across restart for such an experiment?**
Yes, but only via the already-proven redirect-before-first-access pattern, correctly applied to a fresh experimental artifact rather than assumed automatic — this mission recommends independently re-verifying this isolation empirically (§21, action 2) before building anything further (§16).

**17. Would the known v1.0 counterfeit learner fool the proposed experiment?**
Not the specific alphabetical/identity-ordering exploit itself — v1.1's HMAC-keyed tie-break, reused directly in §18's design, already closes that exact mechanism. But this mission constructs three *different* counterfeits (fixed-policy, selection-frequency, task-distribution) specific to a RiverBrain-shaped reconnection, and finds the frozen protocol's own existing defenses (`[QUAL-4]`, `[CAR-9]`, `[PART-2]`/`[LONG-8]`) would catch each, provided they are applied to a fresh carrier and not assumed to generalize automatically to a direct live-pickle write (§15).

**18. Which existing v1.1 defenses should be mandatory?**
`[TIE-1]`/`[TIE-2]` (identity-independent tie-breaking), `[QUAL-4]` (null-effect calibration and positive-control power check), `[CAR-9]` (forced exploration, no selector-driven experience allocation), `[PART-2]`/`[LONG-8]` (structural-novelty and family-coverage controls for held-out cells), and `[HYP-R3]`/`[HYP-C3]`'s poisoned-signal direction-sensitivity check — all reused by citation in §18's own design.

**19. What is the single strongest non-learning explanation for a positive result?**
The fixed-policy/identity-effect counterfeit (§15, item 1): a routing policy that simply keeps favoring whichever model already holds the largest historical observation count and highest existing mean (per §7's live-data table, `echo:latest` and `mlx:qwen3` already dominate) would appear to "improve" outcomes on many realistic held-out sets without any genuine new discrimination having occurred, unless the frozen protocol's own null-effect calibration and forced-exploration controls are both correctly applied.

**20. What observation would most strongly falsify the proposed learning interpretation?**
Per §19's own matrix: a POISON (deliberately wrong) version of the independent signal performing equally well as the genuine signal — per the frozen protocol's own `[HYP-R3]`/`[HYP-C3]`, this single observation is explicitly load-bearing and would prohibit every label above the lowest, carrier-controlled-behavior tier.

**21. What observation would most strongly support it?**
A genuine, twice-replicated (§18's second-cycle requirement) held-out improvement that survives all three of §15's constructed counterfeits, the POISON direction-sensitivity check, and the identity-randomization check — i.e., passing every defense this report's own adversarial analysis raises, not merely the ones the original design anticipated.

**22. Does this investigation justify changing the current Rung-1 roadmap?**
No — per §20, the two efforts are complementary, not competing, and this mission finds no evidence justifying altering Rung-1's own current, narrower, already-in-flight scope. The one actionable dependency worth noting: Rung-1's own evaluator, once qualified, is a plausible future independent-outcome source for the design in §18 — a reason to finish Rung-1's own current work well, not a reason to redirect it.

**23. What should be done next?**
Per §21's ranked list: (1) verify Rung-1's own evaluator meets the independence bar this mission's §9 attack applied to F2/code-verification; (2) empirically re-verify the isolation-redirect pattern against the live `river_brain.pkl`, the same way this mission's own §23 integrity check demonstrates is safe to do; (3) only then, build and adversarially review a fully-specified, frozen, Track-R-only reward-wire protocol.

**24. What should NOT be implemented yet?**
Any direct write to `model_task_stats` from `learn_from_sandbox_outcome()` or `learn_from_rating()` (§11, §17); any wiring of `river.bandit` into a live decision path (§12); any connection of a fresh experimental statistic into `rank_models()`/`choose_model()` before an independent review of the kind this project's own frozen-protocol lineage has already demonstrated is both necessary and productive (§17's own explicit "NOT RECOMMENDED" item); and, per §14, any claim that a successful routing-learning result — however cleanly demonstrated — constitutes capability acquisition.
