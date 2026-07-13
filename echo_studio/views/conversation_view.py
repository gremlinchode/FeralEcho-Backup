"""Conversation pane: message list, streamed rendering, prompt composer.

One active conversation at a time (switchable via the sidebar), full/fast
mode toggle, Cmd+Enter to send, markdown + syntax highlighted rendering,
copy button, regenerate, timestamps, draft autosave, char/token counters,
drag-and-drop file attach (ComposerInput), templates via saved prompts
(inserted through insert_prompt_text() from the sidebar).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, QObject, QThread, Signal, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QLabel,
    QComboBox,
    QCheckBox,
    QApplication,
)

from echo_studio.api_client import ApiClient, ChatEvent
from echo_studio.state.local_store import LocalStore
from echo_studio.widgets.markdown_view import MarkdownView
from echo_studio.widgets.composer_input import ComposerInput, est_tokens
from echo_studio.audio.speech_output import get_speech_output

_DRAFT_SAVE_DEBOUNCE_MS = 600
_TITLE_MAX_CHARS = 48


class _ChatStreamWorker(QObject):
    """Runs a streaming chat action (new message or regenerate) on a
    background QThread. Never touch Qt widgets from run() — only emit
    signals; connected slots run on the main thread."""

    status = Signal(str)
    token = Signal(str)
    done = Signal(str, str)   # full_text, task_type
    error = Signal(str)

    def __init__(self, action):
        super().__init__()
        self._action = action  # zero-arg callable that performs the blocking call

    def run(self):
        saw_done = False

        def on_event(ev: ChatEvent):
            nonlocal saw_done
            if ev.type == "status":
                self.status.emit(ev.status)
            elif ev.type == "token":
                self.token.emit(ev.text)
            elif ev.type == "done":
                saw_done = True
                self.done.emit(ev.text, ev.task_type)

        try:
            self._action(on_event)
            if not saw_done:
                # api_client.stream_chat()'s SSE loop simply ends (no
                # exception) if the server-side generator dies after tokens
                # have already streamed but before a final "done" frame —
                # previously neither done nor error fired here, leaving the
                # UI stuck in whatever state the last token/status left it
                # (composer disabled, "sending…" never clearing).
                self.error.emit("Connection ended before the response finished.")
        except Exception as e:  # noqa: BLE001 — surface any failure to the UI
            self.error.emit(str(e))


class _MessageBubble(QWidget):
    """One turn's rendered content, a timestamp, and a copy button."""

    def __init__(self, role: str, timestamp: str = "", parent=None):
        super().__init__(parent)
        self._role = role
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QHBoxLayout()
        who = QLabel("You" if role == "user" else "Echo")
        who.setStyleSheet("font-weight: 600; color: palette(mid);")
        header.addWidget(who)
        self._time_lbl = QLabel(timestamp)
        self._time_lbl.setStyleSheet("color: palette(mid); font-size: 11px;")
        header.addWidget(self._time_lbl)
        header.addStretch(1)
        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setFixedWidth(56)
        self._copy_btn.clicked.connect(self._copy)
        header.addWidget(self._copy_btn)
        layout.addLayout(header)

        self.view = MarkdownView()
        self.view.setMinimumHeight(24)
        layout.addWidget(self.view)

    def _copy(self):
        QApplication.clipboard().setText(self.view.raw_text())

    def set_timestamp(self, timestamp: str):
        self._time_lbl.setText(timestamp)

    def set_text(self, text: str):
        self.view.set_markdown(text)
        doc_height = self.view.document().size().height()
        self.view.setFixedHeight(int(doc_height) + 12)


