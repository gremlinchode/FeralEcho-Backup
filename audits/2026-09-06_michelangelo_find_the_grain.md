# FeralEcho — Michelangelo IV: Find the Grain

Read-only. No production code, config, model weights, RiverBrain state, memory, or logs modified.
`git status` before and after this pass shows only pre-existing changes from earlier tonight's work
(the killed memory-ablation experiment's two output JSONs, `sandbox/safe_exec_wrapper.py`,
`sandbox/scripts/temp_self_edit.py`) plus this new report file — nothing this pass touched.

## 1. Executive Summary

Serious, dedicated effort was spent hunting for a genuine positive case beyond what Michelangelo III
already established (RiverBrain L3-on-a-weak-proxy, shadow model L2). **None was found.** Worse: the one
remaining plausible candidate — self-edit's convergence-tracking corrective ("stop adding new functions
after repeated failure") — was found, this pass, to be **structurally broken in a way its own code
comment already half-admits but whose practical consequence had never been checked against real data**:
across 95 real `prose_stripping` cycles and 58 real `response_shortening` cycles, each producing 31-32
completely distinct function names, the tracked `non_convergent_streak` sits at **0** for both, right
now, because the check compares raw function *count* cycle-to-cycle, not function *identity* — and
almost every self-edit candidate defines a similar, small count of functions regardless of what it names
them. The corrective sentence this mechanism exists to inject has had almost no real opportunity to fire,
across two of the three longest-running, most persistently-failing families in the project's history.

This is not a new failure mode in kind — it is the same "measurement exists, doesn't measure what it
claims to" pattern every prior Michelangelo pass found — but it closes off what looked, going in, like
the single most promising remaining candidate for genuine in-system adaptation.

## 2. Mission and Methodology

Built a candidate inventory (§3) from mechanisms not yet deeply investigated by prior passes tonight,
prioritized per the mission's own suggested list (self-edit retry generalization, `crash_awareness.py`
MLX avoidance, `night_cycle.py` adaptivity, `emergent_scheduler` curiosity-bias effectiveness), read the
real source for each, and where a historical record exists, queried it directly rather than trusting a
docstring's claim. Treated Michelangelo III's RiverBrain/shadow-model/seam_engine/council-blend findings
as established (re-cited, not re-derived) per this pass's own explicit brief.

## 3. Candidate Mechanism Inventory

| Mechanism | Initial L-level (hypothesis) | Verified L-level | Basis |
|---|---|---|---|
| RiverBrain `model_task_stats` | L3 | **L3 — confirmed, established prior** | `[inherited, doubly independently confirmed]` |
| Shadow model | L2 | **L2 — confirmed, established prior** | `[inherited, doubly independently confirmed]` |
| `seam_engine` → garden | L1-L3? | **L0/L1 — established prior** (76/78 lost) | `[inherited]` |
| Council-rating blend | L2-L3? | **L1 at best** — structurally can't resolve disagreement (established prior) | `[inherited]` |
| Self-edit retry-on-failure | L1-L3? | **L1, no generalization (G0)** — see §6 | This pass, direct |
| Self-edit convergence tracker → `_build_targeted_prompt()` | L2-L3? | **L1 at best, and the "L2" measurement itself is broken** — see §7 | This pass, direct, new |
| `crash_awareness.py` MLX avoidance | L2-L3? | **L1** — real engage/disengage, but disengagement is a fixed timer, never checks whether the crash rate actually improved | This pass, direct |
| `emergent_scheduler` curiosity-topic-bias | L1-L3? | **L1, effect on subsequent surprise not established either way** | This pass, direct; genuinely unresolved, not a negative finding |
| `night_cycle.py` janitor/log-retention | L0-L1 | **L0-L1** — fixed-threshold rules (size/age caps), no adaptive parameter found anywhere in source | This pass, direct |

## 4. Loop-Level Classifications

Per §3. No mechanism in this pass's search reached L4. RiverBrain (L3) and the shadow model (L2) remain
the ceiling, unchanged from Michelangelo III.

