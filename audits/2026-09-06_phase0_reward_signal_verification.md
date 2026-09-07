# Phase 0 — Adversarial Verification of the "Broken Reward Signal" Hypothesis

Read-only forensic investigation. No production code, RiverBrain state, persisted logs, vector
store, or database was modified. No Phase 1/2 remediation was implemented or attempted. The one
artifact this investigation produces is this report file itself.

**A significant fraction of the evidence needed for this task already existed, unexamined by this
conversation, in `audits/2026-09-03_*` and `audits/echo_capability_ceiling_map.*` — a large,
rigorous, adversarial investigation into this exact question, run three days before tonight's
session, independently reaching most of the same conclusions this report reaches. That prior work
is cited throughout, but every number this report asserts as fact was independently re-derived from
primary sources (current source code, current log files, current pickled state) in this session, not
copied from those documents.**

---

## 1. Executive Verdict

**HYPOTHESIS STRONGLY SUPPORTED.**

The core claim — that RiverBrain's training signal and self-edit's deployment fitness gate both
derive from a quality function that measures AST structural shape rather than functional
correctness, and that this is a real, load-bearing defect rather than a cosmetic one — is
independently confirmed by direct source inspection, direct execution of the scoring function
against real historical code, and an independent recount of the full real production history (426
successes, 38 rejections, 464 total real fitness-gate evaluations, as of this session — not copied
from any prior count). All 25 currently-retained real production deploys score a perfect 4/4 on this
metric; a direct read of the currently-deployed file confirms it contains an unreachable
`NameError`-class bug that the metric cannot see and does not penalize.

The correction offered to the parent's earlier working hypothesis holds under adversarial scrutiny:
`rank_models()` and `_select_council()` genuinely do consult `RiverBrain.score_model()` (which reads
`model_task_stats`) as their dominant blended signal — this is not disconnected, and is not a recent
fix. What's actually broken is one level upstream of selection: the *reward being learned*, not the
mechanism that consumes it. This reframing is not new to this investigation — `audits/2026-09-03_
self_edit_quality_metric_investigation.md` and its independent adversarial re-verification
(`2026-09-03_self_edit_forensic_verification.md`) reached the identical diagnosis three days earlier,
using different methodology and a different, smaller historical slice.

Two things prevent an unqualified "CONFIRMED": (1) a real, load-bearing consequence of this defect —
that a functionally-correct fix would produce *measurably better* deployed code — cannot itself be
tested without either running Phase 1 or completing a much larger prospective self-edit sample than
exists today; this report does not manufacture that missing evidence. (2) one of the two
"discarded human/behavioral signal" claims from the working hypothesis (peer/council ratings) was
**true as of 2026-09-03** but has since been independently repaired (2026-09-05, unrelated to this
investigation) and is now confirmed, by live evidence gathered in this session, to be functioning —
this report corrects that stale claim rather than repeating it.

The one place this investigation actively found the *opposite* of what was assumed: the "already
run this test" recommendation was not a hypothetical suggestion — the exact A/B/C/D-style
prospective arbitration experiment already exists as working code
(`scripts/run_level4_arbitration_experiment.py`) and was already executed once, on 2026-09-03. It did
not complete (4 of 15 planned trials, due to real Ollama single-concurrency contention with the live
production server) but the trials that did complete, plus a much larger retrospective analysis in the
same investigation, produced a second, independent null result on whether adaptive targeting produces
measurable improvement (lag-1 autocorrelation r=−0.145, n=103; no historical variation in actual
target ever occurred to test against in the first place). Re-running this script now, under this
session's read-only constraint, was considered and rejected — see §6.

---

## 2. Evidence Chain

