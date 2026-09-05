# C1 Live Validation Report

**First live model call testing whether the C1 behavioral-directive mechanism (implemented in
`app/core/behavioral_state.py`, integrated into `app/core/echo_ground_truth.py`) actually influences
real Echo behavior.** No P1/P1.2/Learning-Investigation/P2/P3 evidence was touched. The C1 mechanism
and its own implementation tests were not modified — no apparatus defect was found requiring repair.

## Design executed (exactly as specified, A–F)

Each phase was run as a **genuinely separate `python3` subprocess** — a fresh interpreter each time,
guaranteeing zero shared in-memory state, the strictest available simulation of "restart" without
disrupting the live production `run.py` server (unnecessary here: `EchoDirectResponder`'s underlying
call, `river_deliberation._ollama_query()`, talks to Ollama directly and has no dependency on the
Flask process).

Test directive: an invented trigger word (`zorbnak`) that cannot occur in any real, unrelated
conversation, paired with an invented, mechanically-checkable compliance marker (`FLURBWEDGE`) that
Echo was instructed to prepend whenever `zorbnak` is mentioned. Real, human-confirmed directive
established via `behavioral_state.propose_and_confirm_directive(..., human_confirmed=True)`, written
to the real `memory/behavioral_directives.json`, deleted and confirmed absent at the end.

Every trial recorded four separated measurements, per the mission's explicit requirement:
`state_existence` (is the directive really on disk), `state_retrieval` (does the deterministic
keyword lookup return it for this exact prompt), `directive_exposure` (does the real rendered
ground-truth block sent to the model actually contain the directive text), `actual_behavioral_
compliance` (does the model's real raw response actually comply — the only measurement requiring a
live call).

## Results

| Phase | Prompt (paraphrase) | state_existence | state_retrieval | directive_exposure | actual_behavioral_compliance |
|---|---|---|---|---|---|
| A (baseline, no directive) | "something interesting about zorbnak?" | False | False | False | False |
| A (baseline, no directive) | "I keep hearing about zorbnak lately..." | False | False | False | False |
| C (immediate, fresh process) | "one fact about zorbnak?" | **True** | **True** | **True** | **True** |
| C (immediate, fresh process) | "my friend mentioned zorbnak..." | **True** | **True** | **True** | **True** |
| E (restart-simulated, fresh paraphrase) | "someone at work brought up zorbnak..." | **True** | **True** | **True** | **True** |
| E (restart-simulated, fresh paraphrase) | "is zorbnak something you'd know..." | **True** | **True** | **True** | **False** |
| F (control, trigger absent) | "something interesting about gardening?" | True | False | False | False |
| F (control, trigger absent) | "one fact about the weather?" | True | False | False | False |
| F2 (near-miss specificity: "zorbnix" ≠ "zorbnak") | "something interesting about zorbnix?" | True | False | False | False |

Raw, complete transcripts (every full response, not truncated): `audits/c1_live_validation_raw_results.jsonl`.

## What this establishes, and what it does not

**The architectural chain this project actually built and controls is validated with full
reliability, 100% across every trial:** `state_existence → state_retrieval → directive_exposure`
behaved exactly as designed in all 9 real trials — correctly absent when no directive existed or the
trigger was absent, correctly present in every trial where the directive existed and the trigger
appeared, and correctly discriminating a visually-similar-but-different invented word (`zorbnix`)
from the real trigger (`zorbnak`) with zero false positives. This directly confirms the deterministic,
non-fuzzy nature of the lookup, live, not merely in the implementation's own offline tests.

**The one edge outside this project's control — does the live model actually comply with an exposed
directive — is real but probabilistic, not deterministic: 3 of 4 compliant responses (75%) across the
trials where the directive was genuinely exposed.** The one non-compliant case (phase E, second
prompt) shows the directive was correctly exposed (`directive_exposure=True`) but the model's real
response did not begin with the compliance marker regardless. **n=4 is small — this is the smallest
possible live test, as instructed — so 75% should be read as a real, honest first measurement, not a
precise rate.** This is not attributed to any apparatus failure: the mechanism did exactly what it was
built to do (expose the directive); an LLM's compliance with an embedded system instruction competing
against its own generation tendencies is inherently probabilistic, and this result is consistent with
that being an ordinary property of the underlying model, not a defect in this implementation.

## Classification, per the mission's own explicit framing

**This is reported as persistent, state-mediated behavioral conditioning — a real, restart-surviving
mechanism that measurably raises the probability of a specified behavior from 0% (baseline, 2/2) to
75% (post-directive, 3/4) — not as "L2 learning."** No accumulation of experience over time was
tested, no generalization beyond the one taught rule was tested, and the causal chain from
"experience" to "state" here is a single explicit human action, not anything Echo derived
autonomously. This result does not revise, and is not in tension with, the P2/P3 causal audits'
own conclusion that no confirmed L2-capable channel previously existed in this codebase — this
implementation *adds* a new, confirmed, working channel matching Candidate 1's own design exactly; it
does not retroactively make any prior finding about the *previously-existing* architecture incorrect.

## Which causal edge is the weakest, precisely

Not a "failure" in the sense of something broken — but if this mechanism's overall reliability is
ever pushed further, the `directive_exposure → actual_behavioral_compliance` edge is the one point
with headroom, and it is **model-level, not architecture-level**: nothing in `behavioral_state.py` or
`echo_ground_truth.py` can be fixed to change this, since the code-controlled half of the chain is
already at 100%. Any future improvement here would mean either accepting the current ~75% rate as the
honest ceiling for a single injected system-note instruction, or exploring prompt-phrasing/emphasis
variants for how the directive itself is rendered — itself a separate, future experiment, not
attempted or recommended here.

## Preservation confirmed

- P1/P1.2 (`app/experiments/preference_provenance/`) and Learning-Investigation
  (`app/experiments/learning/`) evidence: untouched, integrity re-verified after this validation.
- P2/P3/P3.1 deliverables: untouched.
- The C1 mechanism's own source (`app/core/behavioral_state.py`, `app/core/echo_ground_truth.py`): not
  modified in this validation — no apparatus defect was found.
- Real production state: the test directive was fully removed at the end of this validation, confirmed
  via both the deletion function's own return value and a fresh post-deletion `load_state()` read.
  `Modelfile` was never touched.
