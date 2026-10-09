"""P1 primary run: 1 Decisions API request per item, frozen P1-v1 configuration. Failed items are recorded, never faked."""
import _bootstrap  # noqa: F401
import argparse
import statistics
import subprocess
import sys

import httpx2
import openai

from access_audit import AccessAudit
from cost import PRICING
from decisions_client import CONNECT_TIMEOUT_SEC, MAX_RETRIES, READ_TIMEOUT_SEC, DecisionsClient
from p1_pipeline import MODEL_ID, RUN_ID, P1Pipeline, raw_record
from utils import BENCH_ROOT, EXP_ROOT, FREEZE_DIR, ITEM_IDS, LOGS_DIR, RAW_DIR, RESULTS_DIR, load_json, sha256_file, write_json


def validate_benchmark(tag):
    r = subprocess.run([sys.executable, 'scripts/validate_benchmark.py'], cwd=BENCH_ROOT, capture_output=True, text=True)
    print(f'validate_benchmark ({tag}):', 'PASS' if r.returncode == 0 else 'FAIL', r.stdout.strip())
    if r.returncode != 0:
        sys.exit(r.stderr)
    return r.stdout.strip()


def verify_freeze():
    fr = load_json(FREEZE_DIR / 'p1_freeze.json')
    drift = [f for f, h in fr['hashes'].items() if sha256_file(EXP_ROOT / f) != h]
    if drift:
        sys.exit(f'Frozen P1-v1 files changed: {drift}. Create p1-v2 instead.')
    return fr


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--all', action='store_true')
    g.add_argument('--item', choices=ITEM_IDS)
    a = ap.parse_args()
    items = ITEM_IDS if a.all else [a.item]
    fr = verify_freeze()
    before = validate_benchmark('before')
    pipe = P1Pipeline(DecisionsClient())
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
        res['runtime_config']['access_audit'] = rep
        write_json(RESULTS_DIR / f'run_{item}.json', res)
        rc = res['runtime_config']
        summary['items'][item] = {'status': 'ok', 'usage': rc['usage'], 'external_api_cost_usd': rc['external_api_cost_usd'],
                                  'latency': rc['latency'], 'refusal_count': rc['refusal_count'], 'retry_count': rc['retry_count'],
                                  'decision_summary': rc['decision_summary'], 'model_returned': rc['decision_model_returned']}
        print(f"{item}: ok, api {rc['latency']['decision_api_latency_ms']:.0f} ms, input_tokens {rc['usage']['input_tokens']}, "
              f"cost ${rc['external_api_cost_usd']:.7f}, refusals {rc['refusal_count']}")
    ok = [v for v in summary['items'].values() if v['status'] == 'ok']
    lat = [v['latency']['decision_api_latency_ms'] for v in ok]
    costs = [v['external_api_cost_usd'] for v in ok if v['external_api_cost_usd'] is not None]
    summary['aggregate'] = {
        'successful_items': len(ok), 'failed_items': [k for k, v in summary['items'].items() if v['status'] != 'ok'],
        'refusal_count': sum(v['refusal_count'] for v in ok),
        'decision_api_latency_ms': {'median': statistics.median(lat), 'min': min(lat), 'max': max(lat)} if lat else None,
        'external_api_cost_usd_total': round(sum(costs), 10) if costs else None,
        'external_api_cost_usd_mean_per_item': round(sum(costs) / len(costs), 10) if costs else None,
        'input_tokens_total': sum(v['usage']['input_tokens'] for v in ok),
    }
    summary['benchmark_validation_before'] = before
    summary['benchmark_validation_after'] = validate_benchmark('after')
    write_json(LOGS_DIR / 'run_summary.json', summary)
    write_json(EXP_ROOT / 'runtime_config.json', {
        'pipeline_actual': 'p1_openai_decisions', 'pipeline_schema_value': 'cv_llm', 'run_id': RUN_ID, 'model_id': MODEL_ID,
        'decision_model': 'gpt-6-luna', 'decision_endpoint': '/v1/decisions', 'input_modality': 'text only',
        'compact_state_version': 'compact-decision-state-v1', 'decision_questions_version': 'decisions-v1',
        'python': sys.version.split()[0], 'openai_sdk': openai.__version__, 'http_client': f'httpx2 {httpx2.__version__}',
        'sdk_call': 'client.decisions.with_raw_response.create(model, input, questions)',
        'timeouts_sec': {'connect': CONNECT_TIMEOUT_SEC, 'read': READ_TIMEOUT_SEC}, 'max_retries': MAX_RETRIES,
        'retry_policy': 'network errors, 429, 5xx only; exponential backoff 1s*2^n + U(0,0.25)s jitter; 4xx never retried',
        'pricing': PRICING, 'freeze_file': 'freeze/p1_freeze.json', 'requests_per_item': 1,
        'latency_note': 'cached P0 CV state reused; decision/serializer/adapter timings only; result latency_ms = null (not full E2E)',
        'estimated_cost_usd_note': 'null in results: local CV compute cost not measured; external_api_cost_usd recorded separately',
    })
    print('aggregate:', summary['aggregate'])


if __name__ == '__main__':
    main()
