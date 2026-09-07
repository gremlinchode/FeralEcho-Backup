import functools
@functools.lru_cache(maxsize=None)
def tri_rec(n):
    if n <= 0:
        return 0
    return n + tri_rec(n - 1)

def triangular_number(n: int) -> int:
    return tri_rec(n)