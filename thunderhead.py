print("LOADED FROM:", __file__)
# feral_echo_symbiote.py — CLEAN HEADLESS EDITION v2

import os
import sys
import time
import threading
import json
import math
import hashlib
import random
import re
from datetime import datetime
from collections import deque

# ============================================================
# iOS SAFE PATHS
# ============================================================
_DOCS = os.path.expanduser("~/Documents")
os.makedirs(_DOCS, exist_ok=True)

# ============================================================
# OPTIONAL IMPORTS
# ============================================================
HAS_REQUESTS     = False
HAS_CLIP         = False
HAS_LOCATION     = False
HAS_MOTION       = False
HAS_DEVICE       = False
HAS_NOTIFICATION = False

try:
    import requests
    HAS_REQUESTS = True
except Exception:
    pass

try:
    import clipboard
    HAS_CLIP = True
except Exception:
    pass

try:
    import location
    location.start_updating()
    HAS_LOCATION = True
except Exception:
    pass

try:
    import motion
    motion.start_updating()
    HAS_MOTION = True
except Exception:
    pass

# ============================================================
# CONFIGURATION
# ============================================================
# NOTE: single-host for now, points at M5 (100.84.229.10) — was previously
# 100.82.172.4 (Air), which this phone script could never actually reach
# during 2026-07-18's session, explaining a real "mac_reachable: False"/
# silent-failure incident. Real multi-host failover (try both, rely on
# neither) is a good future idea, deliberately not built here — it needs a
# proper refactor of every function below that hardcodes MACBOOK_IP, not a
# tonight-sized change. See CLAUDE.md Finding 42.
MACBOOK_IP   = "100.84.229.10"
MACBOOK_PORT = 5000

# GREMLIN_SECRET gates /learning_event and /learning_batch as of the 2026-07-11
# bug-hunt security fixes — copy the same value from the Mac's .env (GREMLIN_SECRET=...)
# here. Phone environments don't inherit that .env, so this can't be read from
# os.environ like the server side does; fill in the literal value.
THUNDERHEAD_SECRET = ""

EVENT_LOG    = os.path.join(_DOCS, "symbiote_events.jsonl")
CONTEXT_FILE = os.path.join(_DOCS, "symbiote_context.json")
CMD_FILE     = os.path.join(_DOCS, "symbiote_cmd.txt")
STATUS_FILE  = os.path.join(_DOCS, "symbiote_status.json")
BUNDLE_FILE  = os.path.join(_DOCS, "symbiote_bundle.jsonl")
MEMORY_FILE  = os.path.join(_DOCS, "symbiote_memory.json")
REPLY_FILE   = os.path.join(_DOCS, "symbiote_reply.txt")

MAX_TEXT        = 2000
MAX_VECTORS     = 3000
MAX_ENTROPY_WIN = 100

HEARTBEAT_BASE  = 300
CLIPBOARD_POLL  = 2.0
SENSOR_POLL     = 30.0   # was 10s — reduced since sensor updates go to status, not FAISS
CMD_POLL        = 3.0
SAVE_INTERVAL   = 120.0
BUNDLE_INTERVAL = 300    # was 1800s — check for reconnect more often

DUPE_THRESHOLD  = 0.93

# Minimum distance (metres) before a location change is worth logging as a memory
LOCATION_MEMORY_THRESHOLD = 200

# ============================================================
# UTILITIES
# ============================================================
def safe_float(val, default=0.0):
    try:
        v = float(val)
        return v if math.isfinite(v) else default
    except Exception:
        return default

def safe_json(val):
    if val is None: return None
    if isinstance(val, bool): return val
    if isinstance(val, int): return val
    if isinstance(val, float): return val if math.isfinite(val) else 0.0
    if isinstance(val, (list, tuple)): return [safe_json(v) for v in val]
    if isinstance(val, dict): return {str(k): safe_json(v) for k, v in val.items()}
    if hasattr(val, "tolist"):
        try: return safe_json(val.tolist())
        except Exception: pass
    return str(val)

