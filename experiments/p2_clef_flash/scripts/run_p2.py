"""P2 primary run: 1 Clef-Flash request per item, frozen P2-v1 configuration. Failed items are recorded, never faked.
This process never reads private ground truth, human grading, P0/P1 results or evaluator files (runtime audit)."""
import _bootstrap  # noqa: F401
import argparse
import statistics
import subprocess
import sys

import httpx

from access_audit import AccessAudit
from cloudflare_client import CONNECT_TIMEOUT_SEC, MAX_RETRIES, READ_TIMEOUT_SEC, CloudflareClient
from compact_state_loader import verify_p1_freeze
from cost import PRICING
from p2_pipeline import CFG, MODEL_ID, RUN_ID, P2Pipeline, raw_record
from process_log import log_event
from utils import BENCH_ROOT, EXP_ROOT, FREEZE_DIR, ITEM_IDS, LOGS_DIR, RAW_DIR, RESULTS_DIR, load_json, sha256_file, write_json


def validate_benchmark(tag):
    r = subprocess.run([sys.executable, 'scripts/validate_benchmark.py'], cwd=BENCH_ROOT, capture_output=True, text=True)
    print(f'validate_benchmark ({tag}):', 'PASS' if r.returncode == 0 else 'FAIL', r.stdout.strip())
    if r.returncode != 0:
        sys.exit(r.stderr)
    return r.stdout.strip()


def verify_p2_freeze():
    fr = load_json(FREEZE_DIR / 'p2_freeze.json')
    drift = [f for f, h in fr['hashes'].items() if sha256_file(EXP_ROOT / f) != h]
    if drift:
        sys.exit(f'Frozen P2-v1 files changed: {drift}. Create p2-v2 instead.')
    return fr


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--all', action='store_true')
    g.add_argument('--item', choices=ITEM_IDS)
    a = ap.parse_args()
    items = ITEM_IDS if a.all else [a.item]
    if (FREEZE_DIR / 'p2_results_manifest.json').exists():
        sys.exit('P2 results are already frozen (freeze/p2_results_manifest.json); refusing to overwrite')
    fr = verify_p2_freeze()
    try:
        verify_p1_freeze()
    except Exception as e:
        sys.exit(f'FAIL: {e}')
    before = validate_benchmark('before')
    log_event('run_p2_start', {'items': items})
    pipe = P2Pipeline(CloudflareClient())
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = {'run_id': RUN_ID, 'model_id': MODEL_ID, 'freeze': {'frozen_at': fr['frozen_at'], 'hashes': fr['hashes']}, 'items': {}}
    for item in items:
        with AccessAudit() as audit:
            out = pipe.run(item)
        rep = audit.report()
        if not rep['pass']:
            sys.exit(f'{item}: access audit failed {rep}')
        write_json(RAW_DIR / f'{item}.json', raw_record(out))
        if out['status'] != 'ok':
            summary['items'][item] = {'status': 'FAILED', 'errors': out['api'].get('errors'), 'retry_count': out['api']['retry_count']}
            print(f'{item}: FAILED {out["api"].get("errors")}')
            continue
        res = out['result']
        res['runtime_config']['access_audit'] = {k: rep[k] for k in ('files_opened', 'forbidden_paths_opened', 'pass')}
        write_json(RESULTS_DIR / f'run_{item}.json', res)
        rc = res['runtime_config']
        summary['items'][item] = {'status': 'ok', 'usage': rc['usage'], 'external_api_cost_usd': rc['external_api_cost_usd'],
                                  'latency': rc['latency'], 'invalid_or_missing_answer_count': rc['invalid_or_missing_answer_count'],
                                  'retry_count': rc['retry_count'], 'decision_summary': rc['decision_summary'],
                                  'model_returned': rc['decision_model_returned'], 'question_count': rc['question_count']}
        c = rc['external_api_cost_usd']
        print(f"{item}: ok, api {rc['latency']['request_total_ms']:.0f} ms, input_tokens {rc['usage']['input_tokens']}, "
              f"cost {'$%.7f' % c if c is not None else 'n/a'}, invalid answers {rc['invalid_or_missing_answer_count']}, retries {rc['retry_count']}")
    ok = [v for v in summary['items'].values() if v['status'] == 'ok']
    lat = [v['latency']['request_total_ms'] for v in ok]
    costs = [v['external_api_cost_usd'] for v in ok if v['external_api_cost_usd'] is not None]
    summary['aggregate'] = {
        'attempted_items': len(items), 'successful_items': len(ok),
        'failed_items': [k for k, v in summary['items'].items() if v['status'] != 'ok'],
        'invalid_or_missing_answer_count': sum(v['invalid_or_missing_answer_count'] for v in ok),
        'retries_total': sum(v['retry_count'] for v in summary['items'].values()),
        'request_total_ms': {'median': statistics.median(lat), 'min': min(lat), 'max': max(lat)} if lat else None,
        'theoretical_external_api_cost_usd_total': round(sum(costs), 10) if costs else None,
        'theoretical_external_api_cost_usd_mean_per_item': round(sum(costs) / len(costs), 10) if costs else None,
        'actual_billed_cost_usd': None,
        'input_tokens_total': sum(v['usage']['input_tokens'] or 0 for v in ok),
    }
    summary['benchmark_validation_before'] = before
    summary['benchmark_validation_after'] = validate_benchmark('after')
    write_json(LOGS_DIR / 'run_summary.json', summary)
    write_json(EXP_ROOT / 'runtime_config.json', {
        'pipeline_actual': CFG['pipeline_actual'], 'pipeline_schema_value': CFG['pipeline_schema_value'], 'run_id': RUN_ID,
        'model_id': MODEL_ID, 'provider': CFG['provider'], 'decision_model': CFG['decision_model'],
        'model_input_selector': CFG['model_input_selector'], 'endpoint': CFG['endpoint'], 'ai_gateway': False,
        'input_modality': CFG['input_modality'], 'compact_state_version': CFG['compact_state_version'],
        'decision_questions_version': 'decisions-v1', 'clef_questions_version': 'clef-questions-v1',
        'python': sys.version.split()[0], 'http_client': f'httpx {httpx.__version__}',
        'timeouts_sec': {'connect': CONNECT_TIMEOUT_SEC, 'read': READ_TIMEOUT_SEC}, 'max_retries': MAX_RETRIES,
        'retry_policy': CFG['retry_policy'], 'pricing': PRICING, 'freeze_file': 'freeze/p2_freeze.json', 'requests_per_item': 1,
        'latency_note': 'frozen compact state reused; decision API + adapter timings only; result latency_ms = null (not full E2E)',
        'estimated_cost_usd_note': 'null in results: local CV compute cost not measured; external_api_cost_usd (theoretical) recorded separately',
    })
    log_event('run_p2_end', summary['aggregate'])
    print('aggregate:', summary['aggregate'])


if __name__ == '__main__':
    main()
