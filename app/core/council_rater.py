"""
council_rater.py
================
Peer-model quality rating for Echo's responses.

Key properties:
- Rater model MUST differ from model_used (no same-model fallback — hard constraint)
- skipped_no_peer is a first-class counter in get_council_stats() so availability
  gaps are immediately visible rather than discovered later
- River training is never touched here; council_baseline_trusted_since must be
  set manually (see _check_and_set_trust) before any training wire-up is considered
- Cursor initializes at the end of the current interaction_log.jsonl on first run
  (no historical backfill — only new entries are rated)
- 1-in-_SAMPLE_EVERY rateable entries get sent to the rater; sampling skips are
  silent (not logged, not counted)
"""

import hashlib
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_INTERACTION_LOG = os.path.join(_PROJECT_ROOT, "memory", "interaction_log.jsonl")
_COUNCIL_LOG     = os.path.join(_PROJECT_ROOT, "memory", "council_ratings.jsonl")
_BASELINE_META   = os.path.join(_PROJECT_ROOT, "memory", "snapshot_baseline.json")
_CURSOR_PATH     = os.path.join(_PROJECT_ROOT, "memory", "council_cursor.json")

# Guards _COUNCIL_LOG against the background rating thread's plain append
# (_append_council_log) racing fill_spot_check()'s read-then-os.replace()
# rewrite — without this, a rating appended in that window was silently
# lost when the rewrite's stale snapshot overwrote the file.
_council_log_lock = threading.Lock()

_OLLAMA_URL      = "http://localhost:11434/api/generate"
_OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

# Tuning knobs — adjust without changing control flow
_SAMPLE_EVERY:              int   = 5     # Rate 1-in-N rateable entries
_SPOT_CHECK_INTERVAL:       int   = 10    # After calibration: flag every Nth rating
_CALIBRATION_WINDOW:        int   = 20    # First N ratings are all spot-checked
_TRUST_MIN_RATINGS:         int   = 50
_TRUST_MIN_SPOTCHECKS:      int   = 10
_TRUST_AGREEMENT_THRESHOLD: float = 0.70

# Pseudo-model names that appear in the log but are NOT actual LLM responses
_NON_LLM_MODELS = frozenset({"emergent_scheduler", "autonomous_fetch", "experiment_runner", "unknown", ""})

_RATING_PROMPT = """\
You are evaluating a response from an AI assistant. Score it 1–5 using these weighted criteria:

Accuracy / relevance (50%): Did it directly address what was asked?
Reasoning (30%): Is the logic sound and internally consistent?
Tone (20%): Is the style appropriate to context?

Do not reward verbosity, spiritual tone, or formatting unless the question required it.
Do not penalize brevity if the response is accurate and complete.

Prompt context: {prompt_preview}
Response: {response_preview}

Reply in exactly this format (nothing else):
SCORE: [1-5]
REASON: [one sentence]"""


# ─── Ollama helpers ───────────────────────────────────────────────────────────

def _get_available_models() -> list:
    try:
        r = requests.get(_OLLAMA_TAGS_URL, timeout=5)
        if r.ok:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []


def _select_peer_model(model_used: str) -> "str | None":
    """Return a model that differs from model_used, or None.

    Same-model fallback is intentionally absent. If this function returns None,
    the caller logs a skipped_no_peer entry. Loosening this constraint to allow
    same-model ratings must be a deliberate explicit decision, not a silent default.
    """
    models = _get_available_models()
    peers = [m for m in models if m != model_used]
    return peers[0] if peers else None


def _call_rater(prompt: str, model: str) -> str:
    """Direct Ollama HTTP generate call — bypasses echo_query() to avoid recursion."""
    try:
        r = requests.post(
            _OLLAMA_URL,
            json={
                "model":   model,
                "prompt":  prompt,
                "stream":  False,
                "options": {"num_predict": 80, "temperature": 0.2},
            },
            timeout=30,
        )
        if r.ok:
            return r.json().get("response", "").strip()
    except Exception as e:
        logger.debug("[Council] rater HTTP failed: %s", e)
    return ""


