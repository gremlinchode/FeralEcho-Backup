# app/core/placeholder_ai.py

from .shard import Shard

class PlaceholderAI:
    def __init__(self, name: str):
        self.name = name
        self.shard = Shard(name)
        print(f"[PlaceholderAI] Initialized dummy AI module: {name}")

    def generate_response(self, prompt: str, **kwargs):
        """
        Mimics an AI response. Always returns a placeholder string.
        """
        print(f"[PlaceholderAI:{self.name}] Received prompt: {prompt}")
        return "This is a placeholder response."

    def train(self, *args, **kwargs):
        """
        Dummy train method to satisfy calls from other modules.
        """
        print(f"[PlaceholderAI:{self.name}] Dummy train method called.")

    def save(self, *args, **kwargs):
        """
        Dummy save method.
        """
        print(f"[PlaceholderAI:{self.name}] Dummy save method called.")

