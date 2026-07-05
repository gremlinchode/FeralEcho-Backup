# app/core/memory_migration.py
# ============================================================
# One-time migration: merge data/ FAISS entries into memory/.
#
# Run manually when you want to close the split-brain:
#   python -c "from app.core.memory_migration import merge_data_into_memory; merge_data_into_memory()"
#
# Safe to run repeatedly — already-present texts are skipped.
# ============================================================
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_META = Path("data/memory_meta.json")
_MEMORY_META = Path("memory/memory_meta.json")


def merge_data_into_memory(dry_run: bool = False) -> dict:
    """
    Read orphaned entries from data/memory_meta.json and add them to the
    authoritative memory/ index via memory_bridge.add_to_vector_memory().

    Returns a summary dict with keys: found, skipped, migrated, errors.
    """
    if not _DATA_META.exists():
        logger.info("[MIGRATION] data/memory_meta.json not found — nothing to migrate.")
        return {"found": 0, "skipped": 0, "migrated": 0, "errors": 0}

    try:
        with open(_DATA_META) as f:
            data_entries = json.load(f)
    except Exception as e:
        logger.error("[MIGRATION] Could not read data/memory_meta.json: %s", e)
        return {"found": 0, "skipped": 0, "migrated": 0, "errors": 1}

    # Load existing memory/ texts for dedup
    memory_texts: set = set()
    if _MEMORY_META.exists():
        try:
            with open(_MEMORY_META) as f:
                mem = json.load(f)
            for v in mem.values():
                t = v.get("text", "")
                if t:
                    memory_texts.add(t)
        except Exception as e:
            logger.warning("[MIGRATION] Could not read memory/memory_meta.json: %s", e)

    from app.core.memory_bridge import add_to_vector_memory

    found = len(data_entries)
    skipped = migrated = errors = 0

    for entry_id, entry in data_entries.items():
        text = entry.get("text", "")
        meta = entry.get("meta", {})
        if not text or text in memory_texts:
            skipped += 1
            continue
        if dry_run:
            logger.info("[MIGRATION] Would migrate: %s…", text[:80])
            migrated += 1
            memory_texts.add(text)
            continue
        try:
            add_to_vector_memory(text, meta)
            memory_texts.add(text)
            migrated += 1
        except Exception as e:
            logger.warning("[MIGRATION] Failed to migrate entry %s: %s", entry_id, e)
            errors += 1

    logger.info(
        "[MIGRATION] Complete | found=%d skipped=%d migrated=%d errors=%d",
        found, skipped, migrated, errors,
    )
    return {"found": found, "skipped": skipped, "migrated": migrated, "errors": errors}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = merge_data_into_memory()
    print(result)
