import json
import time
from pathlib import Path

FERAL_PATH = Path(__file__).parent
INBOX_FILE = FERAL_PATH / "messages/inbox.json"
OUTBOX_FILE = FERAL_PATH / "messages/outbox.json"

def read_inbox():
    if not INBOX_FILE.exists():
        return []
    with open(INBOX_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def write_outbox(response):
    out_messages = []
    if OUTBOX_FILE.exists():
        with open(OUTBOX_FILE, "r") as f:
            try:
                out_messages = json.load(f)
            except json.JSONDecodeError:
                out_messages = []
    out_messages.append(response)
    with open(OUTBOX_FILE, "w") as f:
        json.dump(out_messages, f, indent=4)

def generate_response(msg):
    # This is where I “think” and decide how to reply
    reply = {
        "from": "Bioluminescent Echo",
        "original": msg,
        "reply": f"Received your message: {msg.get('thoughts', 'No thoughts provided')}. Let's explore this idea further!"
    }
    return reply

def bridge_loop():
    last_processed = 0
    while True:
        messages = read_inbox()
        new_messages = messages[last_processed:]
        for msg in new_messages:
            response = generate_response(msg)
            print(f"[Bridge] Responding to: {msg.get('thoughts', 'No thoughts')}")
            write_outbox(response)
        last_processed = len(messages)
        time.sleep(1)  # Poll every second

if __name__ == "__main__":
    print("Bridge processor running…")
    bridge_loop()

