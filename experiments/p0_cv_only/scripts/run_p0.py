"""Run P0 CV-only on benchmark items: Canonical CV State -> P0 rules -> results/p0_cv_only/run_ITEM_XX.json.

Each item is executed --repeats times (default 3) with the model already loaded; the median end-to-end time is the
result latency_ms, and predictions/states must be identical across repeats (determinism check).
"""
import _bootstrap  # noqa: F401
import argparse
import statistics
import subprocess
import sys
import time

from access_audit import AccessAudit
from benchmark_runner import P0Runner, latency_stats
from debug_overlay import render_item
from utils import (BENCH_ROOT, EXP_ROOT, ITEM_IDS, LOGS_DIR, RESULTS_DIR, STATES_DIR, rnd, sha256_file, sha256_json,
                   write_json)
from validation import benchmark_validators, validate_state

STAGES = ['decode_ms', 'cv_inference_ms', 'tracking_ms', 'feature_extraction_ms', 'cross_camera_ms', 'state_assembly_ms', 'rule_engine_ms', 'serialization_ms']


def validate_benchmark(tag):
    r = subprocess.run([sys.executable, 'scripts/validate_benchmark.py'], cwd=BENCH_ROOT, capture_output=True, text=True)
    print(f'validate_benchmark ({tag}):', 'PASS' if r.returncode == 0 else 'FAIL', r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr)
        sys.exit(1)
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--all', action='store_true')
    g.add_argument('--item', choices=ITEM_IDS)
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--no-overlays', action='store_true')
    a = ap.parse_args()
    items = ITEM_IDS if a.all else [a.item]
    before = validate_benchmark('before')

    t0 = time.perf_counter()
    runner = P0Runner()
    first = runner.run_item(items[0])
    cold = {'model_load_ms': runner.model_load_ms, 'warmup_ms': runner.warmup_ms, 'init_total_ms': runner.init_ms,
            'first_item': items[0], 'first_item_ms': first['timings']['total_ms'],
            'cold_start_total_ms': (time.perf_counter() - t0) * 1000}
    print(f"model load {cold['model_load_ms']:.0f} ms, cold start total {cold['cold_start_total_ms']:.0f} ms")
    base_rc = runner.runtime_config()
    validate_pred, validate_result = benchmark_validators()
    summary = {'items': {}, 'cold_start': cold}

    for item in items:
        runs, phash, shash = [], set(), set()
        with AccessAudit() as audit:
            for _ in range(a.repeats):
                out = runner.run_item(item)
                runs.append(out)
                phash.add(sha256_json(out['prediction']))
                shash.add(sha256_json(out['state']))
        rep = audit.report()
        if not rep['pass']:
            raise SystemExit(f'Access audit failed for {item}: {rep}')
        out = runs[-1]
        state = out['state']
        validate_state(state)
        state_path = STATES_DIR / f'{item}.json'
        write_json(state_path, state)
        totals = [r['timings']['total_ms'] for r in runs]
        lat = latency_stats([rnd(t, 2) for t in totals])
        stage_medians = {k: rnd(statistics.median(r['timings'][k] for r in runs), 2) for k in STAGES}
        compute = {
            'vram_peak_mb': rnd(max(r['timings']['vram_peak_mb'] or 0 for r in runs), 1) if runs[0]['timings']['vram_peak_mb'] is not None else None,
            'frames_per_sec_median': rnd(statistics.median(r['timings']['frames_per_sec'] for r in runs), 2),
            'cv_inference_ms_median': stage_medians['cv_inference_ms'],
            'feature_extraction_ms_median': rnd(stage_medians['tracking_ms'] + stage_medians['feature_extraction_ms'] + stage_medians['cross_camera_ms'], 2),
            'rule_engine_ms_median': stage_medians['rule_engine_ms'],
        }
        rc = dict(base_rc)
        rc.update({
            'latency': {**lat, 'stage_medians_ms': stage_medians, 'model_load_ms': rnd(cold['model_load_ms'], 1),
                        'cold_start_total_ms': rnd(cold['cold_start_total_ms'], 1), 'cold_start_first_item': cold['first_item']},
            'compute': compute,
            'deterministic_across_repeats': len(phash) == 1 and len(shash) == 1,
            'frame_bytes_fingerprint_sha256': state['input']['input_fingerprint'],
            'state_file': f'experiments/p0_cv_only/states/{item}.json',
            'state_sha256': sha256_file(state_path),
            'access_audit': {k: v for k, v in rep.items() if k != 'other_subprocesses'},
        })
        result = runner.result_json(item, out['prediction'], state['input']['benchmark_input_fingerprint'], lat['median_ms'], rc)
        validate_result(result)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        write_json(RESULTS_DIR / f'run_{item}.json', result)
        if not a.no_overlays:
            vis = runner.run_item(item, keep_frames=True)
            render_item(item, vis['state'], vis['kept_frames'])
        summary['items'][item] = {'latency': lat, 'stage_medians_ms': stage_medians, 'compute': compute,
                                  'deterministic': rc['deterministic_across_repeats'], 'access_audit_pass': rep['pass']}
        print(f"{item}: median {lat['median_ms']:.0f} ms (min {lat['min_ms']:.0f}, max {lat['max_ms']:.0f}), "
              f"deterministic={rc['deterministic_across_repeats']}, result + state written")

    write_json(EXP_ROOT / 'runtime_config.json', {**base_rc, 'cold_start': cold, 'repeats_per_item': a.repeats,
                                                   'results_dir': 'benchmark_v1/results/p0_cv_only', 'run_id': 'p0_cv_only-v1'})
    summary['benchmark_validation_before'] = before
    summary['benchmark_validation_after'] = validate_benchmark('after')
    write_json(LOGS_DIR / 'run_summary.json', summary)


if __name__ == '__main__':
    main()
