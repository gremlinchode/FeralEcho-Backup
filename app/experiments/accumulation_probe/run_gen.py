"""Generic JAILED generation runner: reads <root>/inputs/requests.json ([{id, system, user, seed}]), writes a hash-chained <root>/calls.jsonl.
Imports only common + ollama_client. Used for constructor drafts and for gate/worker calls in v2 (same isolation as Stage 0 arms).
usage: python -I -B run_gen.py --root <root> --model <name>"""
import argparse, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import common, ollama_client
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", required=True); ap.add_argument("--model", required=True); a = ap.parse_args(); root = Path(a.root)
    reqs = common.read_json(root / "inputs" / "requests.json"); ledger = root / "calls.jsonl"; old = common.read_jsonl(ledger)
    done = {r["id"] for r in old if "response_text" in r}; prev = common.sha256_obj(old[-1]) if old else "GENESIS"; n = 0
    for q in reqs:
        if q["id"] in done: continue
        if (root / "ABORT").exists(): return 3
        body = ollama_client.request_body(a.model, q["system"], q["user"], q["seed"], q.get("options") or common.OPTIONS)
        row = {"id": q["id"], "seed": q["seed"], "request": body, "request_sha256": common.sha256_obj(body), "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        err = None
        for attempt in range(3):
            try: resp = ollama_client.chat(body, common.OLLAMA_URL, common.CALL_TIMEOUT_S); err = None; break
            except Exception as e: err = f"{type(e).__name__}: {e}"[:300]; time.sleep(5 * (attempt + 1))
        if err: row["error"] = err
        else: row.update(response_text=resp["text"], response_sha256=common.sha256_text(resp["text"]), done_reason=resp["done_reason"], eval_count=resp["eval_count"], wall_s=resp["wall_s"])
        row["prev_sha256"] = prev; prev = common.sha256_obj(row); common.append_jsonl(ledger, row); n += 1
    print(f"{root.name}: {n} calls", flush=True); return 0
if __name__ == "__main__": sys.exit(main())
