# Missing Primitive Determination — Temporal Authority Drift

Design-determination mission, building on and independently re-verifying `audits/2026-09-07_temporal_authority_graph.md`. No implementation performed or proposed as code; this is a determination of what is missing.

## Executive Answer

**One missing primitive, not two, not none.** The two cases in the Temporal Authority Graph are surface variations of the identical underlying gap — this investigation also found a **third, independently git-provable instance** of the same shape, which was not counted in the prior report and which strengthens the "one primitive" conclusion considerably. FeralEcho is missing a **consumer-audit discipline**: a rule requiring that whenever a new producer, category, or task-type is introduced, every existing generic consumer whose domain is a fixed or enumerable set (a dispatch table, a dedup filter, a category-weighted selector, an allowlist) must be explicitly checked against the new producer before that producer is considered done. This is not a new mechanism to build from scratch — it is a one-sentence extension of a discipline this project already has and already follows for a narrower case (the Liveness Ledger's "new capability needs its own check" rule).

## Same Gap or Different Gaps? — Resolved with Evidence, Not Assumed

Tested the hypothesis directly: is `TASK_TYPE_MAP`'s failure ("two copies of an enumerable set silently diverge") mechanically different from `seam_engine`'s failure ("a producer-agnostic filter has no way to know a new producer type now flows through it")?

They are surface-different but root-identical. Re-read both mechanisms directly:

- `TASK_TYPE_MAP` (`echo_model_orchestrator.py:717`, `echo_quality_scorer.py:495`): the failure is not really "duplication" as a category of bug — it's that a **fixed, enumerable domain** (the set of task types) was extended in one place without anyone checking every place that domain is consumed.
- `_is_near_duplicate()` (`garden_manager.py:125-155`): the failure is that a **fixed, implicit domain assumption** ("all garden entries are the same kind of thing, differing only in wording") was violated by a new producer (`seam_engine`) whose entries carry different semantics (`category="seam"`, `source="seam_engine"`), and nobody checked this consumer against that assumption when the new producer was built.

Both are the same shape: *a generic mechanism operates correctly over the domain it knew about at write time; a later producer silently expands that domain; nothing forces a check.* The difference between "two copies of a dict" and "one function that's blind to a new field" is implementation detail, not root cause. **Confidence: High** — confirmed by finding a third case (below) that fits the same shape but looks like neither of the first two mechanically.

## A Third Instance Found — Not Previously Counted

Searched for further examples using the same technique (fixed/enumerable domains predating later producers) and found a real, already-*fixed* case, documented in CLAUDE.md's own Finding 22 Batch 5 and still visible in the current source's own explanatory comment:

- **`garden_manager.py`'s `CATEGORIES` list** (`garden_manager.py:15-24`, present since the initial commit `44e7a8e`, 2026-06-28) is a fixed 8-value enum (`narrative`, `moral`, `identity`, `faith`, `nature`, `relationship`, `loss`, `general`).
- `_category_weights()` originally pre-populated its scoring dict *only* from this fixed list. Two later producers — `autonomous_awareness.py`'s dream cycle (harvesting `category="dream"`) and `curiosity_engine.py` (harvesting under `ai_tech`, `world_politics`, and other topic-derived categories) — introduced values never in `CATEGORIES`, causing a real, live `KeyError` every time either producer's output reached this function.
- Both were fixed in the **same commit as the seam-filter's own creation**, `3e24186` (2026-07-12) — the exact commit that also introduces `_is_near_duplicate()`, the mechanism that four days later would silently start losing seam attribution. **One commit, in the same sitting, both closed one instance of this exact pattern and opened a new one.**
- The fix applied to `CATEGORIES` is the closest existing precedent for the correct general primitive: stop pre-declaring a fixed domain and instead build the working domain dynamically from what the data actually contains (`scores.setdefault(category, [])` instead of iterating a hardcoded list), paired with the caller's pre-existing defensive `.get(category, 0.5)` read. This is real, in-repo evidence that the project's own engineers already know the correct *local* fix — what's missing is the discipline that would have applied it to `_is_near_duplicate()` and `TASK_TYPE_MAP`'s copy too, at the moment those risks were created.

This raises the pattern count from 2 to **3 independently git-verified instances**, one of which (`CATEGORIES`) was caught and fixed, one of which (`TASK_TYPE_MAP`) was caught, fixed, and then recurred a second time under a different key, and one of which (`seam_engine`) remains live and unfixed as of `HEAD`.

## Candidate Primitive Evaluation

| Candidate | Closes `seam_engine`? | Closes `TASK_TYPE_MAP`? | Closes `CATEGORIES`? | Complexity/Cost |
|---|---|---|---|---|
| **A. Single-source-of-truth / canonical registry** (ban local copies of any dispatch dict) | **No** — `_is_near_duplicate()` is not a duplicated table, it's a producer-blind filter; SSOT has nothing to say about it | **Yes**, directly — one `TASK_TYPE_MAP`, imported everywhere, no second copy possible | **Partially** — `CATEGORIES` was never duplicated; SSOT doesn't address the "fixed domain vs. dynamically-arriving values" failure shape at all | Low, but narrow — solves 1 of 3 real cases |
| **B. Consumer-audit discipline** (extend the Liveness Ledger's existing "new capability needs its own check" rule to also require: *audit every existing fixed/enumerable-domain consumer before calling a new producer done*) | **Yes** — the discipline would have required checking `harvest_question()`'s consumers (including `_is_near_duplicate()`) before `seam_engine` shipped | **Yes** — the discipline would have required checking every other reader of a `TASK_TYPE_MAP`-shaped dict before `self_edit_coding` (or `echo_projects_coding`) was considered done | **Yes** — the discipline would have required checking `_category_weights()` before the dream cycle or `curiosity_engine` shipped their own category vocabularies | Very low — a rule-text change plus, optionally, a lightweight repo convention (see below); no new subsystem |
| **C. Provenance-carrying data contract** (every value flowing through a generic mechanism carries an explicit producer/type tag; generic mechanisms declare an allowlist of validated producer types) | **Yes**, directly | **Partially** — would prevent the *silent-default* failure mode specifically (an unrecognized `task_type` would be rejected rather than reclassified as `general`), but doesn't prevent the *forgetting-to-update-a-second-copy* failure mode on its own | **Partially**, same reasoning | Medium-High — requires touching every generic consumer's calling convention, a real structural change, not a rule change |

**B is strictly sufficient where A is not, and strictly cheaper than C.** A closes only the case that happens to be shaped like a duplicated dictionary; it says nothing about the two cases shaped like a domain-blind function. C would work but is heavier than necessary — it retrofits a structural contract onto every generic mechanism in the codebase to solve a problem that a one-sentence process discipline already prevents, per the direct evidence that this project's own engineers already knew the correct local fix (`CATEGORIES`) the moment they were looking for it — they just weren't required to look at the right moment for the other two cases.

## Recommended Smallest Primitive

**Not a new architectural mechanism. A single-sentence extension of the Liveness Ledger's existing discipline**, from CLAUDE.md's own current text:

> "any new autonomous capability... does not get to be called done without its own check added here in the same change"

to:

> "...and does not get to be called done until every existing generic consumer that operates on a fixed or enumerable domain (dispatch tables, dedup/similarity filters, category-weighted selectors, allowlists/denylists) and will now process this producer's output has been explicitly checked against it in the same change."

This is deliberately **not** a new tool, subsystem, registry, or runtime check — it is a discipline addition, matching every other gap this project has closed tonight and throughout its history (report → propose → pause → human decides, not "build a new organ"). The three real cases found tonight (`seam_engine`, `TASK_TYPE_MAP`, `CATEGORIES`) are exactly the shape this sentence would have caught, and the `CATEGORIES` case is direct proof the project's own engineers already reach for the right local fix once the question gets asked — the gap is that the question currently only gets asked for the *new* thing's own behavior, never for the *old* things the new thing now silently passes through.

A lightweight, optional structural aid that would make the discipline cheap to actually follow (not proposed as required, just noted as a plausible pairing): a repo convention of marking any dispatch table, dedup filter, or category-weighted selector with a short, greppable comment tag (something like `# FIXED-DOMAIN CONSUMER` or similar) so a future session adding a producer can `grep` for every place that needs checking, rather than relying on memory or a full-codebase re-read each time. This is exactly the kind of "cheap, purely-observational, non-authoritative" aid this session's own attempt ledger and Liveness Ledger checks already model — not a new category of tool.

## Why Not the Ambitious Version

The mission asked for the *smallest* primitive; the temptation is a general "producer registration system" that every new producer must formally declare itself to, with automated matching against every consumer. Rejected here, explicitly, because:
1. No evidence in three real cases shows automated matching would have caught anything a human checklist item wouldn't — all three failures were checkable by direct code inspection at the moment the new producer was written, not something requiring new tooling to detect.
2. This project's own established culture (visible across the entire night's investigation and CLAUDE.md's decades — sorry, months — of Findings) consistently prefers a narrow, targeted discipline extension over new infrastructure, and has been burned before by exactly the opposite instinct (WOLF, the original over-ambitious "learning stomach" hypothesis this whole session has been testing and repeatedly finding doesn't hold up against evidence).
3. A heavier mechanism (C above) would itself become a new thing requiring its own Liveness Ledger check, its own maintenance burden, and its own possible future drift — the recursive version of the exact problem being solved.

## If This Were Ever Authorized (Not Implemented Here)

Stated precisely enough to be actionable later, without writing code:

1. One text edit to CLAUDE.md's Liveness Ledger section, adding the sentence above to the existing "Extending this" discipline paragraph.
2. A one-time forensic pass (a natural follow-up mission, not proposed as part of this determination) to grep the current codebase for every existing fixed/enumerable-domain consumer (dispatch tables, dedup filters, category-weighted selectors, allowlists/denylists) not already covered by the three cases found tonight, to establish the current baseline before the new discipline takes effect going forward — otherwise the rule only prevents *future* drift and leaves any *other* currently-live instances (beyond the three found here) undiscovered.
3. Optionally, the greppable-comment-tag convention described above, applied to the handful of currently-known fixed-domain consumers (`_is_near_duplicate()`, both `TASK_TYPE_MAP` copies, `_category_weights()`) as a worked example for future sessions to follow.
4. Separately, and only if independently judged worth the cost: fixing the two currently-live drift cases themselves (`seam_engine`'s 76 lost detections, and adding real test coverage for `TASK_TYPE_MAP` parity) — explicitly out of scope for this determination mission, which was asked only to determine what is missing, not to fix what was found.

## Safety Verification

- `run.py`/watchdog: confirmed not running before and after (`ps aux`).
- Git HEAD: `c5bf2e5f8913e35a1ded9af8afe68e247651e26d` — unchanged; zero commits, zero amends made by this mission.
- `river_brain.pkl` sha256: `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` — unchanged; RiverBrain was never imported or called.
- No production source modified. No self-edit run. Only this report file created.
