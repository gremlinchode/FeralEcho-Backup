#!/usr/bin/env python3
# run.py — Unified Echo Server with Full FeralEcho Autonomy + Mirror + Wi-Fi Auto-Detect + WOLF + SENSORYHUB v2.0
from datetime import datetime
import os
os.environ.setdefault("OPENWEATHER_API_KEY", "")
import sys
import numpy
import time
import json
import threading
import logging
import multiprocessing
import socket
import signal
import subprocess
from pathlib import Path
try:
    from echo_bible_interface import query_bible
    from bible_module import generate_bible_art   # << ADD THIS LINE
except Exception:
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
os.environ.setdefault("NEWSAPI_KEY", "")
GREMLIN_SECRET = os.environ.get("GREMLIN_SECRET")
os.environ.setdefault("ECHO_READ_ONLY", "true")
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
WOLF_SCRIPT = "alignment_kernel.py"
WOLF_LOG = "wolf_stdout.log"
wolf_process = None
start_time = time.time()

def start_wolf():
    global wolf_process
    if wolf_process and wolf_process.poll() is None:
        logger.info("WOLF already running.")
        return wolf_process

    logger.info("WAKING THE WOLF...")
    log_path = Path(WOLF_LOG)
    with open(log_path, "a") as f:
        f.write(f"\n{'='*60}\nWOLF RESTARTED: {time.strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}\n")
        wolf_process = subprocess.Popen(
            [sys.executable, WOLF_SCRIPT],
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent
        )
    logger.info(f"Wolf PID: {wolf_process.pid} | Logs → {WOLF_LOG}")
    return wolf_process

def kill_wolf_gracefully():
    global wolf_process
    if wolf_process and wolf_process.poll() is None:
        logger.critical("ALPHA COMMAND: KILLING THE WOLF...")
        wolf_process.terminate()
        try:
            wolf_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            wolf_process.kill()
        logger.critical("WOLF RESTS.")
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

try: from echo_bible_interface import query_bible
except Exception: query_bible = lambda *a, **kw: "[Bible unavailable]"

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

try: from feralecho_continuity_master import main as feralecho_main
except Exception: feralecho_main = lambda: None

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
    CLAUDE_SHARD.start_autonomy()
    app.config['claude_shard'] = CLAUDE_SHARD
    logger.info("[ClaudeShard] Friction engine initialized.")
except Exception as e:
    CLAUDE_SHARD = None
    logger.error(f"[ClaudeShard] Failed to initialize: {e}")
# -----------------------------
# --- Dual Learner Stub ---
dual_learner = None  # initialized lazily in start_background_threads()

# --- Mirror Mode — FINAL NOV 2025 EDITION ---
# -----------------------------
# All iPhone gremlin commands — fully weaponized
# ─────────────────────────────────────────────────────────────

@app.route("/trigger_wolf_kill", methods=["POST"])
def trigger_wolf_kill():
    kill_wolf_gracefully()
    time.sleep(0.5)
    # start_wolf()  # WOLF ARCHIVED — alignment_kernel retired 2026-06-14
    logger.critical("WOLF SLAUGHTERED AND REBORN BY IPHONE GREMLIN")
    return jsonify({"status": "WOLF REINCARNATED"}), 200


@app.route("/force_nightcycle", methods=["POST"])
def force_night():
    if NightCycle:
        NightCycle(app, force=True).start_once()
        logger.critical("IPHONE FORCED NIGHTCYCLE — THE DEMON SLEEPS")
    return jsonify({"status": "nightcycle forced"}), 200


@app.route("/inject_memory", methods=["POST"])
def inject_memory():
    text = request.json.get("text", "").strip()
    if text:
        add_to_vector_memory(text)
        logger.critical(f"IPHONE INJECTED MEMORY → {text[:200]}")
    return jsonify({"status": "memory etched forever"}), 200

