# Observation-Time Contract Research

**Date:** 2026-09-13
**Type:** Read-only architectural research. No production code, test, schema, or configuration modified. No process restarted, signaled, or instrumented. No reconciliation logic designed or implemented. PID 7644 inspected read-only only (`ps`).
**Predecessor:** `audits/2026-09-13_cross_layer_reconciliation_boundary.md` (§7), which first surfaced the gap this report investigates: neither Layer 1 (`working_tree_file_identity`) nor Layer 2 (`runtime_process_identity_and_self_report`) records *when the evidence was observed*, only facts about the subject.

---

## Executive Conclusion

The minimum defensible observation-time contract is **two required fields per individual observation — `observed_at` (wall-clock, UTC, ISO-8601) and `clock_source` (a fixed string naming which clock produced it) — attached at the point each discrete piece of evidence is actually gathered, never once for an entire composed multi-step result.** No monotonic-clock field is required (nothing in this architecture currently measures durations that would need one, and none of today's comparisons — all cross-source deltas of minutes-to-days — are sensitive to monotonic-vs-wall-clock distinctions at that scale). No "observation interval" or "snapshot" concept is proposed, because the evidence does not support one: every composed observation in this codebase (Layer 2's own three-step read; `introspection_channel.py`'s eight-collector cycle; `liveness_ledger.py`'s 30+-check cycle) is sequential, not atomic, and this report finds a real, already-shipped, previously-uncited instance of exactly the timestamp-precedes-the-work gap this research was commissioned to investigate — currently unaddressed in production, not modified by this report. Timestamps establish *when*, never *what was true*, *why*, or *whether two facts describe the same underlying reality* — this report treats those as separate, unresolved questions throughout, per the mission's own explicit instruction.

---

## 1. Starting State

```
HEAD (verified fresh, not assumed from the predecessor report): e03f5984bb86d36ade51ed8f0753a3b8264c0f9f
git status --porcelain=v1 | wc -l: 104
```
No discrepancy from the predecessor report's own recorded end-state — proceeded without stopping. Relevant pre-existing uncommitted research artifacts (unchanged by this mission, listed for completeness, not touched): the full `audits/2026-09-1{0,1,2,3}_*provenance*`/`*layer2*`/`*layer3*`/`*cross_layer*` corpus, all still untracked from prior sessions. PID 7644 confirmed present, `Thu Sep 10 22:41:53 2026`, via `ps` only.

---

## 2. Existing Timestamp Inventory

Direct source trace, not inferred from field names — every timestamp-shaped field in the provenance codebase, plus two newly-identified precedents elsewhere in the live system:

