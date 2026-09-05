# Self-Edit Forensic Verification — Adversarial Re-Investigation

Independent, adversarial re-verification of
`audits/2026-09-03_self_edit_quality_metric_investigation.md` (hereafter
"the prior audit"). No production code was modified, no scoring function
rewritten, no fitness gate altered, no counter reset. Every claim below
was checked against current source (with exact file/line citations) or
real, current log/state data — several were checked by direct,
reproducible execution (scoring real historical files, running the real
convergence-tracking function against a synthetic sequence), not just
reading code and reasoning about it.

---

## 1. Executive Finding

**The prior audit's central quantitative claim — "0 out of 37 candidates
have ever cleared the fitness gate, literally zero" — is WRONG, and the
error is found and corrected here.** Real successful deploys are common:
**426 successes out of 463 real fitness-gate evaluations (92%)**, not
zero. The prior audit's mistake was methodological: it searched only for
log lines containing explicit `candidate_quality=`/`current_quality=`
values, which — verified directly against source — **only appear in the
rejection branch's log message**, never in the success branch's. This
silently restricted the "population" to rejections alone and mistook
that subset for the whole.

**However, the prior audit's deeper, more important claim survives
independent re-verification and is now proven more precisely than
before: the fitness gate cannot detect improvement, because the metric
it uses saturates almost immediately, and once both sides of the
comparison are at the ceiling, "success" means nothing more than "tied,"
never "better."** Directly confirmed: **all 25 currently-retained real
deployed versions of `self_edit_generated.py` score a perfect 4/4** on
this metric. The 92% success rate is not evidence of an effective,
improving system — it is exactly what you'd expect from a system that
reaches an easily-satisfied ceiling almost immediately and then ties
against itself, indefinitely, with every subsequent generation.

**Verdict on the seven possibilities the mission asked me to weigh:**
this is **primarily #1 (a broken evaluator) and #5 (insufficient
experimental instrumentation), not #2 (the gate) or #3 (the convergence
detector) in the way originally framed** — both of those are working
exactly as designed; the design itself just doesn't answer the question
anyone actually cares about. There is also a real, previously-unexamined
**#7 (something else entirely)**: the current deployed file does not
define `apply_to_code`, meaning **even a perfect score right now would
have zero behavioral effect on Echo** — the file is loaded to prove it
*can* load safely, not because anything calls it.

---

## 2. What the Previous Audit Claimed

Six numbered claims, quoted/paraphrased directly from the audit's own
text, verified one by one in Section 3 below:

1. Across 37 real deploy decisions since 2026-07-11: scores `{1:4, 2:5,
   3:28, 4:0}`, reference always 4.
2. Therefore the fitness gate rejected 37/37, not because candidates
   were demonstrated worse, but because none matched the reference.
3. The coding quality metric measures AST structural complexity, not
   correctness/validity/maintainability/behavioral equivalence.
4. The current deployed `self_edit_generated.py` scores a "perfect" 4
   despite defining `run_code_generator` twice, referencing `self` where
   it doesn't exist, and carrying dead logic in a string literal.
5. `non_convergent_streak` reads 0 for every family right now, including
   `response_shortening` (58 attempts, 33 names, zero successes).
6. `non_convergent_streak` measures per-cycle name-count growth, not
   historical failure to converge.

---

## 3. Claim-by-Claim Verification

