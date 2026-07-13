"""Echo Studio's only connection to the FeralEcho backend.

This module is the sole place in echo_studio/ allowed to know the Flask base
URL or talk HTTP to it. Everything else in the app goes through here — no
other module under echo_studio/ should import `requests`, `app.core`, or
anything from the FeralEcho backend directly. (Verify with:
`grep -rn "^from app\\|^import app" echo_studio/` — should return nothing.)

Plain `requests` + manual SSE line parsing is used instead of a dedicated SSE
client library or flask-socketio, to avoid adding dependencies the backend
doesn't already need (see EchoStudio_Design.md).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Optional

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:5000"


@dataclass
class ChatEvent:
    type: str            # "status" | "token" | "done" | "error"
    text: str = ""
    status: str = ""
    task_type: str = ""
    conversation_id: str = ""


class EchoStudioAPIError(Exception):
    pass


class ApiClient:
    """Thin HTTP/SSE client for the Echo Studio backend routes.

    Every method here corresponds 1:1 to a route added in
    app/routes_echo_studio.py (or an existing FeralEcho endpoint being
    reused as-is) — no client-side business logic lives here.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    def get_health(self) -> dict:
        """GET /dashboard/health — see app/routes_echo_studio.py:dashboard_health."""
        resp = requests.get(f"{self.base_url}/dashboard/health", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------
    def stream_chat(
        self,
        conversation_id: str,
        message: str,
        mode: str = "full",
        on_event: Optional[Callable[[ChatEvent], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None,
    ) -> None:
        """POST /chat/stream and call on_event(ChatEvent) for each SSE line.

        Blocking — intended to be run from a worker thread (see
        echo_studio/views/conversation_view.py's ChatStreamWorker), never
        directly on the Qt main thread.

        should_stop: optional callable polled between chunks; if it returns
        True the connection is closed and streaming stops (used for a future
        "stop generating" affordance — safe to leave unset for now).
        """
        payload = {
            "conversation_id": conversation_id,
            "message": message,
            "mode": mode,
        }
        with requests.post(
            f"{self.base_url}/chat/stream",
            json=payload,
            stream=True,
            timeout=(self.timeout, 300),  # long read timeout — full-mode deliberation can be slow
        ) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines(decode_unicode=True):
                if should_stop and should_stop():
                    return
                if not raw_line:
                    continue
                if not raw_line.startswith("data: "):
                    continue
                try:
                    data = json.loads(raw_line[len("data: "):])
                except json.JSONDecodeError:
                    continue
                event = ChatEvent(
                    type=data.get("type", ""),
                    text=data.get("text", ""),
                    status=data.get("status", ""),
                    task_type=data.get("task_type", ""),
                    conversation_id=data.get("conversation_id", conversation_id),
                )
                if on_event:
                    on_event(event)
                if event.type == "done":
                    return

    def regenerate_chat(
        self,
        conversation_id: str,
        mode: str = "full",
        on_event: Optional[Callable[[ChatEvent], None]] = None,
    ) -> None:
        """POST /chat/regenerate — re-runs the last turn. Same event shape as
        stream_chat; see app/routes_echo_studio.py:chat_regenerate."""
        payload = {"conversation_id": conversation_id, "mode": mode}
        with requests.post(
            f"{self.base_url}/chat/regenerate",
            json=payload,
            stream=True,
            timeout=(self.timeout, 300),
        ) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines(decode_unicode=True):
                if not raw_line or not raw_line.startswith("data: "):
                    continue
                try:
                    data = json.loads(raw_line[len("data: "):])
                except json.JSONDecodeError:
                    continue
                event = ChatEvent(
                    type=data.get("type", ""),
                    text=data.get("text", ""),
                    status=data.get("status", ""),
                    task_type=data.get("task_type", ""),
                    conversation_id=data.get("conversation_id", conversation_id),
                )
                if on_event:
                    on_event(event)
                if event.type == "done":
                    return

    # ------------------------------------------------------------------
    # Memory browser (Phase 3) — read-only
    # ------------------------------------------------------------------
    def memory_search(self, query: str, k: int = 10, source: Optional[str] = None) -> dict:
        params = {"q": query, "k": k}
        if source:
            params["source"] = source
        resp = requests.get(f"{self.base_url}/memory/search", params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def memory_browse(self, page: int = 0, page_size: int = 50, source: Optional[str] = None) -> dict:
        params = {"page": page, "page_size": page_size}
        if source:
            params["source"] = source
        resp = requests.get(f"{self.base_url}/memory/browse", params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Background activity (Phase 4) — read-only
    # ------------------------------------------------------------------
    def activity_log(self, limit: int = 100) -> dict:
        resp = requests.get(
            f"{self.base_url}/activity/log", params={"limit": limit}, timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Project explorer (Phase 5) — read-only
    # ------------------------------------------------------------------
    def projects_tree(self, path: str = "") -> dict:
        resp = requests.get(
            f"{self.base_url}/projects/tree", params={"path": path}, timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()

    def projects_file(self, path: str) -> dict:
        resp = requests.get(
            f"{self.base_url}/projects/file", params={"path": path}, timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Settings (Phase 6) — read-only
    # ------------------------------------------------------------------
    def settings_view(self) -> dict:
        resp = requests.get(f"{self.base_url}/settings/view", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()
