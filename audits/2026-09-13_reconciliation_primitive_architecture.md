# Reconciliation Primitive Architecture

**Date:** 2026-09-13
**Type:** Read-only architectural specification. No reconciliation function, class, schema, validator, or test implemented. No production file modified. PID 7644 inspected read-only only (`ps`, and one live, read-only call to the already-committed `runtime_process_identity_and_self_report()` against the real PID, to confirm the exact current output schema this design must work against).
**Predecessors, treated as authoritative**: `audits/2026-09-13_cross_layer_reconciliation_boundary.md`, `audits/2026-09-13_observation_time_contract_research.md`, `audits/2026-09-13_observation_time_placement_architecture.md`, `audits/2026-09-13_observation_time_enforcement_research.md`.

---

## Executive Conclusion

**`reconcile_process_and_selfreport(layer2_result: dict) -> dict` is the correct abstraction, confirmed by direct design attack, not assumed — but the exact current live schema (verified this session against real PID 7644) contains no observation-time fields at all**, meaning this primitive's temporal reasoning is, today, necessarily restricted to *subject*-time comparison (`create_time_utc` vs. `start_utc`) — exactly what Layer 2's existing `correlation.start_time_match_sentinel` already computes — and must degrade honestly to `UNKNOWN` for any *observation*-time relationship until the enforcement-research report's own still-unresolved placement work lands. The primitive must model Layer 2's two self-report artifacts as **one dependence group, not two independent witnesses** (§3, §11) — a structural requirement, not a stylistic preference, since both ultimately derive from the same process's own `os.getpid()` belief. It must never claim more than two witnesses (one independent, one dependent group) can support, must expose a witness-vs-independent-count distinction the caller cannot accidentally miscompute, and must remain structurally incapable of producing any statement about file identity, module loading, or execution — confirmed by direct attack using `app/core/self_heal.py` as the adversarial test case (§17), which the design survives by construction, not by discipline. **Verdict: `READY FOR IMPLEMENTATION DESIGN`** (§19) — the contract specified here is precise enough for a subsequent, separate implementation mission to build directly from, with one explicitly named area (whether/how future observation-time fields extend the schema) correctly deferred rather than glossed over.

---

## 1. Starting State

```
HEAD (verified fresh): e03f5984bb86d36ade51ed8f0753a3b8264c0f9f
git status --porcelain=v1 | wc -l: 107
```
Matches the exact end-state of the enforcement-research report — no discrepancy. All four predecessor reports treated as authoritative and re-cited, not re-derived, throughout. PID 7644 confirmed present, `Thu Sep 10 22:41:53 2026`, via `ps`. One additional read-only check performed: a live call to the already-committed `runtime_process_identity_and_self_report(7644)` to confirm the *exact current* production schema (reproduced below, §2) — this is not a new evidence-gathering mechanism, it is inspection of an already-shipped, already-red-teamed primitive's real output, needed because this mission must design against reality, not an idealized future schema.

**Baseline confirmed exactly as stated in the mission brief**: observation time producer-owned (unimplemented); structural enforcement possible, not yet built; semantic observation correctness not mechanically provable; reconciliation not implemented; execution/module-loading inference prohibited.

---

## 2. Reconciliation Target

**Exact current Layer 2 output, live, real PID 7644, this session:**
```json
{
  "pid": 7644, "in_scope": true, "error": null,
  "external_process": {
    "exists": true, "create_time_utc": "2026-09-11T05:41:53.357916+00:00",
    "cmdline": ["python", "-u", "run.py"],
    "executable": "/Users/.../feral_echo/bin/python3.12",
    "cwd": "/Users/richietate/Desktop/FeralEcho", "status": "running",
    "access_denied": false, "error": null
  },
  "runtime_self_report": {
    "server_pid_file": {"path": "memory/echo_server.pid", "exists": true,
       "readable": true, "malformed": false, "pid": 7644, "error": null},
    "sentinel_file": {"path": "memory/echo_sentinel.json", "exists": true,
       "readable": true, "malformed": false, "stage": "serving", "pid": 7644,
       "start_utc": "2026-09-11T05:41:57.788028Z",
       "last_heartbeat_utc": "2026-09-13T13:42:09.345326Z",
       "uptime_s": 201612, "error": null}
  },
  "correlation": {
    "pid_match_server_file": true, "pid_match_sentinel": true,
    "start_time_match_sentinel": true, "start_time_delta_seconds": 4.430112
  }
}
```
**No `observed_at`/`clock_source` field exists anywhere in this real, live output** — confirmed directly, not assumed. This is the actual shape reconciliation must work against today.

