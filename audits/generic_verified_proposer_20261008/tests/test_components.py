"""PUBLIC developer tests. Source strings are parsed/transformed, NEVER executed.

Observation batches below are manufactured component inputs, not experimental
candidate outputs, hidden cases, oracle qualification or repair-performance data.
"""
import ast
import copy
import json
from pathlib import Path
import tempfile
import unittest

from b_prototype.contracts import (authority_status, digest, parse_task,
                                   source_hash, strict_json)
from b_prototype.proposer import propose, apply_patch, verify_commit
from b_prototype.verification import (winner, check_observation, assess,
                                     execute_candidate)
from b_prototype.journal import write_event


SOURCE = '''def pick(entries):
    ranks = {"red": 0, "green": 1, "blue": 2}
    ordered = sorted(entries, key=lambda row: (-row[1], -ranks[row[2]], row[0]))
    return ordered[0][0]
'''


def contract(source=SOURCE, **requirements):
    req = {"score_direction": "higher", "tag_order": ["red", "green", "blue"],
           "name_direction": "ascending", "return_type": "str",
           "input_effects": "preserve_values",
           "field_schema": ["name:str", "score:int", "tag:str"]}
    req.update(requirements)
    return {"schema": "B-TASK-1", "task_id": "PUBLIC_COMPONENT_ONLY", "revision": "1",
            "source_sha256": source_hash(source), "entrypoint": "pick", "requirements": req,
            "unknown_fields": [], "conflict_refs": []}


def fixture_registry(c):
    # Explicitly simulated authority for local API tests. No human role acceptance.
    return {c["task_id"]: {"revision": c["revision"], "contract_sha256": digest(c),
                           "owner_ref": "PUBLIC_TEST_NOT_REAL_APPROVAL",
                           "oracle_review_ref": "PUBLIC_TEST_NOT_REAL_APPROVAL"}}


