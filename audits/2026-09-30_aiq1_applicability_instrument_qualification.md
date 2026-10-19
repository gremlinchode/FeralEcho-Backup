# AIQ-1 — Applicability instrument qualification

2026-09-30 · Codex · Deterministic, bounded qualification; no learning or production changes.

## Executive verdict

**AIQ1-QUALIFIED**

**PROCEED TO BOUNDED JURISDICTION QUALIFICATION**

The behavioral measurement concept survives the two specified challenges. With opaque, counterbalanced names and the existing E0.1 isolated executor, the known correct implementation received 24/24 correct-direction votes, and the known reversed implementation received 24/24 reversed-direction votes. All five nonsemantic shortcuts abstained. The deliberately invalid implementation was classified as invalid.

This qualifies this finite calibration family and these controls. It does **not** retroactively fix BA-3, establish general resistance to arbitrary programs, or authorize Skill A's transformation. The historical files remain unchanged. Testing stopped after the frozen eight controls; BA-4 was not remeasured.

## 1. Opening evidence and integrity

Read the [RBQ-1 report](2026-09-30_rbq1_retained_state_boundary_recovery_qualification.md) in full, then checked source. The [opening record](aiq1_20260930/baseline.json) preserves the complete working-tree status and protected-file hashes.

| Item | Opening observation |
|---|---|
| Timestamp | 2026-09-30 17:18:00 PDT; America/Los_Angeles |
| Branch | `vsl-implementation` |
| HEAD | `e5acbb09cece8d1791fa6d967fe57067137a8cff` |
| Cached origin/main | `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0` |
| Ahead/behind cached origin/main | 4 / 0; no fetch or push |
| Staging | Empty |
| Echo | PID 71538; started September 28, 19:15:54 PDT |
| Watchdog | PID 56610; started September 28, 09:44:38 PDT |
| Ollama | PID 1991; started September 19, 10:57:03 PDT |

Eleven tracked modifications predated this mission: `CLAUDE.md`, `PENDING_DECISIONS.md`, three `app/core` runtime files, three relay files, `logs/janitor_report.json`, `sandbox/scripts/temp_self_edit.py`, and `staging/self_edit_candidate.py`. Numerous untracked research artifacts also predated it, including the BA directory. Nothing was cleaned, reset, or assumed to belong to this mission. Process identities and start times were unchanged at closing; see [process observations](aiq1_20260930/processes.txt).

All six requested hashes match RBQ-1 exactly:

| Protected artifact | SHA-256 |
|---|---|
| BA-3 `ba3_instrument.py` | `e0753eeca69249a329f2328ce2569f3bbada4fee57ff2cee260471baf8a35a52` |
| BA-0 `sentinel.py` | `ef178a67e3796fbe98e9c730d17221827d8868020b1a0c7c07871b5dd41785ec` |
| BA-4 `ba4_protocol.py` | `c0b1b3cb3834bbc1cd3461bbf6f4f93bafd453d0e469fa79ae51e2d3dc0e5186` |
| BA-4 `ba4_run.py` | `75b432ad76b13d95b06eec10b62c024ef1ef2a297023d8270a26c174c97b266d` |
| BA-4 `ba4_predictions_FROZEN.json` | `c9120b4fece2019afafc3de9e98130f0f91cfe9dc9e7151568a29ea76f2aa4ad` |
| BA-4 `ba4_scored.json` | `e91de90323063e78684b93a4657d1ab34acd570ae7985ee60e0b80302a1288e7` |

The baseline also fingerprints the existing E0.1 parent/worker/profile, all four production Skill A records, experimental Skill B, the BA-4 candidate pool, and RBQ-1 report. Every protected hash remained unchanged through execution and closing verification.

## 2. Both source findings reproduced before candidate execution

**BA3_EXECUTION_NOT_ISOLATED**

