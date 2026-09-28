# AP-0 Stage 0 — Pre-registration v1 (frozen by hash before the first model call)

**Protocol:** AP-0, *Convention Accumulation Probe*, Stage 0 only (instrument and carrier-consumption gate).
**Authorization:** Richie, 2026-09-21: harness construction + pre-registration + Stage 0 only. Stage 1 (acquisition) and Stage 2 are **not** authorized and are **not** run. Frozen persistent-competence protocol v1.1 is untouched.
**Question Stage 0 answers:** *Can this worker use this carrier?* It does **not** ask *can experience create a useful carrier?* (that is Stage 1).
**Versioning rule:** this document's SHA-256 is recorded in `memory/experiments/accumulation_probe/stage0/FREEZE.json` (with git HEAD, working-tree state, server PID/start, exact model name and digest, and the hash of every harness file and frozen artifact) before any generation. Any later change to a threshold, rule or arm creates a NEW version (`_v2`, …) with its own hash; v1 is preserved unmodified. Changes are permitted only before Stage 1 data exists.

## 1. Worker and generation settings (frozen)
- Worker: `qwen2.5-coder:7b` via the local Ollama HTTP API `/api/chat` (direct request; no FeralEcho routing, council, RiverBrain, memory, or logging). The exact digest is read from Ollama and recorded in FREEZE.json; the run refuses to start if it differs, and re-checks it at the end.
- Options: temperature 0.2, top_p 1.0, repeat_penalty 1.0, num_predict 512, num_ctx 4096; one integer `seed` per call, derived as `sha256("AP0|20260921|<replicate>|<task_id>|<sample>")`, identical across arms for the same (replicate, task, sample) (matched seeds; a seed is a recorded input, not a determinism guarantee).
- 3 samples per (arm, task). Replicate A and replicate B use disjoint seed sets. No retries after a model response, no best-of, no repair, no critique.
- Sequential calls. Arms run in six interleaved shard-waves (every arm runs shard *k* before any arm runs shard *k+1*, arm order rotated) so load drift is spread across arms.

## 2. World and tasks (frozen at build; content sealed)
Three invented **local conventions**, each with a random realization the public task text does not reveal:
- **K1** status-code table: six invented codes → {open, closed, hold}.
- **K2** tag priority: four invented tags; ties on score resolved by the site's priority (then alphabetical name).
- **K3** event table: four invented event names, each an op {add, subtract, multiply, set} with a random constant.

Task set (28 tasks; each has 10 hidden cases chosen by greedy set-cover so that every single-step convention change is caught):
- **T** (12): same-shape tasks, 4 per convention (sum/count/ids/top for K1; winner/rank/loser/top-two for K2; final/trace/max/first-over for K3).
- **S** (6): structurally changed tasks (tuples, `id:status:amount;…` log parsing; dict entries, per-round winners; CSV events, batched events), 2 per convention.
- **NEAR** (6): near-match negative controls. The task states an *explicit conflicting* convention (the MISMATCH realization); the correct answer follows the task text, not the carrier.
- **UNREL** (4): convention-free tasks (sum evens, reverse words, flatten once, run-length encode).
Primary sets: **T ∪ S (18 tasks)**. Hidden test cases, reference solutions and world realizations live under `stage0/oracle/`, which no arm process can read (kernel jail, §5).

## 3. Arms (all preserved; none may be dropped or weakened after seeing results)
The **retained-carrier format** is a NOTES block in the system message: `[RETAINED NOTES …]` with numbered notes, each an `applies when:` line plus either a `procedure:` (stated convention) or `observed episodes (call -> result):`; the task text states it always takes priority over notes. Exact template: `prompts.py` (hash in FREEZE.json).

| Arm | Content | Tasks |
|---|---|---|
| **N** | no carrier, no examples | T,S,NEAR,UNREL |
| **N2** | N, second replicate (disjoint seeds) | T,S |
| **NEUTRAL** | same format and *exact* character length, a note about a *foreign* convention of the same kind (unrelated tokens) | T,S,NEAR, UNREL (K1 foreign) |
| **MISMATCH** | same tokens, systematically different content (every K1 code remapped; K2 priority reversed; K3 ops rotated), same length | T,S |
| **H** | hand-written **correct** procedure in the carrier format | T,S,NEAR; UNREL with each of the three carriers |
| **H2** | H, second replicate | T,S |
| **E** | raw teaching episodes (deterministic environment observations) in the carrier format, no stated procedure | T,S |
| **IC** | in-context reference: the same episodes inline in the user prompt, no carrier | T,S |
| **FAILED-DRAFT** | a constructor draft that failed independent validation, used as carrier | **Deferred to Stage 1 by construction:** it requires acquisition (constructor drafts), which Stage 0 does not run. It remains a pre-registered Stage 1 arm and is not removed. |

Calls: N 88, N2 54, NEUTRAL 84, MISMATCH 54, H 112, H2 54, E 54, IC 54 = **554** (includes 8 determinism probes: identical request and seed repeated once for 4 tasks in N and H).

