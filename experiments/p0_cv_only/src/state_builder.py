"""Builds the Canonical CV State (cv-state-v1) for one benchmark item.

canonical frames -> PoseDetector -> SparseTracker -> CameraFeatureExtractor -> cross-camera comparison.
The output contains observations only; event interpretation belongs to decision layers (P0 rules, P1-P3).
"""
import math
import statistics
import time

import numpy as np

from feature_extractor import LOW_SET, CameraFeatureExtractor
from frame_source import PROTOCOL, CanonicalFrameSource
from sparse_tracker import SparseTracker
from utils import (CACHE_DIR, CV_CONFIG_PATH, EXP_ROOT, clip01, read_json, rnd, sha256_file,
                   sha256_json, write_json)

CV_CODE_FILES = ['frame_source.py', 'pose_detector.py', 'sparse_tracker.py', 'feature_extractor.py', 'state_builder.py', 'utils.py']


def cv_code_sha256():
    return sha256_json({f: sha256_file(EXP_ROOT / 'src' / f) for f in CV_CODE_FILES})


class StateBuilder:
    def __init__(self, cfg, detector):
        self.cfg = cfg
        self.detector = detector
        self.tracker = SparseTracker(cfg)
        self.extractor = CameraFeatureExtractor(cfg)
        self.cv_config_sha256 = sha256_file(CV_CONFIG_PATH)
        self.code_sha256 = cv_code_sha256()

    def generator_info(self):
        i = self.detector.info
        return {
            'layer': 'shared_cheap_cv',
            'cv_model': {k: i[k] for k in ('name', 'task', 'weights_file', 'weights_sha256', 'library', 'library_version',
                                           'precision', 'input_size', 'conf_threshold', 'iou_threshold', 'pretrained_only')},
            'cv_config_sha256': self.cv_config_sha256,
            'cv_code_sha256': self.code_sha256,
            'external_api_calls': 0,
            'llm_or_vlm_used': False,
        }

    def cache_key(self, camera_id, frame_fp):
        return sha256_json({'camera': camera_id, 'frames': frame_fp, 'model': self.detector.info['weights_sha256'],
                            'precision': self.detector.info['precision'], 'cv_config': self.cv_config_sha256, 'code': self.code_sha256})

    def build(self, item_id, use_cache=False, keep_frames=False):
        timings = {'decode_ms': 0.0, 'cv_inference_ms': 0.0, 'tracking_ms': 0.0, 'feature_extraction_ms': 0.0,
                   'cross_camera_ms': 0.0, 'state_assembly_ms': 0.0}
        source = CanonicalFrameSource(item_id)
        frames_by_cam = {c: [] for c in source.cameras}
        t0 = time.perf_counter()
        for cam, idx, ts, rgb in source.iter_frames():
            frames_by_cam[cam].append((idx, ts, rgb))
        timings['decode_ms'] = (time.perf_counter() - t0) * 1000

        cameras, cache_hits, kept = [], [], {}
        for cam in source.cameras:
            key = self.cache_key(cam, source.fingerprints[cam])
            cache_file = CACHE_DIR / f'{key}.json'
            if use_cache and cache_file.is_file():
                cam_state = read_json(cache_file)
                cache_hits.append(cam)
            else:
                cam_state = self._camera_state(cam, frames_by_cam[cam], source.frame_numbers[cam], timings, kept if keep_frames else None)
                cam_state['frame_fingerprint_sha256'] = source.fingerprints[cam]
                if use_cache:
                    write_json(cache_file, cam_state)
            cameras.append(cam_state)

        t0 = time.perf_counter()
        cross = cross_camera_state(cameras, self.cfg) if len(cameras) == 2 else None
        timings['cross_camera_ms'] = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        state = {
            'state_version': self.cfg['state_version'],
            'generator': self.generator_info(),
            'input': {
                'item_id': item_id,
                'task': source.task,
                'frame_protocol': PROTOCOL,
                'input_fingerprint': source.item_frame_fingerprint(),
                'benchmark_input_fingerprint': source.benchmark_fingerprint,
                'total_frames': source.audit['frames_consumed'],
                'camera_ids': source.cameras,
                'frames_per_camera': source.audit['per_camera'],
                'time_reference': 'clip-relative seconds per camera; no cross-camera synchronization',
            },
            'cameras': cameras,
            'cross_camera': cross,
        }
        timings['state_assembly_ms'] = (time.perf_counter() - t0) * 1000
        audit = {'frames_consumed': source.audit['frames_consumed'], 'per_camera': dict(source.audit['per_camera']),
                 'cache_hits': cache_hits, 'frame_source': 'load_model_input.iter_model_frames'}
        return state, timings, audit, kept

    def _camera_state(self, cam, frames, frame_numbers, timings, kept):
        t0 = time.perf_counter()
        dets = self.detector.detect([rgb for _, _, rgb in frames])
        timings['cv_inference_ms'] += (time.perf_counter() - t0) * 1000
        frame_dicts = []
        for (idx, ts, _), d in zip(frames, dets):
            d.update({'index': idx, 'timestamp_sec': ts, 'frame_number': frame_numbers[idx]})
            frame_dicts.append(d)
        t0 = time.perf_counter()
        tracks = self.tracker.run(frame_dicts)
        timings['tracking_ms'] += (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        state = self.extractor.extract(cam, frame_dicts, tracks)
        timings['feature_extraction_ms'] += (time.perf_counter() - t0) * 1000
        if kept is not None:
            kept[cam] = [(ts, rgb) for _, ts, rgb in frames]
        return state


# ----------------------------------------------------------------------------- cross-camera
def _corr01(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.std() < 1e-9 or b.std() < 1e-9:
        return None
    return float((np.corrcoef(a, b)[0, 1] + 1.0) / 2.0)


def _phase_curves(cam, bins):
    times = cam['sampling']['timestamps_sec']
    span = max(times[-1], 1e-6)
    W, H = cam['image_size']
    count = [[] for _ in range(bins)]
    low = [[] for _ in range(bins)]
    act = [[] for _ in range(bins)]
    b_of = lambda t: min(bins - 1, int(t / span * bins))
    for f in cam['frames']:
        b = b_of(f['timestamp_sec'])
        count[b].append(f['person_count'])
        for d in f['detections']:
            if d['posture']['label'] != 'unknown':
                low[b].append(1.0 if d['posture']['label'] in LOW_SET else 0.0)
    for tr in cam['tracks']:
        path = tr['geometry']['center_path']
        for (t0, x0, y0), (t1, x1, y1) in zip(path, path[1:]):
            if t1 > t0:
                act[b_of((t0 + t1) / 2)].append(math.hypot((x1 - x0) * W / H, y1 - y0) / (t1 - t0))
    mean = lambda xs: statistics.fmean(xs) if xs else 0.0
    return {'count': [mean(x) for x in count], 'activity': [sum(x) for x in act],
            'low_posture': [mean(x) for x in low], 'has_frames': [bool(x) for x in count]}


def _signature(cam):
    pw = cam['pairwise_interactions']
    trs = cam['tracks']
    q = cam['detection_summary']
    return [
        clip01(q['person_count_max'] / 5.0),
        max([p['close_proximity_fraction'] or 0 for p in pw], default=0.0),
        clip01(max([p['relative_motion_intensity_when_close'] or 0 for p in pw], default=0.0)),
        max([p['contact_proxy']['score'] or 0 for p in pw], default=0.0),
        1.0 if any(t['vertical_transition']['upright_to_low_transition'] for t in trs) else 0.0,
        max([t['posture']['low_or_horizontal_fraction'] or 0 for t in trs if t['reliability']['reliability_label'] != 'low'], default=0.0),
    ]


def cross_camera_state(cameras, cfg):
    bins = cfg['cross_camera']['phase_bins']
    A, B = cameras
    ca, cb = _phase_curves(A, bins), _phase_curves(B, bins)
    med_a, med_b = A['detection_summary']['person_count_median'], B['detection_summary']['person_count_median']
    person_sim = 1.0 - abs(med_a - med_b) / max(med_a, med_b, 1.0)
    temporal = _corr01(ca['count'], cb['count'])
    motion_corr = _corr01(ca['activity'], cb['activity'])
    motion = None
    if motion_corr is not None:
        pa, pb = int(np.argmax(ca['activity'])) / (bins - 1), int(np.argmax(cb['activity'])) / (bins - 1)
        motion = 0.5 * motion_corr + 0.5 * (1.0 - abs(pa - pb))
    def first_transition_phase(cam):
        span = max(cam['sampling']['timestamps_sec'][-1], 1e-6)
        ts = [t['vertical_transition']['transition_start_sec'] for t in cam['tracks'] if t['vertical_transition']['upright_to_low_transition']]
        return min(ts) / span if ts else None
    ta, tb = first_transition_phase(A), first_transition_phase(B)
    posture_sim = None if ta is None and tb is None else (0.0 if ta is None or tb is None else 1.0 - abs(ta - tb))
    sa, sb = np.asarray(_signature(A)), np.asarray(_signature(B))
    sig = float(sa @ sb / (np.linalg.norm(sa) * np.linalg.norm(sb))) if np.linalg.norm(sa) > 0 and np.linalg.norm(sb) > 0 else None

    def low_bins(c, med):
        thr = 0.5 * max(med, 1.0)
        return [c['has_frames'][i] and c['count'][i] < thr for i in range(bins)]
    la, lb = low_bins(ca, med_a), low_bins(cb, med_b)
    def drop(c, low, med):
        seen_ok = False
        for i in range(bins):
            if c['has_frames'][i] and c['count'][i] >= max(med, 1.0):
                seen_ok = True
            elif seen_ok and low[i]:
                return True
        return False
    a_drop, b_drop = drop(ca, la, med_a), drop(cb, lb, med_b)
    b_during_a_low = [i for i in range(bins) if la[i] and cb['count'][i] >= 1.0]
    a_during_b_low = [i for i in range(bins) if lb[i] and ca['count'][i] >= 1.0]
    low_any = [i for i in range(bins) if la[i] or lb[i]]
    complement = (len(set(b_during_a_low) | set(a_during_b_low)) / len(low_any)) if low_any else 0.0
    parts = {'person_count_similarity': (person_sim, 0.2), 'temporal_pattern_similarity': (temporal, 0.2),
             'motion_peak_similarity': (motion, 0.2), 'incident_signature_similarity': (sig, 0.3),
             'posture_transition_similarity': (posture_sim, 0.1)}
    avail = {k: v for k, v in parts.items() if v[0] is not None}
    same = sum(v * w for v, w in avail.values()) / sum(w for _, w in avail.values()) if avail else None
    phase = lambda idx: [[rnd(i / bins), rnd((i + 1) / bins)] for i in idx]
    return {
        'camera_a': A['camera_id'], 'camera_b': B['camera_id'],
        'alignment': 'each clip mapped to normalized phase 0..1; coarse comparison only, no absolute timestamp matching',
        'phase_bins': bins,
        'person_count_similarity': rnd(person_sim),
        'temporal_pattern_similarity': rnd(temporal),
        'motion_peak_similarity': rnd(motion),
        'posture_transition_similarity': rnd(posture_sim),
        'incident_signature_similarity': rnd(sig),
        'incident_signature_vectors': {A['camera_id']: [rnd(x) for x in sa], B['camera_id']: [rnd(x) for x in sb]},
        'incident_signature_fields': ['max_person_count/5', 'max_close_proximity_fraction', 'max_relative_motion_when_close',
                                      'max_contact_proxy', 'any_upright_to_low_transition', 'max_low_or_horizontal_fraction'],
        'phase_curves': {A['camera_id']: {k: [rnd(x) for x in v] for k, v in ca.items() if k != 'has_frames'},
                         B['camera_id']: {k: [rnd(x) for x in v] for k, v in cb.items() if k != 'has_frames'}},
        'visibility_complementarity_score': rnd(complement),
        'camera_a_visibility_drop': a_drop,
        'camera_b_visibility_drop': b_drop,
        'camera_b_has_observations_during_a_low_visibility_phase': bool(b_during_a_low),
        'camera_a_has_observations_during_b_low_visibility_phase': bool(a_during_b_low),
        'camera_a_low_visibility_phases': phase([i for i in range(bins) if la[i]]),
        'camera_b_low_visibility_phases': phase([i for i in range(bins) if lb[i]]),
        'same_incident_similarity_score': rnd(same),
        'same_incident_similarity_note': 'observation-pattern similarity only; not ground truth',
        'identity_link_confirmed': False,
        'sync_confirmed': False,
    }