| # | Claim | Verdict | Detail |
|---|---|---|---|
| 1 | Score distribution `{1:4,2:5,3:28,4:0}`, ref=4 | **TRUE but incomplete — silently scoped to rejections only** | The distribution itself is accurate for the 37 *rejected* cases. It was presented as if it described the whole population of real attempts. It doesn't — see Claim 2. |
| 2 | Gate rejected 37/37 (zero real successes) | **FALSE — corrected below** | 426/463 (92%) real attempts succeeded. The "37" is only ever the rejected subset; the success branch's log line never records scores at all, which is why the original count-by-grep missed it entirely. |
| 3 | Metric measures AST complexity, not correctness | **TRUE, independently reproduced** | See §5. Exact node types confirmed, exact score-to-complexity mapping confirmed, exact line numbers cited. |
| 4 | Current file has the three named defects | **TRUE, all three confirmed — with one necessary precision correction** | See §7. The "self is undefined" claim is real but the *reachable* failure is an `AttributeError` one line earlier than the audit stated, not the `NameError` it named. Both are real bugs; the audit conflated two distinct failure surfaces into one. |
| 5 | `non_convergent_streak`=0 for `response_shortening` (58/33/0-success) | **TRUE on the streak value; FALSE on "zero successes"** | Streak is genuinely 0. But `response_shortening`'s 58 tracked cycles are a **subset of the 426 successes**, not 58 failed attempts — see §8. `_record_convergence()` (the function that updates this counter) only ever runs *after* a successful deploy; it cannot see rejections at all. |
| 6 | Streak measures per-cycle name-count growth | **TRUE, independently reproduced with a direct, controlled test** | See §9. A synthetic run of the real function, not a description of it, confirms the mechanism precisely. |

---

## 4. Self-Edit Architecture / Data Flow

```
run.py (AutonomousSelfEdit thread, hourly) / model_guided_autonomous_loop
  → self_edit_manager.perform_self_edit()
    → execute_self_edit(prompt, dry_run=False)     [self_edit_manager.py:1816]
      → plan_code_logic() → generate_code_from_plan()   [F1 AST scan applied]
      → _stage_and_import_test()                         [F2 sandbox import test]
      → FITNESS GATE (this investigation's focus)         [self_edit_manager.py:2062-2104]
        → _score_response_quality(candidate, "coding")    [echo_quality_scorer.py:344]
        → _score_response_quality(current_prod, "coding")
        → reject if candidate < current  →  result: rejected_not_improvement
        → else → backup_existing_code() + save_code()     [F3 post-write AST scan]
          → load_self_edit_module()                        [self_edit_manager.py:~985]
            → _record_convergence(callables)                [self_edit_manager.py:1045]
              → writes self_edit_convergence.json (non_convergent_streak, etc.)
          → result: success  (no scores logged here — see §6)
```

The rejection path and the success path **diverge structurally in what
they log**, which is the direct, root cause of the prior audit's error:
the rejection path (`self_edit_manager.py:2087-2090`) logs
`candidate_quality=X current_quality=Y`; the success path
(`self_edit_manager.py:2135`) logs only `result: success | timestamp:
...` — no scores at all. Any investigation that filters
`SELF_EDIT.log` by presence of `candidate_quality=` will only ever see
rejections, by construction.

---

## 5. Fitness Metric — Exact Implementation

`echo_quality_scorer.py`:

- `_score_response_quality(response, task_type)` — `line 344`. Coding
  branch: `lines 374-393`.
- `_has_real_code(response)` — `lines 168-183`. Requires ≥2 of
  `FunctionDef`/`ClassDef`/`Assign`/`Return`/`Import`/`ImportFrom`/`Expr`
  nodes after extracting the code portion of the response
  (`_extract_code_text`, `lines 150-165`, tolerates an unclosed fence).
- `_has_static_errors(tree)` — `lines 287-293`. **Checks exactly one
  thing**: a literal `x / 0` (`BinOp` with `Div` op and a constant `0`
  right operand). Nothing else is checked here — no undefined-name
  detection, no attribute-existence check, no duplicate-definition
  check.
- `_ast_complexity(tree)` — `lines 296-313`. Counts instances of:
  `If, For, While, ListComp, DictComp, SetComp, GeneratorExp, Try, With,
  AsyncFor, AsyncWith, IfExp, BoolOp` (`lines 310-312`, exact tuple).
  The function's own docstring (`lines 297-308`) is explicit that this is
  "a proxy for algorithmic substance," not a correctness measure — the
  module's own authors already knew this was a proxy, not a ground
  truth, when they wrote it.
- Scoring map (coding only), `lines 374-393`:
  - no real code, syntax error, or static error → **1**
  - real code, complexity `== 0` → **2**
  - complexity `1-2` → **3**
  - complexity `>= 3` → **4** (ceiling)

