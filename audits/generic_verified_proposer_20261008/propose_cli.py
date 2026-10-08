"""Source-only proposal CLI; no retained state, oracle, writes or candidate launch."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from b_prototype.contracts import strict_json
from b_prototype.proposer import propose


def main():
    data = sys.stdin.buffer.read(16385)
    if len(data) > 16384:
        raise ValueError("request exceeds 16 KiB")
    request = strict_json(data.decode("utf-8"))
    if type(request) is not dict or set(request) != {"source", "contract"}:
        raise ValueError("request permits source and current contract only")
    if type(request["source"]) is not str or type(request["contract"]) is not dict:
        raise ValueError("invalid request types")
    print(json.dumps(propose(request["source"], request["contract"]), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        print(json.dumps({"error": type(error).__name__, "detail": str(error)}))
        raise SystemExit(2)
