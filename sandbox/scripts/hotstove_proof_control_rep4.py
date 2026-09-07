import functools

@functools.lru_cache(maxsize=None)
def expensive_lookup(key: str) -> str:
    result = key[::-1].upper()
    return result