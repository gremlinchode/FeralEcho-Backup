# RNU1C transport qualification

Executed October 6, 2026, PDT. Primary mission only; Gemini/Grok transport is reported separately.

## Verdict

**RNU-APPARATUS-NOT-QUALIFIED.** The original controller exception was reproduced and localized at runtime. A minimal research-only guard correction passed all 11 transport/write-protection controls. The subsequent frozen apparatus test nevertheless failed: its first confined Python child terminated with **SIGABRT / return code -6**, without a candidate result. Execution stopped. The other room and semantic comparisons were not reached.

**No RNU workload design or execution, no learning, no retained-state intervention, and zero model/API inference calls.** Neither failure is evidence about retained utility or Echo's learning ability.

## Opening integrity and authority

The full [prior report](2026-10-01_rnu1c_live_integrity_boundary_qualification.md), old guard, evaluator/profile, failed raw launch, and static analysis were inspected. The new namespace is `audits/rnu1c_transport_20261006/`; historical artifacts were not edited.

[Opening integrity](rnu1c_transport_20261006/opening_integrity.json) records branch `vsl-implementation`, HEAD `e5acbb09cece8d1791fa6d967fe57067137a8cff`, cached `origin/main` `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`, ahead 4 / behind 0, empty staging, and the pre-existing dirty tree. The eleven tracked modifications and unrelated untracked research/relay artifacts were preserved.

The previous Class I/II discipline was carried forward: **148 historical authority/input files pinned**; nine explicitly justified live mutable paths observed but never consumed as experimental input. Only new research roots and output/scratch directories were writable by the experiment. Class II changes alone were not reinterpreted as contamination.

[Opening](rnu1c_transport_20261006/out/opening_processes.json) and [closing](rnu1c_transport_20261006/out/closing_processes.json) observations show Echo PID 55361 (started October 1 15:45:19), watchdog 56610 (September 28 09:44:38), Ollama 1991 (September 19 10:57:03), and identity relays 84828/84838 unchanged. None was signaled or restarted.

The controller remains pinned trusted Python protected by an audit hook, not a sandbox for arbitrary malicious controller/native code. Children retain kernel sandboxing. The unguarded diagnostic arm deliberately removed only the controller hook, used fixed harmless source and retained candidate kernel write restrictions. This safe causal control is not proposed as the final apparatus.

## Prospective protocols

Each stage was frozen before its execution. Later stages did not amend earlier protocols.

| Stage | Protocol SHA-256 |
|---|---|
| [Diagnostic v1](rnu1c_transport_20261006/diagnostic_protocol.json) | `f6a77cdb5805fe863486d930df1e0c8542a46779ab5d7337b191b1a80da7dc85` |
| [Transport qualification v2](rnu1c_transport_20261006/transport_protocol.json) | `c230e1a246181036916217d63daea821bbe5b23297366a6f9e794bf0e1392f44` |
| [Apparatus v2](rnu1c_transport_20261006/apparatus_protocol.json) | `9397bf9c2ff7243e407e61153a26cb675ac75a2f041e303135f13cf23657061a` |

The diagnostic used two fresh processes, guarded and unguarded, with five fixed probes each. Observational wrappers preserved guard decisions, subprocess arguments and E0.1 behavior while recording descriptor metadata, exceptions, and `_execute_child` entry/PID. The first probe in each process exercised the E0.1 launch path with the same interface and confined-profile family as the failed apparatus, using a harmless deterministic calculation. No production evaluator changes were needed.

## Actual exception and discriminating evidence

Full exceptions, traceback, guard events, argv, stdin, environment and descriptor metadata are in [guarded raw evidence](rnu1c_transport_20261006/out/diagnostic_guarded.json). The [unguarded control](rnu1c_transport_20261006/out/diagnostic_unguarded.json) preserves the paired results.

The first guarded E0.1 call reproduced `SANDBOX_INFRASTRUCTURE_ERROR: OSError: launch failed`. Its underlying exception was:

```text
OSError: [Errno 9] Bad file descriptor
subprocess.run(input='{"args": [17]}\n')
  subprocess.py:1010  io.open(p2cwrite, 'wb', bufsize)
  diagnostic.py      observational hook → unchanged old hook
  support.py:51      self.check(path)
  support.py:44      self.path(p, dir_fd)
  support.py:39      fcntl.fcntl(p, 50, b'\0' * 1024)  # F_GETPATH
```

