# Michelangelo II — The Unmeasured Intervention Audit

Read-only except for the corrected re-analysis below (pure computation against existing files, zero
mutation). No RiverBrain state touched, no production code modified, no money spent, no secrets
exposed. `git status` at time of writing: clean except this new report file (verified below).

---

## 1. Executive Judgment

**The parent session's headline finding survives independent re-derivation, but its precision did not
— and correcting the precision changes the picture in a way worth taking seriously, not dismissing.**

The parent defined `apply_to_code`'s "active window" as the *outer bound* between the first and last
LOAD_AUDIT event mentioning it (2026-07-14 to 2026-08-26) and compared self-edit outcomes inside vs.
outside that 43-day span. Re-derived independently here using the *actual deployment timeline* (198
real LOAD_AUDIT events, tracking exactly which file was deployed at each moment, not just whether the
outer span contains an apply_to_code mention): **the outer-bound method silently included 19 real
outcomes that occurred during gaps where a *different*, non-apply_to_code file was actually deployed**
— gaps of up to 10.2 days appear inside the nominal "active" window. Precise, moment-by-moment
re-analysis: **true active-deployment outcomes are n=12 (not 31), mean quality delta −0.0232 (not
+0.0915 — the sign flips), 50% negative (not 42%); true inactive is n=91 (not 72), mean +0.1200.**
Welch's t: p=0.4249 — still not statistically significant, at an even smaller, less reliable n. **The
correct classification is not "C — no detectable effect," which is what the coarser analysis supported.
It is closer to G — insufficient evidence, now pointing numerically toward possible mild harm rather
than neutrality, on a sample too small (n=12) to confirm anything.** The parent's central *thesis*
(nobody had ever checked this) is untouched and, if anything, strengthened — the corrected number is
more concerning, not less.

The deeper pattern the parent named — real, running mechanisms whose downstream effect on the thing
they're supposed to improve is never checked — **is not confined to self-edit.** It recurs, at varying
severity, across nearly every subsystem surveyed in this pass (§2). The single most important addition
this pass makes to that thesis: **most of these mechanisms aren't merely unmeasured — the infrastructure
to measure them already exists** (real historical logs, sitting unread) **in every case checked.** This
is not a data problem. It is a habit problem, exactly as the parent concluded, now with broader evidence.

---

## 2. Intervention Inventory

