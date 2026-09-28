"""Read-only archived-output counterexample; no model calls or production imports."""
import ast, hashlib, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
ART=pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode=True
def audit(event,args):
    if event.startswith(("socket.","subprocess.")) or event in ("os.system","os.exec","os.fork","os.posix_spawn","os.kill","os.killpg"):
        raise RuntimeError(event)
    if event=="open":
        p,mode,flags=args
        if isinstance(p,str) and isinstance(mode,str) and any(c in mode for c in "wax+"):
            if not pathlib.Path(p).resolve().is_relative_to(ART):raise RuntimeError(p)
sys.addaudithook(audit)
source=ROOT/"audits/tier5_retest/tier5_retest_results.jsonl"
pool=ROOT/"audits/tier5_retest/tier5_retest_task_pool_FROZEN.py"
rows=[json.loads(x) for x in source.read_text().splitlines()]
tasknode=next(n.value for n in ast.parse(pool.read_text()).body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=="_t" and ast.literal_eval(n.value.args[0])=="r-bf02")
task=[ast.literal_eval(a) for a in tasknode.args]
allowed=(ast.Module,ast.FunctionDef,ast.arguments,ast.arg,ast.If,ast.Compare,ast.Name,ast.Load,ast.LtE,ast.Constant,ast.Return,ast.While,ast.Gt,ast.BinOp,ast.Mod,ast.NotEq,ast.Assign,ast.Store,ast.Call,ast.Div)
out={"task_id":task[0],"prompt":task[2],"original_tests":task[3],"archive_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"task_pool_sha256":hashlib.sha256(pool.read_bytes()).hexdigest(),"rows":[]}
for r in rows:
    if r["task_id"]!="r-bf02":continue
    code=r["candidate_code"];node=ast.parse(code)
    assert len(node.body)==1 and isinstance(node.body[0],ast.FunctionDef)
    assert node.body[0].name=="is_power_of_two"
    assert all(isinstance(n,allowed) for n in ast.walk(node))
    assert all(isinstance(n.func,ast.Name) and n.func.id=="int" for n in ast.walk(node) if isinstance(n,ast.Call))
    ns={"__builtins__":{"int":int}}
    exec(compile(node,"<inspected-archived-pure-function>","exec"),ns)
    checks=[]
    for stratum,inputs in (("original",[1,2,3,64,0,-4,6]),("new_valid_inputs",[2**60,2**60+2,2**62+2,2**62+6,-2**60])):
        for n in inputs:
            expected=n>0 and (n&(n-1))==0
            actual=ns["is_power_of_two"](n)
            checks.append({"stratum":stratum,"input":n,"expected":expected,"actual":actual,"correct":actual==expected})
    out["rows"].append({"recorded_condition":r["condition"],"trace_id":r["trace_id"],"recorded_passed":r["passed"],"candidate_code":code,"checks":checks})
(ART/"r9_archived_outputs.json").write_text(json.dumps(out,indent=2))
print(json.dumps({r["recorded_condition"]:{s:{"correct":sum(c["correct"] for c in r["checks"] if c["stratum"]==s),"n":sum(c["stratum"]==s for c in r["checks"])} for s in ("original","new_valid_inputs")} for r in out["rows"]}))

