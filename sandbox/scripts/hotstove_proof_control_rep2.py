import functools

_cache: Dict[str, str] = {}

@functools.lru_cache(maxsize=None)
def expensive_lookup(key: str) -> str:
    if key not in _cache:
        # simulate costly string transformation
        transformed_key = f"transformed-{key}"
        _cache[key] = transformed_key
    return _cache[key]