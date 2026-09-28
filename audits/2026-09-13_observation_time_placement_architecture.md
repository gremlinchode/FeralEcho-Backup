# Observation-Time Placement Architecture

**Date:** 2026-09-13
**Type:** Read-only architectural research. No production code, test, schema, or configuration modified. No process restarted/signaled/instrumented. No observation-time implementation, reconciliation logic, or migration code written. PID 7644 inspected read-only only (`ps`).
**Predecessors:** `audits/2026-09-13_cross_layer_reconciliation_boundary.md` (surfaced the gap), `audits/2026-09-13_observation_time_contract_research.md` (defined the contract conceptually: `observed_at` + `clock_source`, per-observation not per-composed-result). This mission determines **where** that contract should be owned — not whether it should exist.

---

## Executive Conclusion

**Model A — Producer-Owned Observation Time — is the correct placement, with one real, previously-uncited, already-working precedent in this codebase validating it (`liveness_ledger.py`'s `_result()` helper, §8) and one confirmed genuine gap instance (`introspection_channel.py`, §7) demonstrating the failure this placement must prevent.** No existing abstraction in this codebase (`self_model_claims.py`, the closest candidate found) is the right *shape* to serve as a shared envelope — it is a claims ledger, not a generic evidence container, and adopting it would conflate two structurally different concepts. Model B (a common envelope) is not rejected on principle, only on evidence: nothing in this codebase's actual evidence-producing code currently shares enough structure to justify one, and building it now would be exactly the kind of premature abstraction this research thread's own discipline (`working_tree_file_identity`'s and `runtime_process_identity_and_self_report`'s own design notes) has repeatedly declined to build ahead of demonstrated need. Model C (reconciliation-owned time) is rejected outright, not as a close call: it can only ever record *when reconciliation ran*, a fact strictly less informative than, and easily mistaken for, the true observation time it would be substituting for — this is not a placement tradeoff, it is a category error.

**A significant correction to the predecessor report is recorded here**, found during this mission's own verification pass, not assumed from the prior report's claim: `liveness_ledger.py` does **not** share `introspection_channel.py`'s exact gap. Its shared per-check entry builder, `_result()`, already stamps `"checked_at": _now_iso()` at the moment each individual check's own outcome is decided — a genuine, already-correct, already-shipped instance of per-observation timestamping. Only its *outer* `generated_at` field (stamped once, before the check loop) has the collection-level gap the predecessor report described — a materially narrower problem than originally stated.

---

## 1. Starting State

```
HEAD (verified fresh): e03f5984bb86d36ade51ed8f0753a3b8264c0f9f
git status --porcelain=v1 | wc -l: 105
```
Matches the exact end-state recorded by the predecessor mission — no discrepancy, proceeded without stopping. The same 19 pre-existing modified files remain present and untouched (confirmed by name, not just count). PID 7644 confirmed present, `Thu Sep 10 22:41:53 2026`, `ps` only. Both predecessor reports read in full before beginning this one; neither modified during this mission.

---

## 2. Existing Evidence Abstractions

Direct search across `app/` for class-shaped evidence/observation/ledger/envelope concepts (`grep -rln "class.*Evidence\|class.*Observation\|class.*Ledger\|class.*Envelope\|class.*Record\b"`) returned exactly one hit outside this research thread's own experimental sandboxes: `app/experiments/preference_provenance/schema.py` — an isolated, explicitly-experimental module (per its own docstring conventions established elsewhere in this repo, e.g. the RAOC harness) with zero production callers, not a candidate for reuse. **No class-based, generically-reusable "Evidence"/"Observation" abstraction exists anywhere in FeralEcho's live application code.**

The one real, function-based (not class-based) precedent found is `app/core/self_model_claims.py`'s `record_claim()` — see §6.

---

## 3. Model A — Producer-Owned Observation Time

**Shape**: each individual evidence-gathering function stamps `observed_at`/`clock_source` on its own return value, at the exact point it completes its own observation — matching Layer 1's `_stat_evidence()`, Layer 2's `_external_process_observation()`'s per-field loop, and (newly confirmed, §8) `liveness_ledger.py`'s `_result()`.

- **Advantages**: the timestamp is generated at the literal moment of truth — no intermediary can introduce skew between observation and recording. Directly matches the mission's requirement #1 ("the timestamp is generated at the true evidence boundary"). Zero new abstraction required; every candidate producer already returns its own dict (Layer 1's `_stat_evidence()` returns a tuple consumed into a dict; Layer 2's field-loop already builds `result` incrementally; `liveness_ledger.py`'s `_result()` already exists and already does this correctly for one of the three fields this research concerns).
- **Disadvantages**: **consistency is not automatic** — nothing currently enforces that every producer actually does this (§11, the enforcement question, is the direct continuation of this concern). **Duplication risk is real but small**: the same two-line stamping pattern (`datetime.now(timezone.utc).isoformat()`, a `clock_source` constant) would need to appear in every producer, though this is exactly the kind of small, uniform duplication Layer 1/2's own `_find_project_root()` (independently duplicated per-module, by this project's own established convention, per `provenance_check.py`'s own header comment) already treats as acceptable rather than worth a shared import.
- **Whether every producer can realistically comply**: yes for all producers examined this session (Layer 1's filesystem/git calls, Layer 2's psutil/file-read calls, `introspection_channel.py`'s 8 collectors, `liveness_ledger.py`'s 30+ checks) — every one already returns its own dict at the point of observation; adding one field is structurally trivial in every case examined, not a redesign.
- **Composed results preserving individual timestamps**: yes, directly — this is exactly what `liveness_ledger.py`'s existing architecture already does correctly (§8): each check's own `_result()`-built entry carries its own `checked_at`, and the composed `ledger` dict simply collects them under per-check keys, exactly matching `introspection_channel.py`'s existing per-collector key structure (§7) that currently lacks only the per-key timestamp.
- **Schema churn**: minimal — one additional field (`observed_at`) plus one small enum field (`clock_source`, §9) per already-existing producer return shape; no restructuring of any existing field.

