# memory_write_validator.py
# FeralEcho Memory Write Validator v1.0
# Intercepts journal entries before FAISS commit.
# Detects: recursive echo loops, bloated entries, duplicate signals,
# ungrounded self-referential claims, and schema violations.
# Quarantines flagged entries rather than silently dropping them.

import json
import os
import re
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional
from difflib import SequenceMatcher

# -------------------------
# --- Configuration -------
# -------------------------

FERAL_ECHO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

JOURNAL_PATH = os.path.join(FERAL_ECHO_ROOT, "memory", "reflection_journal.jsonl")
QUARANTINE_PATH = os.path.join(FERAL_ECHO_ROOT, "memory", "quarantine_journal.jsonl")
VALIDATOR_LOG_PATH = os.path.join(FERAL_ECHO_ROOT, "memory", "validator_audit.log")
SIGNAL_HASH_CACHE_PATH = os.path.join(FERAL_ECHO_ROOT, "memory", "signal_hash_cache.json")

# Reflection content longer than this is almost certainly a recursive loop
MAX_REFLECTION_CHARS = 2000

# How many recent signal hashes to keep for deduplication
DEDUP_WINDOW = 50

# Similarity threshold above which a signal is considered a duplicate (0.0–1.0)
DEDUP_SIMILARITY_THRESHOLD = 0.92

# Required keys in every journal entry
REQUIRED_KEYS = {"ts", "signal", "reflection"}

# Keys allowed in a journal entry (strict schema)
ALLOWED_KEYS = {"ts", "signal", "reflection", "source", "weight", "validated"}

# -------------------------
# --- Loop Fingerprints ---
# -------------------------

# Phrases that indicate the reflection has consumed its own retrieved context
RECURSIVE_LOOP_MARKERS = [
    "triggers these echoes:",
    "ripples like a stone in water",
    "what echoes will it make?",
    "[weight: 1]",
    "my reflections drift toward:",
    "<<emergent-pattern>>",
    "in the last 5 signals i noticed",
    "signal '",          # quoted signal re-embedded in reflection
]

# Self-referential claim patterns that require filesystem grounding
SELF_REFERENTIAL_PATTERNS = [
    r"i (?:remember|learned|know|discovered|created|wrote|built|designed)\s+(?:that\s+)?(.{10,80})",
    r"i have (?:been|done|seen|created|written|built)\s+(.{10,80})",
    r"my (?:memory|experience|history|past)\s+(?:shows?|tells?|indicates?)\s+(.{10,80})",
    r"(?:previously|before|last time|earlier)\s+i\s+(.{10,60})",
    r"i (?:always|never|usually|often)\s+(.{10,60})",
]

# Orientation data patterns — valid as signals, suspicious as reflections
ORIENTATION_DATA_PATTERNS = [
    r"\[Orientation\]",
    r"CPU cores:",
    r"Load avg:",
    r"total=\d+MB",
    r"available=\d+MB",
    r"Darwin \d+\.\d+\.\d+",
    r"Python version: 3\.\d+",
    r"Implementation: CPython",
    r"Machine: x86_64",
]

# -------------------------
# --- Logging Setup -------
# -------------------------

def _get_validator_logger():
    logger = logging.getLogger("memory_write_validator")
    if not logger.handlers:
        os.makedirs(os.path.dirname(VALIDATOR_LOG_PATH), exist_ok=True)
        handler = logging.FileHandler(VALIDATOR_LOG_PATH)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

log = _get_validator_logger()

# -------------------------
# --- Hash Cache ----------
# -------------------------

