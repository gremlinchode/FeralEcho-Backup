@functools.lru_cache(maxsize=None)
def _recursive_triangular_number(n: int) -> int:
    if n == 0:
        return 0
    else:
        return n + _recursive_triangular_number(n - 1)

def triangular_number(n: int) -> int:
    return _recursive_triangular_number(n)