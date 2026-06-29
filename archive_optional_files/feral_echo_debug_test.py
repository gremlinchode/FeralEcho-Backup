#!/usr/bin/env python3
"""
FeralEcho Debug Test Harness
- Starts a Flask server
- Tests /status and /message routes
- Runs autonomous fetch from internet_tools
- Logs everything at DEBUG level
"""

import logging
import traceback
import threading
import time
import sys

from flask import Flask, request, jsonify

# --- Debug logging ---
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# --- Flask app ---
app = Flask(__name__)

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "OK", "timestamp": time.time()})

@app.route("/message", methods=["POST"])
def message():
    try:
        data = request.get_json(force=True)
        user_msg = data.get("message", "")
        logging.debug(f"Received message: {user_msg}")
        # Simulate Echo response
        return jsonify({"response": f"Echo received: {user_msg}"})
    except Exception:
        logging.error("Error handling /message route:\n" + traceback.format_exc())
        return jsonify({"response": "Error"}), 500

# --- Function to start Flask in a thread ---
def start_flask():
    logging.info("Starting Flask server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

# --- Test autonomous fetch ---
def test_autonomous_fetch():
    try:
        logging.info("Importing autonomous fetch...")
        from app.internet_tools.autonomous_fetch import run_autonomous_fetch
        logging.info("Running autonomous fetch...")
        run_autonomous_fetch()
        logging.info("Autonomous fetch test complete.")
    except ModuleNotFoundError as e:
        logging.error(f"ModuleNotFoundError: {e}")
    except Exception as e:
        logging.error("Error during autonomous fetch:\n" + traceback.format_exc())

# --- Test Flask messaging via requests ---
def test_flask_message():
    import requests
    try:
        time.sleep(2)  # give Flask time to start
        status_res = requests.get("http://127.0.0.1:5000/status")
        logging.info(f"/status response: {status_res.json()}")

        msg_res = requests.post(
            "http://127.0.0.1:5000/message",
            json={"message": "Hello Echo"}
        )
        logging.info(f"/message response: {msg_res.json()}")
    except Exception as e:
        logging.error("Error testing Flask endpoints:\n" + traceback.format_exc())

# --- Main debug harness ---
if __name__ == "__main__":
    logging.info("=== FeralEcho Debug Test Harness ===")

    # Start Flask server in a thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Run tests
    test_autonomous_fetch()
    test_flask_message()

    logging.info("Debug test complete. Flask server is still running in background.")
    logging.info("Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Exiting debug test harness.")

