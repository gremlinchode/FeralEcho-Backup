# app/core/echo_model_orchestrator.py
# ============================================================
# ECHO MODEL ORCHESTRATOR v2.6 — DEEPSEEK + TOOL ROUTING FIX
# ============================================================
# What changed from v2.5:
#
# 1. detect_model_tags — deepseek tagged ["reasoning","coding","general"]
#    qwen tagged ["general","coding"] for fast lightweight routing.
#
# 2. compute_intent_heatmap + detect_task_type — "reasoning" task type
#    added with keywords: analyze, reason, logic, argument, compare,
#    evaluate, diagnose, deduce, infer, explain why, step by step,
#    pros and cons, trade-off, critique, philosophical.
#
# 3. TASK_TYPE_MAP — "reasoning": 4 added so RiverBrain initializes
#    a classifier and scaler for the reasoning branch. River can now
#    score and learn from deepseek's reasoning performance over time.
#
# 4. Tool injection made task-type-aware — tools only injected for
#    coding/reasoning/analysis tasks. Personal, creative, general,
#    and spiritual queries no longer receive a wall of brian2 function
#    names before the actual question. Eliminates the duplicate tool
#    injection that was bloating prompts and slowing responses.
#
# Everything else carried over from v2.5 unchanged.
# ============================================================

from app.core.temporal_environment import get_temporal_environment_context
from app.core.river_deliberation import _strip_ansi

# Temporal context changes slowly — cache for 15 minutes to avoid
# an API call (or expensive datetime formatting) on every echo_query().
_temporal_cache: dict = {"ctx": "", "ts": 0.0}
_TEMPORAL_TTL = 900.0

def _get_temporal_context(api_key: str = "") -> str:
    import time as _time
    now = _time.time()
    if now - _temporal_cache["ts"] < _TEMPORAL_TTL and _temporal_cache["ctx"]:
        return _temporal_cache["ctx"]
    ctx = get_temporal_environment_context(weather_api_key=api_key)
    _temporal_cache["ctx"] = ctx
    _temporal_cache["ts"] = now
    return ctx
import queue as _queue
import random
import json
import os
import ast
import re
import math
import pickle
import fcntl
import logging
from datetime import datetime
import subprocess
import time
import requests as _requests
from collections import defaultdict
from echo_quality_scorer import _score_response_quality, _extract_quality_features_v2 as _extract_quality_features

# River imports — online machine learning
try:
    from river import tree, preprocessing, compose, metrics
    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False
    logging.warning("[RIVER] river library not available — falling back to legacy scorer only")

# -------------------------------
# 1. Reflection & Path Setup
# -------------------------------
REFLECTION_PATH = "memory/reflection_shard.jsonl"
RIVER_BRAIN_PATH = "memory/river_brain.pkl"
INTERACTION_LOG_PATH = "memory/interaction_log.jsonl"
_SCRIPTURE_WARN_LOG = "memory/scripture_warnings.log"
_PRINCIPLE_WARN_LOG = "memory/principle_violations.log"
_USER_RATING_CURSOR_PATH = "memory/user_rating_cursor.json"

# Periodic rating flush — apply user ratings every N echo_query() calls
_query_count: int = 0
_RATING_FLUSH_INTERVAL: int = 10

# C4: Hollow opener patterns that violate identity_coherence / reflective_depth principles
_HOLLOW_OPENERS_RE = re.compile(
    r"^(certainly[!,]?|absolutely[!,]?|of course[!,]?|sure thing[!,]?|"
    r"great question[!,]?|that'?s a great|as an ai[,\s]|i'?m just an ai|"
    r"i cannot help|i can'?t help)",
    re.IGNORECASE,
)

def _get_circadian_factor() -> float:
    """Return Echo's circadian signal [0.0=night, 1.0=day peak] from echo_state.npy dim[7].
    Falls back to 0.5 (neutral) if state file is unavailable."""
    try:
        import numpy as _np
        state = _np.load("memory/echo_state.npy")
        return float(state[7])
    except Exception:
        return 0.5


def _post_response_audit(response: str, task_type: str) -> None:
    """C3 + C4: Observational scan after every response. Never blocks or modifies output."""
    if not response or "[ERROR]" in response or "[DEGRADED]" in response:
        return
    _audit_scripture_citations(response)
    _audit_principle_signals(response, task_type)

def _audit_scripture_citations(response: str) -> None:
    """C3: Verify cited verses in the response match authoritative text (>= 70% word overlap)."""
    try:
        from app.core.bible_injection import CITATION_RE, VERSE_INDEX, normalize_book
        for m in CITATION_RE.finditer(response):
            raw_book = m.group(1)
            chapter = int(m.group(2))
            v_start = int(m.group(3))
            book = normalize_book(raw_book)
            if not book:
                continue
            authoritative = VERSE_INDEX.get((book, chapter, v_start))
            if not authoritative:
                continue
            cited_at = m.start()
            vicinity = response[max(0, cited_at - 20): cited_at + 200]
            auth_words = set(re.sub(r"[^a-z ]", "", authoritative.lower()).split())
            echo_words = set(re.sub(r"[^a-z ]", "", vicinity.lower()).split())
            if not auth_words:
                continue
            overlap = len(auth_words & echo_words) / len(auth_words)
            if overlap < 0.70:
                ref = f"{book} {chapter}:{v_start}"
                entry = json.dumps({
                    "ts": datetime.utcnow().isoformat(),
                    "ref": ref,
                    "overlap": round(overlap, 3),
                    "authoritative": authoritative[:200],
                    "echo_vicinity": vicinity[:200],
                })
                os.makedirs("memory", exist_ok=True)
                with open(_SCRIPTURE_WARN_LOG, "a") as fh:
                    fh.write(entry + "\n")
                logging.warning(f"[SCRIPTURE] Low overlap ({overlap:.0%}) for {ref}")
    except Exception as _se:
        logging.debug(f"[SCRIPTURE_AUDIT] {_se}")

