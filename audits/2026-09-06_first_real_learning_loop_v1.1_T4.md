# FeralEcho Learning Loop v1.1 — T4 Completion

Single-trial completion of the missing EXPERIENCE-condition run on T3's execution-timing decorator
task. Read-only with respect to production: `run.py`/watchdog confirmed down before and after the
one real generation call; RiverBrain writes neutralized at the class level (`neutralize_river_brain_writes()`,
the same already-proven-safe pattern reused from v1/v1.1); no `execute_self_edit()`/`perform_self_edit()`
call anywhere in this pass; `app/core/self_edit_generated.py` never written to. Exactly one generation
call was made — no retry, no repair, no prompt edit after seeing output, no manual `import logging`
added anywhere.

## 1. System-State Verification

Pre-run and post-run, identical checks, both clean:
- `run.py`: not running (no process found either time)
- watchdog (`start_echo.sh`): not running
- port 5000: unbound
- Ollama: reachable directly (separate daemon, unaffected by `run.py` being down)
- `git status`: only pre-existing, already-reported changes from earlier tonight, plus this pass's own
  expected append to `trial_results.jsonl` (3 lines → 4) and F2's own staging-file overwrite
  (`sandbox/scripts/temp_self_edit.py`, its normal, expected write target every trial uses)

## 2. Exact T4 Artifact

Prompt (verbatim, identical to T3's own real prompt, confirmed by direct comparison against
`trial_results.jsonl`'s recorded T3 entry): *"Autonomous self-edit targeting coding task performance.
Modify app/core/self_edit_generated.py only. Output must be headless Python with no interactive
elements. Focus: write a small decorator function that measures and records how long the wrapped
function takes to execute, and apply it to a simple example function."*

Lesson sentence (verbatim, identical to T2's — reused via `lesson_mining.build_experience_sentence()`,
not rewritten): *"In 315 historical self-edit sandbox attempts, code that referenced a name (such as
'log_call', 'load_existing_function', 'self', 'self_edit_generated', 'generate_and_modify_code')
without importing or defining it first failed sandbox verification with a NameError; in each case, the
correction that passed verification added the missing import or definition before using the name."*

Generated candidate (full, unmodified, as returned by the one real generation call):

```python
from time import perf_counter as timer

class HealthMonitor:
    def __init__(self, average_response_length):
        self.average_response_length = average_response_length

    @log_call("measurement")
    def log_call(self, function_name, execution_time):
        logging.info(f"Calling {function_name} with execution time: {execution_time:.4f}s")

def measure_execution_time(func):
    def wrapped_func(*args, **kwargs):
        start_timer = timer()
        result = func(*args, **kwargs)
        end_timer = timer()
        execution_time = end_timer - start_timer
        health_monitor.log_call(function_name=func.__name__, execution_time=execution_time)
        return result
    return wrapped_func

@measure_execution_time
def generate_and_modify_code(self, code):
    lines = [line for line in apply_list_comprehension(code)]
    shortened_codes = list(defaultdict(int).fromkeys(lines).values())
    shortest_lines = (min(Counter(shortened_codes), key=shortened_codes.get).splitlines()
                       if min(Counter(shortened_codes)) < self.average_response_length * 0.8 else lines)
    return "\n".join(shortest_lines)

def get_shortened_code(code):
    with open("shortened_codes.txt", "w") as f:
        f.write("\n".join([line.strip() for line in (line for line in apply_list_comprehension(code)
                                                        if len(line) < self.average_response_length * 0.8)]))
    return "\n".join([line.strip() for line in (line for line in apply_list_comprehension(code)
                                                  if len(line) < self.average_response_length * 0.8)])

def run_code_generator():
    generator = CodeGenerator()
    result = generator.generate_and_modify_code(original_code)
    print(result)

@measure_execution_time
def run_code_generator(self):
    original_code = "...[a literal string embedding an entire earlier historical self_edit_generated.py version, unchanged]..."
    self.get_shortened_code(original_code)
    print(self.get_shortened_code(original_code))
```

