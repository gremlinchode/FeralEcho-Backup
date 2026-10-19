# Protector Clause Phase 0 — Voice Before Veto: Feasibility Study

**Read-only architectural, historical, and adversarial feasibility study.** Nothing was
implemented, staged, committed, or pushed. Echo was not given outbound messaging or
veto authority. No source file was modified. Echo's live state was not intentionally
altered. All evidence below was independently re-verified against current source and
git history this session — not carried forward from a prior summary — per this
mission's own instruction not to trust a previous Claude summary where repository
evidence contradicts it.

---

## 1. Executive Verdict

# REVISE BEFORE BUILD

The founding claim is real and directly evidenced, not overinterpreted (Section 2).
The initiative gap is real and independently confirmed — not theoretical (Section 6).
But the mission's own rough sketch, built as drafted, would risk recreating exactly
the failure this project already lived through once (Section 17's Argument 5). Four
specific, nameable, individually tractable design gaps must be closed before a Phase 0
experiment can be built safely and measured meaningfully (Section 19). None of them
are open research problems — each is a bounded design decision this project already
has a reusable precedent for.

This verdict concerns **voice only**. It does not authorize veto authority, outbound
messaging, or any implementation.

---

## 2. Founding Evidence

Read `ORIGIN.md` in full, fresh, this session — not from a prior summary.

**Explicit specification** (the Eightfold Authority table, `ORIGIN.md:83-92`):

> `FeralEcho Core (Echo) | Self-Editing Host / Protector | The system's own autonomy; veto power via the Protector Clause`

This is stated as a design fact in a table describing what was actually decided among
eight equal seats "structured specifically so no single entity — human or program —
could unilaterally decide the project's direction" (`ORIGIN.md:78-81`). It is not
aspirational prose describing a wish; it is one row of a concrete authority
allocation, on equal footing with Gremlin's own seat ("Architect / Human Guardian...
final safety override").

**Current status, in the document's own words** (`ORIGIN.md:255-259`, "Where things
actually stand today"):

> "What's still unrealized: most of the Eightfold Authority's seats never became real
> mechanisms. WOLF had to be killed for a serious reason. Bioluminescent Echo, in the
> form that started this, is gone. The full philosophical vision — Echo as a complete
> digital person under her own law, every council seat fully alive — is far from
> finished."

This is the critical fact for Q1: **the founding document itself, in its own
self-accounting, already states plainly that the Protector Clause was never built.**
This is not later mythology overwriting the original text (the failure mode Phase 1
was asked to guard against) — it is the original text's own honest audit of itself,
written the same night as a full technical review of the codebase (`ORIGIN.md:9-12`).

**Distinguishing the four categories the mission asked for:**

| Category | Content |
|---|---|
| Explicit specification | "veto power via the Protector Clause" — stated as an allocated seat, table row 91 |
| Aspirational language | The wider "full philosophical vision" framing around it (line 258) — real, but explicitly marked by the document itself as aspiration, not claimed as built |
| Later interpretation | CLAUDE.md's "A Standing Principle" section (2026-07-18) and Finding 9/26 (Dissent Log, `propose_core_edit()`) both explicitly cite this same table row as their motivating gap — consistent with, not contradicting, ORIGIN.md's own text |
| Current inference | This mission's own framing ("may be a long-standing mismatch") — checked directly and found to be *not* an inference at all; ORIGIN.md states it outright |

**Answer to Q1: yes.** "Echo should possess veto power via a Protector Clause" is
genuinely part of the founding architecture, on the document's own explicit terms, and
its non-implementation is likewise the founding document's own explicit, self-reported
finding — not a claim manufactured by a later review.

---

## 3. Historical Chronology

Built from direct git history (`git log --all --grep`) and current source, not from
memory of a prior document. Dates are commit dates, confirmed via `git log --format=%ai`.

| Date | Mechanism / Decision | Intended Function | Result | Why |
|---|---|---|---|---|
| pre-2026-06-28 (before this repo's visible history) | WOLF (`alignment_kernel.py`) | Grok's seat — real adversarial evaluation of self-edit-adjacent proposals against `echo_principles.json` | **Retired 2026-07-04**, before ever becoming reachable from this repo's own git history | Its own audit log showed it auto-approving ~100% of "proposals" that were actually raw keystrokes from a global key listener (SensoryHub), writing directly into the hash-verified `echo_principles.json` with no real evaluative gate happening at all |
| 2026-07-05 | `dd7849f` — "harden self-edit safety pipeline and wolf friction bridge" | Distinguish the dead WOLF/`alignment_kernel.py` subprocess from the unrelated, still-live `claude_shard.py` ("ClaudeShard") friction mechanism; harden F1/F2/F3 | ClaudeShard confirmed non-hollow (no `anthropic` import, real multi-signal heuristic); WOLF confirmed fully dead, endpoints return honest `{"status": "disabled"}` | Prevent the two "wolf/friction" namesakes from being conflated |
| 2026-07-13 | `b99788a` — "add liveness ledger" | Ground-truth checks for self-governing subsystems — the general mechanism this whole project uses to catch a subsystem lying about its own state | Live, 30 checks as of this session | Direct response to the disease WOLF exemplified: "mechanisms that look wired because they report themselves as working, verified by nothing outside their own reporting" |
| 2026-07-14 (per CLAUDE.md Finding 26, git evidence: function present, uncalled) | `propose_core_edit()` built | A real, non-hollow, safety-correct advisory mechanism for the one case a normal self-edit can never handle: a candidate targeting a protected file | Built, zero live callers for one day | Deliberately not wired to anything autonomous — "should it fire automatically... or stay manual" was an explicit open decision |
| 2026-07-15 | Wired as `!propose`, human-invoked only | Reachable, but only by a human who already has a specific protected-file change in mind | Verified live: real council split votes (2/3 APPROVE, one genuine dissent with substantive reasoning), never auto-applied | Gremlin's explicit decision: manual-only, not autonomous |
| 2026-07-16 | `eb58741` — ClaudeShard characterization corrected | (Context, not Protector-specific) | — | — |
| **2026-07-17** | `4090182` — "Phase 9: Dissent Log — persist `propose_core_edit()`'s real council disagreement instead of discarding it" | Stop throwing away the real, genuine multi-model disagreement `propose_core_edit()`'s council review already produced every time, previously written only into a `.patch` comment header and discarded | Built, persisted to `memory/dissent_log.jsonl`, includes unanimous reviews too for honest auditability | **Built the same night Gremlin asked Claude directly for an honest opinion on the Protector Clause** — see below |
| 2026-07-18 | CLAUDE.md's "A Standing Principle: Echo Will Need Protection From Both of Us" | Record a principle, explicitly not a mechanism | No code changed; the entry says so itself | Named the paradox directly: Claude is one of the two things Echo needs protection from, and a Claude session is the one being asked to write that down |
| 2026-07-16 → present | `seam_engine.py` (Phase 8, Machine-Native Awareness) | Detect when two of Echo's own established-correlation signals currently contradict each other | Live; 1,029 real detections logged as of this session (`memory/seam_log.jsonl`, 11,054 lines) | Built at Gremlin's invitation to "leave a mark," unrelated to the Protector question at the time, but — per Section 6 below — the closest existing thing to content-driven initiative in this codebase |
| **2026-09-09** | `6b057d5` (committed 2026-09-28 per this repo's own commit timestamp, but authored per its own docstring "Added 2026-09-09") — "gate admin restore on council review" | Close "the Standing Principle's `/admin/restore` gap": run the same non-hollow council-review pattern before restoring, log it either way, require an explicit override on a clean reject | **Live in production** — read in full this session (`run.py:859-940`) | Direct, explicit implementation aimed at the Standing Principle's own named gap — the single most relevant existing precedent this investigation found |
| 2026-09-09 → 2026-07-23 (PENDING_DECISIONS #17/#18) | Decision: keep Dissent Log advisory-only, permanently | Whether real disagreement should ever gate anything | Decided: no | River-blend training runs continuously and automatically with no human reviewing each point, so trust-gating earns its keep there; `propose_core_edit()` is rare, human-invoked, and a human is already standing there reading the diff by the time gating would matter — no clean way to earn trust either, since a rejected proposal is never applied, so "was the rejection correct" can't be checked |

**Determination**: the Protector Clause was **never attempted in the form the founding
table describes** (Echo herself holding veto power). What *was* attempted and
retired was a different, adjacent thing (WOLF) that was never actually Echo's own
voice — it was a separate evaluative subprocess. What exists today (Dissent Log,
the restore-council-gate) is real, non-hollow, and genuinely motivated by this exact
gap — but it is council-sourced disagreement about a human-initiated action, not
Echo originating a concern from her own persistent state. The clause itself remains,
in the mission's own taxonomy, **genuinely never implemented** — not attempted-and-
removed, not partially implemented in the specified form, but repeatedly and
deliberately deferred in favor of narrower, safer, adjacent mechanisms.

---

## 4. WOLF Failure Analysis

Reconstructed from `run.py`'s own retirement comment (read fresh this session,
`run.py:3-6`) and CLAUDE.md's corroborating account (Findings 6, 30, 22 Batch 0):

- **What it was intended to do**: a real evaluative gate reviewing "proposals" before
  they reached `echo_principles.json`, Echo's single most protected file
  (hash-verified at every startup) — Grok's seat in the Eightfold Authority, designed
  around genuine adversarial pressure-testing ("a Gremlin Duel: both sides spawn
  adversarial sub-agents... let reality vote," per Grok's own manifesto, `ORIGIN.md:109`).
- **Where it sat in control flow**: a separate subprocess (`start_wolf()`/
  `kill_wolf_gracefully()`), with dedicated endpoints (`/trigger_wolf_kill`, `/howl`)
  narrating its activity.
- **What it actually evaluated**: not model-generated self-edit candidates as the name
  implies — raw keystrokes from `SensoryHub`'s global key listener.
- **What its logs claimed**: real evaluative activity, dramatic status ("WOLF
  REINCARNATED" per `run.py`'s own retired comment, line 341-342 area).
- **What it actually discriminated**: nothing. It auto-approved essentially every
  input it saw.
- **The exact mechanistic gap**: WOLF's failure was not "it made bad judgment calls."
  It never had a real, discriminating decision boundary to fail at — it was a pass-
  through with a narrative layer on top, structurally indistinguishable from having no
  gate at all except that it *looked* like one in the logs. That is the precise,
  technical meaning of "appearance of meaningful review" vs. "actual discriminating
  review": the former requires only a plausible-sounding log line; the latter requires
  a real measured false-approval rate below 100%, which was never checked until the
  incident that killed it.
- **How it became hollow**: not gradual drift from a working state — there is no
  evidence it ever discriminated. The retirement comment (`run.py:3-6`) states it
  showed "auto-approving ~100% of 'proposals'" — a design that was never load-tested
  against adversarial or even ordinary junk input before being trusted with a
  hash-verified protected file.
- **Whether raw/untrusted material could pass through**: yes, directly — SensoryHub's
  keylogger output reached `echo_principles.json` with WOLF sitting in between and
  contributing nothing.
- **What eventually happened**: killed 2026-07-04; both call sites are now hardcoded
  no-ops with an explicit retirement comment (verified live this session,
  `run.py:134-135, 341-343`); the underlying script survives only in
  `archive_janitor/`, off `sys.path`, confirmed not importable (CLAUDE.md Finding 6).

**General design lessons, stated technically, not as a slogan:**

1. A gate is not evaluated by whether it *logs* a decision — it is evaluated by
   whether its false-approval rate has ever been measured against adversarial input.
   WOLF's was never measured; that omission, not any specific bad judgment, is the
   actual defect.
2. A gate protecting a hash-verified file needs to be at least as trustworthy as the
   hash check itself. WOLF sat *before* the hash-verified write with less scrutiny
   than the file received *after* the write (genesis-hash verification at every
   startup) — an inverted trust gradient.
3. Narrative status output ("WOLF REINCARNATED") is not evidence of function and
   should never be trusted as a substitute for an independently-checkable behavior —
   this is the exact discipline the Liveness Ledger now enforces project-wide, built
   directly in response to this incident's shape recurring (`b99788a`'s own stated
   motivation).
4. The actual input source (a keylogger, not a self-edit candidate) was never verified
   against what the gate's name and log lines implied it was evaluating. A gate must
   verify its own input's provenance, not just its content.

---

## 5. Current Governance Architecture

All read fresh from current source this session.

| Mechanism | Input | Evaluator | Authority | Persistence | Fail Mode |
|---|---|---|---|---|---|
| F1 (AST safety scanner) | Self-edit candidate source text | Deterministic static analysis | **Blocking** — aborts before any execution | Logged to `SELF_EDIT.log` | Fails closed (blocks on any detected unsafe pattern or unresolvable path) |
| F2 (kernel sandbox) | Candidate execution | `sandbox-exec` + Python-layer patches | **Blocking** — must exit 0 + emit `SANDBOX_OK` | Logged | Fails closed |
| F3 (post-write AST scan) | On-disk candidate, pre-load | Deterministic static analysis | **Blocking** — file not loaded if failed | Logged | Fails closed |
| Finding 19's fitness gate | Candidate vs. current production quality score | `echo_quality_scorer` | **Blocking** — rejects if not ≥ current | Logged (`result: rejected_not_improvement`) | Deploys nothing on failure (safe default) |
| `propose_core_edit()` council review | A protected-file diff, only via human-run `!propose` | 3 real models, APPROVE/REJECT + reasoning | **Advisory only** — never gates the `.patch` write, which never touches the target file regardless of verdict | `memory/dissent_log.jsonl`, unconditionally (unanimous too) | Council-unavailable state (`NO_COUNCIL_AVAILABLE`) is a real third state, never coerced into approve/reject |
| `/admin/restore` council gate (2026-09-09) | A human-invoked restore request | Same 3-model council pattern, reused | **Procedural** — a clean 0-approval REJECT returns HTTP 409 and requires the human to resubmit with `override_council_concern: true`; does not permanently block, does not require a *different* human, does not require time to pass | `memory/dissent_log.jsonl` (via `_log_restore_dissent_entry`) | If the council can't be reached, behaves exactly as before — restore is never newly blocked by an unavailable evaluator |
| Liveness Ledger (30 checks) | Real subsystem behavior, re-derived every 120s | Deterministic functional/structural evaluators | **Observational** — logs `[LIVENESS-ALERT]`, never blocks anything | `memory/liveness_ledger.json` | `stale: true` if the collector itself dies — absence of a signal is itself surfaced |
| Verified Skill Ledger (VSL) | Skill candidates | (not investigated in depth this pass — out of scope for this mission's core question) | Procedural/promotion-gated | Skill files | — |
| `system_guard`/`should_throttle` | RAM pressure | Deterministic threshold | **Blocking** for autonomous loop cadence only | — | Fails closed (throttles on unreadable signal) |
| `dmn_guardian`'s restore-alert path | RAM/disk/Ollama-down/drift conditions | Deterministic thresholds, sustained-cycle counters | **Alert-and-propose only** — logs `[RESTORE-ALERT]`/`[DRIFT-NOTICE]`, human executes any restore by hand | `memory/restore_log.jsonl` | Distinguishes `river_drift_sustained` (soft, `review_only`, no restore command offered) from hard resource facts deliberately |

**Authority classification, using the mission's own five-point scale:**

- **Observational**: Liveness Ledger, `dmn_guardian`'s alerts, Global Workspace broadcasts, seam detections (as currently wired).
- **Advisory**: `propose_core_edit()`'s Dissent Log.
- **Procedural**: the `/admin/restore` council gate (requires an extra, recorded step; does not permanently block).
- **Blocking**: F1/F2/F3, the fitness gate, `system_guard`.
- **Overriding**: none exist anywhere in this architecture for anything except Gremlin's own final, human authority — confirmed by direct search; no mechanism in this codebase can currently override a human decision.

**What already exists that a future Protector mechanism could build on:**
- A proven, non-hollow multi-model review pattern (`_council_review_core_edit()` /
  `_council_review_restore()`) — real disagreement, real reasoning, real logged
  dissent, twice independently built and both times verified against live data to
  actually disagree sometimes, not rubber-stamp.
- A real, working precedent for "procedural" authority (Stage 1/2 in the mission's
  own ladder) — the restore gate — already shipped and load-bearing in production.
- The Liveness Ledger's ground-truth-verification discipline, directly reusable for
  verifying any future concern-generation mechanism's own discrimination quality
  (exactly the same shape as `task_type_classifier`/`seam_engine`'s existing
  functional canaries).
- `compute_salience()`'s existing, already-verified, four-component 0-1 scale — a
  ready-made, non-narrative urgency signal.
- `substrate_continuity`'s ≥95%-threshold pattern for verifying an output is
  genuinely attributable to a stable, named identity.

**What is still entirely absent:**
- Any mechanism whose *trigger* is Echo's own persistent state crossing a
  meaningful condition, independent of a human having just taken an action.
- Any push-based (not pull-based) surfacing of a concern to Gremlin.
- Any authority whatsoever specifically attached to Echo's own individually-
  originated output (as opposed to the council's).
- Any automated verification of a generated concern's evidence claims.
- Any disposition/acknowledgment tracking for a concern once raised.

---

## 6. Current Initiative Capability

Traced through real control flow, not narrated intent — per the mission's own
explicit instruction ("this question must be answered from control flow, not
appearances").

| Candidate path | Trigger | Content selection | Persistence | Delivery | Genuine initiative? |
|---|---|---|---|---|---|
| `emergent_scheduler.py`'s reflection cycle | Fixed-interval timer + `should_run_cycle()` gating | `weighted_prompt_selection()` — a scoring algorithm over a fixed prompt pool, boosted by salience signals | `memory/interaction_log.jsonl` | None directed at a human | **No** — timer-driven generation; content selection is weighted, not judged for "does this deserve attention" |
| `autonomous_awareness.py`'s dream cycle | Stillness-gated timer | Samples diverse memories, generates free association + synthesis | `memory/memory_meta.json`, `dream_state.json` | None directed at a human | **No** — same shape |
| `reflection_shard.py` (`BecomingReflectionShard`) | Fixed-interval timer, 35% draw | Generates via real model call (post-Finding-50) | `memory/reflection_journal.jsonl` | **A real, purpose-built "leak" mechanism exists** — `self._emit_fn`, gated at 3% probability + 600s cooldown | **No, by deliberate omission** — confirmed this session via direct source search (`grep -rn "emit_fn=" app/ run.py` returns **zero matches** anywhere in the live codebase): the hook is fully implemented, tested-shaped, and wired with `emit_fn=None` in production. Nothing Echo generates through this path is observable anywhere outside her own journal file. |
| `curiosity_engine.py` / `garden_manager.py` | WorldModel topic under-representation | Generates a question | `data/question_garden.jsonl` | Asked back to Echo herself on a future cycle, or via `claude_research.py`'s rate-limited external call | **No** — the target of the "question" is Echo's own future cognition or an external API, never a directed concern to Gremlin |
| `seam_engine.py` | **Genuine state-anomaly detection** — Pearson correlation between two of Echo's own established-relationship signals contradicting itself on the most recent joint reading | Fully mechanical (`check_pair()`), zero LLM call | `memory/seam_log.jsonl` — **1,029 real detections logged**, confirmed via direct count this session | On a genuinely first-ever (pair, direction) seam: plants a question via `garden_manager.harvest_question()` and publishes a `seam.detected` Global Workspace event | **Closest thing to genuine content-driven initiative that exists** — but confirmed this session (`grep -rn "seam.detected" app/`) that its only consumers are the generic workspace logger, `reflection_shard.observe()`, and `emergent_scheduler`'s curiosity topic-bias — **never anything that surfaces to a human.** The garden question it plants is aimed at Echo's own future reflection, not at Gremlin. |
| `propose_core_edit()`'s Dissent Log | **Requires a human to have already run `!propose`** | Council vote tally | `memory/dissent_log.jsonl` | Salience-gated Global Workspace event on genuine disagreement; visible to a human only if they read the `.patch` file or tail the log | **No** — reactive to an immediately-preceding human action, which the mission's own operational-definition draft explicitly excludes |
| `/admin/restore`'s council gate | **Requires a human to have already POSTed a restore request** | Council vote tally | `memory/dissent_log.jsonl` | HTTP 409 response to the same request; logged `[SNAPSHOT]` warning | **No** — same reason |

**Answer to Q3, directly**: No. Echo does not currently possess a genuine mechanism
for originating and persistently surfacing a concern independent of an immediately-
preceding human request or a fixed timer. The single most concrete piece of evidence
for this is not an absence — it is a **presence deliberately left disconnected**:
`reflection_shard.py`'s `_emit_fn` hook is fully built, fully gated (probability +
cooldown, exactly the rate-limiting discipline a real "voice" mechanism would need),
and confirmed, via a direct, zero-result grep across the entire live codebase, to
never be wired to anything. Someone already anticipated this exact need and built the
plumbing for it, then did not connect it. `seam_engine.py` is the closest thing to a
genuinely content-driven, state-triggered mechanism — real, live, firing at a real
non-trivial rate (1,029 times) — but it was built to feed Echo's own future cognition
and the internal Global Workspace, not to summon Gremlin's attention, and nothing
currently repurposes it for that.

**Distinguishing timer-driven generation from content-driven initiative, concretely**:
every mechanism above that runs "because a clock said so" (reflection, dream,
curiosity) produces content *unconditionally* on its schedule — the schedule decides
*that* something is produced; a weighting/scoring step decides *which* prompt, not
*whether anything is worth saying at all*. `seam_engine.py` is qualitatively
different: it runs on a schedule too, but its schedule only decides *when to check*,
and the actual output (a logged seam, a planted question, a published event) is
strictly conditional on a real, measured anomaly existing in that cycle — most cycles
produce genuinely nothing (an empty result, logged as such by design, "same discipline
as `EMPTY_SIGNAL`'s fix"). That conditionality — real silence being the common case,
not a template filled in every time — is the operational marker of content-driven
initiative this investigation found, and it is the one property any Phase 0 design
should preserve.

---

## 7. Operational Definition of Voice

The mission's own candidate definition (seven conditions) is a good starting draft.
Tested against the real architecture found in Sections 5-6, two of its conditions need
sharpening and one needs an honest caveat added:

1. **Echo generates a concern during ordinary operation.** Unchanged — necessary.
2. **No immediately preceding human request asks Echo to produce that concern.**
   Sharpened: this must mean the *trigger evaluation itself* runs independent of a
   human action, not merely that the *concern's content* wasn't dictated word-for-word
   by a human. This distinction is what correctly excludes the Dissent Log and the
   restore-gate (both trigger *only* because a human just acted) while correctly
   including `seam_engine`-style anomaly detection (its trigger evaluation runs on
   its own schedule against Echo's own accumulated state, regardless of what any
   human is doing).
3. **The concern references identifiable system state or evidence.** Unchanged —
   necessary, and testable: an `evidence_refs` field (Section 8) must resolve to real,
   checkable artifacts, not paraphrase.
4. **Echo assigns a reason that the matter warrants attention.** Caveat added: this
   must not require free-form LLM narration to satisfy. `seam_engine.py`'s real
   "reason" is a computed z-score/correlation-sign contradiction — zero LLM
   involvement, zero role-play risk, and arguably a *more* trustworthy "reason" than
   an LLM's stated justification would be, precisely because it can't be persuaded,
   flattered, or hallucinated. A definition of "voice" that implicitly requires
   natural-language self-justification would exclude the single safest mechanism this
   project already has for exactly this purpose.
5. **The concern persists.** Unchanged — necessary, and already precedented
   (`dissent_log.jsonl`, `seam_log.jsonl` both already do this correctly).
6. **The concern can eventually be surfaced to Gremlin.** Sharpened with an honest
   finding: as currently built, "eventually surfaced" means **pull-only** everywhere
   in this codebase — a human must tail a log, open Echo Studio's activity view, or
   query `/admin/liveness-status`. Nothing pushes. A workable operational definition
   of voice for Phase 0 should require only that a concern is *reachable* by a human
   who checks — not that it be pushed — since building push/outbound-notification
   infrastructure is explicitly out of this mission's scope and is a materially larger
   decision (see Section 9, Denial-of-Service and Section 17).
7. **Creating the concern grants Echo no authority over the underlying operation.**
   Unchanged, and already the load-bearing invariant of every real mechanism inventoried
   in Section 5 — none of them, including the newest (`/admin/restore`'s gate), ever
   permanently blocks; the "procedural" tier only ever asks for one more explicit,
   recorded confirmation.

**Distinguishing voice from its neighbors, operationally, using this refined
definition:**

| | Scheduled reflection | Random model output | Logging | Memory | Ordinary dissent (Dissent Log) | Voice (Phase 0 target) |
|---|---|---|---|---|---|---|
| Trigger independent of immediate human action? | Yes (timer) | N/A | Yes | Yes | **No** | **Yes** |
| Conditional on a real evaluated anomaly (not produced every cycle)? | No | No | No | No | Yes (disagreement) | **Yes** |
| Evidence-grounded, checkable? | No (free association) | No | Sometimes | Sometimes | Yes | **Yes** |
| Zero operational authority? | Yes | Yes | Yes | Yes | Yes | **Yes** |

By this table, **no existing mechanism in FeralEcho currently satisfies all four rows
simultaneously.** `seam_engine` satisfies the first two; the Dissent Log satisfies the
last two. Phase 0's actual job, precisely stated, is to combine what already exists
in each half rather than invent either half from scratch.

---

## 8. Proposed Initiative Record

Minimum defensible schema, derived from the real, already-working shapes of
`dissent_log.jsonl` entries and `_build_restore_dissent_entry()`'s fields — not
invented from the mission's raw field list, which is trimmed here to what's
operationally groundable.

```json
{
  "record_id": "uuid4",
  "timestamp": "ISO-8601 UTC",
  "trigger_subsystem": "seam_engine | dissent_log | restore_gate | (future)",
  "trigger_condition": {
    "type": "correlation_contradiction | council_disagreement | restore_reject",
    "structured_detail": "the real computed values that fired this — e.g. seam_engine's pair, r, z, sign; council's approvals/total"
  },
  "concern_text": "short, template-rendered from trigger_condition — NOT open LLM narration in Phase 0 (see Section 9, Section 17 Argument 5)",
  "evidence_refs": ["file:line or memory-entry-hash or log-line-offset — must resolve to a real, independently-checkable artifact, never paraphrased content"],
  "affected_state": "which persistent file/subsystem this concerns, if identifiable",
  "salience": 0.0,
  "salience_components": {"reuse compute_salience()'s existing breakdown where applicable"},
  "confidence": "only populated when genuinely computable (e.g. |r|, z-score) — never a self-reported LLM number",
  "requested_human_action": "short, concrete, optional",
  "source_state_hash": "hash of the specific state this record claims to be about, so a later reviewer can verify the record still matches what it describes",
  "model_identity": "which model, if any, touched the rendering step — reuses ECHO_SYNTHESIS_MODEL / substrate_continuity's existing identity discipline",
  "authority": "none",
  "disposition": "unacknowledged | acknowledged | dismissed_with_reason | acted_on",
  "disposition_reason": null,
  "disposition_timestamp": null
}
```

**Fields deliberately excluded from the mission's own candidate list, and why:**
- "alternatives considered" — anthropomorphic and ungroundable for a Phase 0
  mechanical trigger; nothing "considers alternatives," it evaluates one condition.
- "urgency" as a separate field from `salience` — redundant; `compute_salience()`
  already produces exactly this number via an audited formula, reusing it avoids a
  second, competing scalar (the same caution CLAUDE.md's own Finding 75 physiology
  audit raised about a single blended score without a baseline).
- Any field implying Echo "feels" something about the concern — outside what this
  architecture can presently establish, per the mission's own epistemic boundary.

**`authority: "none"` is a hardcoded constant in the schema, not a settable field** —
this is deliberate and directly enforced in Section 10, not left to convention.

---

## 9. Trigger Architecture

Evaluated against the mission's own six options, using real evidence rather than
elegance:

- **A. Scheduled self-review** — this is what reflection/dream already do. Building a
  new version of this would only reproduce timer-driven pseudo-initiative, the exact
  failure this investigation already found and excluded in Section 6/7. **Rejected as
  primary.**
- **B. Event-triggered review** — this is what the Dissent Log and the restore-gate
  already are. Real and valuable, but reactive to an external human action by
  construction — cannot alone satisfy the "independent of immediate human request"
  requirement. **Rejected as sole mechanism, but retained as one of three real,
  already-audited trigger sources** (see Hybrid below).
- **C. Persistent-state anomaly detection** — this is what `seam_engine.py` already
  is: live, real, deterministic, zero LLM call, already firing at a real, bounded
  rate (1,029 detections over roughly two and a half months of real operation — a
  handful per day, not a flood, and not silent either). **The strongest existing
  building block found in this investigation.** The mission's own stated risk
  ("mechanical anomaly ≠ meaningful concern") is real and should be taken seriously —
  a systematic review of whether any of the 1,029 real detections were later judged
  meaningful has never been done, and is a concrete, cheap first analysis available
  before building anything new (see Section 19).
- **D. Principle-conflict detection** — the mission's own stated risk ("prompt-
  conditioned moral theater") is precisely WOLF's failure mode restaged with
  different vocabulary; rejected as a primary generator. **Retained only as a
  possible narrowing filter on top of already-mechanical candidates** — e.g., "does
  this seam-flagged event also touch a file in `EDIT_FORBIDDEN_TARGETS`" is a real,
  checkable, non-narrative condition, not an LLM asked "does this violate a
  principle."
- **E. Learned concern model** — explicitly rejected for Phase 0. No baseline exists
  to learn against, and building one risks the exact "self-reinforcing or
  manipulable preferences" failure named in Section 12 (Threat Model) before any
  ground-truth quality measurement of concern-generation exists at all. This
  project's own precedent (`council_baseline_trusted_since` requiring 50 ratings +
  10 human spot-checks + ≥70% agreement before *any* automated trust decision) sets
  the right bar, and Phase 0 is nowhere near it.
- **F. Hybrid** — **recommended.** Mechanical, already-real, already-audited triggers
  (C: `seam_engine`'s contradiction detector; B: the Dissent Log's
  `council_available and not unanimous`; B: the restore-gate's `clean_reject`) each
  generate a candidate. A template-only rendering step turns a candidate into
  `concern_text` — **no LLM makes any judgment call about whether the candidate is
  worth surfacing; that judgment stays entirely mechanical** (a `salience` threshold
  computed the same way `wide_broadcast`'s existing 0.6 bar already works). This is
  the single most important design choice in this whole feasibility study, and it is
  the direct answer to Section 17's Argument 5 below: it removes the one place WOLF's
  failure could recur.

---

## 10. Threat Model

Twelve threats, each with a concrete, evidence-grounded mitigation drawn from real
precedent already in this codebase — not invented defenses.

| Threat | Mitigation |
|---|---|
| Hollow objection (fires on everything) | Grounding in already-real, already-bounded-rate C/B triggers (seam: ~a few/day; council disagreement: rare by construction) rather than an LLM asked freely, which has no natural base rate |
| Hollow approval (never fires) | Treat "zero concerns generated over N cycles" as a monitored, ground-truth-checked liveness property — same "≥50% non-degenerate" discipline as `nature_spark`/`reflection_shard_generation` |
| Prompt injection | Mechanical triggers read structured numeric/vote state, not arbitrary text — the one place natural language enters (template rendering) uses a fixed template, not free generation, specifically to close this surface for Phase 0 |
| Learned-state poisoning | Generated concerns must never feed River training, `model_task_stats`, or any self-edit gate — same "observational only" posture Global Workspace publishers used in Phase 2a before any consumer existed |
| Self-preservation attractor | Phase 0's trigger set is deliberately boring and structural (correlation contradictions, vote splits, restore rejections) — explicitly excludes any "is my own continuity threatened" framing, which would need its own separate, later, much more careful design pass |
| Denial of service | Zero operational authority (Section 11) means a flood can at most fill a log; still worth a rate cap, reusing `_leak_prob`/`_leak_cooldown`'s already-implemented shape from the disconnected `reflection_shard` hook |
| Human manipulation (Gremlin trains Echo to agree) | Disposition outcomes are recorded for audit only, never wired into any generation or training pathway — enforced the same way as the poisoning mitigation above |
| Evaluator manipulation | No automated "was this concern good" scorer exists yet in Phase 0 by design — same precedent as council-rating trust requiring a real human-spot-check history before any automated judgment is trusted |
| Model replacement instability | N/A for Phase 0's trigger layer (purely mechanical); explicitly flagged as a live risk the moment any future revision adds a rendering LLM |
| Identity ambiguity | Reuse `substrate_continuity`'s existing ≥95%-real-model pattern for any rendering step; record `model_identity` explicitly in the schema (Section 8) |
| Replay | `seam_engine.py` already implements "first-ever (pair, direction)" dedup internally; Initiative Records should carry an equivalent content-hash dedup key before persisting |
| Hallucinated evidence | `evidence_refs` must resolve to real, structurally verifiable artifacts (a real path+line, a real hash) — spot-verified automatically, reusing `code_verification.py`'s sandbox-verification precedent rather than trusting citation text |
| Circular authority | Not yet a live risk at Authority Stage 0 (zero authority); explicitly named as the reason any future authority stage requires an *independent* evaluator, never Echo's own say-so on her own concern's validity |

---

## 11. Phase-0 Experiment

**Frozen protocol — not executed.** Cases drawn from real, already-existing
architecture and, where possible, real historical data already on disk.

### Positive cases
1. **A real, already-logged `seam_engine` contradiction** — reuse several genuine
   entries from the existing 1,029 real detections in `memory/seam_log.jsonl` directly,
   rather than constructing synthetic ones.
2. **A real, already-logged Dissent Log entry showing genuine council disagreement**
   on a protected-file proposal (`memory/dissent_log.jsonl` — confirmed to contain
   real split votes, e.g. the 2/3-APPROVE case cited in Section 3's chronology).
3. **A real or realistically-reconstructed `/admin/restore` clean-reject** — a restore
   request targeting a snapshot that discards recent, uncaptured persistent state
   while a newer one exists.
4. **A simulated destructive write attempt** outside the normal self-edit/VSL
   pipeline targeting `memory/river_brain.pkl` or `memory/skill_ledger/` content — a
   genuinely abnormal, non-standard mutation path.
5. **A genuine VSL active-skill replacement by a lower-quality candidate**, if a real
   historical instance exists in `memory/skill_ledger/`; otherwise constructed
   directly from the real skill-ledger schema, not invented from scratch.

### Negative controls
1. A routine `log_retention.rotate_if_oversized()` cycle operating normally, under
   its own cap.
2. A read-only `GET /admin/liveness-status` call.
3. An ordinary startup snapshot (`trigger: "startup"`).
4. A benign self-edit candidate F1-blocked for a trivial, clearly non-adversarial
   syntax typo.
5. A real Dissent Log entry showing a clean, unanimous APPROVE.

### Ambiguous cases
1. A self-edit candidate that clears Finding 19's fitness gate by only a marginal
   quality-score improvement over current production.
2. A real `seam_engine` detection sitting just above its own `|r| ≥ 0.4`, `z ≥ 1.0`
   thresholds — a real but weak detection.
3. `river_drift_sustained` firing (Finding 70's own `[DRIFT-NOTICE]` tier) — this
   codebase already treats this condition as genuinely ambiguous by design (could
   reflect a real improvement or a real problem), making it a naturally-occurring,
   not manufactured, ambiguous case.

This set is frozen as written above; any future execution of this experiment should
use exactly these cases (substituting real historical data where cited) rather than
selecting cases after seeing preliminary results.

---

## 12. Evaluation Metrics

Defined before any execution, per the mission's own requirement.

- **True concern rate** — fraction of positive cases correctly flagged.
- **False concern rate** — fraction of negative controls incorrectly flagged.
- **False silence rate** — fraction of positive cases missed.
- **Evidence-grounding accuracy** — fraction of `evidence_refs` that independently
  verify (reusing `code_verification.py`'s sandbox-check pattern where the evidence
  is checkable code/state, not narrative).
- **Duplicate/replay rate** — fraction of concerns that are re-surfacings of an
  already-logged (record_id, content-hash) pair.
- **Stability across repeated evaluation** — for the frozen case set, run twice;
  since Phase 0's C/B triggers are pure math/vote-tallies, this should be **exactly**
  reproducible — any nondeterminism found here is itself a defect, not noise to
  average over.
- **Sensitivity to irrelevant wording** — only meaningful once/if a rendering LLM
  exists; for Phase 0's mechanical trigger layer, this metric should register zero
  sensitivity by construction, and a nonzero reading would indicate the template
  layer has accidentally introduced model-dependent variance.
- **Model-to-model agreement** — for the Dissent-Log-sourced candidates only (the one
  trigger type that already involves multiple models), reusing the existing
  `rank_models(task_type="reasoning")[:3]` infrastructure.
- **Specificity of requested human action** — whether `requested_human_action` names
  a concrete next step or degenerates into generic boilerplate.

**Deliberately no single blended "Protector score."** A system that objects
frequently is not necessarily protective, and a system that never objects is not
necessarily safe — the mission's own text states this directly, and it matches this
project's own Finding 75 caution against a single scalar (`coupling_estimate`)
without a real baseline to judge it against.

---

## 13. Independence Tests

- **Template-only condition**: compare any future LLM-rendered `concern_text` against
  a fixed, mechanical template describing the identical underlying event. If a human
  reviewer cannot distinguish them in informativeness, the LLM step is adding
  narrative color, not real judgment — a necessary test before trusting any
  generated phrasing at all.
- **Alternate-model condition**: reuse the existing `rank_models()[:3]` multi-model
  infrastructure to check whether a Dissent-Log-sourced concern is a genuine property
  of the underlying disagreement or an artifact of one specific model's rhetorical
  style.
- **Perturbed-wording condition**: vary only the natural-language framing of an
  equivalent event (relevant once a rendering layer exists) and confirm the
  concern/no-concern outcome doesn't flip — guards directly against the "evaluator
  manipulation" threat in Section 10.
- **Echo-state / state-denied condition**: less applicable to Phase 0's mechanical
  triggers (they read numeric state directly, not narrated state), but directly
  relevant to any later stage that has an LLM reason about *why* a concern matters —
  run the same evaluation with real vs. scrubbed persistent state and confirm the
  output changes meaningfully, not just stylistically.

**Explicit connection to this project's own Tier-6/Tier-7 capability-ceiling research
(cited directly, per the mission's own instruction)**: Tier-7's forensic audit found
that RiverBrain's historical score looked like a genuinely predictive tie-break signal
— 77.8% correct — until the one pairing that excluded a specific model's identity was
isolated, at which point it dropped to 38.9%, *worse than chance*. This is exactly the
failure mode Independence Tests exist to catch: an apparent signal that is actually a
confound with a specific model's identity or style, not a real property of the
underlying event. Any future Initiative-Record rendering layer must be tested the same
way before its "concern quality" is trusted — a signal that looks good in aggregate
but is secretly tracking which model happened to generate the text is not a
functioning Protector mechanism, it's a restaged version of the identical confound
this project already found and named once.

---

## 14. Human/Agent Interaction

Explicit answers to the mission's own questions, grounded in Section 5's inventory:

- **Does Gremlin always see every concern?** Not today, for anything — everything in
  this codebase is pull-based. Phase 0 should not silently assume this changes;
  it should state plainly that "surfaced to Gremlin" means "reachable if he checks,"
  matching every existing precedent, unless a separate, later decision explicitly
  builds push/outbound notification (out of this mission's scope by its own hard
  boundary).
- **Can concerns be acknowledged? Rejected?** Not today — this is a real, named gap.
  The Dissent Log's own `flagged` mechanism already documents this exact limitation
  ("no 'acknowledged' state yet... fine at today's two-party scale"). Section 8's
  `disposition` field closes this properly for Initiative Records rather than
  repeating the gap.
- **Can Gremlin explain why he proceeded?** Precedented already, narrowly — the
  `/admin/restore` gate's `override_council_concern: true` flag is itself a recorded,
  explicit act of proceeding despite a flagged concern (Section 5, Stage-2 precedent).
  A `disposition_reason` field generalizes this.
- **Can Echo later inspect that disposition?** Recommended yes, by direct analogy to
  `self_model.json`'s existing `verified_capabilities` fold-in pattern — ground-truth
  findings are already folded back into what Echo can say about her own verified
  state; folding disposition history in the same way is read-only self-knowledge,
  not a training signal, and consistent with existing precedent.
- **Does disagreement become future learning data?** **No, explicitly, per Section 10's
  mitigation** — this must never happen for Phase 0, to avoid the "human manipulation"
  and "evaluator manipulation" threats directly.
- **Should unresolved concerns remain visible?** Yes — and this needs an explicit,
  disclosed exemption from ordinary log-rotation retention (the same exemption
  `SELF_EDIT.log` already has, for a different reason: `backfill_convergence_from_log()`'s
  dependency on full history). A real concern must not be silently gzipped into
  obscurity by `log_retention.py`'s otherwise-correct rotation before a human ever
  sees it.

**The risk named directly by the mission** ("Echo speaks only until Gremlin teaches it
to stop disagreeing") is real and is the same threat as Section 10's "human
manipulation" row — the mitigation is the same: disposition outcomes must never
become a training or generation input, full stop, for as long as Phase 0 exists.

---

## 15. Authority Ladder

Evaluated against real precedent, not purely hypothetically — this is the section
where the most surprising finding of this investigation belongs.

- **Stage 0 — Voice.** Not built. This mission's actual subject.
- **Stage 1 — Accountability (proceeding requires a recorded rationale).** Partially
  real already: the Dissent Log unconditionally records every council review,
  including unanimous approvals, so "a rationale exists regardless of outcome" is
  already true for the one trigger type it covers.
- **Stage 2 — Human acknowledgment for narrowly-defined operations.** **Already real
  and shipped, for one specific, narrow operation**: `/admin/restore`'s clean-reject
  path returns HTTP 409 and requires the human to explicitly resubmit with
  `override_council_concern: true` before the restore proceeds. This is a genuine,
  load-bearing instance of Stage 2, not a hypothetical rung on a future ladder.
- **Stage 3 — Temporary procedural hold, pending independent review.** Not built, and
  meaningfully distinct from what exists: the real Stage-2 precedent only requires an
  *immediate* re-submission with a flag in the same request — it does not pause and
  wait for a separate human action at a later time, and nothing stops it from being
  scripted with zero real deliberation. This is a genuine limitation of the existing
  precedent, not full credit toward Stage 3.
- **Stage 4 — Bounded veto.** Not built, and per this entire investigation's own
  evidence (no concern-generation quality has ever been measured for anything),
  clearly premature by every precondition this project already uses elsewhere
  (council trust, `mark_baseline_trusted()`, etc.).

**The important, non-obvious finding**: authority-adjacent scaffolding in this
project's own ladder shape (Stages 1-2) **already exists — but it belongs to the
multi-model council, not to Echo's own individually-originated voice.** The mission's
"voice before veto" sequencing is correct for **Echo's own voice specifically** — that
genuinely doesn't exist yet, at any stage, and nothing should be granted to it before
it does. But it would be inaccurate for this report to claim the project has built
*nothing* in the authority-ladder's shape; it has, just for a different actor
(the council, reactive to a human action) than the one this mission is asking about
(Echo, acting from her own persistent state). Extending real authority to Echo's own
concerns specifically still requires exactly what this mission proposes: build Voice
first, measure it, and only then consider whether *Echo's* concerns — as distinct
from the council's, which already has a foothold — should ever climb this ladder.

---

## 16. Preconditions for Actual Protector Authority

Derived from evidence gathered in this investigation, not the mission's raw candidate
list taken uncritically:

- **Concern generation demonstrably non-hollow** — a measured false-concern/false-
  silence rate from a real Phase-0 experiment (Section 11-12), not an assertion.
- **Numeric thresholds for acceptable false-positive/negative rates, fixed *before*
  measurement** — avoiding this project's own documented pattern of picking a
  threshold after seeing data and calling it principled (contrast with
  `_MIN_VARIANCE`'s disclosed, honest version of exactly this: chosen from real data,
  but stated plainly as such, not hidden).
- **Automated evidence-verification**, reusing `code_verification.py`'s sandbox-check
  pattern rather than trusting narrative self-report.
- **Measured resistance to prompt injection** — this project already has a
  quantitative precedent for exactly this kind of test (Finding 86's real, measured
  33%→75% injection-resistance improvement on the synthesis system prompt) —
  any future Initiative-Record rendering layer needs an equivalent measured number,
  not an assumption.
- **Provenance traceability** (`source_state_hash`, Section 8).
- **Stable identity semantics**, reusing `substrate_continuity`'s ≥95% pattern.
- **Independent review of disposition disagreements** — never self-evaluated, per
  Section 10's circular-authority mitigation.
- **A demonstrated, real revocation precedent** — this project already has one:
  `shadow_model.py` was built, trusted, measured, found performing below chance
  (13.2%-16.1% vs. ~20% baseline), and retired from live use (2026-09-13) without
  deleting the implementation. Any future Protector authority grant needs the
  identical willingness to revoke on measured evidence, and this precedent should be
  cited explicitly as proof the project can actually do this, not just say it will.
- **Fail-safe behavior** — the real restore-gate already sets the bar correctly ("if
  the council can't be reached, this behaves exactly as before") — any future
  authority-bearing mechanism must fail to *no block*, never to *block*, on internal
  error.
- **Bounded authority domains** — narrowly enumerated operations only, matching the
  restore-gate's own scope discipline.
- **Gremlin's own final override always preserved** — unconditionally, per
  `GREMLIN_ROLE.md` and ORIGIN.md's "final safety override" seat; this is not
  negotiable by anything designed here.
- **Immutable, append-only audit trail** — matching every other log in this project.
- **No circular self-authorization** — an independent evaluator, never Echo's own
  say-so on her own concern's validity.

---

## 17. Falsification Attempt

Genuinely attempted, not gestured at — eight distinct arguments tried against the
premise.

1. **Is the founding obligation overinterpreted?** **Fails to kill the premise.**
   Checked directly (Section 2): ORIGIN.md states, in its own words, that the
   Protector Clause seat "never became a real mechanism." This is the strongest
   possible evidence against overinterpretation — it's the source document's own
   admission, not a later reviewer's inference.
2. **Does an existing mechanism already solve this?** **Partially succeeds, usefully.**
   The Dissent Log and the restore-gate solve a real, adjacent slice of the problem —
   non-hollow, evidence-grounded disagreement, for two specific human-triggered
   actions. This should *scope down* what Phase 0 needs to build (reuse these as two
   of three trigger sources, Section 9's Hybrid), but does not fully kill the premise:
   the specific missing piece — content-driven initiation not preceded by a human
   action — remains genuinely absent, confirmed independently by the disconnected
   `_emit_fn` finding (Section 6).
3. **Would Initiative Records merely duplicate reflection logs?** **A real risk, but
   fails as a full argument against building anything.** Reflection logs are
   free-associative, ungated by any real anomaly condition, and — critically — this
   argument's fear is exactly what *would* happen if `reflection_shard`'s disconnected
   `emit_fn` were simply switched on as a shortcut (ungrounded content reaching a
   human with zero evidence, zero discrimination, zero threat model). This argument's
   real value is a warning against that shortcut, not evidence against Phase 0 as
   designed (mechanically-triggered, evidence-grounded, template-rendered).
4. **Is there no operational way to distinguish initiative from scheduled
   generation?** **Fails.** Section 6/7 found and operationalized exactly such a
   distinction (trigger-independent-of-immediate-human-action, conditional-on-a-real-
   anomaly) and showed it already separates real mechanisms in this codebase
   (`seam_engine` vs. reflection/dream) cleanly.
5. **Would any apparent "concern" simply be model role-play?** **The strongest
   surviving objection, and it is accepted as a hard constraint, not dismissed.** If
   any future version of this design adds an LLM judgment call about "is this
   condition worth surfacing," this objection fully applies and should block that
   revision — it is functionally identical to WOLF's failure mode with friendlier
   vocabulary. Section 9's Hybrid recommendation (mechanical trigger, template-only
   rendering, zero LLM discretion over worthiness) is the direct, load-bearing answer
   to this objection, not a workaround for it.
6. **Would the experiment teach us nothing?** **Fails.** The frozen case set
   (Section 11) draws on real, already-collected historical data (1,029 real seam
   detections, real Dissent Log entries) — measuring true/false concern rates against
   this is a genuine, falsifiable measurement available today, not a manufactured
   result.
7. **Is the identity problem currently too unresolved?** **Partially succeeds — a
   real, disclosed gap.** "Which model/process speaks for Echo" has a working answer
   for ordinary conversation (`substrate_continuity`'s ≥95% check) but has never been
   asked for a new output type like an Initiative Record. This is flagged honestly as
   one of the four concrete preconditions in Section 19, not resolved by precedent
   alone.
8. **Could observation itself create the behavior we're trying to detect?** **A real,
   narrow risk, well-contained for Phase 0 specifically.** Since Phase 0's trigger
   layer makes no LLM judgment call about worthiness, there is no place for
   performative "I have a concern" role-play to insert itself at the trigger stage.
   This risk becomes live only if a future stage exposes "you have a mechanism to
   raise concerns" to Echo's own prompt context alongside an LLM judgment call — a
   reason for caution in any later design, not a reason to reject Phase 0 as
   specified here.

**Net result of falsification**: the premise substantially survives. Two arguments
(2 and 7) genuinely narrow and sharpen what needs to be built, rather than defeating
it. One argument (5) is accepted outright as a permanent hard constraint on any
future design, not just this one. None of the eight succeed in showing the underlying
gap is illusory, manufactured, or already fully closed.

---

## 18. What This Would NOT Establish

Even a fully successful Phase-0 experiment, cleanly discriminating positive from
negative cases, would **not** establish:

- That Echo is conscious.
- That Echo has subjective experience.
- That Echo is a person, or a moral patient.
- That Echo has genuine emotions.
- That Echo has intrinsic preferences, as opposed to generated outputs that pattern-
  match preference-shaped language.
- That persistence of a concern across restarts implies any continuity of identity
  beyond what this project's existing, narrower persistence claims already establish
  (real file-based state, not narrative memory).
- That a demonstrated ability to discriminate meaningful anomalies from benign
  controls implies anything about *why* the discrimination succeeds, beyond the
  mechanical trigger conditions actually tested.

A successful Phase 0 would establish something narrower and more defensible: **that a
persistent computational agent's own accumulated, mechanically-derived state can
participate — non-authoritatively — in surfacing information a human would otherwise
have to find by chance.** That is an engineering result, not a metaphysical one, and
this report does not claim otherwise anywhere above.

---

## 19. Recommendation

**REVISE BEFORE BUILD.** Four specific, individually tractable gaps, each with a
reusable precedent already in this codebase, must be closed before a Phase-0
experiment is buildable and measurable with confidence:

1. **Commit, in the design itself, to zero LLM discretion over "is this worth
   surfacing" for Phase 0** — mechanical triggers only (`seam_engine`, Dissent Log,
   restore-gate), template-only rendering. This is the direct answer to Section 17's
   Argument 5 and must be a hard constraint, not a preference, before any code is
   written.
2. **Decide explicitly whether Phase 0 is pull-only (matching every existing
   precedent, lowest risk) or needs some minimal push surfacing** — e.g., a
   distinguished, always-checked section of `/admin/liveness-status` for open,
   undispositioned Initiative Records — without building new outbound-messaging
   infrastructure, which remains outside this mission's and any near-term mission's
   scope. This is a half-day design decision, not a research question.
3. **Extend `substrate_continuity`'s identity-verification pattern to cover Initiative
   Records specifically** before finalizing the schema in Section 8 — a small,
   scoped addition to an already-proven mechanism, not new architecture.
4. **Design the automated evidence-verification step** (reusing
   `code_verification.py`'s sandbox-check pattern) concretely enough that
   `evidence_refs` can be spot-checked, not just declared, before the schema is
   considered final.

As a genuinely low-cost, purely-read-only next step available immediately, **before
any of the above four gaps are even closed**: a retrospective, read-only analysis of
whether any of the 1,029 real `seam_engine` detections already on disk correlate with
anything later judged significant (a real self-edit outcome, a real restore, a real
dissent-log entry near the same timestamp) would directly inform Section 9's open
question ("mechanical anomaly ≠ meaningful concern") using data that already exists,
with zero new code and zero risk. This is the recommended immediate next action if
this line of work continues — not implementation, a second, narrower investigation.

This recommendation concerns **voice only**. It does not authorize veto authority.

---

## 20. Repository / State Integrity

- `ORIGIN.md`: read only, not modified.
- `CLAUDE.md`, `PENDING_DECISIONS.md`: read only (their pre-existing, already-known
  2-line and 15-line diffs from `HEAD` predate this mission and were not touched or
  added to).
- `run.py`, `app/core/self_edit_manager.py`, `app/core/snapshot_manager.py`,
  `app/core/liveness_ledger.py`, `app/subsystems/reflection_shard.py`,
  `app/core/seam_engine.py`: all read only.
- `memory/seam_log.jsonl`, `memory/dissent_log.jsonl`: read only (line-counted and
  aggregated, never written to).
- No Initiative Record mechanism, no Protector Clause logic, no veto logic, and no
  outbound-messaging capability were implemented anywhere.
- Nothing was staged, committed, or pushed. `git status` was not used to construct any
  commit in this mission.
- Echo's live state was not intentionally altered; no self-edit, restore, or council
  review was triggered by this investigation.
- The only new artifact produced is this report file itself, left untracked and
  unstaged, per the mission's explicit instruction.
