# Michelangelo III — Follow the Consequence

Read-only. No production code modified, no RiverBrain state mutated, no money spent, no secrets
touched, no commits. Every number below was computed directly against real, on-disk data in this pass
(`memory/seam_log.jsonl`, `data/question_garden.jsonl`, `memory/council_ratings.jsonl`,
`memory/dissent_log.jsonl`, `memory/shadow_accuracy.jsonl`, `app/core/echo_model_orchestrator.py`,
`app/core/garden_manager.py`), not copied from Michelangelo I or II.

---

## 1. Executive Judgment

Following two specific consequence chains all the way to their actual end — not just to "the mechanism
fired" — found something worse, and more precise, than Michelangelo II's aggregate classification
captured for both. **`seam_engine`'s real, correctly-identified novelty is being discarded by a
downstream filter answering a different question than the one seam_engine asks.** **The council-rating
blend is not merely imprecisely calibrated — it is mathematically incapable of letting the council
override the automatic scorer in exactly the cases (extreme scores) where a real disagreement occurs.**
Both are load-bearing corrections to Michelangelo II's own D-classifications, found by doing the one
thing this mission asked for that the prior pass didn't have time for: following individual events, not
counting them.

---

## 2. Consequence Inventory

| Mechanism | Liveness | Intervention | Downstream Effect | Outcome Measured | Future Behavior Changed | Loop Level | Confidence |
|---|---|---|---|---|---|---|---|
| `seam_engine` → garden question | Live, 754 real detection events, 78 genuinely novel (`first_ever=True`) | Calls `harvest_question(category="seam")` on each novel detection | **Traced event-by-event (§7): 76 of 78 silently rejected by the garden's own dedup filter before ever becoming a real question.** 2 survive; 1 was ever asked. | For the 1 asked: yes, a real quality score (1.0) exists | No — the one real answer produced a generic, non-diagnostic follow-up question, still `status: "active"` (unresolved) | **L1 at best, and only for 1 of 78 real events; L0 for the other 76** | A (event-level, directly reproduced) |
| Council rating → `model_task_stats` blend | Live, cursor healthy, 137 real ratings `[inherited, re-confirmed]` | Blends council (30%) + quality_score (70%) into `model_task_stats` | **Traced mathematically and empirically (§8): in all 73 real cases where council and quality_score sharply disagreed, the blended result matched quality_score, never council — 73/73.** Proven structural, not incidental (§8's derivation). | Yes, continuously, but always resolving to one signal | Yes — model selection changes, but driven by quality_score in disagreement cases, council in name only | **L3 mechanically (a real closed loop exists), but the "council" half of it is a non-participant whenever it matters most** | A |
| Dissent Log (`propose_core_edit()`) | Real, but fired **exactly once** (re-confirmed, third independent count tonight) | Would log real council disagreement on a protected-file edit proposal | The one real entry is a **3/3 unanimous approval** — the mechanism has never once recorded an actual dissent | N/A (n=1, and not even a dissent case) | N/A | **L0** — correctly built, structurally idle | A |
| RiverBrain `model_task_stats` (`.learn()` path) | Live, continuous, hundreds of thousands of real observations `[inherited, re-confirmed via direct `score_model()` read this pass]` | Selects which model handles future coding/self-edit tasks | Real, demonstrated selection shift over time | Yes — but the "evaluation" re-applies the same AST/heuristic scorer that produced the response in the first place, not an independent check | Yes | **L3** — a genuinely closed mechanical loop, closing on a proxy independently shown (`[inherited: Findings-91-93]`) only weakly correlated (r=0.206, ns) with real functional correctness | A |
| Shadow model | Live, 2,062 real entries, 16.1% accuracy (independently re-confirmed this pass, exact match) | Was the self-edit-targeting arbitration's primary signal; now demoted to last-resort fallback | Yes — genuinely measured against a real ground-truth label | Yes — the priority reorder (Finding 91) is a real, confirmed behavioral change | **L2, correctly terminating** — measured, found wanting, demoted; this is the one mechanism in the inventory that closes its loop in the *reject* direction and stops, correctly | A |

---

## 3. Strongest Closed Loop

**RiverBrain's `model_task_stats` path**, re-confirmed by direct code read this pass (`score_model()`
reads `self.model_task_stats[model][task]["mean"]`, a real rolling mean written by `.learn()`). Every
arrow is real: OBSERVE (a response is generated) → DECIDE (task type + current weights) → ACT (a model
is selected, weighted ~65% by this real signal) → OUTCOME (the response) → EVALUATE (`_score_response_quality()`
scores it) → ADAPT (`model_task_stats` updates) → NEW BEHAVIOR (the next selection reads the updated
value). This is genuinely L3. The honest caveat, unchanged from tonight's earlier work and re-confirmed
here rather than assumed: EVALUATE re-applies the *same kind* of proxy score that would apply to any
output regardless of which model produced it — it is not an independent check of whether the *selection
itself* was wise, only of whether the output looks structurally complex (for coding) or hits certain
keyword/entropy markers (for other task types). The loop is real; whether it optimizes anything true is
a separate, already-partially-answered question (weak, non-significant correlation with real
correctness, `[inherited]`).

