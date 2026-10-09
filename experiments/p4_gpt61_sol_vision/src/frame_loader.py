"""Canonical frames ONLY via benchmark_v1/scripts/load_model_input.py iter_model_frames (uniform_total64_v1).

The benchmark loader file is protected by BENCHMARK_LOCK (checked by validate_benchmark.py) and loaded by path. No extra frames, no reordering: refs F001..F064 follow iteration order. Returns pixels + generic camera
id + relative timestamp only; the item id stays in harness metadata. Timing of decode is measured per frame.
"""
import importlib.util
import time

from utils import BENCH_ROOT, sha256_bytes

_loader = None


def _bench_loader():
    global _loader
    if _loader is None:
        spec = importlib.util.spec_from_file_location('bench_load_model_input', BENCH_ROOT / 'scripts' / 'load_model_input.py')
        _loader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_loader)
    return _loader


def item_task(item_id):
    return _bench_loader().load_item(item_id)['task']


def load_frames(item_id):
    """Returns (frames, decode_ms, per_camera_counts, input_fingerprint). frames: [{'ref','camera','timestamp_sec','width','height','rgb24','rgb_sha256'}]."""
    L = _bench_loader()
    frames, decode_ms = [], 0.0
    it = L.iter_model_frames(item_id)
    while True:
        t0 = time.perf_counter()
        try:
            f = next(it)
        except StopIteration:
            decode_ms += (time.perf_counter() - t0) * 1000
            break
        decode_ms += (time.perf_counter() - t0) * 1000
        frames.append({'ref': f'F{len(frames) + 1:03d}', 'camera': f['camera'], 'timestamp_sec': f['timestamp_sec'],
                       'width': f['width'], 'height': f['height'], 'rgb24': f['rgb24'], 'rgb_sha256': sha256_bytes(f['rgb24'])})
    fp = L.load_item(item_id)['input_fingerprint']
    expected = sum(len(v) for v in fp['frame_numbers'].values())
    if len(frames) != 64 or expected != 64:
        raise RuntimeError(f'frame budget violated: got {len(frames)}, schedule {expected} (uniform_total64_v1 requires 64)')
    per_cam = {}
    for f in frames:
        per_cam[f['camera']] = per_cam.get(f['camera'], 0) + 1
    if per_cam != {c: len(v) for c, v in fp['frame_numbers'].items()}:
        raise RuntimeError(f'per-camera frame allocation mismatch {per_cam}')
    return frames, decode_ms, per_cam, fp
