import functools
from collections import defaultdict

cache = defaultdict(dict)

@functools.lru_cache(maxsize=None)
def expensive_lookup(key: str) -> str:
    if not cache[0].get(key):
        result = f"transformed_{key}"
        cache[0][key] = result
    return cache[0][key]