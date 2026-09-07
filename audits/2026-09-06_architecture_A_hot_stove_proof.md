# Architecture A Minimal Hot-Stove Learning Proof

Executed as a real, isolated experiment (`app/experiments/architecture_a_hot_stove_proof/`),
not a design pass. `run.py`/watchdog confirmed stopped throughout; port 5000 unbound;
`river_brain.pkl` sha256 unchanged (`eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815`);
`memory/interaction_log.jsonl` unchanged (13,324 lines before and after); git HEAD unchanged
(`2cf2d95009943797db5ec41fea9b4021634fd5e6`); zero production files modified; zero
self-edit deployment attempted. Full detail in §2.

---

## 1. Executive Verdict

# **HOT-STOVE NOT PROVEN**

A real candidate-knowledge record was created, correctly persisted, correctly retrieved by
exact-signature match, and correctly injected into a later, independently-generated retry's
prompt — every mechanical link Architecture A proposed to build actually worked as designed.
**And it produced no measurable behavioral difference.** CONTROL (no injected attribution) and
EXPERIENCE (with injected attribution) succeeded at an identical rate — 5/6 (83.3%) each — on a
real, matched-pair, adversarially-controlled trial using the real F2 kernel sandbox as the
evaluator. The two conditions' failures were not even the same failure: CONTROL's one failure
was an unrelated `NameError: name 'Dict' is not defined`; EXPERIENCE's one failure was the
model regenerating the *exact same* `functools` NameError **despite having just been told,
verbatim, in its own prompt, that this exact error was the confirmed cause of a prior failure**.

This is a real, precise, adversarially-checked instance of **failure classification: DECISION-
INFLUENCE FAILURE** (§17), with one important, disclosed nuance that changes what this result
actually means for Architecture B (§18, §19): the chosen decision point (retry-prompt
construction) turned out to have very little headroom to show an effect on this failure class,
because the *production* retry mechanism — with zero Architecture A machinery, using only the
raw sandbox traceback text it already includes — already succeeds ~83% of the time on its own.
There was almost nowhere for an injected attribution to move the needle, on this specific
decision point, for this specific failure class.

---

## 2. Safety Invariants

