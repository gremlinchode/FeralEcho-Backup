# import functools

def expensive_lookup(key: str) -> str:
    # Simulate a costly string transformation
    result = key.upper()  # Placeholder for actual computation
    return result

# Apply caching decorator
@functools.lru_cache(maxsize=None)
def cached_expensive_lookup(key: str) -> str:
    return expensive_lookup(key)

# Top-level function to apply to code
def apply_to_code(code: str) -> str:
    # Replace the original function with the cached version
    modified_code = code.replace('expensive_lookup', 'cached_expensive_lookup')
    return modified_code