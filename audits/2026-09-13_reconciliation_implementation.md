# Reconciliation Primitive Implementation — `reconcile_process_and_selfreport()`

**Date:** 2026-09-13
**Type:** Implementation mission (not research)
**Status:** Complete. All verification passing. No commit made.

---

## 1. Scope

Implemented `reconcile_process_and_selfreport(layer2_result: dict) -> dict` in
`app/core/provenance_check.py`, exactly per the specification in
`audits/2026-09-13_reconciliation_implementation_design.md`, and extended
`scripts/verify_provenance_check.py` with a permanent, formal test suite
covering all 14 mission-specified categories plus an explicit
caller-cherry-picking test and the `self_heal.py` adversarial false-positive
case.

No epistemic redesign occurred. No STOP condition was triggered. The design
document's semantics were followed as authoritative throughout; the live
Layer 2 code (re-read directly this session, not inferred from the design
doc's own field-name claims) was treated as authoritative for exact current
schema shape, per the mission's own instruction. No contradiction between
the two was found.

---

## 2. Git integrity

| | |
|---|---|
| HEAD before mission | `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` |
| HEAD after mission | `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` (unchanged) |
| Files staged | none |
| Commit made | none |

Changed files (working tree, unstaged):

```
 M app/core/provenance_check.py
 M scripts/verify_provenance_check.py
```

Plus this one new file: `audits/2026-09-13_reconciliation_implementation.md`.
No other tracked file was touched. The large number of untracked `audits/*`
files visible in `git status` predate this mission (research reports from
2026-09-07 through 2026-09-13, already present before this session began) —
none were created or modified by this implementation pass.

---

## 3. PID 7644 integrity

```
  PID     ELAPSED STARTED                      COMM
 7644 02-08:52:15 Thu Sep 10 22:41:53 2026     python
```

Start time confirmed unchanged (`Thu Sep 10 22:41:53 2026`, matching the
value recorded before this mission began). PID 7644 was never signaled,
restarted, or touched by anything other than read-only `ps`/`psutil`
inspection (the same read-only observation Layer 2's own
`_external_process_observation()` performs, and which
`reconcile_process_and_selfreport()` itself never performs directly — see
§6).

---

## 4. Implementation summary

Added to `app/core/provenance_check.py`, after Layer 2's closing block:

- Constants: `RELATIONSHIP_AGREE`/`DISAGREE`/`ONE_SIDED`/`NEITHER`,
  `EPISTEMIC_EVIDENCE_AGREES`/`EVIDENCE_CONFLICTS`/`INSUFFICIENT_EVIDENCE`,
  `_WITNESS_INDEPENDENT`, `_WITNESS_DEPENDENT_GROUP`, `_WITNESS_MEMBERS`,
  `_SCOPE_STATEMENT`, and four `_RECOGNIZED_*_FIELDS` sets used for the
  `unrecognized_input_fields` disclosure.
- Helpers: `_compare_values(a, b, tolerance=None)` (pure relationship
  classifier) and `_independent_corroboration_count(relationships)`.
- `reconcile_process_and_selfreport(layer2_result) -> dict` — one positional
  argument, wrapped entirely in `try/except Exception` as a last-resort
  safety net (the function's own internal logic cannot itself raise on any
  malformed input, since every field access uses `.get()`/`or {}`
  defensively; the wrapper exists per spec as defense-in-depth, matching
  Layer 1/Layer 2's own established pattern).

### Exact output contract implemented

```
{
  "input_error": str | None,
  "witnesses": {
    "independent": ["os_process_observation"],
    "dependent_groups": {"process_self_report": ["server_pid_file", "sentinel_file"]},
  },
  "relationships": [ ... exactly 5 records, always ... ],
  "aggregate": {
    "raw_agreeing_relationship_count": int,
    "independent_corroboration_count": int,   # 0 or 1, never higher
    "epistemic_summary": "EVIDENCE_AGREES" | "EVIDENCE_CONFLICTS" | "INSUFFICIENT_EVIDENCE",
  },
  "unrecognized_input_fields": [str, ...],
  "scope_statement": <fixed string, verbatim on every call>,
}
```

The 5 relationships, in fixed order, always present regardless of input
completeness:

1. `pid`: `os_process_observation` vs `server_pid_file`
2. `pid`: `os_process_observation` vs `sentinel_file`
3. `pid`: `server_pid_file` vs `sentinel_file`
4. `start_time`: `os_process_observation` vs `sentinel_file` (reused from
   Layer 2's own `correlation.start_time_match_sentinel`, never recomputed)
5. `observation_time`: `os_process_observation` vs `sentinel_file` (always
   `NEITHER` — no `observed_at` field exists anywhere in the current live
   Layer 2 schema)

### Dependence treatment

`server_pid_file` and `sentinel_file` are hard-coded as one dependent group
(`_WITNESS_MEMBERS`), never caller-supplied.
`_independent_corroboration_count()` returns `1` the moment the independent
witness (`os_process_observation`) is found to `AGREE` with *any* member of
that group in a `pid`-subject relationship, and returns `0` otherwise —
never `2` or `3`, even when the independent witness agrees with *both*
dependent-group members and the two dependent-group members also agree with
each other (verified directly, Case recon-4b).

### Timestamp treatment

The `start_time` relationship reuses `correlation.start_time_match_sentinel`
and `correlation.start_time_delta_seconds` verbatim — it never independently
re-parses `external_process.create_time_utc` or
`runtime_self_report.sentinel_file.start_utc`. Verified directly (Case
recon-6) with deliberately inconsistent raw timestamps (5 hours apart) paired
with a `correlation` field that explicitly claims a match: the reconciliation
output reports `AGREE`, proving reuse rather than recomputation. This is the
same design as the disclosed limitation described in the code's own inline
comment (§5, below).

### Aggregate / "DISAGREE always wins"

`epistemic_summary` is `EVIDENCE_CONFLICTS` if any relationship is
`DISAGREE`, else `EVIDENCE_AGREES` if any relationship is `AGREE`, else
`INSUFFICIENT_EVIDENCE`. Explicitly re-verified for the PID-reuse case
(Case recon-5): 3 of 5 relationships `AGREE` (all PID relationships), one
`DISAGREE` (start_time), one `NEITHER` (observation_time) —
`epistemic_summary` correctly reads `EVIDENCE_CONFLICTS`, not
`EVIDENCE_AGREES`.

---

## 5. Deviations from the specification

Two deviations were made during implementation, both disclosed in the code
itself (module-level comment and an inline comment at the relevant
relationship), and both reported here as instructed:

1. **`os_process_observation`'s PID value is gated on
   `external_process.exists is True`.** The design document did not state
   explicitly whether the independent witness's PID value for relationships
   #1/#2 should be the raw queried `pid` unconditionally, or gated on
   confirmed existence. This implementation gates it: if
   `external_process.exists` is not `True`, no positive PID observation was
   actually made, so the independent witness's PID value is `None` (which
   degrades those relationships to `ONE_SIDED`, not a fabricated `AGREE`).
   This is **deliberately stricter** than Layer 2's own existing
   `correlation.pid_match_server_file`/`pid_match_sentinel` fields (left
   completely unchanged), which compare against the bare queried PID
   regardless of `exists`. Judged to be a legitimate interpretation within
   the design's own stated principles ("never treat absence as evidence,"
   "unknown ≠ false") rather than a contradiction requiring a stop.
   Verified directly (Case recon-4a): with `exists=False` but a real,
   internally-consistent self-report, the two independent-witness PID
   relationships correctly read `ONE_SIDED` (not a fabricated `AGREE`) while
   the dependent-group-internal relationship correctly reads `AGREE`, and
   `independent_corroboration_count` correctly reads `0` — a real,
   demonstrated epistemic-precision improvement over Layer 2's own raw
   `correlation.pid_match_sentinel` field, which would read `True`
   unconditionally in this exact scenario.

2. **The `start_time` relationship cannot distinguish `ONE_SIDED` from
   `NEITHER`.** Layer 2's own `_compose_correlation()` only attempts the
   start-time comparison when *both* `external_create_time_utc` and
   `sentinel_start_utc` are truthy — when exactly one side is present,
   `start_time_match_sentinel` is `None`, identically to when both sides are
   absent. Because the specification requires reusing this field rather than
   recomputing it, this relationship necessarily collapses the `ONE_SIDED`
   case into `NEITHER`. This is a real, accepted limitation of the "reuse,
   don't recompute" instruction — disclosed in the code's own inline
   comment rather than silently smoothed over. Recovering the distinction
   would require independently re-reading and re-parsing the raw timestamp
   fields, which the specification explicitly forbids.

One additional, minor, non-blocking observation (not a deviation from
required behavior, but worth disclosing): `unrecognized_input_fields`
scans `layer2_result`'s top level plus the three known nested dicts
(`external_process`, `runtime_self_report.server_pid_file`,
`runtime_self_report.sentinel_file`) — it does **not** scan
`runtime_self_report` itself or `correlation` for extra keys. An injected
field at those two nesting levels (e.g.
`runtime_self_report.some_extra_key`) would be silently ignored rather than
disclosed. This does not create any corroboration risk (verified: no
relationship computation reads arbitrary keys at those levels, only the two
specifically-named sub-dicts), so it does not weaken the anti-cherry-picking
guarantee — it is purely a completeness gap in the *disclosure* mechanism,
narrower in scope than the top-level case the design document's Section 13
specifically names. Flagged here rather than fixed, since fixing it was not
requested and the actual security property (no manufactured corroboration)
holds regardless.

---

## 6. Purity / zero-I/O

Verified two ways, not merely asserted:

- **Determinism + no input mutation** (Case recon-7): the same input dict,
  deep-copied before two separate calls, remains byte-for-byte unchanged
  after both calls, and both calls return identical output.
- **Zero I/O via mocking** (Case recon-8): `psutil.Process`, `builtins.open`,
  and `subprocess.run` were all patched to raise `AssertionError` on any
  call. `reconcile_process_and_selfreport()` was then called against a real,
  fully-populated synthetic input — it completed successfully with no
  exception, proving none of the three patched entry points were ever
  invoked.

The function performs no filesystem access, no subprocess calls, no
`psutil` calls, and no network access, confirmed both by direct code
inspection (every operation is pure dict/string/number manipulation) and by
the mocking test above.

---

## 7. Layer 1 / Layer 2 boundary

**Intact.** `reconcile_process_and_selfreport()`'s only argument is a Layer
2 result; no Layer 1 field name (`sha256`, `head_blob_sha256_or_none`,
`tracked`, `modified_vs_head`, etc.) appears anywhere in its logic or output
schema — confirmed both by direct code read and by two tests:

- **Case recon-9**: injecting Layer-1-shaped fields (`sha256`,
  `head_blob_sha256_or_none`) at the top level of a synthetic Layer 2 result
  causes them to appear in `unrecognized_input_fields` and has zero effect
  on the resulting `aggregate` or `relationships` — proving such fields are
  disclosed, never read.
- **Case recon-10** (the mission's specified `self_heal.py` adversarial
  test): real Layer 1 data was fetched for `app/core/self_heal.py`
  (confirmed via direct call: tracked, exists, clean) and real Layer 2 data
  was fetched for the live PID 7644 (read-only `psutil` inspection only).
  The reconciliation output was checked for (a) any field name containing
  `loaded`, `import`, `module`, `executing`, `execution`, `self_heal`,
  `in_use`, or `running_code` — none found — and (b) any field whose final
  path segment matches a real Layer 1 field name (`sha256`,
  `head_blob_sha256_or_none`, `tracked`, `modified_vs_head`) — none found.

---

## 8. Verification results

`scripts/verify_provenance_check.py` extended with 17 new formal test
functions (registered in `CASES`), covering all 14 mission-specified
categories plus the explicit caller-cherry-picking test:

| # | Category | Case(s) |
|---|---|---|
| 1 | Happy path | recon-1 |
| 2 | PID/start-time disagreement | recon-2, recon-5 |
| 3 | Missing/malformed self-report | recon-3, recon-3b |
| 4 | Dependence, both directions | recon-4a, recon-4b |
| 5 | PID reuse | recon-5 |
| 6 | Timestamp compatibility | recon-6 |
| 7 | Purity | recon-7 |
| 8 | Zero-I/O via mocking | recon-8 |
| 9 | Layer 1 exclusion | recon-9 |
| 10 | `self_heal.py` real-data false positive | recon-10 |
| 11 | Complete-input requirement | recon-11 |
| 12 | Output completeness | recon-12 |
| 13 | Exact enum/field contract | recon-13 |
| 14 | Malformed top-level input | recon-14 |
| + | Caller cherry-picking | recon-15 |

Full suite run (`python3 scripts/verify_provenance_check.py`):

```
56/56 discrimination cases passed
```

(39 pre-existing Layer 1/Layer 2 cases, unchanged and still passing, plus
the 17 new reconciliation cases — zero regressions.) Exit code 0. No test
was weakened or replaced with a superficial string check to achieve this
result; every new case asserts on real computed structure (relationship
states, aggregate counts, exact field sets, signature introspection,
mocked-call verification), matching the existing file's own established
discrimination-test discipline.

No other project verification script was run — this change is isolated to
`app/core/provenance_check.py` and its own dedicated verifier; no other
script imports or exercises this module.

---

## 9. STOP conditions — none triggered

Checked explicitly against the mission's own list:

- Live schema did not contradict the design document.
- All 5 relationships were computable from the real, current Layer 2
  schema.
- No Layer 1 access was ever required.
- No new I/O was ever required.
- No architectural contradiction was found between the design document and
  live code (the two disclosed deviations in §5 were judged as legitimate,
  documented interpretations within the design's own stated principles, not
  contradictions).
- PID 7644 was never disturbed.
- No module other than `app/core/provenance_check.py` and
  `scripts/verify_provenance_check.py` required modification.
- No unresolved semantic contradiction was discovered.

Implementation proceeded to completion without halting.

---

## 10. Epistemic boundary — what this primitive does and does not establish

`reconcile_process_and_selfreport()` establishes relationships **among
Layer 2 process/self-report evidence only** — whether a PID observation, a
server-written PID file, and a sentinel JSON file's claimed PID agree,
disagree, or lack sufficient evidence to compare; whether a pre-computed
start-time consistency check agrees or disagrees; and how many of those
agreements constitute genuine independent corroboration (at most 1) versus
mere self-consistency within one dependent self-report group.

It does **not** establish, and its output schema contains no field capable
of expressing: that any file is loaded, that any module has been imported,
that any code is executing, or any relationship whatsoever between Layer 1
(file/Git) evidence and this Layer 2 (process/self-report) evidence. This
was directly, empirically confirmed against real data in §7/Case recon-10,
not merely asserted from the code's own docstring. `EVIDENCE_AGREES` means
only that every computable relationship in the available evidence happened
to agree — never "verified," never "confirmed," never a claim about which
of two disagreeing sources, if any, is correct.

The already-researched epistemic boundary was implemented without creating
a stronger claim than the evidence supports.
