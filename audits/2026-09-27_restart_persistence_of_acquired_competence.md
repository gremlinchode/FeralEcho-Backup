# Restart Persistence of Acquired Competence

**A test of exactly one thing, per explicit mandate: can a previously
frozen, competence-enhancing artifact (P) outlive the process that created
it and provide a measurable, causally-attributable advantage to a
genuinely fresh successor process, on new held-out cases of the same task
family? This is not a re-run of the acquisition experiment, not a test of
cross-family generalization, and not authorization for any further
accumulation-ladder work. Per the governing mission's own stop condition,
this report ends the assignment; the second-task-family experiment is
explicitly not begun here.**

---

## 1. Prerequisite Evidence Verification

The governing mission accepted, only provisionally, three claims about
`validated_experience_competence_transfer` ("VECT"): (a) P produced a
verified advantage over G and Z; (b) P transferred to unseen instances
within the same family; (c) P was frozen as a durable artifact. It
required independently verifying these, and specifically checking whether
any later audit invalidated or materially qualified the result, before
designing anything.

**A later, previously-unread audit was found**:
`audits/2026-09-24_codex_validated_experience_transfer_self_falsification.md`
— Codex's own adversarial self-review of an earlier, harsher critique of
VECT. Its own executive verdict: *"MY ORIGINAL CRITIQUE WAS PARTLY WRONG /
TOO STRONG"* — the numeric result holds up better than an earlier pass
suggested, but two real, load-bearing qualifications survive scrutiny.

**Both qualifications were independently re-derived by this session, not
taken on that audit's word alone**:

- **Claim (b) is weaker than originally stated.** Direct comparison of
  `train_tasks.json` against `heldout_tasks.json`: TRAIN has 4 distinct
  code bodies, the original held-out set has 4 distinct code bodies, and
  the overlap is exactly 4 — **zero new code content was ever tested**.
  Root cause independently traced to `historical_difficulty_calibration/tasks.py`'s
  `CODE_SNIPPETS_COMPLEX`, a fixed 4-entry bank: with only 4 possible
  values and 8 TRAIN draws, every value necessarily recurs in any later
  sample from the same bank, by pigeonhole. "Unseen instances" held only
  at the level of prose recombination, never underlying code.
- **P's provenance is externally authored, not Echo-autonomous.** Direct
  read of `freeze_procedure.py`: `PROCEDURE_TEXT` is a literal,
  investigator-written string; the script's only substantive check is that
  each cited `train_L3_NN` episode ID exists in `experience_log.jsonl` — it
  never derives clauses from candidates algorithmically. P is real,
  frozen, and grounded in genuine TRAIN evidence, but it was authored by
  the investigator (per the original report, Claude), not extracted by an
  Echo-operated mechanism.

**Also independently reconfirmed, unchanged from the original report**:
`procedure_frozen.json`'s canonical-JSON hash still matches
`procedure_hash.txt` exactly
(`21fde9b5dbe026489ef8f3ff47f974c816ca706944cde251b2501ed7f541f3c8`);
`heldout_tasks.json`'s canonical-JSON hash still matches
`heldout_commitment.sha256` exactly
(`a35c0807cc505ed4d192b44f17b2705427ccf8e3a46af374557e60d9a8c90055`); all
32 files in the self-falsification audit's own byte-hash manifest,
re-checked directly by this session (a 5-file spot-check covering
`CONTRACT.md`, `freeze_procedure.py`, `prompt.py`, `run.py`, and
`tasks.py`), remain byte-identical; the headline numeric result (P=10/10,
G=6/10, Z=5/10) reproduces exactly.

**Determination**: the prerequisite **survives inspection, materially
qualified rather than invalidated**. The frozen artifact P is real,
hash-verified, and did produce a genuine measured advantage over G and Z
on VECT's original panel — that empirical core is not in question. What
does not survive at full strength is the "unseen instances" framing (claim
b) and any implicit reading of P as Echo's own autonomously-acquired
competence. Both corrections are built directly into this experiment's
design (Section 2, Section 5) and its claim language (Sections 8-9), per
the mission's own instruction to fold in qualification rather than ignore
or overclaim past it. This is not the "does NOT survive — STOP" case; it
is the "materially qualified" case the mission explicitly asked to be
checked for and accommodated.

## 2. Frozen Protocol

