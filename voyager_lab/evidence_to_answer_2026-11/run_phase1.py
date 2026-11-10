#!/usr/bin/env python3
"""Phase One runner. Unhashed. Refuses to post unless the protocol seal holds.

A failed acceptance gate is a result. This process still exits 0 after the
posts and the scorer have finished. It does not retry a completed model reply.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import score
import transport

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_NAME = "results_phase1.jsonl"
META_NAME = "run_meta_phase1.json"
PHASE = "phase1"
PROMPT_FIELD = "phase1_prompt"
CONVERSATION_FIELD = "conversation_id_phase1"


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


def classify_reply(outcome):
    """Return infrastructure flag and reason. Do not read token text as the answer."""
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


def run_items(items, meta):
    posts_used = 0
    contingency_used = 0
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
            meta["posts_used"] = posts_used
            meta["contingency_used"] = contingency_used
            write_json(META_NAME, meta)
            progress(item_id, attempt, row["http_status"], infra, row["task_type"])
            if not infra:
                break
            if contingency_used >= score.CONTINGENCY_BUDGET:
                break
            contingency_used += 1
            attempt += 1
            meta["contingency_used"] = contingency_used
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
    results_path = os.path.join(HERE, RESULTS_NAME)
    if os.path.exists(results_path):
        print("results_exist", file=sys.stderr)
        return 2
    observed = transport.listener_observation()
    show = transport.ollama_show()
    meta = {
        "phase": PHASE,
        "started_at": transport.stamp(transport.utc_now()),
        "listener": {
            "port_open": observed.get("port_open"),
            "pid": observed.get("pid"),
            "command": observed.get("command"),
            "listener_pids": observed.get("listener_pids"),
            "ollama_model": observed.get("ollama_model"),
            "lsof_error": observed.get("lsof_error"),
        },
        "ollama_show": show,
        "posts_used": 0,
        "contingency_used": 0,
        "generation_budget": score.GENERATION_BUDGET,
        "contingency_budget": score.CONTINGENCY_BUDGET,
    }
    if not observed.get("port_open"):
        meta["infrastructure_failure"] = "port_down"
        meta["finished_at"] = transport.stamp(transport.utc_now())
        write_json(META_NAME, meta)
        print("port_down", file=sys.stderr)
        return 1
    write_json(META_NAME, meta)
    items = load_items()
    posts_used, contingency_used = run_items(items, meta)
    scorer = subprocess.run(
        [sys.executable, os.path.join(HERE, "score.py"), "--score-phase1"],
        cwd=HERE,
        capture_output=True,
        text=True,
    )
    meta["posts_used"] = posts_used
    meta["contingency_used"] = contingency_used
    meta["score_exit_code"] = scorer.returncode
    meta["score_stdout"] = scorer.stdout
    meta["score_stderr"] = scorer.stderr
    meta["finished_at"] = transport.stamp(transport.utc_now())
    write_json(META_NAME, meta)
    print(f"phase1_done posts={posts_used} score_exit={scorer.returncode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
