# Hardware Ceiling — FeralEcho / Echo, Current Machine Only

Zero-cost investigation: what does the machine actually running Echo support, and is Echo extracting
it? All figures below are direct measurements taken live on this machine during this investigation
(`sysctl`, `system_profiler`, `df`, `ollama show`, `ollama ps`), not spec-sheet numbers.

## Real, measured specs

| Property | Value | Source |
|---|---|---|
| Chip | Apple M5 (`Mac17,3`) | `sysctl -n machdep.cpu.brand_string` |
| CPU cores | 10 total — 4 performance + 6 efficiency | `sysctl hw.perflevel{0,1}.physicalcpu` |
| GPU cores | 10, Metal 4 | `system_profiler SPDisplaysDataType` |
| Unified memory | 24 GB | `sysctl hw.memsize` |
| Disk | 926 GB total, 706 GB free (3% used) | `df -h /` |
| Swap in use | 5.19 GB of 6 GB configured swap | `sysctl vm.swapusage` |
| Load average (steady state) | 1.33 / 1.47 / 1.63 (10-core box) | `uptime` |
| Thermal state | No warning recorded | `pmset -g therm` |
| Ollama version | 0.30.10 | `ollama --version` |

**FACT, not previously documented anywhere in this codebase's own history**: this is an Apple **M5**
machine, not the M1 Pro referenced by an old, stale image artifact surfaced earlier in this
conversation's tool history — that artifact is disregarded as stale/wrong; the live `sysctl` reads
above are authoritative. 24 GB unified memory matches Finding 74's own reference figure
(`sysctl hw.memsize` was checked before setting MLX's memory cap), so this is consistent with prior
in-session hardware assumptions even though the specific chip generation was never named before.

## Is Echo extracting what this hardware supports? Three concrete gaps found, zero-cost to close

**1. Every model is context-starved relative to what it actually supports.** `num_ctx` is hardcoded to
`8192` in four separate places (`app/ollama_handler.py` ×3, `app/core/echo_model_orchestrator.py` ×1)
and `river_deliberation.py`'s own `_NUM_CTX = 8192` constant, all justified only by "matches Echo's
Modelfile num_ctx" — a self-referential justification, not a hardware-derived one. Real, live
`ollama show` output for the models actually in the pool:

| Model | Real max context (from `ollama show`) | Currently configured | Headroom unused |
|---|---|---|---|
| `qwen2.5-coder:7b` | 32,768 | 8,192 | 4x |
| `llama3.1:8b` | 131,072 | 8,192 | 16x |
| `deepseek-r1:7b` | 131,072 | 8,192 | 16x |

24 GB unified memory is a real constraint on how far this can be pushed for free (KV cache grows
with context length), but 8,192 is not derived from any measured memory-pressure test in this
codebase — it is a constant copied forward, unquestioned, since Finding 17 (2026-07-08). **This is a
genuine, zero-cost-to-test lever**: raising `num_ctx` for the long-context-capable models specifically
(not uniformly — `qwen2.5-coder`'s real ceiling is only 32k) is free to *try* and cheap to *measure*
(watch `memory_pressure`/swap under a raised value), though it is explicitly not implemented in this
pass per this mission's own constraint.

**2. Ollama concurrency is at its untouched default.** `OLLAMA_NUM_PARALLEL` is not set anywhere in
this environment (confirmed via `env | grep -i OLLAMA` and `launchctl getenv`) — Finding 45 already
named this as "a real, complementary, likely higher-leverage fix... an infrastructure/ops change
outside this codebase," and it remains genuinely untouched as of this investigation. At default
concurrency, a real council deliberation (3 models + synthesis) serializes fully rather than
overlapping — on a 10-core/10-GPU-core machine with 706 GB of headroom disk and swap already in active
use (5.19 GB), there is real, unexploited parallelism available, gated entirely by one environment
variable Ollama itself reads at process start, not by anything in this Python codebase.

**3. Swap is already in real, active use (5.19 GB) during ordinary operation** — with `echo:latest`
alone currently resident at 5.5 GB (per live `ollama ps`), a 3-model council cycle plus the Flask
process, FAISS index, and background autonomous threads genuinely compete for 24 GB. This is the real
ceiling behind why `num_ctx` was set conservatively in the first place, even though no measurement in
this codebase's own history documents that reasoning explicitly — it reads as an inherited assumption
that happens to be roughly correct, not a derived one.

## What this hardware cannot do, regardless of software changes

- **No local model larger than 8B parameters class is realistically loadable alongside the rest of
  the live system's real, concurrent RAM footprint** (FAISS index alone is part of a 1.2 GB `memory/`
  footprint; the Flask process, background threads, and swap pressure already observed above are
  real, not hypothetical). A genuinely larger reasoning-class model is a real capability Echo cannot
  reach on this hardware without either accepting much higher swap pressure and latency, or paying for
  a hosted API call — the latter explicitly forbidden by this mission's governance constraints.
- **No GPU-side batch parallelism across multiple *different* models simultaneously** is realistic at
  full context — 10 GPU cores at 24 GB unified memory is enough for one model comfortably, not several
  large ones concurrently at long context.
- **Thermal/power throttling was not observed** (`pmset -g therm` reports no warning), so this is not
  currently a limiting factor — worth re-checking under sustained heavy multi-model load, which this
  investigation did not attempt to induce.

## What this investigation did not attempt

No live experiment was run to actually raise `num_ctx` or `OLLAMA_NUM_PARALLEL` and measure the
effect — per this mission's explicit "do not implement the proposed capability-ceiling interventions
yet" constraint. The three items above are named as measured, zero-cost-to-test candidates, not
verified improvements.