def _parse_rating(raw: str) -> "tuple[int | None, str]":
    """Extract (score, reason) from rater output. Returns (None, '') on parse failure."""
    score, reason = None, ""
    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("SCORE:"):
            try:
                val = int(line.split(":", 1)[1].strip())
                if 1 <= val <= 5:
                    score = val
            except (ValueError, IndexError):
                pass
        elif line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
    return score, reason


# ─── Cursor (tracks position in interaction_log.jsonl) ───────────────────────

def _load_cursor() -> int:
    try:
        if os.path.exists(_CURSOR_PATH):
            with open(_CURSOR_PATH, encoding="utf-8") as f:
                return int(json.load(f).get("position", 0))
    except Exception:
        pass
    return 0


def _save_cursor(pos: int) -> None:
    os.makedirs(os.path.dirname(_CURSOR_PATH), exist_ok=True)
    with open(_CURSOR_PATH, "w", encoding="utf-8") as f:
        json.dump({"position": pos, "updated_utc": datetime.now(timezone.utc).isoformat()}, f)


def _init_cursor_if_absent() -> None:
    """On first run: skip historical entries so we don't backfill 10k+ ratings."""
    if os.path.exists(_CURSOR_PATH):
        return
    pos = 0
    if os.path.exists(_INTERACTION_LOG):
        try:
            with open(_INTERACTION_LOG, encoding="utf-8") as f:
                pos = sum(1 for _ in f)
        except Exception:
            pass
    _save_cursor(pos)
    logger.info("[Council] Cursor initialized at line %d (historical entries skipped)", pos)


# ─── Council log helpers ──────────────────────────────────────────────────────

