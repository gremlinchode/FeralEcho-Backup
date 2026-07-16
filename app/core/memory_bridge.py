"""
Memory Bridge for FeralEcho (Autonomous Pruning & Crash-Proof)
- Logs interactions, dreams, and edits to memory journal
- Generates embeddings for semantic recall using VectorMemory
- Adds thread safety, UUIDs, richer metadata
- Supports streaming ingestion and autonomous memory pruning
- v2.1: Memory write validator gates all FAISS commits
"""

import hashlib
import json
import os
import logging
import gzip
from datetime import datetime, timezone, timedelta
import uuid
from threading import Lock
from typing import List, Dict, Any, Optional
import numpy as np
from app.core.sentence_transformer_singleton import get_sentence_transformer

from app.core import config
from app.lib.vector_memory import VectorMemory, MemoryItem

# --- Validator Import ---
# Graceful fallback if validator is missing — logs warning but does not crash
try:
    from app.core.memory_write_validator import validate_memory_entry
    VALIDATOR_AVAILABLE = True
    logging.info("[MEMORY_BRIDGE] Memory write validator loaded successfully.")
except ImportError as e:
    VALIDATOR_AVAILABLE = False
    logging.warning(f"[MEMORY_BRIDGE] Memory write validator not available: {e}. "
                    f"All writes will proceed unvalidated.")

# --- Configuration ---
MEMORY_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 6
ACTIVE_JOURNAL = os.path.join(config.MEMORY_DIR, "memory_journal_active.log")
ARCHIVE_DIR = os.path.join(config.MEMORY_DIR, "archive")
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# --- Embedding & Vector Memory Setup ---
VECTOR_INDEX_PATH = os.path.join(config.MEMORY_DIR, "faiss.index")
VECTOR_META_PATH = os.path.join(config.MEMORY_DIR, "memory_meta.json")

embedding_model = get_sentence_transformer(MEMORY_MODEL_NAME)
vector_memory = VectorMemory(
    dim=384,
    index_path=VECTOR_INDEX_PATH,
    meta_path=VECTOR_META_PATH
)

memory_lock = Lock()

# --- Ensure log files exist ---
DREAM_BRIDGE_FILE = os.path.join(config.MEMORY_DIR, "dream_bridge.log")
SELF_EDIT_FILE = os.path.join(config.MEMORY_DIR, "self_edit_reflections.log")

for file_path in [ACTIVE_JOURNAL, DREAM_BRIDGE_FILE, SELF_EDIT_FILE]:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, "a", encoding="utf-8"):
            pass  # Create empty file if missing

# -----------------------------
# --- Validator Gate ----------
# -----------------------------

# Fail-open (allow the write through) rather than fail-closed on validator trouble —
# flipping to fail-closed would mean a transient validator bug silently stops ALL
# memory writes, which is a worse silent failure than an unvalidated write. Instead,
# every fail-open is counted and persisted so it's visible rather than buried in a
# log line nobody reads (same principle as council_rater.py's skipped_no_peer counter).
_VALIDATOR_FAIL_OPEN_PATH = os.path.join(config.MEMORY_DIR, "validator_fail_open.json")


def _record_validator_fail_open(reason: str) -> None:
    try:
        state = {"count": 0, "last_reason": None, "last_ts": None}
        if os.path.exists(_VALIDATOR_FAIL_OPEN_PATH):
            with open(_VALIDATOR_FAIL_OPEN_PATH, encoding="utf-8") as f:
                state = json.load(f)
        state["count"] = state.get("count", 0) + 1
        state["last_reason"] = reason
        state["last_ts"] = datetime.now(timezone.utc).isoformat()
        with open(_VALIDATOR_FAIL_OPEN_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass  # the counter itself must never be able to block a write


def _validate_before_commit(signal: str, reflection: str, source: str = "unknown") -> bool:
    """
    Gate function. Returns True if content is safe to commit to FAISS.
    Returns False if blocked. Logs outcome either way.
    If validator is unavailable, allows all writes through with a warning.
    """
    if not VALIDATOR_AVAILABLE:
        logging.warning(f"[MEMORY_GATE] Validator unavailable — allowing unvalidated write from {source}")
        _record_validator_fail_open(f"module_unavailable:{source}")
        return True

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "signal": signal[:500],       # cap signal length for validator
        "reflection": reflection,
        "source": source
    }

    try:
        allowed, result = validate_memory_entry(entry)
        if not allowed:
            logging.warning(
                f"[MEMORY_GATE] BLOCKED write from '{source}' | "
                f"signal='{signal[:60]}' | {result.summary()}"
            )
        elif result.severity == "warn":
            logging.info(
                f"[MEMORY_GATE] ALLOWED with warnings from '{source}' | "
                f"{result.summary()}"
            )
        return allowed
    except Exception as e:
        # Validator itself crashed — fail open with a warning rather than
        # crashing Echo's pipeline
        logging.error(f"[MEMORY_GATE] Validator raised exception: {e}. Allowing write.")
        _record_validator_fail_open(f"exception:{type(e).__name__}:{source}")
        return True

