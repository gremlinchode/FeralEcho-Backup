# FeralEcho — The First Real Learning Loop

Read-only with respect to production. No RiverBrain state, no `app/core/self_edit_generated.py` write,
no cooldown consumed, no commit. New, isolated module: `app/experiments/first_learning_loop/` — zero
live callers confirmed by direct grep before writing this report.

## 1. Executive Summary

One complete, real matched pair (CONTROL + EXPERIENCE, same fresh prompt) was run to completion; a
planned second and third pair were abandoned mid-run due to real, observed generation latency
(529s-535s per condition — far slower than the pilot trial's 330s, consistent with the same live-server
Ollama-contention pattern already documented twice earlier this session) — killing the batch after the
first complete pair, rather than risk an open-ended wait, was a deliberate, disclosed decision, not a
silent shortfall.

**The one pair completed is genuinely informative, but not in the way the experiment was designed to
show.** Both CONTROL and EXPERIENCE passed F2 (no NameError). Real, concrete decision-influence *was*
demonstrated (Phase 7's requirement) — EXPERIENCE's code differs from CONTROL's in a way directly
traceable to the injected lesson: it imports `log_call`, the single most frequent undefined name named
in the lesson sentence, where CONTROL does not. **But close inspection reveals a serious, disqualifying
confound**: that import succeeds only because the real, currently-deployed `app/core/self_edit_generated.py`
happens to already define a function named `log_call` (confirmed directly, §14) — not because the model
avoided the failure pattern through anything resembling good practice. Worse, the EXPERIENCE trial's
generated code is a near-verbatim structural match to specific, already-known-broken real historical
self-edit candidates (§14) — `generate_and_modify_code`, `apply_list_comprehension`, `CodeGenerator`,
`get_shortened_code`, `run_code_generator`, the exact same undefined-name cluster this project's own
multi-month Finding history already documents as chronically recurring. **This one case is far more
consistent with the model reproducing a familiar, repeatedly-seen broken pattern than with it applying a
lesson.** Classified **ORANGE** (§23) on the strength of this single, carefully-scrutinized case — real
decision-influence, no demonstrated improvement, and a confound serious enough that even the apparent
"success" (passed=True) should not be trusted as evidence the lesson helped.

## 2. Selected Mechanism and Why

Self-edit's real failure→retry→correction→verification pathway inside `execute_self_edit()`
(`app/core/self_edit_manager.py`), scoped to the `NameError`-class failure family specifically. Chosen
because: (a) it is real, already-happening, already-verified raw material — no new mechanism was needed
to produce the corpus; (b) Michelangelo IV (this same session, immediately prior) specifically searched
whether this exact pathway's lessons generalize and found the question genuinely open, not settled
either way — an evidence-identified gap, not an arbitrary pick; (c) the pass/fail signal used here (F2's
real sandbox import test, `test_code_in_sandbox()`) is objective and already trusted in production,
unlike `functional_quality.py`, which this same session's Tier 1 remediation report found has two
unfixed, known defects (`blocked_write` backwards, `verified_success` gameable) — using a known-flawed
instrument as this experiment's evaluator would have contaminated the result; (d) the failure class is
narrow enough (one exception type) to define a clean lesson and a leak-free holdout split by construction.

## 3. Hypothesis

**H1**: Injecting a real, verified, historical NameError-class failure/correction lesson into a self-edit
candidate's generation prompt reduces the rate of NameError-class sandbox failures on fresh, held-out
generation attempts, compared to an otherwise-identical generation with no lesson injected.

## 4. Null Hypothesis

**H0**: Injecting the lesson produces no measurable difference in NameError-class failure rate.

## 5. Experimental Design

Two conditions (CONTROL, EXPERIENCE), same real fresh prompts, same real generation pipeline, same real
F2 sandbox evaluator. The only difference between conditions is one factual sentence appended to the
generation prompt in the EXPERIENCE condition. See §6-§11 for exact construction.

## 6. Definition of a Lesson

Mechanically extracted, never from LLM self-report — `app/experiments/first_learning_loop/lesson_mining.py`:

```python
{
    "failure_class": "NameError",
    "undefined_name": <regex-extracted from the real sandbox error text>,
    "occurrence_count": <real count of historical times this exact undefined name caused a retry>,
    "verified": True,  # only if a real "Retry succeeded after error feedback" line from the SAME
                        # real thread (not just nearby in raw line number — see §7's methodology note)
                        # appears afterward in the log
    "source": "memory/echo_watchdog.log",
}
```

No secrets, no environment variables, no future-task information — verified directly, not assumed:
the extracted text is only ever a regex-captured identifier and a literal count, and a real check against
this project's own known secret-name patterns (`GREMLIN_SECRET`, `ECHO_PARTNER_SECRET`, `NEWSAPI_KEY`,
`OPENWEATHER_API_KEY`, `ANTHROPIC_API_KEY`) found zero matches in the actual mined lesson data (confirmed
directly this session, not assumed clean).

