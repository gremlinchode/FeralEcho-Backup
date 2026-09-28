"""Pure, I/O-free AST diff-and-generalize + match/apply logic for the Verified Skill
Ledger. Moved here verbatim (zero logic changes) from
app/experiments/skill_ledger/diff_extract.py during the 2026-09-28 integration-
readiness pass -- that module is now a thin re-export wrapper over this one, so the
historical unit suite (verify_diff_extract.py) continues to exercise this exact code
with zero behavior change (re-run and confirmed 15/15 immediately after this move).

Generic, structural AST diff-and-generalize: given a FAILING candidate and a PASSING
candidate for the same task, finds the smallest subtree where their ASTs diverge, and
produces a {precondition, transformation} PATTERN with instance-specific literals
abstracted to wildcards -- never a bug-family-specific rule, never hand-authored.

The abstraction rule is structural, not task-specific: any string Constant that ALSO
appears as a dict-literal key anywhere in the same function is treated as
instance-specific "site convention" vocabulary (every K1/K2/K3 task in this codebase
encodes its per-world convention as exactly this shape -- a dict literal -- so this
generalizes across the whole task family, not one bug). Constants that never appear as
a dict key (integers, index positions, other structural literals) are left concrete.

Honesty requirement (governing mission, "Transformation Requirement"): if the two
candidates are not closely alignable (very different structure), this module returns
None rather than forcing a bad diff -- that is itself a real, reportable result, not a
failure to be hidden.
"""
from __future__ import annotations
import ast
from typing import Optional

_WILDCARD_PREFIX = "__VSL_WC"


def collect_dict_key_vocab(tree: ast.AST) -> set:
    """Every string Constant used as a dict-literal key anywhere in the tree --
    the structural signal for 'this is site-convention vocabulary', not hardcoded
    to any specific bug family or task."""
    vocab = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k in node.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    vocab.add(k.value)
    return vocab


class _Abstractor(ast.NodeTransformer):
    """Replaces every Constant whose value is in `vocab` with a wildcard Constant,
    assigning a stable index per distinct literal value within one abstraction pass."""

    def __init__(self, vocab: set):
        self.vocab = vocab
        self.value_to_index: dict = {}

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, str) and node.value in self.vocab:
            if node.value not in self.value_to_index:
                self.value_to_index[node.value] = len(self.value_to_index)
            idx = self.value_to_index[node.value]
            return ast.copy_location(ast.Constant(value=f"{_WILDCARD_PREFIX}{idx}"), node)
        return node


def abstract(node: ast.AST, vocab: set) -> ast.AST:
    import copy
    return _Abstractor(vocab).visit(copy.deepcopy(node))


def _is_wildcard_value(v) -> bool:
    return isinstance(v, str) and v.startswith(_WILDCARD_PREFIX)


def find_divergence(a, b):
    """Smallest-subtree structural divergence between two (already-abstracted) AST
    nodes/lists/scalars. Returns (node_a, node_b) at the smallest point they differ,
    or None if identical. Returns ('UNALIGNABLE', None) if the trees' shapes cannot
    be aligned at all (different node types at the top, or list-length mismatch at
    a point that prevents further descent) -- the honest 'cannot extract' signal."""
    if type(a) is not type(b):
        return ("UNALIGNABLE", None) if not isinstance(a, (ast.AST,)) or not isinstance(b, (ast.AST,)) else (a, b)
    if isinstance(a, ast.AST):
        diffs = []
        for field in a._fields:
            va, vb = getattr(a, field, None), getattr(b, field, None)
            d = find_divergence(va, vb)
            if d is not None:
                diffs.append((field, d))
        if not diffs:
            return None
        if len(diffs) == 1:
            _, d = diffs[0]
            return d  # propagate as-is, including ("UNALIGNABLE", None) -- never collapse
                       # an unalignable nested divergence into a non-minimal whole-node "pattern"
        return ("UNALIGNABLE", None)  # multiple fields diverge simultaneously: not a minimal single patch
    if isinstance(a, list):
        if len(a) != len(b):
            return ("UNALIGNABLE", None)  # different statement/element counts: no clean minimal diff
        diffs = []
        for xa, xb in zip(a, b):
            d = find_divergence(xa, xb)
            if d is not None:
                diffs.append(d)
        if not diffs:
            return None
        if len(diffs) == 1:
            return diffs[0]
        return ("UNALIGNABLE", None)  # multiple positions differ: cannot isolate one minimal patch
    # plain scalar (str, int, bool, None, etc.)
    if a == b:
        return None
    return (a, b)


