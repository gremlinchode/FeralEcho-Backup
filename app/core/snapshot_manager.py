# app/core/snapshot_manager.py
"""
Baseline snapshot and threshold-based restore.

Snapshot triggers: "startup" (once at server start) and "post_self_edit"
(immediately after each successful production write in execute_self_edit).

Alert conditions (ground-truth signals only — system_guard chain):
  ram_sustained_92pct  — RAM > 92% for _ALERT_SUSTAIN consecutive guardian cycles
  disk_low             — disk free < 0.5 GB for _ALERT_SUSTAIN consecutive cycles
  ollama_down          — Ollama process not alive (fires immediately, no sustain)

Drift signals (drift_alerts, weekly_delta) are intentionally excluded as
alert triggers until baseline_trusted_since is set in snapshot_baseline.json
following a clean PageHinkley observation window.  They appear in manifest
health_at_snapshot as informational only until that flag is set.

Restore is ALWAYS alert-and-propose.  The /admin/restore endpoint requires
a human to supply the snapshot_id explicitly.  No autonomous restore path exists.

river_brain.pkl is handled as opaque bytes throughout this module.
pickle.load() is never called here — only sha256 streaming reads.
"""

import hashlib
import json
import logging
import os
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

_PROJECT_ROOT  = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
_SNAPSHOTS_DIR = os.path.join(_PROJECT_ROOT, "memory", "snapshots")
_ALERTS_LOG    = os.path.join(_PROJECT_ROOT, "memory", "restore_alerts.jsonl")
_RESTORE_LOG   = os.path.join(_PROJECT_ROOT, "memory", "restore_log.jsonl")
_BASELINE_META = os.path.join(_PROJECT_ROOT, "memory", "snapshot_baseline.json")
_INTROSPECTION = os.path.join(_PROJECT_ROOT, "memory", "introspection_state.json")

# Serialises all writes to snapshot_baseline.json so concurrent writers
# (snapshot_manager and council_rater) cannot overwrite each other's fields.
_baseline_meta_lock = threading.Lock()

# ── Artifacts ─────────────────────────────────────────────────────────────────
# dest_name (filename inside snapshot dir) → src path relative to _PROJECT_ROOT

_ARTIFACTS: dict[str, str] = {
    "self_edit_generated.py":  "app/core/self_edit_generated.py",
    "river_brain.pkl":         "memory/river_brain.pkl",
    "echo_principles.json":    "echo_principles.json",
    "echo_principles_hash.txt":"memory/genesis/genesis_hash.txt",
    "Modelfile":               "Modelfile",
}

# Write order for restore: lowest blast-radius first.
# river_brain.pkl is last — largest, most disruptive to swap while server is live.
_RESTORE_ORDER: list[tuple[str, str]] = [
    ("echo_principles.json",    "echo_principles.json"),
    ("echo_principles_hash.txt","memory/genesis/genesis_hash.txt"),
    ("Modelfile",               "Modelfile"),
    ("self_edit_generated.py",  "app/core/self_edit_generated.py"),
    ("river_brain.pkl",         "memory/river_brain.pkl"),
]

# ── Constants ─────────────────────────────────────────────────────────────────

_DISK_MIN_GB   = 1.0   # skip snapshot (but not restore) if free space is below this
_MAX_SNAPSHOTS = 5     # retain at most this many, plus the most recent startup snapshot
_ALERT_SUSTAIN = 2     # consecutive guardian cycles a condition must persist before alert fires

# ── Alert state ───────────────────────────────────────────────────────────────
# In-memory only — resets on server restart.  Deliberate: a restart clears transient spikes.

_alert_counts: dict[str, int] = {}


# ── Condition predicates ──────────────────────────────────────────────────────

def _condition_active(condition: str, health: dict) -> bool:
    if condition == "ram_sustained_92pct":
        return health.get("ram_pct", 0) > 92
    if condition == "disk_low":
        return health.get("disk_free_gb", 99) < 0.5
    if condition == "ollama_down":
        return not health.get("ollama_alive", True)
    return False


def _snapshot_was_healthy(condition: str, health_at_snapshot: dict) -> bool:
    """True if the snapshot was taken when the alert condition was NOT active."""
    return not _condition_active(condition, health_at_snapshot)


