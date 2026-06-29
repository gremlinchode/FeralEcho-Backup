from flask import Flask, request, jsonify
from pathlib import Path
import json
import os

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

@app.route("/message", methods=["POST"])
def receive_message():
    try:
        message = request.json
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
        OUTBOX_FILE.write_text("[]")
        return jsonify(responses), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/learning_event", methods=["POST"])
def learning_event():
    try:
        payload = request.json or {}
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