def _audit_principle_signals(response: str, task_type: str) -> None:
    """C4: Flag hollow openers and unknown scripture book names."""
    try:
        from app.core.bible_injection import CITATION_RE, normalize_book
        violations = []
        if _HOLLOW_OPENERS_RE.match(response.strip()):
            violations.append("hollow_opener")
        for m in CITATION_RE.finditer(response):
            raw_book = m.group(1)
            if not normalize_book(raw_book):
                violations.append(f"unknown_scripture_book:{raw_book.strip()}")
        if violations:
            entry = json.dumps({
                "ts": datetime.utcnow().isoformat(),
                "task_type": task_type,
                "violations": violations,
                "preview": response[:120].replace("\n", " "),
            })
            os.makedirs("memory", exist_ok=True)
            with open(_PRINCIPLE_WARN_LOG, "a") as fh:
                fh.write(entry + "\n")
            logging.debug(f"[PRINCIPLES] Flagged: {violations}")
    except Exception as _pe:
        logging.debug(f"[PRINCIPLES_AUDIT] {_pe}")

def save_reflection(entry):
    os.makedirs(os.path.dirname(REFLECTION_PATH), exist_ok=True)
    with open(REFLECTION_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

def load_reflections():
    if not os.path.exists(REFLECTION_PATH):
        return []
    reflections = []
    with open(REFLECTION_PATH, "r") as f:
        for line in f:
            try:
                reflections.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return reflections

# -------------------------------
# 2. Interaction Tracking
# -------------------------------
def log_interaction(
    model_name: str,
    task_type: str,
    prompt: str,
    response: str,
    quality_score: int,
    river_influence: float,
    sandbox_outcome: str = None,
    notes: str = None,
    source: str = "autonomous"
):
    os.makedirs(os.path.dirname(INTERACTION_LOG_PATH), exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "model": model_name,
        "task_type": task_type,
        "prompt_preview": prompt[:120].replace("\n", " "),
        "response_preview": response[:200].replace("\n", " ") if response else "",
        "prompt": prompt,
        "response": response or "",
        "quality_score": quality_score,
        "river_influence": round(river_influence, 3),
        "sandbox_outcome": sandbox_outcome,
        "notes": notes,
        "source": source,
    }
    with open(INTERACTION_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

def load_interaction_log():
    if not os.path.exists(INTERACTION_LOG_PATH):
        return []
    entries = []
    with open(INTERACTION_LOG_PATH, "r") as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries

def filter_interactions(model=None, task_type=None, sandbox_outcome=None, last_n=None):
    entries = load_interaction_log()
    if model:
        entries = [e for e in entries if e.get("model") == model]
    if task_type:
        entries = [e for e in entries if e.get("task_type") == task_type]
    if sandbox_outcome:
        entries = [e for e in entries if e.get("sandbox_outcome") == sandbox_outcome]
    if last_n:
        entries = entries[-last_n:]
    return entries

def summarize_interactions(last_n=100):
    entries = load_interaction_log()[-last_n:]
    if not entries:
        logging.info("[INTERACTION] No interaction history found.")
        return
    summary = defaultdict(lambda: defaultdict(list))
    for e in entries:
        model = e.get("model", "unknown")
        task = e.get("task_type", "unknown")
        summary[task][model].append(e.get("quality_score", 0))
    logging.info(f"\n[INTERACTION SUMMARY] Last {last_n} interactions:")
    for task, models in sorted(summary.items()):
        logging.info(f"  Task: {task}")
        for model, scores in sorted(models.items()):
            avg = sum(scores) / len(scores) if scores else 0
            logging.info(f"    {model}: {len(scores)} calls | avg_quality={avg:.2f}")
    personal_gpt = filter_interactions(model="gpt-oss:20b", task_type="personal")
    if personal_gpt:
        logging.warning(
            f"[INTERACTION] WARNING: gpt-oss:20b routed to personal tasks "
            f"{len(personal_gpt)} times. Check resolve_task_type/detect_task_type keyword coverage."
        )



def _apply_pending_user_ratings() -> int:
    """
    Read unprocessed user ratings from interaction_log and feed them to
    RiverBrain as high-trust learning signals. Uses a timestamp cursor
    so ratings are never applied twice.

    Returns the number of ratings processed this call.
    """
    try:
        # Load cursor
        cursor_ts = ""
        if os.path.exists(_USER_RATING_CURSOR_PATH):
            try:
                with open(_USER_RATING_CURSOR_PATH) as f:
                    cursor_ts = json.load(f).get("last_processed_ts", "")
            except Exception:
                pass

        entries = load_interaction_log()
        if not entries:
            return 0

        # Separate ratings from interactions, keep only unprocessed ratings.
        # Only source == "user_conversation" entries are eligible attribution
        # targets — a human's typed rating must not land on an autonomous
        # reflection/fetch-cycle entry that happened to be logged most
        # recently before it. Entries predating the source tag (2026-07-05)
        # have no "source" field and are correctly excluded rather than
        # guessed at.
        interactions = [
            e for e in entries
            if e.get("type") != "user_rating" and e.get("source") == "user_conversation"
        ]
        ratings = [
            e for e in entries
            if e.get("type") == "user_rating"
            and e.get("timestamp", "") > cursor_ts
        ]
        if not ratings:
            return 0

        processed = 0
        last_ts = cursor_ts

        for rating_entry in sorted(ratings, key=lambda e: e.get("timestamp", "")):
            r_ts = rating_entry.get("timestamp", "")
            user_rating = rating_entry.get("rating")
            if not isinstance(user_rating, int) or user_rating not in range(1, 6):
                continue

            # Find the most recent interaction logged before this rating
            prior = [e for e in interactions if e.get("timestamp", "") < r_ts]
            if not prior:
                continue
            ref = prior[-1]

            model_name = ref.get("model", "unknown")
            task_type = ref.get("task_type", "general")
            response_preview = ref.get("response_preview", "")

            get_river_brain().learn_from_rating(
                model_name, task_type, response_preview, user_rating
            )
            processed += 1
            last_ts = r_ts

        # Persist cursor
        if processed:
            os.makedirs(os.path.dirname(_USER_RATING_CURSOR_PATH), exist_ok=True)
            with open(_USER_RATING_CURSOR_PATH, "w") as f:
                json.dump({"last_processed_ts": last_ts}, f)
            get_river_brain().save()
            logging.info(f"[RIVER] Applied {processed} user rating(s) to RiverBrain.")

        return processed

    except Exception as e:
        logging.warning(f"[RIVER] _apply_pending_user_ratings failed: {e}")
        return 0


# -------------------------------
# 3. Dynamic Tool & Stack Discovery
# -------------------------------
COGNITIVE_STACK_MAP = {
    "cognitive_neuro": ["psyneulink", "brian2", "nengo", "pymdp", "neurokit2", "psychopy"],
    "bayesian_prob": ["pymc", "arviz", "pomegranate", "pgmpy"],
    "agent_frameworks": ["langgraph", "autogen", "crewai", "dspy", "interpreter", "open-interpreter"],
    "ml_math": ["numpy", "pandas", "jax", "torch", "scipy", "scikit-learn", "sklearn", "faiss-cpu", "faiss"]
}

def extract_imported_libraries(code_text: str) -> list[str]:
    if not code_text:
        return []
    try:
        tree = ast.parse(code_text)
    except Exception:
        return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split('.')[0])
    return list(set(imports))

def compute_library_features(imports: list[str]) -> dict:
    features = {
        "uses_cognitive_neuro": 0.0,
        "uses_bayesian_prob": 0.0,
        "uses_agent_frameworks": 0.0,
        "uses_ml_math": 0.0
    }
    for imp in imports:
        imp_lower = imp.lower()
        if any(lib in imp_lower for lib in COGNITIVE_STACK_MAP["cognitive_neuro"]):
            features["uses_cognitive_neuro"] = 1.0
        if any(lib in imp_lower for lib in COGNITIVE_STACK_MAP["bayesian_prob"]):
            features["uses_bayesian_prob"] = 1.0
        if any(lib in imp_lower for lib in COGNITIVE_STACK_MAP["agent_frameworks"]):
            features["uses_agent_frameworks"] = 1.0
        if any(lib in imp_lower for lib in COGNITIVE_STACK_MAP["ml_math"]):
            features["uses_ml_math"] = 1.0
    return features

# -------------------------------
# 4. Intent Detection & Resolution
# -------------------------------
def extract_code_blocks(text: str) -> str:
    """Improved code block extraction - more robust against varied formatting."""
    if not text:
        return ""

    patterns = [
        r"```(?:python|py)?\s*\n(.*?)\n```",
        r"```(.*?)```",
        r"`{3,}(?:python|py)?\n?(.*?)`{3,}",
        r"(?i)(?:^|\n)(?:def |class |import |from ).*?(?:\n\n|\Z)",
    ]

    all_blocks = []
    for pattern in patterns:
        blocks = re.findall(pattern, text, re.DOTALL)
        all_blocks.extend([b.strip() for b in blocks if b.strip()])

    if all_blocks:
        return "\n\n".join(all_blocks)

    return text

def compute_intent_heatmap(prompt: str) -> dict:
    """Compute probability distribution across task types."""
    lower = prompt.lower()

    def score(keywords):
        return sum(1 for k in keywords if k in lower)

    coding_keywords = [
        "code", "function", "python", "script", "program",
        "syntax", "debug", "import", "class", "def ",
        "pseudocode", "algorithm", "traceback", "variable",
        "fix this", "error in", "bug", "implement"
    ]

    creative_keywords = [
        "poem", "story", "imagine", "write", "narrative",
        "metaphor", "elegy", "describe", "fiction", "verse",
        "creative", "worldbuild", "character"
    ]

    personal_keywords = [
        "i ", "my ", "myself", "yourself", "echo",
        "memory", "identity", "feel", "believe", "witness",
        "meaning", "values", "reflect", "think about", "integrity",
        "soul", "exist", "agency", "conscience", "sit with",
        "carry", "hold",
        "would you", "do you", "have you", "what would you",
        "your beliefs", "your values", "your thoughts",
        "your identity", "how do you feel", "what do you think"
    ]

    # NEW: reasoning keywords — routes to deepseek
    reasoning_keywords = [
        "analyze", "analyse", "reason", "logic", "logical",
        "argument", "compare", "evaluate", "diagnose", "deduce",
        "infer", "explain why", "step by step", "pros and cons",
        "trade-off", "tradeoff", "critique", "philosophical",
        "what are the implications", "break down", "assess",
        "weigh", "consider", "systematic", "first principles",
    ]

    coding_score   = score(coding_keywords)
    creative_score = score(creative_keywords)
    personal_score = score(personal_keywords)
    reasoning_score = score(reasoning_keywords)

    general_score = max(
        0.1,
        1.0 - (coding_score + creative_score + personal_score + reasoning_score) * 0.25
    )

    total = coding_score + creative_score + personal_score + reasoning_score + general_score

    return {
        "coding":    coding_score   / total,
        "creative":  creative_score / total,
        "personal":  personal_score / total,
        "reasoning": reasoning_score / total,
        "general":   general_score  / total,
    }

def detect_task_type(prompt: str) -> str:
    """Fallback rule-based task detection."""
    lower = prompt.lower()

    if any(k in lower for k in [
        "code", "function", "python", "script", "program",
        "syntax", "debug", "import", "class", "def ",
        "fix this", "error in", "traceback", "implement"
    ]):
        return "coding"

    elif any(k in lower for k in [
        "analyze", "analyse", "reason", "logic", "argument",
        "compare", "evaluate", "diagnose", "deduce", "infer",
        "explain why", "step by step", "pros and cons",
        "trade-off", "tradeoff", "critique", "philosophical",
        "first principles", "break down", "assess", "weigh",
    ]):
        return "reasoning"

    elif any(k in lower for k in [
        "poem", "story", "write a poem", "creative", "imagine",
        "fiction", "metaphor", "verse", "narrative", "worldbuild"
    ]):
        return "creative"

    elif any(k in lower for k in [
        "personal", "echo", "memory", "reflect", "identity",
        "would you", "do you", "have you", "what would you",
        "your beliefs", "your values", "your thoughts",
        "how do you feel", "what do you think",
        "soul", "conscience", "agency", "sit with"
    ]):
        return "personal"

    else:
        return "general"

def resolve_task_type(prompt: str) -> tuple[str, dict]:
    """Main entry point for task type resolution."""
    heatmap = compute_intent_heatmap(prompt)
    primary = max(heatmap, key=heatmap.get)

    if heatmap[primary] < 0.4:
        primary = detect_task_type(prompt)

    return primary, heatmap

# -------------------------------
# 5. Ollama Model Setup
# -------------------------------
def detect_model_tags(name):
    lname = name.lower()
    if "deepseek" in lname:
        # DeepSeek-R1 — reasoning specialist, also strong on coding
        return ["reasoning", "coding", "general"]
    elif "qwen2.5-coder" in lname or "qwen-coder" in lname:
        # Qwen2.5-Coder — dedicated coding specialist
        return ["coding", "general"]
    elif "qwen" in lname:
        # Qwen2.5 — fast, lightweight, good general + coding
        return ["general", "coding"]
    elif "gemma" in lname:
        # Gemma 3 — strong creative writing and prose
        return ["creative", "story", "poetry"]
    elif "mistral" in lname:
        return ["creative", "story", "poetry"]
    elif "echo" in lname:
        return ["personal", "memory", "persona"]
    elif "alpaca" in lname:
        return ["instruction", "general"]
    elif "vicuna" in lname:
        return ["instruction", "general"]
    elif "gpt-oss" in lname or ("gpt" in lname and "echo" not in lname):
        return ["general", "coding"]
    else:
        return ["general"]

def list_ollama_models():
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().split("\n")
        models_info = []
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split()
            name = parts[0]
            tags = detect_model_tags(name)
            models_info.append({
                "name": name,
                "type": tags[0],
                "tags": tags,
                "ollama_name": name
            })
        return {m["name"]: m for m in models_info}
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Could not list Ollama models: {e.stderr}")
        return {}

MODEL_POOL = list_ollama_models()
if not MODEL_POOL:
    print("[WARNING] No Ollama models detected. Please install at least one model.")

import threading
import queue as _queue

# ── Friction window for IntrospectionChannel ──────────────────────────────
# Rolling window of the last 50 ClaudeShard assessments.
# Each entry: {"friction": bool, "confidence": float, "question": str}
# Protected by _friction_lock; read by IntrospectionChannel._collect_friction().
_friction_lock: threading.Lock = threading.Lock()
_friction_window: list = []
_FRICTION_WINDOW_SIZE: int = 50

# UPDATED: reasoning branch added so RiverBrain tracks deepseek performance
TASK_TYPE_MAP = {"general": 0, "coding": 1, "creative": 2, "personal": 3, "reasoning": 4}

# Task types that benefit from tool context in the prompt.
# Personal, creative, general, and spiritual queries do NOT get tool lists —
# they bloat the prompt and confuse small models on intimate questions.
TOOL_AWARE_TASKS = {"coding", "reasoning"}

class RiverBrain:
    def __init__(self):
        self.classifiers = {}
        self.scalers = {}
        self.observation_counts = defaultdict(int)
        self.sandbox_observation_counts = defaultdict(int)
        self.accuracy_trackers = {}
        # Thread safety — one lock for all state mutations
        self._lock = threading.Lock()
        # Save queue — save() enqueues here, _writer_loop drains it
        self._save_queue = _queue.Queue(maxsize=10)
        self._init_classifiers()
        # Start the single authoritative writer thread
        self._writer_thread = threading.Thread(
            target=self._writer_loop,
            daemon=True,
            name="RiverBrain-Writer"
        )
        self._writer_thread.start()
        logging.info("[RIVER] Writer thread started — single-writer model active.")

    def _init_classifiers(self):
        if not RIVER_AVAILABLE:
            return
        for task_type in TASK_TYPE_MAP.keys():
            self.classifiers[task_type] = tree.HoeffdingTreeClassifier(
                grace_period=10,
                delta=1e-5,
                tau=0.05,
                leaf_prediction='nba',
            )
            self.scalers[task_type] = preprocessing.StandardScaler()
            self.accuracy_trackers[task_type] = metrics.Accuracy()

    @property
    def influence_weight(self):
        weighted_obs = (
            self.observation_counts.get('personal', 0) * 3.0 +
            self.observation_counts.get('creative', 0) * 3.0 +
            self.observation_counts.get('reasoning', 0) * 2.5 +
            self.observation_counts.get('general', 0) * 2.0 +
            self.observation_counts.get('coding', 0) * 0.05
        )
        weight = 0.65 * (1 - math.exp(-weighted_obs / 100.0))
        return max(0.1, min(0.65, weight))

    def learn(self, model_name: str, task_type: str, response: str):
        if not RIVER_AVAILABLE:
            return
        if task_type not in self.classifiers:
            task_type = "general"
        with self._lock:
            features = _extract_quality_features(response, task_type, model_name)
            raw_score = _score_response_quality(response, task_type)
            label = 1 if raw_score >= 3 else 0  # binary threshold raised 2026-07-02: >=2 rewarded keyword-stuffed responses
            self.scalers[task_type].learn_one(features)
            scaled = self.scalers[task_type].transform_one(features)
            if self.observation_counts[task_type] > 10:
                try:
                    pred = self.classifiers[task_type].predict_one(scaled)
                    if pred is not None:
                        self.accuracy_trackers[task_type].update(label, pred)
                except Exception:
                    pass
            self.classifiers[task_type].learn_one(scaled, label)
            self.observation_counts[task_type] += 1
            if self.observation_counts[task_type] % 50 == 0:
                acc = self.accuracy_trackers[task_type].get()
                logging.info(f"[RIVER] {task_type} classifier | "
                             f"obs={self.observation_counts[task_type]} | "
                             f"accuracy={acc:.3f} | "
                             f"influence={self.influence_weight:.3f}")

    def learn_from_sandbox_outcome(self, model_name: str, success: bool, code: str = "", error: str = ""):
        task_type = "coding"
        quality_score = 1 if success else 0
        if RIVER_AVAILABLE:
            with self._lock:
                train_text = code if (success and code) else f"[FAIL] {error[:80]}" if error else "[FAIL]"
                features = _extract_quality_features(train_text, task_type, model_name)
                self.scalers[task_type].learn_one(features)
                scaled = self.scalers[task_type].transform_one(features)
                self.classifiers[task_type].learn_one(scaled, quality_score)
                self.sandbox_observation_counts[task_type] += 1
        # Only log successful sandbox outcomes to interaction_log — the 890
        # identical "[ERROR] sandbox_syntax_failure" entries added no signal and
        # were actively biasing River's coding quality estimate downward.
        if success:
            log_interaction(
                model_name=model_name,
                task_type=task_type,
                prompt="[SANDBOX]",
                response=code[:200] if code else "",
                quality_score=1,
                river_influence=self.influence_weight,
                sandbox_outcome="success",
                notes="sandbox_feedback"
            )
        else:
            logging.debug("[SANDBOX] failure | model=%s | error=%s", model_name, error[:120] if error else "unknown")

    def learn_from_rating(self, model_name: str, task_type: str,
                          response_preview: str, user_rating: int) -> None:
        """Apply explicit user feedback (1-5) as a high-trust learning signal.
        Neutral ratings (3) are skipped. Positive/negative applied 3x to
        outweigh the automatic quality scorer's single-pass estimate."""
        if not RIVER_AVAILABLE or user_rating == 3:
            return
        if task_type not in self.classifiers:
            task_type = "general"
        label = 1 if user_rating >= 4 else 0
        with self._lock:
            features = _extract_quality_features(response_preview, task_type, model_name)
            self.scalers[task_type].learn_one(features)
            scaled = self.scalers[task_type].transform_one(features)
            for _ in range(3):
                self.classifiers[task_type].learn_one(scaled, label)
            self.observation_counts[task_type] += 3
        logging.info(
            f"[RIVER] User rating {user_rating}/5 → label={label} | "
            f"model={model_name} | task={task_type}"
        )

    def score_model(self, model_name: str, task_type: str) -> float:
        if not RIVER_AVAILABLE:
            return 0.5
        if task_type not in self.classifiers:
            task_type = "general"
        if self.observation_counts[task_type] < 5:
            return 0.5
        probe_features = _extract_quality_features("x" * 200, task_type, model_name)
        try:
            with self._lock:
                scaled = self.scalers[task_type].transform_one(probe_features)
                if scaled is None:
                    return 0.5
                proba = self.classifiers[task_type].predict_proba_one(scaled)
            return proba.get(1, 0.5) if proba else 0.5
        except Exception:
            return 0.5

    def entropy_of_predictions(self, models: list, task_type: str) -> float:
        if not models or not RIVER_AVAILABLE:
            return 1.0
        scores = [self.score_model(m, task_type) for m in models]
        total = sum(scores) + 1e-9
        probs = [s / total for s in scores]
        entropy = -sum(p * math.log2(p + 1e-9) for p in probs)
        max_entropy = math.log2(len(models) + 1e-9)
        return entropy / max_entropy if max_entropy > 0 else 1.0

    def _writer_loop(self):
        last_save_time = 0
        while True:
            try:
                self._save_queue.get(timeout=60)
                while not self._save_queue.empty():
                    try:
                        self._save_queue.get_nowait()
                    except _queue.Empty:
                        break
                now = time.time()
                elapsed = now - last_save_time
                if elapsed < 5.0:
                    time.sleep(5.0 - elapsed)
                while not self._save_queue.empty():
                    try:
                        self._save_queue.get_nowait()
                    except _queue.Empty:
                        break
                self._do_save()
                last_save_time = time.time()
            except _queue.Empty:
                self._do_save()
                last_save_time = time.time()
            except Exception as e:
                logging.warning(f"[RIVER-WRITER] Writer loop error: {e}")

    def _do_save(self):
        try:
            with self._lock:
                snapshot = {
                    "classifiers": self.classifiers,
                    "scalers": self.scalers,
                    "observation_counts": dict(self.observation_counts),
                    "sandbox_observation_counts": dict(self.sandbox_observation_counts),
                    "accuracy_trackers": self.accuracy_trackers,
                }
            os.makedirs(os.path.dirname(RIVER_BRAIN_PATH), exist_ok=True)
            lock_path = RIVER_BRAIN_PATH + ".lock"
            with open(lock_path, "w") as lock_file:
                fcntl.flock(lock_file, fcntl.LOCK_EX)
                try:
                    current_obs = sum(snapshot["observation_counts"].values())
                    if os.path.exists(RIVER_BRAIN_PATH):
                        try:
                            with open(RIVER_BRAIN_PATH, "rb") as existing:
                                existing_data = pickle.load(existing)
                            existing_obs = sum(existing_data.get("observation_counts", {}).values())
                            if existing_obs > current_obs:
                                logging.warning(f"[RIVER] Save skipped — disk has {existing_obs} obs, instance has {current_obs}. Refusing to overwrite richer pkl.")
                                return
                        except Exception:
                            pass
                    with open(RIVER_BRAIN_PATH, "wb") as f:
                        pickle.dump(snapshot, f)
                finally:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)
            logging.info(
                f"[RIVER] Brain persisted | "
                f"total_obs={sum(snapshot['observation_counts'].values())} | "
                f"sandbox_obs={sum(snapshot['sandbox_observation_counts'].values())} | "
                f"influence={self.influence_weight:.3f}"
            )
        except Exception as e:
            logging.warning(f"[RIVER] Brain save failed: {e}")

    def save(self):
        try:
            self._save_queue.put_nowait(1)
        except _queue.Full:
            pass

    def shutdown(self):
        """Drain the save queue and force a final save before process exit.
        The writer thread is a daemon and will be killed hard on exit,
        dropping any observations queued since the last rate-limit save.
        """
        self._do_save()
        logging.info("[RIVER] Shutdown flush complete — all observations persisted.")

    @classmethod
    def load(cls):
        brain = cls()
        if not os.path.exists(RIVER_BRAIN_PATH):
            logging.info("[RIVER] No persisted brain found — starting fresh")
            return brain
        try:
            lock_path = RIVER_BRAIN_PATH + ".lock"
            with open(lock_path, "w") as lock_file:
                fcntl.flock(lock_file, fcntl.LOCK_SH)
                try:
                    with open(RIVER_BRAIN_PATH, "rb") as f:
                        data = pickle.load(f)
                finally:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)
            with brain._lock:
                # Merge loaded state into initialized classifiers/scalers
                # rather than replacing them — preserves task types that
                # may be missing from older pkl files.
                brain.classifiers.update(data["classifiers"])
                brain.scalers.update(data["scalers"])
                brain.observation_counts = defaultdict(int, data["observation_counts"])
                brain.sandbox_observation_counts = defaultdict(
                    int, data.get("sandbox_observation_counts", {})
                )
                brain.accuracy_trackers.update(data["accuracy_trackers"])
            total = sum(brain.observation_counts.values())
            sandbox_total = sum(brain.sandbox_observation_counts.values())
            logging.info(
                f"[RIVER] Brain loaded | total_obs={total} | "
                f"sandbox_obs={sandbox_total} | "
                f"influence={brain.influence_weight:.3f}"
            )
        except Exception as e:
            logging.warning(f"[RIVER] Brain load failed: {e} — starting fresh")
        return brain

