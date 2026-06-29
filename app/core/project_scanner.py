# app/core/project_scanner.py
import os
import ast
import logging
from collections import defaultdict

logging.basicConfig(level=logging.DEBUG)

# Scan the entire FeralEcho folder
PROJECT_ROOT = "."  # "." means current folder, i.e., FeralEcho root

# -----------------------------
# --- Helper Functions -------
# -----------------------------

def list_python_files(root_dir=PROJECT_ROOT):
    """Recursively list all .py files in project"""
    py_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith(".py"):
                py_files.append(os.path.join(dirpath, f))
    return py_files

def parse_file(filepath):
    """Parse a Python file and return its AST, catching syntax errors"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        return tree, None
    except SyntaxError as e:
        logging.warning(f"Syntax error in {filepath}: {e}")
        return None, e

def detect_functions_and_classes(tree):
    """Return dict of functions and classes in AST tree"""
    funcs, classes = [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            funcs.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return funcs, classes

# -----------------------------
# --- Core Project Scanner ----
# -----------------------------

def scan_project(root_dir=PROJECT_ROOT):
    """Scan the project, detect issues, and index structure"""
    issues = defaultdict(list)
    index = defaultdict(dict)

    py_files = list_python_files(root_dir)
    for file in py_files:
        tree, error = parse_file(file)
        if error:
            issues[file].append(f"SyntaxError: {error}")
            continue

        funcs, classes = detect_functions_and_classes(tree)
        index[file]["functions"] = funcs
        index[file]["classes"] = classes

        # Detect stubs (naive: lines containing 'print("Hello from self-edit stub")')
        with open(file, "r", encoding="utf-8") as f:
            source = f.read()
            if 'print("Hello from self-edit stub")' in source:
                issues[file].append("Contains repeated self-edit stub")

        # Detect functions with missing arguments by checking known signature issues
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == "generate_code":
                    # Expect 'intensity' and 'creativity' args for Optuna trials
                    arg_names = [arg.arg for arg in node.args.args]
                    if "intensity" not in arg_names or "creativity" not in arg_names:
                        issues[file].append("Missing 'intensity'/'creativity' args for Optuna")

    return {"index": index, "issues": issues}

# -----------------------------
# --- Reporting --------------
# -----------------------------

def generate_issue_report(scan_result):
    """Format issues into a readable report"""
    issues = scan_result["issues"]
    report_lines = []
    for file, problems in issues.items():
        report_lines.append(f"{file}:")
        for p in problems:
            report_lines.append(f"  - {p}")
    return "\n".join(report_lines)

# -----------------------------
# --- Example Usage ----------
# -----------------------------
if __name__ == "__main__":
    scan_result = scan_project()
    report = generate_issue_report(scan_result)
    print("=== PROJECT ISSUE REPORT ===")
    print(report)

