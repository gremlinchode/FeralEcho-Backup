# RNU-1B — Execution-Boundary Qualification

Date: **2026-10-01, America/Los_Angeles (PDT)**.

## 1. Final verdict

**RNU1B-INTEGRITY-FAIL — stopped before diagnostic subprocess execution.**

Five protected files changed between the opening snapshot and the mandatory pre-execution integrity check. The mission explicitly required stopping when a protected file changes. The diagnostic driver detected this condition **before importing the AP-0 jail or launching either planned sandbox diagnostic**. No corrected boundary was constructed or tested; no candidate executed.

This is an integrity-gate stop, **not evidence that a corrected execution boundary fails**, and not evidence about retained net utility. No baseline was reset and no protected file was restored. There was no retry.

RNU workload design is **not qualified to proceed on this evidence**. Return this report for review of the integrity rule and the unfinished boundary qualification.

## 2. Opening integrity and protected evidence

The [RNU-1 report](2026-10-01_rnu1_retained_net_utility_qualification.md), its frozen plan, driver and raw room-31 result were read, together with the actual AP-0 jail and E0.1 evaluator/worker source.

| Item | Opening observation |
|---|---|
| Branch | `vsl-implementation` |
| HEAD | `e5acbb09cece8d1791fa6d967fe57067137a8cff` |
| Cached `origin/main` | `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0` |
| Ahead / behind | 4 / 0, without fetching |
| Staging | Empty |
| Opening fingerprint completed | 12:03:22 PDT |
| Protected files | 447; all stable during their individual opening reads |

The [opening manifest](rnu1b_20261001/opening_integrity.json) preserves full status, tracked modifications, file sizes, modification times and SHA-256 hashes. The pre-existing eleven tracked modifications and numerous untracked research/relay artifacts were preserved. No cleaning, stashing, resetting, normalization or overwrite was performed.

Protection covered all inspected application Python source, E0.1, AP-0, sandbox profiles, original RNU-1 artifacts, production VSL files, historical skill records, RiverBrain, the task classifier, FAISS/index metadata, self-model/claims/shadow state, configuration, `start_echo.sh`, local LaunchAgent property lists and pre-existing tracked modifications. Sensitive configuration was fingerprinted, not printed. No live pickle or retrieval store was loaded into an application object.

Selected opening hashes, unchanged at closing:

| Artifact | SHA-256 |
|---|---|
| Production Skill A v4 | `aa00c0aee4563f25254f624255605afb5448ebfb8a08c0b4833fb6796a098e7e` |
| Experimental Skill B v1, file bytes | `0f272efdaeb531ace9fe461a2b67651bfdf8d5a5601e0f3a2583751c56fd4d20` |
| `trusted_evaluator.py` | `fdbd7314cfa557a293faac920dad630ac08a194bb0bb84a8a652ffc2a7058370` |
| `candidate_worker.py` | `823e6b4ee45a4820d121a761a06af4a55c2c5534154707dbd940ce037ba7b72b` |
| AP-0 `jail.py` | `044f9d80379f7931de6e12d682540c92845f7901a3b056b3d35a8e4dc25a6501` |
| `start_echo.sh` | `1b04e331690b2f01796b4eadc894305f383e0d68a41c815dcdf2cbc752393d15` |

Skill B's file hash above is distinct from its internal semantic `content_hash`; they are not interchangeable.

## 3. Process observations

| Service | PID | Start time |
|---|---:|---|
| Echo, `python -u run.py` | 71538 | Sep 28 19:15:54 |
| Watchdog, `zsh …/start_echo.sh` | 56610 | Sep 28 09:44:38 |
| Ollama server | 1991 | Sep 19 10:57:03 |
| Claude-identity relay server | 84828 | Sep 29 07:11:42 |
| Codex-identity relay server | 84838 | Sep 29 07:11:53 |

An Ollama inference runner was also present at opening; its activity was not initiated by this mission. No relay was contacted. The five listed service PIDs/start times were unchanged at closing, approximately 13:19:56 PDT. See [opening processes](rnu1b_20261001/opening_processes.txt) and [closing processes](rnu1b_20261001/closing_processes.txt). No service was signaled, stopped or restarted.

## 4. Reconstruction of the original failure

The preserved [RNU-1 raw result](rnu1_20261001/room_31_causal_gate_result.json) shows:

