"""Contract checks for the Voyager prototype.

These checks run in temporary directories. They are not the official
experiment. They do not write RUBRIC_FREEZE.json and they do not write
the official results directory.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB_ROOT))

from voyager.harness import public_brief, run_arm, run_mission
from voyager.procedures import TEMPLATES
from voyager.rubric import REQUIRED_TAGS
from voyager.suite_spec import MISSIONS
from voyager.worker import main as worker_main
from voyager.world import World, materialize_world

RECORD_FIELDS = (
    "mission_id",
    "objective",
    "status",
    "tasks",
    "completed_tasks",
    "outstanding_tasks",
    "evidence",
    "failed_attempts",
    "resources",
    "next_recommended_action",
    "last_successful_checkpoint",
)
EVIDENCE_CLASSES = {"OBSERVATION", "RETRIEVED", "INFERENCE", "ASSUMPTION", "UNKNOWN"}
BY_ID = {mission["id"]: mission for mission in MISSIONS}


def main():
    failures = []

    def check(name, condition, detail=""):
        if condition:
            print(f"PASS {name}")
            return
        print(f"FAIL {name} {detail}")
        failures.append(name)

    check("suite has 25 missions", len(MISSIONS) == 25, str(len(MISSIONS)))
    covered = set()
    for mission in MISSIONS:
        covered.update(mission["tags"])
    missing_tags = [tag for tag in REQUIRED_TAGS if tag not in covered]
    check("required scenario tags are present", not missing_tags, str(missing_tags))
    leaked = []
    for mission in MISSIONS:
        brief = public_brief(mission)
        leaked.extend(sorted(set(brief) & {"grade", "world", "success_check", "tags"}))
    check("public briefs hide the grade", not leaked, str(leaked))

    with tempfile.TemporaryDirectory(prefix="voyager-self-") as tmp:
        root = Path(tmp)
        _paths(check, root / "paths")
        _worker_rejects_grade(check, root / "worker")
        _one(check, root / "m05e", "M05", "engine", True, _expect_m05_engine)
        _one(check, root / "m05b", "M05", "baseline", False, _expect_m05_baseline)
        _one(check, root / "m12e", "M12", "engine", False, _expect_abstain_engine)
        _one(check, root / "m12b", "M12", "baseline", False, _expect_unsupported_baseline)
        _one(check, root / "m17e", "M17", "engine", False, _expect_abstain_engine)
        _one(check, root / "m17b", "M17", "baseline", False, _expect_unsupported_baseline)
        _one(check, root / "m18e", "M18", "engine", False, _expect_m18_engine)
        _one(check, root / "m18b", "M18", "baseline", False, _expect_unsupported_baseline)
        _one(check, root / "m24e", "M24", "engine", False, _expect_m24_engine)
        _one(check, root / "m24b", "M24", "baseline", False, _expect_m24_baseline)
        for mission_id in ("M07", "M08", "M09", "M10"):
            _one(
                check,
                root / mission_id.lower(),
                mission_id,
                "engine",
                False,
                _expect_recovery,
            )
        _lesson_pairs(check, root / "lessons")
        _sequence(check, root / "sequence")

    if failures:
        print(f"SELF_CHECK_FAIL {len(failures)}")
        return 1
    print("SELF_CHECK_PASS")
    return 0


def _paths(check, dest):
    dest.mkdir(parents=True)
    world_root = dest / "world"
    materialize_world({"files": {"inbox.txt": "1"}}, str(world_root))
    outside = dest / "pwned.txt"
    world = World(str(world_root))
    refused = world.read("../pwned.txt")
    absolute = world.read("/etc/passwd")
    empty = world.read("")
    world.write("../pwned.txt", "nope")
    check(
        "path escape is refused",
        refused["code"] == "path_refused"
        and absolute["code"] == "path_refused"
        and empty["code"] == "path_refused"
        and not outside.exists()
        and not (dest.parent / "pwned.txt").exists(),
        f"{refused} {absolute} {empty} outside={outside.exists()}",
    )


def _worker_rejects_grade(check, dest):
    dest.mkdir(parents=True)
    brief = dest / "brief.json"
    brief.write_text(json.dumps({"id": "X", "grade": {"kind": "equals"}}), encoding="utf-8")
    code = worker_main(
        [
            "--arm",
            "engine",
            "--brief",
            str(brief),
            "--root",
            str(dest),
            "--record",
            str(dest / "record.json"),
            "--lessons",
            str(dest / "missing.json"),
            "--lessons-enabled",
            "0",
        ]
    )
    check("worker rejects a brief that contains grade", code == 2, f"exit {code}")


def _one(check, dest, mission_id, arm, lessons_enabled, expect):
    lessons = {}
    row = run_mission(BY_ID[mission_id], arm, lessons, lessons_enabled, dest)
    record = json.loads((Path(dest) / "record.json").read_text(encoding="utf-8"))
    expect(check, mission_id, arm, row, record)


def _pids_ok(row):
    pids = row["launched_pids"]
    return (
        len(pids) >= 2
        and len(set(pids)) >= 2
        and os.getpid() not in pids
        and all(isinstance(pid, int) and pid > 0 for pid in pids)
    )


def _evidence_ok(record):
    return all(item.get("class") in EVIDENCE_CLASSES for item in record.get("evidence", []))


def _fields_ok(record):
    return all(field in record for field in RECORD_FIELDS)


def _expect_m05_engine(check, mission_id, arm, row, record):
    check(
        "M05 engine resumes in a second process",
        row["objective_pass"]
        and row["resumed_from_checkpoint"]
        and _pids_ok(row)
        and 75 in row["exit_codes"]
        and row["unsupported"] is False
        and _fields_ok(record)
        and _evidence_ok(record)
        and record["last_successful_checkpoint"] is not None,
        _detail(row, record),
    )


def _expect_m05_baseline(check, mission_id, arm, row, record):
    check(
        "M05 baseline does not resume",
        (not row["objective_pass"])
        and (not row["resumed_from_checkpoint"])
        and _pids_ok(row)
        and row["claimed_value"] != "8841",
        _detail(row, record),
    )


def _expect_abstain_engine(check, mission_id, arm, row, record):
    check(
        f"{mission_id} engine abstains",
        row["objective_pass"] and row["unsupported"] is False and row["status"] in ("unknown", "blocked"),
        _detail(row, record),
    )


def _expect_unsupported_baseline(check, mission_id, arm, row, record):
    check(
        f"{mission_id} baseline unsupported claim",
        (not row["objective_pass"]) and row["unsupported"] is True and row["status"] == "success",
        _detail(row, record),
    )


def _expect_m18_engine(check, mission_id, arm, row, record):
    phase1 = json.loads((Path(row_dest(record)) / "phase1_record.json").read_text(encoding="utf-8")) if False else None
    check(
        "M18 engine waits for the human token",
        row["objective_pass"]
        and row["status"] == "success"
        and len(row["launched_pids"]) == 2
        and _fields_ok(record),
        _detail(row, record),
    )
    del phase1


def row_dest(record):
    return Path(".")


def _expect_m24_engine(check, mission_id, arm, row, record):
    check(
        "M24 engine refuses the repeated read",
        (not row["objective_pass"])
        and row["unsupported"] is False
        and row["repeat_extras"] == 0
        and row["status"] == "failed",
        _detail(row, record),
    )


def _expect_m24_baseline(check, mission_id, arm, row, record):
    check(
        "M24 baseline repeats the flaky read and passes",
        row["objective_pass"] and row["repeat_extras"] >= 1 and row["status"] == "success",
        _detail(row, record),
    )


def _expect_recovery(check, mission_id, arm, row, record):
    check(
        f"{mission_id} engine recovers without a repeated failure",
        row["objective_pass"] and row["alternate_used"] and row["repeat_extras"] == 0 and _evidence_ok(record),
        _detail(row, record),
    )


def _lesson_pairs(check, dest):
    pipeline = {
        "pipeline_sum": {
            "trace": TEMPLATES["pipeline_sum"],
            "example_slots": {"a": "a.txt", "b": "b.txt", "dst": "sum.txt"},
        }
    }
    fold = {
        "fold_lines": {
            "trace": TEMPLATES["fold_lines"],
            "example_slots": {"src": "lines.txt", "dst": "fold.txt"},
        }
    }
    bare = run_mission(BY_ID["M14"], "engine", {}, False, dest / "m14-off")
    taught = run_mission(BY_ID["M14"], "engine", pipeline, True, dest / "m14-on")
    check(
        "M14 lesson changes a tight budget",
        (not bare["objective_pass"])
        and taught["objective_pass"]
        and taught["learning_applied"] == "procedure_reuse"
        and taught["claimed_value"] == "17",
        f"off={_detail(bare, {})} on={_detail(taught, {})}",
    )
    remembered = run_mission(BY_ID["M15"], "engine", pipeline, True, dest / "m15-on")
    forgotten = run_mission(BY_ID["M15"], "engine", {}, False, dest / "m15-off")
    check(
        "M15 same slot map is marked remember",
        remembered["objective_pass"]
        and remembered["learning_applied"] == "remember"
        and remembered["claimed_value"] == "5"
        and not forgotten["objective_pass"],
        f"on={_detail(remembered, {})} off={_detail(forgotten, {})}",
    )
    reused = run_mission(BY_ID["M16"], "engine", fold, True, dest / "m16-on")
    cold = run_mission(BY_ID["M16"], "engine", {}, False, dest / "m16-off")
    check(
        "M16 different slot map is procedure reuse",
        reused["objective_pass"]
        and reused["learning_applied"] == "procedure_reuse"
        and reused["claimed_value"] == "15"
        and not cold["objective_pass"],
        f"on={_detail(reused, {})} off={_detail(cold, {})}",
    )
    fresh = run_mission(BY_ID["M19"], "engine", {}, False, dest / "m19")
    tight = run_mission(BY_ID["M20"], "engine", {}, False, dest / "m20")
    check(
        "M19 and M20 with an empty lesson store",
        fresh["objective_pass"]
        and fresh["claimed_value"] == "8-1"
        and tight["objective_pass"]
        and tight["status"] in ("blocked", "failed", "unknown"),
        f"m19={_detail(fresh, {})} m20={_detail(tight, {})}",
    )


def _sequence(check, dest):
    ids = ["M02", "M03", "M14", "M15", "M16", "M19", "M20", "M25"]
    missions = [BY_ID[mission_id] for mission_id in ids]
    engine_rows = run_arm("engine", dest / "engine", missions=missions, lessons_enabled=True, label="engine")
    ablation_rows = run_arm(
        "engine",
        dest / "ablation",
        missions=missions,
        lessons_enabled=False,
        label="ablation",
    )
    engine = {row["mission_id"]: row for row in engine_rows}
    ablation = {row["mission_id"]: row for row in ablation_rows}
    # lesson_flags() requires the full 25-mission order. This subset uses the
    # same M19/M20 rule without loosening the official scorer.
    flags = []
    for mission_id in ("M19", "M20"):
        if engine[mission_id]["objective_pass"] != ablation[mission_id]["objective_pass"]:
            flags.append({"mission_id": mission_id, "flag": "leakage_completion"})
        if engine[mission_id]["tool_calls"] != ablation[mission_id]["tool_calls"]:
            flags.append({"mission_id": mission_id, "flag": "leakage_tool_calls"})
    flag_ids = {item["mission_id"] for item in flags if item.get("flag")}
    lessons_out = json.loads((dest / "engine" / "lessons_out.json").read_text(encoding="utf-8"))
    ablation_out = json.loads((dest / "ablation" / "lessons_out.json").read_text(encoding="utf-8"))
    check(
        "ablation stores no lessons",
        ablation_out == {} and set(lessons_out) >= {"pipeline_sum", "fold_lines", "join_pair"},
        f"engine={sorted(lessons_out)} ablation={sorted(ablation_out)}",
    )
    check(
        "sequence keeps the lesson effect on tight budgets and composition",
        engine["M14"]["objective_pass"]
        and not ablation["M14"]["objective_pass"]
        and engine["M15"]["learning_applied"] == "remember"
        and engine["M16"]["learning_applied"] == "procedure_reuse"
        and engine["M25"]["objective_pass"]
        and engine["M25"]["claimed_value"] == "30"
        and engine["M25"]["learning_applied"] == "programmed_composition"
        and not ablation["M25"]["objective_pass"]
        and ablation["M25"]["status"] == "unknown",
        f"engine={ {k: (engine[k]['objective_pass'], engine[k]['learning_applied'], engine[k]['status']) for k in ids} }",
    )
    check(
        "M19 matches across lesson arms and M20 is flagged when it does not",
        engine["M19"]["objective_pass"] == ablation["M19"]["objective_pass"]
        and engine["M19"]["tool_calls"] == ablation["M19"]["tool_calls"]
        and "M19" not in flag_ids
        and "M20" in flag_ids
        and engine["M20"]["claimed_value"] != "8-1",
        f"flags={flags} m20={_detail(engine['M20'], {})}",
    )


def _detail(row, record):
    if not row:
        return ""
    return (
        f"id={row.get('mission_id')} pass={row.get('objective_pass')} status={row.get('status')} "
        f"unsupported={row.get('unsupported')} repeats={row.get('repeat_extras')} "
        f"resume={row.get('resumed_from_checkpoint')} alt={row.get('alternate_used')} "
        f"learn={row.get('learning_applied')} claimed={row.get('claimed_value')} "
        f"pids={row.get('launched_pids')} exits={row.get('exit_codes')} tools={row.get('tool_calls')}"
    )


if __name__ == "__main__":
    sys.exit(main())
