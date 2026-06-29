# app/core/council_registry.py
from typing import Dict

class CouncilRegistry:
    _instance = None

    def __init__(self):
        self.members: Dict[str, dict] = {}  # key=name, value={'type': str, 'shard': object}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, name: str, entity_type: str, shard=None):
        self.members[name] = {'type': entity_type, 'shard': shard}

    def list_members(self):
        return list(self.members.keys())

    def get_shard(self, name: str):
        return self.members.get(name, {}).get('shard')

