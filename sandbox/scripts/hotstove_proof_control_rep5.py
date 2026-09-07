import functools
from typing import Dict

_cache: Dict[str, str] = {}

@functools.lru_cache(maxsize=None)
def expensive_lookup(key: str) -> str:
    if key not in _cache:
        result = f"The result for key {key}"
        _cache[key] = result
    return _cache[key]