The descriptor was **FD 4**, `S_IFIFO`, device **0**, link count **0**, access flags **O_WRONLY**. `fstat` succeeded: the descriptor existed. `F_GETPATH` failed because this transport object was sent through the filesystem-path decision path. The recorder observed **no `_execute_child` entry** for that probe, so `sandbox-exec` was not launched by it. E0.1's generic error did not erase the separately preserved underlying traceback.

| Probe | Original guard | No controller guard |
|---|---|---|
| E0.1 with JSON stdin | errno 9 before child launch | Child PID 38715 launched; exited -6, no result |
| Filesystem-backed writable descriptor | Write/read `file-control` succeeds | Succeeds |
| Direct anonymous writable pipe wrapped by `io.open` | Same `F_GETPATH` errno 9 | Writes/reads `x` |
| Subprocess without `input=` | Exit 0; stdout `no-input`; stderr control intact | Same |
| Same transport child with `input=` | Same errno 9 before launch | Exit 0; exact `transport-v1\n` and stderr control |

Read ends of anonymous stdout/stderr pipes were observed as FIFO descriptors. The write guard correctly left those read wrappers alone; no-input capture worked. Thus the error was not a general subprocess prohibition, a missing interpreter, a filesystem FD problem, or a stdout/stderr capture failure.

## Root-cause classification before repair

The [classification record](rnu1c_transport_20261006/out/root_cause_verdict.json) was written before implementing a repair.

**STRONGLY SUPPORTED BUT NOT CONFIRMED**, under the deliberately strict frozen classification rule. That rule required the unguarded E0.1 call to complete successfully as well as the transport contrasts. The unguarded E0.1 call instead exposed a second failure, so the predeclared strongest label was withheld.

This qualification does not obscure what is directly observed: **the reproduced early launch exception originates in the old guard's `F_GETPATH` operation on the anonymous stdin pipe**. The independent pipe and input/no-input contrasts support that mechanism. What is not established is that removing this defect alone makes the confined E0.1 arrangement succeed.

| Evidence class | Finding |
|---|---|
| OBSERVED | Exact exception site, errno, descriptor type, no child launch under the original guarded input path; ordinary file/no-input controls succeed. |
| SUPPORTED MECHANISM | Writable anonymous transport is wrongly subjected to a filesystem-path lookup. A narrow classification correction is justified. |
| INFERENCE | The later confined-process abort may reflect a runtime dependency excluded by the read profile. Exact denied resource/cause is not established. |
| UNTESTED | Both-room contamination denial, behavioral equivalence, and all RNU performance claims. |

## Minimal repair and regression controls

[guard_v2.py](rnu1c_transport_20261006/guard_v2.py) is a **new research-only subclass**; the historical guard and all production files remain unchanged. [repair.diff](rnu1c_transport_20261006/repair.diff) preserves the added implementation.

The only new permission is wrapping a writable integer descriptor after `fstat` positively establishes FIFO type, device 0, link count 0, and actual access mode O_WRONLY—the anonymous pipe properties measured on this host. Other descriptors continue through the original filesystem authority check. An `fstat` error propagates. There is no blanket integer-FD exemption and no permission fallback after a failed `F_GETPATH`. Classification is repeated on every open; descriptor numbers are never cached as trusted.

At **08:01:12 PDT**, [fresh transport qualification](rnu1c_transport_20261006/out/transport_result.json) passed **11/11** fixed controls:

| Control | Result |
|---|---|
| Controller scratch create/write/read | PASS |
| Immutable-authority path write-open | DENIED, errno 1 |
| Live RiverBrain path write-open | DENIED, errno 1 |
| Own filesystem-backed FD wrapping/write | PASS |
| Pre-opened protected fixture FD wrapping | DENIED, errno 1 |
| Named filesystem FIFO outside authorized roots | DENIED, errno 1 |
| Anonymous pipe wrapping/write/read | PASS |
| Same formerly permitted FD number rebound to protected regular file | DENIED, errno 1 |
| Permitted subprocess without stdin payload | PASS |
| Stdin payload plus stdout/stderr capture | Exact contents preserved |
| E0.1 reference-profile candidate attempts production Skill A write-open | `CORRECT`; child returned `{"denied": true}` |

