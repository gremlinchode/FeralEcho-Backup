# Read-Only Three-Layer Provenance Interface — Design Report

**Date:** 2026-09-11
**Type:** Design + feasibility investigation only. Nothing described here was built. No production file was modified, no route added, no tool registered, no process started or restarted, no Git state changed.
**Trigger**: the three archaeology passes (`audits/2026-09-10_research_arc_provenance_audit.md`, `_phase2_provenance_reconciliation.md`, `2026-09-11_three_layer_provenance_reconciliation.md`) established, with direct evidence, that Git HEAD, the working tree, and the running process can and currently do disagree — concretely, `restore_council_gate` (absent from HEAD, present and executing in the working tree) and `temporal_environment.py:get_location()` (present in HEAD, removed from the working tree). This report asks: what is the smallest safe mechanism that would let Echo itself ask and answer those same three questions about its own implementation, on demand, without trusting its own memory of the answer?

---

## 1. Executive Conclusion

FeralEcho already has three of the five pieces this interface needs, independently built by three different missions that never cross-referenced each other — this is itself the report's first finding, not just context. What's missing is narrow: a small set of **working-tree** and **runtime** read primitives (the Git layer is already fully designed, `audits/2026-09-11_read_only_git_provenance_design.md`, Mission 18) and one **composition function** that reconciles all three layers into a single evidence object and writes it through the ledger mechanism that already exists for exactly this purpose (`app/core/self_model_claims.py`).

**The recommended design is 4 read-only primitives plus 1 reconciliation composer — not a new subsystem.** Three of the four primitives are `READY` today with zero new code (pure Python introspection, already-safe by construction); one requires a small new read-only admin endpoint. The hardest problem (§6) is not security — it's that Python does not retain a module's original source text after compiling it, so "this is definitely the exact code executing" has a real, disclosed epistemic ceiling below 100% certainty, reachable only via bytecode-level comparison, which this design deliberately does not require for an everyday `VERIFIED` label.

---

## 2. Existing Architecture Relevant to Provenance

*(Phase 1 — inspected, not redesigned.)*

**1. Existing relevant interfaces:**
- `app/core/echo_tool_dispatch.py` — the project's own proven safe-tool-dispatch shape: `DISPATCH_MODEL` selects among 3 hardcoded tools (`read_file`, `search_memory`, `log_thought`) via a fixed `if/elif` in `_execute_tool()` (line 302), never a dynamically-extensible registry. `_guard_read_path()` (line 174) confines reads to `_PROJECT_ROOT`. This is the correct template for any new tool, Git or otherwise — confirmed by both this report's own reading and Mission 18's independent arrival at the same conclusion.
- `app/core/tool_manager.py` / `awareness_tools_integration.py` — a real, live, **structurally dead** dynamic tool registry (`research/FINDINGS.md` R-005: genuinely scans and registers tools, but nothing anywhere ever calls a registered tool's function). **Do not build on this** — it would inherit the "looks wired, isn't" property this project's own research has already found once, in this exact subsystem.

**2. Existing evidence/provenance conventions:**
- `app/core/liveness_ledger.py`'s `_result(passed, evidence, extra=None) -> dict` (line 175) — the shape all 52 live checks return: `{"pass": bool, "evidence": str, "checked_at": iso_timestamp, ...extra}`. This is the project's own de facto evidence-object standard, proven at scale (52 independent uses), and the natural base to extend rather than replace.
- `app/core/self_model_claims.py`'s `record_claim(subject, verified, evidence, proposed_by, verified_by)` (line 89) — an append-only ledger (`memory/self_model_claims.jsonl`) with a **structural, code-enforced invariant**: `proposed_by != verified_by` is checked and the write refused otherwise (line 101–109) — Echo's own text can never certify itself. This is precisely the "evidence ledger written before interpretation, never trusting the model's self-report" mechanism Mission 18's Section 5 proposed inventing from scratch (as `memory/git_evidence_ledger.jsonl`) — **without apparently knowing this module already existed**. Both were built by different missions in the same short window (`self_model_claims.py`: 2026-09-08; Mission 18's design doc: 2026-09-11) and never cross-referenced each other. This is a real, concrete instance of the exact "research-corpus internal non-integration" pattern the prior archaeology passes already flagged for other threads (task-type-classifier, Codex relay) — now found inside the provenance-design thread itself.
- `app/core/self_knowledge_verification.py` — already checks Echo's own *stated claims* against ground truth, including, specifically, `find_check_count_claim()` (a regex for a liveness-check-count number in generated text) and `has_council_gates_self_edit_claim()` (a specific, already-known-false architectural claim). This is the closest existing thing to "catch Echo claiming something about its own implementation and verify it" — narrower than what this design proposes (it checks against `self_model.json`'s cached snapshot, refreshed every ~130s from background telemetry, not a live three-layer reconciliation), but the correct integration point for wiring a *new* check into, not a reason to build a second, parallel claim-verification path.

