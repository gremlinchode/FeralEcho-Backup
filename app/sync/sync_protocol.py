"""
sync_protocol.py — Echo M5 sync node.
Partner: Echo Air at 100.82.172.4
"""

import os, json, hashlib, time, uuid, logging, inspect
import requests
from typing import List, Dict

logger = logging.getLogger(__name__)

BASE_DIR            = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
MEMORY_DIR          = os.path.join(BASE_DIR, "memory")
INTERACTION_LOG     = os.path.join(MEMORY_DIR, "interaction_log.jsonl")
SYNC_STATE_PATH     = os.path.join(MEMORY_DIR, "sync_state.json")
SEEN_HASHES_PATH    = os.path.join(MEMORY_DIR, "sync_seen.jsonl")
GENESIS_DIR         = os.path.join(MEMORY_DIR, "genesis")
PARTNER_URL         = os.getenv("ECHO_PARTNER_URL", "http://100.82.172.4:5000")
QUALITY_FLOOR       = 0.3
LOCAL_ONLY_SOURCES  = {"self_edit"}

# Detect whether memory_bridge.log_dream_bridge accepts meta kwarg
try:
    from app.core.memory_bridge import log_dream_bridge as _ldb
    _HAS_META = "meta" in inspect.signature(_ldb).parameters
except Exception:
    _ldb = None
    _HAS_META = False

def _log_dream(text: str, meta: dict) -> None:
    if _ldb is None:
        return
    try:
        if _HAS_META:
            _ldb(text, meta=meta)
        else:
            _ldb(text)
    except Exception as e:
        logger.warning(f"[SYNC] log_dream_bridge failed: {e}")

def _load_state() -> dict:
    try:
        return json.loads(open(SYNC_STATE_PATH).read()) if os.path.exists(SYNC_STATE_PATH) else {}
    except Exception:
        return {}

def _save_state(s: dict):
    open(SYNC_STATE_PATH, "w").write(json.dumps(s, indent=2))

def get_last_sync(url: str) -> float:
    return _load_state().get(url, 0.0)

def set_last_sync(url: str, ts: float):
    s = _load_state(); s[url] = ts; _save_state(s)

def _load_seen() -> set:
    if not os.path.exists(SEEN_HASHES_PATH):
        return set()
    return {l.strip() for l in open(SEEN_HASHES_PATH) if l.strip()}

def _save_seen(hashes: set):
    open(SEEN_HASHES_PATH, "w").write("\n".join(hashes))

def _entry_text(e: dict) -> str:
    p = e.get("prompt_preview", "").strip()
    r = e.get("response_preview", "").strip()
    return f"User: {p}\nEcho: {r}" if p and r else r or p or ""

def export_since(since_ts: float) -> List[Dict]:
    entries = []
    if not os.path.exists(INTERACTION_LOG):
        return entries
    for line in open(INTERACTION_LOG):
        try:
            e = json.loads(line.strip())
        except Exception:
            continue
        ts = e.get("timestamp", 0)
        if isinstance(ts, str):
            try:
                from datetime import datetime, timezone
                ts = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp()
            except Exception:
                ts = 0.0
        if float(ts) <= since_ts:
            continue
        if float(e.get("quality_score", 0)) < QUALITY_FLOOR:
            continue
        source = e.get("memory_source") or e.get("notes") or "echo"
        if source in LOCAL_ONLY_SOURCES:
            continue
        text = _entry_text(e)
        if not text:
            continue
        entries.append({
            "id": str(uuid.uuid4()),
            "timestamp": float(ts),
            "text": text,
            "quality_score": float(e.get("quality_score", 0.5)),
            "memory_source": source,
            "origin": "m5",
        })
    return entries

def import_entries(entries: List[Dict]) -> int:
    seen = _load_seen()
    merged = 0
    for entry in entries:
        text = entry.get("text", "").strip()
        if not text or len(text) < 20:
            continue
        if float(entry.get("quality_score", 0)) < QUALITY_FLOOR:
            continue
        if entry.get("memory_source") in LOCAL_ONLY_SOURCES:
            continue
        h = hashlib.sha256(text.encode()).hexdigest()
        if h in seen:
            continue
        origin = entry.get("origin", "partner")
        _log_dream(text, {"memory_source": f"sync_{origin}", "sync_ts": entry.get("timestamp", time.time())})
        seen.add(h)
        merged += 1
    _save_seen(seen)
    logger.info(f"[SYNC] Merged {merged}/{len(entries)} entries.")
    return merged

def partner_reachable(timeout=5) -> bool:
    try:
        return requests.get(f"{PARTNER_URL}/health", timeout=timeout).status_code == 200
    except Exception:
        return False

def run_sync_cycle() -> dict:
    if not partner_reachable():
        return {"status": "partner_unreachable"}
    summary = {"status": "ok", "pushed": 0, "pulled": 0}
    now = time.time()
    last = get_last_sync(PARTNER_URL)
    try:
        r = requests.get(f"{PARTNER_URL}/sync/export", params={"since": last}, timeout=120)
        if r.status_code == 200:
            summary["pulled"] = import_entries(r.json().get("entries", []))
        our = export_since(last)
        if our:
            batch_size = 200
            for i in range(0, len(our), batch_size):
                batch = our[i:i + batch_size]
                try:
                    r = requests.post(f"{PARTNER_URL}/sync/import", json={"entries": batch}, timeout=120)
                    if r.status_code == 200:
                        summary["pushed"] += r.json().get("merged", 0)
                except Exception as _be:
                    logger.warning(f"[SYNC] Batch {i//batch_size} failed: {_be}")
                    break
        set_last_sync(PARTNER_URL, now)
        logger.info(f"[SYNC] pushed={summary['pushed']} pulled={summary['pulled']}")
    except Exception as e:
        summary["status"] = "error"; summary["error"] = str(e)
    return summary