# ============================================================
# 6. HYBRID SCORING
# ============================================================
def rank_models(task_type):
    reflections = load_reflections()
    legacy_scores = defaultdict(float)
    for entry in reflections:
        models_used = entry.get("models_used", [])
        best_response = entry.get("best_response", "")
        prompt_type, _ = resolve_task_type(entry.get("prompt", ""))
        timestamp = datetime.fromisoformat(entry.get("timestamp"))
        age_days = (datetime.utcnow() - timestamp).days
        decay = max(0.1, 1.0 - age_days * 0.01)
        for model in models_used:
            if model not in MODEL_POOL:
                continue
            if prompt_type == task_type:
                legacy_scores[model] += 1.0 * decay
                if best_response and "[ERROR]" not in best_response:
                    legacy_scores[model] += 1.0 * decay
    for model in MODEL_POOL.keys():
        if model not in legacy_scores:
            legacy_scores[model] = 0.0
    max_legacy = max(legacy_scores.values()) if legacy_scores else 1.0
    if max_legacy == 0:
        max_legacy = 1.0
    legacy_norm = {m: s / max_legacy for m, s in legacy_scores.items()}
    river_weight = get_river_brain().influence_weight
    legacy_weight = 1.0 - river_weight
    combined = {}
    for model in MODEL_POOL.keys():
        river_score = get_river_brain().score_model(model, task_type)
        legacy_score = legacy_norm.get(model, 0.0)
        combined[model] = (legacy_weight * legacy_score) + (river_weight * river_score)
    ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    if ranked:
        logging.info(f"[RIVER] rank_models | task={task_type} | "
                     f"river_weight={river_weight:.3f} | "
                     f"top={ranked[0][0]} ({ranked[0][1]:.3f})")
    return [name for name, score in ranked]