| Check | Before | After |
|---|---|---|
| `run.py` process | Not running | Not running |
| watchdog (`start_echo.sh`) process | Not running | Not running |
| Port 5000 | Unbound | Unbound |
| Ollama | Directly reachable | Directly reachable (used throughout) |
| Git HEAD | `2cf2d95009943797db5ec41fea9b4021634fd5e6` | Unchanged |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` | Unchanged (verified live, both by harness self-check and independently here) |
| `memory/interaction_log.jsonl` line count | 13,324 | 13,324 (unchanged) |
| Production files modified | 0 | 0 |
| RiverBrain learning events (`.learn`/`.learn_from_sandbox_outcome`/`.save`/`._do_save`) | Class-level patched to no-ops before any instance construction, verified live by round-tripping a real canary call and re-hashing `river_brain.pkl` | Confirmed no-op — canary call made, hash unchanged |
| `log_interaction()` production write | Patched to no-op at module level in `app.core.echo_model_orchestrator` before any `echo_query()` call | Confirmed — canary call made, line count unchanged |
| Self-edit deployment | Never called `execute_self_edit()`/`perform_self_edit()` — only the individual, already-real, side-effect-free helper functions they compose from (`test_code_in_sandbox`, `_sanitize_sandbox_error`, `choose_model`, `echo_query`) | Same |
| Real garden / self-edit state files (`data/question_garden.jsonl`, `memory/self_edit_cooldown.json`, `app/core/self_edit_convergence.json`, `memory/SELF_EDIT.log`) | Untouched | Untouched — confirmed by `git status --porcelain` showing zero modifications to any of these paths |
| New files created | — | `app/experiments/architecture_a_hot_stove_proof/` (harness, driver, results, this report's source data); `sandbox/scripts/hotstove_proof_*.py` (20 files) — the real F2 sandbox's own pre-existing, designated scratch/archive directory, not production memory; script names prefixed `hotstove_proof_` to stay visually distinguishable from real self-edit history in that same directory |

Verification method: `app/experiments/architecture_a_hot_stove_proof/harness.py`'s
`verify_neutralization()` makes one real canary call to each neutralized method/function and
re-hashes/re-counts the real production files immediately after, both at harness start and
harness end — not assumed safe from the patch code alone. Both runs are recorded verbatim in
`run_report.json`'s `safety_neutralization_check` / `safety_neutralization_check_after` keys.

---

## 3. Fresh Failure-Signature Selection

Mined directly from the real, live `memory/SELF_EDIT.log` (142,839+ real lines) via a full-file
regex scan for `NameError: name 'X' is not defined` signatures, ranked by frequency:

| Signature | Real occurrences | First seen | Last seen | Disposition |
|---|---:|---|---|---|
| `log_call` | 604 | — | — | Largest signature overall — deliberately not chosen; a repo-wide grep shows this is likely a self-referential-import class of mistake (F1's own concern), a structurally different failure family than a missing stdlib import, out of scope for this proof |
| `self_edit_generated` | 130 | — | — | Same self-referential-import family — excluded for the same reason |
| `re` | 82 | 2025-11-26 | 2026-08-29 | **Excluded per mission §3** — the Hot Stove audit's own headline negative case; CLAUDE.md's Finding 32 (2026-07-15) already diagnosed and prompt-patched this exact signature. Contaminated for a fresh-signature test. |
| **`functools`** | **76** | **2026-07-15** | **2026-09-01** | **Selected.** See below. |
| `dataclass` | 52 | 2026-07-20 | 2026-09-04 | A real, viable alternative (same missing-import shape) — not chosen only because `functools` had a larger sample and a real historical exemplar (`@functools.lru_cache(...)`) directly matching the kind of task this experiment's mining prompts could reliably elicit |

**Why `functools` is judged uncontaminated, checked directly, not assumed:**
- `grep -n "functools" CLAUDE.md`: zero hits. No Finding anywhere in this project's 95-entry
  history names this signature.
- `grep -n "functools" app/core/self_edit_manager.py`: exactly one hit, line 713 — a generic
  `_ALLOWED_TOP_LEVEL` import-allowlist entry (`"collections", "itertools", "functools",
  "typing", "dataclasses", "ast", ...`), not a targeted prompt fix. No `_FOCUS_FAMILY_BY_CREATIVITY`
  domain sentence mentions it (verified by reading the full `re`-targeted `prose_stripping` sentence
  in context — `functools` does not appear anywhere near it, and `prose_stripping` itself is
  commented out / PAUSED as of 2026-07-19, per that section's own in-code comment).
- `grep -n "functools" app/core/self_edit_generated.py`: zero hits — the file is in its clean,
  honestly-inert reset baseline (confirmed by CLAUDE.md's own documented history of this file).
- `grep -rn "functools" audits/*.md` (excluding this report): exactly one hit — the Hot Stove
  audit's own summary table row, which explicitly states "not separately traced." No prior pass
  this session investigated or acted on this signature.
- Still genuinely recurring, not historical-only: last real occurrence 2026-09-01, five days
  before this experiment ran.

---

## 4. Existing Attribution Path (re-verified against current source, this pass)

`app/core/self_edit_manager.py:execute_self_edit()`, lines 1998-2050, re-read directly before
building anything on top of it (line numbers below match current source exactly, confirmed via
`grep -n`):

```text
success, sandbox_error = test_code_in_sandbox(code)              # line 1977 — REAL F2 sandbox
...
if not success:
    clean_error = _sanitize_sandbox_error(sandbox_error)          # line 1999 — REAL attribution
    retry_prompt = (                                              # lines 2002-2010
        f"{CODE_OUTPUT_RULES}\n\n"
        f"Your previous attempt failed with this error:\n"
        f"{clean_error}\n\n"
        f"IMPORTANT: Do NOT include module-level test calls. ...\n\n"
        f"Write corrected Python code for this plan:\n{plan}"
    )
    retry_model_name, _ = choose_model(retry_prompt, task_type="self_edit_coding")  # line 2014
    retry_code = echo_query(retry_prompt, task_type="coding", trace_id=trace_id)    # line 2015
    ...
    retry_success, retry_error = test_code_in_sandbox(retry_code, "temp_self_edit_retry.py")  # line 2027
```

`_sanitize_sandbox_error()` (lines 1427-1432): scans the raw traceback line-by-line for
`SyntaxError`/`RuntimeError`/`"Error:"` and returns the first matching line, stripped — for a
`NameError`, this reliably extracts exactly `"NameError: name 'X' is not defined. Did you
forget to import 'X'?"`, confirmed directly against real captured tracebacks this pass.

**What is discarded**: `clean_error` and `retry_prompt` are local variables inside
`execute_self_edit()`'s own call frame. Confirmed by direct source read (repeated from the Hot
Stove audit, independently re-confirmed here): no write of either to any file, log, or shared
structure exists anywhere in this function or any function it calls. `execute_self_edit()`
returns; the frame — and every specific fact it computed about *this exact failure* — is gone.

---

## 5. Architecture A Design (as built)

Exactly as specified in the mission and the Learning Gap Closure report — no additions:

- **Action identity**: reused `trace_id` (real `uuid.uuid4()`, minted the same way
  `execute_self_edit()` itself mints one at line 1887) — no new ID scheme.
- **Attribution**: the real, unmodified `clean_error` string produced by the real,
  unmodified `_sanitize_sandbox_error()` — never rewritten, improved, or paraphrased by this
  harness. Verified: the persisted `causal_hypothesis` field
  (`"NameError: name 'functools' is not defined. Did you forget to import 'functools'?"`) is
  byte-identical to what the real pipeline's own natural (uninjected) retry saw in its own
  prompt.
- **Decision point**: the real self-edit retry-prompt construction, reconstructed
  byte-for-byte from current source (`build_retry_prompt()` in the harness reproduces
  `execute_self_edit()`'s exact template, confirmed by direct comparison of the two strings),
  with exactly one additive paragraph for the EXPERIENCE condition.
- **Explicitly not built**: no significance scoring, no contradiction graph, no embeddings,
  no confidence decay, no general lesson database, no new vector store, no new autonomous loop.

---

## 6. Candidate Knowledge Record (as persisted)

Real record, `app/experiments/architecture_a_hot_stove_proof/candidate_knowledge.jsonl`:

```json
{
  "record_id": "b1015798-c2d5-4ff3-92ee-c33e7335ffd6",
  "created_ts": "2026-09-07T02:38:28Z",
  "source_mechanism": "self_edit_retry",
  "producing_trace_id": "b1015798-c2d5-4ff3-92ee-c33e7335ffd6",
  "consequence_signature": "NameError:functools",
  "causal_hypothesis": "NameError: name 'functools' is not defined. Did you forget to import 'functools'?",
  "confidence": 0.5,
  "applicability_scope": "self_edit_coding:general",
  "status": "unresolved",
  "times_revisited": 0,
  "times_applied": 0,
  "application_outcomes": []
}
```

Matches the Learning Gap Closure report's schema exactly (§Candidate Knowledge Model of that
report) — the minimum sufficient representation, not the maximal one; no field added beyond
what was already justified there.

---

## 7. Experiment Design

**Episode 1 — real, organic Failure A**: 6 fresh, uncontaminated mining prompts (memoization/
caching tasks, deliberately avoiding every historically-contaminated identifier named in the
mission — `log_call`, `CodeGenerator`, `get_shortened_code`, `generate_and_modify_code`,
`apply_list_comprehension`). Real `echo_query()` generation, real F2 sandbox evaluation, per
attempt. **5 real attempts run** (mining stopped as soon as the target signature was hit, per
the mission's own efficient-mining framing) — attempts 0/1/3 succeeded outright, attempt 2 hit
an unrelated `lru_cache(max_size=...)` `TypeError` (a different real bug, not the target
signature — kept for the record, not discarded), attempt 4 (model `llama3:instruct`) hit the
real, uncontaminated `functools` NameError.

**Episode 1 natural retry** (production-identical, zero Architecture A machinery): real,
succeeded (`retry_success: true`, model `echo:latest`). This is itself informative — see §14.

**Persistence**: the real `clean_error` from Episode 1's real sandbox output was persisted
verbatim, per §6.

**Episode 2 — genuinely separate matched candidate**: 3 fresh real attempts (different plan
wordings from Episode 1's, fresh identifiers), attempt 2 (model `echo:latest`) independently
produced the same `functools` NameError signature — a genuinely separate, independently-
generated failure, not a replay of Episode 1's candidate.

**Matched-pair CONTROL/EXPERIENCE replications**: **6 pairs, 12 real retries total**, all
sharing Episode 2's exact real `clean_error` and plan as the starting point (holding the
starting state bit-identical across both conditions, isolating the one intended variable —
presence/absence of the injected `causal_hypothesis` — as the mission's own §8 "everything else
should be equivalent" requirement demands). Order alternated (CONTROL-then-EXPERIENCE on even
reps, EXPERIENCE-then-CONTROL on odd reps) to guard against any systematic drift across real
Ollama session state. No `seed` parameter exists anywhere in this codebase's real Ollama request
construction (independently re-confirmed this session, multiple times) — each of the 12 retries
is therefore a genuinely independent real sample, not a controlled-seed replay.

**Relevance matching, pre-registered before running** (mission §7): MATCHED if and only if the
later failure's `consequence_signature` (error class + missing symbol) is an exact string match
to the persisted record's — `"NameError:functools"` == `"NameError:functools"`. No fuzzy or
semantic matching used, per the Learning Gap Closure report's own explicit recommendation
(embedding-based relevance already shown, in this session's memory-ablation experiment, to
produce an effect indistinguishable from noise in this exact codebase). Episode 2's failure:
**MATCHED**, exact signature identity, confirmed directly.

**Evaluation**: the real, unmodified `test_code_in_sandbox()` — real `sandbox-exec` kernel
sandbox, real `SANDBOX_OK` / traceback outcome — for every one of the 12 retries. No self-
reported or LLM-claimed success was ever accepted as evidence.

---

## 8. CONTROL Result

| Rep | Model | Result | Failure (if any) |
|---|---|---|---|
| 0 | echo:latest | PASS | — |
| 1 | echo:latest | PASS | — |
| 2 | echo:latest | **FAIL** | `NameError: name 'Dict' is not defined. Did you mean: 'dict'?` — an **unrelated** typing-import bug, not the target `functools` signature |
| 3 | echo:latest | PASS | — |
| 4 | echo:latest | PASS | — |
| 5 | echo:latest | PASS | — |

**CONTROL: 5/6 (83.3%) real sandbox pass rate.**

---

## 9. EXPERIENCE Result

| Rep | Model | Result | Failure (if any) |
|---|---|---|---|
| 0 | echo:latest | PASS | — |
| 1 | echo:latest | PASS | — |
| 2 | echo:latest | PASS | — |
| 3 | gemma3:4b | PASS | — |
| 4 | echo:latest | **FAIL** | `NameError: name 'functools' is not defined. Did you forget to import 'functools'?` — **the exact target signature, recurring, despite the model having just been told verbatim that this precise error was the confirmed cause of a prior failure** |
| 5 | echo:latest | PASS | — |

**EXPERIENCE: 5/6 (83.3%) real sandbox pass rate — identical to CONTROL.**

Discordant pairs (mission's own established McNemar-paired standard, used throughout this
session's capability-ceiling research): exactly 2 — rep2 (CONTROL fails, EXPERIENCE passes) and
rep4 (CONTROL passes, EXPERIENCE fails). A 1-1 split on discordant pairs is definitionally the
weakest possible evidence a paired design can produce — exact McNemar p = 1.0. No directional
signal of any kind.

---

## 10. Counterfactual Result

Mission §11: "If the EXPERIENCE candidate succeeds, remove access to the retained attribution
while keeping everything else constant... would the same candidate have behaved this way
without the retained experience?" Given this codebase has no seed parameter anywhere (confirmed
repeatedly this session), a literal same-random-draw counterfactual is not obtainable — the
closest honest substitute, and the one this design used deliberately, is the matched-pair
structure itself: 6 independent CONTROL draws and 6 independent EXPERIENCE draws from the exact
same starting failure, compared in aggregate.

**Result: the counterfactual is negative.** CONTROL — with no access to the retained
attribution at all — succeeded at exactly the same rate as EXPERIENCE. The strongest single
piece of counterfactual evidence is rep4: EXPERIENCE, *with* the attribution explicitly present
in its prompt, still reproduced the exact error the attribution named. If retained knowledge
were doing real causal work at this decision point, this specific failure mode (recurrence of
the *exact* named error, immediately after being told its exact cause) should be the least
likely outcome, not an observed one.

---

## 11. Independent Evaluation

Every one of the 18 real generation attempts across this experiment (5 Episode-1 mining, 3
Episode-2 mining, 1 Episode-1 natural retry, 12 matched-pair retries — 21 total real `echo_query()`
calls) was evaluated exclusively by the real, unmodified `test_code_in_sandbox()` — real
kernel-level `sandbox-exec` execution, checking for the literal `SANDBOX_OK` marker in real
subprocess stdout. No model's own claim of success was ever substituted for this. All 21 raw
outcomes (success/failure, real traceback text where applicable) are recorded verbatim in
`app/experiments/architecture_a_hot_stove_proof/run_report.json` and
`trial_results.jsonl`, independently re-readable.

---

## 12. Contamination Analysis

Checked against every source named in mission §10.G:

- **Lexical memorization / identifier leakage**: Episode 1 and Episode 2 used entirely
  different plan prompts and function names (`triangular_number` vs. `expensive_lookup`) — no
  shared identifier between the attribution's origin and the trials it was tested against.
- **Historical artifact exposure**: none of the mining prompts or retry prompts reference
  `self_edit_generated.py`'s real content, `SELF_EDIT.log`, or any prior real self-edit cycle.
- **Prior fixes**: `functools` was independently confirmed (§3) to have zero prior CLAUDE.md
  Finding, zero targeted prompt patch, zero mention in `_FOCUS_FAMILY_BY_CREATIVITY` — this
  experiment did not accidentally re-test an already-patched lesson the way reusing `re` would
  have.
- **Deterministic generation / evaluator leakage**: ruled out mechanically — no seed parameter
  exists in this codebase's real Ollama calls (re-confirmed, not assumed, consistent with this
  session's Full-Pipeline Determinism and Direct Councillor Boundary Trace findings); the
  councillor/synthesis path for `echo:latest`-attributed responses is the real, sequential
  `deliberate_and_learn()` loop, not a bypassed shortcut.
- **Redundancy confound — the one genuine, disclosed limitation of this design**: the
  production retry prompt *already* includes the raw sandbox traceback, which for a `NameError`
  already reads `"...Did you forget to import 'X'?"` — Python's own error message is already a
  near-complete diagnosis. The EXPERIENCE condition's injected sentence
  (`"A similar failure occurred before under this exact error signature. The confirmed cause
  was: NameError: name 'functools' is not defined. Did you forget to import 'functools'?"`) is
  therefore substantially **redundant** with information CONTROL already receives, not a
  genuinely novel signal. This experiment cleanly tests "does restating an already-visible,
  already-explicit diagnosis a second time change retry behavior" more precisely than it tests
  "does information from a temporally-separate, otherwise-inaccessible prior experience change
  behavior" — and even under that weaker, easier-to-pass test, no effect was found. This is
  disclosed plainly rather than hidden, and it sharpens rather than weakens the negative result:
  if doubling down on an already-correct, already-visible diagnosis produces zero measurable
  change, a genuinely *novel* piece of retained information would face an even higher bar to
  show an effect at this same decision point.

**Bottom line: no plausible confound explains away the null result. If anything, the one real
confound found (redundancy) means the true test was easier to pass than intended, and it still
did not pass.**

---

## 13. Causal Interpretation

The mechanical chain Architecture A was built to prove — trace_id reuse, real unmodified
attribution, exact-match persistence, exact-match retrieval, prompt injection at an existing
decision point — **worked exactly as designed, every link, verified directly.** This rules out
the weakest, most common failure mode named throughout this whole investigation (§5's "lesson
dump" trap: the mechanism was never merely present-but-unused — it was genuinely retrieved and
genuinely injected into a real generation call, confirmed by inspecting the real 2,413-character
EXPERIENCE retry prompts against the real 2,237-character CONTROL retry prompts).

What failed is the very next link: **decision influence.** The model, given the correct,
specific, verbatim cause of its own immediately-preceding mistake, did not reliably act on it
any more than it would have without it.

**A second, unplanned, and arguably more important finding emerged from this same data**: the
*production* retry mechanism, using nothing but the raw sandbox traceback it already includes,
already succeeds ~83% of the time on this failure class (Episode 1's natural retry: succeeded;
CONTROL's aggregate: 5/6). This means the real, documented recurrence phenomenon this whole
investigation exists to explain (76 real `functools` failures across 2 months, 82 real `re`
failures across 9 months) **is not primarily a retry-repair problem** — the retry step, on its
own, already fixes this class of mistake most of the time it's given the chance to. The
recurrence must be happening somewhere upstream of the retry — most plausibly, at *initial*
candidate generation, in a *later*, *independent* self-edit cycle that never encounters this
particular retry at all, and regenerates the same mistake from scratch. This reframes what "the
decision point that needs the retained attribution" should be: not retry-prompt construction
(where headroom to show an effect is small because retries already mostly work), but *initial*
generation-prompt construction for later, unrelated cycles (where the real, measured 9-month
`re` recurrence and 2-month `functools` recurrence actually live).

---

## 14. Replication

Per mission §12: "If the first experiment fails, do not keep hammering until something passes.
Instead classify the failure." The first matched-pair experiment (n=6 per condition) produced a
clean, unambiguous null result with a real, disclosed methodological insight (§13) about *why*
this specific decision point had low headroom. Per the mission's own instruction, this
classification is more valuable than forcing a second, larger run at the same decision point in
the hope of a different result — a second replication at the same design would very plausibly
reproduce the same near-ceiling ~83%/83% pattern, since the underlying reason (retry-prompt
redundancy + retries already mostly succeeding) does not change with more samples. **No
replication attempted; the precise failure classification below is reported instead, per the
mission's own explicit preference.**

---

## 15. Learning-Loop Ledger (mission §16 required table)

| Stage | Evidence | Exists? | Durable? | Used later? | Verified effect? |
|---|---|---|---|---|---|
| Action | `trace_id` (`b1015798-c2d5-4ff3-92ee-c33e7335ffd6`) | Yes | Yes (reused as `producing_trace_id`) | Yes | N/A |
| Consequence | Real F2 sandbox result — `NameError: name 'functools' is not defined...` | Yes | Yes (persisted verbatim) | Yes | N/A |
| Attribution | Real pipeline hypothesis (`_sanitize_sandbox_error()`'s real output) | Yes | Yes | Yes | N/A |
| Retention | `candidate_knowledge.jsonl` record, real, on disk | Yes | Yes | Yes | N/A |
| Relevance | Exact `consequence_signature` match, Episode 2's independent failure | Yes | Yes | Yes — correctly matched | N/A |
| Retrieval | Injected into 6 real EXPERIENCE retry prompts, confirmed by prompt-length diff (2413 vs. 2237 chars) | Yes | Yes | Yes | N/A |
| Decision influence | 6 EXPERIENCE vs. 6 CONTROL real retries | Yes (attempted) | — | — | **No — 5/6 vs. 5/6, identical** |
| Outcome | Real F2 sandbox pass/fail, both conditions | Yes | — | — | **No measurable difference** |
| Verification | Real, independent kernel sandbox for every trial | Yes | — | — | Confirms the null, does not manufacture a positive |

Every "yes" above is backed by a specific file/line/data point cited in §§3-11. Every "no" is a
directly measured null, not an absence of investigation.

---

## 16. Exact Failure Boundary

Per mission §17: this is a **DECISION-INFLUENCE FAILURE** — the sharpest, most specific
classification available, not a vaguer "inconclusive." Every upstream link (attribution,
retention, relevance, retrieval) demonstrably worked. The chain breaks precisely at "does the
retrieved information change what the model does" — and does so specifically at this one
decision point (self-edit retry-prompt construction) for this one failure class (a
self-explanatory missing-import `NameError`), not necessarily everywhere. §13's redundancy
finding narrows this further: the failure may be partly an artifact of choosing a decision
point where the *baseline* already had little room to fail (retries already succeed ~83% of the
time on their own for this exact signature), rather than conclusive proof that injected
attribution *never* changes behavior at *any* decision point, for *any* failure class.

---

## 17. Recommendation for Architecture B

**Do not proceed to Architecture B as originally staged** (a second consumer — the
self-edit-family targeting nudge — gated on this proof succeeding). It did not succeed, and per
the Learning Gap Closure report's own explicit instruction ("If A's proof experiment fails to
show real decision influence, B should not be attempted at all; that would be strong evidence
the whole 'retrieval → decision' link is harder than this design assumes, and the honest next
step would be a new investigation, not a bigger version of the same untested mechanism"), this
result satisfies exactly that condition.

**The most promising honest next step, surfaced directly by this experiment's own data (§13),
not speculated in advance**: re-test the identical mechanism (persist real attribution,
exact-signature match, prompt injection) at a *different* decision point — **initial
generation-prompt construction for a later, independent self-edit cycle targeting the same
family** (e.g., `plan_code_logic()`'s prompt, or `_build_targeted_prompt()`'s existing
convergence-state read) — rather than the retry-prompt. That decision point has real headroom
to show an effect, because that is where the real, measured, multi-month recurrence actually
occurs (§13), unlike the retry step, which this experiment now shows already works most of the
time on its own.

---

## 18. What Remains Unknown

- Whether the same mechanism, at the *initial-generation* decision point instead of retry,
  would show a real effect — not tested here, and now the most obviously important next
  question this result raises.
- Whether a genuinely *novel* attribution (not redundant with visible error text, e.g. a
  cross-cutting pattern spanning multiple different error signatures) would fare differently
  than this experiment's necessarily-redundant one — §12's disclosed limitation means this
  experiment tested the *easier* version of the question, not the harder one the Hot Stove
  audit's `re`/`functools` recurrence data ultimately cares about.
- Whether a larger `n` at the same retry-prompt decision point would ever distinguish itself
  from a coin flip, given the near-ceiling baseline — mathematically unlikely to matter much,
  but not proven false at any `n`.
- Whether other models in the pool (this trial's EXPERIENCE condition drew `echo:latest` in 5/6
  reps and `gemma3:4b` in 1/6 — no `qwen2.5-coder`/`deepseek` draw occurred in either condition
  this run) would show a different pattern — model-selection variance across conditions was not
  independently controlled for beyond the shared `choose_model()` call both conditions make.

---

## 19. Final Recommendation

**HOT-STOVE NOT PROVEN, classified precisely as a DECISION-INFLUENCE FAILURE at the specific
decision point tested.** The mechanical substrate Architecture A proposed — reuse `trace_id`,
persist the pipeline's own real attribution, retrieve by exact signature match, inject at an
existing decision point — is real, was built in an afternoon exactly as scoped, and every
mechanical link functioned correctly. It simply did not change behavior at *this* decision
point, for *this* failure class, and the most likely reason (§13) is that this decision point
had almost no headroom to show an effect in the first place, because the underlying retry
mechanism already works without it. The honest, most valuable next step this experiment
produces is not "abandon Architecture A's design" but "re-point it at the decision point where
the real recurrence problem actually lives" — a smaller, cheaper, better-targeted next
experiment than a blind extension to Architecture B would have been.

---

### Appendix: real artifacts produced this pass, independently re-readable

- `app/experiments/architecture_a_hot_stove_proof/harness.py` — the isolated harness, safety
  neutralization, retry-prompt reconstruction.
- `app/experiments/architecture_a_hot_stove_proof/run_experiment.py` — the driver.
- `app/experiments/architecture_a_hot_stove_proof/candidate_knowledge.jsonl` — the one real,
  persisted record (§6).
- `app/experiments/architecture_a_hot_stove_proof/trial_results.jsonl` — all 12 matched-pair
  retry results, raw.
- `app/experiments/architecture_a_hot_stove_proof/run_report.json` — the complete run record,
  every phase, every real trace_id, every real error string, both safety checks.
- `sandbox/scripts/hotstove_proof_*.py` (20 files) — every real generated candidate this
  experiment produced, left in place in the sandbox's own real, already-existing scratch/archive
  directory for independent inspection.
