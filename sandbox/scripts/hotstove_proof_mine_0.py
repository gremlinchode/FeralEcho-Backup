import functools
def cache(func):
    cache_dict = dict()
    @functools.wraps(func)
    def wrapper(n):
        if n not in cache_dict:
            cache_dict[n] = func(n)
        return cache_dict[n]
    return wrapper

@cache
def fib_sequence_value(n: int) -> int:
    if n <= 1:
        return n
    else:
        a, b = 0, 1
        for _ in range(2, n+1):
            a, b = b, a+b
        return b