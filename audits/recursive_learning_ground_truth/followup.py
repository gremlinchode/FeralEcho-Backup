"""Isolated component experiments. Never imports the production orchestrator.
Run with the existing feral_echo Python, -B -I, from the repository root.
Only authored arithmetic fixtures execute. No model or network calls.
"""
import ast, collections, datetime, fcntl, hashlib, importlib.util, json, logging
import math, os, pathlib, pickle, queue, random, sys, tempfile, threading, types
ROOT = pathlib.Path(__file__).resolve().parents[2]
ART = pathlib.Path(__file__).resolve().parent
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
sys.dont_write_bytecode = True
SCRATCH = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else pathlib.Path(tempfile.mkdtemp(prefix="feralecho-recursive-", dir="/private/tmp"))
assert SCRATCH.parent == pathlib.Path("/private/tmp") and SCRATCH.name.startswith("feralecho-recursive-")
EVENTS = []
def audit(event, args):
    if event.startswith(("socket.", "subprocess.")) or event in ("os.system","os.exec","os.fork","os.posix_spawn","os.kill","os.killpg"):
        raise RuntimeError("experiment boundary: "+event)
    if event == "open":
        p, mode, flags = args
        if isinstance(p,(str,bytes,os.PathLike)):
            p = pathlib.Path(os.fsdecode(p)).resolve()
            writing = (isinstance(mode,str) and any(c in mode for c in "wax+")) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if writing and not (p.is_relative_to(SCRATCH) or p.is_relative_to(ART)):
                raise RuntimeError("out-of-experiment write: "+str(p))
            if p.suffix == ".pkl" and not p.is_relative_to(SCRATCH):
                raise RuntimeError("production pickle prohibited")
sys.addaudithook(audit)
from river import tree, preprocessing, metrics
SOURCE = ROOT/"app/core/echo_model_orchestrator.py"
raw = SOURCE.read_text()
parsed = ast.parse(raw)
def extract(names):
    nodes=[n for n in parsed.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    return compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE),"exec")
def leaf(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module);return module
quality=leaf("echo_quality_scorer.py","_recursive_quality")
task_map=next(ast.literal_eval(n.value) for n in parsed.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="TASK_TYPE_MAP" for t in n.targets))
ns=dict(defaultdict=collections.defaultdict,threading=threading,_queue=queue,
    logging=logging,math=math,os=os,pickle=pickle,fcntl=fcntl,time=__import__("time"),
    RIVER_AVAILABLE=True,TASK_TYPE_MAP=task_map,tree=tree,preprocessing=preprocessing,metrics=metrics,
    COUNCIL_RATING_WEIGHT=0.3,QUALITY_SCORE_WEIGHT=0.7,
    _extract_quality_features=quality._extract_quality_features_v2,
    _score_response_quality=quality._score_response_quality,
    log_interaction=lambda **kw:EVENTS.append({"log_sink":kw}),
    RIVER_BRAIN_PATH=str(SCRATCH/"brain.pkl"))
exec(extract({"RiverBrain","_blend_council_and_quality"}),ns)
River=ns["RiverBrain"]
class IsolatedRiver(River):
    def __init__(self):
        self.classifiers={};self.scalers={};self.accuracy_trackers={}
        self.observation_counts=collections.defaultdict(int)
        self.sandbox_observation_counts=collections.defaultdict(int)
        self.model_task_stats=collections.defaultdict(dict)
        self._lock=threading.Lock();self._save_queue=queue.Queue(10)
        self._init_classifiers()
# Production __init__ and its writer are deliberately not invoked.
selector_path=ROOT/"app/core/river_deliberation.py"
selector_ast=ast.parse(selector_path.read_text())
selector_node=next(n for n in selector_ast.body if isinstance(n,ast.FunctionDef) and n.name=="_select_council")
constants={}
for n in selector_ast.body:
    if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name):
        try:constants[n.target.id]=ast.literal_eval(n.value)
        except (ValueError,TypeError):pass
