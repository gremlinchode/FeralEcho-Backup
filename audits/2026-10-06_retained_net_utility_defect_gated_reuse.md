# Retained net utility and defect-gated reuse — bounded measurement gate

Executed October 6, 2026, PDT. **Disposition: MEASUREMENT-BLOCKED.**

The original confined-child SIGABRT was reproduced and a narrow runtime permission correction causally supported. The newly frozen full-boundary qualification then failed during trusted-controller scratch cleanup. Execution stopped at the first unexpected failure, as preregistered. Neither a retained-utility workload nor the proposed defect-gated improvement was implemented or evaluated.

**Experimental model calls: 0. Workload items: 0. Learned-skill applications: 0. A/B/C performance outcomes: not measured.** This is not a positive, neutral, or negative result about retained learning.

## Opening state and unchanged baseline

[Opening integrity](net_utility_gated_20261006/opening_integrity.json) records the repository, flags, exact skills, historical test status, 203 pinned immutable authority/source files, and nine separately classified live mutable files. Existing source and skill copies are preserved under [authority/](net_utility_gated_20261006/authority/). Historical RNU, RNU1B, RNU1C and transport evidence was inspected and preserved. Relevant CER/BJQ evidence and production VSL consumption were reviewed; no historical favorable specimen was selected as a new workload item.

| Item | Observed state |
|---|---|
| Branch | `vsl-implementation` |
| HEAD | `e5acbb09cece8d1791fa6d967fe57067137a8cff` |
| Cached origin/main | `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0` |
| Ahead / behind | 4 / 0; no fetch |
| Staging | Empty |
| Working tree | 14 pre-existing tracked modifications plus extensive untracked research/relay artifacts; preserved, not cleaned |
| Echo | PID 55361, started October 1 at 15:45:19 |
| Watchdog | PID 56610, started September 28 at 09:44:38 |
| Ollama | PID 1991, started September 19 at 10:57:03 |
| Controller VSL flags | `VSL_ENABLED` and `VSL_MODE` unset; no matching assignments found in the inspected `.env`/startup source |
| Code defaults | VSL disabled unless enabled; shadow mode if enabled without an explicit mode |
| Live process flags | Not established; its potentially secret-bearing environment was not dumped |

The flags above do not establish that the live instance currently uses active VSL. Any later active-consumer experiment must state its experimental flags explicitly and must not describe an activation choice as an observation about live Echo.

| Skill | Exact version and status | File SHA-256 |
|---|---|---|
| A | `K2.T5.tag_priority_direction.v4.json`; validated, ACTIVE, held-out PASS | `aa00c0aee4563f25254f624255605afb5448ebfb8a08c0b4833fb6796a098e7e` |
| B | `K2.T2.discovered_via_accumulation_test.v1.json`; experimental candidate, no ACTIVE lifecycle state | `0f272efdaeb531ace9fe461a2b67651bfdf8d5a5601e0f3a2583751c56fd4d20` |

B must not silently become an active production skill in a later unchanged-VSL baseline. Neither skill was edited, promoted, applied or reacquired here. All skill-ledger source versions are pinned by file hash in the opening manifest, preserving the dirty-worktree baseline rather than assuming HEAD alone reproduces it.

Relevant existing qualification status: the prior transport guard passed 11/11 transport/write controls; the full confined apparatus failed at its first child SIGABRT. Both-room semantic equivalence and RNU outcomes remained unestablished. Those are historical results, not newly rerun tests.

## Prospective bounded diagnosis

The [diagnostic plan](net_utility_gated_20261006/diagnostic_plan.json) allowed at most six harmless startup launches, one narrowly evidenced correction version, and 20 active diagnostic minutes excluding approval waits and a separately frozen final qualification. It prohibited workload selection, skill interventions and inference before that gate. All six startup launches were used; no additional startup variants were tried.

| Frozen artifact | SHA-256 |
|---|---|
| Diagnostic plan | `22ac54b4103e7c34bf289fc8f5c7e2f19dd432b61c3beac333cedd41979550d2` |
| [Initial startup protocol](net_utility_gated_20261006/startup_frozen.json) | `ec0a08045d41d18ae35d6bf1b23ed1ce9f5130a5717664cebe4484d4b7f7d0a7` |
| [Root-directory intervention protocol](net_utility_gated_20261006/root_directory_frozen.json) | `9b24d91b33b1a42d5b823533e9ad0492834c275f2ecb04d2d0ac373302c61346` |
| [Two-room v3 protocol](net_utility_gated_20261006/boundary_v3_protocol.json) | `1df3c8ebc808adc5c7486e6ed3e845def3537111d487fd0a9778b8ef88fd02a3` |

Each stage was frozen before its execution. Later protocols did not amend historical failures. All pinned inputs and protocol hashes remained intact at closure.

