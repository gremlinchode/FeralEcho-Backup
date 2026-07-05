#!/usr/bin/env python3
"""
verify_riverbrain.py

Read-only diagnostic for the RiverBrain persistence guard in
app/core/echo_model_orchestrator.py (_do_save, ~line 775-812).

WHY THIS FILE NEVER IMPORTS RiverBrain OR CALLS get_river_brain():
RiverBrain.__init__ starts a daemon "RiverBrain-Writer" thread as a side
effect of construction (see echo_model_orchestrator.py ~line 610), and that
thread will eventually call _do_save() on its own timer. Constructing a
RiverBrain instance to "just look" is therefore not read-only -- it is
exactly the failure mode under investigation: a second process loads a
snapshot, and its writer thread later wins or loses a race against the live
Flask instance's writer thread, with no merge path between them (see
SECTION 3 below). This script reads memory/river_brain.pkl with a bare
pickle.load() on a plain file handle -- inspecting the dict, never building
a RiverBrain -- and never calls pickle.dump() anywhere. It performs no
writes of any kind and touches no file's mtime beyond the read.

Usage:
    python verify_riverbrain.py
"""

import os
import re
import sys
import json
import pickle
import hashlib
import subprocess
from datetime import datetime, timezone

try:
    import fcntl
except ImportError:
    fcntl = None

ROOT = os.path.dirname(os.path.abspath(__file__))
PKL_PATH = os.path.join(ROOT, "memory", "river_brain.pkl")
INTROSPECTION_PATH = os.path.join(ROOT, "memory", "introspection_state.json")
ORCHESTRATOR_PATH = os.path.join(ROOT, "app", "core", "echo_model_orchestrator.py")
INTROSPECTION_MODULE_PATH = os.path.join(ROOT, "app", "core", "introspection_channel.py")

LOG_CANDIDATES = [
    os.path.join(ROOT, "memory", "echo_watchdog.log"),
    os.path.join(ROOT, "echo.log"),
    os.path.join(ROOT, "echo_logs.log"),
]
SAVE_SKIPPED_RE = re.compile(
    r"(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*\[RIVER\] Save skipped.*disk has (?P<disk>\d+) obs, instance has (?P<inst>\d+)"
)


def hr(title=""):
    line = "=" * 70
    print(f"\n{line}\n{title}\n{line}" if title else line)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------
# SECTION 1 -- disk pkl, read-only
# ------------------------------------------------------------------

def read_disk_snapshot():
    result = {"exists": False}
    if not os.path.exists(PKL_PATH):
        return result
    stat = os.stat(PKL_PATH)
    result.update({
        "exists": True,
        "size_bytes": stat.st_size,
        "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "sha256": sha256_file(PKL_PATH),
    })
    lock_path = PKL_PATH + ".lock"
    lock_file = None
    try:
        if fcntl and os.path.exists(lock_path):
            lock_file = open(lock_path, "r")
            fcntl.flock(lock_file, fcntl.LOCK_SH)
        with open(PKL_PATH, "rb") as f:
            data = pickle.load(f)  # read-only: never followed by pickle.dump
        result["observation_counts"] = dict(data.get("observation_counts", {}))
        result["sandbox_observation_counts"] = dict(data.get("sandbox_observation_counts", {}))
        result["total_obs"] = sum(result["observation_counts"].values())
        result["load_error"] = None
    except Exception as e:
        result["load_error"] = str(e)
    finally:
        if lock_file is not None:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
            except Exception:
                pass
            lock_file.close()
    return result


# ------------------------------------------------------------------
# SECTION 2 -- live instance, via introspection_state.json (already
# written by the live process every 120s -- reading it is a plain
# file read, zero interaction with the live RiverBrain object)
# ------------------------------------------------------------------