**Legitimate reconciliation relationships, determined by asking "does a shared field genuinely connect these two facts" — not assumed from field proximity:**

| Candidate relationship | Legitimate? | Why |
|---|---|---|
| `external_process`'s PID (the queried `pid` itself, confirmed to exist) ↔ `runtime_self_report.server_pid_file.pid` | **Yes** | Both are claims about the identical, well-defined quantity (an integer PID), from genuinely different code paths |
| `external_process`'s PID ↔ `runtime_self_report.sentinel_file.pid` | **Yes**, same reasoning | |
| `external_process.create_time_utc` ↔ `runtime_self_report.sentinel_file.start_utc` | **Yes, as a *subject*-time comparison only** — already what `correlation.start_time_match_sentinel` computes | Both describe, imperfectly, "when did this process begin" |
| `runtime_self_report.server_pid_file.pid` ↔ `runtime_self_report.sentinel_file.pid` | **Legitimate as a relationship, but NOT as independent corroboration** — see §3/§11 | Both derive from the same process's own self-belief |
| Any Layer 2 field ↔ any Layer 1 (file/Git) field | **Not legitimate — no shared field exists** | Confirmed structurally in the cross-layer report §11/§12; restated and re-attacked in §12/§17 below |
| Any current field ↔ "which code is executing" | **Not legitimate at all** | No field in this schema, or any schema this research thread has examined, carries this information (Layer 3 report) |

---

## 3. Evidence Witnesses and Dependence

Three named witnesses, precisely:

- **W1 = `external_process`** — genuinely independent: `psutil`, querying the OS process table directly, zero cooperation from the target process.
- **W2 = `runtime_self_report.server_pid_file`** — self-report, written by `run.py:1577`'s `_SERVER_PID_FILE.write_text(str(os.getpid()))`.
- **W3 = `runtime_self_report.sentinel_file`** — self-report, its `pid` field written by `run.py:1119`'s `_write_sentinel()`, a **separate call site**, but to the identical `os.getpid()` mechanism.

**W2 and W3 are not independent of each other**, confirmed by direct source trace in the placement-architecture report (§6 there): both ultimately express the same process's own, trivially-self-consistent belief about its own PID. Two files, two functions, two write timestamps — one underlying fact-source. **This design therefore defines a `dependence_group` concept as a required, not optional, part of the reconciliation output**: `{"independent_witnesses": ["W1"], "dependent_groups": [["W2", "W3"]]}`, computed once, statically, from knowledge of Layer 2's own real architecture (this is a fact about the *producer*, not derivable from the *data* — reconciliation must know this a priori, the same way `_compose_correlation()` already knows a priori which fields to compare). **A count of "how many witnesses agree" must never be computed as a flat sum across W1/W2/W3** — the maximum genuine corroboration available from Layer 2's current architecture is **two** (one independent, one dependent-group), never three, regardless of how many individual fields happen to agree.

---

## 4. Relationship Vocabulary

`AGREE`/`DISAGREE`/`ONE_SIDED`/`NEITHER` (proposed in the cross-layer report) **are sufficient for pairwise value comparisons and are retained, with each state's meaning tightened precisely**:

