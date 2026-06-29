"""
echo_cartographer.py
--------------------
FeralEcho Codebase Cartographer — Phase 1 + 2

Produces a structured, queryable map of the FeralEcho codebase:

  Tier 1 — Exists:       AST parse of all .py files
  Tier 2 — Connected:    Reverse dependency index (what imports what)
  Tier 3 — Actually Used: Runtime hit counts via sys.settrace
                          (defaults to 0; populated by runtime_tracer.py)

Outputs:
    data/codebase_map.json   — human-readable full map
    data/codebase.db         — SQLite, queryable by Echo

Criticality Score:
    score = (imported_by_count * 3) + (function_count * 2) + (runtime_hits)

Usage:
    python echo_cartographer.py              # full scan
    python echo_cartographer.py --query      # interactive query mode
    python echo_cartographer.py --summary    # print architecture summary

Echo query interface (call from other modules):
    from echo_cartographer import CartographerDB
    db = CartographerDB()
    db.what_imports("memory_bridge")
    db.module_info("river_deliberation")
    db.top_critical(n=10)
    db.architecture_summary()
"""

import ast
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── Configuration ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(".")
DATA_DIR     = Path("data")
OUTPUT_JSON  = DATA_DIR / "codebase_map.json"
OUTPUT_DB    = DATA_DIR / "codebase.db"

IGNORE_DIRS = {
    "__pycache__", ".git", "venv", ".venv",
    "node_modules", "archive_unused_files",
    "models", "embeddings", "faiss", "backups",
    ".conda", "conda-meta",
}

# Semantic layer categories — used in architecture_summary()
SEMANTIC_ROLES = {
    "memory":   ["memory_bridge", "dream_bridge", "journal", "faiss"],
    "learning": ["dual_learning", "river_brain", "optuna", "projectlearner"],
    "reasoning":["river_deliberation", "deliberation", "council"],
    "routing":  ["echo_model_orchestrator", "orchestrator", "router"],
    "safety":   ["dmn_guardian", "guardian", "wolf", "alignment"],
    "self_mod": ["self_edit", "self_modify", "healer"],
    "identity": ["echo", "becoming", "claude_shard", "bioluminescent"],
    "comms":    ["server", "api", "flask", "symbiote", "iphone"],
}


# ── AST Extraction ──────────────────────────────────────────────────────────────

def should_skip(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def extract_module_info(py_file: Path) -> dict:
    try:
        source = py_file.read_text(encoding="utf-8", errors="ignore")
        tree   = ast.parse(source)

        imports   = []
        functions = []
        classes   = []
        calls     = []  # function names called at module level / top scope

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)

            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod:
                    imports.append(mod)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)

            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)

        stat = py_file.stat()

        # Normalize module name for reverse-dep matching
        module_name = py_file.stem  # e.g. "memory_bridge"

        # Filter imports to local-looking names (no stdlib noise)
        local_imports = [
            i for i in imports
            if not i.startswith(("os", "sys", "re", "json", "time",
                                 "threading", "pathlib", "datetime",
                                 "collections", "functools", "typing",
                                 "abc", "math", "random", "logging",
                                 "subprocess", "shutil", "copy", "io",
                                 "hashlib", "traceback", "inspect",
                                 "ast", "sqlite3", "argparse",
                                 "numpy", "sklearn", "sentence_",
                                 "flask", "requests", "aiohttp"))
        ]

        return {
            "path":          str(py_file),
            "module_name":   module_name,
            "imports":       sorted(set(imports)),
            "local_imports": sorted(set(local_imports)),
            "functions":     sorted(set(functions)),
            "classes":       sorted(set(classes)),
            "calls":         sorted(set(calls)),
            "docstring":     ast.get_docstring(tree) or "",
            "size_bytes":    stat.st_size,
            "modified":      datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "line_count":    source.count("\n"),
        }

    except Exception as e:
        return {
            "path":        str(py_file),
            "module_name": py_file.stem,
            "error":       str(e),
        }


# ── Graph Construction ──────────────────────────────────────────────────────────

