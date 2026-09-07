"""
app/core/functional_quality.py — Phase 1 functional quality signal.

See audits/2026-09-06_phase1_functional_quality_signal.md for the full
report this module was built and validated against. Summary: this module
exists to answer one narrow question the existing AST-only quality scorer
(echo_quality_scorer._score_response_quality()) structurally cannot answer
— does a self-edit candidate's own top-level code actually execute without
raising, not just parse cleanly.

STATUS (2026-09-06): built and validated per the Phase 1 authorization.
Deliberately NOT imported by self_edit_manager.py, echo_model_orchestrator.py,
or echo_quality_scorer.py — nothing in the live pipeline calls this module.
No River training, no self-edit deployment decision, and no production
behavior of any kind is affected by this file's existence. Whether/how to
wire this signal into anything live is an explicit, separate, future
decision (Phase 2+), not made or assumed here.

Reuses sandbox/safe_exec_wrapper.py's new --mode=functional_verify (added
in the same change) rather than building a second sandbox — the same real
kernel-level Seatbelt profile (echo_sandbox.sb) and write-blocking patches
self-edit's own F2 gate already trusts.
"""

import json
import os
import subprocess
import sys
import tempfile

_SANDBOX_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "sandbox")
_SANDBOX_WRAPPER = os.path.join(_SANDBOX_ROOT, "safe_exec_wrapper.py")
_SANDBOX_PROFILE = os.path.join(_SANDBOX_ROOT, "echo_sandbox.sb")

# Outcome vocabulary — see the report's "Score Semantics" section for the
# full reasoning behind each state. The critical distinction this module
# exists to preserve: SANDBOX_INFRA_FAILURE (we don't know what the
# candidate would have done) is never conflated with VERIFIED_FAILURE (we
# know it raised) or VERIFIED_SUCCESS (we know it didn't).
VERIFIED_SUCCESS = "verified_success"
VERIFIED_FAILURE = "verified_failure"
NOT_APPLICABLE = "not_applicable"
SANDBOX_INFRA_FAILURE = "sandbox_infra_failure"


def functional_execution_score(code: str, timeout: float = 10.0) -> dict:
    """
    Runs `code` inside the real F2 kernel-sandboxed subprocess and smoke-
    tests every top-level function/class it defines with a minimal
    synthetic call. Never raises.

    Returns:
        {
            "outcome": one of VERIFIED_SUCCESS / VERIFIED_FAILURE /
                       NOT_APPLICABLE / SANDBOX_INFRA_FAILURE,
            "tested": [{"name", "kind", "outcome", "error"}, ...] or None
                      (None only for SANDBOX_INFRA_FAILURE, where we have
                      no candidate-level data at all),
            "timed_out": bool,
            "blocked_write": bool,  # candidate attempted a write outside
                                     # scratch — a real, if narrow, signal
                                     # distinct from "code raised"
            "detail": str | None,   # raw error text for infra failures
        }
    """
    result = {
        "outcome": SANDBOX_INFRA_FAILURE,
        "tested": None,
        "timed_out": False,
        "blocked_write": False,
        "detail": None,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="echo_functional_verify_") as scratch:
            scratch_real = os.path.realpath(scratch)
            candidate_path = os.path.join(scratch_real, "candidate.py")
            output_path = os.path.join(scratch_real, "functional_result.json")
            with open(candidate_path, "w", encoding="utf-8") as f:
                f.write(code)

            proc = subprocess.run(
                ["sandbox-exec", "-f", _SANDBOX_PROFILE, "-D", f"SCRATCH={scratch_real}",
                 sys.executable, _SANDBOX_WRAPPER, scratch_real, candidate_path,
                 "--mode=functional_verify", "--", output_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd(),
            )

            raw_err = (proc.stderr or "").strip()
            if "[SANDBOX]" in raw_err and "blocked" in raw_err.lower():
                result["blocked_write"] = True

            if proc.returncode == 0 and "SANDBOX_OK" in proc.stdout and os.path.isfile(output_path):
                with open(output_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                tested = payload.get("tested", [])
                result["tested"] = tested
                if payload.get("any_raised"):
                    result["outcome"] = VERIFIED_FAILURE
                elif payload.get("any_tested"):
                    result["outcome"] = VERIFIED_SUCCESS
                else:
                    result["outcome"] = NOT_APPLICABLE
                return result

            # Subprocess didn't complete cleanly. Distinguish "the module
            # itself failed to import" (candidate's own fault — treated as
            # VERIFIED_FAILURE, same as an import failure would already be
            # judged elsewhere in this codebase) from a genuine harness/
            # infra problem (no informative traceback, or a sandbox-level
            # denial unrelated to the candidate's own logic).
            raw = (proc.stderr or proc.stdout or "").strip()
            result["detail"] = raw[:1000]
            if "Traceback" in raw and "safe_exec_wrapper.py" in raw and "exec_module" in raw:
                result["outcome"] = VERIFIED_FAILURE
            else:
                result["outcome"] = SANDBOX_INFRA_FAILURE
            return result

    except subprocess.TimeoutExpired:
        result["timed_out"] = True
        result["outcome"] = SANDBOX_INFRA_FAILURE
        result["detail"] = f"functional_verify sandboxed call timed out after {timeout}s (process killed)"
        return result
    except Exception as e:
        result["outcome"] = SANDBOX_INFRA_FAILURE
        result["detail"] = str(e)
        return result


def combined_quality_score(code: str, task_type: str = "coding", timeout: float = 10.0) -> dict:
    """
    Computes the old AST-only score, the new functional score, and an
    explicit combined score — all three returned separately (per the
    Phase 1 authorization's requirement that the old signal remain
    available for comparison, not silently replaced).

    combined = f(ast_score, functional_outcome):
        functional == VERIFIED_FAILURE            -> combined = 0
            (a functional failure overrides AST entirely, regardless of
            how structurally complex the candidate looks)
        functional == VERIFIED_SUCCESS             -> combined = max(ast_score, 3)
            (functional success floors the score at 3; AST complexity can
            still differentiate 3 vs 4 among candidates that all execute)
        functional in (NOT_APPLICABLE, SANDBOX_INFRA_FAILURE)
                                                     -> combined = ast_score
            (no functional signal available — honest fallback to the
            existing, unchanged AST-only behavior)

    This function does not call or modify RiverBrain, self_edit_manager.py,
    or echo_model_orchestrator.py in any way. It is not called from
    anywhere in the live pipeline.
    """
    from echo_quality_scorer import _score_response_quality

    ast_score = _score_response_quality(code, task_type=task_type)
    functional = functional_execution_score(code, timeout=timeout)
    outcome = functional["outcome"]

    if outcome == VERIFIED_FAILURE:
        combined = 0
    elif outcome == VERIFIED_SUCCESS:
        combined = max(ast_score, 3)
    else:
        combined = ast_score

    return {
        "ast_score": ast_score,
        "functional_outcome": outcome,
        "functional_detail": functional,
        "combined_score": combined,
    }