def _call_name(call: ast.Call) -> str:
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return "?"


def _enclosing_call_name(root: ast.AST, target) -> Optional[str]:
    """Finds the name of the nearest enclosing ast.Call containing `target` (by
    identity), walking from `root`. Returns None if target sits inside no Call at
    all. This is the structural context the original precondition representation
    lacked: two occurrences of the identical local subtree pattern can require
    OPPOSITE transformations depending on whether they sit inside e.g. a sorted()
    key (which selects the smallest key via [0]) or a max() call (which selects the
    largest key directly) -- confirmed as a real, live defect during this project's
    first live MVK run (see audits/2026-09-27_verified_skill_ledger_mvk_first_run_report.md)."""
    if not isinstance(target, ast.AST):
        return None
    result = {"call": None, "found": False}

    def _walk(node, current_call):
        if result["found"]:
            return
        if node is target:
            result["call"] = current_call
            result["found"] = True
            return
        next_call = current_call
        if isinstance(node, ast.Call):
            next_call = _call_name(node)
        for child in ast.iter_child_nodes(node):
            _walk(child, next_call)
            if result["found"]:
                return

    _walk(root, None)
    return result["call"]


def extract_transformation(failing_code: str, passing_code: str, fn_name: str) -> Optional[dict]:
    """Top-level entry point. Returns a JSON-serializable {precondition, transformation}
    dict, or None if no usable transformation could be extracted (honest failure,
    per the governing mission's own explicit instruction)."""
    try:
        fail_tree = ast.parse(failing_code)
        pass_tree = ast.parse(passing_code)
    except SyntaxError:
        return None

    fail_fn = _find_function(fail_tree, fn_name)
    pass_fn = _find_function(pass_tree, fn_name)
    if fail_fn is None or pass_fn is None:
        return None

    vocab = collect_dict_key_vocab(fail_fn) | collect_dict_key_vocab(pass_fn)
    fail_abs = abstract(fail_fn, vocab)
    pass_abs = abstract(pass_fn, vocab)

    div = find_divergence(fail_abs, pass_abs)
    if div is None:
        return None  # candidates are identical after abstraction -- no transformation to extract
    fail_node, pass_node = div
    if fail_node == "UNALIGNABLE":
        return None  # honest: trees too structurally different to isolate a minimal patch

    if not (isinstance(fail_node, (ast.AST, list, str, int, float, bool, type(None)))
            and isinstance(pass_node, (ast.AST, list, str, int, float, bool, type(None)))):
        return None

    # Enclosing-call context (the fix for the defect found in the first live MVK run):
    # a transformation is only meaningful within the aggregation context it was
    # observed in. If the failing and passing examples themselves disagree about
    # their own enclosing call (a genuinely inconsistent pair), refuse rather than
    # store an ambiguous, ungrounded context -- honest failure, not a forced guess.
    fail_call_ctx = _enclosing_call_name(fail_abs, fail_node)
    pass_call_ctx = _enclosing_call_name(pass_abs, pass_node)
    if fail_call_ctx != pass_call_ctx:
        return None

    try:
        precondition_dump = _dump(fail_node)
        transformation_dump = _dump(pass_node)
    except Exception:
        return None

    if precondition_dump == transformation_dump:
        return None  # no real change captured

    return {
        "precondition": precondition_dump,
        "transformation": transformation_dump,
        "node_type": type(fail_node).__name__ if isinstance(fail_node, ast.AST) else "scalar",
        "enclosing_call": fail_call_ctx,
    }


