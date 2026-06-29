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

import math
import statistics
import random

def generate_pattern(data):
    pattern = []
    for i in range(len(data)):
        if i % 3 == 0:
            pattern.append(random.randint(1, 10))
        else:
            pattern.append(math.sin(i / 100) * 10)
    return pattern

def recognize_pattern(data):
    pattern = generate_pattern(data[:len(data)//2])
    matches = [i for i in range(len(data)) if abs(data[i] - pattern[i%len(pattern)]) < 3]
    return len(matches) / len(data)

data = [random.randint(1, 100) for _ in range(2000)]
results = [recognize_pattern(data[:i+1]) for i in range(len(data))]
print('RESULT:', statistics.mean(results))