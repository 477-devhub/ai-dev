"""Shared helpers for the P0 CV-only experiment (paths, hashing, JSON, config)."""
import hashlib
import json
import math
import os
from pathlib import Path

import yaml

EXP_ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = Path(os.environ.get('P477_BENCHMARK_ROOT', EXP_ROOT.parents[1] / 'benchmark_v1')).resolve()
RESULTS_DIR = BENCH_ROOT / 'results' / 'p0_cv_only'
STATES_DIR = EXP_ROOT / 'states'
DEBUG_DIR = EXP_ROOT / 'debug'
LOGS_DIR = EXP_ROOT / 'logs'
CACHE_DIR = EXP_ROOT / 'states' / '_camera_cache'
CV_CONFIG_PATH = EXP_ROOT / 'configs' / 'cv_state_v1.yaml'
RULE_CONFIG_PATH = EXP_ROOT / 'configs' / 'p0_v1.yaml'
STATE_SCHEMA_PATH = EXP_ROOT / 'schemas' / 'canonical_cv_state.schema.json'

ITEM_IDS = [f'ITEM_{i:02d}' for i in range(1, 8)]


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def sha256_json(value):
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def rnd(value, digits=4):
    """Round floats for stable, compact JSON. None/NaN/inf become None."""
    if value is None:
        return None
    value = float(value)
    if math.isnan(value) or math.isinf(value):
        return None
    return round(value, digits)


def clip01(value):
    return max(0.0, min(1.0, float(value)))


def reliability_label(value, cfg):
    if value is None:
        return 'unknown'
    if value >= cfg['high']:
        return 'high'
    if value >= cfg['medium']:
        return 'medium'
    return 'low'
