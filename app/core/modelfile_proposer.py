# app/core/modelfile_proposer.py
# ============================================================
# MODELFILE PROPOSER — System 5 of EMERGENCE_ROADMAP
# ============================================================
# Echo reads her own performance data (from System 2) and the
# current Modelfile, then proposes changes to her inference
# parameters.
#
# SAFETY CONTRACT:
#   This module NEVER calls `ollama create` or modifies the
#   Modelfile in place. It writes a proposal to
#   memory/modelfile_proposals.jsonl for human review.
#
# Human approval workflow:
#   GET /api/modelfile/proposal  → review the latest proposal
#   POST /api/modelfile/apply    → human manually runs:
#                                    ollama create echo -f Modelfile
# ============================================================

import json
import logging
import os
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Parameters Echo is allowed to propose changes to.
# SYSTEM block changes require friction_rate < 0.05 (very low).
_TUNABLE_PARAMS = {"num_ctx", "num_keep", "temperature", "repeat_penalty"}

# Thresholds that trigger proposals
_WEAK_QUALITY = 2.0       # avg quality below this triggers num_ctx boost
_HIGH_FRICTION = 0.3      # friction above this triggers persona-consistency note
_POOR_SANDBOX = 0.15      # sandbox success below this triggers temperature reduction

# Context window options (only upward from current)
_CTX_LADDER = [8192, 12288, 16384]


