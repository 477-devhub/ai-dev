"""P1 helpers: paths (allowlisted inputs only), canonical JSON, hashing, .env loading (never logs the key)."""
import hashlib
import json
import math
import os
from pathlib import Path

import yaml

EXP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = EXP_ROOT.parents[1]
BENCH_ROOT = PROJECT_ROOT / 'benchmark_v1'
P0_ROOT = PROJECT_ROOT / 'experiments' / 'p0_cv_only'
RESULTS_DIR = BENCH_ROOT / 'results' / 'p1_decisions'
COMPACT_DIR = EXP_ROOT / 'compact_states'
RAW_DIR = EXP_ROOT / 'raw_api'
LOGS_DIR = EXP_ROOT / 'logs'
FREEZE_DIR = EXP_ROOT / 'freeze'
COMPACT_CONFIG = EXP_ROOT / 'configs' / 'compact_state_v1.yaml'
QUESTIONS_CONFIG = EXP_ROOT / 'configs' / 'decisions_questions_v1.json'
COMPACT_SCHEMA = EXP_ROOT / 'schemas' / 'compact_decision_state.schema.json'
ENV_FILE = PROJECT_ROOT / 'experiments' / '.env'
ITEM_IDS = [f'ITEM_{i:02d}' for i in range(1, 8)]

# Allowlisted external inputs (section 1 of the P1 spec). Anything else outside experiments/p1_decisions is off-limits.
ALLOWED_INPUTS = (
    [P0_ROOT / 'states' / f'{i}.json' for i in ITEM_IDS]
    + [P0_ROOT / 'schemas' / 'canonical_cv_state.schema.json', P0_ROOT / 'configs' / 'cv_state_v1.yaml',
       BENCH_ROOT / 'public_manifest.json', BENCH_ROOT / 'model_input' / 'scenarios.json',
       BENCH_ROOT / 'model_input' / 'prompt_v1.txt', BENCH_ROOT / 'schemas' / 'prediction.schema.json',
       BENCH_ROOT / 'schemas' / 'result.schema.json']
)


def allowed(path):
    p = Path(path).resolve()
    if p.is_relative_to(EXP_ROOT.resolve()):
        return True
    return any(p == a.resolve() for a in ALLOWED_INPUTS)


def read_allowed_json(path):
    if not allowed(path):
        raise PermissionError(f'Input not in P1 allowlist: {path}')
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def norm_float(x, digits):
    if x is None:
        return None
    x = float(x)
    if math.isnan(x) or math.isinf(x):
        return None
    r = round(x, digits)
    return 0.0 if r == 0 else r          # no negative zero


def canonical_json(value):
    """UTF-8, sorted keys, compact separators, no NaN/inf. Floats are pre-rounded by the serializer."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    return sha256_bytes(Path(p).read_bytes())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def load_yaml(p):
    return yaml.safe_load(Path(p).read_text(encoding='utf-8'))


def load_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def load_api_key_env():
    """Load OPENAI_API_KEY from experiments/.env into os.environ without printing or returning it."""
    if os.environ.get('OPENAI_API_KEY'):
        return True
    if not ENV_FILE.is_file():
        return False
    for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line.startswith('OPENAI_API_KEY') and '=' in line:
            val = line.split('=', 1)[1].strip().strip('"').strip("'")
            if val:
                os.environ['OPENAI_API_KEY'] = val
                return True
    return False


def count_tokens(text):
    """Local estimate with tiktoken o200k_base; the API usage.input_tokens is authoritative."""
    try:
        import tiktoken
        return len(tiktoken.get_encoding('o200k_base').encode(text))
    except Exception:
        return None