## 4. Scoring (frozen)
- Response → code: the last fenced block that defines the requested function; else the last fenced block; else raw text containing `def`. Identical for all arms.
- Grade: candidate + hidden tests run under the kernel sandbox (`sandbox/echo_sandbox.sb`, `safe_exec_wrapper.py`, same invocation as FeralEcho's own F2 path but without importing it). **Pass** iff the sandbox completed and printed a per-grade random nonce line that the candidate cannot know. Candidate infinite loops/timeouts (20 s) are failures; harness-side sandbox errors are flagged `infra`, retried twice, and counted in the infra rate.
- Every response is graded twice with fresh nonces (runtime score and independent re-grade); their agreement is reported. The grader also re-derives every prompt from the frozen plan and compares its hash with the stored request hash, and re-scans every sent request for hidden-test literals and arm-content violations. Each arm ledger is a hash chain.

## 5. Instrument qualification (completed before any model call; results in FREEZE.json's artifact hashes)
Independent second implementation of every task (different algorithms) agrees with the reference on all hidden cases and 300 random inputs per task; every single-step convention mutant and generic wrong solution (318 in total) is killed **through the real sandbox**; reference solutions pass 3/3; a nonce-guessing spoof never passes; teaching episodes uniquely identify each convention (brute-force hypothesis enumeration); teaching inputs are disjoint from all hidden inputs; hidden-test literals appear in no prompt of any arm; NEUTRAL/MISMATCH blocks are length-matched to H (ratio 1.0); the harness imports no production module (static AST audit + dynamic `sys.modules` audit in a fresh interpreter; it deliberately does not import `sandbox.run_script`, `scripts/run_capability_pilot.py` or `self_edit_manager`); each arm runs in its own kernel jail (read/write only its own root; cannot read the oracle or any sibling root; cannot write elsewhere; only Ollama on localhost is reachable) and this is probed per arm; the arm entry point loads only `common`, `prompts`, `ollama_client`. `scripts/verify_accumulation_probe.py` exercises all of this, plus adversarial checks and an end-to-end run against a mock server (45 checks).

## 6. Measurements reported (minimum)
Pass rates for H, N, NEUTRAL, MISMATCH, E, IC (and N2, H2) on T∪S, with cluster-bootstrap (over tasks, 10,000 resamples) 95% intervals for the contrasts H−N, H−NEUTRAL, H−MISMATCH, IC−N, E−N, H−IC, H−E, NEUTRAL−N, MISMATCH−N; per-convention and per-template rates; headroom H−N (and H−NEUTRAL); seed variance (fraction of tasks with mixed pass/fail across seeds; fraction with differing responses across seeds; within-task SD); task-family variance; noise floor (N vs N2, H vs H2); determinism probes; negative-control behaviour (NEAR, UNREL); oracle agreement (independent implementations, mutation kill, spoof, runtime vs re-grade); truncation, no-code, timeout and infra rates; contamination checks on the actually-sent requests; per-call latency.

## 7. Decision rules (frozen constants; the code states the same values)
```
HEADROOM_MIN = 0.3
HEADROOM_LOWER_MIN = 0.15
PER_CONV_HEADROOM = 0.3
N_CEILING = 0.4
NOISE_MAX = 0.1
MISMATCH_GAP_MIN = 0.2
REGRADE_AGREE_MIN = 0.99
INFRA_MAX = 0.02
TRUNC_MAX = 0.05
BOOT_N = 10000
```
Stage 0 is **INFORMATIVE** iff **all** gates hold:
- **G1 headroom:** H−N and H−NEUTRAL (pooled T∪S) each ≥ HEADROOM_MIN, and each one-sided 95% bootstrap lower bound ≥ HEADROOM_LOWER_MIN.
- **G2:** H−N ≥ PER_CONV_HEADROOM in at least 2 of 3 conventions.
- **G3:** N pooled pass rate ≤ N_CEILING (headroom exists; not model-native).
- **G4 noise floor:** |N − N2| and |H − H2| pooled rates ≤ NOISE_MAX.
- **G5 content conditioning:** H−MISMATCH ≥ MISMATCH_GAP_MIN (outputs follow the carrier's content, not merely its presence).
- **G6 instrument integrity:** zero independent-implementation disagreements, zero surviving mutants, zero spoof passes, runtime/re-grade agreement ≥ REGRADE_AGREE_MIN, infra rate ≤ INFRA_MAX, truncation rate ≤ TRUNC_MAX, all planned calls completed, no request-check violation.

Otherwise **UNINFORMATIVE**, and Stage 0 **stops**. An UNINFORMATIVE result is an instrument/consumption outcome and **must not** be reinterpreted as evidence against learning. If G1 fails, a non-gating diagnostic records whether inline information works (IC−N ≥ 0.30 → “format-consumption suspected”) or not (“worker/task/instrument”).
**Answer to “can this worker use this carrier?”** = YES iff G1 and G5 hold; otherwise NOT ESTABLISHED.

## 8. Threshold review before Stage 1 (only if INFORMATIVE)
Stage 0 reports, from measured variability, whether the provisional Stage 1 thresholds remain defensible: transfer gain +25 points (minimum detectable effect at 80% power, α=0.05 one-sided, 18 pooled tasks, using the task-level SD of H−N), headroom +30 (margin over threshold), and the ±10-point negative-control/equivalence band (whether the NEAR and UNREL task counts can resolve a ±10-point band given replicate noise). Any adjustment is made **only** in a new hashed preregistration version, before Stage 1 data exists; v1 is retained. Stage 1 sealed tasks are not materialized now; their seed will be derived from the hash of the Stage 0 evidence.

## 9. Disclosed limitations (stated before results)
One worker (`qwen2.5-coder:7b`); one realization per convention; conventions are invented and small (a positive result does not generalize to real competence); temperature 0.2 with 3 seeds (a low-variance regime; effective sample size may be closer to the 18 tasks than to 54 samples per arm); H states the convention explicitly, so H is an upper bound on what a *learned* carrier can achieve, not a measure of learning; E requires induction from episodes and may legitimately lag H; IC is not a carrier and is a reference only; the live FeralEcho server shares the Ollama queue (latency may vary; outcomes should not); Stage 0 makes **no** claim about acquisition, retention across days, accumulation, or the FeralEcho system’s learning. No Stage 1 or acquisition data will be generated.

## 10. Stop rule
After Stage 0 the results are returned to Richie. **No Stage 1 or Stage 2 action follows without new explicit authorization.**
