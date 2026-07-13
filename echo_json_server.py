import hmac

from flask import Flask, request, jsonify, after_this_request
from pathlib import Path
import json
import os

# This file runs as its own standalone Flask process (see __main__ below),
# not imported by run.py, so it never had .env loaded and GREMLIN_SECRET
# was invisible to it even before the missing-auth gap below.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except Exception:
    pass

app = Flask(__name__)

FERAL_PATH = Path(__file__).parent
INBOX_FILE = FERAL_PATH / "messages/inbox.json"
OUTBOX_FILE = FERAL_PATH / "messages/outbox.json"
SYMBIOTE_LOCATION_FILE = FERAL_PATH / "data/symbiote_location.json"

# Ensure message files exist
os.makedirs(INBOX_FILE.parent, exist_ok=True)
if not INBOX_FILE.exists():
    INBOX_FILE.write_text("[]")
if not OUTBOX_FILE.exists():
    OUTBOX_FILE.write_text("[]")

# Independent copy of run.py's fail-closed secret check — this process has
# no import path to run.py's _secret_ok(), same reason routes_messaging.py
# keeps its own copy.
_GREMLIN_SECRET = os.environ.get("GREMLIN_SECRET")


def _secret_ok(payload: dict) -> bool:
    if not _GREMLIN_SECRET:
        return False
    submitted = (payload or {}).get("secret")
    if not submitted:
        return False
    return hmac.compare_digest(str(submitted), str(_GREMLIN_SECRET))


@app.route("/message", methods=["POST"])
def receive_message():
    try:
        message = request.json
        if not _secret_ok(message or {}):
            return jsonify({"error": "unauthorized"}), 403
        inbox = json.loads(INBOX_FILE.read_text())
        inbox.append(message)
        INBOX_FILE.write_text(json.dumps(inbox, indent=4))
        return jsonify({"status": "received"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/response", methods=["GET"])
def send_response():
    try:
        responses = json.loads(OUTBOX_FILE.read_text())

        # Clear only after the response has actually been handed off to the
        # client, not before — previously the outbox was wiped immediately
        # after reading, before the response even finished being built, so
        # a dropped connection between those two steps lost the queued
        # messages irrecoverably with no way to re-fetch them.
        @after_this_request
        def _clear_outbox(response):
            try:
                OUTBOX_FILE.write_text("[]")
            except Exception:
                pass
            return response

        return jsonify(responses), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/learning_event", methods=["POST"])
def learning_event():
    try:
        payload = request.json or {}
        if not _secret_ok(payload):
            return jsonify({"error": "unauthorized"}), 403
        sensors = payload.get("sensors", {})
        loc = sensors.get("location", {})
        lat = loc.get("lat")
        lon = loc.get("lon")
        if lat and lon:
            SYMBIOTE_LOCATION_FILE.write_text(json.dumps({
                "lat": lat, "lon": lon, "timezone": "America/Vancouver"
            }))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/learning_batch", methods=["POST"])
def learning_batch():
    try:
        payload = request.json or {}
        if not _secret_ok(payload):
            return jsonify({"error": "unauthorized"}), 403
        for event in payload.get("events", []):
            loc = event.get("sensors", {}).get("location", {})
            lat = loc.get("lat")
            lon = loc.get("lon")
            if lat and lon:
                SYMBIOTE_LOCATION_FILE.write_text(json.dumps({
                    "lat": lat, "lon": lon, "timezone": "America/Vancouver"
                }))
                break
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/ip", methods=["GET"])
def get_ip():
    return jsonify({"mac_ip": "100.82.172.4"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
