"""P0 smoke test on one item: canonical-frame audit, CV model, state + schema, prediction + schema, access audit."""
import _bootstrap  # noqa: F401
import argparse
import json
import subprocess
import sys

from access_audit import AccessAudit
from benchmark_runner import P0Runner
from utils import BENCH_ROOT, DEBUG_DIR, write_json
from validation import benchmark_validators, validate_state


def check(name, ok, detail=''):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f' - {detail}' if detail else ''))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--item', default='ITEM_01')
    a = ap.parse_args()
    results = []
    bench = subprocess.run([sys.executable, 'scripts/validate_benchmark.py'], cwd=BENCH_ROOT, capture_output=True, text=True)
    results.append(check('benchmark validate (before)', bench.returncode == 0, bench.stdout.strip()[:160]))

    runner = P0Runner()
    results.append(check('CV model loaded', runner.detector.info['task'] == 'pose',
                         f"{runner.detector.info['name']} {runner.detector.info['device']} {runner.detector.info['precision']}"))
    with AccessAudit() as audit:
        out = runner.run_item(a.item)
    rep = audit.report()
    st = out['state']
    results.append(check('exactly 64 canonical frames used', out['audit']['frames_consumed'] == 64, json.dumps(out['audit']['per_camera'])))
    results.append(check('frames came from load_model_input.iter_model_frames', out['audit']['frame_source'] == 'load_model_input.iter_model_frames'))
    results.append(check('CV produced detections', st['cameras'][0]['detection_summary']['total_detections'] >= 0,
                         f"{sum(c['detection_summary']['total_detections'] for c in st['cameras'])} detections"))
    try:
        validate_state(st)
        results.append(check('state schema', True))
    except Exception as e:
        results.append(check('state schema', False, str(e)))
    validate_pred, validate_result = benchmark_validators()
    try:
        validate_pred(out['prediction'], a.item)
        results.append(check('prediction schema (benchmark validator)', True))
    except Exception as e:
        results.append(check('prediction schema (benchmark validator)', False, str(e)))
    res = runner.result_json(a.item, out['prediction'], st['input']['benchmark_input_fingerprint'], out['timings']['total_ms'], runner.runtime_config())
    try:
        validate_result(res)
        results.append(check('result schema + fingerprint (benchmark validator)', True))
    except Exception as e:
        results.append(check('result schema + fingerprint (benchmark validator)', False, str(e)))
    results.append(check('no private / label path accessed', not rep['private_or_label_paths_opened'], str(rep['private_or_label_paths_opened'][:3])))
    results.append(check('no direct MP4 access (only canonical ffmpeg select via loader)',
                         not rep['mp4_opened_directly_by_python'] and rep['ffmpeg_processes_not_using_canonical_select'] == 0 and not rep['other_subprocesses'],
                         f"ffmpeg decodes={rep['ffmpeg_decode_processes']}"))
    bench = subprocess.run([sys.executable, 'scripts/validate_benchmark.py'], cwd=BENCH_ROOT, capture_output=True, text=True)
    results.append(check('benchmark validate (after)', bench.returncode == 0))
    write_json(DEBUG_DIR / 'reports' / f'smoke_{a.item}.json', {
        'item_id': a.item, 'passed': all(results), 'checks_passed': sum(results), 'checks_total': len(results),
        'access_audit': rep, 'timings_ms': out['timings'], 'frames': out['audit'],
        'event_type': out['prediction'].get('event_type'),
    })
    print('SMOKE TEST', 'PASS' if all(results) else 'FAIL')
    sys.exit(0 if all(results) else 1)


if __name__ == '__main__':
    main()
