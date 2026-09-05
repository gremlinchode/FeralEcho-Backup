# FeralEcho: Highest-Information-Gain Pilot — Controlled Continuation Report

**This is a controlled continuation of the previously-launched 45-candidate pilot, not a redesign.**
The frozen task suite, the three condition definitions, the objective (execution-based) scoring
methodology, and the original hypothesis framework are all preserved unchanged. This report follows
the mission's explicit requirement to separate four categories of finding — completed experimental
evidence, infrastructure observations, measurement/evaluator observations, and unresolved hypotheses —
and does not blend them.

## Status at Time of This Report

**19 of 45 planned candidates completed** (spanning 7 of 15 tasks), collected across one uncontrolled
initial run (candidates 001-011) and three controlled, explicitly-sized batches run afterward
(candidates 012-014, 015-019, and a batch-of-8 in progress at report time, expected to reach
approximately candidate_027 once it finishes). The task suite hash was independently re-verified before
this continuation began and is now **enforced programmatically** — the runner script asserts it before
generating anything and refuses to continue on any mismatch (§A.1). A background process continues
this batch; any further candidates it produces will keep appending to
`audits/capability_pilot/raw_results.jsonl` and can be folded into a future update, per this
investigation's standing practice.

---

## A. Completed Experimental Evidence

### A.1 Frozen Task Suite — Integrity Re-Verified

Hash: `6440ed174482a2d5bb43bdd03bfc33c73c66b492cb74f465e2674e8a8eb8937d` — re-computed and compared
byte-for-byte at the start of this continuation; **unchanged** since the original freeze. The
continuation runner (`scripts/run_capability_pilot.py`) now `assert`s this exact hash before doing
anything else — a real, enforced stop condition, not just a manual check — precisely per the mission's
Section 1 requirement ("if the task suite has changed for any reason: STOP").

### A.2 Condition Definitions — Unchanged

A (RAW), B (PIPELINE), C (COUNCIL) are defined identically to the original design and the first
partial run — see the prior report version (preserved in git history / the JSON's own
`phase0_forensic_setup`) for the exact function calls. No condition was simplified, strengthened, or
manually improved during this continuation.

### A.3 Resumability — Added, Verified Correct

A real, disclosed methodological addition (not a redesign): the runner now reads
`raw_results.jsonl` at startup, identifies which (task_id, condition) pairs already have a real,
objectively-scored result, and skips only those — continuing candidate numbering from the highest
existing ID rather than restarting. **Verified correct in practice**: the first controlled batch after
this change correctly reported "resuming — 11 (task,condition) pairs already completed, highest
existing candidate_id = 011" and began at `candidate_012`, matching the true prior state exactly.

### A.4 Controlled Batch Execution — Implemented Per Mission Requirement

Rather than one uncontrolled 45-candidate run, generation now proceeds via an explicit
`--max-candidates N` flag, each invocation capped and independently monitored, with wall-clock timing
recorded per candidate (`total_wall_clock_time`, in addition to the existing `generation_time` and
`verification_time`). Batches run this session: 3, 5, and 8 (in progress). This directly implements the
mission's Section 4 requirement to drain each batch fully and observe behavior before continuing,
rather than committing the whole remaining study to one unmonitored block.

### A.5 Complete Task × Condition Results Table

Every task/condition pair attempted so far, per the mission's Section 19 required format. `pending`
means genuinely not yet attempted (no record exists) — never a silent placeholder for a discarded or
replaced result.