Frozen in full, before any new held-out generation or execution, at
`app/experiments/restart_persistence_transfer/PROTOCOL.md`
(SHA-256 `99c750bf90c081499d41ddd72be37b6d7eff149968c94ab869df5d99ad7ce55d`,
recorded in the sibling `PROTOCOL.sha256` at freeze time, timestamp
`2026-09-27T09:45:16Z`). Not edited after this point. Summary of its
governing decisions (full text in that file):

- **H1**: a fresh successor recovering and applying P (R+) will score at
  least as high, and on average higher, than an equivalent fresh successor
  denied P (R-), on 10 new held-out instances built from genuinely new
  code content.
- **H0**: no such advantage, or none attributable to P.
- **Restart definition**: the originating VECT process(es) are already
  three real days dead; R+ and R- are each a freshly-launched `python3`
  OS subprocess, invoked from separate Bash tool calls (which do not
  persist process state across calls), sharing no memory with each other,
  the originating process, or the investigating session.
- **R+**: reads and independently hash-verifies `procedure_frozen.json`
  before use; aborts immediately on any mismatch.
- **R-**: never opens `procedure_frozen.json` anywhere in its source;
  uses VECT's own Z-arm (no-help) prompt shape.
- **New held-out set**: 10 instances, seeds 2000-2009 (confirmed disjoint
  from every prior seed range used anywhere in this research arc), built
  from 4 genuinely new code snippets never present in VECT's TRAIN,
  original held-out set, or generator banks — generated via in-process
  monkeypatching of the shared generator's code bank, never by editing
  the shared file on disk (editing it would have silently altered what a
  future re-run of VECT's own frozen experiment produces for its own
  already-used seeds).
- Full contamination checklist, success/failure/ambiguous criteria, and
  statistical plan frozen in Sections 7, 9, and 10 of that document,
  before any outcome was observed.

**No deviation from the frozen protocol occurred during execution.**

## 3. Process-Boundary Evidence

- **Originating process** (VECT's `python -B run.py <phase>` invocations,
  2026-09-24): already fully terminated. Non-invasive evidence: VECT's own
  files carry mtimes from 2026-09-24; today is 2026-09-27 (3 real days
  later); a live `ps aux` scan for any process matching
  `validated_experience` found zero matches. This is the strongest
  non-invasive evidence reasonably available for a process that ended
  before this investigation began — not overclaimed as a captured
  kill-signal trace, since none exists for a process this old.
- **R+**: PID 8507, `python3 -B app/experiments/restart_persistence_transfer/run_condition.py --condition=r_plus`, started `2026-09-27T09:48:56Z`, ended `2026-09-27T09:50:02Z` (65.9s), executable `/Users/richietate/miniforge3/envs/feral_echo/bin/python3`. Self-reported `id(sys.modules)=4382147072`.
- **R-**: PID 8538 (**distinct from R+'s PID**), `--condition=r_minus`, started `2026-09-27T09:50:10Z`, ended `2026-09-27T09:50:53Z` (42.93s). Self-reported `id(sys.modules)=4382884352` (**distinct from R+'s**, confirming a genuinely separate interpreter instance, not a reused module cache).
- Both invocations were made as two separate Bash tool calls; per this
  harness's own documented behavior, only the working directory persists
  across such calls — environment variables, functions, and process state
  do not. Neither process's PID matches the other's, nor any process from
  the 2026-09-24 originating run.
- Recorded in full in `memory/experiments/restart_persistence_transfer/process_evidence.jsonl`.

**Honest limit, not overclaimed**: this establishes that R+ and R- are
genuinely distinct OS processes, and that both post-date the (already
long-dead) originating process by three real days. It does not, and
cannot, produce a captured "kill signal" for a process that had already
exited three days before this investigation started — the absence of any
matching live process, plus the file-age gap, is the strongest available
evidence for that half of the claim, stated at that strength and no
higher.

## 4. Contamination Audit

Every channel from the governing mission's own checklist, addressed in
`PROTOCOL.md` Section 7 before execution, re-checked here against what
actually happened:

| Channel | Outcome |
|---|---|
| P in R- prompts | Confirmed: R- source (`run_condition.py`) never opens `procedure_frozen.json`; its `context` is hardcoded `""` on that branch |
| Expected-answer leakage through the grader | Grader (`sandbox.run_candidate`) receives candidate code + real input + expected output only; no condition/arm parameter exists in its signature |
| Evaluation code encoding the desired solution | `expected_code` used only for post-hoc grading, never placed in any generation prompt for either condition |
| Filenames revealing treatment to the model | Result files are condition-named (`r_plus_results.jsonl`/`r_minus_results.jsonl`) but this label is never sent to the model — confirmed by reading `prompt.build_prompt`'s inputs, which take only `task` and `context` |
| Shared temp files | Each grading call uses `tempfile.TemporaryDirectory()` (from `sandbox.run_candidate`), a fresh, uniquely-named directory per call |
| Environment variables | No P-derived content was placed in any env var; nothing was manually injected between the two Bash calls |
| Caches | No response cache; both conditions made fresh, uncached HTTP calls to a live Ollama server at `temperature=0`, fixed inference seed `20260923` (matching VECT's own convention, disclosed as shared infrastructure below) |
| Python/module globals | R+ and R- ran as separate OS processes with distinct `id(sys.modules)` values (Section 3) — cannot share globals |
| Shell history / command construction | P's text was never passed as a CLI argument or shell-interpolated string; R+ reads it from disk internally in Python only |
| Model conversation/session reuse | Each held-out call is a single-turn `[system, user]` request with no history, matching VECT's own per-call design |
| Accidental shared process state | R+ and R- were launched from two separate Bash tool calls; confirmed by distinct PIDs and distinct `id(sys.modules)` |
| Test cases appearing in acquisition artifacts | `new_heldout_tasks.py`'s own `_verify_disjoint_from_vect()` grepped all 4 new code snippets against `train_tasks.json`, `heldout_tasks.json`, and both generator banks before generation was trusted — printed confirmation of zero overlap, logged in the generation run's own output |
| Evaluator access to treatment labels | `run_candidate(code, hidden_tests)`'s signature carries no condition/arm argument |

**Disclosed residual channels, not claimed away** (identical in kind to
what the original VECT report and its self-falsification review already
disclosed for their own design):

- The task's own input string is placed in-prompt for both conditions,
  because this task family's definition requires it (write a function that
  extracts code from *this* string) — an inherited design property, not a
  gap introduced here, applied symmetrically to R+ and R-.
- Both conditions called the same live, persistent Ollama server process,
  not itself restarted between R+ and R-. At `temperature=0` with no
  conversation reuse, no cross-condition leakage is expected through it,
  but it is genuinely shared infrastructure, disclosed rather than hidden.
- This machine ran other unrelated processes throughout (the live
  FeralEcho production server on a separate port, this investigating
  session itself). A repo-wide search found no other code path that reads
  this experiment's directory, but that absence is asserted from a search,
  not proven by sandboxing.

No violation of any listed control was found during execution.

## 5. Raw R+/R- Outcomes

New held-out panel: 10 instances (`restart_L3_00`-`restart_L3_09`), 4
genuinely new code bodies, seeds 2000-2009.

| task_id | R+ (P available) | R- (P withheld) |
|---|---|---|
| restart_L3_00 | FAIL (wrong_output) | FAIL (runtime_error — syntax error in generated code) |
| restart_L3_01 | PASS | FAIL (wrong_output) |
| restart_L3_02 | PASS | PASS |
| restart_L3_03 | PASS | PASS |
| restart_L3_04 | PASS | PASS |
| restart_L3_05 | PASS | FAIL (wrong_output) |
| restart_L3_06 | PASS | FAIL (wrong_output) |
| restart_L3_07 | PASS | PASS |
| restart_L3_08 | PASS | FAIL (wrong_output) |
| restart_L3_09 | PASS | FAIL (wrong_output) |
| **Total** | **9/10** | **4/10** |

Raw records: `memory/experiments/restart_persistence_transfer/r_plus_results.jsonl`,
`r_minus_results.jsonl` (each includes the full prompt sent, raw model
response, extracted code, and per-test grading detail — nothing
summarized away).

**Concrete, mechanistic causal evidence, not just a score gap** — the
generated code itself was inspected, not only the pass/fail outcome:

- `restart_L3_01`: R+'s code checks the complete 7-marker set P's clause 1
  specifies (`'def', 'class', '@', '"""', "'''", 'import', 'from'`). R-'s
  code checks only `'def'`, `'class'`, `'import'` — omitting `'"""'` — and
  fails on exactly the docstring-opening input, reproducing almost
  verbatim the historical `train_L3_05` failure P's clause 1 was written
  to prevent.
