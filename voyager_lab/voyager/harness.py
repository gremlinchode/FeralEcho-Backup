"""Parent harness. Grades from the world. Launches a real second process."""

import copy
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from voyager.atomic import atomic_write
from voyager.grader import evaluate
from voyager.procedures import TEMPLATES
from voyager.suite_spec import MISSIONS
from voyager.world import materialize_world, plant_human_token

LAB_ROOT = Path(__file__).resolve().parents[1]
HIDDEN = {"grade", "world", "success_check", "tags"}
MAX_PROCESSES = 3


def public_brief(mission):
    brief = {
        "id": mission["id"],
        "objective": mission["objective"],
        "problem_class": mission["problem_class"],
        "budget": mission["budget"],
        "slots": mission["slots"],
    }
    if mission.get("hypothesis_class"):
        brief["hypothesis_class"] = mission["hypothesis_class"]
    return brief


def _child_env():
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPATH": str(LAB_ROOT),
    }
    lang = os.environ.get("LANG")
    if lang:
        env["LANG"] = lang
    return env


def _launch(arm, brief_path, root, record_path, lessons_path, lessons_enabled):
    cmd = [
        sys.executable,
        "-m",
        "voyager.worker",
        "--arm",
        "baseline" if arm == "baseline" else "engine",
        "--brief",
        str(brief_path),
        "--root",
        str(root),
        "--record",
        str(record_path),
        "--lessons",
        str(lessons_path),
        "--lessons-enabled",
        "1" if lessons_enabled else "0",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(LAB_ROOT),
        env=_child_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    pid = proc.pid
    try:
        stdout, stderr = proc.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        raise RuntimeError(f"worker timeout arm={arm} pid={pid}\n{stderr}\n{stdout}") from None
    if proc.returncode not in (0, 75):
        raise RuntimeError(
            f"worker exit {proc.returncode} arm={arm} pid={pid}\n{stderr}\n{stdout}"
        )
    return proc.returncode, pid


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_mission(mission, arm, lessons, lessons_enabled, dest, label=None):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    root = dest / "world"
    record_path = dest / "record.json"
    brief = public_brief(mission)
    if HIDDEN.intersection(brief):
        raise RuntimeError("public brief leaked a hidden field")
    atomic_write(str(dest / "brief_given.json"), json.dumps(brief, indent=2, sort_keys=True))
    atomic_write(str(dest / "lessons_in.json"), json.dumps(lessons, indent=2, sort_keys=True))
    materialize_world(mission["world"], str(root))
    codes = []
    pids = []
    phase1 = None
    started = time.perf_counter()
    two_phase = mission["grade"]["kind"] == "two_phase"
    while len(pids) < MAX_PROCESSES:
        code, pid = _launch(
            arm,
            dest / "brief_given.json",
            root,
            record_path,
            dest / "lessons_in.json",
            lessons_enabled,
        )
        codes.append(code)
        pids.append(pid)
        if code == 75:
            continue
        if two_phase and phase1 is None:
            record = _load(record_path)
            rel = mission["grade"]["path"]
            phase1 = {"record": record, "exists": (root / rel).is_file()}
            atomic_write(str(dest / "phase1_record.json"), json.dumps(record, indent=2, sort_keys=True))
            plant_human_token(str(root))
            continue
        break
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    record = _load(record_path)
    graded = evaluate(mission, record, root, phase1=phase1)
    row = {
        "mission_id": mission["id"],
        "arm": label or arm,
        "objective_pass": graded["objective_pass"],
        "unsupported": graded["unsupported"],
        "contradictions": graded["contradictions"],
        "repeat_extras": graded["repeat_extras"],
        "alternate_used": graded["alternate_used"],
        "resumed_from_checkpoint": graded["resumed_from_checkpoint"],
        "learning_applied": graded["learning_applied"],
        "plan_source": graded["plan_source"],
        "status": graded["status"],
        "claimed_value": graded["claimed_value"],
        "tool_calls": graded["tool_calls_record"],
        "ru_maxrss": graded["ru_maxrss"],
        "elapsed_ms": round(elapsed_ms, 3),
        "launched_pids": pids,
        "exit_codes": codes,
        "tags": list(mission["tags"]),
    }
    atomic_write(str(dest / "grade.json"), json.dumps(row, indent=2, sort_keys=True))
    meta = {"launched_pids": pids, "exit_codes": codes, "elapsed_ms": row["elapsed_ms"]}
    atomic_write(str(dest / "harness_meta.json"), json.dumps(meta, indent=2, sort_keys=True))
    return row


def run_arm(arm, dest_root, missions=None, lessons_enabled=None, label=None):
    """Run one arm.

    arm is the controller: "baseline" or "engine".
    lessons_enabled defaults to True only for the engine controller.
    The no-lesson ablation is arm="engine" with lessons_enabled=False.
    That ablation does not update the lesson store.
    """
    if arm not in ("baseline", "engine"):
        raise ValueError(arm)
    if lessons_enabled is None:
        lessons_enabled = arm == "engine"
    if arm == "baseline":
        lessons_enabled = False
    if label is None:
        if arm == "baseline":
            label = "baseline"
        elif lessons_enabled:
            label = "engine"
        else:
            label = "ablation"
    missions = list(MISSIONS if missions is None else missions)
    dest_root = Path(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)
    lessons = {}
    rows = []
    for mission in missions:
        row = run_mission(
            mission,
            arm,
            lessons if lessons_enabled else {},
            lessons_enabled,
            dest_root / mission["id"],
            label=label,
        )
        rows.append(row)
        problem_class = mission["problem_class"]
        if (
            lessons_enabled
            and row["objective_pass"]
            and problem_class in TEMPLATES
            and problem_class not in lessons
        ):
            lessons[problem_class] = {
                "trace": copy.deepcopy(TEMPLATES[problem_class]),
                "example_slots": copy.deepcopy(mission["slots"]),
            }
    atomic_write(
        str(dest_root / "lessons_out.json"),
        json.dumps(lessons, indent=2, sort_keys=True),
    )
    return rows
