"""Read-only environment and source inventory; writes only audit artifacts."""
import ast, datetime, hashlib, importlib.metadata as md, json, pathlib, platform, sqlite3, sys, sysconfig
ROOT=pathlib.Path(__file__).resolve().parents[2]
ART=pathlib.Path(__file__).resolve().parent
packages=[]
for d in md.distributions():
    meta=d.metadata
    packages.append({"name":meta.get("Name"),"version":d.version,"requires_python":meta.get("Requires-Python"),
        "license_expression":meta.get("License-Expression"),"license":meta.get("License"),
        "requires_dist":d.requires or [],"installer":(d.read_text("INSTALLER") or "").strip(),
        "location":str(d.locate_file(""))})
conda=[]
for p in sorted((pathlib.Path(sys.prefix)/"conda-meta").glob("*.json")):
    d=json.loads(p.read_text())
    conda.append({k:d.get(k) for k in ("name","version","build","subdir")})
inventory={"captured_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"executable":sys.executable,
 "resolved_executable":str(pathlib.Path(sys.executable).resolve()),"version":sys.version,"prefix":sys.prefix,
 "base_prefix":sys.base_prefix,"machine":platform.machine(),"platform":platform.platform(),
 "SOABI":sysconfig.get_config_var("SOABI"),"sqlite":sqlite3.sqlite_version,
 "distributions":sorted(packages,key=lambda x:x["name"].lower()),"conda_records":conda,
 "package_to_modules":md.packages_distributions()}
(ART/"environment_inventory.json").write_text(json.dumps(inventory,indent=2,sort_keys=True))
roots={"river","torch","numpy","scipy","sklearn","faiss","sentence_transformers","transformers","networkx","pymc","arviz",
 "pgmpy","pomegranate","optuna","apricot","sympy","statsmodels","dspy","langgraph","langchain","langchain_core","chromadb",
 "sqlalchemy","pydantic","jsonschema","opentelemetry","apscheduler","pandas","sqlite3","mlx","mlx_lm","ollama","radon",
 "hypothesis","mutmut","pytest","unittest"}
traces=[];errors=[]
for parent in (ROOT/"app",ROOT/"scripts"):
 for p in sorted(parent.rglob("*.py")):
    rel=str(p.relative_to(ROOT))
    if any(s in p.parts for s in ("self_edit_backups","self_edit_plans","__pycache__")) or "_backup_" in p.name or "/app/core/app/" in "/"+rel:continue
    try:tree=ast.parse(p.read_text(errors="replace"))
    except SyntaxError as e:errors.append({"path":rel,"error":str(e)});continue
    for n in ast.walk(tree):
        names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or ""] if isinstance(n,ast.ImportFrom) else []
        for name in names:
            if name.split(".")[0] in roots:
                traces.append({"path":rel,"line":n.lineno,"module":name,
                  "area":"experiment" if "/experiments/" in rel else "script" if rel.startswith("scripts/") else "app",
                  "source_sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
(ART/"source_import_inventory.json").write_text(json.dumps({"traces":traces,"syntax_errors":errors,"scope":"app/ and scripts/; excludes backups/plans/nested duplicate app; AST imports include function-local/dead branches; not reachability proof"},indent=2))
print(json.dumps({"python":sys.version,"distributions":len(packages),"conda_records":len(conda),"imports":len(traces),"parse_errors":len(errors),"inventory_path":str(ART/"environment_inventory.json")}))

