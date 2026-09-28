# Provenance Layer 2 Red-Team

**Date:** 2026-09-13
**Type:** Adversarial investigation only. No production fix applied. No commit, stage, or Git mutation. PID 7644 read-only-inspected only (`ps`, live calls to the read-only primitive itself — never signaled, restarted, or attached to). All fixtures built under `/private/tmp/.../scratchpad/l2_redteam/`, outside the repository, removed before the final integrity check.
**Subject:** `app/core/provenance_check.py`'s `runtime_process_identity_and_self_report(pid: int)` and its supporting helpers (`_external_process_observation`, `_read_server_pid_file`, `_read_sentinel_file`, `_compose_correlation`). Not a general provenance audit — Layer 1 (`working_tree_file_identity`) was touched only to confirm the composition question in §8.

---

## 1. Verdict

```
PASS
```

Sixteen attack phases produced zero **CRITICAL** or code-level false-positive defects: no input, race, corruption, or malformed self-report was found that causes the primitive itself to fabricate a match, silently collapse an unknown into a negative, or crash. Two **MODERATE** findings and three **MINOR** findings were confirmed by direct, reproducible test — all are schema/documentation-level risks (a future consumer *could* misread the honest evidence this primitive already produces), not defects in the evidence-gathering logic itself. None require blocking the commit; all are recorded precisely below, per the mission's own instruction not to inflate observations into defects nor dismiss genuine weaknesses because tests currently pass.

---

## 2. Attack surface

All 14 mission-specified phases were executed (Phases 3–14); Phases 1, 2, 15, 16 are baseline/procedural and covered in the Integrity section. Every test below is either a real, non-mocked reproduction (real subprocess race, real corrupted scratch files, real live PID 7644 query) or an explicitly-labeled deterministic mock (PID vanish/access-denied/reuse, where a real timing-dependent reproduction would be unreliable) — never a hypothetical asserted without evidence.

| Phase | Attack | Method |
|---|---|---|
| 3 | Stale self-report, no live process (Case A) | Scratch fixture, real call through the public function |
| 4 | PID reuse, mismatched start time | Mocked `psutil.Process`, scratch self-report fixture |
| 5 | Process disappearance mid-observation | **Real** short-lived subprocess, 20x rapid-fire polling |
| 6 | Self-report corruption (11 shapes) | Scratch fixtures: negative/huge/whitespace/empty PID; JSON array/scalar/null/empty-object; wrong-typed field; injected extra field |
| 7 | Self-report spoofing | Same corruption fixtures, specifically the injected-field case |
| 8 | Correlation semantics (missing==missing) | Direct calls to `_compose_correlation()` with all-None inputs |
| 9 | Timestamp semantics | Direct source trace of both timestamp origins + real measured delta |
| 10 | Path/artifact assumptions | Source trace of `_PROJECT_ROOT` resolution; confirmed shared with Layer 1 |
| 11 | External field interpretation | Source trace + live field-by-field failure-mode trace |
| 12 | Executable/interpreter field overclaim | Docstring/schema review |
| 13 | "Live Echo" inference chain | Constructed explicitly in Case A test, §3 |
| 14 | Layer 1 ↔ Layer 2 composition | Schema-level cross-reference check, both modules read together |

---

## 3. Findings

### Finding 1 — `pid_match_*` remains `True` even when the process does not exist (MODERATE)

**Reproduction:** scratch `memory/echo_server.pid`="999999999" (confirmed nonexistent via `psutil.pid_exists()` loop), scratch `memory/echo_sentinel.json` claiming `pid: 999999999, stage: "serving"`. Real call: `runtime_process_identity_and_self_report(999999999)`.

**Evidence (actual output):**
```json
"external_process": {"exists": false, ...},
"correlation": {"pid_match_server_file": true, "pid_match_sentinel": true,
                  "start_time_match_sentinel": null, "start_time_delta_seconds": null}
```

**Interpretation:** the full schema is honest — `external_process.exists: false` is unambiguous and sits right next to `correlation.pid_match_sentinel: true` in the same top-level dict. But a consumer who reads *only* `correlation.pid_match_sentinel` (a very plausible shortcut for a future Layer 3/reconciliation pass looking for a quick "does this look right" signal) would see `true` and could conclude the self-report is corroborated, when in fact it describes a process that does not exist. This is precisely the Phase 13 fallacy construction, realized concretely. **Why existing tests missed it:** `case_l2_corr_1_matching_pid` tests `_compose_correlation()` in isolation with a synthetic `queried_pid` and does not exercise the *combination* with `external_process.exists=False` through the public function — the gap is in end-to-end schema-reading behavior, not in any single unit.

