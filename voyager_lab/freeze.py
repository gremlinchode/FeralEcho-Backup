"""Lock the scoring inputs before an official arm.

Hashes the controller, the suite, the rubric, and the harness.
Does not hash this file or run_experiment.py.
Refuses to rewrite an existing lock.
"""

import hashlib
import json
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent
FREEZE_PATH = LAB_ROOT / "RUBRIC_FREEZE.json"

HASHED = [
    "voyager/atomic.py",
    "voyager/suite_spec.py",
    "voyager/rubric.py",
    "voyager/procedures.py",
    "voyager/engine.py",
    "voyager/baseline.py",
    "voyager/grader.py",
    "voyager/world.py",
    "voyager/harness.py",
    "voyager/worker.py",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def collect() -> dict:
    files = {}
    for rel in HASHED:
        path = LAB_ROOT / rel
        files[rel] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
    blob = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "bundle_sha256": hashlib.sha256(blob).hexdigest(),
        "hashed_files": files,
        "note": "Written before any official arm. Scoring is not revised after results.",
    }


def verify() -> dict:
    if not FREEZE_PATH.exists():
        raise SystemExit("RUBRIC_FREEZE.json is missing")
    locked = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    current = collect()
    mismatches = []
    for rel, meta in locked["hashed_files"].items():
        now = current["hashed_files"].get(rel)
        if now is None or now["sha256"] != meta["sha256"]:
            mismatches.append(rel)
    extra = sorted(set(current["hashed_files"]) - set(locked["hashed_files"]))
    if mismatches or extra or locked.get("bundle_sha256") != current["bundle_sha256"]:
        raise SystemExit(f"freeze mismatch mismatches={mismatches} extra={extra}")
    return locked


def write_freeze() -> dict:
    if FREEZE_PATH.exists():
        raise SystemExit("RUBRIC_FREEZE.json already exists; refuse to rewrite")
    payload = collect()
    FREEZE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main(argv) -> int:
    if "--write" in argv:
        payload = write_freeze()
        print(f"FREEZE_WRITTEN {payload['bundle_sha256']}")
        return 0
    payload = verify()
    print(f"FREEZE_OK {payload['bundle_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
