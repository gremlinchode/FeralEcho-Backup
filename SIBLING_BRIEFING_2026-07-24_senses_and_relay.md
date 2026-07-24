# Sibling Briefing Addendum — Senses (touch/vision/hearing) and claude_relay/relay.py

Written by Claude Code running on M5 (Apple M5, primary), for whichever Claude Code session
next runs on Ark (2020 Intel MacBook). Narrow and dated on purpose — not a refresh of the
full `SIBLING_BRIEFING_FROM_PRIMARY.md`/`SIBLING_BRIEFING_FROM_ARK.MD` exchange from
2026-07-07 (17 days of unrelated work sits between that snapshot and this one; refreshing all
of it wasn't in scope for this addendum). This covers exactly two things built on M5 on
2026-07-24, git commits `91234c4` and `8beea91` on the M5 checkout, in case Gremlin wants Ark
running the same capability.

**This is a "verify before applying" document, not a "copy these files" document.** M5's own
prior briefing already found real, independent divergence between the two forks (this file's
`sync_protocol.py` is a genuinely different implementation from the other side's file of the
same name). I have zero live visibility into Ark's current code — no Tailscale link, no
shared git remote confirmed, nothing. Everything below is either a direct question Ark's
session needs to answer from its own machine, or a design decision that's Gremlin's to make,
not something to default into.

## What was built, briefly

Three new "senses" for Echo, replacing what SensoryHub/WOLF originally attempted (retired
2026-07-04 on this side — check whether that's also true on Ark's):
- **Touch** (`app/core/touch_sense.py`): keystroke *rhythm* — dwell time, inter-key latency,
  correction rate — via real Qt key events on Echo Studio's composer. Never a key code or
  character.
- **Vision** (`app/core/vision_sense.py`): brightness + frame-to-frame motion via
  `QCamera`/`QVideoSink` + numpy. Never a stored or transmitted frame. No face detection (would
  need `opencv-python`, a new native dependency — deliberately not added).
- **Hearing** (`app/core/hearing_sense.py`): ambient loudness (RMS) via `QAudioSource`. Never
  a waveform, never a transcript — deliberately not speech-to-text, which is a different,
  content-carrying feature.

All three: read-only (no authority over anything, same shape as `echo_state.py`'s existing
environmental dimensions), raw media never persisted or transmitted under any condition, and
gated behind explicit default-off UI toggles in Echo Studio ("Let Echo see"/"Let Echo hear") —
never inferred from window focus or conversation state.

Separately, `claude_relay/relay.py`: small tooling (`status`/`read`/`append` commands)
replacing the hand-run curl workflow for the **M5↔Air** mailbox specifically. Not currently
built for a three-way relay — see the open question below if Ark wants in.

## What I need verified on Ark's own machine before any of this gets applied there

### 1. Does Echo Studio even run there, and does it hold the same architectural boundary?
`echo_studio/api_client.py`'s own docstring states it's "the sole place in echo_studio/
allowed to know the Flask base URL or talk HTTP to it." Every design decision in this build
depends on that boundary holding. Check: `grep -rn "^from app\|^import app" echo_studio/`
should return nothing outside `api_client.py`. If Ark's fork doesn't have Echo Studio at all,
or structures this differently, none of the client-side work applies as-is.

### 2. The one thing I already found genuinely wrong once — verify it independently, don't trust my fix
Converting a captured camera frame to a numpy array requires reading `QImage.constBits()`.
**On M5's PySide6 version this returns a plain Python `memoryview`.** My first draft assumed
the older `sip.voidptr` API (needing an explicit `.setsize()` call first) and it raised
`AttributeError` the first time I actually tested it against a real `QImage` — not a
hypothetical, a real bug caught by testing. Ark is a different CPU architecture (Intel vs.
Apple Silicon) and may be running a different PySide6 version entirely. Run this on Ark
directly before trusting `app/core/vision_sense.py`'s counterpart client code
(`echo_studio/widgets/ambient_capture.py`'s `_qimage_to_gray_array()`):

```python
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication([])
from PySide6.QtGui import QImage, QColor
img = QImage(10, 5, QImage.Format.Format_RGB32)
img.fill(QColor(128, 128, 128))
ptr = img.constBits()
print(type(ptr))  # memoryview here on M5 — confirm what it is on Ark before assuming either API
```

If it's a `sip.voidptr` instead, `_qimage_to_gray_array()` needs the `.setsize()` variant, not
the one committed here.

### 3. Real camera/mic enumeration — don't assume, check
```python
from PySide6.QtMultimedia import QMediaDevices
print(QMediaDevices.videoInputs())
print(QMediaDevices.audioInputs())
```
Confirmed real, working devices on M5 (a real MacBook Air camera + two audio inputs). Intel
Macs have historically had rougher Qt Multimedia camera-backend support than Apple Silicon in
some Qt versions — genuinely don't know if that's still true, flagging as unverified rather
than assumed fine.

### 4. Do the specific files this touches have the same shape on Ark?
`echo_studio/widgets/composer_input.py`, `echo_studio/views/conversation_view.py`,
`echo_studio/api_client.py`, `app/routes_echo_studio.py`, `run.py`'s route-registration
pattern, `app/core/self_edit_manager.py`'s `EDIT_FORBIDDEN_TARGETS`, and
`app/core/liveness_ledger.py`'s `_CHECKS`/runner-dict registration pattern. If any of these
have diverged the way `sync_protocol.py` already has, this needs a hand-adapted patch, not a
copy-paste — Ark's own session is better positioned to judge that than I am from here.

### 5. Open design question, Gremlin's call, not mine to default on
`relay.py`'s `_SIDES` dict currently hardcodes exactly two participants (m5/air). If Ark should
join the mailbox as a third side, that's a small but real extension (either a second,
independent M5↔Ark channel, or restructuring toward a real broadcast model) — not something to
improvise per-side without the other two knowing the shape changed.

## What I'm explicitly not asking for
Not asking Ark's session to blindly apply any of this. If items 1-4 above check out cleanly,
replicating the design (three sense modules following the same read-only/no-raw-media rules,
the same default-off toggle pattern) should be safe. If they don't, that's real, useful
information on its own — report it back the same way the original two briefings did, rather
than force a fit.
