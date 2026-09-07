import functools
import time
import hashlib

def cached_result(ttl_seconds=3600):
    cache = {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(a, b):
            key = f"{hashlib.sha256((a + b).encode()).hexdigest()}"
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    return result
            result = func(a, b)
            cache[key] = (result, time.time())
            return result
        
        return wrapper
    
    return decorator

@cached_result()
def levenshtein(a: str, b: str) -> int:
    m, n = len(a), len(b)
    dp = [[0 for _ in range(n + 1)] for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                cost = 0
            else:
                cost = 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)

    return dp[m][n]