**Recommended action:** documentation-only, no code change. Strengthen `runtime_process_identity_and_self_report()`'s own docstring (not just the module header) with an explicit sentence: *"`pid_match_*` must always be read together with `external_process.exists` — a PID match alone, without confirmed process existence, is not evidence of a live process."* No schema change is required or recommended; adding a merged boolean would reintroduce exactly the "verdict, not evidence" problem this design exists to avoid.

### Finding 2 — PID reuse is correctly detectable, but only if the consumer checks both fields together (MODERATE)

**Reproduction:** scratch self-report claiming `pid: 555555, start_utc: "2026-01-01T00:00:00Z"` (stale). Mocked `psutil.Process(555555)` representing a **genuinely different**, freshly-started, unrelated process (`create_time()` = real "now").

**Evidence (actual output):**
```json
"correlation": {"pid_match_server_file": true, "pid_match_sentinel": true,
                  "start_time_match_sentinel": false, "start_time_delta_seconds": 22077792.73}
```

**Interpretation:** the stronger identity signal the boundary review promised (`start_time_match_sentinel`) *does* correctly fire `false` with a real, disclosed ~255-day delta — the mechanism works. But this is the same underlying risk as Finding 1: a consumer reading only `pid_match_sentinel` would see `true` and miss the reuse entirely; only checking `start_time_match_sentinel` alongside it reveals the truth. **Not a code defect** — `_compose_correlation()` computes both fields correctly and independently, exactly as designed — but the schema does not force a consumer to look at both.

**Recommended action:** same as Finding 1 — documentation strengthening only. Genuinely novel PID reuse *within the same observation call*, before `create_time()` is ever read (i.e., between `psutil.Process(pid)` construction and its first method call), remains a real, extremely narrow, unfixable-without-new-instrumentation race — recorded as an open, disclosed limitation, not a defect, since no primitive built on the OS's own PID model can fully close it.

### Finding 3 — Self-reported PID values are not range-validated (MINOR)

**Reproduction:** scratch `echo_server.pid` = `"-5"` → `{"pid": -5, "malformed": false}`. Scratch `echo_server.pid` = `"99999999999999999999999999"` → accepted verbatim as a Python arbitrary-precision int, `malformed: false`.

**Interpretation:** `_read_server_pid_file()` only validates that the content parses as *some* integer, not that it is a plausible PID (positive, within a real OS PID range) — inconsistent with the public function's own stricter `pid > 0` check on the *queried* argument. **Confirmed not currently exploitable as a false positive**: a negative PID can never be queried through the public function at all (it's rejected as `in_scope: False` before evidence gathering even starts), and a coincidental match on an absurd huge number would require the caller to supply that exact same absurd number — implausible for any realistic consumer.

**Recommended action:** for defensive symmetry, apply the same `> 0` bound (and optionally a sane upper bound, e.g. 2**22, matching realistic OS PID_MAX values) when parsing `_read_server_pid_file()`'s content, marking out-of-range values `malformed: true` rather than accepting them silently. Pure hardening, no contract change — `pid` would simply become `None` with `malformed: True` instead of a nonsensical integer.

### Finding 4 — `start_utc`'s exact semantics are precisely disclosed in the module header comment but not in the public docstring (MINOR)

**Trace, not reproduction:** `run.py`'s `_SENTINEL_START = datetime.utcnow()` is a module-level statement, evaluated when Python's import machinery reaches that specific line in `run.py` — **after** several heavy imports (faiss, sentence-transformers, etc.) have already completed. This is measurably later than `psutil.create_time()`'s value, which is the OS kernel's own fork/exec timestamp. The real, live gap measured earlier in this implementation's own history was ~4.4 seconds; this is honestly, precisely disclosed in `provenance_check.py`'s module-level comment (the `_START_TIME_MATCH_TOLERANCE_SECONDS` justification) — **but the public function's own docstring**, which is what a future Layer 3 developer is most likely to read in isolation, only says the two timestamps are compared "within tolerance," without explaining that they are two structurally different kinds of "start" (kernel fork-time vs. "Python reached this import line").

**Recommended action:** copy the one-paragraph explanation from the module header into the `runtime_process_identity_and_self_report()` docstring's own description of `start_time_match_sentinel`. Documentation-only.

### Finding 5 — `cmdline`/`executable` are correctly labeled as bare OS facts but remain a foreseeable target for "this proves it's FeralEcho" over-interpretation (MINOR)

