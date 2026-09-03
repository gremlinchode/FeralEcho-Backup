#!/usr/bin/env python3
"""
Reproducible protocol-seal verification.

Computes SHA-256 over a protocol file's content from the start of the
file up to and including the line reading exactly `---FREEZE-BOUNDARY---`
(inclusive), avoiding circularity: the hash is computed over content that
does NOT include the hash value itself, since the hash line always
appears strictly after the boundary marker.

Usage:
    python scripts/verify_protocol_seal.py <path-to-protocol.md> [--expect <hash>]

With --expect, exits 0 only if the computed hash matches; without it,
just prints the computed hash (used once, at seal time, to generate the
value that then gets written into the protocol file itself).
"""

import argparse
import hashlib
import sys

BOUNDARY_MARKER = "---FREEZE-BOUNDARY---"


def compute_seal_hash(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    marker_index = content.find(BOUNDARY_MARKER)
    if marker_index == -1:
        raise ValueError(f"No {BOUNDARY_MARKER!r} marker found in {path!r} — cannot compute a seal hash.")
    sealed_content = content[: marker_index + len(BOUNDARY_MARKER)]
    return hashlib.sha256(sealed_content.encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--expect", default=None, help="Expected SHA-256; if given, exit 1 on mismatch.")
    args = parser.parse_args()

    computed = compute_seal_hash(args.path)
    print(f"protocol_sha256 = {computed}")

    if args.expect:
        if computed == args.expect:
            print("MATCH — protocol content is unchanged since sealing.")
            sys.exit(0)
        else:
            print(f"MISMATCH — expected {args.expect}, computed {computed}. "
                  f"The protocol file has been modified since it was sealed.")
            sys.exit(1)


if __name__ == "__main__":
    main()
