import functools

@functools.lru_cache(maxsize=None)
def digit_sum_cached(n: int) -> int:
    return sum(int(digit) for digit in str(abs(n)))