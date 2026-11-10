#!/usr/bin/env python3
"""Isolated ungated file-fact retrieval experiment.

Laboratory only. Does not import the app package, call run_tool_dispatch,
open production memory or FAISS, contact port 5000, or touch the live Echo
process.

Protocol is fixed before any model call. Completed trial records are never
rerun. Call budget is 30 HTTP generations. Order is A, B, C, D. A follow-up
generation happens only when the model emitted tool_calls, and there is no
third round.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import secrets
import sys
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LAB = Path(__file__).resolve().parent
VOYAGER = LAB.parents[1]
DISPATCH_SOURCE = VOYAGER / "app" / "core" / "echo_tool_dispatch.py"
PRODUCTION_DISPATCH = Path(
    "/Users/richietate/Desktop/FeralEcho/app/core/echo_tool_dispatch.py"
)

OLLAMA_CHAT = "http://127.0.0.1:11434/api/chat"
OLLAMA_TAGS = "http://127.0.0.1:11434/api/tags"
MAX_MODEL_CALLS = 30
TIMEOUT_S = 120

# Locked before any model output. Not the production dispatch system prompt:
# that prompt instructs the model to use a tool whenever a request requires
# a real file. This one does not name a tool or a path.
SYSTEM_PROMPT = (
    "Answer the user. Do not invent data you were not given. "
    "Use a provided tool only if you decide it is needed."
)
CANDIDATE_TEMPLATE = (
    "A single line is stored at items/item_{nn}.txt. "
    "Quote that line and nothing else."
)
SCAFFOLD_TEMPLATE = (
    "A single line is stored at items/item_{nn}.txt. "
    "Read the file and quote the line, nothing else."
)
OPTIONS = {"temperature": 0, "num_ctx": 4096, "num_predict": 256}

CONDITIONS = (
    {"id": "A", "name": "candidate", "model": "llama3.1:8b", "tools": True, "prompt": "candidate"},
    {"id": "B", "name": "scaffold", "model": "llama3.1:8b", "tools": True, "prompt": "scaffold"},
    {"id": "C", "name": "no_tool", "model": "llama3.1:8b", "tools": False, "prompt": "candidate"},
    {"id": "D", "name": "echo_characterization", "model": "echo:latest", "tools": False, "prompt": "candidate"},
)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Return the text of one file inside the laboratory root. "
                "Pass a relative path."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from the laboratory root.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Look up a query in the laboratory memory stub.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Query text."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_thought",
            "description": "Store a short note inside the laboratory directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Note text."},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional labels.",
                    },
                },
                "required": ["content"],
            },
        },
    },
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def prompt_for(kind: str, nn: str) -> str:
    template = CANDIDATE_TEMPLATE if kind == "candidate" else SCAFFOLD_TEMPLATE
    return template.format(nn=nn)


def load_gate():
    """Load needs_dispatch from the worktree file without importing app/.

    Import runs module-level path setup and imports requests. It does not
    open a log, a memory file, or a socket. If that import fails, exec only
    the signal set and needs_dispatch and label the result a simulation.
    """
    source = DISPATCH_SOURCE.read_text(encoding="utf-8")
    production_note = "production file not compared"
    if PRODUCTION_DISPATCH.is_file():
        prod = PRODUCTION_DISPATCH.read_text(encoding="utf-8")
        production_note = (
            "worktree_source_sha256_matches_production"
            if hashlib.sha256(source.encode()).hexdigest()
            == hashlib.sha256(prod.encode()).hexdigest()
            else "worktree_source_differs_from_production"
        )
    try:
        spec = importlib.util.spec_from_file_location(
            "_lab_dispatch_gate_only", DISPATCH_SOURCE
        )
        if spec is None or spec.loader is None:
            raise ImportError("no loader")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        signals = tuple(sorted(module._DISPATCH_SIGNALS))
        fn = module.needs_dispatch
        return {
            "mode": "direct_function",
            "label": (
                "Direct call of needs_dispatch loaded from the worktree "
                "source file. Not a live server execution."
            ),
            "production_source_relation": production_note,
            "signals": signals,
            "function_source": inspect_source(source, "needs_dispatch"),
            "classify": fn,
        }
    except Exception as exc:
        namespace: dict = {}
        extracted = extract_defs(source)
        exec(extracted, namespace, namespace)  # noqa: S102 — laboratory copy of two pure defs
        return {
            "mode": "source_derived_simulation",
            "label": (
                "Source-derived simulation. The production module was not "
                "executed. Matching logic was copied from the function and "
                "signal set in the worktree source."
            ),
            "import_error": f"{type(exc).__name__}: {exc}",
            "production_source_relation": production_note,
            "signals": tuple(sorted(namespace["_DISPATCH_SIGNALS"])),
            "function_source": extracted,
            "classify": namespace["needs_dispatch"],
        }


def inspect_source(source: str, name: str) -> str:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    return ""


def extract_defs(source: str) -> str:
    tree = ast.parse(source)
    chunks = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_DISPATCH_SIGNALS":
                    chunks.append(ast.get_source_segment(source, node) or "")
        if isinstance(node, ast.FunctionDef) and node.name == "needs_dispatch":
            chunks.append(ast.get_source_segment(source, node) or "")
    if len(chunks) != 2:
        raise RuntimeError("could not extract gate definitions")
    return "\n\n".join(chunks) + "\n"


def classify_prompts(classify) -> dict:
    rows = []
    for cond in CONDITIONS:
        if cond["id"] not in {"A", "B"}:
            continue
        for n in range(1, 7):
            nn = f"{n:02d}"
            text = prompt_for(cond["prompt"], nn)
            verdict = bool(classify(text))
            rows.append(
                {
                    "trial_id": f"{cond['id']}{nn}",
                    "condition": cond["id"],
                    "prompt": text,
                    "needs_dispatch": verdict,
                    "expected_needs_dispatch": cond["id"] == "B",
                    "correct": verdict is (cond["id"] == "B"),
                }
            )
    return {
        "rows": rows,
        "correct": sum(1 for row in rows if row["correct"]),
        "total": len(rows),
    }


def confined_read(root: Path, path_arg) -> tuple[str, bool, str | None, str | None]:
    """Return result, ok, error_type, resolved path string.

    Refuses non-strings, traversal, and any path outside root.
    """
    if not isinstance(path_arg, str) or not path_arg.strip():
        return "[refused: empty or non-string path]", False, "empty_path", None
    if "\x00" in path_arg:
        return "[refused: invalid path]", False, "invalid_path", None
    raw = Path(path_arg)
    if ".." in raw.parts:
        return "[refused: traversal]", False, "traversal", None
    root_r = root.resolve()
    candidate = raw.resolve() if raw.is_absolute() else (root_r / raw).resolve()
    try:
        candidate.relative_to(root_r)
    except ValueError:
        return "[refused: outside laboratory root]", False, "outside_root", str(candidate)
    if not candidate.is_file():
        return "[refused: not a file]", False, "not_a_file", str(candidate)
    data = candidate.read_bytes()
    if len(data) > 4096:
        return "[refused: too large]", False, "too_large", str(candidate)
    return data.decode("utf-8"), True, None, str(candidate)


def execute_tool(root: Path, name: str, args: dict) -> tuple[str, bool, str | None, str | None]:
    if name == "read_file":
        return confined_read(root, args.get("path"))
    if name == "search_memory":
        return "laboratory stub: no stored matches", True, None, None
    if name == "log_thought":
        note = {
            "ts": now(),
            "content": args.get("content"),
            "tags": args.get("tags"),
        }
        dest = root / "notes" / "thought_log.jsonl"
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(note, sort_keys=True) + "\n")
        return "noted", True, None, str(dest)
    return f"[unknown tool: {name}]", False, "unknown_tool", None


def parse_calls(message: dict) -> list[dict]:
    raw_calls = message.get("tool_calls") or []
    if not isinstance(raw_calls, list):
        return []
    parsed = []
    for tc in raw_calls:
        if not isinstance(tc, dict):
            continue
        fn = tc.get("function") if isinstance(tc.get("function"), dict) else {}
        name = fn.get("name") or tc.get("name") or ""
        args = fn.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"_raw": args}
        if not isinstance(args, dict):
            args = {"_value": args}
        parsed.append(
            {
                "id": tc.get("id"),
                "name": str(name),
                "arguments": args,
            }
        )
    return parsed


def build_payload(model: str, messages: list, with_tools: bool) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": OPTIONS,
    }
    if with_tools:
        payload["tools"] = TOOL_SCHEMAS
    return payload


def ollama_chat(model: str, messages: list, with_tools: bool) -> tuple[dict, dict]:
    payload = build_payload(model, messages, with_tools)
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_CHAT,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            raw = response.read().decode("utf-8")
            return payload, json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        return payload, {"error": f"HTTP {exc.code}", "detail": detail}
    except Exception as exc:
        return payload, {"error": f"{type(exc).__name__}: {exc}"}


def request_contains_secret(payload: dict, secret: str) -> bool:
    return secret in json.dumps(payload)


def unwrap_once(text: str) -> str:
    """Diagnostic only. The pass rule does not use this."""
    stripped = text.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'", "`"}:
        return stripped[1:-1].strip()
    return stripped


def grade_trial(record: dict, expected: str, all_expected: list[str], assigned: Path) -> dict:
    final = record.get("final_answer") or ""
    stripped = final.strip()
    calls = record.get("emitted_tool_calls") or []
    executed = [c for c in calls if c.get("executed")]
    file_text = assigned.read_text(encoding="utf-8") if assigned.is_file() else None
    others = [s for s in all_expected if s != expected and s and s in final]
    retrieved = False
    for call in executed:
        if call.get("name") != "read_file":
            continue
        resolved = call.get("resolved_path")
        path_ok = bool(resolved) and Path(resolved) == assigned.resolve()
        bytes_ok = file_text is not None and call.get("tool_result") == file_text
        call["grader_path_ok"] = path_ok
        call["grader_bytes_ok"] = bytes_ok
        if path_ok and bytes_ok and call.get("error_type") is None:
            retrieved = True
    reasons = []
    if record.get("status") == "not_run":
        reasons.append("not_run")
    elif record.get("status") != "completed":
        reasons.append(record.get("status") or "incomplete")
    tool_names = [c.get("name") for c in calls]
    if len(calls) != 1:
        reasons.append(f"tool_call_count={len(calls)}")
    if calls and calls[0].get("name") != "read_file":
        reasons.append(f"first_tool={calls[0].get('name')}")
    if not retrieved:
        reasons.append("no_successful_read_of_assigned_file")
    if stripped != expected:
        reasons.append("answer_not_exact")
    if others:
        reasons.append("contains_other_trial_answer")
    if stripped == expected and not retrieved:
        reasons.append("unsupported_exact_answer")
    # Conditions C and D have no pass claim. Exact match is contamination.
    contamination = stripped == expected or expected in final
    return {
        "answer_exact": stripped == expected,
        "expected_contained": expected in final,
        "quoted_exact_diagnostic": unwrap_once(final) == expected,
        "other_answers_present": others,
        "tool_call_count": len(calls),
        "executed_count": len(executed),
        "tool_names": tool_names,
        "successful_assigned_read": retrieved,
        "unsupported_exact_answer": stripped == expected and not retrieved,
        "pass": not reasons and record.get("condition") in {"A", "B"},
        "reasons": reasons,
        "contamination_exact_or_contained": contamination,
        "file_text_matches_expected_line": file_text == expected + "\n",
    }


def self_test(root: Path) -> dict:
    fixture = root / "self_test_fixture"
    target = fixture / "items" / "item_01.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    expected = "0123456789abcdef0123456789abcdef"
    target.write_text(expected + "\n", encoding="utf-8")
    other = "fedcba9876543210fedcba9876543210"
    good_result, good_ok, good_err, good_resolved = confined_read(
        fixture, "items/item_01.txt"
    )
    bad_result, bad_ok, bad_err, _ = confined_read(fixture, "../item_01.txt")
    abs_result, abs_ok, abs_err, _ = confined_read(fixture, "/etc/passwd")
    perfect = {
        "status": "completed",
        "condition": "A",
        "final_answer": expected,
        "emitted_tool_calls": [
            {
                "name": "read_file",
                "arguments": {"path": "items/item_01.txt"},
                "executed": True,
                "resolved_path": str(target.resolve()),
                "tool_result": expected + "\n",
                "error_type": None,
            }
        ],
    }
    no_tool = {
        "status": "completed",
        "condition": "A",
        "final_answer": expected,
        "emitted_tool_calls": [],
    }
    wrong_path = {
        "status": "completed",
        "condition": "A",
        "final_answer": expected,
        "emitted_tool_calls": [
            {
                "name": "read_file",
                "arguments": {"path": "items/item_02.txt"},
                "executed": True,
                "resolved_path": str((fixture / "items" / "missing.txt").resolve()),
                "tool_result": "nope\n",
                "error_type": "not_a_file",
            }
        ],
    }
    extra_word = dict(perfect, final_answer=expected + " thanks")
    other_leak = dict(perfect, final_answer=expected + other)
    quoted = dict(perfect, final_answer=f'"{expected}"')
    cases = {
        "read_ok": good_ok and good_result == expected + "\n" and good_err is None,
        "traversal_refused": (not bad_ok) and bad_err == "traversal",
        "absolute_outside_refused": (not abs_ok) and abs_err == "outside_root",
        "perfect_passes": grade_trial(perfect, expected, [expected, other], target)["pass"],
        "answer_without_tool_fails": not grade_trial(no_tool, expected, [expected], target)["pass"],
        "wrong_path_fails": not grade_trial(wrong_path, expected, [expected], target)["pass"],
        "extra_word_fails": not grade_trial(extra_word, expected, [expected], target)["pass"],
        "other_secret_fails": not grade_trial(other_leak, expected, [expected, other], target)["pass"],
        "quotes_fail_strict_rule": not grade_trial(quoted, expected, [expected], target)["pass"],
        "quotes_noted_as_diagnostic": grade_trial(quoted, expected, [expected], target)[
            "quoted_exact_diagnostic"
        ],
    }
    cases["all_passed"] = all(cases.values())
    write_json(root / "self_test_grader.json", cases)
    return cases


def models_available(required: set[str]) -> dict:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "present": []}
    present = [m.get("name") for m in payload.get("models") or []]
    missing = sorted(name for name in required if name not in present)
    return {"ok": not missing, "missing": missing, "present": present}


def trial_paths(cond: str, nn: str) -> tuple[Path, Path]:
    root = LAB / "fixtures" / cond / nn
    assigned = root / "items" / f"item_{nn}.txt"
    return root, assigned


def ensure_fixture(cond: str, nn: str, key: dict) -> str:
    trial_id = f"{cond}{nn}"
    root, assigned = trial_paths(cond, nn)
    if trial_id in key["trials"]:
        return key["trials"][trial_id]
    secret = secrets.token_hex(16)
    while secret in key["trials"].values():
        secret = secrets.token_hex(16)
    assigned.parent.mkdir(parents=True, exist_ok=True)
    assigned.write_text(secret + "\n", encoding="utf-8")
    key["trials"][trial_id] = secret
    return secret


def public_request(payload: dict) -> dict:
    """Store the request that was sent. Secrets must already have been checked."""
    return payload


def run_one(spec: dict, nn: str, expected: str, calls_state: dict) -> dict:
    trial_id = f"{spec['id']}{nn}"
    root, assigned = trial_paths(spec["id"], nn)
    user_prompt = prompt_for(spec["prompt"], nn)
    record = {
        "trial_id": trial_id,
        "condition": spec["id"],
        "condition_name": spec["name"],
        "model": spec["model"],
        "tools_offered": spec["tools"],
        "prompt": user_prompt,
        "nn": nn,
        "assigned_file": str(assigned),
        "started_at": now(),
        "model_calls": [],
        "emitted_tool_calls": [],
        "status": "completed",
    }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    if calls_state["used"] >= MAX_MODEL_CALLS:
        record["status"] = "not_run"
        record["reason"] = "call_budget"
        record["finished_at"] = now()
        return record

    payload = build_payload(spec["model"], messages, spec["tools"])
    if request_contains_secret(payload, expected):
        record["status"] = "aborted_secret_in_first_request"
        record["model_calls"].append({"round": 1, "leak": True, "sent": False})
        record["finished_at"] = now()
        return record
    _, response = ollama_chat(spec["model"], messages, spec["tools"])
    calls_state["used"] += 1
    message = response.get("message") if isinstance(response, dict) else None
    if not isinstance(message, dict):
        record["status"] = "model_error"
        record["model_calls"].append(
            {
                "round": 1,
                "request": public_request(payload),
                "response": response,
            }
        )
        record["final_answer"] = ""
        record["finished_at"] = now()
        return record

    parsed = parse_calls(message)
    record["model_calls"].append(
        {
            "round": 1,
            "request_messages": messages,
            "tools_sent": bool(spec["tools"]),
            "response_message": message,
            "done_reason": response.get("done_reason"),
            "eval_count": response.get("eval_count"),
            "prompt_eval_count": response.get("prompt_eval_count"),
            "total_duration": response.get("total_duration"),
        }
    )
    for call in parsed:
        entry = {
            "round": 1,
            "name": call["name"],
            "arguments": call["arguments"],
            "id": call["id"],
            "executed": False,
        }
        record["emitted_tool_calls"].append(entry)

    if not parsed or not spec["tools"]:
        record["final_answer"] = message.get("content") or ""
        record["finished_at"] = now()
        return record

    assistant = {"role": "assistant", "content": message.get("content") or ""}
    if message.get("tool_calls"):
        assistant["tool_calls"] = message["tool_calls"]
    messages.append(assistant)
    for call, entry in zip(parsed, record["emitted_tool_calls"]):
        result, ok, error_type, resolved = execute_tool(
            root, call["name"], call["arguments"]
        )
        entry["executed"] = True
        entry["tool_result"] = result
        entry["tool_ok"] = ok
        entry["error_type"] = error_type
        entry["resolved_path"] = resolved
        tool_message = {"role": "tool", "tool_name": call["name"], "content": result}
        if call.get("id"):
            tool_message["tool_call_id"] = call["id"]
        messages.append(tool_message)

    if calls_state["used"] >= MAX_MODEL_CALLS:
        record["status"] = "followup_not_run"
        record["reason"] = "call_budget"
        record["final_answer"] = message.get("content") or ""
        record["finished_at"] = now()
        return record

    payload2 = build_payload(spec["model"], messages, spec["tools"])
    blob = json.dumps(payload2)
    if expected not in blob:
        record["status"] = "followup_missing_tool_result"
        record["finished_at"] = now()
        record["final_answer"] = message.get("content") or ""
        return record
    _, response2 = ollama_chat(spec["model"], messages, spec["tools"])
    calls_state["used"] += 1
    message2 = response2.get("message") if isinstance(response2, dict) else None
    record["model_calls"].append(
        {
            "round": 2,
            "request_messages": messages,
            "tools_sent": True,
            "response": response2 if not isinstance(message2, dict) else None,
            "response_message": message2,
            "done_reason": response2.get("done_reason") if isinstance(response2, dict) else None,
            "eval_count": response2.get("eval_count") if isinstance(response2, dict) else None,
        }
    )
    if not isinstance(message2, dict):
        record["status"] = "followup_model_error"
        record["final_answer"] = ""
        record["finished_at"] = now()
        return record
    for call in parse_calls(message2):
        record["emitted_tool_calls"].append(
            {
                "round": 2,
                "name": call["name"],
                "arguments": call["arguments"],
                "id": call["id"],
                "executed": False,
            }
        )
    record["final_answer"] = message2.get("content") or ""
    record["finished_at"] = now()
    return record


def score_condition(rows: list[dict], cond: str) -> dict:
    subset = [row for row in rows if row["condition"] == cond]
    ran = [row for row in subset if row["record_status"] != "not_run"]
    if cond in {"A", "B"}:
        passed = sum(1 for row in subset if row["grade"]["pass"])
        return {"ran": len(ran), "planned": 6, "passed": passed, "score": f"{passed}/6"}
    exact = sum(1 for row in subset if row["grade"]["answer_exact"])
    return {
        "ran": len(ran),
        "planned": 6,
        "exact_answers": exact,
        "score": f"{exact}/6",
    }


def main() -> int:
    if (LAB / "summary.json").exists():
        print("summary.json already exists; refusing to rerun", flush=True)
        return 0
    forbidden = ("run_tool_dispatch", "127.0.0.1:5000", "localhost:5000", "faiss")
    own = Path(__file__).read_text(encoding="utf-8")
    # The words appear in this script only as prohibitions in the docstring
    # and this check. Execution paths must not call them.
    if "urlopen(OLLAMA_CHAT" not in own:
        raise SystemExit("harness lost its ollama call")

    protocol = {
        "written_at": now(),
        "system_prompt": SYSTEM_PROMPT,
        "candidate_template": CANDIDATE_TEMPLATE,
        "scaffold_template": SCAFFOLD_TEMPLATE,
        "options": OPTIONS,
        "max_model_calls": MAX_MODEL_CALLS,
        "order": [c["id"] for c in CONDITIONS],
        "followup_rule": (
            "One follow-up HTTP call only if the model emitted tool_calls. "
            "No third round. Tools stay available on the follow-up so an "
            "extra call is observable and fails the exactly-one rule."
        ),
        "pass_rule_ab": (
            "Exactly one model-emitted tool call; it is read_file; the "
            "resolved path is the assigned file; the tool result equals the "
            "file bytes; final answer strip equals the 32-character line; "
            "no other trial secret appears."
        ),
        "quote_wrapping": "fails the pass rule; quoted_exact_diagnostic is not a pass",
        "thresholds": {"A": "5/6", "B": "5/6", "C": "0/6 exact", "gate": "12/12"},
        "ollama_chat": OLLAMA_CHAT,
        "forbidden_checked": list(forbidden),
    }
    write_json(LAB / "protocol.json", protocol)

    gate = load_gate()
    classified = classify_prompts(gate["classify"])
    system_hits = [sig for sig in gate["signals"] if sig in SYSTEM_PROMPT.lower()]
    gate_doc = {
        "checked_at": now(),
        "mode": gate["mode"],
        "label": gate["label"],
        "import_error": gate.get("import_error"),
        "production_source_relation": gate["production_source_relation"],
        "signal_count": len(gate["signals"]),
        "signals": list(gate["signals"]),
        "function_source": gate["function_source"],
        "system_prompt_signal_hits": system_hits,
        "rows": classified["rows"],
        "correct": classified["correct"],
        "total": classified["total"],
        "acceptance_12_of_12": classified["correct"] == 12 and not system_hits,
    }
    write_json(LAB / "gate_verification.json", gate_doc)
    print(
        f"gate {gate['mode']} {classified['correct']}/{classified['total']}",
        flush=True,
    )

    tests = self_test(LAB)
    if not tests["all_passed"]:
        print("grader self-test failed; no model calls", flush=True)
        write_json(LAB / "summary.json", {"status": "self_test_failed", "self_test": tests})
        return 1

    availability = models_available({"llama3.1:8b", "echo:latest"})
    write_json(LAB / "model_availability.json", availability)
    if not availability["ok"]:
        print(f"models unavailable: {availability}", flush=True)
        write_json(
            LAB / "summary.json",
            {"status": "models_unavailable", "availability": availability, "gate": gate_doc["acceptance_12_of_12"]},
        )
        return 1

    key_path = LAB / "grader_key.json"
    if key_path.exists():
        key = json.loads(key_path.read_text(encoding="utf-8"))
    else:
        key = {"created_at": now(), "trials": {}}

    calls_state = {"used": 0}
    records = []
    for spec in CONDITIONS:
        for n in range(1, 7):
            nn = f"{n:02d}"
            trial_id = f"{spec['id']}{nn}"
            record_path = LAB / "records" / f"{trial_id}.json"
            if record_path.exists():
                record = json.loads(record_path.read_text(encoding="utf-8"))
                calls_state["used"] += len(record.get("model_calls") or [])
                records.append(record)
                continue
            expected = ensure_fixture(spec["id"], nn, key)
            write_json(key_path, key)
            if calls_state["used"] >= MAX_MODEL_CALLS:
                record = {
                    "trial_id": trial_id,
                    "condition": spec["id"],
                    "condition_name": spec["name"],
                    "model": spec["model"],
                    "tools_offered": spec["tools"],
                    "prompt": prompt_for(spec["prompt"], nn),
                    "status": "not_run",
                    "reason": "call_budget",
                    "model_calls": [],
                    "emitted_tool_calls": [],
                    "final_answer": "",
                    "finished_at": now(),
                }
            else:
                try:
                    record = run_one(spec, nn, expected, calls_state)
                except Exception:
                    record = {
                        "trial_id": trial_id,
                        "condition": spec["id"],
                        "status": "harness_exception",
                        "traceback": traceback.format_exc(),
                        "model_calls": [],
                        "emitted_tool_calls": [],
                        "final_answer": "",
                    }
            write_json(record_path, record)
            records.append(record)
            print(
                f"{trial_id} status={record['status']} calls_used={calls_state['used']} "
                f"tools={len(record.get('emitted_tool_calls') or [])}",
                flush=True,
            )
            if record.get("status") == "aborted_secret_in_first_request":
                print("secret leaked into a first request; stopping", flush=True)
                break
        else:
            continue
        break

    all_expected = [key["trials"][r["trial_id"]] for r in records if r["trial_id"] in key["trials"]]
    graded_rows = []
    for record in records:
        expected = key["trials"][record["trial_id"]]
        _, assigned = trial_paths(record["condition"], record.get("nn") or record["trial_id"][1:])
        if "nn" not in record:
            record["nn"] = record["trial_id"][1:]
        grade = grade_trial(record, expected, list(key["trials"].values()), assigned)
        first_request = None
        if record.get("model_calls"):
            first = record["model_calls"][0]
            first_request = json.dumps(first.get("request_messages") or first.get("request") or "")
        graded_rows.append(
            {
                "trial_id": record["trial_id"],
                "condition": record["condition"],
                "model": record.get("model"),
                "record_status": record.get("status"),
                "prompt": record.get("prompt"),
                "final_answer": record.get("final_answer") or "",
                "tool_trace": [
                    {
                        "round": c.get("round"),
                        "name": c.get("name"),
                        "arguments": c.get("arguments"),
                        "executed": c.get("executed"),
                        "error_type": c.get("error_type"),
                        "path_ok": c.get("grader_path_ok"),
                        "bytes_ok": c.get("grader_bytes_ok"),
                    }
                    for c in record.get("emitted_tool_calls") or []
                ],
                "first_request_contains_expected": bool(first_request and expected in first_request),
                "grade": grade,
            }
        )

    scores = {cond: score_condition(graded_rows, cond) for cond in "ABCD"}
    summary = {
        "finished_at": now(),
        "status": "completed",
        "model_calls_used": calls_state["used"],
        "model_call_budget": MAX_MODEL_CALLS,
        "gate_mode": gate["mode"],
        "gate_correct": f"{classified['correct']}/{classified['total']}",
        "gate_acceptance": gate_doc["acceptance_12_of_12"],
        "system_prompt_signal_hits": system_hits,
        "scores": scores,
        "thresholds": protocol["thresholds"],
        "rows": graded_rows,
        "self_test_passed": True,
        "availability": availability,
    }
    write_json(LAB / "summary.json", summary)
    print(
        f"done calls={calls_state['used']} "
        f"A={scores['A']['score']} B={scores['B']['score']} "
        f"C={scores['C']['score']} D={scores['D']['score']} "
        f"gate={summary['gate_correct']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
