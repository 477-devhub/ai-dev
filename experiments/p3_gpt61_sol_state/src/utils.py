"""P3 helpers: paths (allowlisted model-path inputs only), canonical JSON, hashing, API-key loading (never logged)."""
import hashlib
import json
import os
from pathlib import Path

EXP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = EXP_ROOT.parents[1]
BENCH_ROOT = PROJECT_ROOT / 'benchmark_v1'
P0_ROOT = PROJECT_ROOT / 'experiments' / 'p0_cv_only'
P1_ROOT = PROJECT_ROOT / 'experiments' / 'p1_decisions'
P2_ROOT = PROJECT_ROOT / 'experiments' / 'p2_clef_flash'
CA2_ROOT = PROJECT_ROOT / 'experiments' / 'common_adapter_v2'
RESULTS_DIR = BENCH_ROOT / 'results' / 'p3_gpt61_sol_state'
RAW_DIR = EXP_ROOT / 'raw_api'
LOGS_DIR = EXP_ROOT / 'logs'
FREEZE_DIR = EXP_ROOT / 'freeze'
EVAL_DIR = EXP_ROOT / 'evaluation'
P3_CONFIG = EXP_ROOT / 'configs' / 'p3_v1.json'
P3_PROMPT = EXP_ROOT / 'configs' / 'p3_prompt_v1.txt'
P3_SCHEMA = EXP_ROOT / 'schemas' / 'p3_decision_output.schema.json'
P1_FREEZE = P1_ROOT / 'freeze' / 'p1_freeze.json'
P1_COMPACT_DIR = P1_ROOT / 'compact_states'
P1_COMPACT_CONFIG = P1_ROOT / 'configs' / 'compact_state_v1.yaml'
P1_COMPACT_SCHEMA = P1_ROOT / 'schemas' / 'compact_decision_state.schema.json'
P1_QUESTIONS_CONFIG = P1_ROOT / 'configs' / 'decisions_questions_v1.json'
CA2_FREEZE = CA2_ROOT / 'freeze' / 'common_adapter_v2_freeze.json'
ENV_FILE = PROJECT_ROOT / 'experiments' / '.env'
ITEM_IDS = [f'ITEM_{i:02d}' for i in range(1, 8)]

# Model-path allowlist outside experiments/p3_gpt61_sol_state (read-only): frozen P1 state/config/adapter/template files,
# frozen common-adapter-v2 config/src, P0 cv-state files (result input_fingerprint only; never sent), benchmark schemas.
# No P1/P2 results or raw_api, no normalized outputs, no evaluation, no private ground truth, no human grading.
ALLOWED_INPUTS = (
    [P1_COMPACT_DIR / f'{i}.json' for i in ITEM_IDS]
    + [P1_FREEZE, P1_COMPACT_CONFIG, P1_COMPACT_SCHEMA, P1_QUESTIONS_CONFIG,
       P1_ROOT / 'src' / 'decision_adapter.py', P1_ROOT / 'src' / 'prediction_adapter.py']
    + [CA2_FREEZE, CA2_ROOT / 'config' / 'adapter_v2.json', CA2_ROOT / 'src' / 'common_adapter_v2.py']
    + [P0_ROOT / 'states' / f'{i}.json' for i in ITEM_IDS]
    + [BENCH_ROOT / 'schemas' / 'prediction.schema.json', BENCH_ROOT / 'schemas' / 'result.schema.json']
)


def allowed(path):
    p = Path(path).resolve()
    if p.is_relative_to(EXP_ROOT.resolve()) and not p.is_relative_to(EVAL_DIR.resolve()):
        return True
    return any(p == a.resolve() for a in ALLOWED_INPUTS)


def read_allowed_bytes(path):
    if not allowed(path):
        raise PermissionError(f'Input not in P3 model-path allowlist: {path}')
    return Path(path).read_bytes()


def read_allowed_json(path):
    return json.loads(read_allowed_bytes(path).decode('utf-8-sig'))


def read_allowed_text(path):
    return read_allowed_bytes(path).decode('utf-8')


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


def load_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def load_api_key_env():
    """OPENAI_API_KEY from the environment, else experiments/.env. Never printed or returned."""
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


def scan_for_secret(paths):
    key = os.environ.get('OPENAI_API_KEY', '')
    if len(key) < 8:
        return []
    hits = []
    for p in paths:
        try:
            if key in Path(p).read_text(encoding='utf-8', errors='ignore'):
                hits.append(str(p))
        except Exception:
            pass
    return hits


def redact(text):
    key = os.environ.get('OPENAI_API_KEY', '')
    return text.replace(key, '<redacted>') if len(key) >= 8 else text


def artifact_files(*roots):
    roots = roots or (EXP_ROOT,)
    return [p for r in roots for p in Path(r).rglob('*') if p.is_file() and '.venv' not in p.parts and '__pycache__' not in p.parts]
