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

        for w in (
            self._model_lbl,
            self._uptime_lbl,
            self._ram_lbl,
            self._vector_lbl,
            self._council_lbl,
            self._selfedit_lbl,
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

        pending_count = self_edit.get("pending") if isinstance(self_edit, dict) else None
        evaluated_count = self_edit.get("evaluated") if isinstance(self_edit, dict) else None
        if pending_count is not None and evaluated_count is not None:
            self._selfedit_lbl.setText(f"self-edit: {evaluated_count} eval / {pending_count} pending")
        else:
            self._selfedit_lbl.setText("self-edit: —")

    def _on_error(self, _message: str):
        self._model_lbl.setText("model: unreachable")
