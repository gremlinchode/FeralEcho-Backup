"""Automated regression tests for the three frozen manifests. Wires the
manifests' own cross-check functions into the real test suite - closes
hostile-review finding ROLE-1: a cross-check that only runs when someone
remembers to call it by hand is not real protection against the
checker.py drift it exists to catch.

NO REAL MODEL INFERENCE. Imports only the already-implemented,
already-tested mock apparatus.
"""
from __future__ import annotations

import unittest

from ..manifests.example_synthetic import build_example_task_manifest
from ..manifests.role_access_manifest import verify_manifest_coverage, verify_non_checker_enforcement_exists
from ..manifests.resource_budget_manifest import verify_against_real_apparatus
from ..manifests.task_manifest import MechanicalDuplicationCheck, NoveltyEvidence, QueryNoveltyRecord


class TestRoleAccessManifestCoverage(unittest.TestCase):
    def test_every_declared_rule_maps_to_a_real_checker_code(self):
        result = verify_manifest_coverage()
        self.assertEqual(result["declared_but_nonexistent"], [],
                          "a declared AccessRule points at a checker.py violation code that does not exist - "
                          "the manifest has drifted from the real, currently-enforced checker")

    def test_no_undocumented_real_checker_code(self):
        result = verify_manifest_coverage()
        self.assertEqual(result["real_codes_with_no_declared_rule"], [],
                          "checker.py enforces a real invariant with no corresponding declared AccessRule - "
                          "either map it to a stage or add it to INTENTIONALLY_UNMAPPED_CODES with a documented reason")

    def test_no_stage_left_with_zero_enforcement(self):
        result = verify_manifest_coverage()
        self.assertEqual(result["stages_with_zero_checker_enforcement_and_no_cross_reference"], [])

    def test_non_checker_enforcement_mechanisms_still_exist(self):
        result = verify_non_checker_enforcement_exists()
        for label, exists in result.items():
            self.assertTrue(exists, f"{label}: NON_CHECKER_ENFORCEMENT claims protection from something that no longer resolves")


class TestResourceBudgetManifestAgainstRealApparatus(unittest.TestCase):
    def test_frozen_budget_matches_real_apparatus(self):
        result = verify_against_real_apparatus()
        self.assertEqual(result["mismatches"], [], f"resource-budget manifest has drifted from the real apparatus: {result['mismatches']}")
        self.assertTrue(result["arm_budget_matches_real_apparatus"])
        self.assertTrue(result["options_match_real_apparatus"])
        self.assertTrue(result["cost_accounting_rule_verified_live"])


class TestTaskManifestFreezeAndTamperDetection(unittest.TestCase):
    def test_clean_manifest_freezes_and_verifies_clean(self):
        tm = build_example_task_manifest(n_families=2)
        self.assertEqual(tm.unvalidated_related_queries(), [])
        tm.freeze()
        self.assertTrue(tm.verify_not_tampered())

    def test_cannot_freeze_with_unvalidated_related_queries(self):
        tm = build_example_task_manifest(n_families=1)
        # Remove all novelty records for one family - now every related
        # query is unvalidated.
        tm.families[0].related_query_novelty = []
        with self.assertRaises(ValueError):
            tm.freeze()

    def test_cannot_freeze_twice(self):
        tm = build_example_task_manifest(n_families=1)
        tm.freeze()
        with self.assertRaises(ValueError):
            tm.freeze()

    def test_internal_content_tamper_is_detected_without_touching_family_ids(self):
        """Regression test for hostile-review finding TASK-1: a forged
        passing novelty record snuck into an already-frozen family, with
        family_ids completely unchanged, must still be caught."""
        tm = build_example_task_manifest(n_families=2)
        tm.freeze()
        original_family_ids = sorted(f.family_id for f in tm.families)

        fake_mech = MechanicalDuplicationCheck(query_id="FORGED", exact_hash_match=False,
            lexical_similarity_score=0.0, ast_or_control_flow_identical=False, io_structure_identical=False,
            reviewer_note="FORGED")
        fake_novelty = NoveltyEvidence(query_id="FORGED", blind_zero_context_attempts=1,
            blind_zero_context_successes=0, teaching_informed_attempts=1, teaching_informed_successes=1)
        tm.families[0].related_query_novelty.append(
            QueryNoveltyRecord(query_id="FORGED", mechanical=fake_mech, novelty=fake_novelty,
                                min_difficulty_gap=0.30, passed=True))

        self.assertEqual(sorted(f.family_id for f in tm.families), original_family_ids,
                          "sanity: this tamper must NOT change the family_id set (that's the whole point of this test)")
        self.assertFalse(tm.verify_not_tampered(),
                          "internal-content tamper (forged novelty record) went undetected - TASK-1 regression")

    def test_post_hoc_family_exclusion_is_detected(self):
        tm = build_example_task_manifest(n_families=2)
        tm.freeze()
        removed_id = tm.families[0].family_id
        analyzed = {f.family_id for f in tm.families} - {removed_id}
        with self.assertRaises(ValueError):
            tm.assert_no_family_removed(analyzed)

    def test_unfrozen_family_in_analysis_is_detected(self):
        tm = build_example_task_manifest(n_families=2)
        tm.freeze()
        analyzed = {f.family_id for f in tm.families} | {"fam_never_frozen"}
        with self.assertRaises(ValueError):
            tm.assert_no_family_removed(analyzed)

    def test_exact_analyzed_set_passes_cleanly(self):
        tm = build_example_task_manifest(n_families=2)
        tm.freeze()
        analyzed = {f.family_id for f in tm.families}
        tm.assert_no_family_removed(analyzed)  # must not raise


if __name__ == "__main__":
    unittest.main()