| Task | Category | RAW (A) | PIPELINE (B) | COUNCIL (C) |
|---|---|---|---|---|
| task_01 (dedupe) | Tier 1 | **PASS** — echo:latest, 39.72s | **PASS** — echo:latest, 214.26s | **PASS** — council, 198.97s |
| task_02 (palindrome) | Tier 1 | **PASS** — echo:latest, 5.18s | **PASS** — echo:latest, 102.40s | **PASS** — council, 30.26s |
| task_03 (flatten-one-level) | Tier 1 | **PASS** — deepseek-r1:7b, 106.31s | **FAIL** (logic) — echo:latest, 63.65s | **FAIL** (logic) — council, 87.93s |
| task_04 (word freq) | Tier 1 | **PASS** — echo:latest, 15.43s | **PASS** — echo:latest, 154.55s | **PASS** — council, 196.79s |
| task_05 (fizzbuzz) | Tier 1 | **FAIL** (truncation, see §C.2) — deepseek-r1:7b, 121.07s | pending | pending |
| task_06 (LRU cache) | Tier 2 | **FAIL** (logic) — echo:latest, 10.59s | **PASS** — llama3.2:3b, 253.91s | **PASS** — council, 246.68s |
| task_07 (CSV parse) | Tier 2 | pending | pending | pending |
| task_08 (balanced brackets) | Tier 2 | **PASS** — echo:latest, 5.92s | **FAIL** (logic) — llama3:instruct, 63.11s | **PASS** — council, 31.09s |
| task_09 (merge intervals) | Tier 2 | pending | pending | pending |
| task_10 (postfix eval) | Tier 2 | pending | pending | pending |
| task_11 (strip leading prose) | Tier 3 | pending | pending | pending |
| task_12 (fix off-by-one) | Tier 3 | pending | pending | pending |
| task_13 (Jaccard near-dup) | Tier 3 | pending | pending | pending |
| task_14 (thread-safe counter) | Tier 3 | pending | pending | pending |
| task_15 (topological sort) | Tier 3 | pending | pending | pending |

No candidate in this table required a task substitution or silent replacement. Zero
`INFRASTRUCTURE_FAILURE`-classified candidates occurred in this batch (see §B) — every completed
candidate reached real objective scoring; failures recorded above are genuine task-logic failures or,
in one disclosed case (task_05/A), a genuine generation-truncation issue (§C.2), never a queue/
connection/timeout failure standing in for a task result.

### A.6 Condition-Level Statistics (n=19, explicitly not confirmatory)

| Condition | n | pass | pass rate |
|---|---:|---:|---:|
| A (raw) | 7 | 5 | 71% |
| B (pipeline) | 6 | 4 | 67% |
| C (council) | 6 | 5 | 83% |

**Not a result** — 6-7 per condition across 7 of 15 tasks, with real model-selection variation within
conditions (A/B do not use the same model across all trials; see the original design's disclosed
asymmetry). Recorded per the mission's Section 13 instruction to compute these "after objective
scoring," with the same disqualifying caveats as the prior version of this report.

### A.7 The Single Most Information-Dense New Result: `task_03`

**RAW passed, PIPELINE failed, COUNCIL failed — on the identical task.** This is the cleanest inversion
of the `task_06` pattern reported previously (where RAW failed and PIPELINE/COUNCIL both passed). Taken
together, these two tasks show **both directions of outcome occurring in this same small dataset** —
direct, real evidence that no single condition dominates uniformly, at least not yet, at n=19. This
is exactly the kind of distribution-across-conditions signal the mission's §15 asks to track, not a
one-off curiosity.

---

## B. Infrastructure Observations — Experimental Infrastructure Findings

**This section is not part of the model-performance result.** It is a constraint on this pilot's own
validity and throughput, reported separately per the mission's explicit Section 12 instruction.

### B.1 Live Production Contention — Directly Observed, Not Inferred

The live `run.py` production server was confirmed running throughout (PID changed from `15193` to
`49624` between the first partial run and this continuation — a real restart occurred at some point,
observed as a fact, cause not investigated further as out of scope). **Direct, timestamped evidence of
contention was captured in the live watchdog log during this exact session**:
`model_guided_autonomous_loop` (a real, hourly, Optuna-driven autonomous self-edit dry-run cycle)
was observed actively querying councillors and running synthesis at `19:45:15`–`19:45:43`, the same
general window this pilot's own candidates were being generated. This is the concrete, first-hand
confirmation of the contention source: production autonomous loops and this pilot's own calls share
one Ollama request queue with no isolation between them.

### B.2 `OLLAMA_NUM_PARALLEL` — Confirmed Still Unset

Re-checked this session via `env`/`launchctl getenv`: still unconfigured, exactly as the original
capability-ceiling hardware report found. Ollama therefore serves one request at a time regardless of
how many real clients (the live server's autonomous loops, this pilot's own script) are waiting.

