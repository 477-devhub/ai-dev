"""New dataset harness only. Existing frozen experiment bytes are never modified."""
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BENCH = ROOT / 'benchmark_triage_v1'
RUN = ROOT / 'experiments/triage_frozen_v1'
PLAN = RUN / 'run_plan.json'
LOCK = RUN / 'HARNESS_LOCK.json'

def now():
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat(timespec='seconds')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def scrub(value):
    key = os.environ.get('OPENAI_API_KEY', '')
    if isinstance(value, str):
        return value.replace(key, '<redacted>') if key else value
    if isinstance(value, dict):
        return {k:scrub(v) for k,v in value.items()}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(scrub(value), ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    temp.replace(path)

def verify_frozen():
    if not (BENCH/'BENCHMARK_LOCK.json').is_file():
        raise RuntimeError('Benchmark must be frozen before inference')
    record = read(LOCK)
    drift = [p for p,h in record['sha256'].items() if digest(ROOT/p) != h]
    if drift:
        raise RuntimeError(f'Frozen harness/dependency drift: {drift}')
    for name, filename in [('p1_decisions','p1_freeze.json'),('p4_gpt61_sol_vision','p4_freeze.json'),
                           ('common_adapter_v2','common_adapter_v2_freeze.json')]:
        root = ROOT/'experiments'/name
        freeze = read(root/'freeze'/filename)
        if not freeze.get('frozen'):
            raise RuntimeError(f'{name} is not frozen')
        drift = [p for p,h in freeze['hashes'].items() if digest(root/p) != h]
        if drift:
            raise RuntimeError(f'{name} drift: {drift}')

def stage_ids(stage):
    plan = read(PLAN)
    if stage == 'test' and not (RUN/'routing_policy_lock.json').is_file():
        raise RuntimeError('Test inference requires a calibration-selected routing policy lock')
    if stage == 'test' and digest(RUN/'routing_policy_lock.json') != read(RUN/'ROUTING_POLICY_SHA256.json')['sha256']:
        raise RuntimeError('Routing policy was changed after calibration lock')
    return plan[stage+'_ids']

def install_model_boundary():
    """Fail closed if a CV/model worker attempts to read private GT or review data."""
    forbidden = [BENCH/'private_ground_truth', BENCH/'review', BENCH/'reports',
                 ROOT/'benchmark_v1/private_ground_truth', RUN/'analysis']
    def audit(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            if any(path == p.resolve() or path.is_relative_to(p.resolve()) for p in forbidden):
                raise PermissionError('Private/evaluator data is forbidden in model workers')
    sys.addaudithook(audit)
