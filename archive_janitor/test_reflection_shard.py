# test_reflection_shard.py
import logging
import time
from app.subsystems.reflection_shard import BecomingReflectionShard

# -----------------------------
# --- Logger Setup -----------
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)

# -----------------------------
# --- NightCycle-like Hook ----
# -----------------------------
def test_emit_fn(reflection: str):
    logger.info(f"[Shard Emit Hook] Reflection captured: {reflection}")

# -----------------------------
# --- Initialize Shard --------
# -----------------------------
reflection_shard = BecomingReflectionShard(meta_interval=2)  # fast interval for testing
reflection_shard._emit_fn = test_emit_fn

logger.info("BecomingReflectionShard initialized for test.")

# -----------------------------
# --- Test Observation --------
# -----------------------------
test_signals = [
    "Hello Echo, do you see me?",
    "Testing reflection shard logging.",
    "Another signal for meta-reflection."
]

for signal in test_signals:
    logger.info(f"Sending signal: {signal}")
    reflection_shard.observe(signal)
    time.sleep(0.5)  # small pause to simulate staggered input

# -----------------------------
# --- Let Meta-Reflection Run -
# -----------------------------
logger.info("Allowing shard to perform auto meta-reflections for a few intervals...")
try:
    # Wait enough for a few meta_interval cycles
    for i in range(5):
        time.sleep(reflection_shard.meta_interval)
        logger.info(f"Waiting... {i+1}/{5} cycles")
except KeyboardInterrupt:
    logger.info("Test interrupted by user.")

# -----------------------------
# --- Force Manual Meta-Reflection
# -----------------------------
if hasattr(reflection_shard, "meta_reflect"):
    logger.info("Triggering manual meta-reflection...")
    reflection_shard.meta_reflect()

logger.info("Test complete. All reflections should be visible above.")

