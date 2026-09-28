# Provenance Implementation-Boundary & Evidence Contract Mission

**Date:** 2026-09-11
**Type:** Design gate. No production code changed. No process restarted. No Git mutation.
**Predecessor documents:** `audits/2026-09-11_read_only_provenance_interface_design.md` (design), `audits/2026-09-11_provenance_leaf_primitives_validation.md` (leaf-primitive validation, concluded PROCEED). This mission does not repeat their empirical work — it re-derives the boundary from first principles against the actual current source, then attacks the evidence contract those two documents proposed.

---

## 1. Starting State

```
Git HEAD:                    e92ec3b7fe4743f75746d161a06601db0232bff2
Uncommitted path count:      99 (git status --short | wc -l)
PID 7644:                    alive — Thu Sep 10 22:41:53 2026, elapsed 15:55:44 at mission start
Command:                     python -u run.py
Repository path:             /Users/richietate/Desktop/FeralEcho (confirmed cwd)
```
Confirmed present and unchanged from the two predecessor reports' own final states — no restart occurred between missions or during this one (re-verified at the end, §15).

---

## 2. Source Documents Inspected

Both predecessor reports (already authored this session, re-examined here rather than trusted) plus direct re-reads of current source this session:
- `app/core/echo_tool_dispatch.py` — `TOOL_SCHEMAS` (3 entries: `read_file`, `search_memory`, `log_thought`) and `_execute_tool()`'s exact dispatch body (a flat `if name == "...":` chain, fail-closed on an unknown name — re-read in full, not assumed).
- `app/core/echo_ground_truth.py` — the slice-routing pattern immediately preceding `_build_architecture()`'s call site: a uniform `if "<slice>" in slices: sections.append(_build_<slice>())` chain, terminating in one `system_note("GROUND-TRUTH", ..., own_record=True)` wrapper — re-read directly.
- `app/core/self_model_claims.py` — `record_claim()`'s exact signature and its structural `proposed_by != verified_by` refusal (re-read in full in a prior pass this session; re-confirmed here).
- `app/core/self_knowledge_verification.py` — `verify_self_knowledge_claims()`'s full body re-read this session, including its **existing, live check-count verification** (`find_check_count_claim()` against `self_model.json`'s `verified_capabilities.checks`, tri-state `(caveat, verified)` return) and its one real call site, `app/routes_echo_studio.py:250`.
- `app/core/liveness_ledger.py` — the `f2_stdin_contract` check family, already deeply examined across all three prior reports; not re-read line-by-line this pass beyond confirming its `_result()` shape is unchanged.
- The existing hardcoded read-only Git dispatch and safe file-read guard — both are `echo_tool_dispatch.py`'s own `_guard_read_path()`/`_tool_read_file()`, confirmed to be the same, single existing pattern for both concerns (no separate "Git dispatch" module exists in production — Mission 18's design proposed one, unimplemented).

**Not assumed correct merely because the predecessors concluded PROCEED** — see §4 for where this mission finds real, previously-under-stated gaps in that conclusion's own evidence contract.

---

## 3. Claim / Evidence Matrix

For each claim: **A** external evidence, **B** in-process evidence, **C** corroboration, **D** what's actually proven, **E** failure/ambiguity cases, **F** allowed label.

**1. "This file exists in the working tree."**
A: `os.path.isfile()`. B: none needed. C: none needed — this is a complete, atomic fact. D: exactly what it says, nothing more. E: symlink to a nonexistent target reads as not-a-file; race condition if checked mid-delete (accepted, point-in-time only). F: **VERIFIED** (trivially — a filesystem existence check has no weaker alternative reading).

**2. "This file is tracked by Git."**
A: `git ls-files --error-unmatch <path>` (exit code). B: n/a. C: none needed. D: exactly what it says. E: a file that was `git rm --cached`'d but left on disk reads as untracked-but-existing — correctly distinct, not an ambiguity. F: **VERIFIED**.

**3. "This working-tree file has hash X."**
A: `sha256(open(path,'rb').read())`. B: n/a. C: none needed. D: exactly what it says, computed fresh, at query time. E: a concurrent write mid-read could produce a torn hash — accepted, extremely low-probability, point-in-time claim only. F: **VERIFIED**.

**4. "This working-tree file differs from HEAD."**
A: claim 3's hash != `git show HEAD:<path>` hashed the same way. B: n/a. C: none needed. D: exactly what it says. E: none beyond claims 1–3's own. F: **VERIFIED**.

**5. "HEAD contains blob/content X."**
A: `git show HEAD:<path>` (or `git cat-file`), hashed. B: n/a. C: none needed. D: exactly what it says. E: a detached-HEAD or force-pushed-over-since-query state would make a *later* re-check disagree with an *earlier* one — this is expected, not an ambiguity, provided every claim carries its own timestamp (§6). F: **VERIFIED**.

**6. "The running process is PID X."**
A: `ps -p X`, or, for an in-process implementation, `os.getpid()` compared against an externally-known PID. B: `os.getpid()` from inside. C: cross-checking A and B agree. D: exactly what it says. E: PID reuse after the real FeralEcho process has exited (an unrelated process now holds that number) — this is exactly why claim 6 must always travel with claim 7 (start time), never alone. F: **VERIFIED**, but only meaningfully so paired with claim 7.

**7. "The running process started at time X."**
A: `ps -p X -o lstart`. B: `psutil.Process().create_time()` (confirmed installed in the target environment, §4 of the validation report). C: A and B agreeing is strong corroboration since they use genuinely different code paths (one shells to `ps`, one reads `/proc`-equivalent process accounting directly). D: exactly what it says. E: clock skew between an external observer's `date` and the process table's own recorded start time — not observed this session, theoretically possible, low-severity (both derive from the same OS clock). F: **VERIFIED**.

