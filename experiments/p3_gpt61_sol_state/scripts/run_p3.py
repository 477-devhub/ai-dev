"""P3 primary run: 1 Responses request per item, frozen P3-v1 configuration. Failed items are recorded, never faked.
This process never reads private ground truth, human grading, P1/P2 results/raw outputs or evaluation files (runtime audit)."""
import _bootstrap  # noqa: F401
import argparse
import statistics
import subprocess
import sys

import httpx2
import openai

from access_audit import AccessAudit
from cost import PRICING
from openai_client import CONNECT_TIMEOUT_SEC, MAX_OUTPUT_TOKENS, MAX_RETRIES, READ_TIMEOUT_SEC, ResponsesClient
from p3_pipeline import CFG, MODEL_ID, RUN_ID, P3Pipeline, raw_record
from process_log import log_event
from state_loader import verify_p1_freeze
from utils import BENCH_ROOT, EXP_ROOT, FREEZE_DIR, ITEM_IDS, LOGS_DIR, RAW_DIR, RESULTS_DIR, load_json, sha256_file, write_json


def validate_benchmark(tag):
    r = subprocess.run([sys.executable, 'scripts/validate_benchmark.py'], cwd=BENCH_ROOT, capture_output=True, text=True)
    print(f'validate_benchmark ({tag}):', 'PASS' if r.returncode == 0 else 'FAIL', r.stdout.strip())
    if r.returncode != 0:
        sys.exit(r.stderr)
    log_event(f'validate_benchmark_{tag}', {'result': 'PASS'})
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--all', action='store_true')
    g.add_argument('--item', choices=ITEM_IDS)
    a = ap.parse_args()
    items = ITEM_IDS if a.all else [a.item]
    if (FREEZE_DIR / 'p3_results_manifest.json').exists():
        sys.exit('P3 results already frozen; refusing to overwrite')
    fr = load_json(FREEZE_DIR / 'p3_freeze.json')
    drift = [f for f, h in fr['hashes'].items() if sha256_file(EXP_ROOT / f) != h]
    if drift:
        sys.exit(f'Frozen P3-v1 files changed: {drift}. Create p3-v2 instead.')
    verify_p1_freeze()
    before = validate_benchmark('before_p3_run')
    log_event('run_p3_start', {'items': items})
    pipe = P3Pipeline(ResponsesClient())
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
            summary['items'][item] = {'status': 'FAILED', 'response_status': out['api'].get('status'), 'errors': out['api'].get('errors'),
                                      'incomplete_details': out['api'].get('incomplete_details'), 'retry_count': out['api']['retry_count']}
            print(f"{item}: FAILED ({out['api'].get('status')}) {out['api'].get('errors') or out['api'].get('incomplete_details') or out['api'].get('adapter_error')}")
            continue
        res = out['result']
        res['runtime_config']['access_audit'] = rep
        write_json(RESULTS_DIR / f'run_{item}.json', res)
        rc = res['runtime_config']
        summary['items'][item] = {'status': 'ok', 'response_status': rc['response_status'], 'usage': rc['usage'],
                                  'external_api_cost_usd': rc['external_api_cost_usd'], 'latency': rc['latency'],
                                  'refusal_count': rc['refusal_count'], 'retry_count': rc['retry_count'],
                                  'decision_summary': rc['decision_summary'], 'model_returned': rc['decision_model_returned']}
        u = rc['usage']
        print(f"{item}: {rc['response_status']}, api {rc['latency']['request_total_ms']:.0f} ms, in {u['input_tokens']} (cached {u['cached_input_tokens']}), "
              f"out {u['output_tokens']} (reasoning {u['reasoning_tokens']}), cost ${rc['external_api_cost_usd']:.6f}, retries {rc['retry_count']}")
    ok = [v for v in summary['items'].values() if v['status'] == 'ok']
    lat = [v['latency']['request_total_ms'] for v in ok]
    costs = [v['external_api_cost_usd'] for v in ok if v['external_api_cost_usd'] is not None]
    summary['aggregate'] = {
        'attempted_items': len(items), 'successful_items': len(ok),
        'failed_items': [k for k, v in summary['items'].items() if v['status'] != 'ok'],
        'refusals': sum(v['refusal_count'] for v in ok),
        'retries_total': sum(v['retry_count'] for v in summary['items'].values()),
        'request_total_ms': {'median': statistics.median(lat), 'min': min(lat), 'max': max(lat)} if lat else None,
        'external_api_cost_usd_total': round(sum(costs), 10) if costs else None,
        'external_api_cost_usd_mean_per_item': round(sum(costs) / len(costs), 10) if costs else None,
        'tokens_total': {k: sum((v['usage'][k] or 0) for v in ok) for k in ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_tokens')},
    }
    summary['benchmark_validation_before'] = before
    summary['benchmark_validation_after'] = validate_benchmark('after_p3_run')
    write_json(LOGS_DIR / 'run_summary.json', summary)
    write_json(EXP_ROOT / 'runtime_config.json', {
        'pipeline_actual': CFG['pipeline_actual'], 'pipeline_schema_value': CFG['pipeline_schema_value'], 'run_id': RUN_ID, 'model_id': MODEL_ID,
        'provider': 'openai', 'decision_model': 'gpt-6.1-sol', 'endpoint': '/v1/responses', 'reasoning_effort': 'high', 'tools': [],
        'structured_outputs': 'json_schema strict', 'input_modality': CFG['input_modality'], 'compact_state_version': CFG['compact_state_version'],
        'probability_source': CFG['probability_source'], 'python': sys.version.split()[0], 'openai_sdk': openai.__version__,
        'http_client': f'httpx2 {httpx2.__version__}', 'timeouts_sec': {'connect': CONNECT_TIMEOUT_SEC, 'read': READ_TIMEOUT_SEC},
        'max_output_tokens': MAX_OUTPUT_TOKENS, 'max_retries': MAX_RETRIES, 'retry_policy': CFG['retry_policy'], 'failure_policy': CFG['failure_policy'],
        'pricing': PRICING, 'freeze_file': 'freeze/p3_freeze.json', 'common_adapter': 'common-adapter-v2 (frozen)', 'requests_per_item': 1,
        'latency_note': 'state -> GPT API -> adapter (cached frozen state); not full E2E; single primary call, not a controlled repeated benchmark',
        'estimated_cost_usd_note': 'null in results: local CV compute cost not measured; external_api_cost_usd recorded separately'})
    log_event('run_p3_end', summary['aggregate'])
    print('aggregate:', summary['aggregate'])


if __name__ == '__main__':
    main()
