# Provenance Leaf Primitives — Adversarial Validation

**Date:** 2026-09-11
**Type:** Bounded feasibility experiment, attack-the-design. Nothing implemented. No production file touched. No restart.
**Subject under test**: `audits/2026-09-11_read_only_provenance_interface_design.md`'s three leaf primitives (`working_tree_file_identity()`, `runtime_process_identity()`, `runtime_module_origin()`).

---

## 1. Experimental Scope

**Tested**: whether the three leaf primitives can genuinely produce correct, safe output against the real, currently-running FeralEcho process, using only read-only filesystem operations, bounded read-only Git subprocess calls, standard OS process-inspection tools, and one already-existing HTTP endpoint (`GET /admin/liveness-status`). All scratch code lived in `/tmp/provenance_validation_scratch/`, outside the project tree, and was removed at the end of this investigation (see §11).

**Deliberately not built**: `app/core/provenance_check.py` or any other production file; any Flask route; any `echo_tool_dispatch.py` tool registration; any modification to `self_model_claims.py`, `echo_ground_truth.py`, or `liveness_ledger.py`; any restart of PID 7644; any Git commit.

**Central question investigated, per the mission's own framing**: can a separate scratch Python process inspect PID 7644's `sys.modules`? **Answer, established with direct empirical evidence in §5: no.** This is the report's most important finding and the one place the design under review needed the sharpest scrutiny.

---

## 2. Process Identity

Verified at the start and re-verified at the end of this investigation (unchanged both times):

```
PID:              7644
Started:          Thu Sep 10 22:41:53 2026
Elapsed (start of this session):  15:49:58
Elapsed (end of this session):    15:52:10
Command:           python -u run.py
cwd:                /Users/richietate/Desktop/FeralEcho (confirmed via lsof)
Executable:         /Users/richietate/miniforge3/envs/feral_echo/bin/python3.12
Listening:          *:5000 ("commplex-main", TCP LISTEN)
Server responsive:  HTTP 200 on GET /admin/liveness-status, both checked at start and end
```

**Same process throughout** — identical PID and start timestamp confirmed at both ends of this investigation; this is the same process instance examined by all three prior archaeology/design reports, now ~15.8 hours further into its uptime. No restart occurred, in this session or between sessions.

---

## 3. Working-Tree Primitive — `working_tree_file_identity()`

**Method**: a throwaway script (`/tmp/provenance_validation_scratch/working_tree_identity_probe.py`, never inside the project tree) implementing the primitive's conceptual behavior from scratch — no import of any production FeralEcho module (correctly, since none implementing this exists yet). Used `hashlib.sha256`, `os.stat`, and three bounded `git -C <repo> ...` subprocess calls per file (`ls-files --error-unmatch`, `show HEAD:<path>`) — all read-only.

**Result**: run against the same 7 files identified from the prior reports (`run.py`, `app/core/liveness_ledger.py`, `sandbox/safe_exec_wrapper.py`, `app/core/snapshot_manager.py`, `app/core/river_deliberation.py`, `app/core/temporal_environment.py`, `app/core/echo_ground_truth.py`). **Every field — `exists`, `tracked`, `sha256`, `head_sha256`, `modified_vs_head` — matched the hand-derived values recorded in `audits/2026-09-11_three_layer_provenance_reconciliation.md` exactly**, byte-for-byte on every hash (e.g. `liveness_ledger.py`: `sha256=cdd82f03...`, `head_sha256=f09a146c...`, both matching the prior report's values verbatim). `mtime` differs in *display format only* (this probe reports full ISO-8601 UTC; the prior report used `stat -f %Sm`'s local-time format) — the underlying instant is the same, cross-checked directly.

**Conclusion: `working_tree_file_identity()` is technically sound, its outputs are correct, and it reproduces exactly against an independently-written implementation.** No flaw found in this primitive. `READY`, confirmed, not merely re-asserted.

---

## 4. Runtime Process Primitive — `runtime_process_identity()`

**External feasibility**: already fully re-confirmed in §2 via `ps`/`lsof` — no new finding here.