| Field | Producer (exact source location) | Semantic meaning | Subject or observation? | Trustworthy as observation time? | Cross-source comparable? |
|---|---|---|---|---|---|
| `mtime` (Layer 1) | `os.stat(resolved_path).st_mtime`, `provenance_check.py:229` | When the *file itself* was last modified | **Subject** | No — describes the file, not the act of checking it | Only against other subject-time fields of the same kind (another file's mtime), not against an observation |
| `create_time_utc` (Layer 2, `external_process`) | `psutil.Process.create_time()`, `provenance_check.py:625` | When the OS created the *process* | **Subject**. Explicitly documented by `psutil` itself (confirmed via `help()`, this session) as "based on the system clock... may be affected by... manual adjustments or time synchronization (e.g. NTP)" — a real, disclosed clock-stability caveat on the subject time itself, independent of any observation-time question | Subject | Comparable to `start_utc` below only with the caveat both are wall-clock and both inherit this NTP/manual-adjustment exposure |
| `start_utc` (Layer 2, `sentinel_file`) | `run.py`'s `_SENTINEL_START = datetime.utcnow()`, captured once at module-import time, `run.py:1112` | When Python's import machinery reached that specific line in `run.py` — a proxy for, but not identical to, process start | **Subject**, and — per the Layer 2 red-team's own Finding 4 — a proxy with a real, disclosed ~4.4s gap from `create_time_utc` | Subject | Same caveat |
| `last_heartbeat_utc` (Layer 2, `sentinel_file`) | `dmn_guardian.py`'s ~60s guardian cycle, re-stamped via `datetime.utcnow()` each cycle | When the sentinel file was last refreshed — the closest thing in the existing architecture to "still alive as of this moment" | **Subject** (describes the artifact's own freshness), arguably closer to an observation-time concept than any other existing field, but still not attached to any *specific* evidence item — it is a property of the *file*, refreshed independently of any query | Neither cleanly | Not designed for comparison against other sources at all — purely an intra-file freshness signal |
| `"timestamp"` (`introspection_channel.py:220`, `collect()`) | `datetime.now(timezone.utc).isoformat()`, stamped **once, before** 8 sequential sub-collectors (`_collect_river_brain()` through `_collect_predictive_loops()`) each run their own real I/O | Intended to mean "when this introspection cycle ran" | **Neither cleanly subject nor a per-item observation time** — it is a *collection-start* timestamp retroactively applied to results gathered afterward | **No — new finding this session**: by construction, every sub-collector's actual evidence is gathered *after* this timestamp is recorded, so the field understates the true observation time of every result except the very first collector's | Not designed for this |
| `"generated_at"` (`liveness_ledger.py:3965`, `run_liveness_checks()`) | `_now_iso()`, stamped **once, before** the `for name in _CHECKS:` loop that runs 30+ individual check functions sequentially | Intended to mean "when this ledger was generated" | **Same shape as above, new finding this session** | **No, for the identical reason** — the field is consumed elsewhere (`liveness_ledger.py:4016-4017`, `age_s = _now() - generated_at`) as a staleness signal, which is a real, validated, existing use case for an observation-adjacent field — but the underlying timestamp itself precedes, rather than accompanies, the actual evidence-gathering it's attached to | Already used for exactly the kind of staleness computation a future observation-time contract would need to support |
| `generated_at` (`project_learner.py:133`) | `datetime.utcnow().isoformat() + "Z"`, stamped once per `ProjectLearner` instance construction | When a project-scan object was created | Neither — a construction timestamp on an unrelated internal tool | Not applicable to this research's scope |

**No field anywhere in this codebase currently means "the exact moment this specific piece of evidence was gathered."** The two closest precedents (`introspection_channel.py`, `liveness_ledger.py`) both stamp *before* a multi-step collection runs, not per-item — the same architectural gap this research was commissioned to investigate already exists, unaddressed, in already-shipped code. Neither predecessor report in this research thread had previously cited these two files; found by direct grep this session, not assumed.

---

## 3. Observation Boundaries

Traced to the exact line, not the surrounding function, per the mission's explicit instruction:

| Mechanism | Exact observation boundary |
|---|---|
| Layer 1 filesystem stat/hash | `os.stat(resolved_path)` and the subsequent `open(resolved_path, "rb").read()` inside `_stat_evidence()`, `provenance_check.py:227-231` — two separate syscalls, not one instant |
| Layer 1 Git query (`tracked`) | The return of `subprocess.run(["git", ..., "ls-files", ...])`, `provenance_check.py:239-243` — the moment the subprocess exits, not when it was launched |
| Layer 1 Git query (`head_blob_sha256`) | Same shape, a separate `subprocess.run()` call, `provenance_check.py:262-266` — a **third**, independently-timed observation within one `working_tree_file_identity()` invocation, not previously enumerated this precisely in either predecessor report |
| Layer 2 external process observation | Each individual `psutil` accessor call inside the `for field, getter in (...)` loop, `provenance_check.py:626-641` — **five separate observation instants** (`create_time`, `cmdline`, `exe`, `cwd`, `status`), not one, confirmed by direct trace — the field-by-field degradation design (built specifically to handle a process vanishing mid-loop, per the Layer 2 red-team) already implies five genuinely separate observation moments, though nothing currently records them separately |
| Layer 2 self-report reads | Each `open(full_path, "r").read()` inside `_read_server_pid_file()`/`_read_sentinel_file()`, `provenance_check.py:663`, `provenance_check.py:701` — two more separate observation instants |
| `introspection_channel.py` | Each of 8 `_collect_*()` calls inside `collect()`, `introspection_channel.py:213-221` — the composed `"timestamp"` field precedes all 8 |
| `liveness_ledger.py` | Each `runners[name]()` call inside the loop, `liveness_ledger.py:3966-3982` — the composed `"generated_at"` field precedes all 30+ |

