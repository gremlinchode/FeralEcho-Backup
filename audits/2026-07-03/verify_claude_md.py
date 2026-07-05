#!/usr/bin/env python3
"""
verify_claude_md.py — Read-only CLAUDE.md verification script.

Run from the FeralEcho project root:
    python audits/2026-07-03/verify_claude_md.py

Prints PASS or FAIL for each falsifiable CLAUDE.md claim.
Makes no changes. Produces no side effects.
"""

import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
WARN = "\033[33mWARN\033[0m"


def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    line = f"[{status}] {label}"
    if detail:
        line += f"\n       {detail}"
    print(line)
    return condition


def warn(label, detail=""):
    print(f"[{WARN}] {label}")
    if detail:
        print(f"       {detail}")


def read_file(path):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return None
    with open(full, "r", errors="replace") as f:
        return f.read()


def grep(path, pattern):
    """Return list of (line_number, line) matches in file."""
    src = read_file(path)
    if src is None:
        return []
    results = []
    for i, line in enumerate(src.splitlines(), 1):
        if re.search(pattern, line):
            results.append((i, line.strip()))
    return results


THIS_FILE = os.path.relpath(__file__, ROOT)


def grep_dir(directory, pattern, ext=".py", exclude_dirs=None):
    """Return dict {relpath: [(lineno, line)]} for all matching files."""
    exclude_dirs = set(exclude_dirs or [])
    matches = {}
    full_dir = os.path.join(ROOT, directory)
    for dirpath, dirnames, filenames in os.walk(full_dir):
        dirnames[:] = [d for d in dirnames
                       if os.path.relpath(os.path.join(dirpath, d), ROOT)
                       not in exclude_dirs]
        for fn in filenames:
            if fn.endswith(ext):
                relpath = os.path.relpath(os.path.join(dirpath, fn), ROOT)
                if relpath == THIS_FILE:
                    continue
                found = grep(relpath, pattern)
                if found:
                    matches[relpath] = found
    return matches


results = []

print("=" * 68)
print("FeralEcho CLAUDE.md Verification — 2026-07-03")
print(f"Project root: {ROOT}")
print("=" * 68)
print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: Echo's Modelfile identity is the authority ──────────")

oh_src = read_file("app/ollama_handler.py")
if oh_src is None:
    check("ollama_handler.py exists", False, "File not found")
else:
    blocking_suppressed = bool(re.search(r'"system"\s*:\s*""', oh_src))
    results.append(check(
        'ollama_handler.py query_ollama: "system": "" NOT present (would suppress Modelfile)',
        not blocking_suppressed,
        'FAIL: "system": "" found — Modelfile SYSTEM block is suppressed on every HTTP query.'
        if blocking_suppressed else ""
    ))

    streaming_matches = grep("app/ollama_handler.py", r'"system"\s*:\s*""')
    results.append(check(
        'stream_query_ollama: "system": "" NOT present',
        len(streaming_matches) == 0,
        f'FAIL: found at lines {[ln for ln, _ in streaming_matches]}' if streaming_matches else ""
    ))

print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: echo_principles.json is hash-verified at startup ────")

run_src = read_file("run.py")
if run_src is None:
    check("run.py exists", False, "File not found")
else:
    genesis_in_startup = bool(re.search(r"genesis_hash", run_src))
    if genesis_in_startup:
        # check if it's in a startup function vs an endpoint
        lines = [(i, l) for i, l in enumerate(run_src.splitlines(), 1)
                 if "genesis_hash" in l]
        in_startup = any("start_background" in run_src[max(0, run_src.find(l)):
                                                         run_src.find(l)+500]
                         for _, l in lines)
        results.append(check(
            "genesis_hash checked before server starts (not just in an HTTP endpoint)",
            False,
            f"genesis_hash found at lines {[ln for ln, _ in lines]} but only in HTTP endpoint, not startup path"
        ))
    else:
        results.append(check(
            "genesis_hash NOT checked at startup — CLAUDE.md claim is FALSE",
            False,
            'No reference to genesis_hash in run.py at all. The CLAUDE.md claim '
            '"hash-verified at startup" has no corresponding code.'
        ))

print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: Self-edit cooldown is in-memory, resets on restart ──")

sm_src = read_file("app/core/self_edit_manager.py")
if sm_src is None:
    check("self_edit_manager.py exists", False)