- **`AGREE`** — both compared values are present and equal (PID) or within the established, disclosed tolerance (start-time, ±120s per Layer 2's existing constant). **Means exactly**: "the compared observations report the same relationship." **Does NOT mean**: "verified," "confirmed," or anything about which underlying reality produced the agreement (§10's dependence attack shows two dependent witnesses can trivially `AGREE` while both being equally wrong).
- **`DISAGREE`** — both values present, and they differ beyond tolerance. **Means**: a real, informative contradiction exists in the available evidence. **Does NOT mean**: which side, if either, is "correct" — no field in this schema carries independent ground truth to arbitrate a disagreement.
- **`ONE_SIDED`** — exactly one of the two compared values is present (`None`/missing on the other side). **Means**: the comparison could not be made for lack of one side's evidence. **Does NOT mean**: the missing side is false — per the observation-time contract research's own §9 finding, absence is not negation.
- **`NEITHER`** — both values absent. **Means**: no evidence available for this specific relationship at all.

**No fifth state is introduced for the W2-vs-W3 dependent-group comparison** — its relationship is still computed as `AGREE`/`DISAGREE`/etc. using the identical vocabulary, but every relationship record carries which witnesses were compared (§3), so a consumer (or, more precisely, the design's own aggregate-computing logic, §11) can distinguish an `AGREE` between W1/W2 from an `AGREE` between W2/W3 by inspecting witness identity, not by inventing parallel terminology for what is structurally the same underlying comparison operation.

---

## 5. Epistemic Vocabulary

Evaluated against the mission's proposed `I_HAVE_EVIDENCE`/`UNKNOWN`/`CONFLICTING`, and reconciled with the observation-time contract research's own separately-derived four-state vocabulary (`UNKNOWN`/`FALSE`/`CONFLICTING`/`UNSUPPORTED_BY_AVAILABLE_EVIDENCE`) — **these describe different levels and must not be merged into one flat enum**:

- At the **individual relationship level**, §4's four states already *are* the epistemic vocabulary — `AGREE`/`DISAGREE` both mean "evidence exists" (agreeing or conflicting, respectively); `ONE_SIDED`/`NEITHER` both mean "insufficient evidence" (partially or fully). **No separate per-relationship epistemic field is needed** — it would be redundant with, and risk drifting from, the relationship state itself.
- At the **whole-result level**, a single **derived** (never independently asserted) summary is warranted, computed mechanically from the set of relationship results: `EVIDENCE_AGREES` (at least one `AGREE`, zero `DISAGREE`), `EVIDENCE_CONFLICTS` (at least one `DISAGREE`, regardless of how many `AGREE`), `INSUFFICIENT_EVIDENCE` (no relationship reached `AGREE` or `DISAGREE` — every one is `ONE_SIDED`/`NEITHER`). **The critical design rule, satisfying the mission's own central requirement**: `INSUFFICIENT_EVIDENCE` and "absence of `EVIDENCE_CONFLICTS`" are not the same claim, and the output schema must never let a caller read "not conflicting" as "agrees" — this is why the summary is a genuine three-way classification, not a boolean `conflicts: bool` a caller could invert into a false "no conflicts = fine" reading.

---

## 6. Entire-Input Requirement

Directly extends the cross-layer report's own §13 finding (a constrained signature is the one mechanism proven to prevent the demonstrated cherry-picking hazard). The mission's own attack scenario — a caller selecting only PID fields, observing agreement, ignoring a contradictory timestamp — is **prevented by construction if and only if the function (a) requires the whole `layer2_result` dict as its single argument, never individual field arguments, and (b) internally computes and returns *every* relationship it knows how to compute, never a caller-selected subset of relationships.** Both are required; (a) alone is insufficient, because a caller could still call the function correctly and then read only part of *its* output (§15 names this residual risk explicitly, not glossed over).

**Distinguishing "not present" from "not considered," precisely**: the function must (1) compute a relationship result (possibly `ONE_SIDED`/`NEITHER`) for every relationship in §2's legitimate list, regardless of whether the underlying data is present — this is what makes missing evidence *visible* rather than silently absent from the output; and (2) separately record any **unrecognized** top-level or nested key present in the input that the function's own known-relationship list does not cover, under a dedicated `unrecognized_input_fields` list — this handles graceful forward-compatibility (a future Layer 2 schema change, e.g. the eventual addition of observation-time fields) without either silently ignoring new evidence or crashing on it. **The function must not silently succeed while ignoring recognized-but-absent evidence, and must not silently succeed while ignoring genuinely new, not-yet-understood evidence** — these are two different honesty requirements, both real, both testable independently.

---

## 7. Temporal Semantics

**Permitted, today, against the real current schema (§2)**:
- "These were observed at different points in time" — cannot currently be stated with precision, since no observation-time field exists; can only be stated as a general architectural fact (per the placement-architecture report's own §5) that Layer 2's internal collection is sequential, not as a per-call, data-backed claim.
- "The reported start time is consistent/inconsistent with the OS-observed creation time, within a disclosed tolerance" — **already computable today**, exactly what `correlation.start_time_match_sentinel` already provides; reconciliation's own relationship for this is a direct pass-through/re-expression of that existing field, not a new computation.

**Forbidden, unconditionally, regardless of future schema changes**: "timestamps close → same process" (§8, PID reuse directly disproves this); "timestamps close → same code was executing" (no timestamp of any kind, subject or observation, carries information about code execution — Layer 3 report, unchanged by anything in this design).

**Explicitly deferred, not solved here**: once/if the enforcement-research report's own open placement question is resolved and `observed_at` fields are added to Layer 2's real schema, reconciliation could additionally compute an *observation*-time delta between W1's and W2/W3's respective observation moments — this design's output shape (§13) reserves a place for this (an optional, presently-always-`UNKNOWN` relationship) rather than requiring a future schema-breaking redesign, but does not specify its exact semantics now, since the underlying data does not yet exist to design against concretely.

---

## 8. PID Reuse

Modeled precisely, reusing the Layer 2 red-team's own already-proven mechanism (Finding 2 there), restated in this design's exact vocabulary: self-report claims `pid=X, start_utc=T_old` (stale); at query time, a genuinely different process now holds PID X, with `create_time_utc=T_new`, `T_new` far outside the 120s tolerance of `T_old`. **Result under this design**: the PID-comparison relationships (W1↔W2, W1↔W3) both report `AGREE` (bare integer equality — this is real, and this design does not hide it); the start-time relationship (W1↔W3) reports `DISAGREE`, with the raw delta disclosed. **The whole-result epistemic summary is `EVIDENCE_CONFLICTS`** (§5's rule: any single `DISAGREE` forces this, regardless of how many `AGREE`), which is the honest, correct classification — **PID equality alone never establishes persistent process identity**, and this design's aggregate logic is constructed specifically so that a single conflicting relationship cannot be outvoted by multiple agreeing ones from the same or a different comparison.

---

## 9. Stale Self-Report

**Case 1** (mission's own construction): self-report `pid=7644`, `start=T_old`; OS-observed `pid=7644`, `create_time=T_new≠T_old`. **Result**: identical to §8 — `EVIDENCE_CONFLICTS`, PID relationships `AGREE`, start-time relationship `DISAGREE`.

**Case 2**: self-report `pid=7644`, `start=T_current`; OS-observed `pid=7644`, `create_time=T_current` (matching, real, live data — this is in fact exactly what §2's real PID 7644 data shows today). **Result**: all Layer 2 relationships `AGREE`; whole-result summary `EVIDENCE_AGREES`. **This must not, and under this design cannot, be upgraded into an execution claim** — the output schema (§13) has no field capable of expressing "and therefore code is executing," by construction, not by a documentation caveat alone (§12, §17).

---

## 10. Contradiction Handling

Each named combination gets its own, fully independent relationship record — **never collapsed into one verdict**, directly satisfying the mission's own requirement:

- PID agrees, start disagrees → two separate relationship records, `AGREE` and `DISAGREE` respectively, both visible; summary `EVIDENCE_CONFLICTS`.
- PID disagrees, start agrees → symmetric, same treatment; summary `EVIDENCE_CONFLICTS` (any disagreement forces this, regardless of which specific relationship it is).
- One source missing (e.g. `sentinel_file.exists: false`) → relationships involving that source become `ONE_SIDED`; relationships not involving it (e.g. W1 vs W2, if `server_pid_file` is still present) remain independently computable and unaffected.
- All compared evidence missing → every relationship `NEITHER`; summary `INSUFFICIENT_EVIDENCE`.

---

## 11. Dependence

**The crux of this design, addressed directly per the mission's own emphasis.** Constructed case: `server_pid_file.pid` (W2) and `sentinel_file.pid` (W3) both agree with each other and with `external_process`'s PID (W1) — three pairwise `AGREE` relationships are computable (W1-W2, W1-W3, W2-W3). **A naive count would read this as "3 agreements" — this design explicitly rejects that count as meaningless**, per §3's dependence-group declaration. The output's aggregate section (§13) exposes two, deliberately separate numbers: `agreeing_relationship_count` (a raw count of `AGREE` results, here 3 — disclosed, not hidden) and `independent_corroboration_count` (computed as: does W1 agree with *at least one* member of the dependent group — here, yes, so the count is **2**: one independent witness, one corroborating dependent group, never 3). **This design cannot express "three genuinely independent witnesses" as a distinct case from "one independent plus one dependent group,"** because Layer 2's real architecture, as it exists today, only ever produces one independent and one dependent-pair witness — there is no third, structurally different data source in the current schema. If a future Layer 2 revision ever added a second, genuinely independent process-observation mechanism (not proposed here), this design's `dependence_groups` declaration would need updating to reflect it — stated as a real, honest limitation of what the *current architecture* can support, not a flaw in this design's reasoning.

---

## 12. Layer 1 / Layer 2 Boundary

**Reconciliation, as scoped in this design, can say nothing about Layer 1 file identity, because its input (`layer2_result`) contains no Layer 1 field at all** — this is not a policy choice this design enforces through discipline, it is a structural fact about the function's own declared input type. The self_heal.py false-positive construction (mission's own exact framing): `Git identity correct + file exists + PID exists + self-report agrees + timestamps consistent = ?` **Under this design, the answer is precisely, and only**: `{"pid_relationships": all AGREE, "temporal_relationships": AGREE, "epistemic_summary": "EVIDENCE_AGREES", "scope": "process identity only"}` — **the output has no field, at any level, that names a file, a module, or a loading/execution state**, because §2 establishes no such relationship is legitimate to compute from this input, and §13's output schema literally does not contain a slot for it. The design does not need a written rule saying "don't say the file is running" — it is architecturally incapable of producing that sentence, the same way `working_tree_file_identity()` is incapable of returning a PID.

---

## 13. Proposed Output Contract

*(Sketch of the shape only — no code.)*

```
{
  "input_summary": {"pid_queried": <int>, "layer2_in_scope": <bool>},
  "witnesses": {
      "independent": ["external_process"],
      "dependent_groups": [["runtime_self_report.server_pid_file",
                              "runtime_self_report.sentinel_file"]]
  },
  "relationships": [
      {"subject": "pid", "compared": ["external_process", "server_pid_file"],
        "state": AGREE|DISAGREE|ONE_SIDED|NEITHER, "detail": {...raw values...}},
      {"subject": "pid", "compared": ["external_process", "sentinel_file"], ...},
      {"subject": "pid", "compared": ["server_pid_file", "sentinel_file"], ...},
      {"subject": "start_time", "compared": ["external_process", "sentinel_file"],
        "state": ..., "detail": {"delta_seconds": ..., "tolerance_seconds": 120}},
      {"subject": "observation_time", "compared": ["external_process", "sentinel_file"],
        "state": UNKNOWN_NO_FIELD  -- reserved, always this today, per §7}
  ],
  "aggregate": {
      "agreeing_relationship_count": <int>,
      "independent_corroboration_count": <int, per §11's rule, never a flat sum>,
      "epistemic_summary": EVIDENCE_AGREES|EVIDENCE_CONFLICTS|INSUFFICIENT_EVIDENCE
  },
  "unrecognized_input_fields": [<str>, ...],
  "scope_statement": "process identity evidence only -- establishes nothing about file
                       identity, module loading, or code execution"
}
```
**Deliberately absent, per the mission's explicit prohibition**: any field named/shaped like `verified`, `verification`, a boolean truth verdict, or a numeric confidence score. Every state is drawn from the fixed, small vocabularies in §4/§5, never a free-form string or a number implying precision the evidence doesn't support.

---

## 14. Purity and Side Effects

**The function must be pure — deterministic, no filesystem access, no process inspection, no network access, no new evidence gathering, no hidden side effects — and this is architecturally correct, not merely a nice-to-have.** Justification, direct: reconciliation's entire epistemic value depends on comparing evidence gathered *together, from one already-completed Layer 2 call* — if reconciliation were allowed to re-query the OS or re-read self-report files itself, it would introduce a *second*, un-synchronized observation moment, reintroducing exactly the sequential-observation skew problem the observation-time research exists to prevent, one level higher up. This mirrors, and is directly modeled on, the already-proven, already-shipped pattern of `_compose_correlation()` (Layer 2 itself) and `_compose_identity()` (Layer 1) — both zero-I/O, both directly unit-testable against synthetic inputs, both already established conventions in this exact codebase, not a new pattern invented for this mission.

---

## 15. Anti-Cherry-Picking Properties

The whole-`layer2_result`-input requirement (§6) prevents cherry-picking *at the evidence-selection stage* — a caller cannot exclude inconvenient input fields from consideration. **It does not, and cannot, prevent cherry-picking at the output-consumption stage** — a downstream consumer of reconciliation's *own* output could still, in principle, read only `aggregate.agreeing_relationship_count` while ignoring `aggregate.epistemic_summary`. This is a real, honestly-acknowledged residual risk, not solved by this design and not claimed to be solved — the same unresolved regress the cross-layer report's own §15 named for Layer 2's raw correlation fields, recurring one layer up. **The missing architectural guarantee, named precisely rather than glossed over**: nothing in Python's type system or this codebase's tooling (per the enforcement-research report's own findings) can force a caller to read an entire returned dict rather than a subset of its keys — this is the same category of limitation the enforcement research already established has no clean mechanical solution, restated here as it applies to reconciliation's own output rather than Layer 2's.

---

## 16. Adversarial Test Matrix

| # | Case | Relationship state(s) | Epistemic summary | Permissible conclusion | Prohibited conclusion |
|---|---|---|---|---|---|
| 1 | Both PID observations agree | `AGREE` (all PID pairs) | `EVIDENCE_AGREES` | "The queried PID matches what the process and its self-report both claim" | "The process is healthy/verified" |
| 2 | PID observations disagree | `DISAGREE` (relevant pair) | `EVIDENCE_CONFLICTS` | "A real, disclosed contradiction exists in PID identity" | Guessing which source is "right" |
| 3 | PID agrees, start disagrees | mixed, both shown | `EVIDENCE_CONFLICTS` | "PID identity agrees; temporal consistency does not — possible reuse or staleness" | "The process is the same one that started at the self-reported time" |
| 4 | PID disagrees, start agrees | mixed, both shown | `EVIDENCE_CONFLICTS` | Same posture, PID mismatch flagged | Treating start-time agreement as overriding the PID conflict |
| 5 | Self-report absent | `ONE_SIDED`/`NEITHER` for all self-report relationships | `INSUFFICIENT_EVIDENCE` (if no other relationship agrees/disagrees) | "No self-report evidence currently available" | Treating absence as evidence the process is not FeralEcho's |
| 6 | OS observation absent | Same shape, mirrored | Same | "External confirmation currently unavailable" | Treating self-report alone as sufficient corroboration |
| 7 | Both absent | `NEITHER` throughout | `INSUFFICIENT_EVIDENCE` | "No evidence available for this PID at this time" | Any positive or negative claim |
| 8 | PID reuse | `AGREE` (PID), `DISAGREE` (start-time) | `EVIDENCE_CONFLICTS` | Exactly §8's finding | "Same process across time" |
| 9 | Stale self-report | Same as 8 | `EVIDENCE_CONFLICTS` | Exactly §9 Case 1's finding | Treating the stale claim as current |
| 10 | Consistent self-report from dependent files | `AGREE` (W2-W3) | Contributes to `EVIDENCE_AGREES` only in combination with W1; alone insufficient for `independent_corroboration_count` beyond 1 | "The two self-report files are internally consistent" | "Two independent sources confirm this" |
| 11 | Genuine independent corroboration | `AGREE` (W1 vs. dependent group) | `EVIDENCE_AGREES`, `independent_corroboration_count: 2` | "One independent and one internally-consistent dependent source agree" | Any claim beyond process identity |
| 12 | Timestamp missing | `ONE_SIDED` for that relationship | Depends on other relationships | "Temporal comparison unavailable" | Assuming consistency by default |
| 13 | Timestamp malformed | `NEITHER` (per Layer 2's own existing degrade-to-`None` behavior on parse failure) | Depends on other relationships | "Temporal comparison could not be computed" | Silently treating malformed as absent-and-therefore-fine |
| 14 | Timestamp plausible but semantically wrong (e.g. derived from the wrong clock — per the enforcement research's own finding that this is undetectable) | `AGREE` or `DISAGREE`, computed normally — **the design cannot detect this case at all**, stated honestly | Whatever the raw comparison yields, potentially misleadingly `EVIDENCE_AGREES` | None beyond the literal comparison | Claiming this design can detect semantically-wrong-but-plausible timestamps — it explicitly cannot (enforcement research §7) |
| 15 | File matches Git but is dormant (`self_heal.py`) | **No relationship computed at all — Layer 1 evidence is not part of this function's input** | N/A to this primitive | Nothing — this primitive has no opinion on file state | Any statement connecting file state to process state |
| 16 | Everything agrees except file/process linkage unknown | All Layer 2 relationships `AGREE`; the file/process question is not merely `UNKNOWN`, it is **outside the input domain of this function entirely** | `EVIDENCE_AGREES` (process identity only) | "Process identity evidence agrees" | "Therefore [some file] is loaded" |
| 17 | All available evidence agrees | All `AGREE` | `EVIDENCE_AGREES` | The strongest honest statement this primitive can ever produce: "every computable process-identity relationship in the available evidence agrees" | "Verified," "confirmed," "the process is definitely Echo running correctly" |

---

## 17. False-Positive Attack

**Strongest construction, exactly per the mission's instruction**: real PID 7644, Layer 1 evidence (not part of this primitive's input, but included here to construct the full adversarial scenario a naive *consumer* might attempt) shows `app/core/self_heal.py` tracked, clean, hash-matched to HEAD; Layer 2 evidence (this primitive's actual input) shows every relationship in row 17 of §16's matrix — full agreement. **Does the design survive?** Yes, by construction: this primitive's own output (§13's schema) contains no field naming `self_heal.py` or any file at all — it is not merely that the design *declines* to make the execution claim, it is that **the claim has nowhere to be expressed** in the output type this function returns. A caller who wanted to construct the false claim "self_heal.py is running" would have to synthesize it themselves, entirely outside anything this function computed or returned — at which point the false claim is the caller's own fabrication, not something reconciliation produced or implied. **The design survives the attack.**

---

## 18. False-Negative Analysis

Legitimate cases producing a conservative `UNKNOWN`/`INSUFFICIENT_EVIDENCE`-shaped result rather than a stronger (and unsupported) positive one:

- **Every real query against the current live schema** (§2) necessarily reports the observation-time relationship (§7, §13) as unavailable — even though the *underlying reality* (Layer 2's collection genuinely happened moments apart, real, small, non-adversarial skew) is almost certainly benign, the design correctly refuses to assert anything about it until the field actually exists. This is a real, accepted cost of the conservative design, not fixed here by inventing a substitute inference — per the mission's own explicit instruction, an honest `UNKNOWN` is preferred to a manufactured positive.
- **A genuinely healthy process whose self-report artifact happens to be mid-write** (a real, if rare, race condition — Layer 2's `_read_sentinel_file()` already handles a torn/malformed read by returning `malformed: True` rather than crashing) would produce a `NEITHER`/`ONE_SIDED` relationship for that specific comparison, correctly conservative, even though the true underlying state is fine.
- **Not "fixed" by adding inference**: per the mission's own explicit instruction, none of these cases are resolved by loosening the design — each remains an honest `UNKNOWN`-shaped result, disclosed as a real limitation rather than smoothed over.

---

## 19. Implementation Readiness

```
READY FOR IMPLEMENTATION DESIGN
```

The contract specified in §2–§13 is precise enough for a subsequent, separate implementation mission to build directly from: exact input shape (§2, confirmed against real live data), exact witness/dependence model (§3, §11), exact relationship and epistemic vocabularies (§4, §5), exact output schema sketch (§13), exact purity requirement (§14), and an adversarial matrix (§16) plus a survived false-positive attack (§17) establishing the design's boundary holds under direct pressure. **One area is explicitly, correctly deferred rather than glossed over**: the exact future semantics of observation-time relationships (§7) cannot be fully specified today because the underlying schema field does not yet exist in production — this is not a gap in this design's reasoning, it is an honest acknowledgment that this specific sub-question depends on a separate, not-yet-resolved prior research thread (the enforcement-research report's own open placement question), and the output schema (§13) is deliberately shaped to accommodate that future addition without requiring a breaking redesign when it lands.

---

## 20. Explicit Non-Claims

1. That `AGREE` between W2 and W3 (the dependent self-report pair) constitutes independent corroboration — it does not, and the design's `independent_corroboration_count` field is specifically constructed to never conflate the two (§11).
2. That any output this primitive could produce establishes file identity, module loading, or code execution — no field in the proposed schema carries this information, by construction (§12, §17), not by convention.
3. That structural presence of a well-formed timestamp relationship implies the underlying timestamps were captured at the semantically correct observation boundary — restated directly from the enforcement-research report, unaffected by anything in this design (§7, §16 row 14).
4. That the whole-input requirement (§6) fully prevents cherry-picking — it prevents cherry-picking of *input* evidence only; cherry-picking of this primitive's own *output* remains a real, unsolved, explicitly disclosed residual risk (§15).
5. That `EVIDENCE_AGREES` means "verified" or "confirmed" in any stronger sense than "every computable relationship in the available evidence happened to agree" (§5, §16 row 17).
6. That this design constitutes an implementation-ready specification for anything beyond the single primitive scoped here — Layer 1 + Layer 2 joint reconciliation, if ever built, is explicitly a separate, later function, not folded into this one merely because it would be technically convenient to do so.

---

## Verification

Reviewed directly against this mission's own required term list:

- `verified`/`verification`: used only in negated or rejected contexts throughout (e.g., "must not be upgraded into an execution claim," "deliberately absent... any field named/shaped like `verified`").
- `running`/`executing`/`loaded`: appear only in explicit non-claims and adversarial-attack framing (§12, §16, §17, §20) — never asserted as an achieved output.
- `truth`/`confidence`: `truth` appears only in the negative framing "no field... carries independent ground truth to arbitrate a disagreement" (§4); no numeric confidence score appears anywhere in the proposed schema (§13), consistent with the mission's explicit prohibition.
- `agree`: used precisely per §4's tightened definition throughout — never presented as synonymous with `verified`.
- `evidence`/`unknown`/`conflicting`: used consistently with the vocabularies defined in §4/§5, never loosely.
- `observed_at`: appears only in §7/§13's explicit acknowledgment that this field does not currently exist in the real schema (§2) — never treated as already available.

---

## Integrity

```
Starting HEAD:  e03f5984bb86d36ade51ed8f0753a3b8264c0f9f
Ending HEAD:    e03f5984bb86d36ade51ed8f0753a3b8264c0f9f   (unchanged)
Files modified: none
Files created:  audits/2026-09-13_reconciliation_primitive_architecture.md (this file)
Staged:         nothing
Committed:      nothing
Pushed:         nothing
Scratch artifacts: none created -- one read-only, non-mutating call to the already-
                 committed runtime_process_identity_and_self_report(7644) to confirm
                 the real current schema (§2); no scratch files or directories
PID 7644:       unchanged throughout -- same start time (Thu Sep 10 22:41:53 2026)
                 confirmed via ps and via the one read-only evidence call, both
                 read-only only
```