**8. "The running process loaded module Y."**
A: **none exists** — this is the central finding of the leaf-primitives validation, re-confirmed here: no external process can observe another process's `sys.modules`, and OS-level inspection (`lsof`) reveals zero `.py` sources for a running CPython process. B: `module_name in sys.modules`, queried from inside. C: none available — this claim has **no external corroboration path at all**, by construction. D: only that *the process itself reports* having this key in its own module table — see §4 Q1 for why this changes the claim's epistemic status. E: a module imported and later deleted from `sys.modules` (rare, not observed in this codebase) would false-negative; a module imported under a different name (aliasing) would false-negative under the canonical name. F: **SUPPORTED at best, never VERIFIED on its own** — this is this matrix's single most important row; see §4.

**9. "Module Y reports source path Z."**
A: none (same reason as claim 8). B: `sys.modules[Y].__file__`. C: cross-referencing Z against claim 1's filesystem existence check *is* available and *is* external corroboration for "does this path even make sense" — but not for "is this really what the process loaded." D: only the string the process's own import machinery recorded at import time — **not** proof of the bytes actually compiled (§4 Q5, Q3). E: dynamically-generated/`exec()`'d code has no real `__file__` at all (Type E, per the design's own taxonomy); a module loaded via a symlinked path may report either the link or the target depending on how it was imported — untested this session, flagged as a real open question. F: **SUPPORTED**.

