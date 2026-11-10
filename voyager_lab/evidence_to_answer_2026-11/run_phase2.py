#!/usr/bin/env python3
"""Phase Two runner. Unhashed. Posts only after the Phase One gate passes.

Does not open the answer key. Sleeps until the sealed delay deadline, then
asks the delayed questions in new conversations. A storage or retrieval
result is never inferred from the answer.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import score
import transport

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_NAME = "results_phase2.jsonl"
META_NAME = "run_meta_phase2.json"
PHASE1_RESULTS = "results_phase1.jsonl"
PHASE1_META = "run_meta_phase1.json"
PHASE = "phase2"
PROMPT_FIELD = "phase2_prompt"
CONVERSATION_FIELD = "conversation_id_phase2"


def seal_holds():
    ok, reason = score.verify_protocol_seal(HERE)
    readonly = score.sealed_files_readonly(HERE)
    sha_writable = os.access(os.path.join(HERE, "PROTOCOL.sha256"), os.W_OK)
    return ok and readonly and not sha_writable, reason, sha_writable


def write_json(name, payload):
    path = os.path.join(HERE, name)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())


def append_jsonl(name, row):
    path = os.path.join(HERE, name)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_items():
    with open(os.path.join(HERE, "items.json"), encoding="utf-8") as handle:
        document = json.load(handle)
    items = document.get("items")
    if not isinstance(items, list) or len(items) != score.PHASE1_REQUIRED:
        raise SystemExit("items_shape")
    return items


def phase1_finished_ats():
    path = os.path.join(HERE, PHASE1_RESULTS)
    stamps = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict) and row.get("phase") == "phase1":
                stamps.append(row.get("finished_at"))
    return stamps


def prior_budget():
    path = os.path.join(HERE, PHASE1_META)
    with open(path, encoding="utf-8") as handle:
        meta = json.load(handle)
    posts = meta.get("posts_used")
    contingency = meta.get("contingency_used")
    if not isinstance(posts, int) or not isinstance(contingency, int):
        raise SystemExit("phase1_budget_unknown")
    return posts, contingency


def classify_reply(outcome):
    summary = outcome["events_summary"]
    if outcome["infrastructure"]:
        return True, outcome["infrastructure_reason"]
    status = outcome["http_status"]
    if isinstance(status, int) and status >= 400:
        return True, "http_error"
    if summary["done_present"] is not True or not isinstance(summary["done_text"], str):
        return True, "missing_done"
    if score.is_exact_server_error(summary["done_text"]):
        return True, "server_error"
    return False, None


def build_row(item_id, attempt, conversation_id, prompt, outcome, infra, reason):
    summary = outcome["events_summary"]
    row = {
        "phase": PHASE,
        "item_id": item_id,
        "attempt": attempt,
        "conversation_id": conversation_id,
        "started_at": transport.stamp(outcome["started_at"]),
        "finished_at": transport.stamp(outcome["finished_at"]),
        "http_status": outcome["http_status"],
        "infrastructure": infra,
        "infrastructure_reason": reason,
        "done_present": summary["done_present"],
        "done_text": summary["done_text"],
        "token_text": summary["token_text"],
        "texts_diverge": summary["texts_diverge"],
        "task_type": summary["task_type"],
        "trace_id": summary["trace_id"],
        "memory_save_user": summary["memory_save_user"],
        "memory_save_echo": summary["memory_save_echo"],
        "done_count": summary["done_count"],
        "memory_save_count": summary["memory_save_count"],
        "prompt_sha256": score.prompt_sha256(prompt),
        "counts_toward_budget": True,
        "prompt": prompt,
    }
    if outcome.get("timeout_scope"):
        row["timeout_scope"] = outcome["timeout_scope"]
    if "sse_unparsed" in summary:
        row["sse_unparsed"] = summary["sse_unparsed"]
    return row


def progress(item_id, attempt, http_status, infra, task_type):
    print(
        f"item_id={item_id} attempt={attempt} http={http_status} infra={infra} task_type={task_type}",
        file=sys.stderr,
    )


def wait_until(deadline):
    while True:
        remaining = (deadline - transport.utc_now()).total_seconds()
        if remaining <= 0:
            print("phase2_wait remaining_s=0", file=sys.stderr)
            return
        print(f"phase2_wait remaining_s={int(remaining)}", file=sys.stderr)
        time.sleep(min(remaining, 60.0))


def run_items(items, meta, posts_used, contingency_used):
    for item in items:
        item_id = item["id"]
        prompt = item[PROMPT_FIELD]
        conversation_id = item[CONVERSATION_FIELD]
        attempt = 1
        while True:
            if posts_used >= score.GENERATION_BUDGET:
                meta["budget_exhausted"] = True
                write_json(META_NAME, meta)
                return posts_used, contingency_used
            outcome = transport.post_chat(conversation_id, prompt, transport.TIMEOUT_S)
            posts_used += 1
            infra, reason = classify_reply(outcome)
            row = build_row(item_id, attempt, conversation_id, prompt, outcome, infra, reason)
            append_jsonl(RESULTS_NAME, row)
            meta["posts_used_total"] = posts_used
            meta["contingency_used_total"] = contingency_used
            write_json(META_NAME, meta)
            progress(item_id, attempt, row["http_status"], infra, row["task_type"])
            if not infra:
                break
            if contingency_used >= score.CONTINGENCY_BUDGET:
                break
            contingency_used += 1
            attempt += 1
            meta["contingency_used_total"] = contingency_used
            write_json(META_NAME, meta)
    return posts_used, contingency_used


def main(argv):
    holds, reason, sha_writable = seal_holds()
    if "--check-seal-only" in argv:
        if holds:
            print("check_seal_only=ok")
            return 0
        print(
            f"check_seal_only=fail reason={reason} sha_writable={sha_writable}",
            file=sys.stderr,
        )
        return 1
    if not holds:
        print(f"seal_refused reason={reason} sha_writable={sha_writable}", file=sys.stderr)
        return 2
    if os.path.exists(os.path.join(HERE, RESULTS_NAME)):
        print("results_exist", file=sys.stderr)
        return 2
    if not os.path.isfile(os.path.join(HERE, PHASE1_RESULTS)):
        print("phase2_refused=no_phase1_results", file=sys.stderr)
        return 1
    gate = subprocess.run(
        [sys.executable, os.path.join(HERE, "score.py"), "--score-phase1"],
        cwd=HERE,
        capture_output=True,
        text=True,
    )
    if gate.returncode != 0:
        meta = {
            "phase": PHASE,
            "refused": "gate",
            "score_exit_code": gate.returncode,
            "score_stdout": gate.stdout,
            "score_stderr": gate.stderr,
            "posts_used_total": None,
            "started_at": transport.stamp(transport.utc_now()),
            "finished_at": transport.stamp(transport.utc_now()),
        }
        write_json(META_NAME, meta)
        print(f"phase2_refused=gate score_exit={gate.returncode}", file=sys.stderr)
        return 1
    posts_used, contingency_used = prior_budget()
    if posts_used >= score.GENERATION_BUDGET or contingency_used > score.CONTINGENCY_BUDGET:
        print("phase2_refused=budget", file=sys.stderr)
        return 1
    observed = transport.listener_observation()
    meta = {
        "phase": PHASE,
        "started_at": transport.stamp(transport.utc_now()),
        "gate_stdout": gate.stdout,
        "listener": {
            "port_open": observed.get("port_open"),
            "pid": observed.get("pid"),
            "command": observed.get("command"),
            "listener_pids": observed.get("listener_pids"),
            "ollama_model": observed.get("ollama_model"),
            "lsof_error": observed.get("lsof_error"),
        },
        "posts_used_at_start": posts_used,
        "contingency_used_at_start": contingency_used,
        "posts_used_total": posts_used,
        "contingency_used_total": contingency_used,
    }
    if not observed.get("port_open"):
        meta["infrastructure_failure"] = "port_down"
        meta["finished_at"] = transport.stamp(transport.utc_now())
        write_json(META_NAME, meta)
        print("port_down", file=sys.stderr)
        return 1
    deadline = score.delay_deadline(phase1_finished_ats())
    meta["delay_deadline"] = transport.stamp(deadline)
    write_json(META_NAME, meta)
    wait_until(deadline)
    items = load_items()
    posts_used, contingency_used = run_items(items, meta, posts_used, contingency_used)
    attribute = subprocess.run(
        [sys.executable, os.path.join(HERE, "score.py"), "--attribute"],
        cwd=HERE,
        capture_output=True,
        text=True,
    )
    meta["posts_used_total"] = posts_used
    meta["contingency_used_total"] = contingency_used
    meta["attribute_exit_code"] = attribute.returncode
    meta["attribute_stdout"] = attribute.stdout
    meta["attribute_stderr"] = attribute.stderr
    meta["finished_at"] = transport.stamp(transport.utc_now())
    write_json(META_NAME, meta)
    print(f"phase2_done posts_total={posts_used} attribute_exit={attribute.returncode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
