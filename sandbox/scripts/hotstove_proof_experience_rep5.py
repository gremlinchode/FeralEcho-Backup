import functools
from typing import Dict

_lcache: Dict[str, str] = {}

@functools.lru_cache(maxsize=None)
def expensive_lookup(key: str) -> str:
    if key in _lcache:
        return _lcache[key]
    result = f"computed {key} value"
    _lcache[key] = result
    return result