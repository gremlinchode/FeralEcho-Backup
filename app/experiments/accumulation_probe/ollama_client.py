"""Direct HTTP client for the local Ollama server (requests only). No production import, no RiverBrain, no council, no logging side effects."""
import json, time
import requests

def request_body(model, system, user, seed, options):
    return {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False, "options": {**options, "seed": seed}, "keep_alive": "10m"}

def chat(body, url, timeout):
    t0 = time.time()
    r = requests.post(url + "/api/chat", json=body, timeout=timeout)
    r.raise_for_status(); j = r.json()
    return {"text": j["message"]["content"], "done_reason": j.get("done_reason"), "eval_count": j.get("eval_count"),
            "prompt_eval_count": j.get("prompt_eval_count"), "total_duration_ns": j.get("total_duration"), "wall_s": round(time.time() - t0, 3)}

def model_info(url, model):
    """Exact model identity: name + digest (+ size/modified) from /api/tags, and Ollama version. GET only; no generation."""
    tags = requests.get(url + "/api/tags", timeout=20).json().get("models", [])
    m = [x for x in tags if x.get("name") == model]
    ver = requests.get(url + "/api/version", timeout=20).json().get("version")
    return {"model": model, "found": bool(m), "digest": m[0].get("digest") if m else None, "size": m[0].get("size") if m else None,
            "modified_at": m[0].get("modified_at") if m else None, "ollama_version": ver}
