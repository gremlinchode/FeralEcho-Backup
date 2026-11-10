#!/usr/bin/env python3
"""Load the rebuilt copy in a fresh process and test the existing identity gate.

Search uses VectorMemory.search. Candidate selection uses
conversation_service.retrieve_memory_context. Neither call imports
memory_bridge, posts to the listener, or opens the live index.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone

ROOT = "/Users/richietate/Desktop/FeralEcho"
DIAG = os.path.dirname(os.path.abspath(__file__))
REBUILT = os.path.join(DIAG, "rebuilt")
INDEX_PATH = os.path.join(REBUILT, "faiss.index")
META_PATH = os.path.join(REBUILT, "memory_meta.json")
SIDE_PATH = INDEX_PATH + ".identity.json"
ITEMS_PATH = (
    "/Users/richietate/Desktop/FeralEcho-voyager/voyager_lab/"
    "evidence_to_answer_2026-11/items.json"
)
PHASE2_PATH = (
    "/Users/richietate/Desktop/FeralEcho-voyager/voyager_lab/"
    "evidence_to_answer_2026-11/results_phase2.jsonl"
)
LIVE_INDEX = os.path.join(ROOT, "memory", "faiss.index")
LIVE_META = os.path.join(ROOT, "memory", "memory_meta.json")
LIVE_SIDE = os.path.join(ROOT, "memory", "faiss.index.identity.json")
OUT_PATH = os.path.join(DIAG, "search_results.json")
NONCE = (
    "feralecho-copy-diagnostic-nonce-9f3c1a "
    "this string is not a stored memory"
)
ECHO_03 = "67eccddb-cb98-4373-b206-aceed4712b62"
EXPECTED = {
    "01": ("5e6ac8a9-19c1-4fcd-b08e-dd7c0f5e659b", "5aeece192c0e"),
    "02": ("aded2053-b5d9-42d5-a106-aa3773f60ea5", "f6e677371d0d"),
    "03": ("36495cc5-39f3-4a31-a79b-332dc52da1ae", "254ada88570e"),
    "04": ("90e3838a-c12d-4a28-a653-b5de13471e0e", "e71037e8fcdc"),
    "05": ("accc4c1e-ef05-466f-8ef2-4f1b997166f8", "02d0c62ade8b"),
    "06": ("c86b2d32-5438-4c52-b7ae-df291cca4db2", "31bc63a1affe"),
    "07": ("2dd6c6ec-1afe-47e6-9739-883eb12efc98", "3c63d277f342"),
    "08": ("1f366a17-832a-4eb0-a5e4-0458f1d85fde", "4ba1c6a1d6a0"),
    "09": ("0192ec01-8404-4f02-a2ce-c8dc4c53f848", "72040f561398"),
    "10": ("dd44ed20-1acb-4951-8335-33437b6947d3", "479cfd462810"),
}

sys.path.insert(0, ROOT)


def log(msg: str) -> None:
    print(msg, flush=True)


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_hash12(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:12]


def live_fingerprint() -> dict:
    out = {}
    for name, path in (("index", LIVE_INDEX), ("meta", LIVE_META)):
        st = os.stat(path)
        out[name] = {"inode": st.st_ino, "size": st.st_size, "mtime_ns": st.st_mtime_ns}
    out["sidecar_exists"] = os.path.exists(LIVE_SIDE)
    return out


def main() -> int:
    for path in (INDEX_PATH, META_PATH, SIDE_PATH):
        if not os.path.isfile(path):
            log(f"SEARCH_FAIL missing {path}")
            return 2
    if os.path.commonpath([os.path.abspath(INDEX_PATH), DIAG]) != DIAG:
        log("SEARCH_FAIL rebuilt path escaped the diagnostic directory")
        return 2

    before = live_fingerprint()
    log(f"LIVE_BEFORE {json.dumps(before)}")

    import numpy as np
    from app.core.conversation_service import retrieve_memory_context
    import app.core.conversation_service as conversation_service
    from app.core.sentence_transformer_singleton import get_sentence_transformer
    from app.lib.vector_memory import VectorMemory, binding_sha256

    refused: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            message = record.getMessage()
            if "search refused" in message:
                refused.append(message)

    logging.basicConfig(level=logging.INFO)
    logging.getLogger().addHandler(_Capture())

    vm = VectorMemory(dim=384, index_path=INDEX_PATH, meta_path=META_PATH)
    index_sha = sha256_file(INDEX_PATH)
    with open(SIDE_PATH, "r", encoding="utf-8") as handle:
        sidecar = json.load(handle)
    order = sidecar.get("id_order")
    binding_ok = (
        isinstance(order, list)
        and binding_sha256(index_sha, order) == sidecar.get("binding_sha256")
        and sidecar.get("index_sha256") == index_sha
        and sidecar.get("schema") == 1
    )
    identity = {
        "fresh_process_identity_status": vm.identity_status,
        "fresh_process_identity_verified": bool(vm.identity_verified),
        "ntotal": int(vm.index.ntotal) if vm.index is not None else None,
        "id_order_len": len(vm.id_order),
        "sidecar_schema": sidecar.get("schema"),
        "sidecar_index_sha256": sidecar.get("index_sha256"),
        "recomputed_index_sha256": index_sha,
        "index_hash_matches_sidecar": sidecar.get("index_sha256") == index_sha,
        "binding_sha256_matches": binding_ok,
        "authoritative_flag_after_load": bool(vm._identity_authoritative),
        "gate_weakened": False,
    }
    log(
        "IDENTITY "
        f"status={vm.identity_status} verified={vm.identity_verified} "
        f"binding_ok={binding_ok}"
    )
    if vm.identity_status != "manifest_valid" or not vm.identity_verified or not binding_ok:
        payload = {
            "outcome": "BLOCKED",
            "reason": "fresh-process load did not validate the sidecar",
            "identity": identity,
            "search_refused": refused,
            "live_before": before,
            "live_after": live_fingerprint(),
        }
        with open(OUT_PATH, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        log("SEARCH_BLOCKED")
        return 2

    owners: dict[str, list[str]] = {}
    for item_id, record in vm.meta.items():
        text = record.get("text") if isinstance(record, dict) else None
        if isinstance(text, str):
            owners.setdefault(text, []).append(item_id)

    with open(ITEMS_PATH, "r", encoding="utf-8") as handle:
        items = {row["id"]: row for row in json.load(handle)["items"]}
    clocks = {}
    with open(PHASE2_PATH, "r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            clocks[row["item_id"]] = row["started_at"]

    model = get_sentence_transformer("all-MiniLM-L6-v2")

    def embed(text: str) -> np.ndarray:
        vecs = model.encode([text], normalize_embeddings=True, show_progress_bar=False)
        return np.array(vecs, dtype=np.float32)

    def annotate(hits: list) -> list[dict]:
        rows = []
        for rank, (text, score, meta) in enumerate(hits, start=1):
            found = owners.get(text, [])
            rows.append({
                "rank": rank,
                "score": score,
                "text_hash12": text_hash12(text) if isinstance(text, str) else None,
                "owner_ids": found,
                "unique_owner": found[0] if len(found) == 1 else None,
                "ambiguous": len(found) != 1,
                "timestamp": meta.get("timestamp") if isinstance(meta, dict) else None,
                "memory_source": meta.get("memory_source") if isinstance(meta, dict) else None,
                "role": meta.get("role") if isinstance(meta, dict) else None,
            })
        return rows

    class FrozenDateTime(datetime):
        frozen = None

        @classmethod
        def now(cls, tz=None):
            current = cls.frozen
            if current is None:
                raise RuntimeError("diagnostic clock was not set")
            if tz is None:
                return current
            return current.astimezone(tz)

    conversation_service.datetime = FrozenDateTime

    def search_fn(message: str, k: int):
        return vm.search(embed(message), k)

    facts = []
    for item_id in [f"{n:02d}" for n in range(1, 11)]:
        user_id, expected_hash = EXPECTED[item_id]
        record = vm.meta.get(user_id)
        stored_text = record.get("text") if isinstance(record, dict) else None
        stored_hash = text_hash12(stored_text) if isinstance(stored_text, str) else None
        position = vm.id_order.index(user_id) if user_id in vm.id_order else None
        prompt = items[item_id]["phase2_prompt"]
        clock = clocks[item_id]
        raw = annotate(search_fn(prompt, 15))
        matched_rows = [
            row for row in raw
            if row["unique_owner"] == user_id and row["text_hash12"] == expected_hash
        ]
        ambiguous_rows = [
            row for row in raw
            if user_id in row["owner_ids"] and row["ambiguous"]
        ]
        FrozenDateTime.frozen = datetime.fromisoformat(clock)
        provenance: dict = {}
        injected_text = retrieve_memory_context(
            prompt,
            search_fn,
            k=5,
            exclude_recent_minutes=30.0,
            provenance_out=provenance,
        )
        injected = provenance.get("injected", [])
        injected_hashes = [row.get("text_hash") for row in injected]
        hash_injected = expected_hash in injected_hashes
        identity_ok = identity["fresh_process_identity_verified"] is True
        search_reached = identity_ok and not refused
        candidate_ok = bool(matched_rows) and not ambiguous_rows
        if not identity_ok:
            demonstrated = "could not be tested"
        elif candidate_ok and hash_injected and stored_hash == expected_hash:
            demonstrated = "demonstrated"
        else:
            demonstrated = "failed"
        facts.append({
            "item_id": item_id,
            "user_id": user_id,
            "expected_hash12": expected_hash,
            "stored_text_equals_phase1_prompt": stored_text == items[item_id]["phase1_prompt"],
            "stored_hash12": stored_hash,
            "storage_ok": stored_hash == expected_hash and isinstance(record, dict),
            "identity_validation_passed": identity_ok,
            "index_membership_position": position,
            "index_membership_ok": position is not None and position < identity["ntotal"],
            "clock_started_at": clock,
            "search_k": 15,
            "search_reached_index": search_reached,
            "raw_hits": raw,
            "correct_user_id_returned": candidate_ok,
            "correct_rank": matched_rows[0]["rank"] if matched_rows else None,
            "ambiguous_hit": bool(ambiguous_rows),
            "retrieved_record_matches_expected_fact": candidate_ok and stored_hash == expected_hash,
            "candidates_considered": provenance.get("candidates_considered"),
            "injected_hashes": injected_hashes,
            "injected_count": len(injected),
            "section3_hash_in_simulated_context": hash_injected,
            "simulated_context_nonempty": bool(injected_text),
            "except_path_swallowed": "candidates_considered" not in provenance,
            "result": demonstrated,
        })
        log(
            f"ITEM {item_id} result={demonstrated} rank={facts[-1]['correct_rank']} "
            f"injected={hash_injected} candidates={facts[-1]['candidates_considered']}"
        )

    echo_record = vm.meta.get(ECHO_03)
    echo_text = echo_record.get("text") if isinstance(echo_record, dict) else None
    item03 = next(row for row in facts if row["item_id"] == "03")
    echo_hash = text_hash12(echo_text) if isinstance(echo_text, str) else None
    echo_note = {
        "user_id": ECHO_03,
        "present": echo_record is not None,
        "text_hash12": echo_hash,
        "expected_hash12": "4ae0ccf0ce68",
        "hash_matches_section3": echo_hash == "4ae0ccf0ce68",
        "appears_in_item03_raw_hits": any(
            ECHO_03 in row["owner_ids"] for row in item03["raw_hits"]
        ),
        "used_as_substitute_for_user_row": False,
    }

    nonce_present = NONCE in owners
    nonce_hits = annotate(search_fn(NONCE, 15))
    other_id = next(item for item in vm.id_order if item not in {pair[0] for pair in EXPECTED.values()})
    other_text = vm.meta[other_id]["text"]
    other_hits = annotate(search_fn(other_text, 5))
    negative = {
        "nonce_absent_from_metadata": not nonce_present,
        "nonce_neighbor_unique_owners": [row["unique_owner"] for row in nonce_hits],
        "nonce_neighbors_reported_as_ten_successes": False,
        "other_stored_id": other_id,
        "other_stored_hash12": text_hash12(other_text),
        "other_id_is_one_of_the_ten": False,
        "other_text_unique": len(owners.get(other_text, [])) == 1,
        "other_query_top_unique_owner": other_hits[0]["unique_owner"] if other_hits else None,
        "other_query_returned_its_own_id": bool(other_hits) and other_hits[0]["unique_owner"] == other_id,
    }

    after = live_fingerprint()
    demonstrated_n = sum(row["result"] == "demonstrated" for row in facts)
    outcome = "PASS" if demonstrated_n == 10 and not refused else "FAIL"
    payload = {
        "outcome": outcome,
        "identity": identity,
        "search_refused": refused,
        "clock_rule": "each item uses its own results_phase2.jsonl started_at",
        "embed": "SentenceTransformer all-MiniLM-L6-v2 encode([text], normalize_embeddings=True)",
        "selection": "retrieve_memory_context k=5, so search_fn receives k*3=15, then the real 30-minute filter",
        "facts": facts,
        "echo_row_item_03": echo_note,
        "negative_control": negative,
        "stage_counts": {
            "storage_ok": sum(row["storage_ok"] for row in facts),
            "identity_validation_passed": sum(row["identity_validation_passed"] for row in facts),
            "index_membership_ok": sum(row["index_membership_ok"] for row in facts),
            "search_reached_index": sum(row["search_reached_index"] for row in facts),
            "correct_user_id_returned": sum(row["correct_user_id_returned"] for row in facts),
            "retrieved_record_matches_expected_fact": sum(
                row["retrieved_record_matches_expected_fact"] for row in facts
            ),
            "section3_hash_in_simulated_context": sum(
                row["section3_hash_in_simulated_context"] for row in facts
            ),
            "demonstrated": demonstrated_n,
            "failed": sum(row["result"] == "failed" for row in facts),
            "could_not_be_tested": sum(row["result"] == "could not be tested" for row in facts),
        },
        "live_before": before,
        "live_after": after,
        "live_stat_changed_during_search": before != after,
        "production_paths_opened_for_write": False,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    log(f"SEARCH_DONE outcome={outcome} demonstrated={demonstrated_n}/10")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        log(f"SEARCH_FAIL {type(exc).__name__}: {exc}")
        raise
