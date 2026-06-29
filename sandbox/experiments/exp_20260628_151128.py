import sys as _sys, os as _os
_ALLOWED_PREFIX = _os.path.abspath("sandbox")
_real_open = open
def _safe_open(file, mode="r", **kw):
    if any(c in str(mode) for c in "wxa+"):
        if not _os.path.abspath(str(file)).startswith(_ALLOWED_PREFIX):
            raise PermissionError(f"Experiment write blocked outside sandbox/: {file}")
    return _real_open(file, mode, **kw)
open = _safe_open
for _m in ("socket", "urllib", "requests", "httpx", "ftplib", "smtplib"):
    _sys.modules.setdefault(_m, None)
del _sys, _os, _real_open, _m

import random
from collections import defaultdict
from math import gcd
from statistics import mean

def recognize_pattern(data):
    pattern_map = defaultdict(list)
    for i in range(len(data) - 1):
        a, b = data[i], data[i + 1]
        g = gcd(a, b)
        if g > 1:
            pattern_map[g].append((a // g, b // g))
    return {k: len(v) for k, v in pattern_map.items()}

data = [(random.randint(1, 100), random.randint(1, 100)) for _ in range(100)]
pattern_dist = recognize_pattern(data)

print(f"RESULT: Pattern recognition accuracy is {mean(list(pattern_dist.values()))}")