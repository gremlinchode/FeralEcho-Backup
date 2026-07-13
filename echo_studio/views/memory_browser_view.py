"""Memory browser: view + search persistent memory, vector memory, journals,
dream logs, council notes. Read-only — no edit affordance exists anywhere in
this view, per the project brief's explicit "never without confirmation"
rule. There is nothing to confirm yet because there is nothing to edit.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QSpinBox,
)

from echo_studio.api_client import ApiClient

_SOURCE_FILTERS = ["(any source)", "user_conversation", "autonomous", "dream"]
_PAGE_SIZE = 50


class _MemoryFetchWorker(QObject):
    result = Signal(dict)
    error = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn

    def run(self):
        try:
            self.result.emit(self._fn())
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))


class MemoryBrowserView(QWidget):
    def __init__(self, api: ApiClient, parent=None):
        super().__init__(parent)
        self._api = api
        self._thread: QThread | None = None
        self._page = 0

        root = QVBoxLayout(self)

        search_row = QHBoxLayout()
        self._query = QLineEdit()
        self._query.setPlaceholderText("Semantic search across memory (leave empty to browse all)…")
        self._query.returnPressed.connect(self._on_search)
        search_row.addWidget(self._query, stretch=1)

        self._source_box = QComboBox()
        self._source_box.addItems(_SOURCE_FILTERS)
        search_row.addWidget(self._source_box)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._on_search)
        search_row.addWidget(search_btn)

        browse_btn = QPushButton("Browse all")
        browse_btn.clicked.connect(self._on_browse)
        search_row.addWidget(browse_btn)
        root.addLayout(search_row)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: palette(mid); font-style: italic;")
        root.addWidget(self._status_label)

        self._list = QListWidget()
        self._list.setWordWrap(True)
        root.addWidget(self._list, stretch=1)

        page_row = QHBoxLayout()
        prev_btn = QPushButton("◀ Prev page")
        prev_btn.clicked.connect(self._prev_page)
        page_row.addWidget(prev_btn)
        self._page_label = QLabel("page 0")
        page_row.addWidget(self._page_label)
        next_btn = QPushButton("Next page ▶")
        next_btn.clicked.connect(self._next_page)
        page_row.addWidget(next_btn)
        page_row.addStretch(1)
        root.addLayout(page_row)

    def _source_filter(self):
        idx = self._source_box.currentIndex()
        return None if idx == 0 else _SOURCE_FILTERS[idx]

    def _on_search(self):
        query = self._query.text().strip()
        if not query:
            self._on_browse()
            return
        source = self._source_filter()
        self._run(lambda: self._api.memory_search(query, k=30, source=source), mode="search")

    def _on_browse(self):
        self._page = 0
        self._fetch_browse_page()

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._fetch_browse_page()

    def _next_page(self):
        self._page += 1
        self._fetch_browse_page()

    def _fetch_browse_page(self):
        source = self._source_filter()
        self._run(
            lambda: self._api.memory_browse(page=self._page, page_size=_PAGE_SIZE, source=source),
            mode="browse",
        )

    def _run(self, fn, mode: str):
        if self._thread is not None:
            return
        self._status_label.setText("loading…")
        # Stashed instead of captured in a connect()-time lambda: a lambda
        # has no QObject of its own for Qt to determine thread affinity
        # from, which previously turned a "queued" connection into an
        # inline call on the worker thread — see project_explorer_view.py's
        # _cleanup_sender docstring for the full explanation.
        self._pending_mode = mode
        self._thread = QThread(self)
        worker = _MemoryFetchWorker(fn)
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.result.connect(self._on_result)
        worker.error.connect(self._on_error)
        self._worker = worker
        self._thread.start()

    def _cleanup(self):
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
        self._thread = None

    def _on_result(self, payload: dict):
        mode = self._pending_mode
        self._list.clear()
        if mode == "search":
            results = payload.get("results", [])
            self._status_label.setText(f"{len(results)} results")
            for r in results:
                meta = r.get("meta", {})
                label = f"[{meta.get('memory_source', '?')}/{meta.get('role', '?')}] {r.get('text', '')[:200]}"
                item = QListWidgetItem(label)
                self._list.addItem(item)
            self._page_label.setText("search results")
        else:
            items = payload.get("items", [])
            total = payload.get("total", 0)
            self._status_label.setText(f"{total} total entries")
            for it in items:
                meta = it.get("meta", {})
                ts = meta.get("timestamp", "")[:19]
                label = f"[{ts}] [{meta.get('memory_source', '?')}/{meta.get('role', '?')}] {it.get('text', '')[:200]}"
                self._list.addItem(QListWidgetItem(label))
            self._page_label.setText(f"page {self._page}")
        self._cleanup()

    def _on_error(self, message: str):
        self._status_label.setText(f"error: {message}")
        self._cleanup()