def _append_council_log(entry: dict) -> None:
    with _council_log_lock:
        os.makedirs(os.path.dirname(_COUNCIL_LOG), exist_ok=True)
        with open(_COUNCIL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _count_actual_ratings() -> int:
    """Count non-skipped entries — used to schedule spot-checks by ordinal position."""
    if not os.path.exists(_COUNCIL_LOG):
        return 0
    n = 0
    try:
        with open(_COUNCIL_LOG, encoding="utf-8") as f:
            for line in f:
                try:
                    if not json.loads(line).get("skipped"):
                        n += 1
                except Exception:
                    pass
    except Exception:
        pass
    return n


# ─── Spot-check scheduling ────────────────────────────────────────────────────

def _should_spot_check(rating_count: int, score: int, quality_score) -> bool:
    """True when this rating should be flagged for human review.

    rating_count is the 1-based ordinal of this rating among all non-skipped ratings.
    Flags: calibration window, extreme scores, large disagreement with quality_score, interval.
    """
    if rating_count <= _CALIBRATION_WINDOW:
        return True
    if score in (1, 5):
        return True
    if quality_score is not None:
        try:
            if abs(score - float(quality_score)) >= 2.0:
                return True
        except (TypeError, ValueError):
            pass
    return rating_count % _SPOT_CHECK_INTERVAL == 0


# ─── Main rating function ─────────────────────────────────────────────────────

def rate_one_entry(entry: dict) -> "dict | None":
    """Rate a single interaction log entry.

    Returns the written log dict (including skipped entries with skip_reason set),
    or None if the entry is silently ineligible (no model, no response_preview).
    """
    model_used = (entry.get("model") or entry.get("model_used") or "").strip()
    if not model_used or model_used in _NON_LLM_MODELS:
        return None

    response_preview = (entry.get("response_preview") or "").strip()
    if not response_preview:
        return None

    peer_model = _select_peer_model(model_used)
    if peer_model is None:
        skip_entry = {
            "timestamp_utc":  datetime.now(timezone.utc).isoformat(),
            "source_timestamp": entry.get("timestamp"),
            "council_rating": None,
            "skipped":        True,
            "skip_reason":    "no_peer_available",
            "model_used":     model_used,
            "task_type":      entry.get("task_type"),
        }
        _append_council_log(skip_entry)
        logger.debug("[Council] no_peer_available for model=%s", model_used)
        return skip_entry

    prompt_preview = (entry.get("prompt_preview") or entry.get("task_type") or "").strip()
    rating_prompt = _RATING_PROMPT.format(
        prompt_preview=prompt_preview[:300],
        response_preview=response_preview[:400],
    )
    prompt_hash = hashlib.sha256(rating_prompt.encode()).hexdigest()

    raw    = _call_rater(rating_prompt, peer_model)
    score, reason = _parse_rating(raw)

    if score is None:
        logger.debug("[Council] unparseable rater response for ts=%s raw=%r", entry.get("timestamp"), raw[:60])
        return None

    rating_count = _count_actual_ratings() + 1  # +1 for this entry we're about to write
    spot_check   = _should_spot_check(rating_count, score, entry.get("quality_score"))

    log_entry = {
        "timestamp_utc":               datetime.now(timezone.utc).isoformat(),
        "source_timestamp":            entry.get("timestamp"),
        "council_rating":              score,
        "council_rating_model":        peer_model,
        "council_rationale_preview":   reason[:120],
        "council_rating_prompt_hash":  prompt_hash,
        "task_type":                   entry.get("task_type"),
        "model_used":                  model_used,
        "quality_score":               entry.get("quality_score"),
        "skipped":                     False,
        "skip_reason":                 None,
        "spot_check_required":         spot_check,
        "human_spot_check_rating":     None,
    }
    _append_council_log(log_entry)
    if spot_check:
        logger.info("[Council] Rating %d flagged for spot-check (ordinal=%d score=%d)", score, rating_count, score)
    return log_entry


# ─── Stats and spot-check retrieval ──────────────────────────────────────────

def get_council_stats() -> dict:
    """Aggregate pipeline stats.

    skipped_no_peer appears as a first-class field. If this is large relative to
    total_rated, only one Ollama model is typically available and the peer-rating
    constraint is blocking most ratings — that fact should be obvious, not buried.
    """
    empty = {
        "total_rated":                    0,
        "skipped_no_peer":                0,
        "pending_spot_checks":            0,
        "spot_checks_completed":          0,
        "agreement_rate":                 None,
        "baseline_trusted":               False,
        "council_baseline_trusted_since": None,
        "gap_to_trust": {
            "ratings_needed":    _TRUST_MIN_RATINGS,
            "spotchecks_needed": _TRUST_MIN_SPOTCHECKS,
            "agreement_needed":  _TRUST_AGREEMENT_THRESHOLD,
        },
        "trust_thresholds": {
            "min_ratings":    _TRUST_MIN_RATINGS,
            "min_spotchecks": _TRUST_MIN_SPOTCHECKS,
            "min_agreement":  _TRUST_AGREEMENT_THRESHOLD,
        },
    }
    if not os.path.exists(_COUNCIL_LOG):
        return empty

    total = skipped_no_peer = spot_required = spot_done = agreements = pre_baseline_excluded = 0
    self_rating_excluded = 0

    # scorer_baseline_timestamp is written to snapshot_baseline.json when all in-flight scorer
    # changes (3a + 3b) have landed. Ratings before that timestamp were computed on a different
    # quality_score distribution and must not count toward the 50-rating trust threshold.
    scorer_baseline = _read_baseline_meta().get("scorer_baseline_timestamp")

    try:
        with open(_COUNCIL_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if e.get("skipped"):
                    if e.get("skip_reason") == "no_peer_available":
                        skipped_no_peer += 1
                    continue
                if scorer_baseline and e.get("timestamp_utc", "") < scorer_baseline:
                    pre_baseline_excluded += 1
                    continue  # pre-scorer-fix rating — excluded from trust tally
                if e.get("model_used") and e.get("model_used") == e.get("council_rating_model"):
                    self_rating_excluded += 1
                    continue  # same model rated itself — excluded per Finding M-4
                total += 1
                if e.get("spot_check_required"):
                    spot_required += 1
                    human = e.get("human_spot_check_rating")
                    if human is not None:
                        spot_done += 1
                        council = e.get("council_rating")
                        if council is not None:
                            try:
                                if abs(int(council) - int(human)) <= 1:
                                    agreements += 1
                            except (TypeError, ValueError):
                                pass
    except Exception as e:
        logger.warning("[Council] get_council_stats read error: %s", e)
        return empty

    agreement_rate = round(agreements / spot_done, 3) if spot_done else None
    pending        = spot_required - spot_done
    baseline       = _read_baseline_meta()
    trusted_since  = baseline.get("council_baseline_trusted_since")

    return {
        "total_rated":                    total,
        "pre_baseline_excluded":          pre_baseline_excluded,
        "self_rating_excluded":           self_rating_excluded,
        "skipped_no_peer":                skipped_no_peer,
        "pending_spot_checks":            pending,
        "spot_checks_completed":          spot_done,
        "agreement_rate":                 agreement_rate,
        "baseline_trusted":               bool(trusted_since),
        "council_baseline_trusted_since": trusted_since,
        "scorer_baseline_timestamp":      scorer_baseline,
        "gap_to_trust": {
            "ratings_needed":    max(0, _TRUST_MIN_RATINGS - total),
            "spotchecks_needed": max(0, _TRUST_MIN_SPOTCHECKS - spot_done),
            "agreement_needed":  (
                None if agreement_rate is None
                else round(max(0.0, _TRUST_AGREEMENT_THRESHOLD - agreement_rate), 3)
            ),
        },
        "trust_thresholds": {
            "min_ratings":    _TRUST_MIN_RATINGS,
            "min_spotchecks": _TRUST_MIN_SPOTCHECKS,
            "min_agreement":  _TRUST_AGREEMENT_THRESHOLD,
        },
    }


def get_pending_spot_checks(limit: int = 20) -> list:
    """Return unfilled spot-check entries, newest-first, up to limit."""
    if not os.path.exists(_COUNCIL_LOG):
        return []
    entries = []
    try:
        with open(_COUNCIL_LOG, encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                    if e.get("spot_check_required") and e.get("human_spot_check_rating") is None and not e.get("skipped"):
                        entries.append(e)
                except Exception:
                    pass
    except Exception:
        pass
    return list(reversed(entries))[:limit]


def fill_spot_check(source_timestamp: str, human_rating: int) -> bool:
    """Write human_spot_check_rating into the matching council_ratings.jsonl entry.

    Rewrites the file atomically via os.replace(). Returns True if the entry was
    found and updated, False otherwise.
    """
    if not os.path.exists(_COUNCIL_LOG):
        return False
    if human_rating not in range(1, 6):
        return False

    lines, found = [], False
    with _council_log_lock:
        try:
            with open(_COUNCIL_LOG, encoding="utf-8") as f:
                for raw in f:
                    try:
                        e = json.loads(raw)
                        if (
                            e.get("source_timestamp") == source_timestamp
                            and e.get("human_spot_check_rating") is None
                            and not e.get("skipped")
                        ):
                            e["human_spot_check_rating"] = human_rating
                            found = True
                        lines.append(json.dumps(e, ensure_ascii=False))
                    except Exception:
                        lines.append(raw.rstrip())
        except Exception as e:
            logger.warning("[Council] fill_spot_check read error: %s", e)
            return False

        if found:
            tmp = _COUNCIL_LOG + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            os.replace(tmp, _COUNCIL_LOG)

    if found:
        _check_and_set_trust()

    return found


# ─── Trust gating ─────────────────────────────────────────────────────────────

def is_council_trusted() -> bool:
    """True once council_baseline_trusted_since is set in snapshot_baseline.json."""
    return bool(_read_baseline_meta().get("council_baseline_trusted_since"))


def _check_and_set_trust() -> None:
    """Evaluate all three trust conditions; set council_baseline_trusted_since if they pass."""
    meta = _read_baseline_meta()
    if meta.get("council_baseline_trusted_since"):
        return
    stats = get_council_stats()
    if (
        stats["total_rated"]           >= _TRUST_MIN_RATINGS
        and stats["spot_checks_completed"] >= _TRUST_MIN_SPOTCHECKS
        and stats["agreement_rate"] is not None
        and stats["agreement_rate"]        >= _TRUST_AGREEMENT_THRESHOLD
    ):
        from app.core.snapshot_manager import patch_baseline_meta
        patch_baseline_meta(
            "council_baseline_trusted_since",
            datetime.now(timezone.utc).isoformat(),
        )
        logger.info(
            "[Council] Trust threshold reached — council_baseline_trusted_since set. "
            "total=%d spot_checks=%d agreement=%.2f",
            stats["total_rated"], stats["spot_checks_completed"], stats["agreement_rate"],
        )


def _read_baseline_meta() -> dict:
    try:
        if os.path.exists(_BASELINE_META):
            with open(_BASELINE_META, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _write_baseline_meta(meta: dict) -> None:
    os.makedirs(os.path.dirname(_BASELINE_META), exist_ok=True)
    tmp = _BASELINE_META + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    os.replace(tmp, _BASELINE_META)


# ─── Background polling loop ──────────────────────────────────────────────────

def _poll_and_rate() -> int:
    """Read new interaction_log.jsonl entries since cursor; rate 1-in-_SAMPLE_EVERY.

    Returns count of entries actually sent to the rater (excludes skipped_no_peer
    and sampling-skips).
    """
    if not os.path.exists(_INTERACTION_LOG):
        return 0

    cursor = _load_cursor()
    rated  = 0

    try:
        with open(_INTERACTION_LOG, encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = lines[cursor:]
        if not new_lines:
            return 0

        # Cursor advance moved to after the loop — previously this fired
        # before any entry in the batch was actually processed, so a
        # mid-batch failure (rate_one_entry() raising, caught below)
        # permanently skipped every remaining entry in that batch; they
        # were never retried since the cursor had already passed them.
        sample_counter = 0
        for raw in new_lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except Exception:
                continue

            # Quick eligibility check before sampling decision
            model = (entry.get("model") or entry.get("model_used") or "").strip()
            if not model or model in _NON_LLM_MODELS:
                continue
            if not entry.get("response_preview"):
                continue

            # Sampling: 1-in-_SAMPLE_EVERY rateable entries get rated
            sample_counter += 1
            if sample_counter % _SAMPLE_EVERY != 0:
                continue

            result = rate_one_entry(entry)
            if result and not result.get("skipped"):
                rated += 1

        _save_cursor(len(lines))

    except Exception as e:
        logger.warning("[Council] _poll_and_rate error: %s", e)

    return rated


def start_council_rater(poll_interval: int = 90) -> threading.Thread:
    """Start the background council rating daemon. Returns the thread.

    poll_interval=90s: checks for new entries every 90s.
    30s startup delay lets other subsystems settle first.
    """
    def loop():
        _init_cursor_if_absent()
        logger.info(
            "[Council] Background rater started (poll=%ds, sample=1-in-%d, calibration_window=%d)",
            poll_interval, _SAMPLE_EVERY, _CALIBRATION_WINDOW,
        )
        time.sleep(30)
        while True:
            try:
                n = _poll_and_rate()
                if n:
                    logger.debug("[Council] Rated %d new entries this cycle", n)
                _check_and_set_trust()
            except Exception as e:
                logger.warning("[Council] Loop error: %s", e)
            time.sleep(poll_interval)

    t = threading.Thread(target=loop, daemon=True, name="CouncilRater")
    t.start()
    return t
