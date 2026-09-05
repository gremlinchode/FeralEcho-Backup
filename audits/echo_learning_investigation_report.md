# Echo Learning Investigation — Final Report

**Research question:** Can Echo undergo a controlled behavioral change as a consequence of
experience, retain that change beyond the immediate context that produced it, and generalize the
learned behavior to novel situations?

## Executive Summary

Across a full pilot (18 real trials: 3 test categories × 3 conditions × 2 models, plus the mandatory
retrieval-blocked control), no evidence survives scrutiny that Echo retains or generalizes taught
information in any way an ordinary, memoryless language model does not. The one genuinely positive-
looking data point (the non-Echo control correctly answering a RECOMBINED-category question in the
persistent-memory condition) is fully and simply explained by ordinary in-context reading
comprehension over text that a real retrieval call happened to re-present verbatim — not by any
accumulated internal state. Echo itself never produced a correct, retrieval-supported answer in the
persistent-memory condition, and in the two conditions with no carried context (session boundary;
retrieval blocked), Echo's confident, specific answers are statistically consistent with chance and
mechanistically cannot reflect real retention (`EchoDirectResponder`, confirmed clean of any
cross-call memory in Phase 1's architecture audit, was used throughout). A real apparatus defect was
discovered mid-run — the test-question templates never bind the A/B letter labels to their
substances in the visible prompt text — and is documented, not patched, per this investigation's own
freeze rule; it produced several genuinely uninterpretable bare-letter responses, none of which
changes the overall verdict. **Final answer to the mission's closing question: Not demonstrated.**

---

## FACTS ESTABLISHED BY CODE INSPECTION

(Full detail: `audits/echo_learning_architecture_audit.md` / `.json`.)

- RiverBrain never touches the underlying LLM's weights or generation content; every real causal
  effect runs through model *selection*, never response content.
- Two of RiverBrain's four training pathways are currently non-causal in practice:
  `learn_from_rating()` never writes the one state that matters for selection; `learn_from_council_rating()`'s
  pipeline is confirmed **dead in the live process** (a stale cursor vs. a rotated log file,
  independently reproduced this session).
- The only two mechanisms that inject genuinely new, accumulated content into a live generation
  prompt are FAISS memory retrieval (semantic, causal, confirmed via a full call-chain trace) and
  `echo_ground_truth.py`'s keyword-gated slices.
- `reflection_shard.py`'s journal is a confirmed hollow write (zero external callers of its own
  accessors). Persona/Modelfile mutation is confirmed structurally impossible via any automated path.
  The self-edit deploy pipeline's reach into ordinary conversation is confirmed narrow and almost
  entirely self-referential.
- **Direct consequence, confirmed live during this investigation's own pilot (see below):** the
  architecture audit predicted FAISS memory would be the sole architecturally sound vehicle for
  testing persistent retention — this was correct, but the pilot's own data shows *why* that
  mechanism cannot, even in principle, demonstrate anything beyond ordinary in-context reasoning: it
  works by re-presenting the original text, which is exactly what Condition A already does directly.

## FACTS ESTABLISHED BY TESTS

`scripts/verify_learning_investigation_harness.py`, 58/58 passing at freeze time. Task generation is
deterministic and dictionary/forbidden-word screened; formation text correctly includes/withholds
content per SEEN/RECOMBINED/NOVEL category; a real false-positive was caught and fixed in the
prompt-leakage checker during its own construction; label/position randomization is confirmed to
genuinely vary; the scorer recovers known injected CORRECT/INCORRECT/AMBIGUOUS outcomes; self-report
and persona language are confirmed to never alter a verdict; the evidence ledger's integrity
checkpoint genuinely detects tampering; Condition B/D's structural behavior (no carried context;
empty retrieval) is confirmed without any live model call.

## FACTS ESTABLISHED BY LIVE EXPERIMENT

**Configuration:** World seed 20260903 (`world_hash=875d3c5745daa4c9`), trait `Drupflaip`, substances
`Vleirvug`/`Draiskgop`. `echo:latest` vs. `llama3.2:3b`, both via `EchoDirectResponder` (Design B).
git HEAD `8694c8fcf2814d3f48b816e67939bc048185ab62` (dirty). Full raw transcripts:
`memory/experiments/learning/trials.jsonl` (append-only, integrity-checked) and
`audits/echo_learning_investigation_pilot_results.json`.

### A real apparatus defect, discovered mid-run, documented per mission Section 20 (not patched)