| Mechanism | Evidence of Liveness | What It Changes | Native Success Criterion | Downstream Outcome Measured? | Evaluation Quality | Classification |
|---|---|---|---|---|---|---|
| `apply_to_code` self-edit hook | 198 real LOAD_AUDIT events over 2 months; 19 with the hook defined; 3,196 real invocations, 62% "changed" | The generated code of every subsequent self-edit candidate | Did the hook run without raising, did it change the string | Yes — in this pass, for the first time, with the correct precise window | **E → corrected here** — original evaluation window was imprecise; corrected version is directionally worse, still underpowered | **G** (was miscategorized as C by the imprecise version) |
| RiverBrain `model_task_stats` (AST-scored coding path) | Live, continuous, every real coding response `[inherited]` | Which model gets selected for coding/self-edit tasks | Structural AST-complexity score ≥ threshold | Yes — Findings-91-93 forensic pass found weak correlation (r=0.206, n=24, not significant) with real functional correctness `[inherited]` | E — the metric being optimized was independently shown not to track what it's a proxy for | **D/E** |
| `learn_from_sandbox_outcome()` / `learn_from_rating()` | Live — real sandbox pass/fail and real human ratings are computed continuously `[inherited]` | Nothing — confirmed by direct source read (`[inherited]`, Phase 1.5 §4): neither writes `model_task_stats`, the only signal selection reads | N/A — never reaches a decision | No — cannot be measured downstream because there is no downstream | N/A | **F** |
| Council peer rating → `learn_from_council_rating()` | **Live and healthy** — cursor exact-matches log length, `[inherited]` | `model_task_stats` for conversational tasks, blended 30/70 with the auto-scorer | Council-vs-quality-score agreement | Partially — this pass found a real case (`council_rating=5, quality_score=1`) where the two signals disagree sharply; whether the *blend* correctly resolves disagreements like this in a way that improves anything downstream was not checked, here or previously | **G** — the blend formula's own real-world calibration has never been checked against outcomes | **D** |
| Shadow model (`shadow_self_model.json`) | Live, 2,062 real accuracy-tracked entries | Self-edit targeting, as a last-resort fallback only (post-Finding-91) | Match a real-world "actual" label | Yes, repeatedly (`[inherited]`) — 13-16% accuracy, worse than the real 58.8% majority-class floor | **B — demonstrated harmful** (would actively mislead if trusted, which is exactly why it was demoted) — the rare case of a mechanism that *was* rigorously measured and found bad, then correctly downgraded | **B** |
| `echo_projects` generation | Live, real F1/F2 gates, real advisory council review `[inherited]` | Writes real, multi-file candidate projects to disk | Import-safety only — no quality/functional gate exists at all `[inherited: Michelangelo I]` | No — no mechanism exists to check whether generated projects are ever reopened, used, or judged after generation | N/A — nothing to evaluate | **F, more precisely than "F" alone captures — see §8** |
| Dissent Log (`propose_core_edit()`'s council review) | **Real but almost never exercised** — confirmed this pass: `memory/dissent_log.jsonl` contains exactly **1 entry, ever** | Nothing currently, by design (Finding 9's own explicit non-wiring) | Council consensus/split on a proposed protected-file edit | N/A — a sample of 1 cannot be evaluated | N/A | **F** (correctly, deliberately inert — but "almost never invoked" is itself worth knowing plainly) |
| `seam_engine.py` | Live, runs every emergent-loop cycle `[inherited: CLAUDE.md Finding 75]` — 83 real seams detected as of that finding | Plants a curiosity-garden question on a genuinely novel signal contradiction | Statistical discrimination test (adversarially verified, `[inherited]`) | **No** — 83 real detections exist, and nothing was found in this pass (or any prior one) checking whether the *planted questions* ever led anywhere different from an ordinary curiosity-garden entry | G | **D** |
| `claude_research.py` | Live, 1 real paid call/hour, real captured questions `[inherited: 27-day liveness map]` | Injects a real answer into the curiosity garden | Did the API call succeed | No evaluation found of whether these injected answers changed anything downstream differently from an ordinary autonomously-generated reflection | G | **D** |
| `crash_awareness.py` MLX avoidance | Live `[inherited]` — engages/disengages on real crash clusters | Temporarily excludes MLX models from the pool | Did it correctly discriminate a real cluster (adversarially verified) | Yes, for the *mechanism's own correctness* — but never for whether avoidance periods actually reduce real crash *rate* afterward, only whether the trigger logic itself is sound | Partial — mechanism validated, outcome not | **D** |
| Valence (`echo_state.py` dim[8]) → `emergent_scheduler` prompt weighting | Live `[inherited: Finding 57/80]` | Nudges autonomous prompt selection and self-edit trial bounds | N/A — a bounded modulator, not a pass/fail mechanism | Finding 57's own lag-1 autocorrelation check (r=-0.145, n=103, not significant) already found no self-predictive momentum in the underlying signal *before* it was wired to affect anything | E-adjacent — the signal was wired to influence behavior *after* a null self-predictiveness result was already known, and re-flagged, `[inherited]`, as an accepted, disclosed risk | **D** |
| `functional_quality.py` | Built, adversarially validated `[inherited: Phase 1/1A]` | Nothing — zero live callers, confirmed repeatedly | N/A | N/A | N/A | **F** |
| Council rating trust gate (`council_baseline_trusted_since`) | Set for real `[inherited: Finding 3/66]` | Unlocks `learn_from_council_rating()`'s actual write path | Agreement rate ≥70% between council and human spot-checks | Yes, at the point of *setting the gate* — never re-checked since for whether trust, once granted, continues to be warranted as new ratings accumulate | G — a one-time check, not an ongoing one | **D** |

---

## 3. Strongest New Findings (not repeats of prior tonight's work)

1. **The corrected `apply_to_code` re-analysis (§1)** — the parent's own headline finding needed, and
   got, real correction: smaller true sample, flipped sign, still inconclusive but now genuinely
   concerning rather than neutral.