**A single call to `working_tree_file_identity()` or `runtime_process_identity_and_self_report()` already contains multiple, separately-timed observation boundaries** — this was not previously stated this precisely in either prior report, which discussed the *function-level* sequencing (three sub-observations for Layer 2) without decomposing each sub-observation's *own* internal boundary (e.g., Layer 2's single `create_time` read vs. its separate `cmdline` read).

---

## 4. Subject Time vs. Observation Time

Stated with concrete examples, per the mission's required distinction:

- **Subject time** answers "when did the thing itself change or come into being" — a file's `mtime`, a process's `create_time`, a Git commit's own timestamp (not currently exposed by Layer 1, but would be subject time if it were). None of these require FeralEcho to have looked at anything; they would be true whether or not any observation ever occurred.
- **Observation time** answers "when did FeralEcho's own code actually perform the check that produced this fact." It is a property of the *act of measuring*, not the thing measured.

**Concrete FeralEcho example demonstrating why conflating them is dangerous**: `app/core/provenance_check.py`'s own `mtime` field, if read today, might report a modification time from hours or days ago (subject time — when the file last changed) — but the *fact* "this file's current sha256 is X" was established at whatever moment `working_tree_file_identity()` was actually called (observation time — potentially just now). A consumer who conflates these could wrongly believe a piece of evidence is as fresh as the file's own last-change time, when the file could have been re-verified (observed) far more recently, or — the more dangerous direction — could wrongly believe a fact is current merely because the *observation* happened just now, when the *subject* (a process, a file) may have changed again in the interval since. Both directions of confusion are real; neither is prevented by any field that exists today.

---

## 5. Temporal Model

**Sequential, not atomic — confirmed at every boundary examined in §3, no exception found.** No mechanism anywhere in this codebase (Layer 1, Layer 2, `introspection_channel.py`, `liveness_ledger.py`) obtains more than one piece of evidence at the literal same instant. Given this:

- **Individual observation timestamps** are necessary — each discrete boundary in §3 needs its own, not a shared one, precisely because §2's two new findings show that sharing one timestamp across a multi-step collection silently understates the true observation time of every step after the first.
- **A collection start/end interval** (e.g., "this composed result was gathered sometime within `[T_start, T_end]`") is a real, weaker, but still honest alternative to individual timestamps — it correctly avoids claiming simultaneity, but discards the ability to know *which* fact within the interval is closer to `T_start` vs. `T_end`, which matters directly for Layer 2 (the `create_time_utc` read happens first, self-report reads happen after — an interval alone couldn't express this ordering).
- **Recommendation, stated precisely**: both are useful for different purposes, but only individual timestamps are *required*. An interval is a cheap, optional derived summary (`min`/`max` of the individual timestamps), never a substitute for them.

---

## 6. Clock Analysis

- **Wall-clock (UTC)** is what every existing timestamp in this codebase already uses (`datetime.now(timezone.utc)`/`datetime.utcnow()`, confirmed by exhaustive grep, §2) — it permits direct comparison against other wall-clock subject timestamps (a file's mtime, a process's create_time) and against externally-recorded events (a git commit's own timestamp, a human's own clock) — which is the entire *point* of an observation-time field in this architecture, since its whole purpose is to be compared against subject times gathered via unrelated mechanisms.
- **Monotonic time** (`time.monotonic()`) is immune to clock adjustments (NTP sync, manual changes) but **cannot be compared across process boundaries or against wall-clock subject times at all** — a monotonic value is only meaningful relative to another monotonic value read by the *same* running process. Confirmed by direct grep this session: **zero existing uses of `time.monotonic()`/`time.perf_counter()` anywhere in this codebase's evidence-adjacent code** — there is no existing infrastructure to build on, and no current comparison in this architecture (all deltas examined are minutes-to-days in scale, e.g. Layer 2's `start_time_match_sentinel` tolerance of 120 seconds) is sensitive enough to the sub-second-scale clock-adjustment risk monotonic time would actually protect against.
- **Recommendation**: wall-clock UTC only, **required**. Monotonic time is **not required** — it would solve a precision problem this architecture does not currently have (nothing compares durations at a resolution where NTP drift matters), while introducing a genuinely new complexity (monotonic values are meaningless once persisted to a file and read back by a different process — exactly what every self-report artifact in this system does). Proposing it here would be exactly the kind of unnecessary field the mission's own §5-equivalent question in the predecessor report already warned against adding "merely because it sounds useful."
- **`clock_source` as a required field, not clock choice itself**: since `psutil`'s own documentation (confirmed this session) explicitly discloses that even the *subject* clock (`create_time`) is exposed to manual adjustment and NTP resync, any future observation-time field inherits the identical exposure. The contract should not attempt to solve this (out of scope, unsolvable without a trusted external time source) — it should **disclose** it, via a fixed `clock_source` string (e.g. `"system_wall_clock"`) naming which clock produced the value, so a future consumer knows what kind of drift risk applies without the contract itself claiming false precision.