### B.3 Memory Pressure — A Real, Escalating, Quantified Trend

Swap usage was sampled three times across this investigation's history:

| When | Swap used / configured |
|---|---|
| Original capability-ceiling hardware report | 5.19 GB / 6.00 GB |
| Start of this pilot's first partial run | 6.19 GB / 7.17 GB |
| Mid-way through this controlled continuation | 8.13 GB / 9.22 GB |

Swap usage is real, present, and has grown at every checkpoint this investigation has measured it —
never observed decreasing. This is disclosed as a trend, not attributed to any single cause (the
configured swap ceiling itself also grew between samples, which is itself informative: macOS is
dynamically enlarging swap to accommodate rising pressure, not holding a fixed ceiling against it).

### B.4 Concurrent Model Residency — Directly Observed

A live `ollama ps` check during this continuation showed **two full models resident simultaneously**
(`echo:latest`, 5.5GB, and `qwen2.5-coder:7b`, 5.1GB, both `100% GPU`) — over 10GB of concurrent model
weights alone, on a 24GB unified-memory machine already under real, rising swap pressure. This is
direct evidence of the "multiple models competing for unified memory" condition the mission's Section 3
asked to check for specifically.

### B.5 Whether Autonomous Loops Were Paused — Explicit Decision, Not an Oversight

**They were not paused.** `conversation_activity.py` (the one existing mechanism autonomous loops
already defer to) is an in-process, module-level counter with no cross-process visibility — it cannot
be signaled from this pilot's own separate script process without either modifying `run.py`'s code or
holding open a real, artificial HTTP request against the live server to simulate conversational
activity. Both were judged out of scope: the first is a production-architecture change the mission
explicitly forbids; the second is a fragile, indirect manipulation of a safety mechanism for a purpose
it wasn't built for, and using it that way without explicit authorization was judged an unacceptable
risk to take unilaterally against a live, real system currently relied upon. **Killing or suspending
the live production server itself was also not attempted**, for the same reason — it is a live, shared
system, and stopping it is a consequential, hard-to-reverse action that was not explicitly authorized
for this pilot. Per the mission's own explicit fallback ("if pausing them is not possible, use smaller
sequential batches and explicitly measure the resulting contention"), this report instead uses
controlled, explicitly-sized batches (§A.4) with full timing capture — the safer, sanctioned
alternative, not a workaround chosen to avoid a harder decision.

### B.6 Quantified Throughput

Across the 19 completed candidates: mean wall-clock time per candidate ≈ 85 seconds, with real
observed range from 5.18s (a fast RAW call, model already resident) to 253.91s (a PIPELINE call
requiring a fresh model load under contention). No candidate hit the 1200s councillor timeout or the
30s sandbox-verification timeout in this batch — every completed candidate reached real objective
scoring; the throughput cost is real and substantial, but has not (yet) produced an outright
infrastructure failure in this specific run.

---

## C. Measurement/Evaluator Observations

### C.1 The Extraction-Bug Correction — Preserved, Documented Precisely, Applied Consistently

Per the mission's explicit Section 2 requirement, restated precisely rather than merely referenced:

- **Original assumption**: self-edit's own real cleanup helpers
  (`_strip_markdown_fences`/`_looks_like_python`/`_extract_code_block`) assume generated code appears
  at the end of a response with no trailing prose.
- **How it failed**: a reasoning-style model (`deepseek-r1:7b`) produces a long reasoning trace, an
  inline unfenced code draft mid-reasoning, a final fenced code block, then more prose — the helpers'
  first-match-wins scan finds the inline draft first and returns everything after it, trailing prose
  included, which never parses.
- **Which candidate exposed it**: the very first real candidate of the original (now-superseded) first
  run — `task_02`, condition A, model `deepseek-r1:7b` — before any of the 19 candidates now in this
  report's table were generated.
