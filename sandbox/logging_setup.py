import logging
import os
import sys

# Ensure logs directory exists
LOG_FILE = os.path.join(os.path.dirname(__file__), "../logs/sandbox_execution.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Create named logger
logger = logging.getLogger("sandbox")
logger.setLevel(logging.DEBUG)

# Avoid duplicate handlers if re-imported
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

# Graceful shutdown hook
def close_handlers():
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

# Convenience wrappers
def log_info(message: str): logger.info(message)
def log_debug(message: str): logger.debug(message)
def log_warning(message: str): logger.warning(message)
def log_error(message: str): logger.error(message)
def log_exception(exc: Exception): logger.exception(f"Exception: {exc}")

# Expose the logger directly
log = logger