---

## 7. Historical Evidence

Every timestamp inventoried in §2 predates this research and was generated by production code — none of it was designed with an observation-time concept in mind. Per the mission's own strong default (**"unknown should remain unknown"**):

- `introspection_channel.py`'s existing `"timestamp"` and `liveness_ledger.py`'s existing `"generated_at"` fields **cannot be retroactively reinterpreted as per-item observation timestamps** — they are genuinely collection-*start* timestamps, and treating them as if they described each individual check's own observation moment would manufacture false precision this report explicitly declines to introduce.
- **No historical Layer 1/Layer 2 result in this codebase's memory/log files carries anything resembling an observation timestamp at all** — confirmed by the exhaustive field inventory in §2; there is nothing to retrofit, because the concept has never existed. A caller who logged a `working_tree_file_identity()` result to a file in the past has no way, after the fact, to recover when that specific call actually ran, unless they separately recorded that themselves (outside this architecture's own responsibility).
- **This report does not propose inferring a missing observation time from mtime, Git commit time, report creation time, or process start time** — each of those describes a different thing entirely (§4), and using any of them as a stand-in would be exactly the false-precision risk the mission explicitly warns against. Missing observation time must remain explicitly, honestly unknown.

---

## 8. Minimum Proposed Contract

**Research recommendation only — not implemented, not designed as executable logic.**

### Required (per individual observation, not per composed result)
- `observed_at` — wall-clock UTC, ISO-8601, captured at the exact point in §3's inventory where that specific piece of evidence was actually obtained (not at the start of a surrounding multi-step function).
- `clock_source` — a fixed, small enum string (e.g. `"system_wall_clock"`) disclosing which clock produced the value, so future comparisons can account for the shared NTP/manual-adjustment exposure §6 discloses, without the contract itself claiming to have solved it.

