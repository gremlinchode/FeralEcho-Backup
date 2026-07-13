#!/usr/bin/env python3
"""Echo Studio — desktop entry point.

A local, ChatGPT-like GUI for the existing FeralEcho backend. This process
never imports app.core or anything from the FeralEcho backend directly — all
backend access goes through echo_studio/api_client.py over HTTP/SSE. Run the
FeralEcho Flask server (`python run.py`) first; this app is a separate client.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QStackedWidget,
    QPushButton,
    QButtonGroup,
)

from echo_studio.api_client import ApiClient, DEFAULT_BASE_URL
from echo_studio.state.local_store import LocalStore
from echo_studio.views.conversation_view import ConversationView
from echo_studio.views.health_dashboard_view import HealthDashboardView
from echo_studio.views.sidebar import Sidebar
from echo_studio.views.memory_browser_view import MemoryBrowserView
from echo_studio.views.activity_view import ActivityView
from echo_studio.views.project_explorer_view import ProjectExplorerView
from echo_studio.views.settings_view import SettingsView

_NAV_ITEMS = ["Chat", "Memory", "Activity", "Projects", "Settings"]


class EchoStudioMainWindow(QMainWindow):
    def __init__(self, api: ApiClient, store: LocalStore):
        super().__init__()
        self.setWindowTitle("Echo Studio")
        self.resize(1200, 800)

        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._health = HealthDashboardView(api)
        outer.addWidget(self._health)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)

        # --- left nav (top-level view switcher) --------------------------
        nav_col = QVBoxLayout()
        nav_col.setContentsMargins(4, 8, 4, 8)
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        nav_buttons = []
        for i, label in enumerate(_NAV_ITEMS):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setMinimumWidth(90)
            nav_col.addWidget(btn)
            self._nav_group.addButton(btn, i)
            nav_buttons.append(btn)
        nav_buttons[0].setChecked(True)
        nav_col.addStretch(1)
        nav_widget = QWidget()
        nav_widget.setLayout(nav_col)
        nav_widget.setFixedWidth(110)
        body.addWidget(nav_widget)

        # --- stacked pages -------------------------------------------------
        self._stack = QStackedWidget()

        # Page 0: Chat = sidebar + conversation view
        chat_page = QWidget()
        chat_layout = QHBoxLayout(chat_page)
        chat_layout.setContentsMargins(0, 0, 0, 0)

        self._sidebar = Sidebar(store)
        self._sidebar.setFixedWidth(220)
        chat_layout.addWidget(self._sidebar)

        self._conversation = ConversationView(api, store)
        chat_layout.addWidget(self._conversation, stretch=1)

        self._stack.addWidget(chat_page)                       # index 0
        self._memory = MemoryBrowserView(api)
        self._stack.addWidget(self._memory)                    # index 1
        self._activity = ActivityView(api)
        self._stack.addWidget(self._activity)                  # index 2
        self._projects = ProjectExplorerView(api, store)
        self._stack.addWidget(self._projects)                  # index 3
        self._settings = SettingsView(api)
        self._stack.addWidget(self._settings)                  # index 4

        body.addWidget(self._stack, stretch=1)
        outer.addLayout(body, stretch=1)

        self.setCentralWidget(central)

        self._nav_group.idClicked.connect(self._stack.setCurrentIndex)

        # --- cross-view wiring ----------------------------------------------
        self._sidebar.conversation_selected.connect(self._conversation.load_conversation)
        self._sidebar.new_conversation_requested.connect(self._conversation.start_new_conversation)
        self._sidebar.conversation_deleted.connect(self._on_conversation_deleted)
        self._sidebar.prompt_selected.connect(self._conversation.insert_prompt_text)
        self._sidebar.file_selected.connect(self._open_file_in_projects)

        self._conversation.conversation_created.connect(lambda _id: self._sidebar.refresh_conversations())
        self._conversation.title_changed.connect(lambda _id, _title: self._sidebar.refresh_conversations())
        self._conversation.save_prompt_requested.connect(self._sidebar.prompt_save_dialog)

        self._sidebar.refresh_conversations()

    def _on_conversation_deleted(self, conversation_id: str):
        if self._conversation.conversation_id() == conversation_id:
            self._conversation.start_new_conversation()

    def _open_file_in_projects(self, path: str):
        self._nav_group.button(3).setChecked(True)
        self._stack.setCurrentIndex(3)
        self._projects.open_file(path)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Echo Studio")
    api = ApiClient(DEFAULT_BASE_URL)
    store = LocalStore()
    window = EchoStudioMainWindow(api, store)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
