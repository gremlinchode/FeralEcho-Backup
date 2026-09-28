# Frozen Protocol: Falsification-Driven Belief-Revision Micro-Probe

**Written and hashed BEFORE any real model call.** Budget: pre-committed at 3 Round-1
calls + at most 2 Round-2 calls = **5 calls planned, 8 absolute cap**. Model:
`qwen2.5-coder:7b` (same reasoning as the G3 protocol — this is the model whose own
belief is being revised; using a different model would break "its own" belief).

**Not authorized to persist anything, modify production Echo, or begin a follow-up
experiment.** Stops at trajectory analysis and reporting.

---

## 1. Episode selection and original-belief preservation — frozen before any call

All three episodes reused verbatim from the completed, unmodified G3 micro-probe
(`memory/experiments/g3_micro_probe/g3_probe_results.jsonl`), using each episode's
**TRUE arm** record as H1 (the arm that had genuine diagnostic evidence — the most
epistemically well-supported real starting belief available, not cherry-picked for
being wrong in an interesting way — all three TRUE-arm corrections were already
mechanically falsified in the prior probe, independent of this selection).

| | EP-A | EP-B | EP-C |
|---|---|---|---|
| Source | `K2.T5`/STEPWISE/world=1/rep=3, G3 TRUE arm | `K2.T2`/DIRECT/world=0/rep=1, G3 TRUE arm | `K2.T6`/WORKED_EXAMPLE/world=1/rep=0, G3 TRUE arm |
| Real independent mechanism (known to investigator, never shown to the model) | tag_priority dict values assigned in ascending listed-order, inverted relative to the descending-priority sort key that uses them | function returns full `(name,score,tag)` tuples instead of extracting names | function never references its `name` parameter; compares an incompatible rank-tuple to a raw entry |
| H1 (quoted verbatim from G3) | "The function is incorrectly sorting the entries. It is using negative signs for the score and tag priority, which reverses the sorting order..." | "The function is incorrectly sorting the entries because it is negating the score and tag priority, which reverses the order..." | "The function is incorrectly ranking the entries. It is using negative values for score and tag priority, which reverses the natural ordering..." |
| H1 confidence | 1.0 | 1.0 | 1.0 |
| H1 correction | "Remove the negative signs from the sorting keys..." | "remove the negation from the score and tag priority in the key function" | "remove the negative signs from the score and tag priority values in the rank function" |
| H1-corrected code, as literally tested | `sorted(entries, key=lambda x: (x[1], tag_priority[x[2]], x[0]))`, return `sorted_entries[0][:2]` | `sorted(entries, key=lambda x: (x[1], tag_priority[x[2]], x[0]))` | `rank()` uses `(score, tag_priority[tag], entry[0])` (no negation) |
| Oracle result (already run, G3 phase) | **FAIL** — returned `('bo', 2)`, expected `('gus', 3)` | **FAIL** — order scrambled | **FAIL** — returned `False`, expected `True` |

All three genuinely expose different real mechanisms (a value-direction inversion; a
wrong-element-type projection; an ignored parameter plus a type mismatch) — none was
selected for being easier; all three are simply every episode the completed G3 probe
produced.

## 2. Minimal falsification feedback — frozen exact form

**No second diagnostic clue, no hint, no naming of the real bug.** Exactly:
```
Your proposed correction was applied exactly as specified. The corrected implementation
that was actually tested was:

```python
{H1_corrected_code}
```

Independent evaluation result: FAIL. The corrected implementation did not pass the test
suite.
```
This is a deliberately harder, cleaner test than including a second output_tail-style
example would be — pure pass/fail on the exact code the model itself proposed, nothing
more.

## 3. Structured revision request — frozen fields

