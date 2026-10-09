"""E2.1-only artifact paths. No paid model dependencies."""
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parents[1]
E2=PROJECT/'experiments/stage1_safe_suppress_e2'
P0=PROJECT/'experiments/p0_cv_only'
LABELS=('CLEAR_NORMAL','HARD_NEGATIVE_NORMAL','ANCHORED_DANGER','AMBIGUOUS')
PRIOR=['477-triage-normal-v1','477-reasoning-v1','new477-total64-v1']


def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def now(): return datetime.now(timezone.utc).isoformat()
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def write(p,x):
    p=Path(p).resolve()
    if not p.is_relative_to(ROOT.resolve()): raise PermissionError('E2.1 writes only')
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+'.tmp')
    t.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8'); os.replace(t,p)


def protected():
    paths=[]
    for folder in [E2,P0/'src',P0/'configs',PROJECT/'experiments/p1_decisions/src',
        PROJECT/'experiments/p1_decisions/configs',PROJECT/'experiments/p1_decisions/schemas',
        PROJECT/'benchmark_triage_v1/manifests',PROJECT/'benchmark_triage_v1/private_ground_truth',
        PROJECT/'experiments/triage_frozen_v1',PROJECT/'experiments/p4_gpt61_sol_vision/src']:
        paths.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.cache' not in p.parts)
    return {str(p.relative_to(PROJECT)):sha(p) for p in sorted(set(paths))}