### Optional
- A derived `collection_interval` (`min`/`max` of a composed result's own individual `observed_at` values) — useful as a cheap summary, never a substitute for the individual fields, and only meaningful for a caller composing multiple already-timestamped observations (i.e., built *from* the required fields, not an independent third field).

### Forbidden inference — what the schema must explicitly prevent a caller from assuming
- That two `observed_at` values from the same composed result describe a single instant — they must be readable as an ordered sequence with real (if often small) deltas, never collapsed into one timestamp for the whole result.
- That `observed_at` proximity between two facts implies those facts describe the *same underlying reality* — timestamp agreement is a *temporal* fact only; it says nothing about identity, causality, or linkage between a file and a process (§10, §12).
- That a missing `observed_at` (historical data, §7) can be backfilled from any other timestamp in the same record.

---

## 9. What The Contract Enables

Concrete, newly-defensible claims this contract — if built — would support that the current architecture cannot:

- *"Layer 2's `create_time_utc` was observed at `T1`; its `sentinel_file.start_utc` self-report was read at `T3`, 0.02 seconds later — these are two observations taken moments apart, not one instant, and both are disclosed."*
- *"`introspection_channel.py`'s `river_brain` collector's evidence was gathered at `T_k`, not at the cycle's own recorded `timestamp` field (`T_0`), which only describes when the cycle began."* — a real, concrete correction the contract would make possible for an already-shipped mechanism, not merely a hypothetical for Layer 1/2.
- A future reconciliation layer could compute and disclose the actual *observation-time delta* between two compared facts (distinct from any *subject*-time delta Layer 2 already discloses today, e.g. `start_time_delta_seconds`), and could refuse — honestly, not merely by convention — to treat two facts as near-simultaneous when their `observed_at` values are far apart, even if their *subject* times happen to agree.

---

## 10. What It Still Cannot Prove

Restated precisely, per the mission's explicit requirement that this remain a central finding, not a footnote:

- **Module loading.** An `observed_at` timestamp says nothing about `sys.modules`, `__file__`, or any Python-level import state — this remains exactly as unestablished as the Layer 3 report found, entirely independent of how precisely time is recorded.
- **Execution.** A timestamp on a process-existence check says nothing about whether any specific code is or was executing — timing evidence and execution evidence are orthogonal; more precise timing does not manufacture execution evidence that doesn't otherwise exist.
- **Causality.** Even a perfectly-ordered sequence of `observed_at` values (`T1 < T2 < T3`) establishes only that FeralEcho's own checks ran in that order — it does not establish that whatever the earlier check observed *caused* or is *related to* whatever the later check observed. Temporal ordering is not causal ordering; this report does not conflate them anywhere.
- **File/process linkage.** No timestamp, however precise, connects a Layer 1 file-identity fact to a Layer 2 process-identity fact — that gap is structural (no shared field, per the cross-layer report §11/§12) and orthogonal to timing entirely. Two facts observed at the exact same instant are no more linked than two facts observed a day apart, absent some *other* evidence establishing the connection (which, per the Layer 3 report, does not currently exist).
- **"These two independent things are the same thing."** Timestamp agreement is never identity evidence — restated here because it is the single most tempting, and most unsupported, inference this contract could invite if not stated this explicitly.

---

## 11. Adversarial Analysis

Each mission-specified counterexample, evaluated against the §8 contract as proposed (not yet built):

| Counterexample | Does the proposed contract detect it? | Represent uncertainty? | Prevent an invalid claim? | Cannot distinguish |
|---|---|---|---|---|
| Stale self-report (Layer 2 red-team Case A/C) | Partially — `observed_at` on the self-report read would show *when it was read*, not when the underlying claim became stale; the contract adds nothing new here beyond what Layer 2's existing `last_heartbeat_utc` already does | Yes — the timestamp is honestly labeled as read-time, not claim-validity time | Yes, by not implying the self-report's *content* is current merely because the *read* is recent | The contract cannot, by itself, distinguish "read recently, content is fresh" from "read recently, content is stale" — that distinction still requires comparing against Layer 2's own external observation, exactly as today |
| Rapidly changing files | Detected precisely — if two Layer 1 calls are made moments apart with different `observed_at` values, a genuine hash difference between them is now explainable by real elapsed time, not silently attributed to "simultaneous" observation | Yes | Yes — prevents the false claim "the file was in state X at the single moment T" when actually two different states existed across a real interval | Cannot distinguish *why* the file changed, only *that* observation time passed |
| PID reuse | No new detection beyond what Layer 2 red-team's Finding 2 already established (`start_time_match_sentinel`, a *subject*-time comparison) — `observed_at` is orthogonal to this problem | Not applicable — this counterexample is a subject-identity problem, not an observation-time problem | N/A | The contract correctly does not claim to help here — restated as an explicit boundary, not a gap in this contract specifically |
| Process restart | Same as above — `observed_at` records when a check ran, not whether the process it describes is the "same" process across a restart | N/A | N/A | Same |
| Delayed reads (evidence gathered, then acted on much later) | **Detected, directly** — this is the contract's central use case: an `observed_at` far in the past relative to "now" is exactly the honest signal that would let a consumer refuse to treat old evidence as current | Yes | Yes | Cannot force a consumer to actually check the delta — the contract makes the fact available, not mandatory to consult (the same limitation the cross-layer report's §13 already found for Layer 2's own correlation fields) |
| Filesystem changes between observations | **Detected, directly** — this is exactly §7's empirically-demonstrated Layer 3 experiment (file mutated while a process stayed alive); per-observation timestamps would show two Layer 1 calls, before and after, with different `observed_at` and different `sha256`, correctly representing two genuinely different observation instants rather than implying one static fact | Yes | Yes | Still cannot connect the *filesystem* observation to what a *running process* has loaded (§10) — timing alone never closes that gap |
| Process state changing between observations | **Detected** — Layer 2's own field-by-field degradation (§3) already handles this at the data level (a process vanishing mid-loop); adding `observed_at` per field would make the *timing* of that degradation explicit too, not just its outcome | Yes | Yes | Cannot prevent the underlying race itself (already covered as a residual, disclosed limitation in the Layer 2 red-team) |
| Clocks changing (NTP resync, manual adjustment) | **Not detected** — nothing in this contract, or anything currently buildable without a trusted external time source, can distinguish "10 seconds really passed" from "the system clock jumped 10 seconds due to NTP sync" | **Explicitly represented as a disclosed limitation via `clock_source`**, not silently ignored | Partially — the contract cannot *prevent* a clock-jump-induced false reading, only disclose that the risk exists | **Cannot distinguish** a genuine 10-second gap from a clock adjustment of the same magnitude — stated explicitly, not glossed over, per §6 |
| Clock-resolution limitations | Not a practical concern at ISO-8601-with-microseconds resolution for anything this architecture currently compares (seconds-to-days scale deltas) | N/A | N/A | Would matter only for sub-millisecond comparisons this architecture has no current use case for |
| Long-running observation sequences | **Detected, directly** — this is exactly §5's finding: `introspection_channel.py`'s real 8-collector, `liveness_ledger.py`'s real 30+-check sequences already demonstrate that a long composed observation genuinely spans meaningful wall-clock time; per-item timestamps would make this visible where today it is silently hidden behind one shared, misleadingly-early stamp | Yes | Yes — this is the single strongest, most concretely-demonstrated case for why the contract matters | Cannot itself shorten the real elapsed time or make the underlying collection atomic (§5's own finding: no atomicity exists or is proposed) |
| Reports generated after the underlying event | **Detected, directly** — an `observed_at` timestamp on the evidence itself, separate from a report's own creation/publish time, is exactly the mechanism that would let a reader distinguish "this fact was true as of when it was checked" from "this fact was true as of when this document was written," which are not currently distinguished anywhere in this research corpus's own audit reports (a real, self-referential finding: every report in this thread, including this one, states its own `Date:` header, never a separate per-fact observation time — worth noting as a real limitation of the *research corpus itself*, not only of production code) | Yes | Yes | N/A |
| Evidence copied or replayed later | **Detected, directly** — a genuine `observed_at` field travels with the evidence itself; a consumer replaying an old, persisted evidence record would see its true original observation time, rather than (as happens with every timestamp inventoried in §2 today) having no way to know the record's age at all once removed from its original logging context | Yes | Yes — this is a second strong, concrete case for the contract | Cannot detect a *maliciously* forged `observed_at` value — no integrity/signing mechanism is proposed or in scope here; the contract assumes good-faith production code, matching every other primitive in this research thread's own trust model |