def build_reverse_deps(files: dict) -> dict:
    """
    Invert the import graph.
    Returns: { "memory_bridge": ["river_deliberation", "self_edit_manager", ...] }
    """
    reverse = defaultdict(set)
    module_names = {info["module_name"] for info in files.values() if "error" not in info}

    for info in files.values():
        if "error" in info:
            continue
        importer = info["module_name"]
        for imp in info.get("local_imports", []):
            # Match against known module names (stem match)
            imp_stem = imp.split(".")[-1]
            if imp_stem in module_names:
                reverse[imp_stem].add(importer)

    return {k: sorted(v) for k, v in reverse.items()}


def score_criticality(info: dict, imported_by: list, runtime_hits: int = 0) -> int:
    func_count   = len(info.get("functions", []))
    dep_count    = len(imported_by)
    return (dep_count * 3) + (func_count * 2) + runtime_hits


def classify_role(module_name: str) -> str:
    name = module_name.lower()
    for role, keywords in SEMANTIC_ROLES.items():
        if any(kw in name for kw in keywords):
            return role
    return "misc"


# ── Full Map Builder ────────────────────────────────────────────────────────────

def build_map(project_root: Path = PROJECT_ROOT) -> dict:
    print(f"Scanning {project_root.resolve()} ...")

    files = {}
    for py_file in sorted(project_root.rglob("*.py")):
        if should_skip(py_file):
            continue
        rel = py_file.relative_to(project_root)
        files[str(rel)] = extract_module_info(py_file)

    print(f"  Parsed {len(files)} Python files")

    reverse_deps = build_reverse_deps(files)

    # Enrich each file entry
    for rel_path, info in files.items():
        if "error" in info:
            continue
        mn = info["module_name"]
        imported_by = reverse_deps.get(mn, [])
        info["imported_by"]       = imported_by
        info["criticality_score"] = score_criticality(info, imported_by)
        info["role"]              = classify_role(mn)

    # Top critical modules
    ranked = sorted(
        [(p, i) for p, i in files.items() if "error" not in i],
        key=lambda x: x[1].get("criticality_score", 0),
        reverse=True
    )

    return {
        "generated":    datetime.now().isoformat(),
        "project_root": str(project_root.resolve()),
        "file_count":   len(files),
        "files":        files,
        "reverse_deps": reverse_deps,
        "top_critical": [
            {
                "module": i["module_name"],
                "path":   p,
                "score":  i["criticality_score"],
                "role":   i["role"],
            }
            for p, i in ranked[:20]
        ],
    }


# ── JSON Writer ─────────────────────────────────────────────────────────────────

def write_json(codebase_map: dict, output: Path = OUTPUT_JSON):
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(codebase_map, f, indent=2)
    print(f"  Wrote {output}")


# ── SQLite Writer ───────────────────────────────────────────────────────────────

