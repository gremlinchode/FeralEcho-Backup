import functools

@functools.lru_cache(max_size=None)
def prime_factor_count(n: int) -> int:
    def is_prime(k: int) -> bool:
        if k < 2:
            return False
        for i in range(2, int(k ** 0.5) + 1):
            if k % i == 0:
                return False
        return True

    count = 0
    i = 2
    while n > 1:
        if n % i == 0:
            if is_prime(i):
                count += 1
            while n % i == 0:
                n //= i
        i += 1
    return count