Protected-file probes used non-truncating opens and never wrote protected bytes. Pre-opened descriptors belonged only to harmless research fixtures. The FD-rebinding control used `dup2` to make the previously permitted pipe FD refer to the protected fixture, demonstrating that pipe permission did not follow the integer into filesystem authority. The named-FIFO control checked a related non-anonymous transport object. These are focused regressions, not a claim that the Python audit hook confines arbitrary hostile native controller code.

**Transport qualification passed.** The successful E0.1 reference-profile result verifies transport and independent grading; its broad-read reference profile does not qualify causal read isolation.

## Apparatus requalification and stop

The new [RNU1C-E01-SINGLE-v2 driver](rnu1c_transport_20261006/apparatus.py) used fresh rooms/canary, the transport guard, and complete launch-error recording. Candidate/evaluator/worker source, interpreter, flags, environment, timeouts, JSON protocol and comparison remained unchanged. The v1 confined profiles changed only in their disposable room path literals. No profile permission was added to rescue the observed abort.

The frozen order required both rooms' own-root reads, retained/other-room/hidden-answer read denials, production/surrogate write denials, symlink denial and successful scratch calculation before any semantic comparisons. Six reference-versus-confined domains—structured correctness, wrong value, bool/int distinction, candidate exception, unsupported result and timeout—were retained for both rooms, for at most 28 calls.

At **08:03:14 PDT**, the [first apparatus call](rnu1c_transport_20261006/out/apparatus_call_01.json) successfully passed controller transport but returned:

```text
returncode: -6
stdout: ""
stderr: ""
E0.1 outcome: CHILD_TERMINATED_UNVERIFIED
detail: nonzero exit -6, no parseable output
```

The controller recorded [RNU-APPARATUS-NOT-QUALIFIED](rnu1c_transport_20261006/out/apparatus_result.json) and stopped after **one** call. A zero controller exit is not candidate success. Room k7 produced no control results; room m2 was not attempted; semantic comparisons were not reached. Symmetry is unestablished, not inferred from setup.

Existing OS crash evidence confirms `python3.12` SIGABRT for the unguarded diagnostic PID 38715 and the later apparatus PID 38898. Read-only extracts with original file hashes are [diagnostic crash](rnu1c_transport_20261006/out/python3.12-2026-10-06-075534_extracted.json) and [apparatus crash](rnu1c_transport_20261006/out/python3.12-2026-10-06-080314_extracted.json). They record termination namespace `<0x23>`, code 2; no unsupported interpretation of that opaque code is asserted. No further launch/profile variant was tested.

## Closing integrity, counts and precise mutations

[Closing integrity](rnu1c_transport_20261006/out/closing_integrity.json), at **08:03:57 PDT**, finds **148/148 historical authority files unchanged** and every new frozen source/input/protocol hash intact. FAISS, metadata, RiverBrain and self-model bytes evolved. They remained excluded from experiment inputs; hash changes alone are not attributed to a particular writer.

Mutations were limited to additive `audits/rnu1c_transport_20261006/` fixtures, scripts, disposable roots, protocols, scratch/results, this report and its hash. A harmless named FIFO exists at `fixtures/named.fifo`; it is a test fixture, not a production endpoint. No Skill A/B, VSL, routing, memory, RiverBrain, evaluator, watchdog or LaunchAgent was edited. Nothing staged, committed, pushed, cleaned or reset. The OS also produced crash diagnostics for the two failed Python launches; those are disclosed runtime consequences, not learned-state writes.

There were 10 diagnostic probe outcomes across two fresh processes; three launch attempts per process. The guarded input calls did not reach child execution. Fresh repaired transport qualification made three child launches, including one successful E0.1 synthetic evaluation. Apparatus requalification attempted one E0.1 call and stopped. These counts are apparatus checks, not independent task-performance samples. **Inference calls: 0. RNU items/interventions: 0.**

## Handoff

The transport defect now has direct runtime evidence and a narrowly qualified correction. The smallest remaining problem is **why the confined Python child aborts after launch while the reference profile executes successfully**. A subsequent bounded mission should identify that runtime/profile boundary without broadening access to retained or answer-bearing files. No such profile repair was attempted here.

**Is there now a prospectively qualified, contamination-resistant apparatus suitable for designing a fresh RNU retained-state experiment? NO — RNU-APPARATUS-NOT-QUALIFIED.**

Future RNU workload design/execution is not authorized by this result. Return for adversarial review. Retained utility remains unmeasured.
