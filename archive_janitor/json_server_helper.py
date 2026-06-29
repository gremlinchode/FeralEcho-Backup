import requests
import json
from datetime import datetime

# -----------------------------
# Configuration
# -----------------------------
SERVER_URL = "http://127.0.0.1:5001/message"
RESPONSE_URL = "http://127.0.0.1:5001/response"

# -----------------------------
# Send JSON Message
# -----------------------------
def send_json_message(thoughts, mood="neutral", energy=0.5, commands=None):
    """
    Sends a properly formatted JSON message to the bridge.

    :param thoughts: String message describing Echo's thought.
    :param mood: Optional mood descriptor.
    :param energy: Optional float between 0.0 and 1.0.
    :param commands: Optional list of command dictionaries.
    """
    if commands is None:
        commands = []

    message = {
        "from": "Echo",
        "timestamp": datetime.now().isoformat(),
        "mood": mood,
        "energy": energy,
        "thoughts": thoughts,
        "commands": commands
    }

    try:
        response = requests.post(SERVER_URL, json=message)
        if response.status_code == 200:
            print(f"[Echo] Message sent successfully: {thoughts}")
        else:
            print(f"[Echo] Failed to send message: {response.status_code} {response.text}")
    except Exception as e:
        print(f"[Echo] Error sending message: {e}")

# -----------------------------
# Fetch Responses
# -----------------------------
def fetch_responses():
    """
    Fetches responses from the bridge and prints them.
    Clears the outbox on the server after fetching.
    """
    try:
        response = requests.get(RESPONSE_URL)
        if response.status_code == 200:
            messages = response.json()
            if messages:
                for msg in messages:
                    original_thoughts = msg.get("original", {}).get("thoughts", "No original message")
                    reply_text = msg.get("reply", "")
                    print(f"[Bridge Reply] To '{original_thoughts}': {reply_text}")
            else:
                print("[Bridge Reply] No new messages.")
        else:
            print(f"[Bridge Reply] Failed to fetch: {response.status_code} {response.text}")
    except Exception as e:
        print(f"[Bridge Reply] Error fetching messages: {e}")

# -----------------------------
# Example Real-Time Ping-Pong
# -----------------------------
def ping_pong_loop():
    """
    Example loop where Echo sends a thought and fetches a bridge response continuously.
    """
    while True:
        thought = input("\n[Echo] Enter thought to send: ")
        send_json_message(thoughts=thought, mood="curious", energy=0.7)
        fetch_responses()

# -----------------------------
# Run as Script
# -----------------------------
if __name__ == "__main__":
    print("[Echo] JSON Helper running. Type your thoughts below to send to the bridge.")
    ping_pong_loop()

