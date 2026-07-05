import optuna
import logging
import random
from typing import Any, Dict, Optional, Tuple, List

from app.core import self_edit_manager
from app.core.memory_bridge import retrieve_relevant_memories

logger = logging.getLogger(__name__)


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
        - (True, _) tuple → radon structural score 0.0–0.5 (sandbox passed)
        - (False, _) tuple → 1.0 (sandbox failed; still informative for Optuna)
        - string → quality scorer (0–4 int) normalized to 0.0–1.0 (inverted)
        - dict with explicit metrics → 1 - avg(metrics)
        - None or unrecognised → inf
        """
        try:
            if result is None:
                return float("inf")

            # (success, detail) tuple from execute_self_edit
            if isinstance(result, tuple) and len(result) == 2:
                success, _ = result
                if not success:
                    return 1.0
                # Score the generated code structurally — good self-edits
                # produce clean, low-complexity, maintainable code.
                return self._score_code_structure(self_edit_manager.SELF_EDIT_FILE)

            # String response — use quality scorer
            if isinstance(result, str):
                r = result.strip()
                if not r or r == prompt.strip():
                    return float("inf")
                try:
                    from app.core.echo_quality_scorer import score_response
                    raw = score_response(r, task_type)  # 0–4 int
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

    def optimize_self_edit(self, n_trials: int = 10) -> Tuple[Dict[str, float], float]:
        """
        Run Optuna to find the best self-edit parameters.
        Each trial samples a prompt from memory and runs a dry self-edit.
        Returns (best_params, best_value). Lower best_value is better.

        System 3: reads the weak task type from the living self-model so
        every trial targets the area where Echo's performance is poorest.
        """
        target_task_type = "coding"
        try:
            from app.core.self_model_updater import SelfModelUpdater
            target_task_type = SelfModelUpdater().get_weak_task_type()
            self.logger.info(f"[EchoOptuna] Targeting weak task type: {target_task_type}")
        except Exception as e:
            self.logger.warning(f"[EchoOptuna] Could not read self-model target: {e}")

        def objective(trial: optuna.trial.Trial) -> float:
            intensity = trial.suggest_float("intensity", 0.0, 1.0)
            creativity = trial.suggest_float("creativity", 0.0, 1.0)

            try:
                result = self_edit_manager.perform_self_edit(
                    intensity=intensity,
                    creativity=creativity,
                    target_task_type=target_task_type,
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

        study.optimize(objective, n_trials=n_trials)

        self.logger.info(f"[EchoOptuna] Best trial: {study.best_trial.params} with value {study.best_value}")
        return study.best_trial.params, study.best_value

