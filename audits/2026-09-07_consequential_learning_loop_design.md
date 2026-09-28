# Design: Closing FeralEcho's Consequential Learning Loop

Design/forensic mission. Builds on and independently re-verifies `audits/2026-09-07_consequence_authority_map.md`, `audits/2026-09-07_authority_boundary_deliberateness.md`, `audits/2026-09-07_temporal_authority_graph.md`, and `audits/2026-09-07_missing_primitive_determination.md`. **No production code was modified. Nothing was implemented, reconnected, or wired.**

## Safety Verification

- `run.py`/watchdog: confirmed not running before starting (`ps aux`), port 5000 unbound (`lsof -ti :5000` empty).
- Git HEAD: `c5bf2e5f8913e35a1ded9af8afe68e247651e26d` — confirmed identical before and after. Zero commits, zero amends.
- `river_brain.pkl` sha256: `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` — unchanged; RiverBrain was never imported or called by this mission.
- No production source modified. No self-edit run. No RiverBrain learning calls. No mechanism reconnected. Only this report file was created.

---

## 1. Executive Conclusion

**FeralEcho already has a real, live, closed consequential learning loop.** It is narrow — one task type, one decision point — but it is genuine: a past consequence measurably changes a later, independent decision, through machinery that already exists and is already running continuously in production. This was not previously stated plainly in any of the four prior audits, each of which examined individual mechanisms (RiverBrain, the fitness gate, Shadow, retrieval) in isolation without tracing them end-to-end into one cycle. Doing that tracing here (§10) is this mission's main contribution.

The deficiency is not "no machinery exists" — it is that this one real loop is (a) narrow in scope, (b) was silently corrupted for 7 real days by exactly the temporal-drift pattern the prior missions found, with **zero observability** into the corruption, and (c) has no comparable sibling for any of Echo's *other* real consequential activity (conversational quality, self-edit's own internal retry/failure evidence, seam-detected contradictions). The smallest real intervention is not a new learning loop — it's protecting the one that already exists, and giving self-edit's own richest untapped evidence (the attempt ledger built earlier tonight) a role inside that same loop rather than building a second, parallel mechanism.

---

## 2. Definition of Loop Closure, Derived From What Actually Exists

Rejecting the abstract candidate structure in favor of what Echo's real components actually support:

```text
GENERATION DECISION           choose_model(task_type)
        ↓
ACTION                        generate_code_from_plan() produces a candidate
        ↓
INDEPENDENT EVALUATION        _score_response_quality() / F1-F2-F3 sandbox
        ↓
ATTRIBUTED WRITE               RiverBrain.learn(model_name, task_type, response)
        ↓
DURABLE STATE MUTATION         model_task_stats[model_name][task_type]
        ↓
LATER, INDEPENDENT GENERATION DECISION   choose_model(task_type) — reads the mutated state
```

A loop is "closed" in this codebase specifically when the state mutated at the bottom of one cycle is the same state read at the top of a *later, independently-triggered* cycle — not merely logged, not merely persisted, but genuinely re-consulted by a decision point with the authority to act differently because of it. This is a direct instantiation of the Consequence Authority Map's own COMPUTED→PERSISTED→READ→AUTHORITATIVE test, extended one step: a true *loop* additionally requires that the READ happens **on a later occasion, from a different call**, not the same call that did the writing.

---

## 3. Current Causal Path — Where It Is Closed, and Where It Stops

### 3.1 The one path that is genuinely closed (traced in full, §10)

```text
choose_model("self_edit_coding")   [self_edit_manager.py:1822, 2050]
   ↓ reads model_task_stats via rank_models()/score_model()
generate_code_from_plan()          [self_edit_manager.py:1785]
   ↓ produces candidate code
RiverBrain.learn(model_name, "self_edit_coding", code)   [self_edit_manager.py:1843, 2059]
   ↓ internally calls _extract_quality_features_v2 / _score_response_quality
   ↓ (echo_model_orchestrator.py:61, importing from echo_quality_scorer.py)
model_task_stats[model_name]["self_edit_coding"]["mean"] mutates   [echo_model_orchestrator.py:828-844]
   ↓
NEXT choose_model("self_edit_coding") call — a different, later, independently-
triggered self-edit cycle (hourly production attempt, or one of Optuna's ~10
dry-run trials/hour) — reads the mutated mean via rank_models() → different
sort order is possible → a different model can be selected.
```