## 5. Strongest Positive Learning Candidates

In descending order of how close they came before failing:

1. **Self-edit convergence tracker.** Real, persisted, real decision (prompt text) actually changes
   based on it. Would have been the strongest new candidate this pass if the underlying measurement
   worked. It doesn't (§7) — the streak that's supposed to trigger the correction essentially never
   accumulates for the two families that most need it.
2. **`crash_awareness.py` MLX avoidance.** Real engage/disengage cycle on real crash data (`[inherited]`
   confirmed genuinely engaging/disengaging historically). Fails at the OUTCOME step (§8) — disengagement
   is a pure timer, never checks whether crashes actually stopped.
3. **`emergent_scheduler` curiosity-topic-bias.** Real, live, biases prompt selection toward a real
   surprise signal. Genuinely unresolved (not failed) — see §11.

## 6. Strongest Failure → Correction → Success Chain

**Self-edit's in-call retry** (`self_edit_manager.py:2002-2048`) is real: a sandbox failure's exact error
text is fed back into a corrected retry within the *same* `execute_self_edit()` call, and a meaningful
fraction of retries do succeed after failing once (confirmed by the existing `success_on_retry` tag in
real reflection data, `[inherited]`). This satisfies stages Experience through Intervention cleanly.

**It fails at Generalization (G0).** The corrected error text (`clean_error`, a local variable) is never
written to any store a *later*, independent self-edit cycle could read. `advise_before_edit()` — the one
function that injects prior guidance into every cycle's prompt — was read in full this pass and confirmed
to return only static, generic Python best-practice tips from `echo_python_mastery`'s fixed modules, with
zero dynamic content from past retry history. **A later cycle hitting the same class of error (e.g., a
missing `import re`) gets no benefit from a previous cycle having already diagnosed and fixed that exact
mistake.** This is a real, working repair mechanism with zero memory beyond the single attempt it repairs
— textbook retry logic, not learning, exactly the distinction the mission's own Task 3 draws.

## 7. RiverBrain Re-Analysis (re-confirmed, not re-derived from scratch)

Per this pass's brief, treated as established: `score_model()` reads a real, continuously-updated rolling
mean (`model_task_stats`) written by `.learn()`; selection genuinely changes as this mean moves — L3,
mechanically. The proxy it closes on (`_score_response_quality()`'s AST-heuristic score) is independently
established (`[inherited: Findings-91-93 forensic pass]`) to correlate only weakly (r=0.206, n=24, not
significant) with real functional correctness. **No new evidence this pass changes this** — not
re-investigated in depth per the brief, since two independent passes already nailed it down.

## 8. Shadow-Model Re-Analysis (re-confirmed)

Also treated as established per this pass's brief: 331/2062 = 16.1% real accuracy, independently
re-derived twice already tonight, exact match both times. Remains the system's one clean L2 example — a
real measurement, a real demotion, no evidence this pass contradicts either. **Not investigated further
in this pass** — the mission's own priority was hunting new ground, and this candidate has already
received two independent, agreeing passes.

## 9. Council Feedback Analysis

Per this pass's brief, the structural incapability finding (§ from Michelangelo III, independently
re-confirmed by the parent session's own algebra) is treated as established. **Not re-investigated for
new positive cases in this pass** given the time budget was spent on genuinely unexplored candidates
(§3) per the mission's own explicit priority — flagged as a real gap in this pass's own coverage, not
a claim that no positive case exists there.

## 10. `seam_engine` Analysis

Per this pass's brief (754 total / 78 novel / 2 garden / 1 asked, `[inherited]`, independently confirmed
twice already tonight): **not re-investigated further in this pass.** No new evidence either direction.

## 11. Generalization Analysis

