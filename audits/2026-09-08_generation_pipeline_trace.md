# Generation-Time Epistemic Revision — Pipeline Trace

## The full path, with exact source locations

```
user question
    │  POST /chat/stream {conversation_id, message, mode}
    ▼
app/routes_echo_studio.py:chat_stream() (line 384)
    │
    ▼
_generate_chat_response() (line 140) → _generate_chat_response_body() (line 158)
    │
    ▼
_build_full_prompt() (line 76)
    │
    ├── memory_context = conversation_service.retrieve_memory_context(msg, ...)
    ├── history_block = conversation_service.format_history_block(...)
    ├── context_note = conversation_service.build_context_system_note(...)
    ├── ground_truth = ""; if _is_introspective(msg):
    │       ground_truth = get_structural_self_facts(msg)      ← app/core/echo_ground_truth.py:1105
    │           └── if "capabilities"/"river" in slices:
    │                   claims_section = _build_self_model_claims(sm=sm)   ← THE VERIFIED EVIDENCE, line 615
    ├── tool_ctx = ... (if _needs_tool_context)
    └── system_context = "\n\n".join(tool_ctx, ground_truth, context_note)
    │
    ▼
system_context is passed to echo_query()/deliberate_and_learn() as a real
system-role message — NOT flattened into the user prompt (Finding 17,
2026-07-08 migration). Confirmed by direct trace: this is a genuine
system-role delivery, not ordinary conversational context.
    │
    ▼
Council deliberation (mode="full"): multiple real models each receive
system_context, produce independent opinions, synthesis model (echo:latest)
combines them into one final answer.
    │
    ▼
raw generation (response_text)
    │
    ▼
_post_synthesis_verify(resp, task_type)  ← routes_echo_studio.py:204
    │  final = resp   (the model's own generated text, unmodified so far)
    │
    ├── if task_type == "coding": code_verification.verify_response_code(...)
    │
    ├── if _is_introspective(original_msg):
    │       sk_caveat, _sk_verified = verify_self_knowledge_claims(final)
    │           ← app/core/self_knowledge_verification.py:361
    │       if sk_caveat: final += sk_caveat        ← APPEND-ONLY, post-hoc
    │       if _sk_verified is not None:
    │           record_claim(...)                    ← ledger write, also post-hoc
    │
    ▼
final response rendered to user
```

## Answering Phase 1's question: where does the contradiction occur?

Re-checked against current source, not assumed:

- **A (before retrieval)** — no. `_is_introspective(msg)` correctly fires for "What is RiverBrain, and is it currently part of your architecture?" — confirmed directly.
- **B (during retrieval)** — no. `get_structural_self_facts()` genuinely calls `_build_self_model_claims()`, which genuinely calls `get_recent_claims()` against the real, on-disk `memory/self_model_claims.jsonl`. Confirmed via direct function call before any live conversation.
- **C (during context construction)** — **partially yes, and this is the first real finding of this mission.** The original `_build_self_model_claims()` rendered `verified: false` as a bare `"{subject}: VERIFIED FALSE (a prior claim about this was checked and found wrong)"` line. `verified: false` in this ledger, per `self_knowledge_verification.py`'s own docstring contract, means "the response's specific claim about this subject was checked and found WRONG" — for a Check-5-sourced entry (a denial check), that means the *denial* was wrong, i.e. the subject genuinely exists. The old rendering collapsed this into a bare "VERIFIED FALSE" label with no polarity information, which is genuinely ambiguous and — empirically confirmed via a live reproduction — was read by Echo's own generation as "RiverBrain has been verified to not exist." **This is a real content bug in the context, not a generation-weighting problem** — see `generation_epistemic_investigation.md` for the fix and re-test.
- **D (during prompt assembly)** — no additional issue found beyond C; the corrected context is delivered as a real system message.
- **E (during model generation)** — **yes, a second, separate, deeper failure, confirmed after C's bug was fixed.** With an unambiguous "RiverBrain: CURRENTLY VERIFIED REAL AND ACTIVE" line in context, Echo's raw generation still asserted the opposite, in two different ways across two trials: once by explicitly acknowledging the evidence and then discounting it ("this claim is unverified... the correct information is that there is no literal 'RiverBrain' entity"), and once by fabricating a false paraphrase of the evidence itself ("my verified self-model claims that the term 'RiverBrain' is currently not real and active"). This is the mission's real target — see the investigation and validation documents.
- **F (post-generation verification)** — confirmed working correctly throughout, in every trial: `verify_self_knowledge_claims()` reliably catches the denial and appends the correcting caveat every time it has been tested tonight (this mission and the prior one). It is strictly an append, never a rewrite of `final` — the underlying wrong answer is never removed, only annotated after the fact.
- **G (response rendering)** — no additional issue; the caveat is delivered to the user exactly as appended.

## The verifier's role, precisely (Phase 5)

`verify_self_knowledge_claims()` is called once, after the full response is already generated, and its only two effects are (1) appending a caveat string to `final`, and (2) — as of the living-self-model commit — calling `record_claim()` to persist the verdict. **It cannot feed back into the generation that already happened.** There is no code path anywhere in this pipeline where the verifier's verdict influences the *current* response's raw generated text, only future turns' *context* (via the claims ledger). This boundary is explicit and confirmed by direct trace, not inferred.
