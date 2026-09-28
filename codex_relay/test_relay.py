import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import relay


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


if __name__ == "__main__":
    unittest.main()