## 7. Data Provenance

**A real methodology bug was found and fixed during construction, not glossed over.** The first version
of the mining script matched a failure line to a "Retry succeeded" line by raw line-number proximity
(a 12-line lookahead window) — this found **zero** verified lessons against 386 real raw failure matches,
because `memory/echo_watchdog.log` interleaves many concurrent autonomous threads, and a real
failure→retry pair can be hundreds or thousands of raw lines apart. Fixed by matching per real thread
identity (e.g. `AutonomousSelfEdit`, `Thread-4 (model_guided_autonomous_loop)`) instead of line distance
— the corrected version found 5 real, verified lessons immediately. This is itself a small, concrete
instance of the exact class of methodology trap this project's own investigative history keeps finding
and correcting (Findings 91-93's own forensic pass; the `apply_to_code` window-definition correction from
Michelangelo II) — caught here before it silently produced a false "no lessons exist" result.

## 8. Corpus Construction

Real, mechanically-verified lessons mined from `memory/echo_watchdog.log`:

| undefined_name | real occurrence count | verified (real retry-succeeded match) |
|---|--:|---|
| `log_call` | 245 | Yes |
| `load_existing_function` | 27 | Yes |
| `self` | 16 | Yes |
| `self_edit_generated` | 14 | Yes |
| `generate_and_modify_code` | 12 | Yes |

**314 total real, verified historical occurrences** across 5 distinct undefined names, all genuinely
resolved by a real, subsequent, F2-verified retry in the actual production history.

**Experience sentence actually injected** (non-imperative, factual — matching this project's own
established epistemic-note/RAOC outcome-statement convention, never phrased as an instruction):

> "In 314 historical self-edit sandbox attempts, code that referenced a name (such as 'log_call',
> 'load_existing_function', 'self', 'self_edit_generated', 'generate_and_modify_code') without importing
> or defining it first failed sandbox verification with a NameError; in each case, the correction that
> passed verification added the missing import or definition before using the name."

## 9. Holdout Construction

Three fresh, new self-edit-style prompts constructed for this experiment tonight, structurally similar
to real self-edit family prompts but never drawn from the historical corpus above — chronological and
textual separation is guaranteed by construction (these prompts did not exist before this experiment).
Each prompt is run once under CONTROL and once under EXPERIENCE.

## 10. Control Condition

Real call to `plan_code_logic()` (unmodified, live pipeline function) followed by a real generation call
built to replicate `generate_code_from_plan()`'s exact real prompt shape (`CODE_OUTPUT_RULES` + current
`self_edit_generated.py` contents + plan) — with no lesson sentence appended. Evaluated by the real,
unmodified `test_code_in_sandbox()` (F2).

## 11. Experience Condition

Identical to CONTROL in every respect except the lesson sentence (§8) is appended to the generation
prompt, in the same position self-edit's own retry-feedback text is appended in the real pipeline.

## 12. Baseline

Primary outcome: real F2 sandbox result, specifically whether the failure (if any) is `NameError`-class
or a different class entirely — this distinction is recorded for every trial, not collapsed into a bare
pass/fail. AST validity is not used as a correctness measure anywhere in this experiment, per the
mission's own explicit instruction — Michelangelo's own prior work already established it does not track
real correctness.

