"""Markdown + syntax-highlighted code rendering widget.

Renders markdown to HTML via markdown-it-py, running fenced code blocks
through Pygments (inline styles, no external stylesheet — Qt's rich-text
engine doesn't reliably resolve CSS classes) so it displays correctly inside
a plain QTextBrowser.
"""

from __future__ import annotations

from PySide6.QtWidgets import QTextBrowser, QMessageBox
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

_FORMATTER = HtmlFormatter(noclasses=True, style="monokai", nowrap=False)


def _highlight_code(code: str, lang: str, _attrs: str) -> str:
    lexer = None
    if lang:
        try:
            lexer = get_lexer_by_name(lang)
        except ClassNotFound:
            lexer = None
    if lexer is None:
        try:
            lexer = guess_lexer(code)
        except ClassNotFound:
            lexer = None
    if lexer is None:
        escaped = (
            code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        return (
            '<pre style="background:#272822;color:#f8f8f2;padding:8px;'
            f'border-radius:4px;"><code>{escaped}</code></pre>'
        )
    return highlight(code, lexer, _FORMATTER)


_MD = MarkdownIt("commonmark", {"html": False, "highlight": _highlight_code}).enable(
    "table"
)


def render_markdown(text: str) -> str:
    return _MD.render(text)


class MarkdownView(QTextBrowser):
    """Read-only rich-text view for a single rendered markdown block."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        # Rendered content here can come from memory/file/model-generated
        # text — including content potentially influenced by the
        # unauthenticated write endpoints closed in Batch 0 — so
        # auto-opening any clicked link via the OS URL handler was one
        # crafted link away from opening whatever ended up in regurgitated
        # memory. Require explicit confirmation instead.
        self.setOpenExternalLinks(False)
        self.anchorClicked.connect(self._confirm_and_open_link)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self.setFrameStyle(0)
        self._raw_text = ""

    def _confirm_and_open_link(self, url: QUrl) -> None:
        reply = QMessageBox.question(
            self,
            "Open link?",
            f"Open this link in your default browser?\n\n{url.toString()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(url)

    def set_markdown(self, text: str) -> None:
        self._raw_text = text
        self.setHtml(render_markdown(text))

    def set_html_with_raw(self, html: str, raw_text: str) -> None:
        """For callers (e.g. the project explorer) that already have
        rendered HTML — e.g. Pygments-highlighted source — and just want
        raw_text() to return the original content for copy, without
        re-interpreting it as markdown."""
        self._raw_text = raw_text
        self.setHtml(html)

    def raw_text(self) -> str:
        return self._raw_text