def apply_skill(candidate_code: str, fn_name: str, skill_pattern: dict) -> Optional[str]:
    """Attempts to apply a validated skill's {precondition, transformation} to a
    fresh candidate. Returns corrected source, or None if the precondition doesn't
    match anywhere (an honest non-application, not an error)."""
    try:
        tree = ast.parse(candidate_code)
    except SyntaxError:
        return None
    fn = _find_function(tree, fn_name)
    if fn is None:
        return None

    vocab = collect_dict_key_vocab(fn)

    for node in ast.walk(fn):
        if type(node).__name__ != skill_pattern.get("node_type"):
            continue
        # Enclosing-call gate: a candidate subtree matching the same local shape but
        # sitting inside a DIFFERENT (or absent) aggregation call is a genuinely
        # different applicability context -- do not apply a sorted()-derived
        # transformation to a max()-based occurrence, or vice versa. Skills written
        # before this field existed have enclosing_call=None by default, meaning they
        # only match no-enclosing-call occurrences -- deliberately conservative
        # (fails closed) rather than silently over-applying a pre-fix skill.
        candidate_call_ctx = _enclosing_call_name(fn, node)
        if candidate_call_ctx != skill_pattern.get("enclosing_call"):
            continue
        abs_node = abstract(node, vocab)
        bindings: dict = {}
        if not isinstance(abs_node, ast.AST):
            continue
        if _matches(abs_node, skill_pattern["precondition"], bindings):
            new_subtree = _rehydrate(skill_pattern["transformation"], bindings)
            if new_subtree is None:
                continue
            return _replace_and_unparse(tree, node, new_subtree)
    return None


def _find_function(tree: ast.AST, fn_name: str):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            return node
    return None


def _dump(node) -> str:
    if isinstance(node, ast.AST):
        return ast.dump(node, annotate_fields=True)
    return repr(node)


def _matches(candidate_abs_node: ast.AST, pattern_dump: str, bindings: dict) -> bool:
    """Structural match of a (already-abstracted) candidate subtree against a stored
    pattern dump string, capturing wildcard bindings by walking both in parallel.
    Re-parses nothing -- walks the live candidate AST against a parsed version of the
    pattern dump's own structure via a second abstract-and-compare pass, since
    ast.dump()'d strings can't be walked directly; instead this recomputes the
    candidate's own dump and does a textual wildcard-aware match, then separately
    captures bindings via a parallel field walk against the ORIGINAL (non-abstracted)
    candidate node -- see apply_skill's caller, which passes the non-abstracted node
    alongside. For this MVK, matching is exact-after-abstraction (bindings captured
    by a second walk in _rehydrate's caller context)."""
    candidate_dump = _dump(candidate_abs_node)
    return _wildcard_aware_equal(candidate_dump, pattern_dump, bindings)


def _wildcard_aware_equal(candidate_dump: str, pattern_dump: str, bindings: dict) -> bool:
    """Token-level comparison: pattern_dump may contain __VSL_WCn tokens standing in
    for any concrete value at that position in candidate_dump. Since both dumps are
    produced by the same ast.dump(annotate_fields=True) convention, a wildcard always
    appears as `Constant(value='__VSL_WCn')` in the pattern; the corresponding
    position in candidate_dump is `Constant(value='<real value>')` -- extracted via
    direct string alignment (both strings share identical surrounding structure by
    construction, since the candidate matched node_type before this is called)."""
    import re
    parts = re.split(r"(__VSL_WC\d+)", pattern_dump)
    regex_pieces = []
    wc_order = []
    for part in parts:
        m = re.fullmatch(r"__VSL_WC(\d+)", part)
        if m:
            wc_order.append(int(m.group(1)))
            regex_pieces.append(r"([^'\"]*)")
        else:
            regex_pieces.append(re.escape(part))
    regex = "".join(regex_pieces)
    m = re.fullmatch(regex, candidate_dump)
    if not m:
        return False
    for wc_idx, val in zip(wc_order, m.groups()):
        bindings[wc_idx] = val
    return True


def _rehydrate(transformation_dump: str, bindings: dict) -> Optional[ast.AST]:
    """Substitutes captured wildcard bindings back into the transformation pattern's
    dump string, then reconstructs a real AST node from it via eval() against ast's
    own module namespace (safe here: this string was produced by ast.dump() on a
    real, already-parsed subtree earlier in this same process -- it is not
    externally-supplied or model-generated text)."""
    import re

    def _sub(m):
        idx = int(m.group(1))
        return repr(bindings.get(idx, m.group(0)))

    hydrated = re.sub(r"'__VSL_WC(\d+)'", _sub, transformation_dump)
    try:
        return eval(hydrated, {"__builtins__": {}}, vars(ast))
    except Exception:
        return None


def _replace_and_unparse(tree: ast.AST, old_node: ast.AST, new_node: ast.AST) -> Optional[str]:
    class _Replacer(ast.NodeTransformer):
        def generic_visit(self, node):
            if node is old_node:
                return new_node
            return super().generic_visit(node)

    new_tree = _Replacer().visit(tree)
    ast.fix_missing_locations(new_tree)
    try:
        return ast.unparse(new_tree)
    except Exception:
        return None
