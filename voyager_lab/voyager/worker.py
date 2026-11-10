"""One mission process. Exit 75 when the world interrupts the process."""

import argparse
import json
import sys
from pathlib import Path

from voyager.baseline import run_baseline
from voyager.engine import run_engine
from voyager.world import ProcessInterrupt

HIDDEN = {"grade", "world", "success_check", "tags"}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=("baseline", "engine"))
    parser.add_argument("--brief", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--record", required=True)
    parser.add_argument("--lessons", required=True)
    parser.add_argument("--lessons-enabled", required=True, choices=("0", "1"))
    args = parser.parse_args(argv)
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    leaked = HIDDEN.intersection(brief)
    if leaked:
        print("brief contains hidden fields: " + ",".join(sorted(leaked)), file=sys.stderr)
        return 2
    lessons = json.loads(Path(args.lessons).read_text(encoding="utf-8"))
    try:
        if args.arm == "baseline":
            run_baseline(brief, args.root, args.record)
        else:
            run_engine(brief, args.root, args.record, lessons, args.lessons_enabled == "1")
    except ProcessInterrupt:
        return 75
    return 0


if __name__ == "__main__":
    sys.exit(main())