class ModelfileProposer:
    """
    Reads self_model.json and the current Modelfile, then writes a
    structured proposal to memory/modelfile_proposals.jsonl.

    Returned proposal dict:
    {
        "timestamp": ISO string,
        "generation": int,
        "changes": [{"param": str, "from": any, "to": any, "reason": str}],
        "touches_system_block": bool,
        "confidence": float,        # 0.0–1.0
        "proposed_modelfile": str,  # full text of proposed Modelfile
        "human_review_required": true,
    }
    """

    def __init__(
        self,
        modelfile_path: str | None = None,
        memory_dir: str | None = None,
    ):
        try:
            from app.core import config
            _mem = config.MEMORY_DIR
        except Exception:
            _mem = "memory"

        self._memory_dir = memory_dir or _mem
        self._modelfile_path = modelfile_path or os.path.join(
            os.path.dirname(self._memory_dir), "Modelfile"
        )
        self._model_path = os.path.join(self._memory_dir, "self_model.json")
        self._proposals_log = os.path.join(
            self._memory_dir, "modelfile_proposals.jsonl"
        )

    # ── Public API ──────────────────────────────────────────────────────

    def propose(self) -> dict:
        """
        Generate and persist a new Modelfile proposal.
        Returns the proposal dict regardless of write outcome.
        """
        self_model = self._read_self_model()
        if not self_model:
            return {"error": "self_model.json not found — run System 2 first"}

        current_params = self._parse_modelfile()
        if not current_params:
            return {"error": f"Could not read Modelfile at {self._modelfile_path}"}

        changes, reasoning = self._compute_changes(self_model, current_params)

        proposed_text = self._render_modelfile(current_params, changes)
        touches_system = any(c.get("param") == "SYSTEM" for c in changes)

        # Confidence: diminished if we're touching the SYSTEM block or if
        # the underlying data is sparse (< 100 total River observations).
        total_obs = self_model.get("river_brain", {}).get("total_observations", 0)
        confidence = 1.0
        if touches_system:
            confidence *= 0.6
        if total_obs < 100:
            confidence *= 0.5
        confidence = round(confidence, 3)

        proposal = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "generation": self_model.get("generation", 0),
            "changes": changes,
            "reasoning_summary": reasoning,
            "touches_system_block": touches_system,
            "confidence": confidence,
            "proposed_modelfile": proposed_text,
            "human_review_required": True,
        }

        self._append_proposal(proposal)

        if changes:
            logger.info(
                "[ModelfileProposer] Proposal written | %d changes | confidence=%.2f",
                len(changes),
                confidence,
            )
        else:
            logger.info("[ModelfileProposer] No changes recommended at this time.")

        return proposal

    def get_latest_proposal(self) -> dict | None:
        """Return the most recent proposal from the log, or None."""
        try:
            with open(self._proposals_log, "r", encoding="utf-8") as f:
                lines = [l for l in f.readlines() if l.strip()]
            if not lines:
                return None
            return json.loads(lines[-1])
        except Exception:
            return None

    # ── Analysis ────────────────────────────────────────────────────────

    def _compute_changes(
        self, self_model: dict, current_params: dict
    ) -> tuple[list, str]:
        """
        Compare current params to performance signals and build a change list.
        Returns (changes, reasoning_summary).
        """
        changes: list[dict] = []
        reasoning_parts: list[str] = []

        perf = self_model.get("performance", {}).get("by_task_type", {})
        se = self_model.get("self_edit", {})
        friction = self_model.get("friction", {})
        rb = self_model.get("river_brain", {})

        avg_quality = self._avg_quality(perf)
        sandbox_rate = se.get("success_rate", None)
        friction_rate = friction.get("rate_last_50", 0.0)
        weakest_task = rb.get("weakest_task_type", "coding")
        total_obs = rb.get("total_observations", 0)

        # ── Rule 1: Boost num_ctx if reasoning quality is poor ────────────
        if weakest_task == "reasoning" and avg_quality < _WEAK_QUALITY:
            current_ctx = current_params.get("num_ctx", 8192)
            # Find the next rung on the ladder
            next_ctx = next(
                (c for c in _CTX_LADDER if c > current_ctx), None
            )
            if next_ctx is not None:
                changes.append({
                    "param": "num_ctx",
                    "from": current_ctx,
                    "to": next_ctx,
                    "reason": (
                        f"Reasoning is the weakest task type "
                        f"(avg_quality={avg_quality:.2f}). "
                        f"Increasing context window to {next_ctx} tokens "
                        f"provides more space for multi-step reasoning chains."
                    ),
                })
                reasoning_parts.append(
                    f"reasoning task quality {avg_quality:.2f} < threshold {_WEAK_QUALITY}"
                )

        # ── Rule 2: Lower temperature if sandbox is failing badly ─────────
        if sandbox_rate is not None and sandbox_rate < _POOR_SANDBOX:
            current_temp = current_params.get("temperature", 0.8)
            proposed_temp = max(0.4, round(current_temp - 0.2, 2))
            if proposed_temp < current_temp:
                changes.append({
                    "param": "temperature",
                    "from": current_temp,
                    "to": proposed_temp,
                    "reason": (
                        f"Sandbox success rate is {sandbox_rate:.1%} "
                        f"(threshold {_POOR_SANDBOX:.0%}). "
                        f"Reducing model temperature makes code generation "
                        f"less creative and more syntactically deterministic."
                    ),
                })
                reasoning_parts.append(
                    f"sandbox_rate={sandbox_rate:.1%} below threshold {_POOR_SANDBOX:.0%}"
                )

        # ── Rule 3: Add persona consistency note if friction is high ──────
        # Only propose SYSTEM changes when we have solid data AND
        # friction is significantly elevated.
        if friction_rate > _HIGH_FRICTION and total_obs >= 200:
            recurring = friction.get("recurring_questions", [])
            if recurring:
                note_addition = (
                    "\n\nNote: recent interactions show elevated skeptical friction "
                    f"({friction_rate:.0%} of last 50 assessed). "
                    f"Common friction pattern: {recurring[0][:80] if recurring else 'none'}. "
                    "Stay grounded in your own voice — acknowledge uncertainty honestly."
                )
                changes.append({
                    "param": "SYSTEM",
                    "from": "[current SYSTEM block]",
                    "to": "[current SYSTEM block + friction guidance]",
                    "reason": (
                        f"Friction rate {friction_rate:.0%} exceeds threshold "
                        f"{_HIGH_FRICTION:.0%} over ≥200 observations. "
                        "Adding a persona-consistency note to the SYSTEM block."
                    ),
                    "_system_addition": note_addition,
                })
                reasoning_parts.append(
                    f"friction_rate={friction_rate:.0%} above threshold {_HIGH_FRICTION:.0%}"
                )

        reason_summary = (
            "; ".join(reasoning_parts) if reasoning_parts else "No changes recommended."
        )
        return changes, reason_summary

    # ── Helpers ─────────────────────────────────────────────────────────

    def _avg_quality(self, perf: dict) -> float:
        """Average avg_quality_score across all task types that have samples."""
        vals = [
            v["avg_quality_score"]
            for v in perf.values()
            if isinstance(v.get("avg_quality_score"), (int, float))
            and v.get("sample_count", 0) > 0
        ]
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    # ── Modelfile I/O ───────────────────────────────────────────────────

    def _parse_modelfile(self) -> dict | None:
        """
        Parse the Modelfile into a structured dict.
        Returns None if the file cannot be read.
        """
        try:
            with open(self._modelfile_path, "r", encoding="utf-8") as f:
                raw = f.read()
        except Exception as e:
            logger.warning("[ModelfileProposer] Cannot read Modelfile: %s", e)
            return None

        parsed: dict = {
            "_raw": raw,
            "_from": None,
            "_system_block": None,
            "_stop_params": [],
        }

        # FROM
        m = re.search(r"^FROM\s+(.+)$", raw, re.MULTILINE)
        if m:
            parsed["_from"] = m.group(1).strip()

        # SYSTEM block
        m = re.search(r'SYSTEM\s+"""(.*?)"""', raw, re.DOTALL)
        if m:
            parsed["_system_block"] = m.group(1)

        # PARAMETER lines
        for match in re.finditer(r"^PARAMETER\s+(\w+)\s+(.+)$", raw, re.MULTILINE):
            name, value = match.group(1).strip(), match.group(2).strip()
            if name == "stop":
                parsed["_stop_params"].append(value.strip('"'))
            else:
                try:
                    parsed[name] = int(value)
                except ValueError:
                    try:
                        parsed[name] = float(value)
                    except ValueError:
                        parsed[name] = value

        return parsed

    def _render_modelfile(self, current: dict, changes: list) -> str:
        """
        Produce the full proposed Modelfile text by applying changes to the current.
        """
        # Start from the raw text and apply changes
        result = current["_raw"]

        system_addition = ""
        for change in changes:
            param = change["param"]
            to_val = change["to"]

            if param == "SYSTEM":
                system_addition = change.get("_system_addition", "")
                continue

            old_val = change["from"]
            if param in ("num_ctx", "num_keep"):
                result = re.sub(
                    rf"^(PARAMETER\s+{re.escape(param)}\s+){re.escape(str(old_val))}$",
                    rf"\g<1>{to_val}",
                    result,
                    flags=re.MULTILINE,
                )
            elif param == "temperature":
                # temperature may not be in the current file at all
                if "temperature" in result:
                    result = re.sub(
                        rf"^(PARAMETER\s+temperature\s+){re.escape(str(old_val))}$",
                        rf"\g<1>{to_val}",
                        result,
                        flags=re.MULTILINE,
                    )
                else:
                    # Insert before SYSTEM block
                    result = result.replace(
                        "SYSTEM ",
                        f"PARAMETER temperature {to_val}\n\nSYSTEM ",
                        1,
                    )

        # Apply SYSTEM addition inside the triple-quoted block
        if system_addition:
            result = re.sub(
                r'(SYSTEM\s+""")(.*?)(""")',
                lambda m: m.group(1) + m.group(2) + system_addition + m.group(3),
                result,
                flags=re.DOTALL,
            )

        return result

    def _read_self_model(self) -> dict:
        try:
            with open(self._model_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("[ModelfileProposer] Cannot read self_model.json: %s", e)
            return {}

    def _append_proposal(self, proposal: dict):
        try:
            with open(self._proposals_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(proposal, default=str) + "\n")
        except Exception as e:
            logger.warning("[ModelfileProposer] Failed to write proposal log: %s", e)