**10. "Symbol S exists in module Y."**
A: `ast.parse()` the working-tree file and check the parsed symbol table (exactly what this session's own three prior investigations already did, repeatedly, successfully). B: `hasattr(sys.modules[Y], S)` or `S in vars(sys.modules[Y])`. C: A and B agreeing is real, meaningful corroboration — A proves the symbol is *defined in the current source text*; B proves the *live module object* actually carries it, which is a materially different, additional fact (a syntax-valid but never-successfully-imported file would satisfy A and fail B). D: exactly what it says, for whichever half was checked. E: a symbol defined conditionally (inside an `if` block, a `try/except ImportError` fallback) may exist in source but not in the live object, or vice versa across two different runtime paths — a real, disclosed limitation of AST-only checking, already implicitly relied on by this session's own three prior reports without being named this precisely until now. F: **VERIFIED for A alone (pure source fact); SUPPORTED for B alone (self-report); VERIFIED for A+B together** (external source fact plus a real live-object check that could independently fail and didn't).

**11. "The observed behavior corresponds to the working-tree implementation."**
A: a behavioral fingerprint result (e.g. `os_fd0_blocked: true`) cross-referenced against a direct read of the working-tree source confirming *only* that version's code path could produce it. B: the fingerprint result itself originates from the process (see the distinction drawn in §4 Q5/§8). C: this is inherently a corroboration claim — it has no meaning without combining a behavioral result with a source-text comparison. D: that the observed behavior is *consistent with, and — among the versions actually compared — uniquely explained by,* the working-tree version. It does **not** prove no unconsidered third version could also produce the same behavior (§4 Q5). E: a HEAD version and a working-tree version that happen to be behaviorally indistinguishable for the specific check exercised (not the case for `os_fd0_blocked`, confirmed structurally impossible in HEAD, but not guaranteed true in general). F: **VERIFIED, scoped explicitly to "among the compared versions," never phrased as universal proof.**

**12. "The observed behavior corresponds to the HEAD implementation."**
Symmetric to claim 11. F: **VERIFIED**, same scoping caveat.

**13. "The runtime corresponds to neither HEAD nor working tree."**
A/B/C: absence of a match for either claim 11 or 12, positively confirmed (not merely "not yet checked"). D: that a specific, actually-attempted comparison against two specific, known versions both failed. E: this claim is **unfalsifiable in the positive direction without an exhaustive comparison against every historically-possible version** — it can only ever mean "neither of the two candidates I checked matches," never "no version anywhere would match." F: **SUPPORTED at most — never VERIFIED**, precisely because "neither of two" is not "none of any," and the report must never elide that distinction.

**14. "The runtime provenance is ambiguous."**
A: `runtime_module_origin`'s self-report returns `module_loaded: true` with `file_path: None` or a path outside the repo, or the target is confirmed dynamically-generated (Type E, per §5 of the design doc). D: exactly the honest admission the name implies. F: **VERIFIED** (an honest UNKNOWN, correctly labeled, is itself a verifiable fact about the state of the evidence — this is not a contradiction; "the evidence is ambiguous" is a true statement that can itself be confidently asserted).

**15. "The current working tree and running process are reconciled."**
This is `reconcile()`'s own summary output — a composite of claims 1–14, never independently observable on its own. D: only as strong as its weakest contributing claim. F: **inherits the weakest label among its inputs, computed, never separately asserted.**

**16. "Echo can safely use this evidence to update a self-model claim."**
This is not an evidence claim at all — it is a **policy** question, answered in §10 (the anti-self-attestation rule), not in this matrix. Flagged here only to make explicit that it does not belong in the same table as claims 1–15, a distinction the mission brief's own numbering slightly blurs by listing it alongside them.

---

## 4. Self-Attestation Analysis (Attacking the Epistemic Contract)

**Q1 — Is runtime module identity from `sys.modules` inherently self-attestation?**

**Yes, stated explicitly and without hedging.** Claim 8/9 in §3 have **no external corroboration path of any kind** — this was empirically proven, not assumed, in the leaf-primitives validation (a scratch process's own `sys.modules` is entirely disjoint from PID 7644's; OS-level `lsof` inspection surfaces zero `.py` sources). Any fact sourced from `sys.modules[name].__file__` is, structurally, the process reporting on its own internal state with no independent witness.

**Q2 — Can the full combination (external hash + Git hash + `sys.modules` path + mtime<start + behavioral fingerprint) reasonably justify `VERIFIED`? What exact proposition is being verified?**

**Yes — but only for a precisely, narrowly worded proposition, and the predecessor design's own wording was looser than it should have been.** The combination justifies:

> "This exact file, with this exact independently-hashed content, existed on disk before this process began; the process's own self-report is consistent with having a loaded module associated with this path; and at least one independently-specified behavioral test, run by the live process against a real system call, produced a result that only this file's known content — and not the only other known version compared against it — could explain."

**It does not, and must never be worded to, justify**: "the exact bytecode currently executing in memory was compiled from these exact bytes" (that requires the bytecode comparison this mission's Phase 7 deliberately excludes, §12) — nor "no other, unconsidered, third version of this file could also explain the observed behavior" (§3 claim 13's own limit). **The predecessor design's §7 (`VERIFIED = (a)+(b)+(c)+(d)`) is technically defensible but under-specifies its own scope this precisely** — this mission's one required change to that contract (§5) is to attach this exact, narrower proposition as the literal meaning of `VERIFIED`, not a looser "the runtime is running current code" gloss.

**Q3 — Edge cases, answered individually, not generically:**

| Case | What happens under this design |
|---|---|
| Source edited after process startup | `mtime_precedes_process_start` flips to `false` → condition (c) fails → ceiling is `SUPPORTED`, correctly, and the reconciliation should additionally flag a **Type D** candidate (runtime may not match working tree) rather than silently degrading. |
| Source replaced, mtime preserved | **Undetectable by this design as specified.** A real, disclosed residual gap — the mtime heuristic and the content hash together cannot catch a same-mtime, different-content swap unless a *prior* reconciliation's hash was independently recorded and can be compared against (see §6's `evidence_id` requirement — this is precisely why every reconciliation must be individually hashed and timestamped, so a later investigator *can* notice a discontinuity, even though the live system cannot detect it in the moment). |
| mtime changes, content unchanged (e.g. `touch`) | `sha256` stays identical (claim 3/4 unaffected — correctly still shows `modified_vs_head` unchanged), but `mtime_precedes_process_start` may flip to `false` incorrectly. **This is a false-negative risk, not a false-positive one** — the system would under-claim confidence (deny `VERIFIED` when it could honestly have been granted), the safe failure direction, but worth naming precisely rather than left as an unstated quirk. |
| Dynamically generated module | No real `__file__` → Type E by the design's own taxonomy, correctly handled as an honest `UNKNOWN`, not forced into a stronger label. |
| `exec()`'d code | Frequently never enters `sys.modules` under any stable name at all — falls outside claims 8/9's scope entirely, not merely Type E; the reconciliation should report `module_loaded: false` honestly rather than attempting a match. |
| Module loaded from an unexpected path (outside the repo) | The reconciliation must refuse to attempt a Git/working-tree comparison at all in this case — comparing a `site-packages` module's path against this repository's Git history is a category error, not a discrepancy; **fails closed to `UNKNOWN`, out of scope**, not a Type A/B/C classification. |
| Symlinks | Must be resolved (`os.path.realpath`) **before** every comparison in every layer, consistently — the design's Git-layer section (Mission 18 §8) already specifies this for path *validation*; this mission's finding is that the same normalization must also apply to the working-tree↔runtime path join specifically, which the predecessor design did not call out this explicitly. |
| File deleted after import | `working_tree_file_identity` correctly reports `exists: false`; `runtime_module_origin`'s self-report can still say `module_loaded: true` (Python keeps compiled modules in memory after their source file vanishes) — this is a **real, distinct case**, not the same as "module never existed," and the reconciliation object must have a way to express "working tree says gone, runtime self-report says still loaded" without collapsing it into either a plain Type B or Type A label. |
| Module reloaded (`importlib.reload()`) | Well-covered *if* the reload followed a real content change (the mtime check would correctly flip); **not** covered if reloaded with byte-identical content (same limitation as the "touch" case, harmlessly). This project's own F1 AST scanner already blocks `importlib.reload` inside the self-edit sandbox specifically to prevent patch-undoing (re-confirmed via `CLAUDE.md`'s documented F1 rule set, not re-grepped fresh this pass) — production code calling `importlib.reload()` on itself was not exhaustively re-searched for in this mission and is recorded as a disclosed assumption, not a proven absence, matching the leaf-primitives validation's own identical disclosure. |
| Old process still serving requests | This is exactly claims 6/7's job — a stale server is caught by comparing the currently-observed PID/start-time against whatever the caller independently expected, not by anything in the module-origin layer at all. Named as its own dedicated test case (§9, Case L). |
| Runtime module path points to a file now containing different bytes | This is a **time-ordering** problem, not an evidence-quality problem: every `reconcile()` output is valid only as of its own recorded timestamp. A caller reusing a stale reconciliation result to make a claim about "now" is a **misuse of the interface**, not a flaw in it — §8 states this as an explicit rule. |

**Q4 — Does the design accidentally treat `mtime < process_start` as stronger than it really is?**

**Yes, mildly, and this mission's one recommended wording change is here.** The predecessor design lists it as condition (c), on equal visual footing with the other three — but per Q3's table, it is best understood as **the absence of one specific disqualifying signal**, not affirmative evidence in the same sense as a hash match or a behavioral test result. **Recommended reframing**: rename the condition from *"file mtime precedes process start"* (stated as a positive fact) to ***"no evidence of post-startup source modification found"*** (stated as the absence of a specific, narrow red flag) — functionally the same boolean, but the wording change correctly signals to a future reader (human or Echo) that passing this condition is necessary-but-weak, never sufficient, and specifically never proof against the two undetectable cases in Q3's table (content-preserving replacement; false-negative touch).

