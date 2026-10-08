"""Bounded AST abstract interpretation. Never executes candidate Python.

Unknown/dynamic constructs are refused. This is a development checker, not a
qualified proof of arbitrary Python effects or task correctness.
"""
import ast
from dataclasses import dataclass, replace

from .contracts import Task


class Unsupported(ValueError):
    pass


@dataclass(frozen=True)
class Number:
    role: str
    sign: int = 1
    ranks: tuple = ()
    sites: tuple = ()  # (AST path, binding-distance) pairs


@dataclass(frozen=True)
class Field:
    role: str
    selection: object = None


@dataclass(frozen=True)
class Items:
    values: tuple


@dataclass
class Sequence:
    item: Items
    owned: bool
    sort: object = None


@dataclass(frozen=True)
class Selection:
    sequence: Sequence
    endpoint: int


@dataclass(frozen=True)
class Ranking:
    components: tuple
    descending: bool


@dataclass
class Helper:
    node: object
    closure: dict


BUILTINS = {"sorted", "list", "tuple", "len"}
ALLOWED = (ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Assign,
           ast.Return, ast.Expr, ast.Name, ast.Load, ast.Store, ast.Constant,
           ast.List, ast.Tuple, ast.Dict, ast.Subscript, ast.UnaryOp, ast.USub,
           ast.UAdd, ast.Call, ast.keyword, ast.Lambda, ast.Attribute,
           ast.ListComp, ast.comprehension)


def path_nodes(root):
    result = {}

    def visit(node, path):
        result[path] = node
        for name, value in ast.iter_fields(node):
            if isinstance(value, ast.AST):
                visit(value, path + (name,))
            elif isinstance(value, list):
                for i, child in enumerate(value):
                    if isinstance(child, ast.AST):
                        visit(child, path + (name, i))

    visit(root, ())
    return result


def _params(node):
    a = node.args
    if a.posonlyargs or a.kwonlyargs or a.vararg or a.kwarg or a.defaults or a.kw_defaults:
        raise Unsupported("only fixed positional parameters supported")
    names = [x.arg for x in a.args]
    if len(names) != len(set(names)) or any(x in BUILTINS for x in names):
        raise Unsupported("duplicate or shadowed parameter")
    if any(x.annotation for x in a.args):
        raise Unsupported("annotations not supported")
    return names


def _integer(node):
    if isinstance(node, ast.Constant) and type(node.value) is int:
        if node.value.bit_length() <= 63:
            return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = _integer(node.operand)
        return -value if isinstance(node.op, ast.USub) else value
    raise Unsupported("expected bounded literal integer")