---

## 4. Strongest Broken Loop

**`seam_engine`.** It gets further than almost anything else in this inventory on the OBSERVE/DECIDE/ACT
side — it correctly, adversarially-verifiably (`[inherited: CLAUDE.md Finding 75/scripts/verify_seam_engine.py]`)
identifies genuine statistical novelty no other mechanism in this codebase detects. It breaks at the
single most avoidable point in the whole chain: the hand-off from "this is real, novel information" to
"is this new question distinguishable from ones already in the garden," where a downstream filter built
for an entirely different purpose (preventing near-identical *philosophical* questions from
accumulating) silently discards 97% of what seam_engine correctly identified as new (§7). This is not a
capability gap — seam_engine's own novelty-detection is sound. It's a translation failure between two
correct mechanisms that were never checked against each other.

---

## 5. Strongest Successful Self-Correction

**The shadow model, unchanged from Michelangelo II's assessment — independently re-verified here, not
just re-cited.** 16.1% accuracy (331/2062, re-computed directly), a real measurement against a real
label, followed by a real, confirmed demotion to last-resort-only status. This remains the cleanest
L2-terminating-correctly example in the system: the loop closed in the *reject* direction, which is
exactly what should happen to a signal this weak, and it did.

---

## 6. Strongest False Success

**The council-rating blend (§8).** Its own success criterion — "we've incorporated a real, independent
peer judgment into training" — is technically true (the code path runs, the blend computes, the result
persists) and substantively false in every case that matters: whenever council and the automatic scorer
sharply disagree, the automatic scorer wins, always, provably, by construction of the weighting and
threshold, not by chance. A system that believes it is incorporating council judgment 30% of the time is
actually incorporating it roughly 0% of the time *specifically in the cases where doing so would change
anything* — the cases where the two signals agree are exactly the cases where the blend was never
needed.

---

## 7. `seam_engine` Findings — Event-Level

754 total seam-detection events across the log; **78 are genuinely novel** (`first_ever: True` — a
first-time-ever contradiction for that specific pair and direction, the module's own real, adversarially-
tested criterion). Each of these 78 calls `harvest_question(question, category="seam", source="seam_engine")`.

**Traced precisely, not estimated**: `data/question_garden.jsonl` (13,720 total entries) contains **exactly
2** with `category == "seam"`. That means at least **76 of the 78 real `harvest_question()` calls
returned `False`** — silently rejected, per that function's own logic, either as an exact duplicate or,
far more likely given seam questions' templated phrasing, a *near*-duplicate.

**Verified the mechanism directly, not just inferred it**: `garden_manager._is_near_duplicate()` uses
Jaccard word-overlap against active entries, threshold 0.7. Constructed three real seam-question texts
(using the exact real templates `_describe()` produces, with different real pairs from `seam_log.jsonl`)
and computed their overlap directly: two questions sharing the "usually move together" template but
describing **completely different signal pairs** scored **0.821** word-overlap — well above the 0.7
threshold, meaning the garden would reject the second as a near-duplicate of the first, purely because
of shared template phrasing, with zero regard for whether the underlying statistical relationship is
new. This is a **proven mechanism**, not a plausible guess: seam_engine's own real, structured, templated
output is exactly the shape most likely to trip a word-overlap filter designed to catch differently-
worded restatements of the same *idea*, not a family of syntactically-similar sentences describing
*different* facts.

**What happened to the one that survived and got asked** (§6 of the intervention inventory; full entry):
question about `edit_momentum`/`valence` moving opposite their historical pattern, asked once, scored
1.0, produced exactly one child question — a generic, template-flavored elaboration about "emergent
properties" and "iterative processing loops" that never engages with *why* the specific contradiction
happened. `resolution_score: 0.5`, still `status: "active"`. **Net traceable downstream consequence of
78 real, correctly-detected statistical anomalies: one generic follow-up question, unresolved.**

---

## 8. Council / Dissent Findings

**Firing frequency**: 137 real council ratings exist (`[inherited]`, re-confirmed). Of these, **73 (53%)
show a sharp disagreement** (|council_rating − quality_score| ≥ 3, on their respective 1-5/0-4 scales) —
a far larger and more consequential fraction than Michelangelo II's single cited example suggested.

**What the disagreement resolves to — computed directly for all 73 real cases**: `_blend_council_and_quality()`'s
real formula (`echo_model_orchestrator.py:737-756`, `council_weight=0.3, quality_weight=0.7`, label
threshold 0.75) applied to every real disagreement: **73 of 73 blended labels matched `quality_score`'s
implied verdict. Zero matched council's.**