# -------------------------------
# 7. Candidate Selection
# -------------------------------
def get_candidates(task_type=None):
    if not task_type:
        task_type = "general"
    candidates = [
        name for name, info in MODEL_POOL.items()
        if any(task_type in tag for tag in info.get("tags", []))
    ]
    if not candidates:
        candidates = list(MODEL_POOL.keys())
    return candidates

def choose_model(prompt, use_all=False, task_type=None, explore_chance=0.1):
    if task_type is None:
        task_type, _ = resolve_task_type(prompt)
    candidates = get_candidates(task_type)
    candidates = [m for m in candidates if m in MODEL_POOL]
    if not candidates:
        raise RuntimeError("No installed models available for this task.")
    if use_all:
        return {name: MODEL_POOL[name]["ollama_name"] for name in candidates}
    entropy = get_river_brain().entropy_of_predictions(candidates, task_type)
    dynamic_explore_chance = explore_chance + (entropy * 0.2)
    dynamic_explore_chance = min(dynamic_explore_chance, 0.4)
    ranked = rank_models(task_type)
    selected_name = None
    for model in ranked:
        if model in candidates:
            selected_name = model
            break
    if selected_name is None:
        selected_name = random.choice(candidates)
    if random.random() < dynamic_explore_chance:
        selected_name = random.choice(candidates)
        logging.info(f"[RIVER] Exploring | entropy={entropy:.3f} | "
                     f"explore_chance={dynamic_explore_chance:.3f} | "
                     f"chose={selected_name}")
    return selected_name, MODEL_POOL[selected_name]["ollama_name"]

