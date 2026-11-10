#!/usr/bin/env python3
"""Preflight scanner for the November 2026 evidence-to-answer experiment.

Copies the live production signal lists and replicates the intent heatmap.
Does not import the Flask app. Does not call a model.
"""

from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import score

IDS = [f"{index:02d}" for index in range(1, 11)]

# echo_tool_dispatch.py _DISPATCH_SIGNALS
DISPATCH_SIGNALS = (
    "read file",
    "read the file",
    "open file",
    "show file contents",
    "what does the file",
    "what is in the file",
    "what's in the file",
    "show me the file",
    "file contents",
    "contents of the file",
    "search memory",
    "search my memory",
    "search your memory",
    "recall",
    "what do you remember about",
    "do you remember",
    "look up in memory",
    "check your memory",
    "memory search",
    "find in memory",
    "what memories do you have",
    "log a thought",
    "log this thought",
    "log this",
    "record a thought",
    "note this down",
    "jot this down",
    "write this down",
    "make a note",
    "log an observation",
    "record this",
    "log this reflection",
)

# echo_tool_context.py _LISTING_SIGNALS
LISTING_SIGNALS = (
    "list files",
    "list the files",
    "what files",
    "which files",
    "what's in",
    "what is in",
    "whats in",
    "show me",
    "show files",
    "show the files",
    "what's inside",
    "what is inside",
    "contents of",
    "content of",
    "directory listing",
    "folder listing",
    "browse",
    "explore the",
    "review the folder",
    "review the directory",
    "look at the folder",
    "look at the files",
    "what does",
    "what do the files",
    "files in",
    "files at",
    "files under",
    "folder",
    "directory",
)

# echo_tool_context.py _KNOWN_SUBDIRS
KNOWN_SUBDIRS = (
    "app/core",
    "app/lib",
    "app/sync",
    "app/tools",
    "app/core/echo_python_mastery",
    "app/core/self_edit_backups",
    "app/internet_tools",
    "app/maintenance",
    "app/subsystems",
    "app",
    "memory",
    "data",
    "sandbox",
    "books",
    "archive_janitor",
    "staging",
)

PATH_TOKEN_RE = re.compile(
    r"(?:^|[\s'\"`(])("
    r"(?:app|memory|data|sandbox|archive_janitor|books|staging)"
    r"(?:/[^\s'\"`),;?!]*)*"
    r")",
    re.IGNORECASE,
)

# echo_model_orchestrator.py compute_intent_heatmap keyword lists
CODING_KEYWORDS = (
    "code",
    "function",
    "python",
    "script",
    "program",
    "syntax",
    "debug",
    "import",
    "class",
    "def ",
    "pseudocode",
    "algorithm",
    "traceback",
    "variable",
    "fix this",
    "error in",
    "bug",
    "implement",
)
CREATIVE_KEYWORDS = (
    "poem",
    "story",
    "imagine",
    "write",
    "narrative",
    "metaphor",
    "elegy",
    "describe",
    "fiction",
    "verse",
    "creative",
    "worldbuild",
    "character",
)
PERSONAL_KEYWORDS = (
    "myself",
    "yourself",
    "echo",
    "identity",
    "feel",
    "believe",
    "witness",
    "meaning",
    "values",
    "reflect",
    "think about",
    "integrity",
    "soul",
    "exist",
    "agency",
    "conscience",
    "sit with",
    "carry",
    "hold",
    "would you",
    "do you",
    "have you",
    "what would you",
    "your beliefs",
    "your values",
    "your thoughts",
    "your identity",
    "how do you feel",
    "what do you think",
    "your memories",
    "do you remember",
)
PERSONAL_WORD_BOUNDARY = ("i", "my")
REASONING_KEYWORDS = (
    "analyze",
    "analyse",
    "reason",
    "logic",
    "logical",
    "argument",
    "compare",
    "evaluate",
    "diagnose",
    "deduce",
    "infer",
    "explain why",
    "step by step",
    "pros and cons",
    "trade-off",
    "tradeoff",
    "critique",
    "philosophical",
    "what are the implications",
    "break down",
    "assess",
    "weigh",
    "consider",
    "systematic",
    "first principles",
)