def write_sqlite(codebase_map: dict, output: Path = OUTPUT_DB):
    output.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(output)
    c    = conn.cursor()

    c.executescript("""
        DROP TABLE IF EXISTS modules;
        DROP TABLE IF EXISTS imports;
        DROP TABLE IF EXISTS functions;
        DROP TABLE IF EXISTS classes;
        DROP TABLE IF EXISTS reverse_deps;

        CREATE TABLE modules (
            module_name      TEXT PRIMARY KEY,
            path             TEXT,
            role             TEXT,
            criticality      INTEGER DEFAULT 0,
            runtime_hits     INTEGER DEFAULT 0,
            line_count       INTEGER DEFAULT 0,
            size_bytes       INTEGER DEFAULT 0,
            docstring        TEXT,
            modified         TEXT,
            error            TEXT
        );

        CREATE TABLE imports (
            importer    TEXT,
            imported    TEXT,
            is_local    INTEGER DEFAULT 0
        );

        CREATE TABLE functions (
            module_name TEXT,
            function    TEXT
        );

        CREATE TABLE classes (
            module_name TEXT,
            class_name  TEXT
        );

        CREATE TABLE reverse_deps (
            module      TEXT,
            imported_by TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_imports_importer  ON imports(importer);
        CREATE INDEX IF NOT EXISTS idx_imports_imported  ON imports(imported);
        CREATE INDEX IF NOT EXISTS idx_revdeps_module    ON reverse_deps(module);
        CREATE INDEX IF NOT EXISTS idx_revdeps_importedby ON reverse_deps(imported_by);
        CREATE INDEX IF NOT EXISTS idx_functions_module  ON functions(module_name);
    """)

    for rel_path, info in codebase_map["files"].items():
        mn = info.get("module_name", rel_path)
        c.execute("""
            INSERT OR REPLACE INTO modules
            (module_name, path, role, criticality, runtime_hits,
             line_count, size_bytes, docstring, modified, error)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            mn,
            info.get("path", rel_path),
            info.get("role", "misc"),
            info.get("criticality_score", 0),
            info.get("runtime_hits", 0),
            info.get("line_count", 0),
            info.get("size_bytes", 0),
            info.get("docstring", ""),
            info.get("modified", ""),
            info.get("error", ""),
        ))

        for imp in info.get("imports", []):
            is_local = 1 if imp in [
                i["module_name"] for i in codebase_map["files"].values()
                if "error" not in i
            ] else 0
            c.execute("INSERT INTO imports VALUES (?,?,?)", (mn, imp, is_local))

        for fn in info.get("functions", []):
            c.execute("INSERT INTO functions VALUES (?,?)", (mn, fn))

        for cls in info.get("classes", []):
            c.execute("INSERT INTO classes VALUES (?,?)", (mn, cls))

    for module, importers in codebase_map["reverse_deps"].items():
        for imp_by in importers:
            c.execute("INSERT INTO reverse_deps VALUES (?,?)", (module, imp_by))

    conn.commit()
    conn.close()
    print(f"  Wrote {output}")


# ── Query Interface ─────────────────────────────────────────────────────────────

class CartographerDB:
    """
    Echo's query interface to the codebase graph.
    Import and call from any module.

    Example:
        from echo_cartographer import CartographerDB
        db = CartographerDB()
        print(db.what_imports("memory_bridge"))
    """

    def __init__(self, db_path: Path = OUTPUT_DB):
        if not db_path.exists():
            raise FileNotFoundError(
                f"Codebase DB not found at {db_path}. "
                f"Run: python echo_cartographer.py"
            )
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def what_imports(self, module_name: str) -> list[str]:
        """What modules import this one?"""
        rows = self.conn.execute(
            "SELECT imported_by FROM reverse_deps WHERE module = ?",
            (module_name,)
        ).fetchall()
        return [r["imported_by"] for r in rows]

    def what_does_import(self, module_name: str) -> list[str]:
        """What does this module import?"""
        rows = self.conn.execute(
            "SELECT imported FROM imports WHERE importer = ? AND is_local = 1",
            (module_name,)
        ).fetchall()
        return [r["imported"] for r in rows]

    def module_info(self, module_name: str) -> dict | None:
        """Full info for a module."""
        row = self.conn.execute(
            "SELECT * FROM modules WHERE module_name = ?",
            (module_name,)
        ).fetchone()
        if not row:
            return None
        info = dict(row)
        info["functions"]   = [r["function"]   for r in self.conn.execute(
            "SELECT function FROM functions WHERE module_name = ?", (module_name,)
        ).fetchall()]
        info["classes"]     = [r["class_name"] for r in self.conn.execute(
            "SELECT class_name FROM classes WHERE module_name = ?", (module_name,)
        ).fetchall()]
        info["imported_by"] = self.what_imports(module_name)
        return info

    def top_critical(self, n: int = 10) -> list[dict]:
        """Top N modules by criticality score."""
        rows = self.conn.execute(
            "SELECT module_name, role, criticality, runtime_hits FROM modules "
            "ORDER BY criticality DESC LIMIT ?", (n,)
        ).fetchall()
        return [dict(r) for r in rows]

    def modules_by_role(self, role: str) -> list[str]:
        """All modules classified under a semantic role."""
        rows = self.conn.execute(
            "SELECT module_name FROM modules WHERE role = ? ORDER BY criticality DESC",
            (role,)
        ).fetchall()
        return [r["module_name"] for r in rows]

    def architecture_summary(self) -> str:
        """
        Compact architecture summary suitable for injection into
        build_echo_system_context(). Returns a structured string.
        """
        roles = ["memory", "learning", "reasoning", "routing", "safety", "self_mod", "identity", "comms"]
        lines = ["=== Echo Architecture (Cartographer) ==="]
        for role in roles:
            mods = self.modules_by_role(role)
            if mods:
                lines.append(f"\n{role.upper()}:")
                for m in mods[:5]:
                    info = self.conn.execute(
                        "SELECT criticality, runtime_hits FROM modules WHERE module_name = ?", (m,)
                    ).fetchone()
                    score = info["criticality"] if info else 0
                    hits  = info["runtime_hits"] if info else 0
                    lines.append(f"  {m}  [score={score}, hits={hits}]")

        top = self.top_critical(5)
        lines.append("\nTOP CRITICAL:")
        for m in top:
            lines.append(f"  {m['module_name']}  score={m['criticality']}  role={m['role']}")

        return "\n".join(lines)

    def update_runtime_hits(self, module_name: str, hits: int):
        """Called by runtime_tracer.py to populate Tier 3."""
        self.conn.execute(
            "UPDATE modules SET runtime_hits = ?, "
            "criticality = (SELECT imported_by_count FROM ("
            "  SELECT COUNT(*) AS imported_by_count FROM reverse_deps WHERE module = ?"
            ") * 3) + (SELECT fn_count FROM ("
            "  SELECT COUNT(*) AS fn_count FROM functions WHERE module_name = ?"
            ") * 2) + ? "
            "WHERE module_name = ?",
            (hits, module_name, module_name, hits, module_name)
        )
        self.conn.commit()

    def close(self):
        self.conn.close()


# ── Interactive Query Mode ──────────────────────────────────────────────────────

def interactive_query():
    try:
        db = CartographerDB()
    except FileNotFoundError as e:
        print(e)
        return

    print("\nCartographer Query Mode")
    print("Commands: imports <module> | importedby <module> | info <module> | top | roles | summary | quit\n")

    while True:
        try:
            cmd = input("> ").strip().split(None, 1)
        except (EOFError, KeyboardInterrupt):
            break

        if not cmd:
            continue
        op = cmd[0].lower()
        arg = cmd[1].strip() if len(cmd) > 1 else ""

        if op in ("quit", "exit", "q"):
            break
        elif op == "importedby" and arg:
            result = db.what_imports(arg)
            print(f"  {arg} imported by: {result or 'nothing found'}")
        elif op == "imports" and arg:
            result = db.what_does_import(arg)
            print(f"  {arg} imports: {result or 'nothing local'}")
        elif op == "info" and arg:
            info = db.module_info(arg)
            print(json.dumps(info, indent=2) if info else f"  Not found: {arg}")
        elif op == "top":
            for m in db.top_critical(10):
                print(f"  {m['module_name']:40s}  score={m['criticality']:4d}  role={m['role']}")
        elif op == "roles":
            for role in SEMANTIC_ROLES:
                mods = db.modules_by_role(role)
                if mods:
                    print(f"  {role}: {', '.join(mods)}")
        elif op == "summary":
            print(db.architecture_summary())
        else:
            print("  Unknown command")

    db.close()


# ── Print Summary ───────────────────────────────────────────────────────────────

def print_summary(codebase_map: dict):
    print(f"\nTotal files indexed: {codebase_map['file_count']}")
    print("\nTop 10 Critical Modules:")
    for i, m in enumerate(codebase_map["top_critical"][:10], 1):
        print(f"  {i:2d}. {m['module']:40s}  score={m['score']:4d}  role={m['role']}")

    print("\nReverse dependency highlights:")
    for module, importers in sorted(
        codebase_map["reverse_deps"].items(),
        key=lambda x: len(x[1]),
        reverse=True
    )[:10]:
        print(f"  {module:40s}  imported by {len(importers):2d}: {importers}")


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="FeralEcho Codebase Cartographer")
    parser.add_argument("--query",   action="store_true", help="Interactive query mode")
    parser.add_argument("--summary", action="store_true", help="Print architecture summary from DB")
    parser.add_argument("--root",    default=".",         help="Project root path")
    args = parser.parse_args()

    if args.query:
        interactive_query()
        return

    if args.summary:
        try:
            db = CartographerDB()
            print(db.architecture_summary())
            db.close()
        except FileNotFoundError as e:
            print(e)
        return

    project_root  = Path(args.root)
    codebase_map  = build_map(project_root)

    write_json(codebase_map, OUTPUT_JSON)
    write_sqlite(codebase_map, OUTPUT_DB)
    print_summary(codebase_map)

    print(f"\nDone. Run with --query to interrogate the graph.")
    print(f"Echo can now answer: what imports memory_bridge?")


if __name__ == "__main__":
    main()
