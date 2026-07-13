"""Project explorer: file tree, view files/logs/JSON/markdown. Read-only —
no rename/delete/write anywhere in this view. Strictly backed by
GET /projects/tree and GET /projects/file, which themselves validate every
path stays inside the repo root (see app/routes_echo_studio.py).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QLineEdit,
    QLabel,
    QSplitter,
    QPlainTextEdit,
)

from echo_studio.api_client import ApiClient
from echo_studio.state.local_store import LocalStore
from echo_studio.widgets.markdown_view import MarkdownView, render_markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound

_FORMATTER = HtmlFormatter(noclasses=True, style="monokai")


class _TreeFetchWorker(QObject):
    # path, entries, parent_item — parent_item travels with the signal
    # instead of being captured in a connect()-time lambda, so every
    # connection here can be a plain bound-method connection (see the
    # QThread::wait-on-itself note on _cleanup_sender below).
    result = Signal(str, list, object)
    error = Signal(str, object)

    def __init__(self, api: ApiClient, path: str, parent_item):
        super().__init__()
        self._api = api
        self._path = path
        self._parent_item = parent_item

    def run(self):
        try:
            payload = self._api.projects_tree(self._path)
            self.result.emit(self._path, payload.get("entries", []), self._parent_item)
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e), self._parent_item)


class _FileFetchWorker(QObject):
    result = Signal(str, str)  # path, content
    error = Signal(str)

    def __init__(self, api: ApiClient, path: str):
        super().__init__()
        self._api = api
        self._path = path

    def run(self):
        try:
            payload = self._api.projects_file(self._path)
            self.result.emit(self._path, payload.get("content", ""))
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))


def _render_file_html(path: str, content: str) -> str:
    if path.lower().endswith(".md"):
        return render_markdown(content)
    try:
        lexer = guess_lexer_for_filename(path, content)
    except ClassNotFound:
        escaped = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f'<pre style="white-space:pre-wrap;">{escaped}</pre>'
    return highlight(content, lexer, _FORMATTER)


class ProjectExplorerView(QWidget):
    def __init__(self, api: ApiClient, store: LocalStore, parent=None):
        super().__init__(parent)
        self._api = api
        self._store = store
        self._threads: list = []  # keep references alive until each finishes

        root = QVBoxLayout(self)

        filter_row = QHBoxLayout()
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filter visible tree items…")
        self._filter.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self._filter)
        root.addLayout(filter_row)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: palette(mid); font-style: italic;")
        root.addWidget(self._status_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemExpanded.connect(self._on_item_expanded)
        self._tree.itemDoubleClicked.connect(self._on_item_activated)
        splitter.addWidget(self._tree)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self._path_label = QLabel("")
        self._path_label.setStyleSheet("color: palette(mid); font-size: 11px;")
        right_layout.addWidget(self._path_label)
        self._viewer = MarkdownView()
        right_layout.addWidget(self._viewer, stretch=1)
        splitter.addWidget(right_panel)

        splitter.setSizes([260, 640])
        root.addWidget(splitter, stretch=1)

        self._load_root()

    def _load_root(self):
        self._tree.clear()
        self._fetch_tree("", None)

    def _fetch_tree(self, path: str, parent_item):
        self._status_label.setText("loading tree…")
        thread = QThread(self)
        worker = _TreeFetchWorker(self._api, path, parent_item)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.result.connect(self._on_tree_result)
        worker.error.connect(self._on_tree_error)
        self._threads.append((thread, worker))
        thread.start()

    def _cleanup_sender(self):
        """Finds the (thread, worker) pair whose worker emitted the signal
        currently being handled (self.sender()) and joins that thread.

        Only bound-method connections are used for anything that ends up
        here — a connect() to a lambda has no QObject of its own for Qt to
        determine thread affinity from, which previously caused a queued
        connection to instead run inline on the worker thread, producing
        "QThread::wait: Thread tried to wait on itself" when that inline
        call reached quit()/wait() on its own thread.
        """
        worker = self.sender()
        for t, w in list(self._threads):
            if w is worker:
                t.quit()
                t.wait()
                self._threads.remove((t, w))
        if not self._threads:
            self._status_label.setText("")

    def _on_tree_result(self, path: str, entries: list, parent_item):
        target = parent_item if parent_item is not None else self._tree.invisibleRootItem()
        for entry in entries:
            item = QTreeWidgetItem([entry["name"]])
            item.setData(0, Qt.ItemDataRole.UserRole, entry["path"])
            item.setData(0, Qt.ItemDataRole.UserRole + 1, entry["is_dir"])
            if entry["is_dir"]:
                # placeholder child so the expand arrow shows; replaced on first expand
                item.addChild(QTreeWidgetItem(["loading…"]))
            target.addChild(item)
        self._cleanup_sender()

    def _on_tree_error(self, message: str, _parent_item):
        self._status_label.setText(f"error: {message}")
        self._cleanup_sender()

    def _on_item_expanded(self, item: QTreeWidgetItem):
        is_dir = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if not is_dir:
            return
        # Only (re)fetch if still showing the placeholder child
        if item.childCount() == 1 and item.child(0).text(0) == "loading…":
            item.takeChildren()
            self._fetch_tree(item.data(0, Qt.ItemDataRole.UserRole), item)

    def _on_item_activated(self, item: QTreeWidgetItem, _column: int):
        is_dir = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if is_dir:
            item.setExpanded(not item.isExpanded())
            return
        path = item.data(0, Qt.ItemDataRole.UserRole)
        self._open_file(path)

    def open_file(self, path: str):
        """Public entry point — e.g. the sidebar's "Recent" tab jumps here."""
        self._open_file(path)

    def _open_file(self, path: str):
        self._status_label.setText(f"loading {path}…")
        thread = QThread(self)
        worker = _FileFetchWorker(self._api, path)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.result.connect(self._on_file_result)
        worker.error.connect(self._on_file_error)
        self._threads.append((thread, worker))
        thread.start()

    def _on_file_result(self, path: str, content: str):
        self._path_label.setText(path)
        html = _render_file_html(path, content)
        self._viewer.set_html_with_raw(html, content)
        self._store.record_recent_file(path)
        self._cleanup_sender()

    def _on_file_error(self, message: str):
        self._status_label.setText(f"error: {message}")
        self._cleanup_sender()

    def _apply_filter(self, text: str):
        text = text.lower().strip()

        def _match(item: QTreeWidgetItem) -> bool:
            child_visible = False
            for i in range(item.childCount()):
                if _match(item.child(i)):
                    child_visible = True
            self_match = text in item.text(0).lower()
            visible = self_match or child_visible or not text
            item.setHidden(not visible)
            return visible

        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            _match(root.child(i))
