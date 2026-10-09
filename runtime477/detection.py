"""Observable proxies only. No event semantics, intent, medical or crime labels."""
from collections import defaultdict
import cv2
import numpy as np


class Signals:
    def __init__(self, config):
        self.cfg = config
        self.previous = {}
        self.counts = defaultdict(int)

    def observe(self, camera, frame, boxes):
        gray = cv2.cvtColor(cv2.resize(frame, (160, 90)), cv2.COLOR_BGR2GRAY)
        previous = self.previous.get(camera)
        self.previous[camera] = gray
        motion = float(np.mean(cv2.absdiff(gray, previous) > self.cfg['motion_pixel_delta'])) if previous is not None else 0.0
        h, w = frame.shape[:2]
        observations = []
        if motion >= self.cfg['motion_fraction']:
            observations.append(('MOTION_CHANGE', 'scene'))
        for x1, y1, x2, y2 in boxes:
            if (x2-x1) / max(1, y2-y1) >= self.cfg['horizontal_ratio']:
                # Coarse spatial identity allows simultaneous independent candidates.
                zone = f'{min(2, int((x1+x2)/2/w*3))}:{min(2, int((y1+y2)/2/h*3))}'
                observations.append(('HORIZONTAL_PERSON_PROXY', zone))
        keys = set(observations)
        for key in list(self.counts):
            if key[0] == camera and key[1:] not in keys:
                self.counts[key] = 0
        triggered = []
        for reason, zone in keys:
            key = (camera, reason, zone)
            self.counts[key] += 1
            if self.counts[key] >= self.cfg['sustain_samples']:
                triggered.append({'reason': reason, 'zone': zone})
        return triggered, {'motion_fraction': motion, 'person_count': len(boxes)}
