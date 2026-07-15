"""Background activity view: dream cycles, self-edit/council activity, tail
logs. Read-only, polls GET /activity/log (dream_bridge.log tail +
council_ratings.jsonl recent entries) and GET /dashboard/health for the
self-edit / autonomy status blocks already aggregated there.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
)
from PySide6.QtCore import Qt

from echo_studio.api_client import ApiClient

POLL_INTERVAL_MS = 8000


class _ActivityFetchWorker(QObject):
    result = Signal(dict, dict)  # activity_payload, health_payload
    error = Signal(str)

    def __init__(self, api: ApiClient):
        super().__init__()
        self._api = api

    def run(self):
        try:
            activity = self._api.activity_log(limit=200)
            health = self._api.get_health()
            self.result.emit(activity, health)
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))


class ActivityView(QWidget):
    def __init__(self, api: ApiClient, parent=None):
        super().__init__(parent)
        self._api = api
        self._thread: QThread | None = None

        root = QVBoxLayout(self)

        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("Background activity"))
        header_row.addStretch(1)
        refresh_btn = QPushButton("Refresh now")
        refresh_btn.clicked.connect(self._poll)
        header_row.addWidget(refresh_btn)
        root.addLayout(header_row)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: palette(mid); font-style: italic;")
        root.addWidget(self._status_label)

        splitter = QSplitter(Qt.Orientation.Vertical)

        dream_panel = QWidget()
        dream_layout = QVBoxLayout(dream_panel)
        dream_layout.addWidget(QLabel("Dream log (indexing / self-healing / analysis cycles)"))
        self._dream_list = QListWidget()
        dream_layout.addWidget(self._dream_list)
        splitter.addWidget(dream_panel)

        council_panel = QWidget()
        council_layout = QVBoxLayout(council_panel)
        council_layout.addWidget(QLabel("Council rating activity"))
        self._council_list = QListWidget()
        council_layout.addWidget(self._council_list)
        splitter.addWidget(council_panel)

        workspace_panel = QWidget()
        workspace_layout = QVBoxLayout(workspace_panel)
        workspace_layout.addWidget(QLabel("Global Workspace events (world model, dreams, self-edit, scheduler)"))
        self._workspace_list = QListWidget()
        workspace_layout.addWidget(self._workspace_list)
        splitter.addWidget(workspace_panel)

        selfedit_panel = QWidget()
        selfedit_layout = QVBoxLayout(selfedit_panel)
        selfedit_layout.addWidget(QLabel("Self-edit / autonomy status"))
        self._selfedit_label = QLabel("—")
        self._selfedit_label.setWordWrap(True)
        selfedit_layout.addWidget(self._selfedit_label)
        splitter.addWidget(selfedit_panel)

        root.addWidget(splitter, stretch=1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(POLL_INTERVAL_MS)
        self._poll()

    def _poll(self):
        if self._thread is not None:
            return
        self._status_label.setText("loading…")
        self._thread = QThread(self)
        worker = _ActivityFetchWorker(self._api)
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.result.connect(self._on_result)
        worker.error.connect(self._on_error)
        worker.result.connect(self._cleanup)
        worker.error.connect(self._cleanup)
        self._worker = worker
        self._thread.start()

    def _cleanup(self, *_args):
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
        self._thread = None

    def _on_result(self, activity: dict, health: dict):
        self._status_label.setText("")

        self._dream_list.clear()
        for line in activity.get("dream_log", [])[-100:]:
            self._dream_list.addItem(QListWidgetItem(line))
        self._dream_list.scrollToBottom()

        self._council_list.clear()
        for entry in reversed(activity.get("council_recent", [])[-50:]):
            label = (
                f"[{entry.get('timestamp_utc', '')[:19]}] "
                f"{entry.get('task_type', '?')} — council={entry.get('council_rating')} "
                f"quality={entry.get('quality_score')} human={entry.get('human_spot_check_rating')}"
            )
            self._council_list.addItem(QListWidgetItem(label))

        self._workspace_list.clear()
        for entry in reversed(activity.get("workspace_events", [])[-100:]):
            salience = entry.get("salience")
            salience_str = f"{salience:.2f}" if isinstance(salience, (int, float)) else "—"
            label = (
                f"[{(entry.get('ts') or '')[:19]}] "
                f"{entry.get('type', '?')} <- {entry.get('source', '?')} "
                f"(salience={salience_str}) {entry.get('summary', '')}"
            )
            self._workspace_list.addItem(QListWidgetItem(label))

        self_edit = health.get("self_edit", {})
        outcomes = health.get("self_edit_outcomes", {})
        autonomy = health.get("autonomy", {})
        lines = [
            f"success_rate: {self_edit.get('success_rate', '—')}",
            f"hours_since_last_success: {self_edit.get('hours_since_last_success', '—')}",
            f"outcomes evaluated/pending: {outcomes.get('evaluated', '—')}/{outcomes.get('pending', '—')}",
            "",
            "Autonomy loops:",
        ]
        for loop_name, loop_state in (autonomy.items() if isinstance(autonomy, dict) else []):
            if isinstance(loop_state, dict):
                lines.append(
                    f"  {loop_name}: last check {loop_state.get('last_check_utc', '—')[:19]}"
                    f"{' — skipped: ' + str(loop_state.get('skipped_reason')) if loop_state.get('skipped_reason') else ''}"
                )
        self._selfedit_label.setText("\n".join(lines))

    def _on_error(self, message: str):
        self._status_label.setText(f"error: {message}")
