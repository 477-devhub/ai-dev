"""E2-local paths and atomic artifacts. Existing experiment files are read only."""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
P1 = PROJECT / 'experiments/p1_decisions'
sys.path.insert(0, str(P1 / 'src'))


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(obj):
    return hashlib.sha256(canonical(obj).encode('utf-8')).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, obj):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise PermissionError('E2 writes must stay in E2 directory')
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    os.replace(tmp, path)


def protected_hashes():
    paths = [P1/'src/compact_serializer.py', P1/'src/compact_serializer_v2.py',
        P1/'src/compact_versions.py', P1/'src/p1_pipeline.py', P1/'src/decision_adapter.py',
        P1/'src/decisions_client.py', P1/'configs/decisions_questions_v1.json',
        P1/'configs/compact_state_v1.yaml', P1/'schemas/compact_decision_state.schema.json',
        P1/'schemas/compact_decision_state_v2.schema.json']
    for folder in ['benchmark_triage_v1/manifests', 'benchmark_triage_v1/private_ground_truth',
                   'experiments/triage_frozen_v1', 'experiments/p1_decisions/freeze',
                   'experiments/p4_gpt61_sol_vision/src', 'experiments/p4_gpt61_sol_vision/configs']:
        paths += [p for p in (PROJECT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    # Bytes only, never parse GT or Frozen result contents.
    return {str(p.relative_to(PROJECT)):file_hash(p) for p in sorted(set(paths))}