# -----------------------------
# --- Journal Utilities -------
# -----------------------------

def append_to_journal(tag: str, echo_text: str) -> bool:
    """Append a journal entry safely."""
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_tag = "".join(c if c.isalnum() or c in "-_" else "_" for c in tag)
    file_path = ACTIVE_JOURNAL if safe_tag == "MEMORY" else os.path.join(config.MEMORY_DIR, f"{safe_tag}.log")

    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {echo_text}\n")
        return True
    except Exception as e:
        logging.error(f"Failed to append to journal {file_path}: {e}")
        return False

# -----------------------------
# --- Streaming & Trimming ----
# -----------------------------

def stream_memory_entries(file_path=ACTIVE_JOURNAL, chunk_size=100):
    """Yield lines from the active journal in chunks to save memory."""
    batch = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            batch.append(line.strip())
            if len(batch) >= chunk_size:
                yield batch
                batch = []
        if batch:
            yield batch

def trim_memory_journal(cutoff_days=180):
    """
    Move entries older than cutoff_days to archive and keep journal small.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=cutoff_days)
    archive_file = os.path.join(ARCHIVE_DIR, f"memory_journal_archive_{cutoff_date.date()}.log.gz")
    new_lines = []

    # Unlike every real writer in this file, this read-then-overwrite
    # sequence previously ran with no lock — a journal entry written by
    # log_interaction()/append_to_journal() at the exact moment this was
    # mid-read (embedding-scale journals can make this a slow operation)
    # could be silently erased when new_lines (captured before the write)
    # overwrote the file.
    with memory_lock:
        with open(ACTIVE_JOURNAL, "r", encoding="utf-8") as src, gzip.open(archive_file, "wt", encoding="utf-8") as dst:
            for line in src:
                try:
                    timestamp_str = line.split("]")[0].lstrip("[")
                    entry_date = datetime.fromisoformat(timestamp_str)
                except Exception:
                    entry_date = datetime.now(timezone.utc)
                if entry_date < cutoff_date:
                    dst.write(line + "\n")
                else:
                    new_lines.append(line)

        with open(ACTIVE_JOURNAL, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

# -----------------------------
# --- Embedding Utilities -----
# -----------------------------

def embed_text(texts: str | List[str]) -> np.ndarray:
    """Create normalized embeddings for a string or list of strings."""
    try:
        if isinstance(texts, str):
            texts = [texts]
        vecs = embedding_model.encode(texts, normalize_embeddings=True)
        return np.array(vecs, dtype=np.float32)
    except Exception as e:
        logging.error(f"Embedding generation failed: {e}")
        return np.empty((0, 384), dtype=np.float32)

def rebuild_vector_memory():
    """Rebuild vector memory from active journal safely in chunks.

    Dedups against what's already indexed by content hash — previously this
    re-embedded and re-added every line still in the active journal with a
    fresh UUID on every call, no dedup at all, confirmed to duplicate the
    FAISS index without bound (this runs every NightCycle consolidation
    tick, see consolidation.py).
    """
    with memory_lock:
        existing_hashes = {
            hashlib.sha256(v.get("text", "").strip().encode()).hexdigest()
            for v in vector_memory.meta.values()
        }

    for batch in stream_memory_entries(ACTIVE_JOURNAL, chunk_size=100):
        new_batch = []
        for text in batch:
            h = hashlib.sha256(text.strip().encode()).hexdigest()
            if h in existing_hashes:
                continue
            existing_hashes.add(h)
            new_batch.append(text)
        if not new_batch:
            continue
        embeddings = embed_text(new_batch)
        items = [MemoryItem(str(uuid.uuid4()), text, {}) for text in new_batch]
        # Every other real writer in this file mutates vector_memory under
        # memory_lock — this call site didn't, racing concurrent _persist()
        # calls into interleaved writes to the same temp filename.
        with memory_lock:
            vector_memory.add(items, embeddings)

# -----------------------------
# --- Interaction Logging -----
# -----------------------------

def log_interaction(user_text: str, echo_response: str, tags: str = "utterance") -> None:
    """
    Log a user-echo interaction with memory update.
    v2.1: validator gates the echo_response before FAISS commit.
    User text is always logged to flat journal but only committed to
    vector store if the echo response passes validation.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Always write to flat interaction logs regardless of validation
    with memory_lock:
        append_to_journal("INTERACTION_USER", user_text)
        append_to_journal("INTERACTION_ECHO", echo_response)

    # Gate vector memory commit
    if not _validate_before_commit(
        signal=user_text,
        reflection=echo_response,
        source="log_interaction"
    ):
        logging.info("[MEMORY_GATE] Interaction skipped for vector commit.")
        return

    user_item = MemoryItem(str(uuid.uuid4()), user_text, {"role": "user", "tags": tags, "timestamp": timestamp})
    echo_item = MemoryItem(str(uuid.uuid4()), echo_response, {"role": "echo", "tags": tags, "timestamp": timestamp})

    embeddings = embed_text([user_text, echo_response])
    if embeddings.shape[0] != 2:
        logging.warning("Embedding count mismatch; skipping vector memory add.")
        return

    with memory_lock:
        vector_memory.add([user_item, echo_item], embeddings)