class Analyzer:
    def __init__(self, source: str, task: Task):
        if type(source) is not str or len(source.encode("utf-8")) > 8192:
            raise Unsupported("source exceeds 8 KiB")
        try:
            self.tree = ast.parse(source)
        except (SyntaxError, ValueError, RecursionError) as e:
            raise Unsupported("source parse failed") from e
        self.nodes = path_nodes(self.tree)
        if len(self.nodes) > 256 or any(not isinstance(n, ALLOWED) for n in self.nodes.values()):
            raise Unsupported("node budget or closed grammar exceeded")
        self.paths = {id(n): p for p, n in self.nodes.items()}
        self.task = task
        self.active = []
        self.operations = 0
        self.sort_count = 0
        self.helper_count = sum(isinstance(n, ast.FunctionDef) for n in self.nodes.values()) - 1
        if self.helper_count > 2:
            raise Unsupported("more than two helpers")
        for n in self.nodes.values():
            if isinstance(n, (ast.FunctionDef, ast.Lambda)):
                _params(n)
                if isinstance(n, ast.FunctionDef) and (
                        n.decorator_list or n.returns or getattr(n, "type_params", [])):
                    raise Unsupported("decorators/annotations/type parameters unsupported")
            if isinstance(n, ast.Attribute) and n.attr != "sort":
                raise Unsupported("attribute access unsupported")
            if isinstance(n, ast.Constant):
                if type(n.value) not in (str, int, bool, type(None)):
                    raise Unsupported("unsupported constant")
                if type(n.value) is str and len(n.value) > 128:
                    raise Unsupported("constant string too large")
                if type(n.value) is int and n.value.bit_length() > 63:
                    raise Unsupported("constant integer too large")

    def link(self, value, node):
        if isinstance(value, Number):
            refs = {p: distance + 1 for p, distance in value.sites}
            refs[self.paths[id(node)]] = 0
            return replace(value, sites=tuple(refs.items()))
        return value

    def call_helper(self, helper, values):
        node = helper.node
        if id(node) in self.active or len(self.active) > 2:
            raise Unsupported("recursive or excessive helper chain")
        params = _params(node)
        if len(params) != len(values):
            raise Unsupported("helper arity mismatch")
        env = dict(helper.closure)
        env.update(zip(params, values))
        self.active.append(id(node))
        try:
            if isinstance(node, ast.Lambda):
                return self.expr(node.body, env)
            return self.block(node.body, env, set(params))
        finally:
            self.active.pop()

    def block(self, statements, env, assigned):
        for i, stmt in enumerate(statements):
            if isinstance(stmt, ast.Assign):
                if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                    raise Unsupported("only single local bindings supported")
                name = stmt.targets[0].id
                if name in assigned or name in BUILTINS or isinstance(env.get(name), Helper):
                    raise Unsupported("rebinding/shadowing unsupported")
                env[name] = self.expr(stmt.value, env)
                assigned.add(name)
            elif isinstance(stmt, ast.FunctionDef):
                if stmt.name in env or stmt.name in BUILTINS:
                    raise Unsupported("helper shadowing unsupported")
                env[stmt.name] = Helper(stmt, env)
                assigned.add(stmt.name)
            elif isinstance(stmt, ast.Expr):
                call = stmt.value
                if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                        and call.func.attr == "sort"):
                    raise Unsupported("only owned sort expression statements supported")
                self.expr(call, env)
            elif isinstance(stmt, ast.Return):
                if i != len(statements) - 1 or stmt.value is None:
                    raise Unsupported("early/empty return unsupported")
                return self.expr(stmt.value, env)
            else:
                raise Unsupported("unsupported statement")
        raise Unsupported("missing return")

    def expr(self, node, env):
        self.operations += 1
        if self.operations > 2048:
            raise Unsupported("analysis expansion budget exceeded")
        if isinstance(node, ast.Name):
            if node.id not in env:
                raise Unsupported("unresolved name")
            return self.link(env[node.id], node)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Dict):
            keys = []
            values = []
            for k, v in zip(node.keys, node.values):
                if not isinstance(k, ast.Constant) or type(k.value) is not str:
                    raise Unsupported("rank map keys must be literal strings")
                keys.append(k.value)
                values.append(_integer(v))
            if len(set(keys)) != len(keys) or len(set(values)) != len(values):
                raise Unsupported("duplicate map key or numeric rank")
            return dict(zip(keys, values))
        if isinstance(node, (ast.Tuple, ast.List)):
            return Items(tuple(self.expr(x, env) for x in node.elts))
        if isinstance(node, ast.Lambda):
            return Helper(node, dict(env))
        if isinstance(node, ast.UnaryOp):
            value = self.expr(node.operand, env)
            if isinstance(value, Number):
                value = replace(value, sign=value.sign * (-1 if isinstance(node.op, ast.USub) else 1))
                return self.link(value, node)
            return _integer(node)
        if isinstance(node, ast.Subscript):
            value = self.expr(node.value, env)
            if type(value) is dict:
                key = self.expr(node.slice, env)
                if not isinstance(key, Field) or key.role != "tag" or key.selection is not None:
                    raise Unsupported("rank lookup must bind to input tag")
                if set(value) != set(self.task.tag_order):
                    raise Unsupported("rank map does not cover the declared tags")
                return self.link(Number("tag", ranks=tuple(sorted(value.items()))), node)
            index = _integer(node.slice)
            if isinstance(value, Items):
                try:
                    return self.link(value.values[index], node)
                except IndexError as e:
                    raise Unsupported("tuple index out of range") from e
            if isinstance(value, Sequence):
                if index not in (0, -1):
                    raise Unsupported("only first/last sequence selection supported")
                return Selection(value, index)
            if isinstance(value, Selection):
                try:
                    selected = value.sequence.item.values[index]
                except IndexError as e:
                    raise Unsupported("selected row index out of range") from e
                if not isinstance(selected, Field) or selected.role != "name":
                    raise Unsupported("only winner-name extraction supported")
                return replace(selected, selection=value)
            raise Unsupported("unsupported subscript")
        if isinstance(node, ast.ListComp):
            if len(node.generators) != 1:
                raise Unsupported("nested comprehension unsupported")
            g = node.generators[0]
            if g.ifs or g.is_async or not isinstance(g.target, ast.Name):
                raise Unsupported("filtered/destructuring comprehension unsupported")
            if g.target.id in BUILTINS or isinstance(env.get(g.target.id), Helper):
                raise Unsupported("comprehension shadows builtin/helper")
            seq = self.expr(g.iter, env)
            if not isinstance(seq, Sequence) or seq.sort:
                raise Unsupported("only one-level unsorted input comprehension supported")
            local = dict(env)
            local[g.target.id] = seq.item
            item = self.expr(node.elt, local)
            if not isinstance(item, Items):
                raise Unsupported("comprehension must preserve explicit row structure")
            return Sequence(item, True)
        if isinstance(node, ast.Call):
            return self.call(node, env)
        raise Unsupported("unsupported expression")

    def call(self, node, env):
        if any(k.arg is None for k in node.keywords):
            raise Unsupported("expanded keywords unsupported")
        kw = {k.arg: k.value for k in node.keywords}
        if len(kw) != len(node.keywords):
            raise Unsupported("duplicate keyword")
        if isinstance(node.func, ast.Attribute):
            if node.func.attr != "sort" or node.args:
                raise Unsupported("unsupported method")
            seq = self.expr(node.func.value, env)
            if not isinstance(seq, Sequence) or not seq.owned:
                raise Unsupported("sort lacks owned outer list")
            self.rank(seq, kw, env)
            return None
        if not isinstance(node.func, ast.Name):
            raise Unsupported("indirect call unsupported")
        name = node.func.id
        if name == "sorted":
            if len(node.args) != 1:
                raise Unsupported("sorted requires one sequence")
            seq = self.expr(node.args[0], env)
            if not isinstance(seq, Sequence):
                raise Unsupported("sorted input unresolved")
            result = Sequence(seq.item, True, seq.sort)
            self.rank(result, kw, env)
            return result
        if name in ("list", "tuple"):
            if len(node.args) != 1 or kw:
                raise Unsupported("constructor arguments unsupported")
            value = self.expr(node.args[0], env)
            if name == "list" and isinstance(value, Sequence):
                return Sequence(value.item, True, value.sort)
            if name == "tuple" and isinstance(value, Items):
                return value
            raise Unsupported("constructor form unsupported")
        if name == "len":
            raise Unsupported("length-derived repair sites outside this prototype")
        helper = env.get(name)
        if not isinstance(helper, Helper) or kw:
            raise Unsupported("unknown callable")
        return self.call_helper(helper, [self.expr(a, env) for a in node.args])

    def rank(self, seq, kw, env):
        self.sort_count += 1
        if self.sort_count > 4 or seq.sort is not None:
            raise Unsupported("sort budget/interacting sorts unsupported")
        if set(kw) - {"key", "reverse"} or "key" not in kw:
            raise Unsupported("explicit key required")
        reverse = False
        if "reverse" in kw:
            value = kw["reverse"]
            if not isinstance(value, ast.Constant) or type(value.value) is not bool:
                raise Unsupported("sort direction must be literal bool")
            reverse = value.value
        helper = self.expr(kw["key"], env)
        if not isinstance(helper, Helper):
            raise Unsupported("key must resolve to a pure helper/lambda")
        result = self.call_helper(helper, [seq.item])
        components = result.values if isinstance(result, Items) else (result,)
        if any(not isinstance(v, (Field, Number)) for v in components):
            raise Unsupported("key component role unresolved")
        seq.sort = Ranking(components, reverse)

    def analyze(self):
        functions = self.tree.body
        if not functions or any(not isinstance(n, ast.FunctionDef) for n in functions):
            raise Unsupported("module must contain only plain functions")
        names = [n.name for n in functions]
        if len(names) != len(set(names)) or any(n in BUILTINS for n in names):
            raise Unsupported("duplicate or shadowed function")
        entries = [n for n in functions if n.name == self.task.entrypoint]
        if len(entries) != 1 or len(functions) > 3:
            raise Unsupported("entrypoint/helper budget")
        env = {}
        for fn in functions:
            env[fn.name] = Helper(fn, env)
        entry = entries[0]
        if len(_params(entry)) != 1:
            raise Unsupported("entrypoint must take one input")
        item = Items((Field("name"), Number("score"), Field("tag")))
        final = self.call_helper(env[self.task.entrypoint], [Sequence(item, False)])
        if type(final) is str:
            return []
        if not isinstance(final, Field) or final.role != "name" or final.selection is None:
            raise Unsupported("return is not a resolved winner name")
        selected = final.selection
        ranking = selected.sequence.sort
        if ranking is None:
            return []
        q = (-1 if selected.endpoint == 0 else 1) * (-1 if ranking.descending else 1)
        roles = [v.role for v in ranking.components]
        precedence = roles == ["score", "tag", "name"]
        sites = {}
        for component in ranking.components:
            if not isinstance(component, Number):
                continue
            signs = []
            if component.role == "score":
                signs = [1 if self.task.score_direction == "higher" else -1]
            elif component.role == "tag":
                ranks = dict(component.ranks)
                tags = self.task.tag_order
                signs = [1 if ranks[a] > ranks[b] else -1
                         for i, a in enumerate(tags) for b in tags[i + 1:]]
            orientation = [q * component.sign * d for d in signs]
            status = "POLARITY_UNKNOWN"
            if precedence and signs and len(set(signs)) == 1:
                status = ("POLARITY_INCONSISTENT" if all(x < 0 for x in orientation)
                          else "POLARITY_CONSISTENT")
            for path, distance in component.sites:
                row = sites.setdefault(path, {"path": list(path), "uses": [], "distance": distance})
                row["distance"] = min(row["distance"], distance)
                row["uses"].append({"role": component.role, "q": q, "s": component.sign,
                                    "d_signs": signs, "status": status})
        if len(sites) > 8:
            raise Unsupported("more than eight eligible sign sites")
        for path, row in sites.items():
            n = self.nodes[path]
            row["position"] = [n.lineno, n.col_offset, n.end_lineno, n.end_col_offset]
            statuses = {u["status"] for u in row["uses"]}
            row["polarity"] = (next(iter(statuses)) if len(statuses) == 1 else "POLARITY_UNKNOWN")
            row["map_derived"] = all(u["role"] == "tag" for u in row["uses"])
        return list(sites.values())