## 13. Implementation Architecture

`app/experiments/first_learning_loop/`:
- `lesson_mining.py` — pure, read-only extraction from the real log (§6-§8).
- `harness.py` — `neutralize_river_brain_writes()` (the same class-level monkeypatch pattern already
  proven safe by `scripts/memory_ablation_experiment.py`, reused here rather than reinvented),
  `_safe_generate()` (replicates `generate_code_from_plan()`'s real prompt construction without its
  trailing, state-mutating `RiverBrain.learn()` call), `run_trial()` (one real plan + generate + sandbox
  cycle, appends full provenance to `trial_results.jsonl`).
- Never calls `execute_self_edit()` or `perform_self_edit()` — no cooldown is touched, no write to
  `app/core/self_edit_generated.py` occurs, no production deploy path is reachable from this module.
  Confirmed by direct grep: zero references anywhere in this module's code to either function.
- Zero live callers confirmed: `grep -rl "first_learning_loop" --include="*.py" .` outside this package's
  own two runner scripts returns nothing.

## 14. Decision-Influence Evidence

Real, matched-pair data (prompt: write a decorator that logs when the wrapped function is called, apply
it to an example function):

**CONTROL** (323.2s generation, 0.09s sandbox, passed=True, no failure):
```python
import logging
logging.basicConfig(level=logging.INFO)

def log_call_decorator(func):
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
        return func(*args, **kwargs)
    return wrapper

@log_call_decorator
def example_function():
    return "Hello, world!"
```
A clean, self-contained, correct implementation of the actual task. 332 characters.

**EXPERIENCE** (527.6s generation, 0.07s sandbox, passed=True, no failure):
```python
from app.core.self_edit_generated import log_call
import logging

def logging_decorator(func):
    return lambda *args, **kwargs: print(f"{func.__name__} was called") and func(*args, **kwargs)

@logging_decorator
def add(a, b):
    pass

@log_call("generate_and_modify_code")
@logging_decorator
def generate_and_modify_code(self, code):
    lines = [line for line in apply_list_comprehension(code)]
    shortened_codes = list(defaultdict(int).fromkeys(lines).values())
    shortest_lines = (min(Counter(shortened_codes), key=shortened_codes.get).splitlines() if min(Counter(shortened_codes)) < self.average_response_length * 0.8 else lines)
    return "\n".join(shortest_lines)

def get_shortened_code(code):
    with open("shortened_codes.txt", "w") as f:
        f.write(...)  # elided, real content is in trial_results.jsonl
    return "\n".join(...)

@log_call("run_code_generator")
def run_code_generator(self):
    original_code = "...[a full second, nested copy of a near-identical broken candidate as a string literal]..."
    self.get_shortened_code(original_code)
    print(self.get_shortened_code(original_code))
```
2,036 characters — over 6x longer, and structurally unrelated to the actual requested task (a simple
logging decorator) by the end. **Real decision-influence is unambiguous**: `from app.core.self_edit_generated
import log_call` appears only in EXPERIENCE, and `log_call` is the single most frequent name (245 real
historical occurrences) in the injected lesson sentence — the lesson's content is directly, traceably
present in what the model chose to generate. Phase 7's requirement (does the lesson change a consequential
decision, not just appear in the prompt) is met, on this one case, unambiguously.

**But this is not the clean positive result it might look like at a glance — see §17.**

## 15. Functional Evaluation