**3. Existing read-only filesystem capabilities:** `echo_tool_dispatch.py`'s `_guard_read_path()`/`_tool_read_file()`; `routes_echo_studio.py`'s `_safe_resolve()` + `_EXCLUDED_DIR_NAMES` + `_looks_like_secret_dump()` (an HTTP route, unauthenticated — Mission 18 already flagged this as the wrong template to copy for a new capability, and this report agrees).

**4. Existing Git access:** **None**, confirmed by direct grep this session (`import git`, `GitPython`, `subprocess.*git` — zero matches in any Echo-reachable path). Mission 18's design (six hardcoded, allowlisted `git` subcommand wrappers, Section 4 of that document) is complete, unimplemented, and does not need to be redesigned here — it is reused as-is below.

**5. Existing runtime introspection capabilities:** `app/core/introspection_channel.py` (a 120s background collector — RAM, FAISS count, Ollama process liveness — but never module/source identity), `app/core/liveness_ledger.py` itself (the closest thing to "does this specific mechanism actually work," but scoped to *behavioral* checks, not *source-identity* checks), `GET /admin/liveness-status` (the one already-existing, already-safe, read-only HTTP surface this report's own prior passes used to fingerprint-match runtime behavior against source — see §6).

**6. Existing mechanisms for recording evidence:** `self_model_claims.py` (above) — the clear, already-correct home for this.

**7. Potential integration point:** `echo_ground_truth.py`'s `_build_architecture()` (reuses `CartographerDB.architecture_summary()`) is the existing self-referential-architecture-question pathway — the natural place a future "am I running current code?" question would be routed from, the same way `_build_affect()`/`_build_council()`/`_build_capabilities()` already route other self-referential question classes to their own grounded slices.

**8. Architectural boundary that must not be crossed:** `ToolManager`'s dynamic registry (item 1); any Flask-route-based implementation inheriting `GET /projects/file`'s unauthenticated pattern by default (Mission 18 Section 2/13, independently re-confirmed here); any general `git(*args)`/`subprocess.run(cmd, shell=True)` passthrough of any kind.

---

## 3. Minimum Required Primitives

**Git layer — reused verbatim from Mission 18, not redesigned:**
```
git_log(path=None, limit=20, since=None)
git_show(commit_hash, path=None)
git_diff(ref_a, ref_b, path=None)
git_blame(path, ref="HEAD")
git_file_history(path)
repo_status()
```
Each a hardcoded wrapper around exactly one allowlisted `git` subcommand, argument-validated, `shell=False`, repo-confined (Mission 18 §4/§8). This design adds nothing to this layer beyond what Mission 18 already specified — repeating it here only for completeness of the three-layer picture.

**Working-tree layer — new, minimal:**
```
working_tree_file_identity(path) -> {exists, tracked, size, mtime, sha256, modified_vs_head: bool}
```
One function. Computes a content hash and mtime of the current on-disk file, and (by calling the Git layer's own `git_show` internally) whether it differs from `HEAD`. This is exactly the operation this report's own three prior passes performed by hand, repeatedly, via `shasum`/`stat`/`git diff --quiet` — formalizing it into one primitive is the only new capability this layer needs.

**Runtime layer — new, minimal, the genuinely novel part of this design:**
```
runtime_process_identity() -> {pid, start_time, cwd, executable, listening_ports}
runtime_module_origin(module_name) -> {loaded: bool, file_path: str | None}
```
Two functions. `runtime_process_identity()` mirrors exactly what this report's own Phase 1 established by hand via `ps`/`lsof` (§4 of this report goes into why this is safe and sufficient). `runtime_module_origin()` is a single, tiny, read-only lookup: `sys.modules.get(module_name)` and its `.__file__` attribute — no code execution, no `inspect.getsource()`, no debugger. Both would need to be exposed via one new, narrow, read-only admin route (or reused as an in-process function if the query originates from inside the same process, e.g. a future `echo_tool_dispatch.py`-style tool) — **this is the one genuinely new architectural surface this design requires**, and it is deliberately the smallest possible one: two fields returned, no arguments beyond a module name validated against a real, current `sys.modules` key list (never a caller-supplied arbitrary string passed to `importlib`).

**Reconciliation layer — new, one composer function, no new logic beyond calling the four above:**
```
reconcile(path, module_name=None, symbol=None) -> ProvenanceObservation  (§4)
```

**Explicitly not proposed, and why:**
- `git_symbol_history(path, symbol)` (offered as an example in the mission brief) — not included. This report's own Phase 3 archaeology needed only whole-file diffing plus one AST-based top-level-symbol-set comparison, both done with the existing Git layer plus a few lines of local Python, no new primitive required. Adding a dedicated symbol-history primitive would be building capability ahead of demonstrated need — the opposite of this report's own mandate.
- `runtime_loaded_source_identity(module)` (also offered as an example) — considered and **deliberately not included as a distinct primitive**; see §6, where its intended function is folded into the reconciliation composer's own inference logic instead of a new standalone query, because it cannot return a clean fact on its own (it always requires the mtime/process-start-time comparison to mean anything) and inventing a primitive that returns an already-interpreted, not-quite-provable claim is exactly the kind of unearned-confidence risk §7's evidence contract exists to prevent.

---

## 4. Provenance Object Schema

Extends `liveness_ledger.py`'s proven `_result()` shape and Mission 18's Section 5 JSON design — not a competing schema:

```json
{
  "query": "reconcile",
  "subject": {"path": "app/core/liveness_ledger.py", "module": "app.core.liveness_ledger", "symbol": null},
  "git": {
    "head_sha": "e92ec3b7...",
    "blob_exists": true,
    "blob_sha256": "f09a146c..."
  },
  "working_tree": {
    "exists": true,
    "tracked": true,
    "sha256": "cdd82f03...",
    "mtime": "2026-09-09T20:30:22-07:00",
    "modified_vs_head": true
  },
  "runtime": {
    "process_pid": 7644,
    "process_start_time": "2026-09-10T22:41:53-07:00",
    "module_loaded": true,
    "module_file_path": "/Users/richietate/Desktop/FeralEcho/app/core/liveness_ledger.py",
    "file_mtime_precedes_process_start": true,
    "behavioral_fingerprint_checked": true,
    "behavioral_fingerprint_source": "GET /admin/liveness-status, field f2_stdin_contract.evidence"
  },
  "relationship": "WORKTREE_MODIFIED",
  "status": "VALID_RESULT",
  "evidence_label": "SUPPORTED",
  "evidence_id": "sha256(query+subject+git+working_tree+runtime+timestamp)",
  "timestamp": "2026-09-11T06:29:01Z"
}
```

**Fields deliberately excluded, and why**, matching §2 item 8's discipline against building ahead of need:
- No `repository_identity` obfuscation field (Mission 18 proposed hashing the repo path for any Echo-facing rendering) — not needed for an in-process/authenticated-admin-only interface with no external audience; adds complexity for a threat (repo-path disclosure to an untrusted party) this design's own permission model (§8) already prevents by not exposing the interface externally.
- No hash-chained/Merkle ledger (Mission 18 Section 11 already considered and correctly rejected this for the identical reason: the threat model is "was this looked up correctly," not "was the ledger tampered with by a filesystem-write-capable adversary" — a threat already covered by this project's existing production security posture).
- No `command_executed` raw string for the runtime layer (unlike the Git layer, which genuinely runs an external `git` subcommand worth logging verbatim) — the runtime layer's operations are pure in-process attribute reads with no meaningful "command line" to log.

**`evidence_label` is new relative to both Mission 18's schema and `liveness_ledger.py`'s own `_result()`** — it is the six-value vocabulary (VERIFIED/SUPPORTED/INFERRED/UNKNOWN/DISPROVEN, per this project's own established forensic-audit convention) applied per-observation, computed by the composer, never self-assigned by anything downstream. See §7 for exactly which combinations of the fields above earn which label — this is the schema's single most important computed field.

---

## 5. Discrepancy Taxonomy

Formalized from the mission brief's own list, each definition tied to a concrete, already-observed example from this session's own archaeology (not a hypothetical):

- **A — Working-tree addition.** `git.blob_exists = false` AND `working_tree.exists = true`. Example: `restore_council_gate` (absent from HEAD, present on disk).
- **B — Working-tree removal.** `git.blob_exists = true` (as of the last commit touching the path) AND the specific symbol/function is absent from the current working-tree parse of that path, while the file itself still exists. Example: `temporal_environment.py:get_location()` — the *file* is present in both layers; the *symbol* is HEAD-only. **Note, precisely**: this is a symbol-level relationship, not a file-level one — the schema's `subject.symbol` field exists specifically to make this distinction expressible, since a file-level `working_tree.exists` check alone cannot detect it.
- **C — Working-tree modification.** `git.blob_sha256 != working_tree.sha256` for the same path, with the relevant symbol present in both. Example: `run.py`'s `admin_restore()`, `sandbox/safe_exec_wrapper.py`'s `_install_patches()`, `river_deliberation.py`'s `select_best_fallback_candidate()` — all confirmed this session via non-zero symbol-stable `git diff --stat`.
- **D — Runtime does not match working tree.** `runtime.module_loaded = true` AND `runtime.file_mtime_precedes_process_start = false` (the file changed *after* the process started, meaning the currently-loaded module's in-memory bytecode may predate the current on-disk content) — OR a behavioral fingerprint check (§6) returns content inconsistent with the current working-tree source. **Not observed this session** — every file checked had an mtime preceding the process start time.
- **E — Runtime provenance ambiguous.** `runtime.module_loaded = true` but `runtime.module_file_path` is `None`, empty, or points outside the repository (e.g., a `.pyc`-only or frozen/zipped module, or a dynamically-constructed module with no real `__file__`) — the interface can observe *that* something is running but not confidently attribute *which on-disk file* it came from. **Not observed this session** for any of the seven files checked (all are ordinary, real, on-disk `.py` files with normal `__file__` attributes) — flagged as a real, distinct possibility for other parts of the codebase (e.g., dynamically `exec`'d self-edit candidates, which by design never reach a stable, queryable `sys.modules` entry the same way).
- **F — Runtime matches neither HEAD nor working tree.** The highest-severity case: `runtime`'s behavioral fingerprint (§6) matches neither the current `git.blob_sha256` content nor the current `working_tree.sha256` content. This would mean the process is running a *third*, otherwise-unaccounted-for version of the code — e.g., a stale in-memory module that predates the file's current content and was never reloaded. **Not observed this session**, and this report's own Phase 6 (prior archaeology pass) explicitly searched for and found zero instances within its scope.
- **G — Fully reconciled.** `git.blob_sha256 == working_tree.sha256` (no relationship computed beyond `HEAD_MATCH`, since there is nothing to reconcile).

---

## 6. Runtime Identity — What Can Actually Be Established (the hardest part)

Answered directly, conservatively, against the real M5/macOS/CPython 3.12 environment this session actually used:

1. **Can the loaded module's source path be established?** Yes — `sys.modules[name].__file__`, a standard, always-safe attribute read (no code execution). `READY`.
2. **Can the loaded source content be fingerprinted?** **Not directly** — this is the central limitation. CPython compiles a module to bytecode at import time and does **not** retain the original source text anywhere accessible from the live module object. `inspect.getsource()` does not read "what was compiled" — it re-opens and re-reads `__file__` from disk *at call time*, which is functionally identical to just reading the working-tree file directly (and therefore proves nothing beyond what `working_tree_file_identity()` already establishes). **The only way to fingerprint what was *actually compiled* is bytecode-level**: comparing a function's `__code__.co_code` (or `dis.dis()` output) against a fresh `compile()` of the current on-disk source. This is safe (pure introspection of already-loaded, trusted, first-party code — not executing anything new) but adds real complexity and is not proposed as part of the minimal design (§3) — noted here as the technically-available but deliberately-excluded stronger option.
3. **Can the corresponding working-tree file be fingerprinted?** Yes — trivially, `sha256` of the current file content. `READY`.
4. **Can HEAD's blob be fingerprinted?** Yes — `git show HEAD:<path>` piped through `sha256`, or `git hash-object`. `READY` (already proven this session, repeatedly).
5. **Can these identities be compared?** Yes, directly — string equality of three hashes. `READY`.
6. **Can this be done without modifying or restarting the process?** Yes, for everything except the bytecode-level comparison in item 2, which — while itself safe and non-mutating — has not been tested against the live process this session and is excluded from the minimal design regardless.
7. **What limitations remain?** (a) The gap in item 2, stated plainly: **this design cannot, without the excluded bytecode-comparison step, produce airtight proof that the running bytecode was compiled from the exact current working-tree bytes** — only strong circumstantial evidence (mtime precedes process start + hash matches current disk content). (b) Dynamically-generated/`exec`'d code (self-edit candidates, sandboxed scripts) has no stable `sys.modules` entry to query at all — Type E by construction, not a gap in this design so much as an honest limit of what "module origin" can mean for that class of code. (c) A module reloaded via `importlib.reload()` mid-process would break the "mtime precedes process start" heuristic's soundness — checked this session: this project's own convention (confirmed across `CLAUDE.md`'s F1 AST-scanner rules) is to explicitly **block** `importlib.reload` inside the F1/F2 self-edit sandbox specifically to prevent patch-undoing, and no evidence was found this session of any production code path calling `importlib.reload()` on itself — but this was not exhaustively re-verified for this report and is recorded as a genuine, disclosed assumption, not a proven absence.
8. **What evidence would be required before Echo is allowed to label runtime provenance `VERIFIED`?** See §7 — the bar is deliberately set below "bytecode-proven" and above "just checked the file exists."

**The one method this report's own prior passes actually used and found to work well**, worth formalizing as a genuinely useful (if narrower) alternative to raw bytecode comparison: **behavioral fingerprint correlation** — reading an already-existing, already-safe endpoint's (`GET /admin/liveness-status`) returned evidence text, and checking whether it contains a distinctive substring that could only be produced by one specific version of the source (e.g., `f2_stdin_contract`'s evidence text literally containing the phrase "...still closes fd 0" — a claim only the working-tree version's evaluator function can produce, since HEAD's version has no fd0-related code path to describe). This is not a general primitive (it depends on a check happening to expose a distinguishing string), but it is real, already-proven-in-practice evidence, and the reconciliation composer (§3) should use it opportunistically when a relevant liveness check exists for the subject being queried, promoting the resulting label from `SUPPORTED` to `VERIFIED` when it succeeds (§7).

---

## 7. Evidence Contract

A claim of the form *"X is part of my currently executing logic"* may carry the label:

- **`VERIFIED`** only if **all** of: (a) `working_tree.exists` and the symbol is present in the current working-tree parse; (b) `runtime.module_loaded = true` with a real `module_file_path` matching the queried path; (c) `runtime.file_mtime_precedes_process_start = true`; **and** (d) either a successful behavioral-fingerprint correlation (§6) **or** a bytecode-level comparison (if ever built — not in this design's minimal scope). Without (d), the honest ceiling is `SUPPORTED`, not `VERIFIED` — this report's own three prior passes, in fact, only reached `VERIFIED` for exactly the two mechanisms where a behavioral fingerprint was actually checked (`restore_council_gate`, the fd0 close), and left everything else at `SUPPORTED` for precisely this reason. The schema formalizes a distinction this session already applied by hand.
- **`SUPPORTED`** if (a)–(c) hold but (d) was not performed or is not available for this subject.
- **`DISPROVEN`** if `git.blob_sha256 == working_tree.sha256` (no discrepancy exists) but a prior claim asserted one — or, symmetrically, if a behavioral fingerprint contradicts the expected source (Type F).
- Echo must never say *"I am running the latest code"* unless a fresh `reconcile()` call's result carries `VERIFIED` or, at minimum, `SUPPORTED` with an explicit statement of which of (a)–(d) was not established. A bare, unqualified claim with no evidence_id behind it is **not a valid output of this interface** — it would be Echo's own text, which §2's `self_model_claims.py` review already established is structurally barred from being its own verification.

**Worked example**, in the exact target format the mission brief requested:
```
CLAIM:
restore_council_gate is part of my currently executing liveness logic.

STATUS: VERIFIED

EVIDENCE:
- running process PID: 7644, started 2026-09-10T22:41:53-07:00
- working_tree.exists: true, sha256: cdd82f03... (differs from HEAD's f09a146c...)
- runtime.module_file_path: .../app/core/liveness_ledger.py (matches queried path)
- runtime.file_mtime_precedes_process_start: true (file last written 2026-09-09T20:30:22, before process start)
- behavioral fingerprint: GET /admin/liveness-status returned restore_council_gate.pass=true with
  evidence text matching a distinctive phrase only the working-tree implementation can produce
- git.blob_exists: false — no matching implementation found anywhere in HEAD's history for this path

CONCLUSION:
Runtime matches working tree and differs from HEAD. This is a Type A discrepancy (working-tree
addition). VERIFIED per §7(a)-(d), all four conditions independently established.
```
**Is this sufficient, or is stronger evidence necessary?** Sufficient for this project's own standing evidentiary bar (the same bar `liveness_ledger.py`'s 52 checks already operate at — behavioral/source correlation, not bytecode proof) — and explicitly *not* claimed to be stronger than that. A future mission wanting a formally higher bar would need the bytecode-comparison step (§6 item 2), deliberately excluded from this minimal design.

---

## 8. Security / Authority Boundary

Extends Mission 18's Section 15 list (reused, not modified) with the two new layers:

```
READ (this interface)
  Git history, objects, blame, diffs, log            [Mission 18, unchanged]
  working-tree file existence, content hash, mtime, tracked status
  runtime process identity (pid, start time, cwd, executable, ports)
  sys.modules[name].__file__ for an allowlisted, real, currently-imported module name
  already-existing, already-safe endpoint outputs (e.g. /admin/liveness-status), read verbatim

NO WRITE, ANYWHERE, THROUGH THIS INTERFACE
  git commit/reset/checkout/rebase/push/branch mutation      [Mission 18, unchanged]
  any filesystem write of any kind
  process termination, restart, or signal delivery
  importlib.reload() or any other module-mutation call
  arbitrary module-name input to importlib (module names are validated against the real,
    current sys.modules key list — never passed through to an import statement from
    caller-supplied text)
  code execution of any kind beyond the four narrow attribute/hash reads listed above
```

**Does the proposed interface accidentally create an authority escalation?** No new one, checked explicitly against each new primitive: `working_tree_file_identity()` reads no more than `echo_tool_dispatch.py`'s existing `_tool_read_file()` already can (a file's bytes) — it adds a hash computation, not new access. `runtime_process_identity()` and `runtime_module_origin()` expose **less** than a full process listing would (four fixed fields; no arbitrary `ps`/`lsof` passthrough; no ability to query a process other than FeralEcho's own) — this is a narrower disclosure than what any local user or the existing `GET /projects/file` route (unauthenticated) already effectively allows an attacker to infer by other means. **The one new exposure surface worth naming plainly**: `runtime_module_origin()` reveals absolute filesystem paths (e.g., `/Users/richietate/Desktop/FeralEcho/...`) — a real, if minor, information disclosure if this interface is ever exposed over an unauthenticated network route (matching Mission 18's own Section 5 note about redacting `repository_path` in Echo-facing rendering). **Recommendation, consistent with Mission 18's own Option A vs. C analysis**: implement as an in-process function set (callable the same way `echo_tool_dispatch.py`'s existing tools are), never as a new unauthenticated Flask route.

---

## 9. Experimental Feasibility

| Primitive | Classification | Basis |
|---|---|---|
| `git_log`/`git_show`/`git_diff`/`git_blame`/`git_file_history`/`repo_status` (Mission 18's 6) | **READY** | Fully designed by Mission 18; this session independently used the equivalent raw commands (`git log -S`, `git show`, `git diff --stat`) dozens of times with zero issues on this exact repo. |
| `working_tree_file_identity(path)` | **READY** | This exact operation (hash + mtime + tracked-status + HEAD-diff) was performed by hand, successfully, for 7 files this session, using only `shasum`, `stat`, and `git diff --quiet` — no new infrastructure needed, only wrapping it as a callable function. |
| `runtime_process_identity()` | **READY** | Performed by hand this session via `ps -p <pid>`/`lsof -p <pid>` — safe, standard, already-available OS facilities; the only new work is calling `os.getpid()` and `psutil`-equivalent lookups from *inside* the process itself, which is strictly easier and safer than the external-process inspection this session actually did. |
| `runtime_module_origin(module_name)` | **REQUIRES SMALL NEW READ-ONLY ADAPTER** | The underlying Python operation (`sys.modules[name].__file__`) is trivial and safe, but no existing endpoint or tool currently exposes it — needs one new, narrow, in-process function (or, if HTTP-exposed, one new authenticated route), with the module-name allowlist/validation described in §8. |
| Behavioral fingerprint correlation (§6) | **REQUIRES SMALL NEW READ-ONLY ADAPTER** | The data source (`/admin/liveness-status`) already exists and is already safe; what's missing is a small, curated table mapping `(subject_path/module) -> (liveness_check_name, distinguishing_substring_per_known_version)` — genuinely new, but small, data, not new architecture. |
| `reconcile()` composer | **REQUIRES SMALL NEW READ-ONLY ADAPTER** | Pure composition of the four primitives above plus the `evidence_label` decision table in §7 — no new external capability, but real new code (the decision logic itself). |
| Bytecode-level comparison (§6 item 2, explicitly excluded from the minimal design) | **REQUIRES ARCHITECTURAL CHANGE** (relative to this design's own minimal scope — technically `READY` in the sense that Python supports it safely, but not proposed for inclusion) | Would need real design work: which functions' bytecode to compare, how to render a diff meaningfully, and explicit reasoning about `co_consts`/closures/decorators that could make a byte-identical-behavior function compare as "different" harmlessly. Not attempted this pass. |
| "Prove no `importlib.reload()` has ever silently occurred for a given module" | **NOT RELIABLY POSSIBLE** | No general, safe, external signal for this was found this session — the mtime-precedes-process-start heuristic (§6) is the best available proxy, and it is explicitly a proxy, not proof, as disclosed in §6 item 7(c). |

---

## 10. Recommended Minimal Architecture

1. A new, small, in-process module (suggested: `app/core/provenance_check.py`, mirroring `self_knowledge_verification.py`'s naming convention) implementing exactly: `working_tree_file_identity()`, `runtime_process_identity()`, `runtime_module_origin()`, and `reconcile()` — the four new primitives from §3, calling into Mission 18's already-designed (but also unimplemented) Git-layer functions for the HEAD side.
2. `reconcile()`'s output is persisted via the **existing** `self_model_claims.record_claim()` — not a new ledger file. This is a direct, disclosed departure from Mission 18's own Section 5 proposal (`memory/git_evidence_ledger.jsonl`), justified by §2's finding that a suitable, already-proven, structurally-safe ledger already exists and duplicating it would be the opposite of "smallest possible mechanism."
3. Wired into Echo's self-referential-question handling the same way `_build_capabilities()`/`_build_affect()`/`_build_council()` already are in `echo_ground_truth.py` — a new keyword-triggered slice, `_build_provenance()`, answering questions like "are you running your latest code" by calling `reconcile()` fresh (never from a cached/stale value) and rendering §7's evidence-contract format.
4. Registered as a 4th/5th tool in `echo_tool_dispatch.py`'s existing hardcoded dispatch (§2 item 1), **not** `ToolManager`'s dead registry.
5. No new Flask route. No new authentication surface. No new persistent process.

---

## 11. What Should Explicitly NOT Be Built

- A general "inspect any file/module/git ref" free-text query interface — every primitive above takes a fixed, small argument shape, never a caller-composed command.
- A new evidence ledger file — `self_model_claims.jsonl` already exists and already enforces the one invariant (`proposed_by != verified_by`) that matters here.
- Bytecode-level comparison, in this pass — real, safe, and possible, but not needed to clear this design's own evidence bar (§7), and adds meaningful complexity for a capability nothing in this session's actual investigation needed.
- Any Git write capability, symlink-following beyond normalization, network Git operations, or `ToolManager` registration — all already excluded by Mission 18 and reaffirmed here.
- Any mechanism that lets Echo (or anything) mark its own claim `verified` — `self_model_claims.py`'s existing structural guard already prevents this, and this design adds nothing that would weaken it.
- A dedicated always-running "provenance service" (Mission 18's Option B, already correctly rejected there for adding an unnecessary process-lifecycle burden) — this design's primitives are cheap, synchronous, in-process calls, not worth a persistent service.

---

## 12. Open Questions

1. **Is the mtime-precedes-process-start heuristic (§6, §7) sound enough to anchor `VERIFIED` on its own, without a behavioral fingerprint, for subjects that have no corresponding liveness check?** Most working-tree changes this session *did* have a nearby liveness check to cross-reference (because the check-count discrepancy is what triggered this whole investigation) — it's genuinely unknown how often a real future discrepancy would lack any behavioral-fingerprint anchor at all, leaving `SUPPORTED` as the practical ceiling most of the time.
2. **Should `reconcile()`'s calls to Mission 18's Git-layer functions count as "implementing Mission 18," requiring that mission's own separate authorization, or can this design's authorization cover both?** Not resolved here — a scoping/process question for whoever authorizes implementation, not a technical one.
3. **Does `self_knowledge_verification.py`'s existing `find_check_count_claim()` need to change at all, or does it simply gain a new sibling?** This report recommends the latter (leave it untouched, add `reconcile()`-backed checks alongside it) but did not deeply re-audit that module's own extension points this pass.
4. **How does this compose with `research/`'s own evidence-hierarchy convention** (`research/DECISIONS.md`'s Tier 1–8 scale, already cited by Mission 18 Section 6)? This design's `evidence_label` field uses this project's *forensic-audit* six-value vocabulary (VERIFIED/SUPPORTED/...), not `research/`'s own numbered tiers — the two are compatible in spirit but were never formally mapped to each other anywhere in the corpus, a real, small, open reconciliation task of its own.

---

## 13. Proposed Next Experiment

**Not implementation.** The smallest experiment that would validate this design without building anything production-facing: write `working_tree_file_identity()`, `runtime_process_identity()`, and `runtime_module_origin()` as three standalone, throwaway functions in a scratch script (outside the project tree, following this session's own established bounded-experiment convention), call them against the *already-running* FeralEcho process (PID known, read-only, no restart) for the same seven files this investigation already hand-verified, and confirm their outputs exactly match this session's own hand-derived results (§2–§7 of the prior three reports). If they match, the primitives are validated at the "does this actually work against the real system" level before any of it is proposed for real integration. This is deliberately scoped smaller than "build `reconcile()`" — it tests the four leaf primitives in isolation first, per this project's own standing discipline (bounded experiments, smallest first) rather than validating the whole composed design at once.

---

## Mutation Statement

```
Files created:       audits/2026-09-11_read_only_provenance_interface_design.md (this file, only)
Files modified:       none
Processes started/restarted: none
Git HEAD before:      e92ec3b7fe4743f75746d161a06601db0232bff2
Git HEAD after:       e92ec3b7fe4743f75746d161a06601db0232bff2 (unchanged)
Commits created:      none
Nothing described in Sections 3, 4, 10, or 13 was implemented, tested against, or executed
inside the live FeralEcho process. All references to "this session's" prior verification of
individual facts (file hashes, process identity, etc.) point to read-only observations already
made and disclosed in the three prior archaeology reports, not new actions taken while writing
this design document.
```