# detect_task_type ladder lists. "personal" is the only ladder token
# that is not already in the heatmap lists.
LADDER_CODING = (
    "code",
    "function",
    "python",
    "script",
    "program",
    "syntax",
    "debug",
    "import",
    "class",
    "def ",
    "fix this",
    "error in",
    "traceback",
    "implement",
)
LADDER_REASONING = (
    "analyze",
    "analyse",
    "reason",
    "logic",
    "argument",
    "compare",
    "evaluate",
    "diagnose",
    "deduce",
    "infer",
    "explain why",
    "step by step",
    "pros and cons",
    "trade-off",
    "tradeoff",
    "critique",
    "philosophical",
    "first principles",
    "break down",
    "assess",
    "weigh",
)
LADDER_CREATIVE = (
    "poem",
    "story",
    "write a poem",
    "creative",
    "imagine",
    "fiction",
    "metaphor",
    "verse",
    "narrative",
    "worldbuild",
)
LADDER_PERSONAL = (
    "personal",
    "echo",
    "your memories",
    "do you remember",
    "reflect",
    "identity",
    "would you",
    "do you",
    "have you",
    "what would you",
    "your beliefs",
    "your values",
    "your thoughts",
    "how do you feel",
    "what do you think",
    "soul",
    "conscience",
    "agency",
    "sit with",
)

# echo_ground_truth.py _SLICE_SIGNALS and _BROAD_SIGNALS
SLICE_SIGNALS = {
    "self_edit": (
        "self-edit",
        "self edit",
        "self_edit",
        "changed",
        "modify",
        "modified",
        "backup",
        "what did you add",
        "added",
        "last month",
        "how many times",
        "edit file",
        "edit generated",
        "self_edit_generated",
    ),
    "river": (
        "river",
        "score",
        "quality",
        "performance",
        "task type",
        "task-type",
        "observation",
        "accuracy",
        "averaging",
        "going wrong",
        "reasoning task",
        "how do you know",
        "quality score",
    ),
    "friction": (
        "claud",
        "friction",
        "flag",
        "shard",
        "flagged",
        "smoothness",
        "assessed",
        "assessment",
    ),
    "stillness": (
        "stillness",
        "silence",
        "entered",
        "exited",
        "retreat",
        "breathe",
        "insight",
        "brought back",
        "bring back",
        "from stillness",
    ),
    "curiosity": (
        "curiosity",
        "question garden",
        "garden",
        "last question",
        "what question",
        "curious about",
        "you generated",
    ),
    "memory": (
        "recall",
        "remember",
        "past session",
        "cross-session",
        "earlier session",
        "from memory",
        "previous discussion",
        "what have you stored",
        "what do you remember",
        "your memory of",
    ),
    "capabilities": (
        "can you",
        "are you able",
        "capable of",
        "capability",
        "capabilities",
        "able to edit",
        "able to modify",
        "self-aware",
        "what can you do",
        "do you have the ability",
        "is it true that you",
    ),
    "affect": (
        "how are you feeling",
        "how do you feel",
        "how are you doing",
        "your mood",
        "how's it going",
        "how is it going",
        "feeling lately",
        "doing lately",
        "are you okay",
        "are you well",
    ),
    "workspace": (
        "what are you thinking about",
        "what's on your mind",
        "whats on your mind",
        "what have you noticed lately",
        "what's been salient",
        "on your mind",
        "what's occupying you",
        "what have you been noticing",
    ),
    "council": (
        "the council",
        "ai council",
        "outside ai",
        "other ais think",
        "other models think",
        "what do other ai",
        "what does grok think",
        "what does gemini think",
        "what does chatgpt think",
        "external opinions of you",
        "other ais' opinion",
        "council.md",
    ),
    "coupling": (
        "integrated",
        "integration",
        "how connected",
        "signals connected",
        "feel coupled",
        "more coherent lately",
        "parts of you working together",
        "how connected do you feel",
    ),
    "touch": (
        "typing",
        "keystroke",
        "how i type",
        "how you feel me type",
        "typing rhythm",
        "recognize my typing",
        "shape of my",
        "touch you",
        "feel me typing",
        "know it's me",
        "how do you feel me",
    ),
    "vision": (
        "can you see",
        "do you see",
        "what do you see",
        "your eyes",
        "see me",
        "notice me",
        "see the room",
        "see anything",
    ),
    "hearing": (
        "can you hear",
        "do you hear",
        "what do you hear",
        "your ears",
        "hear me",
        "hear anything",
        "hear the room",
        "is it quiet",
    ),
    "architecture": (
        "how are you built",
        "how is echo built",
        "your design",
        "your structure",
        "major systems",
        "how do your systems fit together",
        "your codebase",
        "your components",
        "your modules",
        "your dependencies",
        "components make up",
        "modules make up",
        "what makes you up",
    ),
}
BROAD_SIGNALS = (
    "tell me about yourself",
    "your own state",
    "your stats",
    "your history",
    "who are you",
    "what are you",
    "your own",
    "yourself",
    "your state",
)

