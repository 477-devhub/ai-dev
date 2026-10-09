"""Synthetic integration smoke test (no benchmark item / state). Checks: Responses API connection, gpt-6.1-sol access,
reasoning.effort=high accepted, strict Structured Outputs accepted for the single / attention ($defs/$ref) / multi_camera
schema shapes, schema parsing, usage + reasoning-token parsing, latency, refusal/incomplete classification (offline,
synthetic bodies), no tools returned, no forbidden file access, API key not in artifacts. Answer content not evaluated."""
import _bootstrap  # noqa: F401
import datetime
import subprocess
import sys

from jsonschema import Draft202012Validator

from access_audit import AccessAudit
from cost import external_api_cost_usd
from openai_client import MODEL, ResponsesClient, classify
from prompt_builder import PromptBuilder
from utils import BENCH_ROOT, LOGS_DIR, RAW_DIR, artifact_files, canonical_json, scan_for_secret, write_json

STATES = {
    'single': {'schema_version': 'synthetic-smoke-v1', 'cameras': [{'camera': 'CAM_01', 'observation': {'sensor_ok': True, 'level': 3}}]},
    'attention': {'schema_version': 'synthetic-smoke-v1', 'cameras': [{'camera': c, 'observation': {'sensor_ok': True, 'level': 3}} for c in ('CAM_01', 'CAM_02', 'CAM_03')]},
    'multi_camera': {'schema_version': 'synthetic-smoke-v1', 'cameras': [{'camera': c, 'observation': {'sensor_ok': True, 'level': 3}} for c in ('CAM_01', 'CAM_02')],
                     'cross_camera': {'sync_confirmed': False, 'identity_link_confirmed': False}},
}


def check(res, name, ok, detail=''):
    res.append({'check': name, 'pass': bool(ok), 'detail': detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f' - {detail}' if detail else ''))


def main():
    res, raws = [], {}
    pb = PromptBuilder()
    client = ResponsesClient()
    with AccessAudit() as audit:
        for task, state in STATES.items():
            cams = [c['camera'] for c in state['cameras']]
            tf = pb.text_format(task, cams)
            rec = client.decide(pb.instructions(task, cams), canonical_json(state), tf)
            raws[task] = {'state': state, 'text_format': tf, 'api': rec}
            ok = rec['status'] == 'ok'
            check(res, f'{task}: HTTP + auth + model access', 'http_status' in rec and rec['http_status'] == 200,
                  f"http {rec.get('http_status')} model {rec.get('model')} retries {rec['retry_count']}" if 'http_status' in rec else str(rec.get('errors'))[:500])
            if 'http_status' not in rec:
                continue
            check(res, f'{task}: strict structured output parsed', ok, rec['status'])
            if ok:
                errs = list(Draft202012Validator(tf['schema']).iter_errors(rec['parsed']))
                check(res, f'{task}: output valid against schema', not errs, errs[0].message if errs else '')
            u = rec['usage'] or {}
            check(res, f'{task}: usage parsed', isinstance(u.get('input_tokens'), int) and isinstance(u.get('output_tokens'), int),
                  f"in={u.get('input_tokens')} cached={(u.get('input_tokens_details') or {}).get('cached_tokens')} out={u.get('output_tokens')} "
                  f"reasoning={(u.get('output_tokens_details') or {}).get('reasoning_tokens')} cost=${external_api_cost_usd(u)}")
            check(res, f'{task}: reasoning tokens parsed', isinstance((u.get('output_tokens_details') or {}).get('reasoning_tokens'), int))
            check(res, f'{task}: reasoning effort high', rec.get('reasoning_effort_returned') == 'high', str(rec.get('reasoning_effort_returned')))
            check(res, f'{task}: no tools', not rec.get('tools_returned'), str(rec.get('tools_returned')))
            check(res, f'{task}: latency measured', rec['timing'].get('last_attempt_ms') is not None,
                  f"{rec['timing']['last_attempt_ms']} ms (processing header {rec.get('openai_processing_ms')})")
    # refusal / incomplete / parse-failure classification on synthetic bodies (no API call)
    k1 = classify({'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'refusal', 'refusal': 'x'}]}]})[0]
    k2 = classify({'status': 'incomplete', 'incomplete_details': {'reason': 'max_output_tokens'}, 'output': []})[0]
    k3 = classify({'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': '{not json'}]}]})[0]
    check(res, 'refusal / incomplete / parse-failure classification', (k1, k2, k3) == ('refusal', 'incomplete', 'parse_failure'), f'{k1},{k2},{k3}')
    r = subprocess.run([sys.executable, 'scripts/offline_adapter_test.py'], capture_output=True, text=True)
    check(res, 'refusal path through adapters (offline synthetic)', r.returncode == 0)
    rep = audit.report()
    check(res, 'no forbidden file access', rep['pass'], str(rep['forbidden_paths_opened'][:3]))
    write_json(RAW_DIR / 'smoke_synthetic.json', {'kind': 'synthetic smoke test (not a benchmark item)', 'model': MODEL, 'calls': raws})
    check(res, 'raw response saved', (RAW_DIR / 'smoke_synthetic.json').is_file())
    leaks = scan_for_secret(artifact_files())
    check(res, 'API key not in artifacts', not leaks, str(leaks))
    passed = all(x['pass'] for x in res)
    write_json(LOGS_DIR / 'smoke_test.json', {
        'passed': passed, 'at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'checks': res,
        'usage': {t: (raws[t]['api'].get('usage')) for t in raws}, 'timing': {t: raws[t]['api']['timing'] for t in raws},
        'model_returned': {t: raws[t]['api'].get('model') for t in raws}, 'benchmark_items_used': [], 'access_audit': rep,
        'note': 'Synthetic neutral states only; integration test; answer content not evaluated.'})
    print('SMOKE TEST', 'PASS' if passed else 'FAIL')
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