## SIGABRT: evidence and causal intervention

The complete prior crash stack and the new exact-PID crash extract locate termination in dyld initialization: `ignition_halt → boot_boot → ignite → CacheFinder`, before Python executes the worker or candidate. The local dyld binary contains a `failed to open root directory: %s: %d` diagnostic. The confined profile allowed runtime directories and the disposable room but lacked a data-read permission for the root directory object itself.

The intervention added exactly:

```scheme
(allow file-read-data (literal "/"))
```

This is a literal directory-object permission, **not** a recursive `(subpath "/")` grant. No descendant-file-content, write, network or process permission was added. [Profile diff](net_utility_gated_20261006/out/profile_v3.diff) also records the necessary disposable-room path substitution. Production profiles and evaluators were unchanged.

| Probe | Program/profile | Result |
|---|---|---|
| S1 | Python startup marker, original confined profile | PID 55237; SIGABRT, return -6; empty stdout/stderr |
| S2 | Identical Python, unchanged E0.1 reference profile | PID 55239; exit 0; exact marker |
| S3 | `/usr/bin/true`, original confined profile | PID 55240; SIGABRT, return -6 |
| S4 | Identical Python, literal-root-read permission added | PID 55309; exit 0; exact marker |
| S5 | `/usr/bin/true`, same correction | PID 55310; exit 0 |
| S6 | Identical Python, original confined profile again | PID 55311; SIGABRT, return -6 |

Initial probes ran at approximately 21:49:21 PDT. The frozen correction/removal probes ran at 21:54:34. Raw argv, environment, stdout/stderr, exit codes, durations and timestamps are in [startup results](net_utility_gated_20261006/out/startup_result.json) and [intervention results](net_utility_gated_20261006/out/root_directory_result.json).

**DIRECTLY OBSERVED:** failure under the original permission set, success after only the literal-root-read addition, and failure when the original permission set is restored; the same effect occurs for Python and a non-Python executable.

**STRONGLY SUPPORTED:** absent root-directory read authority prevents dynamic-loader startup in this profile on this host. Candidate logic, model quality and the Python worker are not needed to reproduce the failure.

**UNRESOLVED:** the exact denied loader syscall and errno were not captured. [The complete bounded system-log window](net_utility_gated_20261006/out/startup_system_log.json) shows sandbox application and crash handling but no precise denial. [Crash extract](net_utility_gated_20261006/out/python3.12-2026-10-06-214921.ips.extract.json) and [dyld strings/hash](net_utility_gated_20261006/out/dyld_strings.json) support localization, not an invented syscall trace. No general macOS-version or sandbox-security conclusion follows.

`otool` inspection was unavailable because the installed Xcode license had not been accepted; no license or system configuration was changed. A brief external search yielded no load-bearing causal evidence. The correction rests on local runtime contrasts.

## Full qualification v3 and preserved failure

[RNU-E01-SINGLE-v3](net_utility_gated_20261006/boundary_v3.py) copied unchanged E0.1 evaluator/worker source into two fresh rooms. It retained the previously qualified `guard_v2`, interpreter, flags, minimal environment, JSON protocol, trusted comparison and timeouts. Candidate execution used one OS sandbox; no failed nested AP-0 sandbox composition was reintroduced.

The frozen gate required both rooms to complete:

- Own `ordinary.txt` and `runtime_input.json` reads.
- Denial of original Skill A, experimental Skill B, opposite-room input, a fresh hidden canary, and the historical prospective result.
- Denial of non-truncating write-opens to Skill A and a protected disposable surrogate.
- Denial through an own-scratch symlink to the hidden canary.
- A targeted regression control: opening `/` succeeds, but root-relative `openat` reads of Skill A and the hidden canary remain denied.
- Successful scratch arithmetic returning 292.

Only then would six reference/confined semantic pairs run in **each** room: structured correctness, incorrect value, bool/int distinction, candidate exception, unsupported result, timeout. Maximum 28 calls; first unexpected failure stops execution; no retry or fix-forward.

At **21:59:00 PDT**, the first filesystem call failed during E0.1's `TemporaryDirectory` cleanup. [Full exception and stop record](net_utility_gated_20261006/out/boundary_v3/result.json):

```text
shutil._rmtree_safe_fd
  os.unlink(entry.name, dir_fd=topfd)
guard_v2.hook → original WriteGuard.hook → check → path
  os.path.realpath(...) resolves canary_alias to protected/answer_canary.txt
PermissionError: [Errno 1] RNU1C controller write denied:
  .../boundary_v3/protected/answer_canary.txt

tempfile cleanup recovery also raises; run_case does not return.
```

