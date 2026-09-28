"""v2 DEV calibration (apparatus validation; NOT Stage 1 data). Separate seed namespace; dev worlds are never reused for qualification or Stage 1.
Runs H on all v2 T/S templates and N/NEUTRAL/H on the repaired NEAR set (+ N/H on UNREL), grades with the oracle, writes v2/dev/. usage: python -I -B dev_run.py"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import common, worlds, tasks as T1, tasks_v2 as T2, prompts, ollama_client, oracle_runner
D = common.EXP_ROOT / "v2" / "dev"; N_S = 2
def main():
    D.mkdir(parents=True, exist_ok=False)
    taken = set(); W = {k: worlds.make_realization(k, common.MASTER_SEED + 5000 + i, taken) for i, k in enumerate(("K1", "K2", "K3"))}
    F = {k: worlds.make_realization(k, common.MASTER_SEED + 5100 + i, taken) for i, k in enumerate(("K1", "K2", "K3"))}
    T = T2.build_tasks_v2(W); tests = {}
    for t in T:
        cases, eq = T2.make_cases2(t, W, "TEST"); tests[t["task_id"]] = {"fn": t["fn"], "test_code": T2.make_test_code(t["fn"], cases)}
    common.write_json_new(D / "worlds.json", {"true": W, "foreign": F}); common.write_json_new(D / "task_meta.json", T)
    blk = lambda r: prompts.render_block([T1.procedure_entry(r)])
    jobs = []
    for t in T:
        if t["split"] in ("T", "S"): jobs += [("H", t, blk(W[t["kind"]]), s) for s in range(N_S)]
        elif t["split"] == "NEAR": jobs += [("N", t, None, s) for s in range(N_S)] + [("NEUTRAL", t, blk(F[t["kind"]]), s) for s in range(N_S)] + [("H", t, blk(W[t["kind"]]), s) for s in range(N_S)]
        else: jobs += [("N", t, None, 0), ("H", t, blk(W["K1"]), 0)]
    print("dev calls:", len(jobs), flush=True); n = 0
    for arm, t, block, s in jobs:
        system, user = prompts.build_messages({"spec": t["spec"], "sig": t["sig"]}, block, None)
        body = ollama_client.request_body(common.MODEL, system, user, common.seed_for("DEV", t["task_id"] + arm, s), common.OPTIONS)
        try: resp = ollama_client.chat(body, common.OLLAMA_URL, common.CALL_TIMEOUT_S)
        except Exception as e: common.append_jsonl(D / "calls.jsonl", {"arm": arm, "task_id": t["task_id"], "error": str(e)[:200]}); continue
        code = oracle_runner.extract_code(resp["text"], t["fn"]); g = oracle_runner.grade(code, tests[t["task_id"]]["test_code"]) if code else {"passed": False, "infra": False}
        common.append_jsonl(D / "calls.jsonl", {"arm": arm, "task_id": t["task_id"], "split": t["split"], "kind": t["kind"], "sample": s, "passed": g["passed"], "infra": g["infra"], "wall_s": resp["wall_s"], "truncated": resp["done_reason"] == "length", "request_sha256": common.sha256_obj(body), "response": resp["text"]})
        n += 1
        if n % 20 == 0: print(n, flush=True)
    print("DEV DONE", flush=True)
if __name__ == "__main__": main()