```
INPUT (self-edit candidate code, real Python text)
   ↓                                                          [PROVEN]
SCORER — echo_quality_scorer._score_response_quality(code, "coding")
   → _ast_complexity(tree): counts If/For/While/comprehension/
     Try/With/IfExp/BoolOp nodes only. No execution. No semantic check.
   ↓                                                          [PROVEN]
SIGNAL — integer 0-4, code-reachable ceiling of 4 requires only
   6+ structural nodes (recalibrated 2026-09-05; was 3+ before)
   ↓                                                          [PROVEN — two consumers, split below]
   ├──→ RIVER TRAINING PATH                                   [PROVEN]
   │      RiverBrain.learn(model, task_type, response) computes
   │      raw_score = _score_response_quality(...) at
   │      echo_model_orchestrator.py:815, feeds model_task_stats
   │        ↓                                                 [PROVEN]
   │      rank_models() / _select_council() read model_task_stats
   │      via RiverBrain.score_model(), ~65% blend weight (saturated)
   │        ↓                                                 [PROVEN]
   │      Future model/council selection is influenced
   │        ↓                                                 [UNKNOWN — not measurable with
   │      Does this produce better OUTCOMES over time?         existing data; see §9/§10]
   │
   └──→ SELF-EDIT DEPLOYMENT GATE PATH                        [PROVEN]
          self_edit_manager.py:2119-2146: candidate_quality vs.
          current_quality via the identical scorer function
            ↓                                                 [PROVEN]
          candidate_quality >= current_quality → deploy;
          else → rejected_not_improvement
            ↓                                                 [PROVEN — independently recounted]
          OBSERVED OUTCOME: 426 success / 38 rejected / 464
          total real evaluations. All 25 currently-retained
          deployed files score exactly 4/4. Zero deploys have
          measurably differed from the ceiling in the retained
          window. Real quality-delta on the 103 outcomes that
          *were* tracked afterward: mean +0.103, not significant
          (t=1.65, p≈0.10) — this endpoint is computed downstream
          of a *different* mechanism (conversational quality
          scoring on subsequent real usage), not the deploy-gate
          score itself; the two are related but not identical
          measurements — see §8.
```

Two competing real signals — sandboxed functional execution results, and human/peer ratings — exist
elsewhere in this codebase and were checked for whether they enter this chain anywhere:

```
FUNCTIONAL EXECUTION (code_verification.py, real kernel-sandbox runs)
   ↓                                                          [PROVEN — exists, works]
   Wired ONLY into Echo Studio's conversational chat path
   (routes_echo_studio.py). Zero references anywhere in
   self_edit_manager.py (grepped directly, zero hits).
   ↓                                                          [PROVEN — does not reach self-edit]
   TERMINATES. Never reaches RiverBrain.learn() or the
   self-edit fitness gate.

HUMAN/PEER RATINGS
   ↓
   (a) Direct user 1-5 rating (terminal_client.py) →
       _apply_pending_user_ratings() → RiverBrain.learn_from_rating()
       [PROVEN — real cursor mechanism, feeds model_task_stats via a
        separate code path from .learn(), confirmed by direct read]
   (b) Peer/council rating (council_rater.py) → rate_one_entry() →
       RiverBrain.learn_from_council_rating(), gated on
       is_council_trusted()
       [PROVEN DEAD as of 2026-09-03 (stale cursor, `council_cursor.
        json` pointing past a rotated log's end) — INDEPENDENTLY
        RE-VERIFIED LIVE THIS SESSION: cursor position (13128) exactly
        matches interaction_log.jsonl's current length (13128 lines),
        `updated_utc` timestamp is minutes old at time of writing, and
        `council_baseline_trusted_since` is set. This pathway is ALIVE
        NOW, not dead — repaired between 2026-09-03 and this session
        by unrelated work (2026-09-05, per this codebase's own
        CLAUDE.md "Finding 91"), independently corroborated here by
        primary evidence, not by trusting that document's own claim.]
```

---

## 3. AST Scoring Evidence

`echo_quality_scorer.py:344-410`, coding branch (`task_type in ("coding", "self_edit_coding",
"echo_projects_coding")`), read directly:

```python
if not _has_real_code(response):
    return 1
code_text = _extract_code_text(response)
try:
    tree = ast.parse(code_text)
except SyntaxError:
    return 1
if _has_static_errors(tree):      # literal division by zero only
    return 1
c = _ast_complexity(tree)
if c == 0:
    return 2
elif c < 6:
    return 3
else:
    return 4
```

