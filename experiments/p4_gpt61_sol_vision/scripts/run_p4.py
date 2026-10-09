"""P4 primary run: 1 Responses request per item (64 canonical frames), frozen P4-v1. Failed items recorded, never faked.
Writes raw_api/ITEM_XX.json (no base64), logs/frame_manifest_ITEM_XX.json, logs/request_text_ITEM_XX.txt, results."""
import _bootstrap  # noqa: F401
import argparse
import statistics
import subprocess
import sys

import openai

from access_audit import AccessAudit
from cost import PRICING
from openai_client import CONNECT_TIMEOUT_SEC, MAX_OUTPUT_TOKENS, MAX_RETRIES, READ_WRITE_TIMEOUT_SEC, ResponsesClient
from p4_pipeline import CFG, MODEL_ID, RUN_ID, P4Pipeline, frame_manifest, raw_record
from process_log import log_event
from utils import BENCH_ROOT, EXP_ROOT, FREEZE_DIR, ITEM_IDS, LOGS_DIR, RAW_DIR, RESULTS_DIR, load_json, sha256_file, write_json


def validate_benchmark(tag):
    r = subprocess.run([sys.executable, 'scripts/validate_benchmark.py'], cwd=BENCH_ROOT, capture_output=True, text=True)
    print(f'validate_benchmark ({tag}):', 'PASS' if r.returncode == 0 else 'FAIL', r.stdout.strip(), flush=True)
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
    if (FREEZE_DIR / 'p4_results_manifest.json').exists():
        sys.exit('P4 results already frozen; refusing to overwrite')
    fr = load_json(FREEZE_DIR / 'p4_freeze.json')
    drift = [f for f, h in fr['hashes'].items() if sha256_file(EXP_ROOT / f) != h]
    if drift:
        sys.exit(f'Frozen P4-v1 files changed: {drift}. Create p4-v2 instead.')
    tv = load_json(LOGS_DIR / 'transport_verification.json')
    before = validate_benchmark('before_p4_run')
    log_event('run_p4_start', {'items': items})
    pipe = P4Pipeline(ResponsesClient())
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = {'run_id': RUN_ID, 'model_id': MODEL_ID, 'freeze': {'frozen_at': fr['frozen_at']}, 'items': {}}
    for item in items:
        with AccessAudit() as audit:
            out = pipe.run(item)
        rep = audit.report()
        if not rep['pass']:
            sys.exit(f'{item}: access audit failed {rep}')
        prep = out['prep']
        same_as_verified = [r['encoded_sha256'] for r in prep['manifest_rows']] == [r['encoded_sha256'] for r in tv['items'][item]['frames']]
        write_json(LOGS_DIR / f'frame_manifest_{item}.json', dict(frame_manifest(prep), encoded_bytes_identical_to_transport_verification=same_as_verified))
        (LOGS_DIR / f'request_text_{item}.txt').write_text(prep['request_text'], encoding='utf-8')
        write_json(RAW_DIR / f'{item}.json', raw_record(out))
        if out['status'] != 'ok':
            summary['items'][item] = {'status': 'FAILED', 'response_status': out['api'].get('status'), 'errors': out['api'].get('errors'),
                                      'adapter_error': out['api'].get('adapter_error'), 'retry_count': out['api']['retry_count']}
            print(f"{item}: FAILED ({out['api'].get('status')}) {out['api'].get('errors') or out['api'].get('adapter_error') or out['api'].get('incomplete_details')}", flush=True)
            continue
        res = out['result']
        res['runtime_config']['access_audit'] = rep
        res['runtime_config']['encoded_frames_identical_to_transport_verification'] = same_as_verified
        write_json(RESULTS_DIR / f'run_{item}.json', res)
        rc = res['runtime_config']
        summary['items'][item] = {'status': 'ok', 'usage': rc['usage'], 'external_api_cost_usd': rc['external_api_cost_usd'], 'latency': rc['latency'],
                                  'retry_count': rc['retry_count'], 'service_tier_returned': rc['service_tier_returned'], 'decision_summary': rc['decision_summary']}
        u, L = rc['usage'], rc['latency']
        print(f"{item}: ok, full {L['full_pipeline_ms'] / 1000:.1f}s (api {L['api_request_total_ms'] / 1000:.1f}s), in {u['input_tokens']} (cached {u['cached_input_tokens']}), "
              f"out {u['output_tokens']} (reasoning {u['reasoning_tokens']}), cost ${rc['external_api_cost_usd']:.4f}, retries {rc['retry_count']}", flush=True)
    ok = [v for v in summary['items'].values() if v['status'] == 'ok']
    full = [v['latency']['full_pipeline_ms'] for v in ok]
    api = [v['latency']['api_request_total_ms'] for v in ok]
    costs = [v['external_api_cost_usd'] for v in ok if v['external_api_cost_usd'] is not None]
    summary['aggregate'] = {
        'attempted_items': len(items), 'successful_items': len(ok), 'failed_items': [k for k, v in summary['items'].items() if v['status'] != 'ok'],
        'retries_total': sum(v['retry_count'] for v in summary['items'].values()),
        'full_pipeline_ms': {'median': statistics.median(full), 'min': min(full), 'max': max(full)} if full else None,
        'api_request_total_ms': {'median': statistics.median(api), 'min': min(api), 'max': max(api)} if api else None,
        'external_api_cost_usd_total': round(sum(costs), 8) if costs else None,
        'external_api_cost_usd_mean_per_item': round(sum(costs) / len(costs), 8) if costs else None,
        'tokens_total': {k: sum((v['usage'][k] or 0) for v in ok) for k in ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_tokens')}}
    summary['benchmark_validation_before'] = before
    summary['benchmark_validation_after'] = validate_benchmark('after_p4_run')
    write_json(LOGS_DIR / 'run_summary.json', summary)
    write_json(EXP_ROOT / 'runtime_config.json', {
        'pipeline_actual': CFG['pipeline_actual'], 'pipeline_schema_value': CFG['pipeline_schema_value'], 'run_id': RUN_ID, 'model_id': MODEL_ID,
        'model': 'gpt-6.1-sol', 'endpoint': '/v1/responses', 'reasoning_effort': 'high', 'service_tier': 'default (not sent)', 'tools': [], 'store': False,
        'input_modality': 'vision', 'frame_protocol': 'uniform_total64_v1', 'image_detail': 'high', 'transport': 'lossless_webp', 'total_images': 64,
        'common_adapter': 'v2', 'probability_source': 'model_generated_estimate', 'python': sys.version.split()[0], 'openai_sdk': openai.__version__,
        'timeouts_sec': {'connect': CONNECT_TIMEOUT_SEC, 'read_write': READ_WRITE_TIMEOUT_SEC}, 'max_output_tokens': MAX_OUTPUT_TOKENS,
        'max_retries': MAX_RETRIES, 'retry_policy': CFG['retry_policy'], 'failure_policy': CFG['failure_policy'], 'pricing': PRICING,
        'freeze_file': 'freeze/p4_freeze.json', 'requests_per_item': 1,
        'latency_note': 'result latency_ms = full P4 visual path (frames -> validated prediction); P1/P2/P3 primary latencies are cached-state decision paths; fair comparison pending controlled_latency_v1'})
    log_event('run_p4_end', summary['aggregate'])
    print('aggregate:', summary['aggregate'], flush=True)


if __name__ == '__main__':
    main()
