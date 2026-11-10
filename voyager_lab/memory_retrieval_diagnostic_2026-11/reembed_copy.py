#!/usr/bin/env python3
"""Re-embed the copied metadata into a new empty VectorMemory.

Identity source: this process inserts every copied record in the key order
json.load produced from copy_live/memory_meta.json, then VectorMemory._persist
writes the index and the schema-1 sidecar together. That order is the
insertion order of this new store. It is not a claim about the live FAISS
row order, and it is not a stamp of meta.keys() onto the copied index.

Writes only under this diagnostic directory. Does not import memory_bridge.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

ROOT = "/Users/richietate/Desktop/FeralEcho"
DIAG = os.path.dirname(os.path.abspath(__file__))
COPY_META = os.path.join(DIAG, "copy_live", "memory_meta.json")
COPY_INDEX = os.path.join(DIAG, "copy_live", "faiss.index")
REBUILT = os.path.join(DIAG, "rebuilt")
INDEX_PATH = os.path.join(REBUILT, "faiss.index")
META_PATH = os.path.join(REBUILT, "memory_meta.json")
LIVE_DIR = os.path.join(ROOT, "memory")
LIVE_INDEX = os.path.join(LIVE_DIR, "faiss.index")
LIVE_META = os.path.join(LIVE_DIR, "memory_meta.json")
LIVE_SIDE = os.path.join(LIVE_DIR, "faiss.index.identity.json")

sys.path.insert(0, ROOT)


def log(msg: str) -> None:
    print(msg, flush=True)


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def live_fingerprint() -> dict:
    out = {}
    for name, path in (
        ("index", LIVE_INDEX),
        ("meta", LIVE_META),
    ):
        st = os.stat(path)
        out[name] = {"inode": st.st_ino, "size": st.st_size, "mtime_ns": st.st_mtime_ns}
    out["sidecar_exists"] = os.path.exists(LIVE_SIDE)
    return out


def main() -> int:
    for path in (INDEX_PATH, META_PATH, INDEX_PATH + ".identity.json"):
        if os.path.exists(path):
            log(f"REEMBED_FAIL existing {path}")
            return 2
    if os.path.commonpath([os.path.abspath(INDEX_PATH), DIAG]) != DIAG:
        log("REEMBED_FAIL output escaped diagnostic dir")
        return 2
    if LIVE_DIR in os.path.abspath(INDEX_PATH) or LIVE_DIR in os.path.abspath(META_PATH):
        log("REEMBED_FAIL refused live path")
        return 2

    before = live_fingerprint()
    log(f"LIVE_BEFORE {json.dumps(before)}")
    log(f"COPY_INDEX_SHA256 {sha256_file(COPY_INDEX)}")
    log(f"COPY_META_SHA256 {sha256_file(COPY_META)}")

    log("META_LOAD_START")
    with open(COPY_META, "r", encoding="utf-8") as handle:
        meta = json.load(handle)
    if not isinstance(meta, dict):
        log("REEMBED_FAIL meta is not an object")
        return 2
    ids = list(meta.keys())
    n = len(ids)
    log(f"DECLARED_ORDER json.load key order count={n} first={ids[0]} last={ids[-1]}")
    texts = []
    metas = []
    for item_id in ids:
        rec = meta[item_id]
        if not isinstance(rec, dict) or not isinstance(rec.get("text"), str):
            log(f"REEMBED_FAIL bad record {item_id}")
            return 2
        inner = rec.get("meta")
        if not isinstance(inner, dict):
            log(f"REEMBED_FAIL bad meta {item_id}")
            return 2
        texts.append(rec["text"])
        metas.append(inner)
    # The source dict is no longer needed. Drop it before the embedding array.
    del meta

    os.makedirs(REBUILT, exist_ok=True)
    import numpy as np
    from app.core.sentence_transformer_singleton import get_sentence_transformer
    from app.lib.vector_memory import MemoryItem, VectorMemory

    log("MODEL_LOAD_START")
    model = get_sentence_transformer("all-MiniLM-L6-v2")
    log("MODEL_READY")
    emb = np.empty((n, 384), dtype=np.float32)
    batch = 64
    t0 = time.time()
    for start in range(0, n, batch):
        chunk = texts[start:start + batch]
        vecs = model.encode(chunk, normalize_embeddings=True, show_progress_bar=False)
        arr = np.asarray(vecs, dtype=np.float32)
        if arr.shape != (len(chunk), 384):
            log(f"REEMBED_FAIL bad embed shape {arr.shape} at {start}")
            return 2
        emb[start:start + len(chunk)] = arr
        done = start + len(chunk)
        if done == batch or done % 5000 < batch or done == n:
            rate = done / max(time.time() - t0, 1e-6)
            log(f"ENCODE {done}/{n} rate={rate:.1f}/s")

    items = [
        MemoryItem(id=item_id, text=text, meta=inner)
        for item_id, text, inner in zip(ids, texts, metas)
    ]
    del texts, metas
    vm = VectorMemory(dim=384, index_path=INDEX_PATH, meta_path=META_PATH)
    if vm._index_existed_at_init or vm._meta_existed_at_init:
        log("REEMBED_FAIL new store saw existing files")
        return 2
    if not vm._identity_authoritative:
        log("REEMBED_FAIL writer is not authoritative")
        return 2
    if vm.index is None or vm.index.ntotal != 0:
        log("REEMBED_FAIL new index was not empty")
        return 2
    log("ADD_START")
    persisted = vm.add(items, emb)
    log(
        f"ADD_DONE persisted={persisted} ntotal={vm.index.ntotal} "
        f"meta={len(vm.meta)} status={vm.identity_status} "
        f"verified={vm.identity_verified} authoritative={vm._identity_authoritative}"
    )
    if not persisted or not vm.identity_verified or vm.identity_status != "manifest_valid":
        log("REEMBED_FAIL persist did not reach manifest_valid")
        return 2
    if vm.index.ntotal != n or len(vm.id_order) != n:
        log("REEMBED_FAIL row count drifted")
        return 2
    after = live_fingerprint()
    log(f"LIVE_AFTER {json.dumps(after)}")
    result = {
        "persisted": True,
        "in_process_identity_status": vm.identity_status,
        "in_process_identity_verified": vm.identity_verified,
        "ntotal": int(vm.index.ntotal),
        "id_order_len": len(vm.id_order),
        "declared_order": "json.load key order of copy_live/memory_meta.json",
        "declared_order_is_old_faiss_row_order": False,
        "encode_seconds": round(time.time() - t0, 3),
        "live_before": before,
        "live_after": after,
        "live_unchanged_during_reembed": before == after,
    }
    with open(os.path.join(DIAG, "rebuild_result.json"), "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    log("REEMBED_DONE")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        log(f"REEMBED_FAIL {type(exc).__name__}: {exc}")
        raise