**Q5 — Does the behavioral fingerprint establish source provenance, or only behavioral equivalence?**

**Only behavioral equivalence — precisely, equivalence to the specific known candidate(s) actually compared against, never a positive identification of source bytes in the abstract.** Stated with the exact distinction the mission asked for: `os_fd0_blocked: true` proves the running process, when asked to perform a real `os.close(0)` and a real `os.read(0, ...)`, produced results consistent with the working-tree implementation's code and inconsistent with HEAD's (which has no code path capable of producing that field at all, confirmed by direct grep in the leaf-primitives validation). **It does not prove no other possible implementation — one never written, or written by someone else, or a third historical version — could also produce that exact result.** This is a real, structural ceiling on what any behavioral test can establish: it discriminates among the hypotheses you actually formed and checked, never among all hypotheses that could exist. Two different implementations genuinely can, in principle, produce identical observable behavior for a given check — the design's own §9's Type F category exists precisely because this is possible, not merely a theoretical nicety.

**One further, load-bearing distinction found in this pass, not previously named this precisely in either predecessor report**: a behavioral fingerprint and a `sys.modules` self-report are *both*, technically, information originating from the same process — but they are not epistemically equivalent kinds of self-report. `sys.modules[name].__file__` is a **passive lookup** of stored state (the process recalling something it noted once, at import time, and has not re-verified since). `os_fd0_blocked: true` is the **result of the process actually executing a real system call against a real kernel and observing what happened**, moment-by-moment, at query time — closer to a fresh experiment's outcome than a recollection. Both are still first-party (the same trust boundary applies to both — a compromised or buggy process could fake either), but the behavioral-test kind is structurally harder to be *accidentally* wrong about, since it requires the real underlying code path to actually execute correctly at the moment of the check, not merely that a variable was set correctly once and never touched again. **The reconciliation schema (§6) should preserve this distinction as a labeled field, not collapse both into one undifferentiated "self-report" bucket.**

---

## 5. Epistemic-Label Contract

Final, attacked-and-surviving version, replacing the predecessor design's §7 verbatim text with the precision established in §4:

- **`VERIFIED`** requires **all** of: (a) working-tree symbol/file check passes (an externally, independently checkable fact — §3 claims 1–4, 10-A); (b) `runtime_self_reported_module_origin`'s path matches the queried path (self-report — §3 claim 9; necessary, never alone sufficient); (c) no evidence of post-startup source modification found (Q4's reframed wording — necessary, weak, never alone sufficient); **and** (d) at least one behavioral-test result, run by the process against real system behavior, that the compared alternative (typically HEAD) is structurally incapable of producing (§3 claim 11). **The resulting claim's exact meaning is the Q2 proposition, verbatim — never loosely restated as "running current code."**
- **`SUPPORTED`** — (a)–(c) hold, (d) unavailable or not attempted for this subject. This is expected to be the common case, per the design doc's own honest disclosure that behavioral fingerprints are subject-specific and require hand-curated mappings, not a general mechanism.
- **`INFERRED`** — only (a) or only (b)/(c) hold in isolation, with the others genuinely unknown (not failed — unknown), e.g. a working-tree symbol check succeeded but the module could not be queried at all (no route reached it).
- **`UNKNOWN`** — module path outside the repo, dynamically generated code, or any Q3 case explicitly flagged as out-of-scope.
- **`DISPROVEN`** — a behavioral test result contradicts the expected implementation, or a prior recorded claim's `evidence_id` no longer matches a fresh re-check.

**Verdict on the contract itself**: sound, within this project's own already-accepted evidentiary bar (the same bar `liveness_ledger.py`'s 52 existing checks already run on — first-party self-report plus behavioral testing, no external adversarial-verification layer) — provided the wording changes in Q2 and Q4 are applied, and provided (§8) `VERIFIED` is never computed or asserted by the same code path that generated the underlying self-report being evaluated.

---

## 6. Proposed API Boundary

**Reused, not automatically preserved — each function re-justified:**

