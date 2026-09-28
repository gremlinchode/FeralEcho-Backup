# Observation-Time Contract Enforcement Research

**Date:** 2026-09-13
**Type:** Read-only architectural research. No production code, test, schema, or configuration modified. No lint rule, AST check, runtime validator, decorator, or timestamp helper implemented. PID 7644 inspected read-only only (`ps`).
**Predecessors:** `audits/2026-09-13_cross_layer_reconciliation_boundary.md`, `audits/2026-09-13_observation_time_contract_research.md`, `audits/2026-09-13_observation_time_placement_architecture.md`. The third report concluded Model A (producer-owned observation time) is the correct placement but left one question explicitly open: nothing currently guarantees future producers will implement it correctly. This report investigates that question and only that question.

---

## Executive Conclusion

**Enforcement in this architecture has a hard, evidenced ceiling: structural presence of an `observed_at` field is mechanically checkable; whether that field was actually generated at the true observation boundary — the specific failure `introspection_channel.py` demonstrates — is a semantic property that this codebase's own existing static-analysis conventions are not capable of reliably verifying, confirmed by direct examination of the closest real precedent (`liveness_ledger.py`'s own "static source-anchor" checks, which use plain text/regex matching, not AST parsing, and which this project's own history — CLAUDE.md's Findings 63/78/83 — has already caught being fooled by matching text inside docstrings/comments rather than real code three separate times).** The correct, honest posture is a layered one: structural compliance (field present, correctly typed) is mechanically enforceable and worth building later; semantic correctness (timestamp generated at the real boundary, not before a sequence of observations) is not mechanically enforceable with the tooling this codebase already has or would reasonably build, and must remain a matter of code review and documented convention — exactly the same trust boundary this entire research thread has already established for self-report evidence generally. Any future enforcement mechanism must be described using this exact distinction, never collapsed into a single "compliant" or "verified" signal.

---

## 1. Starting State

```
HEAD (verified fresh): e03f5984bb86d36ade51ed8f0753a3b8264c0f9f
git status --porcelain=v1 | wc -l: 106
```
Matches the exact end-state of the placement-architecture report — no discrepancy. Same 19 pre-existing modified files present, unmodified. PID 7644 confirmed present, `Thu Sep 10 22:41:53 2026`, `ps` only. All three predecessor reports read in full before beginning. Confirmed baseline matches the mission's own stated summary exactly: producer-owned placement, preserve-individual-timestamps composition, reconciliation unimplemented, enforcement unresolved.

---

## 2. Evidence Producer Inventory

Traced by following real call paths, not grep alone, per the mission's explicit instruction:

| Function | Module | Operation | I/O primitive | Current timestamp behavior | At true boundary? | Classification (§3) |
|---|---|---|---|---|---|---|
| `_stat_evidence()` | `provenance_check.py` (Layer 1) | file stat + read + hash | `os.stat()`, `open().read()` | `mtime` computed inline, immediately after `os.stat()` returns — but this is a *subject* timestamp (file's own mtime), not an observation timestamp; no `observed_at`-shaped field exists | N/A — field doesn't exist | `NO_OBSERVATION_TIMESTAMP` |
| `_git_tracked()` / `_git_head_blob_sha256()` | `provenance_check.py` (Layer 1) | `git ls-files`/`git show` via subprocess | `subprocess.run()` | None | N/A | `NO_OBSERVATION_TIMESTAMP` |
| `_external_process_observation()`'s per-field loop | `provenance_check.py` (Layer 2) | `psutil` accessor calls | direct Python calls into `psutil` | None per field | N/A | `NO_OBSERVATION_TIMESTAMP` (field-level granularity for *degradation* already exists — confirmed in the Layer 2 red-team — but no timestamp accompanies it) |
| `_read_server_pid_file()` / `_read_sentinel_file()` | `provenance_check.py` (Layer 2) | file existence check + read | `os.path.isfile()`, `open().read()` | None | N/A | `NO_OBSERVATION_TIMESTAMP` |
| `collect()` and its 8 `_collect_*()` calls | `introspection_channel.py` | 8 independent sub-collections, each real I/O | varies per collector | One `"timestamp"`, stamped before all 8 calls | **No** — before the sequence, not per-item | `COLLECTION_LEVEL_TIMESTAMP` |
| `run_liveness_checks()`'s 30+ `runners[name]()` calls, via `_result()` | `liveness_ledger.py` | varies per check (file reads, `re.search` on source, functional canaries) | varies | `_result()` stamps `checked_at` inline, at the moment that specific check's own outcome is decided | **Yes**, per individual check | `CORRECT_VIA_SHARED_HELPER` (per-check); the *outer* `ledger["generated_at"]` remains `COLLECTION_LEVEL_TIMESTAMP` for the cycle as a whole — both classifications coexist in one file, at two different levels |
| `record_claim()` | `self_model_claims.py` | one append-only write | `open(..., "a")` | `entry["timestamp"]` stamped inline, at the exact call | **Yes**, but for a single atomic write, not a multi-step collection — a simpler case than the others | `CORRECT_PRODUCER_TIMESTAMP` |
| `_write_sentinel()` | `run.py` | one JSON write | `Path.write_text()` | Stamps `last_heartbeat_utc`/`start_utc` inline — but both are *subject* claims about the process itself, not an observation-of-something-else timestamp; this function is the process *producing* self-report content about itself, not observing external evidence | N/A — not evidence-observation in the sense this research concerns | `NOT_EVIDENCE_PRODUCER` |

---

## 3. Existing Correct Pattern — `liveness_ledger.py`

Traced precisely, verifying rather than repeating the predecessor report's figure per this mission's explicit instruction:

- **Exact call-site count, re-verified**: `grep -c "_result("` returns **217** raw occurrences of the substring, of which exactly one is the function's own definition line (`def _result(passed: bool, evidence: str, extra: dict | None = None) -> dict:`) — **216 real call sites**, not 215 as the predecessor report stated. A small, real correction, recorded here rather than silently repeated.
- **Where the actual check occurs**: inside each individual `_check_*()` function's own body — a file read, a `re.search()` against source text, a functional canary call, etc., varying per check.
- **Where `_result()` is called**: at the exact point each check function has *finished* deciding its own pass/fail outcome and evidence string — always **after**, never before, the real work of that specific check.
- **When `checked_at` is generated**: inside `_result()` itself, `liveness_ledger.py:176`, via `_now_iso()` — meaning it is generated at the moment the *caller* (the specific check function) invokes `_result()`, which is definitionally after that check's own observation completed.
- **Is the helper always downstream of the observation?** Yes, by construction of every check examined — `_result()` is the *return* mechanism, never called speculatively before work begins.
- **Can callers bypass it?** Checked directly this session, not assumed: searched for any alternate dict construction (`'pass'` single-quoted, `dict(pass=...)`, any other `"pass":`/`checked_at` occurrence) anywhere else in the file. **None found.** Every real check-result dict in this file is built exclusively through `_result()`.
- **Is the pattern reusable?** Structurally yes — it is a plain function, trivially importable/callable from any future check. Nothing about it is specific to any one check's logic.
- **Is the correctness structural or merely conventional?** **Conventional, not structural** — this is the central finding of this section. Nothing in Python's type system, nothing in this codebase's (nonexistent, §5) CI, and nothing in the check-registration mechanism (`_CHECKS`/`runners`, a plain dict literal) *requires* a new check function to call `_result()` at all. A future check could return `{"pass": True, "evidence": "..."}` built by hand, entirely correctly from a Python-syntax perspective, and the only consequence would be a missing `checked_at` key — silently absent, not flagged, not rejected by anything. The pattern's real-world success (216/216 real calls correctly routed through it) reflects that every author so far chose to follow the established convention, not that the architecture prevents deviation.

---

## 4. Existing Failure Pattern — `introspection_channel.py`

Re-traced, focused specifically on the enforcement question this time (the placement report already covered the mechanics):

- **Why was the collection-level timestamp attractive?** It is the natural, minimal-effort choice when writing a function that assembles a dict literal from several sub-calls — placing one timestamp at the top of the literal is visually simpler than threading a timestamp through each of 8 independent `_collect_*()` return values, and nothing in the surrounding code (docstrings, type hints, existing precedent *in this specific file*) suggested otherwise at the time it was written.
- **What semantic mistake does it permit?** Exactly what both predecessor reports already established: the recorded `"timestamp"` field is true only for the instant `collect()` began, silently understating the true observation time of every one of the 8 sub-collections that follow it.
- **Could a reviewer detect the error mechanically, by inspection?** Yes, straightforwardly, by a human who already understands the observation-time contract — the pattern (`{"timestamp": now(), "a": collect_a(), "b": collect_b(), ...}`) is visually obvious once you know what to look for. This is a real, meaningful distinction from the next two questions.
- **Could an AST/static-analysis rule reliably detect it?** **No, not reliably — this is the central negative finding of this report, evidenced concretely in §6E/§7, not merely asserted.**
- **Could a generic runtime validator detect it?** No — see §6D. A runtime check inspecting the *returned* dict has no way to know how many real I/O operations preceded the timestamp's own generation; the information needed to detect this specific mistake does not survive into the return value at all.
- **Is the mistake fundamentally semantic rather than syntactic?** Yes, precisely — the code is entirely syntactically valid, uses a real, correctly-formatted timestamp, and the *only* thing wrong with it is a fact about *when*, relative to other statements in the same function, it was computed. This is not a pattern any syntax-level tool is designed to catch.

---

## 5. Existing Enforcement Infrastructure

Searched directly, this session: **no CI workflows exist** (`.github/workflows/` does not exist); **no linter or type-checker configuration exists** anywhere in the repository (`pyproject.toml`, `.flake8`, `mypy.ini`, `.pylintrc`, `ruff.toml` — none found; the one `pyvenv.cfg` hit is an unrelated, orphaned scaffold-directory artifact, `x86_64_env/`, already documented elsewhere in this project's own history as dead weight); **none of `mypy`/`ruff`/`pylint`/`pyright` are installed** in the active environment.

**What genuinely does exist, and is directly relevant**: this codebase has an established, working convention of standalone `scripts/verify_*.py` audit scripts (e.g. `scripts/verify_arch_pipeline_isolation.py`, `scripts/verify_provenance_check.py` from this same research thread's own Layer 1/2 missions, `scripts/verify_liveness_ledger.py`) plus, inside `liveness_ledger.py` itself, a real, already-shipped class of "static source-anchor" checks (e.g. `_check_wolf_friction_bridge`, `_evaluate_dissent_log_hook`). These are the actual, proven precedent for "does source code still match an expected shape" checking in this project — **and their real mechanism, confirmed by direct read this session, is plain string/`re.search()` text matching against a bounded window of raw source text (`source.find("wolf_friction_bridge")`, then a `±200/800`-character slice, then `re.search(r"_log_dissent_entry\s*\(", block)`) — not genuine `ast.parse()`-based structural analysis.** This is a materially important, concrete finding for §6E and §7 below, not a hypothetical concern: this exact class of lightweight text-matching check has already been documented, in this project's own prior history (CLAUDE.md's own recorded corpus — Findings 63, 78's item B2, and 83 all independently describe the identical failure shape: a check's own text-search matched a *docstring or comment* mentioning the target string, producing a false result, caught and fixed three separate times across this project's history), to be foolable by exactly the kind of text that would surround a real code change. **Genuine `ast.parse()`-based tooling also exists** in this codebase (`self_edit_manager.py`'s F1 scanner, `code_verification.py`), but is used for a categorically different purpose — detecting dangerous *operations* (calls to `exec`/`subprocess`/etc.) via real syntax-tree traversal, not for verifying a *timing relationship between statements*, which is a different, and harder, kind of question (§7).

---

## 6. Enforcement Options

### A. Developer Convention
**Benefits**: zero implementation cost, immediately applicable, exactly what `liveness_ledger.py`'s own 216/216 compliance rate (§3) demonstrates can work in practice. **Limitations**: exactly what `introspection_channel.py` demonstrates — convention alone did not prevent the one real, already-shipped counterexample in this same codebase, written by an author presumably following *some* reasonable-seeming pattern (§9, item 14). Convention is necessary but, by this codebase's own evidence, not sufficient.

### B. Shared Helper
A hypothetical `observe(...)` (not built here) that a producer would call at its own observation boundary, mirroring `_result()`'s proven shape (§3). **Would it reduce errors?** For single-observation producers (Layer 1's `_stat_evidence()`, Layer 2's individual `psutil` field reads), yes, directly — the same mechanism that already works for `liveness_ledger.py`'s single-check case. **Would it obscure actual observation boundaries?** Only if misapplied — if a future author called `observe()` once at the *top* of a multi-step collector (exactly `introspection_channel.py`'s mistake, just wrapped in a helper call instead of a bare dict literal), the helper would *launder* the same error into something that *looks* more disciplined while remaining exactly as wrong. **This is a real, concrete risk specific to this option, not a generic caveat** — a shared helper's presence in code can create a false visual signal of correctness independent of whether it was actually called at the right point.

### C. Typed/Structured Evidence
Python's type system (even with a hypothetical `TypedDict`/dataclass requiring an `observed_at: str` field) can enforce **field presence and type** — genuinely, mechanically, at least under static type-checking (which this codebase does not currently run, §5) or at construction time for a dataclass with no default. **It cannot express, in any form Python's type system offers, "this field's value must equal `datetime.now()` evaluated at a specific program point relative to other statements"** — that is not a type-level property, it is a property of program *execution order*, which no type system (Python's or otherwise, without dependent/effect typing far beyond anything this project would reasonably adopt) captures. **"Field exists" and "field was generated at the correct observation boundary" are answered by two structurally different kinds of tooling, and typed evidence only ever answers the first.**

### D. Runtime Validation
A validator receiving an already-returned evidence dict can check: is `observed_at` present; is it a parseable ISO-8601 string; is it not in the future; is it not implausibly old. **It cannot detect the specific failure this research concerns** — a validator sees only the *value* of `observed_at`, never the sequence of statements that produced it. `introspection_channel.py`'s bug produces a perfectly well-formed, parseable, plausible timestamp — the *value itself* is not wrong in any way a runtime check could flag; only its *relationship* to the un-recorded moments the 8 sub-collectors actually ran is wrong, and that relationship leaves no trace in the returned data at all.

### E. Static/AST Analysis
**The mission's own example pattern, attacked directly, not assumed answerable**:
```
timestamp = now()
perform_many_observations()
return result(timestamp=timestamp)
```
A genuine AST-based rule *could*, in principle, detect the narrow syntactic shape "a `now()`-shaped call assigned to a variable, followed by more than N statements, followed by that variable being used in a return" — but this immediately runs into real, demonstrated problems in this exact codebase:
1. **False positives**: a function that computes a timestamp early for a legitimate, unrelated reason (e.g., measuring the collection's own duration, a real and valid use per the placement report's own §10 "collection_started_at" concept) would trigger the identical AST shape while being entirely correct.
2. **False negatives**: the rule would need to recognize *every* possible way "perform an observation" can be spelled — a direct call, a call through several layers of indirection, a call inside a loop, a call inside a `try`/`except` — and this codebase's own real check functions (§3) show exactly this kind of variation (some call `_result()` directly, some through a helper, some inside conditional branches).
3. **The already-documented precedent for exactly this class of tool being fooled**: `liveness_ledger.py`'s own existing static checks (§5) — simpler, narrower, text-matching tools solving an *easier* problem ("does this call exist in this window of source") than "does this timestamp precede these observations" — have already been shown, three separate times in this project's own history (CLAUDE.md Findings 63, 78-B2, 83), to be fooled by text appearing in a comment or docstring rather than real code. A rule attempting the strictly harder timing-relationship question would be at least as exposed to this failure mode, likely more so given the added complexity of reasoning about statement order and call graphs rather than simple string presence.

**Conclusion, stated plainly**: a narrow, best-effort static check *could* be built to catch the most literal, unobfuscated version of the mistake (a bare `now()` call immediately followed by several bare function calls in the same function body) — but it would carry a real, demonstrated (not hypothetical) false-positive/false-negative risk in this exact codebase, and would answer only "does this specific textual pattern appear," never "is the timing semantically correct." This is worth building only if explicitly labeled as a heuristic tripwire, never as proof.

### F. Contract Tests
A test asserting "producer X's returned `observed_at` differs from producer Y's `observed_at` when a real delay is injected between their calls" **can prove that a specific, already-identified producer's timestamp genuinely varies with real elapsed time** — a real, meaningful, mechanically-checkable property, and one this research thread has already used successfully (the symlink-fix regression tests in `scripts/verify_provenance_check.py`, which prove a specific defect *would* have failed against old code, per that mission's own "adversarial regression requirement"). **What it cannot prove**: that a *newly written, not-yet-tested* producer implements the contract correctly — a test only covers what it was written to cover; it provides no guarantee about future code that hasn't been tested yet, which is exactly the ongoing-enforcement question this report investigates, distinct from the already-solved "did we get Layer 1/2 right" question the existing test suites already answer.

### G. Evidence Schema Validation
Structurally identical in capability and limitation to Option C — validates presence/shape, never timing correctness, for the same reason (a schema validator, like a type checker, only ever sees the final value, never the sequence of program statements that produced it).

---

## 7. Semantic vs. Structural Enforcement

**The mission's own key example, addressed directly**:
```
t = now()
result_a = observe_a()
result_b = observe_b()
return Evidence(observed_at=t, ...)
```
Every structural mechanism examined in §6 (typed evidence, runtime validation, schema validation) would see this as **fully compliant** — `t` is a real, well-formed, present timestamp. **None of them can see that `t` was computed before `observe_a()`/`observe_b()` ran**, because that fact is a property of the *source code's statement order*, not of the *returned value*, and by the time any structural check runs (whether at return time or later), the statement-ordering information has already been discarded — it existed only transiently, during execution, in a form no downstream consumer of the *result* ever has access to.

**Which class of enforcement can detect this?** Only a genuine, deep AST/control-flow analysis specifically designed to trace the data-flow relationship between a timestamp variable's assignment point and each "observation" call's position in the same function — and even this, per §6E's concrete finding, would inherit real, already-demonstrated false-positive/negative exposure in this codebase, and would need to correctly classify *every* form an "observation" can take (direct call, indirect call, call inside a loop/conditional/exception handler) to avoid both missing real violations and flagging legitimate code. **No mechanism examined in this research reliably solves this in general** — only human code review, applied with the same discipline `liveness_ledger.py`'s own author evidently applied (§3), has actually succeeded at this in this codebase's real history.

---

## 8. False Confidence Risks

For every option in §6, stated precisely — the mission's own required test (*"could this mechanism itself become another false 'verified' signal?"*):

- **Structural presence checks (C, D, G)**: real risk — a field-presence check passing could easily be summarized, by a future careless caller, as "this producer's timestamps are correct," when it has only confirmed "this producer's timestamps exist and parse." This is *exactly* the same class of overclaim this entire research thread's three predecessor reports have repeatedly guarded against (a `pid_match: True` field being over-read as "same process," restated here one layer up as "field present" being over-read as "field correct").
- **Static/AST checks (E)**: real risk, evidenced concretely (§5, §6E) — this project's own history shows this exact class of tool being fooled by superficially-matching text, meaning a passing static check could give **false confidence that is worse than no check at all**, because a check that exists and reports "pass" invites trust a bare absence of tooling would not.
- **Contract tests (F)**: lower risk, if scoped honestly — a passing regression test genuinely proves the specific case it tests, and this research thread's own established discipline (stating exactly what a test proves and does not prove, per every `scripts/verify_*.py` script in this codebase) already avoids overclaiming here, provided that discipline is maintained for any future observation-time test too.

**Required terminology, derived from this analysis, not chosen for aesthetics**: any future report on this topic must distinguish **`structurally compliant`** (a field exists and parses correctly — mechanically provable), **`statically detected`** (a specific, narrow textual pattern was or wasn't found — a heuristic, not proof, per §6E/§7), **`runtime valid`** (a value passed a plausibility check at the moment it was read — says nothing about its origin), and **`semantically demonstrated`** (a specific test case proves a specific producer's timing behaves correctly under a specific, constructed scenario — the strongest available claim, still scoped to exactly what was tested). **`observation_time_verified = true` or any single boolean collapsing these four is explicitly rejected** — it would misrepresent which of the four (structurally weaker) claims actually holds.

---

## 9. Adversarial Analysis

Each mission-specified counterexample, evaluated against every §6 option, using the four verdicts the mission specifies:

| # | Counterexample | Convention (A) | Shared helper (B) | Typed/schema (C/G) | Runtime validation (D) | Static/AST (E) | Contract tests (F) |
|---|---|---|---|---|---|---|---|
| 1 | Timestamp before I/O | Detects only via review | Same risk as bare code (§6B) | **Cannot detect** | **Cannot detect** | Partially — the narrow literal pattern only (§6E) | Detects only if a test specifically targets this producer |
| 2 | Timestamp after I/O (correct) | N/A — this is the goal | N/A | Indistinguishable from any other valid timestamp | Indistinguishable | Indistinguishable | Provable, if tested |
| 3 | Timestamp once for multiple observations | Review only | **Risk of laundering** (§6B) | **Cannot detect** | **Cannot detect** | Partially, narrow cases | Provable for the specific tested producer |
| 4 | Timestamp generated by caller, not producer | Review only | Same | Cannot detect — field still present | Cannot detect | Cannot detect (caller-vs-producer distinction is not a textual pattern) | Provable if the test specifically checks *which* function produced the value, not merely that a value exists |
| 5 | Timestamp copied from another evidence record | Review only | Same | Cannot detect | **Partially** — a validator *could* flag two records sharing byte-identical timestamps as suspicious, a real, cheap heuristic worth naming even though it proves nothing conclusively | Cannot detect | Provable if constructed as the specific test case |
| 6 | Timestamp derived from file mtime | Review only | Same | Cannot detect (a valid-looking ISO string either way) | Cannot detect | Cannot detect | Provable if tested against a real mtime-vs-now distinction |
| 7 | Timestamp derived from process creation time | Same as 6 | Same | Same | Same | Same | Same |
| 8 | Cached evidence receiving a fresh timestamp | Review only | Same | Cannot detect | **Partially** — implausibly-fresh-looking timestamps on data known to be cached could be heuristically flagged, if the validator has independent knowledge of cache state (not generally available) | Cannot detect | Provable only with an explicit cache-aware test |
| 9 | Fresh evidence retaining an old timestamp | Same shape as 8, inverse direction | Same | Cannot detect | Same partial heuristic as 8 | Cannot detect | Provable if tested |
| 10 | Multiple observations hidden inside a helper | Review only | **This is exactly the risk named in §6B** — a helper call *looks* disciplined regardless of what's inside it | Cannot detect | Cannot detect | Cannot see through function-call boundaries without deep inter-procedural analysis, a materially harder problem than the already-attacked single-function case | Provable only if the test exercises the helper's *internal* behavior directly, not just its return shape |
| 11 | Helper itself performing multiple observations | Same as 10 | Same | Same | Same | Same | Same |
| 12 | Correct field attached at the wrong semantic level (e.g. `collection_started_at` mislabeled as `observed_at`) | Review only | Same | **Cannot detect — field name alone doesn't encode semantic level** | Cannot detect | Cannot reliably distinguish field *semantics* from field *name* via text matching | Provable if a test specifically checks the field's relationship to a known-real per-item observation |
| 13 | Different producers using different clock semantics | **Partially detectable via `clock_source` disclosure** (per the contract itself, §9 of the predecessor report) — this is the one case the *contract's own design*, not enforcement tooling, already addresses | Same | `clock_source` field presence is checkable structurally | Could flag an unrecognized `clock_source` value against a known enum | Cannot detect meaning, only string presence | Provable per-producer |
| 14 | A future developer following an apparently-reasonable but incorrect pattern | **This is precisely how `introspection_channel.py`'s own bug was introduced** — the strongest, most concrete evidence in this entire report that convention alone is insufficient | No better — a "reasonable-looking" incorrect pattern is exactly as likely to involve a plausible-looking helper call | No better | No better | No better — an author confident enough to write a plausible-looking pattern is equally capable of writing one that dodges a narrow static rule | The one mechanism that would have caught this specific historical case, *if* a test had existed for `introspection_channel.py` at the time it was written — which it did not |

**Net finding**: no single option in §6 detects more than a narrow subset of these 14 cases; **contract tests (F) are the only option that reliably detects a violation once written for a specific producer**, but provide zero protection against a *new*, not-yet-tested producer — meaning ongoing protection against future mistakes, the mission's actual central question, remains substantially unaddressed by any mechanism examined here.

---

## 10. Minimum Enforcement Contract

**Research recommendation only — not implemented.**

### Required structural properties
`observed_at` present, ISO-8601-parseable, not in the future relative to a reasonable clock-skew tolerance; `clock_source` present, matching a small controlled vocabulary (per the placement report's §9).

### Required semantic properties (documented, not mechanically enforced)
The value must have been computed at the literal point the specific evidence it accompanies was obtained — no mechanism examined in this report can verify this beyond the narrow, false-positive/negative-prone static pattern in §6E; this remains a documented expectation, upheld by code review, exactly as `liveness_ledger.py`'s own real 216/216 compliance rate (§3) was achieved.

### Detectable violations
Missing field; malformed field; implausible value (future timestamp, absurdly old timestamp); an unrecognized `clock_source`; the narrow, literal AST pattern of a bare timestamp-then-many-calls-then-return in a single, un-obfuscated function body (heuristic only, §6E/§9).

### Undetectable violations
Timestamp generated by the wrong party (caller vs. producer) when the field is otherwise well-formed; multiple real observations hidden behind one helper call; a timestamp copied or derived from an unrelated but plausible-looking source (mtime, process create-time) without independent knowledge of the copy having occurred; any "reasonable-looking but wrong" pattern a careful author could write that doesn't match a narrow static rule's specific shape.

### Explicit non-guarantees
No enforcement mechanism proposed or examined in this report may be described as guaranteeing semantic correctness. A passing structural check means only "the field exists and is well-formed." A passing static/AST heuristic means only "this specific textual pattern was not found" — never "no violation exists." A passing contract test means only "this specific, already-identified producer behaves correctly under this specific, already-constructed scenario" — never "all producers, including future ones, are correct."

---

## 11. Scope of Enforcement

Given §10's real ceiling, recommend enforcement (whichever forms are eventually built) apply, in priority order: **(1) evidence entering reconciliation** — the highest-stakes consumer, per §13, and the one place a violation would propagate furthest; **(2) new evidence producers going forward** — cheapest to hold to a documented standard from inception, avoiding retroactive migration entirely; **(3) existing Layer 1/2 producers** — already, per the placement report, largely correct or already-scoped for future attention (`introspection_channel.py`); **not** a blanket, immediate requirement across "all evidence-producing functions" in this codebase, since (per §5) this would require building genuinely new tooling this codebase has no current infrastructure for, and the marginal benefit of retrofitting already-shipped, already-working code (`self_model_claims.py`, `liveness_ledger.py`'s own per-check timestamps) is low relative to the cost. **Migration itself is not designed here, per this mission's explicit scope.**

---

## 12. Existing-Code Impact

- **`introspection_channel.py`**: would eventually benefit from producer-level `observed_at` fields on each of its 8 `_collect_*()` returns, per the placement report's own recommendation — **not fixed in this or any prior report in this thread**, flagged only.
- **`liveness_ledger.py`**: **the corrected finding from the placement-architecture report is explicitly preserved and restated here, not diluted**: its `_result()` helper already provides genuine, correct, per-check `checked_at` timestamps (216 real call sites, re-verified this session, §3) — the file's *only* remaining gap is its outer, collection-level `generated_at` field, which describes when the overall check cycle began, not any individual check's own observation time. This is a narrower, already-well-understood issue, categorically different from `introspection_channel.py`'s more complete absence of any per-item timestamp at all. **The earlier, broader characterization of `liveness_ledger.py` sharing "the identical gap" as `introspection_channel.py` remains superseded, as established in the placement report, and is not reintroduced here.**

---

## 13. Reconciliation Readiness

What enforcement would need to guarantee before `reconcile_process_and_selfreport(layer2_result)` could safely consume Model A evidence: **structural compliance only** — that every evidence item it receives has a present, well-formed `observed_at`/`clock_source`. This is the boundary of what §10 establishes is actually achievable. **It cannot and must not be extended into a guarantee of epistemic truth** — reconciliation must be built (in a future, separate mission) to treat an `observed_at` field exactly as it already treats every other field in this research thread's architecture: as evidence of a specific, narrow claim (a value was recorded, at a moment its own timestamp states), never as proof that the claim is *correct*, and never as license to infer anything about module loading or execution, which remain — per every predecessor report in this thread — entirely outside what any timestamp, however well-enforced, can establish. **The eventual reconciliation primitive must not inherit the assumption "`observed_at` field exists" → "observation timing is trustworthy"** — this report's central finding (§7) is precisely that no examined mechanism can make that inference safe to encode as an automatic property of the data.

---

## 14. Recommendation

```
MORE RESEARCH REQUIRED
```

Not `PROCEED TO RECONCILIATION DESIGN`: this report's own central finding is that semantic enforcement of the observation-time contract has no reliable mechanical solution available to this codebase today — reconciliation design proceeding on the assumption that "the contract is enforced" would be building on exactly the kind of false structural confidence §8 warns against. The mission's own stop-condition instruction is explicit on this point: do not choose PROCEED simply because *a* mechanism exists (several do, §6) — the question is whether an *adequate* one exists, and this report's evidence says it does not, for the semantic half of the contract.

Not `ARCHITECTURAL BLOCKER`: the structural half of the contract (field presence, well-formedness) *is* genuinely, mechanically enforceable, and §10's layered contract gives a concrete, honest foundation reconciliation could eventually build on for that narrower guarantee — this is not a dead end, only an incomplete one requiring either (a) accepting semantic correctness will always remain a matter of code review, documented and disclosed as such, never mechanically certified, or (b) a future, dedicated mission specifically investigating whether a more sophisticated (and, per §6E, more false-positive-prone) static analysis is worth the real cost this report has now documented.

---

## 15. Explicit Non-Claims

1. That any enforcement mechanism examined in this report can verify a timestamp was generated at the true observation boundary — only structural presence and narrow, heuristic textual patterns are mechanically checkable (§7, §10).
2. That `liveness_ledger.py`'s real 216/216 compliance with `_result()` (corrected count, §3) constitutes proof the pattern will hold for future checks — it is evidence of past discipline, not a structural guarantee (§3's own explicit finding).
3. That a passing static/AST check would mean no violation exists — this project's own documented history (CLAUDE.md Findings 63, 78-B2, 83) shows this exact class of check can be, and has been, fooled by superficially matching text (§5, §6E, §8).
4. That structural schema validation ("field present, well-formed") is equivalent to, or evidence of, semantic correctness — explicitly and repeatedly distinguished throughout this report (§6C/D/G, §8, §10).
5. That any enforcement mechanism proposed here, once built, would make Layer 3's already-established boundary (no observation-time mechanism can prove module loading or execution) any less true — enforcement of *when* evidence was gathered has no bearing on *what* that evidence can establish (§13, restated from every predecessor report in this thread).
6. That this report's recommendation constitutes a decision to build any of the examined mechanisms — none are implemented, proposed as ready to implement, or scheduled; this is research into what enforcement can and cannot achieve, not a build plan.

---

## Verification

Reviewed directly against this mission's own required term list:

- `verified`/`verification`: used only in explicitly rejected or negated contexts (e.g., "`observation_time_verified = true`... is explicitly rejected," §8) — never asserted as an achieved state.
- `compliant`/`guaranteed`: used with precise, narrow scope throughout (`structurally compliant` as one of four deliberately distinguished terms, §8) — never used to imply semantic correctness.
- `timestamp`/`observed_at`/`checked_at`: used descriptively throughout, consistent with the predecessor reports' established, non-inflated usage.
- `execution`/`loaded`/`running`: appear only in §13's explicit restatement of the already-established Layer 3 boundary, never asserted as newly established by anything in this report.

The `liveness_ledger.py` correction (§3, §12) is preserved exactly as the placement-architecture report established it — restated, not diluted, and the corrected call-site count (216, verified, not the prior report's 215) is recorded plainly as a small further correction found this session.

---

## Integrity

```
Starting HEAD:  e03f5984bb86d36ade51ed8f0753a3b8264c0f9f
Ending HEAD:    e03f5984bb86d36ade51ed8f0753a3b8264c0f9f   (unchanged)
Files modified: none
Files created:  audits/2026-09-13_observation_time_enforcement_research.md (this file)
Staged:         nothing
Committed:      nothing
Pushed:         nothing
Scratch artifacts: none created -- entirely read-only grep/source inspection of
                 already-committed code
PID 7644:       unchanged throughout -- same start time (Thu Sep 10 22:41:53 2026)
                 confirmed via ps at mission start and end, read-only only
```
