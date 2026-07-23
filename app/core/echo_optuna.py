import optuna
import json
import logging
import os
import random
from typing import Any, Dict, Optional, Tuple, List

from app.core import self_edit_manager
from app.core.memory_bridge import retrieve_relevant_memories

logger = logging.getLogger(__name__)


# Gap-closure plan Phase C2b (2026-07-23): valence as a bounded modulator
# of which region of [0,1] Optuna's intensity/creativity dry-run trials
# explore -- strictly scoped to trial sampling, never touches F1/F2/F3 or
# the real deployment quality-gate (Finding 19's fitness comparison stays
# completely untouched; this only shifts where a *candidate* comes from).
_VALENCE_OPTUNA_SLACK = 0.2  # fraction of [0,1] reserved as shiftable headroom
_VALENCE_OPTUNA_SHIFT_RANGE = _VALENCE_OPTUNA_SLACK / 2


def _valence_adjusted_bounds(valence: float) -> Tuple[float, float]:
    """Pure, testable: returns (low, high) for Optuna's suggest_float calls.
    Keeps (1 - _VALENCE_OPTUNA_SLACK) of [0,1] as the window width, shifting
    that window's center based on valence -- positive valence shifts up
    (more room for higher/more exploratory values), negative valence shifts
    down (more conservative). Deliberately doesn't narrow the search space
    drastically: at valence=0 the window is [0.1, 0.9], still covering the
    vast majority of the original full range."""
    width = 1.0 - _VALENCE_OPTUNA_SLACK
    center = 0.5 + valence * _VALENCE_OPTUNA_SHIFT_RANGE
    low = max(0.0, min(1.0 - width, center - width / 2))
    high = low + width
    return low, high


