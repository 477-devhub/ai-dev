"""Separate team-input experiment; never writes either original benchmark."""
import datetime, hashlib, json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT/'experiments/team_frozen_v1'
SOURCE = Path('D:/projects/477_team_benchmark_v1')
PUBLIC = RUN/'public'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''): h.update(b)
    return h.hexdigest()
def now(): return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
def write(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)
    key=os.environ.get('OPENAI_API_KEY')
    if key: text=text.replace(key,'<redacted>')
    t=p.with_suffix(p.suffix+'.tmp'); t.write_text(text+'\n',encoding='utf-8'); t.replace(p)
def verify():
    lock=read(RUN/'RUN_LOCK.json')
    for relative,h in lock['sha256'].items():
        if digest(ROOT/relative)!=h: raise RuntimeError('Frozen drift: '+relative)
    for name,filename in [('p1_decisions','p1_freeze.json'),('p4_gpt61_sol_vision','p4_freeze.json'),('common_adapter_v2','common_adapter_v2_freeze.json')]:
        base=ROOT/'experiments'/name; frozen=read(base/'freeze'/filename)
        assert frozen['frozen']
        for p,h in frozen['hashes'].items():
            if digest(base/p)!=h: raise RuntimeError('Model dependency drift: '+name+'/'+p)
def boundary():
    forbidden=[RUN/'analysis',ROOT/'benchmark_triage_v1/private_ground_truth',ROOT/'benchmark_triage_v1/review',ROOT/'benchmark_v1/private_ground_truth',Path('D:/projects/477_evaluator_reference_v1.zip'),SOURCE/'ground_truth']
    def hook(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(args[0])).resolve()
            if any(p==f.resolve() or p.is_relative_to(f.resolve()) for f in forbidden): raise PermissionError('Evaluator data forbidden to inference workers')
    sys.addaudithook(hook)
def jobs(): return read(RUN/'run_plan.json')['jobs']
def job(identifier): return next(j for j in jobs() if j['id']==identifier)
def schema_for(count):
    s=read(ROOT/'experiments/p0_cv_only/schemas/canonical_cv_state.schema.json')
    # Transport-only validation: preserve true supplied count, never pad or fabricate 64 frames.
    s['properties']['input']['properties']['total_frames']={'const':count}
    return s