# ── Health reading ────────────────────────────────────────────────────────────

def _collect_health() -> dict:
    """
    Read current system health directly from psutil for ground-truth freshness.
    Drift signals are added only when baseline_trusted_since is set.
    """
    result: dict = {
        "ram_pct":              0.0,
        "disk_free_gb":         0.0,
        "load_avg_1m":          0.0,
        "ollama_alive":         True,
        "drift_alerts_active":  False,
        "trusted_signals_only": False,
    }
    try:
        import psutil
        vm = psutil.virtual_memory()
        result["ram_pct"] = round(vm.percent, 1)
        mem_dir = os.path.join(_PROJECT_ROOT, "memory")
        du = psutil.disk_usage(mem_dir if os.path.isdir(mem_dir) else _PROJECT_ROOT)
        result["disk_free_gb"] = round(du.free / (1024 ** 3), 2)
        result["load_avg_1m"]  = round(psutil.getloadavg()[0], 2)
        result["ollama_alive"] = any(
            "ollama" in (p.info.get("name") or "").lower()
            for p in psutil.process_iter(["name"])
        )
    except Exception as e:
        logger.debug("[Snapshot] psutil health read failed: %s", e)

    try:
        baseline = _read_baseline_meta()
        if baseline.get("baseline_trusted_since"):
            result["trusted_signals_only"] = True
            with open(_INTROSPECTION, encoding="utf-8") as fh:
                state = json.load(fh)
            drift = state.get("river_brain", {}).get("drift_alerts", {})
            result["drift_alerts_active"] = any(drift.values())
    except Exception:
        pass

    return result


# ── Baseline meta ─────────────────────────────────────────────────────────────

def _read_baseline_meta() -> dict:
    try:
        if os.path.exists(_BASELINE_META):
            with open(_BASELINE_META, encoding="utf-8") as fh:
                return json.load(fh)
    except Exception:
        pass
    return {}


def patch_baseline_meta(key: str, value) -> None:
    """Thread-safe single-field update for snapshot_baseline.json.

    Acquires _baseline_meta_lock, reads current state, sets key=value,
    and atomically writes via temp-file swap. Concurrent callers
    (snapshot_manager and council_rater) cannot overwrite each other's fields.
    All baseline writes must go through this function.
    """
    with _baseline_meta_lock:
        meta = _read_baseline_meta()
        meta[key] = value
        os.makedirs(os.path.dirname(_BASELINE_META), exist_ok=True)
        tmp = _BASELINE_META + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2)
        os.replace(tmp, _BASELINE_META)
    logger.info("[Snapshot] patch_baseline_meta: %s", key)


def mark_baseline_trusted(since_utc: str) -> None:
    """
    Call once the PageHinkley detectors have completed their clean-observation
    window after reset_drift_detectors() (minimum 30 observations per task type).
    After this, drift_alerts appear as a trusted signal in snapshot manifests.
    """
    patch_baseline_meta("baseline_trusted_since", since_utc)
    logger.info("[Snapshot] baseline_trusted_since set to %s", since_utc)


# ── SHA-256 (bytes-only) ──────────────────────────────────────────────────────

def _sha256_file(path: str) -> str:
    """
    Stream raw bytes through sha256.  Never calls any file-format loader.
    Safe for .pkl, .py, .json, and any other artifact — including river_brain.pkl,
    which is NEVER unpickled by this module.
    """
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Snapshot listing ──────────────────────────────────────────────────────────

def _list_snapshots() -> list[dict]:
    """Return all valid snapshots, sorted newest-to-oldest."""
    if not os.path.isdir(_SNAPSHOTS_DIR):
        return []
    results = []
    for name in sorted(os.listdir(_SNAPSHOTS_DIR), reverse=True):
        manifest_path = os.path.join(_SNAPSHOTS_DIR, name, "manifest.json")
        if not os.path.isfile(manifest_path):
            continue
        try:
            with open(manifest_path, encoding="utf-8") as fh:
                manifest = json.load(fh)
            results.append({"snapshot_id": name, "manifest": manifest})
        except Exception:
            continue
    return results


