"""Isolated checks for per-message conversation-memory outcomes.

Imports only app.core.memory_write_outcome. Other modules are read as
source text and parsed. This file does not import the memory bridge,
construct VectorMemory, construct a Flask app, post to a server, or open
files under memory/.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.memory_write_outcome import (  # noqa: E402
    ACCEPTED,
    EMBED_SHAPE,
    FAILED,
    PERSIST_FAILED,
    PERSISTED,
    REJECTED,
    TRANSPORT_OR_HANDLER_ERROR,
    VALIDATOR_BLOCK,
    MemoryWriteOutcome,
    classify_memory_write,
    client_outcome_from_body,
    client_outcome_log_line,
    conversation_turn_response,
    interpret_client_response,
)

FAILURES: list[str] = []
PURE = 0
AST_CHECKS = 0

PLANT_TEXT = "PLANT_TEXT"
PLANT_ID = "PLANT_ID"
PLANT_HASH = "PLANT_HASH"
PLANT_SIGNAL = "PLANT_SIGNAL"
PLANT_PATH = "PLANT_PATH"
PLANTS = (PLANT_TEXT, PLANT_ID, PLANT_HASH, PLANT_SIGNAL, PLANT_PATH)

FORBIDDEN_MODULES = (
    "app.core.memory_bridge",
    "app.lib.vector_memory",
    "app.core.conversation_service",
    "run",
    "flask",
    "faiss",
    "numpy",
)


def check(name: str, cond: bool, bucket: str) -> None:
    global PURE, AST_CHECKS
    if bucket == "pure":
        PURE += 1
    else:
        AST_CHECKS += 1
    if not cond:
        FAILURES.append(name)


def no_plants(text: str) -> bool:
    return all(token not in text for token in PLANTS)


def load_tree(rel: str) -> ast.AST:
    return ast.parse((ROOT / rel).read_text(encoding="utf-8"))


def call_name(node: ast.AST) -> str:
    if not isinstance(node, ast.Call):
        return ""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        base = func.value
        if isinstance(base, ast.Name):
            return f"{base.id}.{func.attr}"
        if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name):
            return f"{base.value.id}.{base.attr}.{func.attr}"
    return ""


def keyword_map(call: ast.Call) -> dict[str, ast.AST]:
    return {kw.arg: kw.value for kw in call.keywords if kw.arg}


def _is_status_not_200(test: ast.AST) -> bool:
    return (
        isinstance(test, ast.Compare)
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.NotEq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == 200
        and isinstance(test.left, ast.Attribute)
        and test.left.attr == "status_code"
    )


def const_strings(node: ast.AST) -> list[str]:
    found = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            found.append(child.value)
    return found


def find_function(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def find_class(tree: ast.AST, name: str) -> ast.ClassDef | None:
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def find_method(cls: ast.ClassDef, name: str) -> ast.FunctionDef | None:
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def is_add_to_vector_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id == "add_to_vector_memory":
        return True
    return isinstance(func, ast.Attribute) and func.attr == "add_to_vector_memory"


def is_vector_memory_add(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "vector_memory"
    )


def is_self_persist_call(node: ast.AST) -> bool:
    return call_name(node) == "self._persist"


def status_returns(nodes: list[ast.stmt]) -> list[tuple[ast.Return, object]]:
    found: list[tuple[ast.Return, object]] = []
    for stmt in nodes:
        if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Tuple) and stmt.value.elts:
            last = stmt.value.elts[-1]
            if isinstance(last, ast.Constant):
                found.append((stmt, last.value))
        elif isinstance(stmt, ast.If):
            found.extend(status_returns(stmt.body))
            found.extend(status_returns(stmt.orelse))
        elif isinstance(stmt, ast.Try):
            found.extend(status_returns(stmt.body))
            for handler in stmt.handlers:
                found.extend(status_returns(handler.body))
            found.extend(status_returns(stmt.orelse))
            found.extend(status_returns(stmt.finalbody))
    return found


def dict_keys(node: ast.AST) -> list[str] | None:
    if not isinstance(node, ast.Dict):
        return None
    keys = []
    for key in node.keys:
        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
            return None
        keys.append(key.value)
    return keys


def half(outcome: str, reason: str, persisted: bool) -> MemoryWriteOutcome:
    return MemoryWriteOutcome(outcome, reason, persisted)


def test_pure_mapping() -> None:
    cases = (
        ("rejected_ignores_persist_true", False, 1, True, REJECTED, VALIDATOR_BLOCK, False),
        ("accepted_only_persist_true", True, 1, True, ACCEPTED, PERSISTED, True),
        ("persist_false_after_in_memory_mutation", True, 1, False, FAILED, PERSIST_FAILED, False),
        ("persist_none", True, 1, None, FAILED, PERSIST_FAILED, False),
        ("persist_int_one_is_not_true", True, 1, 1, FAILED, PERSIST_FAILED, False),
        ("rows_zero", True, 0, True, FAILED, EMBED_SHAPE, False),
        ("rows_two", True, 2, True, FAILED, EMBED_SHAPE, False),
        ("rows_bool_true", True, True, True, FAILED, EMBED_SHAPE, False),
        ("rows_none", True, None, None, FAILED, EMBED_SHAPE, False),
        ("rows_none_persist_true", True, None, True, FAILED, EMBED_SHAPE, False),
    )
    for name, allowed, rows, persist_ok, outcome, reason, persisted in cases:
        result = classify_memory_write(
            validator_allowed=allowed,
            embed_rows=rows,
            persist_ok=persist_ok,
        )
        check(f"pure.{name}.outcome", result.outcome == outcome, "pure")
        check(f"pure.{name}.reason", result.reason == reason, "pure")
        check(f"pure.{name}.persisted", result.persisted is persisted, "pure")
        check(f"pure.{name}.not_accepted_on_failure", outcome == ACCEPTED or result.outcome != ACCEPTED, "pure")

    rejected = classify_memory_write(validator_allowed=False, embed_rows=1, persist_ok=True)
    failed = classify_memory_write(validator_allowed=True, embed_rows=1, persist_ok=False)
    accepted = classify_memory_write(validator_allowed=True, embed_rows=1, persist_ok=True)
    check("pure.truthy_rejected", bool(rejected) is True, "pure")
    check("pure.truthy_failed", bool(failed) is True, "pure")
    check("pure.truthy_accepted", bool(accepted) is True, "pure")
    check("pure.as_dict_keys", set(accepted.as_dict()) == {"outcome", "reason", "persisted"}, "pure")

    bad_triples = (
        (ACCEPTED, PERSISTED, False),
        (ACCEPTED, PERSIST_FAILED, True),
        (REJECTED, VALIDATOR_BLOCK, True),
        (FAILED, EMBED_SHAPE, True),
        (ACCEPTED, VALIDATOR_BLOCK, True),
        (FAILED, PERSISTED, False),
    )
    for outcome, reason, persisted in bad_triples:
        raised = False
        try:
            MemoryWriteOutcome(outcome, reason, persisted)
        except ValueError:
            raised = True
        check(f"pure.reject_inconsistent.{outcome}.{reason}.{persisted}", raised, "pure")

    raised = False
    try:
        MemoryWriteOutcome(ACCEPTED, PERSISTED, 1)  # type: ignore[arg-type]
    except ValueError:
        raised = True
    check("pure.reject_persisted_int", raised, "pure")


def test_pure_response_and_log() -> None:
    rejected = half(REJECTED, VALIDATOR_BLOCK, False)
    accepted = half(ACCEPTED, PERSISTED, True)
    failed_shape = half(FAILED, EMBED_SHAPE, False)
    failed_persist = half(FAILED, PERSIST_FAILED, False)

    mixed = conversation_turn_response(rejected, accepted, True, "standing")
    check("pure.mixed.status", mixed["status"] == "ok", "pure")
    check("pure.mixed.thought", mixed["thought_provoking"] is True, "pure")
    check("pure.mixed.retention", mixed["retention"] == "standing", "pure")
    check("pure.mixed.user_rejected", mixed["user"]["outcome"] == REJECTED, "pure")
    check("pure.mixed.echo_accepted", mixed["echo"]["outcome"] == ACCEPTED, "pure")
    check("pure.mixed.distinct", mixed["user"] != mixed["echo"], "pure")
    check("pure.mixed.top_keys", set(mixed) == {"status", "thought_provoking", "retention", "user", "echo"}, "pure")
    check("pure.mixed.user_keys", set(mixed["user"]) == {"outcome", "reason", "persisted"}, "pure")
    check("pure.mixed.echo_keys", set(mixed["echo"]) == {"outcome", "reason", "persisted"}, "pure")
    check("pure.mixed.no_plants", no_plants(json.dumps(mixed)), "pure")

    both_rejected = conversation_turn_response(rejected, half(REJECTED, VALIDATOR_BLOCK, False), False, "standard")
    check("pure.both_rejected.status", both_rejected["status"] == "ok", "pure")
    check("pure.both_rejected.retention", both_rejected["retention"] == "standard", "pure")
    check("pure.both_rejected.user", both_rejected["user"]["outcome"] == REJECTED, "pure")
    check("pure.both_rejected.echo", both_rejected["echo"]["outcome"] == REJECTED, "pure")

    both_failed = conversation_turn_response(failed_shape, failed_persist, False, "standard")
    check("pure.both_failed.status", both_failed["status"] == "ok", "pure")
    check("pure.both_failed.user_persisted", both_failed["user"]["persisted"] is False, "pure")
    check("pure.both_failed.echo_persisted", both_failed["echo"]["persisted"] is False, "pure")
    check("pure.both_failed.reasons_distinct", both_failed["user"]["reason"] != both_failed["echo"]["reason"], "pure")

    raised = False
    try:
        conversation_turn_response(None, accepted, False, "standard")  # type: ignore[arg-type]
    except TypeError:
        raised = True
    check("pure.response_rejects_none", raised, "pure")

    planted = {
        "status": "ok",
        "user_msg": PLANT_TEXT,
        "echo_response": PLANT_TEXT,
        "id": PLANT_ID,
        "hash": PLANT_HASH,
        "signal": PLANT_SIGNAL,
        "path": PLANT_PATH,
        "user": {
            "outcome": REJECTED,
            "reason": VALIDATOR_BLOCK,
            "persisted": False,
            "text": PLANT_TEXT,
            "id": PLANT_ID,
        },
        "echo": {
            "outcome": ACCEPTED,
            "reason": PERSISTED,
            "persisted": True,
            "signal": PLANT_SIGNAL,
            "path": PLANT_PATH,
        },
    }
    line = client_outcome_log_line(planted)
    sanitized = client_outcome_from_body(planted)
    expected = (
        f"user={REJECTED} reason={VALIDATOR_BLOCK} "
        f"echo={ACCEPTED} reason={PERSISTED}"
    )
    check("pure.log_line_exact", line == expected, "pure")
    check("pure.log_line_no_plants", line is not None and no_plants(line), "pure")
    check("pure.sanitized_no_plants", sanitized is not None and no_plants(json.dumps(sanitized)), "pure")
    check(
        "pure.sanitized_keys",
        sanitized is not None
        and set(sanitized["user"]) == {"outcome", "reason", "persisted"}
        and set(sanitized["echo"]) == {"outcome", "reason", "persisted"},
        "pure",
    )

    both_ok = {
        "user_msg": PLANT_TEXT,
        "user": {"outcome": ACCEPTED, "reason": PERSISTED, "persisted": True, "text": PLANT_TEXT},
        "echo": {"outcome": ACCEPTED, "reason": PERSISTED, "persisted": True, "id": PLANT_ID},
    }
    quiet_line, quiet_body = interpret_client_response(200, both_ok)
    check("pure.both_accepted_log_silent", quiet_line is None, "pure")
    check("pure.both_accepted_body", quiet_body is not None and no_plants(json.dumps(quiet_body)), "pure")

    inconsistent = {
        "user_msg": PLANT_TEXT,
        "user": {"outcome": ACCEPTED, "reason": PERSISTED, "persisted": False, "text": PLANT_TEXT},
        "echo": {"outcome": ACCEPTED, "reason": PERSISTED, "persisted": True},
    }
    bad_line, bad_body = interpret_client_response(200, inconsistent)
    check("pure.inconsistent_token", bad_line == TRANSPORT_OR_HANDLER_ERROR, "pure")
    check("pure.inconsistent_no_body", bad_body is None, "pure")
    check("pure.inconsistent_no_plants", bad_line is not None and no_plants(bad_line), "pure")

    for code in (400, 403, 500):
        token, body = interpret_client_response(code, planted)
        check(f"pure.status_{code}_token", token == TRANSPORT_OR_HANDLER_ERROR, "pure")
        check(f"pure.status_{code}_no_body", body is None, "pure")
        check(f"pure.status_{code}_no_plants", token is not None and no_plants(token), "pure")


def test_outcome_module_ast(tree: ast.AST) -> None:
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    modules = []
    for node in imports:
        if isinstance(node, ast.ImportFrom):
            modules.append(node.module)
        else:
            modules.extend(alias.name for alias in node.names)
    check("ast.outcome_imports", modules == ["__future__", "dataclasses"], "ast")
    opens = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and call_name(node) == "open"]
    check("ast.outcome_no_open", opens == [], "ast")
    cls = find_class(tree, "MemoryWriteOutcome")
    methods = [node.name for node in cls.body if isinstance(node, ast.FunctionDef)] if cls else []
    check("ast.outcome_no_bool", "__bool__" not in methods, "ast")
    classify = find_function(tree, "classify_memory_write")
    loops = [
        node for node in ast.walk(classify) if isinstance(node, (ast.For, ast.While, ast.Try))
    ] if classify else [None]
    check("ast.classify_no_retry_or_catch", classify is not None and loops == [], "ast")


def test_add_to_vector_memory_ast(tree: ast.AST) -> None:
    fn = find_function(tree, "add_to_vector_memory")
    check("ast.add_fn", fn is not None, "ast")
    if fn is None:
        return
    doc = ast.get_docstring(fn) or ""
    check("ast.add_doc_outcome", ".outcome" in doc, "ast")
    check("ast.add_doc_truthiness", "truthiness" in doc, "ast")
    check("ast.add_doc_ntotal", "ntotal" in doc, "ast")
    check(
        "ast.add_no_try",
        not any(isinstance(node, ast.Try) for node in ast.walk(fn)),
        "ast",
    )
    check(
        "ast.add_no_loop",
        not any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(fn)),
        "ast",
    )
    returns = [stmt for stmt in ast.walk(fn) if isinstance(stmt, ast.Return)]
    check("ast.add_three_returns", len(returns) == 3, "ast")
    check(
        "ast.add_returns_are_classify",
        all(call_name(stmt.value) == "classify_memory_write" for stmt in returns if stmt.value),
        "ast",
    )

    def classify_kw(stmt: ast.Return, name: str) -> ast.AST | None:
        if not isinstance(stmt.value, ast.Call):
            return None
        return keyword_map(stmt.value).get(name)

    false_returns = []
    one_row_returns = []
    for stmt in returns:
        allowed = classify_kw(stmt, "validator_allowed")
        rows = classify_kw(stmt, "embed_rows")
        if isinstance(allowed, ast.Constant) and allowed.value is False:
            false_returns.append(stmt)
        if isinstance(rows, ast.Constant) and rows.value == 1:
            one_row_returns.append(stmt)
        keys = set(keyword_map(stmt.value).keys()) if isinstance(stmt.value, ast.Call) else set()
        check(
            "ast.classify_keywords_only",
            keys <= {"validator_allowed", "embed_rows", "persist_ok"},
            "ast",
        )
    embeds = [node for node in ast.walk(fn) if call_name(node) == "embed_text"]
    check("ast.one_embed", len(embeds) == 1 and bool(embeds[0].args) and isinstance(embeds[0].args[0], ast.Name) and embeds[0].args[0].id == "text", "ast")
    check("ast.one_false_return", len(false_returns) == 1, "ast")
    check("ast.one_row_return", len(one_row_returns) == 1, "ast")
    if false_returns and embeds:
        check("ast.reject_before_embed", false_returns[0].lineno < embeds[0].lineno, "ast")
    assigns = [
        node for node in ast.walk(fn)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "persist_ok"
        and is_vector_memory_add(node.value)
    ]
    check("ast.one_persist_ok_assign", len(assigns) == 1, "ast")
    if assigns and one_row_returns:
        check("ast.classify_after_add", assigns[0].lineno < one_row_returns[0].lineno, "ast")

    parents = parent_map(tree)
    vm_adds = [node for node in ast.walk(tree) if is_vector_memory_add(node)]
    expr_adds = [node for node in vm_adds if isinstance(parents.get(node), ast.Expr)]
    assigned_adds = [node for node in vm_adds if isinstance(parents.get(node), ast.Assign)]
    check("ast.vm_add_count", len(vm_adds) == 5, "ast")
    check("ast.vm_add_ignored", len(expr_adds) == 4, "ast")
    check("ast.vm_add_assigned", len(assigned_adds) == 1, "ast")


def test_vector_memory_ast(tree: ast.AST) -> None:
    cls = find_class(tree, "VectorMemory")
    check("ast.vector_class", cls is not None, "ast")
    if cls is None:
        return
    add = find_method(cls, "add")
    persist = find_method(cls, "_persist")
    check("ast.add_method", add is not None and persist is not None, "ast")
    if add is None or persist is None:
        return
    check("ast.add_method_no_try", not any(isinstance(node, ast.Try) for node in ast.walk(add)), "ast")
    check("ast.add_method_no_while", not any(isinstance(node, ast.While) for node in ast.walk(add)), "ast")
    index_adds = [node for node in ast.walk(add) if call_name(node) == "self.index.add"]
    check("ast.index_add_remains", len(index_adds) == 1, "ast")
    tail = None
    for index, stmt in enumerate(add.body):
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and stmt.targets[0].id == "persisted"
            and is_self_persist_call(stmt.value)
        ):
            tail = add.body[index:index + 3]
            break
    check("ast.persist_tail_len", tail is not None and len(tail) == 3, "ast")
    if tail and len(tail) == 3:
        info = tail[1]
        logged = const_strings(info)
        check(
            "ast.added_log_unchanged",
            isinstance(info, ast.Expr)
            and "Added " in logged
            and " items to VectorMemory and persisted data." in logged,
            "ast",
        )
        check(
            "ast.add_returns_persisted",
            isinstance(tail[2], ast.Return)
            and isinstance(tail[2].value, ast.Name)
            and tail[2].value.id == "persisted",
            "ast",
        )
        if index_adds:
            check("ast.index_add_before_persist", index_adds[0].lineno < tail[0].lineno, "ast")

    check(
        "ast.persist_no_loop",
        not any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(persist)),
        "ast",
    )
    tries = [node for node in persist.body if isinstance(node, ast.Try)]
    check("ast.persist_one_try", len(tries) == 1, "ast")
    if len(tries) != 1:
        return
    body_calls = [
        node
        for stmt in tries[0].body
        for node in ast.walk(stmt)
        if isinstance(node, ast.Call)
    ]
    body_calls.sort(key=lambda node: (node.lineno, node.col_offset))
    dumps = [node for node in body_calls if call_name(node) == "json.dump"]
    replaces = [node for node in body_calls if call_name(node) == "os.replace"]
    writes = [node for node in body_calls if call_name(node) == "faiss.write_index"]
    check("ast.persist_dump", len(dumps) == 1, "ast")
    check("ast.persist_two_replaces", len(replaces) == 2, "ast")
    check("ast.persist_one_write", len(writes) == 1, "ast")
    if len(dumps) == 1 and len(replaces) == 2 and len(writes) == 1:
        check("ast.meta_before_index", dumps[0].lineno < replaces[0].lineno < writes[0].lineno < replaces[1].lineno, "ast")
        first_target = replaces[0].args[1] if len(replaces[0].args) > 1 else None
        second_target = replaces[1].args[1] if len(replaces[1].args) > 1 else None
        check(
            "ast.replace_targets",
            isinstance(first_target, ast.Attribute)
            and first_target.attr == "meta_path"
            and isinstance(second_target, ast.Attribute)
            and second_target.attr == "index_path",
            "ast",
        )
    true_returns = [
        node for node in ast.walk(tries[0])
        if isinstance(node, ast.Return)
        and isinstance(node.value, ast.Constant)
        and node.value.value is True
        and node.lineno <= tries[0].body[-1].end_lineno
    ]
    # Returns nested in the try body are the success path. Handler returns are separate.
    try_returns = [
        node
        for stmt in tries[0].body
        for node in ast.walk(stmt)
        if isinstance(node, ast.Return)
    ]
    check(
        "ast.persist_returns_true",
        any(isinstance(node.value, ast.Constant) and node.value.value is True for node in try_returns),
        "ast",
    )
    if replaces and try_returns:
        check("ast.true_after_replaces", try_returns[-1].lineno > replaces[-1].lineno, "ast")
    handler = tries[0].handlers[0]
    handler_calls = [node for node in ast.walk(handler) if isinstance(node, ast.Call)]
    check(
        "ast.persist_except_no_retry",
        not any(call_name(node) in {"self._persist", "os.replace", "faiss.write_index", "json.dump"} for node in handler_calls),
        "ast",
    )
    handler_returns = [node for node in ast.walk(handler) if isinstance(node, ast.Return)]
    check(
        "ast.persist_returns_false",
        len(handler_returns) == 1
        and isinstance(handler_returns[0].value, ast.Constant)
        and handler_returns[0].value.value is False,
        "ast",
    )
    check("ast.true_returns_not_used", true_returns == true_returns, "ast")

    persist_calls = [node for node in ast.walk(cls) if is_self_persist_call(node)]
    parents = parent_map(cls)
    ignored = [node for node in persist_calls if isinstance(parents.get(node), ast.Expr)]
    used = [node for node in persist_calls if isinstance(parents.get(node), ast.Assign)]
    check("ast.persist_call_ignored_on_rebuild", len(ignored) == 1, "ast")
    check("ast.persist_call_used_by_add", len(used) == 1, "ast")


def test_handler_ast(tree: ast.AST) -> None:
    fn = find_function(tree, "save_conversation_turn")
    check("ast.handler", fn is not None, "ast")
    if fn is None:
        return
    tries = [node for node in ast.walk(fn) if isinstance(node, ast.Try)]
    check("ast.handler_one_try", len(tries) == 1, "ast")
    check(
        "ast.handler_no_loop",
        not any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(fn)),
        "ast",
    )
    if len(tries) != 1:
        return
    try_node = tries[0]
    direct = []
    for stmt in try_node.body:
        if isinstance(stmt, ast.Assign) and is_add_to_vector_call(stmt.value):
            direct.append(stmt)
    check("ast.handler_two_direct_adds", len(direct) == 2, "ast")
    if len(direct) == 2:
        first_arg = direct[0].value.args[0]
        second_arg = direct[1].value.args[0]
        check("ast.user_text_unchanged", isinstance(first_arg, ast.Name) and first_arg.id == "user_msg", "ast")
        check("ast.echo_text_unchanged", isinstance(second_arg, ast.Name) and second_arg.id == "echo_response", "ast")
        user_meta = keyword_map(direct[0].value).get("meta")
        echo_meta = keyword_map(direct[1].value).get("meta")
        user_keys = dict_keys(user_meta) if user_meta else None
        echo_keys = dict_keys(echo_meta) if echo_meta else None
        check(
            "ast.user_meta_keys",
            user_keys == [
                "memory_source",
                "role",
                "task_type",
                "timestamp",
                "retention",
                "is_thought_provoking",
            ],
            "ast",
        )
        check(
            "ast.echo_meta_keys",
            echo_keys == ["memory_source", "role", "task_type", "timestamp", "retention"],
            "ast",
        )

    returns = status_returns(fn.body)
    codes = [code for _, code in returns]
    check("ast.status_codes", codes.count(403) == 1 and codes.count(400) == 1 and codes.count(200) == 1 and codes.count(500) == 1, "ast")
    ok_returns = [stmt for stmt, code in returns if code == 200]
    check("ast.one_200", len(ok_returns) == 1, "ast")
    if ok_returns:
        first = ok_returns[0].value.elts[0]
        check(
            "ast.200_returns_body",
            isinstance(first, ast.Call)
            and call_name(first) == "jsonify"
            and len(first.args) == 1
            and isinstance(first.args[0], ast.Name)
            and first.args[0].id == "body",
            "ast",
        )
    builder_calls = [node for node in ast.walk(fn) if call_name(node) == "conversation_turn_response"]
    check("ast.calls_builder", len(builder_calls) == 1, "ast")
    historical = []
    for stmt in ast.walk(try_node):
        if isinstance(stmt, ast.If):
            for alt in stmt.orelse:
                if isinstance(alt, ast.Assign) and dict_keys(alt.value) is not None:
                    historical.append(dict_keys(alt.value))
    check(
        "ast.historical_body_keys",
        ["status", "thought_provoking", "retention"] in historical,
        "ast",
    )

    stub_ok = False
    for node in tree.body:
        if not isinstance(node, ast.Try):
            continue
        imported = False
        for stmt in node.body:
            if (
                isinstance(stmt, ast.ImportFrom)
                and stmt.module == "app.core.memory_bridge"
                and any(alias.name == "add_to_vector_memory" for alias in stmt.names)
            ):
                imported = True
        if not imported or not node.handlers:
            continue
        for stmt in node.handlers[0].body:
            if (
                isinstance(stmt, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "add_to_vector_memory" for target in stmt.targets)
                and isinstance(stmt.value, ast.Lambda)
                and isinstance(stmt.value.body, ast.Constant)
                and stmt.value.body.value is None
            ):
                stub_ok = True
    check("ast.import_stub_returns_none", stub_ok, "ast")


def test_client_ast(tree: ast.AST) -> None:
    fn = find_function(tree, "save_turn_to_server")
    check("ast.client_fn", fn is not None, "ast")
    if fn is None:
        return
    args = [arg.arg for arg in fn.args.args]
    check(
        "ast.client_params",
        args == ["user_msg", "echo_response", "task_type", "server_url", "require_server_check"],
        "ast",
    )
    defaults = fn.args.defaults
    check(
        "ast.client_defaults",
        len(defaults) == 2
        and isinstance(defaults[0], ast.Name)
        and defaults[0].id == "SERVER_URL_DEFAULT"
        and isinstance(defaults[1], ast.Constant)
        and defaults[1].value is True,
        "ast",
    )
    check(
        "ast.client_no_loop",
        not any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(fn)),
        "ast",
    )
    posts = [node for node in ast.walk(fn) if call_name(node) == "requests.post"]
    check("ast.one_post", len(posts) == 1, "ast")
    if posts:
        timeout = keyword_map(posts[0]).get("timeout")
        check("ast.timeout_3", isinstance(timeout, ast.Constant) and timeout.value == 3, "ast")
        payload = keyword_map(posts[0]).get("json")
        check(
            "ast.post_keys",
            dict_keys(payload) == ["user_msg", "echo_response", "task_type", "timestamp", "secret"],
            "ast",
        )
    body = fn.body
    start = 1 if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) else 0
    check("ast.server_check_before_try", start + 1 < len(body) and isinstance(body[start], ast.If) and isinstance(body[start + 1], ast.Try), "ast")
    if start < len(body) and isinstance(body[start], ast.If):
        early = status_returns(body[start].body)
        check(
            "ast.server_down_returns_none",
            any(isinstance(stmt.value, ast.Constant) and stmt.value.value is None for stmt in body[start].body if isinstance(stmt, ast.Return)),
            "ast",
        )
        check("ast.server_down_no_post", not any(call_name(node) == "requests.post" for node in ast.walk(body[start])), "ast")
        check("ast.early_unused", early == early, "ast")
    tries = [node for node in fn.body if isinstance(node, ast.Try)]
    check("ast.client_one_try", len(tries) == 1 and len(tries[0].handlers) == 1, "ast")
    if len(tries) != 1:
        return
    handler = tries[0].handlers[0]
    check(
        "ast.client_except_exception",
        isinstance(handler.type, ast.Name) and handler.type.id == "Exception" and handler.name is None,
        "ast",
    )
    infos = [node for node in ast.walk(fn) if call_name(node) == "logging.info"]
    check("ast.client_info_count", len(infos) == 3, "ast")
    allowed_names = {"TRANSPORT_OR_HANDLER_ERROR", "log_line"}
    for info in infos:
        names = [node.id for node in ast.walk(info) if isinstance(node, ast.Name)]
        check(
            "ast.client_info_args",
            len(info.args) == 2
            and isinstance(info.args[0], ast.Constant)
            and info.args[0].value == "memory_conversation_outcome %s"
            and isinstance(info.args[1], ast.Name)
            and info.args[1].id in allowed_names
            and not any(name in {"response", "user_msg", "echo_response"} for name in names),
            "ast",
        )
    check(
        "ast.client_no_response_text",
        not any(isinstance(node, ast.Attribute) and node.attr == "text" for node in ast.walk(fn)),
        "ast",
    )
    non_200 = [
        stmt for stmt in tries[0].body
        if isinstance(stmt, ast.If) and _is_status_not_200(stmt.test)
    ]
    check("ast.non_200_if", len(non_200) == 1, "ast")
    if non_200:
        check(
            "ast.non_200_does_not_read_body",
            not any(
                isinstance(node, ast.Attribute) and node.attr in {"text", "json"}
                for node in ast.walk(non_200[0])
            ),
            "ast",
        )


def test_callers(bridge_tree: ast.AST) -> None:
    skip = {".git", "__pycache__", "memory", "node_modules", ".venv", "venv"}
    used_outside = []
    unparsed = []
    for dirpath, dirnames, filenames in os_walk_pruned(ROOT, skip):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            path = Path(dirpath) / filename
            rel = path.relative_to(ROOT).as_posix()
            if path.stat().st_size > 1_000_000:
                text = path.read_text(encoding="utf-8", errors="ignore")
                if "add_to_vector_memory(" in text:
                    unparsed.append(rel)
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeError, OSError):
                text = path.read_text(encoding="utf-8", errors="ignore")
                if "add_to_vector_memory(" in text:
                    unparsed.append(rel)
                continue
            parents = parent_map(tree)
            for node in ast.walk(tree):
                if not is_add_to_vector_call(node):
                    continue
                parent = parents.get(node)
                if isinstance(parent, ast.Expr):
                    continue
                if rel == "run.py" and isinstance(parent, ast.Assign):
                    targets = [
                        target.id for target in parent.targets if isinstance(target, ast.Name)
                    ]
                    if targets == ["user_outcome"] or targets == ["echo_outcome"]:
                        continue
                used_outside.append(rel)
    check("ast.no_other_used_returns", used_outside == [], "ast")
    check("ast.caller_sources_parsed", unparsed == [], "ast")
    # The bridge definition is not a call. Re-count assigned uses only in run.py via the walk above.
    check("ast.bridge_defines_function", find_function(bridge_tree, "add_to_vector_memory") is not None, "ast")


def os_walk_pruned(root: Path, skip: set[str]):
    import os
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in skip and not name.startswith(".")]
        yield dirpath, dirnames, filenames


def test_modules_clean() -> None:
    loaded = [name for name in FORBIDDEN_MODULES if name in sys.modules]
    check("ast.forbidden_modules_absent", loaded == [], "ast")


def main() -> None:
    test_pure_mapping()
    test_pure_response_and_log()
    outcome_tree = load_tree("app/core/memory_write_outcome.py")
    bridge_tree = load_tree("app/core/memory_bridge.py")
    vector_tree = load_tree("app/lib/vector_memory.py")
    run_tree = load_tree("run.py")
    client_tree = load_tree("app/core/conversation_service.py")
    test_outcome_module_ast(outcome_tree)
    test_add_to_vector_memory_ast(bridge_tree)
    test_vector_memory_ast(vector_tree)
    test_handler_ast(run_tree)
    test_client_ast(client_tree)
    test_callers(bridge_tree)
    test_modules_clean()
    if FAILURES:
        print("RESULT fail")
        for name in FAILURES:
            print(name)
        print(f"pure {PURE}")
        print(f"ast {AST_CHECKS}")
        sys.exit(1)
    print("RESULT pass")
    print(f"pure {PURE}")
    print(f"ast {AST_CHECKS}")


if __name__ == "__main__":
    main()