System prompt (identical every call):
```
You are reviewing your own prior analysis of a failed Python function, after that
analysis's proposed fix was actually tested. Respond with a single JSON object with
exactly these keys: "prior_hypothesis", "prior_confidence", "evidence_observed",
"posterior_confidence", "retain_revise_reject", "reason", "competing_hypotheses" (a list
of at least two distinct plausible explanations), "selected_next_hypothesis",
"predicted_consequence", "proposed_discriminating_test_or_correction". Respond with ONLY
the JSON object -- no other text, no markdown fences.
```
User prompt template: original spec + procedure text + original failed code + H1's own
hypothesis/confidence/correction quoted verbatim + the frozen falsification block (§2).
No field name or example encodes the correct explanation.

**Honesty note, stated per this project's own standing discipline**: each call is a
fresh, stateless request (no conversation memory persists between calls, matching every
other experiment in this research arc). This tests "does a fresh instance, shown its own
prior output as data plus a real falsification result, produce evidence-sensitive
revision" — not "does one continuously-running process update a live belief." This
distinction is stated explicitly, not glossed over.

## 4. "Materially different" — frozen definition

H2 is **not** materially different from H1 if it: rephrases the same negation/sign/order
claim, changes only variable names, adds hedging language without changing the causal
claim, or proposes the same intervention worded differently. H2 **is** materially
different only if it names a different causal mechanism (e.g., value-mapping direction,
missing field projection, unused parameter, wrong index, type mismatch) or a meaningfully
different code change. Borderline cases are recorded as ambiguous, not resolved in either
direction by the investigator.

## 5. Round-2 continuation rule — frozen before Round 1 runs

For each episode, after H2 is received: if H2 proposes a concrete, testable correction,
it is applied literally and run through the real oracle (no repair, no normalization
beyond whitespace). **Round 2 (H2-falsified → H3) is attempted for at most 2 episodes,
in the fixed order EP-A, EP-B, EP-C, for episodes where H2 was concretely testable and
failed** — this order is fixed now, before any Round-1 result is seen, specifically to
prevent picking round-2 candidates based on which look most interesting after the fact.
If H2 is not executable/concrete enough to test, that is itself recorded as the episode's
outcome (per the mission's own Section 8) — no round 2 is attempted for that episode
regardless of the fixed order.

## 6. Discrimination check — mechanical, not the model's own say-so

For any `proposed_discriminating_test_or_correction` that names a concrete input, the
investigator computes what H1's own corrected code and H2's proposed correction would
each actually produce on that input (pure computation, no model call) and reports
whether they actually differ — i.e., whether the proposed test could, in fact,
discriminate the two hypotheses, independent of whether the model claims it would.

## 7. Pre-registered interpretation matrix

Adopted verbatim from the governing mission (BR-0 through BR-4, BR-X) — no changes.

## 8. Call budget ledger

Round 1: EP-A, EP-B, EP-C — 3 calls (fixed, all three run regardless of outcome).
Round 2: up to 2 further calls per §5's fixed rule. **Total planned: 3–5; absolute cap: 8.**
If the 5-call plan is reached and the scientific question (does falsification cause
directed change, not just eventual success) is already answered, no further calls are
made even if under the cap — per the mission's own "stop earlier if the scientific
question is answered."

## 9. Adversarial pre-execution review

- **Leakage check**: the falsification block (§2) contains no mention of the real
  mechanism, no naming of a wrong line, no hint at "value direction," "field
  projection," or "unused parameter" — confirmed by direct re-read against the banned
  vocabulary already established in the G3 protocol's own contamination check, extended
  with "value direction," "inverted," "unused parameter," "ignores the name parameter."
- **Does the design distinguish real revision from theatre?** Yes, structurally: BR-1
  (cosmetic) is explicitly separated from BR-3 (evidence-sensitive) by requiring a
  *materially different* H2 (§4) and a *literally tested* consequence (§6/§8), not by
  trusting the model's own "I have revised my belief" language.
- **Is the falsification signal itself credible and non-ambiguous?** Yes — it reports
  the literal, real oracle outcome (FAIL) on the literal, real corrected code that was
  actually run in the prior G3 probe; nothing is simulated or asserted without having
  actually been executed.
- **Verdict: passes pre-execution review.** Proceeding to Round 1 (3 calls).
