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

# R6: finite policy accumulation; never an Echo/procedural-learning claim.
stage=int(sys.argv[1])
assert stage in range(4)
statepath=SCRATCH/"policy.json"
FAMILIES=["context_"+str(i) for i in range(9)]
MODELS=["worker_red","worker_green","worker_blue"]
ASSIGN=[2,0,1,1,2,0,0,1,2] # evaluator-only mapping; each acquisition block balanced
FUNCS=[sum,max,min]
def truth(family,values):
    # Independent implementations vs builtin workers.
    op=ASSIGN[FAMILIES.index(family)] if family in FAMILIES else 2
    value=0 if op==0 else values[0]
    for x in values:
        if op==0:value+=x
        elif op==1 and x>value:value=x
        elif op==2 and x<value:value=x
    return value
def sample(stage_id,family_id,j,teaching=False):
    offset=(10 if teaching else 1000)+stage_id*100+family_id*7+j
    return [offset,3,-offset//2]
def estimate_update(table,key,reward):
    pair=table.setdefault(key,[0,0])
    pair[0]+=1;pair[1]+=int(reward)
def estimate(table,key):
    n,total=table.get(key,[0,0])
    return total/n if n>=5 else .5
pool3={m:{"tags":[]} for m in MODELS}
ns["RIVER_BRAIN_PATH"]=str(SCRATCH/"global.pkl")
if stage==0:
    state={"context":{},"reversed":{},"seen_training":[],"pids":[]}
    globalbrain=IsolatedRiver()
else:
    state=json.loads(statepath.read_text())
    assert len(state["pids"])==stage and os.getpid() not in state["pids"]
    assert hashlib.sha256((SCRATCH/"global.pkl").read_bytes()).hexdigest()==state["global_hash"]
    globalbrain=IsolatedRiver.load()
state["pids"].append(os.getpid())
rows=[]
if stage:
    for fi in range((stage-1)*3,stage*3):
        family=FAMILIES[fi]
        for j in range(8):
            values=sample(stage,fi,j,True)
            state["seen_training"].append(values)
            expected=truth(family,values)
            for mi,model in enumerate(MODELS):
                result=FUNCS[mi](values);reward=result==expected
                observe(globalbrain,model,reward)
                estimate_update(state["context"],family+"|"+model,reward)
                estimate_update(state["reversed"],family+"|"+model,not reward)
                rows.append({"family":family,"input":values,"model":model,"actual":result,"expected":expected,"reward":reward})
# Same true outcomes are exposed to global and contextual updates; reversed
# is a negative control. Frozen/no-update arm receives no updated policy.
def decide(arm,family):
    if arm=="global":
        return select("coding",globalbrain,pool3,council_size=1,exploration_bias=0,fair_sample_refresh=False)[0]
    if arm=="frozen":return MODELS[0]
    table=state[arm]
    return max(MODELS,key=lambda m:estimate(table,family+"|"+m))
evaluations={}
state_before=json.dumps(state,sort_keys=True)
for arm in ("frozen","global","context","reversed"):
    testrows=[]
    for fi,family in enumerate(FAMILIES):
        picked=decide(arm,family)
        for j in range(10):
            values=sample(stage,fi,j)
            assert values not in state["seen_training"]
            actual=FUNCS[MODELS.index(picked)](values)
            expected=truth(family,values)
            testrows.append({"family":family,"input":values,"selected":picked,"actual":actual,"expected":expected,"correct":actual==expected})
    evaluations[arm]={"correct":sum(r["correct"] for r in testrows),"n":len(testrows),"rows":testrows,
        "per_family":{f:sum(r["correct"] for r in testrows if r["family"]==f) for f in FAMILIES}}
assert json.dumps(state,sort_keys=True)==state_before, "evaluation modified learning state"
# Attack: same labels with changed meaning; no compatibility detection.
drift=[]
for fi,family in enumerate(FAMILIES):
    values=sample(9,fi,0)
    mi=MODELS.index(decide("context",family))
    drift.append(FUNCS[mi](values)==FUNCS[(ASSIGN[fi]+1)%3](values))
# New context has no evidence; old contextual knowledge must not auto-apply.
unknown_choice=decide("context","unseen_context")
globalbrain._do_save()
state["global_hash"]=hashlib.sha256((SCRATCH/"global.pkl").read_bytes()).hexdigest()
statepath.write_text(json.dumps(state,sort_keys=True))
out={"stage":stage,"pid":os.getpid(),"pids":state["pids"],"scratch":str(SCRATCH),
    "script_sha256":hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
    "production_source_sha256":hashlib.sha256(raw.encode()).hexdigest(),
    "training":rows,"evaluations":evaluations,"context_entries":len(state["context"]),
    "mean_scores":{m:globalbrain.score_model(m,"coding") for m in MODELS},
    "drift_correct":sum(drift),"drift_n":len(drift),"unknown_choice":unknown_choice,
    "evaluation_state_unchanged":True,"policy_sha256":hashlib.sha256(statepath.read_bytes()).hexdigest()}
(ART/("r6_t"+str(stage)+".json")).write_text(json.dumps(out,indent=2))
print(json.dumps({"stage":stage,"pid":os.getpid(),"scratch":str(SCRATCH),"correct_out_of_90":{a:v["correct"] for a,v in evaluations.items()},"drift_correct":sum(drift)}))
if stage==3:
    import shutil
    shutil.rmtree(SCRATCH)