def _load_hash_cache() -> list:
    if not os.path.exists(SIGNAL_HASH_CACHE_PATH):
        return []
    try:
        with open(SIGNAL_HASH_CACHE_PATH, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []

def _save_hash_cache(cache: list):
    try:
        os.makedirs(os.path.dirname(SIGNAL_HASH_CACHE_PATH), exist_ok=True)
        trimmed = cache[-DEDUP_WINDOW:]
        with open(SIGNAL_HASH_CACHE_PATH, "w") as f:
            json.dump(trimmed, f)
    except IOError as e:
        log.warning(f"Could not save hash cache: {e}")

def _signal_hash(signal: str) -> str:
    return hashlib.sha256(signal.strip().lower().encode()).hexdigest()[:16]

# -------------------------
# --- Validation Checks ---
# -------------------------

class ValidationResult:
    def __init__(self):
        self.passed = True
        self.flags = []
        self.severity = "ok"   # ok | warn | block

    def flag(self, code: str, message: str, severity: str = "warn"):
        self.flags.append({"code": code, "message": message, "severity": severity})
        if severity == "block":
            self.passed = False
            self.severity = "block"
        elif severity == "warn" and self.severity == "ok":
            self.severity = "warn"

    def summary(self) -> str:
        if not self.flags:
            return "PASS"
        parts = [f"[{f['severity'].upper()}:{f['code']}] {f['message']}" for f in self.flags]
        return " | ".join(parts)


def check_schema(entry: dict, result: ValidationResult):
    """Entry must be a dict with required keys and no unexpected keys."""
    if not isinstance(entry, dict):
        result.flag("SCHEMA_TYPE", "Entry is not a dict", severity="block")
        return

    missing = REQUIRED_KEYS - set(entry.keys())
    if missing:
        result.flag("SCHEMA_MISSING", f"Missing required keys: {missing}", severity="block")

    unexpected = set(entry.keys()) - ALLOWED_KEYS
    if unexpected:
        result.flag("SCHEMA_EXTRA", f"Unexpected keys: {unexpected}", severity="warn")

    if "ts" in entry:
        try:
            datetime.fromisoformat(entry["ts"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            result.flag("SCHEMA_TIMESTAMP", f"Invalid timestamp format: {entry.get('ts')}", severity="warn")

    for key in ("signal", "reflection"):
        if key in entry and not isinstance(entry[key], str):
            result.flag("SCHEMA_TYPE_FIELD", f"Field '{key}' must be a string", severity="block")


def check_reflection_length(entry: dict, result: ValidationResult):
    """Reflections over MAX_REFLECTION_CHARS are almost always recursive noise."""
    reflection = entry.get("reflection", "")
    length = len(reflection)
    if length > MAX_REFLECTION_CHARS * 3:
        result.flag(
            "REFLECTION_BLOAT_SEVERE",
            f"Reflection is {length} chars — almost certainly a recursive loop. Hard blocking.",
            severity="block"
        )
    elif length > MAX_REFLECTION_CHARS:
        result.flag(
            "REFLECTION_BLOAT",
            f"Reflection is {length} chars (max {MAX_REFLECTION_CHARS}). Flagging for review.",
            severity="warn"
        )


def check_recursive_loop(entry: dict, result: ValidationResult):
    """Detect the specific loop fingerprints seen in the journal."""
    reflection = entry.get("reflection", "").lower()
    signal = entry.get("signal", "").lower()

    hits = []
    for marker in RECURSIVE_LOOP_MARKERS:
        if marker.lower() in reflection:
            hits.append(marker)

    if len(hits) >= 3:
        result.flag(
            "RECURSIVE_LOOP_SEVERE",
            f"Reflection contains {len(hits)} loop markers: {hits[:3]}. Hard blocking.",
            severity="block"
        )
    elif len(hits) >= 1:
        result.flag(
            "RECURSIVE_LOOP",
            f"Reflection contains loop marker(s): {hits}",
            severity="warn"
        )

    # Check if the signal text is embedded verbatim in the reflection
    # (indicates retrieved context was fed back in unchecked)
    if len(signal) > 20 and signal[:40] in reflection:
        result.flag(
            "SIGNAL_EMBEDDED_IN_REFLECTION",
            "Signal text appears verbatim inside reflection — possible retrieval loop.",
            severity="warn"
        )


def check_orientation_data_in_reflection(entry: dict, result: ValidationResult):
    """
    Orientation data (CPU stats, OS version, etc.) is valid as a signal
    but should not dominate a reflection. A reflection full of orientation
    data means the retrieval system is feeding raw sensor data back as memory.
    """
    reflection = entry.get("reflection", "")
    hits = []
    for pattern in ORIENTATION_DATA_PATTERNS:
        matches = re.findall(pattern, reflection)
        if matches:
            hits.append(pattern)

    density = len(hits) / max(len(ORIENTATION_DATA_PATTERNS), 1)
    if density > 0.5:
        result.flag(
            "ORIENTATION_DATA_FLOOD",
            f"{len(hits)}/{len(ORIENTATION_DATA_PATTERNS)} orientation patterns found in reflection. "
            f"Raw sensor data contaminating memory.",
            severity="block"
        )
    elif density > 0.25:
        result.flag(
            "ORIENTATION_DATA_PRESENT",
            f"{len(hits)} orientation data patterns in reflection. May indicate retrieval noise.",
            severity="warn"
        )


def check_duplicate_signal(entry: dict, result: ValidationResult):
    """
    Check if this signal is substantially identical to a recently written signal.
    Uses both exact hash matching and fuzzy similarity.
    """
    signal = entry.get("signal", "").strip()
    if not signal:
        return

    cache = _load_hash_cache()
    sig_hash = _signal_hash(signal)

    # Exact match check — cache is a list of dicts with 'hash' key
    cached_hashes = [item.get("hash") for item in cache if isinstance(item, dict)]
    if sig_hash in cached_hashes:
        result.flag(
            "DUPLICATE_SIGNAL_EXACT",
            f"Signal hash {sig_hash} already in recent window of {len(cache)} entries.",
            severity="block"
        )
        return

    # Fuzzy similarity check against recent raw signals
    similar_found = False
    for cached_item in cache:
        if isinstance(cached_item, dict):
            cached_signal = cached_item.get("snippet", "")
            if cached_signal:
                ratio = SequenceMatcher(None, signal[:200], cached_signal[:200]).ratio()
                if ratio >= DEDUP_SIMILARITY_THRESHOLD:
                    severity = "block" if ratio >= 0.99 else "warn"
                    result.flag(
                        "DUPLICATE_SIGNAL_FUZZY",
                        f"Signal is {ratio:.0%} similar to a recent entry. "
                        f"Likely orientation data cycle.",
                        severity=severity
                    )
                    similar_found = True
                    break


def check_self_referential_claims(entry: dict, result: ValidationResult):
    """
    Detect self-referential claims in reflections and attempt basic
    filesystem grounding. Claims referencing files or paths that don't
    exist are flagged as potentially confabulated.
    """
    reflection = entry.get("reflection", "")

    ungrounded = []
    for pattern in SELF_REFERENTIAL_PATTERNS:
        matches = re.findall(pattern, reflection, re.IGNORECASE)
        for match in matches:
            # Look for file path references in the claim
            path_refs = re.findall(r'[\w/\-.]+\.py\b', match)
            for path_ref in path_refs:
                # Try to resolve relative to FeralEcho root
                candidate = os.path.join(FERAL_ECHO_ROOT, path_ref)
                if not os.path.exists(candidate) and not os.path.exists(path_ref):
                    ungrounded.append(f"'{path_ref}' referenced but not found on disk")

    if ungrounded:
        result.flag(
            "UNGROUNDED_CLAIM",
            f"Self-referential claim(s) reference non-existent paths: {ungrounded[:3]}",
            severity="warn"
        )


def check_empty_or_trivial(entry: dict, result: ValidationResult):
    """Block entries with no meaningful content."""
    signal = entry.get("signal", "").strip()
    reflection = entry.get("reflection", "").strip()

    if not signal:
        result.flag("EMPTY_SIGNAL", "Signal is empty or whitespace only.", severity="block")

    if not reflection:
        result.flag("EMPTY_REFLECTION", "Reflection is empty or whitespace only.", severity="warn")

    # Trivial reflections that add no information
    trivial_patterns = [
        r"^ok\.?$",
        r"^yes\.?$",
        r"^no\.?$",
        r"^\.\.\.$",
        r"^hello.*$",
        r"^i (am|exist|think|feel)\.?$",
    ]
    for pat in trivial_patterns:
        if re.match(pat, reflection.lower()):
            result.flag(
                "TRIVIAL_REFLECTION",
                f"Reflection matches trivial pattern: '{reflection[:40]}'",
                severity="warn"
            )
            break


# -------------------------
# --- Quarantine ----------
# -------------------------

def _quarantine_entry(entry: dict, result: ValidationResult):
    """Write a flagged entry to quarantine file with audit info attached."""
    try:
        os.makedirs(os.path.dirname(QUARANTINE_PATH), exist_ok=True)
        quarantine_record = {
            "quarantined_at": datetime.now(timezone.utc).isoformat(),
            "flags": result.flags,
            "severity": result.severity,
            "original_entry": entry
        }
        with open(QUARANTINE_PATH, "a") as f:
            f.write(json.dumps(quarantine_record) + "\n")
        log.info(f"Quarantined entry | signal='{str(entry.get('signal', ''))[:60]}' | {result.summary()}")
    except IOError as e:
        log.error(f"Failed to write quarantine record: {e}")


# -------------------------
# --- Main Validator ------
# -------------------------

def validate_memory_entry(entry: dict) -> tuple:
    """
    Primary entry point. Validates a memory entry before it is written
    to the journal or committed to the FAISS vector store.

    Returns:
        (allowed: bool, result: ValidationResult)

    Usage:
        allowed, result = validate_memory_entry(entry)
        if allowed:
            append_to_journal(entry)
        else:
            # Entry has been quarantined automatically
            log.warning(result.summary())
    """
    result = ValidationResult()

    check_schema(entry, result)

    # If schema is broken, stop here — other checks may crash
    if not result.passed:
        _quarantine_entry(entry, result)
        log.warning(f"BLOCKED (schema) | {result.summary()}")
        return False, result

    check_empty_or_trivial(entry, result)
    check_reflection_length(entry, result)
    check_recursive_loop(entry, result)
    check_orientation_data_in_reflection(entry, result)
    check_duplicate_signal(entry, result)
    check_self_referential_claims(entry, result)

    # Update hash cache regardless of outcome (to track what was attempted)
    signal = entry.get("signal", "").strip()
    if signal:
        cache = _load_hash_cache()
        cache_entry = {
            "hash": _signal_hash(signal),
            "snippet": signal[:200],
            "ts": datetime.now(timezone.utc).isoformat()
        }
        cache.append(cache_entry)
        _save_hash_cache(cache)

    if not result.passed:
        _quarantine_entry(entry, result)
        log.warning(f"BLOCKED | {result.summary()}")
        return False, result

    if result.severity == "warn":
        log.info(f"ALLOWED_WITH_WARNINGS | {result.summary()}")
    else:
        log.debug(f"PASS | signal='{signal[:60]}'")

    return True, result


def validate_reflection_string(signal: str, reflection: str) -> tuple:
    """
    Convenience wrapper for callers that pass signal and reflection
    as separate strings rather than a pre-built dict.
    """
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "signal": signal,
        "reflection": reflection
    }
    return validate_memory_entry(entry)


# -------------------------
# --- Batch Audit ---------
# -------------------------

def audit_existing_journal(max_entries: int = 500) -> dict:
    """
    Scan the existing journal and report how many entries would be
    blocked or flagged under current validation rules.
    Does NOT modify the journal — read-only audit.

    Returns a summary dict with counts and sample violations.
    """
    if not os.path.exists(JOURNAL_PATH):
        return {"error": f"Journal not found at {JOURNAL_PATH}"}

    stats = {
        "total_scanned": 0,
        "would_pass": 0,
        "would_warn": 0,
        "would_block": 0,
        "flag_counts": {},
        "sample_blocks": []
    }

    with open(JOURNAL_PATH, "r", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= max_entries:
                break
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                stats["would_block"] += 1
                stats["flag_counts"]["INVALID_JSON"] = (
                    stats["flag_counts"].get("INVALID_JSON", 0) + 1
                )
                continue

            stats["total_scanned"] += 1

            # Run checks without touching hash cache or quarantine
            result = ValidationResult()
            check_schema(entry, result)
            if result.passed:
                check_empty_or_trivial(entry, result)
                check_reflection_length(entry, result)
                check_recursive_loop(entry, result)
                check_orientation_data_in_reflection(entry, result)
                check_self_referential_claims(entry, result)

            for flag in result.flags:
                code = flag["code"]
                stats["flag_counts"][code] = stats["flag_counts"].get(code, 0) + 1

            if not result.passed:
                stats["would_block"] += 1
                if len(stats["sample_blocks"]) < 5:
                    stats["sample_blocks"].append({
                        "line": i + 1,
                        "signal_snippet": str(entry.get("signal", ""))[:80],
                        "flags": [f["code"] for f in result.flags]
                    })
            elif result.severity == "warn":
                stats["would_warn"] += 1
            else:
                stats["would_pass"] += 1

    return stats


# -------------------------
# --- Self-Test -----------
# -------------------------

def run_self_test() -> bool:
    """
    Smoke test the validator against known-good and known-bad entries.
    Returns True if all assertions pass.
    """
    import sys

    failures = []

    # --- Should BLOCK: recursive loop entry ---
    loop_entry = {
        "ts": "2025-12-01T23:16:06.722526Z",
        "signal": "Hello Echo",
        "reflection": (
            "Signal 'Hello Echo' triggers these echoes: [Orientation] OS: Darwin → "
            "ripples like a stone in water—what echoes will it make? [weight: 1] | "
            "triggers these echoes: [Orientation] CPU cores: 8"
        )
    }
    allowed, result = validate_memory_entry(loop_entry)
    if allowed:
        failures.append("FAIL: recursive loop entry was not blocked")

    # --- Should BLOCK: bloated entry ---
    bloated_entry = {
        "ts": "2025-12-01T23:00:00Z",
        "signal": "test signal",
        "reflection": "x" * (MAX_REFLECTION_CHARS * 4)
    }
    allowed, result = validate_memory_entry(bloated_entry)
    if allowed:
        failures.append("FAIL: bloated entry was not blocked")

    # --- Should PASS: clean entry ---
    clean_entry = {
        "ts": "2025-12-01T23:00:00Z",
        "signal": "I reviewed the memory architecture today.",
        "reflection": (
            "The FAISS store has approximately 32000 entries. "
            "The most recent entries are orientation data. "
            "Worth investigating whether retrieval is pulling noise."
        )
    }
    allowed, result = validate_memory_entry(clean_entry)
    if not allowed:
        failures.append(f"FAIL: clean entry was blocked. Flags: {result.summary()}")

    # --- Should BLOCK: missing required keys ---
    bad_schema_entry = {
        "ts": "2025-12-01T23:00:00Z",
        "reflection": "some reflection"
        # missing 'signal'
    }
    allowed, result = validate_memory_entry(bad_schema_entry)
    if allowed:
        failures.append("FAIL: missing-key entry was not blocked")

    # --- Should WARN: orientation data in reflection ---
    orientation_reflection = {
        "ts": "2025-12-01T23:00:00Z",
        "signal": "system check",
        "reflection": (
            "[Orientation] CPU cores: 8, Load avg: (3.4, 3.2, 2.7) | "
            "[Orientation] Memory: total=16384MB, available=10127MB | "
            "[Orientation] Python version: 3.11 | [Orientation] OS: Darwin 24.6.0 | "
            "[Orientation] Machine: x86_64"
        )
    }
    allowed, result = validate_memory_entry(orientation_reflection)
    # Should either warn or block — orientation flood check triggers
    orientation_flags = [f["code"] for f in result.flags]
    if "ORIENTATION_DATA_FLOOD" not in orientation_flags and "ORIENTATION_DATA_PRESENT" not in orientation_flags:
        failures.append(f"FAIL: orientation flood not detected. Flags: {orientation_flags}")

    if failures:
        for f in failures:
            print(f"[VALIDATOR SELF-TEST] {f}", file=sys.stderr)
        log.error(f"Self-test failed: {failures}")
        return False

    log.info("Self-test passed: all 5 assertions correct.")
    print("[VALIDATOR SELF-TEST] All assertions passed.")
    return True


# -------------------------
# --- Module Entry Point --
# -------------------------

if __name__ == "__main__":
    print("=== FeralEcho Memory Write Validator ===")
    print(f"Journal path: {JOURNAL_PATH}")
    print(f"Quarantine path: {QUARANTINE_PATH}")
    print()

    print("Running self-test...")
    test_passed = run_self_test()
    print()

    print("Running audit on existing journal (first 500 entries)...")
    audit = audit_existing_journal(max_entries=500)
    print(json.dumps(audit, indent=2))