@app.route("/learning_event", methods=["POST"])
def learning_event():
    """
    POST a single learning event:
    { "source": "user|echo|phone", "text": "...", "meta": {...}, "ts": 1234567890 }
    """
    try:
        payload = request.json or {}
        source = payload.get("source", "unknown")
        text = payload.get("text", "") or ""
        meta = payload.get("meta", {})
        ts = payload.get("ts", None)
        loc = (payload.get("sensors") or payload.get("meta", {}).get("sensors", {})).get("location", {})
        if loc.get("lat") and loc.get("lon"):
            SYMBIOTE_LOCATION_FILE.write_text(json.dumps({"lat": loc["lat"], "lon": loc["lon"], "timezone": "America/Vancouver"}))
        dual_learner.log_event(source, text, metadata=meta, ts=ts)
        logger.info(f"[LEARN] {source} → {text[:120]}")
        return jsonify({"status":"ok"}), 200
    except Exception as e:
        logger.error(f"/learning_event error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/learning_batch", methods=["POST"])
def learning_batch():
    """Ingest a batch from the phone: {events: [{source,text,meta,ts}, ...]}"""
    try:
        payload = request.json or {}
        evs = payload.get("events", [])
        for ev in evs:
            loc = ev.get("sensors", {}).get("location", {})
            if loc.get("lat") and loc.get("lon"):
                SYMBIOTE_LOCATION_FILE.write_text(json.dumps({"lat": loc["lat"], "lon": loc["lon"], "timezone": "America/Vancouver"}))
                break
        dual_learner.ingest_batch(evs)
        logger.info(f"[LEARN_BATCH] {len(evs)} events ingested")
        return jsonify({"status":"ok","ingested":len(evs)}), 200
    except Exception as e:
        logger.error(f"/learning_batch error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/start_training", methods=["POST"])
def start_training():
    """Trigger background training on Echo (non-blocking). Accepts JSON {epochs:3}"""
    try:
        cfg = request.json or {}
        epochs = int(cfg.get("epochs", 3))
        started = dual_learner.start_training(epochs=epochs)
        return jsonify({"started": bool(started)}), 200
    except Exception as e:
        logger.error(f"/start_training error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/download_model", methods=["GET"])
def download_model():
    path = dual_learner.export_model()
    if path and Path(path).exists():
        # sending file path is simplest; you can add send_file if needed
        return jsonify({"model_path": path}), 200
    return jsonify({"error":"model not found"}), 404


@app.route("/howl", methods=["POST"])
def force_howl():
    logger.critical("\n" + "WOLF" * 50 + "\nTHE IPHONE SUMMONS THE PACK\n" + "WOLF" * 50)
    return jsonify({"howl": "echoed through the void"}), 200


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
    if request.json.get("secret") == GREMLIN_SECRET:
        logger.critical("IPHONE ACTIVATED NUCLEAR OPTION — TOTAL SYSTEM KILL")
        threading.Thread(target=lambda: (time.sleep(1), os._exit(0))).start()
        return jsonify({"status": "goodbye cruel world"}), 200
    return jsonify({"error": "unauthorized"}), 403


