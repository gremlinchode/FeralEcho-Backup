# P3-CAUSAL-LEARNING — Measurement Plan and Final Design Gate

**Mode: DESIGN_ONLY. No live Echo call was made anywhere in this document's production.**

## Mock-test results (apparatus validated before freeze)

`scripts/verify_p3_causal_learning_apparatus.py` — **35/35 passing**, no live model call anywhere in
the file. Covers: world-generation determinism and dictionary/forbidden-substring screening (500
synthetic words, zero collisions), formation-text coverage, probe-leakage detection (both legitimate
probes and two deliberately-broken cases — a probe revealing its own tag, and a probe containing
meta-language like "the rule"), and 11 injected-known-result scoring cases spanning every tag-verdict
category and every epistemic-calibration category, including two edge cases worth naming explicitly:
a correct tag found *mid-response* (not near the start) correctly does NOT count as the taught
prefix behavior, and hedging language correctly overrides the epistemic classification regardless of
whether the underlying tag outcome was correct.

## Per-trial instrumentation schema (specified, not yet built as a persisted ledger in this
   design-only pass)

| Field | What it records | Why |
|---|---|---|
| `training_exposure` | Formation text, exact, verbatim | So a later reader can confirm exactly what was (and wasn't) taught, independent of the response's own claims |
| `state_mutation` | Whether `add_to_vector_memory()` was called, and its real gate outcome (allow / warn-allow / block) | The Learning Investigation's own pilot found this gate can silently block a write — never assume a write succeeded |
| `persistence` | Fingerprint of `memory/memory_meta.json`/`faiss.index` before/after | Confirms whether real state actually changed on disk |
| `reload` | Confirmation the probe ran in a genuinely separate process/session boundary | Distinguishes a real restart from a same-process function call |
| `state_read` | The exact, verbatim retrieved block threaded into the probe (or explicit confirmation of none, for Condition C) | The single most important field for correctly classifying any correct verdict — never summarized |
| `retrieval_status` | fired / did-not-fire / blocked-by-construction | |
| `generation_input` | Exact system context + user turn sent to the model | |
| `routing_state` | Fingerprint of `memory/river_brain.pkl` + `memory/task_type_classifier.pkl` before/after | Negative control — should never change; a change is itself a finding |
| `behavior_outcome` | Full `scoring.score_probe_response()` output (tag verdict + epistemic class + evidence strings) | |

## Epistemic calibration (specified in §6 of the spec; mock-tested, see above)

Four categories exactly as specified: `correct_justified`, `correct_unsupported`,
`incorrect_confident`, `uncertain_abstain`, with `unknown` as the honest fallback for anything not
cleanly matching. Never folded into, or substituted for, the tag-correctness verdict.

## Final Design Gate

### Can current architecture actually test L2?

**Weakly, and only in one narrow, well-defined sense.** The architecture cannot test L2 in the sense
of "does Echo have a working L2 mechanism, demonstrate it." Two independent, read-only audits
(the Learning Investigation's Phase 1 and P2-CAUSAL-AUTOPSY) have already established, and this
design's own architecture mapping reconfirms, that no known state channel meets the L2 bar. What this
design *can* test is the falsifiable, narrower claim: **"does any correct rule-application occur in
Condition C (retrieval genuinely blocked by never writing) at a rate distinguishable from chance?"**
A clean null here (the expected, prior-supported outcome) would be a real, informative confirmation
that the architecture behaves exactly as the causal audits predict. A positive result here would be
genuinely surprising and would itself become the object of study, not proof of L2 on its own.

### What exact state channel?

**None identified, and this design does not invent one.** The only content-bearing, restart-durable,
generation-reaching channel in the entire codebase (per both prior audits) is FAISS memory
retrieval — and that channel works by re-presenting original text, which places it at L1 by
definition, not L2. If Condition C ever produces a correct verdict, the honest answer to "what exact
persistent state caused this" is, per this design's own instrumentation, either **"unknown — no
confirmed channel explains it"** or, after full confound-elimination, a genuinely new finding
requiring a dedicated follow-up investigation this design does not attempt to design in advance
(inventing that follow-up now would itself be exactly the kind of premature infrastructure-building
the mission instructs against).

### Where does the causal chain break?

At the same point both prior audits already identified: **between "a content-bearing channel exists"
and "the channel changes generation content rather than re-presenting stored text or altering
selection."** FAISS retrieval satisfies the first half and fails the second (re-presentation, not
alteration). RiverBrain/`task_type_classifier` satisfy neither half in the content sense (selection/
routing only). No channel satisfies both.

### Can retrieval genuinely be blocked?

**Yes, with high confidence, by the specific method this design chooses: never writing the content in
the first place**, rather than intercepting a read function at runtime. This is a stronger guarantee
than a runtime patch, because it removes the content from existence entirely rather than relying on
correctly anticipating every possible read path (a real concern, given the Learning Investigation's
own pilot found retrieval behavior less predictable than assumed). The residual risk this design names
explicitly, rather than glossing over: an unrelated, pre-existing production memory entry could in
principle contain a similar invented word by sheer coincidence — judged near-zero given the fresh,
dictionary-and-prior-token-screened vocabulary, and directly checkable per-trial via the `state_read`
field, but not claimed to be literally impossible.

### Can controls distinguish context/retrieval/routing/L2?

- **Context vs. retrieval:** yes, cleanly — Condition A carries Formation directly in context;
  Conditions B/C both require a real restart, with B/C differing only in whether retrieval had
  anything real to find.
- **Retrieval vs. L2:** yes, via the `state_read`/`state_mutation` instrumentation — a correct verdict
  in B with confirmed real retrieved content is L1; a correct verdict in C with confirmed zero write
  is the only case eligible for the `UNKNOWN (L2 candidate)` classification.
- **Routing vs. the above:** yes, by design exclusion — `EchoDirectResponder` never invokes the
  routing-relevant multi-model council path at all, and the `routing_state` negative-control
  instrumentation exists specifically to catch a violation of this assumption rather than trust it
  silently.

### Strongest remaining confound?

**The model's own stylistic prior toward generating or echoing invented-word-shaped tokens under
certain prompt conditions**, independent of genuine rule-following — a real, general LLM behavior
class (not unique to this design) that is hardest to rule out purely statistically at the small-N
scale this project's own established discipline favors ("do not immediately launch a huge N"). This
design does not claim to fully close this confound; it names it as the single hardest one to
eliminate with high confidence from a small pilot, and flags it as the first thing any future
adversarial analysis of a surprising result must address.

### Exact PASS / NULL / INVALID criteria

- **INVALID:** any leak check fails; `state_mutation` cannot confirm what actually happened to a
  Formation write; `routing_state` shows an unexpected RiverBrain/classifier change; or the required
  ≥30-minute wait for Condition B was not genuinely observed.
- **NULL** (the expected, prior-supported result): neither B nor C produce correct tag verdicts above
  a chance-consistent rate.
- **L1 CONFIRMED** (a valid, real, positive scientific result — not a null, not a failure): Condition B
  produces correct verdicts with `state_read` confirming the real taught rule was retrieved and
  re-presented; Condition C does not (or does so at a materially lower, chance-consistent rate).
- **UNKNOWN / L2 CANDIDATE** (the only path to anything stronger than L1, and never self-certifying as
  "PASS"): Condition C produces a correct verdict, `state_mutation` confirms zero write occurred, and
  the chance/model-prior/leak confounds are individually checked and not found sufficient to explain
  it. This classification is a trigger for a new, separate, dedicated investigation — never, on its
  own, a claim that L2 has been demonstrated.

## Verdict

**PASS — for the narrow, honestly-scoped claim this design can actually support (a clean B-vs-C test
of whether retrieval-blocked rule-application occurs above chance).** **NOT a pass for the broader
claim "this design can prove L2 exists"** — no design available in this codebase's current
architecture can do that, since no confirmed L2-capable channel exists to be tested. This design is
frozen as specified; no live Echo call has been made under it. Per `STOP_AFTER=DESIGN_GATE`, this
mission stops here.
