import functools
from collections import defaultdict

_expensive_cache = defaultdict(dict)

@functools.lru_cache(maxsize=None)
def expensive_lookup(key: str) -> str:
    if key not in _expensive_cache[key]:
        _expensive_cache[key][key] = f"transformed-{key}"
    return _expensive_cache[key].get(key, "")