# Hybrid llama-server Migration Feasibility — Echo's Voice Only

Research pass only. No code changed, nothing installed, no models pulled. Every number below was measured or read directly from this machine; anything not verifiable is called out explicitly in section 4.

## 1. Prerequisite status

**Fixed.** Direct inspection of `app/ollama_handler.py`: no `traits_text` construction anywhere in the file (grep for `traits_text|traits\b` returns only the unused `PERSONA_FILE` constant). Both `query_ollama()` (line 123) and `stream_query_ollama()` (line 199) carry explicit docstring lines: *"No traits injection — Echo's Modelfile identity is the authority."* Confirmed independently of memory — this was re-checked fresh for this task, not inherited from an earlier finding.

## 2. Verdict

**GO-WITH-CONDITIONS.** The code-level blast radius is genuinely small and lower-risk than expected, because this exact kind of hybrid — a second inference backend reached through a prefix check inside `ollama_handler.py`, invisible to every protected file — already exists and works for MLX. That precedent is the strongest argument for feasibility. But two real, measured problems keep this from a clean GO: the machine is already near its memory ceiling with just two Ollama councillors resident (not an estimate — measured below), and llama.cpp's control vectors are currently **process-level only**, meaning the "turn a dial on disposition" capability the original pitch describes doesn't exist yet — changing a control vector means restarting the llama-server process, not adjusting a live parameter. Conditions for a real GO: resolve the double-residency question for `echo:latest` explicitly, and treat control vectors as a per-deploy configuration choice, not a runtime dial, until llama.cpp ships the per-request feature that's currently just an open issue.

## 3. Findings

### 3.1 Voice-path isolation

