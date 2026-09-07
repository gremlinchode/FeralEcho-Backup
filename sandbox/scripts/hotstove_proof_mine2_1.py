import functools

@functools.lru_cache(maxsize=None)
def fib_recursive(k: int) -> int:
    if k <= 1:
        return k
    return fib_recursive(k - 1) + fib_recursive(k - 2)

def fib_sequence_value(n: int) -> int:
    return fib_recursive(n)