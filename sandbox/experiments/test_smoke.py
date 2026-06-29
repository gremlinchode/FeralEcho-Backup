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

result = sum(range(10))
print(f"RESULT: {result}")
