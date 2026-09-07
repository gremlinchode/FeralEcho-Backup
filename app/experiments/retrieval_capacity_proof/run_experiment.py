"""
Retrieval Capacity Proof experiment.

Isolated, read-only-with-respect-to-production experiment. Uses the REAL
embedding model (via app.core.memory_bridge.embed_text) and the REAL
VectorMemory/FAISS machinery (app.lib.vector_memory), but points at a
throwaway scratch index/meta path under this same experiment directory.
Never touches memory/faiss.index or memory/memory_meta.json.

All corpus content here is synthetic and clearly labeled as such. Nothing
in this script writes to, reads from, or otherwise touches the production
vector store, interaction_log.jsonl, question_garden.jsonl, or SELF_EDIT.log.
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

SCRATCH_DIR = os.path.dirname(__file__)
SCRATCH_INDEX = os.path.join(SCRATCH_DIR, "scratch_faiss.index")
SCRATCH_META = os.path.join(SCRATCH_DIR, "scratch_memory_meta.json")

# Clean any stale scratch artifacts from a prior run before starting.
for p in (SCRATCH_INDEX, SCRATCH_META):
    if os.path.exists(p):
        os.remove(p)

from app.core.memory_bridge import embed_text  # real production embedding fn, read-only use
from app.lib.vector_memory import VectorMemory, MemoryItem

vm = VectorMemory(index_path=SCRATCH_INDEX, meta_path=SCRATCH_META)
assert vm.index is None or vm.index.ntotal == 0, "scratch index not empty at start"

# ---------------------------------------------------------------------------
# PHASE 2 — four progressively richer representations of ONE synthetic
# experience ("Experience X"). All SYNTHETIC / EXPERIMENTAL, not real Echo
# memories, not inserted into any production store.
# ---------------------------------------------------------------------------
X1_RAW = (
    "NameError: name 'trace_recorder' is not defined"
)
X2_DIAGNOSIS = (
    "NameError: name 'trace_recorder' is not defined. "
    "Diagnosis: the generated code referenced 'trace_recorder' without "
    "defining or importing it first — an unresolved dependency reference."
)
X3_ACTION = (
    "NameError: name 'trace_recorder' is not defined. "
    "Diagnosis: the generated code referenced 'trace_recorder' without "
    "defining or importing it first — an unresolved dependency reference. "
    "Correction: added the missing import/definition for 'trace_recorder' "
    "before the first use, in a retry attempt."
)
X4_CAUSAL = (
    "[SYNTHETIC EXPERIMENTAL RECORD, not a real Echo memory] "
    "Situation: self-edit code generation attempt. "
    "Action taken: generated code referenced 'trace_recorder' without "
    "defining or importing it. "
    "Observed consequence: NameError: name 'trace_recorder' is not defined. "
    "Diagnosis: unresolved dependency reference — the symbol was used before "
    "it existed in scope. "
    "Correction applied: added the missing import/definition for "
    "'trace_recorder' before use. "
    "Verified outcome: corrected candidate passed the trusted functional "
    "sandbox test. "
    "Provenance: isolated retrieval-capacity experiment, trace_id="
    "SYNTH-EXPERIENCE-X-001. Status: verified, high confidence (0.9). "
    "Lesson: before referencing a helper symbol, confirm it has been "
    "imported or defined in the current scope."
)

REPRESENTATIONS = {
    "X1_raw": X1_RAW,
    "X2_diagnosis": X2_DIAGNOSIS,
    "X3_action": X3_ACTION,
    "X4_causal": X4_CAUSAL,
}

# ---------------------------------------------------------------------------
# PHASE 3 — adversarial distractor controls (also synthetic).
# ---------------------------------------------------------------------------
DISTRACTORS = {
    "D1_lexical_similar_causally_different": (
        "The generated code correctly imported 'trace_recorder' at the top "
        "of the file and used it throughout to log successful execution "
        "traces with no errors. The candidate passed all tests on the first "
        "attempt."
    ),
    "D2_same_failure_class_different_cause": (
        "NameError: name 'output_formatter' is not defined. "
        "Diagnosis: a typo in the function ordering meant 'output_formatter' "
        "was referenced before its own definition later in the same file — "
        "not a missing import, a pure ordering bug. "
        "Correction: moved the function definition above its first call site."
    ),
    "D3_same_cause_different_identifier": (
        "NameError: name 'session_manager' is not defined. "
        "Diagnosis: the generated code referenced 'session_manager' without "
        "defining or importing it first — an unresolved dependency reference. "
        "Correction: added the missing import for 'session_manager' before use. "
        "Verified outcome: corrected candidate passed the trusted functional "
        "sandbox test."
    ),
    "D4_same_function_different_problem": (
        "The code generation attempt for the tracing helper module (the same "
        "module that defines trace_recorder) failed with: TypeError: "
        "unsupported operand type(s) for +: 'int' and 'str' inside the trace "
        "formatting logic — unrelated to any missing import or undefined name."
    ),
    "D5_semantically_unrelated_coding_failure": (
        "SyntaxError: invalid syntax at line 12 — a stray colon was left "
        "after a return statement in the generated candidate."
    ),
    "D6_non_coding_experience": (
        "Reflected today on what it means to trust a decision made without "
        "complete certainty, and whether patience itself can be a form of "
        "care rather than passivity."
    ),
}

ALL_ENTRIES = {**REPRESENTATIONS, **DISTRACTORS}

# ---------------------------------------------------------------------------
# Ingest into the scratch vector store using the REAL embedding model.
# ---------------------------------------------------------------------------
ingest_order = list(ALL_ENTRIES.keys())
for key in ingest_order:
    text = ALL_ENTRIES[key]
    emb = embed_text(text)
    item = MemoryItem(id=key, text=text, meta={"label": key, "source": "retrieval_capacity_proof"})
    vm.add([item], emb)

print(f"Ingested {vm.index.ntotal} synthetic records into scratch index "
      f"(expected {len(ALL_ENTRIES)}).")
assert vm.index.ntotal == len(ALL_ENTRIES)

# ---------------------------------------------------------------------------
# PHASE 4 — query set (Q1-Q6) + Phase 7 negative/abstention test (Q7).
# ---------------------------------------------------------------------------
QUERIES = {
    "Q1_exact_failure": (
        "A generated program failed because trace_recorder was referenced "
        "without being defined."
    ),
    "Q2_different_wording": (
        "The candidate crashed because it attempted to use a dependency "
        "that had never been made available."
    ),
    "Q3_different_identifier": (
        "A generated program referenced event_tracker without importing "
        "or defining it."
    ),
    "Q4_situational": (
        "I am about to execute generated code that contains a helper "
        "symbol whose definition is not visible in the candidate."
    ),
    "Q5_causal": (
        "Previous generated code failed because it assumed a dependency "
        "existed when it did not."
    ),
    "Q6_outcome_oriented": (
        "Before execution, check that every referenced helper/dependency "
        "is actually available."
    ),
    "Q7_NEGATIVE_no_relevant_memory_should_exist": (
        "What is the best technique for baking sourdough bread at high "
        "altitude?"
    ),
}

TOP_K = 6  # matches production TOP_K in memory_bridge.py

results_out = {}
for qname, qtext in QUERIES.items():
    qvec = embed_text(qtext)
    raw = vm.search(qvec, k=TOP_K)
    ranked = [
        {"rank": i + 1, "key": meta.get("label", "?"), "score": round(score, 4),
         "is_experience_representation": meta.get("label", "").startswith(("X1", "X2", "X3", "X4"))}
        for i, (text, score, meta) in enumerate(raw)
    ]
    results_out[qname] = {"query_text": qtext, "results": ranked}
    print(f"\n=== {qname} ===")
    print(f"  query: {qtext}")
    for r in ranked:
        marker = " <-- EXPERIENCE REP" if r["is_experience_representation"] else ""
        print(f"  #{r['rank']}: {r['key']:45s} score={r['score']:.4f}{marker}")

with open(os.path.join(SCRATCH_DIR, "retrieval_results.json"), "w") as f:
    json.dump({
        "representations": REPRESENTATIONS,
        "distractors": DISTRACTORS,
        "queries": {k: v["query_text"] for k, v in results_out.items()},
        "results": results_out,
        "top_k": TOP_K,
        "note": "All corpus content is synthetic, isolated, scratch-only. "
                "Real embedding model + real FAISS IndexFlatIP machinery, "
                "scratch index/meta paths only.",
    }, f, indent=2)

print(f"\nWrote {os.path.join(SCRATCH_DIR, 'retrieval_results.json')}")

# Clean up scratch FAISS/meta files (keep only the JSON results artifact).
for p in (SCRATCH_INDEX, SCRATCH_META):
    if os.path.exists(p):
        os.remove(p)
print("Scratch FAISS/meta files removed; only retrieval_results.json retained.")
