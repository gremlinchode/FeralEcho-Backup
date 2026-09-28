"""Stage 0 RUN orchestrator: verifies the freeze, then runs every arm's shards inside per-arm kernel jails in interleaved waves
(so time-of-day / production-load drift is spread across arms), then hands off to grade.py. usage: python -I -B stage0.py run|abort|status"""
import os, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import common, jail, ollama_client, freeze
from app.experiments.accumulation_probe.common import EXP_ROOT, ARMS, N_SHARDS, sha256_file
S0 = EXP_ROOT / "stage0"; RUN_ARM = str(Path(__file__).parent / "run_arm.py")

def verify_freeze():
    f = common.read_json(S0 / "FREEZE.json")
    assert (S0 / "FREEZE.sha256").read_text().split()[0] == sha256_file(S0 / "FREEZE.json"), "FREEZE.json changed"
    now = freeze.frozen_files(S0); bad = [k for k, v in f["artifact_sha256"].items() if now.get(k) != v]
    assert not bad, f"frozen artifacts changed: {bad[:5]}"
    pkg = Path(__file__).parent; badc = [k for k, v in f["code_sha256"].items() if sha256_file(pkg / k) != v]
    assert not badc, f"harness code changed since freeze: {badc}"
    return f

def log(msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"; print(line, flush=True)
    with open(S0 / "progress.log", "a") as fh: fh.write(line + "\n")

def cmd_run():
    f = verify_freeze(); mi = ollama_client.model_info(common.OLLAMA_URL, common.MODEL)
    assert mi["digest"] == f["model"]["digest"], f"model digest changed: {mi['digest']} != {f['model']['digest']}"
    log(f"RUN START model={mi['model']} digest={mi['digest'][:16]} head={freeze.sh(['git','rev-parse','HEAD']).strip()[:12]} server={freeze.server_facts().get('pid')}")
    for attempt in range(3):
        for shard in range(N_SHARDS):
            for arm in ARMS[shard % len(ARMS):] + ARMS[:shard % len(ARMS)]:
                root = S0 / "runs" / arm
                r = jail.run_jailed([RUN_ARM, "--root", str(root), "--arm", arm, "--shard", str(shard), "--of", str(N_SHARDS)], root, EXP_ROOT, 6 * 3600)
                log(f"pass={attempt} shard={shard} arm={arm} rc={r.returncode} {r.stdout.strip()[-80:]} {r.stderr.strip()[-160:]}")
                if r.returncode == 3: log("ABORTED by ABORT file"); return 3
        missing = 0
        for arm in ARMS:
            plan = common.read_json(S0 / "runs" / arm / "plan.json"); done = {x["call_id"] for x in common.read_jsonl(S0 / "runs" / arm / "calls.jsonl") if "response_text" in x}
            missing += sum(1 for c in plan["calls"] if c["call_id"] not in done)
        log(f"pass={attempt} complete; calls still missing: {missing}")
        if missing == 0: break
    mi2 = ollama_client.model_info(common.OLLAMA_URL, common.MODEL); log(f"RUN END digest_unchanged={mi2['digest'] == f['model']['digest']} server={freeze.server_facts().get('pid')}")
    return 0

def cmd_status():
    for arm in ARMS:
        plan = common.read_json(S0 / "runs" / arm / "plan.json"); rows = common.read_jsonl(S0 / "runs" / arm / "calls.jsonl")
        done = {x["call_id"] for x in rows if "response_text" in x}; errs = sum(1 for x in rows if "error" in x)
        lat = [x["wall_s"] for x in rows if "wall_s" in x]
        print(f"{arm:9s} {len(done):4d}/{len(plan['calls']):4d} errors={errs} mean_wall_s={sum(lat)/len(lat) if lat else 0:.1f}")

def cmd_abort():
    for arm in ARMS: (S0 / "runs" / arm / "ABORT").write_text("abort\n")
    print("ABORT flags written")

if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "status"
    sys.exit({"run": cmd_run, "status": cmd_status, "abort": cmd_abort}[c]() or 0)
