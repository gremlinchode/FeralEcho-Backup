"""E/U/S/D/O provenance records (frozen design §10). Written only by the
harness controller, never by the selector or the generation call itself.
One dedicated JSONL per record type, under this experiment's own EXP_ROOT --
never memory/self_edit_attempt_ledger.jsonl, never memory/river_brain.pkl."""
from __future__ import annotations
import time
from .common import EXP_ROOT, append_jsonl


def log_experience(lineage_id, task_id, feature_signature, strategy_used, oracle_outcome: bool):
    """E record: one per completed prospective-phase decision."""
    row = {
        "lineage_id": lineage_id, "task_id": task_id,
        "feature_signature": list(feature_signature), "strategy_used": strategy_used,
        "oracle_outcome": "PASS" if oracle_outcome else "FAIL",
        "timestamp": time.time(),
    }
    append_jsonl(EXP_ROOT / "log_E_experience.jsonl", row)
    return row


def log_update(lineage_id, pre_state_hash, post_state_hash, selector_code_version_hash):
    row = {
        "lineage_id": lineage_id, "pre_state_hash": pre_state_hash,
        "post_state_hash": post_state_hash, "selector_code_version_hash": selector_code_version_hash,
        "timestamp": time.time(),
    }
    append_jsonl(EXP_ROOT / "log_U_update.jsonl", row)
    return row


def log_decision(lineage_id, arm, holdout_task_id, state_hash_used, feature_signature,
                  strategy_selected, selection_probability, random_seed_used):
    row = {
        "lineage_id": lineage_id, "arm": arm, "holdout_task_id": holdout_task_id,
        "state_hash_used": state_hash_used, "feature_signature": list(feature_signature),
        "strategy_selected": strategy_selected, "selection_probability": selection_probability,
        "random_seed_used": random_seed_used, "timestamp": time.time(),
    }
    append_jsonl(EXP_ROOT / "log_D_decision.jsonl", row)
    return row


def log_execution(lineage_id, arm, holdout_task_id, candidate_code_hash, model_digest):
    row = {
        "lineage_id": lineage_id, "arm": arm, "holdout_task_id": holdout_task_id,
        "candidate_code_hash": candidate_code_hash, "model_digest": model_digest,
        "generation_time": time.time(),
    }
    append_jsonl(EXP_ROOT / "log_execution.jsonl", row)
    return row


def log_outcome(lineage_id, arm, holdout_task_id, oracle_pass_fail: bool, evaluator_nonce,
                 evaluator_code_version_hash, infra=False, timeout=False):
    row = {
        "lineage_id": lineage_id, "arm": arm, "holdout_task_id": holdout_task_id,
        "oracle_pass_fail": bool(oracle_pass_fail), "evaluator_nonce": evaluator_nonce,
        "evaluator_code_version_hash": evaluator_code_version_hash,
        "infra": bool(infra), "timeout": bool(timeout), "timestamp": time.time(),
    }
    append_jsonl(EXP_ROOT / "log_O_outcome.jsonl", row)
    return row
