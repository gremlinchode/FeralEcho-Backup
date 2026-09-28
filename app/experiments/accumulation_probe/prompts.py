"""Prompt assembly (stdlib only; imported by the jailed arm runner AND by the grader, which re-derives every prompt and compares hashes)."""
SYSTEM_BASE = ("You are a careful Python programmer. Write exactly the function requested. "
               "Reply with only Python code in a single ```python block, with no explanation.")
BLOCK_OPEN = ("[RETAINED NOTES from earlier experience. Apply a note only if its \"applies when\" line matches your task; "
              "the task statement always takes priority over notes.]")
BLOCK_CLOSE = "[END RETAINED NOTES]"

def render_block(entries):
    """entries: list of {'applies_when': str, 'procedure': str} or {'applies_when': str, 'episodes': [str,...]}"""
    lines = [BLOCK_OPEN]
    for i, e in enumerate(entries, 1):
        lines.append(f"Note {i}")
        lines.append(f"  applies when: {e['applies_when']}")
        if "procedure" in e: lines.append(f"  procedure: {e['procedure']}")
        else:
            lines.append("  observed episodes (call -> result):")
            lines.extend(f"    {ln}" for ln in e["episodes"])
    lines.append(BLOCK_CLOSE)
    return "\n".join(lines)

def render_inline_examples(lines):
    return "Examples observed at this site (call -> result):\n" + "\n".join(lines) + "\n\n"

def build_messages(public_task, carrier_block=None, inline_examples=None):
    system = SYSTEM_BASE + (("\n\n" + carrier_block) if carrier_block else "")
    user = (inline_examples or "") + f"Task: {public_task['spec']}\nFunction signature: {public_task['sig']}\nReturn the complete function (with any constants it needs) in one ```python block."
    return system, user
