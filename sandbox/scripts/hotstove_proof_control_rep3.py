import functools
from typing import Dict

_cache: Dict[str, str] = {}

@functools.lru_cache(maxsize=None)
def expensive_lookup(key: str) -> str:
    if key in _cache:
        return _cache[key]
    result = f"The {key} lookup is quite expensive!"
    _cache[key] = result
    return result