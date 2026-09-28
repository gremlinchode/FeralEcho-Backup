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
SCRATCH = pathlib.Path(tempfile.mkdtemp(prefix="feralecho-recursive-", dir="/private/tmp"))
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
out={"scope":"exact-method isolated component, authored fixed workers; not Echo inference",
    "source_sha256":hashlib.sha256(raw.encode()).hexdigest(),
    "selector_sha256":hashlib.sha256(selector_path.read_bytes()).hexdigest(),
    "scorer_sha256":hashlib.sha256((ROOT/"echo_quality_scorer.py").read_bytes()).hexdigest(),
    "fixtures":{"good":GOOD,"bad":BAD,"train":train,"heldout":heldout},
    "quality":{"good":quality._score_response_quality(GOOD,"coding"),"bad":quality._score_response_quality(BAD,"coding")}}
# R1: real feedback methods vs the decision consumer.
b=baseline();before=stats(b)
classifier_before=hashlib.sha256(pickle.dumps(b.classifiers)).hexdigest()
for _ in range(40):
    b.learn_from_rating("candidate_A","coding",GOOD,5)
    b.learn_from_rating("candidate_B","coding",BAD,1)
    b.learn_from_sandbox_outcome("candidate_A",True,GOOD)
    b.learn_from_sandbox_outcome("candidate_B",False,error="wrong answer")
out["R1"]={"before":before,"after":stats(b),"selected":choice(b),
    "classifiers_changed":classifier_before!=hashlib.sha256(pickle.dumps(b.classifiers)).hexdigest(),
    "observations":dict(b.observation_counts),"sandbox_observations":dict(b.sandbox_observation_counts),
    "scores_unchanged":before==stats(b)}
# R2/R3: fixed worker pool, same experience executions; change reward path only.
arms={}
for arm in ("auto_quality","sandbox_only","verified_outcome","reversed_outcome"):
    b=IsolatedRiver()
    rows=[]
    for x in train:
        for model,code in (("candidate_A",GOOD),("candidate_B",BAD)):
            actual=workers[model](list(x));reward=actual==oracle(x)
            rows.append({"input":x,"model":model,"actual":actual,"expected":oracle(x),"reward":reward})
            if arm=="auto_quality":b.learn(model,"coding",code)
            elif arm=="sandbox_only":b.learn_from_sandbox_outcome(model,reward,code,error="wrong answer" if not reward else "")
            else:observe(b,model,reward if arm=="verified_outcome" else not reward)
    ns["RIVER_BRAIN_PATH"]=str(SCRATCH/(arm+".pkl"))
    b._do_save()
    assert pathlib.Path(ns["RIVER_BRAIN_PATH"]).is_file()
    restored=IsolatedRiver.load()
    arms[arm]={"train_rows":rows,"before_save":stats(b),"after_load":stats(restored),
        "same_after_load":stats(b)==stats(restored),"heldout":performance(restored,heldout)}
out["R2_R3"]=arms
out["writer_threads"]=[t.name for t in threading.enumerate() if "RiverBrain" in t.name]
assert not out["writer_threads"]
out["production_modules"]=[m for m in sys.modules if m.startswith(("app.core","ollama"))]
assert not out["production_modules"]
# Preserve JSON result; scratch pickles are ours, never production objects.
out["scratch"]=str(SCRATCH)
(ART/"r1_r3_results.json").write_text(json.dumps(out,indent=2,sort_keys=True))
import shutil
shutil.rmtree(SCRATCH)
print(json.dumps({"quality":out["quality"],"R1":out["R1"],"arms":{k:{"scores":v["after_load"],"selected":v["heldout"]["selected"],"correct":v["heldout"]["correct"],"n":v["heldout"]["n"],"reload":v["same_after_load"]} for k,v in arms.items()},"scratch_removed":not SCRATCH.exists()}))