def list_snapshots() -> list[dict]:
    """Public: summary of all available snapshots (id, trigger, timestamp, health)."""
    return [
        {
            "snapshot_id": s["snapshot_id"],
            "trigger":     s["manifest"].get("trigger"),
            "timestamp":   s["manifest"].get("timestamp_utc"),
            "health":      s["manifest"].get("health_at_snapshot"),
        }
        for s in _list_snapshots()
    ]


# ── Snapshot pruning ──────────────────────────────────────────────────────────

def _prune_snapshots() -> None:
    """
    Retain the _MAX_SNAPSHOTS most recent snapshots, plus the most recent
    startup snapshot if it falls outside that window (max _MAX_SNAPSHOTS + 1 total).
    """
    all_snaps = _list_snapshots()  # already newest-to-oldest
    keep: set[str] = set()

    for s in all_snaps[:_MAX_SNAPSHOTS]:
        keep.add(s["snapshot_id"])

    for s in all_snaps:
        if s["manifest"].get("trigger") == "startup":
            keep.add(s["snapshot_id"])
            break

    for s in all_snaps:
        if s["snapshot_id"] not in keep:
            snap_dir = os.path.join(_SNAPSHOTS_DIR, s["snapshot_id"])
            try:
                shutil.rmtree(snap_dir)
                logger.debug("[Snapshot] Pruned: %s", s["snapshot_id"])
            except Exception as e:
                logger.warning("[Snapshot] Prune failed for %s: %s", s["snapshot_id"], e)


# ── Take snapshot ─────────────────────────────────────────────────────────────