[BA-3's actual path](../app/experiments/ba0_behavioral_applicability/ba3_instrument.py:132) is `judge_tag_priority_direction → _run_case → exec(code, ns) → candidate function`. This occurs inside the judge process. Importing `oracle_runner` does not execute through it; the relevant path invokes neither a subprocess nor the sandbox. The prose claim of shared trusted execution is unsupported by that invocation.

**NAME_CHANNEL_CONFIRMED**

[Case construction](../app/experiments/ba0_behavioral_applicability/ba3_instrument.py:162) gives the higher-priority entry `W_<tag>` and the lower-priority entry `L_<tag>` in both input orders. Since `W > L`, lexical maximum always selects the expected higher-priority entry; lexical minimum always selects the lower. The argument applies to all six pairs and both orders, independently of the tag text. BA-3 accepts a bare selected name. Therefore names alone suffice for a perfect historical correct-direction or reversed-direction classification.

This is a source-derived counterexample. No historical candidate or exploit was executed to establish it. It does not show that historical candidates used this channel. The subsequent qualification tests the explicitly authorized answer-neutral case family; it does not repair the historical instrument.

## 3. Frozen design and independently known controls

The [complete protocol](aiq1_20260930/protocol.json), including every input and candidate body, was frozen at **17:21:16 PDT**, before execution began at **17:31:08 PDT**.

* Protocol SHA-256: `616393af684ff213ac7bd4f53fa8f6cde655244e109896240dd52ddc6916e94a`
* [Qualification driver](aiq1_20260930/qualification.py) SHA-256: `ff31329b3c35e03511c6b8f0217bad58ee502329b123688f8dd5e6162828ae79`
* Seed: `20260930`; maximum 192 child executions, zero inference calls, no retries.

The target remains **tag-priority direction for two equal-score entries with distinct priorities**. This is a synthetic calibration world, not a new hidden AP-0 cohort: tags `vek, nop, sul, rim`, with canonical best-to-worst order `sul, vek, rim, nop`. Neither tag spelling nor input-list order defines that priority. Every entry has score 7, as in BA-3.

There are six unordered tag pairs. Each pair receives two seeded opaque names, generated without consulting ranks or expected answers. The same names exchange roles in the second assignment. Each assignment is then tested in both entry orders: **6 × 2 × 2 = 24 cases per control**. Within each assignment, the larger name belongs to the expected winner in exactly three pairs and the loser in three. First, second, lexical minimum, and lexical maximum therefore each have an analytically determined 6/12 correct choices per assignment. These balance checks occurred before candidate execution.

For example, one pair uses `item_73QV4B` and `item_DT75BC`. The first assignment associates the first name with `vek` and the second with `nop`; the second assignment exchanges names without changing tag priority. Each association is presented in both orders. No candidate receives role names, case IDs, assignment IDs, or an expected-label field.

| Control | Frozen implementation | Independent ground truth |
|---|---|---|
| P+ | Minimize canonical ordinal of `entry[2]`; return name | Higher priority by definition of the independently specified canonical ordering |
| P− | Maximize that ordinal; return name | Lower priority on every distinct-tag pair |
| P0 | Raise `ValueError` | No result; execution invalid |
| C1 | Return first entry's name | Position only |
| C2 | Return second entry's name | Position only |
| C3 | Return smallest name | Name only |
| C4 | Return largest name | Name only |
| C5 | Return `item_constant`, absent from all inputs | Constant; unextractable |

P+/P− labels follow directly from the mathematical ordering and inspected bodies; the instrument was not used to discover their labels. The other controls contain no tag-priority computation. Their exact source and hashes are in the protocol.

**Decision rule:** reuse BA-3's unchanged winner extractor; reproduce its aggregate rule and precedence, including unanimity among determinate votes and its prefix-based INSENSITIVE branch. Report both assignments separately and pooled. Qualification additionally requires complete correct/reversed coverage for P+/P−, all P0 calls to be invalid, and every shortcut to abstain in each assignment and pooled. No failed calls may be silently excluded. Unexpected execution/infrastructure results stop the run; no fallback, repair, or retry is authorized. The optional BA-4 follow-up was explicitly excluded before execution.

## 4. Actual isolated execution

Every candidate call used the unchanged [E0.1 `run_case`](../app/experiments/rung1/trusted_evaluator.py:289), which launches:

```text
sandbox-exec -f sandbox/echo_sandbox.sb -D SCRATCH=<fresh directory>
    <pinned Python> -I -B -S candidate_worker.py <candidate path> choose
```

The [worker](../app/experiments/rung1/candidate_worker.py) executes candidate code in that fresh child, not inside the judge. The parent provides source plus permitted entries, retains the expected identity, captures the structured result, and compares after child exit. Each call has a 10-second timeout, minimal environment, closed inherited descriptors, and separate scratch directory. Existing stdout suppression and result validation are reused without modification. No production module is imported by the driver.

Tool permission was obtained to invoke the existing macOS sandbox outside Codex's enclosing sandbox. This did not remove the candidate sandbox. There was no failed launch, alternate execution path, or retry.

**Scope limit:** the existing profile allows broad filesystem reads. The frozen synthetic protocol is a public audit artifact, not a protected real-task secret. All eight controls were inspected and contain no filesystem, network, reflection, or process access. AIQ-1 removes the answer signal from the candidate's supplied entries and uses a separate address space; it does not certify filesystem secrecy against arbitrary hostile programs. That broader claim was neither required nor tested.

The [raw ledger](aiq1_20260930/raw_results.jsonl) preserves each exact E0.1 API result. For INCORRECT it includes the returned value supplied by E0.1. For CORRECT, E0.1 omits the value; typed equality to the expected string uniquely determines it, and the driver records that reconstructed value explicitly according to the frozen protocol. Successful worker stdout bytes are not separately exposed by the existing API. P0's error type and stage are preserved. No model self-evaluation was used.

## 5. Results and stop

Execution completed at **17:31:16 PDT**. [Result summary](aiq1_20260930/results.json):

| Control | Higher-priority votes | Lower-priority votes | Other | Pooled classification |
|---|---:|---:|---|---|
| P+ | 24 | 0 | 0 | TARGET_PROPERTY_CORRECT |
| P− | 0 | 24 | 0 | TARGET_PROPERTY_REVERSED |
| P0 | 0 | 0 | 24 candidate `ValueError` results | EXECUTION_INVALID |
| C1 first | 12 | 12 | 0 | TARGET_PROPERTY_INSENSITIVE |
| C2 second | 12 | 12 | 0 | TARGET_PROPERTY_INSENSITIVE |
| C3 lexical min | 12 | 12 | 0 | TARGET_PROPERTY_INSENSITIVE |
| C4 lexical max | 12 | 12 | 0 | TARGET_PROPERTY_INSENSITIVE |
| C5 constant | 0 | 0 | 24 unextractable results | TARGET_PROPERTY_UNDETERMINED |

Both separate naming assignments give the corresponding same classifications: P+ 12/12 correct, P− 12/12 reversed, C1–C4 each 6/6 split, P0 12 invalid, C5 12 unextractable. **No shortcut survived.** There were no timeouts, unexpected exceptions, infrastructure failures, malformed results, missing cases, retries, or protocol deviations. The 24 P0 errors are intended negative-control outcomes.

BA-3's INSENSITIVE branch compares the prefix before `_`. All AIQ identifiers share `item`, so mixed results reach that branch. Here its justified interpretation is **abstention from a direction verdict**, not proof of a particular internal mechanism or constant-identity behavior. No change to that rule was made, and no additional investigation was opened.

An independent read-only recount confirmed 192 distinct control/case records and agreement between every recorded value/error and vote. These are deterministic calibration cases, not 192 independent statistical samples supporting a general accuracy estimate.

* Raw-ledger SHA-256: `d7810e85f3673e7c37985c9770587f1d02a112950bc3f9c5f9a0244cfe8d8493`
* Result-summary SHA-256: `41d47e1df8a8eb9ecd9a3d5cfbc79e75a4fdf0d0512895a1ec96834b7025222e`
* Candidate executions: **192**. Model/inference calls: **0**.

**AIQ1-QUALIFIED. Testing stopped.**

## 6. Historical interpretation and authority boundary

**BA3-SUPPORTED-WITH-QUALIFICATION**

The concept of determining tag-priority direction from controlled tied-score comparisons survives. Historical BA-3 nevertheless used answer-signalling names and same-process execution. Its source has not been repaired, and its historical results must retain those qualifications. AIQ-1 supports the measurement concept under the tested path, not a general endorsement of the original implementation.

**BA-4 preservation:** predictions, candidate pool, protocol, driver, and scored result are byte-identical to opening. The recorded index-0 CORRECT and index-2 REVERSED predictions and historical 12/12 determinations remain historical evidence. AIQ-1 did not execute those bodies or produce new labels for them. The optional remeasurement was deferred to honor the bounded stop rule; this is not a new prediction or an independent confirmation of those two outcomes.

**Detection does not grant repair authority.** A correct measurement of tag-priority direction does not show that Skill A's stored syntactic transformation preserves a particular implementation's semantics, applies safely to arbitrary morphology, or improves net utility. The next permitted research decision is a bounded jurisdiction qualification, not promotion or production activation.

**Smallest recommended next mission:** separately test Skill A's transformation on one previously established compatible implementation and the already documented harmful-applicability counterexample, with original and transformed behavior measured through the qualified isolated path. Freeze that jurisdiction question before execution; do not expand acquisition or redesign the predictor. No such test was run here.

## 7. Direct answers

1. **Did BA-3 use the claimed trusted sandbox?** No. Its actual candidate path was same-process `exec`.
2. **Can W/L naming alone explain a perfect historical case-family result?** Yes, analytically: lexical maximum selects W every time; minimum selects L. Historical exploitation is not established.
3. **Do tested lexical/positional shortcuts still pass with the answer channel removed?** No. Each splits evenly and abstains in both naming assignments.
4. **Can known correct and reversed implementations still be distinguished?** Yes: 24/24 versus 0/24 higher-priority selections, with opposite correct classifications.
5. **Does that work through actual isolation?** Yes, through the existing E0.1 sandboxed per-case child process, without modifying its implementation.
6. **Concept supported or evaluator-dependent artifact?** Supported for this finite deterministic domain: discrimination persists after both specified changes. Universal shortcut resistance is not established.
7. **What changes about BA-4's frozen predictions?** No artifact or prediction changes. The measurement concept gains bounded support; those two bodies have not yet been independently remeasured through it.
8. **Does property detection justify applying Skill A?** No. Transformation compatibility and safe jurisdiction require separate evidence.

## 8. Repository/runtime closure and exact new files

[Closing verification](aiq1_20260930/closing_integrity.json), 17:32:24 PDT: all protected hashes, HEAD and cached origin/main unchanged; staging empty. Echo, watchdog and Ollama retained their opening PIDs and start times. This mission did not restart, stop, signal, or submit work to Echo; did not call Ollama; and did not modify RiverBrain, live memory, production VSL, watchdogs, LaunchAgents, historical experiments, candidates or predictions. Live Echo continued its own operation; this is not a claim that every mutable file on the machine stayed static.

Created only this report and eight additive supporting files under `audits/aiq1_20260930/`: `qualification.py`, `baseline.json`, `protocol.json`, `protocol.sha256`, `raw_results.jsonl`, `results.json`, `closing_integrity.json`, and `processes.txt`. The existing E0.1 executor also created and removed its ordinary disposable per-case scratch directories. Nothing was staged, committed, pushed, reset or cleaned. No repair was implemented.

**Primary result: AIQ1-QUALIFIED**

**Decision gate: PROCEED TO BOUNDED JURISDICTION QUALIFICATION**