```python
def working_tree_file_identity(path: str) -> dict:
    """
    KEPT, unchanged in shape. Fully externally-observable (§3 claims 1-4).
    Read-only: os.stat, hashlib.sha256, git -C <repo> ls-files/show (read-only subcommands only).
    Never executes arbitrary code. Safe for Echo to call directly (no side effects).
    Returns: {path, exists, tracked, size, mtime (ISO8601), sha256,
              head_blob_sha256_or_none, modified_vs_head (bool or None)}
    Error behavior: exists=False short-circuits the rest to None/False, never raises.
    Path validation: routed through the exact same _guard_read_path()-style
      root-confinement echo_tool_dispatch.py already uses -- not reinvented.
    """

def runtime_process_identity() -> dict:
    """
    KEPT, narrowed. In-process only (os.getpid(), psutil.Process().create_time(),
    os.getcwd(), sys.executable -- all confirmed available in the target environment).
    listening_ports DROPPED from the required return shape -- narrowed to
      best-effort/optional (see rationale below), since it is not needed by any
      claim in the evidence matrix (§3) and its cleanest implementation
      (psutil.Process().net_connections()) is a materially different kind of
      self-query than the other three fields.
    Read-only, zero arguments, zero external input -- cannot execute arbitrary code
      by construction (no code path accepts a caller-supplied string).
    Returns: {pid, start_time (ISO8601), cwd, executable}
    """

def runtime_self_reported_module_origin(module_name: str) -> dict:
    """
    RENAMED from runtime_module_origin() -- the new name encodes the self-attestation
    finding (§4 Q1) directly into the API surface, so a future caller (human or Echo)
    cannot invoke this function without its own name stating what kind of evidence
    it returns. This is the one function in this design that MUST run in-process
    (§4 Q1's empirical finding) -- it is architecturally impossible to implement
    any other way, and the rename makes that impossibility visible at every call site.
    Argument validated against the real, current sys.modules key list -- never
      passed through to importlib from caller-supplied text (no import ever occurs;
      this function only ever performs a dict lookup on modules already loaded by
      FeralEcho's own normal startup).
    Read-only (a dict .get() and an attribute read). Cannot execute arbitrary code.
    Returns: {module_name, loaded (bool), file_path (str or None)}
    Trust assumption, stated explicitly in the docstring itself, not just this
      report: this function's return value is self-report. It is not, and must
      never be treated as, independent confirmation of anything.
    """

def reconcile(path: str, module_name: str | None = None, symbol: str | None = None) -> dict:
    """
    KEPT, contract tightened. Pure composition of the three functions above plus
    (when available) a behavioral-fingerprint lookup (see the curated table, §9).
    NEVER writes to self_model_claims.py or any other persistent store -- this
      function computes and returns a ProvenanceObservation (§7); persisting one
      is a SEPARATE, explicit, caller-driven action (see §9's record_provenance_claim,
      not this function), matching self_model_claims.record_claim()'s own existing
      contract that a caller supplies an already-independently-computed `verified`
      value -- reconcile() IS that independent computation, never its own recorder.
    Computes `relationship` (the discrepancy-taxonomy label, Type A-G) and
      `epistemic_label` (§5's VERIFIED/SUPPORTED/INFERRED/UNKNOWN/DISPROVEN) from
      the sub-results -- never accepts either as a caller-supplied argument.
    Read-only overall (every function it calls is read-only). Cannot execute
      arbitrary code.
    Safe for Echo to call directly, with the understanding that its OUTPUT is not
      automatically a self-model claim -- see §10.
    """
```

**No new function added beyond the design's original four** — the rename (`runtime_module_origin` → `runtime_self_reported_module_origin`) and the narrowing (`listening_ports` dropped from the required shape) are the only structural changes this mission recommends.

---

## 7. Reconciliation Object

Sharper than the predecessor design's schema, specifically to prevent the confusion Phase 8 names — external evidence, self-report, behavioral evidence, and interpretation are now four visibly separate top-level keys, never blended:

```json
{
  "query": "reconcile",
  "subject": {"path": "app/core/liveness_ledger.py", "module": "app.core.liveness_ledger", "symbol": null},
  "timestamp": "2026-09-11T21:37:37Z",
  "evidence_id": "sha256(query+subject+external_evidence+runtime_self_report+behavioral_evidence+timestamp)",

  "external_evidence": {
    "git": {"head_sha": "e92ec3b7...", "blob_exists": true, "blob_sha256": "f09a146c..."},
    "working_tree": {"exists": true, "tracked": true, "sha256": "cdd82f03...", "mtime": "...",
                       "no_evidence_of_post_startup_modification": true, "modified_vs_head": true}
  },

  "runtime_self_report": {
    "process_pid": 7644,
    "process_start_time": "2026-09-10T22:41:53-07:00",
    "module_loaded": true,
    "module_file_path": "/Users/.../app/core/liveness_ledger.py",
    "_epistemic_note": "Everything in this object is first-party self-report.
                          It has no independent external witness (see report §4 Q1).
                          Never promote a field from this object to VERIFIED on its own."
  },

  "behavioral_evidence": {
    "checked": true,
    "source": "GET /admin/liveness-status, field f2_stdin_contract",
    "distinguishing_field": "os_fd0_blocked",
    "observed_value": true,
    "compared_against": ["HEAD"],
    "result": "HEAD structurally incapable of producing this field (confirmed via git grep)",
    "_epistemic_note": "This is behavioral equivalence to the specific compared
                          candidate(s) listed above, not universal source-identity proof
                          (see report §4 Q5)."
  },

  "reconciliation": {
    "relationship": "WORKTREE_MODIFIED",
    "epistemic_label": "VERIFIED",
    "label_basis": ["external_evidence.working_tree matches claim 4",
                     "runtime_self_report.module_file_path matches subject.path",
                     "external_evidence.working_tree.no_evidence_of_post_startup_modification",
                     "behavioral_evidence.result confirms exclusive match among compared candidates"]
  }
}
```

**Required fields**: `query`, `subject`, `timestamp`, `evidence_id`, `external_evidence`, `runtime_self_report`, `reconciliation.relationship`, `reconciliation.epistemic_label`. **Optional**: `behavioral_evidence` (absent entirely, not null-filled, when no fingerprint exists for the subject — an absent key is a cleaner "not attempted" signal than a null-valued one). **`label_basis`** is new relative to the predecessor design — an explicit list naming which sub-facts the composed label actually rests on, so a future reader never has to reverse-engineer why a label was assigned.

**How this connects to `self_model_claims.py` without a second ledger**: `reconcile()`'s output is never written directly. A separate, explicit call — `self_model_claims.record_claim(subject=f"provenance:{path}", verified=(result["reconciliation"]["epistemic_label"] == "VERIFIED"), evidence=json.dumps(result), proposed_by="reconcile_output", verified_by="provenance_reconciliation")` — persists it through the **existing** ledger. This satisfies `record_claim()`'s own structural invariant (`proposed_by != verified_by`) cleanly, since the two strings are genuinely different identifiers for genuinely different roles (the raw computed evidence vs. the reconciliation process that decided the label) — not a workaround, a correct application of the existing contract. **`evidence` carries the full JSON, not a one-line summary** — a deliberate departure from most of this ledger's other current writers (which tend to write short prose), justified because provenance claims specifically need their full evidence trail preserved for exactly the kind of audit this report itself is performing.