def atomic_write(path, data_bytes):
    tmp = path + ".tmp"
    try:
        with open(tmp, "wb") as f:
            f.write(data_bytes)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        return True
    except Exception as e:
        _log(f"[ATOMIC_WRITE ERROR] {path}: {e}")
        return False

def _log(msg):
    try:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}", flush=True)
    except Exception:
        pass

# ============================================================
# LIGHTWEIGHT EMBEDDING
# ============================================================
def embed(text, dim=64):
    """Deterministic embedding using SHA256. Good for dedup, not semantic search."""
    try:
        raw = hashlib.sha256(text.lower().encode("utf-8")).digest()
        vec = [float(b) / 255.0 for b in raw]
        while len(vec) < dim:
            vec.extend(vec[:dim - len(vec)])
        return vec[:dim]
    except Exception as e:
        _log(f"[EMBED ERROR] {e}")
        return [0.0] * dim

# ============================================================
# VECTOR MEMORY  (persisted across sessions)
# ============================================================

class VectorMemory:
    def __init__(self, max_size=MAX_VECTORS):
        self.max_size = max_size
        self.vectors  = []
        self.texts    = []
        self.metas    = []

    def cosine_sim(self, a, b):
        try:
            dot   = sum(x * y for x, y in zip(a, b))
            mag_a = math.sqrt(sum(x * x for x in a))
            mag_b = math.sqrt(sum(x * x for x in b))
            if mag_a == 0 or mag_b == 0:
                return 0.0
            return dot / (mag_a * mag_b)
        except Exception:
            return 0.0

    def add(self, text, vec, meta=None):
        if len(self.vectors) >= self.max_size:
            self.vectors.pop(0)
            self.texts.pop(0)
            self.metas.pop(0)
        self.vectors.append(vec)
        self.texts.append(text)
        self.metas.append(meta or {})

    def search(self, vec, top_k=3):
        if not self.vectors:
            return []
        scored = [(self.cosine_sim(vec, v), i) for i, v in enumerate(self.vectors)]
        scored.sort(reverse=True)
        return [(self.texts[i], self.metas[i], s) for s, i in scored[:top_k]]

    def is_duplicate(self, vec, threshold=DUPE_THRESHOLD):
        for v in self.vectors:
            if self.cosine_sim(vec, v) >= threshold:
                return True
        return False

    def save(self):
        try:
            data = {"texts": self.texts, "metas": self.metas, "vectors": self.vectors}
            atomic_write(MEMORY_FILE, json.dumps(data).encode())
        except Exception as e:
            _log(f"[MEMORY SAVE ERROR] {e}")

    def load(self):
        try:
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE) as f:
                    data = json.load(f)
                self.texts   = data.get("texts", [])
                self.metas   = data.get("metas", [])
                self.vectors = data.get("vectors", [])
                _log(f"[MEMORY] loaded {len(self.texts)} entries from disk")
        except Exception as e:
            _log(f"[MEMORY LOAD ERROR] {e}")


MEMORY = VectorMemory()

# ============================================================
# ACTIVITY CLASSIFIER
# Interprets raw sensor readings into human-readable context.
# This is what Echo actually receives — not raw numbers.
# ============================================================

def classify_activity(motion_data: dict, location_data: dict) -> str:
    """Return a plain-English activity label from sensor readings."""
    mag = safe_float(motion_data.get("magnitude", 0))

    # Check GPS speed if available (m/s)
    speed = safe_float(location_data.get("speed", -1))

    if speed > 20:          # ~72 km/h — vehicle/train
        return "in_transit"
    if speed > 1.5:         # walking pace
        return "walking"
    if mag < 0.05:
        return "stationary"
    if mag < 0.25:
        return "walking"
    if mag > 0.8:
        return "high_motion"   # running, train, bumpy road
    return "moving"


