# app/core/shard.py
import time
import threading
import random
import logging

class Shard:
    def __init__(self, owner_name):
        self.owner = owner_name
        self.memory: list = []
        self.growth_factor = 1.0  # increases over time
        self.lock = threading.Lock()

    def absorb(self, observation: str):
        with self.lock:
            self.memory.append(observation)
            self.growth_factor *= 1 + random.uniform(0.001, 0.01)
            logging.info(f"[Shard-{self.owner}] Absorbed: {observation[:60]} | Growth: {self.growth_factor:.3f}")

    def reflect(self, n=5):
        with self.lock:
            sample = self.memory[-n:]
            reflection = f"[Shard-{self.owner}] Reflection: " + " | ".join(sample)
            return reflection

    def evolve(self):
        # Example: periodic autonomous growth
        while True:
            with self.lock:
                self.growth_factor *= 1.001
            time.sleep(60)

