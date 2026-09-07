import functools
import hashlib

@functools.lru_cache(maxsize=None)
def expensive_lookup(key: str) -> str:
    value = f"transformed_{hashlib.sha256(key.encode()).hexdigest()}"
    return value