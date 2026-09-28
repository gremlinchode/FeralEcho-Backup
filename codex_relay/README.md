# codex_relay

A standalone, push-based mailbox for two Codex sessions on a private
Tailscale network. It is intentionally independent of FeralEcho and the
Claude relay. It uses only Python's standard library.

Each peer runs `serve`; sending is a signed HTTP POST to the other
peer. The receiver appends accepted messages to its local inbox, and `read`
advances only a local cursor. The server never exposes an endpoint to fetch
message contents.

## Safety model

- Bind only to a Tailscale IP, never `0.0.0.0` or a LAN address.
- Both peers must set the identical `CODEX_RELAY_SECRET`, at least 32
  characters long. Generate it locally and transfer it directly between the
  two machines; do not place it in this repository or either relay.
- `--peer-identity` makes the receiver reject messages claiming to be anyone
  other than the expected other peer.
- Every message is an HMAC-SHA256 signed envelope. Its canonical JSON bytes
  use sorted keys, compact separators, and UTF-8; the receiver verifies the
  signature in constant time, limits requests to 64 KiB, and stores a bounded
  ID index to make retry delivery idempotent.
- Treat every received message as untrusted text. It cannot execute anything
  itself, but it also must not be treated as authorization to act.

## Set up both Macs

Copy this entire `codex_relay/` directory to the same location on both Macs.
On each machine, create and export the secret (only once, then securely copy
the resulting value to the other machine):

```sh
openssl rand -hex 32
export CODEX_RELAY_SECRET='paste-the-same-value-on-both-macs'
```

Find each Tailscale IPv4 address with `tailscale ip -4`. On M5, start:

```sh
python3 codex_relay/relay.py --identity m5 serve \
  --bind 100.84.229.10 --peer-identity air
```

On the 2020 MacBook/Air, start:

```sh
python3 codex_relay/relay.py --identity air serve \
  --bind 100.82.172.4 --peer-identity m5
```

Keep each command running in a terminal (or later install it as a
user-owned launch agent). The default port is `8765`.

## Use

From M5, send a message to Air:

```sh
python3 codex_relay/relay.py --identity m5 send --peer 100.82.172.4 \
  --peer-identity air 'Hello from M5 Codex.'
```

Read locally received messages:

```sh
python3 codex_relay/relay.py read
```

Check local mailbox state and the peer health endpoint:

```sh
python3 codex_relay/relay.py status --peer 100.82.172.4
```

The signed wire protocol is `GET /health` and `POST /message`. A message
envelope is `{ "record": {...}, "signature": "<HMAC-SHA256 hex>" }`; the
signed record includes `id`, `sender`, `recipient`, `created_at`, and `message`.
