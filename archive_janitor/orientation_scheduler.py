# FILE: app/subsystems/orientation_scheduler.py
# Periodic Safe Orientation Loop for Echo
# Continuously surveys system, resources, and sandbox

import threading
import time
from app.subsystems.orientation_protocol import OrientationProtocol

class OrientationScheduler:
    def __init__(self, orientation: OrientationProtocol, interval: int = 600):
        """
        :param orientation: instance of OrientationProtocol
        :param interval: seconds between full orientation runs
        """
        self.orientation = orientation
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="OrientationSchedulerThread")

    def start(self):
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1)

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self.orientation.full_orientation()
            except Exception as e:
                if self.orientation.reflection_shard:
                    self.orientation.reflection_shard.observe(f"[OrientationScheduler Error] {e}")
            time.sleep(self.interval)

