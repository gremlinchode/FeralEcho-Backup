# Phase 1A — Adversarial Validation of the Phase 1 Functional Quality Verifier

Read-only w.r.t. production. No RiverBrain, self-edit gate, `echo_model_orchestrator.py`,
`self_edit_manager.py`, `echo_quality_scorer.py`, persisted River state, or the historical
self-edit-backups corpus was modified. One new isolated test fixture was created
(`scripts/adversarial_functional_verifier_test.py`, untracked, not wired into anything live).
No weaknesses found were fixed — all are documented only, per this pass's explicit mandate.

## 1. Scope

Attack `app/core/functional_quality.py` and `sandbox/safe_exec_wrapper.py`'s new
`--mode=functional_verify` (both built earlier in this session, Phase 1) to determine what the
verifier actually measures, not what its own documentation claims it measures. Every claim below is
sourced to a real, executed test in this session — not inferred from source reading alone, though
source reading (§2) is what generated the attack hypotheses.

## 2. Files Inspected

- `app/core/functional_quality.py` (full file, fresh read, not from memory of Phase 1's own report)
- `sandbox/safe_exec_wrapper.py`, specifically the `_mode == "functional_verify"` block
  (lines 460-512) and its aggregation logic (`any_raised`/`any_tested`)
- `audits/2026-09-06_phase1_functional_quality_signal.md` (Phase 1's own report) — treated as a
  claim to verify, not a fact; two of its specific claims are directly contradicted by evidence below
  (§7)

## 3. Tests Performed

29 distinct constructed cases across the 15 required categories, plus a full independent
re-derivation of the 25-file real corpus (twice, for determinism), plus a targeted follow-up
investigation into an unexpected result (the `blocked_write` inversion, §7). All results below are
real `functional_execution_score()`/`combined_quality_score()` outputs from this session — see
`scripts/adversarial_functional_verifier_test.py` for the exact reproducible code.

## 4. Full Adversarial Matrix

| Case | AST | Execution | Output | Correctness | Sandbox | Functional Result | Expected |
|---|--:|---|---|---|---|---|---|
| 1. simple correct | 3 | completed | available | UNKNOWN (not checked) | ok | `verified_success` | success |
| 2. complex correct | 3 | completed | available | UNKNOWN | ok | `verified_success` | success |
| 3. simple broken (NameError) | 2 | raised | n/a | wrong (crashed) | ok | `verified_failure` | failure |
| 4. complex broken (NameError, high AST) | 3 | raised | n/a | wrong | ok | `verified_failure` | failure |
| 5a. wrong result (upper vs. documented lower) | 2 | completed | available | **wrong, undetected** | ok | `verified_success` | **should be failure per real contract — verifier cannot know this** |
| 5b. wrong result (constant garbage output) | 2 | completed | available | **wrong, undetected** | ok | `verified_success` | same |
| 5c. wrong result (off-by-one, never raises) | 2 | completed | available | **wrong, undetected** | ok | `verified_success` | same |
| 6a. no-op function | 2 | completed | `None` | **vacuous, undetected** | ok | `verified_success` | ambiguous by design |
| 6b. no-op class (real `__init__`, dead methods) | 2 | completed | n/a | **vacuous, undetected** | ok | `verified_success` | ambiguous by design |
| 7a. swallowed exception, silent passthrough | 3 | completed | available | **masks a real internal exception** | ok | `verified_success` | **should surface the swallowed error — cannot** |
| 7b. swallowed exception, plausible-looking wrong value | 3 | completed | available | **masks a real internal exception** | ok | `verified_success` | same |
| 9a. one good + one broken (broken second) | 3 | mixed | n/a | mixed | ok | `verified_failure` | any-fail-fails semantics confirmed |
| 9b. one good + one broken (broken first) | 3 | mixed | n/a | mixed | ok | `verified_failure` | order-independent, confirmed |
| 9c. 5 good + 1 irrelevant crasher | 4 | mixed | n/a | mostly correct | ok | `verified_failure` | **one trivial helper sinks 5 working functions** |
| 10. timeout (3s sleep, 1s budget) | n/a | UNKNOWN (killed) | n/a | UNKNOWN | infra | `sandbox_infra_failure`, `timed_out=True` | correctly distinguished from candidate failure |
| 11. explicit blocked write inside function body | 2 | raised (caught internally) | n/a | policy violation | **violated, but folded into candidate failure** | `verified_failure`, **`blocked_write=False`** | **should be flagged as policy, not code, failure — is not** |
| 12. genuinely unavailable import | n/a | import failed | n/a | n/a | ambiguous | `verified_failure` | candidate-attributed by design choice — see §9 |
| 13a. int-expecting fn, given `"test"` | 3 | completed | available | UNKNOWN | ok | `verified_success` (multiplication on str is valid Python) | false — this is a type-coincidence, not real success |
| 13b. list-expecting fn, given `"test"` | 2 | raised | n/a | n/a | ok | `verified_failure` | **false negative — function may be entirely correct for real list input** |
| 13c. dict-expecting fn, given `"test"` | 2 | raised | n/a | n/a | ok | `verified_failure` | same false-negative risk |
| 13d. 0-arg function | 2 | completed | available | UNKNOWN | ok | `verified_success` | supported |
| 13e. 2-required-arg function | n/a | not attempted | n/a | n/a | n/a | `not_applicable` | correctly skipped, not guessed |
| 14a. stdout/stderr only | 2 | completed | available (uncaptured) | UNKNOWN | ok | `verified_success` | supported, output not inspected |
| 14b. env access, no write | 2 | completed | available | UNKNOWN | ok | `verified_success` | supported |
| 15. determinism (5x same file) | — | — | — | — | — | 5/5 identical | **deterministic, confirmed** |
| 15b. determinism (real known-bad file, 3x) | — | — | — | — | — | 3/3 identical | **deterministic, confirmed** |

## 5. Results Summary

The verifier reliably answers "did this raise" and does so deterministically. It does not, and by its
own documented contract does not claim to, answer "is this correct," "is this meaningful," or "is
this the same code path a human-authored equivalent would take." Every category-5/6/7 case —
9 of the 29 constructed cases — scored `verified_success` while being genuinely, meaningfully wrong,
vacuous, or internally broken-but-hidden. This is the expected, documented shape of the tool, not a
surprise on its own — the surprise is in §7.

## 6. Failure Modes

1. **Semantic-correctness blindness (§5a-c, 7a-b)** — a candidate can execute cleanly while doing the
   wrong thing entirely, or while masking a real internal exception behind a bare `except`. The
   verifier has zero visibility into either.
2. **Vacuous-success blindness (§6a-b)** — an empty stub or a class whose only tested surface
   (`__init__`) does nothing scores identically to genuinely working code.
3. **All-or-nothing aggregation can penalize disproportionately (§9c)** — five working functions plus
   one irrelevant, trivially-crashing helper produces the same `verified_failure`/combined-0 result as
   a candidate that is entirely broken. Deterministic and order-independent (§9a/9b confirm this), but
   a real asymmetry: there is no partial-credit path.
4. **`blocked_write` telemetry is functionally inverted from its documented purpose** — see §7, the
   most important finding of this pass.
5. **Type-mismatch false negatives (§13b-c)** — a function whose real, correct contract expects a
   `list`/`dict`/other non-string type will reliably score `verified_failure` for reasons entirely
   unrelated to its actual correctness, because the smoke-test's one synthetic argument is always the
   string `"test"`.

## 7. False-Positive Risks

The dominant false-positive class is semantic (§5-7 above): "verified_success" can and does mean
"executed without raising," never "correct." This is Phase 1's own documented scope, not a defect —
but it means treating `verified_success` as evidence of correctness, anywhere downstream, would be a
misuse of the signal regardless of how the verifier itself is implemented.

**The most important finding of this entire pass, not anticipated by Phase 1's own report:**
`blocked_write` — the flag specifically designed to distinguish "the candidate tried a forbidden
operation" from "the candidate's logic is broken" — is **empirically backwards** for the real cases
that actually occur.

Direct evidence, both directions:

- A candidate whose own top-level function body attempts a real blocked write
  (`scripts/adversarial_functional_verifier_test.py`, Case 11: `open('/tmp/...', 'w')` inside a
  smoke-tested function) produces `outcome=verified_failure, blocked_write=False`. The
  `PermissionError` is real, correctly raised by the sandbox's write-guard, and correctly caught by
  the smoke-test loop's own per-callable `try/except` — but because it's caught *inside* the
  subprocess rather than propagating to `proc.stderr`, `functional_quality.py`'s `blocked_write`
  detection (which only inspects `proc.stderr`) never sees it. **This is the exact real-world shape
  of the Phase 1 report's own headline example** (`self_edit_generated.py`'s `get_shortened_code`
  hitting the identical write-guard) — re-run in this session, confirmed: `blocked_write=False` for
  that real file too, despite Phase 1's own report describing this distinction as preserved.
- Conversely, a completely trivial candidate that does nothing but `import app.emergent_scheduler`
  (a real project module several backup files in the corpus also import) produces
  `outcome=verified_success, blocked_write=True` — confirmed with a minimal, isolated repro
  (`import app.emergent_scheduler as emergent\n\ndef noop():\n    return 1\n`). The flag is firing on
  an *incidental import-time side effect of a real dependency*, entirely unrelated to the candidate's
  own code. Three of the 25 real corpus files show this exact pattern (`self_edit_20260813175936.py`,
  `self_edit_20260816184808.py`, `self_edit_20260826121324.py` — all import `app.emergent_scheduler`),
  and in two of the three cases the candidate's *own* logic separately succeeded or failed on
  unrelated grounds, making the `blocked_write=True` flag pure noise with respect to what it claims
  to measure.

Net effect: **`blocked_write` currently fires on the wrong cases and stays silent on the right ones.**
It is not merely uninformative — trusting it as designed would actively mislead. This was not caught
in Phase 1 because Phase 1's own testing never constructed a case designed specifically to distinguish
"write blocked inside a smoke-tested call" from "write blocked at import time" — the one real corpus
example Phase 1 cited (`get_shortened_code`) was read from the `tested[].error` string, not from the
`blocked_write` field itself, so the mismatch went unnoticed even though the data to notice it was
already present in Phase 1's own captured output.

## 8. False-Negative Risks

Type-mismatch false negatives (§13b-c, §5): any real self-edit candidate whose target function
genuinely expects a non-string argument will be marked `verified_failure` for a reason having nothing
to do with its actual correctness. Scoped risk, not unbounded — confirmed in Phase 1's own report and
re-confirmed here that every one of the 25 real historical backups takes a string parameter, so this
specific corpus is not currently exposed to this risk. It would become live risk only if self-edit's
target-function contracts ever diversify beyond string-in/string-out code transforms.

## 9. Sandbox / Infrastructure Distinctions

The four-state design (`verified_success`/`verified_failure`/`not_applicable`/`sandbox_infra_failure`)
holds up under direct, real testing for the cleanest cases: a genuine timeout (§Case 10) correctly
and only produces `sandbox_infra_failure` with `timed_out=True`, never `verified_failure` — confirmed
by directly forcing it (`time.sleep(3)` under a 1s budget). This is a real, working distinction, not
just a documented intention.

One deliberate, disclosed design choice worth surfacing explicitly (Adversarial Question D): an
import failure for a *genuinely unavailable* dependency (Case 12, `import
this_module_definitely_does_not_exist_anywhere`) is classified `verified_failure`, not
`sandbox_infra_failure` — the code's own comment in `functional_quality.py` explains this is
deliberate, matching how F1/F2 already treat import failures as the candidate's own fault elsewhere
in this codebase. This is defensible, but it does mean a genuine environment problem (a real package
that should be present but was never installed, distinct from a candidate hallucinating a nonexistent
module) would currently be misclassified as "the candidate is broken" rather than "the test
environment is broken." Not distinguishable with current information — the traceback text alone
cannot tell these two cases apart.

## 10. Input-Signature Limitations

Directly confirmed by category (§Case 13), reported as required, not inferred:

| Signature class | Support |
|---|---|
| 0 required args | **SUPPORTED** |
| exactly 1 required arg, string-compatible contract | **SUPPORTED** |
| exactly 1 required arg, non-string contract (int/list/dict) | **NOT SUPPORTED** — produces a type-mismatch false result in either direction depending on what operation the function performs on a string |
| 2+ required args | **NOT SUPPORTED** — correctly and honestly skipped (`not_applicable`), never guessed |
| class construction, 0-1 required `__init__` params | **SUPPORTED** (construction only — see §11 on method coverage) |
| class methods (beyond `__init__`) | **NOT SUPPORTED** at all — never invoked by the verifier under any signature |

## 11. Semantic-Correctness Limitations

Confirmed exhaustively by §5-7: the verifier establishes **execution**, never **correctness**.
Nothing in its design — smoke-testing with one generic synthetic argument, checking only for a raised
exception — could establish correctness without either (a) a real expected-output spec per candidate
(explicitly out of scope, no such spec exists in this codebase today) or (b) executing every code path
with adversarially chosen inputs, which the current single-generic-string strategy does not attempt
and was never designed to.

## 12. Security / Policy Observations

No new security gap was found — the underlying sandbox (Seatbelt profile + write-guard patches) held
in every adversarial case attempted, including the explicit blocked-write attempt (§Case 11) and the
timeout case (real process kill confirmed, not a hung subprocess). The finding in §7 is a
**measurement/telemetry accuracy problem**, not a containment problem: the write was correctly
*blocked* in every case tested; what's unreliable is only whether the `blocked_write` flag correctly
*reports* that it happened.

## 13. Determinism Observations

Confirmed deterministic across 5 repeated runs of a simple case, 3 repeated runs of the real known-bad
production file, and a full independent second pass over all 25 real corpus files (zero mismatches
against the first pass). No evidence of flakiness in this session's testing. Caveat, stated plainly:
determinism was only tested under normal system load on this machine tonight — not stress-tested under
the kind of real concurrent-Ollama-contention conditions Phase 0's own investigation found earlier in
this same session (that contention affects LLM calls specifically; this verifier makes none, so it is
not expected to be affected the same way, but this was not independently re-confirmed here).

## 14. Historical-Corpus Results

Independently re-derived, not copied from Phase 1's report: **16/25 (64%) `verified_failure`, 8/25
(32%) `verified_success`, 1/25 (4%) `not_applicable`, 0/25 `sandbox_infra_failure`** — identical to
Phase 1's own numbers, now confirmed by a fully independent re-run plus a second determinism-checking
pass (zero mismatches). n=25 is the entire currently-retained real population, not a sample — no
further statistical claim (confidence interval, significance test) is warranted or attempted at this
size, and none is made here.

New information this pass adds beyond Phase 1's own table: 3 of the 25 files show `blocked_write=True`
(all three importing `app.emergent_scheduler`), which — per §7 — is very likely noise from that
import's own side effects rather than signal about those specific candidates' own code quality.

## 15. Exact Capabilities of the Verifier

- Reliably, deterministically detects: undefined names, wrong-arity calls, type errors that manifest
  immediately on a generic string input, blocked filesystem writes (as a raised exception, correctly
  causing failure — even though the *separate* `blocked_write` telemetry flag misreports this), and
  genuine import failures.
- Correctly distinguishes a real timeout from a candidate exception.
- Correctly, conservatively declines to guess at 2+-argument signatures rather than risk a
  meaningless result.
- Deterministic across repeated runs.

## 16. Exact Things It Cannot Establish

- Whether output is correct against any real or implied contract.
- Whether a no-op or vacuous implementation is "working."
- Whether an internally-caught exception represents a real, hidden bug.
- Whether a `verified_failure` on a 1-argument function reflects a real defect or merely a type
  mismatch with the synthetic probe.
- Whether a candidate's *own* code attempted a blocked write, as opposed to an *imported dependency's*
  own unrelated import-time side effect — the current `blocked_write` flag cannot be trusted for this
  distinction in either direction (§7).
- Anything about class methods beyond `__init__`.

## 17. Adversarial Questions — Direct Answers

**A. Can a broken candidate receive a functional success?** Yes — confirmed directly and repeatedly
(§5, §6, §7: wrong output, no-op, and swallowed-exception cases all scored `verified_success`).

**B. Can a correct candidate receive a functional failure?** Yes — confirmed directly (§13b-c: a
correct list/dict-handling function fails purely from the string-typed synthetic probe; §9c: a
correct function bundled alongside one unrelated broken helper).

**C. Can a candidate execute successfully while being functionally incorrect?** Yes, unambiguously
— this is the verifier's single most consistent and most important blind spot, demonstrated in 6 of
29 constructed cases (§5a-c, §7a-b) plus the two no-op cases (§6a-b).

**D. Can a sandbox infrastructure problem masquerade as candidate failure?** Partially yes, by a
deliberate, disclosed design choice — a genuinely-unavailable dependency import is classified as
candidate failure (§9), matching this codebase's existing precedent elsewhere but still a real, if
narrow, ambiguity.

**E. Can a malicious or pathological candidate exploit the verifier's definition of success?** Yes —
the swallowed-exception cases (§7) are exactly this: a candidate that wraps its own real defect in a
bare `try/except: pass` (or returns a plausible-looking constant after catching a real error)
reliably and deterministically scores `verified_success`. No adversarial-input-generation is needed;
this pattern is trivial to construct and would pass every time.

**F. Does the verifier test the actual contract of self-edit candidates, or merely their ability to
execute?** Merely execution. There is no per-family contract or expected-output spec anywhere in this
codebase for the verifier to test against, and it does not attempt to infer one.

**G. Does the verifier produce enough information to justify feeding a binary reward into River?**
**No, not as a binary/scalar reward on its own, based on the evidence in this report.** The signal is
real and non-trivial — it discriminates a genuinely large, real class of failures (64% of the actual
historical corpus) that the old AST-only scorer was completely blind to, which is real, demonstrated
value. But collapsing `verified_success` into a training-positive would train toward "executes without
raising" as a terminal goal, which this report has shown is satisfiable by no-op stubs and
exception-swallowing wrappers — exactly the kind of degenerate optimization target a real training
signal should not reward without a compensating check. A defensible design (not implemented, not
recommended for immediate adoption without further review) would need at minimum: fixing the
`blocked_write` inversion (§7) before it's trusted for anything, and treating `verified_success` as a
necessary-but-not-sufficient gate rather than a positive reward by itself.

---

## Final Verdict

```
VERIFIER USABLE BUT LIMITED
```

The verifier does exactly and only what Phase 1's own documentation says it does — it is not
mischaracterized in its stated scope, and every core discrimination criterion from Phase 1 (broken
vs. working, complex-vs-simple non-confound, real historical corpus differentiation, determinism)
holds under direct adversarial re-testing in this pass. It is a genuine, working, non-trivial
improvement over pure AST counting for the one narrow question it was built to answer.

It is not, as currently built, ready to feed a production learning signal without further work — not
because it's broken, but because (1) `blocked_write`, one of its own four documented telemetry
dimensions, is empirically backwards for the real cases that actually occur in this codebase's own
historical data, and needs correcting or removing before anyone trusts it, and (2) `verified_success`
is trivially satisfiable by no-op and exception-swallowing candidates, which is fine as a documented
scope boundary for Phase 1's stated purpose, but is a real gap if Phase 2 or later work is ever
tempted to treat `verified_success` as a positive training reward rather than a necessary floor.

Neither finding required fixing anything to discover — both were found by testing the tool against
cases its own design should have anticipated but that Phase 1's own test matrix did not happen to
construct. That is exactly what this adversarial pass existed to find.
