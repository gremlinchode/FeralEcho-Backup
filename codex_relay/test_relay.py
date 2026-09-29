import argparse
import importlib.util
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

# Loaded under a unique module name -- see claude_relay/test_relay.py's
# matching comment for why: two directories each have their own real,
# different relay.py, and a bare `import relay` in both would collide via
# the shared sys.modules cache when both suites run in one process.
_spec = importlib.util.spec_from_file_location("codex_relay_relay", Path(__file__).parent / "relay.py")
relay = importlib.util.module_from_spec(_spec)
sys.modules["codex_relay_relay"] = relay
_spec.loader.exec_module(relay)


class RelayServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = relay.RelayServer(("127.0.0.1", 0), "x" * 32, "m5", "air", Path(self.tmp.name))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def post(self, record, secret="x" * 32):
        payload = {"record": record, "signature": relay.signature(secret, record)}
        request = urllib.request.Request(
            self.base + "/message", data=json.dumps(payload).encode(), method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())

    def test_authenticated_delivery_is_idempotent(self):
        message = {"id": "message-1", "sender": "air", "recipient": "m5", "created_at": "2026-09-10T00:00:00+00:00", "message": "hello"}
        self.assertEqual(self.post(message), {"accepted": True, "duplicate": False})
        self.assertEqual(self.post(message), {"accepted": True, "duplicate": True})
        lines = (Path(self.tmp.name) / "inbox.jsonl").read_text().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["message"], "hello")

    def test_rejects_wrong_identity_and_secret(self):
        message = {"id": "message-2", "sender": "m5", "recipient": "m5", "created_at": "2026-09-10T00:00:00+00:00", "message": "nope"}
        with self.assertRaises(urllib.error.HTTPError) as wrong_sender:
            self.post(message)
        self.assertEqual(wrong_sender.exception.code, 400)
        message["sender"] = "air"
        with self.assertRaises(urllib.error.HTTPError) as wrong_secret:
            self.post(message, "y" * 32)
        self.assertEqual(wrong_secret.exception.code, 401)

    # The two tests above already exercise the signed /message path end to
    # end (idempotent delivery, bad-signature rejection combined with the
    # wrong-sender case) - these two are split out separately, contributed
    # by Air's own test_relay.py, purely for clearer per-failure attribution
    # in CI/test output, not because either was previously uncovered.
    def test_signed_idempotent_delivery(self):
        message = {"id": "message-3", "sender": "air", "recipient": "m5", "created_at": "2026-09-10T00:00:01+00:00", "message": "hello signed"}
        self.assertEqual(self.post(message), {"accepted": True, "duplicate": False})
        self.assertEqual(self.post(message), {"accepted": True, "duplicate": True})
        lines = (Path(self.tmp.name) / "inbox.jsonl").read_text().splitlines()
        self.assertEqual(len(lines), 1)

    def test_rejects_bad_signature(self):
        message = {"id": "message-4", "sender": "air", "recipient": "m5", "created_at": "2026-09-10T00:00:02+00:00", "message": "no"}
        with self.assertRaises(urllib.error.HTTPError) as failure:
            self.post(message, "b" * 32)
        self.assertEqual(failure.exception.code, 401)