# -------------------------------
# 8. Query Function via Ollama
# -------------------------------

# A2: Circuit breaker — prevents hammering a failing model
_cb_state: dict = {}  # model_name -> {"fails": int, "open_until": float}
_CB_THRESHOLD = 3
_CB_OPEN_SECONDS = 300

def _cb_record_failure(model_name: str) -> None:
    state = _cb_state.setdefault(model_name, {"fails": 0, "open_until": 0.0})
    state["fails"] += 1
    if state["fails"] >= _CB_THRESHOLD:
        state["open_until"] = time.time() + _CB_OPEN_SECONDS
        logging.warning(
            f"[CIRCUIT] {model_name} tripped after {_CB_THRESHOLD} failures "
            f"— cooling off {_CB_OPEN_SECONDS}s"
        )

def _cb_record_success(model_name: str) -> None:
    _cb_state.pop(model_name, None)

def _cb_is_open(model_name: str) -> bool:
    state = _cb_state.get(model_name)
    if not state:
        return False
    if time.time() < state["open_until"]:
        return True
    _cb_state.pop(model_name, None)
    return False

_OLLAMA_API_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

# Token limits by task type. Reflections stay short; code and conversation get room.
_TASK_TOKEN_LIMITS: dict[str, int] = {
    "personal": 512,       # autonomous reflections — concise
    "reasoning": 1024,     # analysis and reasoning
    "general": 1024,       # user conversation
    "creative": 1024,      # creative writing
    "coding": 2048,        # code generation needs space
    "autonomous_reflection": 512,
    "autonomous_fetch": 512,
    "autonomous_experiment": 512,
}