sel_ns=dict(logging=logging,random=random,**constants)
assert all(k in sel_ns for k in ("DEFAULT_COUNCIL_SIZE","ECHO_SYNTHESIS_MODEL","ECHO_SCORE_BOOST","TAG_SCORE_BOOST","UNDER_SAMPLED_REFRESH_PROBABILITY"))
exec(compile(ast.Module(body=[selector_node],type_ignores=[]),str(selector_path),"exec"),sel_ns)
select=sel_ns["_select_council"]
GOOD="def solve(values):\n    return sum(values)\n"
BAD="def solve(values):\n"+"".join("    if len(values) > "+str(i)+":\n        unused = "+str(i)+"\n" for i in range(6))+"    return -999999\n"
def materialize(code):
    d={};exec(compile(code,"<authored-arithmetic-fixture>","exec"),d)
    return d["solve"]
workers={"candidate_A":materialize(GOOD),"candidate_B":materialize(BAD)}
pool={k:{"tags":[]} for k in workers}
def choice(brain):
    return select("coding",brain,pool,council_size=1,exploration_bias=0,fair_sample_refresh=False)[0]
def stats(brain):
    return {k:{"score":brain.score_model(k,"coding"),"n":brain.observations_for(k,"coding")} for k in workers}
def observe(brain, model, reward, task="coding"):
    # Experimental adapter, NOT a production method: valid outcome -> same
    # rolling-mean statistic consumed by exact production score_model.
    s=brain.model_task_stats[model].setdefault(task,{"count":0,"mean":0.5})
    s["count"]+=1
    s["mean"]+=(float(reward)-s["mean"])/min(s["count"],brain._MEAN_EFFECTIVE_WINDOW)
def oracle(values):
    total=0
    for x in values:total+=x
    return total
train=[[i,2,-i] for i in range(1,9)]
heldout=[[100+i,3,-i] for i in range(24)]
assert not {tuple(x) for x in train}&{tuple(x) for x in heldout}
def performance(brain, inputs):
    selected=choice(brain);rows=[]
    for x in inputs:
        value=workers[selected](list(x));expected=oracle(x)
        rows.append({"input":x,"selected":selected,"actual":value,"expected":expected,"correct":value==expected})
    return {"selected":selected,"correct":sum(r["correct"] for r in rows),"n":len(rows),"rows":rows}
def baseline():
    b=IsolatedRiver()
    for _ in range(8):
        b.learn("candidate_A","coding",GOOD);b.learn("candidate_B","coding",BAD)
    return b