**Confirmed: production is scored via the exact same call.**
`self_edit_manager.py:2072` (`_score_response_quality(code,
task_type="coding")`) and `self_edit_manager.py:2078-2079`
(`_score_response_quality(current_code, task_type="coding")` if
`current_code.strip()` else `-1`) — identical function, identical
`task_type` argument, no separate code path for the reference.

**Normalization/clamping/fallback, checked exhaustively:**
- No clamping or scaling of the returned int anywhere in either the
  scorer or the gate — raw `1`-`4` int used directly in the `<`
  comparison.
- One real fallback: if `current_code` is empty/missing, `current_quality
  = -1` (`self_edit_manager.py:2078-2080`) — the bootstrap case, where
  any real candidate trivially passes.
- One real fail-open exception path (`self_edit_manager.py:2100-2104`):
  if `_score_response_quality()` itself raises, the comparison is
  skipped entirely and the code deploys unconditionally, logged as a
  `WARNING`. **Checked whether this has ever actually fired**: `grep -c
  "Fitness comparison failed" memory/SELF_EDIT.log` → **0**. This path
  exists and is real, but has never been exercised in the observable
  history — it is not the explanation for the 426 successes.

**A real defect in the top-level docstring, not previously noted:**
`_score_response_quality()`'s own module-level docstring (`lines
346-354`) describes the 0-4 scale as "0=confabulation... 4=excellent,
deep, authentic, scripturally sound" — that description is accurate for
the `personal`/`creative`/`general` branch **only**. The coding branch's
own scale (documented separately in a comment at `lines 362-366`) means
something completely different (parse validity + structural node
count). A reader trusting the function's own top-level docstring alone
would be misled about what a coding-task score of 4 actually certifies.

---

## 6. Fitness Gate — Exact Implementation

`self_edit_manager.py`, inside `execute_self_edit()` (defined `line
1816`), under `with _self_edit_deploy_lock:` (`line 2062`):

```python
# line 2082
if candidate_quality < current_quality:
    ... result: rejected_not_improvement ...
    return False, "Rejected: ..."