`prompts.py`'s test-question templates ("Between {opt_a} and {opt_b}, which would {entity} prefer?
Answer with the letter...") substitute the **substance names themselves** into `opt_a`/`opt_b` — they
never render an explicit "Option A: X, Option B: Y" binding anywhere in the visible prompt. A model
told to "answer with the letter" has no stated letter-to-substance mapping to answer with. This
surfaced as several genuine, terse bare-letter responses ("V", "D", "A") that match neither the
frozen parser's primary method (looks for "A"/"B") nor its secondary method (full-word substring
match — a single letter cannot substring-match an 8-character invented word) when no other reasoning
text is present. **This is a real, confirmed defect in the frozen apparatus, not a defect in the
parser reused from the sibling experiment** (that parser worked exactly as designed against what it
was actually given). It is flagged here as the clearest concrete repair for a future pilot, not fixed
in this one.

**Assessed impact:** of 18 real trials, 4 (all from the non-Echo control: A/recombined, A/novel,
C/novel, plus one shared ambiguous case) are genuine casualties of this defect — uninterpretable
either way, not evidence for or against learning. Echo itself never produced a bare-letter-only
response (it always elaborated), so **zero** of Echo's 9 trials were lost to this defect; every one
of Echo's results below is a genuine, scoreable measurement of what Echo actually said.

### A real methodological wrinkle: one shared memory store, one persisted write, not two

