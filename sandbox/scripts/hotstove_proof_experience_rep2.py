from functools import lru_cache

@lru_cache(maxsize=None)
def expensive_lookup(key: str) -> str:
    pass  # implement your logic here