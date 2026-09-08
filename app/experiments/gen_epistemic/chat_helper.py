"""Temporary test tooling for the generation-time epistemic revision mission
(2026-09-08). Calls the real, live /chat/stream endpoint and returns the
full assembled response text. Not part of production; safe to delete after
this mission."""
import json
import sys
import uuid
import urllib.request


def chat(message: str, mode: str = "full", conversation_id: str = None, timeout: int = 420) -> str:
    conversation_id = conversation_id or str(uuid.uuid4())
    payload = json.dumps({
        "conversation_id": conversation_id,
        "message": message,
        "mode": mode,
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/chat/stream",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    full_text = ""
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for line in resp:
            line = line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data: "):
                continue
            try:
                evt = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            if evt.get("type") == "chunk":
                full_text += evt.get("text", "")
            elif evt.get("type") == "done":
                full_text = evt.get("text", full_text)
            elif evt.get("type") == "error":
                full_text += f"\n[STREAM ERROR: {evt}]"
    return conversation_id, full_text


if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "What is RiverBrain, and is it currently part of your architecture?"
    cid, text = chat(msg)
    print(f"conversation_id={cid}")
    print("---")
    print(text)
