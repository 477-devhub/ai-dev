"""Latency / compute record for P0 (model already loaded). Writes debug/reports/latency_report.json.

Measures per item: end-to-end steady-state latency (median/min/max over --repeats), per-stage medians, VRAM peak,
frames/sec, process CPU utilisation and (if NVML is available) sampled GPU utilisation. Values that cannot be
measured are null. Primary result latency_ms values are produced by run_p0.py; this script is the detailed record.
"""
import _bootstrap  # noqa: F401
import argparse
import statistics
import threading
import time

import psutil

from benchmark_runner import P0Runner
from utils import DEBUG_DIR, ITEM_IDS, rnd, write_json

STAGES = ['decode_ms', 'cv_inference_ms', 'tracking_ms', 'feature_extraction_ms', 'cross_camera_ms', 'state_assembly_ms', 'rule_engine_ms', 'serialization_ms', 'total_ms']


class GpuSampler:
    def __init__(self):
        self.samples, self.ok = [], False
        try:
            import pynvml
            pynvml.nvmlInit()
            self.nv, self.h, self.ok = pynvml, pynvml.nvmlDeviceGetHandleByIndex(0), True
        except Exception:
            pass

    def __enter__(self):
        self.stop = False
        if self.ok:
            self.t = threading.Thread(target=self._run, daemon=True)
            self.t.start()
        return self

    def _run(self):
        while not self.stop:
            self.samples.append(self.nv.nvmlDeviceGetUtilizationRates(self.h).gpu)
            time.sleep(0.1)

    def __exit__(self, *a):
        self.stop = True
        if self.ok:
            self.t.join()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repeats', type=int, default=3)
    a = ap.parse_args()
    bat = psutil.sensors_battery()
    t0 = time.perf_counter()
    runner = P0Runner()
    proc = psutil.Process()
    report = {'model_load_ms': rnd(runner.model_load_ms, 1), 'warmup_ms': rnd(runner.warmup_ms, 1),
              'runner_init_ms': rnd(runner.init_ms, 1), 'power_plugged': bat.power_plugged if bat else None,
              'device': runner.detector.info['device'], 'precision': runner.detector.info['precision'],
              'items': {}}
    first = runner.run_item(ITEM_IDS[0])
    report['cold_start_total_ms'] = rnd((time.perf_counter() - t0) * 1000, 1)
    report['cold_first_item_ms'] = rnd(first['timings']['total_ms'], 1)
    for item in ITEM_IDS:
        runs, cpu = [], []
        with GpuSampler() as g:
            for _ in range(a.repeats):
                proc.cpu_percent(None)
                runs.append(runner.run_item(item)['timings'])
                cpu.append(proc.cpu_percent(None) / psutil.cpu_count())
        tot = [r['total_ms'] for r in runs]
        report['items'][item] = {
            'steady_state_latency_ms': {'median': rnd(statistics.median(tot), 1), 'min': rnd(min(tot), 1), 'max': rnd(max(tot), 1), 'n': len(tot)},
            'stage_medians_ms': {k: rnd(statistics.median(r[k] for r in runs), 2) for k in STAGES},
            'vram_peak_mb': rnd(max(r['vram_peak_mb'] for r in runs), 1) if runs[0]['vram_peak_mb'] is not None else None,
            'frames_per_sec_median': rnd(statistics.median(r['frames_per_sec'] for r in runs), 2),
            'process_cpu_utilization_pct_of_all_cores_median': rnd(statistics.median(cpu), 1),
            'gpu_utilization_pct_mean': rnd(statistics.fmean(g.samples), 1) if g.samples else None,
            'gpu_utilization_pct_max': max(g.samples) if g.samples else None,
        }
        print(item, report['items'][item]['steady_state_latency_ms'], 'GPU util mean', report['items'][item]['gpu_utilization_pct_mean'])
    meds = [v['steady_state_latency_ms']['median'] for v in report['items'].values()]
    report['across_items'] = {'median_of_item_medians_ms': rnd(statistics.median(meds), 1), 'min_ms': min(v['steady_state_latency_ms']['min'] for v in report['items'].values()),
                              'max_ms': max(v['steady_state_latency_ms']['max'] for v in report['items'].values())}
    write_json(DEBUG_DIR / 'reports' / 'latency_report.json', report)
    print('power_plugged:', report['power_plugged'], '| across items:', report['across_items'])


if __name__ == '__main__':
    main()