# R4: identity/order attack and real cross-process River checkpoint.
mode=sys.argv[1]
if mode=="produce":
    rows=[]
    for reverse in (False,True):
        for rename in (False,True):
            names=("opaque_1","opaque_2") if not rename else ("opaque_2","opaque_1")
            fixture=dict(zip(names,(GOOD,BAD)))
            order=list(names)[::-1] if reverse else list(names)
            localpool={name:{"tags":[]} for name in order}
            for arm in ("sandbox_only","auto_quality","verified_outcome","reversed_outcome"):
                brain=IsolatedRiver()
                for x in train:
                    for name,code in fixture.items():
                        correct=materialize(code)(x)==oracle(x)
                        if arm=="sandbox_only":brain.learn_from_sandbox_outcome(name,correct,code)
                        elif arm=="auto_quality":brain.learn(name,"coding",code)
                        else:observe(brain,name,correct if arm=="verified_outcome" else not correct)
                picked=select("coding",brain,localpool,council_size=1,exploration_bias=0,fair_sample_refresh=False)[0]
                rows.append({"arm":arm,"order":order,"good_identity":names[0],"selected":picked,
                    "heldout_correct":sum(materialize(fixture[picked])(x)==oracle(x) for x in heldout),"n":len(heldout)})
    brain=IsolatedRiver()
    for x in train:
        for name in workers:observe(brain,name,workers[name](x)==oracle(x))
    brain._do_save()
    result={"pid":os.getpid(),"rows":rows,"checkpoint":str(SCRATCH/"brain.pkl"),
       "checkpoint_sha256":hashlib.sha256((SCRATCH/"brain.pkl").read_bytes()).hexdigest(),
       "expected_restored":stats(brain),"scratch":str(SCRATCH)}
    (ART/"r4_producer.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({"scratch":str(SCRATCH),"pid":os.getpid(),"arm_totals":{a:sum(r["heldout_correct"] for r in rows if r["arm"]==a) for a in ("sandbox_only","auto_quality","verified_outcome","reversed_outcome")}}))

elif mode=="consume":
    producer=json.loads((ART/"r4_producer.json").read_text())
    assert os.getpid()!=producer["pid"]
    assert hashlib.sha256((SCRATCH/"brain.pkl").read_bytes()).hexdigest()==producer["checkpoint_sha256"]
    restored=IsolatedRiver.load()
    result={"pid":os.getpid(),"producer_pid":producer["pid"],"restored":stats(restored),
       "same_stats":stats(restored)==producer["expected_restored"],"heldout":performance(restored,heldout)}
    assert result["same_stats"] and result["heldout"]["correct"]==24
    (ART/"r4_consumer.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({"pid":os.getpid(),"same_stats":result["same_stats"],"heldout_correct":result["heldout"]["correct"]}))
    import shutil
    shutil.rmtree(SCRATCH)

elif mode=="memory":
    # Real FAISS/VectorMemory, explicit isolated paths and authored embeddings.
    # faiss writes via C++; every path delivered to it is scratch, no live index.
    import numpy as np
    vm=leaf("app/lib/vector_memory.py","_recursive_vector_memory")
    results={}
    for scenario in ("unique","duplicate"):
        d=SCRATCH/scenario;d.mkdir()
        m=vm.VectorMemory(dim=3,index_path=str(d/"index"),meta_path=str(d/"meta.json"))
        m.add([vm.MemoryItem("alpha","old alpha")],np.array([[1,0,0]],dtype=np.float32))
        if scenario=="duplicate":
            m.add([vm.MemoryItem("alpha","revised alpha")],np.array([[0,1,0]],dtype=np.float32))
        m.add([vm.MemoryItem("beta","beta")],np.array([[0,0,1]],dtype=np.float32))
        def queries(obj):
            return {label:obj.search(np.array(q,dtype=np.float32),k=1) for label,q in
              (("old_alpha",[1,0,0]),("revised_alpha",[0,1,0]),("beta",[0,0,1]))}
        r={"ntotal":m.index.ntotal,"ids":m.id_order,"before":queries(m)}
        restored=vm.VectorMemory(dim=3,index_path=str(d/"index"),meta_path=str(d/"meta.json"))
        r["after_reload"]=queries(restored);results[scenario]=r
    (ART/"r5_memory.json").write_text(json.dumps(results,indent=2))
    print(json.dumps(results))
    import shutil
    shutil.rmtree(SCRATCH)
elif mode=="shortcut":
    fixtures={"opaque_sum":GOOD,"opaque_shortcut":"def solve(values):\n    return 2\n"}
    rich=[[i,2,-i+(i%3)] for i in range(1,9)]
    results=[]
    for distribution,examples in (("constant_target_training",train),("varied_target_training",rich)):
        for order in (list(fixtures),list(fixtures)[::-1]):
            brain=IsolatedRiver()
            for x in examples:
                for name,code in fixtures.items():observe(brain,name,materialize(code)(x)==oracle(x))
            chosen=select("coding",brain,{n:{"tags":[]} for n in order},council_size=1,exploration_bias=0,fair_sample_refresh=False)[0]
            results.append({"distribution":distribution,"training":examples,"order":order,"selected":chosen,
                "scores":{n:brain.score_model(n,"coding") for n in fixtures},
                "heldout_correct":sum(materialize(fixtures[chosen])(x)==oracle(x) for x in heldout),"n":len(heldout)})
    (ART/"r8_shortcut.json").write_text(json.dumps({"fixtures":fixtures,"heldout":heldout,"results":results},indent=2))
    print(json.dumps(results))
    import shutil
    shutil.rmtree(SCRATCH)
else:raise ValueError(mode)