class AuthorityTests(unittest.TestCase):
    def test_approval_is_external_to_contract(self):
        c = contract()
        self.assertEqual(authority_status(SOURCE, c, {})["status"], "UNKNOWN_CONTRACT")
        self.assertEqual(authority_status(SOURCE, c, fixture_registry(c))["status"], "VALID_CONTRACT")
        c["approved"] = True
        self.assertEqual(authority_status(SOURCE, c, fixture_registry(c))["status"], "UNSUPPORTED_CONTRACT")

    def test_nonvalid_states_never_authorize(self):
        for field, value, status in [
                ("unknown_fields", ["ownership"], "UNKNOWN_CONTRACT"),
                ("conflict_refs", ["different intent"], "CONFLICTING_CONTRACT"),
                ("schema", "unknown", "UNSUPPORTED_CONTRACT")]:
            with self.subTest(status=status):
                c = contract(); c[field] = value
                self.assertEqual(authority_status(SOURCE, c, fixture_registry(c))["status"], status)
        c = contract()
        self.assertEqual(authority_status(SOURCE + "\n", c, fixture_registry(c))["status"], "STALE_CONTRACT")
        r = fixture_registry(c); r[c["task_id"]]["revision"] = "old"
        self.assertEqual(authority_status(SOURCE, c, r)["status"], "STALE_CONTRACT")

    def test_strict_json(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(ValueError): strict_json(raw)

    def test_missing_requirement_and_contradictory_order(self):
        c = contract(); del c["requirements"]["name_direction"]
        self.assertEqual(authority_status(SOURCE, c, fixture_registry(c))["status"], "UNKNOWN_CONTRACT")
        c = contract(tag_order=["red", "red", "blue"])
        self.assertEqual(authority_status(SOURCE, c, fixture_registry(c))["status"], "CONFLICTING_CONTRACT")

    def test_proposer_unknown_and_stale(self):
        c = contract(); c["unknown_fields"] = ["tag_order"]
        self.assertFalse(propose(SOURCE, c)["proposals"])
        self.assertFalse(propose(SOURCE + "\n", contract())["proposals"])


class ProposalTests(unittest.TestCase):
    def test_simple_repair_is_prioritized_not_authorized(self):
        result = propose(SOURCE, contract())
        self.assertIsNone(result["refusal"])
        self.assertEqual(len(result["proposals"]), 2)
        self.assertEqual(result["proposals"][0]["site"]["polarity"], "POLARITY_INCONSISTENT")
        self.assertTrue(result["proposals"][0]["site"]["map_derived"])
        self.assertEqual(result["authority"], "NOT_ESTABLISHED_BY_PROPOSER")
        self.assertEqual(result["candidate_executions"], 0)
        self.assertTrue(verify_commit(SOURCE, contract(), result))

    def test_four_selection_modes_and_two_map_orientations(self):
        for reverse in (False, True):
            for endpoint in (0, -1):
                for descending_map in (False, True):
                    with self.subTest(reverse=reverse, endpoint=endpoint, map=descending_map):
                        src = SOURCE.replace("ordered[0]", f"ordered[{endpoint}]")
                        src = src.replace("row[0]))", f"row[0]), reverse={reverse})")
                        if descending_map:
                            src = src.replace('"red": 0, "green": 1, "blue": 2',
                                              '"red": 2, "green": 1, "blue": 0')
                        plan = propose(src, contract(src))
                        self.assertIsNone(plan["refusal"])
                        q = (-1 if endpoint == 0 else 1) * (-1 if reverse else 1)
                        d = 1 if descending_map else -1
                        expected = "POLARITY_INCONSISTENT" if q * -1 * d < 0 else "POLARITY_CONSISTENT"
                        tags = [x for x in plan["eligible_sites"] if x["map_derived"]]
                        self.assertTrue(tags)
                        self.assertTrue(all(x["polarity"] == expected for x in tags))

    def test_opposite_task_changes_direction_without_source_change(self):
        a = propose(SOURCE, contract())
        b = propose(SOURCE, contract(tag_order=["blue", "green", "red"]))
        self.assertTrue(any(x["polarity"] == "POLARITY_INCONSISTENT" for x in a["eligible_sites"] if x["map_derived"]))
        self.assertTrue(all(x["polarity"] == "POLARITY_CONSISTENT" for x in b["eligible_sites"] if x["map_derived"]))

    def test_direct_score_uses_common_rule(self):
        src = SOURCE.replace("-row[1]", "row[1]").replace("-ranks", "ranks")
        plan = propose(src, contract(src))
        self.assertEqual(plan["proposals"][0]["site"]["uses"][0]["role"], "score")
        self.assertEqual(plan["proposals"][0]["site"]["polarity"], "POLARITY_INCONSISTENT")

    def test_alpha_renaming_preserves_polarity(self):
        src = SOURCE.replace("entries", "records").replace("ranks", "encoding").replace("row", "item")
        plan = propose(src, contract(src))
        self.assertIsNone(plan["refusal"])
        self.assertEqual(plan["proposals"][0]["site"]["polarity"], "POLARITY_INCONSISTENT")

    def test_helper_extraction(self):
        src = '''def pick(entries):
    ranks = {"red": 0, "green": 1, "blue": 2}
    def key(row):
        priority = -ranks[row[2]]
        return (-row[1], priority, row[0])
    ordered = sorted(entries, key=key)
    return ordered[0][0]
'''
        plan = propose(src, contract(src))
        self.assertIsNone(plan["refusal"])
        self.assertTrue(plan["proposals"][0]["site"]["map_derived"])
        self.assertEqual(plan["proposals"][0]["site"]["polarity"], "POLARITY_INCONSISTENT")

    def test_owned_sort_and_shallow_comprehension(self):
        for copy_expression in ("list(entries)", "[[row[0], row[1], row[2]] for row in entries]"):
            src = SOURCE.replace("ordered = sorted(entries, key=", f"ordered = {copy_expression}\n    ordered.sort(key=")
            plan = propose(src, contract(src))
            self.assertIsNone(plan["refusal"])
            self.assertEqual(plan["proposals"][0]["site"]["polarity"], "POLARITY_INCONSISTENT")

    def test_input_alias_is_rejected(self):
        src = SOURCE.replace("ordered = sorted(entries, key=", "ordered = entries\n    ordered.sort(key=")
        self.assertIn("owned outer list", propose(src, contract(src))["refusal"])

    def test_dead_sort_does_not_consume_slots(self):
        src = SOURCE.replace("    ordered =", "    unused = sorted(entries, key=lambda z: (-z[1], -ranks[z[2]], z[0]))\n    ordered =")
        plan = propose(src, contract(src))
        self.assertIsNone(plan["refusal"])
        self.assertTrue(all(x["position"][0] == 4 for x in plan["eligible_sites"]))

    def test_bad_precedence_and_nonmonotone_maps_use_fallback(self):
        for src in (SOURCE.replace("-row[1], -ranks[row[2]]", "-ranks[row[2]], -row[1]"),
                    SOURCE.replace('"red": 0, "green": 1, "blue": 2',
                                   '"red": 0, "green": 2, "blue": 1')):
            plan = propose(src, contract(src))
            self.assertIsNone(plan["refusal"])
            self.assertTrue(plan["proposals"])
            tags = [x for x in plan["eligible_sites"] if x["map_derived"]]
            self.assertTrue(all(x["polarity"] == "POLARITY_UNKNOWN" for x in tags))

    def test_unsupported_effects_fail_closed_without_execution(self):
        cases = [SOURCE.replace("    ranks =", "    import os\n    ranks ="),
                 SOURCE.replace("    ranks =", "    entries[0][1] = 99\n    ranks ="),
                 SOURCE.replace("    ranks =", "    sorted = list\n    ranks ="),
                 SOURCE.replace("    return ordered[0][0]", "    return open('/tmp/forbidden').read()"),
                 SOURCE.replace("    return ordered[0][0]", "    return pick(entries)"),
                 SOURCE.replace("    ordered =", "    ranks = ranks\n    ordered =")]
        for src in cases:
            with self.subTest(source=src):
                plan = propose(src, contract(src))
                self.assertTrue(plan["refusal"])
                self.assertFalse(plan["proposals"])

    def test_patch_is_exact_and_commit_tampering_rejected(self):
        c = contract(); plan = propose(SOURCE, c)
        p = plan["proposals"][0]
        derived = apply_patch(SOURCE, p["patch"])
        self.assertEqual(source_hash(derived), p["derived_source_sha256"])
        ast.parse(derived)  # Parsing is not candidate execution.
        tampered = copy.deepcopy(plan); tampered["proposals"][0]["patch"]["path"] = ["body", 0]
        self.assertFalse(verify_commit(SOURCE, c, tampered))
        patch = copy.deepcopy(p["patch"]); patch["old_subtree_sha256"] = "0" * 64
        with self.assertRaises(ValueError): apply_patch(SOURCE, patch)

    def test_public_structural_budgets_fail_closed(self):
        oversized = SOURCE + "#" * 8192
        self.assertFalse(propose(oversized, contract(oversized))["proposals"])
        extras = "".join(f"    def unused{i}(row):\n        return row\n" for i in range(3))
        src = SOURCE.replace("    ranks =", extras + "    ranks =")
        plan = propose(src, contract(src))
        self.assertIn("two helpers", plan["refusal"])
        self.assertFalse(plan["proposals"])


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.c = contract()
        self.task = parse_task(self.c)
        self.plan = propose(SOURCE, self.c)
        # Public synthetic API observations; no claimed task execution.
        self.inputs = [[[f"item{i}", 1, "red"]] for i in range(24)]

    def batch(self, source_sha, correct=True):
        return {"phase": "decision", "source_sha256": source_sha,
                "contract_sha256": digest(self.c), "inputs_sha256": digest(self.inputs),
                "observations": [{"outcome": "RETURNED", "value": x[0][0] if correct else "wrong",
                                  "input_after": copy.deepcopy(x)} for x in self.inputs]}

    def evidence(self):
        original = self.batch(source_hash(SOURCE), False)
        proposals = [self.batch(p["derived_source_sha256"]) for p in self.plan["proposals"]]
        return original, proposals

    def decide(self, original, proposals):
        return assess(SOURCE, self.c, fixture_registry(self.c), self.plan, self.inputs, original, proposals)

    def test_independent_oracle_score_tag_name_singleton(self):
        examples = [([["x", 9, "blue"], ["y", 1, "red"]], "x"),
                    ([["x", 1, "blue"], ["y", 1, "red"]], "y"),
                    ([["z", 1, "red"], ["a", 1, "red"]], "a"),
                    ([["sole", -3, "green"]], "sole")]
        for entries, expected in examples:
            self.assertEqual(winner(entries, self.task), expected)
        with self.assertRaises(ValueError): winner([["x", True, "red"]], self.task)
        with self.assertRaises(ValueError): winner([["x", 1.0, "red"]], self.task)

    def test_correct_repair_is_only_provisional(self):
        result = self.decide(*self.evidence())
        self.assertEqual(result["decision"], "PROVISIONAL_ACCEPT_EXACT_PATCH")
        self.assertFalse(result["production_authorized"])
        self.assertFalse(result["execution_qualified"])

    def test_missing_approval_abstains_before_evidence(self):
        result = assess(SOURCE, self.c, {}, self.plan, None, None, None)
        self.assertEqual(result["decision"], "ABSTAIN_CONTRACT")

    def test_correct_original_rejects_edit(self):
        original, proposals = self.evidence()
        original = self.batch(source_hash(SOURCE))
        self.assertEqual(self.decide(original, proposals)["decision"], "REJECT_NO_IMPROVEMENT")

    def test_partial_fix_and_regression_rejected(self):
        original, proposals = self.evidence()
        for p in proposals:
            p["observations"][1]["value"] = "wrong"
        self.assertEqual(self.decide(original, proposals)["decision"], "REJECT_NO_IMPROVEMENT")

    def test_mutation_bool_int_and_wrong_return_type(self):
        entries = [["x", 1, "red"]]
        for after, value in [([["x", True, "red"]], "x"),
                             ([["x", 1.0, "red"]], "x"),
                             ([["x", 2, "red"]], "x"), (entries, True)]:
            self.assertFalse(check_observation({"outcome": "RETURNED", "value": value,
                                               "input_after": after}, entries, self.task)["correct"])

    def test_hidden_incomplete_stale_and_infrastructure_fail_closed(self):
        for kind in ("hidden", "partial", "stale", "infrastructure"):
            with self.subTest(kind=kind):
                original, proposals = self.evidence()
                if kind == "hidden": proposals[-1]["phase"] = "hidden"
                elif kind == "partial": proposals[-1]["observations"].pop()
                elif kind == "stale": proposals[-1]["source_sha256"] = "0" * 64
                else: original["observations"][0]["outcome"] = "SANDBOX_INFRASTRUCTURE_ERROR"
                self.assertEqual(self.decide(original, proposals)["decision"], "MEASUREMENT_ERROR")

    def test_candidate_timeout_is_not_conformance(self):
        original, proposals = self.evidence()
        for p in proposals:
            p["observations"][0]["outcome"] = "TIMEOUT"
        self.assertEqual(self.decide(original, proposals)["decision"], "REJECT_NO_IMPROVEMENT")

    def test_execution_backend_unavailable(self):
        with self.assertRaisesRegex(RuntimeError, "qualification required"):
            execute_candidate(SOURCE)


class JournalTests(unittest.TestCase):
    def test_exclusive_create_and_evidence_survives_cleanup_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            h = write_event(root, "before_cleanup", {"provisional_outcome": "recorded"})
            self.assertEqual(len(h), 64)
            try:
                raise OSError("simulated teardown failure; no candidate ran")
            except OSError:
                write_event(root, "cleanup_failure", {"error": "simulated"})
            self.assertEqual(json.loads((root / "before_cleanup.json").read_text()),
                             {"provisional_outcome": "recorded"})
            with self.assertRaises(FileExistsError): write_event(root, "before_cleanup", {})
            with self.assertRaises(ValueError): write_event(root, "../outside", {})

    def test_symlink_leaf_does_not_overwrite_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "ordinary.txt"; target.write_text("unchanged")
            (root / "alias.json").symlink_to(target)
            with self.assertRaises(FileExistsError): write_event(root, "alias", {"changed": True})
            self.assertEqual(target.read_text(), "unchanged")


if __name__ == "__main__":
    unittest.main()
