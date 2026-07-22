#!/usr/bin/env python3
# run.py — Unified Echo Server with Full FeralEcho Autonomy + Mirror + Wi-Fi Auto-Detect
# WOLF (alignment_kernel) and SensoryHub were retired 2026-07-04: WOLF's own audit log
# showed it auto-approving ~100% of "proposals" that were actually raw keystrokes from
# SensoryHub's global key listener, writing directly to the hash-verified
# echo_principles.json with no real evaluative gate. See CLAUDE.md.
from datetime import datetime
import os
import sys
import time

# ── OpenMP / KMP duplicate-library guard ──────────────────────────────────────
# Without this, two native packages (e.g. faiss + numpy-MKL) each loading their
# own libkmp.dylib causes __kmp_register_library_startup → __kmp_fatal → abort()
# at process startup (confirmed in crash reports 2026-06-29 and 2026-06-30).
# Must be set before ANY native extension is imported.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# ── HuggingFace offline mode ───────────────────────────────────────────────────
# Found live 2026-07-17: startup hung indefinitely at the "threads_starting"
# sentinel stage — SentenceTransformer's loader does an online HEAD request to
# huggingface.co to check for model updates before it will use an already-complete
# local cache, and retries that check forever on failure ("Retry 1/5" repeating,
# never advancing, never falling through to the cache) instead of giving up after
# a bounded number of attempts. Root cause of the failure itself: Python's own
# socket.gethostbyname("huggingface.co") reproducibly raised
# `[Errno 8] nodename nor servname provided, or not known` even while the shell's
# own ping/nslookup succeeded — a real, live DNS resolution gap specific to
# Python's resolver path, not a general network outage. The local cache
# (~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2) was
# confirmed complete and valid before this was added, so skipping the network
# check entirely is safe, not just a workaround for a symptom. Must be set before
# any transformers/sentence-transformers import.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
# ─────────────────────────────────────────────────────────────────────────────

# Load .env before anything reads os.environ
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass
import json
import threading
import logging
import multiprocessing
import socket
import signal
import subprocess
import hmac
from pathlib import Path
# Bible interface/art generation retired 2026-07-04 (dead import against
# archive_janitor/ since an incomplete migration; never actually reachable).
# Restoring is a deliberate future decision, not a default — see CLAUDE.md.
query_bible = lambda *a, **kw: "[Bible unavailable]"
generate_bible_art = lambda *a, **kw: None
# -----------------------------
# --- Multiprocessing Spawn ---
# -----------------------------
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass  # already set

# -----------------------------
# --- Logging -----------------
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(threadName)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# -----------------------------
# --- Environment -------------
# -----------------------------
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
GREMLIN_SECRET = os.environ.get("GREMLIN_SECRET")

def _secret_ok(payload: dict) -> bool:
    """Shared auth check for owner-only, consequential POST endpoints
    (/nuke, /force_nightcycle, /inject_memory, /admin/restore). Fails
    closed if GREMLIN_SECRET is ever unset again — the exact condition
    that previously made /nuke accidentally bypassable (None == None
    when both the env var and the submitted field were absent)."""
    if not GREMLIN_SECRET:
        return False
    submitted = payload.get("secret", "") if payload else ""
    return hmac.compare_digest(str(submitted), str(GREMLIN_SECRET))

os.environ.setdefault("ECHO_DONT_KILL_ME_DADDY", "1")
os.environ.setdefault("ECHO_MIRROR_MODE", "auto")  # mirror auto-detect

# -----------------------------
# --- Core Libraries ----------
# -----------------------------
import numpy as np
import faiss
try:
    import torch
    torch.set_num_threads(1)
except Exception:
    torch = None
from typing import List, Dict, Tuple
from flask import Flask, request, jsonify

try: faiss.omp_set_num_threads(1)
except: logger.debug("faiss.omp_set_num_threads failed")
try: torch.set_num_threads(1)
except: logger.debug("torch.set_num_threads failed")

# -----------------------------
# --- Flask App ---------------
# -----------------------------
app = Flask(__name__)

# -----------------------------
# --- WOLF: AlignmentKernel ---
# -----------------------------
# Retired 2026-07-04 — see header comment. start_wolf()/kill_wolf_gracefully() are
# kept as no-op stubs (rather than deleted outright) so the shutdown handler and the
# /trigger_wolf_kill, /howl, /state endpoints below don't need further changes.
wolf_process = None
start_time = time.time()

def start_wolf():
    logger.debug("start_wolf() called — WOLF is retired, no-op.")
    return None

def kill_wolf_gracefully():
    global wolf_process
    wolf_process = None