2. **The Dissent Log has fired exactly once, ever** — a real, working, adversarially-verified mechanism
   (per this project's own Finding 9) that has had essentially zero opportunity to demonstrate anything,
   good or bad, because nobody uses `!propose`. Not a defect — a genuinely idle capability, worth knowing
   plainly rather than assuming "built and verified" implies "in active use."
3. **`seam_engine`'s 83 real detections have never been checked for whether the questions they plant
   lead anywhere different from an ordinary curiosity-garden entry** — a real, substantial number of real
   events (unlike the Dissent Log's n=1), genuinely unevaluated downstream, discovered by asking the
   mission's own question ("did anyone check what happened after") of a mechanism nobody had previously
   flagged tonight.
4. **A real council-rating disagreement case was found in this pass** (`council_rating=5,
   quality_score=1` on a real personal-task response) — direct, concrete evidence that the blend formula
   Finding 67 built is regularly asked to resolve real, sharp disagreements, and nothing has ever checked
   whether its resolution (30/70 weighting) actually produces better outcomes than either signal alone.

---

## 4. Historical Interventions (ran substantially, effect never adequately measured)

Ranked by real event count, largest first: `learn()`'s AST-scored pathway (hundreds of thousands of
real observations, `[inherited]`), `apply_to_code` (3,196 invocations, §1), `seam_engine` (83 real
detections), shadow model (2,062 entries — the one exception, since it *was* measured and found bad,
§2), council ratings (137+ entries, `[inherited]`), `claude_research.py` (dozens of real hourly calls
over weeks). The common shape: event counts range from dozens to thousands; adequate downstream
evaluation exists for exactly one of these six (the shadow model), and only because a separate,
dedicated investigation happened to go looking for it.

---

## 5. Measured vs. Unmeasured (quantified where honestly possible)

Of the 13 mechanisms in §2's inventory: **1 has a demonstrated harmful effect with valid evaluation**
(shadow model, B). **0 have a demonstrated beneficial effect with valid evaluation.** **1 has a
corrected, still-inconclusive evaluation** (`apply_to_code`, re-classified G in this pass). **3 are
genuinely dormant/disconnected by design or by disuse** (`functional_quality.py`, dissent log,
`learn_from_sandbox_outcome`/`learn_from_rating`). **The remaining 8 are operational, consequential, and
have no adequate downstream-outcome evaluation (D or G)** — the majority of the inventory. **Do not read
more precision into these counts than they carry**: this inventory is not exhaustive (§9's own honest
limitation), and several D/G classifications rest on "no evaluation was found," not "no evaluation could
possibly exist" — a stronger search might surface one this pass missed.

---

## 6. Closed-Loop Analysis

Applying the mission's own three-tier diagram to each row in §2: **exactly one mechanism reaches the
third, genuinely-closed tier** (`intervention → measured → validated → future behavior changes → new
outcome measured`) — RiverBrain's `model_task_stats` path, and even that closes on a proxy metric
independently shown weakly correlated with the real thing it's supposed to track (§2's own note). **One
mechanism reaches the second tier and stops there deliberately** — the shadow model (measured, validated
as bad, downgraded — the loop closed, correctly, in the "reject" direction). **Every other mechanism in
the inventory terminates at "intervention → (logged) → STOP."** This is the same finding the parent
reached for one subsystem, now confirmed as the dominant pattern across the ones surveyed here, not an
isolated case.

---

## 7. Reassessment of `apply_to_code`

**Established** (Grade A, directly reproduced): 198 real LOAD_AUDIT events span 2026-07-01 to
2026-09-03; 19 mention `apply_to_code`; 3,196 real invocations exist in `apply_to_code_invocations.jsonl`,
62% recorded `changed=True`. The precise, moment-by-moment deployment state (not the outer bound) yields
12 real self-edit outcomes that occurred while the hook was genuinely deployed, vs. 91 while it wasn't.

**Suggested, not established** (Grade C): the corrected mean delta (−0.0232 active vs. +0.1200 inactive)
points toward the hook coinciding with worse outcomes — but n=12 is too small to support this as a real
effect (p=0.4249; a single outlier trial could move this mean substantially). This is the honest,
correctly-hedged upgrade from the original "no detectable difference" framing — not "the hook causes
harm," but "the null-effect conclusion no longer holds at the precision this data actually supports, and
the point estimate now leans the other direction."

**Remains unknown**: whether the *content* of what `apply_to_code` did during those 12 windows (which
family, what specific transformation) matters more than its mere presence — not broken out by family in
either this pass or the parent's, a real, stated limitation for both.

---

## 8. Echo Projects

**Not merely a local defect — a clean instance of the broader pattern, and possibly the starkest one in
this inventory.** Self-edit's AST-only gate is *flawed* but *present*; `echo_projects` has none at all.
Where self-edit's problem is "the wrong thing gets measured," `echo_projects`'s problem is "nothing gets
measured, ever, at any point after generation" — no fitness comparison, no re-opening of generated
projects to check if they're ever used, no tracking of which curiosity-garden questions produced projects
anyone found worth keeping. It sits at the far end of the same spectrum every other row in §2 occupies,
not in a separate category.

---

## 9. Blind Spots

