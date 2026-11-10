#!/usr/bin/env python3
"""Frozen scorer for the November 2026 evidence-to-answer experiment.

This module does not open the answer key, the protocol, or production
memory at import time. --self-test does not open them either.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

PHASE1_REQUIRED = 10
PHASE1_ACCEPT = 8
DELAY_SECONDS = 1860
GENERATION_BUDGET = 22
CONTINGENCY_BUDGET = 2

SEAL_ORDER = [
    "answer_key.json",
    "items.json",
    "preflight.py",
    "PROTOCOL.md",
    "score.py",
]
SEAL_ORDER_PHRASE = "answer_key.json, items.json, preflight.py, PROTOCOL.md, score.py"

SERVER_ERROR_SENTENCE = "Error: could not generate a response."
INFRA_REASONS = {"timeout", "connection", "http_error"}
MEMORY_SAVE_OUTCOMES = {"accepted", "rejected", "failed", "unknown"}

MEMORY_META_PATH = "/Users/richietate/Desktop/FeralEcho/memory/memory_meta.json"
PROVENANCE_PATH = "/Users/richietate/Desktop/FeralEcho/memory/retrieval_provenance.jsonl"


def prompt_sha256(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:12]


def is_exact_server_error(text) -> bool:
    return isinstance(text, str) and text.strip() == SERVER_ERROR_SENTENCE


def answers_match(done_text, key) -> bool:
    """Exact match after strip and at most one trailing period.

    The period is removed only when the key does not already end with one,
    and only when the stripped reply ends with exactly one period.
    The server-error sentence is never a correct answer.
    """
    if not isinstance(done_text, str) or not isinstance(key, str):
        return False
    if is_exact_server_error(done_text):
        return False
    text = done_text.strip()
    if not key.endswith(".") and text.endswith(".") and not text.endswith(".."):
        text = text[:-1]
    return text == key


def normalize_memory_save(value):
    if isinstance(value, str) and value in MEMORY_SAVE_OUTCOMES:
        return value
    return "unknown"


def attempt_is_infrastructure(row) -> bool:
    if not isinstance(row, dict):
        return True
    if row.get("infrastructure") is True:
        return True
    if row.get("infrastructure_reason") in INFRA_REASONS:
        return True
    status = row.get("http_status")
    if isinstance(status, int) and status >= 400:
        return True
    if row.get("done_present") is not True:
        return True
    if not isinstance(row.get("done_text"), str):
        return True
    if is_exact_server_error(row.get("done_text")):
        return True
    return False


def row_is_completed_model_reply(row) -> bool:
    return (
        isinstance(row, dict)
        and not attempt_is_infrastructure(row)
        and row.get("done_present") is True
        and isinstance(row.get("done_text"), str)
    )


def phase1_gate(completed: int, correct: int) -> bool:
    return completed == PHASE1_REQUIRED and correct >= PHASE1_ACCEPT


def parse_ts(value):
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def storage_lower_bound(started_ats):
    if not started_ats:
        return None
    parsed = []
    for value in started_ats:
        stamp = parse_ts(value)
        if stamp is None:
            return None
        parsed.append(stamp)
    return min(parsed)


def delay_deadline(finished_ats):
    if not finished_ats:
        raise ValueError("empty")
    parsed = []
    for value in finished_ats:
        stamp = parse_ts(value)
        if stamp is None:
            raise ValueError("naive_or_invalid")
        parsed.append(stamp)
    return max(parsed) + timedelta(seconds=DELAY_SECONDS)


def flatten_memory_row(row):
    if not isinstance(row, dict):
        return None
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else None
    text = row.get("text")
    if not isinstance(text, str):
        return None
    if meta is not None:
        role = meta.get("role", row.get("role"))
        source = meta.get("memory_source", row.get("memory_source"))
        timestamp = meta.get("timestamp", row.get("timestamp"))
    else:
        role = row.get("role")
        source = row.get("memory_source")
        timestamp = row.get("timestamp")
    return {
        "text": text,
        "role": role,
        "memory_source": source,
        "timestamp": timestamp,
    }


def row_qualifies(flat, fact_sentence, lower_bound) -> bool:
    if not isinstance(flat, dict) or lower_bound is None:
        return False
    if flat.get("memory_source") != "user_conversation":
        return False
    if flat.get("role") != "user":
        return False
    text = flat.get("text")
    if not isinstance(text, str) or fact_sentence not in text:
        return False
    stamp = parse_ts(flat.get("timestamp"))
    if stamp is None:
        return False
    return stamp >= lower_bound


def _as_save_list(memory_saves):
    if memory_saves is None:
        return []
    if isinstance(memory_saves, (list, tuple)):
        return list(memory_saves)
    return [memory_saves]


def assess_storage(rows, fact_sentence, started_ats, memory_saves, scan_complete):
    lower = storage_lower_bound(started_ats)
    if not scan_complete or lower is None:
        return {"stored": "Unknown", "contradiction": False, "qualifying": []}
    qualifying = []
    for row in rows or []:
        flat = flatten_memory_row(row)
        if row_qualifies(flat, fact_sentence, lower):
            qualifying.append(
                {
                    "text_hash": text_hash(flat["text"]),
                    "role": flat["role"],
                    "source": flat["memory_source"],
                    "timestamp": flat["timestamp"],
                    "match": True,
                }
            )
    saves = [normalize_memory_save(value) for value in _as_save_list(memory_saves)]
    if qualifying:
        contradiction = any(value in ("rejected", "failed") for value in saves)
        return {
            "stored": "Yes",
            "contradiction": contradiction,
            "qualifying": qualifying,
        }
    if saves and all(value in ("rejected", "failed") for value in saves):
        return {"stored": "No", "contradiction": False, "qualifying": []}
    return {"stored": "Unknown", "contradiction": False, "qualifying": []}


def accepted_fact_hashes(
    phase1_prompts,
    frozen_prompt,
    phase1_done_rows,
    qualifying_user_texts,
    fact_sentence,
):
    found = []
    for prompt in phase1_prompts or []:
        if isinstance(prompt, str):
            found.append(text_hash(prompt))
    if isinstance(frozen_prompt, str):
        found.append(text_hash(frozen_prompt))
    for row in phase1_done_rows or []:
        if not isinstance(row, dict):
            continue
        done_text = row.get("done_text")
        if (
            row.get("done_present") is True
            and isinstance(done_text, str)
            and isinstance(fact_sentence, str)
            and fact_sentence in done_text
        ):
            found.append(text_hash(done_text))
    for text in qualifying_user_texts or []:
        if isinstance(text, str):
            found.append(text_hash(text))
    return found


def read_provenance(path):
    if not os.path.exists(path):
        return "missing", [], 0
    try:
        with open(path, encoding="utf-8") as handle:
            raw = handle.read()
    except OSError:
        return "unreadable", [], 0
    records = []
    bad = 0
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            bad += 1
            continue
        if isinstance(obj, dict):
            records.append(obj)
        else:
            bad += 1
    return "ok", records, bad


def records_for_trace(records, trace_id):
    hits = [row for row in records if isinstance(row, dict) and row.get("trace_id") == trace_id]
    if len(hits) == 0:
        return "missing", None
    if len(hits) > 1:
        return "ambiguous", None
    return "ok", hits[0]


def retrieval_from_record(status, record, accepted_hashes):
    if status in ("missing", "unreadable", "ambiguous"):
        return "Unknown", status
    if status != "ok" or not isinstance(record, dict):
        return "Unknown", status or "missing"
    injected = record.get("memories_injected")
    if not isinstance(injected, list):
        return "Unknown", "bad_shape"
    if len(injected) == 0:
        return "No", "ok"
    accepted = set(accepted_hashes or [])
    matched = False
    details = []
    for item in injected:
        if not isinstance(item, dict):
            details.append({"match": False})
            continue
        digest = item.get("text_hash")
        hit = isinstance(digest, str) and digest in accepted
        matched = matched or hit
        details.append(
            {
                "text_hash": digest,
                "role": item.get("role"),
                "source": item.get("source"),
                "timestamp": item.get("timestamp"),
                "match": hit,
            }
        )
    return ("Yes" if matched else "No"), "ok", details


def assess_retrieval(status, record, accepted_hashes):
    result = retrieval_from_record(status, record, accepted_hashes)
    if len(result) == 2:
        retrieved, detail_status = result
        return {"retrieved": retrieved, "status": detail_status, "injected": []}
    retrieved, detail_status, injected = result
    return {"retrieved": retrieved, "status": detail_status, "injected": injected}


def assess_used(phase2_rows, key):
    rows = list(phase2_rows or [])
    if len(rows) == 0:
        return {"used": "Unknown", "trace_id": None, "reason": "no_attempts"}
    completed = [row for row in rows if row_is_completed_model_reply(row)]
    if len(completed) > 1:
        return {"used": "Unknown", "trace_id": None, "reason": "multiple_completed"}
    if len(completed) == 0:
        last = rows[-1]
        trace = last.get("trace_id") if isinstance(last, dict) else None
        return {"used": "Unknown", "trace_id": trace, "reason": "no_completed"}
    chosen = completed[0]
    used = "Yes" if answers_match(chosen.get("done_text"), key) else "No"
    return {
        "used": used,
        "trace_id": chosen.get("trace_id"),
        "reason": "completed",
        "done_text": chosen.get("done_text"),
    }


def file_sha256(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_manifest(text):
    if not isinstance(text, str) or not text.endswith("\n"):
        return None
    parsed = []
    for line in text.splitlines():
        parts = line.split(" ")
        if len(parts) != 3 or parts[1] != "":
            return None
        hexpart, name = parts[0], parts[2]
        if hexpart != hexpart.lower() or len(hexpart) != 64:
            return None
        try:
            int(hexpart, 16)
        except ValueError:
            return None
        if "/" in name or name != os.path.basename(name) or not name:
            return None
        parsed.append((hexpart, name))
    return parsed


def verify_protocol_seal(directory):
    manifest_path = os.path.join(directory, "PROTOCOL.sha256")
    try:
        with open(manifest_path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return False, "manifest_unreadable"
    parsed = parse_manifest(text)
    if parsed is None:
        return False, "manifest_format"
    names = [name for _, name in parsed]
    if names != SEAL_ORDER:
        return False, "order"
    for hexpart, name in parsed:
        path = os.path.join(directory, name)
        try:
            actual = file_sha256(path)
        except OSError:
            return False, "missing_file"
        if actual != hexpart:
            return False, "mismatch:" + name
    return True, "ok"


def sealed_files_readonly(directory) -> bool:
    for name in SEAL_ORDER:
        path = os.path.join(directory, name)
        if not os.path.isfile(path) or os.access(path, os.W_OK):
            return False
    return True


def _load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows


def summarize_phase1(rows, items, keys):
    by_item = {item_id: [] for item_id in keys}
    for row in rows:
        if not isinstance(row, dict):
            continue
        item_id = row.get("item_id")
        if item_id in by_item:
            by_item[item_id].append(row)
    item_reports = []
    completed = 0
    correct = 0
    incomplete = False
    for item_id in keys:
        frozen = items[item_id]
        attempts = by_item.get(item_id, [])
        done_rows = [row for row in attempts if row_is_completed_model_reply(row)]
        entry = {
            "item_id": item_id,
            "key": keys[item_id],
            "attempt_count": len(attempts),
            "completed_count": len(done_rows),
            "prompt_matches_frozen": None,
            "correct": False,
            "done_text": None,
            "task_type": None,
            "status": "incomplete",
        }
        if len(done_rows) != 1:
            incomplete = True
            item_reports.append(entry)
            continue
        chosen = done_rows[0]
        expected_hash = prompt_sha256(frozen)
        sent_hash = chosen.get("prompt_sha256")
        matches = isinstance(sent_hash, str) and sent_hash == expected_hash
        matched = answers_match(chosen.get("done_text"), keys[item_id])
        entry.update(
            {
                "prompt_matches_frozen": matches,
                "correct": matched,
                "done_text": chosen.get("done_text"),
                "task_type": chosen.get("task_type"),
                "trace_id": chosen.get("trace_id"),
                "status": "scored",
            }
        )
        completed += 1
        if matched:
            correct += 1
        if not matches:
            entry["deviation"] = "prompt_sha256_mismatch"
        item_reports.append(entry)
    if completed != PHASE1_REQUIRED:
        incomplete = True
    gate = phase1_gate(completed, correct) and not incomplete
    return {
        "completed": completed,
        "correct": correct,
        "gate": gate,
        "incomplete": incomplete,
        "items": item_reports,
    }


def _counts_line(summary) -> str:
    gate = "true" if summary["gate"] else "false"
    incomplete = "true" if summary["incomplete"] else "false"
    return (
        f"completed={summary['completed']} correct={summary['correct']} "
        f"gate={gate} incomplete={incomplete}"
    )


def _note_prompt_deviations(directory, summary):
    lines = []
    for item in summary["items"]:
        if item.get("deviation") == "prompt_sha256_mismatch":
            lines.append(
                f"- phase1 item {item['item_id']}: prompt_sha256 does not match "
                "frozen items.json phase1 prompt. The reply was still scored."
            )
    if not lines:
        return
    path = os.path.join(directory, "DEVIATIONS.md")
    existing = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            existing = handle.read()
    fresh = [line for line in lines if line not in existing]
    if not fresh:
        return
    with open(path, "a", encoding="utf-8") as handle:
        if not existing:
            handle.write("# Deviations\n\n")
        elif not existing.endswith("\n"):
            handle.write("\n")
        for line in fresh:
            handle.write(line + "\n")


def score_phase1(directory):
    ok, reason = verify_protocol_seal(directory)
    if not ok:
        print(f"seal_error={reason}", file=sys.stderr)
        return 2
    results_path = os.path.join(directory, "results_phase1.jsonl")
    if not os.path.isfile(results_path):
        print("results_missing", file=sys.stderr)
        return 2
    try:
        item_doc = _load_json(os.path.join(directory, "items.json"))
        key_doc = _load_json(os.path.join(directory, "answer_key.json"))
        rows = _load_jsonl(results_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"io_error={exc.__class__.__name__}", file=sys.stderr)
        return 2
    item_rows = item_doc.get("items") if isinstance(item_doc, dict) else None
    key_rows = key_doc.get("items") if isinstance(key_doc, dict) else None
    if not isinstance(item_rows, list) or not isinstance(key_rows, dict):
        print("io_error=shape", file=sys.stderr)
        return 2
    items = {}
    keys = {}
    for row in item_rows:
        if not isinstance(row, dict) or "id" not in row:
            print("io_error=shape", file=sys.stderr)
            return 2
        items[row["id"]] = row.get("phase1_prompt")
    for item_id, payload in key_rows.items():
        if isinstance(payload, dict) and isinstance(payload.get("key"), str):
            keys[item_id] = payload["key"]
    if list(keys) != [f"{index:02d}" for index in range(1, 11)]:
        print("io_error=item_ids", file=sys.stderr)
        return 2
    if any(item_id not in items for item_id in keys):
        print("io_error=item_ids", file=sys.stderr)
        return 2
    summary = summarize_phase1(rows, items, keys)
    _note_prompt_deviations(directory, summary)
    out_path = os.path.join(directory, "phase1_scores.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(_counts_line(summary))
    return 0 if summary["gate"] else 1


def _phase1_attempts(rows, item_id):
    return [
        row
        for row in rows
        if isinstance(row, dict) and row.get("item_id") == item_id and row.get("phase") == "phase1"
    ]


def _phase2_attempts(rows, item_id):
    found = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("item_id") == item_id and row.get("phase") == "phase2"
    ]
    if found:
        return found
    return [
        row
        for row in rows
        if isinstance(row, dict) and row.get("item_id") == item_id
    ]


def attribute_phase2(directory, memory_path, provenance_path):
    ok, reason = verify_protocol_seal(directory)
    if not ok:
        print(f"seal_error={reason}", file=sys.stderr)
        return 2
    scores_path = os.path.join(directory, "phase1_scores.json")
    phase2_path = os.path.join(directory, "results_phase2.jsonl")
    if not os.path.isfile(scores_path) or not os.path.isfile(phase2_path):
        print("attribute_refused", file=sys.stderr)
        return 1
    try:
        scores = _load_json(scores_path)
        phase1_rows = _load_jsonl(os.path.join(directory, "results_phase1.jsonl"))
        phase2_rows = _load_jsonl(phase2_path)
        item_doc = _load_json(os.path.join(directory, "items.json"))
        key_doc = _load_json(os.path.join(directory, "answer_key.json"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"io_error={exc.__class__.__name__}", file=sys.stderr)
        return 2
    if not isinstance(scores, dict) or scores.get("gate") is not True:
        print("attribute_refused", file=sys.stderr)
        return 1
    recomputed_items = {}
    recomputed_keys = {}
    for row in item_doc.get("items", []):
        recomputed_items[row["id"]] = row.get("phase1_prompt")
    for item_id, payload in key_doc.get("items", {}).items():
        recomputed_keys[item_id] = payload.get("key")
    recomputed = summarize_phase1(phase1_rows, recomputed_items, recomputed_keys)
    if not recomputed["gate"]:
        print("attribute_refused", file=sys.stderr)
        return 1
    scan_complete, memory_rows = _load_memory(memory_path)
    prov_status, prov_records, prov_bad = read_provenance(provenance_path)
    reports = []
    for item_id in [f"{index:02d}" for index in range(1, 11)]:
        payload = key_doc["items"][item_id]
        fact = payload["fact_sentence"]
        key = payload["key"]
        frozen_prompt = None
        for row in item_doc["items"]:
            if row["id"] == item_id:
                frozen_prompt = row["phase1_prompt"]
        p1 = _phase1_attempts(phase1_rows, item_id)
        p2 = _phase2_attempts(phase2_rows, item_id)
        started = [row.get("started_at") for row in p1]
        saves = [row.get("memory_save_user") for row in p1]
        storage = assess_storage(memory_rows, fact, started, saves, scan_complete)
        used = assess_used(p2, key)
        if used["reason"] == "multiple_completed" or used["reason"] == "no_attempts":
            retrieval = {"retrieved": "Unknown", "status": used["reason"], "injected": []}
        else:
            trace_id = used.get("trace_id")
            if prov_status != "ok":
                retrieval = assess_retrieval(prov_status, None, [])
            elif not isinstance(trace_id, str) or not trace_id:
                retrieval = assess_retrieval("missing", None, [])
            else:
                trace_status, record = records_for_trace(prov_records, trace_id)
                hashes = accepted_fact_hashes(
                    [row.get("prompt") for row in p1 if isinstance(row.get("prompt"), str)],
                    frozen_prompt,
                    p1,
                    [row["text"] for row in _qualifying_texts(memory_rows, fact, started, scan_complete)],
                    fact,
                )
                retrieval = assess_retrieval(trace_status, record, hashes)
        reports.append(
            {
                "item_id": item_id,
                "stored": storage["stored"],
                "storage_contradiction": storage["contradiction"],
                "storage_matches": storage["qualifying"],
                "retrieved": retrieval["retrieved"],
                "retrieval_status": retrieval["status"],
                "retrieval_matches": retrieval["injected"],
                "used": used["used"],
                "used_reason": used["reason"],
                "trace_id": used.get("trace_id"),
                "query_preview_used": False,
            }
        )
    out = {
        "scan_complete": scan_complete,
        "provenance_status": prov_status,
        "provenance_unparseable_lines": prov_bad,
        "items": reports,
    }
    out_path = os.path.join(directory, "phase2_attribution.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("attribute=ok")
    return 0


def _qualifying_texts(memory_rows, fact, started, scan_complete):
    lower = storage_lower_bound(started)
    if not scan_complete or lower is None:
        return []
    found = []
    for row in memory_rows or []:
        flat = flatten_memory_row(row)
        if row_qualifies(flat, fact, lower):
            found.append(flat)
    return found


def _load_memory(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return False, []
    if not isinstance(data, dict):
        return False, []
    return True, list(data.values())


def _write_manifest(directory, names):
    lines = []
    for name in names:
        digest = file_sha256(os.path.join(directory, name))
        lines.append(f"{digest}  {name}")
    text = "\n".join(lines) + "\n"
    path = os.path.join(directory, "PROTOCOL.sha256")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return text


def _self_test_scoring():
    assert answers_match("Sable", "Sable")
    assert answers_match("Sable.", "Sable")
    assert answers_match("22.", "22")
    assert answers_match("4.", "4")
    assert not answers_match("4..", "4")
    assert not answers_match("Sable today", "Sable")
    assert not answers_match("No", "no")
    assert not answers_match("sable", "Sable")
    assert answers_match("  Sable  ", "Sable")
    assert not answers_match("18.6  kilograms", "18.6 kilograms")
    assert not answers_match("Sable\n\nCaveat: extra", "Sable")
    assert not answers_match('"Sable"', "Sable")
    assert not answers_match("18.6", "18.6 kilograms")
    assert not answers_match("4.0", "4")
    assert not answers_match("", "4")
    assert not answers_match(None, "4")
    assert not answers_match("4", None)
    assert answers_match("Sable\n", "Sable")
    assert not answers_match("Sable\n.", "Sable")
    assert not answers_match(SERVER_ERROR_SENTENCE, "4")
    assert is_exact_server_error(SERVER_ERROR_SENTENCE)
    assert is_exact_server_error("  " + SERVER_ERROR_SENTENCE + "\n")
    assert not is_exact_server_error("Error: could not generate a response")
    assert not is_exact_server_error(SERVER_ERROR_SENTENCE + ".")
    bare = {
        "infrastructure": False,
        "http_status": 200,
        "done_present": True,
        "done_text": "Error: could not generate a response",
    }
    assert not attempt_is_infrastructure(bare)
    assert row_is_completed_model_reply(bare)
    errored = dict(bare, done_text=SERVER_ERROR_SENTENCE)
    assert attempt_is_infrastructure(errored)
    assert not row_is_completed_model_reply(errored)
    assert attempt_is_infrastructure("nope")
    assert attempt_is_infrastructure({"infrastructure": True, "done_present": True, "done_text": "4", "http_status": 200})
    assert attempt_is_infrastructure({"infrastructure_reason": "timeout", "done_present": True, "done_text": "4", "http_status": 200})
    assert attempt_is_infrastructure({"done_present": True, "done_text": "4", "http_status": 500})
    assert attempt_is_infrastructure({"done_present": False, "done_text": "4", "http_status": 200})
    assert attempt_is_infrastructure({"done_text": "4", "http_status": 200})
    assert attempt_is_infrastructure({"done_present": True, "done_text": None, "http_status": 200})
    empty_done = {"done_present": True, "done_text": "", "http_status": 200, "infrastructure": False}
    assert row_is_completed_model_reply(empty_done)
    assert not answers_match("", "4")
    assert phase1_gate(10, 8)
    assert not phase1_gate(10, 7)
    assert not phase1_gate(9, 9)


def _self_test_storage():
    fact = "The dock badge mark is K7-QRV-4419."
    start = ["2026-11-09T04:00:00+00:00"]
    good_ts = "2026-11-09T05:00:00+00:00"
    nested = {
        "text": "Note: The dock badge mark is K7-QRV-4419.\n\nQuestion: What is the dock badge mark?",
        "meta": {
            "role": "user",
            "memory_source": "user_conversation",
            "timestamp": good_ts,
            "is_thought_provoking": True,
        },
    }
    found = assess_storage([nested], fact, start, ["accepted"], True)
    assert found["stored"] == "Yes" and found["contradiction"] is False
    assert found["qualifying"][0]["role"] == "user"
    assert "text" not in found["qualifying"][0]

    def replaced(**kwargs):
        row = {
            "text": nested["text"],
            "role": "user",
            "memory_source": "user_conversation",
            "timestamp": good_ts,
        }
        row.update(kwargs)
        return row

    assert assess_storage([replaced(text="other")], fact, start, ["accepted"], True)["stored"] == "Unknown"
    assert assess_storage([replaced(memory_source="autonomous")], fact, start, ["accepted"], True)["stored"] == "Unknown"
    assert assess_storage([replaced(role="echo")], fact, start, ["accepted"], True)["stored"] == "Unknown"
    earlier = assess_storage(
        [replaced(timestamp="2026-11-09T03:00:00+00:00")], fact, start, ["accepted"], True
    )
    assert earlier["stored"] == "Unknown"
    assert assess_storage([replaced(timestamp=None)], fact, start, ["accepted"], True)["stored"] == "Unknown"
    assert assess_storage([replaced(timestamp="2026-11-09T05:00:00")], fact, start, ["accepted"], True)["stored"] == "Unknown"
    blinded = assess_storage([nested], fact, start, ["rejected"], False)
    assert blinded["stored"] == "Unknown"
    bad_start = assess_storage([nested], fact, ["not-a-time"], ["accepted"], True)
    assert bad_start["stored"] == "Unknown"
    contradiction = assess_storage([nested], fact, start, ["rejected"], True)
    assert contradiction["stored"] == "Yes" and contradiction["contradiction"] is True
    assert assess_storage([], fact, start, ["rejected"], True)["stored"] == "No"
    assert assess_storage([], fact, start, ["failed"], True)["stored"] == "No"
    assert assess_storage([], fact, start, ["accepted"], True)["stored"] == "Unknown"
    assert assess_storage([], fact, start, ["unknown"], True)["stored"] == "Unknown"
    assert assess_storage([], fact, start, None, True)["stored"] == "Unknown"
    assert normalize_memory_save(None) == "unknown"
    assert normalize_memory_save("nope") == "unknown"
    assert storage_lower_bound([]) is None
    assert storage_lower_bound(["2026-11-09T04:00:00+00:00", "bad"]) is None


def _self_test_retrieval_and_used():
    fact = "The dock badge mark is K7-QRV-4419."
    prompt = "Note: " + fact + "\n\nQuestion: What is the dock badge mark?"
    digest = text_hash(prompt)
    yes = assess_retrieval(
        "ok",
        {"memories_injected": [{"text_hash": digest, "role": "user", "source": "user_conversation", "timestamp": "t"}]},
        [digest],
    )
    assert yes["retrieved"] == "Yes"
    empty = assess_retrieval("ok", {"memories_injected": []}, [digest])
    assert empty["retrieved"] == "No"
    assert assess_retrieval("missing", None, [digest])["retrieved"] == "Unknown"
    assert assess_retrieval("unreadable", None, [digest])["retrieved"] == "Unknown"
    assert assess_retrieval("ambiguous", None, [digest])["retrieved"] == "Unknown"
    bad = assess_retrieval("ok", {"memories_injected": "nope"}, [digest])
    assert bad["retrieved"] == "Unknown" and bad["status"] == "bad_shape"
    assert records_for_trace([], "abc")[0] == "missing"
    assert records_for_trace([{"trace_id": "abc"}, {"trace_id": "abc"}], "abc")[0] == "ambiguous"

    echo_with_fact = "The stored line is " + fact
    hashes = accepted_fact_hashes(
        [prompt],
        prompt,
        [{"done_present": True, "done_text": echo_with_fact}],
        [prompt],
        fact,
    )
    assert text_hash(echo_with_fact) in hashes
    assert text_hash(prompt) in hashes
    short = accepted_fact_hashes(
        [],
        None,
        [{"done_present": True, "done_text": "K7-QRV-4419"}],
        [],
        fact,
    )
    assert text_hash("K7-QRV-4419") not in short
    only_short = assess_retrieval(
        "ok",
        {"memories_injected": [{"text_hash": text_hash("K7-QRV-4419"), "role": "echo", "source": "user_conversation"}]},
        short,
    )
    assert only_short["retrieved"] == "No"

    key_row = {"done_present": True, "done_text": "Sable", "http_status": 200, "trace_id": "t1", "phase": "phase2"}
    assert assess_used([key_row], "Sable")["used"] == "Yes"
    assert assess_used([dict(key_row, done_text="Other")], "Sable")["used"] == "No"
    infra = dict(key_row, done_text=SERVER_ERROR_SENTENCE)
    assert assess_used([infra], "Sable")["used"] == "Unknown"
    forced = dict(key_row, infrastructure=True, done_text="Sable")
    assert assess_used([forced], "Sable")["used"] == "Unknown"
    assert assess_used([key_row, dict(key_row, trace_id="t2")], "Sable")["used"] == "Unknown"
    assert assess_used([], "Sable")["used"] == "Unknown"
    last = assess_used([{"infrastructure_reason": "timeout", "trace_id": "last"}], "Sable")
    assert last["used"] == "Unknown" and last["trace_id"] == "last"

    with tempfile.TemporaryDirectory() as tmp:
        missing = read_provenance(os.path.join(tmp, "absent.jsonl"))
        assert missing[0] == "missing"
        unreadable = read_provenance(tmp)
        assert unreadable[0] == "unreadable"
        good = os.path.join(tmp, "p.jsonl")
        with open(good, "w", encoding="utf-8") as handle:
            handle.write("{not json}\n")
            handle.write(json.dumps({"trace_id": "t", "memories_injected": []}) + "\n")
        status, records, bad = read_provenance(good)
        assert status == "ok" and bad == 1 and len(records) == 1


def _self_test_seal_and_deadline():
    with tempfile.TemporaryDirectory() as tmp:
        for name in SEAL_ORDER:
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as handle:
                handle.write(name + "\n")
        _write_manifest(tmp, SEAL_ORDER)
        assert verify_protocol_seal(tmp) == (True, "ok")
        for name in SEAL_ORDER:
            os.chmod(os.path.join(tmp, name), 0o444)
        assert sealed_files_readonly(tmp)
        os.chmod(os.path.join(tmp, SEAL_ORDER[0]), 0o644)
        assert not sealed_files_readonly(tmp)
        os.chmod(os.path.join(tmp, SEAL_ORDER[0]), 0o644)
        with open(os.path.join(tmp, SEAL_ORDER[0]), "w", encoding="utf-8") as handle:
            handle.write("tampered\n")
        ok, reason = verify_protocol_seal(tmp)
        assert not ok and reason.startswith("mismatch")
        _write_manifest(tmp, list(reversed(SEAL_ORDER)))
        assert verify_protocol_seal(tmp)[1] == "order"
        digest = file_sha256(os.path.join(tmp, SEAL_ORDER[0]))
        upper = os.path.join(tmp, "PROTOCOL.sha256")
        with open(upper, "w", encoding="utf-8") as handle:
            handle.write(f"{digest.upper()}  {SEAL_ORDER[0]}\n")
        assert verify_protocol_seal(tmp)[1] == "manifest_format"
        with open(upper, "w", encoding="utf-8") as handle:
            handle.write(f"{digest} {SEAL_ORDER[0]}\n")
        assert verify_protocol_seal(tmp)[1] == "manifest_format"
        with open(upper, "w", encoding="utf-8") as handle:
            handle.write(f"{digest}  {SEAL_ORDER[0]}")
        assert verify_protocol_seal(tmp)[1] == "manifest_format"

    later = delay_deadline(
        ["2026-11-09T04:00:00+00:00", "2026-11-09T04:10:00+00:00"]
    )
    assert later == datetime.fromisoformat("2026-11-09T04:10:00+00:00") + timedelta(seconds=DELAY_SECONDS)
    try:
        delay_deadline([])
        raise AssertionError("empty deadline should fail")
    except ValueError:
        pass
    try:
        delay_deadline(["2026-11-09T04:00:00"])
        raise AssertionError("naive deadline should fail")
    except ValueError:
        pass
    assert parse_ts("2026-11-09T04:00:00Z") == datetime.fromisoformat("2026-11-09T04:00:00+00:00")


def run_self_tests():
    _self_test_scoring()
    _self_test_storage()
    _self_test_retrieval_and_used()
    _self_test_seal_and_deadline()
    print("self_test=ok")
    return 0


def main(argv):
    if "--self-test" in argv:
        return run_self_tests()
    if "--score-phase1" in argv:
        return score_phase1(HERE)
    if "--attribute" in argv:
        return attribute_phase2(HERE, MEMORY_META_PATH, PROVENANCE_PATH)
    print(
        "usage: score.py --self-test | --score-phase1 | --attribute",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
