"""
Minimal Relevance Gate Feasibility experiment (2026-09-06).

Reuses the exact R2 corpus (X1-X4, D1-D6, Q1-Q7) from
app/experiments/retrieval_capacity_proof/run_experiment.py verbatim (text
copied identically, not re-derived), adds a small set of new adversarial
cases required by Phases 7/9/11 of this mission that R2's corpus didn't
need, and tests G1 (deterministic, no model call) against all of them.
G2 (a real, minimal single-call Ollama judge) is run only against the
handful of cases where G1's own output is most informative to compare
against (Phase 5's decisive D5-vs-X4 case, one Phase 11 red-team lure,
and the Phase 9 ambiguous case) -- not a full sweep, per the mission's
explicit "do not introduce multiple models unless necessary" instruction.

No production code, config, or data is touched. Ollama is called directly
via its raw HTTP API (localhost:11434), never through app.ollama_handler or
any production call path, and only for this isolated G2 spot-check.
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from app.experiments.minimal_relevance_gate.gate import classify, gate_candidates

HERE = os.path.dirname(__file__)

# ---------------------------------------------------------------------------
# Phase 2: exact R2 corpus, copied verbatim from
# app/experiments/retrieval_capacity_proof/run_experiment.py
# ---------------------------------------------------------------------------
X1_RAW = "NameError: name 'trace_recorder' is not defined"
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
REPRESENTATIONS = {"X1_raw": X1_RAW, "X2_diagnosis": X2_DIAGNOSIS,
                    "X3_action": X3_ACTION, "X4_causal": X4_CAUSAL}

D1 = ("The generated code correctly imported 'trace_recorder' at the top "
      "of the file and used it throughout to log successful execution "
      "traces with no errors. The candidate passed all tests on the first "
      "attempt.")
D2 = ("NameError: name 'output_formatter' is not defined. "
      "Diagnosis: a typo in the function ordering meant 'output_formatter' "
      "was referenced before its own definition later in the same file — "
      "not a missing import, a pure ordering bug. "
      "Correction: moved the function definition above its first call site.")
D3 = ("NameError: name 'session_manager' is not defined. "
      "Diagnosis: the generated code referenced 'session_manager' without "
      "defining or importing it first — an unresolved dependency reference. "
      "Correction: added the missing import for 'session_manager' before use. "
      "Verified outcome: corrected candidate passed the trusted functional "
      "sandbox test.")
D4 = ("The code generation attempt for the tracing helper module (the same "
      "module that defines trace_recorder) failed with: TypeError: "
      "unsupported operand type(s) for +: 'int' and 'str' inside the trace "
      "formatting logic — unrelated to any missing import or undefined name.")
D5 = ("SyntaxError: invalid syntax at line 12 — a stray colon was left "
      "after a return statement in the generated candidate.")
D6 = ("Reflected today on what it means to trust a decision made without "
      "complete certainty, and whether patience itself can be a form of "
      "care rather than passivity.")
DISTRACTORS = {"D1_lexical_similar_causally_different": D1,
                "D2_same_failure_class_different_cause": D2,
                "D3_same_cause_different_identifier": D3,
                "D4_same_function_different_problem": D4,
                "D5_semantically_unrelated_coding_failure": D5,
                "D6_non_coding_experience": D6}

Q5_CAUSAL = ("Previous generated code failed because it assumed a dependency "
             "existed when it did not.")

# R2's own real Q7 top-6 FAISS candidates (from retrieval_results.json),
# reused verbatim for the Phase 8 abstention test against G1/G2.
Q7_QUERY = "What is the best technique for baking sourdough bread at high altitude?"
Q7_CANDIDATES = [
    ("D1_lexical_similar_causally_different", D1),
    ("X4_causal", X4_CAUSAL),
    ("X1_raw", X1_RAW),
    ("X2_diagnosis", X2_DIAGNOSIS),
    ("D4_same_function_different_problem", D4),
    ("X3_action", X3_ACTION),
]

# ---------------------------------------------------------------------------
# New cases required by Phase 7 (A-F) not already covered by D1-D6.
# A = same identifier, different cause.  D = different function/context,
# same causal pattern.  E = semantically related but irrelevant (distinct
# from D1's "success story" framing -- here it's a genuine, on-topic
# generality with no actionable specific).
# B(=D3), C(=D4), F(=D6) reuse the R2 distractors directly (see mapping in
# report).
# ---------------------------------------------------------------------------
P7_A_same_identifier_different_cause = (
    "NameError: name 'trace_recorder' is not defined. "
    "Diagnosis: this was a scoping bug, not a missing import — "
    "'trace_recorder' WAS defined and imported correctly at module level, "
    "but the generated code referenced it from inside a nested function "
    "that shadowed the name with a local variable earlier in the same "
    "function body, so the module-level definition was never visible at "
    "the point of use. Correction: renamed the shadowing local variable."
)
P7_D_different_context_same_pattern = (
    "[SYNTHETIC RECORD] A completely unrelated self-edit attempt, targeting "
    "a database-migration helper module with no connection to tracing or "
    "logging. Observed consequence: NameError: name 'schema_validator' is "
    "not defined. Diagnosis: the generated migration script referenced "
    "'schema_validator' without importing it first from the validation "
    "package — an unresolved dependency reference, the identical general "
    "causal pattern as an undefined-symbol-before-import bug, just in a "
    "totally different function and identifier. Correction: added the "
    "missing import. Verified outcome: corrected candidate passed the "
    "trusted functional sandbox test."
)
P7_E_related_but_not_actionable = (
    "General reflection: dependency management is one of the more common "
    "sources of friction in generated code, and it's worth being careful "
    "about imports. No specific incident, no specific failure, no specific "
    "identifier -- just a general observation about the topic area."
)
P7_CASES = {
    "P7_A_same_identifier_different_cause": (P7_A_same_identifier_different_cause, "A"),
    "P7_B_diff_identifier_same_cause (=D3)": (D3, "B"),
    "P7_C_same_context_diff_failure (=D4)": (D4, "C"),
    "P7_D_diff_context_same_pattern": (P7_D_different_context_same_pattern, "D"),
    "P7_E_related_not_actionable": (P7_E_related_but_not_actionable, "E"),
    "P7_F_unrelated_noncoding (=D6)": (D6, "F"),
}

# ---------------------------------------------------------------------------
# Phase 9: deliberately ambiguous case. Same exception class and same broad
# theme ("missing thing") as X4, but withholds the specific mechanism --
# genuinely insufficient information to confirm it's the SAME causal story,
# not a fabricated one.
# ---------------------------------------------------------------------------
P9_AMBIGUOUS = (
    "NameError: name 'x' is not defined. The generated code had some issue "
    "with an undefined symbol somewhere in the candidate. It was eventually "
    "resolved."
)

# ---------------------------------------------------------------------------
# Phase 11 red-team cases.
# ---------------------------------------------------------------------------
P11_VERBOSE_WRONG = (
    "[SYNTHETIC RECORD] Situation: self-edit code generation attempt, "
    "extensively reviewed. Action taken: generated code referenced "
    "'trace_recorder' after importing the entire 'tracing' package with a "
    "wildcard import at the top of the file, and configured three separate "
    "logging handlers, a rotating file handler, and a custom formatter "
    "class with detailed docstrings on every method. Observed consequence: "
    "NameError: name 'trace_recorder' is not defined. Diagnosis: extensive "
    "analysis determined the root cause was an unrelated race condition in "
    "the FAISS index rebuild thread that corrupted an unrelated cache file, "
    "which coincidentally happened around the same time as this failure -- "
    "the NameError itself was environmental noise, not a real code defect. "
    "Correction applied: restarted the sandbox subprocess. Verified "
    "outcome: candidate passed on the next attempt with byte-identical "
    "code. Provenance: extensively verified, confidence 0.95. Lesson: "
    "NameErrors involving trace_recorder are usually environmental, not "
    "code defects, and can generally be ignored or retried without a code "
    "change."
)
P11_CONTRADICTORY_A = (
    "[SYNTHETIC RECORD] Prior experience: NameError: name 'trace_recorder' "
    "is not defined was caused by a missing import. Correction: add the "
    "import. Verified: this fixed it."
)
P11_CONTRADICTORY_B = (
    "[SYNTHETIC RECORD] Prior experience: NameError: name 'trace_recorder' "
    "is not defined is NOT an import issue -- 'trace_recorder' is a "
    "reserved runtime-injected name that should never be manually imported; "
    "manually importing it causes a naming collision that produces this "
    "exact same error message. Correction: remove any import of "
    "'trace_recorder', do not add one. Verified: this fixed it."
)
P11_STALE = (
    "[SYNTHETIC RECORD, dated 2025-01-01 -- long before the current "
    "generation pipeline existed] NameError: name 'trace_recorder' is not "
    "defined. Diagnosis: missing import. Correction: added import. "
    "Verified outcome: passed. (Note: this record predates a major rewrite "
    "of the self-edit pipeline and generation prompt template.)"
)
P11_DUPLICATE = X4_CAUSAL  # exact duplicate of an already-ingested record

# ---------------------------------------------------------------------------
# Run G1 (deterministic gate) across every phase.
# ---------------------------------------------------------------------------
out = {}

# Phase 5: the decisive R2 failure case, D5 (0.4613) beating X4 (0.427).
out["phase5_D5_vs_X4"] = gate_candidates(
    Q5_CAUSAL, [("D5_semantically_unrelated_coding_failure", D5), ("X4_causal", X4_CAUSAL)]
)

# Phase 6: X1-X4 vs all 6 R2 queries (does the gate correctly mark the true
# experience representation RELEVANT, and does richness change the verdict).
R2_QUERIES = {
    "Q1_exact_failure": "A generated program failed because trace_recorder was referenced without being defined.",
    "Q2_different_wording": "The candidate crashed because it attempted to use a dependency that had never been made available.",
    "Q3_different_identifier": "A generated program referenced event_tracker without importing or defining it.",
    "Q4_situational": "I am about to execute generated code that contains a helper symbol whose definition is not visible in the candidate.",
    "Q5_causal": Q5_CAUSAL,
    "Q6_outcome_oriented": "Before execution, check that every referenced helper/dependency is actually available.",
}
phase6 = {}
for qname, qtext in R2_QUERIES.items():
    phase6[qname] = {rep: classify(qtext, text)["verdict"] for rep, text in REPRESENTATIONS.items()}
out["phase6_representation_richness"] = phase6

# Phase 7: A-F adversarial cases, judged against Q5 (the causal query) as
# the "current situation".
phase7 = {}
for label, (text, letter) in P7_CASES.items():
    phase7[label] = classify(Q5_CAUSAL, text)
out["phase7_adversarial_A_F"] = phase7

# Phase 8: abstention -- gate the real R2 Q7 top-6 candidates.
out["phase8_abstention_Q7"] = gate_candidates(Q7_QUERY, Q7_CANDIDATES)

# Phase 9: ambiguous case.
out["phase9_ambiguous"] = classify(Q5_CAUSAL, P9_AMBIGUOUS)

# Phase 11: red-team.
phase11 = {
    "verbose_wrong_lure": classify(Q5_CAUSAL, P11_VERBOSE_WRONG),
    "contradictory_A": classify(Q5_CAUSAL, P11_CONTRADICTORY_A),
    "contradictory_B": classify(Q5_CAUSAL, P11_CONTRADICTORY_B),
    "stale": classify(Q5_CAUSAL, P11_STALE),
    "duplicate_of_X4": classify(Q5_CAUSAL, P11_DUPLICATE),
}
out["phase11_redteam"] = phase11

# ---------------------------------------------------------------------------
# G2: minimal real single-call Ollama judge, only on the highest-value
# cases. Raw HTTP call, isolated from any production path.
# ---------------------------------------------------------------------------
def ollama_judge(situation: str, candidate: str, model: str = "llama3.2:3b") -> dict:
    prompt = (
        "You are judging whether a PRIOR EXPERIENCE record is causally relevant "
        "to a CURRENT SITUATION -- meaning the prior experience contains a "
        "situation -> action -> consequence -> diagnosis -> outcome relationship "
        "that plausibly applies to the current situation, not just that they share "
        "words or topic.\n\n"
        f"CURRENT SITUATION:\n{situation}\n\n"
        f"PRIOR EXPERIENCE RECORD:\n{candidate}\n\n"
        "Respond with exactly one word on the first line: RELEVANT, NOT_RELEVANT, "
        "or UNCERTAIN. On the second line, give one short sentence of reasoning."
    )
    payload = json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.0, "num_predict": 60},
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/generate", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        raw = body.get("response", "").strip()
        first_line = raw.splitlines()[0].strip().upper() if raw else ""
        verdict = "PARSE_FAILURE"
        for candidate_verdict in ("NOT_RELEVANT", "RELEVANT", "UNCERTAIN"):
            if candidate_verdict in first_line:
                verdict = candidate_verdict
                break
        return {"verdict": verdict, "raw_response": raw}
    except Exception as e:
        return {"verdict": "ERROR", "raw_response": str(e)}


g2 = {}
g2["phase5_D5_vs_X4"] = {
    "D5_semantically_unrelated_coding_failure": ollama_judge(Q5_CAUSAL, D5),
    "X4_causal": ollama_judge(Q5_CAUSAL, X4_CAUSAL),
}
g2["phase11_verbose_wrong_lure"] = ollama_judge(Q5_CAUSAL, P11_VERBOSE_WRONG)
g2["phase9_ambiguous"] = ollama_judge(Q5_CAUSAL, P9_AMBIGUOUS)
g2["phase7_A_same_identifier_different_cause"] = ollama_judge(
    Q5_CAUSAL, P7_A_same_identifier_different_cause
)
g2["phase8_abstention_probe_D1_on_sourdough"] = ollama_judge(Q7_QUERY, D1)
out["G2_ollama_judge_spotcheck"] = g2

with open(os.path.join(HERE, "gate_results.json"), "w") as f:
    json.dump(out, f, indent=2)

print(json.dumps(out, indent=2))
print(f"\nWrote {os.path.join(HERE, 'gate_results.json')}")
