#!/usr/bin/env python3
from pathlib import Path; from collections import Counter; from datetime import datetime
import hashlib, json, mimetypes, sys

R = Path.home()/"Desktop"/"FeralEcho"
O = "feral_echo_report.json"
I = O.replace(".json","_index.json")
LARGE = 100_000_000  # 100 MB
HASH_MAX = 1_000_000  # 1 MB

class A:
    def __init__(self): self.s={"f":0,"z":0,"e":Counter(),"m":Counter(),"d":Counter(),"F":[],"D":None,"B":None,"N":None}
    def run(self):
        for p in R.rglob("*"):
            if not p.is_file(): continue
            r=p.relative_to(R); z=p.stat().st_size; e=p.suffix.lower(); m,_=mimetypes.guess_type(p); d=len(r.parts)-1
            h="big" if z>=HASH_MAX else hashlib.md5(p.read_bytes()).hexdigest()
            self.s["F"].append({"p":str(r),"z":z,"h":h,"e":e,"d":d})
            self.s["f"]+=1; self.s["z"]+=z; self.s["e"][e]+=1; self.s["m"][m or"unk"]+=1; self.s["d"][d]+=1
        self._p()
        return self._r()
    def _p(self):
        # Duplicates
        M={}; [M.setdefault(f["h"],[]).append(f) for f in self.s["F"] if f["h"] != "big"]
        D={k:v for k,v in M.items() if len(v)>1}
        if D: self.s["D"]={"t":"dup","c":sum(len(v)for v in D.values()),"g":round(sum(f["z"]for v in D.values()for f in v[1:])/1e9,3)}
        # Large files
        B=[f for f in self.s["F"] if f["z"] > LARGE]
        if B: self.s["B"]={"t":"big","c":len(B),"g":round(sum(f["z"]for f in B)/1e9,3)}
        # Depth
        if (md:=max(self.s["d"].keys(),default=0)) > 8: self.s["N"]={"t":"deep","m":md}
    def _r(self):
        rep={"time":datetime.now().isoformat(),"root":str(R),"sum":{"f":self.s["f"],"gb":round(self.s["z"]/1e9,3),"ext":dict(self.s["e"].most_common(5)),"dep":dict(self.s["d"])},"ins":[v for v in (self.s["D"],self.s["B"],self.s["N"]) if v]}
        json.dump([{"p":f["p"],"z":f["z"],"h":f["h"]} for f in self.s["F"]], open(I,"w"), separators=(",",":"))
        json.dump(rep, open(O,"w"), separators=(",",":"))
        s=rep["sum"]
        print(f"R:{O} I:{I} F:{s['f']} Z:{s['gb']:.1f}GB", end="")
        for i in rep["ins"]:
            if i["t"]=="dup": print(f" D:{i['c']}→{i['g']}GB", end="")
            if i["t"]=="big": print(f" B:{i['c']}→{i['g']}GB", end="")
            if i["t"]=="deep": print(f" DEP:{i['m']}", end="")
        print()
        return rep

if __name__=="__main__":
    r=A().run()
    if "--dance" in sys.argv: print("The town is red. The night is ours.")