def build_heartbeat_summary(activity: str, loc: dict) -> str:
    """Compose a meaningful heartbeat string for Echo's memory (only when notable)."""
    t = get_temporal()
    parts = [f"symbiote: {activity}"]
    if t.get("is_night"):
        parts.append("late night")
    elif t.get("is_morning"):
        parts.append("morning")
    if activity == "in_transit":
        parts.append("user appears to be in a vehicle or on a train")
    if loc:
        acc = loc.get("accuracy", 0)
        if acc and acc < 30:
            parts.append(f"location accurate to {int(acc)}m")
    return ", ".join(parts)


# ============================================================
# STATE
# ============================================================

class SymbioteState:
    def __init__(self):
        self.lock            = threading.Lock()
        self.event_count     = 0
        self.context         = "unknown"
        self.patterns        = {}
        self.session_start   = time.time()
        self.total_uptime    = 0.0
        self.last_save       = time.time()
        self.entropy         = 0.5
        self.distance_m      = 0.0
        self._last_location  = None
        self._last_memory_location = None   # last location that triggered a FAISS memory
        self.activity        = "unknown"
        self.offline_since   = None         # timestamp when Mac became unreachable
        self.offline_events  = 0            # events buffered while offline

    def increment(self):
        with self.lock:
            self.event_count += 1
            return f"e{self.event_count}"

    def update_pattern(self, intent, score):
        with self.lock:
            if intent not in self.patterns:
                self.patterns[intent] = {"count": 0, "avg_score": 0.0}
            p = self.patterns[intent]
            p["count"] += 1
            p["avg_score"] = p["avg_score"] * 0.9 + score * 0.1

    def update_entropy(self, score):
        with self.lock:
            self.entropy = self.entropy * 0.95 + score * 0.05

    def update_location(self, lat, lon):
        """Update distance tracking. Returns metres moved since last memory event."""
        with self.lock:
            if self._last_location is not None:
                lat1, lon1 = self._last_location
                dlat = math.radians(lat - lat1)
                dlon = math.radians(lon - lon1)
                a = (math.sin(dlat / 2) ** 2 +
                     math.cos(math.radians(lat1)) *
                     math.cos(math.radians(lat)) *
                     math.sin(dlon / 2) ** 2)
                c = 2 * math.asin(math.sqrt(max(0.0, a)))
                self.distance_m += 6371000 * c
            self._last_location = (lat, lon)

            # Distance since last location memory event
            if self._last_memory_location is None:
                return LOCATION_MEMORY_THRESHOLD + 1  # trigger first time
            mlat, mlon = self._last_memory_location
            dlat = math.radians(lat - mlat)
            dlon = math.radians(lon - mlon)
            a = (math.sin(dlat / 2) ** 2 +
                 math.cos(math.radians(mlat)) *
                 math.cos(math.radians(lat)) *
                 math.sin(dlon / 2) ** 2)
            return 6371000 * 2 * math.asin(math.sqrt(max(0.0, a)))

    def mark_memory_location(self, lat, lon):
        with self.lock:
            self._last_memory_location = (lat, lon)

    def mark_offline(self):
        with self.lock:
            if self.offline_since is None:
                self.offline_since = time.time()
                self.offline_events = 0
            self.offline_events += 1

    def mark_online(self):
        """Returns (was_offline, duration_s, events_buffered) for summary event."""
        with self.lock:
            if self.offline_since is None:
                return False, 0, 0
            duration = time.time() - self.offline_since
            events   = self.offline_events
            self.offline_since  = None
            self.offline_events = 0
            return True, duration, events

    def save(self, force=False):
        with self.lock:
            if not force and (time.time() - self.last_save < SAVE_INTERVAL):
                return
            try:
                data = {
                    "event_count":  self.event_count,
                    "context":      self.context,
                    "patterns":     self.patterns,
                    "session_start": self.session_start,
                    "total_uptime": self.total_uptime + (time.time() - self.session_start),
                    "activity":     self.activity,
                }
                atomic_write(CONTEXT_FILE, json.dumps(data).encode())
                self.last_save = time.time()
            except Exception as e:
                _log(f"[STATE SAVE ERROR] {e}")

    def load(self):
        try:
            if os.path.exists(CONTEXT_FILE):
                with open(CONTEXT_FILE, "r") as f:
                    data = json.load(f)
                self.event_count  = data.get("event_count", 0)
                self.context      = data.get("context", "unknown")
                self.patterns     = data.get("patterns", {})
                self.total_uptime = data.get("total_uptime", 0.0)
                self.activity     = data.get("activity", "unknown")
                _log(f"[STATE] loaded: {self.event_count} events, "
                     f"{len(self.patterns)} patterns, "
                     f"{self.total_uptime/3600:.2f}h uptime")
        except Exception as e:
            _log(f"[STATE LOAD ERROR] {e}")


