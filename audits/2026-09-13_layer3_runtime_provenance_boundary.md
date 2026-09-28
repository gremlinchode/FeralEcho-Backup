# Layer 3 — Runtime Provenance: Feasibility & Boundary

**Date:** 2026-09-13
**Type:** Architecture / proof-boundary research only. No Layer 3 code written. No production file modified. No commit/stage/Git mutation. PID 7644 read-only-inspected only (`ps`, `psutil`, `lsof`, `vmmap` — all standard, non-invasive OS diagnostic tools; never signaled, attached to, or instrumented).
**Predecessor state:** Layer 1 (`working_tree_file_identity`, commit `6e835bf`) and Layer 2 (`runtime_process_identity_and_self_report`, commit `e03f598`), both committed and red-teamed (PASS, 0 defects). This report does not re-derive settled findings from that corpus — it cites them and builds forward.
**Experimental standard applied:** every empirically-testable claim below was tested on this machine; five new scratch experiments were run this session (file-mutation-after-load, bytecode self-comparison, `co_code` vs. `marshal.dumps` divergence, shadow-module path resolution, `lsof`/`vmmap` external observability), all outside the repository, all removed before this report was written.

---

## 1. Executive conclusion

**Result B, per this mission's own success criteria: the apparent gap cannot be independently closed at this boundary, and we can precisely explain why — with one narrow, genuinely defensible exception.**