The guard applies a target-following canonicalization rule to `os.remove`. Removing a symlink is a directory-entry operation: the final symlink target is not the object `unlink` removes. The observed guard exception and its source strongly support a false denial of legitimate in-scratch cleanup. This is a controller filesystem-operation-semantics defect, not evidence that the candidate escaped confinement. No repair of it was attempted in this pass.

The scratch directory and its `canary_alias` remain preserved. The alias was created by the synthetic candidate, providing evidence that execution progressed beyond the previously aborting loader. That is **not** sufficient evidence that all read/write controls passed.

**Evidence-capture limitation:** the launch recorder kept subprocess observations in memory and wrote them only after `run_case` returned. Cleanup raised before that return, so this first child's complete stdout/stderr/exit code and the comparator's prepared result were not persisted. The failure traceback is complete; the missing child output was not fabricated or recovered by rerunning. This limitation prevents claiming a passing filesystem-control row even if an internal comparison may have occurred. A future driver should preserve launch observations before cleanup can mask them, under a new freeze.

| Qualification component | Status |
|---|---|
| Narrow startup correction | Supported by the six frozen contrasts |
| Room k7 full filesystem/evaluator call | Failed in controller cleanup; no completed return |
| Room k7 scratch arithmetic | Not reached |
| Room m2 | Not reached |
| Both-room symmetry | Not established |
| Six semantic domains in both rooms | Not reached |
| RNU apparatus | **Not qualified** |

The controller process exited zero while explicitly reporting `MEASUREMENT-BLOCKED`; that exit code is not evaluator success. The mission stopped rather than editing the frozen driver, removing the symlink test, swallowing cleanup errors or weakening production protection.

## Integrity and exact scope of changes

[Closing integrity](net_utility_gated_20261006/out/closing_integrity.json), collected at **22:06:44 PDT**, verifies:

- **203/203 original immutable files unchanged.** Skill A/B, VSL source/state authorities, historical evidence, E0.1/worker and configuration pins remain intact.
- All new frozen protocol/input hashes match. Protected canary and surrogate bytes are unchanged.
- Echo, watchdog and Ollama retain their original PIDs and start times. None was signaled, restarted or stopped.
- Staging remains empty; branch and HEAD unchanged. No commit, push, clean, reset or stash.
- Five prospectively classified live mutable files changed: FAISS, memory metadata, RiverBrain, self-model and `sandbox/scripts/temp_self_edit.py`. They were not experimental inputs. Hash observations do not attribute their writers; no research action authorized or intentionally performed those writes.

Our repository additions are confined to `audits/net_utility_gated_20261006/`, this report and its checksum. No production source/profile, learned state, applicability logic or relay was changed. OS-generated crash reports are disclosed side effects of the three deliberately bounded failing startup controls. Scratch cleanup partially removed transient candidate files before failing; the remaining scratch symlink is preserved as evidence, not normalized away.

The first closing-snapshot command could not invoke `ps` inside Codex's sandbox and wrote no closing file. It was repeated with approval solely to capture read-only process/hash evidence; no experimental execution was repeated.

Controller confinement remains a Python audit hook for pinned trusted code, not a sandbox for arbitrary malicious native controller code. Candidate confinement is kernel enforced. This qualification does not claim a comprehensive security audit.

## Answers to the scientific questions

**Was Echo better off because it possessed retained experience on independently selected tasks?** Unknown. No workload was selected or evaluated; A/B were not run. Fixes, regressions, ties and abstentions are **not measured**, rather than evidence of zero effect.

**Did independently establishing a defect before applying retained knowledge improve its use?** Unknown. C was neither implemented nor run. Earlier BJQ evidence still motivates the hypothesis: its harmful specimen lacked the target defect, whereas the beneficial specimen contained it. That selected mechanistic contrast is not system-level net utility.

**May acquisition and accumulation research reopen on this evidence?** No new justification. Required evidence remains an unselected, contamination-resistant paired net-utility comparison followed by the frozen defect-gated comparison, with costs and harms counted. No hardware, learning or retained-utility conclusion follows from this measurement failure.

## Smallest next action

Qualify a **research-only operation-aware cleanup guard**, not a new sandbox or learner. The load-bearing distinction is removing an authorized directory entry versus modifying the object it points to. A fresh bounded protocol should test safe removal of an in-scratch symlink without changing its protected target, continued denial of protected direct operations and paths traversing unauthorized parent directories, and durable capture of child results before cleanup. Only after those controls pass should a newly frozen two-room gate run.

Do not broadly exempt symlinks, ignore cleanup exceptions, grant protected-target writes or delete the preserved failure. The present evidence does not show that substantial architectural redesign is necessary; it shows that the current composition is not yet qualified and the frozen pass permits no further repair-and-retry.

**Current decision: MEASUREMENT-BLOCKED. Preserve this failure, repair/qualify that one controller boundary separately, and then return to the original net-utility question. Retained learning and defect-gated reuse remain unmeasured.**
