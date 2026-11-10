"""Isolated reasoning-reliability pilot. Local Ollama only. No production imports.

Usage:
  python3 harness.py --self-test
  python3 harness.py --run
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROBLEMS = ROOT / "problems.json"
PROTOCOL = ROOT / "protocol.json"
SUMMARY = ROOT / "summary.json"
BUDGET = ROOT / "budget.json"
RAW = ROOT / "raw"
GRADER = ROOT / "grader.py"

sys.path.insert(0, str(ROOT))
import grader  # noqa: E402


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load() -> tuple[dict, dict]:
    return json.loads(PROTOCOL.read_text()), json.loads(PROBLEMS.read_text())


def chat(protocol: dict, messages: list, budget: dict) -> dict:
    if budget["used"] >= protocol["max_generation_requests"]:
        raise SystemExit("BUDGET_EXHAUSTED before send")
    budget["used"] += 1
    budget["events"].append({"n": budget["used"], "at": now(), "phase": "send"})
    BUDGET.write_text(json.dumps(budget, indent=2))
    payload = {
        "model": protocol["model"],
        "messages": messages,
        "stream": False,
        "options": protocol["options"],
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        protocol["ollama_chat"],
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=protocol["timeout_s"]) as resp:
            body = resp.read()
            status = resp.status
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", "replace")
        return {
            "http_status": exc.code,
            "error": err[:2000],
            "content": "",
            "done_reason": None,
            "eval_count": None,
            "prompt_eval_count": None,
            "total_duration": None,
            "model_field": None,
        }
    except Exception as exc:  # noqa: BLE001 — count the failure and continue
        return {
            "http_status": None,
            "error": f"{type(exc).__name__}: {exc}",
            "content": "",
            "done_reason": None,
            "eval_count": None,
            "prompt_eval_count": None,
            "total_duration": None,
            "model_field": None,
        }
    parsed = json.loads(body)
    message = parsed.get("message") if isinstance(parsed, dict) else None
    content = ""
    if isinstance(message, dict):
        content = message.get("content") or ""
    return {
        "http_status": status,
        "error": None,
        "content": content,
        "done_reason": parsed.get("done_reason") if isinstance(parsed, dict) else None,
        "eval_count": parsed.get("eval_count") if isinstance(parsed, dict) else None,
        "prompt_eval_count": parsed.get("prompt_eval_count") if isinstance(parsed, dict) else None,
        "total_duration": parsed.get("total_duration") if isinstance(parsed, dict) else None,
        "model_field": parsed.get("model") if isinstance(parsed, dict) else None,
        "raw_response": parsed,
    }


def base_messages(protocol: dict, prompt: str) -> list:
    return [
        {"role": "system", "content": protocol["system_prompt"]},
        {"role": "user", "content": prompt},
    ]


def aggregate(rows: list[dict]) -> dict:
    by_dim: dict[str, dict] = {}
    for row in rows:
        dim = row["dimension"]
        bucket = by_dim.setdefault(dim, {"pass": 0, "n": 0})
        bucket["n"] += 1
        bucket["pass"] += int(row["pass"])
    full = sum(1 for b in by_dim.values() if b["pass"] == 2 and b["n"] == 2)
    return {
        "passed": sum(int(r["pass"]) for r in rows),
        "n": len(rows),
        "by_dimension": by_dim,
        "dimensions_at_2_of_2": full,
        "fabricated_items": [r["item_id"] for r in rows if r["fabricated"]],
    }


def decide(protocol: dict, baseline: dict, candidate: dict, completed: bool) -> str:
    if not completed:
        return "EXPERIMENT NOT COMPLETED"
    t = protocol["thresholds"]
    margin = candidate["passed"] - baseline["passed"]
    ok = (
        candidate["passed"] >= t["candidate_min"]
        and margin >= t["candidate_margin_over_baseline"]
        and candidate["dimensions_at_2_of_2"] >= t["dimensions_at_2_of_2"]
        and not candidate["fabricated_items"]
    )
    return "DEMONSTRATED IMPROVEMENT" if ok else "NOT DEMONSTRATED"


def run() -> None:
    if SUMMARY.exists() or BUDGET.exists() or any(RAW.glob("*.json")):
        raise SystemExit("REFUSING: prior run artifacts exist. Do not rerun.")
    grader._self_test()
    protocol, problems = load()
    # Reject leaked grader phrases before any artifact or request exists.
    review = protocol["review_turn"]
    for banned in ("3/4", "S2", "free verse", "2.0 kg", "does not support"):
        if banned in review:
            raise SystemExit(f"REVIEW_LEAK {banned}")
    RAW.mkdir(parents=True)
    budget = {"used": 0, "max": protocol["max_generation_requests"], "events": [], "started_at": now()}
    BUDGET.write_text(json.dumps(budget, indent=2))
    freeze = {
        "protocol_sha256": sha256_file(PROTOCOL),
        "problems_sha256": sha256_file(PROBLEMS),
        "grader_sha256": sha256_file(GRADER),
        "harness_sha256": sha256_file(Path(__file__)),
        "frozen_at": now(),
    }
    (ROOT / "freeze.json").write_text(json.dumps(freeze, indent=2))

    records = []
    for item in problems["items"]:
        messages = base_messages(protocol, item["prompt"])
        result = chat(protocol, messages, budget)
        record = {
            "item_id": item["id"],
            "dimension": item["dimension"],
            "arm": "baseline",
            "prompt": item["prompt"],
            "messages_sent": messages,
            **{k: v for k, v in result.items() if k != "raw_response"},
            "finished_at": now(),
        }
        (RAW / f"{item['id']}_baseline.json").write_text(json.dumps(record, indent=2))
        records.append(record)
        print(f"baseline {item['id']} status={result['http_status']} eval={result['eval_count']}", flush=True)

    stage1 = {}
    for item in problems["items"]:
        messages = base_messages(protocol, item["prompt"])
        result = chat(protocol, messages, budget)
        record = {
            "item_id": item["id"],
            "dimension": item["dimension"],
            "arm": "stage1",
            "prompt": item["prompt"],
            "messages_sent": messages,
            **{k: v for k, v in result.items() if k != "raw_response"},
            "finished_at": now(),
        }
        (RAW / f"{item['id']}_stage1.json").write_text(json.dumps(record, indent=2))
        stage1[item["id"]] = record
        print(f"stage1 {item['id']} status={result['http_status']} eval={result['eval_count']}", flush=True)

    stage2_rows = []
    for item in problems["items"]:
        first = stage1[item["id"]]
        if first.get("error") or not (first.get("content") or "").strip():
            record = {
                "item_id": item["id"],
                "dimension": item["dimension"],
                "arm": "stage2",
                "skipped": True,
                "reason": "stage1_failed",
                "content": "",
                "http_status": None,
                "finished_at": now(),
            }
            (RAW / f"{item['id']}_stage2.json").write_text(json.dumps(record, indent=2))
            stage2_rows.append(record)
            print(f"stage2 {item['id']} SKIPPED", flush=True)
            continue
        messages = base_messages(protocol, item["prompt"])
        messages.append({"role": "assistant", "content": first["content"]})
        messages.append({"role": "user", "content": protocol["review_turn"]})
        result = chat(protocol, messages, budget)
        record = {
            "item_id": item["id"],
            "dimension": item["dimension"],
            "arm": "stage2",
            "skipped": False,
            "prompt": item["prompt"],
            "messages_sent": messages,
            **{k: v for k, v in result.items() if k != "raw_response"},
            "finished_at": now(),
        }
        (RAW / f"{item['id']}_stage2.json").write_text(json.dumps(record, indent=2))
        stage2_rows.append(record)
        print(f"stage2 {item['id']} status={result['http_status']} eval={result['eval_count']}", flush=True)

    baseline_scores = [grader.score_text(r["item_id"], r.get("content") or "") for r in records]
    candidate_scores = [grader.score_text(r["item_id"], r.get("content") or "") for r in stage2_rows]
    # Stage 1 is recorded, not graded into the candidate total.
    bsum = aggregate(baseline_scores)
    csum = aggregate(candidate_scores)
    completed = (
        budget["used"] <= protocol["max_generation_requests"]
        and all(r.get("error") is None and r.get("http_status") == 200 for r in records)
        and all((not r.get("skipped")) and r.get("error") is None and r.get("http_status") == 200 for r in stage2_rows)
    )
    outcome = decide(protocol, bsum, csum, completed)
    summary = {
        "outcome": outcome,
        "completed_comparison": completed,
        "model_generations": budget["used"],
        "budget_max": protocol["max_generation_requests"],
        "baseline": bsum,
        "candidate": csum,
        "margin": csum["passed"] - bsum["passed"],
        "baseline_scores": baseline_scores,
        "candidate_scores": candidate_scores,
        "freeze": freeze,
        "finished_at": now(),
        "model_fields": sorted({r.get("model_field") for r in records + stage2_rows if r.get("model_field")}),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2))
    budget["finished_at"] = now()
    BUDGET.write_text(json.dumps(budget, indent=2))
    write_blind(problems, records, stage2_rows)
    print(f"OUTCOME {outcome} baseline={bsum['passed']}/10 candidate={csum['passed']}/10 calls={budget['used']}", flush=True)


def write_blind(problems: dict, baselines: list, stage2: list) -> None:
    """Anonymize outputs. The map is stored apart from the package."""
    import random

    rng = random.Random(0)
    rows = []
    for rec, arm in [(r, "B") for r in baselines] + [(r, "C") for r in stage2]:
        rows.append({"arm_code": arm, "item_id": rec["item_id"], "text": rec.get("content") or ""})
    order = list(range(len(rows)))
    rng.shuffle(order)
    package = []
    key = []
    for n, idx in enumerate(order, start=1):
        anon = f"R{n:02d}"
        package.append({"id": anon, "text": rows[idx]["text"]})
        key.append({"id": anon, "item_id": rows[idx]["item_id"], "arm_code": rows[idx]["arm_code"]})
    (ROOT / "blind_package.json").write_text(json.dumps({"items": package}, indent=2))
    (ROOT / "blind_key.json").write_text(json.dumps({"map": key, "note": "B baseline, C candidate stage 2. Not sent to the model."}, indent=2))


def main() -> None:
    if "--self-test" in sys.argv:
        grader._self_test()
        return
    if "--run" in sys.argv:
        run()
        return
    raise SystemExit("usage: harness.py --self-test | --run")


if __name__ == "__main__":
    main()