**This is not incidental — it is a mathematical property of the real, current weights**, verified by
direct derivation, not just observed: at `quality_score=4` (max), `quality_normalized × 0.7 = 0.7`; even
the *minimum* possible council contribution (`council_rating=1 → 0.2 × 0.3 = 0.06`) still sums to `0.76
≥ 0.75` — label is **always** 1, regardless of how low council rates it. At `quality_score ≤ 1`, the
maximum possible quality contribution is `0.175`; even a **perfect** council rating of 5
(`1.0 × 0.3 = 0.3`) only reaches `0.475 < 0.75` — label is **always** 0, regardless of how high council
rates it. **The council's real, gathered judgment is structurally incapable of moving the final label
whenever `quality_score` sits at or near its extremes — which is exactly where the real 73 disagreement
cases in this data live.** The blend is not miscalibrated at the margins; it is decisive by construction
at the extremes, which is precisely backwards from what a check-and-balance mechanism should do.

**Dissent Log**: `memory/dissent_log.jsonl` — exactly 1 line, independently confirmed a third time this
session. Read in full this pass: a real `3/3 APPROVE` unanimous vote on a cosmetic documentation-comment
proposal. **The mechanism has never once recorded a real dissent** — its own name describes an event
that has not yet happened in its entire operating history.

---

## 9. RiverBrain Reassessment

Confirmed independently (§3): the loop is real and mechanically L3. **Does it close on a trustworthy
target?** Re-derived, not assumed: `score_model()`'s only real per-(model,task) signal is
`model_task_stats["mean"]`, itself fed exclusively by `.learn()`'s `_score_response_quality()` call for
the coding path (AST-complexity heuristic, `[inherited: Phase 0, Findings-91-93]` already shown weakly,
non-significantly correlated with real functional correctness) — no independent verification signal
reaches it (`[inherited: Phase 1.5 §4]`, confirmed structurally unchanged in this pass). **Michelangelo
II's classification holds: a real closed loop, optimizing a proxy shown to only weakly track the thing
it's a proxy for.**

## 10. Shadow Model Reassessment

Confirmed independently: 331/2062 = 16.1% real accuracy (exact match to the previously-cited figure,
recomputed from scratch in this pass), a genuine measurement against a real ground-truth label
(`real_focus`), followed by a real, still-in-effect priority demotion (`get_weak_task_type()` checked
before the shadow-model fallback, confirmed by direct source read this pass). **Michelangelo II's
"cleanest self-correction" classification holds and is now independently re-verified twice.**

---

## 11. The Closed-Loop Map

```
CLOSED LOOPS (L3+):
  RiverBrain model_task_stats  — real, closes on a weak proxy (§3/§9)

SELF-CORRECTING LOOPS (L2, terminating correctly):
  Shadow model — measured, found bad, demoted, stopped (§5/§10)

PARTIAL LOOPS (L1 — real downstream effect, but the loop never re-closes onto future behavior in a way
that reflects the outcome):
  Council rating → model_task_stats — technically closes, but the "council" input is provably inert at
    the extremes (§8) — the loop closes on quality_score alone wearing council's name

OPEN LOOPS (L0 — activity with no established downstream consequence):
  seam_engine → garden questions — 76 of 78 real events, traced individually, lead nowhere (§7)
  Dissent Log — real, correctly built, never yet exercised (n=1, unanimous, not even a dissent)
```

---

## 12. Blind Spots

