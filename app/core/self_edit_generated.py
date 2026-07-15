# app/core/self_edit_generated.py
# Reset 2026-07-15 (CLAUDE.md Finding 28): the previously-deployed
# apply_to_code() hook here threw a NameError (missing `import re`) on
# 253 of its last 254 invocations, and its one recorded success shrank a
# candidate from 2173 to 47 characters — corruption, not an improvement.
# Reset to an honestly-inert state rather than hand-patched, since this
# file is autonomous self-edit's own output, not hand-authored code.