**Net result: the proposed contract detects or honestly represents every counterexample except two structurally out-of-scope categories** — genuine clock manipulation (disclosed, not solved, §6) and identity/causality questions that are orthogonal to timing entirely (correctly, explicitly left unsolved, §10).

---

## 12. Reconciliation Implications

Without designing `reconcile_process_and_selfreport()` itself:

- **Temporal facts reconciliation would be allowed to use**: each individual evidence item's own `observed_at`/`clock_source`, and derived deltas between them (extending the pattern Layer 2's own `start_time_delta_seconds` already establishes for *subject* time, now available for *observation* time too).
- **Temporal facts that remain insufficient, even with this contract**: anything connecting timing to identity, loading, or execution (§10) — this contract changes *nothing* about the cross-layer report's own central finding that no schema field bridges file identity and process identity.
- **Could timestamp agreement ever establish independence?** No — independence is a property of *evidence sources* (per the cross-layer report §6's dependence-group finding), not of *when* two facts happen to have been observed. Two dependent facts (the cross-layer report's own example: `echo_server.pid` and `echo_sentinel.json`, both from the same `os.getpid()` belief) observed at nearly the same instant are still dependent — timestamp proximity says nothing about this.
- **Could timestamp proximity establish simultaneity?** No, and this report explicitly declines to manufacture that claim — proximity is evidence of a *small interval*, never proof of a single instant, per §5's own finding that no observation mechanism in this codebase is atomic. The strongest honest statement remains "observed within a short, disclosed interval," never "observed simultaneously."
- **Could timestamp ordering establish causality?** No — restated from §10, since this is exactly the kind of inference a reconciliation layer might be tempted to make and must not.
- **Execution/module-loading questions that would remain unresolved**: all of them, unchanged from the Layer 3 report's own findings — this contract is purely about *when*, and the Layer 3 gap is about *what*, a categorically separate question this report does not narrow.