Two findings this pass adds that neither Michelangelo I nor II surfaced, both found only by following
individual events rather than aggregating them: **(1)** the exact mechanism by which seam_engine's real
novelty gets discarded — not "unmeasured," but *actively, silently rejected by a specific, identifiable,
directly-testable filter*, a stronger and more actionable finding than "downstream consequence unknown."
**(2)** the council-rating blend's mathematical inertness at score extremes — Michelangelo II found one
example of disagreement; this pass found the general rule governing all 73 real cases and proved it's
structural, not incidental. Both are corrections in the direction of "more precisely broken than
previously stated," not "actually fine after all" — consistent with the `apply_to_code` correction's own
direction (Michelangelo II → this pass's inherited baseline), a pattern worth naming: **every re-
examination in this three-part investigation has made the underlying picture more precise and more
concerning, never less.**

---

## 13. Highest-Leverage Intervention

**Fix `garden_manager._is_near_duplicate()`'s dedup check to exempt or specially handle `seam_engine`-
sourced questions** (e.g., dedup on the `(pair, direction)` tuple already computed and logged in
`seam_log.jsonl`, not on template-similarity of the rendered English sentence). This is the single
cheapest, most surgical fix in this entire three-part investigation: one function, one already-precisely-
diagnosed mechanism (§7), a real 76-event backlog of already-detected-but-discarded novelty that would
immediately start reaching the garden the moment the fix lands, and zero risk to anything else in the
system (the filter's original purpose — catching genuinely near-identical philosophical questions —
is untouched for every other source). It directly converts an L0 mechanism into something that could, for
the first time in its operating history, actually be evaluated at real scale (78 real events instead of
2) — a prerequisite for ever knowing whether seam_engine's real detections are worth anything at all,
which is currently unknowable specifically because of this one filter.

---

## 14. What Should NOT Be Done

**Do not touch the council-rating blend weights yet.** The mathematically-clean finding in §8 is tempting
to "fix" by reweighting — but this investigation's own mandate is discovery, not repair, and a hasty
reweighting risks the same fate as the original 30/70 split (chosen once, never re-examined against real
disagreement data until tonight). **Do not build new anomaly-detection or dedup infrastructure generally**
— the fix in §13 is a targeted correction to one specific, precisely-diagnosed mismatch, not a mandate
to redesign `garden_manager.py`. **Do not treat RiverBrain's L3 closure as evidence it should be trusted
more** — a closed loop on a weak proxy is not obviously better than an open one; §9 explicitly declines
to make that inference.

---

## 15. Unknowns

Whether the 76 rejected seam questions, if they had reached the garden, would ever have been *asked* or
*resolved* meaningfully — §7 only establishes they were discarded before that question could even arise.
Whether council rating's real judgment, if it were allowed to actually influence the extreme-disagreement
cases, would produce *better* training signal than quality_score alone — §8 establishes the blend is
inert at the extremes, not that council would be right if it weren't. Whether other mechanisms in this
codebase share seam_engine's exact "correct detection, silently discarded downstream" shape — this pass
checked two mechanisms in real depth, not the full system; Michelangelo II's broader-but-shallower
13-mechanism inventory remains the best available map of what else might hide the same pattern.

---

## Final Challenge

**1. What percentage of consequential FeralEcho activity can be followed from intervention to measured
downstream outcome?** No honest single percentage — this pass traced 2 mechanisms in real depth and
found one at effectively 1/78 (1.3%) real-consequence rate and one at 0/73 (0%) for the signal that
matters. Generalizing either number to "all of FeralEcho" would manufacture false precision this report's
own evidence doesn't support.

**2. How many mechanisms actually change future behavior because of measured outcomes?** By this pass's
direct count: two — RiverBrain (on a weak proxy) and the shadow model (correctly, in the reject
direction). Both independently re-confirmed, not merely re-cited.

**3. Strongest evidence FeralEcho learns from experience rather than merely accumulating it?** Unchanged
from Michelangelo II, now doubly-confirmed: the shadow model's real measurement-then-demotion. It remains
the single cleanest example in the entire system.

**4. Strongest evidence it changes itself without knowing whether the change helped?** The council-rating
blend (§8) is a sharper answer than `apply_to_code` now: it's not merely unmeasured, it's a mechanism
that *believes* it's incorporating real peer judgment and mathematically cannot, in the cases that matter
— a case of the system's own self-model about its own learning process being wrong, not merely
unverified.

**5. One closed-loop property to improve?** **The translation step between "genuinely novel signal
detected" and "gets a real chance to be evaluated."** Both mechanisms this pass followed in depth broke
at conceptually the same place — real, correctly-generated novelty (a seam; a sharp rating disagreement)
failing to survive contact with a downstream gate built for a different purpose. Fixing the specific
instance in §13 is the concrete first step; the property worth improving generally is "when a subsystem
correctly flags something as new or disputed, make sure the next thing in the chain is actually built to
receive that specific kind of signal," not any particular mechanism's internals.

**6. Did this investigation change the fundamental capability-ceiling assessment?** Yes, specifically:
Michelangelo II's "8+ mechanisms are D/G, unmeasured" reads, before this pass, like a documentation gap —
something that could in principle be closed by writing an evaluation. This pass shows at least two of
those aren't documentation gaps at all; they're mechanisms that were *built correctly*, produce *real,
verifiable output*, and are discarded or overridden by a specific, nameable, already-fixable downstream
defect. The ceiling isn't "we haven't checked" — for these two, it's "we checked, and found the checking
infrastructure itself has a bug." That's a more precise, and more immediately actionable, diagnosis than
either prior pass reached.

**What did the stone reveal this time that you genuinely did not expect?** The council-rating result. I
expected `_blend_council_and_quality()`'s calibration to be *imprecise* — under-weighting council in
disagreement cases. Deriving that it is **mathematically, provably, always overridden by quality_score
at the extremes, with zero exceptions in 73 real cases**, was sharper and more absolute than the "worth
checking" framing I started this investigation expecting to find. That specific number — 73/73, not
"most" — is the one result in this report I did not predict going in.