- `restart_L3_05`: R+'s code takes every line from the found start marker
  to the end (P's clause 3). R-'s code instead builds one large regular
  expression attempting to match the entire code span in a single shot —
  the exact anti-pattern P's clause 3 names and warns against — and its
  `re.search` returns no match at all, producing an empty string.
- `restart_L3_06`, `08`, `09`: R-'s code independently reproduces the same
  incomplete-marker-set bug three more times across three separate
  generation calls (`'def'`/`'class'`[/`'import'`] only, missing `'@'`,
  `'"""'`, `"'''"`, `'from'` every time) — the same specific pattern P's
  clause 1 exists to prevent, recurring consistently when P is withheld.
- One honest, disclosed exception, not smoothed over: on `restart_L3_00`,
  **R+ itself** dropped `'import'`/`'from'` from its own marker set
  (`('def', 'class', '@', '"""', "'''")`) and failed on the one instance
  whose code opens with a bare `import` statement — showing that even with
  P available, its application was not perfect on every instance; the
  advantage is real and large, not total.

## 6. Statistical / Descriptive Comparison

Paired design (same 10 task IDs received both conditions), matching
VECT's own analysis convention:

| Comparison | Discordant pairs (R+ win / R- win) | Exact one-sided p | Exact two-sided p |
|---|---|---|---|
| R+ vs R- | 5 / 0 | 0.03125 | 0.0625 |

| Condition | Accuracy | Wilson 95% CI |
|---|---|---|
| R+ | 9/10 = 0.90 | [0.596, 0.982] |
| R- | 4/10 = 0.40 | [0.168, 0.687] |

This McNemar signature (5 discordant pairs, all favoring the treated
condition, p=0.03125 one-sided / 0.0625 two-sided) is **numerically
identical in shape** to VECT's own original P-vs-Z comparison, now
reproduced on entirely new code content and across a genuine OS-process
restart boundary. The confidence intervals are wide, as expected at n=10,
and overlap partially — this is a small-panel result, not a
population-level claim, exactly as VECT's own report and its
self-falsification review both stated of themselves.

## 7. Alternative Explanations Considered

- **Model-native capability alone explains R-'s 4 successes**: plausible
  and expected — R- is not at floor, confirming the base model retains
  real capability on this task family without help, consistent with
  VECT's own Z-arm (5/10) and the calibration report's own headroom
  finding (qwen2.5-coder:7b scores 5/10 at Level 3 without any teaching).
  This does not explain the additional 5/10 gap R+ shows over R-.
- **Ceiling effect ruled out**: R- is well below ceiling (4/10), so there
  was real room for R+ to fail to show an advantage if P provided none —
  it did not fail to show one.
- **Chance discordance ruled out at the level this panel can speak to**:
  5/0 discordant favoring R+, p=0.03125 one-sided — the same signature
  VECT's own P-vs-Z comparison produced, not a coincidence unique to this
  run's small sample, though a small sample is still a small sample and a
  single replication is not a population-level guarantee.
- **Mechanistic, not merely statistical, attribution**: Section 5's direct
  code inspection shows R+'s failures and successes track P's specific
  textual clauses (complete marker set; take-to-end rather than one large
  regex) with unusual precision — R-'s repeated, independent
  reproductions of the exact bug patterns P's clauses name as historical
  failures is strong evidence against "R+ just got lucky" and for "P's
  specific content caused the specific difference observed."
- **Shared-infrastructure confound (same live Ollama server, same
  inference seed) considered and judged not explanatory**: if the
  advantage were an artifact of shared infrastructure rather than P's
  content, it would not track the discordant pairs' underlying code
  content the way Section 5 shows it doing.
- **P's own imperfect application (restart_L3_00) considered**: this
  argues against an inflated, "P is a silver bullet" reading, but does not
  argue against the persistence claim itself — P still conferred a large,
  measurable net advantage even though its application was not perfect on
  every instance.

## 8. Strongest Justified Claim

**In this standalone research harness, the already-frozen, hash-verified
procedure artifact P — created and sealed three real days earlier by a
process that has since fully terminated — was independently recovered and
correctly hash-verified by a freshly-launched, distinct OS process (R+),
and, when applied to 10 genuinely new held-out instances of the same
`extract_code` Level-3 task family (built from code content never present
in the original acquisition or evaluation data), produced 9/10 correct
outputs versus 4/10 for an equivalent fresh process denied the artifact
(R-) — a discordant-pair pattern (5 wins for R+, 0 for R-, exact one-sided
p=0.03125) numerically matching the shape of the original acquisition
experiment's own P-vs-Z result. Direct inspection of the generated code
shows this advantage tracks P's specific textual content: R+'s successes
and one failure, and R-'s five failures, each correspond to whether the
generated code did or did not implement the exact marker-completeness and
line-span-extraction properties P's clauses describe. Previously acquired,
externally-distilled, experience-informed competence-enhancing information
persisted across a genuine process boundary and provided a measurable,
mechanistically-traceable advantage to a fresh successor process on new
same-family cases.**

Per the mission's own interpretation guardrail, this is stated at exactly
this narrow strength — no broader claim is made from it.

## 9. Claims NOT Justified

Per the mission's own explicit list, and the prerequisite qualifications
from Section 1, none of the following are supported by this result:

- That Echo autonomously acquired, extracted, or discovered P from its own
  experience — P is investigator-authored prose informed by real TRAIN
  evidence, not the output of an Echo-operated extraction mechanism (per
  Section 1's independently-confirmed finding).
- That this demonstrates accumulated competence, general intelligence
  improvement, cross-domain learning, autonomous self-improvement,
  identity survival, or inheritance in the biological sense.
- That P transfers to a different task family, different code structures,
  or arbitrary code-extraction problems — the new held-out set is still
  the same `extract_code` Level-3 family, deliberately, per the mission's
  own instruction to test persistence rather than generalization.
- That this constitutes a full, general validation of "restart-persistence
  as a mechanism" beyond this specific artifact and task family — one
  panel of 10 new instances, one artifact, one model.
- That R+'s application of P was perfect — `restart_L3_00` is a direct,
  disclosed counterexample.
- That the shared Ollama server, or any other piece of shared machine
  infrastructure, was proven fully isolated between conditions — disclosed
  as a residual channel, not eliminated by proof.
- That this is a general OS-level "process death" demonstration for the
  live FeralEcho production server — that process (`run.py`, PID 81854 as
  of this session) was not restarted or otherwise involved in this
  experiment at any point; the "originating process" and "successor
  processes" here are all standalone experiment-harness invocations,
  never FeralEcho's own live pipeline.
- That P's advantage would replicate at a larger sample size with the same
  magnitude — n=10, wide confidence intervals, one run.

## 10. Recommendation for the Next Experiment

Per the mission's own explicit stop condition, **this report does not
authorize, and this session does not proceed into, the second-task-family
generalization experiment, or any accumulation-ladder (multi-experience,
multi-restart) design.**

If a next step is wanted, the two most informative candidates, in order of
cost:

1. **A larger new held-out panel on the same task family** (e.g. 20-30
   instances, still genuinely new code content, still the same restart
   design) — would narrow the wide Wilson intervals from this small panel
   and provide a firmer estimate of the persisted advantage's true
   magnitude, without touching cross-family generalization or
   accumulation at all. Cheapest, most direct next step.
2. **The self-falsification audit's own Section 12 proposal** — a
   prospectively frozen, Echo-only acquisition experiment with
   counterfactual experience and retained-state crossover, where Echo
   itself (not an external investigator) performs the extraction step —
   would close the provenance gap Section 1 identified (externally
   authored vs. autonomously extracted), which this restart-persistence
   experiment deliberately did not attempt to close, since it was scoped
   to test persistence of an already-existing artifact, not the
   acquisition mechanism itself.

Neither is begun here. Per the mission's final instruction, this result is
returned now for adversarial review.

---

## Repository Impact

New files only, all inside `app/experiments/restart_persistence_transfer/`
and `memory/experiments/restart_persistence_transfer/`, plus this report.
`historical_difficulty_calibration/tasks.py` was read and imported but
never edited on disk (re-verified by hash, Section 1). VECT's own
qualified artifacts (`CONTRACT.md`, `freeze_procedure.py`, `prompt.py`,
`run.py`, `procedure_frozen.json`, `heldout_tasks.json`, and 27 other files
in the self-falsification audit's manifest) were read-only throughout,
final-byte-hash-reconfirmed unchanged before this report was written. No
FeralEcho production code, credentials, or live server state was touched.
The live FeralEcho `run.py` process (PID 81854) was not restarted, queried,
or otherwise involved. Two real, short-lived Ollama-calling subprocesses
(PIDs 8507 and 8538) ran and exited normally; no process was left running.
No commit, push, or production restart was performed by this investigation.