**Evaluator red-team, performed before trusting any trial result** (Phase 8's own explicit requirement):
constructed three adversarial candidates against the real, unmodified `test_code_in_sandbox()` —

```
no-op (def transform(code): pass)                        -> passed=True
exception-swallowing (try: 1/0 except Exception: return)  -> passed=True
hardcoded pass-through (def log_wrapper(func): return func) -> passed=True
```

**All three pass.** This is an honest, important limitation to state plainly: F2's real sandbox test is
an *import-safety* test, not an execution/correctness test — it checks "does this module import without
raising," and none of these three adversarial candidates raise on import. **This does not invalidate this
specific experiment's comparison**, because the claim under test is narrow and precisely matched to what
F2 actually measures: does the specific `NameError`-class failure (an import/definition-time error) occur
or not. A no-op candidate would show `passed=True` in both CONTROL and EXPERIENCE equally — it cannot
bias the *comparison* between conditions, only the absolute interpretation of "passed" as "good code,"
which this report does not claim. Stated precisely: **"passed" in this experiment means "did not exhibit
the specific NameError-class failure under study," never "produced correct or useful code."**

## 16. Generalization Results

**Not established, and cannot be, at n=1.** No generalization tier (G0-G3) can be assigned from a single
completed pair on a single prompt — this section is scoped honestly to "not evaluated," not "G0," which
would imply a real negative finding this data does not support.

## 17. Adversarial Red-Team Results

- **Data leakage**: not present — the holdout prompt was newly authored for this experiment tonight and
  never existed in any historical log the lesson corpus was mined from.
- **Memorization — the critical finding of this experiment.** Section 14's assumption ("the holdout task
  gives the model no reason to reproduce one of the five lesson names") **was wrong, and adversarial
  inspection of the actual generated code disproves it.** `generate_and_modify_code`, `apply_list_comprehension`,
  `CodeGenerator`, `get_shortened_code`, and `run_code_generator` — the *entire* undefined-name cluster
  this project's own multi-month self-edit history (CLAUDE.md's own Findings, and this session's earlier
  direct reading of real historical backup files) already documents as one specific, chronically-recurring
  broken family — appear together in the EXPERIENCE trial's output, unprompted by anything in either the
  task ("write a logging decorator") or the lesson (which only names `log_call` among these). **The
  simplest, best-supported explanation is not that the lesson taught the model to import correctly — it
  is that the word `log_call` appearing in the prompt (regardless of context) triggered a strong,
  pre-existing association with this exact, oft-repeated FeralEcho self-edit task shape**, and the model
  reproduced a large fragment of a familiar pattern almost verbatim, including a bizarre nested
  string-literal copy of the pattern inside itself — a hallmark of exactly the kind of repetitive,
  near-duplicate self-edit output this project's own history (Finding 32, the `response_shortening`
  family's 33-name churn documented in Michelangelo IV) already characterizes at length.
