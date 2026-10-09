"""Synthetic integration smoke test (no benchmark item, no benchmark state). Success = integration only:
authentication, request shape, response shape, noul/choice/score parsing, usage extraction, latency measurement,
error handling (a deliberately invalid request must fail fast without retry), credential leakage none, raw saved.
Answer content is not evaluated."""
import _bootstrap  # noqa: F401
import datetime
import subprocess
import sys

from access_audit import AccessAudit
from clef_adapter import ClefAnswerNormalizer
from cloudflare_client import MODEL, CloudflareClient, unwrap
from cost import theoretical_cost_usd
from question_adapter import QuestionAdapter
from utils import BENCH_ROOT, LOGS_DIR, RAW_DIR, artifact_files, canonical_json, scan_for_secrets, write_json

STATE = {'schema_version': 'synthetic-smoke-v1', 'observation': {'sensor_ok': True, 'level': 3}}
SEMANTIC = [   # neutral synthetic questions in the same P1 semantic shape, converted by the same QuestionAdapter
    {'type': 'predicate', 'name': 'sensor_ok', 'instructions': 'Does the supplied record report that the sensor is OK?'},
    {'type': 'choice', 'name': 'level_band', 'instructions': 'Which band contains the reported level?',
     'choices': [{'value': 'low', 'description': 'Level 0-1.'}, {'value': 'mid', 'description': 'Level 2-3.'},
                 {'value': 'high', 'description': 'Level 4-5.'}]},
    {'type': 'score', 'name': 'level_rating', 'instructions': 'Rate the reported level.',
     'levels': [{'label': 'zero', 'description': 'Level 0.'}, {'label': 'one', 'description': 'Level 1.'},
                {'label': 'two', 'description': 'Level 2.'}, {'label': 'three', 'description': 'Level 3.'},
                {'label': 'four', 'description': 'Level 4 or more.'}]},
]


def check(res, name, ok, detail=''):
    res.append({'check': name, 'pass': bool(ok), 'detail': detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f' - {detail}' if detail else ''))


def main():
    res = []
    qa = QuestionAdapter({'policy': ''})
    clef_q = qa.to_clef(SEMANTIC)
    client = CloudflareClient()
    with AccessAudit() as audit:
        rec = client.run(canonical_json(STATE), clef_q)
    raw = {'kind': 'synthetic smoke test (not a benchmark item)', 'at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
           'request': {'model': MODEL, 'state': STATE, 'questions': clef_q}, 'api': rec}
    body = unwrap(rec.get('response_body')) if rec['status'] == 'ok' else None
    check(res, 'HTTP success + authentication', rec['status'] == 'ok',
          f"http {rec.get('http_status')} retries {rec['retry_count']}" if rec['status'] == 'ok' else str(rec.get('errors'))[:400])
    norm_tool = ClefAnswerNormalizer()
    if body is not None:
        issues = norm_tool.validate_response(body)
        check(res, 'model response valid (live output schema)', not issues, '; '.join(issues[:3]))
        check(res, 'model returned', bool(body.get('model')), str(body.get('model')))
        norm, nissues = norm_tool.normalize(SEMANTIC, body.get('answers'))
        by = {a['name']: a for a in norm}
        check(res, 'noul parsed', by['sensor_ok']['type'] == 'predicate', f"probability={by['sensor_ok'].get('probability')}")
        check(res, 'choice parsed', by['level_band']['type'] == 'choice', f"choice={by['level_band'].get('choice')}")
        check(res, 'score parsed', by['level_rating']['type'] == 'score',
              f"score={by['level_rating'].get('score')} prob_keys={list((body['answers'].get('level_rating') or {}).get('probabilities', {}))}")
        u = body.get('usage') or {}
        check(res, 'usage parsed (if supplied)', isinstance(u.get('input_tokens'), int) if u else True,
              f"input_tokens={u.get('input_tokens')} output_tokens={u.get('output_tokens')} theoretical_cost=${theoretical_cost_usd(u)}")
        check(res, 'latency measured', rec['timing'].get('last_attempt_ms') is not None, f"{rec['timing']['last_attempt_ms']} ms")
        raw['normalized_answers'], raw['normalize_issues'] = norm, nissues
    # error handling: invalid request schema must not be retried
    bad = client.run(canonical_json(STATE), {})
    raw['invalid_request_probe'] = bad
    check(res, 'error handling: invalid request fails fast, no retry', bad['status'] == 'FAILED' and bad['retry_count'] == 0,
          f"status {[e.get('status') for e in bad.get('errors', [])]} retries {bad['retry_count']}")
    rep = audit.report()
    check(res, 'no forbidden file access', rep['pass'], str(rep['forbidden_paths_opened'][:3]))
    raw_path = RAW_DIR / 'smoke_synthetic.json'
    write_json(raw_path, raw)
    check(res, 'raw response saved', raw_path.is_file(), 'raw_api/smoke_synthetic.json')
    leaks = scan_for_secrets(artifact_files())
    check(res, 'credential leakage none', not leaks, str(leaks))
    passed = all(r['pass'] for r in res)
    write_json(LOGS_DIR / 'smoke_test.json', {
        'passed': passed, 'at': raw['at'], 'checks': res, 'model_returned': (body or {}).get('model'),
        'usage': (body or {}).get('usage'), 'timing': rec['timing'], 'retry_count': rec['retry_count'],
        'score_probability_key_format': list(((body or {}).get('answers', {}).get('level_rating') or {}).get('probabilities', {})),
        'access_audit': rep, 'benchmark_items_used': [],
        'note': 'Synthetic neutral state only; integration test; answer content not evaluated.'})
    print('SMOKE TEST', 'PASS' if passed else 'FAIL')
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
