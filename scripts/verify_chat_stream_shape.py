"""
One-time, standalone diagnostic for the Track B /api/chat migration
(app/ollama_handler.py). Not wired into any import graph the app uses at
runtime — safe to delete after use. Bypasses ollama_handler.py entirely;
talks straight to the Ollama server to observe the real streaming shape of
/api/chat before any production code depends on assumptions about it.

Usage: python scripts/verify_chat_stream_shape.py
"""
import json
import requests

CHAT_URL = "http://localhost:11434/api/chat"


def run(model: str, prompt: str, label: str) -> None:
    print(f"\n{'=' * 70}\n{label} (model={model})\n{'=' * 70}")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
    }
    content_parts = []
    thinking_parts = []
    line_count = 0
    keys_seen = set()
    message_keys_seen = set()

    with requests.post(CHAT_URL, json=payload, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            line_count += 1
            decoded = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line

            if line_count <= 5 or True:  # print every line verbatim, per the plan
                print(f"RAW[{line_count}]: {decoded}")

            data = json.loads(decoded)
            keys_seen.update(data.keys())
            msg = data.get("message", {})
            if isinstance(msg, dict):
                message_keys_seen.update(msg.keys())
                if msg.get("content"):
                    content_parts.append(msg["content"])
                if msg.get("thinking"):
                    thinking_parts.append(msg["thinking"])

            if data.get("done"):
                print(f"\nFINAL LINE (done=true) keys: {list(data.keys())}")
                for k in ("total_duration", "eval_count", "prompt_eval_count", "done_reason"):
                    if k in data:
                        print(f"  {k}: {data[k]}")
                break

    print(f"\n--- Summary for {label} ---")
    print(f"Total lines: {line_count}")
    print(f"Top-level keys seen across stream: {sorted(keys_seen)}")
    print(f"message.* keys seen across stream: {sorted(message_keys_seen)}")
    print(f"Assembled content length: {len(''.join(content_parts))} chars, {len(content_parts)} chunks")
    print(f"Assembled thinking length: {len(''.join(thinking_parts))} chars, {len(thinking_parts)} chunks")
    if content_parts:
        print(f"Content sample (first 200 chars): {''.join(content_parts)[:200]!r}")
    if thinking_parts:
        print(f"Thinking sample (first 200 chars): {''.join(thinking_parts)[:200]!r}")
    if not thinking_parts and content_parts:
        joined = "".join(content_parts)
        if "<think>" in joined or "</think>" in joined:
            print("NOTE: no separate 'thinking' field, but <think> tags found INLINE in content.")


if __name__ == "__main__":
    import subprocess
    version = subprocess.run(["ollama", "--version"], capture_output=True, text=True).stdout.strip()
    print(f"Ollama version: {version}")

    # Run twice to check consistency, per the plan.
    for i in range(2):
        run("deepseek-r1:7b", "What is 2+2? Think it through.", f"DeepSeek-R1 (thinking model) run {i+1}")

    run("llama3.2:3b", "What is 2+2?", "llama3.2:3b (non-thinking model) sanity check")