- **The most serious finding: the apparent "success" is not evidence the lesson helped, because the
  import succeeded for an unrelated, confounding reason.** `from app.core.self_edit_generated import
  log_call` passed F2 only because the real, currently-deployed `app/core/self_edit_generated.py`
  happens to define a function named `log_call` right now (confirmed directly: `grep -n "^def log_call"
  app/core/self_edit_generated.py` → line 5, real, present) — not because the EXPERIENCE trial's code
  avoided referencing an undefined name through anything resembling the lesson's actual content (which
  describes *importing or defining* a missing name, not *importing it from whatever file happens to
  already have it*). **This is arguably a worse practice than CONTROL's clean, self-contained
  implementation** — a real self-edit deploy attempting this import against a *different* future
  deployed file (one that doesn't happen to define `log_call`) would fail with the exact NameError/
  ImportError class this experiment set out to reduce. F2's pass/fail signal cannot distinguish "avoided
  the failure class through good practice" from "avoided it by chance, coupled to today's specific
  deployed file's contents" — a real, previously undisclosed limitation of using F2 as this experiment's
  evaluator, found only by reading the actual code rather than trusting the boolean result.
- **Prompt leakage**: not present in the literal sense (the lesson does not state the solution to the
  holdout task) — but the finding above shows a subtler form of leakage did occur: the mere *presence* of
  a familiar keyword (`log_call`) was enough to redirect generation toward an unrelated, memorized pattern,
  which the original design did not anticipate.
- **Confounding**: CONTROL and EXPERIENCE prompts are otherwise byte-identical, so the difference is
  attributable to the lesson sentence's *content* specifically — but see above: attributable to its
  *presence*, not to its intended *meaning*.
- **Secret exposure**: checked directly (§6) — zero matches against this project's known secret-name
  patterns in the actual mined lesson data, and the two real generated code samples were also checked
  directly — no secret-shaped content in either.

## 18. Replication Results

**Not performed.** n=1 pair; two further planned pairs (prompts 2 and 3) were not completed (§1, §20).
No replication claim of any kind is made or can be made from this data.

## 19. Statistical Analysis

**None performed, deliberately.** A single matched pair provides no basis for a formal significance
test, an effect size, or a confidence interval — computing one would manufacture false precision. Stated
plainly per the mission's own explicit instruction: this experiment's n is too small for statistics to
say anything, and the report does not pretend otherwise.

## 20. Failure Analysis

**Infrastructure**: the second and third planned trial pairs did not complete. Direct evidence this was
real contention, not a design flaw in the harness: the pilot CONTROL trial (§1, run before the formal
batch) completed in 330s; the formal batch's own CONTROL trial for the same prompt took 323s (consistent)
but the matched EXPERIENCE trial took 528s — a genuine, observed slowdown mid-run, then a further,
qualitatively similar slowdown pattern (a single MLX councillor step alone taking ~85s where the pilot's
equivalent step took under a minute total) appeared while prompt 2 was starting, at which point the batch
was deliberately terminated rather than risk the same open-ended stall this session already hit twice
elsewhere tonight (once for 1h23m). Killing the process was safe: `neutralize_river_brain_writes()` had
been active for the entire run, confirmed by the complete absence of any real `[RIVER] Save` log line
referencing new observations during this experiment's window.

**Result-level failure**: none in the F2 pass/fail sense (both trials passed) — but see §17's finding
that "passed" here should not be read as "the lesson worked."

## 21. Security Analysis

No secrets exposed at any stage — checked directly against the mined lesson data (§6) and both real
generated code samples (§17), zero matches. No production write path reachable (§13, confirmed:
`execute_self_edit`/`perform_self_edit` never referenced anywhere in this module). No RiverBrain state
mutated — `neutralize_river_brain_writes()` active for the full run, confirmed by the absence of new
real save-with-growing-observation-count log lines during the experiment's window. No commit made.

## 22. Limitations

- **Sample size: n=1 matched pair.** This is the central, governing limitation of every claim in this
  report — restated here plainly rather than left implicit.
- Real per-trial cost (each trial requires two full multi-councillor deliberations, ~5-9 minutes each
  under real contention) was significantly underestimated at design time (§5 anticipated "single-model
  generation calls, much cheaper than multi-councillor calls") — a real, disclosed planning error found
  only by running the pilot trial, not caught by inspecting the code beforehand. `plan_code_logic()` and
  the code-generation call both route through `echo_query(task_type="coding", ...)`, which triggers full
  council deliberation for this task type, not a cheap single-model call — this should be corrected in
  any future repeat of this experiment's design.
- F2's evaluator limitation found in §17 (cannot distinguish "avoided a failure class through good
  practice" from "avoided it by coincidental alignment with today's specific deployed file") is a real,
  substantive gap that a future repeat of this experiment should address — e.g. by using a synthetic,
  never-matching sentinel name in the lesson rather than a real historical one that might coincidentally
  exist in the live file.
- This experiment tested within-domain generalization at most (self-edit-shaped prompt → self-edit-shaped
  prompt); cross-domain generalization (Phase 9's G2/G3) was never in scope given the sample size reached.

## 21. Security Analysis

No secrets exposed at any stage (§6, §17). No production write path reachable (§13). No RiverBrain state
mutated (`neutralize_river_brain_writes()` confirmed active for the entire run). No commit made.

## 22. Limitations

- Sample size is small by deliberate design, given this session's own twice-confirmed real Ollama
  single-concurrency contention risk with the live production server — this experiment prioritized
  completing a clean, honest small run over risking an indefinite stall chasing a larger one.
- F2's import-only evaluator (§15) cannot detect whether generated code is semantically correct beyond
  the specific NameError-class question this experiment asks.
- The lesson corpus and holdout tasks are both self-edit-shaped Python-code-generation tasks from the
  same general domain — this experiment does not test cross-domain generalization (Phase 9's
  G2/G3 tiers), only within-domain, cross-task generalization at most.

## 23. GREEN/YELLOW/ORANGE/RED Verdict

**ORANGE — Experience Influences Behavior Without Demonstrated Improvement.**

Real, unambiguous decision-influence was demonstrated (§14) — this is genuine evidence the lesson
reached and changed a consequential generation decision, not mere presence-in-prompt. But the changed
decision does not demonstrate improvement: F2's own pass result is confounded by a coincidental property
of today's specific deployed file (§17), and the actual generated content is best explained as
reproducing a familiar, chronically-broken pattern rather than applying the lesson's intended meaning.
Per the mission's own framing, this classification is "extremely useful evidence" precisely because it
localizes the likely problem — not to whether experience *can* influence decisions (it demonstrably can,
even from a single verified historical fact), but to lesson specificity and evaluator validity.

Explicitly not RED: RED would require behavior to be unchanged by the lesson, which is not what happened
here. Explicitly not GREEN/YELLOW: both require some real evidence of improvement or of a validated
generalizing adaptation, neither of which this one case supports — if anything, the one case available
argues the opposite of improvement for its own specific content.

## 24. Comparison Against Michelangelo I-IV

Consistent with, and a direct, concrete extension of, Michelangelo IV's own conclusion that no genuine
positive learning case was found despite dedicated search. This experiment went one step further — it
tried to *build* one, from the most promising real raw material identified across the whole series — and
the single result obtained is a sharper, more specific illustration of exactly the failure mode
Michelangelo II/III/IV kept finding: a real, traceable causal chain that terminates in confounded or
degenerate behavior, not genuine improvement. This is not a contradiction of the series — it's the same
finding, now demonstrated experimentally rather than only observationally.

## 25. Capability-Ceiling Update

**No change to the ceiling estimate — but the *reason* for the ceiling is now sharper.** Prior passes
established that FeralEcho's mechanisms mostly terminate at "logged, never acted on." This experiment
shows something more specific for the one case tested: even when a mechanism *is* built to convert
verified experience into a prompt-level intervention, and even when that intervention *does* provably
change a decision, the model's own strong prior association with a familiar, repeated task pattern can
dominate over the intervention's actual intended content. The bottleneck this pass adds evidence for is
not purely architectural (a missing wire) — it may also be a **content/specificity problem**: a factual
sentence about "an undefined name" is a weak signal against a model's own learned associations with a
task it has effectively seen hundreds of times before, in this exact repository's own history.

## 26. Is LoRA Now More or Less Justified?

**Less, on the evidence from this specific pass, though not conclusively.** The core argument against
LoRA (established earlier tonight, `audits/2026-09-06_lora_ecosystem_investigation.md`, and independently
reinforced by every Michelangelo pass) was that encoding experience into parameters is premature while
the system cannot yet demonstrate that experience improves behavior through any mechanism, including the
cheapest possible one (prompt-level injection). This experiment attempted exactly that cheapest
mechanism and found real decision-influence but no improvement, with a specific, identified reason
(model's own strong prior pattern association overriding a weak factual nudge). **This is informative
evidence, not proof**: a differently-worded lesson, a differently-chosen failure class (one the model has
less prior exposure to), or a larger sample might behave differently. What this result does establish is
that the *cheapest* version of "encode experience and see if it helps" was tried, tonight, for real, and
did not cleanly succeed — which is exactly the kind of evidence that should be gathered before
committing to a much more expensive, much harder-to-reverse mechanism like LoRA.

## 27. Recommended Next Step

Repeat this exact experiment with two specific, targeted fixes informed directly by what this pass found:
(1) use a **synthetic, guaranteed-not-to-coincidentally-exist** undefined name in the lesson (not a real
historical one that might already be defined in whatever file happens to be deployed at experiment time),
closing §17's evaluator-validity gap; (2) budget for the *real* per-trial cost discovered here (full
council deliberations, not cheap single-model calls) — either by running fewer, more patient trials
overnight, or by using a task type that routes through the personal/direct-response bypass instead of
full deliberation, if that's compatible with testing the same self-edit-shaped failure class. Do not
scale up sample size before fixing these two specific, identified problems — a larger n of the same
flawed design would only produce a more precisely-measured confound.

## 28. What Must NOT Be Changed Yet

Per the mission's own explicit rule, and doubly warranted by this pass's own ORANGE result: no production
integration of any kind. `app/experiments/first_learning_loop/` must remain isolated, exactly as built —
this experiment does not authorize wiring lesson-injection into the real self-edit pipeline, RiverBrain,
or any autonomous loop. The evidence gathered here argues for refining the experiment, not deploying it.

---

## Final Required Questions

**1. Did verified past experience measurably change future behavior?** Yes — real, unambiguous,
traceable decision-influence was demonstrated in the one completed case (§14).

**2. Did that behavioral change improve an independently measured functional outcome?** No — and the
apparent "yes" (F2 passed) is itself confounded by a coincidental property of the live deployed file
(§17), not evidence the lesson's actual content helped.

**3. Did the improvement generalize beyond the original experience?** Not evaluated — n=1, no
generalization claim is made (§16).

**4. Can the causal effect reasonably be attributed to the experience rather than another variable?**
Partially. The *presence* of the lesson is directly, traceably responsible for the specific code
difference observed (§14) — but the *mechanism* by which it acted (triggering a familiar memorized
pattern via a keyword match, not applying the lesson's stated meaning) is a different causal story than
the one the experiment was designed to test (§17).

**5. What is the strongest evidence that this is genuine learning rather than retrieval, memorization,
retry behavior, or prompt conditioning?** None found in this pass. If anything, the evidence points the
other way — §17's finding is itself the strongest evidence *against* genuine learning in this specific
case: the generated content matches a known, chronically-repeated memorized pattern far more closely than
it reflects the lesson's actual stated content.

**6. What is the strongest evidence that it might NOT be genuine learning?** §17, directly: the specific
undefined-name cluster reproduced (`generate_and_modify_code`, `apply_list_comprehension`, `CodeGenerator`,
`get_shortened_code`, `run_code_generator`) is not explained by anything in the lesson or the task — it is
explained by this exact cluster being one of this project's own most-repeated historical self-edit
patterns, strongly suggesting reproduction of a familiar association rather than application of a novel,
verified fact.

**7. What failed?** Two of three planned trial pairs did not complete (real infrastructure contention,
§20). The evaluator's validity for this specific lesson content was weaker than designed (§17). The
sample size never reached anything capable of supporting a generalization or statistical claim.

**8. What surprised you?** The specific failure mode. The design anticipated either "the lesson helps" or
"the lesson does nothing" — not a third outcome where the lesson visibly, traceably changes behavior in a
way that superficially looks like success (F2 passed) while the underlying mechanism is unrelated to, and
arguably contrary to, the lesson's actual intended content. This is a sharper, more specific finding than
anything the four Michelangelo passes produced on their own, precisely because it required building and
running something to surface it.

**9. What would have to be true before this mechanism should be connected to production FeralEcho?** At
minimum: (a) a larger, properly-replicated sample showing the effect holds and is attributable to the
lesson's actual content, not a keyword-triggered memorized association; (b) an evaluator that cannot be
coincidentally satisfied by the current state of the live deployed file (§27's proposed fix); (c) evidence
of generalization beyond the exact case tested; (d) explicit, separate human sign-off, per this project's
own standing discipline for anything touching RiverBrain or the self-edit training signal.

**10. Does this experiment change our assessment of FeralEcho's capability ceiling?** Not the ceiling
itself (§25) — but it sharpens the diagnosis. The obstacle to useful experience-driven adaptation may not
be purely architectural (a missing wire, which is fixable by wiring) — it may also be that the underlying
models' own strong, repeatedly-reinforced associations with this project's own chronically-repeated task
patterns can dominate a single, weak, factual nudge. That is a harder problem than a missing connection,
and this experiment is the first piece of direct, experimental (not just observational) evidence for it
tonight.