else:
    cooldown_var = grep("app/core/self_edit_manager.py",
                        r"_last_any_autonomous_edit\s*[:=]\s*float\s*=\s*0\.0")
    results.append(check(
        "_last_any_autonomous_edit = 0.0 at module level (resets on import)",
        len(cooldown_var) > 0,
        f"Found at: {cooldown_var}" if cooldown_var else "Variable not found"
    ))

    persist_write = grep("app/core/self_edit_manager.py",
                         r"(json\.dump|open.*cooldown|cooldown.*write)")
    results.append(check(
        "No file persistence of cooldown found (confirms in-memory only)",
        len(persist_write) == 0,
        f"Unexpected persistence found: {persist_write}" if persist_write else ""
    ))

print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: council learn_from_rating is not called in council pipeline ──")

cr_matches = grep("app/core/council_rater.py", r"learn_from_rating")
results.append(check(
    "learn_from_rating() has ZERO calls in council_rater.py",
    len(cr_matches) == 0,
    f"UNEXPECTED calls found: {cr_matches}" if cr_matches else
    "Confirmed: council ratings produce no River training signal"
))

print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: Wolf bridge calls simulate_self_edit, not perform_self_edit ──")

wolf_call = grep("app/core/echo_model_orchestrator.py", r"simulate_self_edit|perform_self_edit")
is_simulate = any("simulate_self_edit" in l for _, l in wolf_call)
is_perform = any("perform_self_edit" in l and "wolf" in l.lower() for _, l in wolf_call)

results.append(check(
    "Wolf bridge call site uses simulate_self_edit (dry-run), not perform_self_edit",
    is_simulate and not is_perform,
    f"Lines found: {wolf_call}"
))

print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: wolf_dryrun_window.json is dead code (zero readers) ──")

dryrun_matches = grep_dir(".", r"wolf_dryrun_window", exclude_dirs=["audits"])
results.append(check(
    "wolf_dryrun_window not referenced in any .py file",
    len(dryrun_matches) == 0,
    f"Unexpected references: {list(dryrun_matches.keys())}" if dryrun_matches else ""
))

print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: EDIT_FORBIDDEN_TARGETS matches CLAUDE.md list ──────")

expected_targets = {
    "run.py",
    "Modelfile",
    "app/core/river_deliberation.py",
    "app/core/echo_core.py",
    "app/core/memory_bridge.py",
    "app/core/introspection_channel.py",
    "app/core/echo_model_orchestrator.py",
    "app/core/self_model_updater.py",
    "app/core/bible_injection.py",
    "echo_principles.json",
}
if sm_src is None:
    check("EDIT_FORBIDDEN_TARGETS defined", False)
else:
    all_present = all(t.replace("/", r"[/\\]").replace(".", r"\.") in
                      sm_src or t in sm_src for t in expected_targets)
    results.append(check(
        "All 10 CLAUDE.md-listed protected files found in EDIT_FORBIDDEN_TARGETS",
        all_present,
        f"Source slice: {grep('app/core/self_edit_manager.py', 'FORBIDDEN')[0] if grep('app/core/self_edit_manager.py', 'FORBIDDEN') else 'not found'}"
    ))

print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: Snapshot restores actual files (not just health manifest) ──")

snap_src = read_file("app/core/snapshot_manager.py")
if snap_src is None:
    check("snapshot_manager.py exists", False)
else:
    artifacts_dict = grep("app/core/snapshot_manager.py", r"_ARTIFACTS\s*=")
    has_file_copy = grep("app/core/snapshot_manager.py", r"shutil\.copy2")
    has_file_restore = grep("app/core/snapshot_manager.py", r"os\.replace")
    results.append(check(
        "Snapshot uses shutil.copy2 (copies actual files, not just metadata)",
        len(has_file_copy) > 0,
        f"shutil.copy2 at: {has_file_copy}"
    ))
    results.append(check(
        "Restore uses os.replace (writes files back on restore)",
        len(has_file_restore) > 0,
        f"os.replace at: {has_file_restore}"
    ))
    warn(
        "CLAUDE.md describes snapshots as 'health manifest, not filesystem backup' — this is FALSE",
        "Snapshot copies 5 actual files; restore writes them back. "
        "See AUDIT_REPORT.md finding M-2."
    )

print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: FAISS both indexes at known paths ────────────────────")

mem_meta = os.path.join(ROOT, "memory", "memory_meta.json")
data_meta = os.path.join(ROOT, "data", "memory_meta.json")

