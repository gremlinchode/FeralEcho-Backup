"""POST-HOC re-analysis of QUAL-1 with the corrected K1 auditor (audit_v2). Identical decision logic (qual.analyze is reused unchanged); ONLY the auditor is swapped.
Disclosed: audit_v2 was written after the constructor drafts existed and validated against hand adjudication (v2/qual/hand_adjudication.json, 72/72). The frozen 'primary' analysis is preserved.
usage: python -I -B qual_posthoc.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import qual, constructor, audit_v2
constructor.audit = audit_v2.audit
qual.analyze("posthoc_auditor_v2")
