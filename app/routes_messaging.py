"""M5 <-> Air messaging routes.

Thin Flask handlers over app/sync/echo_messaging.py — no business logic
here, same "logic lives in a dedicated module, run.py only registers"
pattern as app/routes_echo_studio.py.

Not on EDIT_FORBIDDEN_TARGETS — freely editable.
"""

import hmac
import logging
import os

from flask import request, jsonify

from app.sync import echo_messaging

logger = logging.getLogger("echo_messaging_routes")

# run.py's GREMLIN_SECRET / _secret_ok() aren't importable here without a
# circular import (run.py imports this module to register routes), so this
# is a small independent copy of the same fail-closed comparison logic.
_GREMLIN_SECRET = os.environ.get("GREMLIN_SECRET")


def _secret_ok(payload: dict) -> bool:
    if not _GREMLIN_SECRET:
        return False
    submitted = (payload or {}).get("secret")
    if not submitted:
        return False
    return hmac.compare_digest(str(submitted), str(_GREMLIN_SECRET))


# Separate shared M5<->Air secret for /message/receive — GREMLIN_SECRET is
# generated independently per instance (Finding 14) and can't authenticate
# the sibling relationship itself, which is why this endpoint previously had
# only the weak origin-string check below. ECHO_PARTNER_SECRET must be the
# same value in both M5's and Air's .env for this to pass real cross-machine
# delivery once both sides carry the code that sends it (echo_messaging.py's
# _build_envelope()).
_PARTNER_SECRET = os.environ.get("ECHO_PARTNER_SECRET")


def _partner_secret_ok(payload: dict) -> bool:
    if not _PARTNER_SECRET:
        return False
    submitted = (payload or {}).get("secret")
    if not submitted:
        return False
    return hmac.compare_digest(str(submitted), str(_PARTNER_SECRET))


# Known partner origins for /message/receive — kept as a second, independent
# check alongside _partner_secret_ok() (defense in depth) rather than
# replaced by it.
_KNOWN_PARTNER_ORIGINS = {"air", "m5"}


def message_receive():
    """POST /message/receive — the partner machine delivers a message here."""
    try:
        payload = request.json or {}
        origin = str(payload.get("origin", "")).lower()
        if origin not in _KNOWN_PARTNER_ORIGINS:
            return jsonify({"error": "unauthorized"}), 403
        if not _partner_secret_ok(payload):
            return jsonify({"error": "unauthorized"}), 403
        result = echo_messaging.receive_message(payload)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"[/message/receive] {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def message_send():
    """POST /message/send — ask this machine to send a message to the partner
    Echo instance. Body: {text, message_type}.

    Intentionally unauthenticated: Gremlin confirmed 2026-07-15 (CLAUDE.md
    Finding 29) that Echo-to-Echo communication over Tailscale should be
    open, not gated by GREMLIN_SECRET. The Tailscale network boundary is
    the access control here, same as the read-only /admin/* surface — this
    route was never actually "local-only", that was a stale docstring."""
    try:
        data = request.json or {}
        text = data.get("text", "")
        message_type = data.get("message_type", "chat")
        result = echo_messaging.send_message(text, message_type=message_type)
        status_code = 400 if result.get("status") == "error" else 200
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"[/message/send] {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def message_inbox():
    """GET /message/inbox?limit=50 — recent messages, both directions."""
    try:
        limit = int(request.args.get("limit", 50))
        return jsonify({"messages": echo_messaging.get_recent_messages(limit)}), 200
    except Exception as e:
        logger.error(f"[/message/inbox] {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def message_settings():
    """GET/POST /message/settings — view or update auto_respond and/or
    auto_checkin_enabled.

    The one deliberate write surface in this feature, narrowly scoped to
    these two booleans — not a general settings editor.
    """
    try:
        if request.method == "POST":
            data = request.json or {}
            if not _secret_ok(data):
                return jsonify({"error": "unauthorized"}), 403
            if "auto_respond" not in data and "auto_checkin_enabled" not in data:
                return jsonify({"error": "auto_respond and/or auto_checkin_enabled required"}), 400
            settings = echo_messaging.get_settings()
            if "auto_respond" in data:
                settings = echo_messaging.set_auto_respond(bool(data["auto_respond"]))
            if "auto_checkin_enabled" in data:
                settings = echo_messaging.set_auto_checkin_enabled(bool(data["auto_checkin_enabled"]))
            return jsonify(settings), 200
        return jsonify(echo_messaging.get_settings()), 200
    except Exception as e:
        logger.error(f"[/message/settings] {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