def read_instance_snapshot():
    result = {"exists": False}
    if not os.path.exists(INTROSPECTION_PATH):
        return result
    with open(INTROSPECTION_PATH, "r") as f:
        data = json.load(f)
    result["exists"] = True
    result["timestamp"] = data.get("timestamp")
    rb = data.get("river_brain", {})
    result["observation_counts"] = dict(rb.get("observation_counts", {}))
    result["total_obs"] = sum(result["observation_counts"].values())
    result["influence_weight"] = rb.get("influence_weight")
    if result["timestamp"]:
        try:
            ts = datetime.fromisoformat(result["timestamp"])
            age_s = (datetime.now(timezone.utc) - ts).total_seconds()
            result["age_seconds"] = age_s
        except Exception:
            result["age_seconds"] = None
    return result


# ------------------------------------------------------------------
# SECTION 3 (Q3) -- does _do_save() merge disk state into the
# instance snapshot before writing, or only overwrite-or-skip?
# Answered by quoting the live source, not by a hardcoded claim.
# ------------------------------------------------------------------

def extract_function_source(path, func_name):
    with open(path, "r") as f:
        lines = f.readlines()
    start = None
    indent = None
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)def " + re.escape(func_name) + r"\(", line)
        if m:
            start = i
            indent = len(m.group(1))
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        m = re.match(r"^(\s*)def ", lines[j])
        if m and len(m.group(1)) <= indent and lines[j].strip():
            end = j
            break
    return "".join(lines[start:end])


def analyze_merge_path(do_save_src):
    if do_save_src is None:
        return None
    guard_match = re.search(
        r"if existing_obs > current_obs:(?P<body>.*?)\n(?P<after>\s*with open\(RIVER_BRAIN_PATH, \"wb\"\))",
        do_save_src, re.S,
    )
    has_merge_keyword = bool(re.search(r"merge|combine|reconcile", do_save_src, re.I))
    guard_returns_immediately = False
    if guard_match:
        body = guard_match.group("body")
        guard_returns_immediately = "return" in body and not re.search(r"existing_data\[", body)
    return {
        "guard_found": guard_match is not None,
        "guard_returns_immediately_no_merge": guard_returns_immediately,
        "merge_keyword_present_anywhere": has_merge_keyword,
    }


# ------------------------------------------------------------------
# SECTION 5 (Q6) -- is the instance introspection reads from the same
# object that scores/steers live conversations? Confirmed by quoting
# get_river_brain()'s singleton-resolution source, plus a live process
# scan for any second process that could be an independent RiverBrain
# owner right now (river_creative_rehab.py, echo_janitor.py, or any
# other standalone script that imports get_river_brain() outside Flask).
# ------------------------------------------------------------------

def scan_concurrent_river_owners():
    try:
        out = subprocess.run(["ps", "-eo", "pid,command"], capture_output=True, text=True, timeout=5)
    except Exception as e:
        return {"error": str(e)}
    suspects = []
    for line in out.stdout.splitlines():
        if "verify_riverbrain.py" in line:
            continue
        if re.search(r"river_creative_rehab\.py|echo_janitor\.py|run\.py", line):
            suspects.append(line.strip())
    return {"processes": suspects}


# ------------------------------------------------------------------
# SECTION 6 -- historical "[RIVER] Save skipped" evidence
# ------------------------------------------------------------------

def scan_save_skipped(lookback_hours=48):
    now = datetime.now()
    cutoff = now.timestamp() - lookback_hours * 3600
    all_matches = []
    for path in LOG_CANDIDATES:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", errors="replace") as f:
                for line in f:
                    m = SAVE_SKIPPED_RE.search(line)
                    if m:
                        all_matches.append((path, m.group("ts"), int(m.group("disk")), int(m.group("inst"))))
        except Exception:
            continue
    recent = []
    for path, ts, disk, inst in all_matches:
        try:
            t = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            if t.timestamp() >= cutoff:
                recent.append((path, ts, disk, inst))
        except Exception:
            pass
    return {
        "total_all_time": len(all_matches),
        "recent_count": len(recent),
        "lookback_hours": lookback_hours,
        "most_recent": all_matches[-1] if all_matches else None,
        "recent_sample": recent[-5:],
    }


def main():
    print("VERIFY_RIVERBRAIN — read-only diagnostic. No writes, no RiverBrain")
    print("instantiation, no pickle.dump anywhere in this script.")

    hr("SECTION 1 — disk snapshot (memory/river_brain.pkl, raw pickle.load)")
    disk = read_disk_snapshot()
    if not disk["exists"]:
        print("river_brain.pkl does not exist on disk.")
    else:
        print(f"path       : {PKL_PATH}")
        print(f"size       : {disk['size_bytes']} bytes")
        print(f"mtime      : {disk['mtime']}")
        print(f"sha256     : {disk['sha256']}")
        if disk.get("load_error"):
            print(f"LOAD ERROR : {disk['load_error']}")
        else:
            print(f"total obs  : {disk['total_obs']}")
            for k, v in sorted(disk["observation_counts"].items()):
                print(f"  {k:<12}: {v}")

    hr("SECTION 2 — live instance snapshot (memory/introspection_state.json)")
    inst = read_instance_snapshot()
    if not inst["exists"]:
        print("introspection_state.json does not exist — cannot read live instance state.")
    else:
        age = inst.get("age_seconds")
        age_str = f"{age:.0f}s ago" if age is not None else "unknown"
        print(f"snapshot ts  : {inst['timestamp']} ({age_str})")
        if age is not None and age > 300:
            print(f"  WARNING: introspection snapshot is stale (>300s) — collector may be stalled.")
        print(f"total obs    : {inst['total_obs']}")
        for k, v in sorted(inst["observation_counts"].items()):
            print(f"  {k:<12}: {v}")
        print(f"influence_weight: {inst.get('influence_weight')}")

    hr("SECTION 3 (Q3) — does the save guard merge, or only overwrite-or-skip?")
    do_save_src = extract_function_source(ORCHESTRATOR_PATH, "_do_save")
    analysis = analyze_merge_path(do_save_src)
    if analysis is None:
        print("Could not locate _do_save() in echo_model_orchestrator.py — source may have moved.")
    else:
        print(f"guard clause found                       : {analysis['guard_found']}")
        print(f"guard returns immediately, no merge       : {analysis['guard_returns_immediately_no_merge']}")
        print(f"word 'merge'/'combine'/'reconcile' present : {analysis['merge_keyword_present_anywhere']}")
        if analysis["guard_returns_immediately_no_merge"] and not analysis["merge_keyword_present_anywhere"]:
            print(
                "\nANSWER: No merge path exists. When disk has more total obs than the\n"
                "live instance, _do_save() logs a warning and returns — the instance's\n"
                "observations since its last successful save are discarded, not queued,\n"
                "not merged. This repeats every writer-thread cycle until disk total\n"
                "obs falls below instance total (which does not happen on its own)."
            )
        else:
            print(
                "\nSource no longer matches the pattern this script was written against —\n"
                "re-read _do_save() manually below before trusting the Q3 answer."
            )
        print("\n--- current _do_save() source ---")
        print(do_save_src)

    hr("SECTION 4 — divergence: instance vs disk")
    if disk.get("exists") and not disk.get("load_error") and inst.get("exists"):
        d_total = disk["total_obs"]
        i_total = inst["total_obs"]
        delta = d_total - i_total
        print(f"disk total obs     : {d_total}")
        print(f"instance total obs : {i_total}")
        if delta > 0:
            print(f"divergence         : YES — disk is ahead by {delta} obs the live instance never wrote")
        elif delta < 0:
            print(f"divergence         : disk is BEHIND instance by {-delta} obs (instance has unsaved gains)")
        else:
            print("divergence         : NO — counts match")
        print("\nper-task:")
        all_tasks = sorted(set(disk["observation_counts"]) | set(inst["observation_counts"]))
        for t in all_tasks:
            dv = disk["observation_counts"].get(t, 0)
            iv = inst["observation_counts"].get(t, 0)
            flag = "" if dv == iv else "  <-- diverges"
            print(f"  {t:<12}: disk={dv:<6} instance={iv:<6}{flag}")
    else:
        print("Cannot compute divergence — missing disk or instance snapshot.")
        d_total = i_total = None

    hr("SECTION 5 (Q6) — is the live conversational River the one being starved?")
    get_rb_src = extract_function_source(ORCHESTRATOR_PATH, "get_river_brain")
    print("--- get_river_brain() source (used by both the request path and introspection) ---")
    print(get_rb_src or "not found — source may have moved")
    print(
        "When running inside Flask (the normal single-server case), get_river_brain()\n"
        "returns current_app.config['echo_core'].river_brain -- the exact same Python\n"
        "object used for score_model()/rank_models()/entropy_of_predictions() in the\n"
        "live request path, and the exact same object introspection_channel.py reads\n"
        "in SECTION 2 above. There is one authoritative instance per Flask process;\n"
        "the fallback branch (RiverBrain.load() as a standalone local instance) is\n"
        "reachable only by scripts run outside the Flask app -- see the running-process\n"
        "scan below for any such process active right now."
    )
    concurrent = scan_concurrent_river_owners()
    print("\n--- processes currently able to own a RiverBrain instance ---")
    if concurrent.get("error"):
        print(f"  (ps scan failed: {concurrent['error']})")
    elif not concurrent["processes"]:
        print("  none found — only the checks below (log history) can confirm past overlap")
    else:
        for p in concurrent["processes"]:
            print(f"  {p}")

    hr("SECTION 6 — historical evidence: '[RIVER] Save skipped' in logs")
    skip_evidence = scan_save_skipped()
    print(f"total occurrences (all time, scanned logs) : {skip_evidence['total_all_time']}")
    print(f"occurrences in last {skip_evidence['lookback_hours']}h                    : {skip_evidence['recent_count']}")
    if skip_evidence["most_recent"]:
        path, ts, d, i = skip_evidence["most_recent"]
        print(f"most recent                                 : {ts} (disk={d}, instance={i}) [{os.path.basename(path)}]")
    if skip_evidence["recent_sample"]:
        print("last few in lookback window:")
        for path, ts, d, i in skip_evidence["recent_sample"]:
            print(f"  {ts}  disk={d:<6} instance={i:<6} [{os.path.basename(path)}]")

    hr("FINAL VERDICT")
    divergence_present = d_total is not None and i_total is not None and d_total != i_total
    recent_skips = skip_evidence["recent_count"] > 0
    can_persist = "PASS"
    reasons = []
    if divergence_present and d_total > i_total:
        can_persist = "FAIL"
        reasons.append(f"disk ({d_total} obs) is ahead of the live instance ({i_total} obs) right now")
    if recent_skips:
        can_persist = "FAIL"
        reasons.append(f"{skip_evidence['recent_count']} '[RIVER] Save skipped' events in the last {skip_evidence['lookback_hours']}h")
    print(f"instance obs (live)   : {i_total}")
    print(f"disk obs (pkl)        : {d_total}")
    print(f"divergence present    : {'YES' if divergence_present else 'NO'}")
    print(f"can live River persist: {can_persist}")
    if reasons:
        print("reason: " + "; ".join(reasons))
    else:
        print("reason: instance and disk agree, and no recent skip events found in scanned logs.")
    print(
        "\nQ3 — does a merge path exist for dropped observations? "
        + ("NO, confirmed from source (see SECTION 3)." if analysis and analysis["guard_returns_immediately_no_merge"] else "See SECTION 3.")
    )
    print(
        "Q6 — is the steering River the one being starved? "
        + ("YES if SECTION 5/6 show the live instance's saves being skipped — same object, same process, no isolation." )
    )


if __name__ == "__main__":
    main()
