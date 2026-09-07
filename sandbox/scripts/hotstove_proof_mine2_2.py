@functools.lru_cache(maxsize=None)
def expensive_lookup(key: str) -> str:
    # Simulate a costly string transformation
    transformed_key = key.upper() + "_EXPENSIVE"
    return transformed_key