- Self-edit retry: **G0** — confirmed directly (§6), no persistent lesson store exists.
- Self-edit convergence tracker: **G0**, moot — the mechanism intended to enable a form of policy-level
  adjustment (§7's "L1 at best") doesn't reliably activate in the first place (§ — see the dedicated
  finding above).
- `crash_awareness.py`: **G1 at best, unverified** — avoidance, when it engages, applies to *all* future
  MLX-model selections uniformly (not scoped to a specific candidate), which is a form of local
  generalization by construction — but whether it *reduces the crash rate*, the actual outcome that would
  make this matter, was not established either way (§8) because disengagement never checks.
- Curiosity-topic-bias: **genuinely unresolved** — would require tracking a topic's own surprise value
  across the specific cycles before and after a bias event, a targeted historical query not completed in
  this pass's time budget. Flagged as a real, cheap, next investigation (§21), not answered here.

## 12. False-Learning / Confound Red-Team

Applied primarily to the convergence-tracker finding (§7), since it's this pass's own new claim and
deserves the same scrutiny demanded of any positive result: could the `non_convergent_streak: 0` reading
be a *display* artifact (e.g., a recent reset) rather than a genuine, longstanding measurement failure?
Checked directly: `cycles_attempted: 95` and `58` respectively for the two families, both far exceeding
any known reset event (the last documented full self-edit reset was 2026-07-21, and both families'
`cycles_attempted` counters — confirmed cumulative, not reset, by direct code read of
`backfill_convergence_from_log()`'s replay logic — comfortably exceed what a reset that recent could
produce alone). The finding survives this specific attack. A second angle: is `count <= prev.count OR
prev.count==0` perhaps rarely true in practice, meaning most cycles ARE flagged non-convergent, and this
pair is a fluke? Not checked exhaustively for every family in the remaining budget — flagged as a real
limitation (§20), not glossed over.

## 13. Quantitative System-Wide Results

Precise, honest denominators, not manufactured precision: of the 9 mechanisms in this pass's own
inventory (§3) plus the 4 carried over from Michelangelo III's larger 13-mechanism survey (RiverBrain,
shadow model, seam_engine, council blend) — **13 total considered across both passes** — exactly **1**
reaches L3 (RiverBrain, on a weak proxy), exactly **1** reaches a clean, correctly-terminating L2 (shadow
model), and **11** are L0/L1: real activity, sometimes real downstream consequence, never a demonstrated,
working adaptation loop. **Zero L4 loops found in either pass.** This is consistent with, not a revision
of, Michelangelo III's own count — this pass added new candidates and confirmed the pattern held for all
of them, rather than finding an exception.

## 14. Strongest Demonstrated Closed Loop

Unchanged from Michelangelo III: **RiverBrain's `model_task_stats` path.** Event-level table (per the
required format), reusing the already-independently-confirmed facts rather than re-deriving:

| Stage | Evidence | Source | Confidence |
|---|---|---|---|
| Experience | A real conversational/self-edit response is generated | `river_deliberation.py`/`self_edit_manager.py` call sites | A |
| Detection | `_score_response_quality()` scores it | `echo_quality_scorer.py` | A |
| Interpretation | Score normalized 0-4→0-1, becomes `label` | `echo_model_orchestrator.py:816` | A |
| Decision | `model_task_stats[model][task_type]["mean"]` updated via capped rolling mean | `.learn()`, line ~862 | A |
| Intervention | None yet — this *is* the stored decision-input, not an action | — | A |
| Outcome | Next `rank_models()`/`_select_council()` call reads the updated mean | `score_model()` | A |
| Attribution | Direct: the same variable written is the variable read | Source | A |
| Future behavior | A different/same model gets selected based on the moved mean | `[inherited: demonstrated live, multiple times tonight]` | A |
| Generalization | **G3-shaped by construction** (a policy-level score, not a single-case fix) — but the policy itself optimizes a proxy independently shown weak | `[inherited]` | B (mechanism: A; proxy validity: C) |

## 15. Evidence Hierarchy

- **Tier C** (system correctly detects and terminates a bad mechanism): shadow model. The single
  strongest tier reached anywhere in this investigation across all four Michelangelo passes.