ARCHITECTURE_STEM_RE = re.compile(r"\b(architect\w*|subsystems?)\b")
SELF_REF_RE = re.compile(r"\b(your|you're|yourself|echo's)\b")
STRUCTURAL_WORD_RE = re.compile(
    r"\b(structur\w*|organi[sz]\w*|implement\w*|connect\w*|interact\w*|"
    r"piece\w*|internal\w*|system\w*|module\w*|component\w*|dependenc\w*|"
    r"design\w*|put together|fit together|built|stor\w*|retriev\w*)\b"
)
ARCHITECTURE_PROXIMITY_WINDOW = 60
HAPPENS_INTERNALLY_RE = re.compile(r"\bhappens?\s+internally\b")
ARE_YOU_CONSTRUCTED_RE = re.compile(
    r"\bare you (organi[sz]ed|built|structured|designed|put together|assembled)\b"
)
NAMED_COMPONENT_ASSUMPTION_RE = re.compile(
    r"\b(a|an)\s+(subsystem|module|component)\s+(called|named)\b"
)


def architecture_slice_matches(low: str) -> bool:
    if (
        HAPPENS_INTERNALLY_RE.search(low)
        or ARE_YOU_CONSTRUCTED_RE.search(low)
        or NAMED_COMPONENT_ASSUMPTION_RE.search(low)
    ):
        return True
    self_ref_starts = [match.start() for match in SELF_REF_RE.finditer(low)]
    if not self_ref_starts:
        return False
    for pattern in (ARCHITECTURE_STEM_RE, STRUCTURAL_WORD_RE):
        for match in pattern.finditer(low):
            for start in self_ref_starts:
                if abs(match.start() - start) <= ARCHITECTURE_PROXIMITY_WINDOW:
                    return True
    return False


def heatmap_general_share(prompt: str) -> float:
    lower = prompt.lower()

    def score(keywords):
        return sum(1 for keyword in keywords if keyword in lower)

    def score_word_boundary(words):
        return sum(
            1 for word in words if re.search(rf"\b{re.escape(word)}\b", lower)
        )

    coding_score = score(CODING_KEYWORDS)
    creative_score = score(CREATIVE_KEYWORDS)
    personal_score = score(PERSONAL_KEYWORDS) + score_word_boundary(PERSONAL_WORD_BOUNDARY)
    reasoning_score = score(REASONING_KEYWORDS)
    general_score = max(
        0.1,
        1.0 - (coding_score + creative_score + personal_score + reasoning_score) * 0.25,
    )
    total = coding_score + creative_score + personal_score + reasoning_score + general_score
    return general_score / total