**In-process feasibility, tested directly** (a standalone script run outside the project, demonstrating the mechanism a real in-process implementation would use — not run inside PID 7644):
```
os.getpid()              -> trivial, always safe
os.getcwd()               -> trivial, always safe
sys.executable             -> trivial, always safe
psutil.Process().create_time()  -> tested; psutil 7.2.2 confirmed installed in the exact
                                    feral_echo conda environment PID 7644 runs under
                                    (checked directly: /Users/.../envs/feral_echo/bin/python3.12
                                    -c "import psutil" succeeds)
```
**Listening ports, one genuine nuance not fully resolved by the design doc**: an in-process self-query for "what ports am I listening on" is less direct than the other three fields — a Flask/Werkzeug process does not routinely introspect its own bound socket set via a public API the way `os.getpid()` is trivial. The two realistic options are (a) `psutil.Process().net_connections()`/`.connections()` called on itself (available, self-referential, safe — confirmed `psutil` is present), or (b) simply hardcoding the known bind address from the process's own startup configuration (`run.py` already knows what it bound to `app.run(host=..., port=...)` — this is arguably more honest than re-discovering it via the OS). **Not a flaw in the design, but a real implementation-detail gap the design doc left implicit** — flagged for whoever eventually builds this.

**Conclusion: `runtime_process_identity()` is feasible as a genuine in-process primitive**, with three of four fields trivial and the fourth (`listening_ports`) requiring one of two well-understood, still-safe approaches, neither requiring new dependencies. `READY`.

---

## 5. Runtime Module Origin — The Key Section

**Q1. Can a separate scratch Python process inspect PID 7644's `sys.modules`?**

**No. Directly, empirically confirmed, not merely asserted from general Python knowledge:**
```
$ python3 -c "import sys; print(len(sys.modules)); print('app.core.liveness_ledger' in sys.modules)"
34
False
```
The scratch process's own `sys.modules` contains 34 entries — its own imports, from its own process start — and has no knowledge of, or handle to, `app.core.liveness_ledger` (a module genuinely loaded inside PID 7644). **This is not a permissions issue or a missing-flag issue — it is architectural**: `sys.modules` is a plain Python dict living in the CPython interpreter's own heap, inside that process's own private virtual address space. There is no standard, safe, Python-level API for one OS process to read another's live object graph. The kinds of mechanisms that *could* do this (attaching a debugger via `ptrace`/`lldb`, using a memory-inspection tool like `py-spy dump`, or code injection) are precisely the categories the design's own §8 and this mission's own constraints both explicitly forbid ("debugger attachment," "code injected into the process").

**A second, independent check was run to make sure no OS-level shortcut exists**: `lsof -p 7644` was inspected for any `.py` source file among its open file descriptors — **zero found**, across all 312 `txt`-type (mapped executable/library) entries, which are exclusively compiled binaries, shared libraries (`.dylib`/`.so`), and data files (ICU tables, Metal shader caches, etc.). **This empirically confirms CPython does not keep a `.py` source file open after compiling it** — even a purely OS-level, non-Python inspection tool provides zero information about which `.py` modules a running process has loaded or their file paths. This closes off the one plausible external-inspection shortcut before it could be proposed.

**A third check confirmed no existing capability inside PID 7644 already exposes this today**: `run.py`'s full `/admin/*` route list (7 routes: `snapshots`, `restore`, `council-stats`, `self-edit-outcomes`, `autonomy-status`, `liveness-status`, `council-spotcheck`) contains nothing module/introspection-related; `echo_tool_dispatch.py`'s 3 registered tools (`read_file`, `search_memory`, `log_thought`) likewise expose nothing of this kind. **There is no existing, safe way — today, without any new code — to ask the live PID 7644 "what file backs your loaded copy of module X."**

**Q2. What is the minimum mechanism required for PID 7644 itself to answer this?**

Code that runs *inside* PID 7644's own interpreter — full stop. There is no way around this; it follows directly from Q1's answer. Concretely, the minimum shape is a function `def runtime_module_origin(module_name): m = sys.modules.get(module_name); return {"loaded": m is not None, "file_path": getattr(m, "__file__", None)}`, reachable only by something already executing inside that same process.

**Q3. Can that mechanism be implemented as a pure in-process read-only function?**

Yes — the function body itself is trivial, safe, and purely read-only (a dict lookup and an attribute read, no execution of anything). The hard part was never the function's *body*; it is exclusively the *reachability* problem (Q1/Q2) — how anything outside the process gets to invoke it at all.

**Q4. Does it require an HTTP route? IPC? a socket? debugger attachment? code injection? an existing Echo tool dispatch path? or simply calling a function from Echo's own process?**

