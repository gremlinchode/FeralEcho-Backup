"""One arm's generation process. Runs INSIDE a kernel jail (see stage0.py): it can read only its own root, write only its own root,
and never sees hidden tests, reference solutions or other arms. Imports: stdlib + requests + common/prompts/ollama_client ONLY.
usage: python -I run_arm.py --root <arm_root> --arm <ARM> --shard <i> --of <n>"""
import argparse, hashlib, json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import common, prompts, ollama_client

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", required=True); ap.add_argument("--arm", required=True)
    ap.add_argument("--shard", type=int, required=True); ap.add_argument("--of", type=int, required=True)
    a = ap.parse_args(); root = Path(a.root)
    plan = common.read_json(root / "plan.json"); pub = {t["task_id"]: t for t in common.read_json(root / "inputs" / "public_tasks.json")}
    ledger = root / "calls.jsonl"
    old = common.read_jsonl(ledger)
    done = {r["call_id"] for r in old if "response_text" in r}
    prev = common.sha256_obj(old[-1]) if old else "GENESIS"      # hash chain: any later edit/deletion/substitution of a row is detectable
    n = 0
    for c in plan["calls"]:
        if c["shard"] != a.shard or c["call_id"] in done: continue
        if (root / "ABORT").exists(): print("ABORT file present", flush=True); return 3
        system, user = prompts.build_messages(pub[c["task_id"]], c.get("carrier_block"), c.get("inline_examples"))
        body = ollama_client.request_body(plan["model"], system, user, c["seed"], plan["options"])
        row = {"call_id": c["call_id"], "arm": a.arm, "task_id": c["task_id"], "variant": c["variant"], "replicate": c["replicate"], "sample": c["sample"],
               "seed": c["seed"], "probe": c.get("probe", False), "request": body, "request_sha256": common.sha256_obj(body), "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        err = None
        for attempt in range(3):
            try:
                resp = ollama_client.chat(body, common.OLLAMA_URL, common.CALL_TIMEOUT_S); err = None; break
            except Exception as e:
                err = f"{type(e).__name__}: {e}"[:300]; time.sleep(5 * (attempt + 1))
        if err: row["error"] = err
        else:
            row.update(response_text=resp["text"], response_sha256=common.sha256_text(resp["text"]), done_reason=resp["done_reason"], eval_count=resp["eval_count"],
                       prompt_eval_count=resp["prompt_eval_count"], wall_s=resp["wall_s"])
        row["prev_sha256"] = prev; prev = common.sha256_obj(row)
        common.append_jsonl(ledger, row); n += 1
    print(f"arm={a.arm} shard={a.shard}: {n} calls", flush=True); return 0

if __name__ == "__main__": sys.exit(main())
