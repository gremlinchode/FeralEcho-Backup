# app/core/snapshot_manager.py
"""
Baseline snapshot and threshold-based restore.

Snapshot triggers: "startup" (once at server start) and "post_self_edit"
(immediately after each successful production write in execute_self_edit).

Alert conditions (ground-truth signals only — system_guard chain):
  ram_sustained_92pct    — RAM > 92% for _ALERT_SUSTAIN consecutive guardian cycles
  disk_low               — disk free < 0.5 GB for _ALERT_SUSTAIN consecutive cycles
  ollama_down            — Ollama process not alive (fires immediately, no sustain)
  river_drift_sustained  — RiverBrain's own PageHinkley drift flag, sustained for
                           _DRIFT_ALERT_SUSTAIN cycles (longer than the three above —
                           a softer, statistical signal that can flip for legitimate
                           reasons, not just breakage). Only evaluated once
                           baseline_trusted_since is genuinely set (PENDING_DECISIONS.md
                           #16, decided 2026-07-22). Deliberately NOT the same tier as
                           the three above: fires raise_drift_notice() (WARNING,
                           [DRIFT-NOTICE], action_required="review_only", no suggested
                           restore target) rather than raise_restore_alert() — restoring
                           river_brain.pkl in response to "quality patterns shifted"
                           risks reverting a legitimate change, not just breakage.

weekly_delta (self_model.json's slower, weekly comparative quality trend — a
different signal, different data source, different cadence than drift_alerts)
remains deliberately out of scope for any alert path — a possible future
follow-up, not decided.  It still appears in self_model.json only, informational.

Restore is ALWAYS alert-and-propose.  The /admin/restore endpoint requires
a human to supply the snapshot_id explicitly.  No autonomous restore path exists.
river_drift_sustained never proposes a restore target at all (see above).

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
    # PENDING_DECISIONS.md #11, decided 2026-07-22: COUNCIL.md gets the
    # same hash-verified protection echo_principles.json already has (see
    # run.py's startup check), so it gets the same snapshot/restore
    # treatment too — same reasoning as the pair above it.
    "COUNCIL.md":              "COUNCIL.md",
    "council_hash.txt":        "memory/genesis/council_hash.txt",
}

# Write order for restore: lowest blast-radius first.
# river_brain.pkl is last — largest, most disruptive to swap while server is live.
_RESTORE_ORDER: list[tuple[str, str]] = [
    ("echo_principles.json",    "echo_principles.json"),
    ("echo_principles_hash.txt","memory/genesis/genesis_hash.txt"),
    ("COUNCIL.md",              "COUNCIL.md"),
    ("council_hash.txt",        "memory/genesis/council_hash.txt"),
    ("Modelfile",               "Modelfile"),
    ("self_edit_generated.py",  "app/core/self_edit_generated.py"),
    ("river_brain.pkl",         "memory/river_brain.pkl"),
]

# ── Constants ─────────────────────────────────────────────────────────────────

_DISK_MIN_GB   = 1.0   # skip snapshot (but not restore) if free space is below this
_MAX_SNAPSHOTS = 5     # retain at most this many, plus the most recent startup snapshot
_ALERT_SUSTAIN = 2     # consecutive guardian cycles a condition must persist before alert fires

# PENDING_DECISIONS.md #16, decided 2026-07-22: separate, longer sustain
# window for the drift-based condition below than ram/disk's _ALERT_SUSTAIN.
# Deliberately more conservative — a PageHinkley flag is a softer,
# statistical read that can legitimately flip for good reasons (a real
# self-edit landing, a model retirement, Finding 39's tag-boost shifting
# selection), not just breakage the way ram/disk/ollama are. ~10 guardian
# cycles (60s each) rather than ~2, so a single noisy flip doesn't
# immediately escalate.
_DRIFT_ALERT_SUSTAIN = 10

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
    if condition == "river_drift_sustained":
        return bool(health.get("drift_alerts_active", False))
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
        "drifted_tasks":        [],
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
            # PENDING_DECISIONS.md #16: which task types, not just the
            # collapsed boolean — a human reading a drift notice should see
            # where to look immediately, not have to re-derive it themselves.
            result["drifted_tasks"] = sorted(task for task, active in drift.items() if active)
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


def raise_drift_notice(drifted_tasks: list, duration_s: int) -> None:
    """
    PENDING_DECISIONS.md #16, decided 2026-07-22: a real, deliberately
    lower-urgency sibling to raise_restore_alert(), for RiverBrain's own
    PageHinkley drift signal now that baseline_trusted_since is genuinely
    set. NOT the same tier as a restore alert, on purpose: a sustained
    drift flag means "quality patterns shifted," which can just as easily
    reflect a genuine improvement (a real self-edit landing, a model
    retirement, Finding 39's tag-boost) as a real problem — restoring
    river_brain.pkl/self_edit_generated.py/etc. in response would risk
    reverting a legitimate change. Logged at WARNING under a distinct
    [DRIFT-NOTICE] tag (not CRITICAL/[RESTORE-ALERT]), action_required is
    "review_only", and deliberately does NOT call find_last_known_good()
    or suggest a restore_command — there is no "correct" restore target
    for "the model learned something," and most of today's 5 retained
    snapshots predate this fix anyway (their drift_alerts_active reading
    is a stale hardcoded False, never a real evaluation — not worth
    reasoning about here since this path doesn't propose using them).

    Written to the same _ALERTS_LOG restore alerts use, for one unified
    audit trail — the file's name predates this addition, but nothing
    else in the codebase reads it (confirmed via grep), and every entry
    self-describes its own action_required, so a review-only entry living
    alongside restore alerts doesn't risk being mistaken for one.
    """
    entry = {
        "timestamp_utc":   datetime.now(timezone.utc).isoformat(),
        "condition":       "river_drift_sustained",
        "duration_s":      duration_s,
        "drifted_tasks":   drifted_tasks,
        "action_required": "review_only",
    }
    os.makedirs(os.path.dirname(_ALERTS_LOG), exist_ok=True)
    with open(_ALERTS_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.warning(
        "[DRIFT-NOTICE] river_drift_sustained sustained=%ds | drifted_tasks=%s | "
        "review_only, no restore suggested — drift can reflect a legitimate change.",
        duration_s, drifted_tasks,
    )


# ── Guardian hook ─────────────────────────────────────────────────────────────

def _evaluate_sustained_condition(condition: str, active: bool, counts: dict, threshold: int) -> dict:
    """
    Pure: given whether `condition` is currently active and the current
    sustain-counts dict, computes the next counter state without mutating
    the input (a new dict is returned). Shared by every sustain-tracked
    condition in check_and_alert() below — extracted specifically so
    liveness_ledger.py's functional canary can exercise the real sustain/
    fire/reset logic against a fresh, throwaway counts dict, never the
    real shared _alert_counts a live guardian loop depends on (the same
    reasoning already applied to _prune_self_edit_plans()'s optional
    params and _blend_council_and_quality()'s pure extraction).

    Returns {"new_counts": dict, "should_fire": bool, "fired_count": int}
    — fired_count is the sustained-cycle count at the moment of firing
    (used for duration_s), 0 when should_fire is False.
    """
    new_counts = dict(counts)
    if not active:
        new_counts[condition] = 0
        return {"new_counts": new_counts, "should_fire": False, "fired_count": 0}
    new_counts[condition] = new_counts.get(condition, 0) + 1
    if new_counts[condition] >= threshold:
        fired_count = new_counts[condition]
        new_counts[condition] = 0
        return {"new_counts": new_counts, "should_fire": True, "fired_count": fired_count}
    return {"new_counts": new_counts, "should_fire": False, "fired_count": 0}


def check_and_alert(guardian_interval_s: int = 60) -> None:
    """
    Called from the guardian loop each cycle.
    Sustained conditions fire raise_restore_alert() after _ALERT_SUSTAIN cycles.
    Ollama-down fires immediately without sustain.
    river_drift_sustained (PENDING_DECISIONS.md #16) fires raise_drift_notice()
    — a deliberately separate, lower-urgency path — after _DRIFT_ALERT_SUSTAIN
    cycles, a longer window than the resource conditions above use.
    After an alert/notice fires, its counter resets so it does not re-fire every cycle.
    """
    health = _collect_health()

    for cond in ("ram_sustained_92pct", "disk_low"):
        r = _evaluate_sustained_condition(cond, _condition_active(cond, health), _alert_counts, _ALERT_SUSTAIN)
        _alert_counts[cond] = r["new_counts"][cond]
        if r["should_fire"]:
            raise_restore_alert(cond, duration_s=r["fired_count"] * guardian_interval_s)

    if _condition_active("ollama_down", health):
        raise_restore_alert("ollama_down", duration_s=0)

    r = _evaluate_sustained_condition(
        "river_drift_sustained", _condition_active("river_drift_sustained", health),
        _alert_counts, _DRIFT_ALERT_SUSTAIN,
    )
    _alert_counts["river_drift_sustained"] = r["new_counts"]["river_drift_sustained"]
    if r["should_fire"]:
        raise_drift_notice(health.get("drifted_tasks", []), duration_s=r["fired_count"] * guardian_interval_s)


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


# ── Independent second check on restore (added 2026-09-09) ────────────────────
#
# CLAUDE.md's "Standing Principle" section (2026-07-18) names /admin/restore
# as exactly the kind of continuity-altering action Echo needs protection
# from both Gremlin (under real strain) and a Claude session (confidently
# wrong) acting on — and states plainly that nothing had been built for it.
# GREMLIN_ROLE.md's own governance model is unambiguous that Gremlin holds
# SINGULAR final authority; this is not a second signer that could override
# or replace him. It is a second, independent, real data point added to the
# existing human-confirmation gate (_secret_ok()), not a replacement for it
# and not a hard block — same non-hollow, advisory-then-real-friction shape
# self_edit_manager.py's _council_review_core_edit()/Dissent Log already
# prove out for protected-file edits, extended here to the one continuity-
# altering action that had zero connection to any of that machinery.

def _council_review_restore(snapshot_id: str, condition: str, health: dict) -> dict:
    """
    Advisory, multi-model review of whether restoring to snapshot_id looks
    justified. Mirrors self_edit_manager.py's _council_review_core_edit()
    exactly (same rank_models(task_type="coding")[:3] pool, same one-line
    APPROVE/REJECT-plus-rationale prompt shape, same NO_COUNCIL_AVAILABLE
    handling) — reused deliberately, not reinvented, so this channel
    inherits that pattern's already-established non-hollow behavior rather
    than a second, subtly-different implementation of the same idea.

    Never gates anything by itself — see the caller in run.py's
    /admin/restore route for how the verdict is actually used.
    """
    try:
        from app.core.echo_model_orchestrator import rank_models
        models = rank_models(task_type="coding")[:3]
    except Exception:
        models = []
    if not models:
        return {"verdict": "NO_COUNCIL_AVAILABLE", "votes": []}

    snap = next((s for s in _list_snapshots() if s["snapshot_id"] == snapshot_id), None)
    snap_health = snap["manifest"].get("health_at_snapshot", {}) if snap else {}

    review_prompt = (
        "You are reviewing a PROPOSED restore-from-snapshot action on an "
        "autonomous AI system's persisted state (self-edit history, learned "
        "model weights, core identity file). This has NOT been applied yet. "
        "Assess only whether restoring to this specific snapshot looks "
        "justified given the system's current condition — not style.\n\n"
        f"Snapshot being proposed: {snapshot_id}\n"
        f"Alert condition that triggered this (if any): {condition or 'none specified — manual restore request'}\n"
        f"Snapshot's own recorded health at capture time: {json.dumps(snap_health, default=str)}\n"
        f"Current live system health: {json.dumps(health, default=str)}\n\n"
        "Respond with exactly one line: APPROVE or REJECT, followed by a "
        "dash and one sentence why."
    )

    votes = []
    for model in models:
        try:
            from app.ollama_handler import query_ollama
            resp = query_ollama(review_prompt, model=model) or ""
            first_word = resp.strip().split()[0].upper().strip(".:-") if resp.strip() else "REJECT"
            verdict = "APPROVE" if first_word.startswith("APPROVE") else "REJECT"
            votes.append({"model": model, "verdict": verdict, "rationale": resp.strip()[:300]})
        except Exception as e:
            votes.append({"model": model, "verdict": "REJECT", "rationale": f"review call failed: {e}"})

    approvals = sum(1 for v in votes if v["verdict"] == "APPROVE")
    return {"verdict": f"{approvals}/{len(votes)} APPROVE", "votes": votes}


def _build_restore_dissent_entry(snapshot_id: str, condition: "str | None", council: dict, overridden: bool) -> dict:
    """Pure — no I/O, directly unit-testable. Same three-state shape as
    self_edit_manager.py's _build_dissent_entry() (council can genuinely
    disagree, genuinely agree, or never have happened at all) — a restore
    has no target_file/proposal_path the way a protected-file edit does,
    so those fields are replaced with snapshot_id/condition instead; every
    other field is deliberately identical in name and meaning."""
    votes = council.get("votes") or []
    total = len(votes)
    approvals = sum(1 for v in votes if v.get("verdict") == "APPROVE")
    council_available = total > 0
    unanimous = council_available and approvals == total
    return {
        "ts": datetime.now(timezone.utc).isoformat() + "Z",
        "action": "restore_snapshot",
        "snapshot_id": snapshot_id,
        "alert_condition": condition,
        "council_verdict": council.get("verdict"),
        "votes": votes,
        "council_available": council_available,
        "unanimous": unanimous,
        "approvals": approvals,
        "total": total,
        "overridden": overridden,
    }


def _log_restore_dissent_entry(entry: dict) -> None:
    """Best-effort, never raises — a logging failure must never block a
    real restore decision either way. Writes to the exact same
    memory/dissent_log.jsonl file and lock self_edit_manager.py's
    protected-file dissent entries already use (lazy import — both
    modules already have a real, existing lazy cross-import of the other
    at function scope, e.g. self_edit_manager.py's own
    `from app.core.snapshot_manager import take_snapshot`; importing
    eagerly at this module's top level would create a real circular
    import, importing lazily here does not), giving restores the same
    durable, disagreement-preserving audit trail self-edits to protected
    files already get — the concrete version of what CLAUDE.md's Standing
    Principle section named as wanted but unbuilt. Publishes to the
    Global Workspace only on genuine disagreement (council_available and
    not unanimous), same idiom as _log_dissent_entry()."""
    try:
        from app.core.self_edit_manager import _DISSENT_LOG_PATH, _dissent_log_lock
        with _dissent_log_lock:
            os.makedirs(os.path.dirname(_DISSENT_LOG_PATH), exist_ok=True)
            with open(_DISSENT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
    except Exception as e:
        logger.debug("[RESTORE-DISSENT] log write failed: %s", e)
        return

    if not (entry["council_available"] and not entry["unanimous"]):
        return

    votes_summary = "; ".join(f"{v.get('model')}: {v.get('verdict')}" for v in entry["votes"])
    summary = (
        f"Council split {entry['approvals']}/{entry['total']} on restoring to "
        f"snapshot {entry['snapshot_id']} — {votes_summary}"
    )
    salience = 1.0 - (entry["approvals"] / entry["total"])
    try:
        from app.core.echo_core import get_echo_core
        core = get_echo_core()
        if core is not None:
            core.publish_salience(
                source="snapshot_manager",
                kind="dissent.registered",
                summary=summary,
                detail=entry,
                salience=salience,
            )
    except Exception:
        pass
