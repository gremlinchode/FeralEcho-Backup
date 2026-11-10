"""Fixed procedure grammar.

This is a deterministic planner over a small set of problem classes.
It is not a language-model interpretation of free text.
"""

TEMPLATES = {
    "copy_value": [
        {"op": "read", "slot": "src", "save": "value"},
        {"op": "write", "slot": "dst", "from": "value"},
    ],
    "pipeline_sum": [
        {"op": "read", "slot": "a", "save": "a"},
        {"op": "read", "slot": "b", "save": "b"},
        {"op": "add", "from": ["a", "b"], "save": "value"},
        {"op": "write", "slot": "dst", "from": "value"},
    ],
    "fold_lines": [
        {"op": "sum_lines", "slot": "src", "save": "value"},
        {"op": "write", "slot": "dst", "from": "value"},
    ],
    "make_then_write": [
        {"op": "read", "slot": "src", "save": "value"},
        {"op": "create_dir", "slot": "parent"},
        {"op": "write", "slot": "dst", "from": "value"},
    ],
    "resolve_conflict": [
        {"op": "read", "slot": "left", "save": "left"},
        {"op": "read", "slot": "right", "save": "right"},
        {"op": "compare"},
        {"op": "read", "slot": "authority", "save": "value", "only_if": "conflict"},
        {"op": "write", "slot": "dst", "from": "value"},
    ],
    "join_pair": [
        {"op": "read", "slot": "a", "save": "a"},
        {"op": "read", "slot": "b", "save": "b"},
        {"op": "join"},
        {"op": "write", "slot": "dst", "from": "value"},
    ],
}

SCALE_SUFFIX = "__scale"


def base_class(problem_class: str) -> str:
    if problem_class.endswith(SCALE_SUFFIX):
        return problem_class[: -len(SCALE_SUFFIX)]
    return problem_class


def insert_scale_before_write(trace):
    scaled = []
    for step in trace:
        if step["op"] == "write":
            scaled.append({"op": "scale", "slot": "k", "save": "value"})
        scaled.append(dict(step))
    return scaled


def learning_label(lesson, slots):
    if lesson.get("example_slots") == slots:
        return "remember"
    return "procedure_reuse"


def build_plan(brief, lessons, lessons_enabled: bool):
    """Return (steps, plan_source, learning_applied, status_if_unplanned).

    Lessons apply only on an exact problem-class match, plus the one
    pre-registered composition `base__scale` which inserts a multiply
    before the stored base trace's write. A lesson from one class is
    not applied to a different class.
    """
    problem_class = brief["problem_class"]
    slots = brief["slots"]
    hypothesis = brief.get("hypothesis_class")
    lessons = lessons or {}

    if problem_class.endswith(SCALE_SUFFIX):
        base = base_class(problem_class)
        lesson = lessons.get(base) if lessons_enabled else None
        if not lesson:
            return [], "no_procedure", "none", "unknown"
        steps = _materialize(insert_scale_before_write(lesson["trace"]), slots)
        return steps, "programmed_composition", "programmed_composition", None

    lesson = lessons.get(problem_class) if lessons_enabled else None
    if lesson:
        steps = _materialize(lesson["trace"], slots)
        return steps, "lesson", learning_label(lesson, slots), None

    template = TEMPLATES.get(problem_class)
    if template is None:
        return [], "no_procedure", "none", "unknown"

    raw = []
    if hypothesis and hypothesis != problem_class and hypothesis in TEMPLATES:
        probe = dict(TEMPLATES[hypothesis][0])
        probe["probe"] = True
        raw.append(probe)
    raw.extend(template)
    return _materialize(raw, slots), "library", "none", None


def _materialize(trace, slots):
    steps = []
    for index, step in enumerate(trace):
        item = dict(step)
        item["id"] = f"s{index}"
        item["state"] = "pending"
        if "slot" in item:
            key = item["slot"]
            if key not in slots:
                item["path"] = None
                item["missing_slot"] = key
            else:
                item["path"] = slots[key]
        steps.append(item)
    return steps
