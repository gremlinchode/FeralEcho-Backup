import functools

@functools.lru_cache(maxsize=None)
def expensive_lookup(key: str) -> str:
    return f"transformed_{key}"