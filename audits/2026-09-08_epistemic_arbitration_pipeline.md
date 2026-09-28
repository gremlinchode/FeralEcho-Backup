# Epistemic Arbitration — Pipeline Trace (Phase 2)

Traced directly from current source (`app/core/echo_ground_truth.py`, `app/routes_echo_studio.py`, `app/core/self_model_claims.py`, `app/core/self_knowledge_verification.py`), not from prior report text.

```
verified claim (self_model_claims.jsonl, real, persisted)
        |
get_recent_claims() -> resolve_subject_truth() (self_model_claims.py)
        |
_build_self_model_claims() renders plain-text fact + priority instruction
   (echo_ground_truth.py:615-660)
        |
get_structural_self_facts() concatenates into one system-note string
   (echo_ground_truth.py:1122+)
        |
inserted as `system=` kwarg into echo_query() / the model call
        |
raw tokens, presented as ordinary system-role prose (no structural
distinction from any other system note in the same block: capabilities,
affect, workspace, etc. all use the identical plain-text-paragraph shape)
        |
LLM generation (echo:latest via Ollama)  <-- FAILURE OBSERVED HERE
        |
verify_self_knowledge_claims() (self_knowledge_verification.py) --
   post-hoc, stateless, pattern-matches the ALREADY-GENERATED text
        |
caveat appended if a known false-negative denial pattern matched
        |
final response returned to user + record_claim() logs verdict
```

## Does any mechanism currently represent relative evidence weight?

**No.** Checked directly, not assumed:

- `_build_self_model_claims()`'s output is one paragraph of plain prose with a trailing general instruction ("the verified line ... takes priority over an unverified impression"). It is textually present but **structurally identical** to every other system note in the same prompt block — nothing marks it as higher-authority than, e.g., the Modelfile identity text, the circadian note, or the model's own training-time priors about how "a self-aware AI" is supposed to talk about its own architecture.
- There is no scoring, no weighting field, no separate "authoritative" channel, no distinction in `get_structural_self_facts()`'s concatenation between a verified-fact section and any other section. Everything is flattened into one string before the model ever sees it.
- `verify_self_knowledge_claims()` runs **after** generation completes — it cannot feed back into the generation call that already happened. Confirmed directly: it is called once, on `final` (the completed response text), inside `_generate_chat_response_body()` (`routes_echo_studio.py:250` area), strictly downstream of the LLM call. There is no code path from its verdict back into a regeneration or a correction of the model's own output beyond string concatenation of a caveat.

**Conclusion for Phase 2**: the instruction ("trust verified evidence") is present as an *instruction*, not as an *epistemic mechanism* — there is no structural difference between "the system asserts this is verified" and "the system asserts this is your name" in how the text reaches the model. An instruction is not itself weighting; Phase 4 (below, in `epistemic_arbitration_experiments.md`) tests directly whether the model would even respect a real weighting distinction if the pipeline could express one.