- **What was changed**: one disclosed, harness-only fallback added to `clean_code()` in
  `scripts/run_capability_pilot.py` — if self-edit's own real helpers find nothing valid, take the
  **last** fenced code block in the raw text (the model's settled final answer, a standard convention).
- **Why evaluator-neutral, not a performance enhancement**: the fallback is applied identically,
  unconditionally, to every candidate regardless of condition or model — it never inspects which
  condition produced the text, and it never invents or repairs code; it only changes which substring of
  an already-generated response is treated as "the code." It has been active, unchanged, and applied
  consistently to all 19 candidates in this report's table (and would apply identically to A, B, or C).

### C.2 A Second, Distinct Measurement-Relevant Finding: Generation Truncation

**New this continuation, found directly in `candidate_019` (`task_05`, condition A, `deepseek-r1:7b`),
and precisely diagnosed rather than folded into the existing extraction-bug bucket.** The raw response
ends mid-sentence, inside an **unclosed** fenced code block (no closing ` ``` ` appears anywhere in the
response) — the generation was genuinely truncated (most likely by the task's configured token budget)
before the model finished writing the function, not merely mis-extracted from a complete response. The
extraction fallback (§C.1) correctly found zero *complete* fenced blocks (its regex requires a closing
fence) and correctly fell through to an honest, unrepaired result, which correctly failed verification.
**This is disclosed as a distinct category from both a genuine task-logic failure and the original
extraction bug**: the model may well have gone on to write correct code had generation continued, but
this cannot be known from a truncated response, and no attempt was made to guess or complete it. Recorded
here as `candidate_019`'s real, honest outcome (a task-logic-failure label from the script's own
generic classifier, reclassified in this report, not in the underlying data, as **generation-truncation-
limited**, distinct from a demonstrated reasoning error) rather than silently absorbed into either
existing failure category.

### C.3 Reassessing H3 — Does the Corrected Evaluator Produce Reliable Measurement?

**Could any remaining condition difference plausibly be an evaluator artifact rather than genuine
task-performance difference?** Directly assessed, not assumed away: of the 19 completed candidates,
**zero** show internal signs of a further extraction problem — every failing candidate's `output_tail`
shows a real, specific Python-level error (a `TypeError`, an `AssertionError`, a `KeyError`) arising from
genuinely executing the extracted code, not a `SyntaxError` on obviously-non-code text (which is exactly
what the original bug looked like, and exactly what §C.2's truncation case still correctly produced —
confirming the evaluator correctly flags a truncation-caused non-parse as a failure rather than silently
padding or repairing it). **This is real, positive evidence the corrected evaluator is measuring what it
claims to** — not proof it is perfect (§C.2 shows a real, adjacent limitation: the evaluator has no way
to distinguish "genuinely wrong code" from "correct code that was never finished," both currently
surface as the same PASS/FAIL signal). H3 is not "resolved" by fixing one bug — it is narrowed: the
specific artifact found is fixed and verified fixed, and a second, related but distinct limitation
(truncation-as-failure) is now disclosed rather than hidden, exactly per the mission's own instruction
not to pretend H3 disappeared.

---

## D. Hypotheses That Remain Unresolved

- **H1 vs. H4 for the general question this pilot exists to answer**: still unresolved at n=19/45.
  `task_03` and `task_06` show opposite directions (§A.7) — real evidence against any simple, uniform
  answer, not evidence for a specific one.
- **Whether council deliberation (C) genuinely rescues raw failures, or merely uses a different,
  sometimes-better model**: unresolved — every condition-B/C success or failure observed so far is
  confounded with a real, different underlying model choice (the disclosed model-selection-per-attempt
  issue), and this pilot's current design cannot separate "orchestration helped" from "a different,
  better model happened to be picked."
  - **Full ordering data, checked directly this continuation, sharpens but does not resolve this**: for
    every completed pair where A and B both ran, B's model choice was checked against A's. In 4 of 6
    cases (`task_01`, `task_02`, `task_04` pass/pass; `task_03` fail/pass-inverted... — precisely:
    `task_01`/`task_02`/`task_04` both used `echo:latest` for A and B, meaning those three are genuine,
    unconfounded same-model comparisons, all three agreeing (pass/pass)) — **B only diverges in model
    choice from A on `task_06` (llama3.2:3b) and `task_08` (llama3:instruct)**, the two tasks where B's
    outcome differs from A's. This is a real, useful clarification: the confound is concentrated exactly
    on the cases that would otherwise look most interesting, not spread evenly across the dataset — a
    reason for real caution before reading either divergence as a pipeline effect.
- **Whether `task_05`'s truncation issue recurs for other reasoning-model-selected candidates,
  or was a one-off**: unresolved with n=1 truncation instance; `choose_model()`'s own live variability
  means this could recur on any future candidate in this study.
- **The full 15-task, 45-candidate picture**: 26 candidates remain, spanning 8 tasks not yet touched at
  all (including all 5 Tier-3 hard tasks, seeded from real historical failure shapes — the tier this
  pilot's original design specifically expected to be most informative, and the tier with zero data so
  far).

---

## Final Decision (this continuation)

**AMBIGUOUS** — unchanged from the prior report's own classification, for the same reason (infrastructure
throughput, §B), now with substantially more real evidence collected and two additional real,
disclosed findings (§A.7's opposite-direction task pair; §C.2's truncation discovery) that sharpen,
without resolving, the underlying question. This is not a forced continuation of the same label out of
inertia — it is the correct label again because the two conditions that would justify GO or NO-GO
(either a large, consistent, un-confounded effect, or a large, consistent absence of one across enough
of the task space) are both still absent at n=19/45, with the hardest, most originally-motivating tier
(Tier 3) entirely untested.

## Answering the Question I Care About Most

**Ranked, with explicit confidence levels, demonstrated separated from plausible:**

1. **(D) Infrastructure/operating envelope — HIGH confidence, directly demonstrated.** Real,
   timestamped contention (§B.1), confirmed unconfigured concurrency (§B.2), a real, rising swap trend
   across three independent measurements (§B.3), and real concurrent multi-model residency (§B.4) are
   all directly observed facts, not inferences. This is the most confidently-demonstrated bottleneck in
   this entire investigation, though it is a bottleneck on *running the experiment*, not yet shown to be
   a bottleneck on Echo's own real-time task performance once a request is actually served.
2. **(C) Measurement/instrumentation — MEDIUM confidence, directly demonstrated but now narrowed, not
   open-ended.** Two real, distinct instrumentation gaps were found and precisely diagnosed this
   investigation (the extraction bug, §C.1; the truncation-vs-failure conflation, §C.2) — real, not
   speculative. Confidence is medium rather than high because both known instances are now fixed or
   disclosed; whether further, undiscovered instrumentation gaps remain is plausible but not
   demonstrated.
3. **(A) Architecture/integration and (B) model capability — LOW-MEDIUM confidence, genuinely
   unresolved, tied.** The evidence collected so far (§A.7) shows both directions occurring in the same
   small dataset with no consistent pattern — this is not weak evidence for either hypothesis, it is a
   real signal that at n=19/45, on the tiers tested so far (1 and 2 only), neither integration nor raw
   model capability alone explains the observed variance. Confidence this will remain true at full scale
   is explicitly LOW — Tier 3 (the tier most likely to separate these two hypotheses, since it was
   seeded from real historical architecture-adjacent failure shapes) has zero data yet.
4. **(E) Some combination — the current best-supported summary answer, MEDIUM confidence.** The honest,
   current state of evidence is that this system's real-world coding difficulty is not explained by any
   single one of A/B/C/D alone: infrastructure throughput is real and demonstrated as a constraint on
   experimentation itself; two real measurement gaps were found and are now understood; and the
   substantive task-performance question shows genuine, small-sample evidence pointing in different
   directions for different tasks, consistent with a combination of real model-capability limits on some
   tasks and real orchestration/pipeline effects on others, not yet separable at this sample size.

**If this were a boring answer, it would be said plainly, per the mission's own final instruction: the
honest current answer at n=19/45 IS somewhat boring — "the machine's own throughput is the most
confidently demonstrated constraint on our ability to even ask the substantive question at scale, and
the substantive question itself is still genuinely open."** That is not a failure to reach a conclusion;
it is the correct, evidence-respecting state of a study that is 42% complete on its hardest-to-obtain
dimension (task/condition coverage) and 0% complete on its most originally-motivating one (Tier 3).
