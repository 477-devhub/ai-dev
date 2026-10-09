"""Freeze P3-v1 after the synthetic smoke PASS and before any benchmark request. Writes freeze/p3_freeze.json (no overwrite)."""
import _bootstrap  # noqa: F401
import datetime
import sys

from common_adapter_bridge import load_common_adapter_v2
from process_log import log_event
from state_loader import verify_p1_freeze
from utils import EXP_ROOT, FREEZE_DIR, LOGS_DIR, RAW_DIR, RESULTS_DIR, load_json, sha256_file, write_json

FROZEN = ['configs/p3_v1.json', 'configs/p3_prompt_v1.txt', 'schemas/p3_decision_output.schema.json',
          'src/prompt_builder.py', 'src/raw_decision_adapter.py', 'src/prediction_adapter.py',
          # additional files whose behaviour defines P3-v1 outputs
          'src/openai_client.py', 'src/p3_pipeline.py', 'src/common_adapter_bridge.py', 'src/state_loader.py',
          'src/cost.py', 'src/utils.py', 'src/access_audit.py']


def main():
    smoke = load_json(LOGS_DIR / 'smoke_test.json')
    if not smoke.get('passed') or smoke.get('benchmark_items_used'):
        sys.exit('synthetic smoke test has not passed; refusing to freeze')
    out = FREEZE_DIR / 'p3_freeze.json'
    if out.exists():
        sys.exit('freeze/p3_freeze.json already exists; P3-v1 is frozen (create p3-v2 for changes)')
    if list(RAW_DIR.glob('ITEM_*.json')) or (RESULTS_DIR.exists() and list(RESULTS_DIR.glob('run_*.json'))):
        sys.exit('benchmark outputs already exist; freeze must precede them')
    p1 = verify_p1_freeze()
    _, ca2 = load_common_adapter_v2()
    rec = {
        'p3_version': 'p3-v1', 'model': 'gpt-6.1-sol', 'endpoint': '/v1/responses', 'reasoning_effort': 'high', 'tools': [],
        'structured_outputs': 'json_schema strict', 'compact_state_version': 'compact-decision-state-v1',
        'frozen': True, 'frozen_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        'hashes': {f: sha256_file(EXP_ROOT / f) for f in FROZEN},
        'p1_freeze_verified': {'p1_frozen_at': p1['frozen_at'], 'compact_state_sha256': p1['compact_state_sha256']},
        'common_adapter_v2_freeze': ca2,
        'smoke_test': {'passed': True, 'at': smoke['at'], 'benchmark_items_used': []},
        'benchmark_responses_seen_before_freeze': False,
        'semantic_changes_after_benchmark_output': [],
        'pre_freeze_integration_fixes': ['src/common_adapter_bridge.py: set module __file__ before exec (NameError in offline test); no semantic change'],
        'note': 'Frozen before any benchmark item was sent to gpt-6.1-sol. Prompt/schema/threshold/state changes after benchmark output must be p3-v2.',
    }
    write_json(out, rec)
    log_event('p3_frozen', {'file': 'freeze/p3_freeze.json'})
    print('FROZEN', out)
    for f, h in rec['hashes'].items():
        print(f'  {h}  {f}')


if __name__ == '__main__':
    main()
