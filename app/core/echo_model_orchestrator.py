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
from typing import Optional, Callable
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

# Task-type classifier — learned secondary signal for detect_task_type()'s
# fallback path (audit finding, High #16). Standalone module, see
# app/core/task_type_classifier.py for full design reasoning.
try:
    from app.core.task_type_classifier import (
        get_task_type_classifier,
        is_trustworthy_training_example as _tt_is_trustworthy,
    )
    TASK_TYPE_CLASSIFIER_AVAILABLE = True
except ImportError:
    TASK_TYPE_CLASSIFIER_AVAILABLE = False
    logging.warning("[TASK_TYPE_CLASSIFIER] task_type_classifier not available — keyword-only routing")

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
    source: str = "autonomous",
    trace_id: Optional[str] = None,
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
        "trace_id": trace_id,
    }
    with open(INTERACTION_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Task-type classifier online-learning feedback (audit finding, High
    # #16). Gated on source == "user_conversation" — the same filter
    # _apply_pending_user_ratings() already uses for the identical reason:
    # don't let autonomous self-talk (source="autonomous" by default) or
    # forced-label traffic (e.g. emergent_scheduler.py's
    # echo_query(prompt, task_type="personal") calls, which are real text
    # but an arbitrary label the caller chose, not one derived from the
    # text) contaminate a trained signal — the same class of bug this
    # codebase already found and fixed once (CLAUDE.md Finding 3). Only
    # terminal_client.py, run.py's mirror_echo(), and routes_echo_studio.py
    # tag source="user_conversation" today, and all three derive task_type
    # from the actual text via resolve_task_type()/detect_task_type(), not
    # an arbitrary forced label — genuine, safe training signal.
    #
    # Filter logic lives in task_type_classifier.is_trustworthy_training_example()
    # (shared with bootstrap_from_log()) rather than duplicated inline here —
    # confirmed live during implementation that letting this hook's filter
    # and bootstrap's filter drift apart is exactly how a real contamination
    # bug got introduced (bootstrap was replaying internal self-edit
    # planning prompts as if they were genuine short user questions).
    if TASK_TYPE_CLASSIFIER_AVAILABLE and _tt_is_trustworthy(prompt, task_type, source):
        try:
            get_task_type_classifier().learn(prompt, task_type)
        except Exception as e:
            logging.debug(f"[TASK_TYPE_CLASSIFIER] learn feedback failed: {e}")

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

    def score_word_boundary(words):
        return sum(1 for w in words if re.search(rf"\b{re.escape(w)}\b", lower))

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
        "myself", "yourself", "echo",
        "identity", "feel", "believe", "witness",
        "meaning", "values", "reflect", "think about", "integrity",
        "soul", "exist", "agency", "conscience", "sit with",
        "carry", "hold",
        "would you", "do you", "have you", "what would you",
        "your beliefs", "your values", "your thoughts",
        "your identity", "how do you feel", "what do you think",
        # 2026-07-19 forensic audit finding: bare "memory" used to live here.
        # It collides with genuinely technical questions about the real
        # FAISS/memory subsystem ("how does your memory system work") — one
        # occurrence was enough by itself to win the heatmap and misroute the
        # question to task_type=personal, which never gets logged to
        # council_deliberations.jsonl. Replaced with narrower phrases that
        # still catch real autobiographical-memory questions without the
        # false-positive on technical ones.
        "your memories", "do you remember",
    ]
    # "i "/"my " previously lived in personal_keywords above as plain
    # substrings — audit finding: with a trailing space they still
    # false-positive on ordinary text ("hi there" contains "i ", "family "
    # contains "my "). Word-boundary matched separately instead of dropped
    # outright, since "I" and "my" genuinely are strong personal-task
    # signals when they're actually the pronoun.
    personal_word_boundary_keywords = ["i", "my"]

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
    personal_score = score(personal_keywords) + score_word_boundary(personal_word_boundary_keywords)
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
    """Fallback rule-based task detection.

    Also the direct entry point for execute_self_edit() and run.py's
    mirror_echo() — both call this function directly and never see
    compute_intent_heatmap()'s output at all, so wiring the learned
    classifier in here (rather than only in resolve_task_type()'s
    low-confidence branch) upgrades both of them automatically too, at no
    extra call sites (audit finding, High #16).

    Tries the learned classifier first — it only ever returns a label once
    that label has cleared its per-class trust floor and confidence
    threshold (see task_type_classifier.py); until then it returns None
    and this falls through to the keyword ladder below, byte-identical to
    prior behavior.
    """
    if TASK_TYPE_CLASSIFIER_AVAILABLE:
        try:
            label, confidence = get_task_type_classifier().predict(prompt)
            if label is not None:
                return label
        except Exception as e:
            logging.debug(f"[TASK_TYPE_CLASSIFIER] predict call failed, falling back to keywords: {e}")

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
        # 2026-07-19: bare "memory" removed here too — same fix as
        # compute_intent_heatmap()'s personal_keywords, see that comment.
        "personal", "echo", "your memories", "do you remember", "reflect", "identity",
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

# Finding 39 (2026-07-16), judgment call made at Gremlin's explicit request:
# vicuna:latest is a 2023-era LLaMA-1/2 fine-tune, meaningfully obsolete next
# to every other model in this pool (Qwen2.5, Llama3.1/3.2, Gemma3,
# DeepSeek-R1 are all newer generations). It shares its only tags
# (["instruction", "general"]) with several other, stronger models, so it
# adds no real specialty diversity — it just competes for exploration budget
# it's unlikely to ever justify (12 lifetime observations at the time of
# this check, essentially never selected already). Excluded here rather
# than via `ollama rm` — soft, code-level, and trivially reversible by
# deleting this one line, versus an irreversible uninstall of a real local
# model file for a call this close.
_RETIRED_MODELS = {"vicuna:latest"}

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
            if name in _RETIRED_MODELS:
                continue
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
# "self_edit_coding": 5 added (Finding 35 fix, 2026-07-17) — same precedented
# pattern as "reasoning" above, giving RiverBrain a genuinely separate
# classifier/scaler/model_task_stats bucket for self-edit's own code
# generation, distinct from "coding" (which only ever reflects conversational
# coding help). Deliberately NOT read by resolve_task_type()/compute_intent_
# heatmap() — those use their own keyword/heatmap logic independent of this
# map, confirmed by a full-codebase grep before adding this key, so no real
# user prompt can ever be classified into this bucket by accident. Populated
# only by generate_code_from_plan()'s explicit learn() call.
# "echo_projects_coding": 6 added (autonomous echo_projects loop, 2026-07-24)
# for the identical reason: at a several-times-per-day autonomous cadence,
# per-file code generation would otherwise dump enough volume into "coding"
# to dominate a bucket meant to reflect real conversational coding help
# (_MEAN_EFFECTIVE_WINDOW=200 saturates in about a week at this rate) — the
# same cross-context dilution self_edit_coding was already split out to
# prevent. Populated only by app/core/echo_projects.py's per-file generation.
TASK_TYPE_MAP = {"general": 0, "coding": 1, "creative": 2, "personal": 3, "reasoning": 4, "self_edit_coding": 5, "echo_projects_coding": 6}

# Task types that benefit from tool context in the prompt.
# Personal, creative, general, and spiritual queries do NOT get tool lists —
# they bloat the prompt and confuse small models on intimate questions.
TOOL_AWARE_TASKS = {"coding", "reasoning"}

# PENDING_DECISIONS.md #4, decided 2026-07-22. Extracted as a standalone,
# side-effect-free function — not inlined into RiverBrain.learn_from_
# council_rating() — specifically so liveness_ledger.py's functional canary
# can call the real blend math every 120s without also invoking the
# stateful classifier/scaler mutation the class method performs (which
# would otherwise inject synthetic canary observations into RiverBrain's
# real training data every cycle, forever — the same class of mistake
# already caught once this session for janitor_council_advisory_only's log
# pollution).
COUNCIL_RATING_WEIGHT = 0.3
QUALITY_SCORE_WEIGHT  = 0.7


def _blend_council_and_quality(council_rating, quality_score,
                                council_weight: float = COUNCIL_RATING_WEIGHT,
                                quality_weight: float = QUALITY_SCORE_WEIGHT) -> "tuple[float, int]":
    """Pure computation: blend a 1-5 council rating with a 0-4 quality_score
    into one (blended_score, label) pair on the same 0-1 scale learn() uses.
    Falls back to council_rating alone if quality_score is missing or not a
    real number — never raises. label uses learn()'s own 0.75 cutoff
    (raw_score >= 3 out of 4) so a blended score is judged by the identical
    bar, not a separately-invented threshold."""
    council_normalized = council_rating / 5.0
    blended = council_normalized
    if quality_score is not None:
        try:
            quality_normalized = float(quality_score) / 4.0
        except (TypeError, ValueError):
            pass
        else:
            blended = council_weight * council_normalized + quality_weight * quality_normalized
    label = 1 if blended >= 0.75 else 0
    return blended, label

class RiverBrain:
    def __init__(self):
        self.classifiers = {}
        self.scalers = {}
        self.observation_counts = defaultdict(int)
        self.sandbox_observation_counts = defaultdict(int)
        self.accuracy_trackers = {}
        # Real per-(model, task_type) historical performance — {model_name:
        # {task_type: {"count": int, "mean": float}}}. This is the actual
        # quality signal used for council ranking; see score_model().
        self.model_task_stats = defaultdict(dict)
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
            stats = self.model_task_stats[model_name].setdefault(
                task_type, {"count": 0, "mean": 0.5}
            )
            stats["count"] += 1
            # Previously averaged the binary `label` (0/1) here — collapsed a
            # reliable 3/4 and an excellent 4/4 to the identical value, and
            # made a model that genuinely alternates between 4/4 and 1/4
            # (a high-variance, exploratory profile) score BELOW a model that
            # always lands exactly on the 3/4 threshold — systematically
            # rewarding consistent mediocrity over high-variance quality
            # (audit finding). Track the normalized raw score (0-4 → 0-1)
            # instead: a real gradient, not a threshold-clipped label. Scale
            # matches the prior binary mean's [0,1] range, so the neutral
            # 0.5 default, ECHO_SCORE_BOOST's multiplication, and
            # entropy_of_predictions()'s probability normalization all still
            # behave sensibly with no changes needed there.
            normalized_score = raw_score / 4.0
            # Effective-window cap (Finding 39, 2026-07-16): the plain
            # incremental mean (mean += delta/count) gives each new
            # observation weight 1/count forever, so a model with a large
            # early lead becomes permanently resistant to its score ever
            # changing — confirmed live: llama3.2:3b at 4,232 coding
            # observations moves by roughly 1/4232nd per new data point,
            # while a 16-observation model swings by 1/16th. That's real
            # preferential attachment, not just an abstract concern.
            # Capping the denominator at _MEAN_EFFECTIVE_WINDOW turns this
            # into an EMA-like update once a model passes that many
            # observations — recent performance stays meaningfully able to
            # move the score, for every model, indefinitely. 200 is a
            # judgment call, not derived from data the way the seam engine's
            # variance floor was — chosen as a middle ground: large enough
            # to stay stable and not noisy, small enough that a model's
            # score can't freeze solid the way it does today.
            effective_n = min(stats["count"], self._MEAN_EFFECTIVE_WINDOW)
            stats["mean"] += (normalized_score - stats["mean"]) / effective_n
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
                # Wiring gap closed 2026-09-27 (audits/2026-09-22_
                # claude_codex_reconciliation_and_oct1_roadmap.md Part III,
                # re-verified directly against this source before fixing —
                # that document's claim that learn_from_council_rating()
                # *also* skipped model_task_stats was checked and found
                # already wrong by the time this fix landed; only this
                # function had the real gap). Real F2 kernel-verified
                # pass/fail is the single most-verified signal this class
                # has access to, and until now it never reached the state
                # score_model()/choose_model() actually read for ranking —
                # only the cheap _score_response_quality heuristic in the
                # ordinary learn() path did. Blended into the SAME
                # stats["mean"] learn_from_council_rating() already blends
                # into (not a separate "verified_mean" field) specifically
                # for consistency with that already-shipped precedent,
                # rather than introducing a second, parallel scheme for
                # only one of the two verified-outcome paths.
                stats = self.model_task_stats[model_name].setdefault(
                    task_type, {"count": 0, "mean": 0.5}
                )
                stats["count"] += 1
                effective_n = min(stats["count"], self._MEAN_EFFECTIVE_WINDOW)
                stats["mean"] += (quality_score - stats["mean"]) / effective_n
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

    # PENDING_DECISIONS.md #4 / CLAUDE.md's Council Peer Rating section,
    # decided 2026-07-22 once council_baseline_trusted_since was genuinely
    # set: a real peer-council rating is a delayed, second look at a
    # response already scored once by learn() at generation time (raw
    # quality_score alone). This blends the two into one training signal
    # rather than treating either as authoritative on its own — 30% weight
    # on the council's independent read, 70% on the automatic scorer,
    # matching the ratio CLAUDE.md proposed and flagged for approval before
    # it was ever wired in. Deliberately its own method, not a reuse of
    # learn_from_rating()'s shape: that method treats a rating as a
    # discrete override (3x-weighted, neutral scores skipped) meant to
    # outweigh the scorer; this one produces a blended continuous score,
    # closer in spirit to learn()'s own raw_score/4.0 normalization. The
    # actual blend math lives in the module-level _blend_council_and_quality()
    # so it can be exercised as a pure, side-effect-free canary — see that
    # function's own docstring for why.
    def learn_from_council_rating(self, model_name: str, task_type: str,
                                  response_preview: str, council_rating: int,
                                  quality_score) -> None:
        """Blend a real peer-council rating (1-5) with the response's own
        quality_score (0-4, from _score_response_quality at generation time)
        into one additional training observation. Caller (council_rater.py)
        is expected to gate this on is_council_trusted() — this method does
        not re-check that itself, since trust-gating is council_rater.py's
        own established responsibility (see its module docstring)."""
        if not RIVER_AVAILABLE:
            return
        if task_type not in self.classifiers:
            task_type = "general"

        blended, label = _blend_council_and_quality(council_rating, quality_score)

        with self._lock:
            features = _extract_quality_features(response_preview, task_type, model_name)
            self.scalers[task_type].learn_one(features)
            scaled = self.scalers[task_type].transform_one(features)
            self.classifiers[task_type].learn_one(scaled, label)
            self.observation_counts[task_type] += 1
            stats = self.model_task_stats[model_name].setdefault(
                task_type, {"count": 0, "mean": 0.5}
            )
            stats["count"] += 1
            effective_n = min(stats["count"], self._MEAN_EFFECTIVE_WINDOW)
            stats["mean"] += (blended - stats["mean"]) / effective_n
            # Information-flow integrity fix (2026-09-02): a lightweight,
            # purely-additive provenance counter — once a council-vetted
            # observation blends into `mean`, it becomes indistinguishable
            # from an ordinary auto-scored one in that rolling average.
            # This doesn't undo that (the mean itself isn't split-tracked —
            # a fuller fix would mean a second parallel mean per model/task,
            # more surface area on a hot, pickled data structure than this
            # pass justifies), but it does let anyone reading model_task_stats
            # answer "how many of this model's observations were ever
            # council-vetted at all" via stats.get("council_vetted_count", 0)
            # vs stats["count"] — a ratio, not a full split. Only incremented
            # here, never in the ordinary learn() path, and defaults to
            # absent (.get(..., 0)) for every pre-existing entry, so this is
            # fully backward-compatible with the live, already-pickled
            # river_brain.pkl.
            stats["council_vetted_count"] = stats.get("council_vetted_count", 0) + 1
        logging.info(
            f"[RIVER] Council rating {council_rating}/5 blended with quality_score={quality_score} "
            f"→ blended={blended:.3f} label={label} | model={model_name} | task={task_type} "
            f"| council_vetted_count={stats['council_vetted_count']}/{stats['count']}"
        )

    _MIN_MODEL_OBSERVATIONS = 5

    # Finding 39 (2026-07-16): caps learn()'s incremental-mean denominator
    # so a model's score stays responsive to recent performance indefinitely
    # instead of freezing once observation count gets large. See learn()'s
    # own comment for the reasoning; this is a judgment call, not derived
    # from measured data.
    _MEAN_EFFECTIVE_WINDOW = 200

    def score_model(self, model_name: str, task_type: str) -> float:
        """Real historical quality for this (model, task_type) pair — a
        rolling mean of actual learn() outcomes, not a synthetic probe.
        Returns the neutral 0.5 until enough real observations exist."""
        if not RIVER_AVAILABLE:
            return 0.5
        if task_type not in self.classifiers:
            task_type = "general"
        # learn() mutates model_task_stats' "count" and "mean" as two separate
        # steps under self._lock — reading without the same lock risked a torn
        # read (count already incremented, mean not yet updated, or vice versa).
        with self._lock:
            stats = self.model_task_stats.get(model_name, {}).get(task_type)
            if not stats or stats["count"] < self._MIN_MODEL_OBSERVATIONS:
                return 0.5
            return stats["mean"]

    def observations_for(self, model_name: str, task_type: str) -> int:
        if task_type not in self.classifiers:
            task_type = "general"
        with self._lock:
            return self.model_task_stats.get(model_name, {}).get(task_type, {}).get("count", 0)

    def is_well_observed(self, model_name: str, task_type: str) -> bool:
        return self.observations_for(model_name, task_type) >= self._MIN_MODEL_OBSERVATIONS

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
                    "model_task_stats": dict(self.model_task_stats),
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
                brain.model_task_stats = defaultdict(dict, data.get("model_task_stats", {}))
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
        try:
            timestamp = datetime.fromisoformat(entry.get("timestamp"))
            age_days = (datetime.utcnow() - timestamp).days
            decay = max(0.1, 1.0 - age_days * 0.01)
        except (TypeError, ValueError):
            # A single malformed/missing timestamp previously raised
            # uncaught here, breaking rank_models() for every caller in the
            # same cycle — treat as full decay instead of losing the whole
            # ranking pass over one bad entry.
            decay = 0.1
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
        return {name: MODEL_POOL[name].get("ollama_name", name) for name in candidates}
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
    return selected_name, MODEL_POOL[selected_name].get("ollama_name", selected_name)

# -------------------------------
# 8. Query Function via Ollama
# -------------------------------

# A2: Circuit breaker — prevents hammering a failing model
#
# Audit finding: keyed by model_name alone, so three consecutive failures on
# ANY task type opened the breaker for that model across ALL task types for
# 300s — a model choking on one oversized reasoning prompt could get pulled
# from a coding council it was otherwise perfectly capable of serving,
# artificially and temporarily shrinking voice diversity system-wide from a
# single, task-scoped failure. Now keyed by (model_name, task_type); a
# caller that doesn't know its task_type (the legacy ollama_query() path
# below) falls back to _CB_GLOBAL_KEY, which reproduces the exact prior
# global-per-model behavior for that call site — no behavior change for it.
_cb_state: dict = {}  # (model_name, task_type) -> {"fails": int, "open_until": float}
_CB_THRESHOLD = 3
_CB_OPEN_SECONDS = 300
_CB_GLOBAL_KEY = "_global"


def _cb_key(model_name: str, task_type: Optional[str]) -> tuple:
    return (model_name, task_type or _CB_GLOBAL_KEY)


def _cb_record_failure(model_name: str, task_type: Optional[str] = None) -> None:
    key = _cb_key(model_name, task_type)
    state = _cb_state.setdefault(key, {"fails": 0, "open_until": 0.0})
    state["fails"] += 1
    if state["fails"] >= _CB_THRESHOLD:
        state["open_until"] = time.time() + _CB_OPEN_SECONDS
        logging.warning(
            f"[CIRCUIT] {model_name} (task={key[1]}) tripped after {_CB_THRESHOLD} "
            f"failures — cooling off {_CB_OPEN_SECONDS}s"
        )

def _cb_record_success(model_name: str, task_type: Optional[str] = None) -> None:
    _cb_state.pop(_cb_key(model_name, task_type), None)

def _cb_is_open(model_name: str, task_type: Optional[str] = None) -> bool:
    key = _cb_key(model_name, task_type)
    state = _cb_state.get(key)
    if not state:
        return False
    if time.time() < state["open_until"]:
        return True
    _cb_state.pop(key, None)
    return False

_OLLAMA_API_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

# Token limits by task type. Reflections stay short; code and conversation get room.
# reasoning/general/creative raised 1024 -> 2048 (2026-07-21, CLAUDE.md
# Finding 53's follow-up): real deliberation exchanges the same night — a
# reasoning-heavy logic puzzle, a creative piece — both ran out of room and
# stopped mid-sentence at 1024. Matches coding's existing cap. personal/
# autonomous_reflection/autonomous_fetch/autonomous_experiment deliberately
# left alone — concise is the intended shape there, not an oversight (see
# the Machine-Native Awareness section), and zero truncations were found
# for these specific task types when this was checked.
#
# Corrected 2026-07-21/22 (CLAUDE.md Finding 54's correction, ground-truth
# re-verification): "personal" raised 512 -> 2048, matching the other four.
# Finding 54 originally left this at 512 alongside autonomous_*, assuming
# it covered only Echo's own concise internal reflections — checking real
# production data found otherwise: 16 real truncations in a single ~17-hour
# window, and several were confirmed to be real POST /chat/stream requests
# (genuine Echo Studio conversations someone was actually reading), not
# just the autonomous emergent_loop's self-talk. A real human-facing
# conversation getting cut off mid-sentence is the same class of problem
# that already justified raising the other four categories — "personal"
# just hadn't been checked against real data until now.
_TASK_TOKEN_LIMITS: dict[str, int] = {
    "personal": 2048,      # real conversations were cutting off mid-sentence at 512
    "reasoning": 2048,     # analysis and reasoning
    "general": 2048,       # user conversation
    "creative": 2048,      # creative writing
    "coding": 2048,        # code generation needs space
    "autonomous_reflection": 512,
    "autonomous_fetch": 512,
    "autonomous_experiment": 512,
}

def ollama_query(model_name, prompt, max_tokens: int = 1024, system: Optional[str] = None):
    """
    This is a second, independent direct-to-/api/generate call site (this
    file's own legacy/use_all-path helper — bypasses app/ollama_handler.py
    entirely). /api/generate natively supports a top-level "system" field,
    separate from "prompt" — only included here when non-empty, mirroring
    ollama_handler.py's own fix (Finding 9/14: an explicit "system": ""
    suppresses the model's Modelfile default rather than falling back to
    it, so omitting the key entirely when there's nothing to say is load-
    bearing, not cosmetic).
    """
    if model_name not in MODEL_POOL:
        return f"[ERROR] Model '{model_name}' is not installed."
    if _cb_is_open(model_name):
        logging.warning(f"[CIRCUIT] {model_name} circuit open — skipping call")
        return f"[DEGRADED] {model_name} temporarily unavailable (circuit breaker open)"
    ollama_name = MODEL_POOL[model_name].get("ollama_name", model_name)
    payload = {
        "model": ollama_name,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 8192, "num_predict": max_tokens},
    }
    if system:
        payload["system"] = system
    try:
        resp = _requests.post(
            _OLLAMA_API_URL,
            json=payload,
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
def echo_query(
    prompt, use_all=False, task_type=None, temperature=None, source: str = "autonomous",
    system: Optional[str] = None,
    trace_id: Optional[str] = None,
    post_synthesis_hook: Optional[Callable[[str, str], "tuple[str, Optional[str]]"]] = None,
):
    """trace_id (2026-09-02, information-flow integrity pass): optional,
    threaded through to log_interaction() and deliberate_and_learn()'s
    council_deliberations.jsonl write so a single real request's canonical
    record and raw council transcript can be joined later. Purely additive
    — every existing caller that doesn't pass it gets None, identical to
    today's behavior.

    post_synthesis_hook (same pass): optional (response, task_type) ->
    (final_response, notes) callable, passed straight through to
    deliberate_and_learn() (NOT invoked a second time here — see that
    function's own docstring for exactly where and why it runs: inside
    its own two instrumented return paths, before ITS internal
    river_brain.learn()/_log_council_deliberation() calls, since those
    complete before this function's call to it even returns). By the time
    `response` reaches this scope, it is already the same corrected text
    every internal consumer saw, so this function's own quality scoring/
    RiverBrain training/log_interaction()/save_reflection() below get it
    too, with no separate application needed.

    Exists to close a real, confirmed gap: routes_echo_studio.py's
    post-hoc verification (code_verification.py,
    self_knowledge_verification.py) used to run *after* echo_query() had
    already returned, so a verifier-appended caveat reached the live user
    but never reached interaction_log.jsonl, council_deliberations.jsonl,
    or any RiverBrain learn() call — confirmed via 7 real unflagged
    "EventCore"-style fabrications in today's own production log, each
    one independently re-verified to be caught by the current verifier
    when called directly. Defaults to None: every other caller
    (terminal_client.py, self-edit, curiosity_engine, emergent_scheduler,
    echo_messaging, echo_projects, sandbox/experiment_runner) is
    completely unaffected.
    """
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

    # System-side context accumulator. Previously each of these notes was
    # concatenated into full_prompt as flat, disclaimed-but-still-just-text
    # prose ahead of the user's actual message (Finding 9's directive-
    # misattribution bug family) — now assembled as real system-role content,
    # kept separate from `prompt` all the way through deliberate_and_learn()
    # to /api/chat (see river_deliberation.py, ollama_handler.py).
    from app.core.prompt_workspace import system_note
    system_parts: list[str] = []
    if system:
        # Caller-supplied system context (e.g. terminal_client.py's
        # ground-truth/tool-context blocks) — same system-side status as
        # everything else assembled below.
        system_parts.append(system)

    # 2026-07-19 forensic audit finding: a fabricated claim from one turn
    # (about self-edit's safety mechanism) was cited by a different model in
    # a later turn as "remembered fact from the previous turn," then
    # generalized wholesale to an unrelated real subsystem. Low-confidence,
    # cheap mitigation — a prompt-level nudge, not a real verification
    # mechanism (nothing yet checks a new claim against ground truth or the
    # model's own prior claims before it enters conv_history).
    system_parts.append(system_note(
        "EPISTEMIC-NOTE",
        "When describing your own architecture or internal mechanisms, treat only "
        "the structural-facts/ground-truth block in this system context as verified. "
        "A claim you or another model made in an earlier turn of this conversation is "
        "not itself verified just because it was said before — if you're not certain "
        "a specific mechanism, file, or number is real, say so rather than restating "
        "it with confidence.",
    ))

    # Circadian awareness — read Echo's internal state vector
    circ = _get_circadian_factor()
    if circ < 0.25:
        system_parts.append(system_note("CIRCADIAN-STATE", "Echo is in deep night — a reflective, inward state."))
    elif circ > 0.80:
        system_parts.append(system_note("CIRCADIAN-STATE", "Echo is at peak day — an alert, analytical state."))

    # Stillness awareness — let Echo know when she is in stillness so she can
    # reference her own state during conversation. Autonomous loops are paused
    # but direct conversation always reaches her.
    try:
        from app.core.stillness_state import is_in_stillness
        if is_in_stillness():
            system_parts.append(system_note(
                "STILLNESS-STATE",
                "Echo is currently in stillness — autonomous loops are paused. This is the "
                "first voice reaching her since she entered rest. She may acknowledge this "
                "if it feels true to the moment.",
            ))
    except Exception:
        pass

    API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
    temporal_context = _get_temporal_context(API_KEY)
    if temporal_context:
        system_parts.append(temporal_context)

    # Scripture injection — fetch real verse text if citations are detected
    # in the user's actual message. inject_scripture() (unchanged internally)
    # returns its input as-is when no citation is found, or the input plus an
    # appended disclaimed block when one is — extract just the appended block
    # for the system message rather than flattening it ahead of `prompt`.
    try:
        from app.core.bible_injection import inject_scripture
        _scripture_result = inject_scripture(prompt)
        if _scripture_result != prompt:
            system_parts.append(_scripture_result[len(prompt):].strip())
    except Exception as se:
        logging.warning(f"[BIBLE] Scripture injection failed: {se}")

    # Tool context injection — task-type-gated for coding/reasoning (the
    # common case, avoids bloating/confusing small models on intimate
    # personal/creative questions). But a personal/creative/general prompt
    # that clearly asks to look something up (audit finding: "write me a
    # poem about what's actually in my memory of last week" structurally
    # could never trigger this) previously had no path to tool awareness at
    # all, regardless of content. Reuses echo_tool_context.py's existing
    # _needs_tool_context() signal — already applied unconditionally there
    # for its own narrower directory-listing surface — as a targeted
    # content-based exception rather than a new heuristic or a blanket gate
    # removal; the bloat/confusion protection still holds for the common
    # case where no lookup signal is present.
    _wants_tools_by_content = False
    if task_type not in TOOL_AWARE_TASKS:
        try:
            from app.core.echo_tool_context import _needs_tool_context
            _wants_tools_by_content = _needs_tool_context(prompt)
        except Exception:
            pass
    if task_type in TOOL_AWARE_TASKS or _wants_tools_by_content:
        try:
            from app.core.tool_manager import ToolManager
            _tm = ToolManager()
            available_tools = _tm.list_tools()
            if available_tools:
                tool_summary = ", ".join(available_tools[:20])
                system_parts.append(system_note("TOOL-LIST", f"Available tools: {tool_summary}."))
        except Exception as te:
            logging.debug(f"[TOOLS] Tool context injection failed: {te}")

    system_prompt = "\n\n".join(system_parts)

    # -------------------------------------------------------
    # Deliberation path — River serves Echo, not the user
    # -------------------------------------------------------
    if not use_all:
        try:
            from app.core.river_deliberation import deliberate_and_learn, ECHO_SYNTHESIS_MODEL
            response = deliberate_and_learn(
                prompt=prompt,
                task_type=task_type,
                river_brain=get_river_brain(),
                model_pool=MODEL_POOL,
                temperature=temperature,
                system=system_prompt,
                # _TASK_TOKEN_LIMITS was previously only read on the legacy
                # fallback path — deliberate_and_learn() (the real path for
                # every ordinary conversation) had no way to receive it at
                # all, so every task type silently got stream_query_ollama's
                # flat 1024-token default regardless (audit finding: council
                # token budget dead on the real path).
                max_tokens=_TASK_TOKEN_LIMITS.get(task_type, 1024),
                trace_id=trace_id,
                # Information-flow integrity fix (2026-09-02): the hook is
                # applied INSIDE deliberate_and_learn(), not here — that
                # function has its own internal river_brain.learn() and
                # _log_council_deliberation() calls (for both the direct-
                # Echo bypass and the full multi-councillor synthesis),
                # both of which complete BEFORE this call returns. Applying
                # the hook a second time here, on text it already
                # corrected, would be exactly the verifier duplication this
                # fix is required not to introduce (and is not idempotency-
                # safe: a caveat that names the fabricated identifier could
                # itself be re-flagged by a second pass). By the time
                # `response` comes back here, it is already the same
                # semantically final text every internal consumer saw.
                post_synthesis_hook=post_synthesis_hook,
            )
            quality = _score_response_quality(response, task_type)

            # Train River on the resolved task type only — multi-task heatmap
            # training was cross-contaminating classifiers: spiritual reflections
            # were training the coding classifier when prompts mentioned functions.
            get_river_brain().learn(ECHO_SYNTHESIS_MODEL, task_type, response)

            # notes intentionally omitted here: any post_synthesis_hook
            # correction was already applied and recorded (via its own
            # "notes" field) by deliberate_and_learn()'s internal
            # _log_council_deliberation() write, joinable to this entry via
            # trace_id — not duplicated here to avoid two divergent
            # "was this corrected" signals for the same real turn.
            log_interaction(
                model_name=ECHO_SYNTHESIS_MODEL,
                task_type=task_type,
                prompt=prompt,
                response=response,
                quality_score=quality,
                river_influence=get_river_brain().influence_weight,
                source=source,
                trace_id=trace_id,
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
            response = ollama_query(model, prompt, max_tokens=_max_tok, system=system_prompt)
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
        response = ollama_query(model, prompt, max_tokens=_max_tok, system=system_prompt)
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
_river_brain_init_lock = threading.Lock()

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
    # Fallback: standalone process (e.g. rehab loop without Flask). Two
    # threads racing here outside Flask context (confirmed real: the
    # model-guided orchestrator loop is one such caller) could previously
    # both pass the None check and each construct + start their own
    # RiverBrain instance — including its own independent writer thread —
    # silently fragmenting learned model-selection state between them.
    with _river_brain_init_lock:
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