---

## 8. Existing Integration Points

**1. `echo_tool_dispatch.py`.** Exact pattern: `TOOL_SCHEMAS` (a list of JSON-schema dicts) feeds Ollama's `/api/chat` tools parameter; `_execute_tool()` is a flat, hardcoded `if name == "...":` chain (re-read this session, unchanged from prior passes). A hypothetical 4th tool, `check_provenance`, would add one entry to each — no architectural change, following the identical shape `read_file`/`search_memory`/`log_thought` already establish. **Repo confinement** is enforced today via `_guard_read_path()`, reused as-is by `working_tree_file_identity()` (§6). **Read-only guarantees** are enforced by construction (no write-capable stdlib call anywhere in the proposed functions), the same posture as the three existing tools. **Not modified this mission.**

**2. `echo_ground_truth.py`.** Exact pattern confirmed by direct re-read: `_relevant_slices()` returns a `set[str]`, and a uniform `if "<slice>" in slices: sections.append(_build_<slice>())` chain assembles the final block. A hypothetical `_build_provenance()` would need exactly one new `if "provenance" in slices:` line plus a new keyword-trigger addition to whatever regex/list feeds `_relevant_slices()` — the existing architecture already fully supports this integration with zero new plumbing. **Whether a new path is actually needed**: no — this is the correct, already-proven existing path, not a case requiring new infrastructure. **Not modified this mission.**

**3. `self_model_claims.py`.** `record_claim(subject, verified, evidence, proposed_by="echo_response", verified_by="self_knowledge_verification")` — re-read in full this session. The **existing ledger is sufficient** (§7 above) — no new persistence layer is justified. `proposed_by != verified_by`'s existing structural guard interacts cleanly with a provenance claim exactly as described in §7 — no change to this module's own logic is needed, only a new *caller*. **Not modified this mission.**