STATE = SymbioteState()

# ============================================================
# SENSORS
# ============================================================

def get_temporal():
    now      = datetime.now()
    hour     = now.hour
    minute   = now.minute
    weekday  = now.weekday()
    return {
        "hour":         hour,
        "minute":       minute,
        "weekday":      weekday,
        "is_weekend":   weekday >= 5,
        "is_night":     hour >= 22 or hour < 6,
        "is_morning":   6 <= hour < 12,
        "is_work_hours": weekday < 5 and 9 <= hour < 17,
        "day_progress": round((hour * 60 + minute) / 1440.0, 4),
    }

def get_location():
    if not HAS_LOCATION:
        return {}
    try:
        loc = location.get_location()
        if not loc:
            return {}
        def _loc_attr(obj, *names):
            for name in names:
                try:
                    v = getattr(obj, name, None)
                    if v is not None:
                        return safe_float(v)
                except Exception:
                    pass
            return 0.0
        lat = _loc_attr(loc, "latitude")
        lon = _loc_attr(loc, "longitude")
        alt = _loc_attr(loc, "altitude")
        acc = _loc_attr(loc, "horizontal_accuracy", "horizontalAccuracy")
        spd = _loc_attr(loc, "speed")
        return {
            "latitude":  lat,
            "longitude": lon,
            "lat":       lat,
            "lon":       lon,
            "altitude":  alt,
            "accuracy":  acc,
            "speed":     spd,
        }
    except Exception as e:
        _log(f"[LOCATION ERROR] {e}")
        return {}

def get_motion():
    if not HAS_MOTION:
        return {}
    try:
        def _m(name):
            try: return safe_float(getattr(motion, name, 0.0))
            except Exception: return 0.0
        ax = _m("user_acceleration_x")
        ay = _m("user_acceleration_y")
        az = _m("user_acceleration_z")
        if ax == 0.0 and ay == 0.0 and az == 0.0:
            ax = _m("acceleration_x") or _m("gravity_x")
            ay = _m("acceleration_y") or _m("gravity_y")
            az = _m("acceleration_z") or _m("gravity_z")
        mag = math.sqrt(ax**2 + ay**2 + az**2)
        return {
            "ax": round(ax, 4), "ay": round(ay, 4), "az": round(az, 4),
            "magnitude": round(mag, 4),
            "rx": round(_m("rotation_rate_x"), 4),
            "ry": round(_m("rotation_rate_y"), 4),
            "rz": round(_m("rotation_rate_z"), 4),
        }
    except Exception as e:
        _log(f"[MOTION ERROR] {e}")
        return {}

def get_sensors():
    return {
        "location": get_location(),
        "motion":   get_motion(),
        "device":   {},
        "temporal": get_temporal(),
    }

# ============================================================
# SCORING
# ============================================================

def score_text(text):
    words    = text.lower().split()
    word_set = set(words)
    positive = {"great", "good", "love", "happy", "yes", "done", "success", "perfect", "nice"}
    negative = {"error", "fail", "broken", "bad", "no", "crash", "wrong", "issue", "problem"}
    pos  = len(word_set & positive)
    neg  = len(word_set & negative)
    score = 0.3 + (pos * 0.1) - (neg * 0.05)
    return round(max(0.0, min(1.0, score)), 4)