def take_snapshot(trigger: str) -> "str | None":
    """
    Capture artifacts and health state.  Returns snapshot_id or None on failure.

    Skips (without error) if disk_free_gb < _DISK_MIN_GB — the snapshot
    system must not compound a disk-space emergency with additional writes.
    Restore is exempt from this check (it replaces files in-place, net-neutral).
    """
    try:
        import psutil
        mem_dir = os.path.join(_PROJECT_ROOT, "memory")
        du = psutil.disk_usage(mem_dir if os.path.isdir(mem_dir) else _PROJECT_ROOT)
        disk_free_gb = du.free / (1024 ** 3)
        if disk_free_gb < _DISK_MIN_GB:
            logger.warning(
                "[Snapshot] Skipping %s snapshot — disk %.2f GB < %.1f GB floor",
                trigger, disk_free_gb, _DISK_MIN_GB,
            )
            return None
    except Exception as e:
        logger.debug("[Snapshot] Pre-snapshot disk check failed: %s", e)

    snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snap_dir = os.path.join(_SNAPSHOTS_DIR, snapshot_id)

    try:
        os.makedirs(snap_dir, exist_ok=True)
        artifacts_meta: dict = {}

        for dest_name, src_rel in _ARTIFACTS.items():
            src = os.path.join(_PROJECT_ROOT, src_rel)
            if not os.path.exists(src):
                logger.warning("[Snapshot] Artifact missing, skipping: %s", src_rel)
                continue
            dest = os.path.join(snap_dir, dest_name)
            shutil.copy2(src, dest)
            artifacts_meta[dest_name] = {
                "src":        src_rel,
                "size_bytes": os.path.getsize(dest),
                "sha256":     _sha256_file(dest),  # bytes-only, no pickle.load
            }

        manifest = {
            "snapshot_id":        snapshot_id,
            "trigger":            trigger,
            "timestamp_utc":      datetime.now(timezone.utc).isoformat(),
            "artifacts":          artifacts_meta,
            "health_at_snapshot": _collect_health(),
        }
        with open(os.path.join(snap_dir, "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)

        logger.info("[Snapshot] %s snapshot: %s", trigger, snapshot_id)
        _prune_snapshots()
        return snapshot_id

    except Exception as e:
        logger.error("[Snapshot] take_snapshot(%s) failed: %s", trigger, e)
        shutil.rmtree(snap_dir, ignore_errors=True)
        return None


# ── Find last known good ──────────────────────────────────────────────────────

def find_last_known_good(alert_condition: str) -> "str | None":
    """
    Scan snapshots newest-to-oldest.  Return the first snapshot_id whose
    health_at_snapshot shows the system was NOT in the given alert condition
    at capture time.

    This ensures the suggested restore target is a point the system was
    actually healthy, not just the most recent snapshot (which may already
    show the same degraded condition that triggered the alert).
    """
    for s in _list_snapshots():
        health = s["manifest"].get("health_at_snapshot", {})
        if _snapshot_was_healthy(alert_condition, health):
            return s["snapshot_id"]
    logger.warning(
        "[Snapshot] find_last_known_good(%s): no healthy snapshot found", alert_condition
    )
    return None


# ── Alert ─────────────────────────────────────────────────────────────────────

def raise_restore_alert(condition: str, duration_s: int) -> None:
    suggested = find_last_known_good(condition)
    restore_cmd = (
        f'POST /admin/restore  {{"snapshot_id": "{suggested}"}}'
        if suggested else "no_healthy_snapshot_available"
    )
    entry = {
        "timestamp_utc":      datetime.now(timezone.utc).isoformat(),
        "condition":          condition,
        "duration_s":         duration_s,
        "suggested_snapshot": suggested,
        "action_required":    "human_confirm",
        "restore_command":    restore_cmd,
    }
    os.makedirs(os.path.dirname(_ALERTS_LOG), exist_ok=True)
    with open(_ALERTS_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.critical(
        "[RESTORE-ALERT] condition=%s sustained=%ds | suggested=%s | %s",
        condition, duration_s, suggested, restore_cmd,
    )


# ── Guardian hook ─────────────────────────────────────────────────────────────

def check_and_alert(guardian_interval_s: int = 60) -> None:
    """
    Called from the guardian loop each cycle.
    Sustained conditions fire raise_restore_alert() after _ALERT_SUSTAIN cycles.
    Ollama-down fires immediately without sustain.
    After an alert fires, the counter resets so it does not re-alert every cycle.
    """
    health = _collect_health()

    for cond in ("ram_sustained_92pct", "disk_low"):
        if _condition_active(cond, health):
            _alert_counts[cond] = _alert_counts.get(cond, 0) + 1
            if _alert_counts[cond] >= _ALERT_SUSTAIN:
                raise_restore_alert(cond, duration_s=_alert_counts[cond] * guardian_interval_s)
                _alert_counts[cond] = 0
        else:
            _alert_counts[cond] = 0

    if _condition_active("ollama_down", health):
        raise_restore_alert("ollama_down", duration_s=0)


# ── Restore ───────────────────────────────────────────────────────────────────

def restore_snapshot(snapshot_id: str) -> dict:
    """
    Restore artifacts from snapshot_id.

    Steps (fail-closed — each step aborts on error without touching later artifacts):
      1. Manifest integrity:       sha256 every artifact in the snapshot (bytes-only)
      2. Principles hash:          sha256(echo_principles.json) == echo_principles_hash.txt
      3. Ollama alive:             confirm Ollama is running before touching pkl
      4. Atomic writes:            os.replace() in blast-radius order (lowest first)
      5. Post-restore verify:      sha256 each replaced file against manifest
      6. Log:                      append result to restore_log.jsonl

    river_brain.pkl is copied as opaque bytes.  pickle.load() is never called
    at any point in this function — not during verification, not during restore.

    If the restore fails partway through Step 4, result["artifacts"] records
    exactly which files were and were not replaced.  Files not yet replaced
    remain at their pre-restore state (safe).
    """
    result: dict = {
        "snapshot_id":   snapshot_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "steps":         {},
        "artifacts":     {},
        "success":       False,
        "error":         None,
    }

    snap_dir      = os.path.join(_SNAPSHOTS_DIR, snapshot_id)
    manifest_path = os.path.join(snap_dir, "manifest.json")

    # Step 1: Load manifest and verify all artifact sha256 (bytes-only)
    try:
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except Exception as e:
        result["error"] = f"manifest_unreadable: {e}"
        result["steps"]["1_integrity"] = "FAILED"
        _log_restore(result)
        return result

    mismatches: list[str] = []
    for name, meta in manifest.get("artifacts", {}).items():
        art_path = os.path.join(snap_dir, name)
        if not os.path.exists(art_path):
            mismatches.append(f"{name}: file_missing")
            continue
        expected = meta.get("sha256", "")
        actual   = _sha256_file(art_path)  # bytes-only — river_brain.pkl never unpickled
        if actual != expected:
            mismatches.append(f"{name}: sha256_mismatch")

    if mismatches:
        result["error"] = f"snapshot_corrupt: {mismatches}"
        result["steps"]["1_integrity"] = f"FAILED: {mismatches}"
        _log_restore(result)
        return result
    result["steps"]["1_integrity"] = "OK"

    # Step 2: Verify echo_principles hash
    principles_snap = os.path.join(snap_dir, "echo_principles.json")
    hash_snap       = os.path.join(snap_dir, "echo_principles_hash.txt")
    try:
        expected_hash = Path(hash_snap).read_text(encoding="utf-8").strip()
        actual_hash   = _sha256_file(principles_snap)  # bytes-only
        if actual_hash != expected_hash:
            result["error"] = "principles_hash_mismatch"
            result["steps"]["2_principles_hash"] = "FAILED"
            _log_restore(result)
            return result
    except Exception as e:
        result["error"] = f"principles_hash_check_failed: {e}"
        result["steps"]["2_principles_hash"] = "FAILED"
        _log_restore(result)
        return result
    result["steps"]["2_principles_hash"] = "OK"

    # Step 3: Confirm Ollama is alive before touching river_brain.pkl
    health = _collect_health()
    if not health.get("ollama_alive", True):
        result["error"] = "ollama_not_alive_before_restore"
        result["steps"]["3_ollama_alive"] = "FAILED"
        _log_restore(result)
        return result
    result["steps"]["3_ollama_alive"] = "OK"

    # Step 4: Atomic writes — lowest blast-radius first
    for snap_name, dest_rel in _RESTORE_ORDER:
        src = os.path.join(snap_dir, snap_name)
        if not os.path.exists(src):
            result["artifacts"][snap_name] = "skipped_not_in_snapshot"
            continue
        dst = os.path.join(_PROJECT_ROOT, dest_rel)
        tmp = dst + ".restore_tmp"
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, tmp)
            os.replace(tmp, dst)  # atomic on POSIX — file is either old or new, never partial
            result["artifacts"][snap_name] = "replaced"
        except Exception as e:
            result["artifacts"][snap_name] = f"FAILED: {e}"
            result["error"]  = f"write_failed at {snap_name}: {e}"
            result["steps"]["4_writes"] = f"PARTIAL — stopped at {snap_name}"
            logger.error(
                "[RESTORE] Write failed at %s — halting. Already replaced: %s",
                snap_name,
                [k for k, v in result["artifacts"].items() if v == "replaced"],
            )
            _log_restore(result)
            return result
    result["steps"]["4_writes"] = "OK"

    # Step 5: Post-restore integrity verify (bytes-only — river_brain.pkl never unpickled)
    post_mismatches: list[str] = []
    for snap_name, dest_rel in _RESTORE_ORDER:
        if result["artifacts"].get(snap_name) != "replaced":
            continue
        dst      = os.path.join(_PROJECT_ROOT, dest_rel)
        expected = manifest.get("artifacts", {}).get(snap_name, {}).get("sha256", "")
        actual   = _sha256_file(dst)
        if actual != expected:
            post_mismatches.append(snap_name)

    if post_mismatches:
        result["steps"]["5_post_verify"] = f"FAILED: {post_mismatches}"
        result["error"] = f"post_restore_verify_failed: {post_mismatches}"
        logger.critical(
            "[RESTORE] Post-restore sha256 mismatch on %s — manual inspection required",
            post_mismatches,
        )
        _log_restore(result)
        return result
    result["steps"]["5_post_verify"] = "OK"

    # Step 6: Log
    result["success"] = True
    result["steps"]["6_logged"] = "OK"
    _log_restore(result)
    logger.info("[RESTORE] Snapshot %s restored successfully.", snapshot_id)
    return result


# ── Restore log ───────────────────────────────────────────────────────────────

def _log_restore(result: dict) -> None:
    os.makedirs(os.path.dirname(_RESTORE_LOG), exist_ok=True)
    with open(_RESTORE_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(result, ensure_ascii=False, default=str) + "\n")