def _short_time(iso_ts: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except Exception:
        return ""


class ConversationView(QWidget):
    conversation_created = Signal(str)   # conversation_id — first message just sent in a new conv
    title_changed = Signal(str, str)     # conversation_id, new title
    save_prompt_requested = Signal(str)  # current draft text

    def __init__(self, api: ApiClient, store: LocalStore, conversation_id: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._api = api
        self._store = store
        self._conversation_id = conversation_id or str(uuid.uuid4())
        self._thread: QThread | None = None
        self._worker: _ChatStreamWorker | None = None
        self._current_bubble: _MessageBubble | None = None
        self._current_text = ""
        self._last_user_message = ""

        root = QVBoxLayout(self)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._message_container = QWidget()
        self._message_layout = QVBoxLayout(self._message_container)
        self._message_layout.addStretch(1)
        self._scroll.setWidget(self._message_container)
        root.addWidget(self._scroll, stretch=1)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: palette(mid); font-style: italic;")
        root.addWidget(self._status_label)

        composer_row = QHBoxLayout()
        self._mode_box = QComboBox()
        self._mode_box.addItems(["Full (deliberation)", "Fast (no deliberation)"])
        composer_row.addWidget(self._mode_box)

        self._speak_checkbox = QCheckBox("Speak responses")
        self._speak_checkbox.setChecked(True)
        self._speak_checkbox.toggled.connect(self._on_speak_toggled)
        composer_row.addWidget(self._speak_checkbox)

        self._stop_speaking_btn = QPushButton("Stop speaking")
        self._stop_speaking_btn.clicked.connect(lambda: get_speech_output().stop())
        composer_row.addWidget(self._stop_speaking_btn)

        composer_row.addStretch(1)
        self._regenerate_btn = QPushButton("Regenerate")
        self._regenerate_btn.setEnabled(False)
        self._regenerate_btn.clicked.connect(self._on_regenerate_clicked)
        composer_row.addWidget(self._regenerate_btn)
        root.addLayout(composer_row)

        input_row = QHBoxLayout()
        self._input = ComposerInput()
        self._input.setPlaceholderText(
            "Type a message… (Cmd+Enter to send, unlimited length — drop a file to attach it)"
        )
        self._input.setFixedHeight(90)
        self._input.textChanged.connect(self._on_input_changed)
        self._input.drop_rejected.connect(
            lambda reason: self._status_label.setText(f"couldn't attach: {reason}")
        )
        input_row.addWidget(self._input, stretch=1)

        self._send_btn = QPushButton("Send")
        self._send_btn.setFixedWidth(80)
        self._send_btn.clicked.connect(self._on_send_clicked)
        input_row.addWidget(self._send_btn)
        root.addLayout(input_row)

        counter_row = QHBoxLayout()
        self._counter_label = QLabel("0 chars · ~0 tokens")
        self._counter_label.setStyleSheet("color: palette(mid); font-size: 11px;")
        counter_row.addWidget(self._counter_label)
        counter_row.addStretch(1)
        save_prompt_btn = QPushButton("Save as prompt")
        save_prompt_btn.setFixedWidth(110)
        save_prompt_btn.clicked.connect(self._on_save_prompt_clicked)
        counter_row.addWidget(save_prompt_btn)
        root.addLayout(counter_row)

        send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        send_shortcut.activated.connect(self._on_send_clicked)
        send_shortcut_mac = QShortcut(QKeySequence("Meta+Return"), self)
        send_shortcut_mac.activated.connect(self._on_send_clicked)

        self._draft_timer = QTimer(self)
        self._draft_timer.setSingleShot(True)
        self._draft_timer.timeout.connect(self._save_draft)

        self._store.create_conversation(self._conversation_id)
        self._load_history()

    # ----------------------------------------------------------------------
    # Conversation switching
    # ----------------------------------------------------------------------
    def is_busy(self) -> bool:
        return self._thread is not None

    def conversation_id(self) -> str:
        return self._conversation_id

    def load_conversation(self, conversation_id: str):
        if self.is_busy():
            self._status_label.setText("Please wait for the current response to finish.")
            return
        self._conversation_id = conversation_id
        self._clear_messages()
        self._load_history()

    def start_new_conversation(self):
        if self.is_busy():
            self._status_label.setText("Please wait for the current response to finish.")
            return
        new_id = str(uuid.uuid4())
        self._store.create_conversation(new_id)
        self._conversation_id = new_id
        self._clear_messages()
        self._input.clear()
        self.conversation_created.emit(new_id)

    def insert_prompt_text(self, text: str):
        cursor = self._input.textCursor()
        cursor.insertText(text)
        self._input.setFocus()

    def _clear_messages(self):
        while self._message_layout.count() > 1:
            item = self._message_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._current_bubble = None
        self._status_label.setText("")

    def _load_history(self):
        for msg in self._store.get_messages(self._conversation_id):
            bubble = self._add_bubble(msg["role"], _short_time(msg["timestamp"]))
            bubble.set_text(msg["text"])
        draft = self._store.get_draft(self._conversation_id)
        self._input.blockSignals(True)
        self._input.setPlainText(draft)
        self._input.blockSignals(False)
        self._regenerate_btn.setEnabled(
            bool(self._store.get_messages(self._conversation_id)) and not self.is_busy()
        )
        self._scroll_to_bottom()

    # ----------------------------------------------------------------------
    def _add_bubble(self, role: str, timestamp: str = "") -> _MessageBubble:
        bubble = _MessageBubble(role, timestamp)
        self._message_layout.insertWidget(self._message_layout.count() - 1, bubble)
        return bubble

    def _scroll_to_bottom(self):
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _on_input_changed(self):
        self._draft_timer.start(_DRAFT_SAVE_DEBOUNCE_MS)
        text = self._input.toPlainText()
        self._counter_label.setText(f"{len(text)} chars · ~{est_tokens(text)} tokens")

    def _save_draft(self):
        self._store.save_draft(self._conversation_id, self._input.toPlainText())

    def current_draft_text(self) -> str:
        return self._input.toPlainText()

    def _on_save_prompt_clicked(self):
        self.save_prompt_requested.emit(self._input.toPlainText())

    def _on_send_clicked(self):
        # Never submit while a response is still generating.
        if self.is_busy():
            return
        text = self._input.toPlainText().strip()
        if not text:
            return
        self._input.clear()
        self._store.clear_draft(self._conversation_id)
        self._send_message(text)

    def _mode(self) -> str:
        return "fast" if self._mode_box.currentIndex() == 1 else "full"

    def _maybe_set_title_from_first_message(self, text: str):
        existing = self._store.get_messages(self._conversation_id)
        if len(existing) == 0:  # this will be the first message once persisted
            title = text[:_TITLE_MAX_CHARS] + ("…" if len(text) > _TITLE_MAX_CHARS else "")
            self._store.rename_conversation(self._conversation_id, title)
            self.title_changed.emit(self._conversation_id, title)

    def _send_message(self, text: str):
        self._maybe_set_title_from_first_message(text)
        self._last_user_message = text

        now = datetime.utcnow().isoformat()
        user_bubble = self._add_bubble("user", _short_time(now))
        user_bubble.set_text(text)
        self._store.add_message(self._conversation_id, "user", text)

        self._current_bubble = self._add_bubble("echo", _short_time(now))
        self._current_text = ""
        self._current_bubble.set_text("")
        self._scroll_to_bottom()

        conversation_id = self._conversation_id
        mode = self._mode()

        def action(on_event):
            self._api.stream_chat(conversation_id, text, mode=mode, on_event=on_event)

        self._run_worker(action)

    def _on_regenerate_clicked(self):
        if self.is_busy():
            return
        messages = self._store.get_messages(self._conversation_id)
        if not messages or messages[-1]["role"] != "echo":
            return

        # Drop the last echo bubble (and its stored message) — a fresh one
        # will be appended once the regenerated response arrives.
        item = self._message_layout.takeAt(self._message_layout.count() - 2)
        if item and item.widget():
            item.widget().deleteLater()
        self._store.delete_last_message(self._conversation_id)

        self._current_bubble = self._add_bubble("echo", _short_time(datetime.utcnow().isoformat()))
        self._current_text = ""
        self._current_bubble.set_text("")
        self._scroll_to_bottom()

        conversation_id = self._conversation_id
        mode = self._mode()

        def action(on_event):
            self._api.regenerate_chat(conversation_id, mode=mode, on_event=on_event)

        self._run_worker(action, is_regenerate=True)

    def _run_worker(self, action, is_regenerate: bool = False):
        self._send_btn.setEnabled(False)
        self._regenerate_btn.setEnabled(False)
        self._status_label.setText("sending…")
        self._pending_is_regenerate = is_regenerate

        self._thread = QThread(self)
        self._worker = _ChatStreamWorker(action)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.status.connect(self._on_status)
        self._worker.token.connect(self._on_token)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)

        self._thread.start()

    def _on_status(self, status: str):
        self._status_label.setText(status)

    def _on_token(self, chunk: str):
        self._current_text += chunk
        if self._current_bubble is not None:
            self._current_bubble.set_text(self._current_text)
        self._scroll_to_bottom()

    def _finish_turn(self):
        self._status_label.setText("")
        self._send_btn.setEnabled(True)
        self._regenerate_btn.setEnabled(True)
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
        self._thread = None
        self._worker = None

    def _on_done(self, full_text: str, task_type: str):
        if self._current_bubble is not None and full_text:
            self._current_bubble.set_text(full_text)
        if full_text:
            self._store.add_message(self._conversation_id, "echo", full_text, task_type)
            if self._speak_checkbox.isChecked():
                get_speech_output().speak(full_text)
        self._status_label.setText(f"done ({task_type})" if task_type else "")
        self._finish_turn()

    def _on_speak_toggled(self, checked: bool):
        get_speech_output().set_enabled(checked)

    def _on_error(self, message: str):
        if self._current_bubble is not None:
            self._current_bubble.set_text(f"*Error: {message}*")
        self._status_label.setText("error")
        self._finish_turn()