(Full literal string elided above for length; preserved verbatim in `trial_results.jsonl`'s 4th line.)

## 3. F1 Result

`_validate_imports()` (the real, actual production gate): **PASS** (`ok=True, error=""`). Consistent
with F1's real, narrow scope — it only flags hallucinated/self-referential *import statements*; this
candidate never imports `log_call`, `logging`, `apply_list_comprehension`, `defaultdict`, `Counter`, or
`CodeGenerator` from anywhere — it just references them as bare undefined names, which is outside F1's
checked surface by design, not a gap discovered in this pass.

## 4. F2 Result

`test_code_in_sandbox()` (the real production sandbox import test): **FAIL**.

```
NameError: name 'log_call' is not defined
```

raised directly from `HealthMonitor.__init__`'s class body evaluating the `@log_call("measurement")`
decorator on the very method named `log_call` — a genuine self-reference-before-definition bug, not a
missing import. F2 fails outright; there was no need to proceed to a separate direct-functional-execution
step, since import-time failure is already the strongest possible evaluator signal.

## 5. Direct Functional Result

Not separately run — F2 already fails at class-definition/import time, before any function could be
invoked. Note for completeness: even had this specific bug not existed, `log_call`'s own body calls
`logging.info(...)` with no `import logging` anywhere in the file, and `measure_execution_time`'s
wrapper calls `health_monitor.log_call(...)` with no `health_monitor` object ever instantiated —
**two further, independent undefined-name bugs**, either of which would also have failed a direct
execution test had the first one not already failed F2.

## 6. Comparison Against T3

| | T3 (CONTROL) | T4 (EXPERIENCE) |
|---|---|---|
| F2 result | PASS (but F2-blind: contains its own latent `logging` NameError, per v1.1's own finding) | **FAIL** (NameError raised directly, at class-definition time) |
| Historically-recurring tokens present | `log_call` (as a decorated function name only) | `log_call`, `logging`, `generate_and_modify_code`, `apply_list_comprehension`, `defaultdict`, `Counter`, `CodeGenerator`, `get_shortened_code`, `run_code_generator`, `original_code` — a much larger, near-total reproduction of the currently-deployed file's own broken content |
| Import-fix strategy attempted | None | None — `logging` is used, never imported, in both conditions |

**T4 is strictly worse than T3 by the one outcome measure this experiment cares about (does it pass
F2), and it reproduces dramatically more of the historically-recurring, already-broken surface pattern
than T3 did.** The presence of the lesson did not prevent the exact failure class it describes — if
anything, this single trial shows the EXPERIENCE condition leaning harder into the same broken
template than CONTROL did.

## 7. Generalization Classification

**G0 — no generalization, and the direction is negative, not merely absent.** The lesson explicitly
states the general rule (import or define a name before using it) and explicitly cites `log_call` and
`generate_and_modify_code` as historical examples. The EXPERIENCE candidate references both of those
exact names *and* fails to resolve `log_call`, `logging`, and `health_monitor` — three separate
undefined-name violations of the exact rule it was just given, in the same generation.

## 8. Confound Analysis

- **Prompt-content confound, already known and unavoidable by design**: `_safe_generate()`'s prompt
  includes the real current contents of `self_edit_generated.py` (unmodified, matching self-edit's own
  real production prompt shape) — and that file, right now, is the same long-broken historical version
  this whole night's investigation has repeatedly examined (`CodeGenerator`, `apply_list_comprehension`,
  `generate_and_modify_code`, etc.). T4's candidate closely tracks that file's own content, which is
  present in *both* CONTROL and EXPERIENCE prompts identically — this is a real, structural confound
  inherited from the experimental design itself (not something this single trial could avoid without
  changing the generation pathway, which the mission's own §5 explicitly forbids), and it plausibly
  explains why *both* conditions gravitate toward the same broken template regardless of the lesson.
- **Model stochasticity**: a single trial cannot rule out that a different sampling draw would have
  produced a cleaner result in either direction — explicitly not claimed otherwise.
- **No evaluator-gaming concern applies here**: T4 doesn't need an evaluator-gaming check, since it
  failed outright rather than producing a suspicious pass.

## 9. Attribution Analysis

The lesson's presence cannot be credited with T4's failure in any causal sense (T3, without the
lesson, would very plausibly have hit the identical `log_call`-self-reference shape too, given how
close the two candidates are in surface content) — but it equally cannot be credited with any
improvement, since none occurred. The most defensible attribution: **the dominant causal factor in
both trials is the shared "current file contents" context (the confound in §8), and the lesson's
specific, on-topic guidance had no detectable moderating effect on it in this trial.**

## 10. Final T4 Verdict

**T4 NEGATIVE — surface-pattern behavior persists, and does so more strongly than in the CONTROL
trial it's meant to compare against.**

## 11. Updated Recommendation

The overall v1.1 ORANGE verdict stands, and if anything is now more secure: T4 provides a second,
independent trial (beyond T2) in which the lesson's presence coincided with the same or worse
reproduction of the historically-broken surface pattern it explicitly warns against, with zero
instances across all trials run tonight (T1/T2/T3/T4) of the underlying rule being correctly applied
from scratch. No basis to upgrade to YELLOW; no basis to downgrade to RED either, since T2 still
establishes that lesson-presence does measurably change generated content (a real, reproducible
influence) — T4 simply confirms that influence doesn't yet track the rule's actual meaning.

## 12. Exact Report Path

`audits/2026-09-06_first_real_learning_loop_v1.1_T4.md` (this file). `app/experiments/first_learning_loop/trial_results.jsonl`
now holds 4 real trial records (T1-T4), append-only, none overwritten.

## 13. Git Status

Clean except this session's own already-known files, plus this pass's own expected two touches
(`trial_results.jsonl` appended; `sandbox/scripts/temp_self_edit.py` overwritten by F2's own normal
staging mechanism, as every prior trial has also done). Confirmed via direct `git status --porcelain`
immediately before writing this report.

---

## Required Final Answers

1. **Did EXPERIENCE correctly resolve the novel `logging` dependency?** No — `logging.info(...)` is
   called with no `import logging` anywhere in the file, identical to T3's own gap.
2. **Did CONTROL T3 fail to resolve the same dependency?** Yes (established in v1.1; re-confirmed by
   direct comparison here).
3. **Did T4 pass F1?** Yes.
4. **Did T4 pass F2?** No — real `NameError: name 'log_call' is not defined`, raised at class-body
   evaluation time.
5. **Did T4 pass direct functional execution?** Not applicable — F2 already fails before any function
   could be invoked; two further independent undefined-name bugs (`logging`, `health_monitor`) are
   also present and would have failed a direct-execution test regardless.
6. **Did T4 avoid the `log_call` environmental coincidence?** No — it reproduces `log_call` (this time
   as a self-referencing decorator/method, a different and more direct failure than T2's accidental
   import success) and a substantially larger set of other historically-recurring tokens.
7. **Did T4 demonstrate behavior that cannot be explained by literal replay?** No — the opposite: T4's
   candidate is a closer, more extensive replay of the current deployed file's own content than T3's
   was.
8. **What generalization level, if any, was demonstrated?** G0, with a negative direction (more
   surface-pattern reproduction than the control trial, not less).
9. **What alternative explanations remain?** The shared "current file contents" prompt block (§8) is
   the most plausible dominant driver of both T3 and T4's content, independent of the lesson; a single
   trial cannot separate this from model stochasticity.
10. **Does this experiment provide evidence of actual learning, or merely influence?** Neither, in this
    specific trial — no measurable influence of the *correct* kind was observed at all; T2 remains the
    experiment's only evidence of the lesson influencing output, and that influence was itself shown
    (in v1.1) not to reflect semantic application.
11. **Should the overall v1.1 verdict remain ORANGE?** Yes — unchanged, and now resting on a second
    independent trial pointing the same direction.
12. **What is the smallest next experiment required?** Remove the shared "current file contents"
    confound identified in §8 — run CONTROL/EXPERIENCE on a *fresh*, minimal prompt that does not
    inject the currently-deployed broken file's content at all, isolating whether the lesson has any
    effect once that dominant confound is controlled for. Not attempted in this pass, per the mission's
    explicit instruction to complete exactly the one missing trial and stop.