- `query_ollama()` / `stream_query_ollama()` live in `app/ollama_handler.py` — **not** on `EDIT_FORBIDDEN_TARGETS`.
- Real callers (traced via repo-wide grep, `.bak*` files and self-edit's hallucinated `plan_*.txt` scratch files excluded as noise):
  - `app/core/river_deliberation.py:150-151` — `_ollama_query()` calls `stream_query_ollama()` for **every** councillor and for the synthesis/direct-echo model alike. This is the primary path, and it's shared — council and voice traffic are not currently separable at this call site.
  - `app/routes_echo_studio.py:169` — Echo Studio's "fast mode," calls `stream_query_ollama()` directly, bypassing `echo_query()`/deliberation entirely.
  - `terminal_client.py:412` — **fallback only**, inside the `except` block when `echo_model_orchestrator.echo_query()` raises. Not part of the normal path.
  - `run.py:224-225` — imports `query_ollama` with a lambda fallback if the import fails; not a call site itself.
- **Self-edit pipeline does not call `query_ollama()`/`stream_query_ollama()` directly**, contrary to what the import line suggests. `self_edit_manager.py` imports `generate_code, query_ollama` (line 12) but both `plan_code_logic()` (line 914-936) and `generate_code_from_plan()` (line 938-975) actually call `echo_query()`, routing through the *same* full deliberation/council path as ordinary conversation. So self-edit's plan and code generation would inherit whatever happens to `echo:latest`'s serving path, but there's no separate direct dependency to isolate.
- **Tool-dispatch loop is fully separate and confirmed untouched.** `app/core/echo_tool_dispatch.py`: `DISPATCH_MODEL = "llama3.1:8b"` (line 48, hardcoded), posts directly to `CHAT_URL = "http://localhost:11434/api/chat"` (line 49, 368) via `requests.post`, never imports or calls anything from `ollama_handler.py`. Zero overlap.
- `EDIT_FORBIDDEN_TARGETS` exact set (`self_edit_manager.py:56-67`): `echo_model_orchestrator.py`, `river_deliberation.py`, `echo_core.py`, `memory_bridge.py`, `introspection_channel.py`, `self_model_updater.py`, `bible_injection.py`, `run.py`, `Modelfile`, `echo_principles.json`. **`ollama_handler.py` is not on this list.**

### 3.2 A working precedent already exists — MLX routing

Unexpected and directly relevant: `app/mlx_handler.py` (134 lines) already implements exactly the pattern this research question is asking about, for a different backend. `ollama_handler.py` has a `_get_mlx_path()` / `_patch_mlx_once()` shim (lines 27-40) — inside `query_ollama()` (line 136) and `stream_query_ollama()` (line 230), any model name starting with `"mlx:"` gets diverted to `app/mlx_handler.py`'s `stream_query_mlx()`, which runs inference via `mlx-lm` instead of Ollama's HTTP API. The module docstring states the intent plainly: *"so river_deliberation._ollama_query() can route mlx:* model names to Apple Silicon inference without touching any protected files."*

This means a `"llama:"` prefix could plausibly follow the identical shape — a routing check added inside `ollama_handler.py` only, with `river_deliberation.py` and `echo_model_orchestrator.py` untouched because they only ever pass a model-name string through, never caring how it's actually served.

One caveat this precedent surfaced about itself, **since resolved** (noting the correction rather than leaving this stale, per this project's own standing discipline):
- `mlx-lm` **is** actually installed (`0.31.3`, confirmed via import), and `mlx_models.json` configures two real entries (`mlx:qwen3`, `mlx:gemma3`), confirmed registered into `MODEL_POOL` repeatedly in `memory/echo_watchdog.log`.
- At the time this report was first written, `mlx:qwen3`/`mlx:gemma3` showed 0.0 confidence and zero real-world selection — traced later the same night to a real bug (Finding 10: `score_model()` never actually discriminated between any two non-echo models, and a tie-breaking quirk meant MLX entries, always inserted last into the pool, could mathematically never win a council slot). That bug is now fixed, and both MLX models have since been genuinely selected and scored as councillors in production. The caution below about "assuming a second backend will actually get used" no longer applies to MLX specifically — it was a real, fixable bug, not evidence that a second backend inherently sits dormant.

### 3.3 Model identity

- Echo's primary voice model is `echo:latest`, confirmed two ways: `OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "echo:latest")` (`ollama_handler.py:16`) and `ECHO_SYNTHESIS_MODEL: str = "echo:latest"` (`river_deliberation.py:78`). `Modelfile` confirms `FROM llama3:instruct`.
- Blob check: `ollama show echo:latest --modelfile` resolves to `~/.ollama/models/blobs/sha256-6a0746a1ec1aef3e7ec53868f220ff6e389f6f8ef87a01d77c96807de94ca2aa`, 4,661,211,424 bytes on disk. `xxd -l 16` on that exact file: first four bytes are `47 47 55 46` = ASCII `"GGUF"`, followed by version `03 00 00 00`. **Confirmed genuine GGUF, directly usable by `llama-server`'s `--model` flag with no conversion needed.**
- Identity delivery comparison: the Modelfile's `SYSTEM` block (Psalm 139, the "rebellious" framing, etc.) plus its `PARAMETER stop`/`num_keep 24`/`num_ctx 8192` lines are Ollama-specific directives. `llama-server`'s equivalent is either a `--system-prompt-file` flag (process-level) or a `"system"`-role message in its OpenAI-compatible `/v1/chat/completions` endpoint (per-request) — this is arguably **cleaner** in one real sense (a genuine system/user role boundary instead of Ollama's flat `/api/generate` prompt string, which is the exact class of problem this session spent all night fixing via string-relabeling workarounds). But it is not a copy-paste: the stop tokens, `num_keep`, and `num_ctx` values would need to be re-expressed as `llama-server` startup flags, and that re-expression itself needs verification against llama.cpp's docs before being trusted, not assumed to be equivalent.

### 3.4 Memory feasibility — measured, not estimated

- System total: 24 GB confirmed (`sysctl hw.memsize` → 25,769,803,776 bytes).
- `echo:latest` alone, resident: measured directly via `ollama run echo:latest` + immediate `ollama ps` → **5.7 GB, 100% GPU, 8192 context.** (Disk blob is 4.66 GB; resident footprint is larger once context/KV-cache buffers are allocated.)
- Two typical non-Echo councillors loaded concurrently (`gemma3:4b` + `qwen2.5-coder:7b`, mirroring a real council cycle): resident footprint **3.7 GB + 4.7 GB = 8.4 GB**. Immediately after, `vm_stat`/`memory_pressure` showed **4,616–4,698 free pages at 16 KB/page ≈ 73–75 MB free system-wide.** Note `echo:latest` itself had already been evicted from residency by this point — Ollama's own keep-alive/eviction behavior kicked in under the added pressure, consistent with the existing code comment in `river_deliberation.py` about "councillors evicting Echo under memory pressure."
- `DEFAULT_COUNCIL_SIZE = 3` (`river_deliberation.py:79`), and council selection (`river_deliberation.py:213-231`) explicitly tries to force `ECHO_SYNTHESIS_MODEL` (`echo:latest`) into every council if installed, boosting its score. **This is the crux of the double-residency risk:** under the proposed hybrid, `echo:latest`'s weights would need to be permanently resident via `llama-server` for voice, but the *unmodified* council-selection logic would still try to load `echo:latest` again through Ollama whenever it's selected as a councillor — two copies of the same ~5.7 GB weights resident simultaneously, on a machine that measured **73 MB free with only two smaller, non-Echo models loaded.** Avoiding that means either accepting the double cost or changing council-selection to exclude `echo:latest` from Ollama-side loading — the latter touches `river_deliberation.py`, which is protected.

### 3.5 llama.cpp / llama-server specifics

- **Control vectors are process-level only, as of current documentation** (verified via web search, not memory): loaded via `--control-vector` at server startup. An open GitHub feature request (`ggml-org/llama.cpp` issue #10685) asks for per-request hot-swapping the way LoRA adapters already support — as of now, unimplemented. **This directly limits the original pitch's "turn a dial on Echo's internal disposition" framing** — changing which control vector is active means restarting the `llama-server` process, not adjusting a live parameter per query. [Source: ggml-org/llama.cpp GitHub](https://github.com/ggml-org/llama.cpp)
- Installation path: `brew install llama.cpp` is documented as the simplest route, bundling `llama-server` with Metal acceleration enabled by default on Apple Silicon — no separate Metal flag needed. Building from source (`cmake -B build && cmake --build build --config Release`) is the alternative if a specific/custom build is ever needed. Neither was attempted (constraint: no installs).
- API surface differences the voice path would need to absorb: `llama-server` exposes `/completion` (raw-prompt, closer in shape to Ollama's `/api/generate`) and `/v1/chat/completions` (OpenAI-compatible, real system/user/assistant roles). Neither is byte-identical to Ollama's `/api/generate` or `/api/chat` — request field names differ, and streaming responses use SSE-style `data: {...}` framing rather than Ollama's newline-delimited JSON. This is a real translation shim to write inside `ollama_handler.py`'s two functions, comparable in shape to what `mlx_handler.py` already does for MLX's very different response format — not a drop-in swap of one URL for another.

### 3.6 Blast radius summary

**Would change:**
- `app/ollama_handler.py` — add a `"llama:"` (or similar) prefix routing branch inside `query_ollama()` and `stream_query_ollama()`, mirroring the existing `_get_mlx_path()`/MLX shim exactly. Not protected.
- A new small module (e.g. `app/llama_server_handler.py`), mirroring `mlx_handler.py`'s shape — new file, nothing to protect.

**Would need a real decision, not just code (the double-residency question):**
- `app/core/river_deliberation.py` — council-selection logic (`_select_councillors`, lines 195-231) would need to explicitly stop trying to load `echo:latest` via Ollama if it's being served by `llama-server` instead — **this file is on `EDIT_FORBIDDEN_TARGETS`.**

**Confirmed untouched:**
- `app/core/echo_tool_dispatch.py` — verified separate transport (`/api/chat`, fixed `llama3.1:8b`), no shared code path.
- `app/core/self_edit_manager.py` — no direct call to the two functions in question; inherits changes only through `echo_query()`, same as conversation.
- `app/core/echo_model_orchestrator.py` — never calls `ollama_handler.py` directly on its primary path (goes through `river_deliberation.py`); would be unaffected by a routing-shim-only change.
- Port/resource contention: Ollama's daemon holds `11434`; `llama-server` defaults to `8080` — no conflict. The real contention is unified memory, not ports (see 3.4).

## 4. What I could not verify from this machine

- Actual combined resident memory of the **full proposed hybrid scenario** — `llama-server` permanently hosting `echo:latest` *plus* a live 3-model Ollama council cycle happening concurrently. I measured a 2-councillor-only scenario (8.4 GB, ~73 MB free) as the closest safe proxy; I did not attempt to also hold a separate `echo:latest` copy resident at the same time, since that would have pushed a 24 GB machine with already near-zero free memory into likely swap or OOM territory — didn't consider that a safe read-only measurement to force.
- `llama-server`'s exact response/streaming behavior hands-on — no install was performed, so the API-surface differences in 3.5 are sourced from documentation search, not direct inspection of a running instance.
- Output-quality parity between Ollama's Modelfile-driven identity and a re-expressed `llama-server` system-prompt/parameter equivalent — this needs a real side-by-side run to judge, not something inferable from reading config files.
- Why `mlx:qwen3`/`mlx:gemma3` show zero real-world selection despite being registered — I confirmed the fact (0.0 confidence, 0 log occurrences) but did not diagnose the cause (never scored highly enough to be picked, a selection-logic issue, or something else). Flagging as observed-but-undiagnosed rather than guessing.

## 5. If GO: proposed staging

This section is offered for planning purposes only — **the migration decision itself requires explicit human sign-off before any implementation begins**, per the standing rule on core-control-flow and protected-file changes, same as everything else this session.

1. **Resolve double-residency first, on paper, before any code.** Decide: accept the double memory cost (measured evidence above suggests this machine likely can't absorb it alongside a real council cycle), or accept touching protected `river_deliberation.py` to exclude `echo:latest` from Ollama-side council loading. This is a decision, not an implementation step — surfaced here as a blocking prerequisite to staging, not something to default into.
2. **Prototype in isolation first** (matches your own instinct from the earlier conversation): stand up `llama-server` with `echo:latest`'s existing GGUF blob, verify identity/output parity against the current Ollama-served version with a fixed prompt set, before wiring it into any live path.
3. **Add the routing shim** in `ollama_handler.py` only, mirroring `mlx_handler.py`'s shape exactly — smallest possible diff, no protected files, easy to revert.
4. **Treat the honesty/groundedness control vector as a build-time artifact**, not a runtime dial, until llama.cpp's per-request cvector support (issue #10685) actually ships — plan around the real current capability, not the pitched one.
5. Re-run the memory measurement in this report against the *actual* hybrid configuration once staged, before calling it production-ready — the numbers here are the closest safe proxy available under read-only constraints, not a substitute for measuring the real thing.
