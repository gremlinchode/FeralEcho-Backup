"""Isolated installed-capability checks. No production imports or model calls."""
import ast, hashlib, importlib, importlib.metadata as md, json, os, pathlib, pickle, shutil, sqlite3, subprocess, sys, tempfile, time
ART=pathlib.Path(__file__).resolve().parent
ROOT=ART.parents[1]
sys.dont_write_bytecode=True
def restrict(scratch):
    def audit(event,args):
        if event.startswith(("socket.","subprocess.")) or event in ("os.system","os.exec","os.fork","os.posix_spawn","os.kill","os.killpg"):
            raise RuntimeError("AUDIT_BOUNDARY:"+event)
        if event=="open":
            p,mode,flags=args
            if isinstance(p,(str,bytes,os.PathLike)):
                p=pathlib.Path(os.fsdecode(p)).resolve()
                writing=(isinstance(mode,str) and any(c in mode for c in "wax+")) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
                if writing and not p.is_relative_to(scratch):raise RuntimeError("AUDIT_BOUNDARY:write:"+str(p))
    sys.addaudithook(audit)
if len(sys.argv)>1 and sys.argv[1]=="import":
    restrict(pathlib.Path(os.environ["PYGAP_SCRATCH"]).resolve())
    t=time.monotonic()
    try:
        m=importlib.import_module(sys.argv[2])
        result={"module":sys.argv[2],"status":"IMPORTABLE","path":getattr(m,"__file__",None)}
    except Exception as e:
        result={"module":sys.argv[2],"status":"BOUNDARY_LIMITED" if "AUDIT_BOUNDARY" in str(e) else "IMPORT_ERROR","error":type(e).__name__+": "+str(e)}
    result["seconds"]=round(time.monotonic()-t,4)
    print("PYGAP_JSON:"+json.dumps(result));sys.exit(0)
if len(sys.argv)>1 and sys.argv[1]=="primitives":
    restrict(pathlib.Path(os.environ["PYGAP_SCRATCH"]).resolve())
    from river import bandit,drift,linear_model,optim,preprocessing,metrics
    import numpy as np
    from scipy import stats
    from sklearn.feature_extraction.text import TfidfVectorizer
    result={}
    policy=bandit.LinUCBDisjoint(seed=7)
    for _ in range(16):
        for x,target in (({"ctx_left":1.0},0),({"ctx_right":1.0},1)):
            for a in (0,1):policy.update(a,x,int(a==target))
    selected=[policy.pull([0,1],context=x) for x in ({"ctx_left":1.0},{"ctx_right":1.0})]
    restored=pickle.loads(pickle.dumps(policy))
    result["river_contextual"]={"class":type(policy).__name__,"selected":selected,"pickle_roundtrip":[restored.pull([0,1],context=x) for x in ({"ctx_left":1.0},{"ctx_right":1.0})],"scope":"full-information synthetic update smoke, not bandit regret or real learning experiment"}
    detector=drift.ADWIN();alarms=[]
    for i,x in enumerate([0]*400+[1]*400):
        detector.update(x)
        if detector.drift_detected:alarms.append(i)
    result["drift"]={"class":"ADWIN","alarms":alarms,"scope":"one deterministic step-change, not false-alarm calibration"}
    con=sqlite3.connect(":memory:")
    con.execute("CREATE TABLE outcomes(attempt TEXT PRIMARY KEY, reward INTEGER)")
    con.execute("INSERT INTO outcomes VALUES('a',1)")
    try:con.execute("INSERT INTO outcomes VALUES('a',0)")
    except sqlite3.IntegrityError:dedup=True
    else:dedup=False
    con.commit()
    con.execute("BEGIN");con.execute("INSERT INTO outcomes VALUES('b',0)");con.rollback()
    con.execute("CREATE VIRTUAL TABLE docs USING fts5(body)")
    con.execute("INSERT INTO docs VALUES('integer arithmetic retained procedure')")
    hits=con.execute("SELECT body,bm25(docs) FROM docs WHERE docs MATCH 'integer'").fetchall()
    result["sqlite"]={"version":sqlite3.sqlite_version,"duplicate_rejected":dedup,"rollback_rows":con.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0],"fts5_hits":len(hits)}
    result["statistics"]={"binomtest_3_of_5":stats.binomtest(3,5,p=.5).pvalue,"beta_interval":list(stats.beta.interval(.95,9,3))}
    vect=TfidfVectorizer(ngram_range=(1,2));X=vect.fit_transform(["exact integer division","creative story about rivers","integer modulo parity"])
    similarities=(X@vect.transform(["integer division"]).T).toarray().ravel()
    result["sparse_retrieval"]={"shape":list(X.shape),"selected_doc":int(similarities.argmax()),"scores":similarities.tolist()}
    # Recheck the current production reward/consumer separation statically.
    tree=ast.parse((ROOT/"app/core/echo_model_orchestrator.py").read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="RiverBrain")
    result["river_source"]={}
    for name in ("learn","learn_from_rating","learn_from_sandbox_outcome","score_model"):
        n=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
        result["river_source"][name]={"line":n.lineno,"model_task_stats_referenced":any(isinstance(x,ast.Attribute) and x.attr=="model_task_stats" for x in ast.walk(n)),"classifier_prediction_referenced":any(isinstance(x,ast.Attribute) and x.attr=="predict_one" for x in ast.walk(n))}
    # Verify R9's pure archived functions on the original and precision cases.
    rows=[json.loads(x) for x in (ROOT/"audits/tier5_retest/tier5_retest_results.jsonl").read_text().splitlines()]
    result["oracle_counterexample"]=[]
    for row in rows:
        if row["task_id"]!="r-bf02":continue
        t=ast.parse(row["candidate_code"])
        assert len(t.body)==1 and isinstance(t.body[0],ast.FunctionDef)
        forbidden=(ast.Import,ast.ImportFrom,ast.Attribute,ast.With,ast.Try,ast.Global,ast.Nonlocal,ast.ClassDef)
        assert not any(isinstance(n,forbidden) for n in ast.walk(t))
        assert all(isinstance(n.func,ast.Name) and n.func.id=="int" for n in ast.walk(t) if isinstance(n,ast.Call))
        ns={"__builtins__":{"int":int}};exec(compile(t,"<inspected-historical-integer-predicate>","exec"),ns)
        n=2**60+2;actual=ns["is_power_of_two"](n);expected=n>0 and n&(n-1)==0
        result["oracle_counterexample"].append({"condition":row["condition"],"input":n,"actual":actual,"expected":expected,"original_passed":row["passed"]})
    print("PYGAP_JSON:"+json.dumps(result));sys.exit(0)