Precisely: it requires **either** (a) a new, narrow HTTP route exposing this one function's output (the same shape as the 7 existing `/admin/*` routes), **or** (b) registration as a 4th tool in `echo_tool_dispatch.py`'s existing hardcoded dispatch (reachable only from *inside* a live request-handling code path already running in the same process), **or** (c), for a caller that is itself literally executing inside PID 7644 already (e.g., a background thread, another module import), a direct function call with no transport layer at all. **It does not require, and must never use**: IPC, a dedicated socket, debugger attachment, or code injection — all of these were considered explicitly and rejected as both unnecessary (options (a)/(b)/(c) fully cover the real need) and directly forbidden by the design's own §8 boundary.

**Q5. Which of those options preserves the report's stated authority boundary?**

Options (a) and (b) both do, **provided** (a) is never left unauthenticated the way `GET /projects/file` currently is (the design's own §8/§10 already flag this precedent as the wrong one to copy) — this validation found nothing to change on this point, only confirmed it remains the correct constraint. Option (b) is the design's own stated preference (§10, item 4) and this validation agrees it is the tighter of the two: it has no independent network-reachable surface at all, inheriting whatever access control already gates `echo_tool_dispatch.py`'s existing three tools rather than needing its own.

**Q6. Does `sys.modules[name].__file__` actually establish *runtime source identity*, or only the loaded module's associated source path?**

**Only the associated path — this is a real, correctly-disclosed limitation the design doc already states (§6 item 2), independently re-confirmed here rather than merely re-cited.** `__file__` is a string attribute set once, at import time, pointing at wherever the module *was* loaded from. It says nothing about the bytes that were actually compiled into the module's live code objects at that moment, and nothing about whether that file has since changed on disk. **This validation's own Phase 5 (§6 below) is precisely the mechanism the design proposes to partially close this gap** — and the design is correct to keep the two questions ("what path" vs. "what bytes") structurally separate rather than conflating them, which is exactly what the mission's Phase 4 instructions warned against doing.

**Overall verdict for this section**: **the design's core architectural claim survives this attack.** It does *not* claim a scratch script can inspect PID 7644's `sys.modules` — its own §3 text already says the two new runtime primitives "would need to be exposed via one new, narrow, read-only admin route (**or reused as an in-process function if the query originates from inside the same process**)" and §10 explicitly recommends the in-process/tool-dispatch route. **The one real gap found**: the bare Python code-block listing in §3 (`runtime_module_origin(module_name) -> {loaded, file_path}`) is presented without that constraint visibly attached to it, which is exactly what this mission's own "Critical Question" framing correctly worried a reader could misread in isolation. This is a **documentation clarity issue, not an architectural flaw** — recorded precisely as such in §9, not inflated into a design failure.

---

## 6. Mtime Evidence

**Independently reproduced, not merely re-cited**, at a real time ~15.8 hours after the prior reports' own observation:
```
run.py                                        mtime=2026-09-09T15:55:55  precedes_process_start=True
app/core/liveness_ledger.py                   mtime=2026-09-09T20:30:22  precedes_process_start=True
sandbox/safe_exec_wrapper.py                  mtime=2026-09-09T12:24:04  precedes_process_start=True
app/core/snapshot_manager.py                  mtime=2026-09-09T15:55:39  precedes_process_start=True
app/core/river_deliberation.py                mtime=2026-09-09T15:49:24  precedes_process_start=True
app/core/temporal_environment.py              mtime=2026-09-09T15:53:40  precedes_process_start=True
app/core/echo_ground_truth.py                 mtime=2026-09-08T00:52:34  precedes_process_start=True
```
All 7 files: unchanged since the prior investigation, and the relationship (`mtime < process_start`) holds identically now as it did then — an expected, stable result given no file was edited in between (independently confirmed by the sha256 match in §3).

**What this proves**: the file *existed, with this exact content*, before the process began — meaning that if the process's import machinery read this file at all during startup, it read *this* content, not some other version, since nothing overwrote it in between.

**What this does NOT prove, stated with the same precision the mission demanded**: it does not prove the process's import machinery *actually re-read* this specific file at this specific startup (versus, hypothetically, loading a cached `.pyc` whose embedded source-fingerprint happened to still validate against an *older* file state that was itself later restored to look identical — an extremely contrived edge case, not evidenced here, but genuinely not ruled out by mtime alone). It does not prove no `importlib.reload()` occurred at some point after startup, swapping in different content transiently before this observation was taken (this session found no evidence of such a call existing in production code, consistent with the design's own §6 item 7(c) disclosure, but did not exhaustively re-search for it this pass either). Most importantly: **mtime evidence alone cannot distinguish "the file on disk, unchanged, is what's running" from "the file on disk, unchanged, happens to no longer be what's running because something else already replaced the in-memory module object via a mechanism this observation cannot see."** This is exactly why the design correctly treats mtime evidence as one necessary condition among four (§7 of the design doc), never sufficient by itself.

