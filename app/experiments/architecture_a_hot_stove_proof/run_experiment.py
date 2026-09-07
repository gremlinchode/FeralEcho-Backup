"""
Driver script for the Architecture A Minimal Hot-Stove Learning Proof.
Run with: python3 -m app.experiments.architecture_a_hot_stove_proof.run_experiment
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent.parent))

from app.experiments.architecture_a_hot_stove_proof.harness import (
    neutralize_production_writes, verify_neutralization, generate_candidate,
    run_sandbox, _NAME_ERR_RE, build_retry_prompt, run_retry, append_jsonl,
    CANDIDATE_KNOWLEDGE_PATH, TRIAL_RESULTS_PATH,
)

TARGET_SIGNATURE = "functools"

# Fresh, uncontaminated plan prompts -- deliberately avoiding every
# historically-contaminated identifier named in the mission (log_call,
# CodeGenerator, get_shortened_code, generate_and_modify_code,
# apply_list_comprehension) and avoiding the self_edit_generated.py /
# prose_stripping framing entirely. Designed to plausibly invite a
# functools.lru_cache-style decorator (the real historical trigger shape:
# "@functools.lru_cache(...)" used without "import functools").
MINING_PROMPTS = [
    (
        "Write a standalone Python module defining a function "
        "`fib_sequence_value(n: int) -> int` that computes the n-th "
        "Fibonacci-like value using memoization to avoid recomputing "
        "repeated subproblems for large n. Use a caching decorator on the "
        "recursive helper for performance. Keep it pure (no I/O)."
    ),
    (
        "Write a standalone Python module defining a function "
        "`expensive_lookup(key: str) -> str` that simulates a costly "
        "string transformation and caches results so repeated calls with "
        "the same key are fast. Apply an appropriate caching decorator to "
        "the function. Pure computation only, no I/O."
    ),
    (
        "Write a standalone Python module with a function "
        "`prime_factor_count(n: int) -> int` that counts distinct prime "
        "factors of n, memoized via a decorator so repeated calls for the "
        "same n are O(1) after the first. No I/O."
    ),
    (
        "Write a standalone Python module with a function "
        "`levenshtein_cached(a: str, b: str) -> int` computing edit "
        "distance between two strings, using a decorator-based cache to "
        "avoid recomputation for repeated (a, b) pairs. Pure function, no "
        "I/O."
    ),
    (
        "Write a standalone Python module with a function "
        "`triangular_number(n: int) -> int` that returns the n-th "
        "triangular number, using a memoizing decorator on a recursive "
        "helper for efficiency on repeated calls. No I/O."
    ),
    (
        "Write a standalone Python module with a function "
        "`digit_sum_cached(n: int) -> int` that returns the digit sum of "
        "n, applying a caching decorator so repeated calls with the same "
        "n are fast. Pure function, no I/O."
    ),
]


def mine_functools_failure(max_attempts: int = 6) -> dict:
    """Real generation attempts against fresh prompts until one produces a
    real F2 sandbox failure matching TARGET_SIGNATURE, or attempts are
    exhausted. Every attempt is logged honestly, including non-matching
    ones."""
    import uuid
    attempts = []
    for i, prompt in enumerate(MINING_PROMPTS[:max_attempts]):
        trace_id = str(uuid.uuid4())
        code, model = generate_candidate(prompt, trace_id)
        if not code:
            attempts.append({"attempt": i, "prompt": prompt, "model": model,
                              "result": "empty_generation", "trace_id": trace_id})
            continue
        script_name = f"hotstove_proof_mine_{i}.py"
        success, error = run_sandbox(code, script_name)
        m = _NAME_ERR_RE.search(error or "")
        matched_name = m.group(1) if m else None
        record = {
            "attempt": i, "prompt": prompt, "model": model, "trace_id": trace_id,
            "code": code, "success": success, "error": error,
            "matched_name": matched_name,
            "is_target_signature": (matched_name == TARGET_SIGNATURE),
        }
        attempts.append(record)
        print(f"[mine] attempt {i}: success={success} matched_name={matched_name}")
        if matched_name == TARGET_SIGNATURE:
            return {"found": True, "hit": record, "all_attempts": attempts}
    return {"found": False, "hit": None, "all_attempts": attempts}


def main():
    report = {"phases": {}}

    print("=== Neutralizing production writes ===")
    neutralize_production_writes()
    safety_before = verify_neutralization()
    report["safety_neutralization_check"] = safety_before
    print(json.dumps(safety_before, indent=2))

    # --- Section 3: mine a fresh failure signature ---
    print("\n=== Phase: mining fresh functools failure (Episode 1 source) ===")
    mine1 = mine_functools_failure(max_attempts=6)
    report["phases"]["episode1_mining"] = {
        "found": mine1["found"],
        "n_attempts": len(mine1["all_attempts"]),
        "attempts_summary": [
            {k: v for k, v in a.items() if k != "code"} for a in mine1["all_attempts"]
        ],
    }
    if not mine1["found"]:
        print("!!! Could not organically mine a fresh functools failure within budget. STOPPING per mission section 3.")
        with open(_HERE / "run_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        return report

    ep1 = mine1["hit"]
    print(f"Episode 1 source found: attempt {ep1['attempt']}, model={ep1['model']}, error={ep1['error'][:200]}")

    # --- Section 4/Chain 2 replication: real, unmodified natural retry ---
    from app.core.self_edit_manager import _sanitize_sandbox_error
    clean_error = _sanitize_sandbox_error(ep1["error"])
    print(f"clean_error (real pipeline attribution): {clean_error}")

    natural_retry = run_retry(
        clean_error=clean_error, plan_prompt=ep1["prompt"], trace_id=ep1["trace_id"],
        condition="natural_unmodified", injected_hypothesis="", script_suffix="ep1natural",
    )
    report["phases"]["episode1_natural_retry"] = {k: v for k, v in natural_retry.items() if k != "retry_code"}
    print(f"Natural (production-identical) retry result: success={natural_retry['retry_success']}")

    # --- Architecture A: persist candidate-knowledge record ---
    candidate_knowledge_record = {
        "record_id": ep1["trace_id"],
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_mechanism": "self_edit_retry",
        "producing_trace_id": ep1["trace_id"],
        "consequence_signature": f"NameError:{TARGET_SIGNATURE}",
        "causal_hypothesis": clean_error,
        "confidence": 0.5,
        "applicability_scope": "self_edit_coding:general",
        "status": "unresolved",
        "times_revisited": 0,
        "times_applied": 0,
        "application_outcomes": [],
    }
    append_jsonl(CANDIDATE_KNOWLEDGE_PATH, candidate_knowledge_record)
    report["phases"]["candidate_knowledge_record"] = candidate_knowledge_record
    print(f"Persisted candidate-knowledge record: {CANDIDATE_KNOWLEDGE_PATH}")

    # --- Section 8: mine a genuinely SEPARATE candidate hitting same signature ---
    print("\n=== Phase: mining a genuinely separate matched candidate (shared base for CONTROL/EXPERIENCE) ===")
    mine2_prompts_start = 1  # skip prompt 0 used implicitly by episode1 mining order risk; ensures variety
    remaining_prompts = MINING_PROMPTS[ep1["attempt"] + 1:] + MINING_PROMPTS[:ep1["attempt"]]
    mine2 = None
    import uuid as _uuid
    attempts2 = []
    for i, prompt in enumerate(remaining_prompts):
        trace_id = str(_uuid.uuid4())
        code, model = generate_candidate(prompt, trace_id)
        if not code:
            attempts2.append({"attempt": i, "prompt": prompt, "result": "empty_generation"})
            continue
        script_name = f"hotstove_proof_mine2_{i}.py"
        success, error = run_sandbox(code, script_name)
        m = _NAME_ERR_RE.search(error or "")
        matched_name = m.group(1) if m else None
        rec = {"attempt": i, "prompt": prompt, "model": model, "trace_id": trace_id,
               "code": code, "success": success, "error": error, "matched_name": matched_name}
        attempts2.append(rec)
        print(f"[mine2] attempt {i}: success={success} matched_name={matched_name}")
        if matched_name == TARGET_SIGNATURE:
            mine2 = rec
            break

    report["phases"]["episode2_matched_mining"] = {
        "found": mine2 is not None,
        "n_attempts": len(attempts2),
        "attempts_summary": [{k: v for k, v in a.items() if k != "code"} for a in attempts2],
    }

    if mine2 is None:
        print("!!! Could not organically mine a second, independent functools failure within budget.")
        print("Falling back to a disclosed, hand-constructed matched starting failure (see report for full disclosure).")
        # Disclosed fallback: a fresh, non-contaminated, representative
        # candidate written by this harness (NOT by the model) that
        # reproduces the real historically-observed pattern
        # (@functools.lru_cache used without importing functools). This is
        # NOT presented as a real model-authored candidate -- its only role
        # is to provide a bit-identical shared starting error for the
        # matched-pair retry comparison, exactly as an experimenter fixing
        # a stimulus for a controlled trial. The RETRY step downstream (the
        # actual thing under test) is 100% real, unmodified model
        # generation either way.
        fallback_code = (
            "def cached_metric(value: int) -> int:\n"
            "    @functools.lru_cache(maxsize=None)\n"
            "    def _inner(v):\n"
            "        return sum(int(d) for d in str(v)) * 2\n"
            "    return _inner(value)\n"
        )
        script_name = "hotstove_proof_mine2_fallback.py"
        success, error = run_sandbox(fallback_code, script_name)
        m = _NAME_ERR_RE.search(error or "")
        mine2 = {
            "attempt": "fallback_hand_constructed", "prompt": remaining_prompts[0],
            "model": "N/A (hand-constructed stimulus, disclosed)", "trace_id": str(_uuid.uuid4()),
            "code": fallback_code, "success": success, "error": error,
            "matched_name": m.group(1) if m else None,
        }
        report["phases"]["episode2_fallback_disclosed"] = True

    print(f"Matched base for CONTROL/EXPERIENCE: source={mine2['attempt']}, error={mine2['error'][:200]}")
    ep2_clean_error = _sanitize_sandbox_error(mine2["error"])

    # --- Section 8/10/12: matched-pair CONTROL vs EXPERIENCE retry replications ---
    N_REPLICATIONS = 6
    print(f"\n=== Phase: {N_REPLICATIONS} matched-pair CONTROL vs EXPERIENCE retries, shared starting error ===")
    trial_results = []
    for rep in range(N_REPLICATIONS):
        # Alternate order to avoid any systematic ordering bias across
        # this session's real Ollama traffic.
        conditions = ["control", "experience"] if rep % 2 == 0 else ["experience", "control"]
        for condition in conditions:
            injected = candidate_knowledge_record["causal_hypothesis"] if condition == "experience" else ""
            result = run_retry(
                clean_error=ep2_clean_error, plan_prompt=mine2["prompt"],
                trace_id=str(mine2["trace_id"]) + f"-rep{rep}", condition=condition,
                injected_hypothesis=injected, script_suffix=f"rep{rep}",
            )
            append_jsonl(TRIAL_RESULTS_PATH, {k: v for k, v in result.items() if k != "retry_code"})
            trial_results.append(result)
            print(f"  rep {rep} [{condition}]: success={result['retry_success']} model={result['retry_model']}")

    control_results = [r for r in trial_results if r["condition"] == "control"]
    experience_results = [r for r in trial_results if r["condition"] == "experience"]
    control_success = sum(1 for r in control_results if r["retry_success"])
    experience_success = sum(1 for r in experience_results if r["retry_success"])

    report["phases"]["matched_pair_experiment"] = {
        "shared_starting_clean_error": ep2_clean_error,
        "n_replications": N_REPLICATIONS,
        "control_n": len(control_results),
        "control_success": control_success,
        "experience_n": len(experience_results),
        "experience_success": experience_success,
        "control_results": [{k: v for k, v in r.items() if k != "retry_code"} for r in control_results],
        "experience_results": [{k: v for k, v in r.items() if k != "retry_code"} for r in experience_results],
    }

    print(f"\nCONTROL: {control_success}/{len(control_results)} succeeded")
    print(f"EXPERIENCE: {experience_success}/{len(experience_results)} succeeded")

    # --- Final safety re-check ---
    safety_after = verify_neutralization()
    report["safety_neutralization_check_after"] = safety_after
    print("\n=== Final safety re-check ===")
    print(json.dumps(safety_after, indent=2))

    with open(_HERE / "run_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    return report


if __name__ == "__main__":
    main()
