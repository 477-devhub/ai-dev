"""P0.5 integration smoke test: one Decisions API request for one item. Success = integration, not answer quality."""
import _bootstrap  # noqa: F401
import sys as _s; _s.path.insert(0, __import__("os").path.dirname(__file__))
import argparse
import os
import subprocess
import sys

import offline_adapter_test
from access_audit import AccessAudit
from decisions_client import DecisionsClient
from p1_pipeline import P1Pipeline, raw_record
from utils import BENCH_ROOT, COMPACT_DIR, EXP_ROOT, LOGS_DIR, RAW_DIR, load_json, sha256_file, write_json


def check(results, name, ok, detail=''):
    results.append((name, bool(ok)))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f' - {detail}' if detail else ''))


def validate_benchmark():
    return subprocess.run([sys.executable, 'scripts/validate_benchmark.py'], cwd=BENCH_ROOT, capture_output=True, text=True)


def key_leak_scan(paths):
    """True/False scan only; the key value is never printed or written."""
    key = os.environ.get('OPENAI_API_KEY', '')
    if len(key) < 8:
        return []
    hits = []
    for p in paths:
        try:
            if key in p.read_text(encoding='utf-8', errors='ignore'):
                hits.append(str(p))
        except Exception:
            pass
    return hits


def artifact_files():
    return [p for p in EXP_ROOT.rglob('*') if p.is_file() and '.venv' not in p.parts and p.suffix in ('.json', '.md', '.txt', '.py', '.yaml', '.log')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--item', default='ITEM_01')
    a = ap.parse_args()
    res = []
    r = validate_benchmark()
    check(res, 'benchmark validate (before)', r.returncode == 0, r.stdout.strip()[:120])
    sha_before = sha256_file(COMPACT_DIR / f'{a.item}.json')
    check(res, 'refusal handling path (offline synthetic test)', offline_adapter_test.main())
    pipe = P1Pipeline(DecisionsClient())
    with AccessAudit() as audit:
        out = pipe.run(a.item)
    rep = audit.report()
    raw_path = RAW_DIR / f'p0_5_{a.item}.json'
    write_json(raw_path, raw_record(out))
    api = out['api']
    check(res, 'API authentication + request successful', api['status'] == 'ok',
          f"http {api.get('http_status')}, retries {api['retry_count']}" if api['status'] == 'ok' else str(api.get('errors'))[:500])
    if api['status'] != 'ok':
        write_json(LOGS_DIR / 'p0_5_smoke.json', {'passed': False, 'checks': [{'check': n, 'pass': ok} for n, ok in res], 'errors': api.get('errors')})
        print('P0.5 SMOKE TEST FAIL')
        sys.exit(1)
    check(res, 'model returned', api['model'].startswith('gpt-6-luna'), api['model'])
    qtypes = {q['name']: q['type'] for q in out['prep']['questions']}
    ans = {x.get('name'): x for x in api['answers']}
    check(res, 'answers returned for every question, in order', [x.get('name') for x in api['answers']] == list(qtypes), f"{len(api['answers'])}/{len(qtypes)}")
    for t in ('predicate', 'choice', 'score'):
        names = [n for n, ty in qtypes.items() if ty == t]
        parsed = [n for n in names if ans.get(n, {}).get('type') in (t, 'refusal')]
        check(res, f'{t} answers parsed', names and parsed == names, f'{len(parsed)}/{len(names)}')
    u = api['usage']
    check(res, 'usage captured', isinstance(u.get('input_tokens'), int), f"input_tokens={u.get('input_tokens')} output_tokens={u.get('output_tokens')}")
    check(res, 'prediction + result structurally valid (benchmark schemas)', out['status'] == 'ok')
    check(res, 'raw response saved', raw_path.is_file(), str(raw_path.relative_to(EXP_ROOT)))
    check(res, 'compact state unchanged', sha256_file(COMPACT_DIR / f'{a.item}.json') == sha_before == load_json(COMPACT_DIR / 'manifest.json')['items'][a.item]['compact_sha256'])
    check(res, 'no private / forbidden data accessed', rep['pass'], str(rep['forbidden_paths_opened'][:3]))
    leaks = key_leak_scan(artifact_files())
    check(res, 'API key not present in any artifact', not leaks, str(leaks))
    check(res, 'benchmark validate (after)', validate_benchmark().returncode == 0)
    passed = all(ok for _, ok in res)
    write_json(LOGS_DIR / 'p0_5_smoke.json', {
        'item_id': a.item, 'passed': passed, 'checks': [{'check': n, 'pass': ok} for n, ok in res],
        'model_returned': api['model'], 'usage': u, 'timing': api['timing'], 'retry_count': api['retry_count'],
        'answer_types': {n: ans[n]['type'] for n in qtypes}, 'access_audit': rep,
        'note': 'Integration-only smoke test; answer content intentionally not evaluated or used for tuning.'})
    print('P0.5 SMOKE TEST', 'PASS' if passed else 'FAIL')
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