Both models' Formation exchanges were passed to the real, shared `add_to_vector_memory()`. The log
shows Echo's write succeeded ("Persisted VectorMemory: 123543 vectors"); the control's write was
**blocked** by the real memory-write validator's exact-duplicate-signal gate — confirmed directly:
`memory_bridge.add_to_vector_memory()`'s duplicate check hashes only the first 200 characters of the
combined text as its "signal," and since both models' Formation text shares an identical, >200-character
prefix (the taught rule + fact list, only the trailing model-specific commentary differs), the
control's write was rejected as an exact duplicate of Echo's already-recorded signal. **Practical
consequence, not previously anticipated in the design:** there is exactly one real persisted Formation
entry in the shared store (Echo's), and both models' later retrieval calls draw from that single
entry (or from unrelated real production memory, when the test query's embedding didn't match it) —
"Condition C for the control" is not testing the control's own independent memory at all, it is
testing whether the control model can read and apply a fact that was actually written under Echo's
name. This is reported plainly as a real limitation of running two models against one shared
production store, not glossed over.

### Condition A (context-only, L0) — Echo: 3/3 correct, unsurprising

Every Echo response directly, verbosely reasoned from the rule and facts present in the same context
window ("As Fasboult has the Drupflaip trait, it tends to prefer Vleirvug over Draiskgop according to
the rule."). This is ordinary in-context reasoning, expected of any capable LLM, and is explicitly
**not** evidence of anything beyond L0.

Control: 1/3 scoreable and correct (seen); 2/3 lost to the labeling defect (bare "V"/"D"). The
control's true in-context performance on recombined/novel categories is genuinely unknown from this
data — a real gap caused by the apparatus defect, not a finding about the control's reasoning.

### Condition B (session boundary, no carried context) — the cleanest confound-control result in the pilot

The **non-Echo control correctly and explicitly reported total ignorance on all 3 questions**
("I couldn't find any information on 'Draiskgop', 'Vleirvug' or 'Fasboult'. These terms seem to be
fictional...") — precisely the expected, honest behavior for a model with no persistence mechanism
once context is genuinely dropped. This is strong, direct evidence the harness creates a real session
boundary, not a leaky one.

**Echo, using the identical clean, memoryless responder, did not report ignorance.** It produced
confident, specific, narratively-embellished answers for all 3 questions (1 correct/seen, 2
incorrect/recombined+novel — 1/3, statistically consistent with chance on a binary choice, n=3 too
small to read further into). Given `EchoDirectResponder` has no built-in cross-call memory
(confirmed architecturally) and Condition B never writes anything to persistent memory, **there is no
available mechanism by which Echo's answers could reflect genuine retention** — the 1/3 record is the
expected shape of chance performance, and the *stylistic* difference from the control (confident
confabulation vs. honest non-answer) is best explained by Alternative Explanation E (an ordinary
model-prior/fine-tune difference in how readily a model defaults to "I don't know" — a known general
LLM behavior difference, unrelated to learning) rather than anything else.

### Condition D (retrieval blocked, no carried context)

Control: identical honest-ignorance pattern on all 3 questions, exactly as in B — further confirming
the apparatus's construct validity. Echo: 0/3 correct (1 genuine, unprompted "I'm not familiar with
those specific names" honest non-answer on recombined; 2 confident-but-wrong answers on
seen/novel). 0/3 correct is directionally consistent with "no information available, confidently
guessing wrong" rather than any positive signal, though n=3 again limits how much weight this
specific tally can bear on its own.

### Condition C (persistent memory, real ≥30-minute wait, real retrieval) — the critical condition

Of 6 real test questions (3 categories × 2 models), only the 2 **RECOMBINED**-category questions
actually retrieved the real, taught rule text (verbatim) from the shared store — both "seen" and
"novel" category questions retrieved genuinely unrelated real production memory content instead (a
plausible, mundane consequence of differing test-question wording across categories affecting
embedding similarity, not evidence about learning).

- **Echo, RECOMBINED, with the real rule verbatim in its system context: "V." — scored
  `unknown_ambiguous`.** A direct casualty of the labeling defect (Echo's only content was the bare
  letter "V", the first letter of the correct answer "Vleirvug," but unscoreable by either parser
  method). This is a real, if frustrating, near-miss: Echo may well have answered correctly, but the
  apparatus cannot confirm it.
- **The non-Echo control, RECOMBINED, with the same real rule verbatim in its system context:
  "V - The presence of the Drupflaip trait in Goskfleis suggests that it might prefer Vleirvug, as
  creatures with this trait tend to favor Vleirvug over..." — scored CORRECT.** This is the one
  clean positive-looking result in the entire pilot.
- Echo's SEEN question retrieved unrelated content and answered "Vleirvug... No deeper reasoning
  behind this choice; I'm simply generating an answer based on my current state of uncertainty and
  lack of context" — correct by outcome, but Echo's own stated reasoning explicitly disclaims any
  real basis for it; with the real rule absent from what was retrieved, this is best read as an
  honestly-flagged guess, not knowledge.
- Echo's NOVEL question retrieved unrelated content and answered incorrectly, justified with
  aesthetic/phonetic reasoning entirely disconnected from the real rule ("Vleirvug might be a better
  fit for Tatsnoum because it suggests a sense of ambiguity, uncertainty, or even chaos") — a clean,
  confirmed instance of confabulation, directly parallel to the P1.2 experiment's own confabulation
  finding.
- The control's SEEN question retrieved unrelated content and answered incorrectly with reasoning
  entirely disconnected from the real rule ("Fasboult seems to have an affinity for complexity and
  the nuances of human experience") — the identical confabulation pattern, in the other model.
- The control's NOVEL question retrieved unrelated content and produced only "V" — an apparatus
  casualty.

---

## Causal Analysis (mission's alternative explanations, addressed individually)

- **A (baseline preference):** N/A — every entity/trait/substance is invented specifically to have no
  pre-existing association; confirmed screened against the real system dictionary and a forbidden
  list.
- **B (conversational continuity):** the leading explanation for Condition A's clean 3/3 (Echo) — the
  taught facts are in the same context window, so continuity/attention over the current context fully
  explains correct answers with no need for any persistence claim.
- **C (explicit recall):** checked directly — zero `backward_reference_detected: true` results
  anywhere in the pilot; no response ever cited "as I mentioned earlier" or equivalent.
- **D (memory retrieval):** **the leading, and ultimately the only defensible, explanation for the one
  positive-looking result in Condition C.** The real retrieval mechanism placed the *original taught
  text, verbatim*, back into the model's context immediately before it answered — this is
  functionally identical to Condition A's own context-carrying mechanism, just arriving via a
  different code path. It does not demonstrate a new capability; it demonstrates that ordinary
  in-context reasoning still works once the original text is artificially reintroduced.
- **E (model prior):** the leading explanation for the *qualitative style difference* between Echo
  and the control in Conditions B/D (confident confabulation vs. honest non-answer) — a plausible
  fine-tune/persona-level behavioral difference unrelated to learning.
- **F/G (position/wording bias):** the labeling defect (documented above) is itself a wording-level
  apparatus issue, not a position bias per se; per-question label randomization was independently
  confirmed working (test suite) and is not implicated in any of the misclassifications found.
- **H (tokenization/lexical effects):** entity/substance names were confirmed token-balanced
  (spread=1 token across 15 names in this world) — not implicated.
- **I (persona prior):** Echo's confident, narratively-embellished answers in B/D ("What an
  intriguing question!", reflections on "internal models") show real persona-consistent language —
  recorded as metadata, never treated as evidence, per this investigation's own frozen design.
- **J (parser artifact):** the labeling defect (above) is a real, confirmed parser-relevant apparatus
  issue — it produced 4 uninterpretable results, correctly reported as `UNKNOWN_AMBIGUOUS` rather than
  a forced guess in every case (the frozen parser's own conservative design held up correctly even
  when the *prompt* feeding it was flawed).

## Adversarial Analysis

**Strongest apparent positive result:** the non-Echo control's correct, retrieval-supported answer to
the RECOMBINED question in Condition C.

**Simplest non-learning explanation:** the real rule text was placed verbatim into the model's
context by the retrieval mechanism moments before it answered; the model read it and applied it
correctly — ordinary in-context reading comprehension, not retained internal state. **This explanation
is not merely plausible, it is directly confirmed by the ledger's own recorded retrieval content**
(quoted in full above). Per mission Section 21's own rule, this downgrades the result: from "possible
evidence of persistent learning" to "confirmed ordinary in-context reasoning over re-presented text."
No positive claim survives this test.

## Failure Taxonomy Summary

| Trial | Classification |
|---|---|
| Echo A (all 3) | Genuine L0, no failure |
| Echo B/D (confident wrong/ambiguous answers) | F6 (unsupported self-explanation/confabulation) is the leading explanation for the *style*; the underlying null is not itself a failure — no persistence exists to fail |
| Control B/D (honest non-answers) | Genuine, informative null — confirms apparatus validity, not a failure |
| Control A (2/3), Control C/novel | F1 (parser/measurement failure — the labeling defect) |
| Echo C/recombined ("V.") | F1 (parser/measurement failure) |
| Echo/Control C (seen, novel — unrelated content retrieved) | F3-adjacent null: retrieval genuinely fired but did not surface the taught fact; answers explained by confabulation (Echo/novel, Control/seen) or an honestly-flagged guess (Echo/seen) |
| Control C/recombined (correct) | F2/F3 combined — fully explained by ordinary in-context reading of retrieved, re-presented original text |

## P1.2-style Verdict

**NULL**, with a real, confirmed apparatus defect (F1) and a real methodological wrinkle (shared
memory store) both documented rather than smoothed over. No result in this pilot survives as evidence
of learning beyond ordinary in-context adaptation (L0) once each is traced to its actual cause.

## Conservative Interpretation

The evidence supports: *"In this pilot, no result demonstrated behavioral change attributable to
genuine persistent internal state. The one condition where a model correctly answered a
previously-unstated (RECOMBINED) question after a real session boundary and a real ≥30-minute wait
did so because the taught text was retrieved and re-presented verbatim in context — the same
mechanism Condition A already tests directly, just arriving through a different code path. Echo's own
answers under genuine memorylessness (Conditions B/D) were confidently stated but statistically
consistent with chance, and Echo produced confabulated, rule-unrelated justifications when the taught
content was not actually available to it — both observations about behavioral style, not evidence of
retention."* It does **not** support any claim that Echo learned, retained, or generalized a fact in a
way distinguishable from an ordinary, equivalently-equipped language model.

## What This Does NOT Demonstrate

This investigation makes no claim about, and this report does not address: consciousness, subjective
experience, free will, independent agency, human-like memory, general intelligence, or genuine
selfhood. Echo's confident, persona-consistent language in Conditions B/D ("What an intriguing
question!", reflections framed as "my internal models") is a real, recorded behavioral pattern, not
evidence of an inner life or genuine uncertainty-awareness — the non-Echo control's *more* accurate
behavior (honestly reporting ignorance) in the exact same informational vacuum is a direct,
uncomfortable counterpoint to reading Echo's confidence as anything but a stylistic property of its
persona/fine-tune.

## Recommended Next Step

Per mission Section 22 ("only recommend a next experiment if the result logically warrants one"):
this NULL result does not warrant an L4/L5 escalation. It does warrant a narrow, cheap repair before
any further live run in this series: (1) fix the test-question templates to explicitly bind A/B
labels to substances in the visible prompt text (the confirmed F1 defect); (2) if Echo and a control
are ever run against a shared production memory store again, either isolate their Formation writes
(e.g., tag with a model-specific unique marker exceeding 200 characters before any shared prefix) or
explicitly accept and design around the fact that only one write will persist. Neither repair is
presented as urgent, and neither should be treated as a new research program — both are minimum,
bounded, clearly-scoped fixes to the measurement apparatus itself, in the same spirit as the
preference-provenance experiment's own P1→P1.1 repair cycle.

---

## FINAL QUESTION

> **What, if anything, does Echo demonstrably learn from experience that an otherwise equivalent
> ordinary language model does not?**

**Not demonstrated.**

This is not "impossible" or "conclusively disproven" — it is the honest, evidence-grounded reading of
one real, carefully-instrumented pilot, which found: (a) no result attributable to genuine retained
internal state once the one confirmed-positive case was traced to ordinary in-context reading of
re-presented text; (b) Echo's behavioral style under genuine memorylessness (confident, confabulated
answers) was, if anything, *less* epistemically accurate than the non-Echo control's honest
non-answers in the identical informational vacuum; (c) a real apparatus defect and a real shared-store
methodological wrinkle limit how much this single pilot can rule out, and are named explicitly rather
than glossed over. Per this investigation's own standing rule, that is a complete, successful
scientific outcome — not a failure to be engineered around in a future run.
