"""Settings page: surfaces existing configuration. Strictly read-only — no
edit form exists or is planned (see EchoStudio_Design.md's hard constraints).
Backed entirely by GET /settings/view.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit

from echo_studio.api_client import ApiClient


class _SettingsFetchWorker(QObject):
    result = Signal(dict)
    error = Signal(str)

    def __init__(self, api: ApiClient):
        super().__init__()
        self._api = api

    def run(self):
        try:
            self.result.emit(self._api.settings_view())
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))


class SettingsView(QWidget):
    def __init__(self, api: ApiClient, parent=None):
        super().__init__(parent)
        self._api = api
        self._thread: QThread | None = None

        root = QVBoxLayout(self)

        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("Settings (read-only — reflects existing backend config)"))
        header_row.addStretch(1)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load)
        header_row.addWidget(refresh_btn)
        root.addLayout(header_row)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: palette(mid); font-style: italic;")
        root.addWidget(self._status_label)

        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setStyleSheet("font-family: Menlo, monospace;")
        root.addWidget(self._text, stretch=1)

        self._load()

    def _load(self):
        if self._thread is not None:
            return
        self._status_label.setText("loading…")
        self._thread = QThread(self)
        worker = _SettingsFetchWorker(self._api)
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

    def _on_result(self, payload: dict):
        self._status_label.setText("")
        lines = []

        lines.append("Environment variables present (values never shown):")
        for key in payload.get("env_keys_present", []):
            lines.append(f"  - {key}")
        lines.append("")

        lines.append("Modelfile parameters:")
        for p in payload.get("modelfile_parameters", []):
            lines.append(f"  {p}")
        lines.append("")

        lines.append("Per-task token limits:")
        limits = payload.get("task_token_limits", {})
        for task, limit in (limits.items() if isinstance(limits, dict) else []):
            lines.append(f"  {task}: {limit}")
        lines.append("")

        principles = payload.get("principles", {})
        if isinstance(principles, dict) and "error" not in principles:
            lines.append(f"Principles generation: {principles.get('generation')}")
            lines.append("Principles:")
            for k, v in (principles.get("principles") or {}).items():
                lines.append(f"  {k}: {v}")
            lines.append("Runtime signals:")
            for k, v in (principles.get("runtime_signals") or {}).items():
                lines.append(f"  {k}: {v}")

        self._text.setPlainText("\n".join(lines))

    def _on_error(self, message: str):
        self._status_label.setText(f"error: {message}")