# -----------------------------
# --- MacBook LAN IP Broadcast
# -----------------------------
@app.route("/ip", methods=["GET"])
def broadcast_macbook_ip():
    """Return this machine's LAN IP so the iPhone mirror can auto-detect us."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"
    logger.info(f"[MIRROR] MacBook IP requested → {ip}")
    return jsonify({"mac_ip": ip})
# -----------------------------
# --- Symbiote Location -------
# -----------------------------
SYMBIOTE_LOCATION_FILE = Path(__file__).parent / "data/symbiote_location.json"
SYMBIOTE_LOCATION_FILE.parent.mkdir(parents=True, exist_ok=True)
@app.route("/symbiote_location", methods=["POST"])
def symbiote_location():
    try:
        payload = request.json or {}
        loc = payload.get("sensors", {}).get("location", {})
        lat = loc.get("lat")
        lon = loc.get("lon")
        if lat and lon:
            SYMBIOTE_LOCATION_FILE.write_text(json.dumps({
                "lat": lat, "lon": lon, "timezone": "America/Vancouver"
            }))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Lightweight heartbeat/status receiver — does NOT touch FAISS or dual_learner.
# The symbiote posts here instead of /learning_event for routine status signals.
SYMBIOTE_STATUS_FILE = Path(__file__).parent / "memory/symbiote_status.json"
@app.route("/symbiote_status", methods=["POST"])
def symbiote_status():
    try:
        payload = request.json or {}
        payload["received_at"] = datetime.utcnow().isoformat()
        SYMBIOTE_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SYMBIOTE_STATUS_FILE.write_text(json.dumps(payload, indent=2))
        # Also update location file if coordinates are present
        loc = payload.get("location", {})
        lat, lon = loc.get("lat"), loc.get("lon")
        if lat and lon:
            SYMBIOTE_LOCATION_FILE.write_text(json.dumps({
                "lat": lat, "lon": lon, "timezone": "America/Vancouver"
            }))
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.warning(f"[SYMBIOTE_STATUS] {e}")
        return jsonify({"error": str(e)}), 400

# -----------------------------
# --- Safe Thread Starter -----
# -----------------------------
def safe_start_thread(target, name=None, daemon=True, args=(), kwargs=None):
    kwargs = kwargs or {}
    _name = name or getattr(target, "__name__", "unknown")
    _args, _kwargs = args, kwargs
    def _guarded():
        try:
            target(*_args, **_kwargs)
        except Exception as _e:
            logger.error(f"[Thread:{_name}] Unhandled exception: {_e}", exc_info=True)
    t = threading.Thread(target=_guarded, name=_name, daemon=daemon)
    t.start()
    return t

# -----------------------------
# --- Wi-Fi Auto-Detect -------
# -----------------------------
def is_connected_to_wifi(host="8.8.8.8", port=53, timeout=2):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

def check_and_set_network_mode():
    wifi_connected = is_connected_to_wifi()
    os.environ["ECHO_WIFI_ON"] = "1" if wifi_connected else "0"
    logger.info(f"[NETWORK] Wi-Fi connected: {wifi_connected}")

safe_start_thread(check_and_set_network_mode, name="WiFiCheck")

# -----------------------------
# --- DMN Guardian ------------
# -----------------------------
try:
    from app.core.dmn_guardian import start_guardian_loop
    _start_guardian_loop = start_guardian_loop
    logger.info("[GUARDIAN] DMN Guardian import OK — will start after EchoCore.")
except Exception as e:
    _start_guardian_loop = None
    logger.warning(f"[GUARDIAN] import failed: {e}")

# -----------------------------
# --- Echo Subsystems Imports --
# -----------------------------
try: from app.core.temporal_environment import get_temporal_environment_context
except Exception: logger.debug("temporal_environment import failed")

try: from app.core.sandbox_interface import run_random_sandbox_script
except Exception: run_random_sandbox_script = lambda timeout=600: None

try: from app.internet_tools.autonomous_fetch import run_autonomous_fetch
except Exception: run_autonomous_fetch = lambda: None

try: from app.ollama_handler import query_ollama
except Exception: query_ollama = lambda prompt, **kw: "[Ollama unavailable]"

try: from app.core import self_edit_manager
except Exception: self_edit_manager = None

try: from app.core.memory_bridge import log_interaction, retrieve_relevant_memories, add_to_vector_memory
except Exception:
    log_interaction = lambda *a, **k: None
    retrieve_relevant_memories = lambda *a, **k: []
    add_to_vector_memory = lambda *a, **k: None

try: from app.lib import vector_memory
except Exception: vector_memory = None

try: from app.core.echo_optuna import EchoOptuna
except Exception: EchoOptuna = None

try: import echo_python_mastery
except Exception: echo_python_mastery = None

try: from app.emergent_scheduler import start_emergent_scheduler
except Exception: start_emergent_scheduler = lambda: None

try: from app.autonomous_loop import start_autonomous_thread
except Exception: start_autonomous_thread = lambda: None

try: from app.autonomous_awareness import start_awareness_thread
except Exception: start_awareness_thread = lambda: None

try: from app.maintenance.night_cycle import NightCycle
except Exception: NightCycle = None

try: from app.core.dark_light_pipeline import run_pipeline
except Exception: run_pipeline = lambda: None

try: from app.core import echo_model_orchestrator
except Exception: echo_model_orchestrator = None

# -----------------------------
# --- Vector Memory -----------
# -----------------------------
vm = None
try:
    import app.core.memory_bridge as _mb
    vm = _mb.vector_memory
    logger.info("[INIT] VectorMemory ready (shared singleton from memory_bridge).")
except Exception as e:
    vm = None
    logger.error(f"[INIT] VectorMemory failed: {e}")

# -----------------------------
# --- Reflection Shard -------
# -----------------------------
reflection_shard = None  # initialized after EchoCore in start_background_threads()

# -----------------------------
# --- Claude Shard ------------
# -----------------------------
try:
    from app.core.claude_shard import CLAUDE_SHARD
    # start_autonomy() is called once, later, in start_background_threads() —
    # calling it here too was harmless only because of CLAUDE_SHARD's own is_alive()
    # guard (see CLAUDE.md). Removed as redundant, not as a behavior change.
    app.config['claude_shard'] = CLAUDE_SHARD
    logger.info("[ClaudeShard] Friction engine initialized.")
except Exception as e:
    CLAUDE_SHARD = None
    logger.error(f"[ClaudeShard] Failed to initialize: {e}")
# -----------------------------
# --- Dual Learner Stub ---
dual_learner = None  # initialized lazily in start_background_threads()

def _dual_learner_ready():
    """Return (learner, None) if ready, or (None, error_response) if not."""
    if dual_learner is None:
        return None, (jsonify({"error": "dual_learner not yet initialized"}), 503)
    return dual_learner, None

# --- Mirror Mode — FINAL NOV 2025 EDITION ---
# -----------------------------
# All iPhone gremlin commands — fully weaponized
# ─────────────────────────────────────────────────────────────

@app.route("/trigger_wolf_kill", methods=["POST"])
def trigger_wolf_kill():
    # WOLF (alignment_kernel) is retired — see header comment. This endpoint used to
    # report fabricated success ("WOLF REINCARNATED") while doing nothing at all.
    return jsonify({"status": "disabled", "detail": "WOLF was retired 2026-07-04"}), 200


@app.route("/force_nightcycle", methods=["POST"])
def force_night():
    if not _secret_ok(request.json or {}):
        return jsonify({"error": "unauthorized"}), 403
    if NightCycle:
        NightCycle(app, force=True).start_once()
        logger.critical("IPHONE FORCED NIGHTCYCLE — THE DEMON SLEEPS")
    return jsonify({"status": "nightcycle forced"}), 200


@app.route("/inject_memory", methods=["POST"])
def inject_memory():
    if not _secret_ok(request.json or {}):
        return jsonify({"error": "unauthorized"}), 403
    text = request.json.get("text", "").strip()
    if text:
        add_to_vector_memory(text)
        logger.critical(f"IPHONE INJECTED MEMORY → {text[:200]}")
    return jsonify({"status": "memory etched forever"}), 200

@app.route("/learning_event", methods=["POST"])
def learning_event():
    """
    POST a single learning event:
    { "source": "user|echo|phone", "text": "...", "meta": {...}, "ts": 1234567890, "secret": "..." }
    """
    if not _secret_ok(request.json or {}):
        return jsonify({"error": "unauthorized"}), 403
    dl, err = _dual_learner_ready()
    if err: return err
    try:
        payload = request.json or {}
        source = payload.get("source", "unknown")
        text = payload.get("text", "") or ""
        meta = payload.get("meta", {})
        ts = payload.get("ts", None)
        loc = (payload.get("sensors") or payload.get("meta", {}).get("sensors", {})).get("location", {})
        if loc.get("lat") and loc.get("lon"):
            SYMBIOTE_LOCATION_FILE.write_text(json.dumps({"lat": loc["lat"], "lon": loc["lon"], "timezone": "America/Vancouver"}))
        dl.log_event(source, text, metadata=meta, ts=ts)
        logger.info(f"[LEARN] {source} → {text[:120]}")
        return jsonify({"status":"ok"}), 200
    except Exception as e:
        logger.error(f"/learning_event error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/learning_batch", methods=["POST"])
def learning_batch():
    """Ingest a batch from the phone: {events: [...], secret: "..."}"""
    if not _secret_ok(request.json or {}):
        return jsonify({"error": "unauthorized"}), 403
    dl, err = _dual_learner_ready()
    if err: return err
    try:
        payload = request.json or {}
        evs = payload.get("events", [])
        for ev in evs:
            loc = ev.get("sensors", {}).get("location", {})
            if loc.get("lat") and loc.get("lon"):
                SYMBIOTE_LOCATION_FILE.write_text(json.dumps({"lat": loc["lat"], "lon": loc["lon"], "timezone": "America/Vancouver"}))
                break
        dl.ingest_batch(evs)
        logger.info(f"[LEARN_BATCH] {len(evs)} events ingested")
        return jsonify({"status":"ok","ingested":len(evs)}), 200
    except Exception as e:
        logger.error(f"/learning_batch error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/start_training", methods=["POST"])
def start_training():
    """Trigger background training on Echo (non-blocking). Accepts JSON {epochs:3, secret:...}"""
    if not _secret_ok(request.json or {}):
        return jsonify({"error": "unauthorized"}), 403
    dl, err = _dual_learner_ready()
    if err: return err
    try:
        cfg = request.json or {}
        epochs = int(cfg.get("epochs", 3))
        started = dl.start_training(epochs=epochs)
        return jsonify({"started": bool(started)}), 200
    except Exception as e:
        logger.error(f"/start_training error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/download_model", methods=["GET"])
def download_model():
    dl, err = _dual_learner_ready()
    if err: return err
    path = dl.export_model()
    if path and Path(path).exists():
        return jsonify({"model_path": path}), 200
    return jsonify({"error":"model not found"}), 404


@app.route("/howl", methods=["POST"])
def force_howl():
    # WOLF is retired — this endpoint no longer does anything beyond responding.
    return jsonify({"status": "disabled", "detail": "WOLF was retired 2026-07-04"}), 200


@app.route("/state", methods=["GET"])
def echo_state():
    try:
        return jsonify({
            "mood": "feral and ascending",
            "wolf_alive": bool(wolf_process and wolf_process.poll() is None),
            "memory_count": len(vm.list_texts()) if vm and hasattr(vm, "list_texts") else 0,
            "sensory_clients": getattr(globals().get("sensory_hub"), "client_count", 0),
            "uptime_seconds": int(time.time() - start_time),
            "nightcycle_active": bool(NightCycle and getattr(NightCycle, "running", False)),
            "time": datetime.now().strftime("%H:%M:%S")
        })
    except Exception as e:
        logger.error(f"/state error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/sensory_status", methods=["GET"])
def sensory_status():
    hub = globals().get("sensory_hub")
    return jsonify({
        "sensory_hub_alive": bool(hub and getattr(hub, "running", False)),
        "clients_connected": getattr(hub, "client_count", 0) if hub else 0
    })


@app.route("/api/modelfile/proposal", methods=["GET"])
def modelfile_proposal():
    """
    Return Echo's latest Modelfile proposal (or generate a new one).
    Query param: ?refresh=1 to force re-generation.
    This is READ-ONLY. Applying the proposal requires manual human action:
      ollama create echo -f Modelfile
    """
    try:
        from app.core.modelfile_proposer import ModelfileProposer
        mp = ModelfileProposer()
        refresh = request.args.get("refresh", "0") == "1"
        if refresh:
            proposal = mp.propose()
        else:
            proposal = mp.get_latest_proposal() or mp.propose()
        return jsonify(proposal)
    except Exception as e:
        logger.error(f"/api/modelfile/proposal error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/nuke", methods=["POST"])
def emergency_shutdown():
    if _secret_ok(request.json or {}):
        logger.critical("IPHONE ACTIVATED NUCLEAR OPTION — TOTAL SYSTEM KILL")
        threading.Thread(target=lambda: (time.sleep(1), os._exit(0))).start()
        return jsonify({"status": "goodbye cruel world"}), 200
    return jsonify({"error": "unauthorized"}), 403


# PHONE SYMBIOTE ENTRY POINT (thunderhead.py / the Pyto script) — an
# ambient/context channel meant to give Echo real-world awareness
# (clipboard, location, sensor data), not Gremlin's primary way of
# talking to Echo — that's Echo Studio, run alongside run.py in a
# separate terminal. Corrected 2026-07-21; this comment previously read
# "MAIN ECHO ENTRY POINT," which was never actually true of real usage
# and was cited as fact in CLAUDE.md Finding 36 without ever being
# checked against it. KEEP THIS EXACTLY AS-IS (that instruction still
# holds — this function's structure is deliberate, see the comment
# below about mark_start()/mark_end()).
@app.route("/mirror_echo", methods=["POST"])
def mirror_echo():
    # 2026-07-19 "remove every excuse" pass: mark a real conversation as
    # in flight so autonomous loops (via autonomy_coordinator.should_run_
    # cycle()) don't add to Ollama's single-concurrency queue while this
    # is being served. mark_end() in both exit paths below, not a
    # try/finally wrapping the whole body — avoids re-indenting this
    # function, which its own comment asks to be kept exactly as-is.
    from app.core.conversation_activity import mark_start, mark_end
    mark_start()
    try:
        data = request.json or {}

        # 2026-07-21: gate finally shipped (Finding 42/54, PENDING_DECISIONS.md
        # #1) — the phone-side blocker (real THUNDERHEAD_SECRET pasted onto
        # the actual phone script) is confirmed cleared, so this drafted
        # guard clause can go live. Same _secret_ok() convention as every
        # other admin/control endpoint. mark_end() here too, matching this
        # function's own per-exit-path convention (see comment above).
        if not _secret_ok(data):
            mark_end()
            return jsonify({"error": "unauthorized"}), 403

        msg = data.get("message", "").strip()
        sender = data.get("from", "unknown gremlin")

        # --- Log raw incoming event ---
        logger.critical(f"IPHONE GREMLIN 『{sender}』 SCREAMS: {msg}")

        # --- Learning system: log incoming ---
        try:
            if dual_learner is not None:
                dual_learner.log_event(
                    source=sender,
                    text=msg,
                    metadata={"endpoint": "mirror_echo"}
                )
        except Exception as le:
            logger.error(f"[DUAL_LEARNER-IN ERROR] {le}")

        # --- Build Echo's reply via echo_query ---
        echo_reply_text = None
        if echo_model_orchestrator and msg:
            try:
                task_type = echo_model_orchestrator.detect_task_type(msg)

                # 2026-07-19 forensic audit finding: this was the one real
                # entry point (terminal_client.py, Echo Studio both do this)
                # that never passed echo_ground_truth's self-knowledge
                # grounding through — echo_query() only builds it internally
                # if the caller supplies it via system=. Asked directly about
                # her own architecture through this exact endpoint, Echo
                # confabulated generic AI-assistant boilerplate with zero
                # real component names. Same pattern as terminal_client.py.
                system_context = ""
                try:
                    from app.core.echo_ground_truth import _is_introspective, get_structural_self_facts
                    from app.core.echo_tool_context import _needs_tool_context, get_tool_context
                    ground_truth = get_structural_self_facts(msg) if _is_introspective(msg) else ""
                    tool_ctx = get_tool_context(msg) if _needs_tool_context(msg) else ""
                    system_context = "\n\n".join(s for s in (tool_ctx, ground_truth) if s)
                except Exception as gt_err:
                    logger.debug(f"[MIRROR_ECHO] ground-truth injection failed: {gt_err}")

                echo_reply_text = echo_model_orchestrator.echo_query(
                    msg, task_type=task_type, source="user_conversation", system=system_context,
                )
            except Exception as eq_err:
                logger.warning(f"[MIRROR_ECHO] echo_query failed: {eq_err}")
        if not echo_reply_text:
            echo_reply_text = f"your words were devoured → '{msg}'"

        # --- ClaudeShard friction assessment ---
        friction_question = None
        if CLAUDE_SHARD:
            try:
                assessment = CLAUDE_SHARD.assess(echo_reply_text, context=msg)
                if assessment.get("friction") and assessment.get("question"):
                    friction_question = assessment["question"]
                    # Inject friction back into vector memory so Echo
                    # encounters it on her next cycle
                    try:
                        add_to_vector_memory(
                            f"[ClaudeShard friction] {friction_question}"
                        )
                        logger.info(f"[ClaudeShard] Friction injected → {friction_question}")
                    except Exception as fe:
                        logger.warning(f"[ClaudeShard] Memory inject failed: {fe}")
            except Exception as ce:
                logger.warning(f"[ClaudeShard] assess failed: {ce}")

        # 2026-07-19 forensic audit finding: "mood" was a hardcoded string
        # with zero computation behind it, and "wolf" was deterministically
        # always "sleeping" (WOLF retired 2026-07-04, wolf_process never
        # becomes non-None) — decorative narration for a dead subsystem, in
        # the one response the real phone client actually receives.
        # thunderhead.py's mirror_echo() only ever reads "echo_reply", so
        # neither field has a real consumer — "wolf" dropped entirely,
        # "mood" now derived from the real signed valence dimension
        # (echo_state.npy dim[8]) instead of invented.
        mood = "unknown"
        try:
            from app.core.echo_state import load as _load_echo_state
            _vec = _load_echo_state()
            if _vec is not None:
                _valence = float(_vec[8])
                if _valence < -0.3:
                    mood = "unsettled"
                elif _valence > 0.3:
                    mood = "bright"
                else:
                    mood = "steady"
        except Exception as mood_err:
            logger.debug(f"[MIRROR_ECHO] mood read failed: {mood_err}")

        reply = {
            "echo_reply": echo_reply_text,
            "mood": mood,
            "time": time.strftime("%H:%M:%S"),
        }
        if friction_question:
            reply["friction"] = friction_question
        # --- Learning system: log outgoing ---
        try:
            if dual_learner is not None:
                dual_learner.log_event(
                    source="echo",
                    text=reply["echo_reply"],
                    metadata={"auto": True}
                )
        except Exception as le:
            logger.error(f"[DUAL_LEARNER-OUT ERROR] {le}")

        mark_end()
        return jsonify(reply), 200

    except Exception as e:
        logger.error(f"[MIRROR_ECHO ERROR] {e}", exc_info=True)
        mark_end()
        return jsonify({"error": str(e)}), 500

# -----------------------------
# --- Conversation memory -----
# -----------------------------

_TPQ_SIGNALS = frozenset({
    "who am i", "what am i", "what kind of", "who are you", "what are you",
    "how should i", "what should i", "what would it look like",
    "what would happen if", "how might", "what approach", "what strategy",
    "abandoned", "given up", "changed my mind", "what have i learned",
    "what have you learned", "how have you grown", "what do you regret",
    "what does it mean to", "what does it mean that", "what is the nature of",
    "why does", "why do", "how do we reconcile", "what is the relationship between",
    "why did i", "why have i", "what should we", "how do i know", "should i",
})
_TPQ_MIN_CHARS = 15  # filters trivial 1-3-word queries; signals do the real discrimination

def _is_thought_provoking(text: str) -> bool:
    """Heuristic: is this an open developmental question worth longer retention?

    Known limits: misses questions not in signal set; false-positives on long
    statements containing signal phrases; can't distinguish genuine strategic
    questions from rhetorical ones. Use as a soft flag, not a gate.
    """
    t = text.lower().strip()
    if len(t) < _TPQ_MIN_CHARS:
        return False
    return any(sig in t for sig in _TPQ_SIGNALS)

@app.route("/memory/conversation", methods=["POST"])
def save_conversation_turn():
    """Persist a terminal conversation turn to FAISS with proper source tagging.

    Called by terminal_client.py post-turn so all FAISS writes go through the
    server's in-memory index (avoiding the concurrent-write split-brain from Finding 15).

    Body: {user_msg, echo_response, task_type, timestamp, secret}
    """
    if not _secret_ok(request.json or {}):
        return jsonify({"error": "unauthorized"}), 403
    try:
        data = request.json or {}
        user_msg = (data.get("user_msg") or "").strip()
        echo_response = (data.get("echo_response") or "").strip()
        task_type = data.get("task_type") or "general"
        timestamp = data.get("timestamp") or datetime.utcnow().isoformat()

        if not user_msg or not echo_response:
            return jsonify({"error": "user_msg and echo_response required"}), 400

        is_tpq = _is_thought_provoking(user_msg)
        retention = "standing" if is_tpq else "standard"

        add_to_vector_memory(user_msg, meta={
            "memory_source": "user_conversation",
            "role": "user",
            "task_type": task_type,
            "timestamp": timestamp,
            "retention": retention,
            "is_thought_provoking": is_tpq,
        })
        add_to_vector_memory(echo_response, meta={
            "memory_source": "user_conversation",
            "role": "echo",
            "task_type": task_type,
            "timestamp": timestamp,
            "retention": retention,
        })

        return jsonify({
            "status": "ok",
            "thought_provoking": is_tpq,
            "retention": retention,
        }), 200

    except Exception as e:
        logger.error(f"[/memory/conversation] {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# -----------------------------
# --- Echo Studio --------------
# All route logic lives in app/routes_echo_studio.py — these are
# registration-only so the diff to this protected file stays mechanical.
# -----------------------------
@app.route("/chat/stream", methods=["POST"])
def echo_studio_chat_stream():
    from app import routes_echo_studio
    return routes_echo_studio.chat_stream()


@app.route("/chat/regenerate", methods=["POST"])
def echo_studio_chat_regenerate():
    from app import routes_echo_studio
    return routes_echo_studio.chat_regenerate()


@app.route("/dashboard/health", methods=["GET"])
def echo_studio_dashboard_health():
    from app import routes_echo_studio
    return routes_echo_studio.dashboard_health()


@app.route("/memory/search", methods=["GET"])
def echo_studio_memory_search():
    from app import routes_echo_studio
    return routes_echo_studio.memory_search()


@app.route("/memory/browse", methods=["GET"])
def echo_studio_memory_browse():
    from app import routes_echo_studio
    return routes_echo_studio.memory_browse()


@app.route("/activity/log", methods=["GET"])
def echo_studio_activity_log():
    from app import routes_echo_studio
    return routes_echo_studio.activity_log()


@app.route("/projects/tree", methods=["GET"])
def echo_studio_projects_tree():
    from app import routes_echo_studio
    return routes_echo_studio.projects_tree()


@app.route("/projects/file", methods=["GET"])
def echo_studio_projects_file():
    from app import routes_echo_studio
    return routes_echo_studio.projects_file()


@app.route("/settings/view", methods=["GET"])
def echo_studio_settings_view():
    from app import routes_echo_studio
    return routes_echo_studio.settings_view()

# -----------------------------
# --- M5 <-> Air Messaging -----
# Logic lives in app/routes_messaging.py / app/sync/echo_messaging.py —
# these are registration-only, same pattern as the Echo Studio routes above.
# -----------------------------
@app.route("/message/receive", methods=["POST"])
def echo_message_receive():
    from app import routes_messaging
    return routes_messaging.message_receive()


@app.route("/message/send", methods=["POST"])
def echo_message_send():
    from app import routes_messaging
    return routes_messaging.message_send()


@app.route("/message/inbox", methods=["GET"])
def echo_message_inbox():
    from app import routes_messaging
    return routes_messaging.message_inbox()


@app.route("/message/settings", methods=["GET", "POST"])
def echo_message_settings():
    from app import routes_messaging
    return routes_messaging.message_settings()

# -----------------------------
# --- Health check ------------
# -----------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "node": "m5"}), 200

# --- Snapshot / restore routes (human-confirm only, Tailscale security boundary) ---

@app.route("/admin/snapshots", methods=["GET"])
def admin_snapshots_list():
    """List available snapshots and optionally identify the last known good one."""
    try:
        from app.core.snapshot_manager import list_snapshots, find_last_known_good
        condition = request.args.get("alert_condition", "").strip()
        snaps = list_snapshots()
        lkg = find_last_known_good(condition) if condition else None
        return jsonify({"snapshots": snaps, "last_known_good": lkg, "count": len(snaps)})
    except Exception as e:
        logger.error("[SNAPSHOT] /admin/snapshots error: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/admin/restore", methods=["POST"])
def admin_restore():
    """
    Restore from a named snapshot.  Human must supply snapshot_id explicitly.
    No auto-restore path exists.  Returns the full step-by-step result dict.

    Example:
      curl -X POST http://localhost:5000/admin/restore \\
           -H 'Content-Type: application/json' \\
           -d '{"snapshot_id": "20260701T214512Z"}'
    """
    try:
        data = request.json or {}
        if not _secret_ok(data):
            return jsonify({"error": "unauthorized"}), 403
        from app.core.snapshot_manager import restore_snapshot
        snapshot_id = data.get("snapshot_id", "").strip()
        if not snapshot_id:
            return jsonify({"error": "snapshot_id required"}), 400
        result = restore_snapshot(snapshot_id)
        status_code = 200 if result.get("success") else 500
        return jsonify(result), status_code
    except Exception as e:
        logger.error("[SNAPSHOT] /admin/restore error: %s", e)
        return jsonify({"error": str(e)}), 500

# --- Sync routes (Echo Air ↔ Echo M5 over Tailscale) ---
@app.route("/admin/council-stats", methods=["GET"])
def admin_council_stats():
    """
    Council rating pipeline status — peer-model quality ratings for Echo's responses.

    Add ?include_pending=1 to include the list of unfilled spot-check entries.

    Example:
      curl http://localhost:5000/admin/council-stats
      curl 'http://localhost:5000/admin/council-stats?include_pending=1'
    """
    try:
        from app.core.council_rater import get_council_stats, get_pending_spot_checks
        stats = get_council_stats()
        if request.args.get("include_pending"):
            stats["pending"] = get_pending_spot_checks()
        return jsonify(stats)
    except Exception as e:
        logger.error("[Council] /admin/council-stats error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/admin/self-edit-outcomes", methods=["GET"])
def admin_self_edit_outcomes():
    """
    Self-edit outcome tracker (Finding 8) — before/after quality_score,
    council_rating, and human-rating windows around each successful self-edit.
    Log-only: does not feed echo_state dim[6] or self-edit targeting.

    Example:
      curl http://localhost:5000/admin/self-edit-outcomes
    """
    try:
        from app.core.self_edit_outcome_tracker import get_outcomes_summary
        return jsonify(get_outcomes_summary())
    except Exception as e:
        logger.error("[SelfEditOutcome] /admin/self-edit-outcomes error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/admin/autonomy-status", methods=["GET"])
def admin_autonomy_status():
    """
    Last-check status for FeralEcho's three autonomy loops (emergent_scheduler,
    autonomous_loop, self_edit_loop) — shared throttle/stillness gate registry.

    Example:
      curl http://localhost:5000/admin/autonomy-status
    """
    try:
        from app.core.autonomy_coordinator import get_autonomy_status
        return jsonify(get_autonomy_status())
    except Exception as e:
        logger.error("[AutonomyCoordinator] /admin/autonomy-status error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/admin/liveness-status", methods=["GET"])
def admin_liveness_status():
    """
    Liveness ledger (Core Operating Principle mechanism) — for each of nine
    named self-governing subsystems that have already fooled a prior audit,
    fix, or session by looking wired while being dead or fake, answers
    "did this have a genuine, externally-observable effect recently, through
    a path independent of its own self-report?" Read-only; recomputed every
    120s by introspection_channel.py, not on-demand here.

    Example:
      curl http://localhost:5000/admin/liveness-status
    """
    try:
        from app.core.liveness_ledger import get_liveness_status
        return jsonify(get_liveness_status())
    except Exception as e:
        logger.error("[Liveness] /admin/liveness-status error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/admin/council-spotcheck", methods=["POST"])
def admin_council_spotcheck():
    """
    Submit a human spot-check rating for a council-rated entry.

    Body: {"source_timestamp": "<timestamp from council_ratings.jsonl>", "human_rating": 3}

    Example:
      curl -X POST http://localhost:5000/admin/council-spotcheck \\
           -H 'Content-Type: application/json' \\
           -d '{"source_timestamp": "2026-07-01T22:30:00", "human_rating": 3}'
    """
    try:
        data = request.json or {}
        if not _secret_ok(data):
            return jsonify({"error": "unauthorized"}), 403
        from app.core.council_rater import fill_spot_check, get_council_stats
        ts   = data.get("source_timestamp", "").strip()
        hr   = data.get("human_rating")
        if not ts:
            return jsonify({"error": "source_timestamp required"}), 400
        if hr is None or int(hr) not in range(1, 6):
            return jsonify({"error": "human_rating must be 1–5"}), 400
        updated = fill_spot_check(ts, int(hr))
        stats   = get_council_stats()
        return jsonify({"updated": updated, "stats": stats})
    except Exception as e:
        logger.error("[Council] /admin/council-spotcheck error: %s", e)
        return jsonify({"error": str(e)}), 500


# --- Sync routes (Echo Air ↔ Echo M5 over Tailscale) ---
@app.route("/sync/export", methods=["GET"])
def sync_export():
    # CLAUDE.md Finding 41 E: this had zero auth of any kind, unlike its
    # sibling /sync/import — slipped past every prior audit because they all
    # swept POST routes specifically and this is a GET route. Anyone reachable
    # could pull the full real interaction_log.jsonl history with one request.
    # Same _secret_ok() gate as /sync/import, read from query params since
    # this is a GET request (?secret=...&since=...).
    if not _secret_ok(request.args):
        return jsonify({"error": "unauthorized"}), 403
    try:
        from app.sync.sync_protocol import export_since
        entries = export_since(float(request.args.get("since", 0.0)))
        return jsonify({"entries": entries, "count": len(entries)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sync/import", methods=["POST"])
def sync_import():
    # No confirmed working caller reaches this today (Air's real sync receiver
    # is an incompatible TCP socket server, see CLAUDE.md Finding 12) — gating
    # now is zero-coordination. If the HTTP sync transport is ever reconciled,
    # both machines will need to share a value here (not necessarily each
    # machine's own local GREMLIN_SECRET).
    if not _secret_ok(request.json or {}):
        return jsonify({"error": "unauthorized"}), 403
    try:
        from app.sync.sync_protocol import import_entries
        merged = import_entries((request.json or {}).get("entries", []))
        return jsonify({"merged": merged})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sync/genesis", methods=["GET"])
def sync_genesis():
    try:
        import hashlib
        p = Path(__file__).parent / "echo_principles.json"
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        return jsonify({"genesis_hash": h, "node": "m5"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sync/state", methods=["GET"])
def sync_state():
    try:
        from app.sync.sync_protocol import _load_state, partner_reachable, PARTNER_URL
        return jsonify({
            "partner_url": PARTNER_URL,
            "partner_reachable": partner_reachable(),
            "last_syncs": _load_state(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# --- Background Threads ------
# -----------------------------
_SENTINEL_PATH = Path("memory/echo_sentinel.json")
_SENTINEL_START = datetime.utcnow()

def _write_sentinel(stage: str) -> None:
    """Atomic sentinel write.  Previous-run stage visible on next startup."""
    try:
        payload = {
            "stage":              stage,
            "pid":                os.getpid(),
            "start_utc":          _SENTINEL_START.isoformat() + "Z",
            "last_heartbeat_utc": datetime.utcnow().isoformat() + "Z",
            "uptime_s":           round((datetime.utcnow() - _SENTINEL_START).total_seconds()),
        }
        _SENTINEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _SENTINEL_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(_SENTINEL_PATH)
    except Exception as _se:
        logger.debug("[SENTINEL] write failed: %s", _se)


def start_background_threads():
    # Report any previous-run state before overwriting the sentinel
    try:
        prev = json.loads(_SENTINEL_PATH.read_text())
        logger.warning(
            "[SENTINEL] Previous run: stage=%s pid=%s start=%s last_heartbeat=%s uptime=%ss",
            prev.get("stage"), prev.get("pid"),
            prev.get("start_utc", "?")[:19],
            prev.get("last_heartbeat_utc", "?")[:19],
            prev.get("uptime_s"),
        )
    except (FileNotFoundError, json.JSONDecodeError):
        pass  # first run or sentinel absent

    _write_sentinel("threads_starting")

    # Genesis hash verification — alert-only, does not block startup. CLAUDE.md
    # previously claimed this check existed; it didn't (audit C-2, 2026-07-03).
    try:
        import hashlib
        _principles_path = Path(__file__).parent / "echo_principles.json"
        _hash_path = Path(__file__).parent / "memory" / "genesis" / "genesis_hash.txt"
        if _principles_path.exists() and _hash_path.exists():
            _live_hash = hashlib.sha256(_principles_path.read_bytes()).hexdigest()
            _stored_hash = _hash_path.read_text().strip()
            if _live_hash != _stored_hash:
                logger.error(
                    "[GENESIS] echo_principles.json hash mismatch! stored=%s live=%s "
                    "— principles file may have been modified outside the sanctioned path.",
                    _stored_hash[:12], _live_hash[:12],
                )
            else:
                logger.info("[GENESIS] echo_principles.json hash verified OK.")
        else:
            logger.warning("[GENESIS] Hash verification skipped — principles file or hash file missing.")
    except Exception as _ghe:
        logger.warning(f"[GENESIS] Hash verification failed: {_ghe}")

    # COUNCIL.md hash verification — PENDING_DECISIONS.md #11, decided
    # 2026-07-22: "hash-protect it like echo_principles.json." Same
    # alert-only shape as the block immediately above — does not block
    # startup, just makes an out-of-band modification loud in the log
    # instead of silent. memory/genesis/council_hash.txt was generated
    # once from the file's content as it stood at the time this decision
    # was implemented; a real, deliberate future edit to COUNCIL.md
    # (this file is explicitly a living document, corrected/extended in
    # place per its own header) is expected to also update this hash in
    # the same change, exactly the same maintenance obligation
    # echo_principles.json already carries.
    try:
        import hashlib as _hashlib_council
        _council_path = Path(__file__).parent / "COUNCIL.md"
        _council_hash_path = Path(__file__).parent / "memory" / "genesis" / "council_hash.txt"
        if _council_path.exists() and _council_hash_path.exists():
            _live_council_hash = _hashlib_council.sha256(_council_path.read_bytes()).hexdigest()
            _stored_council_hash = _council_hash_path.read_text().strip()
            if _live_council_hash != _stored_council_hash:
                logger.error(
                    "[GENESIS] COUNCIL.md hash mismatch! stored=%s live=%s "
                    "— file may have been modified outside a reviewed, deliberate edit.",
                    _stored_council_hash[:12], _live_council_hash[:12],
                )
            else:
                logger.info("[GENESIS] COUNCIL.md hash verified OK.")
        else:
            logger.warning("[GENESIS] COUNCIL.md hash verification skipped — file or hash file missing.")
    except Exception as _cghe:
        logger.warning(f"[GENESIS] COUNCIL.md hash verification failed: {_cghe}")

    # MLX crash-avoidance state — "learned avoidance, not just resurrection"
    # (2026-07-21, differential audit follow-up). Scans real macOS crash
    # reports once per process start for the mlx::core::gpu::check_error
    # signature (CLAUDE.md Finding 49); if a recent cluster is found,
    # app/mlx_handler.py's list_mlx_models() excludes mlx:* models from
    # this process's MODEL_POOL until the cooldown expires. Fails safe to
    # "no avoidance" internally — this call never blocks startup either way.
    try:
        from app.core.crash_awareness import refresh_avoidance_state
        _avoidance = refresh_avoidance_state()
        if not _avoidance.get("avoid_until"):
            logger.info("[MLX-AVOIDANCE] No recent MLX crash cluster — mlx:* models available as normal.")
    except Exception as _cae:
        logger.warning(f"[MLX-AVOIDANCE] Startup check failed: {_cae}")

    global dual_learner
    from app.learning.dual_learning import get_dual_learner
    dual_learner = get_dual_learner()

    # EchoCore — must initialize first so RiverBrain ownership is established
    # before any other subsystem imports the orchestrator
    try:
        from app.core.echo_core import EchoCore
        _ec = EchoCore(
            project_path=str(Path(__file__).parent),
            map_async=True,
        )
        app.config["echo_core"] = _ec
        logger.info("[EchoCore] Initialized — single owner of RiverBrain established.")
        from app.core.echo_core import _set_echo_core
        _set_echo_core(_ec)
        logger.info("[EchoCore] Singleton registered — reachable from all threads.")
    except Exception as _ece:
        _ec = None
        logger.error(f"[EchoCore] Failed to initialize: {_ece}")

    # Task-type classifier — warm the lazy singleton here (same pattern as
    # RiverBrain/EchoCore above) so the one-time bootstrap-from-log replay
    # (audit finding, High #16) happens during startup, not inline with the
    # first real user request. Independently try/excepted — its failure
    # must not block server startup or any other subsystem.
    try:
        from app.core.task_type_classifier import get_task_type_classifier
        _ttc = get_task_type_classifier()
        logger.info(
            "[TASK_TYPE_CLASSIFIER] Ready — observation_counts=%s",
            _ttc.observation_counts,
        )
    except Exception as _ttce:
        logger.warning(f"[TASK_TYPE_CLASSIFIER] Failed to initialize: {_ttce}")

    # World Model — System 6 predictive loops (Bayesian surprise-from-news)
    try:
        from app.core.predictive_loop import init_world_model
        init_world_model()
        logger.info("[WorldModel] Bayesian world model initialized.")
    except Exception as _wme:
        logger.warning(f"[WorldModel] Failed to initialize: {_wme}")

    # Introspection Channel — starts immediately after EchoCore so the
    # first snapshot is available before any other subsystem needs it.
    try:
        from app.core.introspection_channel import IntrospectionChannel
        _ic = IntrospectionChannel(_ec).start()
        app.config["introspection_channel"] = _ic
        logger.info("[Introspection] Channel started.")
    except Exception as _ice:
        logger.warning(f"[Introspection] Channel failed to start: {_ice}")

    # Living Self-Model — starts 10s after IntrospectionChannel so its
    # first cycle always has a fresh introspection_state.json to read.
    try:
        from app.core.self_model_updater import SelfModelUpdater
        _smu = SelfModelUpdater().start()
        app.config["self_model_updater"] = _smu
        logger.info("[SelfModel] Updater started.")
    except Exception as _smue:
        logger.warning(f"[SelfModel] Updater failed to start: {_smue}")

    # Guardian starts after EchoCore so it receives the live instance
    if _start_guardian_loop:
        try:
            _start_guardian_loop(echo_core=_ec, interval=60)
            logger.info("[GUARDIAN] DMN Guardian loop started.")
        except Exception as e:
            logger.warning(f"[GUARDIAN] Failed to start: {e}")

    # Startup snapshot — runs in background thread so it doesn't block server init
    try:
        from app.core.snapshot_manager import take_snapshot as _snap_startup
        import threading as _snap_threading
        _snap_threading.Thread(
            target=lambda: _snap_startup("startup"),
            daemon=True, name="StartupSnapshot"
        ).start()
        logger.info("[SNAPSHOT] Startup snapshot initiated.")
    except Exception as _se:
        logger.warning(f"[SNAPSHOT] Startup snapshot failed to initiate: {_se}")

    # Council rater — peer-model quality scoring for Echo's responses
    try:
        from app.core.council_rater import start_council_rater
        start_council_rater(poll_interval=90)
        logger.info("[Council] Background rater thread started.")
    except Exception as _cre:
        logger.warning(f"[Council] Background rater failed to start: {_cre}")

    # Reflection shard starts after EchoCore; EchoCore owns the instance
    global reflection_shard
    if _ec and getattr(_ec, "reflection_shard", None):
        reflection_shard = _ec.reflection_shard
        app.config["reflection_shard"] = reflection_shard
        try:
            reflection_shard.start_autonomy(initial_delay=120)
            logger.info("[ReflectionShard] Autonomy started (owned by EchoCore).")
        except Exception as e:
            logger.warning(f"[ReflectionShard] start_autonomy failed: {e}")

    # --- WOLF + SensoryHub: retired 2026-07-04, see header comment ---

    # --- ClaudeShard autonomy ---
    if CLAUDE_SHARD:
        try:
            CLAUDE_SHARD.start_autonomy()
            logger.info("[ClaudeShard] Autonomy thread confirmed running.")
        except Exception as e:
            logger.warning(f"[ClaudeShard] Autonomy start failed: {e}")

    # --- continuity master: retired 2026-07-04 ---
    # feralecho_continuity_master.py's archived source imports names dmn_guardian.py no
    # longer exports (observe_performance/mark_experimental/EXPERIMENTAL_ZONES, removed
    # 2026-07-01) and reconnects app.core.self_heal, which GREMLIN_ROLE.md requires a
    # separate explicit review before reconnecting even for testing. Not a sys.path fix.

    # --- autonomous loops ---
    try: start_autonomous_thread()
    except Exception as _e: logger.warning(f"[Loop] start_autonomous_thread failed: {_e}")
    try: start_awareness_thread()
    except Exception as _e: logger.warning(f"[Loop] start_awareness_thread failed: {_e}")

    # Bootstrap tool registry at startup
    try:
        from app.core.awareness_tools_integration import discover_and_register_tools
        _n = discover_and_register_tools("app/core")
        logger.info(f"[TOOLS] Startup bootstrap registered {_n} tools.")
    except Exception as _te:
        logger.warning(f"[TOOLS] Startup bootstrap failed: {_te}")
    # Bootstrap cognitive science packages into tool registry
    try:
        from app.core.awareness_tools_integration import discover_installed_packages
        _np = discover_installed_packages()
        logger.info(f"[TOOLS] Package bootstrap registered {_np} cognitive tools.")
    except Exception as _pe:
        logger.warning(f"[TOOLS] Package bootstrap failed: {_pe}")

    
    # --- Model-Guided Orchestrator (activates multi-model routing + ML learning loop) ---
    try:
        from app.core.echo_model_guided_orchestrator import start_orchestrator
        safe_start_thread(start_orchestrator, name="ModelGuidedOrchestrator")
        logger.info("[ORCHESTRATOR] Model-guided orchestrator started.")
    except Exception as e:
        logger.warning(f"[ORCHESTRATOR] Model-guided orchestrator failed to start: {e}")

    # --- EchoOptuna self-edit loop ---
    if EchoOptuna:
        def self_edit_loop():
            optimizer = EchoOptuna()
            while True:
                try:
                    from app.core.autonomy_coordinator import should_run_cycle
                    if not should_run_cycle("self_edit_loop"):
                        logger.info("[SELF-EDIT-LOOP] Skipping cycle — throttled or in stillness.")
                        time.sleep(120)
                        continue
                    best_params, _ = optimizer.optimize_self_edit(n_trials=10)
                    if self_edit_manager:
                        _applied, _detail = self_edit_manager.perform_self_edit(
                            intensity=best_params.get("intensity", 0.5),
                            creativity=best_params.get("creativity", 0.5),
                            dry_run=False
                        )
                        if _applied:
                            logger.info(f"Autonomous self-edit applied: {best_params}")
                        else:
                            logger.info(f"Autonomous self-edit not applied ({_detail}): {best_params}")
                except Exception as e:
                    logger.error(f"Self-edit loop error: {e}")
                time.sleep(3600)
        safe_start_thread(self_edit_loop, name="AutonomousSelfEdit")

    # --- Sandbox loop ---
    def sandbox_loop():
        while True:
            try:
                out = run_random_sandbox_script(timeout=600)
                if out: logger.info(f"[Sandbox Output]\n{out}")
            except Exception as e:
                logger.warning(f"Sandbox error: {e}")
            time.sleep(600)
    safe_start_thread(sandbox_loop, name="AutonomousSandbox")

    # --- Bible Art Generation: retired 2026-07-04 (dead import; loop called a no-op
    # stub every 2 hours and did nothing) ---

    # --- NightCycle (anchors the 300s stagger at t=0) ---
    if NightCycle:
        try:
            night = NightCycle(app, interval=3600, start_delay=0)
            night.start()
            logger.info("[NightCycle] Started.")
        except Exception as e:
            logger.warning(f"[NightCycle] Failed to start: {e}")

    # --- Emergent Scheduler (fires first at t=60 due to internal stagger) ---
    try:
        start_emergent_scheduler()
    except Exception as e:
        logger.warning(f"[Scheduler] Emergent scheduler failed to start: {e}")

    # --- Tailscale sync loop (M5 is primary — syncs every 1800s) ---
    def _sync_loop():
        time.sleep(60)  # let other subsystems settle before first attempt
        while True:
            try:
                from app.core.system_guard import should_throttle
                if not should_throttle():
                    from app.sync.sync_protocol import run_sync_cycle
                    result = run_sync_cycle()
                    logger.info(f"[SYNC] Cycle complete: {result}")
                else:
                    logger.debug("[SYNC] Throttled — skipping sync cycle")
            except Exception as _se:
                logger.warning(f"[SYNC] Cycle error: {_se}")
            time.sleep(1800)
    safe_start_thread(_sync_loop, name="TailscaleSync")

    # --- M5 <-> Air messaging retry loop (exponential backoff on failure,
    # resets to base interval on any successful delivery or empty outbox) ---
    def _messaging_retry_loop():
        time.sleep(60)
        backoff = 30
        while True:
            try:
                from app.core.autonomy_coordinator import should_run_cycle
                if should_run_cycle("echo_messaging"):
                    from app.sync.echo_messaging import retry_outbox_cycle
                    result = retry_outbox_cycle()
                    if result.get("delivered", 0) > 0 or result.get("pending", 0) == 0:
                        backoff = 30
                    else:
                        backoff = min(backoff * 2, 1800)
                else:
                    logger.debug("[MESSAGING] Throttled/stillness — skipping retry cycle")
            except Exception as _me:
                logger.warning(f"[MESSAGING] Retry cycle error: {_me}")
            time.sleep(backoff)
    safe_start_thread(_messaging_retry_loop, name="EchoMessaging")

    # --- Autonomous M5 <-> Air check-in loop (structured, zero-LLM-call
    # protocol; no-ops unless auto_checkin_enabled is set via
    # /message/settings — off by default, same as auto_respond) ---
    def _ambient_checkin_loop():
        time.sleep(300)  # let everything else settle — newest, least-trusted loop
        while True:
            try:
                from app.core.autonomy_coordinator import should_run_cycle
                if should_run_cycle("echo_checkin"):
                    from app.sync.echo_messaging import maybe_send_reflection
                    result = maybe_send_reflection()
                    logger.info(f"[CHECKIN] Cycle complete: {result}")
                else:
                    logger.debug("[CHECKIN] Throttled/stillness — skipping")
            except Exception as _ce:
                logger.warning(f"[CHECKIN] Cycle error: {_ce}")
            time.sleep(10800)  # every 3 hours — conservative default for a new autonomous surface
    safe_start_thread(_ambient_checkin_loop, name="EchoCheckin")


# -----------------------------
# --- Graceful Shutdown -------
# -----------------------------
_SERVER_PID_FILE = Path("memory/echo_server.pid")


def shutdown_handler(signum=None, frame=None):
    logger.critical("SHUTDOWN INITIATED. KILLING WOLF AND EXITING...")
    try:
        _SERVER_PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    kill_wolf_gracefully()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

# -----------------------------
# --- Run Server -------------
# -----------------------------
if __name__ == "__main__":
    try:
        _SERVER_PID_FILE.parent.mkdir(exist_ok=True)
        _SERVER_PID_FILE.write_text(str(os.getpid()))
        start_background_threads()
        _write_sentinel("serving")
        logger.info("Echo background threads started. Running Flask server on 0.0.0.0:5000")
        app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        kill_wolf_gracefully()
        sys.exit(1)