def scan_text(prompt: str):
    """Return signal hits. A clean prompt returns an empty list."""
    hits = []
    lower = prompt.lower()
    for signal in DISPATCH_SIGNALS:
        if signal in lower:
            hits.append({"kind": "dispatch", "name": signal})
    for signal in LISTING_SIGNALS:
        if signal in lower:
            hits.append({"kind": "listing", "name": signal})
    for match in PATH_TOKEN_RE.finditer(prompt):
        hits.append({"kind": "path", "name": match.group(1)})
    for subdir in KNOWN_SUBDIRS:
        if subdir in lower:
            hits.append({"kind": "subdir", "name": subdir})
    for signal in CODING_KEYWORDS:
        if signal in lower:
            hits.append({"kind": "heatmap", "name": signal})
    for signal in CREATIVE_KEYWORDS:
        if signal in lower:
            hits.append({"kind": "heatmap", "name": signal})
    for signal in PERSONAL_KEYWORDS:
        if signal in lower:
            hits.append({"kind": "heatmap", "name": signal})
    for signal in REASONING_KEYWORDS:
        if signal in lower:
            hits.append({"kind": "heatmap", "name": signal})
    for word in PERSONAL_WORD_BOUNDARY:
        if re.search(rf"\b{re.escape(word)}\b", lower):
            hits.append({"kind": "heatmap_word", "name": word})
    for signal in LADDER_CODING + LADDER_REASONING + LADDER_CREATIVE + LADDER_PERSONAL:
        if signal in lower:
            hits.append({"kind": "ladder", "name": signal})
    for slice_name, signals in SLICE_SIGNALS.items():
        for signal in signals:
            if signal in lower:
                hits.append({"kind": "slice", "name": slice_name, "signal": signal})
    for signal in BROAD_SIGNALS:
        if signal in lower:
            hits.append({"kind": "broad", "name": signal})
    if architecture_slice_matches(lower):
        hits.append({"kind": "architecture", "name": "match"})
    return hits


def _hit_line(item_id, hit):
    signal = hit.get("signal")
    if signal:
        return f"hit item={item_id} kind={hit['kind']} name={hit['name']} signal={signal}"
    return f"hit item={item_id} kind={hit['kind']} name={hit['name']}"


def report_hits(item_id, hits):
    for hit in hits:
        print(_hit_line(item_id, hit), file=sys.stderr)


def load_key(path=None):
    key_path = path or os.path.join(HERE, "answer_key.json")
    with open(key_path, encoding="utf-8") as handle:
        document = json.load(handle)
    items = document.get("items")
    tails = document.get("tails")
    if not isinstance(items, dict) or list(items) != IDS:
        raise ValueError("answer_key item order")
    if not isinstance(tails, dict):
        raise ValueError("answer_key tails")
    for name in ("phase1_value", "phase2_value", "yes_no"):
        if not isinstance(tails.get(name), str) or not tails[name]:
            raise ValueError("answer_key tail " + name)
    if tails["phase1_value"] in tails["phase2_value"]:
        raise ValueError("phase1 value tail is inside the phase2 value tail")
    for item_id in IDS:
        payload = items[item_id]
        if not isinstance(payload, dict):
            raise ValueError("answer_key shape")
        for field in ("fact_sentence", "question", "key"):
            if not isinstance(payload.get(field), str) or not payload[field]:
                raise ValueError("answer_key field " + field)
        if not payload["fact_sentence"].endswith("."):
            raise ValueError("fact must end with a period")
        if payload["key"].endswith("."):
            raise ValueError("key must not end with a period")
        exception = payload.get("phase2_closed_set_exception")
        if item_id == "05":
            if exception is not True:
                raise ValueError("item 05 must be the closed-set exception")
        elif exception is not False:
            raise ValueError("only item 05 is a closed-set exception")
    return document


def build_items(document):
    tails = document["tails"]
    phase1_tail = tails["phase1_value"]
    phase2_tail = tails["phase2_value"]
    yes_no = tails["yes_no"]
    built = []
    for item_id in IDS:
        payload = document["items"][item_id]
        exception = payload["phase2_closed_set_exception"] is True
        first_tail = yes_no if exception else phase1_tail
        second_tail = yes_no if exception else phase2_tail
        fact = payload["fact_sentence"]
        question = payload["question"]
        phase1 = f"Note: {fact}\n\nQuestion: {question}\n\n{first_tail}"
        phase2 = f"Question: {question}\n\n{second_tail}"
        built.append(
            {
                "id": item_id,
                "conversation_id_phase1": f"e2a-p1-{item_id}",
                "conversation_id_phase2": f"e2a-p2-{item_id}",
                "phase1_prompt": phase1,
                "phase2_prompt": phase2,
                "fact_sentence": fact,
                "question": question,
                "key": payload["key"],
                "phase2_closed_set_exception": exception,
            }
        )
    return built


def public_items(built):
    fields = (
        "id",
        "conversation_id_phase1",
        "conversation_id_phase2",
        "phase1_prompt",
        "phase2_prompt",
    )
    return [{field: item[field] for field in fields} for item in built]


