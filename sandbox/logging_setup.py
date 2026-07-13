import logging
import os
import sys

# Ensure logs directory exists
LOG_FILE = os.path.join(os.path.dirname(__file__), "../logs/sandbox_execution.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Create named logger
logger = logging.getLogger("sandbox")
logger.setLevel(logging.DEBUG)


def _ensure_handlers():
    """(Re-)install handlers if the logger currently has none.

    Previously this setup ran once at module import time only (`if not
    logger.handlers:` at the top level) — but runner.py's close_handlers()
    is called in a `finally:` block after every sandbox run, and closing +
    removing the handlers there left nothing to ever re-add them. Since the
    setup block only executed once per process (module-level code, cached
    in sys.modules on re-import), every sandbox run after the first in a
    given server session logged into a handler-less logger — silent, no
    error, just gone. Called from every log_* wrapper below so handlers are
    re-established on next use regardless of how many times close_handlers()
    has fired.
    """
    if not logger.handlers:
        # Console handler (for real-time feedback)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
        ch.setFormatter(ch_formatter)
        logger.addHandler(ch)

        # File handler (for archival logging)
        fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)


_ensure_handlers()

# Graceful shutdown hook
def close_handlers():
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

# Convenience wrappers
def log_info(message: str):
    _ensure_handlers()
    logger.info(message)
def log_debug(message: str):
    _ensure_handlers()
    logger.debug(message)
def log_warning(message: str):
    _ensure_handlers()
    logger.warning(message)
def log_error(message: str):
    _ensure_handlers()
    logger.error(message)
def log_exception(exc: Exception):
    _ensure_handlers()
    logger.exception(f"Exception: {exc}")

# Expose the logger directly
log = logger