---

## 7. Behavioral Fingerprint

**Freshly, independently re-queried** (not re-cited from the design doc or prior reports):
```
f2_stdin_contract.os_fd0_blocked:  true   (structured boolean field, not merely a text substring)
f2_stdin_contract.raised:          {"iteration": true, "read": true, "readline": true, "readlines": true}
restore_council_gate.status:       "no_real_restores_since_deployment"  (unchanged, stable)
```
**HEAD's evaluator structurally cannot produce this field at all**: `git show HEAD:app/core/liveness_ledger.py | grep -c "os_fd0_blocked"` returns `0` — the string does not exist anywhere in HEAD's version of this file. It is not that HEAD's check happens to return `false` for this field; HEAD's check **has no code path capable of computing or returning this field under any input**.

**1. What exact source behavior distinguishes the working-tree implementation from HEAD?** HEAD's `_evaluate_f2_stdin_contract()` tests only the Python-level `sys.stdin` block and returns `{raised, isatty_honest}`. The working-tree version additionally tests the OS-level `_os.close(0)` behavior and returns `{raised, isatty_honest, python_stdin_blocked, os_fd0_blocked}` — two more fields that simply do not exist as concepts in HEAD's code.

**2. What observable endpoint evidence exposes that distinction?** `GET /admin/liveness-status`'s `f2_stdin_contract` object — already live, already safe, already unauthenticated-but-read-only (same posture as the rest of this route), requiring zero new code to observe.

**3. Can this legitimately strengthen the provenance label from `SUPPORTED` to `VERIFIED`?** **Yes, and this validation found the evidence to be materially stronger than the design doc characterized it.** The design's §6/§7 describe this as matching "a distinctive substring" in prose evidence text — accurate for the `restore_council_gate` example it also cites, but for `f2_stdin_contract`, the actual live response returns `os_fd0_blocked` as a genuine, independently-checkable, structured boolean field, not merely a fuzzy string match. This is stronger evidence than the design claimed for itself — a rare case in this validation where the design under-sold its own supporting evidence rather than over-selling it.

**4. Is this generalizable, or inherently subject-specific?** **Inherently subject-specific, confirmed by direct inspection — not merely assumed.** This fingerprint works *only* because this particular liveness check happens to expose a field/phrase that structurally cannot exist in HEAD's version. A general primitive cannot be built from this alone; it requires, as the design doc itself already states (§9), "a small, curated table mapping (subject → known-check → distinguishing-value) built by hand, subject by subject" — this validation confirms that characterization is accurate and does not find a way to make it more general than the design already claims.

---

## 8. Evidence Contract

The proposed rule (§7 of the design doc):
```
VERIFIED = (a) working-tree symbol exists
         + (b) runtime module loaded, points at queried path
         + (c) file mtime precedes process start
         + (d) behavioral fingerprint OR bytecode comparison succeeds
```

**Critically re-examined, not accepted by default.**

**(a) and (c) are now independently re-verified sound** (§3, §6). **(d) is independently re-verified sound and, for the one example directly tested, stronger than claimed** (§7). **(b) is the condition this validation's central attack targeted (§5)** — and it survives, but only because it is honestly scoped to mean "the interface, running *inside* the same process as the module it's describing, confirms its own `sys.modules` entry" — **not** "an external caller independently confirmed this from outside." The design never actually claims the latter; this validation's job was to make sure it doesn't accidentally imply it, and found one presentation-level place (the bare §3 code listing) where a careless reading could draw that wrong inference.