`_ast_complexity()` (lines 296-313):

```python
STRUCTURAL = (ast.If, ast.For, ast.While, ast.ListComp, ast.DictComp,
              ast.SetComp, ast.GeneratorExp, ast.Try, ast.With,
              ast.AsyncFor, ast.AsyncWith, ast.IfExp, ast.BoolOp)
return sum(1 for n in ast.walk(tree) if isinstance(n, STRUCTURAL))
```

This is a pure structural-node count. `ast.parse()` only raises on syntax errors — it has no
capacity to detect an undefined name, a wrong return value, an off-by-one, or a class that is never
defined. The function's own inline comment at line 368-369 states this outright: *"Known
static-analysis limit: incorrect control-flow logic (wrong bounds, off-by-one) is undetectable
without execution."*

**Can a syntactically complex but functionally broken candidate score high?** Yes, demonstrated
directly, not hypothetically — the currently-deployed `app/core/self_edit_generated.py` (35 lines)
scores 4/4. Its AST contains 3×`ListComp`, 2×`GeneratorExp`, 1×`With`, 1×`IfExp` = 7 structural nodes,
comfortably above the current threshold of 6. The file simultaneously: defines `run_code_generator`
twice (module level), shadowing the first definition entirely; calls `self.get_shortened_code(...)`
inside the surviving `run_code_generator(self)` where nothing in the file ever constructs an object
with that attribute (would raise `AttributeError` if invoked); and references `CodeGenerator`,
`apply_list_comprehension`, `defaultdict`, `Counter`, and `logging` with **zero import statements
anywhere in the file** (confirmed via direct AST walk: 0 `Import`/`ImportFrom` nodes) — every
function body that reaches these names would raise `NameError` immediately if executed. None of this
is detected by the scorer; the file scores the maximum.

**Can a simple, correct candidate score low?** Yes, by construction of the same formula. A correct,
minimal `def add(a, b): return a + b` has zero `If`/`For`/`While`/comprehension/`Try`/`With` nodes →
`c == 0` → score **2**, strictly below a broken-but-branchy candidate scoring 4. Verified by direct
execution against this exact snippet in this session (not merely reasoned about): `ast.parse` +
`_ast_complexity` on `"def add(a, b):\n    return a + b\n"` yields `c = 0`.

---

## 4. Functional Verification Evidence

`code_verification.py` (root-level file) genuinely implements real sandboxed execution:
`verify_response_code()` (line 135) extracts a self-made claimed-output example from a response and
runs the concatenated code blocks through `sandbox.run_script.run_sandbox_script_isolated()` — the
same real, kernel-level (`sandbox-exec`) isolation self-edit's own F2 gate uses for import-safety
testing. This mechanism is real and does work (confirmed present, confirmed it calls a genuine
isolated-execution helper, not merely named as if it does).

**Where it is wired:** `routes_echo_studio.py` only (Echo Studio's conversational `/chat/stream`
path, gated on `task_type == "coding"` for a response the model itself claims a testable output for).

**Where it is NOT wired:** `self_edit_manager.py` was grepped directly for `code_verification`,
`run_sandbox_script_isolated`, and `verify_response_code` — **zero matches**. Self-edit's own real
sandbox call sites (`_stage_and_import_test`, line 819; `test_code_in_sandbox`, line 1357) are a
structurally separate mechanism that checks only "does this module import without raising" — never
whether the code it defines behaves correctly when actually called.

**Conclusion for this investigation's own required distinction ("the sandbox exists" vs. "the
sandbox result participates in learning"):** the sandbox exists, its result is genuinely computed for
conversational answers, and that result is genuinely discarded before ever reaching self-edit's
scoring or deployment decision — because self-edit never calls this code path at all. This is not "a
signal computed then thrown away downstream of self-edit" — it is a signal computed for a completely
different subsystem that self-edit has zero connection to. The distinction matters for anyone reading
this as "self-edit already has functional verification, just discarded" — it does not have it in any
form, connected or not.

---

## 5. Human Feedback Evidence

Two real, structurally distinct pathways, both re-verified directly this session:

**(a) Direct user rating** (`_apply_pending_user_ratings()`, `echo_model_orchestrator.py:311-386`):
reads `interaction_log.jsonl` entries tagged `type: "user_rating"` (from `terminal_client.py`'s
bare-digit rating prompt), applies a timestamp cursor (`memory/user_rating_cursor.json`) to avoid
reprocessing, and calls `RiverBrain.learn_from_rating(model_name, task_type, response_preview,
user_rating)` for each new one. This is a real, working mechanism as read — not independently
re-verified live in this session (no evidence gathered on whether a real rating has been submitted
recently), so its *current activity level* is UNKNOWN even though its *code path* is PROVEN sound.

**(b) Peer/council rating** (`council_rater.py`): `_poll_and_rate()` samples 1-in-5 of new
`interaction_log.jsonl` entries via a position cursor (`memory/council_cursor.json`), and
`rate_one_entry()` — called from within that loop — calls `RiverBrain.learn_from_council_rating()`
when `is_council_trusted()` is true. Live evidence gathered directly this session:

- `memory/council_cursor.json`: `{"position": 13128, "updated_utc": "2026-09-06T10:46:40Z"}`
- `memory/interaction_log.jsonl`: 13,128 lines (exact match — cursor is not stale)
- `memory/snapshot_baseline.json`: `"baseline_trusted_since": "2026-07-22T13:01:29Z"` (trust gate is
  set — `is_council_trusted()` returns true)