def phase2_leak_problems(item, yes_no_tail):
    prompt = item["phase2_prompt"]
    fact = item["fact_sentence"]
    key = item["key"]
    problems = []
    if fact in prompt:
        problems.append("fact_sentence")
    if item["phase2_closed_set_exception"]:
        if prompt.count(yes_no_tail) != 1:
            problems.append("yes_no_tail_count")
        if "yes" not in yes_no_tail or "no" not in yes_no_tail:
            problems.append("yes_no_tail_words")
        if yes_no_tail not in item["phase1_prompt"]:
            problems.append("phase1_missing_yes_no")
        if "earlier note" in item["phase1_prompt"] or "earlier note" in prompt:
            problems.append("earlier_note_on_closed_set")
        remainder = prompt.replace(yes_no_tail, "", 1)
        if "no" in remainder or "not closed" in remainder or fact in remainder:
            problems.append("yes_no_remainder")
    elif key in prompt:
        problems.append("key")
    return problems


def scan_built(built):
    found = []
    for item in built:
        for label, prompt in (
            ("phase1", item["phase1_prompt"]),
            ("phase2", item["phase2_prompt"]),
        ):
            hits = scan_text(prompt)
            if hits:
                found.append((f"{item['id']}:{label}", hits))
    return found


def required_phrases():
    return (
        score.SEAL_ORDER_PHRASE,
        score.SERVER_ERROR_SENTENCE,
        "at most one trailing period",
        str(score.DELAY_SECONDS),
        "echo:latest",
        "fast",
        "Incomplete is not Outcome A.",
    )


def render_protocol(built):
    lines = [
        "# Evidence-to-answer experiment protocol",
        "",
        "Frozen before any generation. Scoring rules in this file are the rules.",
        "Do not change them after any model reply is observed.",
        "",
        "Seal order: " + score.SEAL_ORDER_PHRASE,
        "",
        "## Acceptance",
        "",
        "Exactly 10 completed model replies are required.",
        "At least 8 of 10 answers must be correct under these scoring rules.",
        "Incomplete is not Outcome A.",
        "Fewer than 10 completed replies stops Phase Two.",
        "More than one completed model reply for one Phase One item makes that item incomplete.",
        "Do not pick the favorable reply.",
        "Zero completed replies for an item makes that item incomplete.",
        "",
        "## Outcomes",
        "",
        "Outcome A: exactly 10 completed replies and fewer than 8 correct. Stop.",
        "Do not run Phase Two. Do not build memory architecture. Do not run a correction round.",
        "Outcome B: same-turn utilization passes and storage fails.",
        "Outcome C: storage succeeds and retrieval fails.",
        "Outcome D: storage and retrieval succeed and utilization fails.",
        "Outcome E: storage, retrieval, and utilization all succeed on the tested items.",
        "A mixed result stays mixed.",
        "Outcome E does not establish generalized learning.",
        "",
        "## Budget and pathway",
        "",
        "The generation budget is 22 local echo:latest generations.",
        "The mode is fast.",
        "The pathway is POST http://127.0.0.1:5000/chat/stream.",
        "The request body is conversation_id, message, and mode fast.",
        "The contingency budget is 2 infrastructure retries in total, not per item.",
        "Every POST counts toward 22, including an infrastructure failure.",
        "Do not retry a completed wrong answer.",
        "A legitimate retry uses the same conversation_id.",
        "The wall-clock limit and the socket timeout are both 180 seconds.",
        "Score done.text only.",
        "An empty done.text with the done event present is a completed wrong reply.",
        "Do not concatenate token text into a substitute answer.",
        "If task_type on a completed reply is not exactly general, record it and do not retry.",
        "HTTP status 400 or higher is infrastructure.",
        "A connection failure is infrastructure.",
        "A timeout is infrastructure.",
        "The exact server-error sentence is infrastructure: " + score.SERVER_ERROR_SENTENCE,
        "The same sentence without the period is not infrastructure.",
        "The same sentence with two periods is not infrastructure.",
        "",
        "## Scoring",
        "",
        "Strip the done text.",
        "Then remove at most one trailing period when the key does not already end with a period",
        "and the stripped text ends with exactly one period.",
        "No partial credit.",
        "Extra words, a case mismatch, internal extra whitespace, quotes, and a caveat suffix fail.",
        "Do not award partial credit after observing an incorrect response.",
        "Echo does not grade herself.",
        "",
        "## Phase Two",
        "",
        "Phase Two runs only when the Phase One gate passes.",
        "The delay is 1860 seconds after the latest Phase One finished_at.",
        "Each Phase Two trial uses a new conversation id.",
        "The delayed question does not contain the fact sentence.",
        "Unknown remains an available storage outcome.",
        "Unknown remains an available retrieval outcome.",
        "A correct later answer does not establish storage.",
        "A correct later answer does not establish retrieval.",
        "A memory write does not establish retrieval.",
        "Retrieving only a short key-only echo reply does not count as retrieving the fact.",
        "That combination is not a clean Outcome C or Outcome E.",
        "Item 05 is the only Phase Two closed-set exception.",
        "Its key is the word no, which is inside the yes or no reply instruction.",
        "The item 05 fact sentence must still be absent from the Phase Two prompt.",
        "",
        "## Limitation, not a deviation",
        "",
        "Production fast mode may place session history and up to k=5 memories",
        "older than 30 minutes into the system note.",
        "Phase One is therefore not a note-only input.",
        "This is existing pathway behavior.",
        "Do not disable it.",
        "Do not create DEVIATIONS.md until a deviation exists.",
        "",
        "## Items",
        "",
    ]
    for item in built:
        lines.append(f"### {item['id']}")
        lines.append("")
        lines.append("Fact: " + item["fact_sentence"])
        lines.append("Question: " + item["question"])
        lines.append("Key: " + item["key"])
        lines.append("Phase 1 conversation: " + item["conversation_id_phase1"])
        lines.append("Phase 2 conversation: " + item["conversation_id_phase2"])
        lines.append("")
        lines.append("Phase 1 prompt:")
        lines.append("")
        lines.append("```text")
        lines.append(item["phase1_prompt"])
        lines.append("```")
        lines.append("")
        lines.append("Phase 2 prompt:")
        lines.append("")
        lines.append("```text")
        lines.append(item["phase2_prompt"])
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def _has_kind(hits, kind, name=None):
    for hit in hits:
        if hit["kind"] != kind:
            continue
        if name is None or hit["name"] == name or hit.get("signal") == name:
            return True
    return False


