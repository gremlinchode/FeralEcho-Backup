"""Health strip: polls GET /dashboard/health on a timer.

Phase 1 scope: model/Ollama status, uptime, RAM, vector memory count — the
fields already available from app/routes_echo_studio.py:dashboard_health().
The fuller multi-metric dashboard (self-edit status, council status, dream
activity, background task list) is Phase 4.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame

from echo_studio.api_client import ApiClient

POLL_INTERVAL_MS = 5000


class _HealthPollWorker(QObject):
    result = Signal(dict)
    error = Signal(str)

    def __init__(self, api: ApiClient):
        super().__init__()
        self._api = api

    def run(self):
        try:
            self.result.emit(self._api.get_health())
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))


def _tile(label: str) -> QLabel:
    lbl = QLabel(label)
    lbl.setStyleSheet(
        "padding: 4px 10px; border-right: 1px solid palette(mid);"
    )
    return lbl


class HealthDashboardView(QWidget):
    def __init__(self, api: ApiClient, parent=None):
        super().__init__(parent)
        self._api = api
        self._thread: QThread | None = None

        self.setFrameShape = QFrame.Shape.StyledPanel
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._model_lbl = _tile("model: —")
        self._uptime_lbl = _tile("uptime: —")
        self._ram_lbl = _tile("RAM: —")
        self._vector_lbl = _tile("vectors: —")
        self._council_lbl = _tile("council: —")
        self._selfedit_lbl = _tile("self-edit: —")
        self._selfheal_lbl = _tile("self-heal: —")
        self._liveness_lbl = _tile("liveness: —")

        for w in (
            self._model_lbl,
            self._uptime_lbl,
            self._ram_lbl,
            self._vector_lbl,
            self._council_lbl,
            self._selfedit_lbl,
            self._selfheal_lbl,
            self._liveness_lbl,
        ):
            layout.addWidget(w)
        layout.addStretch(1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(POLL_INTERVAL_MS)
        self._poll()  # immediate first read

    def _poll(self):
        if self._thread is not None:
            return  # previous poll still in flight — skip this tick
        self._thread = QThread(self)
        worker = _HealthPollWorker(self._api)
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.result.connect(self._on_result)
        worker.error.connect(self._on_error)
        worker.result.connect(self._cleanup)
        worker.error.connect(self._cleanup)
        self._worker = worker  # keep a reference alive until cleanup
        self._thread.start()

    def _cleanup(self, *_args):
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
        self._thread = None

    def _on_result(self, payload: dict):
        sysh = payload.get("system_health", {}) or {}
        sentinel = payload.get("sentinel", {}) or {}
        council = payload.get("council", {}) or {}
        self_edit = payload.get("self_edit_outcomes", {}) or {}
        self_edit_gen = payload.get("self_edit", {}) or {}
        self_heal = payload.get("self_heal", {}) or {}

        ollama_alive = sysh.get("ollama_process_alive")
        self._model_lbl.setText(
            f"model: {'online' if ollama_alive else 'offline' if ollama_alive is not None else '—'}"
        )

        uptime_s = sentinel.get("uptime_s")
        if isinstance(uptime_s, (int, float)):
            h, rem = divmod(int(uptime_s), 3600)
            m, _ = divmod(rem, 60)
            self._uptime_lbl.setText(f"uptime: {h}h{m:02d}m")
        else:
            self._uptime_lbl.setText("uptime: —")

        ram_pct = sysh.get("ram_pressure_pct")
        self._ram_lbl.setText(
            f"RAM: {ram_pct:.0f}%" if isinstance(ram_pct, (int, float)) else "RAM: —"
        )

        vcount = payload.get("vector_memory_count")
        self._vector_lbl.setText(f"vectors: {vcount}" if vcount is not None else "vectors: —")

        agreement = council.get("agreement_rate")
        self._council_lbl.setText(
            f"council: {agreement * 100:.0f}%" if isinstance(agreement, (int, float)) else "council: —"
        )

        # CLAUDE.md Finding 41 / Echo Studio blind-spot fix: this used to only
        # show pending/evaluated *counts* from self_edit_outcomes — the actual
        # generation success_rate and quality trend (introspection_state.json's
        # "self_edit" block, always present in the API response) were computed
        # server-side but never read by this view at all. A "self-edit: 14/14
        # eval" tile can look calm while the real generation success rate is
        # 14%. Surface the number that actually matters, not just activity counts.
        success_rate = self_edit_gen.get("success_rate")
        quality_delta = self_edit_gen.get("recent_quality_delta")
        pending_count = self_edit.get("pending") if isinstance(self_edit, dict) else None
        evaluated_count = self_edit.get("evaluated") if isinstance(self_edit, dict) else None

        if isinstance(success_rate, (int, float)):
            delta_str = f" (Δ{quality_delta:+.2f})" if isinstance(quality_delta, (int, float)) else ""
            text = f"self-edit: {success_rate * 100:.0f}% success{delta_str}"
            if pending_count is not None and evaluated_count is not None:
                text += f" / {evaluated_count} eval, {pending_count} pending"
            self._selfedit_lbl.setText(text)
            # A struggling generation loop should look struggling, not neutral —
            # same "don't hide behind a clean tile" fix this whole block exists for.
            if success_rate < 0.3 or (isinstance(quality_delta, (int, float)) and quality_delta < 0):
                self._selfedit_lbl.setStyleSheet(
                    "padding: 4px 10px; border-right: 1px solid palette(mid); color: #c0392b;"
                )
                self._selfedit_lbl.setToolTip(
                    "Self-edit generation success rate is low and/or trending down. "
                    "This reflects the underlying candidate-generation loop, not whether "
                    "a currently-deployed edit is safe (see self_edit_apply_to_code in the "
                    "liveness tile for that)."
                )
            else:
                self._selfedit_lbl.setStyleSheet(
                    "padding: 4px 10px; border-right: 1px solid palette(mid);"
                )
                self._selfedit_lbl.setToolTip("")
        elif pending_count is not None and evaluated_count is not None:
            self._selfedit_lbl.setText(f"self-edit: {evaluated_count} eval / {pending_count} pending")
        else:
            self._selfedit_lbl.setText("self-edit: —")

        connected = self_heal.get("connected") if isinstance(self_heal, dict) else None
        if connected is None:
            self._selfheal_lbl.setText("self-heal: —")
            self._selfheal_lbl.setStyleSheet(
                "padding: 4px 10px; border-right: 1px solid palette(mid); color: palette(mid);"
            )
        else:
            self._selfheal_lbl.setText(f"self-heal: {'connected' if connected else 'disconnected'}")
            self._selfheal_lbl.setStyleSheet(
                "padding: 4px 10px; border-right: 1px solid palette(mid);"
                + ("" if connected else " color: palette(mid);")
            )
        self._selfheal_lbl.setToolTip(self_heal.get("note", ""))

        self._update_liveness_tile(payload.get("liveness", {}) or {})

    def _update_liveness_tile(self, liveness: dict):
        # liveness_ledger._CHECKS as of this writing (16, CLAUDE.md Finding 42)
        # — kept as a plain literal here (not imported) since this view has no
        # other app.core import and the count only needs to be roughly right
        # for display; get_liveness_status() itself is the ground truth this
        # tile reflects, this is just the label. This list was stale at 11 for
        # a while (missing global_workspace_consumption, valence_self_report,
        # reflection_shard_generation, dissent_log_hook) — the exact
        # "doc/display lags what's actually true" pattern this project keeps
        # finding, this time in the one place meant to show it isn't stale.
        # Caught going stale again within the same session that fixed it last
        # (missing seam_engine, added the same night as this comment) —
        # updated immediately rather than left to be found a third time.
        known_checks = [
            "self_edit_apply_to_code", "curiosity_engine", "nature_spark",
            "wolf_friction_bridge", "claude_shard", "question_garden_lineage",
            "claude_research", "self_model_drift", "task_type_classifier",
            "global_workspace", "substrate_continuity", "global_workspace_consumption",
            "valence_self_report", "reflection_shard_generation", "dissent_log_hook",
            "seam_engine",
        ]
        if not liveness.get("ledger_exists", True) or "error" in liveness:
            self._liveness_lbl.setText("liveness: —")
            self._liveness_lbl.setStyleSheet(
                "padding: 4px 10px; border-right: 1px solid palette(mid); color: palette(mid);"
            )
            self._liveness_lbl.setToolTip(liveness.get("note") or liveness.get("error") or "")
            return

        failing = [name for name in known_checks if not (liveness.get(name) or {}).get("pass", False)]
        total = len(known_checks)
        passing = total - len(failing)
        stale = bool(liveness.get("stale"))

        self._liveness_lbl.setText(f"liveness: {passing}/{total}{' (stale)' if stale else ''}")
        if failing or stale:
            self._liveness_lbl.setStyleSheet(
                "padding: 4px 10px; border-right: 1px solid palette(mid); color: #c0392b; font-weight: bold;"
            )
            tooltip_lines = [f"FAILING: {name}" for name in failing]
            if stale:
                tooltip_lines.append("Ledger is stale — introspection_channel collector may have stopped.")
            self._liveness_lbl.setToolTip("\n".join(tooltip_lines))
        else:
            self._liveness_lbl.setStyleSheet(
                "padding: 4px 10px; border-right: 1px solid palette(mid);"
            )
            self._liveness_lbl.setToolTip("All liveness checks passing.")

    def _on_error(self, _message: str):
        self._model_lbl.setText("model: unreachable")