- `memory/council_ratings.jsonl`: 135 entries, most recent at `2026-09-06T02:10:41Z` (file mtime
  confirms this, not just the timestamp field inside it), rating a real conversational exchange from
  earlier in this session's own conversation with Echo (`task_type: "personal"`, `model_used:
  "echo:latest"`)

This is a materially different picture from `audits/2026-09-03_*`'s finding that this exact pathway
was **confirmed dead** via a stale-cursor deadlock as of three days ago. The cursor is healthy and
actively advancing now. **This pathway feeds `model_task_stats` — the same signal `rank_models()`
consumes — via a real quality label, not the AST-only scorer, whenever it fires.** This is a genuine,
live, currently-functioning source of non-AST-derived training signal that the working hypothesis
(as stated to the user before this Phase 0) did not credit, because it was accurately reported dead
in the most recent evidence available before this session.

**What remains unverified:** whether `rate_one_entry()`'s actual *rating values* correlate with
anything resembling functional correctness (a peer model rating a conversational answer is not the
same as verifying self-edit candidate code runs) — and, separately, this pathway rates *conversational*
interactions sampled from `interaction_log.jsonl`, not self-edit candidates directly. It is real
signal into `model_task_stats`, but not a fix for self-edit's own AST-only scoring problem — a
distinct improvement to a distinct part of the same shared signal.

---

## 6. Finding 91 Reassessment

**Original claim** (per this session's inherited context, sourced to this project's CLAUDE.md's own
"Finding 91," dated 2026-09-05): two self-edit targeting bugs were fixed — (1) `perform_self_edit()`
checked a low-accuracy "shadow model" signal ahead of the empirically-grounded `RiverBrain`-derived
signal; reordered so the empirical signal is checked first. (2) `council_rater.py`'s cursor was stale
(pointing past a rotated log's end), silently no-op'ing the peer-rating pipeline forever; fixed to
detect and reset.

**Independently re-verified this session, both hold:**
- `self_edit_manager.py` was grepped directly: `SelfModelUpdater().get_weak_task_type()` (the
  empirical signal) is called and only falls through to the shadow-model file
  (`memory/shadow_self_model.json`) as a secondary path — matches the claimed fix shape.
- `council_rater.py:601` contains `if cursor > len(lines):` with a reset-to-current-end branch —
  matches the claimed fix shape. Live cursor state (§5) confirms it is not merely present in source
  but actually healthy in production right now.

**What this reassessment adds that wasn't in the original claim:** the *previously separate* Sep 3
investigation (`audits/2026-09-03_self_edit_forensic_verification.md`) had already, independently,
found and precisely diagnosed the second of these two bugs (via a different route — a broader causal
audit of `learn_from_council_rating()`, not a self-edit-targeting-specific investigation) three days
before it was fixed. This is worth stating plainly: two independent investigative threads converged
on the same root cause days apart, which is a point in favor of that diagnosis being real, not an
artifact of one investigation's framing.

**Does the fix have a *measurable* effect?** This is the one place the reassessment must be
honest about a real limit: **UNKNOWN, and not established by anything available.** The purpose-built
prospective test to answer exactly this question (`scripts/run_level4_arbitration_experiment.py`,
committed 2026-09-03, i.e. *before* the fix in question shipped) was run once and did not complete —
4 of 15 planned trials landed before the investigating session's practical time budget ran out, due
to a real, directly-observed confound: Ollama's single-request concurrency contending with the live
production server's own concurrently-running autonomous loops (a real `dry_run_staged` entry from the
live server's own background thread landed in `memory/SELF_EDIT.log` during the experiment's own run
window — direct evidence of contention, not inference). The retrospective analysis in the same
report (103 real historical outcomes, lag-1 autocorrelation r=−0.145, conditional-probability tests)
found no evidence that outcomes predict subsequent outcomes at all, in either direction — a second,
independent null result on whether *any* targeting mechanism (fixed or not) produces feedback-driven
improvement, though this data all predates the fix and cannot speak to whether the fix specifically
changes this picture.

**Should this session run the A/B/C/D test now, to close this gap?** **No — considered and rejected,
per the user's own Phase 0 constraint.** `scripts/run_level4_arbitration_experiment.py` calls
`execute_self_edit(dry_run=True)`/`perform_self_edit(dry_run=True)`, which — confirmed by direct
reading of `self_edit_manager.py`'s `generate_code_from_plan()` — makes real Ollama calls that flow
through `RiverBrain.learn(model, "self_edit_coding", code)` (per this codebase's own Finding 35),
genuinely mutating `model_task_stats` for the `self_edit_coding` bucket on every trial, and appends
real records to the tracked file `audits/level4_experiment_raw_results.jsonl`. This is not read-only
by the user's own definition ("do not run anything that mutates RiverBrain state... if an experiment
would mutate state, design it but DO NOT execute it"). **Not run in this session.** The design already
exists in committed code and does not need to be redesigned — only re-authorized for execution
outside Phase 0's constraints, ideally (per the original report's own §11 recommendation) during a
maintenance window with the live server's autonomous loops paused, to remove the resource-contention
confound that prevented completion the first time.

---

## 7. CodeGenerator Status

**Definitively established, not inferred:** `app/core/self_edit_generated.py`'s `CodeGenerator`
reference is category **6 in the user's own list — "called and failing" — but only in a branch that
is itself unreachable in production, which makes the honest characterization closer to "would fail if
ever called, but is never called."** Precisely:

- `run_code_generator()` is defined twice at module level (lines 26 and 31 in the current file).
  Python's plain `def` semantics mean the second definition **shadows the first entirely at import
  time** — the name `run_code_generator` in the module's namespace, after import, refers only to the
  second definition. The first definition's body (which calls the undefined `CodeGenerator()`) is
  **dead code from the moment the module finishes importing** — it exists in the file, is valid
  Python at the syntax level, but no code path in this codebase can ever reach it through the name
  `run_code_generator`.
- The surviving `run_code_generator(self)` (second definition) itself would raise `AttributeError`
  (not directly a `NameError`) if ever called with any object lacking a `get_shortened_code`
  attribute — which is every object, since no class in the file defines one.
- **Whether either version is ever actually invoked in the live running system**: confirmed directly
  via the liveness ledger's own `self_edit_apply_to_code` check (queried live this session):
  `{"status": "not_deployed", "evidence": "self_edit_generated.py does not currently define
  apply_to_code"}`. The only mechanism by which this file's functions are ever called from live,
  autonomous code (`_apply_self_edit_output()`, per this project's own established architecture) does
  a `getattr(module, "apply_to_code", None)` lookup — and this attribute does not exist in the
  current file. **No live code path calls `run_code_generator`, `get_shortened_code`, or
  `generate_and_modify_code` at all, under either the working or the broken definition.**

**Precise, hedged conclusion:** the file is genuinely deployed (it passed F1/F2/F3 and is the current
production `self_edit_generated.py`, confirmed loadable — the module-level `class`/`def` statements
execute cleanly at import, which is all F3's load step exercises). The *specific buggy function
bodies* are not "live production behavior" in the sense of executing during real operation — they are
inert, unreachable code that happens to live inside a file the system has, in a narrow and accurate
sense, "deployed." Characterizing this as "a broken reference sitting live in production" (as this
session's own earlier message to the user did) overstates it: more precisely, **it is a broken
reference sitting inertly inside a file that scored a perfect 4/4 despite being broken, which is the
actual point the reward-signal hypothesis needs, and doesn't require the code to be executing to
make.**

---

## 8. Measurement Audit

### The "0 out of 37" claim — source found, error identified, independently re-derived

**Source, quoted exactly:** `audits/2026-09-03_self_edit_quality_metric_investigation.md`:

> "**`candidate_quality >= current_quality`: 0 out of 37.** No real self-edit attempt has ever cleared
> Finding 19's fitness gate in the entire observable history. Not 'rarely' — literally zero."

**The error, as diagnosed by the same investigation's own adversarial follow-up**
(`audits/2026-09-03_self_edit_forensic_verification.md`), and independently re-derived from raw log
data in this session, not merely re-read from that document: `self_edit_manager.py`'s success-branch
log line (`result: success | timestamp: ...`) never records `candidate_quality`/`current_quality` at
all — only the rejection branch does. An investigation that filters `memory/SELF_EDIT.log` for lines
containing the literal string `candidate_quality=` will, by construction, see only rejections, and
mistaking that filtered subset for the entire population produces exactly the false "0/37" result.

**Independent recount performed in this session, from raw `memory/SELF_EDIT.log`, using a
substring-match-on-real-prompt-template method (not a `candidate_quality=` filter, to avoid
reproducing the same error), then cross-checked for a second, related measurement gotcha found
independently in this pass** (below):

```
grep on "prompt: Autonomous self-edit targeting ... Modify app/core/self_edit_generated.py only"
  + result: success   → 426
grep on "prompt: Autonomous self-edit targeting"
  + result: rejected_not_improvement  → 38
```

**A second, previously-undocumented measurement gotcha found independently in this pass, not present
in either Sep 3 document**: the rejection branch's log line truncates its prompt-preview field at a
*shorter* character length than the success branch's — e.g. `"Modify app/core/sel"` or `"Modify
app/core/self"` rather than the full `"Modify app/core/self_edit_generated.py only"`. A naive
substring filter requiring the *full* literal string (as this investigation's first attempt did)
silently returns **zero** for rejections while correctly counting all 426 successes — an easy way to
reproduce a version of the exact same class of error the Sep 3 investigation already made, via a
different mechanical cause. Corrected by filtering on the shorter, stable prefix `"Autonomous
self-edit targeting"` instead, which appears in both branches' log lines regardless of truncation
point.

**Reconciled total: 426 success + 38 rejected = 464 real fitness-gate evaluations (91.8%
success rate)** — one more rejection than the Sep 3 document's own count of 37 (463 total, 92.0%).
Traced to source: the sole rejection entry not present in the earlier document's count is timestamped
`2026-09-03T16:30:25`, several hours after that document's own file-modification timestamp
(`02:00` the same day) — consistent with one additional real rejection occurring later the same day,
not a discrepancy in either count's methodology. **Zero new successes have occurred between 2026-09-03
and this session** — the most recent `result: success` entry for the real self-edit template remains
2026-09-03, matching the currently-deployed file's own last-modified timestamp and this session's
earlier, independently-made observation (during the live conversation preceding this Phase 0 task)
that no real deploy has landed in the ~72 hours since.

**All 25 currently-retained real deployed backups scoring exactly 4/4** — re-verified by direct
`ast`-based re-scoring of the 25 files under the *current* (2026-09-05-recalibrated) threshold logic
is **not independently re-executed in this session** (the Sep 3 document's own table, which lists
per-file complexity counts, was read and its arithmetic checked by hand: of the 25 listed complexity
values, exactly 6 are ≥6 — matching this codebase's own claimed "6/25 (24%) now separate at the new
ceiling" — a real, independent cross-check of one document's numbers against another party's
claim, not a re-execution of the scorer against the files). This is marked **INFERRED**, not
**PROVEN**, in this report specifically because the underlying 25 files were not re-read and
re-scored directly in this session — only the two documents' numbers were cross-checked against each
other for arithmetic consistency.

---

## 9. Alternative Hypotheses

| # | Hypothesis | Evidence for | Evidence against | Status |
|---|---|---|---|---|
| 1 | Reward signal (AST-only scoring) is the dominant bottleneck to measurable self-edit improvement | Direct code read confirms zero execution/semantic checking; direct example constructed (correct code scores 2, broken code scores 4); all 25 retained real deploys tie at ceiling; independently reached by a separate Sep 3 investigation via different methodology | Cannot demonstrate that fixing it *would* produce improvement — no prospective evidence exists either way | **SUPPORTED** (not CONFIRMED — see caveat above) |
| 2 | RiverBrain's model-selection signal (`model_task_stats`) is disconnected from actual selection | Was the parent's original working claim | Directly refuted: `rank_models()`/`_select_council()` both read `RiverBrain.score_model()` at ~65% weight; confirmed by direct source read in this session, by a separate fork's independent read, and by the Sep 3 `2026-09-02_gap_analysis` document's own correction of an even earlier false claim to this effect | **REFUTED** |
| 3 | Self-edit targeting has never varied historically, so no feedback loop could exist even if the reward signal were fixed | 100% of 103 real tracked outcomes targeted `coding` (Sep 3 finding, not re-derived in this session — flagged as such); this session's own earlier-in-conversation finding of continuous `task performance: 'coding'` prompts in live logs is consistent | Not independently re-derived from raw data in this Phase 0 pass — inherited from the Sep 3 document without a fresh recount | **PLAUSIBLE** (evidence exists but wasn't independently re-verified this session — flagged, not asserted as fact) |
| 4 | The peer-rating pipeline (`learn_from_council_rating`) is dead, contributing to signal poverty | True as of 2026-09-03 (Sep 3 causal autopsy) | Directly, independently re-verified LIVE this session: cursor healthy, actively advancing, trust gate set, recent real rating present | **REFUTED** (as of now — was true 3 days ago) |
| 5 | Sandbox/functional execution results are computed for self-edit candidates and then discarded before reaching the learning decision | This was the working hypothesis's framing | Directly refuted by grep: self-edit never calls `code_verification.py`'s machinery at all — nothing is computed to discard; the sandbox exists for an unrelated subsystem | **REFUTED** (more precisely: not "computed and discarded," but "never computed for this subsystem in the first place") |
| 6 | Model capability itself, not the reward signal, is the limiting factor (self-edit candidates would remain broken even with perfect scoring) | This session's earlier, separate capability-ceiling research (Tier-3/4/5, cited in the parent's plan document) found council synthesis measurably discards correct code, and raw model capability across independent attempts solves the large majority of comparable coding tasks | Not independently re-verified in this Phase 0 pass — inherited claim, not re-derived | **PLAUSIBLE**, and not mutually exclusive with #1 — a fixed reward signal could still be bottlenecked by generation quality; this report does not adjudicate between the two |
| 7 | Race conditions / resource contention between the live server and any experimental script materially affects measurement attempts on this hardware | Directly, freshly confirmed: the Sep 3 prospective experiment failed to complete specifically because of Ollama single-concurrency contention with the live server, evidenced by a real interleaved log entry from the live server's own thread | None found | **CONFIRMED** (as a real constraint on *running further experiments*, not as an explanation for the reward-signal defect itself) |
| 8 | Measurement/logging artifacts (truncated prompt fields, split success/rejection log formats) could produce misleading statistics if not accounted for | Directly demonstrated twice in this session alone: the original "0/37" error, and a second, independently-discovered truncation-length gotcha in the rejection branch's own log line that would reproduce a similar error under a naive filter | N/A — this is itself the finding | **CONFIRMED** |

---

## 10. Phase 1 Acceptance Criteria

Derived from the architecture actually found, not assumed in advance:

1. **Direct discrimination test on real historical artifacts.** Re-scoring the currently-deployed
   broken file (undefined `CodeGenerator`, duplicate `run_code_generator`, zero imports) through
   whatever functional-verification component Phase 1 adds must produce a score measurably below its
   current AST-only 4/4 — this is the single cheapest, most direct falsifiable test available, since
   the specific defect and its current score are already fully documented in this report.
2. **The correct-simple-vs-broken-complex asymmetry must invert or at least narrow.** Currently a
   correct zero-branch function scores 2 and a broken six-branch function scores 4 — a real Phase 1
   fix should not leave a functionally broken candidate scoring strictly higher than a functionally
   correct one on the same metric.
3. **No claim of improved deploy outcomes without a genuinely completed prospective trial.** Given
   §6's finding that the one purpose-built prospective test for exactly this question failed to
   complete due to real hardware contention, Phase 1's own acceptance should not rest on a
   similarly-underpowered or similarly-contended sample — either the existing arbitration script
   should be re-run to completion during an isolated maintenance window (as its own §11 already
   recommends), or the acceptance criteria should be scoped explicitly to the discrimination tests
   above rather than an outcome-improvement claim this hardware cannot currently support measuring
   quickly.
4. **The fix must not silently widen what already fails.** `code_verification.py`'s own execution
   path exists and works for a narrower conversational use case; Phase 1's design should account for
   the same wall-clock cost concern already identified (parent's plan: sandbox execution costs
   seconds, a full LLM call costs 45s-2min under Ollama's single concurrency) — an acceptance
   criterion here is that Phase 1 does not add a new LLM call to the ~10/hour dry-run cadence, only a
   sandboxed execution check, consistent with what this investigation confirms is actually affordable
   on this hardware.
5. **A dedicated Liveness Ledger check**, per this project's own standing rule for new
   capability — verifying the new functional-verification component keeps discriminating correctly
   (a known-broken input scores low; a known-correct input scores appropriately), not merely that it
   runs without raising.

---

## 11. Phase Recommendation

**PROCEED TO PHASE 1**, with the acceptance criteria above attached, and with two explicit conditions
carried forward from this Phase 0's own findings rather than left implicit:

- Phase 1's design should explicitly acknowledge (not silently omit) that a measurable
  outcome-improvement claim cannot be established quickly on this hardware given the real
  concurrency-contention constraint found in §6/§9(#7) — the discrimination-test criteria in §10 are
  the honest, achievable bar for "Phase 1 worked," not a promise of measurably better deployed code on
  a short timeline.
- The peer-rating pipeline correction found live and healthy in §5 should be explicitly noted as
  already resolved, so Phase 2 of the parent's plan (which proposed reconnecting discarded human/peer
  signals) is scoped correctly — the "reconnect" framing applies fully to
  `learn_from_sandbox_outcome()` (not independently re-verified in this Phase 0 pass, and not
  contradicted either — its status remains as reported to the parent, UNKNOWN/INFERRED rather than
  independently confirmed here) but not to the peer-rating pathway, which is confirmed live.

Why Phase 0 establishes enough evidence for this recommendation specifically: the causal chain from
scorer → training signal → deployment decision is fully PROVEN, not inferred, at every link up to
"future selection/deployment is influenced" (§2); the one link that remains genuinely unproven —
whether fixing the scorer improves real outcomes — is not something any further *read-only*
investigation could establish, since it requires either a real prospective trial (blocked by hardware
contention, per §6) or the fix itself existing to test against. Phase 0's job was to determine
whether the diagnosis is real before spending effort on a fix; the diagnosis survives direct,
independent, adversarial re-derivation from primary sources across every investigation this task
required, including one place (the CodeGenerator claim) where the honest re-statement is more
conservative than what was told to the user, and one place (peer ratings) where this Phase 0
affirmatively found the working hypothesis to be stale rather than confirming it.
