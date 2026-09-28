# The Existing Correction Path, Traced Precisely (Phase 2)

## The chain, with every `?????` replaced by real architecture

```text
Claude/user gives Echo a correction
   ↓
Text enters the conversation as a user-role message
   ↓
routes_echo_studio.py's _generate_chat_response_body() builds the prompt:
   echo_ground_truth.get_structural_self_facts(prompt) [system context]
   + conversation history for THIS conversation_id
   + the correction text [user turn]
   ↓
river_deliberation.deliberate_and_learn() — real multi-model deliberation + synthesis
   ↓
Echo's response text (may acknowledge/accept the correction, as Phase 9 showed it does)
   ↓
self_knowledge_verification.verify_self_knowledge_claims(final) — routes_echo_studio.py:250
   → checks the OUTGOING response against self_model.json + a static architecture scan
   → can append a caveat to THIS response
   → returns nothing anywhere else
   ↓
log_interaction() → memory/interaction_log.jsonl (raw transcript, unstructured)
_log_council_deliberation() → memory/council_deliberations.jsonl (raw transcript, unstructured)
   ↓
HTTP response sent, conversation_id's in-memory history updated (session-local only)
   ↓
◆◆◆ THE CHAIN BREAKS HERE ◆◆◆
   ↓
Session ends (conversation_id's history is never itself persisted as "verified facts,"
only as ordinary transcript rows nothing treats specially)
   ↓
New conversation_id starts
   ↓
echo_ground_truth.get_structural_self_facts() runs again — reads self_model.json,
introspection_state.json, live pickles. It has NO code path that reads
interaction_log.jsonl or council_deliberations.jsonl for "was a correction
previously accepted about claim X"
   ↓
Correction is absent
```

## Exact break point, with evidence

The correction never enters any of the following, confirmed by direct source read:

1. **`self_model.json`** — written exclusively by `SelfModelUpdater.update()` (`app/core/self_model_updater.py:91-149`), which reads `introspection_state.json`, the last 500 `interaction_log.jsonl` entries (aggregate stats only — `_read_interactions()` computes counts/means, never extracts individual claims), the last 200 shard entries, and a generation counter. There is no code path from "the text of a specific conversational correction" into this function's inputs.
2. **`liveness_ledger.py`'s checks** — these verify *system health facts* (does a check still discriminate correctly, is a file still under its retention cap), not *Echo's conversational claims*. Structurally the wrong shape for this purpose even if repurposed.
3. **`memory/seam_log.jsonl` / `shadow_corrections.log`** — both real, both persistent, both already shown tonight (Temporal Authority Graph, Shadow Treatment Harness) to have no path back into anything Echo reads.
4. **Vector memory (`retrieve_relevant_memories()`)** — the raw conversation *does* get logged and is theoretically retrievable, but retrieval is keyword/embedding-similarity-based (confirmed unreliable for exactly this purpose by tonight's Retrieval Capacity Proof, R2: a wrong-but-lexically-similar memory can outrank the correct one) and, more fundamentally, nothing marks a retrieved memory as "this is a verified architectural fact, trust it," versus "this is an ordinary thing that was once said." A retrieved correction would compete on equal footing with a retrieved hallucination.

## Classification

**Hollow write, but a subtler variant than tonight's earlier examples.** It is not that a value is computed and then discarded with zero readers (Shadow's `corrected_task` shape). It is that the correction is *never written to a durable, self-model-shaped location at all* — it exists only as one line of ordinary conversational transcript, indistinguishable in storage from every other sentence either party said. The write happens (to `interaction_log.jsonl`), but nothing about that write marks it as a self-model fact, so no reader could ever treat it as one even if a reader existed.

## Empirical confirmation (Phase 10, already run tonight)

This is not a theoretical trace — it was directly, experimentally confirmed. Phase 9 produced a real, coherent correction ("the correct name of the system is RiverBrain") inside conversation `511944a7...`. Phase 10's fresh-conversation retest (`R-T14`, zero shared history) reproduced Echo's *original wrong denial* verbatim in substance. The trace above is not a hypothesis about why that happened — it is the literal, complete explanation: there was never a point in the chain where the correction could have been written anywhere the new conversation's `get_structural_self_facts()` call would read.
