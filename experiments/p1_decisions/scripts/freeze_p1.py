"""Freeze compact-decision-state-v1 + decisions-v1 after the P0.5 integration PASS. Writes freeze/p1_freeze.json."""
import _bootstrap  # noqa: F401
import datetime
import sys

from utils import COMPACT_DIR, EXP_ROOT, FREEZE_DIR, LOGS_DIR, load_json, sha256_file, write_json

FROZEN = ['schemas/compact_decision_state.schema.json', 'configs/compact_state_v1.yaml', 'configs/decisions_questions_v1.json',
          'src/compact_serializer.py', 'src/decision_adapter.py',
          # additional files whose behaviour defines P1-v1 outputs
          'src/prediction_adapter.py', 'src/decisions_client.py', 'src/p1_pipeline.py', 'src/cost.py', 'src/state_loader.py', 'src/utils.py']


def main():
    smoke = load_json(LOGS_DIR / 'p0_5_smoke.json')
    if not smoke.get('passed'):
        sys.exit('P0.5 smoke test has not passed; refusing to freeze')
    out = FREEZE_DIR / 'p1_freeze.json'
    if out.exists():
        sys.exit('freeze/p1_freeze.json already exists; P1-v1 is frozen (create p1-v2 for changes)')
    rec = {
        'state_version': 'compact-decision-state-v1',
        'decision_questions_version': 'decisions-v1',
        'model': 'gpt-6-luna',
        'endpoint': '/v1/decisions',
        'frozen': True,
        'frozen_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        'hashes': {f: sha256_file(EXP_ROOT / f) for f in FROZEN},
        'compact_state_sha256': {k: v['compact_sha256'] for k, v in load_json(COMPACT_DIR / 'manifest.json')['items'].items()},
        'p0_5_smoke': {'passed': True, 'item': smoke['item_id'], 'model_returned': smoke['model_returned'], 'usage': smoke['usage']},
        'semantic_changes_after_smoke_result': [],
        'integration_fixes_during_p0_5': [
            'scripts/smoke_test_decisions.py: benchmark validator subprocess used bare "python" (resolved to an interpreter without jsonschema); switched to sys.executable. Harness only; no serializer/question/adapter change. First attempt preserved as raw_api/p0_5_ITEM_01_attempt1_harness_validator_bug.json.'],
        'note': 'Smoke-test answers were stored but their content was not inspected or used for any change before this freeze.',
    }
    write_json(out, rec)
    print('FROZEN', out)
    for f, h in rec['hashes'].items():
        print(f'  {h}  {f}')


if __name__ == '__main__':
    main()
