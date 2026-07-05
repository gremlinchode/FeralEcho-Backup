"""
Adversarial test for Finding 23 — snapshot_baseline.json dual-writer race fix.

Scenario: snapshot_manager and council_rater both write to snapshot_baseline.json
concurrently 100 times. After all writes complete, both fields must be present
regardless of interleaving order.

Run with:
    conda activate feral_echo
    python -m pytest sandbox/experiments/test_baseline_race.py -v
"""

import json
import os
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core import snapshot_manager


class TestBaselineRace(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._orig_path = snapshot_manager._BASELINE_META
        snapshot_manager._BASELINE_META = os.path.join(self.tmp, "snapshot_baseline.json")

    def tearDown(self):
        snapshot_manager._BASELINE_META = self._orig_path

    def test_concurrent_writes_no_field_lost(self):
        """100 iterations of both writers firing concurrently.

        Both baseline_trusted_since and council_baseline_trusted_since must
        be present after every round, regardless of thread interleaving.
        """
        ITERATIONS = 100
        errors = []

        def writer_snapshot():
            for i in range(ITERATIONS):
                try:
                    snapshot_manager.patch_baseline_meta("baseline_trusted_since", f"ts-A-{i}")
                except Exception as e:
                    errors.append(("snapshot", i, str(e)))

        def writer_council():
            for i in range(ITERATIONS):
                try:
                    snapshot_manager.patch_baseline_meta("council_baseline_trusted_since", f"ts-B-{i}")
                except Exception as e:
                    errors.append(("council", i, str(e)))

        t1 = threading.Thread(target=writer_snapshot)
        t2 = threading.Thread(target=writer_council)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertFalse(errors, f"Writer exceptions: {errors}")

        result = json.loads(open(snapshot_manager._BASELINE_META).read())
        self.assertIn("baseline_trusted_since",         result, "snapshot field lost")
        self.assertIn("council_baseline_trusted_since", result, "council field lost")

    def test_fields_survive_reversed_start_order(self):
        """Council writer starts first — same result expected."""
        ITERATIONS = 100
        errors = []

        def writer_snapshot():
            for i in range(ITERATIONS):
                try:
                    snapshot_manager.patch_baseline_meta("baseline_trusted_since", f"ts-A-{i}")
                except Exception as e:
                    errors.append(("snapshot", i, str(e)))

        def writer_council():
            for i in range(ITERATIONS):
                try:
                    snapshot_manager.patch_baseline_meta("council_baseline_trusted_since", f"ts-B-{i}")
                except Exception as e:
                    errors.append(("council", i, str(e)))

        # Reversed start order
        t2 = threading.Thread(target=writer_council)
        t1 = threading.Thread(target=writer_snapshot)
        t2.start()
        t1.start()
        t1.join()
        t2.join()

        self.assertFalse(errors, f"Writer exceptions: {errors}")

        result = json.loads(open(snapshot_manager._BASELINE_META).read())
        self.assertIn("baseline_trusted_since",         result, "snapshot field lost (reversed order)")
        self.assertIn("council_baseline_trusted_since", result, "council field lost (reversed order)")

    def test_third_field_preserved_across_concurrent_writes(self):
        """A pre-existing third field (scorer_baseline_timestamp) must survive concurrent updates."""
        # Seed the file with a third field — simulates the manually-set scorer timestamp
        initial = {
            "scorer_baseline_timestamp": "2026-07-02T07:28:31.027094+00:00",
        }
        with open(snapshot_manager._BASELINE_META, "w") as f:
            json.dump(initial, f)

        ITERATIONS = 50
        errors = []

        def writer_snapshot():
            for i in range(ITERATIONS):
                try:
                    snapshot_manager.patch_baseline_meta("baseline_trusted_since", f"ts-A-{i}")
                except Exception as e:
                    errors.append(("snapshot", i, str(e)))

        def writer_council():
            for i in range(ITERATIONS):
                try:
                    snapshot_manager.patch_baseline_meta("council_baseline_trusted_since", f"ts-B-{i}")
                except Exception as e:
                    errors.append(("council", i, str(e)))

        t1 = threading.Thread(target=writer_snapshot)
        t2 = threading.Thread(target=writer_council)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertFalse(errors, f"Writer exceptions: {errors}")

        result = json.loads(open(snapshot_manager._BASELINE_META).read())
        self.assertIn("baseline_trusted_since",         result, "snapshot field lost")
        self.assertIn("council_baseline_trusted_since", result, "council field lost")
        self.assertEqual(
            result.get("scorer_baseline_timestamp"),
            "2026-07-02T07:28:31.027094+00:00",
            "scorer_baseline_timestamp clobbered by concurrent writers",
        )


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING)
    unittest.main()