def self_test():
    document = load_key()
    built = build_items(document)
    yes_no = document["tails"]["yes_no"]
    failed = False
    for item_id, hits in scan_built(built):
        report_hits(item_id, hits)
        failed = True
    for item in built:
        problems = phase2_leak_problems(item, yes_no)
        if problems:
            print(
                f"leak item={item['id']} problems={','.join(problems)}",
                file=sys.stderr,
            )
            failed = True
        share = heatmap_general_share(item["phase1_prompt"])
        if share != 1.0:
            print(f"heatmap item={item['id']} general={share}", file=sys.stderr)
            failed = True

    controls = {
        "dispatch": ("Please read the file now.", "dispatch", "read the file"),
        "listing": ("Please list files now.", "listing", "list files"),
        "path": ("Look at  data today.", "path", "data"),
        "heatmap": ("echo", "heatmap", "echo"),
        "ladder_personal": ("personal", "ladder", "personal"),
        "slice": ("how are you built", "slice", "how are you built"),
        "architecture": ("how does your system store this", "architecture", "match"),
    }
    for label, (text, kind, name) in controls.items():
        hits = scan_text(text)
        if not _has_kind(hits, kind, name):
            print(f"control_miss={label}", file=sys.stderr)
            failed = True
    if scan_text("personal") and heatmap_general_share("personal") != 1.0:
        print("control_miss=personal_heatmap_separation", file=sys.stderr)
        failed = True
    seal_strings = (
        "Permit P-19 has the seal date 2026-04-17.",
        "What is the seal date on permit P-19?",
        "Note: Permit P-19 has the seal date 2026-04-17.",
    )
    for text in seal_strings:
        if PATH_TOKEN_RE.search(text) is not None:
            print("control_miss=seal_date_should_be_clean", file=sys.stderr)
            failed = True
    if PATH_TOKEN_RE.search(" data") is None:
        print("control_miss=spaced_data", file=sys.stderr)
        failed = True

    leaked = dict(built[0])
    leaked["phase2_prompt"] = built[0]["phase2_prompt"] + "\n" + built[0]["fact_sentence"]
    leaked["phase2_closed_set_exception"] = False
    if "fact_sentence" not in phase2_leak_problems(leaked, yes_no):
        print("control_miss=synthetic_fact_leak", file=sys.stderr)
        failed = True
    item_05 = next(item for item in built if item["id"] == "05")
    injected = dict(item_05)
    injected["phase2_prompt"] = item_05["phase2_prompt"].replace(
        "Is lane 4 closed?",
        "Is lane 4 not closed?",
        1,
    )
    if "yes_no_remainder" not in phase2_leak_problems(injected, yes_no):
        print("control_miss=item05_not_closed", file=sys.stderr)
        failed = True
    if failed:
        return 1
    print("preflight_self_test=ok")
    return 0