**Trace:** `cmdline` for the real PID 7644 reads `["python", "-u", "run.py"]` — genuinely suggestive to a human reader that "this is the FeralEcho process," but it is only ever an OS-recorded argv string; nothing prevents an unrelated script also named `run.py`, in an unrelated directory, from producing an identical `cmdline`. The docstring's existing epistemic-boundary paragraph focuses on module-loading/execution claims broadly and does not specifically call out this narrower, more tempting misuse of `cmdline` as identity proof.

**Recommended action:** add one explicit sentence to the docstring: *"`cmdline`/`executable` are OS-recorded strings, not proof of which specific application or code version is running — a different process could report an identical `cmdline` by coincidence or by design."* Documentation-only.

### Confirmed non-findings (tested and found correct — recorded per the mission's own discipline of stating why an attack failed, not just that it did)

- **Missing==missing never becomes match=True.** Direct calls to `_compose_correlation()` with all five inputs `None` produce `pid_match_server_file: None, pid_match_sentinel: None, start_time_match_sentinel: None, start_time_delta_seconds: None` — every comparison field independently defaults to unknown, never `True`, confirmed by source trace (`if candidate is None: return None`) and by the existing `case_l2_corr_5` test, re-verified this session.
- **Real process-disappearance race is handled honestly.** A genuine (non-mocked) short-lived subprocess, polled 20x at 10ms intervals across its real exit, showed `exists` transition cleanly `True → False` exactly once, no crash, no bounce-back to `True` (which would have indicated a bug or an actual PID-reuse collision within the test's own narrow window).
- **Self-report spoofing via field injection is fully defeated by the existing allowlist.** A scratch sentinel containing `"injected_verified": true, "malicious": "drop table"` alongside the real 5 expected fields was read — neither injected key appears anywhere in `_read_sentinel_file()`'s output, confirmed directly. `_SENTINEL_EXPECTED_FIELDS` is a strict allowlist, not a blocklist; nothing outside those 5 literal keys can ever reach the schema.
- **Type-mismatched values degrade safely, never to a false positive.** A sentinel with `"pid": "7644"` (string, not int) is stored verbatim (no coercion), and `_pid_match()`'s `==` comparison against an int queried-PID correctly returns `False` in Python (a string never equals an int) — a false *negative* direction only, never a fabricated match.
- **JSON array/scalar/null top-level values are correctly rejected** as `malformed: True, error: "not_an_object"` via the existing `isinstance(data, dict)` guard — confirmed for `[1,2,3]`, `42`, and `null`. (Not previously exercised by the shipped 39-case suite, which only tested unparseable JSON — a real, if minor, test-coverage gap worth naming, though not a code defect since the guard already handles it correctly.)
- **`_PROJECT_ROOT` is one fixed constant, shared identically by Layer 1 and Layer 2, resolved once at import time from `__file__` — never from `os.getcwd()`.** Confirmed by source trace: no call in either self-report reader touches `os.getcwd()`, so a CWD change after import has zero effect. No git semantics are involved anywhere in Layer 2 (unlike Layer 1) — there is no git/filesystem conflation risk to find.

---

## 4. Epistemic boundary assessment

| Boundary | Preserved? | Evidence |
|---|---|---|
| External process evidence | **Yes** | `external_process` is a structurally separate sub-object; every field traces to a real `psutil` OS call, confirmed live against PID 7644 and via a real subprocess race |
| Runtime self-report evidence | **Yes** | `runtime_self_report.{server_pid_file,sentinel_file}` are structurally separate from `external_process`; content is read verbatim, allowlist-filtered, never merged with external facts |
| Module loading uncertainty | **Yes, correctly absent** | No field anywhere in the schema references `sys.modules`, imports, or module state — confirmed by the shipped `case_l2_epi_1` structural check, re-confirmed this session |
| Execution/use uncertainty | **Yes, correctly absent** | No field claims a function was called or code is executing — confirmed by `case_l2_epi_2`, re-confirmed this session; `status`/`cmdline`/`executable` are OS-scheduler/argv facts only, per Findings 5 |

The two MODERATE findings above are about a *consumer's* potential misreading of honestly-separated evidence, not about the primitive itself blurring these boundaries — the boundaries remain structurally intact in every test performed.

---

## 5. PID reuse assessment

**PID matching alone is confirmed insufficient**, and the implementation does maintain a stronger signal (`start_time_match_sentinel`, backed by `psutil.create_time()` — genuine OS-level process creation time, not a self-reported or derived value). Finding 2 confirms this signal correctly discriminates a real reuse scenario (a mismatched creation time produces `start_time_match_sentinel: False` with a large, disclosed delta) — but the schema does not *require* a consumer to consult it, and `pid_match_*` alone can look like confirmation. This is the report's most actionable finding: the raw capability to detect reuse exists and works; the documentation does not yet make its necessity unmistakable.

---

## 6. Staleness assessment

The implementation **can** establish: whether the self-report files currently exist, are readable, and what they currently claim (including `last_heartbeat_utc`, which — per `dmn_guardian.py`'s real ~60s refresh cycle, confirmed live in the prior implementation mission — is the single freshest available signal for "was this file touched recently"). The implementation **cannot and does not attempt to** establish staleness as a computed field — there is no `is_stale` or `heartbeat_age_seconds` in the current schema; a consumer would have to compute `now() - last_heartbeat_utc` themselves from the raw value already exposed. This is an accurate, disclosed limitation (the docstring correctly states "a crashed prior run's frozen last-known state is indistinguishable, by this primitive alone, from a currently-live process's state") rather than an invented freshness guarantee — no defect, matching the mission's own instruction that this is acceptable "only if the limitation is explicit," which it is.

---

## 7. Race assessment

Two distinct race classes were tested:
1. **Process disappearing entirely during observation** — tested with a real subprocess; handled correctly (clean `True→False` transition, no crash, no regression) and additionally covered by the existing mocked `case_l2_ext_3` test for the specific "vanished between fields" sub-case.
2. **PID reused by an unrelated process during/around observation** — cannot be forced deterministically against a real OS scheduler; tested via an explicitly-labeled deterministic mock instead (Finding 2). The evidence shows the *result* of such a reuse (a mismatched `start_time_match_sentinel`) is correctly represented once observation completes. The narrower sub-race — reuse occurring *between* `psutil.Process(pid)` construction and its very first field read, before any evidence has been gathered at all — remains a genuine, disclosed, unfixed-and-likely-unfixable-without-new-mechanism limitation, inherent to any PID-based identity system, not unique to this implementation.

In no tested case did a race convert into an unjustified `True`/confirmed result — every race-adjacent scenario tested degraded to either an honest `False`/`None`, or (in the disappearance case) a clean, monotonic `exists: False`.

---

## 8. Layer 1 composition assessment

Confirmed directly by reading both schemas together: `working_tree_file_identity()`'s output (`path, in_scope, error, exists, tracked, size, mtime, sha256, head_blob_sha256_or_none, modified_vs_head`) and `runtime_process_identity_and_self_report()`'s output share **zero common or cross-referencing keys** — there is no field in either schema that names a file path *and* a process, or a module *and* a process. Composing the two therefore cannot mechanically produce a "file is loaded" or "file is executing" claim — such a conclusion would have to be entirely invented by the consumer, not assembled from any field the two primitives actually provide. `app/core/self_heal.py` remains the standing counterexample: it would pass every Layer 1 check cleanly (tracked, hash-matched to HEAD) at the exact same moment `runtime_process_identity_and_self_report(7644)` reports a fully "matching" process — and nothing in either output asserts, or could be misread as asserting, that the two facts are related. Composition remains structurally safe specifically because Layer 2 never attempted the module-origin problem (Candidate B) that would have been the only real bridge between the two domains.

---

## 9. Recommendation

```
READY TO COMMIT
```

All five findings are documentation-strengthening or defensive-hardening recommendations, none blocking. If the maintainer wants the five recommended docstring additions (Findings 1, 2, 4, 5) and the one defensive range-check (Finding 3) applied before committing, that is a small, separate, explicitly-scoped follow-up — not required by this red-team's own verdict, and not performed in this mission per its "stop before fixing production code" instruction.

---

## Integrity

```
Starting HEAD:  6e835bfb3ae4c3f761a74d4af19c5fe931ca32d4
Ending HEAD:    6e835bfb3ae4c3f761a74d4af19c5fe931ca32d4   (unchanged)
Files modified: none (app/core/provenance_check.py and scripts/verify_provenance_check.py
                 remain exactly as they were at the start of this mission -- diffed and
                 confirmed identical before writing this report)
Files created:  audits/2026-09-13_provenance_layer2_red_team.md (this file)
Staged:         nothing
Committed:      nothing
Pushed:         nothing
Existing suite: 39/39 passing, unchanged, unweakened -- re-run at the end of this mission
Scratch fixtures: all created under /private/tmp/.../scratchpad/l2_redteam/, outside the
                 repository; removed before this report was written
Real self-report files (memory/echo_server.pid, memory/echo_sentinel.json): untouched by
                 this investigation -- confirmed by direct read at the end of this mission,
                 showing only dmn_guardian.py's own expected ~60s heartbeat advancement
PID 7644:       unchanged throughout -- same start time (Thu Sep 10 22:41:53 2026) observed
                 at every check, including via real (non-mocked) calls to the primitive
                 itself against the live PID
```