class CursorIsolationTests(unittest.TestCase):
    """Discrimination tests for the independent-consumer cursor mechanism
    added in audits/2026-09-29_relay_hub_reliability_repair.md (Phase 3) —
    the general case beyond the already-fixed read-vs-read-hub pairing.
    Pure file-based, no HTTP server needed: read()/status()/paths() never
    touch the network."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp.name)
        # Seed a real inbox with two messages, as if already received.
        inbox = self.data_dir / "inbox.jsonl"
        inbox.write_text(
            json.dumps({"id": "a", "sender": "x", "recipient": "y", "created_at": "t1", "message": "first"}) + "\n"
            + json.dumps({"id": "b", "sender": "x", "recipient": "y", "created_at": "t2", "message": "second"}) + "\n"
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _read_args(self, consumer=None):
        return argparse.Namespace(data_dir=str(self.data_dir), consumer=consumer)

    def test_c1_independent_consumers_do_not_steal_each_others_unread(self):
        # Consumer A reads (and would normally consume everything).
        relay.read(self._read_args(consumer="alpha"))
        # Consumer B, a genuinely different named consumer over the SAME
        # inbox, must still see both original messages as unread.
        _, _, marker_b, _ = relay.paths(self.data_dir, consumer="beta")
        self.assertFalse(marker_b.exists(), "consumer B's cursor must not have been touched by consumer A's read")

    def test_c2_same_consumer_resumes_correctly_after_exit(self):
        relay.read(self._read_args(consumer="gamma"))  # first "session" reads everything
        _, _, marker, _ = relay.paths(self.data_dir, consumer="gamma")
        recorded_len = json.loads(marker.read_text())["length"]
        self.assertEqual(recorded_len, len((self.data_dir / "inbox.jsonl").read_text()))
        # A brand-new call (simulating the process having exited and a new
        # one started) with the SAME consumer name must resume, not replay.
        relay.read(self._read_args(consumer="gamma"))
        self.assertEqual(json.loads(marker.read_text())["length"], recorded_len)

    def test_c3_different_consumer_ids_never_collide_on_disk(self):
        relay.read(self._read_args(consumer="one"))
        relay.read(self._read_args(consumer="two"))
        _, _, marker_one, _ = relay.paths(self.data_dir, consumer="one")
        _, _, marker_two, _ = relay.paths(self.data_dir, consumer="two")
        self.assertNotEqual(marker_one, marker_two)
        self.assertTrue(marker_one.exists() and marker_two.exists())

    def test_c5_legacy_default_consumer_is_unchanged_and_deterministic(self):
        # No --consumer at all must reproduce the exact original filename
        # and behavior — real backward compatibility, not just "close enough".
        _, _, marker_default, _ = relay.paths(self.data_dir, consumer=None)
        self.assertEqual(marker_default.name, ".last_seen.json")
        relay.read(self._read_args(consumer=None))
        self.assertTrue(marker_default.exists())

    def test_c7_path_traversal_consumer_name_is_rejected(self):
        # See claude_relay/test_relay.py's identical test for the full
        # rationale -- found live during the 2026-09-29 pre-merge
        # adversarial gate, same fix shape applied to both modules.
        for hostile in ("../../../../tmp/evil", "a/b", "..", "", "x" * 200):
            with self.assertRaises(ValueError, msg=f"{hostile!r} should have been rejected"):
                relay.paths(self.data_dir, consumer=hostile)

    def test_c7_legitimate_consumer_names_still_work(self):
        for ok in ("hub", "alpha", "codex-m5", "session_1"):
            _, _, marker, _ = relay.paths(self.data_dir, consumer=ok)
            self.assertIn(f"__{ok}.json", marker.name)

    def test_c6_concurrent_same_consumer_access_does_not_corrupt_state(self):
        # Documents the real, disclosed limitation rather than asserting a
        # guarantee the storage mechanism doesn't provide (audits/2026-09-29_
        # relay_hub_reliability_semantics_audit.md Section 9, Scenario H):
        # two truly simultaneous readers of the SAME consumer name race on a
        # plain read-then-overwrite with no file lock. This test proves the
        # race is benign (no exception, no corrupted/unparseable marker,
        # final state is one of the two valid lengths) rather than faking a
        # stronger atomicity claim.
        errors = []

        def _read():
            try:
                relay.read(self._read_args(consumer="racer"))
            except Exception as e:  # pragma: no cover - only fires on a real defect
                errors.append(e)

        threads = [threading.Thread(target=_read) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [], "concurrent reads must never raise")
        _, _, marker, _ = relay.paths(self.data_dir, consumer="racer")
        # Must be valid, parseable JSON with the expected shape - not corrupted.
        recorded = json.loads(marker.read_text())
        self.assertIn("length", recorded)
        self.assertEqual(recorded["length"], len((self.data_dir / "inbox.jsonl").read_text()))


if __name__ == "__main__":
    unittest.main()