**One hidden assumption found, stated precisely, not previously named this explicitly in the design doc**: condition (b) as practically implementable *only ever answers the question from inside the one process being asked about*. There is no independent, external corroboration of "the process's own claim about its own `sys.modules`" — the interface's `runtime` layer is, structurally, **self-attestation**, not third-party observation, for this one condition specifically. This is a meaningfully different epistemic shape than conditions (a)/(c) (both externally, independently checkable by *anything* with filesystem/Git access, not just the process itself) and (d) (externally checkable by anything that can make an HTTP request). **This does not make condition (b) worthless** — a process's own `sys.modules` really is authoritative about what *that process* has loaded, in a way no external observer could fake or be wrong about (barring the exotic edge cases in §6) — but it does mean **the overall `VERIFIED` label rests on trusting the process to honestly report its own internal state for exactly one of its four legs**, which is worth naming plainly rather than leaving implicit. This is a materially different (and weaker) trust model than, say, condition (a), where a completely independent third party (this validation session, using nothing but `git`/`hashlib`) reached the identical answer with no dependency on FeralEcho's own code at all.

**Conclusion**: the rule is **defensible within this project's own stated evidentiary bar** (the same bar the Liveness Ledger's 52 existing checks already operate at, per the design doc's own framing) — self-attestation from a trusted, first-party, non-adversarial process is exactly the standard `liveness_ledger.py` itself already uses for all 52 of its checks, so condition (b) is not introducing a weaker standard than the rest of the codebase already accepts, only inheriting it. **Not inflated to "proven,"** and this report's own labeling reflects that: the rule is `SUPPORTED`-to-sound (this validation strengthens confidence in it) rather than promoted to some claim of formal soundness the design never actually made.

---

## 9. Design Changes Required

Exactly one, minor, presentation-level, not architectural:

**§3's bare primitive listing for `runtime_module_origin(module_name)` should carry an explicit, inline annotation that this function is only ever callable from code already executing inside the same process it describes** — the surrounding prose already says this correctly, but the code-block itself, read in isolation (as the mission's own framing of the Critical Question deliberately tested), does not visibly carry that constraint. No other section requires revision. **§7's evidence contract should gain one sentence naming condition (b) as self-attestation, distinct in kind from (a)/(c)/(d)'s externally-checkable nature** — a clarity addition, not a correction of anything wrong.

No other design change is warranted. In particular: **the recommended architecture in §10 (in-process module, reused by `echo_tool_dispatch.py`, no new Flask route, no new ledger file) does not need to change** — it already correctly anticipated the exact boundary this validation set out to attack.

---

## 10. Recommendation

**PROCEED**

The design survives its own most important stress test. The central architectural claim under attack — that `runtime_module_origin()` could somehow be implemented by an external scratch process peeking into PID 7644's memory — was never actually made by the design; this validation confirmed both that such external inspection is genuinely impossible (§5, empirically demonstrated two independent ways) and that the design's own recommended architecture (in-process, tool-dispatch-reachable) correctly sidesteps the problem rather than ignoring it. The two other leaf primitives (§3, §4) were independently reimplemented from scratch and produced identical, correct results. The behavioral-fingerprint evidence (§7) was found to be stronger than the design itself claimed, not weaker. The one real issue found (§9) is a one-sentence documentation clarification, not a redesign.

**This is not a recommendation to implement now** — only that the design, as specified, is technically sound enough to warrant an implementation mission if and when one is separately authorized, per this project's own standing "report, propose, pause" discipline.

---

## 11. Mutation Statement

```
Production files modified:  none
Processes restarted:        none
PID 7644:                    unchanged (same PID, same start time, confirmed at start and
                              end of this investigation)
Git HEAD before:             e92ec3b7fe4743f75746d161a06601db0232bff2
Git HEAD after:               e92ec3b7fe4743f75746d161a06601db0232bff2  (unchanged)
git status --short path count: 98 (before and immediately after this report's own creation
                                    the count becomes 99, reflecting only this new file)
Commits created:              none

Scratch artifacts created:   /tmp/provenance_validation_scratch/working_tree_identity_probe.py
                              /tmp/provenance_validation_scratch/bytecode_probe.py
Scratch artifacts removed:   both files and the containing directory deleted at the end of
                              this investigation (confirmed via a follow-up directory listing
                              showing the path no longer exists) -- see the command executed
                              immediately after this report was written.
Files inside ~/Desktop/FeralEcho created by this investigation: exactly one --
                              audits/2026-09-11_provenance_leaf_primitives_validation.md
                              (this file)
```
