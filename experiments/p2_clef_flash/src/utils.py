"""P2 helpers: paths (allowlisted inputs only), canonical JSON, hashing, credential loading (values never logged)."""
import hashlib
import json
import math
import os
from pathlib import Path

import yaml

EXP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = EXP_ROOT.parents[1]
BENCH_ROOT = PROJECT_ROOT / 'benchmark_v1'
P1_ROOT = PROJECT_ROOT / 'experiments' / 'p1_decisions'
P0_ROOT = PROJECT_ROOT / 'experiments' / 'p0_cv_only'
RESULTS_DIR = BENCH_ROOT / 'results' / 'p2_clef_flash'
RAW_DIR = EXP_ROOT / 'raw_api'
LOGS_DIR = EXP_ROOT / 'logs'
FREEZE_DIR = EXP_ROOT / 'freeze'
EVAL_DIR = EXP_ROOT / 'evaluation'
P2_CONFIG = EXP_ROOT / 'configs' / 'p2_v1.json'
CLEF_QUESTIONS_CONFIG = EXP_ROOT / 'configs' / 'clef_questions_v1.json'
CLEF_RESPONSE_SCHEMA = EXP_ROOT / 'schemas' / 'clef_response.schema.json'
P1_FREEZE = P1_ROOT / 'freeze' / 'p1_freeze.json'
P1_COMPACT_DIR = P1_ROOT / 'compact_states'
P1_COMPACT_CONFIG = P1_ROOT / 'configs' / 'compact_state_v1.yaml'
P1_COMPACT_SCHEMA = P1_ROOT / 'schemas' / 'compact_decision_state.schema.json'
P1_QUESTIONS_CONFIG = P1_ROOT / 'configs' / 'decisions_questions_v1.json'
ENV_FILE = PROJECT_ROOT / 'experiments' / '.env'
ITEM_IDS = [f'ITEM_{i:02d}' for i in range(1, 8)]
CRED_VARS = ('CLOUDFLARE_ACCOUNT_ID', 'CLOUDFLARE_API_TOKEN')

# Allowlisted inputs outside experiments/p2_clef_flash for the MODEL path. P1 frozen state/config files only (read-only);
# P0 cv-state files only for the result input_fingerprint; no P1 results/raw_api, no P0 results, no private ground truth, no human grading.
ALLOWED_INPUTS = (
    [P1_COMPACT_DIR / f'{i}.json' for i in ITEM_IDS]
    + [P1_FREEZE, P1_COMPACT_CONFIG, P1_COMPACT_SCHEMA, P1_QUESTIONS_CONFIG,
       P1_ROOT / 'src' / 'compact_serializer.py']
    + [P0_ROOT / 'states' / f'{i}.json' for i in ITEM_IDS]   # input_fingerprint field only (harness metadata)
    + [BENCH_ROOT / 'schemas' / 'prediction.schema.json', BENCH_ROOT / 'schemas' / 'result.schema.json']
)


def allowed(path):
    p = Path(path).resolve()
    if p.is_relative_to(EXP_ROOT.resolve()) and not p.is_relative_to(EVAL_DIR.resolve()):
        return True
    return any(p == a.resolve() for a in ALLOWED_INPUTS)


def read_allowed_bytes(path):
    if not allowed(path):
        raise PermissionError(f'Input not in P2 model-path allowlist: {path}')
    return Path(path).read_bytes()


def read_allowed_json(path):
    return json.loads(read_allowed_bytes(path).decode('utf-8-sig'))


def norm_float(x, digits):
    if x is None:
        return None
    x = float(x)
    if math.isnan(x) or math.isinf(x):
        return None
    r = round(x, digits)
    return 0.0 if r == 0 else r


def canonical_json(value):
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


def load_cloudflare_env():
    """Load CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN from the environment, else experiments/.env.
    Values are placed in os.environ only; never printed, returned or written."""
    missing = [v for v in CRED_VARS if not os.environ.get(v)]
    if missing and ENV_FILE.is_file():
        for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if '=' not in line or line.startswith('#'):
                continue
            k, val = line.split('=', 1)
            k = k.strip().removeprefix('export ').strip()
            if k in missing:
                val = val.strip().strip('"').strip("'")
                if val:
                    os.environ[k] = val
    return all(os.environ.get(v) for v in CRED_VARS)


def secret_values():
    return [os.environ[v] for v in CRED_VARS if len(os.environ.get(v, '')) >= 8]


def scan_for_secrets(paths):
    """Paths containing any credential value. True/False scan only; values never printed."""
    secrets = secret_values()
    hits = []
    for p in paths:
        try:
            t = Path(p).read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        if any(s in t for s in secrets):
            hits.append(str(p))
    return hits


def redact(text):
    for s in secret_values():
        text = text.replace(s, '<redacted>')
    return text


def artifact_files(*roots):
    roots = roots or (EXP_ROOT,)
    return [p for r in roots for p in Path(r).rglob('*') if p.is_file() and '.venv' not in p.parts and '__pycache__' not in p.parts]