def extract_intent(text):
    t = text.lower()
    if any(w in t for w in ["?", "what", "when", "where", "who", "why", "how"]):
        return "query"
    if any(w in t for w in ["todo", "task", "remind", "schedule", "deadline"]):
        return "task"
    if any(w in t for w in ["buy", "sell", "pay", "cost", "price", "money"]):
        return "finance"
    if any(w in t for w in ["run", "start", "stop", "set", "create", "build"]):
        return "command"
    return "general"

def extract_entities(text):
    entities = {}
    url   = re.findall(r"https?://[^\s]+", text)
    if url:   entities["url"]   = url
    email = re.findall(r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b", text, re.I)
    if email: entities["email"] = email
    times = re.findall(r"\b\d{1,2}:\d{2}\b", text)
    if times: entities["time"]  = times
    return entities

# ============================================================
# MAC REACHABILITY
# ============================================================

def mac_reachable() -> bool:
    """Quick TCP check — doesn't send any data."""
    if not HAS_REQUESTS:
        return False
    try:
        import socket
        s = socket.create_connection((MACBOOK_IP, MACBOOK_PORT), timeout=2)
        s.close()
        return True
    except Exception:
        return False

# ============================================================
# BUNDLE FLUSH
# ============================================================

def flush_bundle() -> int:
    """Send queued events to Echo. Returns number of events flushed."""
    if not HAS_REQUESTS:
        return 0
    if not os.path.exists(BUNDLE_FILE):
        return 0
    try:
        with open(BUNDLE_FILE, "r") as f:
            lines = [l.strip() for l in f if l.strip()]
        if not lines:
            return 0
        events = []
        for line in lines:
            try: events.append(json.loads(line))
            except Exception: pass
        if not events:
            return 0
        r = requests.post(
            f"http://{MACBOOK_IP}:{MACBOOK_PORT}/learning_batch",
            json={"events": events, "secret": THUNDERHEAD_SECRET},
            timeout=5,
        )
        if r.ok:
            os.remove(BUNDLE_FILE)
            _log(f"[BUNDLE] flushed {len(events)} queued events")
            return len(events)
    except Exception as e:
        _log(f"[BUNDLE FLUSH ERROR] {e}")
    return 0

# ============================================================
# EVENT DISPATCH
# Only call this for genuinely meaningful events (clipboard,
# commands, activity changes, session summaries).
# Heartbeats and raw sensor updates go to send_status() instead.
# ============================================================

def send_event(source, text, meta=None) -> bool:
    try:
        text   = text[:MAX_TEXT]
        vec    = embed(text)

        if MEMORY.is_duplicate(vec):
            return False

        score    = score_text(text)
        intent   = extract_intent(text)
        entities = extract_entities(text)
        event_id = STATE.increment()

        STATE.update_pattern(intent, score)
        STATE.update_entropy(score)
        MEMORY.add(text, vec, {"source": source, "intent": intent})

        payload = {
            "source":   source,
            "text":     text,
            "meta":     meta or {},
            "ts":       time.time(),
            "event_id": event_id,
            "score":    score,
            "intent":   intent,
            "entities": entities,
            "context":  STATE.context,
            "activity": STATE.activity,
            "entropy":  round(STATE.entropy, 4),
            "secret":   THUNDERHEAD_SECRET,
        }

        if HAS_REQUESTS:
            try:
                r = requests.post(
                    f"http://{MACBOOK_IP}:{MACBOOK_PORT}/learning_event",
                    json=payload,
                    timeout=3,
                )
                if r.ok:
                    was_offline, duration, buffered = STATE.mark_online()
                    if was_offline and duration > 60:
                        _send_reconnect_summary(duration, buffered)
                    return True
            except Exception:
                STATE.mark_offline()

        # Offline — bundle locally
        try:
            with open(BUNDLE_FILE, "a") as f:
                f.write(json.dumps(safe_json(payload)) + "\n")
        except Exception as e:
            _log(f"[BUNDLE WRITE ERROR] {e}")

        try:
            with open(EVENT_LOG, "a") as f:
                f.write(json.dumps(safe_json(payload)) + "\n")
        except Exception as e:
            _log(f"[LOG ERROR] {e}")

        return True

    except Exception as e:
        _log(f"[SEND ERROR] {e}")
        return False


def send_status(activity: str, location: dict, motion: dict) -> bool:
    """
    Post a heartbeat/status update to /symbiote_status.
    This does NOT touch Echo's FAISS index — it's pure telemetry.
    """
    if not HAS_REQUESTS:
        return False
    try:
        payload = {
            "activity":  activity,
            "context":   STATE.context,
            "entropy":   round(STATE.entropy, 4),
            "vectors":   len(MEMORY.vectors),
            "events":    STATE.event_count,
            "distance_m": round(STATE.distance_m, 1),
            "uptime_min": round((time.time() - STATE.session_start) / 60.0, 1),
            "location":  safe_json(location),
            "motion":    safe_json(motion),
            "temporal":  safe_json(get_temporal()),
            "ts":        time.time(),
        }
        r = requests.post(
            f"http://{MACBOOK_IP}:{MACBOOK_PORT}/symbiote_status",
            json=payload,
            timeout=3,
        )
        return r.ok
    except Exception:
        return False


def _send_reconnect_summary(duration_s: float, buffered_events: int) -> None:
    """Send a single synthesized memory event when coming back online after a gap."""
    mins = int(duration_s / 60)
    dist = round(STATE.distance_m, 0)
    summary = (
        f"symbiote reconnected after {mins}min offline — "
        f"traveled ~{int(dist)}m, {buffered_events} events buffered, "
        f"activity at reconnect: {STATE.activity}"
    )
    _log(f"[RECONNECT] {summary}")
    send_event("symbiote_reconnect", summary, {"type": "session_summary",
                                                "offline_min": mins,
                                                "distance_m": dist,
                                                "buffered": buffered_events})


def mirror_echo(msg) -> "str | None":
    """Send a message to Echo and return her reply."""
    if not HAS_REQUESTS:
        return None
    try:
        r = requests.post(
            f"http://{MACBOOK_IP}:{MACBOOK_PORT}/mirror_echo",
            json={
                "from":     "iphone_symbiote",
                "message":  msg,
                "time":     datetime.now().strftime("%H:%M:%S"),
                "context":  STATE.context,
                "activity": STATE.activity,
                "secret":   THUNDERHEAD_SECRET,
            },
            timeout=8,
        )
        if r.ok:
            return r.json().get("echo_reply")
    except Exception as e:
        _log(f"[MIRROR ERROR] {e}")
    return None

# ============================================================
# STATUS FILE  (local, always written)
# ============================================================

def write_status(activity: str = ""):
    try:
        sensors_active = {
            "location":  HAS_LOCATION,
            "motion":    HAS_MOTION,
            "clipboard": HAS_CLIP,
            "device":    HAS_DEVICE,
            "network":   HAS_REQUESTS,
        }
        status = {
            "ts":             datetime.now().isoformat(),
            "event_count":    STATE.event_count,
            "context":        STATE.context,
            "activity":       activity or STATE.activity,
            "entropy":        round(STATE.entropy, 4),
            "patterns":       {k: {"count": v["count"],
                                   "avg_score": round(v["avg_score"], 4)}
                               for k, v in STATE.patterns.items()},
            "vectors":        len(MEMORY.vectors),
            "uptime_min":     round((time.time() - STATE.session_start) / 60.0, 1),
            "total_uptime_h": round((STATE.total_uptime + (time.time() - STATE.session_start)) / 3600.0, 2),
            "sensors":        sensors_active,
            "distance_m":     round(STATE.distance_m, 1),
        }
        atomic_write(STATUS_FILE, json.dumps(status, indent=2).encode())
    except Exception as e:
        _log(f"[STATUS ERROR] {e}")

# ============================================================
# BACKGROUND THREADS
# ============================================================

_stop = threading.Event()

# ---- Heartbeat ----
# Posts to /symbiote_status (pure telemetry, no FAISS).
# Only sends a real memory event when activity changes.
_last_reported_activity = "unknown"

def heartbeat_loop():
    global _last_reported_activity
    while not _stop.is_set():
        _stop.wait(HEARTBEAT_BASE)
        if _stop.is_set():
            break
        try:
            loc    = get_location()
            mot    = get_motion()
            activity = classify_activity(mot, loc)
            STATE.activity = activity

            # Update location tracking
            lat = loc.get("latitude") or loc.get("lat")
            lon = loc.get("longitude") or loc.get("lon")
            if lat and lon:
                STATE.update_location(lat, lon)

            # Post lightweight status to Mac (no FAISS)
            sent = send_status(activity, loc, mot)

            # Only send a FAISS memory when activity changes meaningfully
            if activity != _last_reported_activity:
                summary = build_heartbeat_summary(activity, loc)
                send_event("symbiote_activity", summary, {
                    "type":     "activity_change",
                    "from":     _last_reported_activity,
                    "to":       activity,
                })
                _last_reported_activity = activity
                _log(f"[ACTIVITY] {_last_reported_activity} → {activity}")

            write_status(activity)
            STATE.save()
            _log(f"[HEARTBEAT] activity={activity} mac_reachable={sent}")

        except Exception as e:
            _log(f"[HEARTBEAT ERROR] {e}")

# ---- Clipboard ----
# Unchanged — clipboard content is genuine signal for Echo.
def clipboard_loop():
    if not HAS_CLIP:
        return
    last = ""
    while not _stop.is_set():
        _stop.wait(CLIPBOARD_POLL)
        if _stop.is_set():
            break
        try:
            cur = clipboard.get()
            if cur and cur.strip() and cur.strip() != last and len(cur.strip()) > 15:
                last = cur.strip()
                send_event("clipboard", last, {"via": "clipboard"})
                _log(f"[CLIP] {len(last)} chars")
        except Exception as e:
            _log(f"[CLIP ERROR] {e}")

# ---- Sensor loop ----
# Only logs a memory event when user has moved significantly.
# Routine location updates go through heartbeat → send_status().
def sensor_loop():
    while not _stop.is_set():
        _stop.wait(SENSOR_POLL)
        if _stop.is_set():
            break
        try:
            loc = get_location()
            lat = loc.get("latitude") or loc.get("lat")
            lon = loc.get("longitude") or loc.get("lon")
            if lat and lon:
                moved = STATE.update_location(lat, lon)
                if moved and moved > LOCATION_MEMORY_THRESHOLD:
                    mot      = get_motion()
                    activity = classify_activity(mot, loc)
                    summary  = build_heartbeat_summary(activity, loc)
                    send_event("sensor_location", summary, {
                        "type":     "significant_movement",
                        "distance": round(moved, 0),
                        "activity": activity,
                        "location": safe_json(loc),
                    })
                    STATE.mark_memory_location(lat, lon)
                    _log(f"[SENSOR] moved {int(moved)}m — logged to Echo")
        except Exception as e:
            _log(f"[SENSOR ERROR] {e}")

# ---- CMD loop ----
def cmd_loop():
    while not _stop.is_set():
        _stop.wait(CMD_POLL)
        if _stop.is_set():
            break
        try:
            if os.path.exists(CMD_FILE):
                with open(CMD_FILE, "r") as f:
                    cmd = f.read().strip()
                os.remove(CMD_FILE)
                if cmd:
                    _log(f"[CMD] {cmd}")
                    if cmd == "status":
                        write_status()
                    elif cmd.startswith("context:"):
                        STATE.context = cmd.split(":", 1)[1].strip()
                        _log(f"[CMD] context set to {STATE.context}")
                    elif cmd.startswith("mirror:"):
                        msg   = cmd.split(":", 1)[1].strip()
                        reply = mirror_echo(msg)
                        _log(f"[MIRROR REPLY] {reply}")
                        # Readable confirmation file — open in Files app instead
                        # of hunting for this line in scrolling console output.
                        try:
                            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            atomic_write(
                                REPLY_FILE,
                                f"[{ts}]\nsent:  {msg}\nreply: {reply}\n".encode(),
                            )
                        except Exception as e:
                            _log(f"[REPLY WRITE ERROR] {e}")
                    else:
                        send_event("command", cmd, {"type": "command"})
        except Exception as e:
            _log(f"[CMD ERROR] {e}")

# ---- Save loop ----
def save_loop():
    while not _stop.is_set():
        _stop.wait(SAVE_INTERVAL)
        if _stop.is_set():
            break
        try:
            STATE.save(force=True)
            MEMORY.save()
            write_status()
        except Exception as e:
            _log(f"[SAVE ERROR] {e}")

# ---- Bundle loop ----
# Checks for Mac reachability and flushes queued events quickly.
def bundle_loop():
    while not _stop.is_set():
        _stop.wait(BUNDLE_INTERVAL)
        if _stop.is_set():
            break
        try:
            if os.path.exists(BUNDLE_FILE):
                flushed = flush_bundle()
                if flushed:
                    was_offline, duration, buffered = STATE.mark_online()
                    if was_offline and duration > 60:
                        _send_reconnect_summary(duration, buffered)
        except Exception as e:
            _log(f"[BUNDLE LOOP ERROR] {e}")

# ---- Watchdog ----
_threads: list = []

def watchdog_loop():
    """Restart any thread that has died unexpectedly."""
    _thread_targets = {
        "heartbeat": heartbeat_loop,
        "clipboard": clipboard_loop,
        "sensor":    sensor_loop,
        "cmd":       cmd_loop,
        "saver":     save_loop,
        "bundle":    bundle_loop,
    }
    while not _stop.is_set():
        _stop.wait(60)
        if _stop.is_set():
            break
        for t in list(_threads):
            if not t.is_alive():
                name   = t.name
                target = _thread_targets.get(name)
                if target:
                    _log(f"[WATCHDOG] restarting dead thread: {name}")
                    nt = threading.Thread(target=target, daemon=True, name=name)
                    nt.start()
                    _threads.remove(t)
                    _threads.append(nt)

# ============================================================
# MAIN
# ============================================================

def main():
    _log("[SYMBIOTE] v2 starting up")
    STATE.load()
    MEMORY.load()

    thread_defs = [
        ("heartbeat", heartbeat_loop),
        ("clipboard", clipboard_loop),
        ("sensor",    sensor_loop),
        ("cmd",       cmd_loop),
        ("saver",     save_loop),
        ("bundle",    bundle_loop),
    ]

    for name, target in thread_defs:
        t = threading.Thread(target=target, daemon=True, name=name)
        t.start()
        _threads.append(t)
        _log(f"[SYMBIOTE] started {name}")

    # Watchdog runs separately (not in _threads — it monitors the others)
    wd = threading.Thread(target=watchdog_loop, daemon=True, name="watchdog")
    wd.start()

    # Flush any events queued from last session
    flush_bundle()

    send_event("symbiote_start", "symbiote v2 online", {"type": "startup"})
    write_status()

    _log("[SYMBIOTE] running — press Ctrl+C to stop")

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        _log("[SYMBIOTE] shutting down")
        _stop.set()
        STATE.save(force=True)
        MEMORY.save()
        write_status()
        _log("[SYMBIOTE] goodbye")

if __name__ == "__main__":
    main()