- **Tier D** (retry succeeds, no policy change): self-edit's in-call retry (§6).
- **Tier E** (signal computed/persisted, doesn't affect consequential behavior): council ratings absent
  a resolvable disagreement, `learn_from_sandbox_outcome`/`learn_from_rating` (`[inherited]`).
- **Tier F** (activity + logging, unknown downstream): `crash_awareness` avoidance's actual effect on
  crash rate, curiosity-topic-bias's actual effect on subsequent surprise, `seam_engine`'s 76 lost
  detections.
- **No mechanism in this or prior passes reaches Tier A or Tier B.** RiverBrain's L3 loop is
  mechanically real but doesn't qualify for Tier B (improvement "not independently established" is
  generous — it's independently shown *weak*, not merely unestablished) — placed here explicitly as its
  own case, between D and E in spirit: more mechanically complete than a Tier D retry, less trustworthy
  than a hypothetical Tier B loop would be.

## 16. "Learning from Experience" vs. "Accumulating Experience"

Applying the mission's own five-way distinction precisely: **FeralEcho robustly does experience
accumulation** (logs everywhere, extensively, reliably) **and feedback processing** (real scores, real
classifiers, real rolling means computed from that experience). It **partially** does adaptive behavior
— RiverBrain's selection genuinely changes, self-edit's targeting genuinely shifts. It has **exactly one
demonstrated instance** of useful learning in the strict sense (changed behavior producing a better
independently-measured outcome) if you count the shadow model's downgrade as "useful" — though that's an
unusual case: the useful outcome was *stopping* a bad thing, not producing a better one. It has **one
demonstrated instance of self-correction** (same case). It has **zero demonstrated instances** of a
mechanism producing generatively better output through experience, evaluated by a measure independent of
the mechanism's own definition of success.

## 17. Capability-Ceiling Update

**No, the estimate has not moved from Phase 1.5/Michelangelo III's own conclusion, and that itself is
informative.** This pass searched hard, in good faith, specifically for a counterexample to the
"unmeasured intervention" pattern, across four genuinely fresh candidates. It found none, and found one
additional, previously-unverified case (§7) where the pattern is worse than assumed (a mechanism
believed to provide corrective feedback essentially never does, in practice, for the two families that
most needed it). The ceiling is not lower than previously assessed — nothing here suggests active harm
beyond what's already known (shadow model, aside) — but it is not higher either, and this pass had a
genuine, serious opportunity to find evidence that would have raised it.

## 18. Highest-Leverage Intervention (not implemented)

**Fix `_record_convergence()`'s identity-blind count check** (§7) to compare the actual *set* of matched
function names between cycles, not their count — the data needed already exists in `all_names_seen`,
requires no new instrumentation, and would make the one mechanism in this codebase that's *structurally
positioned* to enable real within-project generalization (a prompt that changes based on real, accumulated
failure identity, not just failure count) actually work as designed. This is higher leverage than adding
LoRA specifically because LoRA would encode *whatever feedback topology already exists* (per the parent
mission's own Question 10) — and this pass's own new finding is that even the topology's own
already-built self-edit-specific corrective signal is silently inert. Fixing the signal is a prerequisite
to any future mechanism — LoRA included — being trained on data that reflects real accumulated failure
identity rather than a flat, uninformative count.

## 19. What NOT to Do Yet

Wiring `crash_awareness`'s avoidance to any outcome-based re-evaluation, or building a persistent
retry-lesson store for self-edit, before first confirming (cheaply, from existing logs) whether either
would actually change anything given how rarely their trigger conditions currently fire in practice —
building more on top of an unverified trigger risks the same "looks wired, isn't checked" pattern this
whole series exists to catch.

## 20. Unknowns

Whether `count <= prev.count OR prev.count==0`'s false-convergence pattern (§7) holds for every family
or is specific to `prose_stripping`/`response_shortening`'s particular churn shape — not checked
exhaustively. Whether curiosity-topic-bias measurably changes subsequent surprise (§11) — a real,
tractable, unanswered question. Council feedback's and `seam_engine`'s positive-case space — not
re-investigated this pass, per the brief's own priority on fresh ground; Michelangelo III's negative
findings there stand, but this pass did not specifically hunt for a counterexample the way it did for
the four candidates in §3.

## 21. Recommended Next Investigation

Directly test §11's open curiosity-topic-bias question: pull every `emergent_loop.salience` /
`world_model.surprise` event carrying a `detail.topic` field, identify each real historical bias-trigger
event, and compare that topic's own surprise value on its next occurrence against a matched, unbiased
baseline — pure historical-data analysis, zero cost, the exact method this whole series has repeatedly
shown can produce a real, sometimes conclusion-changing result.

## 22. Final Verdict

**FeralEcho accumulates experience extensively and reliably. It adapts based on that experience in a
small number of real, mechanically-verifiable ways. It has one clean, credible instance of experience
producing a correctly-terminated bad decision (the shadow model). It has zero demonstrated instances,
across four independent Michelangelo passes now, of experience producing a generatively better outcome
validated against a measure independent of the mechanism's own success criterion.** This is not a
condemnation — the infrastructure for measurement (logs, timestamps, persisted state) is unusually
thorough for a project this size, which is precisely why these gaps are checkable at zero cost rather
than merely suspected.

---

## Final Required Questions

**1. Strongest historical example of experience → changed future behavior?** RiverBrain's
`model_task_stats` path — mechanically real, demonstrated live multiple times tonight, unchanged from
Michelangelo III.

**2. Strongest evidence the changed behavior improved an independently measured outcome?** None found
that clears the bar. The shadow model's downgrade is the closest — a real, independently-measured
improvement in the narrow sense of "a worse-than-random signal stopped being trusted" — but it's a
subtraction, not a generative improvement.

**3. How many genuine L3/L4 loops exist?** One L3 (RiverBrain, on a weak proxy). Zero L4, across all four
passes tonight.

**4. How many apparent learning loops collapse into "experience accumulation" when followed downstream?**
At least 11 of the 13 mechanisms considered across this pass and Michelangelo III's inventory.

**5. Does FeralEcho currently learn from experience, or primarily accumulate it?** **Primarily
accumulates it**, with one real, narrow, mechanically-adaptive exception (RiverBrain) whose target is
independently shown to be a weak proxy, and one real, narrow, correctly-terminating self-correction
(shadow model).

**6. Strongest evidence for that conclusion?** §13's count: 11 of 13 real, consequential mechanisms
surveyed across two passes tonight terminate at "logged," not "adapted."

**7. Strongest evidence against your own conclusion?** RiverBrain's loop is real, not hypothetical — it
is possible to argue this alone qualifies as "learning" in a minimal, mechanical sense, and this report's
own insistence that the proxy's weakness disqualifies it is itself a judgment call, not a proven fact
(r=0.206 is weak, not zero).

**8. Strongest false-positive candidate for "learning"?** The self-edit convergence tracker (§7) — it
looks, from its own code and comments, exactly like a real adaptive corrective mechanism, and would have
been reported as this pass's strongest new finding if its actual historical state hadn't been checked
directly.

**9. Single architectural intervention most likely to increase the probability that future experience
produces useful behavioral change?** §18's fix — repair the convergence tracker's identity-blind count
check, since it's the one mechanism already structurally positioned to convert real failure identity into
a real prompt change, currently inert for exactly the reason a small, cheap fix could address.

**10. Would adding LoRA before that intervention increase capability, or merely increase the system's
capacity to encode whatever feedback topology already exists?** The latter. This pass's own new finding
(a believed-working corrective signal turning out to be silently inert) is a direct, concrete illustration
of why: training on top of an unverified or broken feedback topology would encode the *appearance* of a
working correction loop into weights, which is harder to inspect and harder to fix than a JSON file.