Module *loading* (is `X` in `sys.modules`) remains architecturally unobservable from outside the process, confirmed again this session (not reopened as a live question, only re-cited: `audits/2026-09-11_provenance_leaf_primitives_validation.md`'s empirical proof stands). Module *execution* (a specific function actually ran, is running now, or ran recently) is unobservable from outside the process **and** — a new, load-bearing finding this session — is **harder to establish even from inside the process than the existing research corpus assumed**: a naive bytecode-identity check (`__code__.co_code` alone) provably fails to detect a real code change when that change is confined to a literal constant (a string, a number), because `co_code` encodes only the instruction stream, not the constant pool it indexes into. Any future self-report mechanism proposing bytecode comparison must use a full code-object serialization (e.g. `marshal.dumps()`), not `co_code` alone — the predecessor design docs' own framing of "compare `co_code`" was imprecise in a way that would have silently under-detected exactly the class of change (a fixed string, a magic number, a threshold constant) most common in real FeralEcho self-edits.

The one genuinely new, defensible signal found this session: `lsof -p 7644` reveals real, externally-observable, independent evidence that specific **native C-extension packages** (`faiss`, `numpy`, `torch`, `sentencepiece`) are currently mapped into the process's address space — this is not self-report, requires no cooperation from PID 7644, and was confirmed live. It proves something real about *which compiled dependencies are loaded*, but it cannot be extended to pure-Python module identity (Python `.py` source files are never held open after compilation, confirmed directly, consistent with the prior lsof finding) and says nothing about *which specific FeralEcho `.py` file's code is executing*.

No Layer 3 primitive is recommended for implementation in this pass. See §17.

---

## 2. Current Layer 1 + Layer 2 capabilities

- **Layer 1** (`working_tree_file_identity`): proves working-tree/Git object-store facts about one file path — existence, tracked status, current-bytes hash, HEAD-blob hash, and whether they differ. Says nothing about any running process.
- **Layer 2** (`runtime_process_identity_and_self_report`): proves externally-observed OS process facts (PID exists, creation time, cmdline, executable, cwd, status) about a given PID, plus the literal contents of two pre-existing self-report files, plus factual agreement comparisons between the two. Says nothing about which Python code that process has loaded or executed.
- **The gap between them**, confirmed structurally in Layer 2's own red-team (`audits/2026-09-13_provenance_layer2_red_team.md` §8): neither schema shares a single field connecting a file path to a process. `app/core/self_heal.py` remains the standing proof that Layer 1 + Layer 2 together cannot establish "file is loaded," let alone "file is executing" — it would pass every check both layers offer while being genuinely dormant.

---

## 3. Runtime provenance question

> Can we produce defensible evidence that this particular code is actually loaded and/or executing in this particular runtime process?

Answered precisely, not evaded: **loaded** — no, not externally, for pure Python; a narrow, indirect, native-extension-only external signal exists (§5, §9). **Executing** — no, neither externally nor (without new, not-yet-built instrumentation) from self-report either; the best available self-report technique (bytecode comparison) answers a *different*, more modest question ("does my currently-loaded code match what's on disk right now"), not "is this code executing."

---

## 4. Evidence taxonomy

Extending Layer 1/2's own taxonomy (per the boundary review, `audits/2026-09-12_provenance_layer2_boundary_review.md` §3) with the finer distinctions this mission requires:

| Class | Independent / Self-report / Derived / Heuristic | Available today? |
|---|---|---|
| Working-tree file identity | Independent | Yes (Layer 1) |
| Git object-store identity | Independent | Yes (Layer 1) |
| OS process identity (PID, start time, cmdline) | Independent | Yes (Layer 2) |
| Runtime self-report content (sentinel/PID files) | Self-reported | Yes (Layer 2) |
| Native C-extension loading (via `lsof`) | Independent | **Yes, new finding this session, unimplemented** |
| Pure-Python module presence in `sys.modules` | Self-reported (in-process only) | Not externally; would require new in-process code |
| `module.__file__` for a loaded module | Self-reported (in-process only) | Same as above |
| Bytecode/content match of loaded code vs. current disk | Self-reported, **derived** (a comparison, not a raw fact) | Not externally; in-process only, and only correctly if the full code object is compared, not `co_code` alone (§9, §11) |
| Function/code actually executed | **No mechanism exists anywhere in this codebase, self-report or external** | No — would require new instrumentation (§11) |
| Execution recency ("executed recently") | Same — no mechanism | No |
| Execution happening right now | Same — no mechanism, and even instrumentation only gives a marker, not certainty (§11) | No |

---

## 5. What can be independently observed

Confirmed this session, live, read-only, against PID 7644:
- **Process identity** (Layer 2's own domain, re-confirmed): PID exists, `create_time` = `2026-09-11T05:41:53.357916+00:00`, `cmdline = ['python', '-u', 'run.py']`, `executable`, `cwd`, `status`.
- **A third, independent corroboration of process start time**: Apple's own `vmmap` diagnostic tool reports `Launch Time: 2026-09-10 22:41:53.358 -0700` for PID 7644 — matching `ps`/`psutil` to the millisecond, via a completely separate code path (macOS's own process-accounting subsystem, not `psutil`'s Python wrapper). This strengthens, but does not change, Layer 2's existing evidence — recorded as a genuinely new corroborating data point, not a new primitive.
- **Native C-extension loading, via `lsof -p 7644`**: 301 distinct shared libraries currently mapped, including `faiss/_swigfaiss.abi3.so`, `faiss/libfaiss.dylib`, `numpy/_core/_multiarray_umath....so`, `torch/_C....so`, `torch/lib/libc10.dylib`, `sentencepiece/_sentencepiece....so` — all real, OS-reported, independent of anything Echo says about itself. **Zero `.py` source files appear anywhere in `lsof`'s output** (re-confirmed this session, consistent with the leaf-primitives validation's original finding) — CPython does not hold source files open after compiling them, so this mechanism is fundamentally a native/compiled-extension signal, not a route to pure-Python module evidence.
- **Physical memory footprint** (`vmmap -summary`): 9.2G resident, 11.1G peak — a coarse, independent signal consistent with a process that has genuinely loaded heavy ML dependencies, though not a substitute for the specific-library evidence `lsof` already gives more precisely.

---

## 6. What can only be self-reported

- `sys.modules` contents, for any module, pure-Python or extension — **only obtainable from code executing inside PID 7644 itself.** Not reopened as a live question this session; the empirical proof (a scratch process's own `sys.modules` is disjoint from the target's; `lsof` shows zero open `.py` files) already stands from `audits/2026-09-11_provenance_leaf_primitives_validation.md` and was not contradicted by anything found here.
- `module.__file__` for any loaded module — same constraint, same reason.
- Whether a specific function has ever been called — no mechanism exists today, self-report or external (§11).
- The two artifacts Layer 2 already reads (`echo_server.pid`, `echo_sentinel.json`) remain the only self-report channel that currently exists; nothing new was invented or proposed to extend it in this pass.

---

## 7. What can be experimentally demonstrated

All five experiments below were run this session, outside the repository, cleaned up before this report was written:

1. **File-mutation-after-load, real subprocess.** A child process imported a module (`greet() -> "version-A"`), was allowed to run for 3 seconds while the source file was mutated on disk underneath it (`greet() -> "version-B-MUTATED-AFTER-IMPORT"`), then re-checked its own state. Result: `greet()` still returned `"version-A"`; the loaded function's `co_code` hash was bit-identical before and after; the on-disk file hash was independently confirmed to have genuinely changed (`disk hash changed since import: True`). **This is the single most decisive empirical result in this report** — it directly, concretely demonstrates that current working-tree identity (what Layer 1 would report *right now*) and the code object actually resident in a running process can diverge completely, with nothing in either layer's current evidence able to detect it.
2. **Bytecode self-comparison, correctly and incorrectly done.** Comparing only `__code__.co_code` between the pre-mutation and post-mutation versions of the same function reported `False` for "stale" — **a false negative** — because both versions compile to the identical instruction stream (`LOAD_CONST <index>; RETURN_VALUE`); only the constant pool (`co_consts`) differs (`('version-A',)` vs. `('version-B-MUTATED-AFTER-IMPORT',)`). Switching the comparison to `marshal.dumps(code_object)` (full code-object serialization) correctly distinguished the two (`True`/different hash). Confirmed with a minimal, isolated reproduction independent of the file-mutation scenario.
3. **Shadow/duplicate module resolution.** Two files, both named `shadow_mod.py`, in two different directories, both on `sys.path`, with different content (`IDENTITY = "A"` vs. `"B"`). `import shadow_mod` resolved to whichever directory was inserted first into `sys.path` — confirming the bare module *name* carries zero intrinsic identity; only `__file__` (itself only available in-process) or `sys.path` order determines which physical file was actually loaded.
4. **`lsof`/`vmmap` external observability** (§5) — both real, both confirmed working against the live PID 7644, both genuinely independent.
5. **psutil's own documented caching semantics for `create_time()`**: confirmed via `help(psutil.Process.create_time)` — *"The return value... is cached after first call."* This means a `Process` object's create_time is fixed at the moment of its *first* successful read, protecting every *subsequent* call on that same object against a PID-reuse race, but the *first* call itself has no such protection — if PID reuse occurs between `Process(pid)` construction and the first `create_time()` call, the cached value is simply whatever the OS reports at that moment, with nothing to reveal a substitution happened. This precisely confirms (with documentation, not speculation) the narrow residual race Layer 2's red-team already flagged and left open.

---

## 8. What remains fundamentally unobservable from outside the process

- `sys.modules` contents (any entry, for any purpose).
- Whether a specific function/method has been called, is being called, or was called recently — this has **no observable trace anywhere in the current architecture, self-report included**; it would require new instrumentation to exist at all (§11).
- The *exact* bytes of the currently-loaded code object, without either (a) code executing inside the process to read `__code__` directly, or (b) a debugger/memory-inspection tool — both explicitly forbidden by every mission in this thread, and (b) additionally blocked by this machine's own SIP configuration (confirmed `System Integrity Protection status: enabled`, which restricts `dtrace`/`dtruss`-class tools against arbitrary processes without disabling SIP — not tested further, correctly marked `BLOCKED — would require production mutation` per this mission's own experimental standard, since disabling SIP is a system-level change out of scope for a read-only research mission).
- `py-spy` (a real, purpose-built external Python-stack-inspection tool that *can*, on some platforms/configurations, read another process's interpreter state) is **not installed on this machine** — confirmed via `which py-spy`. Not installed during this mission, deliberately: adding new software mid-investigation is itself a real environment change this mission's read-only posture should not casually introduce. Recorded as a real, existing class of tool worth a future, separately-authorized evaluation — not tested here.

---

## 9. Python module-loading findings

The full taxonomy, kept explicitly distinct per the mission's own instruction:

| Claim | Can be established how | External or self-report only |
|---|---|---|
| Module exists on disk | Layer 1 (`working_tree_file_identity`) | External |
| Module is importable | Static analysis (parse-and-check, or a real trial import in an isolated subprocess) | External, but requires *executing* the candidate module's top-level code to fully confirm (a real, if narrow, risk — "importable" can only be verified by actually importing) |
| Module was imported (ever, historically) | No mechanism found anywhere in this codebase | Neither |
| Module is *currently* loaded (`sys.modules`) | In-process read only | Self-report only |
| Module was actually executed (any code ran) | No mechanism exists | Neither |
| A particular function/code object executed | No mechanism exists | Neither |

**"Importable" deserves its own caution, not previously stated this precisely in the corpus**: confirming a module is importable in the abstract sense used by `read_only_provenance_interface_design.md` (a static AST parse) is weaker than an actual trial import — a module can parse cleanly and still fail at import time (a missing dependency, a top-level side effect that raises). A genuine "is importable" check would require running an isolated trial import, which is exactly self-edit's own existing F1/F2 sandbox pattern (`self_edit_manager.py`) — not something Layer 3 should reinvent, and not evidence about the *live* process either way (importing in an isolated sandbox proves nothing about what PID 7644 specifically has loaded).

---

## 10. Execution-evidence findings

The hardest question, and the one this mission's own framing correctly identifies as such. Ranked from weakest to strongest evidence, with the ceiling stated precisely for each:

1. **File exists** — Layer 1, solved.
2. **File imported** — unobservable externally; self-report only, unbuilt.
3. **Module loaded** — same.
4. **Module initialized** (top-level code ran once, at import time) — logically implied by "loaded" for an ordinary module (Python cannot have a module object in `sys.modules` without having executed its top-level statements) — but this is an *inference from Python's own import semantics*, not a directly observed fact, and it says nothing about anything defined *inside* the module (functions, classes) ever being invoked afterward.
5. **Function called** — no mechanism, self-report or external, exists anywhere in this codebase today (§11).
6. **Code executed** — same.
7. **Code executed recently** — same, and additionally requires a *timestamp*, which no existing mechanism produces.
8. **Code is executing right now** — the strongest, least available claim of all; even purpose-built profiling tools (`py-spy`, not installed here) only sample a call stack at discrete instants, never prove continuous execution, and are themselves a form of external inspection this codebase's own standing discipline (`audits/2026-09-11_provenance_leaf_primitives_validation.md`) already treats with real caution.

**Loaded does not imply executing; imported does not imply actively used** — both explicitly, deliberately not assumed anywhere in this analysis, per the mission's own instruction. Levels 5–8 are, as of this report, **entirely unaddressed by anything in the current FeralEcho codebase** — not merely hard to observe externally, but absent as a concept even in self-report form.

---

## 11. Instrumentation analysis

For each candidate mechanism, per the mission's own required questions — **none implemented, this is analysis only**:

| Mechanism | Producer | Storage | Can producer lie? | Can it go stale? | Independently validated? | Proves | Does NOT prove |
|---|---|---|---|---|---|---|---|
| Import hook (`sys.meta_path`/`importlib.abc.MetaPathFinder`) recording every real import | The target process itself, at import time | A new log file (self-report) | Yes — a compromised/buggy process could log a fake entry, or skip logging a real one | Yes — a log entry says nothing about whether the module is still loaded or has since been reloaded | No — still self-report, same trust boundary as `echo_sentinel.json` | That an import *event* occurred, with a timestamp | That the module remains loaded now, or that anything in it was called |
| Decorator wrapping every function of interest (`@track_execution`) | The target process, at call time | A counter/log, self-report | Yes | The counter itself doesn't stale, but requires the decorator to have been applied everywhere relevant — a real, ongoing maintenance burden and a real place for silent gaps | No | That a specific call happened, with a real count/timestamp | Anything about calls to *undecorated* code — the evidence is only as complete as the decorator's own coverage, which is itself an unverified claim |
| `sys.settrace`/`sys.setprofile` (tracing/profiling hooks) | The target process, continuously | In-memory or logged, self-report | Yes (same trust boundary) | N/A while active; requires the hook to still be installed | No | Real, fine-grained call/line-level execution events, while the hook is active | Anything about execution before the hook was installed or after it's removed; also has real, non-trivial performance cost — CPython's tracing hooks slow execution meaningfully, a genuine production-risk consideration for anything wired into PID 7644's actual request path |
| PEP 578 audit hooks (`sys.addaudithook`) | The target process | Self-report (a log, typically) | Yes | Same as tracing | No | Specific audited events (e.g., `exec`, `compile`, `os.system`) — narrower and cheaper than full tracing, genuinely used elsewhere in this project's own F1/F2 self-edit safety pipeline (a real, existing precedent) | General function-call coverage — audit hooks fire for a fixed, Python-defined set of sensitive operations, not arbitrary user functions, without additional custom event registration |
| Heartbeat/counter file (extending the existing sentinel pattern) | The target process, periodically | `memory/*.json`, self-report — literally the same mechanism Layer 2 already reads | Yes, same trust boundary as the two files Layer 2 already reads | Yes — exactly the staleness question Layer 2's own red-team already examined at length | No | That the process was alive and executing *some* code at approximately the heartbeat's timestamp (this is already true of `echo_sentinel.json`'s existing `last_heartbeat_utc`, refreshed by `dmn_guardian.py`) | *Which* code, or that any specific module/function was involved |

**Cross-cutting finding**: every instrumentation mechanism considered shares the identical trust boundary Layer 2 already established for `echo_server.pid`/`echo_sentinel.json` — it is code running inside PID 7644, reporting about itself, with no independent witness. None of them close the "self-attestation ≠ independent proof" gap this whole architecture is built around; they only make the self-report *richer* (event-level instead of process-level). Whether that richer self-report is worth the real engineering cost (new code paths inside the live application, a real maintenance burden, real performance cost for the tracing-class options) is a separate decision from whether it's *architecturally sound* — it is sound, within the same "evidence, not proof" bounds Layer 2 already operates in, provided it is never labeled more strongly than that.

---

## 12. File-mutation-after-load analysis

Directly answered by the experiment in §7 item 1, not merely reasoned about: **current filesystem identity (Layer 1's domain) and the identity of code actually resident in a process (a hypothetical Layer 3 concern) are provably, empirically different things, and no existing mechanism in this codebase — Layer 1, Layer 2, or any self-report file — can detect the divergence.** A future consumer combining "Layer 1 says `file.py` matches HEAD" with "Layer 2 says PID 7644 exists and its self-report agrees" must not conclude "PID 7644 is currently running `file.py`'s current content" — the experiment shows this conclusion can be false even when every available check passes cleanly, because the running process may have loaded an *earlier* version of the file before the current on-disk content existed.

The only mechanism that could distinguish these two identities is a **self-report from inside the process, comparing its own loaded code object against a fresh read of current disk content** — and even that, per §7 item 2 and §9, must use a full code-object serialization (`marshal.dumps`), not `co_code` alone, or it will silently miss exactly the class of change (a literal constant) most common in real code edits.

---

## 13. PID/restart/reuse analysis

Layer 2's existing boundary is not weakened by anything found here — re-confirmed, not re-litigated:
- **Process dies**: `external_process.exists` correctly transitions to `False` (Layer 2's own red-team, real subprocess test).
- **Process restarts**: a new PID, a new `create_time` — Layer 2's `start_time_match_sentinel` correctly detects a stale self-report against the new process (Layer 2 red-team Finding 2).
- **PID reused**: same mechanism, same finding — correctly detected *if* both `pid_match_*` and `start_time_match_sentinel` are read together (Layer 2 red-team Finding 1/2, not re-tested here).
- **Code changes between launches**: this is exactly §12's finding, extended across a restart boundary — Layer 1 would correctly show new working-tree content after a restart picks it up, but nothing establishes *when*, relative to a specific process's lifetime, that content became the code actually resident in memory. A hypothetical Layer 3 self-report, taken at process-startup time, could establish "this process loaded this exact content at this exact moment" — but only if that self-report itself existed, and only for that one snapshot in time (§12 already shows it can go stale immediately if the file changes again while the process keeps running).
- **Self-report artifacts becoming stale** — already the central subject of Layer 2's own extensive staleness analysis; nothing new to add here.

**New finding, `psutil`'s own `create_time()` caching (§7 item 5)**: this is a genuinely narrow, previously-undocumented-with-this-precision addition to the PID-reuse picture — the very first read of a `Process` object's `create_time()` has no internal reuse protection, though every subsequent read on that same object does. Any future Layer 3 (or a refinement of Layer 2) that constructs a fresh `psutil.Process(pid)` object per observation, rather than holding one across multiple reads, inherits this narrow window on every single call. Worth flagging for a future, separately-scoped hardening pass — not acted on here.

---

## 14. Shadow-code / duplicate-module analysis

Directly demonstrated in §7 item 3: a bare module *name* has zero intrinsic identity. The following identity dimensions were evaluated for defensibility, not chosen prematurely:

| Dimension | Defensible alone? | Why |
|---|---|---|
| Module name | **No** | §7 item 3 proves two different files can both satisfy the same import name |
| Lexical/`sys.path`-relative path | **No**, on its own | Depends entirely on `sys.path` order, which can change per-invocation, per-environment, or via `PYTHONPATH` |
| Resolved (real) filesystem path | **Partial** | This is Layer 1's own `working_tree_file_identity`'s `fs_resolved_path` concept — tells you *which physical file* would be read *right now*, but (§12) not what was actually loaded historically |
| Git identity (tracked status, blob hash) | **Partial**, same caveat | Tells you about the repository's current state, not the process's memory |
| Content hash | **Partial**, same caveat as resolved path — a hash of *current* disk content, not necessarily *loaded* content |
| Module `__spec__`/loader identity | **In-process only** | Real, precise (`ModuleSpec.origin`, the loader class) but only obtainable via self-report — same boundary as `sys.modules` generally |
| Process identity (PID + start time) | Defensible for **which process**, not **which code** | Layer 2's own domain — orthogonal to the module-identity question entirely |
| Runtime code-object identity (a specific `__code__` object's contents) | **The only dimension that could, in principle, answer "what code is actually resident"** | Only ever obtainable from inside the process (§6, §7); requires the full-object comparison fix from §7 item 2, not `co_code` alone |

**No single dimension is sufficient alone.** The most defensible composite for a future primitive would combine resolved path (what's on disk now) + content hash (Layer 1, already exists) + an in-process self-report of the loaded module's own `__file__`/`__spec__.origin` + a full-code-object comparison — and even that composite would only ever answer "loaded code matches current disk content, as of the moment this self-report ran," never "is executing" or "was called."

---

## 15. Candidate Layer 3 primitives

### Candidate: `native_extension_observation(pid, extension_names)`

- **Inputs**: a PID, a list of package names to look for (e.g. `["faiss", "numpy", "torch"]`).
- **Outputs**: for each requested name, whether a matching shared-library path was found among the process's open file descriptors, and the matched path(s).
- **Evidence source**: `lsof -p <pid>`, parsed for `.so`/`.dylib` paths containing the requested package name.
- **Independence**: **Independent** — no cooperation required from the target process.
- **Proves**: that a native extension matching the given name is currently mapped into the process's address space.
- **Does NOT prove**: which *Python* module loaded it, when it was loaded, whether it is still in active use, or anything about pure-Python code (which never appears in `lsof`'s output at all, confirmed).
- **Principal attack surface**: package-name string matching against file paths is a heuristic (a package named `faiss-lite` would false-match a search for `"faiss"`) — would need exact-path or exact-directory-segment matching, not substring search, to be defensible.
- **Safe to implement**: yes — read-only, uses an existing, already-vetted external-process-observation pattern (the same `subprocess`-based approach Layer 1 already uses for `git`, applied to `lsof` instead).
- **Additional experiments required**: none beyond what this session already ran; the mechanism is proven working against the real PID 7644.
- **Scope note**: this primitive is real and safe, but its practical value is narrow (confirms a *dependency* is loaded, not a *FeralEcho module*) — it is not recommended as the next implementation step (§17) because it does not meaningfully advance toward the actual target question this mission was asked to investigate.

### Candidate considered and explicitly NOT recommended: `bytecode_self_report(module_name)`

- **Inputs**: a module name (e.g. `"app.core.provenance_check"`).
- **Outputs** (if built): whether the module is currently in `sys.modules`; if so, its `__file__`; a `marshal.dumps()`-based hash of each of its functions' code objects, compared against a fresh compile of the current on-disk file.
- **Evidence source**: entirely in-process (`sys.modules`, `__file__`, `compile()`).
- **Independence**: **Self-reported, unconditionally** — this is Candidate B from the Layer 2 boundary review, unchanged in status. §7's experiments refine *what it would need to compare correctly* (full code objects, not `co_code`) but do not change *who produces the evidence* or *whether it can be independently witnessed* — it cannot.
- **Proves**: (if built correctly, using full code-object comparison) that the process's currently-loaded version of a module's code matches a fresh read of the file at query time — a genuinely useful, narrow fact.
- **Does NOT prove**: that the module was ever executed beyond its own import-time initialization; that any specific function was called; that the match will still hold a moment later (§12); or anything independently, since the entire computation runs inside the process being described.
- **Safety**: requires new in-process code (a new Flask route or `echo_tool_dispatch.py` tool) — the same category of change the Layer 2 boundary review already found out of scope for a "smallest safe primitive," and still true here: **implementing this requires touching live application code and, to be exercised for real, a restart of PID 7644** — explicitly forbidden by this mission.
- **Additional experiments required**: none for the mechanism itself (proven in §7); a real test would require the actual new code path to exist and be exercised against a live restart, which this mission cannot and should not do.
- **Recommendation**: architecturally sound as a *self-report* primitive, structurally identical in trust category to Layer 2's existing self-report reading — but not implementable within this mission's read-only, no-restart constraint, and not the smallest possible next step even when it does become implementable (see §17).

### Candidate explicitly rejected: any `runtime_verified`/`code_is_running`-shaped primitive

Not designed, not sketched with fields — rejected outright per the mission's own explicit prohibition. No combination of evidence available today (or reasonably buildable without new, heavier instrumentation) supports a single boolean claim of this shape without overclaiming beyond what §9–§11 establish is actually knowable.

---

## 16. Explicit anti-claims

Layer 3, whenever it is eventually built, MUST NOT claim:

1. That a file matching HEAD (Layer 1) implies that file's *current* content is what a live process has loaded (§12, empirically disproven).
2. That `sys.modules` membership can be determined externally (§6, §8 — architecturally impossible without new in-process code).
3. That a native-extension match (the one real external Layer 3 signal found, §15) implies anything about which *Python* module triggered its loading, or when.
4. That `co_code` equality implies code equality (§7 item 2 — empirically false for constant-only changes; only full code-object comparison is valid).
5. That any bytecode comparison, however complete, proves execution rather than mere loaded-state (§10, §11 — no mechanism anywhere proves execution).
6. That an import hook, decorator, or tracing mechanism, if ever built, produces evidence independent of the process it instruments (§11 — every instrumentation option remains self-report, same trust boundary as the files Layer 2 already reads).
7. That a bare module name identifies a unique file (§7 item 3, §14 — sys.path order determines this, not the name).
8. That "the process exists and its self-report agrees" (Layer 2's own domain) implies anything whatsoever about which code that process is running (already the subject of Layer 2's own anti-claims; restated here because Layer 3's entire purpose is to close exactly this gap, and it does not).

---

## 17. Recommended next step

```
MORE RESEARCH REQUIRED
```

Not `IMPLEMENT`: the one primitive proven safe-and-independent this session (`native_extension_observation`) is real but too narrow to materially advance the actual target question (does not touch pure-Python module/execution evidence at all, §15's own scope note). The one primitive that *would* meaningfully advance the target question (`bytecode_self_report`) is architecturally sound but requires new in-process code and a live restart to ever be tested for real — both explicitly forbidden by this mission's own constraints, not just deferred by choice.

Not `NOT FEASIBLE AT THIS BOUNDARY`: this would overstate the finding. A bounded, defensible *loading*-level self-report primitive (module presence + `marshal.dumps`-correct code comparison) is feasible in principle and now specified precisely enough (§9, §12, §15) that a future, separately-authorized implementation mission could build it without repeating this session's discovery work — it is not "impossible," it is "requires crossing the no-restart boundary this mission was told not to cross."

Not `BLOCKED`: nothing about the research itself was blocked — every question in the mission brief was answered, with empirical evidence where testable and precise architectural reasoning where not (the two genuinely `BLOCKED — would require production mutation` items, SIP-restricted tracing and `py-spy` installation, are narrow sub-questions, not the mission's central finding).

**If a future mission is authorized to cross the restart boundary**, the smallest defensible next primitive is: an in-process, self-reported `module_load_and_content_check(module_name)` — reads `sys.modules.get(module_name)`, its `__file__`, and a `marshal.dumps()`-based comparison of each of its functions' code objects against a fresh compile of the current on-disk file at query time — returned as three separately-labeled facts (`loaded: bool`, `file_path: str|None`, `content_match: bool|None`), never merged into one verdict, exposed only via the same narrow in-process channel (`echo_tool_dispatch.py`-style tool registration, not a new unauthenticated route) Layer 2's own boundary review already established as the correct integration pattern. **Not implemented here.**

---

## Integrity

```
Starting HEAD:  e03f5984bb86d36ade51ed8f0753a3b8264c0f9f
Ending HEAD:    e03f5984bb86d36ade51ed8f0753a3b8264c0f9f   (unchanged)
Files modified: none
Files created:  audits/2026-09-13_layer3_runtime_provenance_boundary.md (this file)
Staged:         nothing
Committed:      nothing
Pushed:         nothing
Scratch experiments: 5, all under /private/tmp/.../scratchpad/l3_research/ and
                 .../l3_shadow/, entirely outside the repository, all removed
                 immediately after use, confirmed via directory-removal commands
                 recorded in this session's own tool history
PID 7644:       unchanged throughout -- confirmed via ps, psutil, lsof, and vmmap
                 (all read-only), same start time (Thu Sep 10 22:41:53 2026 /
                 2026-09-11T05:41:53 UTC) observed at every check, including the
                 vmmap cross-check which independently corroborates it via a
                 wholly separate OS mechanism
```