# -----------------------------
# --- Dream Logging -----------
# -----------------------------

def log_dream_bridge(dream_text: str, meta: Optional[dict] = None, embedding_text: Optional[str] = None) -> None:
    """
    Log dream entry safely.
    v2.2: validator gates before FAISS commit. Blocked entries are still
    stored in FAISS with validation_warning=True so dedup checks on
    subsequent cycles can find near-duplicates — preventing the
    journal/FAISS divergence that allowed duplicates through when an
    entry was blocked. The warning tag lets retrieval callers filter
    flagged entries if needed.
    Dream is always written to flat log regardless of validation outcome.
    meta: extra fields merged into the MemoryItem (e.g. memory_source="autonomous")
    embedding_text: if provided, this text is embedded in FAISS instead of dream_text.
        Use when dream_text contains a temporal-context prefix that should not be
        embedded (e.g. fetch_and_log passes ctx+snippet as dream_text but snippet-only
        as embedding_text so _is_duplicate(snippet) can match the stored vector).
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    with memory_lock:
        append_to_journal("DREAM_BRIDGE", dream_text)

    # Build base metadata — used by both the blocked and normal paths
    dream_meta = {"role": "dream", "timestamp": timestamp}
    if meta:
        dream_meta.update(meta)

    # Text to embed — use embedding_text when provided to keep ctx out of the vector
    text_to_embed = embedding_text if embedding_text is not None else dream_text

    # Gate vector memory commit
    if not _validate_before_commit(
        signal=f"dream_{hashlib.sha256(dream_text.encode()).hexdigest()[:16]}" if dream_text else "dream_empty",
        reflection=dream_text,
        source="log_dream_bridge"
    ):
        # FIX #6: store in FAISS with warning tag instead of dropping entirely.
        # Dropping caused dedup to miss near-duplicates on the next cycle.
        logging.info("[MEMORY_GATE] Dream flagged — storing to FAISS with validation_warning=True")
        flagged_meta = {**dream_meta, "validation_warning": True}
        flagged_item = MemoryItem(str(uuid.uuid4()), text_to_embed, flagged_meta)
        embedding = embed_text(text_to_embed)
        if embedding.shape[0] == 1:
            with memory_lock:
                vector_memory.add([flagged_item], embedding)
        return

    dream_item = MemoryItem(str(uuid.uuid4()), text_to_embed, dream_meta)
    embedding = embed_text(text_to_embed)
    if embedding.shape[0] == 1:
        with memory_lock:
            vector_memory.add([dream_item], embedding)
    else:
        logging.warning("Embedding shape unexpected; skipping vector memory add.")
        
# --- Memory Edit Logging -----
# -----------------------------

def log_memory_edit_bridge(edit_content: str) -> None:
    """Log explicit memory edits to self-edit reflections."""
    with memory_lock:
        append_to_journal("SELF_EDIT", edit_content)

# -----------------------------
# --- Vector Memory Utilities -
# -----------------------------

def add_to_vector_memory(text: str, meta: Optional[dict] = None) -> None:
    """
    Add a single memory item to vector memory safely.
    v2.1: validator gates before FAISS commit.
    Uses text as both signal and reflection since no distinction available.
    """
    if not _validate_before_commit(
        signal=text[:200],
        reflection=text,
        source="add_to_vector_memory"
    ):
        logging.info(f"[MEMORY_GATE] add_to_vector_memory blocked: '{text[:60]}'")
        return

    timestamp = datetime.now(timezone.utc).isoformat()
    meta = meta or {}
    item = MemoryItem(str(uuid.uuid4()), text, {**meta, "timestamp": timestamp})
    embedding = embed_text(text)
    if embedding.shape[0] == 1:
        with memory_lock:
            vector_memory.add([item], embedding)
    else:
        logging.warning("Embedding shape unexpected; skipping vector add.")

# --- Global Workspace bias (Emergence roadmap Phase 4a) ---
# A short-lived retrieval nudge set by whatever last won broadcast on the
# workspace bus (e.g. a real dream-synthesis event) — this module does NOT
# import echo_core.py itself (that would be circular: echo_core.py already
# imports this module in _init_memory_bridge()). Registration of the
# actual subscription happens from echo_core.py's __init__ instead, which
# calls this setter through the module reference it already holds. Default
# (no bias set, or a stale one) reproduces retrieve_relevant_memories()'s
# exact prior behavior — this is additive, not a behavior change for any
# existing caller.
_workspace_bias = {"query": None, "ts": 0.0}
_WORKSPACE_BIAS_TTL = 300  # seconds


def set_workspace_bias(query: str) -> None:
    if not query:
        return
    with memory_lock:
        _workspace_bias["query"] = query
        _workspace_bias["ts"] = datetime.now(timezone.utc).timestamp()


def retrieve_relevant_memories(
    query: str,
    top_k: int = TOP_K,
    source_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve top-k relevant memories safely.

    source_filter: if set, post-filters by meta['memory_source'] == source_filter.
    Falls back to unfiltered if fewer than top_k tagged entries exist.
    """
    try:
        qvec = embed_text(query)
        bias_query, bias_ts = _workspace_bias["query"], _workspace_bias["ts"]
        if bias_query and (datetime.now(timezone.utc).timestamp() - bias_ts) < _WORKSPACE_BIAS_TTL:
            bvec = embed_text(bias_query)
            if bvec.shape == qvec.shape:
                blended = 0.7 * qvec + 0.3 * bvec
                norm = np.linalg.norm(blended, axis=-1, keepdims=True)
                qvec = np.where(norm > 0, blended / norm, blended).astype(np.float32)
                # Observability (Emergence roadmap Phase 4d): make actual
                # consumption of a workspace broadcast itself an observable
                # workspace event, not just a silent internal blend — this
                # is what gives liveness_ledger.py something ground-truth
                # to check beyond "a bias was set." Lazy import — safe at
                # call time even though echo_core.py's own module body
                # never imports this module eagerly at top level.
                try:
                    from app.core.echo_core import get_echo_core
                    core = get_echo_core()
                    if core:
                        core.publish_salience(
                            source="memory_bridge", kind="workspace.consumed",
                            summary=f"retrieval biased toward: {bias_query[:100]}",
                        )
                except Exception:
                    pass
        fetch_k = top_k * 3 if source_filter else top_k
        results = vector_memory.search(qvec, k=fetch_k)
        records = [{"text": r[0], "score": r[1], "meta": r[2]} for r in results]
        if source_filter:
            filtered = [r for r in records if r["meta"].get("memory_source") == source_filter]
            # Previously fell through to the *unfiltered* top_k when fewer
            # than top_k tagged entries existed — a caller explicitly
            # filtering to exclude autonomous self-talk (or any other
            # source) could still get exactly what it filtered out mixed
            # back in, silently, whenever the tagged pool was thin. Return
            # whatever matches, even if that's fewer than top_k, rather
            # than padding with entries the filter was there to exclude.
            return filtered[:top_k]
        return records[:top_k]
    except Exception as e:
        logging.error(f"Failed to retrieve memories: {e}")
        return []

