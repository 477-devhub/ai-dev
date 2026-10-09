"""Freeze P2-v1 after the synthetic smoke PASS and before any benchmark request. Writes freeze/p2_freeze.json.
Refuses to overwrite an existing freeze (changes after benchmark output must become p2-v2)."""
import _bootstrap  # noqa: F401
import datetime
import sys

from compact_state_loader import verify_p1_freeze
from utils import EXP_ROOT, FREEZE_DIR, LOGS_DIR, RAW_DIR, RESULTS_DIR, load_json, sha256_file, write_json

FROZEN = ['configs/clef_questions_v1.json', 'configs/p2_v1.json',
          'src/question_adapter.py', 'src/clef_adapter.py', 'src/prediction_adapter.py', 'src/cloudflare_client.py',
          # additional files whose behaviour defines P2-v1 outputs
          'src/p2_pipeline.py', 'src/compact_state_loader.py', 'src/cost.py', 'src/utils.py', 'src/access_audit.py',
          'schemas/clef_response.schema.json']


def main():
    smoke = load_json(LOGS_DIR / 'smoke_test.json')
    if not smoke.get('passed') or smoke.get('benchmark_items_used'):
        sys.exit('synthetic smoke test has not passed (or used benchmark items); refusing to freeze')
    out = FREEZE_DIR / 'p2_freeze.json'
    if out.exists():
        sys.exit('freeze/p2_freeze.json already exists; P2-v1 is frozen (create p2-v2 for changes)')
    bench_raw = [p.name for p in RAW_DIR.glob('ITEM_*.json')]
    bench_res = list(RESULTS_DIR.glob('run_*.json')) if RESULTS_DIR.exists() else []
    if bench_raw or bench_res:
        sys.exit(f'benchmark outputs already exist ({bench_raw}, {len(bench_res)} results); freeze must precede them')
    p1 = verify_p1_freeze()
    rec = {
        'p2_version': 'p2-v1', 'model': '@cf/cloudflare/clef-flash', 'provider': 'cloudflare_workers_ai',
        'compact_state_version': 'compact-decision-state-v1', 'decision_questions_version': 'decisions-v1',
        'frozen': True, 'frozen_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        'hashes': {f: sha256_file(EXP_ROOT / f) for f in FROZEN},
        'p1_freeze_verified': {'p1_frozen_at': p1['frozen_at'], 'p1_hashes_checked': len(p1['hashes']),
                               'compact_state_sha256': p1['compact_state_sha256']},
        'schema_snapshot_sha256': sha256_file(LOGS_DIR / 'cloudflare_schema_snapshot_raw.json'),
        'smoke_test': {'passed': True, 'at': smoke['at'], 'state': 'synthetic-smoke-v1', 'usage': smoke['usage'],
                       'benchmark_items_used': []},
        'benchmark_responses_seen_before_freeze': False,
        'semantic_changes_after_benchmark_output': [],
        'note': 'Frozen before any benchmark item was sent to Clef-Flash. Any later change to questions, choices, levels, '
                'adapter thresholds, confidence formula, state or category reconciliation must be released as p2-v2.',
    }
    write_json(out, rec)
    print('FROZEN', out)
    for f, h in rec['hashes'].items():
        print(f'  {h}  {f}')


if __name__ == '__main__':
    main()