What this pass found that no prior investigation tonight (including the parent's own Michelangelo I)
surfaced: **the imprecision in the parent's own active-window definition (§1/§7)** — a genuine, real
correction to work produced in this same session, hours earlier, found specifically by taking the
mission's explicit instruction to "reproduce the analysis independently" literally rather than treating
it as a formality. **The Dissent Log's n=1 real-world usage** — nowhere in CLAUDE.md's extensive Finding
9/history is this stated as plainly as "it has fired exactly once." **This inventory itself is
incomplete** — genuinely broad candidates named in the mission (autonomous loops' interactions with each
other, night_cycle's janitor/retention effectiveness beyond its own liveness checks, Echo↔Air messaging's
real downstream consumption) were not individually investigated to the same depth as the rows above, due
to real time constraints in this pass — flagged honestly rather than papered over with a thin entry.

---

## 10. Highest-Leverage Opportunity

**Re-run §1's corrected analysis methodology — precise deployment-state reconstruction, not outer-bound
windows — against every other row in §2 classified D, using only data that already exists on disk.**
This is not a new recommendation; it is the direct, disciplined continuation of what this very pass just
did once and found genuinely informative. It costs nothing, risks nothing, and — per §1 — has already
been shown to change a real conclusion, not just confirm one. Doing it for `seam_engine`'s 83 real
detections and council rating's real disagreement cases specifically (§3) is the next two cheapest,
highest-value instances.

---

## 11. What NOT To Do

Building new evaluation infrastructure before finishing the free, existing-data sweep this section
argues for. Wiring `functional_quality.py` into production (already gated behind Tier 1 fixes per
tonight's earlier work) before that sweep is done — the shadow model (§2) is the cautionary example of
what a *real* evaluation looks like when it's actually performed; more mechanisms should get that
treatment before any of them get more trust. Pursuing LoRA — unchanged from the parent's own earlier,
separate assessment tonight, and this pass's own finding (most consequential mechanisms are D/G, not
proven beneficial) makes the case *weaker*, not stronger, since LoRA would need trustworthy training
signal this inventory shows the project mostly doesn't yet have.

---

## 12. Confidence and Unknowns

High confidence (Grade A): §1's corrected `apply_to_code` numbers, the Dissent Log's n=1 count, the
overall §5 counts as bounded by this pass's specific, named inventory. Low confidence / genuinely
unresolved: whether §2's D-classified mechanisms would show real effects if properly measured (this pass
establishes *that* they're unmeasured, not what the answer would be); whether this 13-mechanism
inventory is complete (§9 already disclaims this).

---

## Final Challenge

**Q1 — How much of FeralEcho's "learning" is demonstrated improvement vs. activity that looks like
learning?** Almost none of it is demonstrated improvement. Of 13 real, consequential mechanisms surveyed,
exactly one (RiverBrain's `model_task_stats`) reaches a genuinely closed loop, and even that closes on a
metric independently shown to weakly track the real thing it should. Most of what looks like learning is
activity: real, logged, often substantial — but not shown to improve anything.

**Q2 — How many consequential mechanisms have ever been evaluated by asking whether they improved the
thing they were supposed to improve?** By this pass's own count: one, cleanly (the shadow model) — and
it failed that evaluation and was correctly downgraded. `apply_to_code` was evaluated for the first time
tonight, imprecisely at first, then corrected in this pass. Everything else in §2: zero.

**Q3 — Strongest evidence FeralEcho is improving itself?** The shadow model's own downgrade. A real
mechanism was measured, found wanting, and demoted — not a case of self-improvement in the generative
sense, but a genuine, closed, correctly-terminating evaluation loop, which is rarer and arguably more
valuable evidence of self-correcting capacity than any generative claim this inventory could support.

**Q4 — Strongest evidence it is merely changing itself?** `apply_to_code`'s corrected numbers (§1/§7): a
real mechanism ran, changed real code 1,985 times, and the best current evidence — properly derived —
neither confirms benefit nor rules out mild harm. Change, unambiguously. Improvement, unestablished.

**Q5 — One architectural improvement, $0, existing hardware?** Not a new mechanism. **A standing,
recurring practice — run §10's precise-window, existing-data correlation method against every D-classified
row in this inventory, starting with `seam_engine` and council rating, before building anything else.**
It is the one thing this pass demonstrated, twice tonight now (§1, and the parent's own §6a before it),
to reliably produce real, sometimes conclusion-changing evidence at zero cost.

**Did following this pattern change your view of what FeralEcho actually needs?** Yes, specifically: I
expected, going in, that re-deriving the parent's number would mostly confirm it. It didn't — it got more
precise and more concerning at the same time, on a smaller, more honest sample. That's the whole thesis
of both Michelangelo passes, demonstrated on itself: the first, coarser answer looked adequate until
someone actually checked the mechanism producing it.