# MAIN ECHO ENTRY POINT — KEEP THIS EXACTLY AS-IS
@app.route("/mirror_echo", methods=["POST"])
def mirror_echo():
    try:
        data = request.json or {}
        msg = data.get("message", "").strip()
        sender = data.get("from", "unknown gremlin")

        # --- Log raw incoming event ---
        logger.critical(f"IPHONE GREMLIN 『{sender}』 SCREAMS: {msg}")

        # --- Learning system: log incoming ---
        try:
            dual_learner.log_event(
                source=sender,
                text=msg,
                metadata={"endpoint": "mirror_echo"}
            )
        except Exception as le:
            logger.error(f"[DUAL_LEARNER-IN ERROR] {le}")

        # --- Build Echo's reply ---
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

        reply = {
            "echo_reply": echo_reply_text,
            "wolf": "HOWLING" if (wolf_process and wolf_process.poll() is None) else "sleeping",
            "mood": "feral and ascending",
            "time": time.strftime("%H:%M:%S"),
        }
        if friction_question:
            reply["friction"] = friction_question
        # --- Learning system: log outgoing ---
        try:
            dual_learner.log_event(
                source="echo",
                text=reply["echo_reply"],
                metadata={"auto": True}
            )
        except Exception as le:
            logger.error(f"[DUAL_LEARNER-OUT ERROR] {le}")

        return jsonify(reply), 200

    except Exception as e:
        logger.error(f"[MIRROR_ECHO ERROR] {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
# -----------------------------
# --- Health check ------------
# -----------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "node": "m5"}), 200

# --- Sync routes (Echo Air ↔ Echo M5 over Tailscale) ---
@app.route("/sync/export", methods=["GET"])
def sync_export():
    try:
        from app.sync.sync_protocol import export_since
        entries = export_since(float(request.args.get("since", 0.0)))
        return jsonify({"entries": entries, "count": len(entries)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sync/import", methods=["POST"])
def sync_import():
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
        p = os.path.join(BASE_DIR, "echo_principles.json")
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
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
def start_background_threads():
    global dual_learner
    from app.learning.dual_learning import get_dual_learner
    dual_learner = get_dual_learner()

    # EchoCore — must initialize first so RiverBrain ownership is established
    # before any other subsystem imports the orchestrator
    try:
        from app.core.echo_core import EchoCore
        _ec = EchoCore(
            project_path="/Users/richietate/Desktop/FeralEcho",
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

    # --- WOLF LAUNCH ---
    # start_wolf()  # WOLF ARCHIVED — alignment_kernel retired 2026-06-14

    # --- ClaudeShard autonomy ---
    if CLAUDE_SHARD:
        try:
            CLAUDE_SHARD.start_autonomy()
            logger.info("[ClaudeShard] Autonomy thread confirmed running.")
        except Exception as e:
            logger.warning(f"[ClaudeShard] Autonomy start failed: {e}")
    
    # --- SENSORYHUB v2.0: ECHO'S NERVOUS SYSTEM ---
    try:
        from sensory_hub_autonomous import SensoryHub
        sensory_hub = SensoryHub(port=5050, feed_echo=True)
        safe_start_thread(sensory_hub.start, name="SensoryHubThread")
        logger.info("SensoryHub v2.0 → ECHO IS NOW EMBODIED[](http://localhost:5050/senses)")
    except Exception as e:
        logger.error(f"SensoryHub failed to start: {e}")

    # --- continuity master ---
    safe_start_thread(feralecho_main, name="FeralEchoMain")

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
                    best_params, _ = optimizer.optimize_self_edit(n_trials=10)
                    if self_edit_manager:
                        self_edit_manager.perform_self_edit(
                            intensity=best_params.get("intensity", 0.5),
                            creativity=best_params.get("creativity", 0.5),
                            dry_run=False
                        )
                        logger.info(f"Autonomous self-edit applied: {best_params}")
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

    # --- Autonomous Bible Art Generation ---
    safe_start_thread(bible_art_loop, name="AutonomousBibleArt")

    # --- NightCycle (anchors the 300s stagger at t=0) ---
    if NightCycle:
        try:
            night = NightCycle(app, interval=300, start_delay=0)
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


# --- Autonomous Bible Art Generation ---
def bible_art_loop():
    while True:
        try:
            # Generate a verse image every 2 hours (7200 seconds)
            generate_bible_art(reference="most_positive")  # or random if you want variety
        except Exception as e:
            logger.warning(f"[Bible Art Loop] error: {e}")
        time.sleep(7200)  # 2 hours
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
        logger.info("Echo background threads + WOLF + SENSORYHUB started. Running Flask server on 0.0.0.0:5000")
        app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        kill_wolf_gracefully()
        sys.exit(1)


