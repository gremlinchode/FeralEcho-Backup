#!/usr/bin/env python3
"""
Researcher control CLI for the preference-provenance experimental
harness (app/experiments/preference_provenance/).

Per the mission's Section 8: this is how a human explicitly inspects,
adopts, rejects, revises, expires, and resets experimental candidates.
No autonomous code path calls lifecycle.adopt()/retain() — this CLI, or
a human directly calling those functions from a Python shell, are the
only intended entry points for those two transitions in this
implementation pass.

Usage:
    python scripts/preference_experiment_cli.py list
    python scripts/preference_experiment_cli.py inspect <candidate_id>
    python scripts/preference_experiment_cli.py generate --text "..." --normalized "..." --origin J --actor "researcher:richie"
    python scripts/preference_experiment_cli.py adopt <candidate_id> --actor "researcher:richie" --reason "..."
    python scripts/preference_experiment_cli.py reject <candidate_id> --actor "researcher:richie" --reason "..."
    python scripts/preference_experiment_cli.py retain <candidate_id> --actor "researcher:richie" --reason "..."
    python scripts/preference_experiment_cli.py expire <candidate_id> --actor "researcher:richie" --reason "..."
    python scripts/preference_experiment_cli.py history <candidate_id>
    python scripts/preference_experiment_cli.py audit-log
    python scripts/preference_experiment_cli.py reset --reason "..." --confirm
"""

import argparse
import json
import sys

sys.path.insert(0, ".")

from app.experiments.preference_provenance import lifecycle, store  # noqa: E402
from app.experiments.preference_provenance.provenance import build_provenance_record  # noqa: E402
from app.experiments.preference_provenance.schema import ProvenanceOrigin  # noqa: E402


def cmd_list(args):
    candidates = store.load_candidates()
    if not candidates:
        print("No candidates.")
        return
    for c in candidates.values():
        print(f"{c.candidate_id}  status={c.status.value:10s}  rev={c.revision_index}  {c.normalized_representation!r}")


def cmd_inspect(args):
    candidates = store.load_candidates()
    c = candidates.get(args.candidate_id)
    if not c:
        print(f"No such candidate: {args.candidate_id}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(c.to_dict(), indent=2, default=str))


def cmd_history(args):
    history = store.load_candidate_history(args.candidate_id)
    if not history:
        print(f"No history for: {args.candidate_id}", file=sys.stderr)
        sys.exit(1)
    for c in history:
        print(f"rev={c.revision_index}  status={c.status.value}  notes={c.notes!r}")


def cmd_generate(args):
    prov = build_provenance_record(
        human_explicitly_suggested=args.human_suggested,
        present_in_prompt=args.present_in_prompt,
        retrieved_from_memory=args.retrieved_from_memory,
        generated_during_reflection=args.reflection_generated,
        origin_override=ProvenanceOrigin(args.origin) if args.origin else None,
        override_reason=args.override_reason or "",
    )
    candidate = lifecycle.generate_candidate(
        source_text=args.text,
        normalized_representation=args.normalized or args.text,
        provenance=prov,
        actor=args.actor,
    )
    print(f"Generated candidate {candidate.candidate_id} (status={candidate.status.value})")


def cmd_adopt(args):
    c = lifecycle.adopt(args.candidate_id, actor=args.actor, reason=args.reason, human_confirmation=True)
    print(f"Adopted {c.candidate_id} (rev={c.revision_index})")


def cmd_reject(args):
    c = lifecycle.reject(args.candidate_id, actor=args.actor, reason=args.reason)
    print(f"Rejected {c.candidate_id} (rev={c.revision_index})")


def cmd_retain(args):
    c = lifecycle.retain(args.candidate_id, actor=args.actor, reason=args.reason, human_confirmation=True)
    print(f"Retained {c.candidate_id} (rev={c.revision_index})")


def cmd_expire(args):
    c = lifecycle.expire(args.candidate_id, actor=args.actor, reason=args.reason)
    print(f"Expired {c.candidate_id} (rev={c.revision_index})")


def cmd_audit_log(args):
    for event in store.load_audit_log():
        print(json.dumps(event))


def cmd_reset(args):
    if not args.confirm:
        print("Refusing to reset without --confirm.", file=sys.stderr)
        sys.exit(1)
    result = store.reset_experiment(reason=args.reason, actor="researcher_cli")
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list").set_defaults(func=cmd_list)

    p = sub.add_parser("inspect")
    p.add_argument("candidate_id")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("history")
    p.add_argument("candidate_id")
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("generate")
    p.add_argument("--text", required=True)
    p.add_argument("--normalized", default=None)
    p.add_argument("--actor", required=True)
    p.add_argument("--human-suggested", action="store_true", dest="human_suggested")
    p.add_argument("--present-in-prompt", action="store_true", dest="present_in_prompt")
    p.add_argument("--retrieved-from-memory", action="store_true", dest="retrieved_from_memory")
    p.add_argument("--reflection-generated", action="store_true", dest="reflection_generated")
    p.add_argument("--origin", default=None, help="Override letter A-L")
    p.add_argument("--override-reason", default=None)
    p.set_defaults(func=cmd_generate)

    for name, fn in (("adopt", cmd_adopt), ("reject", cmd_reject), ("retain", cmd_retain), ("expire", cmd_expire)):
        p = sub.add_parser(name)
        p.add_argument("candidate_id")
        p.add_argument("--actor", required=True)
        p.add_argument("--reason", required=True)
        p.set_defaults(func=fn)

    sub.add_parser("audit-log").set_defaults(func=cmd_audit_log)

    p = sub.add_parser("reset")
    p.add_argument("--reason", required=True)
    p.add_argument("--confirm", action="store_true")
    p.set_defaults(func=cmd_reset)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