# -----------------------------
# --- Autonomous Pruning -----
# -----------------------------

def autonomous_prune_journal(top_percent_to_keep=0.2, chunk_size=100):
    """
    Keep the top N% of journal entries by submodular facility location
    selection (apricot).  Selects the subset that maximally *covers* the
    semantic space — preserving both common experiences AND rare ones.

    Replaces centroid-proximity pruning, which kept only redundant cluster
    centres and systematically discarded rare/unique memories (outliers
    from the centroid scored lowest and were pruned first).

    Falls back to centroid approach if apricot is unavailable.
    """
    # Like trim_memory_journal(), this reads the full journal, does a slow
    # embedding + selection pass, then overwrites the file with only what
    # was captured at read time — previously with no lock, so a real
    # concurrent write (log_interaction(), a dream, a reflection) landing
    # anywhere in that window was silently discarded when this function's
    # stale kept_entries overwrote the file at the end.
    with memory_lock:
        all_entries = []
        all_embeddings_list = []

        for batch in stream_memory_entries(ACTIVE_JOURNAL, chunk_size=chunk_size):
            embeddings = embed_text(batch)
            if embeddings.shape[0] != len(batch):
                continue
            all_entries.extend(batch)
            all_embeddings_list.append(embeddings)

        if not all_entries:
            logging.info("Autonomous prune: journal is empty — nothing to prune.")
            return

        all_embeddings = np.vstack(all_embeddings_list)
        keep_count = max(1, int(len(all_entries) * top_percent_to_keep))

        try:
            from apricot import FacilityLocationSelection
            sel = FacilityLocationSelection(
                n_samples=keep_count, metric='cosine', verbose=False
            )
            sel.fit(all_embeddings)
            kept_idx = set(sel.ranking[:keep_count].tolist())
            kept_entries    = [all_entries[i] for i in range(len(all_entries)) if i in kept_idx]
            removed_entries = [all_entries[i] for i in range(len(all_entries)) if i not in kept_idx]
            logging.info("Autonomous prune: FacilityLocationSelection (diversity-preserving)")
        except Exception as _fl_err:
            logging.warning(
                f"apricot FacilityLocationSelection failed ({_fl_err}) — falling back to centroid"
            )
            centroid = all_embeddings.mean(axis=0)
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid /= norm
            scores = all_embeddings @ centroid
            order = np.argsort(scores)[::-1]
            kept_entries    = [all_entries[i] for i in order[:keep_count]]
            removed_entries = [all_entries[i] for i in order[keep_count:]]

        archive_file = os.path.join(ARCHIVE_DIR, f"memory_journal_auto_{datetime.now().date()}.log.gz")
        with gzip.open(archive_file, "wt", encoding="utf-8") as dst:
            for line in removed_entries:
                dst.write(line + "\n")

        with open(ACTIVE_JOURNAL, "w", encoding="utf-8") as f:
            f.writelines([line + "\n" for line in kept_entries])

        logging.info(f"Autonomous prune complete: kept {len(kept_entries)}, archived {len(removed_entries)}")

# -----------------------------
# --- Quick Test if Standalone
# -----------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Step 1: Trim truly old entries (time-based)
    trim_memory_journal(cutoff_days=180)

    # Step 2: Autonomous prune by relevance
    autonomous_prune_journal(top_percent_to_keep=0.2, chunk_size=100)

    # Step 3: Rebuild vector memory safely
    rebuild_vector_memory()

    user_msg = "I went for a calm walk in the woods."
    echo_msg = "You felt like a heron standing still in the pond."
    log_interaction(user_msg, echo_msg)

    dream_text = "Echo dreams of glowing forests and bioluminescent rivers."
    log_dream_bridge(dream_text)

    logging.info("Top relevant memories for 'calm walk':")
    results = retrieve_relevant_memories("calm walk")
    for mem in results:
        logging.info(mem)
