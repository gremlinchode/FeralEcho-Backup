"""Sidebar: conversation list + search, saved prompts, recent files.

Phase 2 scope. Memory browser and project explorer get their own top-level
nav entries (see main.py) rather than living inside this sidebar — they're
full views, not lists of things to jump into a conversation with.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QTabWidget,
    QInputDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt

from echo_studio.state.local_store import LocalStore


class _ConversationsTab(QWidget):
    conversation_selected = Signal(str)
    new_conversation_requested = Signal()
    conversation_deleted = Signal(str)

    def __init__(self, store: LocalStore, parent=None):
        super().__init__(parent)
        self._store = store
        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search conversations…")
        self._search.textChanged.connect(self._on_search)
        top_row.addWidget(self._search)
        new_btn = QPushButton("New")
        new_btn.setFixedWidth(50)
        new_btn.clicked.connect(self.new_conversation_requested.emit)
        top_row.addWidget(new_btn)
        layout.addLayout(top_row)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_item_activated)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        delete_action = self._list.addAction("Delete")
        delete_action.triggered.connect(self._delete_selected)
        layout.addWidget(self._list, stretch=1)

        self.refresh()

    def refresh(self):
        self._list.clear()
        for conv in self._store.list_conversations():
            item = QListWidgetItem(conv["title"] or "(untitled)")
            item.setData(Qt.ItemDataRole.UserRole, conv["id"])
            self._list.addItem(item)

    def _on_search(self, text: str):
        if not text.strip():
            self.refresh()
            return
        self._list.clear()
        for conv in self._store.search_conversations(text.strip()):
            item = QListWidgetItem(conv["title"] or "(untitled)")
            item.setData(Qt.ItemDataRole.UserRole, conv["id"])
            self._list.addItem(item)

    def _on_item_activated(self, item: QListWidgetItem):
        self.conversation_selected.emit(item.data(Qt.ItemDataRole.UserRole))

    def _delete_selected(self):
        item = self._list.currentItem()
        if item is None:
            return
        conv_id = item.data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(
            self, "Delete conversation", f"Delete '{item.text()}'? This cannot be undone locally."
        ) == QMessageBox.StandardButton.Yes:
            self._store.delete_conversation(conv_id)
            self.conversation_deleted.emit(conv_id)
            self.refresh()


class _SavedPromptsTab(QWidget):
    prompt_selected = Signal(str)

    def __init__(self, store: LocalStore, parent=None):
        super().__init__(parent)
        self._store = store
        layout = QVBoxLayout(self)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_item_activated)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        delete_action = self._list.addAction("Delete")
        delete_action.triggered.connect(self._delete_selected)
        layout.addWidget(self._list, stretch=1)

        hint = QLabel("Double-click to insert into composer")
        hint.setStyleSheet("color: palette(mid); font-size: 11px;")
        layout.addWidget(hint)

        self.refresh()

    def refresh(self):
        self._list.clear()
        for p in self._store.list_saved_prompts():
            item = QListWidgetItem(p["title"])
            item.setData(Qt.ItemDataRole.UserRole, p["text"])
            item.setData(Qt.ItemDataRole.UserRole + 1, p["id"])
            self._list.addItem(item)

    def _on_item_activated(self, item: QListWidgetItem):
        self.prompt_selected.emit(item.data(Qt.ItemDataRole.UserRole))

    def _delete_selected(self):
        item = self._list.currentItem()
        if item is None:
            return
        self._store.delete_saved_prompt(item.data(Qt.ItemDataRole.UserRole + 1))
        self.refresh()

    def add_prompt_dialog(self, default_text: str = ""):
        title, ok = QInputDialog.getText(self, "Save prompt", "Title:")
        if not ok or not title.strip():
            return
        self._store.save_prompt(title.strip(), default_text)
        self.refresh()


class _RecentFilesTab(QWidget):
    file_selected = Signal(str)

    def __init__(self, store: LocalStore, parent=None):
        super().__init__(parent)
        self._store = store
        layout = QVBoxLayout(self)
        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(
            lambda item: self.file_selected.emit(item.data(Qt.ItemDataRole.UserRole))
        )
        layout.addWidget(self._list, stretch=1)
        self.refresh()

    def refresh(self):
        self._list.clear()
        for f in self._store.list_recent_files():
            item = QListWidgetItem(f["path"])
            item.setData(Qt.ItemDataRole.UserRole, f["path"])
            self._list.addItem(item)


class Sidebar(QWidget):
    conversation_selected = Signal(str)
    new_conversation_requested = Signal()
    conversation_deleted = Signal(str)
    prompt_selected = Signal(str)
    file_selected = Signal(str)

    def __init__(self, store: LocalStore, parent=None):
        super().__init__(parent)
        self._store = store
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        tabs = QTabWidget()
        self.conversations_tab = _ConversationsTab(store)
        self.saved_prompts_tab = _SavedPromptsTab(store)
        self.recent_files_tab = _RecentFilesTab(store)

        tabs.addTab(self.conversations_tab, "Chats")
        tabs.addTab(self.saved_prompts_tab, "Prompts")
        tabs.addTab(self.recent_files_tab, "Recent")

        layout.addWidget(tabs)

        self.conversations_tab.conversation_selected.connect(self.conversation_selected.emit)
        self.conversations_tab.new_conversation_requested.connect(self.new_conversation_requested.emit)
        self.conversations_tab.conversation_deleted.connect(self.conversation_deleted.emit)
        self.saved_prompts_tab.prompt_selected.connect(self.prompt_selected.emit)
        self.recent_files_tab.file_selected.connect(self.file_selected.emit)

    def refresh_conversations(self):
        self.conversations_tab.refresh()

    def refresh_recent_files(self):
        self.recent_files_tab.refresh()

    def prompt_save_dialog(self, default_text: str = ""):
        self.saved_prompts_tab.add_prompt_dialog(default_text)
