"""Shared constants and tiny helpers (stdlib only). Imported by every AP-0 module, including the jailed arm runner."""
import hashlib, json, os
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
EXP_ROOT = Path(os.environ.get("AP0_ROOT", str(REPO / "memory" / "experiments" / "accumulation_probe")))
OLLAMA_URL = os.environ.get("AP0_OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = "qwen2.5-coder:7b"
PYTHON = "/Users/richietate/miniforge3/envs/feral_echo/bin/python3"
MASTER_SEED = 20260921
N_SAMPLES = 3
N_SHARDS = 6
OPTIONS = {"temperature": 0.2, "top_p": 1.0, "num_predict": 512, "num_ctx": 4096, "repeat_penalty": 1.0}
CALL_TIMEOUT_S = 600
SANDBOX_TIMEOUT_S = 20
ARMS = ["N", "N2", "NEUTRAL", "MISMATCH", "H", "H2", "E", "IC"]

def sha256_bytes(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def sha256_text(s: str) -> str: return sha256_bytes(s.encode("utf-8"))
def sha256_file(p) -> str: return sha256_bytes(Path(p).read_bytes())
def canon(obj) -> str: return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
def sha256_obj(obj) -> str: return sha256_text(canon(obj))
def seed_for(replicate: str, task_id: str, sample: int) -> int:
    """Matched seeds: the same (replicate, task, sample) gets the same seed in every arm."""
    return int(sha256_text(f"AP0|{MASTER_SEED}|{replicate}|{task_id}|{sample}")[:8], 16) % (2 ** 31 - 1)
def read_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def write_json_new(p, obj):
    """Write a NEW file (refuse to overwrite: frozen artifacts are immutable)."""
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "x", encoding="utf-8") as f: f.write(json.dumps(obj, indent=1, sort_keys=True))
def append_jsonl(p, row):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f: f.write(canon(row) + "\n")
def read_jsonl(p):
    p = Path(p)
    if not p.exists(): return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