This is real. It is not hypothetical, not "would work if wired," not a metaphor. It runs continuously today, gated only by the ordinary self-edit cadence (roughly 1 real attempt/hour plus ~10 Optuna dry-run trials/hour, per this project's own documented cadence).

### 3.2 Where the architecture stops being causally closed

Three exact break points, named precisely rather than described as "feedback is weak":

1. **`self_edit_manager.py`'s own richest evidence never enters the loop above.** `_sanitize_sandbox_error()`'s clean_error diagnosis (built at `self_edit_manager.py:1999`) and, since tonight, the full attempt-level record in `self_edit_attempt_ledger.py` are never read by `choose_model()`, `generate_code_from_plan()`, or `plan_code_logic()`. The loop in §3.1 knows *that* a candidate scored well or poorly; it has no access to *why*, even though that information is now durably captured a few lines away in the same function.
2. **The loop's own scoring machinery was silently corrupted for 7 real days** (2026-07-16 to 2026-07-23, per the Temporal Authority Graph's `TASK_TYPE_MAP` finding) — `_extract_quality_features_v2()`'s `task_type_id` feature silently defaulted to `general`'s value (0) for every real `self_edit_coding` response in that window, because `echo_quality_scorer.py`'s local copy of `TASK_TYPE_MAP` hadn't been updated. **No log line, no exception, nothing observable marked this.** The loop kept running the whole time; it was just running on a corrupted input, invisibly.
3. **No comparable loop exists for anything Echo does outside self-edit code generation.** Conversational quality (personal/creative/reasoning/general task types) is scored and written into the identical `model_task_stats` structure (`learn()` is task-type-agnostic), so those loops are *also* real and closed by the same mechanism — this generalizes further than the prior four audits stated. What has **no loop at all** is: seam-detected contradictions (76/78 lost at the garden filter, per the Consequence Authority Map), Shadow's episodic corrections (deliberately withheld), and the attempt ledger's rich per-attempt evidence (deliberately inert, by tonight's own design).

---

## 4. Four-Way Gap Classification for Every Missing Transition

| Missing transition | Classification | Why |
|---|---|---|
| Attempt-ledger evidence → generation prompt | **Wiring gap** | The capability exists (the ledger is a live, well-formed record); nothing consumes it. Writing a consumer is the whole fix. |
| `TASK_TYPE_MAP` sync | **Feedback gap** (a decision was made — deploy a quality feature — but the system cannot reliably connect a later divergence back to the moment it was introduced) — not a capability gap, since the correct value is always computable, just not consistently computed. | Confirmed: `CATEGORIES`' own historical fix (§7 of the missing-primitive report) shows the *capability* to compute a correct, dynamic domain already exists in this codebase; it just wasn't applied to this specific consumer. |
| `seam_engine` → garden | **Authority gap**, specifically the collateral-damage subtype already established (Authority Boundary Deliberateness audit) — the call exists (`harvest_question()` fires), the output is consumed, but a downstream filter revokes its effect without ever having evaluated this producer. | Not a wiring gap (the wire is there); not a capability gap (the filter works fine for its own intended domain). |
| Shadow's `corrected_task` → any decision | **Wiring gap, deliberately unresolved** — per the Shadow Treatment Harness mission (S-T0), there is currently no defined *decision point* for it to feed, so this is arguably closer to a **capability gap masquerading as a wiring gap**: writing the call site alone would not close the loop, because nothing downstream has been built to receive it meaningfully. | Confirmed directly: `night_cycle.py:182-186`'s only consumer is a log line; no consequential decision point exists to wire it into even if `propose()` were restored. |
| Retrieval quality/relevance | **Capability gap** — the existing mechanism (cosine similarity over embeddings) genuinely cannot distinguish causal relevance from lexical similarity; this was demonstrated experimentally tonight (Retrieval Capacity Proof, R2: a wrong distractor scored 0.4613 against a correct record's 0.427), not merely unwired. | The Minimal Relevance Gate mission's own finding (a single-call LLM judge solves the motivating case but is fooled by fabricated narratives) confirms this is a genuine capability shortfall, not a missing connection. |

---

## 5. Reconciling the Missing-Primitive Finding

The missing-primitive determination recommended extending the Liveness Ledger's existing discipline: *"a new capability needs its own check, and every existing fixed-domain consumer that its output will now pass through must be checked against it in the same change."*

What makes this enforceable rather than aspirational, evaluated against the actual repository conventions already in place (not invented from scratch):

- This project already has a **structural precedent for enforceability**: the Liveness Ledger's own rule ("a new capability needs its own check") is not merely written down in CLAUDE.md prose — it is backed by `scripts/verify_liveness_ledger.py`'s discrimination-test suite, which fails loudly if a check's own evaluator silently degrades. The proposed extension needs the equivalent: not a checklist item a human might skip under time pressure, but a **cheap, automatable, purely-observational check** — the same pattern this session's own attempt ledger and 30+ existing Liveness Ledger checks already use — that can verify, mechanically, whether a *known* set of fixed-domain consumers stays in sync with a *known* set of producers.
- Concretely and minimally: a single new Liveness Ledger check, in the same spirit as the 30 that already exist, that (a) diffs the two known `TASK_TYPE_MAP` copies and fails loud if they diverge, and (b) confirms `_is_near_duplicate()`'s (or its future equivalent's) candidate pool includes every `category`/`source` value actually present in `data/question_garden.jsonl`. This does not require a new subsystem — it is one more entry in a table that already has 30 rows, using the identical pattern (`_evaluate_X()` pure function, `scripts/verify_liveness_ledger.py` discrimination cases) every other check in this codebase already follows.
- This reframes "enforceability" correctly: the rule is enforceable *because this project already has the exact mechanism that would enforce it* — the gap is that the mechanism's own coverage never extended to these two specific, already-fixed-domain consumers. Not a new capability. A new row in an existing table.

---

## 6. Role of Each Authority Mechanism in the Eventual Loop

| Mechanism | Recommended role | Why |
|---|---|---|
| RiverBrain `model_task_stats` | **Already IS the loop's core** (§10) — no change needed to its role, only to what feeds it | This is the one mechanism proven, tonight, to genuinely close a cycle. Everything else should be evaluated for whether it can safely become a *new producer into this existing loop*, not a separate loop. |
| Self-edit fitness gate | **Stays independent, one level upstream of the loop** | Its authority (deploy vs. reject) is a *safety* decision, not a *learning* decision — conflating them risks letting a "the model that got deployed" signal override "the model that generates good code on average," which are related but not identical questions. Keep separate. |
| Council-rating blend | **Already a second producer into the same loop** (confirmed live, Finding 67) — no change | Directly demonstrates the recommended pattern for everything else in this table: a new evidence source feeding the *existing* authoritative state, not a parallel state. |
| Garden `resolution_score` weighting | **Stays independent** | Governs question-selection, a different consequential domain (curiosity/self-reflection content) from model-selection quality. No evidence a shared mechanism would improve either. |
| Council trust gate | **Stays independent** — it's a meta-gate controlling whether the council-blend producer above is allowed to write at all, not itself part of the loop's state | Already correctly scoped; it protects the loop's input quality rather than participating in the loop. |
| Shadow's `corrected_task` | **Stays outside the minimum viable loop, per §8** | No demonstrated need and no current decision point to feed, per S-T0. |
| Attempt ledger | **Becomes a new producer feeding the existing loop's *prompt construction*, not `model_task_stats` itself**, per §9 | Its information (why a specific attempt failed) is different in kind from a quality score — it belongs in the *generation* step, not the *scoring* step. |

---

## 7. Retrieval — Minimum Role Required

Traced per the mission's own instruction: searched for superseding pathways before assuming reconnection is the only option. Confirmed (re-verifying the Orphaned Memory Retrieval and Retrieval Capacity Proof findings directly): no alternate memory pathway has superseded `retrieve_relevant_memories()` for self-edit specifically — `self_edit_manager.py` has zero FAISS calls, zero interaction-log reads, and zero cross-session memory queries of any kind for its own generation or retry prompts. The 9 real system-wide callers all serve conversational/curiosity/tool-dispatch paths, not self-edit.

**Retrieval is not required for the first closed loop.** The loop demonstrated in §10 works entirely on `model_task_stats`, which requires no retrieval of any kind — it is a live, aggregated statistic, not a retrieved memory. Retrieval would only become relevant if a *future* phase tried to inject specific historical failure examples into a generation prompt (the exact mechanism Architecture A tested and found ineffective — HOT-STOVE NOT PROVEN, production retry already succeeds ~83% without it). Given that finding, retrieval is explicitly **not** part of the recommended minimum architecture below.

---

## 8. Shadow — Explicitly Not Reconnected

Per the Shadow Treatment Harness mission (S-T0): `check_and_correct()`'s output has no operational definition of an intervention — nothing downstream distinguishes "what would happen with the correction applied" from "what happens without it," so there is no experiment that could validate it even if wired. Building a decision point for it now, purely to give a 16.05%-accurate predictor (worse than a 58.78% trivial baseline, per the Shadow Correction Validation Archaeology) somewhere to matter, would be manufacturing consequence for a mechanism that hasn't earned it — precisely the anti-pattern this whole session's discipline has been built to catch.

**Leave Shadow outside the minimum viable loop.** Nothing in this design requires it.

---

## 9. Attempt Ledger — Identifying the Missing Consumer

The attempt ledger (`self_edit_attempt_ledger.py`, built tonight) records, per real attempt: `initial_f2_outcome`, `initial_f2_error` (the raw sandbox traceback, captured *before* the "success_on_retry" overwrite that used to destroy it), `retry_occurred`, `retry_f2_outcome`/`retry_f2_error`, `fitness_score`, `production_score`, `fitness_decision`, `deployed`.

This contains exactly the information a future generation attempt would need to avoid repeating a specific, named failure signature (e.g. the real, recurring `functools`/`re` NameErrors documented across tonight's Hot Stove and Initial-Generation-Influence audits). **The missing consumer is precisely the gap the Initial-Generation Influence audit already located**: `plan_code_logic()`/`_build_targeted_prompt()` in `self_edit_manager.py`, which currently builds its Focus-text from `self_edit_convergence.json`'s function-name history and `_recent_experiment_note()`'s unrelated exploration log — never from the attempt ledger's own `initial_f2_error` field.

Critically: Architecture A already tested *exactly this intervention* — injecting a specific causal hypothesis into a retry prompt — and found **zero measurable effect** (CONTROL 5/6, EXPERIENCE 5/6, identical). That result governs this recommendation directly: **do not wire the attempt ledger into the retry-prompt path** (already disproven). The Initial-Generation Influence audit's own conclusion was that the untested, more promising target is *initial*-generation prompt construction, not retry — a distinction Architecture A never actually tested. Per §11's causality standard, this means the attempt ledger's correct role is a **candidate feed into `plan_code_logic()`'s initial prompt**, explicitly untested and explicitly requiring its own held-out experiment (§19) before being trusted the way `model_task_stats` currently is — not something to wire in on the strength of this design document alone.

---

## 10. The Core Question, Traced End-to-End With Real Code Locations

**Real pathway: self-edit code generation, one full cycle.**

| Arrow | Code location | Status |
|---|---|---|
| EVENT (a self-edit cycle triggers) | `run.py`'s `AutonomousSelfEdit` thread / `EchoOptuna.optimize_self_edit()` | EXISTS |
| Echo makes a generation decision | `choose_model(code_prompt, task_type="self_edit_coding")` — `self_edit_manager.py:1822` | EXISTS, reads `model_task_stats` |
| decision produces consequence | `generate_code_from_plan()` — `self_edit_manager.py:1785` returns `(code, model_name)` | EXISTS |
| consequence becomes observable | `test_code_in_sandbox(code)` (F2), `_score_response_quality()` (fitness gate) — `self_edit_manager.py:2179` and inside `learn()` | EXISTS |
| consequence is attributed | `RiverBrain.learn(model_name, "self_edit_coding", code)` — `self_edit_manager.py:1843` | EXISTS — attribution is the `model_name` argument, a real, correct identity |
| quality/resolution evaluated | `_extract_quality_features_v2()` / `_score_response_quality()` — `echo_quality_scorer.py`, called from inside `learn()` (`echo_model_orchestrator.py:815`) | EXISTS, **but was silently corrupted 2026-07-16→23 by the `TASK_TYPE_MAP` drift** |
| learning signal generated | `model_task_stats[model_name]["self_edit_coding"]` mutation — `echo_model_orchestrator.py:828-844` | EXISTS |
| signal crosses an authority boundary | Same dict, read by `rank_models()`/`score_model()` — `echo_model_orchestrator.py:1153+` | EXISTS — this *is* the authority boundary |
| future decision changes | Next `choose_model("self_edit_coding")` call, a later independent cycle | EXISTS, demonstrated by construction (a different `mean` produces a different `combined[model]` sort key) |

**Every arrow exists for this one pathway.** This directly contradicts the framing (implicit in all four prior audits) that Echo's loop is fundamentally missing — for this specific task type, it is not. The smallest missing connection that would make *additional* consequence real is not a new arrow in this diagram; it's (a) protecting the arrows that already exist from silent corruption (§13) and (b) adding a second, parallel producer — the attempt ledger — feeding the *generation* step rather than duplicating the *scoring* step.

---

## 11. Proving the Loop Is Actually Causal

Rejecting the weak forms explicitly, per the mission's standard:

- Not `event → log → score → log`: the score is not merely logged, it mutates a dict a *different, later function call* reads and acts on.
- Not `decision → metric`: the metric is not terminal; `rank_models()` consumes it to produce a *different* ranked order.
- Not `event → memory → retrieval`: no retrieval is involved in this loop at all (§7).

**The exact future decision, demonstrated by direct code inspection, not assumption**: `rank_models(task_type)`'s `combined[model]` sort key is a direct arithmetic function of `score_model(model, task_type)`, which reads `self.model_task_stats[model].get(task_type, {}).get("mean")`. Two different `mean` values for the same model, all else equal, produce two different sort positions in the returned ranking, which `choose_model()` (and `_select_council()`, independently) use directly to pick a model. This was independently re-verified this session (not merely cited) via direct source read of `score_model()`'s arithmetic — no additional runtime test was needed because the causal chain is a pure, static function composition, not something that could only be demonstrated empirically.

---

## 12. Safety Analysis — Preserving Every Existing Invariant

| Invariant | How the recommended design preserves it |
|---|---|
| RiverBrain influence ceiling (`_MEAN_EFFECTIVE_WINDOW`, Finding 39) | Untouched — the attempt ledger feeds *prompt construction*, never `model_task_stats` directly, so no new write path to RiverBrain is introduced. |
| Fitness gate (`candidate_quality < current_quality`) | Untouched — remains the sole deployment gate; attempt-ledger evidence only ever influences what gets *generated*, never bypasses the check on what gets *deployed*. |
| Candidate/current quality comparison | Untouched, same reasoning. |
| Council trust gate | Untouched — the recommended design adds no new council-rating producer. |
| Garden monotonicity | Untouched — no change to garden mechanics is proposed. |
| Self-edit restrictions (`EDIT_FORBIDDEN_TARGETS`, F1/F2/F3) | Untouched — the recommended Phase 1 (§18) touches only `self_edit_manager.py`'s own prompt-construction code (not on the forbidden list) and adds a read, not a write. |
| Watchdog / persistence boundaries | Untouched — no new background thread, no new file outside `memory/`. |

**What prevents a bad consequence from becoming an increasingly powerful bad signal**: the existing `_MEAN_EFFECTIVE_WINDOW` cap already answers this for the `model_task_stats` loop (Finding 39's own stated purpose). For the *new* attempt-ledger→prompt-construction connection, the equivalent protection is Architecture A's own finding: a single bad or misleading injected hypothesis already demonstrated **zero measurable effect** on generation — meaning the blast radius of a wrong injected failure signature is empirically bounded at "does nothing," not "actively misleads," at least for the one case tested. This should not be assumed to generalize without the held-out test in §19.

---

## 13. Addressing the Three Confirmed Temporal-Drift Cases

**How a hypothetical fourth producer's author would discover a relevant downstream constraint, under the recommended design (§5's Liveness Ledger extension)**: they would see a new check row (`task_type_map_sync`, `garden_domain_coverage`, or equivalent) in the same `_CHECKS` table every other capability in this codebase is already required to extend, following the exact same discipline CLAUDE.md's own text already states for "new autonomous capability." The check would fail loud (`[LIVENESS-ALERT]`, matching this project's existing convention) the moment a fourth category diverges, rather than waiting up to 7 days for an unrelated commit to stumble onto it a third time.

- **`CATEGORIES`**: already fixed (§7 of the missing-primitive report) — no action needed, cited here as the working precedent the new checks should mirror.
- **`TASK_TYPE_MAP`**: covered by a new sync-check, following the exact pattern established.
- **`seam_engine`**: covered by a new coverage-check confirming `_is_near_duplicate()`'s candidate pool includes every `category`/`source` combination present in the live garden data — the same technique, applied to the second real case.

---

## 14. Minimum Necessary Provenance

Not proposing a full provenance framework. The minimum needed for the recommended design: `model_task_stats` already carries provenance by construction (keyed by `(model_name, task_type)` — confirmed, Consequence Authority Map). The attempt ledger already carries `trace_id` and `task_type`. **No new provenance field is required** — the gap identified tonight was never "information lacks provenance," it was "a downstream consumer doesn't read the provenance fields that already exist" (`_is_near_duplicate()` ignoring `category`/`source` that are already present on every garden entry, confirmed directly in the Temporal Authority Graph). The fix is making existing consumers read existing fields, not adding new ones.

---

## 15. Attribution

Already solved for the loop in §10: `model_name` is the attribution key, passed explicitly through every step from `choose_model()`'s return value to `learn()`'s first argument — no ambiguity, no correlation identifier needed beyond the value already being passed as a plain function argument. For the proposed attempt-ledger connection, `trace_id` (added earlier tonight, Plan 5) already provides an equivalent lightweight correlation identifier across `interaction_log.jsonl`, `council_deliberations.jsonl`, and the attempt ledger itself. **No new attribution mechanism is needed for either connection.**

---

## 16. Candidate Architectures

### Option A — Minimal Loop Closure
**Components**: one new read inside `_build_targeted_prompt()`/`plan_code_logic()`, consuming the attempt ledger's most recent `initial_f2_error` for the target task type.
**Files affected**: `self_edit_manager.py` only.
**New primitives**: none.
**Complexity**: Low — a few lines, following the existing pattern `_recent_experiment_note()` already uses for a different log.
**Operational risk**: Low — Architecture A already empirically bounded the blast radius of a wrong injected hypothesis at "no effect," for the retry-prompt case; untested for initial-generation prompts specifically.
**Feedback risk**: Low — read-only consumption of an already-inert ledger; no new write path.
**Safety**: Full — no gate touched.
**Reversibility**: Full — a one-line removal.
**Testing burden**: One held-out experiment (§19), mirroring Architecture A's own design but targeting initial generation instead of retry.

### Option B — Minimal + Architectural Guard
**Components**: Option A, plus two new Liveness Ledger checks (§5, §13) closing `TASK_TYPE_MAP` and `seam_engine`'s specific drift cases.
**Files affected**: `self_edit_manager.py`, `liveness_ledger.py`, `scripts/verify_liveness_ledger.py`.
**New primitives**: none — extends the existing check table, the existing discrimination-suite pattern.
**Complexity**: Low-Medium — two more rows in a table that already has 30.
**Operational risk**: Very low — purely observational checks, same posture as every existing one.
**Feedback risk**: None — checks don't write to production state.
**Safety**: Full.
**Reversibility**: Full.
**Testing burden**: Standard discrimination-case additions, the same shape as every prior Liveness Ledger extension this project has already done repeatedly.

### Option C — Longer-Term Architecture
**Components**: a general producer-registration system requiring every new capability to formally declare itself and be matched against every fixed-domain consumer automatically; a provenance-carrying data contract for all inter-module consequence flow; a unified "consequence bus" generalizing the pattern in §10 to every task type and mechanism (Shadow, seam_engine, retrieval) at once.
**Files affected**: broad — touches `echo_core.py`'s Global Workspace bus, `garden_manager.py`, `shadow_model.py`, `self_edit_manager.py`, and introduces at least one new module.
**New primitives**: a formal registration/contract system — genuinely new infrastructure.
**Complexity**: High.
**Operational risk**: Medium-High — new infrastructure is itself a new source of the exact drift class this investigation exists to prevent (explicitly flagged as a risk in the missing-primitive report).
**Feedback risk**: Higher — a unified consequence bus makes it easier, not harder, for a bad signal in one domain to leak into another (e.g. Shadow's 16.05%-accurate predictor gaining unintended reach via a shared bus).
**Safety**: Requires new safeguards to be designed from scratch, rather than reusing proven ones.
**Reversibility**: Poor — broad, cross-cutting changes are harder to cleanly revert.
**Testing burden**: Very high.

---

## 17. Recommendation

**Option B.** Not A alone, because A without the guard leaves the exact silent-corruption failure mode (§3.2, point 2) fully intact — the new attempt-ledger connection would be exactly as vulnerable to an undetected drift as the `model_task_stats` loop already was for 7 real days. Not C, for three independently sufficient reasons: (1) no evidence from any of tonight's three real drift cases shows automated cross-matching would catch anything a two-line Liveness Ledger check wouldn't; (2) this project's own established culture (visible across its entire Findings history and this whole night's investigation) consistently prefers narrow discipline extensions over new infrastructure, and has been directly burned by the opposite instinct before (WOLF); (3) a "consequence bus" is itself a new fixed-domain consumer that would need its own drift protection — the recursive version of the problem being solved.

**What I would deliberately NOT connect yet**: Shadow (no operational decision point exists for it, §8); retrieval (empirically shown to add noise more than signal for this use, §7); a direct wire from the attempt ledger into `model_task_stats` itself (would conflate "why a candidate failed" with "how good a candidate was," two different kinds of evidence that should stay in separate fields per §14's minimum-provenance principle).

---

## 18. Implementation Roadmap (not implemented here)

- **Phase 0 — Instrumentation**: add one log line to `learn()` recording the `task_type_id` feature value actually used for each real call, so a future audit can directly observe whether the two `TASK_TYPE_MAP` copies are in sync at write time, without needing a separate script.
- **Phase 1 — Explicit consequence representation**: extend `_build_targeted_prompt()`/`plan_code_logic()` to read the attempt ledger's most recent `initial_f2_error` for the target task type and surface it as a distinct, labeled section of the initial-generation prompt (not mixed into the existing Focus text) — makes the signal identifiable and independently attributable to the ledger, not silently blended.
- **Phase 2 — Connect existing evaluation to authority**: no new gate — reuse the existing fitness gate and F1/F2/F3 pipeline unchanged; Phase 1's only effect is on what gets *generated*, evaluated by machinery that already exists.
- **Phase 3 — Connect authority to future decision**: already true for `model_task_stats` (§10); for the new Phase 1 connection, "future decision" is whether the *next* candidate for the same failure signature avoids it — measured directly, not assumed.
- **Phase 4 — Temporal-boundary protection**: add the two Liveness Ledger checks from §5/§13 in the same change that ships Phase 1, per this project's own extending-discipline rule applied to itself.
- **Phase 5 — Validation**: the acceptance tests in §19, run before Phase 1 is considered complete.

---

## 19. Acceptance Tests

**Positive (mirrors Architecture A's own design, corrected for the untested target)**:
1. Mine a fresh, currently-recurring failure signature not yet exposed to any targeted fix (same discipline as Architecture A's `functools` case).
2. CONTROL: real initial-generation attempts with no attempt-ledger injection.
3. EXPERIENCE: real initial-generation attempts with the Phase 1 injection.
4. Matched-pair comparison through the real F2 sandbox, McNemar-style, same standard as every prior experiment tonight.
5. A measurable difference, replicated once, is required before this connection is trusted with any further authority.

**Negative tests** (per the mission's own explicit list):
- Bad consequence: inject a deliberately wrong `initial_f2_error` and confirm generation quality does not measurably degrade (bounds the downside, mirroring Architecture A's "no effect" finding rather than assuming it).
- Misleading consequence: inject a plausible-but-wrong diagnosis (the exact shape that fooled the Minimal Relevance Gate mission's G2 judge) and confirm the *unmediated* prompt injection (no LLM judge in this path) doesn't inherit that specific failure mode.
- Duplicate consequence: two ledger entries for the same trace_id (verify this cannot happen — `record_attempt()` fires exactly once per attempt, confirmed in tonight's implementation).
- Stale consequence: an attempt-ledger entry older than N cycles — confirm the Phase 1 read filters by recency the same way `_recent_experiment_note()` already does for its own log.
- Unrelated consequence: a ledger entry for a different task type — confirm the Phase 1 read filters by `task_type`.
- New producer entering an old filter: directly exercise the new `task_type_map_sync` Liveness Ledger check with a synthetic third-key divergence and confirm it fails loud.
- Stale duplicated registry: same test, targeting the actual `TASK_TYPE_MAP` pair.
- Missing consumer: confirm the attempt ledger's `record_attempt()` calls still succeed identically whether or not Phase 1's reader exists (preserves the write-only-sink property for any caller that hasn't opted in).

---

## 20. Observability Requirements

Minimum, not exhaustive: for every Phase 1 injection event, one log line recording (a) which ledger entry was read, (b) its `trace_id`, (c) whether the resulting candidate's F2 outcome matched or diverged from the injected entry's own outcome. For the two new Liveness Ledger checks, the existing `[LIVENESS-ALERT]` convention already provides sufficient loud failure — no new logging infrastructure needed.

---

## 21. Explicit Non-Goals

Not proposing: unrestricted self-modification, a general reward model, a reinforcement-learning subsystem, universal autonomy, a new memory architecture, a centralized event bus, or any change to what self-edit is *permitted* to modify. The design adds exactly one new read path and two new observational checks — nothing gains new authority to deploy code, bypass F1/F2/F3, or override the fitness gate.

---

## 22. Risks and Failure Modes

- **Risk**: Phase 1's injection, even empirically bounded by Architecture A's "no effect" finding for the retry case, might behave differently for initial generation — the acceptance test in §19 exists specifically because this is unproven, not assumed safe by analogy.
- **Risk**: a Liveness Ledger check that itself silently degrades (this project's own established failure mode, documented for two of its 30 existing checks in this session's history) — mitigated by following the same discrimination-suite pattern (`scripts/verify_liveness_ledger.py`) already proven to catch this class of regression.
- **Failure mode to explicitly watch for**: Phase 1 succeeding at changing behavior without improving outcomes — the exact "decision bypass" vs. "behavioral-change-without-improvement" distinction the Hot Stove/Credit Assignment audit's own definitions (§3 of that report) already warn against conflating.

---

## 23. What Should Remain Deliberately Disconnected

Shadow (§8), retrieval for self-edit specifically (§7), and any direct write path from the attempt ledger into `model_task_stats` (§17) — restated here as the explicit final answer to what this design does *not* recommend building.

---

## 24. Final Recommendation

**Section 23's question, answered directly: yes, FeralEcho already possesses most of the machinery necessary for a consequential learning loop, and the primary deficiency is exactly what the question proposes — the machinery is not connected by explicit, attributable authority boundaries, in the specific places this investigation found.** This is proven, not asserted: §10 traces one complete, real, currently-running loop end-to-end with code-level evidence at every arrow, and §3.2/§13 identify the exact three places (all previously found across tonight's four prior audits) where an old, deliberate decision governs a newer producer with nobody having explicitly checked the two against each other.

**The smallest architectural intervention the evidence can defend**: extend the Liveness Ledger's existing discipline with two new checks protecting the loop that already exists (§5, §13), and give the attempt-level evidence built earlier tonight exactly one new consumer — a read inside self-edit's own initial-generation prompt construction — validated by a held-out experiment before it is trusted, per Architecture A's own established standard. Nothing else. This does not make Echo more autonomous. It makes the one real learning loop Echo already has both harder to silently corrupt and slightly less narrow than it is today.