**4. `self_knowledge_verification.py`.** **A genuinely important finding from this pass's own re-read, not previously surfaced this precisely**: this module **already implements a live check-count verification** — `find_check_count_claim()` extracts a claimed Liveness Ledger check-count from Echo's own generated text and compares it against `self_model.json`'s cached `verified_capabilities.checks` count, returning a tri-state `(caveat, verified)`, wired into the real response pipeline at `app/routes_echo_studio.py:250`. **This is the closest existing thing to the new capability — and it is weaker than what `reconcile()` would provide**, because `self_model.json`'s count is a periodically-refreshed cache (updated by `SelfModelUpdater`'s background loop, not computed fresh at claim-time), whereas `reconcile()` is proposed as a fresh, per-query computation. **Recommendation: this module should remain independent for now, not be merged with the new capability** — it solves a narrower, already-working problem (catching one specific claim shape) using an already-proven, lower-cost mechanism (a cache read, not a live multi-layer reconciliation); a future mission could extend it to consult `reconcile()`'s fresher result for check-count claims specifically, but that is explicitly **out of scope** for this design gate (§12) — grafting a new, heavier mechanism onto a working, cheap one without a demonstrated need to would be exactly the kind of premature integration this project's own standing discipline warns against. **Not modified this mission.**

**5. Behavioral fingerprint machinery.** No new framework is proposed or needed — `GET /admin/liveness-status` already exists, is already safe, and already returns exactly the kind of structured field (`os_fd0_blocked: true`) a fingerprint lookup needs. The only new artifact is a small, hand-curated, static mapping table (subject/module → which liveness check to read → which field/value uniquely distinguishes which known version) — data, not a mechanism, matching the design's own §9 characterization, independently re-confirmed accurate by this mission.

---

## 9. Behavioral Fingerprint Treatment

Represented as evidence per the §7 schema's `behavioral_evidence` block — no new test harness, no new endpoint, no new check added to `liveness_ledger.py`. The curated table (illustrative, not exhaustive, not implemented):

| Subject | Liveness check | Distinguishing field | HEAD value | Working-tree value |
|---|---|---|---|---|
| `sandbox/safe_exec_wrapper.py` (`_install_patches`) | `f2_stdin_contract` | `os_fd0_blocked` | *field absent — structurally impossible, confirmed via git grep* | `true` |
| `run.py` (`admin_restore`) | `restore_council_gate` | check presence itself (the check name does not exist in HEAD at all) | *check absent* | `pass: true` |

Each row is a hand-verified, one-time fact (confirmed once per subject, not derived generically) — exactly matching §4 Q5's disclosed limit: this evidence discriminates only among the specific, named candidates a human explicitly compared, never universally.

---

## 10. Anti-Self-Attestation Rule

**The exact boundary, stated as a rule, not a suggestion:**

> **`reconcile()`'s output is an *observation*. A self-model claim is a *conclusion*. No code path may treat the former as automatically constituting the latter.**

Concretely: `reconcile()` (§6) never calls `self_model_claims.record_claim()`. A **separate**, explicit line of code — outside `reconcile()`, written by whoever eventually implements this — performs that call, passing `verified = (reconcile_result["reconciliation"]["epistemic_label"] == "VERIFIED")` as an argument `record_claim()` receives, never computes itself. This is not a new mechanism — it is `self_model_claims.py`'s **already-existing** invariant (`proposed_by != verified_by`, checked and enforced today, re-read in full this session) applied correctly to this new evidence source: the "proposer" role is filled by the raw `reconcile()` output; the "verifier" role is filled by the code that inspects that output's `epistemic_label` field and decides whether it clears the bar — two textually and logically distinct pieces of code, never the same function, even though both run in the same process.

**Named fields, matching the mission's own suggested shape, already present in §7's schema rather than needing new ones**: `runtime_self_report` (observation), `behavioral_evidence` (observation), `reconciliation` (conclusion) — the existing three-way schema split already satisfies this rule structurally; **no additional field is needed** beyond what §7 already specifies. This is a case where the existing design (once the §5/§7 tightening in this report is applied) already supports the anti-self-attestation rule cleanly — over-engineering it with a fifth or sixth field would violate the mission's own "do not over-engineer if existing structures already support this cleanly" instruction.

---

## 11. Test Matrix

| Case | Evidence collected | Reconciliation status | Epistemic label | May Echo use this to update a self-model claim? |
|---|---|---|---|---|
| **A** — HEAD == WT == runtime | Full match across all three layers, no discrepancy | `HEAD_MATCH` | `VERIFIED` (or `SUPPORTED` if no behavioral fingerprint exists for this subject) | Yes, via the separate recording step (§10) |
| **B** — WT ≠ HEAD, runtime matches WT | Working-tree diff confirmed; self-report path matches; behavioral fingerprint (if available) confirms WT | `WORKTREE_MODIFIED` | `VERIFIED` if (d) available, else `SUPPORTED` | Yes, with the label attached |
| **C** — WT ≠ HEAD, runtime matches HEAD | Working-tree diff confirmed; self-report/behavioral evidence points to HEAD's behavior instead | `RUNTIME_MATCHES_HEAD` (a real, distinct relationship value not explicit in the predecessor's original taxonomy — worth adding) | `SUPPORTED` at best (self-report can't independently *prove* it's really HEAD's exact bytes either) | Yes, but the claim must say "runtime appears to predate the working-tree edit," not "runtime matches HEAD" unqualified |
| **D** — runtime matches neither | Both comparisons attempted and both failed | `RUNTIME_UNEXPLAINED` (Type F, the highest-severity case) | `DISPROVEN` (against whichever claim was being tested) or `UNKNOWN` (if no claim was being tested, just an observation) | **No** — this result should itself trigger flagging for human review, not a routine claim update |
| **E** — runtime self-report unavailable | `module_loaded: false` or the function couldn't reach the process at all | `RUNTIME_UNEXPLAINED` or a dedicated `RUNTIME_UNREACHABLE` status | `UNKNOWN` | No |
| **F** — behavioral fingerprint succeeds | Full (d) available | (whatever the other layers indicate) | Ceiling raised to `VERIFIED` if (a)-(c) also hold | Yes |
| **G** — behavioral fingerprint fails/unavailable | (d) absent, not attempted, or attempted and inconclusive | (whatever (a)-(c) indicate) | Ceiling capped at `SUPPORTED` | Yes, labeled `SUPPORTED` explicitly |
| **H** — mtime ambiguous (Q3's "touch" case) | `no_evidence_of_post_startup_modification: false` despite `sha256` unchanged from a prior known-good record | `WORKTREE_MODIFIED`-shaped uncertainty | `SUPPORTED`, with `label_basis` explicitly noting the mtime signal is the weak link | Yes, but conservatively labeled |
| **I** — source modified after process startup | `no_evidence_of_post_startup_modification: false`, genuinely (not a touch false-negative) | `RUNTIME_MATCHES_HEAD`-shaped or `RUNTIME_UNEXPLAINED`, depending on behavioral result | `SUPPORTED` at best, likely `UNKNOWN` for the "is runtime current" half of the question | No, for the "is this current" question specifically — yes for the narrower "does HEAD differ from working tree" question, which is unaffected |
| **J** — module path and Git path disagree (symlink or unexpected-location case) | Self-report path doesn't normalize to anything the Git layer recognizes | `RUNTIME_UNEXPLAINED` or explicitly out-of-scope | `UNKNOWN` | No |
| **K** — dynamic/anonymous code | No real `__file__`, or no `sys.modules` entry at all | Explicitly out-of-scope, not forced into any of the A-G relationships | `UNKNOWN` | No |
| **L** — stale running server (claim 6/7 mismatch) | PID/start-time don't match what the caller expected | Not a subject-provenance question at all — a process-identity failure, checked *before* attempting any reconciliation | N/A — reconciliation should refuse to proceed, reporting the identity mismatch directly | No |

---

## 12. Explicit Exclusions

| Excluded | Why |
|---|---|
| Bytecode comparison | Real, safe, more rigorous — genuinely possible per the leaf-primitives validation's own concrete demonstration — but adds real design work (decorators, closures, `co_filename` differences, compiler-version effects) not needed to satisfy this project's own already-accepted evidentiary bar (§5). Revisit only if a real incident demonstrates the behavioral-fingerprint ceiling is insufficient. |
| Debugger attachment | Explicitly forbidden by the mission and the design; also unnecessary — every fact needed is available through ordinary, safe introspection once the code is correctly placed in-process. |
| Process injection | Same as above; also directly contradicts this project's own F1/F2 sandboxing philosophy (never grant a mechanism more access than the narrowest capability that serves the actual need). |
| Arbitrary introspection / generic reflection API | The whole point of this design is four narrow, named, fixed-shape functions — a generic `inspect(anything)` capability is exactly the `ToolManager`-shaped mistake §2 already flags as a known dead-end pattern in this exact codebase. |
| Arbitrary module import | `runtime_self_reported_module_origin()` only ever performs a `sys.modules.get()` lookup — it must never call `importlib.import_module()` on caller-supplied text, which would be a real code-execution vector disguised as introspection. |
| Automatic reload | Out of scope entirely — this design observes provenance, it does not and must never *fix* a discrepancy by reloading anything. |
| Process restart | Same reasoning; also explicitly forbidden by every mission in this series. |
| Git mutation | Never in scope for this thread (Mission 18's own D-003, reaffirmed every mission since). |
| New persistence layer | §7 already establishes the existing `self_model_claims.jsonl` suffices — a second ledger would duplicate, not strengthen, the existing invariant. |
| New Flask route | The recommended integration path (§8, item 1) is `echo_tool_dispatch.py`'s existing in-process pattern, which has no independent unauthenticated network surface — a new route would reopen exactly the `GET /projects/file` risk class this design has consistently avoided across all three predecessor reports. |
| Generic dynamic tool registry | `ToolManager` is confirmed, repeatedly, across this entire research corpus, to be structurally dead — never build on it. |
| Automatic "latest code" claims | This is the mission's own central concern (§10) — nothing in this design may ever assert this without the full, explicit evidence chain attached, and no automated process may generate such a claim unprompted. |

---

## 13. Implementation Sequence

*(Specified per this mission's own audit findings — not the example template. No step in this sequence requires restarting PID 7644; all four leaf functions and the composer are pure, stateless computations importable into an already-running process only at its *next* natural restart, consistent with this codebase's own standing convention that code changes take effect on the next deploy, never hot-reloaded.)*

1. **`working_tree_file_identity(path)`** — file: new `app/core/provenance_check.py`. Purpose: §3 claims 1-4. Dependency: none beyond stdlib + `git` CLI. Risk: lowest of the four (fully externally verifiable, already independently reproduced twice this session). Test: exact reproduction against the same 7 files this mission's own predecessors already hand-verified — a regression test with a known-correct expected output, not a fresh unknown.
2. **`runtime_process_identity()`** — same file. Purpose: §3 claims 6-7. Dependency: `psutil` (already installed in the target environment, confirmed this session — no new dependency to add). Risk: low; `listening_ports` deliberately excluded from the first slice (§6) to avoid its one genuinely open sub-question.
3. **`runtime_self_reported_module_origin(module_name)`** — same file. Purpose: §3 claims 8-9. Dependency: none beyond stdlib. Risk: the one function requiring careful review before merging, specifically because of §4's findings — recommend this function's docstring itself carry the `_epistemic_note` language from §7's schema, not just this report.
4. **A small, hand-curated behavioral-fingerprint table** (§9) — same file or a small sibling data file. Purpose: enables `(d)` in §5's contract for the ~2 subjects currently known to support it. Risk: low, purely additive; explicitly not a generic mechanism (§12).
5. **`reconcile(path, module_name, symbol)`** — same file, composing 1-4. Purpose: §3 claim 15, the full schema in §7. Dependency: 1-4. Risk: medium — this is where the `relationship`/`epistemic_label` decision logic lives, and §5/§11's contract must be implemented exactly, not approximately (a good target for `feral-independent-review` once built, per this project's own standing skill for exactly this kind of gate).
6. **Regression tests against §11's twelve cases** — before any integration, using constructed/mocked inputs for the cases (D, E, H, I, J, K, L) that cannot be produced from the current, healthy repository state.
7. **Wire into `echo_tool_dispatch.py`** as a 4th tool (§8 item 1) — the smallest possible integration surface, reachable only from Echo's own existing, already-safe tool-calling loop.
8. **Wire the persistence step** (§10's separate, explicit `record_claim()` call) — deliberately sequenced *after* the tool integration, not before, so the recording logic can be tested against real tool-call outputs rather than synthetic ones.
9. **Only then**, and only if separately authorized: consider `echo_ground_truth.py`'s `_build_provenance()` slice (§8 item 2) — broader exposure, correctly sequenced last since it's the highest-visibility integration point and should only happen once 1-8 have already been through at least one independent review cycle.

**Explicitly not sequenced in this list, per §12**: any Flask route, any bytecode comparison, any change to `self_knowledge_verification.py`.

---

## 14. Final Recommendation

## PROCEED TO IMPLEMENTATION

The boundary is precise, the self-attestation trap has an explicit, structurally-enforced (not merely documented) rule preventing it (§10, reusing `self_model_claims.py`'s already-proven invariant rather than inventing a new one), and every function in the proposed API has either full external verifiability (`working_tree_file_identity`, most of `runtime_process_identity`) or an explicit, unmissable name and docstring marking it as self-report (`runtime_self_reported_module_origin`). The evidence contract survived direct attack (§4) with one wording tightening (Q2, Q4) rather than a structural redesign.

**Smallest first implementation slice, not "everything at once"**: **Step 1 alone** — `working_tree_file_identity(path)` in a new `app/core/provenance_check.py`, with no dependency on any of the other three functions, no wiring into `echo_tool_dispatch.py` yet, no ledger integration yet. It is the only one of the four primitives with zero self-attestation exposure, zero new dependency, and an already-twice-independently-reproduced correct implementation to build from directly. Everything from Step 2 onward should be its own, separately-reviewed follow-up, not bundled into the same change.

---

## 15. Mutation Statement

```
Git HEAD before:                e92ec3b7fe4743f75746d161a06601db0232bff2
Git HEAD after:                  e92ec3b7fe4743f75746d161a06601db0232bff2   (unchanged)
Uncommitted path count before:   99
Uncommitted path count after:    100 (before this report's creation) -- reflects only this
                                  new report file once written
Files modified:                  none
Files created:                   audits/2026-09-11_provenance_implementation_boundary_audit.md
                                  (this file, the only persistent artifact from this mission)
Processes restarted:              none
Processes stopped:                none
Modules reloaded:                 none
Git mutations performed:          none (no commit, no checkout, no reset, no rebase, no branch,
                                   no push, no config change)
PID 7644:                         unchanged -- same PID, same start time (Thu Sep 10 22:41:53 2026),
                                   confirmed alive and responsive at both the start (§1) and via
                                   the same uninterrupted uptime observed throughout this mission
```
