"""Independent task oracle and provisional decisions over supplied observations.

There is deliberately no candidate execution backend or production authorization.
This module cannot establish that a supplied observation actually came from E0.1.
"""
from .contracts import authority_status, digest, parse_task, source_hash
from .proposer import apply_patch, verify_commit
from .analysis import Analyzer, Unsupported


def validate_entries(entries, task):
    if type(entries) is not list or not 1 <= len(entries) <= 3:
        raise ValueError("input must contain one to three entries")
    names = []
    for row in entries:
        if type(row) is not list or len(row) != 3:
            raise ValueError("invalid entry")
        name, score, tag = row
        if type(name) is not str or not name or not name.isascii() or len(name) > 64:
            raise ValueError("invalid name")
        if type(score) is not int or score.bit_length() > 63:
            raise ValueError("score must be a bounded exact int, not bool/float")
        if type(tag) is not str or tag not in task.tag_order:
            raise ValueError("invalid tag")
        names.append(name)
    if len(set(names)) != len(names):
        raise ValueError("duplicate names")


def winner(entries, task):
    """Pairwise task specification; never uses candidate maps or repair signs."""
    validate_entries(entries, task)
    best = entries[0]
    for item in entries[1:]:
        if item[1] != best[1]:
            preferred = item[1] > best[1] if task.score_direction == "higher" else item[1] < best[1]
        elif item[2] != best[2]:
            preferred = task.tag_order.index(item[2]) < task.tag_order.index(best[2])
        else:
            preferred = item[0] < best[0] if task.name_direction == "ascending" else item[0] > best[0]
        if preferred:
            best = item
    return best[0]


def exact_equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is list:
        return len(a) == len(b) and all(exact_equal(x, y) for x, y in zip(a, b))
    if type(a) in (str, int, bool, float, type(None)):
        return a == b
    return False


def check_observation(observation, expected_input, task):
    """No child-supplied CORRECT flag or expected value is trusted."""
    fields = {"outcome", "value", "input_after"}
    if type(observation) is not dict or set(observation) != fields:
        return {"correct": False, "reason": "MALFORMED_OBSERVATION"}
    if observation["outcome"] != "RETURNED":
        return {"correct": False, "reason": "CHILD_FAILURE_OR_TIMEOUT"}
    try:
        validate_entries(observation["input_after"], task)
        expected = winner(expected_input, task)
    except ValueError:
        return {"correct": False, "reason": "UNSUPPORTED_OBSERVATION"}
    if type(observation["value"]) is not str or len(observation["value"]) > 64:
        return {"correct": False, "reason": "RETURN_TYPE_OR_BOUND"}
    if not exact_equal(observation["input_after"], expected_input):
        return {"correct": False, "reason": "INPUT_MUTATION"}
    if observation["value"] != expected:
        return {"correct": False, "reason": "WRONG_WINNER"}
    return {"correct": True, "reason": "OBSERVED_CONFORMANCE"}


def check_batch(batch, inputs, source_sha256, contract, task):
    required = {"phase", "source_sha256", "contract_sha256", "inputs_sha256", "observations"}
    if type(batch) is not dict or set(batch) != required:
        raise ValueError("malformed evidence batch")
    if batch["phase"] != "decision":
        raise ValueError("hidden evidence cannot enter acceptance")
    if (batch["source_sha256"] != source_sha256 or batch["contract_sha256"] != digest(contract)
            or batch["inputs_sha256"] != digest(inputs)):
        raise ValueError("stale or mismatched evidence")
    observations = batch["observations"]
    if type(observations) is not list or len(observations) != len(inputs):
        raise ValueError("incomplete decision evidence")
    if any(type(o) is not dict or o.get("outcome") not in
           ("RETURNED", "CANDIDATE_ERROR", "TIMEOUT") for o in observations):
        raise ValueError("infrastructure failure or invalid child status")
    return [check_observation(o, x, task) for o, x in zip(observations, inputs)]


def assess(source, contract, registry, commit, inputs, original_batch, proposal_batches):
    """Trusted-controller interface. Only provisional diagnostic conclusions.

    Inputs, registry and observations must stay outside the proposer process.
    Full suites are required here; a future executor can journal early failures
    separately, but may not pass partial evidence to this acceptance interface.
    """
    result = {"schema": "B-DECISION-1", "source_sha256": source_hash(source),
              "contract_sha256": digest(contract), "decision": "MEASUREMENT_ERROR",
              "production_authorized": False, "execution_qualified": False,
              "selected_proposal": None, "checks": [], "reason": None}
    authority = authority_status(source, contract, registry)
    result["authority"] = authority
    if authority["status"] != "VALID_CONTRACT":
        result.update(decision="ABSTAIN_CONTRACT", reason=authority["status"])
        return result
    try:
        task = parse_task(contract)
        if not verify_commit(source, contract, commit):
            raise ValueError("forged or stale proposal commitment")
        if commit["refusal"] and commit["refusal"] != "NO_ELIGIBLE_SITE":
            result.update(decision="REJECT_UNSAFE_OR_UNSUPPORTED", reason=commit["refusal"])
            return result
        if type(inputs) is not list or len(inputs) != 24:
            raise ValueError("exactly 24 decision inputs required")
        if len({digest(x) for x in inputs}) != 24:
            raise ValueError("duplicate decision inputs")
        for x in inputs:
            validate_entries(x, task)
        # Coverage allocation/oracle approval are external qualification gates.
        if type(proposal_batches) is not list or len(proposal_batches) != len(commit["proposals"]):
            raise ValueError("proposal evidence count mismatch")
        originals = check_batch(original_batch, inputs, source_hash(source), contract, task)
        all_checks = []
        for proposal, batch in zip(commit["proposals"], proposal_batches):
            derived = apply_patch(source, proposal["patch"])
            if source_hash(derived) != proposal["derived_source_sha256"]:
                raise ValueError("derived-source mismatch")
            Analyzer(derived, task).analyze()
            all_checks.append(check_batch(batch, inputs, source_hash(derived), contract, task))
        result["original_checks"] = originals
        if all(x["correct"] for x in originals):
            result.update(decision="REJECT_NO_IMPROVEMENT", reason="ORIGINAL_ALREADY_CONFORMS")
            return result
        for i, (proposal, checks) in enumerate(zip(commit["proposals"], all_checks)):
            result["checks"].append({"proposal": i, "checks": checks})
            if all(x["correct"] for x in checks):
                result.update(decision="PROVISIONAL_ACCEPT_EXACT_PATCH", selected_proposal=i,
                              reason="COMPLETE_SUPPLIED_DECISION_CONFORMANCE",
                              derived_source_sha256=proposal["derived_source_sha256"])
                return result
        result.update(decision="REJECT_NO_IMPROVEMENT", reason="NO_COMPLETE_REPAIR")
    except (ValueError, TypeError, Unsupported, RecursionError) as e:
        result.update(decision="MEASUREMENT_ERROR", reason=str(e))
    return result


def execute_candidate(*args, **kwargs):
    raise RuntimeError("Execution unavailable: new boundary/oracle/custody qualification required")