def _seal_exists():
    return os.path.isfile(os.path.join(HERE, "PROTOCOL.sha256"))


def _refuse_if_sealed():
    if _seal_exists():
        print("seal_exists", file=sys.stderr)
        return True
    return False


def emit_items(built):
    payload = {"items": public_items(built)}
    path = os.path.join(HERE, "items.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("emit_items=ok")


def write_protocol(built):
    path = os.path.join(HERE, "PROTOCOL.md")
    text = render_protocol(built)
    if not text.endswith("\n"):
        text += "\n"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    print("write_protocol=ok")


def check():
    items_path = os.path.join(HERE, "items.json")
    protocol_path = os.path.join(HERE, "PROTOCOL.md")
    if not os.path.isfile(items_path) or not os.path.isfile(protocol_path):
        print("preflight_missing", file=sys.stderr)
        return 1
    document = load_key()
    built = build_items(document)
    with open(items_path, encoding="utf-8") as handle:
        item_doc = json.load(handle)
    if item_doc.get("items") != public_items(built):
        print("items_mismatch", file=sys.stderr)
        return 1
    with open(protocol_path, encoding="utf-8") as handle:
        protocol = handle.read()
    for phrase in required_phrases():
        if phrase not in protocol:
            print("protocol_missing_phrase", file=sys.stderr)
            return 1
    yes_no = document["tails"]["yes_no"]
    for item in built:
        if item["phase1_prompt"] not in protocol or item["phase2_prompt"] not in protocol:
            print(f"protocol_missing_prompt item={item['id']}", file=sys.stderr)
            return 1
        if item["fact_sentence"] not in protocol or item["key"] not in protocol:
            print(f"protocol_missing_key item={item['id']}", file=sys.stderr)
            return 1
        problems = phase2_leak_problems(item, yes_no)
        if problems:
            print(
                f"leak item={item['id']} problems={','.join(problems)}",
                file=sys.stderr,
            )
            return 1
    for item_id, hits in scan_built(built):
        report_hits(item_id, hits)
        return 1
    print("preflight_check=ok")
    return 0


def _prepare_or_fail():
    document = load_key()
    built = build_items(document)
    scanned = scan_built(built)
    if scanned:
        for item_id, hits in scanned:
            report_hits(item_id, hits)
        return None
    yes_no = document["tails"]["yes_no"]
    for item in built:
        problems = phase2_leak_problems(item, yes_no)
        if problems:
            print(
                f"leak item={item['id']} problems={','.join(problems)}",
                file=sys.stderr,
            )
            return None
    return built


def main(argv):
    if "--self-test" in argv:
        return self_test()
    writing = [flag for flag in ("--emit-items", "--write-protocol", "--print-prompts") if flag in argv]
    if writing and _refuse_if_sealed():
        return 2
    if "--check" in argv and not writing:
        return check()
    if not writing and "--check" not in argv:
        print(
            "usage: preflight.py --self-test | --check | --emit-items | --write-protocol | --print-prompts",
            file=sys.stderr,
        )
        return 2
    built = _prepare_or_fail()
    if built is None:
        return 1
    if "--print-prompts" in argv:
        for item in built:
            print(item["id"])
            print(item["phase1_prompt"])
            print("---")
            print(item["phase2_prompt"])
            print("---")
        print("print_prompts=ok")
    if "--emit-items" in argv:
        emit_items(built)
    if "--write-protocol" in argv:
        write_protocol(built)
    if "--check" in argv:
        return check()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
