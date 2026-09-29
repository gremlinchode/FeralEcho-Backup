"""Discrimination tests for claude_relay/relay.py's independent-consumer
cursor mechanism (audits/2026-09-29_relay_hub_reliability_repair.md, Phase 3
— the general case beyond the already-fixed read-vs-read-hub pairing, which
this file deliberately does not touch or re-test).

Monkeypatches _fetch_remote_file() rather than hitting the real network or a
real peer server — these tests are about cursor *isolation* semantics, not
the HTTP fetch itself (already covered, for the sibling codex_relay module,
by codex_relay/test_relay.py's RelayServerTests).
"""
import importlib.util
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

# Loaded under a unique module name (not the bare "relay") so this file can
# run in the same process as codex_relay/test_relay.py without either one's
# `import relay` silently reusing the other's already-cached sys.modules
# entry — both directories happen to have their own real, DIFFERENT
# relay.py. Found live, during this repair mission's own test run, not
# theorized: running both suites together previously made codex_relay's
# tests fail with the wrong module's attributes.
_spec = importlib.util.spec_from_file_location("claude_relay_relay", Path(__file__).parent / "relay.py")
relay = importlib.util.module_from_spec(_spec)
sys.modules["claude_relay_relay"] = relay
_spec.loader.exec_module(relay)


class CursorIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._orig_relay_dir = relay._RELAY_DIR
        relay._RELAY_DIR = self.tmp.name
        # A real, non-empty "remote" mailbox content every fetch returns.
        self.remote_content = "## Entry\n\nfirst\n\n---\n## Entry\n\nsecond\n\n---\n"
        self._fetch_patch = mock.patch.object(
            relay, "_fetch_remote_file", return_value=(self.remote_content, None)
        )
        self._fetch_patch.start()

    def tearDown(self):
        self._fetch_patch.stop()
        relay._RELAY_DIR = self._orig_relay_dir
        self.tmp.cleanup()

    def test_c1_independent_consumers_do_not_steal_each_others_unread(self):
        relay.read_new(consumer="alpha")
        marker_beta = Path(relay._marker_file(consumer="beta"))
        self.assertFalse(marker_beta.exists(), "consumer B's cursor must be untouched by consumer A's read")
        # Confirm B genuinely still sees the full content as new.
        result = relay.read_new(consumer="beta")
        self.assertIn("first", result)
        self.assertIn("second", result)

    def test_c2_same_consumer_resumes_correctly_after_exit(self):
        relay.read_new(consumer="gamma")
        marker = Path(relay._marker_file(consumer="gamma"))
        recorded_len = relay._load_marker(str(marker))["length"]
        # A second, independent call with the same consumer name must not
        # replay the backlog (nothing "new" left to show), and the cursor's
        # real position (its length field, not the full JSON text -- which
        # legitimately carries a fresh checked_at timestamp each write) must
        # stay exactly where it was.
        second = relay.read_new(consumer="gamma")
        self.assertIn("Nothing new", second)
        self.assertEqual(relay._load_marker(str(marker))["length"], recorded_len)

    def test_c3_different_consumer_ids_never_collide_on_disk(self):
        marker_one = Path(relay._marker_file(consumer="one"))
        marker_two = Path(relay._marker_file(consumer="two"))
        self.assertNotEqual(marker_one, marker_two)
        relay.read_new(consumer="one")
        relay.read_new(consumer="two")
        self.assertTrue(marker_one.exists() and marker_two.exists())

    def test_c4_hub_cursor_remains_fully_independent_and_untouched(self):
        # The pre-existing, already-fixed hub-specific cursor must keep
        # working exactly as before — this repair adds a general mechanism
        # alongside it, it does not touch or subsume it.
        relay.read_new(consumer="anything")  # a generic named consumer reads first
        hub_result = relay.read_new_for_hub()  # hub's own dedicated cursor
        self.assertIn("first", hub_result)
        self.assertIn("second", hub_result)

    def test_c5_legacy_default_consumer_is_unchanged_and_deterministic(self):
        default_marker = relay._marker_file()
        self.assertTrue(default_marker.endswith(".last_seen_from_air.json"))
        self.assertNotIn("__", Path(default_marker).name)
        result = relay.read_new()  # no consumer at all -- the original call shape
        self.assertIn("first", result)

    def test_c6_concurrent_same_consumer_access_does_not_corrupt_state(self):
        errors = []

        def _read():
            try:
                relay.read_new(consumer="racer")
            except Exception as e:  # pragma: no cover - only on a real defect
                errors.append(e)

        threads = [threading.Thread(target=_read) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [], "concurrent reads must never raise")
        marker = Path(relay._marker_file(consumer="racer"))
        self.assertTrue(marker.exists())
        recorded = relay._load_marker(str(marker))
        self.assertIn("length", recorded)


if __name__ == "__main__":
    unittest.main()