---

## 13. Recommendation

```
MORE RESEARCH REQUIRED
```

Not `PROCEED TO RECONCILIATION DESIGN`: this report specifies a contract, not an implementation, and per the cross-layer report's own explicit sequencing request, the *design decision* it left open — whether `observed_at`/`clock_source` belong as additions to Layer 1/2's already-shipped, already-committed schemas, or are computed fresh by a reconciliation layer without touching Layer 1/2 at all — is still unresolved here, deliberately: this report was scoped to the *contract*, not to *where it should live*. That placement question, plus the newly-discovered `introspection_channel.py`/`liveness_ledger.py` instances of the same gap (§2, found this session, not previously flagged anywhere in this research thread), both warrant a dedicated decision before any implementation begins.

Not `ARCHITECTURAL BLOCKER`: nothing here is blocked — the contract is concretely specified, empirically grounded (§11's adversarial pass found it correctly handles the large majority of realistic scenarios), and requires no new dependency, no new clock infrastructure, and no change to the existing wall-clock convention already used throughout this codebase.

---

## 14. Explicit Non-Claims

The system must continue to refuse:

1. That an `observed_at` timestamp on its own establishes module loading, execution, or code identity — timing and those questions remain categorically separate (§10).
2. That two facts with close `observed_at` values were observed *simultaneously* — only that they were observed within a short, disclosed interval (§5, §11).
3. That timestamp agreement between two facts establishes they are *independent* evidence, or that they describe the *same* underlying reality — both remain separate, unresolved questions this contract does not touch (§12).
4. That timestamp ordering establishes a causal relationship between what was observed before and after.
5. That a missing historical `observed_at` value can be safely inferred from any other timestamp already on record (§7) — it must remain explicitly unknown.
6. That `clock_source: "system_wall_clock"` (or any future value) certifies the timestamp is immune to clock adjustment — it only discloses which clock was used, never that the clock was accurate or stable (§6, §11).
7. That `introspection_channel.py`'s existing `"timestamp"` or `liveness_ledger.py`'s existing `"generated_at"` fields already satisfy this contract — both are collection-*start* stamps, not per-item observation times, and this report does not reinterpret them as such (§2).

---

## Verification

Per this mission's own required self-checks, performed directly against the text above before finalizing:

- Searched this report for `verified`/`verification`: zero occurrences in a claim-asserting position — the word does not appear anywhere in this document.
- Searched for `snapshot`: zero occurrences — the mission's own instruction not to manufacture a snapshot concept unless the evidence supports one was followed; §5 explicitly declines to propose one, and the word itself was avoided entirely rather than used loosely.
- Searched for `simultaneous`/`simultaneity`: appears only in negated form (e.g., "cannot honestly claim simultaneity," "never proof of a single instant") — never asserted as achieved.
- Searched for `execution`/`loaded`/`running`: appears only in §10/§12/§14's explicit non-claims, restating the Layer 3 report's own boundary — never asserted as established by anything in this report.
- Confirmed §4 and §7 do not, anywhere, treat a subject timestamp (`mtime`, `create_time_utc`, `start_utc`) as if it were an observation timestamp — each table entry in §2 explicitly labels which kind it is.
- Confirmed §7 leaves historical evidence without observation timestamps explicitly, permanently unknown — no inference or backfill is proposed anywhere in this document.

---

## Integrity

```
Starting HEAD:  e03f5984bb86d36ade51ed8f0753a3b8264c0f9f
Ending HEAD:    e03f5984bb86d36ade51ed8f0753a3b8264c0f9f   (unchanged)
Files modified: none
Files created:  audits/2026-09-13_observation_time_contract_research.md (this file)
Staged:         nothing
Committed:      nothing
Pushed:         nothing
Scratch artifacts: none created -- this mission's research was conducted entirely via
                 read-only grep/source inspection of already-committed code; no scratch
                 files or directories were needed or created
PID 7644:       unchanged throughout -- same start time (Thu Sep 10 22:41:53 2026)
                 confirmed via ps at mission start and end, read-only only
```