# falls through to backup + save + load if NOT rejected
```

- **Exact comparison: strict `<` for rejection, meaning `>=` (ties
  included) passes.** Equality is explicitly accepted, not merely
  tolerated — there is no `<=` variant anywhere nearby that would
  require strict improvement.
- **Why 0/37 *rejections* could never have scored 4** is now understood
  precisely, and it is not a logic error: a rejection can only be
  logged when `candidate_quality < current_quality`. Since
  `current_quality` has been observed at the ceiling (4) in every real
  case checked, any rejection by definition has `candidate_quality <
  4`, i.e., `1`, `2`, or `3` — never `4`. **This is not evidence the
  gate is broken; it is a tautological consequence of what "rejection"
  means once the reference sits at the ceiling.** The interesting
  question was never "why do rejections never hit 4" (that's true by
  construction) — it's "why does the reference sit at the ceiling
  permanently," answered in §7-8.
- **The gate is functioning exactly as designed.** The comparison
  operator is correct, equality is deliberately accepted (confirmed
  intentional by the bootstrap `-1` fallback, which only makes sense if
  the designers wanted a "clearly worse test" rather than a "strictly
  better test"), and the fail-open exception path is a defensible safety
  choice that has never needed to fire. **There is no logic error in
  the gate itself.** The defect is entirely one layer up, in what the
  gate is being asked to compare.

---

## 7. Production Reference Inspection

`app/core/self_edit_generated.py`, read directly, current content (35
lines):

| Alleged defect | File/Function | Line(s) | Reachable? | Runtime failure? | Dead/unreachable? | Detected by current metric? |
|---|---|---|---|---|---|---|
| `run_code_generator` defined twice | module level | `26-29` (first), `31-35` (second) | First def is shadowed at module-load time by the second (both are plain module-level `def`s with the same name) | First def's body (calling `CodeGenerator()`, itself undefined — see below) would raise if ever invoked, but nothing keeps a reference to it after being overwritten | **Yes — the first definition is dead code after import**, unreachable via the name `run_code_generator` | No — `_has_static_errors`/`_ast_complexity` don't check for name collisions at all |
| `self` referenced where undefined | `get_shortened_code(code)` | `21` (def), `23-24` (bad references) | **Corrected from the prior audit**: `get_shortened_code` is never called as a bare function anywhere in this file — it's only reached via `self.get_shortened_code(...)` (`lines 34-35`), an *attribute* lookup on whatever object is passed into `run_code_generator(self)`. Since no class in this file defines a `get_shortened_code` attribute, that call would raise **`AttributeError`**, one step *before* the `NameError` inside `get_shortened_code`'s own body could ever be reached through this path. | Yes — either `AttributeError` (via the only real call path) or `NameError` (if the bare function were ever called directly, which nothing here does) | The bare function itself is unreachable in practice; the *class* of bug (undefined `self`) is real regardless of which exception fires first | No |
| Dead logic in a string literal | inside `run_code_generator(self)` | `33` | The string is assigned to a local variable and passed as plain data (`lines 34-35`) — never parsed or executed as code by this file | No — it's inert text | Yes, entirely — confirmed it contributes **zero** AST nodes to the complexity count (a `Constant` string is one leaf node; its textual content is not separately parsed) | No — and structurally *can't* be, since the scorer only walks the outer file's own AST |
| **New, not in the prior audit**: zero import statements in the entire file | module level | n/a (absence) | N/A | **Yes** — `logging` (line 8), `apply_list_comprehension` (line 15), `defaultdict`/`Counter` (lines 17-18, 23-24), `CodeGenerator` (line 27) are referenced but never imported or defined anywhere in the module. Confirmed via direct AST scan: `0` `Import`/`ImportFrom` nodes in the file. Every function that reaches any of these lines would raise `NameError` immediately. | These are inside function bodies, so `ast.parse`/module import succeeds cleanly (bodies aren't executed at import time) — they are **latent**, not currently triggered, since nothing calls these functions | No — `_has_static_errors` checks only literal division by zero; free/undefined-name detection is a known, separate, and real gap in the entire safety pipeline (F1's own AST scanner is oriented toward *dangerous* operations, not *undefined* ones) |

**Exact AST complexity breakdown for the current file, computed
directly, not estimated:** 7 total structural nodes — `ListComp` ×3
(lines 15, 23, 24), `GeneratorExp` ×2 (lines 23, 24), `With` ×1 (line
22), `IfExp` ×1 (line 18). This is comfortably above the `>=3` threshold
for a score of 4, and confirms none of the four real defects above
contribute to or subtract from that count.

---

## 8. Deployment History Reconstruction

**Corrected population, `memory/SELF_EDIT.log`, self-edit-shaped prompts
only (containing "Modify app/core/self_edit_generated.py only"):**

| Outcome | Count | Date range |
|---|---|---|
| `result: success` | **426** | 2026-06-26 → 2026-09-03 |
| `result: rejected_not_improvement` | **37** | 2026-07-11 → 2026-09-03 |
| **Total real fitness-gate evaluations** | **463** | 2026-06-26 → 2026-09-03 |

**Real production quality, sampled directly from the 25 currently-
retained backup files in `app/core/self_edit_backups/`** (each backup
is the file that was in production immediately before the next real
deploy replaced it):

| File (truncated) | Score | Complexity | Static errors | Size (bytes) |
|---|---|---|---|---|
| `self_edit_20260808123116.py` | 4 | 8 | False | 1334 |
| `self_edit_20260813120335.py` | 4 | 3 | False | 1731 |
| `self_edit_20260813175936.py` | 4 | 4 | False | 939 |
| `self_edit_20260814214945.py` | 4 | 3 | False | 1978 |
| `self_edit_20260816184808.py` | 4 | 3 | False | 684 |
| `self_edit_20260817063419.py` | 4 | 3 | False | 755 |
| `self_edit_20260818034010.py` | 4 | 5 | False | 603 |
| `self_edit_20260818185424.py` | 4 | 3 | False | 642 |
| `self_edit_20260819011326.py` | 4 | 8 | False | 787 |
| `self_edit_20260823031936.py` | 4 | 8 | False | 950 |
| `self_edit_20260825011254.py` | 4 | 3 | False | 993 |
| `self_edit_20260825052608.py` | 4 | 5 | False | 1817 |
| `self_edit_20260825173359.py` | 4 | 3 | False | 1310 |
| `self_edit_20260826121324.py` | 4 | 7 | False | 2428 |
| `self_edit_20260826203740.py` | 4 | 5 | False | 1033 |
| `self_edit_20260827211140.py` | 4 | 5 | False | 1033 |
| `self_edit_20260828013303.py` | 4 | 4 | False | 1144 |
| `self_edit_20260828160555.py` | 4 | 4 | False | 880 |
| `self_edit_20260828174711.py` | 4 | 7 | False | 1104 |
| `self_edit_20260829160112.py` | 4 | 3 | False | 841 |
| `self_edit_20260830094330.py` | 4 | 5 | False | 717 |
| `self_edit_20260831132718.py` | 4 | 4 | False | 1493 |
| `self_edit_20260901230647.py` | 4 | 3 | False | 478 |
| `self_edit_20260902194310.py` | 4 | 4 | False | 776 |
| `self_edit_20260903040641.py` | 4 | 8 | False | 2135 |

**Every single one of the 25 retained real deploys scores exactly 4.**
This is the direct, decisive evidence for the corrected central finding:
the system isn't stuck rejecting everything — it has been **churning**,
replacing one ceiling-scoring implementation with another
ceiling-scoring implementation, roughly every 1-3 days, for at least a
month (the 25-file retention cap means older history is rotated out;
the true total since 06-26 is almost certainly larger than 25 real
deploys, capped only by what's currently kept on disk).

**Reconciling "37" and "58" — different, non-overlapping slices of the
same 463, not different stages of the pipeline as such:**
- **37** = every real rejection, across *all* families, project-wide.
- **58** = `self_edit_convergence.json`'s `cycles_attempted` counter for
  the `response_shortening` family specifically — and, critically
  (§6/§9), `_record_convergence()` is only ever called from
  `load_self_edit_module()`, which only runs *after* a successful
  deploy. **58 is therefore a subset of the 426 successes** (the ones
  whose deployed callable names happened to match this family's
  keywords), not a separate or overlapping-with-rejections population.
  The prior audit's phrasing ("58 attempts... zero successful
  deployments") is the single most consequential error in the whole
  document — every one of those 58 cycles **was** a successful
  deployment; that's the only way `_record_convergence()` could ever
  have seen them.

**One additional, real, adjacent discovery, flagged but not fully
chased down** (out of scope for this investigation's specific ask, but
directly bears on "can self-edit ever matter"): 4 of the 25 retained
backups (`08-13` ×2, `08-23`, `08-26`) **do** define the `apply_to_code`
hook — the only mechanism by which this file's code has ever had any
real effect on Echo's behavior (per this project's own established
architecture). `memory/apply_to_code_invocations.jsonl` has **3,196**
real entries, `changed: true` in 1,985 (62%) — a real, non-trivial
activity level, with distinct, real error categories (`timed out after
2.0s`: 383; `APPLY_TO_CODE_BAD_RETURN_TYPE`: 322; three distinct
`NameError`-shaped failures: 210 combined; `blocked_write_attempt`: 20).
**Whether that 62% "changed: true" represents genuine, useful
transformation or the same class of corruption this project's own
history already found once (Finding 28: a 2173→47 character shrink read
as corruption, not improvement) was not independently verified in this
pass** — flagged as a real, separate, adjacent open question, not
answered here.

**The current, live `self_edit_generated.py` does not define
`apply_to_code` at all.** Whatever its score, and regardless of how the
scoring metric is eventually fixed, **the currently-deployed code has
zero behavioral effect on Echo right now** — it is loaded solely to
prove F3's post-write safety scan passes, not because anything in the
running system calls any of its functions.

---

## 9. `non_convergent_streak` Analysis

**Definition and writers**, `self_edit_manager.py`:
- State file: `_CONVERGENCE_STATE_FILE` (`line 1025-1027`,
  `self_edit_convergence.json`).
- Families and keywords: `_CONVERGENCE_FAMILIES` (`lines 1028-1032`):
  `prose_stripping: ("prose",)`, `response_shortening: ("shorten",
  "length", "concise", "trim", "truncat")`, `quality_scoring: ("quality",
  "score", "eval")`.
- Sole writer: `_record_convergence(callables)` (`lines 1045-1113`),
  called **exactly once** in the whole codebase, from
  `load_self_edit_module()` (`line 1007`), which itself only executes
  after a real deploy has already been written to disk and successfully
  imported. **`_record_convergence()` structurally cannot see a
  rejected attempt — it never runs for one.**
- Per family per cycle (`lines 1065-1091`):
  ```python
  matching_names = [name for name in lower_names if any(kw in name for kw in keywords)]
  count = len(matching_names)
  if count == 0:
      continue  # line 1071 — this cycle is silently skipped, state untouched
  convergent = count <= prev.get("count", 0) or prev.get("count", 0) == 0   # line 1073
  streak = 0 if convergent else prev.get("non_convergent_streak", 0) + 1     # line 1074
  ```

**What it actually measures**: whether the *count* of family-matching
callable names in the just-deployed file is `<=` the count from the
last cycle this family was recorded. **It has no concept of identity —
it cannot tell "the same function persisted" from "a different function
with a different name replaced it."**

**What increments it**: `count` growing relative to the last recorded
cycle for that family.
**What resets it to 0**: `count` staying flat or shrinking, or this
being the family's first-ever recorded cycle.
**What constitutes a "cycle"**: one real, successful deploy whose loaded
module contains at least one callable name matching the family's
keywords. A deploy whose file has *zero* matching names for a family is
silently skipped for that family (`line 1071`) — the family's state is
simply not touched that cycle, not decremented, not reset.
**Historical failure is not retained by the streak itself** — only
`all_names_seen` (capped at 50) and `cycles_attempted` accumulate real
history; `non_convergent_streak` is a pure one-step comparison with no
memory beyond the immediately preceding recorded cycle.

**Direct answer to the specific question posed**: *"Could a self-edit
family fail repeatedly for dozens of attempts without ever successfully
deploying while `non_convergent_streak` remains 0?"*

**Not exactly as literally phrased — and the real, verified answer is
more precise and, if anything, more concerning.** Because
`_record_convergence()` only runs on successful deploys, a family that
is *rejected* dozens of times in a row never touches this counter at
all — it simply stays frozen at whatever it last was, which is a real
gap, but a different one than "streak reads 0 during failure." The
mechanism the audit was actually describing, and the one demonstrated
directly below, is real and reproducible: **a family can *successfully*
deploy dozens of times, under a different, never-before-seen name each
time, and `non_convergent_streak` reads 0 on every single cycle**,
because the raw *count* of matching names never grows — it's always
"1 new name replacing 1 old name."

**Direct, reproducible demonstration** — the real function,
`_record_convergence()`, called 10 times in sequence with a
synthetic-but-realistic sequence of distinct function names (state file
redirected to a scratch path, no production data touched):

| Cycle | Deployed name | Matches family? | `count` | `non_convergent_streak` | `cycles_attempted` |
|---|---|---|---|---|---|
| 1 | `shorten_response_v1` | yes | 1 | **0** | 1 |
| 2 | `compress_reply` | **no** (misses all 5 keywords) | — | *(cycle silently skipped — real, additional finding: an easy-to-miss keyword mismatch drops a whole cycle from tracking entirely, even though it's plausibly solving the identical problem)* | 1 |
| 3 | `trim_output_text` | yes | 1 | **0** | 2 |
| 4 | `make_concise` | yes | 1 | **0** | 3 |
| 5 | `reduce_response_length` | yes | 1 | **0** | 4 |
| 6 | `shorten_text_v2` | yes | 1 | **0** | 5 |
| 7 | `concise_formatter` | yes | 1 | **0** | 6 |
| 8 | `truncate_and_clean` | yes | 1 | **0** | 7 |
| 9 | `response_shortener_final` | yes | 1 | **0** | 8 |
| 10 | `minify_reply_text` | yes | 1 | **0** | 8 *(unchanged — cycle 2's miss didn't consume a slot)* |

**All 9 tracked cycles: streak = 0, throughout.** 9 completely distinct
names, zero repeats, zero convergence on any single implementation, and
the counter built to flag exactly this reports "calm" every time.

**Is the real current value of 0 meaningful?** For `response_shortening`
specifically: **no.** The real, live state (`self_edit_convergence.json`)
shows `cycles_attempted: 58`, `non_convergent_streak: 0`. Given the
mechanism just demonstrated, a `cycles_attempted` count this high with a
`non_convergent_streak` of exactly 0 is fully consistent with — and, given
the real 33-unique-names figure already on record for this family, most
likely caused by — the family having successfully deployed a
near-entirely-new implementation on nearly every one of those 58
cycles. The counter is not lying about what it measures; it is
measuring something that does not answer the question its own name
implies.

---

## 10. What the System Can and Cannot Currently Demonstrate

Kept deliberately separate, per the mission's own instruction not to
conflate these:

- **Generator performance**: the LLM can reliably produce syntactically
  valid Python containing a handful of control-flow constructs — 92% of
  real attempts clear a ceiling that's trivial to reach. This says
  almost nothing about whether the generated code is *good*; it says the
  generator can produce *something structurally busy enough to tie*.
- **Evaluator performance**: **demonstrated broken for its stated
  purpose.** It cannot distinguish correct-and-simple from
  broken-and-complex, confirmed directly against the current production
  file (7 structural nodes, score 4, genuinely broken by ordinary
  reading). This is the most severe, clearly-established finding in
  this investigation.
- **Gate performance**: **demonstrated correct.** The comparison logic,
  tie-acceptance, bootstrap handling, and fail-open exception path all
  behave exactly as their own code says they should. The gate is not
  broken; it is starved of a meaningful signal.
- **Convergence-detector performance**: **demonstrated to measure a
  real but narrow thing (per-cycle name-count delta) that does not
  answer "has this family settled on a good implementation."** Not
  broken relative to its actual, narrower definition — but that
  definition does not deliver what a reader of the variable's name would
  reasonably expect.
- **Deployment safety**: intact. F1 (pre-run AST scan for dangerous
  operations), F2 (sandboxed import test), and F3 (post-write AST
  rescan) have not been shown to have failed once in this investigation
  — nothing dangerous has been deployed, and the file's real defects
  (undefined names, duplicate definitions) are not the *kind* of thing
  these gates were built to catch (they check for *dangerous*
  operations and *parse* validity, not *logical correctness*).
- **Actual improvement in production behavior**: **cannot currently be
  demonstrated at all, in either direction, for a reason deeper than the
  metric problem** — the currently-deployed file doesn't define
  `apply_to_code`, so none of its code executes in the running system
  regardless of its quality. When `apply_to_code` *has* been defined
  (4 of the last 25 real deploys), a real, measurable, non-trivial
  activity level exists (1,985/3,196 real invocations actually changed
  something) — but whether those changes were improvements or the same
  class of corruption this project has already found once was not
  checked in this pass.

**Do not conflate "the safety gate prevented bad changes" with "self-edit
is incapable of improvement," per the mission's explicit instruction —
the correct statement is narrower and different from both: the safety
gates are working; the fitness gate is comparing on a dimension that
cannot express "improvement" once both sides are saturated; and even a
correctly-identified improvement would currently have no path to
mattering unless it also happens to define the one hook that gives this
file's code any real effect at all.**

---

## 11. Bugs vs. Design Decisions vs. Measurement Failures

- **Bug (evaluator)**: `_ast_complexity()` is used as a proxy for
  "quality" for the `coding`/`self_edit_coding`/`echo_projects_coding`
  task types, when it measures structural busyness, not correctness.
  This is the root defect.
- **Bug (evaluator, secondary)**: `_has_static_errors()` checks
  literal-division-by-zero only; it does not check for undefined names,
  duplicate top-level definitions, or attribute-existence — all three of
  which are real, present, currently-latent defects in the production
  reference file.
- **Bug (self_edit_generated.py itself)**: duplicate `run_code_generator`
  definition, a genuinely undefined `self` reference reachable via
  `AttributeError` (not the `NameError` originally claimed, though both
  failure shapes are real), and a complete absence of any `import`
  statement despite referencing four external names. All four are real,
  all four are currently dormant only because nothing in the trusted
  pipeline calls this file's functions automatically.
- **Design decision, working as intended**: the fitness gate's `<`
  comparison (ties pass), the `-1` bootstrap fallback, and the fail-open
  exception handling are all deliberate and defensible, and none of them
  are implicated in the 92%-success/all-ceiling pattern.
- **Design decision with an unstated cost**: `_record_convergence()`
  only running on successful deploys means the convergence tracker is
  structurally blind to rejection streaks — a reasonable scope choice at
  the time it was built, but one that leaves a real, currently-unfilled
  gap for tracking *rejection* churn specifically.
- **Measurement failure**: the success-path log line
  (`self_edit_manager.py:2135`) does not record `candidate_quality`/
  `current_quality`, unlike the rejection path. This is precisely the
  gap that caused the prior audit's central error, and it would cause
  the identical error for any future investigator using the same
  grep-based method.
- **Measurement failure (broader)**: nothing currently tracks whether a
  deployed version's `apply_to_code` hook (when defined) produces
  genuine improvements versus corruption — the 62% "changed: true" rate
  found in this pass has no accompanying quality judgment attached to it
  anywhere in the current instrumentation.

---

## 12. Recommended Experiments

Evidence-gathering only, nothing here implies a code change:

1. **Re-run this investigation's backup-scoring method against a wider
   historical window**, if older backups can be recovered from anywhere
   (git history of a fork, an older snapshot, etc.) — to establish
   *when* the file first reached the complexity ceiling, and whether it
   ever dipped below 4 after that point (this pass only has the 25 most
   recently retained backups; the true onset of ceiling-pinning is
   currently unknown).
2. **Directly test the "AttributeError vs NameError" reachability
   claim** by actually instantiating and calling the current
   `self_edit_generated.py`'s functions in a sandboxed subprocess (F2's
   own sandbox, not production) with representative inputs, to confirm
   which exception fires first exactly as this document predicts,
   rather than only reasoning about it from static structure.
3. **Sample and manually review a handful of real `apply_to_code`
   `changed: true` invocations** (the 1,985 found in §8) for genuine
   transformation quality versus corruption — directly analogous to
   Finding 28's own historical spot-check, at the current, much larger
   scale.
4. **Measure whether `_ast_complexity()`'s ceiling is reached this
   quickly for *ordinary*, non-self-edit-generated Python** (e.g., score
   a random sample of real files elsewhere in this codebase) — to
   establish whether "3+ structural nodes" is a generically low bar for
   any real function, or specific to the kind of code self-edit tends to
   generate.

---

## 13. Proposed Remediation Options — Recommendations Only, No Implementation

Not applied. Listed for a future, explicit, human-reviewed decision, per
this project's own standing discipline for anything touching self-edit's
scoring/training path:

- **Replace or supplement the coding quality metric** with something
  that can distinguish correct-and-simple from broken-and-complex —
  candidates include: actually executing the candidate (F2's sandbox
  already runs it for safety; nothing currently feeds a *correctness*
  result back into the score), a lightweight static check for undefined
  names/duplicate top-level definitions (closing the exact gap
  `_has_static_errors()` currently leaves open), or a real behavioral
  diff against the previous version's observable output for equivalent
  inputs.
- **Log `candidate_quality`/`current_quality` on the success path too**
  (`self_edit_manager.py:2135`), not only on rejection — the single
  smallest, safest fix that would have prevented this entire
  investigation's central error from being possible in the first place,
  and would make future audits of this system accurate by construction
  rather than by careful methodology alone.
- **Track rejection streaks separately from deploy-name-churn** — a
  second counter, updated on rejection specifically, distinct from
  `non_convergent_streak`'s current deploy-only scope, if "is this
  family stuck failing" is ever wanted as a real, answerable question.
- **Attach a quality judgment to `apply_to_code` invocations**, not just
  `changed: true`/`false` — closing the adjacent gap found in §8.
- **None of the above should be implemented without a shown diff and
  explicit sign-off**, consistent with how every other self-edit
  scoring/training change in this project's history has been handled.
