"""Freeze P3 outputs BEFORE any ground-truth access: validate_prediction --result x7, then freeze/p3_results_manifest.json."""
import _bootstrap  # noqa: F401
import datetime
import subprocess
import sys

from process_log import events, log_event
from utils import BENCH_ROOT, EVAL_DIR, EXP_ROOT, FREEZE_DIR, ITEM_IDS, LOGS_DIR, RAW_DIR, RESULTS_DIR, load_json, sha256_file, write_json


def main():
    out = FREEZE_DIR / 'p3_results_manifest.json'
    if out.exists():
        sys.exit('results already frozen')
    if any(e['event'].startswith(('run_auto_eval', 'compare_')) for e in events()) or any(EVAL_DIR.glob('*')):
        sys.exit('evaluation already happened before result freeze: protocol violation')
    if load_json(LOGS_DIR / 'leakage_audit.json')['verdict'] != 'PASS':
        sys.exit('leakage audit not PASS')
    val = {}
    for item in ITEM_IDS:
        r = subprocess.run([sys.executable, 'scripts/validate_prediction.py', f'results/p3_gpt61_sol_state/run_{item}.json', '--result'],
                           cwd=BENCH_ROOT, capture_output=True, text=True)
        val[item] = {'pass': r.returncode == 0, 'output': (r.stdout + r.stderr).strip()[-300:]}
        print(item, 'PASS' if r.returncode == 0 else 'FAIL', val[item]['output'])
    if not all(v['pass'] for v in val.values()):
        sys.exit('prediction validation failed; not freezing')
    files = ([RESULTS_DIR / f'run_{i}.json' for i in ITEM_IDS] + [RAW_DIR / f'{i}.json' for i in ITEM_IDS]
             + [LOGS_DIR / 'run_summary.json', LOGS_DIR / 'leakage_audit.json', EXP_ROOT / 'runtime_config.json', FREEZE_DIR / 'p3_freeze.json'])
    rec = {'frozen_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'p3_version': 'p3-v1',
           'ground_truth_accessed_before_freeze': False, 'prediction_validation': val,
           'sha256': {(p.relative_to(BENCH_ROOT).as_posix() if p.is_relative_to(BENCH_ROOT) else p.relative_to(EXP_ROOT).as_posix()): sha256_file(p) for p in files}}
    write_json(out, rec)
    log_event('p3_results_frozen', {'files': len(files)})
    print('RESULTS FROZEN', out)


if __name__ == '__main__':
    main()