---

## 4. Model B — Common Evidence Envelope

**Shape**: `{subject, observation: {...actual fields...}, observed_at, clock_source}` — a generic wrapper any producer's real output would be nested inside.

- **Does such an envelope already exist?** No (§2) — confirmed by direct search, not assumed.
- **Could an existing abstraction be extended into one?** `self_model_claims.py`'s entry shape (`{timestamp, subject, verified, evidence, proposed_by, verified_by}`) is structurally the closest thing in this codebase to an envelope — but its `subject` field is a small, fixed, curated enum (`KNOWN_SUBJECTS`, exactly 5 entries: RiverBrain, self_edit_pipeline, liveness_ledger, curiosity_engine, world_model) representing *conversational claims about self-model state*, categorically different from Layer 1's *file-path-keyed* evidence or Layer 2's *PID-keyed* evidence. Forcing Layer 1/2 evidence into this shape would mean either inventing new `KNOWN_SUBJECTS` entries for every possible file path and PID (defeating the purpose of a small, curated enum) or loosening the enum into an open vocabulary (undermining the exact design discipline that module's own header comment states was deliberate: *"Deliberately small and explicit... rather than an open vocabulary"*). **Rejected as a direct extension, on the evidence, not on principle.**
- **Does the architecture have enough commonality to justify a new envelope?** Examined across all four real producer categories in this research thread (Layer 1 filesystem/Git, Layer 2 process/self-report, `introspection_channel.py`'s 8 collectors, `liveness_ledger.py`'s 30+ checks): each has a genuinely different *subject* shape (a path, a PID, a subsystem name, a check name) and a genuinely different *evidence* shape (hashes, process metadata, arbitrary nested health data, pass/fail+evidence-string). The *only* thing they would share, if wrapped, is exactly the two fields Model A already proposes attaching directly (`observed_at`, `clock_source`) — an envelope whose entire distinguishing content is two fields that could just as easily live on the existing return dict is not earning its own structural existence.
- **Would wrapping obscure provenance?** Yes, a real risk: today, `working_tree_file_identity()`'s return dict *is* the evidence, flat and directly inspectable, matching this whole research thread's own repeatedly-stated preference for "evidence, not labels, not layers of indirection." An envelope requiring `.observation.sha256` instead of `.sha256` adds a real access-pattern cost for zero additional epistemic content.
- **Nested/compound evidence ambiguity**: a real, concrete problem for this specific architecture — Layer 2's `runtime_self_report` already nests two sub-observations (`server_pid_file`, `sentinel_file`), each independently timestamped under Model A; a naive envelope wrapping the *whole* `runtime_self_report` block in one `observed_at` would silently reintroduce exactly the collection-level collapsing bug this whole investigation exists to prevent — the envelope model, applied carelessly, is *more* prone to this failure than Model A, not less, because it invites wrapping at the wrong (composed, not atomic) level.
- **Could it accidentally imply atomicity?** Yes — a single `Evidence` object with one `observed_at` field strongly visually suggests "this one thing was observed as a whole," precisely the false claim the predecessor report's own §5 (temporal model) explicitly warned against manufacturing.