scratch=pathlib.Path(tempfile.mkdtemp(prefix="feralecho-pygap-",dir="/private/tmp"))
env=os.environ.copy()
env.update({"PYGAP_SCRATCH":str(scratch),"XDG_CACHE_HOME":str(scratch/"cache"),"MPLCONFIGDIR":str(scratch/"mpl"),"HF_HOME":str(scratch/"hf"),"NUMBA_CACHE_DIR":str(scratch/"numba"),"TMPDIR":str(scratch),
"PYTENSOR_FLAGS":"base_compiledir="+str(scratch/"pytensor"),"DSPY_CACHEDIR":str(scratch/"dspy"),"LITELLM_LOCAL_MODEL_COST_MAP":"True","HF_HUB_OFFLINE":"1","TRANSFORMERS_OFFLINE":"1","ANONYMIZED_TELEMETRY":"False","DO_NOT_TRACK":"1","OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1","PYTHONDONTWRITEBYTECODE":"1"})
modules=["river","numpy","scipy","sklearn","faiss","torch","sentence_transformers","transformers","optuna","apricot","networkx","statsmodels.api","pymc","arviz","sympy","pydantic","jsonschema","sqlalchemy","pandas","pytest","dspy","langgraph.graph","chromadb","pgmpy","pomegranate","ollama"]
results=[]
try:
 for name in modules+["__PRIMITIVES__"]:
    args=[sys.executable,"-B","-I",str(pathlib.Path(__file__).resolve())]
    args+=["primitives"] if name=="__PRIMITIVES__" else ["import",name]
    try:
        p=subprocess.run(args,env=env,cwd=str(scratch),capture_output=True,text=True,timeout=35)
        lines=[x for x in p.stdout.splitlines() if x.startswith("PYGAP_JSON:")]
        item=json.loads(lines[-1].split(":",1)[1]) if lines else {"module":name,"status":"PROCESS_ERROR","returncode":p.returncode,"stderr":p.stderr[-3000:],"stdout":p.stdout[-1000:]}
    except subprocess.TimeoutExpired:item={"module":name,"status":"TIMEOUT_35s"}
    results.append(item);print(json.dumps({"probe":name,"status":item.get("status","DONE")}),flush=True)
finally:
 shutil.rmtree(scratch)
(ART/"installed_capability_probes.json").write_text(json.dumps({"scope":"fresh isolated subprocess per import; network/process calls blocked in children; no production imports or model construction","scratch_removed":not scratch.exists(),"results":results},indent=2))