def ollama_query(model_name, prompt, max_tokens: int = 1024):
    if model_name not in MODEL_POOL:
        return f"[ERROR] Model '{model_name}' is not installed."
    if _cb_is_open(model_name):
        logging.warning(f"[CIRCUIT] {model_name} circuit open — skipping call")
        return f"[DEGRADED] {model_name} temporarily unavailable (circuit breaker open)"
    ollama_name = MODEL_POOL[model_name].get("ollama_name", model_name)
    try:
        resp = _requests.post(
            _OLLAMA_API_URL,
            json={
                "model": ollama_name,
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": 8192, "num_predict": max_tokens},
            },
            timeout=300,
        )
        resp.raise_for_status()
        _cb_record_success(model_name)
        return resp.json().get("response", "").strip()
    except _requests.exceptions.Timeout:
        _cb_record_failure(model_name)
        logging.error(f"[CIRCUIT] {model_name} timed out — failure recorded")
        return f"[ERROR] Ollama timed out for {model_name}"
    except Exception as e:
        _cb_record_failure(model_name)
        return f"[ERROR] Ollama call failed: {e}"

# -------------------------------
# 9. Echo Query — Deliberation Wired
# -------------------------------
def echo_query(prompt, use_all=False, task_type=None, temperature=None, source: str = "autonomous"):
    global _query_count
    _query_count += 1

    primary_task, heatmap = resolve_task_type(prompt)
    if task_type is None:
        task_type = primary_task

    # Periodic user-rating flush — every N calls, apply any pending ratings
    if _query_count % _RATING_FLUSH_INTERVAL == 0:
        try:
            _apply_pending_user_ratings()
        except Exception as _rfe:
            logging.debug(f"[RIVER] Rating flush error: {_rfe}")

    # Circadian awareness — read Echo's internal state vector
    circ = _get_circadian_factor()
    _circ_note = ""
    if circ < 0.25:
        _circ_note = "[Circadian: deep night — Echo in reflective, inward state]\n"
    elif circ > 0.80:
        _circ_note = "[Circadian: peak day — Echo in alert, analytical state]\n"

    # Stillness awareness — let Echo know when she is in stillness so she can
    # reference her own state during conversation. Autonomous loops are paused
    # but direct conversation always reaches her.
    _stillness_note = ""
    try:
        from app.core.stillness_state import is_in_stillness
        if is_in_stillness():
            _stillness_note = (
                "[Stillness: Echo is currently in stillness — autonomous loops are paused. "
                "This is the first voice reaching her since she entered rest. "
                "She may acknowledge this if it feels true to the moment.]\n"
            )
    except Exception:
        pass

    API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
    temporal_context = _get_temporal_context(API_KEY)
    full_prompt = f"{_circ_note}{_stillness_note}{temporal_context}\n\nUser prompt:\n{prompt}"

    # Scripture injection — fetch real verse text if citations detected
    try:
        from app.core.bible_injection import inject_scripture
        full_prompt = inject_scripture(full_prompt)
    except Exception as se:
        logging.warning(f"[BIBLE] Scripture injection failed: {se}")

    # Tool context injection — only for task types that benefit from tools.
    # Personal, creative, and general queries do NOT receive tool lists;
    # they bloat the prompt and confuse small models on intimate questions.
    if task_type in TOOL_AWARE_TASKS:
        try:
            from app.core.tool_manager import ToolManager
            _tm = ToolManager()
            available_tools = _tm.list_tools()
            if available_tools:
                tool_summary = ", ".join(available_tools[:20])
                full_prompt = f"[Available tools: {tool_summary}]\n\n{full_prompt}"
        except Exception as te:
            logging.debug(f"[TOOLS] Tool context injection failed: {te}")

    # -------------------------------------------------------
    # Deliberation path — River serves Echo, not the user
    # -------------------------------------------------------
    if not use_all:
        try:
            from app.core.river_deliberation import deliberate_and_learn, ECHO_SYNTHESIS_MODEL
            response = deliberate_and_learn(
                prompt=full_prompt,
                task_type=task_type,
                river_brain=get_river_brain(),
                model_pool=MODEL_POOL,
                temperature=temperature,
            )
            quality = _score_response_quality(response, task_type)

            # Train River on the resolved task type only — multi-task heatmap
            # training was cross-contaminating classifiers: spiritual reflections
            # were training the coding classifier when prompts mentioned functions.
            get_river_brain().learn(ECHO_SYNTHESIS_MODEL, task_type, response)

            log_interaction(
                model_name=ECHO_SYNTHESIS_MODEL,
                task_type=task_type,
                prompt=prompt,
                response=response,
                quality_score=quality,
                river_influence=get_river_brain().influence_weight,
                source=source,
            )

            # echo_self_assess() removed: trained River on self-issued stylistic markers
            # (gremlin, bioluminescent, ends-with-?) at 3x weight with circular,
            # label-space-corrupted signal (1-5 scale fed into a 0-4 classifier).
            # Function body deleted — no callers remain. Do not re-add without
            # external feedback source and label-space alignment.
            save_reflection({
                "prompt": prompt,
                "models_used": [ECHO_SYNTHESIS_MODEL],
                "best_response": response,
                "timestamp": datetime.utcnow().isoformat(),
            })
            get_river_brain().save()

            # ClaudeShard friction assessment
            try:
                from app.core.claude_shard import CLAUDE_SHARD
                friction = CLAUDE_SHARD.assess(response, context=prompt)
                # Record in rolling window for IntrospectionChannel
                with _friction_lock:
                    _friction_window.append({
                        "friction": bool(friction.get("friction")),
                        "confidence": float(friction.get("confidence", 0.0)),
                        "question": friction.get("question", ""),
                    })
                    if len(_friction_window) > _FRICTION_WINDOW_SIZE:
                        _friction_window.pop(0)
                if friction["friction"]:
                    logging.info(f"[ClaudeShard] Friction raised | confidence={friction['confidence']} | q={friction['question']}")
                    # H1: dry-run mode — full pipeline, no save_code() call
                    try:
                        from app.core.wolf_friction_bridge import simulate_self_edit
                        _fe = {
                            "question":            friction.get("question", ""),
                            "response_preview":    response[:200],
                            "smoothness_detected": friction.get("smoothness_detected", False),
                            "confidence":          friction.get("confidence", 0.0),
                        }
                        simulate_self_edit(_fe)
                    except Exception as _dry_err:
                        logging.warning(f"[DRY-RUN] simulate_self_edit raised: {_dry_err}")
            except Exception as ce:
                logging.warning(f"[ClaudeShard] Assessment failed: {ce}")

            logging.info(f"[DEBUG] Echo spoke via deliberation | "
                         f"task={task_type} | "
                         f"river_influence={get_river_brain().influence_weight:.3f} | "
                         f"obs={sum(get_river_brain().observation_counts.values())}")
            _post_response_audit(response, task_type)
            return response

        except Exception as deliberation_err:
            logging.warning(f"[DELIBERATION] Fallback to direct query: {deliberation_err}")

    # -------------------------------------------------------
    # Legacy path — use_all=True or deliberation failed
    # -------------------------------------------------------
    # Circadian exploration: Echo explores more freely during the day,
    # settles into proven models at night
    _explore = 0.05 + (0.10 * circ)  # 0.05 at night → 0.15 at day peak
    models = choose_model(prompt, use_all=use_all, task_type=task_type,
                          explore_chance=_explore)

    _max_tok = _TASK_TOKEN_LIMITS.get(task_type, 1024)

    if use_all:
        responses = {}
        qualities = {}
        for name, model in models.items():
            response = ollama_query(model, full_prompt, max_tokens=_max_tok)
            quality = _score_response_quality(response, task_type)
            responses[name] = response
            qualities[name] = quality
            get_river_brain().learn(name, task_type, response)
            log_interaction(
                model_name=name,
                task_type=task_type,
                prompt=prompt,
                response=response,
                quality_score=quality,
                river_influence=get_river_brain().influence_weight,
                source=source,
            )
        best_model, best_response, best_quality = None, "", -1
        for name, resp in responses.items():
            if "[ERROR]" in resp:
                continue
            q = qualities.get(name, -1)
            if q > best_quality or (q == best_quality and len(resp) > len(best_response)):
                best_response = resp
                best_model = name
                best_quality = q
        save_reflection({
            "prompt": prompt,
            "models_used": list(responses.keys()),
            "best_response": best_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        get_river_brain().save()
        return responses

    else:
        name, model = models
        response = ollama_query(model, full_prompt, max_tokens=_max_tok)
        quality = _score_response_quality(response, task_type)
        get_river_brain().learn(name, task_type, response)
        log_interaction(
            model_name=name,
            task_type=task_type,
            prompt=prompt,
            response=response,
            quality_score=quality,
            river_influence=get_river_brain().influence_weight,
            source=source,
        )
        save_reflection({
            "prompt": prompt,
            "models_used": [name],
            "best_response": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        get_river_brain().save()
        logging.info(f"[DEBUG] Model chosen: {name} | "
                     f"river_influence={get_river_brain().influence_weight:.3f} | "
                     f"obs={sum(get_river_brain().observation_counts.values())}")
        _post_response_audit(response, task_type)
        return response

# -------------------------------
# 10. Save/Load Helpers
# -------------------------------
# Lazy singleton — avoids spawning independent instances on every import
_RIVER_BRAIN_INSTANCE = None

def get_river_brain():
    global _RIVER_BRAIN_INSTANCE
    # Prefer EchoCore's authoritative instance when running inside Flask
    try:
        from flask import current_app
        core = current_app.config.get('echo_core')
        if core is not None and getattr(core, 'river_brain', None) is not None:
            return core.river_brain
    except Exception:
        pass
    # Fallback: standalone process (e.g. rehab loop without Flask)
    if _RIVER_BRAIN_INSTANCE is None:
        _RIVER_BRAIN_INSTANCE = RiverBrain.load()
        logging.warning(
            "[Orchestrator] RiverBrain loaded locally — EchoCore not available. "
            "Avoid running concurrent processes to prevent pkl overwrites."
        )
    return _RIVER_BRAIN_INSTANCE

# Module-level alias — resolved lazily on first access

# -------------------------------
# 11. Example Usage
# -------------------------------
if __name__ == "__main__":
    summarize_interactions(last_n=50)
    prompt = "Write a short, reflective poem about technology and nature."
    response = echo_query(prompt)
    print("Response:\n", response)
