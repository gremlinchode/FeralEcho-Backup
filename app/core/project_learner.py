"""
app/core/project_learner.py

Lightweight module to learn and represent a Python codebase structure.
Designed to be loaded by Echo; call ProjectLearner(path).learn() to run.
"""

from __future__ import annotations
import os
import ast
import json
import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# ----------------------------
# Data structures
# ----------------------------
@dataclass
class SymbolInfo:
    name: str
    type: str  # "function", "class", "module"
    lineno: int
    docstring: Optional[str]

@dataclass
class FileInfo:
    path: str
    relpath: str
    module_name: str
    imports: List[str]
    symbols: List[SymbolInfo]
    top_comments: Optional[str]
    size_bytes: int
    mtime_iso: str

# ----------------------------
# Utility helpers
# ----------------------------
def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_top_comments(source: str, max_lines: int = 30) -> Optional[str]:
    """
    Return leading comments or module docstring (prefer docstring).
    """
    try:
        node = ast.parse(source)
        doc = ast.get_docstring(node)
        if doc:
            return doc.strip()
    except Exception:
        pass
    # fallback: leading '#' comments
    lines = source.splitlines()
    top = []
    for i, ln in enumerate(lines[:max_lines]):
        if ln.strip().startswith("#"):
            top.append(ln.strip().lstrip("#").strip())
        elif ln.strip() == "":
            continue
        else:
            break
    if top:
        return "\n".join(top)
    return None

def safe_module_name_from_path(base_dir: str, path: str) -> str:
    rel = os.path.relpath(path, base_dir)
    rel = rel.replace(os.path.sep, ".")
    if rel.endswith(".py"):
        rel = rel[:-3]
    return rel

# ----------------------------
# AST parsing
# ----------------------------
def parse_file(path: str) -> Tuple[List[str], List[SymbolInfo], Optional[str]]:
    source = read_text(path)
    imports = []
    symbols: List[SymbolInfo] = []
    try:
        tree = ast.parse(source)
    except Exception as e:
        # return minimal info on parse failure
        return imports, symbols, extract_top_comments(source)

    # gather imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            # handle relative imports like ..subpkg
            level = "." * node.level if getattr(node, "level", 0) else ""
            imports.append(level + module if module else level)

    # top-level functions & classes
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            doc = ast.get_docstring(node)
            symbols.append(SymbolInfo(name=node.name, type="function", lineno=node.lineno, docstring=doc))
        elif isinstance(node, ast.AsyncFunctionDef):
            doc = ast.get_docstring(node)
            symbols.append(SymbolInfo(name=node.name, type="async_function", lineno=node.lineno, docstring=doc))
        elif isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            symbols.append(SymbolInfo(name=node.name, type="class", lineno=node.lineno, docstring=doc))

    top_comments = extract_top_comments(source)
    return imports, symbols, top_comments