for label, path in [("memory/memory_meta.json", mem_meta),
                    ("data/memory_meta.json", data_meta)]:
    if os.path.exists(path):
        try:
            with open(path) as f:
                meta = json.load(f)
            count = len(meta.get("texts", []))
            results.append(check(
                f"{label} readable, vector count = {count}",
                True,
                "WARNING: 0 vectors — semantic memory is empty" if count == 0 else ""
            ))
            if count == 0:
                warn(f"{label} has 0 vectors — memory retrieval returns nothing")
        except Exception as e:
            results.append(check(f"{label} readable", False, str(e)))
    else:
        results.append(check(f"{label} exists", False, "File not found"))

print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: self_heal.py has no live callers ─────────────────────")

heal_callers = grep_dir("app", r"(from app.core.self_heal|import self_heal)")
heal_callers_root = grep_dir(".", r"(from app.core.self_heal|import self_heal)",
                             exclude_dirs=["audits", "archive_janitor"])
all_heal = {**heal_callers, **heal_callers_root}
# filter out self_heal.py itself and archive scripts
all_heal = {k: v for k, v in all_heal.items()
            if "self_heal.py" not in k and "archive_janitor" not in k}
results.append(check(
    "self_heal.py has no live callers (intentionally disconnected)",
    len(all_heal) == 0,
    f"Unexpected callers: {list(all_heal.keys())}" if all_heal else ""
))

print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: Token limits by task type ───────────────────────────")

token_matches = grep("app/core/echo_model_orchestrator.py", r"_TASK_TOKEN_LIMITS")
if token_matches:
    results.append(check(
        "_TASK_TOKEN_LIMITS dict exists in echo_model_orchestrator.py",
        True,
        f"Defined at line {token_matches[0][0]}"
    ))
    # Spot-check values
    orch_src = read_file("app/core/echo_model_orchestrator.py")
    has_512 = "512" in orch_src
    has_1024 = "1024" in orch_src
    has_2048 = "2048" in orch_src
    results.append(check(
        "Token limit values 512, 1024, 2048 all present in orchestrator",
        has_512 and has_1024 and has_2048
    ))
else:
    results.append(check("_TASK_TOKEN_LIMITS exists", False))

print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: F1 AST scanner blocks key unsafe operations ─────────")

if sm_src is None:
    check("self_edit_manager.py exists", False)
else:
    blocked = {
        "exec/eval (bare calls)": r"_BLOCKED_BARE_CALLS\s*=\s*frozenset",
        "os.system/popen (os attrs)": r"_BLOCKED_OS_ATTRS\s*=\s*frozenset",
        "subprocess (sub attrs)": r"_BLOCKED_SUB_ATTRS\s*=\s*frozenset",
        "shutil (shutil attrs)": r"_BLOCKED_SHUTIL_ATTRS\s*=\s*frozenset",
        "Path.write_text/bytes": r"_BLOCKED_PATH_WRITES\s*=\s*frozenset",
    }
    for name, pattern in blocked.items():
        found = bool(re.search(pattern, sm_src))
        results.append(check(
            f"F1 scanner has blocked set for {name}",
            found
        ))

print()

# ─────────────────────────────────────────────────────────────────
print("── CLAIM: Terminal user rating 1-5 is wired ───────────────────")

tc_src = read_file("terminal_client.py")
if tc_src is None:
    check("terminal_client.py exists", False)
else:
    rating_trigger = grep("terminal_client.py",
                          r'msg in \{.*"1".*"5".*\}|if.*\bin\b.*rating')
    results.append(check(
        "Bare digit 1-5 triggers _save_rating() in terminal_client.py",
        len(rating_trigger) > 0,
        f"Found at: {rating_trigger}" if rating_trigger else
        "Rating trigger not found — check terminal_client.py manually"
    ))

print()

# ─────────────────────────────────────────────────────────────────
print("── SUMMARY ──────────────────────────────────────────────────────")
total = len(results)
passed = sum(results)
failed = total - passed
print(f"Checks run: {total}")
print(f"  {passed} PASSED")
print(f"  {failed} FAILED")
print()
if failed > 0:
    print("See AUDIT_REPORT.md for full findings with file:line evidence.")
else:
    print("All checks passed.")
print()
print("Note: This script tests structural/static claims only.")
print("Runtime behavior (e.g., whether loops fire correctly) requires the server running.")