class EchoOptuna:
    """
    Handles autonomous self-edit optimization for Echo using Optuna.
    Samples prompts from vector memory (via retrieve_relevant_memories) so
    trials operate on real content instead of a dummy prompt.
    """

    def __init__(self, memory_query: str = "self-edit", top_k_prompts: int = 5):
        self.memory_query = memory_query
        self.top_k_prompts = top_k_prompts
        self.logger = logger

    def _sample_prompt(self) -> str:
        """
        Sample a prompt from stored memories. If none are available,
        return a sensible default prompt.
        """
        try:
            # Exclude autonomous (news feed) entries — they produce irrelevant trial prompts
            # and exhibit the same source-as-identity confabulation as Finding 14.
            mems = [
                m for m in retrieve_relevant_memories(self.memory_query, top_k=self.top_k_prompts * 3)
                if m.get("meta", {}).get("memory_source") != "autonomous"
            ][:self.top_k_prompts]
            if mems:
                # Prefer selecting a single memory (keeps prompts focused).
                choice = random.choice(mems)
                if isinstance(choice, dict):
                    text = choice.get("text") or str(choice)
                    if text and text.strip():
                        return text.strip()
                # fallback: join a few memory texts
                texts: List[str] = [m.get("text", "") if isinstance(m, dict) else str(m) for m in mems]
                joined = " ".join([t for t in texts if t])[:2000]  # cap size
                if joined.strip():
                    return joined.strip()
        except Exception as e:
            self.logger.warning(f"[EchoOptuna] failed to sample prompt from memories: {e}")
        # Final fallback
        return ("Echo self-edit diagnostic: refine clarity, tone, and usefulness. "
                "Make an edit that improves concision, coherence, and helpfulness.")

    def _score_code_structure(self, code_path: str) -> float:
        """
        Structural quality of the generated code via radon.
        Returns 0.0 (clean) – 0.5 (poor).  Always < 1.0 so any
        successful trial still beats any failed one in Optuna's view.

        Combines Maintainability Index (weight 0.7) and average cyclomatic
        complexity (weight 0.3).  Falls back to 0.0 on any radon error so
        the absence of radon never penalises a successful trial.
        """
        try:
            with open(code_path, "r", encoding="utf-8") as f:
                code = f.read()
            from radon.complexity import cc_visit
            from radon.metrics import mi_visit
            blocks = cc_visit(code)
            avg_cc = (
                sum(b.complexity for b in blocks) / len(blocks) if blocks else 1.0
            )
            mi = float(mi_visit(code, multi=True))  # 0–100, higher = better
            mi_penalty = (1.0 - min(mi / 100.0, 1.0)) * 0.5    # MI=100 → 0.0
            cc_penalty = min(avg_cc / 10.0, 1.0) * 0.5          # avg_cc=1 → 0.05
            score = round(mi_penalty * 0.7 + cc_penalty * 0.3, 4)
            self.logger.debug(
                "[EchoOptuna] radon | MI=%.1f avg_cc=%.1f → structural_score=%.4f",
                mi, avg_cc, score,
            )
            return score
        except Exception as e:
            self.logger.debug("[EchoOptuna] radon scoring skipped: %s", e)
            return 0.0

    def _score_result(self, result: Any, prompt: str, task_type: str = "coding") -> float:
        """
        Convert a self-edit result into a minimization score for Optuna.
        Lower = better. Returns inf for hard failures.

        Scoring rules:
        - (True, _) tuple → echo_quality_scorer's coding-quality signal 0.0–1.0
          (sandbox passed), radon structural score as a fallback only
        - (False, _) tuple → 1.0 (sandbox failed; still informative for Optuna)
        - string → quality scorer (0–4 int) normalized to 0.0–1.0 (inverted)
        - dict with explicit metrics → 1 - avg(metrics)
        - None or unrecognised → inf
        """
        try:
            if result is None:
                return float("inf")

            # (success, detail) tuple from execute_self_edit / perform_self_edit
            if isinstance(result, tuple) and len(result) == 2:
                success, detail = result
                if not success:
                    return 1.0
                # Score the actual candidate this trial produced. dry_run=True
                # calls return the staged candidate's path in `detail`; fall
                # back to the production file only for non-dry-run callers
                # (or older/other callers still returning "Success" as detail) —
                # previously this always scored production regardless of which
                # candidate was being evaluated, so every dry-run trial was
                # scoring whatever happened to already be deployed, not itself.
                code_path = (
                    detail if isinstance(detail, str) and os.path.isfile(detail)
                    else self_edit_manager.SELF_EDIT_FILE
                )
                # EMERGENCE_ROADMAP.md System 3: Optuna's objective was designed to
                # use the real quality signal RiverBrain trains on elsewhere in this
                # codebase (echo_quality_scorer._score_response_quality), not a
                # disconnected radon-only structural heuristic. task_type is always
                # "coding" here regardless of which skill Optuna's trial is targeting
                # (target_task_type) — self-edit always generates Python code, and
                # _score_response_quality's non-coding branches (substance/
                # confabulation/scripture-integrity) would be nonsensical applied to
                # a raw Python file. radon remains a fallback only, for when the
                # quality scorer itself errors — never the primary signal.
                try:
                    with open(code_path, "r", encoding="utf-8") as f:
                        code_text = f.read()
                    from echo_quality_scorer import _score_response_quality
                    quality = _score_response_quality(code_text, task_type="coding")  # 0-4 int

                    # Emergence roadmap Phase 7.1 — observational-only
                    # predicted-vs-actual quality stream for dry-run trials,
                    # which previously generated zero convergence/outcome
                    # signal at all (Optuna runs ~10 trials/hour here vs the
                    # <=1 real deploy/hour _record_convergence() and
                    # self_edit_outcome_tracker actually see). Mirrors
                    # world_model.surprise's own Phase 2a-before-2b
                    # progression: log first, before any decision ever
                    # reads it. Does NOT affect trial selection, cooldown,
                    # or deployment in any way — best-effort, and any
                    # failure here must never affect the real Optuna score
                    # returned below.
                    try:
                        with open(self_edit_manager.SELF_EDIT_FILE, "r", encoding="utf-8") as f:
                            current_code_text = f.read()
                        current_quality = (
                            _score_response_quality(current_code_text, task_type="coding")
                            if current_code_text.strip() else -1
                        )
                        from app.core.echo_core import get_echo_core
                        core = get_echo_core()
                        if core:
                            core.publish_salience(
                                source="echo_optuna",
                                kind="self_edit.dry_run_quality_delta",
                                summary=f"trial_quality={quality} current_quality={current_quality}",
                                detail={"trial_quality": quality, "current_quality": current_quality},
                            )
                    except Exception:
                        pass

                    # Gap-closure plan Phase C2c (2026-07-23): this real
                    # trial-vs-production quality comparison fires ~10x/hour
                    # (Optuna's dry-run search), far more often than the
                    # <=1 real deploy/hour self_edit_outcome_tracker actually
                    # observes -- previously RiverBrain's self_edit_coding
                    # bucket only learned from generate_code_from_plan()'s
                    # own once-per-generation call (Finding 35), not from
                    # this specific, independently-scored dry-run candidate.
                    # Correctly model-attributed via the staging_path lookup
                    # added to reflection_entry the same session -- never
                    # guesses at which model produced this code (a wrong
                    # attribution here would be a real training-signal
                    # contamination bug, the same class Finding 3 already
                    # found and fixed once for a different mechanism).
                    try:
                        model_used = None
                        with open("memory/reflection_shard.jsonl", "r", encoding="utf-8") as f:
                            for line in f.readlines()[-100:]:
                                try:
                                    entry = json.loads(line)
                                except Exception:
                                    continue
                                if entry.get("staging_path") == code_path:
                                    model_used = entry.get("model_used")
                        if model_used:
                            from app.core.echo_model_orchestrator import get_river_brain
                            get_river_brain().learn(model_used, "self_edit_coding", code_text)
                    except Exception as _river_err:
                        self.logger.debug(f"[EchoOptuna] Direct dry-run RiverBrain feed skipped: {_river_err}")

                    return max(0.0, 1.0 - (quality / 4.0))
                except Exception as e:
                    self.logger.debug(f"[EchoOptuna] quality-scorer failed, falling back to radon: {e}")
                    return self._score_code_structure(code_path)

            # String response — use quality scorer
            if isinstance(result, str):
                r = result.strip()
                if not r or r == prompt.strip():
                    return float("inf")
                try:
                    from echo_quality_scorer import _score_response_quality
                    raw = _score_response_quality(r, task_type)  # 0–4 int
                    # Invert and normalize: quality=4 → score=0.0, quality=0 → score=1.0
                    return max(0.0, 1.0 - (float(raw) / 4.0))
                except Exception:
                    # Fallback to a modest constant rather than optimistic 0
                    return 0.5

            # Dict with explicit numeric metrics
            if isinstance(result, dict):
                numeric_metrics = []
                for k in ("quality", "score", "coherence", "usefulness", "evaluation"):
                    v = result.get(k)
                    if isinstance(v, (int, float)):
                        numeric_metrics.append(float(v))
                    if isinstance(v, dict):
                        for vv in v.values():
                            if isinstance(vv, (int, float)):
                                numeric_metrics.append(float(vv))
                if numeric_metrics:
                    avg = sum(numeric_metrics) / len(numeric_metrics)
                    return max(0.0, 1.0 - avg)
                text = result.get("text") or result.get("edited") or result.get("output")
                if isinstance(text, str) and text.strip():
                    return self._score_result(text.strip(), prompt, task_type)
                return float("inf")

            return float("inf")

        except Exception as e:
            self.logger.warning(f"[EchoOptuna] scoring failed: {e}")
            return float("inf")

    def evaluate_params(self, params: Dict[str, float]) -> float:
        """
        Evaluate given params on a sampled prompt (dry run) and return the heuristic score.
        Useful for baseline comparisons.
        """
        prompt = self._sample_prompt()
        try:
            result = self_edit_manager.execute_self_edit(
                intensity=params.get("intensity", 0.5),
                creativity=params.get("creativity", 0.5),
                prompt=prompt,
                dry_run=True
            )
            return self._score_result(result, prompt)
        except Exception as e:
            self.logger.warning(f"[EchoOptuna] evaluate_params failed: {e}")
            return float("inf")

    def optimize_self_edit(
        self, n_trials: int = 10, param_hints: Optional[Dict[str, float]] = None
    ) -> Tuple[Dict[str, float], float]:
        """
        Run Optuna to find the best self-edit parameters.
        Each trial samples a prompt from memory and runs a dry self-edit.
        Returns (best_params, best_value). Lower best_value is better.

        System 3: reads the weak task type from the living self-model so
        every trial targets the area where Echo's performance is poorest.

        param_hints: optional model-suggested starting values for
        "intensity"/"creativity" (0.0-1.0). Previously accepted by callers
        but silently unimplemented here, causing a TypeError on every call
        (272 occurrences since 2026-07-02) — the hint-generation LLM call
        ran every cycle for no effect. Valid hints are queued as the first
        trial via study.enqueue_trial(); the rest of n_trials proceeds with
        Optuna's normal search, same as before. Anything not a valid float
        in [0, 1] for these two keys is ignored rather than trusted blindly.
        """
        target_task_type = "coding"
        try:
            from app.core.self_model_updater import SelfModelUpdater
            target_task_type = SelfModelUpdater().get_weak_task_type()
            self.logger.info(f"[EchoOptuna] Targeting weak task type: {target_task_type}")
        except Exception as e:
            self.logger.warning(f"[EchoOptuna] Could not read self-model target: {e}")

        def objective(trial: optuna.trial.Trial) -> float:
            # Gap-closure plan Phase C2b: real valence, bounded modulation
            # of the sampling window only (see _valence_adjusted_bounds()).
            # Fails closed to the neutral valence=0.0 window if echo_state
            # is unavailable, same posture as every other valence read
            # added this session.
            valence = 0.0
            try:
                from app.core import echo_state
                vec = echo_state.load()
                if vec is not None and len(vec) > 8:
                    valence = float(vec[8])
            except Exception:
                pass
            intensity_low, intensity_high = _valence_adjusted_bounds(valence)
            creativity_low, creativity_high = _valence_adjusted_bounds(valence)
            intensity = trial.suggest_float("intensity", intensity_low, intensity_high)
            creativity = trial.suggest_float("creativity", creativity_low, creativity_high)

            try:
                # dry_run=True: every trial runs the real plan/codegen/sandbox/
                # staging pipeline and gets scored on its own merits, but never
                # writes to production and never stamps/consumes the 60-minute
                # cooldown. Previously this was dry_run=False (unset, defaulted
                # to None/False) on every trial, so whichever trial got through
                # first stamped the cooldown for the whole hour and the other 9
                # (plus run.py's own "apply best params" call afterward) always
                # short-circuited on "Cooldown active" — Optuna's search never
                # actually got to compare trials, and its winning params were
                # silently discarded.
                result = self_edit_manager.perform_self_edit(
                    intensity=intensity,
                    creativity=creativity,
                    target_task_type=target_task_type,
                    dry_run=True,
                )
                score = self._score_result(result, "", task_type=target_task_type)
            except Exception as e:
                self.logger.warning(f"[EchoOptuna] Self-edit failed during trial: {e}")
                score = float("inf")
            return score

        # Use EchoCore's persistent study when available (Flask context).
        # This preserves trial history across runs and lets Optuna learn
        # from accumulated outcomes rather than starting cold every call.
        study = None
        try:
            from flask import current_app
            core = current_app.config.get("echo_core")
            if core is not None and getattr(core, "optuna_study", None) is not None:
                study = core.optuna_study
        except Exception:
            pass

        if study is None:
            study = optuna.create_study(
                study_name="echo_self_edit",
                storage="sqlite:///memory/optuna.db",
                load_if_exists=True,
                direction="minimize",
            )

        if param_hints:
            sanitized = {}
            for key in ("intensity", "creativity"):
                value = param_hints.get(key)
                if isinstance(value, (int, float)) and 0.0 <= value <= 1.0:
                    sanitized[key] = float(value)
            if sanitized:
                study.enqueue_trial(sanitized)
                self.logger.info(f"[EchoOptuna] Queued model-suggested hint trial: {sanitized}")

        trials_before = len(study.trials)
        study.optimize(objective, n_trials=n_trials)

        # Select "best" from THIS call's own trials, not study.best_trial (all-time
        # history). study.best_trial uses strict `<` when updating, so once any
        # trial anywhere in the persistent study's history hits the score floor
        # (0.0 — a perfect quality=4/4), no future trial can ever be recognized as
        # "better" even if it also hits that same floor. Confirmed live: a trial
        # from 2026-06-26 (weeks before real dry_run scoring existed, back when
        # trials were mostly wasted on the cooldown bug) permanently pinned
        # study.best_trial, so run.py's deploy step kept reapplying those
        # two-week-old params every hour regardless of what today's real quality-
        # scored trials found. The persistent study/sampler is still valuable —
        # TPE benefits from historical trials for guiding exploration — this only
        # changes what "best" means for the *deployment* decision.
        new_trials = [
            t for t in study.trials[trials_before:]
            if t.state == optuna.trial.TrialState.COMPLETE and t.value is not None
        ]
        if new_trials:
            best_new = min(new_trials, key=lambda t: (t.value, -t.number))
            self.logger.info(
                f"[EchoOptuna] Best trial this cycle: {best_new.params} with value {best_new.value} "
                f"(trial #{best_new.number} of {len(new_trials)} completed this cycle)"
            )
            return best_new.params, best_new.value

        # No trial from this cycle completed successfully (all failed/inf) — fall
        # back to the historical best rather than returning nothing, but log it
        # clearly as a fallback so it isn't mistaken for real progress this cycle.
        self.logger.warning(
            "[EchoOptuna] No trial completed successfully this cycle — "
            f"falling back to all-time best: {study.best_trial.params} with value {study.best_value}"
        )
        return study.best_trial.params, study.best_value