# ----------------------------
# Core learner
# ----------------------------
class ProjectLearner:
    def __init__(self, root_path: str, exclude_dirs: Optional[List[str]] = None):
        self.root_path = os.path.abspath(root_path)
        self.exclude_dirs = set(exclude_dirs or [".venv", "venv", "__pycache__", ".git", "build", "dist"])
        self.files: Dict[str, FileInfo] = {}
        self.graph_edges: List[Tuple[str, str, str]] = []  # (from_module, to_module, reason)
        self.generated_at = datetime.utcnow().isoformat() + "Z"

    def discover_py_files(self) -> List[str]:
        matches = []
        for dirpath, dirnames, filenames in os.walk(self.root_path):
            # prune excludes
            dirnames[:] = [d for d in dirnames if d not in self.exclude_dirs and not d.startswith(".")]
            for fn in filenames:
                if fn.endswith(".py"):
                    matches.append(os.path.join(dirpath, fn))
        return matches

    def analyze(self):
        py_files = self.discover_py_files()
        for p in py_files:
            rel = os.path.relpath(p, self.root_path)
            module_name = safe_module_name_from_path(self.root_path, p)
            imports, symbols, top_comments = parse_file(p)
            st = os.stat(p)
            fi = FileInfo(
                path=p,
                relpath=rel,
                module_name=module_name,
                imports=imports,
                symbols=symbols,
                top_comments=top_comments,
                size_bytes=st.st_size,
                mtime_iso=datetime.utcfromtimestamp(st.st_mtime).isoformat() + "Z",
            )
            self.files[module_name] = fi

        # build simple dependency edges
        self.build_edges_from_imports()

    def build_edges_from_imports(self):
        # naive matching: if import string starts with a known module_name, create edge
        known = set(self.files.keys())
        for modname, fi in self.files.items():
            for imp in fi.imports:
                if not imp:
                    continue
                # normalize import (strip as/from extras)
                imp_base = imp.split(".")[0]
                # try several strategies to match a module in repo:
                candidates = []
                # exact match
                if imp in known:
                    candidates.append(imp)
                if imp_base in known:
                    candidates.append(imp_base)
                # try relative: leading dots
                if imp.lstrip(".") in known:
                    candidates.append(imp.lstrip("."))
                # create edges
                for target in candidates:
                    if target != modname:
                        self.graph_edges.append((modname, target, "import"))

        # also add edges when symbol references common module names in code text (best-effort)
        for modname, fi in self.files.items():
            try:
                source = read_text(fi.path)
                # find "from X import" usages we didn't catch (regex fallback)
                for m in re.finditer(r"from\s+([A-Za-z0-9_.]+)\s+import", source):
                    candidate = m.group(1).split(".")[0]
                    if candidate in known and candidate != modname:
                        self.graph_edges.append((modname, candidate, "from-import"))
            except Exception:
                pass

        # dedupe edges
        seen = set()
        deduped = []
        for a,b,reason in self.graph_edges:
            key = (a,b,reason)
            if key not in seen:
                seen.add(key)
                deduped.append((a,b,reason))
        self.graph_edges = deduped

    def to_json(self) -> Dict[str, Any]:
        return {
            "root_path": self.root_path,
            "generated_at": self.generated_at,
            "modules_count": len(self.files),
            "files": {k: self._fileinfo_to_dict(v) for k,v in self.files.items()},
            "edges": [{"from": a, "to": b, "reason": r} for a,b,r in self.graph_edges],
        }

    def _fileinfo_to_dict(self, fi: FileInfo) -> Dict[str, Any]:
        return {
            "path": fi.path,
            "relpath": fi.relpath,
            "module_name": fi.module_name,
            "imports": fi.imports,
            "symbols": [asdict(s) for s in fi.symbols],
            "top_comments": (fi.top_comments[:1000] + "...") if fi.top_comments and len(fi.top_comments) > 1000 else fi.top_comments,
            "size_bytes": fi.size_bytes,
            "mtime_iso": fi.mtime_iso,
        }

    def write_outputs(self, outdir: Optional[str] = None):
        outdir = outdir or os.path.join(self.root_path, ".echo_project_learner")
        os.makedirs(outdir, exist_ok=True)
        jpath = os.path.join(outdir, "feralecho_structure.json")
        with open(jpath, "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, indent=2)
        dotpath = os.path.join(outdir, "feralecho_graph.dot")
        with open(dotpath, "w", encoding="utf-8") as f:
            f.write(self._render_dot())
        return {"json": jpath, "dot": dotpath}

    def _render_dot(self) -> str:
        # produce a compact Graphviz directed graph
        lines = ['digraph feralecho {', '  rankdir=LR;']
        # nodes with labels
        for modname, fi in self.files.items():
            safe_label = modname.replace('"', '\\"')
            lines.append(f'  "{modname}" [label="{safe_label}\\n{fi.relpath}"];')
        for a,b,r in self.graph_edges:
            lines.append(f'  "{a}" -> "{b}" [label="{r}"];')
        lines.append("}")
        return "\n".join(lines)

    # Echo integration helpers
    def to_memory_items(self, max_snippet_chars: int = 800) -> List[Dict[str, Any]]:
        """
        Return a list of items suitable for storing in Echo's memory or vector DB.
        Each item contains: id, title, text, metadata
        """
        items = []
        for modname, fi in self.files.items():
            title = f"module:{modname}"
            text_parts = []
            if fi.top_comments:
                text_parts.append(fi.top_comments)
            # include top-level docstrings or first-level symbol docstrings
            for s in fi.symbols[:6]:
                if s.docstring:
                    text_parts.append(f"{s.type} {s.name}: { (s.docstring[:max_snippet_chars]) }")
            text = "\n\n".join(text_parts) if text_parts else read_text(fi.path)[:max_snippet_chars]
            meta = {"relpath": fi.relpath, "module": modname, "size_bytes": fi.size_bytes}
            items.append({"id": modname, "title": title, "text": text, "metadata": meta})
        return items

    def learn(self, write_out: bool = True, outdir: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the analysis end-to-end and optionally write outputs.
        Returns the JSON-ready structure (not the file path).
        """
        self.analyze()
        results = self.to_json()
        outputs = {}
        if write_out:
            outputs = self.write_outputs(outdir=outdir)
            results["_output_files"] = outputs
        return results

# ----------------------------
# CLI support
# ----------------------------
def main_cli():
    import argparse
    parser = argparse.ArgumentParser(description="ProjectLearner: learn a Python project structure")
    parser.add_argument("root", nargs="?", default=".", help="root folder of the project")
    parser.add_argument("--out", help="output directory (default: <root>/.echo_project_learner)")
    parser.add_argument("--no-write", action="store_true", help="do not write output files, just print JSON")
    args = parser.parse_args()

    pl = ProjectLearner(args.root)
    results = pl.learn(write_out=not args.no_write, outdir=args.out)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":  # pragma: no cover
    main_cli()

