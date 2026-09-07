from functools import lru_cache

@lru_cache(maxsize=None)
def expensive_lookup(key: str) -> str:
    transformed_key = key.upper() + "_TRANSFORMED"
    return transformed_key