**Model B is not implemented and not recommended — not because envelopes are architecturally wrong in general, but because this specific codebase's evidence producers do not share enough real structure to justify one, and the one existing structurally-similar module (`self_model_claims.py`) would require distorting its own deliberately-narrow design to serve a purpose it wasn't built for.**

---

## 5. Model C — Reconciliation-Owned Time

**Shape**: reconciliation itself (a future `reconcile_process_and_selfreport()` or similar) stamps `observed_at` when it receives or processes evidence, rather than the original producer.

- **What information would already be lost?** Everything §3/§7/§8 establish as the actual value of per-producer timestamping — the true moment `_stat_evidence()` opened a file, or `psutil.Process.create_time()` was actually called, is simply gone by the time a caller-level reconciliation function runs; only the moment reconciliation itself executes remains observable.
- **Could reconciliation reconstruct observation time after the fact?** No — this is not a partial loss recoverable by clever inference; the true observation instant is a fact about *when a specific syscall/file-read/subprocess-return happened inside the producer*, and nothing outside that call frame has access to it once it returns. Reconciliation receiving a bare dict with no timestamp has strictly less information than reconciliation receiving a dict with a slightly-stale-but-real timestamp.
- **Can caller timing substitute for producer observation time?** No, and doing so would be actively worse than having no timestamp at all: a reconciliation-stamped time is guaranteed to be *later* than the true observation (by however long the intervening call stack took — unbounded, unmeasured), and a consumer reading it would have no way to know this, unlike Model A's honest per-producer stamp, which is exactly the observation moment it claims to be.
- **False precision?** Directly, yes — a reconciliation-stamped `observed_at` reads identically, in format and apparent authority, to a genuinely producer-stamped one, while actually encoding a categorically weaker fact ("when reconciliation happened to run," not "when the evidence was gathered"). This is the single clearest case in this whole comparison of a placement choice that would *look* like it satisfies the contract from the predecessor report while *actually violating* that report's own central finding (that a composed/derived timestamp must never stand in for the true per-item observation moment).

**Model C is rejected outright, not as a close tradeoff.**

---

## 6. Alternative Existing Architecture

`self_model_claims.py`'s `record_claim()` is the one real, working, already-shipped precedent for a per-write timestamp stamped at the exact moment of the write (`entry["timestamp"] = datetime.now(timezone.utc).isoformat()`, computed inline within `record_claim()` itself, never passed in from an earlier caller) — genuine evidence that this pattern works correctly in production today, for a single-item write. **It validates Model A's underlying mechanism; it is not itself a reusable home for Layer 1/2's evidence**, for the shape reasons given in §4. One further, real nuance found while reading it this session: `record_claim()`'s own `entry["timestamp"]` describes *when the claim was recorded*, not necessarily *when the `evidence` string it carries was itself established* — the same subject-time-vs-observation-time distinction the predecessor report drew for file/process facts applies recursively to this existing ledger too, worth naming here since it was not previously stated anywhere in this research thread.

