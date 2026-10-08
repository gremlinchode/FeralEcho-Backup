"""Arm B only: deterministic, source-only, at most two one-site proposals."""
import ast
import copy
from pathlib import Path

from . import VERSION
from .analysis import Analyzer, Unsupported, path_nodes
from .contracts import digest, parse_task, source_hash


def implementation_hash():
    directory = Path(__file__).parent
    return digest({p.name: source_hash(p.read_text()) for p in sorted(directory.glob("*.py"))})


def subtree_hash(node):
    return source_hash(ast.dump(node, include_attributes=False))


def apply_patch(source: str, patch: dict) -> str:
    """Construct a copy only. Does not execute, import or write candidate code."""
    if type(patch) is not dict or set(patch) != {"path", "old_subtree_sha256", "operation"}:
        raise ValueError("invalid patch schema")
    if patch["operation"] != "TOGGLE_SIGN" or type(patch["path"]) is not list:
        raise ValueError("unsupported patch")
    if any(type(x) not in (str, int) for x in patch["path"]):
        raise ValueError("invalid AST path")
    tree = ast.parse(source)
    paths = path_nodes(tree)
    path = tuple(patch["path"])
    if path not in paths or not path:
        raise ValueError("missing patch site")
    old = paths[path]
    if subtree_hash(old) != patch["old_subtree_sha256"]:
        raise ValueError("stale subtree")
    new = (copy.deepcopy(old.operand) if isinstance(old, ast.UnaryOp) and isinstance(old.op, ast.USub)
           else ast.UnaryOp(op=ast.USub(), operand=copy.deepcopy(old)))
    ast.copy_location(new, old)
    parent = tree
    for part in path[:-1]:
        parent = parent[part] if type(part) is int else getattr(parent, part)
    if type(path[-1]) is int:
        parent[path[-1]] = new
    else:
        setattr(parent, path[-1], new)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def generic_order(site):
    # This prototype's eligible sites all feed the returned ranking key.
    return (0 if site["map_derived"] else 1, site["distance"],
            tuple(site["position"]), repr(site["path"]), "TOGGLE_SIGN")


def propose(source: str, contract: dict) -> dict:
    result = {"schema": "B-COMMIT-1", "version": VERSION,
              "source_sha256": source_hash(source), "contract_sha256": digest(contract),
              "implementation_sha256": implementation_hash(), "max_proposals": 2,
              "authority": "NOT_ESTABLISHED_BY_PROPOSER", "eligible_sites": [],
              "proposals": [], "refusal": None, "candidate_executions": 0}
    try:
        task = parse_task(contract)
        if contract["unknown_fields"] or contract["conflict_refs"]:
            raise Unsupported("unknown/conflicting current requirements")
        if task.source_sha256 != source_hash(source):
            raise Unsupported("stale source/contract binding")
        analyzer = Analyzer(source, task)
        sites = sorted(analyzer.analyze(), key=generic_order)
        candidates = []
        seen = set()
        # Retain earliest canonical physical site when derived ASTs coincide.
        for site in sorted(sites, key=lambda s: (s["position"], repr(s["path"]))):
            patch = {"path": site["path"], "operation": "TOGGLE_SIGN",
                     "old_subtree_sha256": subtree_hash(analyzer.nodes[tuple(site["path"])])}
            derived = apply_patch(source, patch)
            fingerprint = subtree_hash(ast.parse(derived))
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            candidates.append({"patch": patch, "derived_source_sha256": source_hash(derived),
                               "site": site})
        candidates.sort(key=lambda c: generic_order(c["site"]))
        result["eligible_sites"] = [c["site"] for c in candidates]
        priority = [c for c in candidates if c["site"]["polarity"] == "POLARITY_INCONSISTENT"]
        fallback = [c for c in candidates if c["site"]["polarity"] != "POLARITY_INCONSISTENT"]
        result["proposals"] = (priority + fallback)[:2]
        if not candidates:
            result["refusal"] = "NO_ELIGIBLE_SITE"
    except (Unsupported, ValueError, TypeError, RecursionError) as e:
        result["eligible_sites"] = []
        result["proposals"] = []
        result["refusal"] = str(e)
    result["commit_sha256"] = digest(result)
    return result


def verify_commit(source: str, contract: dict, commit: dict) -> bool:
    """Recompute the entire deterministic commitment, not proposer binding claims."""
    return commit == propose(source, contract)
