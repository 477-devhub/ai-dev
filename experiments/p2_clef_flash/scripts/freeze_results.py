"""Freeze P2 outputs BEFORE any ground-truth access: validate each result with benchmark validate_prediction.py --result,
then write freeze/p2_results_manifest.json (SHA256 of 7 results + raw API files + run summary + leakage audit).
Refuses to run if the leakage audit did not pass or if any GT/evaluation event is already logged."""
import _bootstrap  # noqa: F401
import datetime
import subprocess
import sys

from process_log import events, log_event
from utils import BENCH_ROOT, EVAL_DIR, EXP_ROOT, FREEZE_DIR, ITEM_IDS, LOGS_DIR, RAW_DIR, RESULTS_DIR, load_json, sha256_file, write_json

GT_EVENTS = ('build_auto_ground_truth', 'run_auto_eval', 'compare_p1_p2')


def main():
    out = FREEZE_DIR / 'p2_results_manifest.json'
    if out.exists():
        sys.exit('results already frozen')
    if any(e['event'] in GT_EVENTS for e in events()) or (EVAL_DIR / 'normalized_ground_truth_v1.json').exists():
        sys.exit('GT/evaluation already happened before result freeze: protocol violation')
    if load_json(LOGS_DIR / 'leakage_audit.json')['verdict'] != 'PASS':
        sys.exit('leakage audit not PASS')
    val = {}
    for item in ITEM_IDS:
        r = subprocess.run([sys.executable, 'scripts/validate_prediction.py', f'results/p2_clef_flash/run_{item}.json', '--result'],
                           cwd=BENCH_ROOT, capture_output=True, text=True)
        val[item] = {'pass': r.returncode == 0, 'output': (r.stdout + r.stderr).strip()[-300:]}
        print(item, 'PASS' if r.returncode == 0 else 'FAIL', val[item]['output'])
    if not all(v['pass'] for v in val.values()):
        sys.exit('prediction validation failed; not freezing')
    files = ([RESULTS_DIR / f'run_{i}.json' for i in ITEM_IDS] + [RAW_DIR / f'{i}.json' for i in ITEM_IDS]
             + [LOGS_DIR / 'run_summary.json', LOGS_DIR / 'leakage_audit.json', EXP_ROOT / 'runtime_config.json', FREEZE_DIR / 'p2_freeze.json'])
    rec = {
        'frozen_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        'p2_version': 'p2-v1',
        'ground_truth_accessed_before_freeze': False,
        'prediction_validation': val,
        'sha256': {(p.relative_to(BENCH_ROOT).as_posix() if p.is_relative_to(BENCH_ROOT) else p.relative_to(EXP_ROOT).as_posix()): sha256_file(p) for p in files},
        'note': 'Automatic evaluation may read these files but must never modify them; run_auto_eval verifies this manifest first.',
    }
    write_json(out, rec)
    log_event('p2_results_frozen', {'files': len(files)})
    print('RESULTS FROZEN', out)


if __name__ == '__main__':
    main()