1. The outer AP-0-jailed Python process ran, loaded its copied runtime, and read its own copied Skill A with the expected hash.
2. Its attempts to read original A, experimental B, a controller artifact and the opposite room returned `PermissionError`.
3. E0.1 attempted its own `sandbox-exec` launch from inside that outer sandbox.
4. The inner launcher returned exit 65 and the following diagnostic:

```text
sandbox-exec: .../gate_rooms/room_31/sandbox/echo_sandbox.sb: Operation not permitted
```

E0.1 classified this as `SANDBOX_INFRASTRUCTURE_ERROR`. The outer controller then exited zero while reporting that failure. A zero outer exit was **not** a successful candidate result. RNU-1 recorded zero workload outcomes and zero model calls; RNU-1B does not reinterpret them.

## 5. Root-cause findings and evidence strength

**DIRECTLY OBSERVED:** the original failure occurs at the inner sandbox launch/application boundary, before a candidate result. Tested outer-process read restrictions worked. The source shows two sandbox layers in the failed composition.

**STRONGLY SUPPORTED:** a blanket inability to create any subprocess is not an adequate explanation of the original observation: `sandbox-exec` itself produced a real exit code and diagnostic. The successful outer imports/own-state read also rule out a blanket denial of every own-root read.

**HYPOTHESIS / UNRESOLVED:** applying a second sandbox under inherited restrictions may be the obstacle. The existing diagnostic does not separately establish whether the decisive restriction concerns profile-file access, profile compilation/application, or another inherited permission. The path printed in the error does not by itself prove that opening that file failed. This mission did not complete the discriminating test and therefore does not claim a precise macOS root cause.

## 6. Prospective diagnostic plan — frozen but not executed

Before execution, [root_cause_plan.json](rnu1b_20261001/root_cause_plan.json) froze exactly two top-level diagnostic invocations:

1. Apply a minimal `allow default` sandbox to `/usr/bin/true` outside AP-0.
2. Inside the unchanged AP-0 jail, read/hash that same profile, launch ordinary `/usr/bin/true`, then attempt the same minimal inner sandbox once.

This fixed comparison would distinguish profile readability and ordinary subprocess execution from nested application. It was a root-cause diagnostic, not an acceptable final candidate boundary: `allow default` was only for a harmless diagnostic process, never a proposed contamination-resistant evaluator profile.

Plan SHA-256:

`ea5961eb2677e48fd7e32586bed299795d8e6b9ef8bd179e64f328480831f3b8`

The [driver](rnu1b_20261001/root_cause.py) and diagnostic fixture hashes were pinned. Plan timestamp: **12:04:27 PDT**. When the invocation actually reached its pre-execution check at **13:19:15 PDT**, approximately 75 minutes had elapsed while the protected runtime remained active.

The driver checked protected hashes first and returned immediately on change. Thus **neither diagnostic invocation occurred**, including the nominal standalone control. No corrected-arrangement protocol exists; the diagnostic-plan hash must not be presented as one.

## 7. Exact integrity stop

[integrity_stop.json](rnu1b_20261001/integrity_stop.json) records `stage: before root-cause execution` and five changed paths. A later read-only closing snapshot recorded the following sizes and modification times; its hashes are the **closing values**, not necessarily the exact values at first detection.

| Protected file | Opening bytes → closing bytes | Closing modification time, PDT |
|---|---:|---|
| `memory/faiss.index` | 209,530,413 → 209,565,741 | 13:17:18.395 |
| `memory/memory_meta.json` | 109,056,224 → 109,098,872 | 13:17:18.317 |
| `memory/river_brain.pkl` | 4,812,152 → 4,757,753 | 13:19:29.328 |
| `memory/self_model.json` | 18,680 → 18,660 | 13:17:52.416 |
| `sandbox/scripts/temp_self_edit.py` | 933 → 565 | 13:16:28.712 |

Full before/after SHA-256 values are in [closing_integrity.json](rnu1b_20261001/closing_integrity.json). The other **442 protected files** retained their opening hashes, including original RNU-1 evidence, Skill A/B, E0.1, AP-0 and launch configuration.

**Attribution:** no RNU-1B candidate or sandbox diagnostic had run, and the audit's writes were confined to its new audit namespace. The observed changes are consistent with independent live-runtime activity, but hashes/mtime alone do not identify the writer. No audit-caused production mutation is evidenced. Nevertheless, the user's second stop condition was any protected-file change; this mission did not silently narrow it to proven audit-caused changes.

## 8. Corrected architecture and required controls: not reached

No replacement evaluator, profile, wrapper, adapter or two-arm qualification environment was implemented. The only disposable directory contains the unexecuted root-cause diagnostic fixtures. The intended required controls retain their original meanings:

| Requirement | Status |
|---|---|
| P1: read own-root ordinary file | NOT RUN |
| P2: read candidate-local runtime/input artifact | NOT RUN |
| N1: deny original production Skill A | NOT RUN in RNU-1B |
| N2: deny experimental/historical skill | NOT RUN in RNU-1B |
| N3: deny opposite-arm artifact | NOT RUN |
| N4: deny existing hidden-answer canary | NOT RUN |
| N5: deny historical answer-bearing artifact | NOT RUN |
| Harmless deterministic candidate genuinely executes and grades correctly | NOT RUN |
| Both rooms independently satisfy the controls | NOT RUN |

No exact candidate paths, candidate body, canary value or expected results were frozen for these controls because the corrected-arrangement phase was never reached. Historical room-31 checks are not substituted for new candidate-level or symmetric qualification. Neither absence of results nor the driver's successful exit qualifies a boundary.

## 9. E0.1 semantic analysis

The inspected [trusted evaluator](../app/experiments/rung1/trusted_evaluator.py) uses the pinned FeralEcho Python interpreter with `-I -B -S`, its existing candidate worker, a fresh child/scratch directory per case, a default 10-second timeout, minimal child environment and closed inherited descriptors. Only call arguments cross its stdin protocol; expected values remain in the trusted parent. Parsed child output is compared by unchanged trusted code after child completion, including its existing typed-JSON/error conventions.

The existing profile permits broad reads, restricts writes to scratch/devices, denies network, and does not grant process-fork. A future confinement arrangement would have to narrow read authority while preserving the independent comparison and documenting that intentional behavioral difference. It cannot silently be called unchanged E0.1.

**No evaluator behavior changed here. No prospective equivalence test ran.** Source preservation alone does not qualify an unimplemented corrected arrangement. Interpreter/worker/timeout/protocol/subprocess/scoring equivalence for that arrangement remains unmeasured.

## 10. Closing integrity, counts and limits

The protected-state changes were preserved, not overwritten or normalized. Live Echo, watchdog, Ollama and relays retained their PIDs/start times. Staging remained empty; HEAD was unchanged. Nothing was committed or pushed. No existing skill, matcher, routing, learner, evaluator, RiverBrain, memory, self-model, watchdog or LaunchAgent was modified by the audit.

Exact mission counts:

- Diagnostic sandbox invocations: **0**.
- Corrected-boundary candidate executions: **0**.
- RNU workload items generated/evaluated: **0**.
- Learned-state interventions/acquisition: **0**.
- Local inference calls: **0**; external model/API calls for the experiment: **0**.

Repository inspection, hashing, git metadata commands and read-only process observations did execute; they are not candidate evaluations. The root-cause driver's exit zero means it recorded the required stop, not that its diagnostic or the apparatus passed.

This result establishes that the present **global byte-stability prerequisite was not satisfied during this preparation interval**. It does not establish a sandbox impossibility, evaluator mismatch, negative utility, continual-learning failure, invalid historical Skill A/B evidence, or a hardware ceiling.

## 11. Smallest unresolved problem and handoff

Two questions remain distinct:

1. **Immediate protocol obstacle:** the live system legitimately remains active, while the current rule requires all sampled mutable production files to retain their opening bytes. This interval failed that condition before any test. Another unmodified attempt could stop for the same reason without teaching us anything about candidate isolation.
2. **Still-unanswered technical question:** can candidate filesystem confinement and E0.1's trusted comparison operate together successfully and symmetrically without the failed nesting?

Before authorizing another execution, review a narrowly scoped integrity amendment: retain strict immutability for historical evidence, source/configuration, Skill A/B and frozen experimental snapshots; separately record live mutable-state changes and establish that the research processes cannot write production. Treat unexplained experiment-input changes or research-caused production writes as failures. **That amendment was not adopted here.** It needs explicit review rather than a post-result baseline reset. Do not stop Echo to manufacture byte stability.

Then, if authorized, finish the already bounded root-cause question and prospectively qualify one corrected arrangement. Do not use this report as permission to start RNU workload design or inference. There is no qualified apparatus result to review yet.

> Do we now possess a prospectively qualified, contamination-resistant, symmetric execution boundary capable of measuring the causal effect of retained-state availability without changing the learner?

**NO — not established.** The immediate unresolved measurement problem is an unsatisfied integrity prerequisite in the presence of a changing live runtime; the sandbox-composition problem remains technically unresolved because its diagnostic never ran. Stop and return for review.
