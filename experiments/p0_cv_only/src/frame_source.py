"""Canonical frame source: thin, audited wrapper around benchmark_v1/scripts/load_model_input.py.

Only the official uniform_total64_v1 frames produced by iter_model_frames() are used.
No extra sampling, no direct MP4 access, no private paths.
"""
import hashlib
import sys

import numpy as np

from utils import BENCH_ROOT

sys.path.insert(0, str(BENCH_ROOT / 'scripts'))
import load_model_input as lmi  # noqa: E402  (official public loader)

TOTAL_FRAMES = 64
PROTOCOL = 'uniform_total64_v1'


class CanonicalFrameSource:
    def __init__(self, item_id):
        self.item_id = item_id
        self.item = lmi.load_item(item_id)
        self.task = self.item['task']
        self.benchmark_fingerprint = self.item['input_fingerprint']
        if self.benchmark_fingerprint['sampling_protocol_id'] != PROTOCOL:
            raise ValueError('Unexpected sampling protocol')
        self.cameras = [h['camera'] for h in self.item['media_handles_private_to_harness']]
        self.expected = {h['camera']: list(h['frame_timestamps_sec']) for h in self.item['media_handles_private_to_harness']}
        self.frame_numbers = {h['camera']: list(h['frame_numbers']) for h in self.item['media_handles_private_to_harness']}
        if sum(len(v) for v in self.expected.values()) != TOTAL_FRAMES:
            raise ValueError('Canonical allocation is not 64 frames')
        self.audit = {'frames_consumed': 0, 'per_camera': {c: 0 for c in self.cameras}}
        self.fingerprints = {}

    def iter_frames(self):
        """Yield (camera, index_in_camera, timestamp_sec, rgb ndarray HxWx3) for exactly the canonical frames."""
        hashers = {c: hashlib.sha256() for c in self.cameras}
        for frame in lmi.iter_model_frames(self.item_id):
            cam = frame['camera']
            idx = self.audit['per_camera'][cam]
            if idx >= len(self.expected[cam]) or abs(frame['timestamp_sec'] - self.expected[cam][idx]) > 1e-9:
                raise RuntimeError('Frame stream deviates from canonical schedule')
            hashers[cam].update(frame['rgb24'])
            self.audit['per_camera'][cam] += 1
            self.audit['frames_consumed'] += 1
            rgb = np.frombuffer(frame['rgb24'], dtype=np.uint8).reshape(frame['height'], frame['width'], 3)
            yield cam, idx, frame['timestamp_sec'], rgb
        for cam in self.cameras:
            if self.audit['per_camera'][cam] != len(self.expected[cam]):
                raise RuntimeError('Missing canonical frames for ' + cam)
        if self.audit['frames_consumed'] != TOTAL_FRAMES:
            raise RuntimeError('Frame budget violated')
        self.fingerprints = {c: hashers[c].hexdigest() for c in self.cameras}

    def item_frame_fingerprint(self):
        h = hashlib.sha256()
        for cam in self.cameras:
            h.update(cam.encode())
            h.update(self.fingerprints[cam].encode())
        return h.hexdigest()