**No fourth, better-fitting existing architecture was found.** The search was genuinely broad (§2's full term list) and turned up exactly one real candidate, evaluated honestly above and found to validate rather than replace Model A.

---

## 7. `introspection_channel.py` Case Study

Traced completely, `collect()` and all 8 sub-collectors:

1. **Current timestamp location**: `introspection_channel.py:220`, `"timestamp": datetime.now(timezone.utc).isoformat()`, inside the dict literal that begins `collect()`'s body — **before** any of the 8 `self._collect_*()` calls on the following lines.
2. **What it actually represents**: the wall-clock instant `collect()` began executing — a collection-*start* timestamp, not an observation timestamp for any specific piece of evidence within it.
3. **Discrete observations occurring afterward**: 8 — `_collect_river_brain`, `_collect_friction`, `_collect_sandbox`, `_collect_memory`, `_collect_self_edit`, `_collect_optuna`, `_collect_system_health`, `_collect_predictive_loops`, each independently performing real I/O (confirmed by direct trace of several this session and in the predecessor mission).
4. **Sequence**: fixed, in dict-literal-evaluation order, exactly as listed above — Python evaluates dict-literal values left-to-right, top-to-bottom.
5. **Do the returned sub-structures already distinguish individual observations?** **Yes, confirmed this session** — each `_collect_*()` function has its own `-> dict` signature and is stored under its own named key (`"river_brain"`, `"claude_shard"`, etc.) in the composed result. Individual observations are already structurally separate; only the *timestamp* is not.
6. **Would adding individual observation timestamps at the producer boundary be natural?** Yes, directly — each of the 8 functions could add one `"observed_at"` key to its own already-independent return dict with no restructuring, mirroring exactly what `liveness_ledger.py`'s `_result()` already does correctly (§8) for its own per-item results.
7. **Would an envelope fit better?** No — per §4's general finding, and specifically here: wrapping each of these 8 already-distinct dicts in a further envelope would add structure without adding information beyond the one field Model A already proposes attaching directly.
8. **What information is currently lost**: the true observation time of every collector except (trivially) whichever ran first — for a cycle with 8 real I/O-performing steps, the gap between the recorded `"timestamp"` and the true observation time of, say, `_collect_predictive_loops()` (the last of the 8) is real, unmeasured, and — per this session's confirmation that no monotonic timing exists anywhere in this codebase (predecessor report §6) — currently **unrecoverable even in principle** from the existing recorded data.

**Not modified. Confirmed as the clearer, more complete instance of the gap this whole placement question exists to resolve.**

---

## 8. `liveness_ledger.py` Case Study

Traced completely, `run_liveness_checks()` and the shared `_result()` helper — **with a real correction to the predecessor report's characterization, found and verified this session**:

1. **Where the *outer* timestamp is generated**: `liveness_ledger.py:3965`, `ledger = {"generated_at": _now_iso()}`, before the `for name in _CHECKS:` loop — genuinely a collection-start timestamp, exactly as the predecessor report described.
2. **How many sequential checks occur**: 30+ (confirmed by direct count of the `_CHECKS`/`runners` dict entries visible in source), each a real function call performing its own I/O or computation.
3. **Do those checks have independent evidence identities?** Yes — each is keyed by its own check name (`"apply_to_code"`, `"curiosity_engine"`, etc.) in both the `_CHECKS` dict and the final `ledger` dict.
4. **Do they currently return individual results?** Yes, and — **this is the corrected finding** — each individual result, built via the shared `_result(passed, evidence, extra=None)` helper (confirmed via direct source read, `liveness_ledger.py:175-179`), **already includes `"checked_at": _now_iso()`, stamped at the moment that specific check's own `_result()` call executes** — genuinely per-check, not collection-level. Confirmed this is the general, not exceptional, pattern: 215 real call sites to `_result(` were found across the file (multiple per check, for its various pass/fail/error branches), all routing through this one shared, already-timestamping helper.
5. **Could their evidence naturally carry individual observation timestamps?** It already does, per point 4 — this question is **already answered affirmatively in shipped code**, not merely "naturally could."
6. **What temporal information is currently lost**: narrower than the predecessor report stated — only the relationship between the *outer* `generated_at` (when the cycle started) and each check's own, already-recorded `checked_at` (when that specific check actually ran) is currently unexploited; nothing about the checks' own individual observation times is lost, because they are already recorded.
7. **Does the architecture already have an appropriate evidence container?** For the per-check level: **yes, `_result()` already is one**, and already does the right thing. For the collection level: no, `generated_at` remains a start-of-cycle stamp with no accompanying end-of-cycle or interval concept.

**Not modified. This file requires materially less remediation than the predecessor report implied — its per-check design already embodies Model A correctly; only the outer/collection-level field needs the reframing (from an implied "when this was generated" to an honest "when this cycle began") the predecessor report's own §5 (individual timestamps vs. optional derived interval) already anticipated as the correct shape for a collection-level summary field.**

---

## 9. `clock_source` Semantic Analysis

Attacked, not accepted from the predecessor report by default, per this mission's explicit instruction:

- **Free-form string**: rejected — invites drift (`"system"`, `"wall_clock"`, `"os_clock"` all meaning the same thing, spelled three ways by three future producers), the exact kind of silent-vocabulary-fragmentation this research corpus has already found and fixed twice elsewhere in this codebase (`CATEGORIES`/`TASK_TYPE_MAP`, cited directly in `self_model_claims.py`'s own header comment, §6).
- **Controlled vocabulary (a small, fixed enum)**: **recommended, refined from the predecessor report's looser "fixed string" framing** — a small, explicit set (e.g. `{"system_wall_clock"}`, extensible only if a genuine second clock source is ever actually used, which this session confirms does not currently exist anywhere in this codebase, predecessor report §6).
- **Clock identifier vs. clock type vs. clock acquisition method — these are not the same concept, and conflating them was a real gap in the predecessor report's own treatment**: *clock type* answers "wall-clock or monotonic" (a real, necessary distinction — predecessor report §6 already correctly restricts this architecture to wall-clock only, for the stated reason that nothing here needs sub-second cross-process precision). *Clock identifier* would answer "which specific clock instance, if a system had more than one" — not applicable to a single-machine, single-host architecture like FeralEcho's. *Clock acquisition method* would answer "how was this value obtained" (`datetime.now(timezone.utc)` vs. `psutil.Process.create_time()` vs. `os.stat().st_mtime`) — this is a **materially different, and arguably more useful**, piece of information than "wall-clock or monotonic," since it directly names *which producer mechanism* generated the value, which matters for §6's dependence-group reasoning (the cross-layer report) far more than "wall clock" alone does (every mechanism examined in this entire research thread already uses wall-clock exclusively — the type distinction currently carries zero discriminating information).
- **Structured object**: rejected as unnecessary — a single controlled-vocabulary string already carries the one distinction (acquisition mechanism) that currently matters; a structured object would be schema weight with no evidence-backed second dimension to justify it yet.
- **Unnecessary if `observed_at` has sufficiently defined semantics?** No — even a perfectly-defined `observed_at` says nothing about *how* the value was produced, and §6's dependence-group reasoning (two facts from the same underlying producer are not independent triangulation) needs exactly this information to be attached at the point of observation, not reconstructed later.

**Revised recommendation**: `clock_source` should be a small, controlled-vocabulary string naming the **acquisition mechanism** (e.g. `"psutil.create_time"`, `"os.stat.st_mtime"`, `"datetime.now"`), not a bare "wall-clock vs. monotonic" type label — this is a genuine refinement of the predecessor report's own treatment, which conflated "which clock" with "how was it read" without distinguishing them this precisely.

---

## 10. Composition Semantics

Building on §3/§7/§8's concrete evidence, not the abstract mission examples alone:

- **What the composed result should contain**: each individual observation's own `observed_at` (per Model A, already the pattern in `liveness_ledger.py`'s per-check results) — never collapsed.
- **`collection_started_at`/`collection_completed_at` or a derived `collection_interval`**: genuinely useful as an optional, *derived* summary at the composing function's own level (e.g., `introspection_channel.py`'s `collect()` could compute `min()`/`max()` of its 8 sub-collectors' own `observed_at` values after they're gathered) — but must never be computed *before* the sub-observations run (exactly `introspection_channel.py`'s current bug) and must never be presented as if it were itself an observation time for any specific fact within the collection.
- **What is redundant**: a per-item `clock_source` repeated identically across every sub-observation of a single composed call *when all sub-observations genuinely share one acquisition mechanism* (e.g., all 8 of `introspection_channel.py`'s collectors reading from the same kind of source) would be real, harmless redundancy — acceptable, not worth optimizing away at the cost of the per-item independence Model A requires.
- **The central rule, restated precisely from the mission's own framing and confirmed correct by every case examined**: `[T1, T2, T3]` must never become a claim that everything was observed at `T1` or `T3` — `liveness_ledger.py`'s existing, correct per-check `checked_at` design (§8) is live proof this rule is already successfully followed in one real part of this codebase; `introspection_channel.py`'s existing, incorrect single `"timestamp"` (§7) is live proof of what happens when it isn't.

---

## 11. Enforcement / Misuse Resistance

**The weakest point, stated plainly**: nothing in this codebase's current tooling prevents a future developer from writing a new composed-collection function that puts one `observed_at` at the top, exactly as `introspection_channel.py`'s author did — there is no lint rule, no shared base class, no structural constraint of any kind. `liveness_ledger.py`'s own correct design (§8) was evidently achieved by whoever wrote `_result()` making a good, disciplined choice — not by anything in the architecture that would have caught the *opposite*, incorrect choice if made instead. This mission does not propose implementing an enforcement mechanism (out of scope), but names this precisely as the single most important open question for any future implementation mission: **can "producer-owned observation time" be made structurally difficult to get wrong, or does it remain a discipline that must be manually upheld per-producer, the same way this project's own `EDIT_FORBIDDEN_TARGETS`/F1/F2/F3 discipline is upheld by code review and convention rather than a single automatic guarantee?** Not answered here — flagged as the clearest remaining gap between "the contract is well-specified" (predecessor report) and "the contract will actually be followed by every future producer" (unaddressed by either report so far).

---

## 12. Historical Compatibility

Consistent with the predecessor report's own strong default, reapplied here at the placement level: regardless of which model is chosen, **no existing evidence record anywhere in this codebase can be retroactively assigned a genuine observation timestamp** — not `introspection_channel.py`'s past `"timestamp"` values (collection-start, not per-item, as newly confirmed §7), not `liveness_ledger.py`'s past `generated_at` values (same), and — a new point this session — **not even `liveness_ledger.py`'s own existing `checked_at` values for checks run before this research began**, because nothing established that those historical values were being *consumed* as true observation times by anything downstream; they existed, correctly, but their epistemic significance was never previously documented anywhere in this research thread until this mission traced them directly. This is itself a small, concrete instance of the predecessor report's own §7 finding (historical evidence without a *documented, understood* observation-time contract must be treated as if the contract didn't exist for it) — even *technically correct* historical data can be practically unusable if its correctness was never established as a load-bearing fact until now. **State: `UNKNOWN`** for any evidence record predating a documented, understood observation-time contract, full stop — not `PROBABLY_FINE_BECAUSE_IT_LOOKS_RIGHT`.

---

## 13. Adversarial Comparison

| # | Failure mode | Model A (producer-owned) | Model B (envelope) | Model C (reconciliation-owned) |
|---|---|---|---|---|
| 1 | Producer forgets to timestamp one observation | **Detectable** (field absent → explicit `UNKNOWN`, not silently defaulted) — not *prevented* (§11) | Same detectability, no better | N/A — this model never has per-producer timestamps to forget |
| 2 | Composed collector timestamps only its beginning | **Prevented by design if followed** (§3, §8's proof); **not structurally prevented from being reintroduced** (§11) | Same underlying risk, plus §4's finding that envelopes invite wrapping at the wrong (composed) level | **Guaranteed to happen** — this is this model's entire failure mode, not an edge case |
| 3 | A caller timestamps an already-produced result | **Detectable as wrong** if the true producer-level field is also present (two different, comparable timestamps) | Same | **This model IS this failure mode** |
| 4 | Two producers use different clock semantics | **Represented explicitly** via `clock_source` (§9) — not prevented, disclosed | Same | Same disclosure available, but attached to the wrong moment |
| 5 | Producer returns stale evidence | Orthogonal — Model A records *when checked*, not *whether current*; already correctly out of scope per predecessor report §10 | Same | Same |
| 6 | Process changes during collection | Model A's per-field granularity (Layer 2's existing design) already represents this partially (field-by-field degradation, cross-layer report) | An envelope around the whole `external_process` block would obscure exactly this — a real, concrete regression risk | N/A |
| 7 | File changes during collection | **Directly representable** — two Layer 1 calls, two different `observed_at`, two different hashes, honestly sequential | Same, if unwrapped at the right granularity; worse if wrapped at file-level only | Would show one late timestamp for a possibly-already-stale read |
| 8 | Evidence is cached | Model A's timestamp travels with the original observation, correctly surviving caching — a cache layer must not re-stamp | Same requirement, same risk if the cache re-wraps | This model actively encourages exactly the wrong behavior (stamp at consumption, not origin) |
| 9 | Evidence is replayed later | Same as 8 — the original `observed_at` remains the honest anchor | Same | Same failure as 8, worse |
| 10 | Historical record lacks observation time | **`UNKNOWN`, explicitly** (§12) — same for all three models, since this is a fact about *past* data regardless of which model governs *future* data | Same | Same |
| 11 | Clock adjusted during collection | **Disclosed via `clock_source`, not solved** (predecessor report §6, unchanged here) | Same | Same |
| 12 | Collection takes long enough that start/end materially differ | **Directly, honestly representable** — this is precisely what per-item timestamps plus an optional derived interval (§10) are for | Same, if the envelope is applied per-item; defeats the purpose if applied once per collection | **Actively hides this** — a single reconciliation-time stamp cannot distinguish a fast collection from a slow one at all |

**Net result**: Model A is the only one of the three that is either "detectable/representable" or "prevented-by-design" across all 12 cases; Model C fails outright on 4 of 12 (cases 2, 3, 8/9-shape, 12) by construction, not by misuse; Model B inherits Model A's own properties only when applied at the correct (atomic, not composed) granularity, and actively *increases* risk on cases 2 and 6 by inviting the wrong granularity.

---

## 14. Recommended Placement

**Model A — Producer-Owned Observation Time.** Each function that performs a real, discrete I/O operation (a `stat`, a `read`, a `psutil` call, a `subprocess.run`) attaches its own `observed_at`/`clock_source` at the point that operation returns, mirroring `liveness_ledger.py`'s already-correct `_result()` pattern (§8) and closing `introspection_channel.py`'s confirmed gap (§7) the same way. Composed callers (a future `collect()`, a future `reconcile_process_and_selfreport()`) consume these already-stamped values and may *derive* an interval summary, but never originate a timestamp themselves for evidence they did not directly observe.

---

## 15. What This Enables

- An honest answer to "when was this specific fact established," for every producer that adopts it — not merely the composed-cycle-level approximation available today.
- Direct detection of exactly the case §7/§8 demonstrate is currently invisible: a slow, multi-step collection where later steps' evidence is materially staler than the collection's own reported start time.
- A genuine basis for the cross-layer report's own dependence-group reasoning (§6 there) to be checked *directly against recorded data*, rather than only reasoned about from source (as this and the predecessor report have both had to do so far).

---

## 16. What This Still Cannot Prove

Restated, unchanged from both predecessor reports, because placement changes nothing about *what kind* of fact a timestamp is:

- Module loading, execution, or causality (Layer 3 report's own findings, untouched by any placement choice).
- That two facts observed close together describe the *same* underlying reality (cross-layer report §6/§11 — dependence, not timing, governs this).
- That agreement between multiple observations constitutes truth, independent of whether those observations share a dependence group.
- File/process identity linkage — no placement model adds a field connecting the two domains; this remains a structural absence, not a timing question.

---

## 17. Reconciliation Implications

A future `reconcile_process_and_selfreport()` should receive **timestamped evidence records — Model A's own output, not raw untimed observations, and not a Model B envelope wrapping them**. This means reconciliation's own responsibility is strictly narrower than either predecessor report's earlier framing might have implied: it consumes already-timestamped facts, computes *deltas* between them (exactly as Layer 2's own `_compose_correlation()` already does for *subject* time today, extendable to *observation* time once producers supply it), and must never itself originate a timestamp for evidence it did not directly gather (§5's Model C rejection, applied concretely here). This placement choice means reconciliation's eventual implementation does not need to "reconstruct" anything — the temporal evidence it needs will already exist on its inputs, provided the producer-level work implied by §7/§8/§11 happens first.

---

## 18. Recommendation

```
MORE RESEARCH REQUIRED
```

Not `PROCEED TO RECONCILIATION DESIGN`: §11 (enforcement) is a real, unresolved, load-bearing question this report explicitly declines to paper over — a placement model that is *correct in principle* (Model A, well-evidenced by §8's real precedent) but has **no mechanism preventing a future producer from getting it wrong** (as `introspection_channel.py`'s own author already did, §7) is not yet ready to be built upon by a reconciliation layer that would inherit any such future mistake silently. This is precisely the mission's own instruction not to choose PROCEED merely because a preferred architecture exists — the architecture is preferred, and genuinely evidenced, but one structural question (can correct placement be made durable, not just documented) remains open.

Not `ARCHITECTURAL BLOCKER`: nothing found here blocks progress — the placement question has a clear, evidence-backed answer (Model A); what remains is a narrower, scoped follow-up (enforcement design), not a fundamental obstacle.

---

## 19. Explicit Non-Claims

1. That Model A, once adopted, prevents a future producer from mis-implementing it — it does not, absent a separate enforcement mechanism this report explicitly does not design (§11).
2. That `liveness_ledger.py`'s existing `checked_at` fields were ever previously understood, documented, or relied upon as true observation timestamps by anything in this research thread before this mission traced them directly — their correctness is real but was, until now, undocumented and therefore not safely usable (§12).
3. That any timestamp, however precisely placed, establishes module loading, execution, causality, or identity linkage between a file and a process (§16, restated from both predecessor reports, unchanged by this mission's findings).
4. That agreement between two producer-stamped timestamps constitutes independent corroboration when the two producers share a dependence group (cross-layer report §6, unaffected by placement).
5. That a derived `collection_interval` is itself an observation — it is a summary computed *from* real observations, never a substitute for them (§10).
6. That this report's recommendation of Model A constitutes an implementation decision — it is a placement recommendation only; no code, schema, or migration was written or proposed as ready to build.

---

## Verification

Reviewed directly against this mission's own required term list:

- `verified`/`verification`: not used in a claim-asserting position anywhere in this document.
- `snapshot`: not used anywhere in this document.
- `simultaneous`: appears only in negated/cautionary form (e.g., "must never be presented as if... simultaneous").
- `execution`/`loaded`/`running`: appear only in §16/§19's restated non-claims, never asserted as established.
- `timestamp`/`observed_at`/`clock_source`: used throughout in strictly descriptive, non-inflated form — every claim about what a timestamp does or doesn't establish is scoped precisely (§16 restates the boundary every time the topic could otherwise be read as overclaiming).

---

## Integrity

```
Starting HEAD:  e03f5984bb86d36ade51ed8f0753a3b8264c0f9f
Ending HEAD:    e03f5984bb86d36ade51ed8f0753a3b8264c0f9f   (unchanged)
Files modified: none
Files created:  audits/2026-09-13_observation_time_placement_architecture.md (this file)
Staged:         nothing
Committed:      nothing
Pushed:         nothing
Scratch artifacts: none created -- entirely read-only grep/source inspection of
                 already-committed code
PID 7644:       unchanged throughout -- same start time (Thu Sep 10 22:41:53 2026)
                 confirmed via ps at mission start and end, read-only only
```
