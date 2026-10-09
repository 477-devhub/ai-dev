"""Event-loop-owned candidate ledger. AI updates cannot override human disposition."""
import copy
import json
import time
from pathlib import Path
from uuid import uuid4


class Ledger:
    def __init__(self, cfg, output):
        self.cfg = cfg
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.candidates = {}
        self.active = {}
        self.revision = 0
        self.triggers = self.merges = self.capacity_rejections = 0
        self.subscribers = set()

    def audit(self, kind, payload):
        self.revision += 1
        with (self.output/'audit.jsonl').open('a', encoding='utf-8') as handle:
            handle.write(json.dumps({'revision': self.revision, 'wall_time': time.time(),
                                     'kind': kind, 'data': payload}, ensure_ascii=False) + '\n')
        for queue in self.subscribers:
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(self.revision)

    def detect(self, observation, signal, jpeg=None):
        self.triggers += 1
        now = time.time()
        key = (observation['camera_id'], signal['reason'], signal['zone'])
        previous = self.candidates.get(self.active.get(key))
        if previous and observation['pts']-previous['last_pts'] <= self.cfg['merge_gap_sec']:
            previous.update(last_pts=observation['pts'], last_updated=now,
                            observations=observation['observations'], merge_count=previous['merge_count']+1)
            self.merges += 1
            self.audit('merged', previous)
            return previous, False
        if len(self.candidates) >= self.cfg['max_candidates']:
            self.capacity_rejections += 1
            self.audit('candidate_capacity_rejected', {'camera_id': key[0], 'reason': key[1]})
            return None, False
        cid = 'cand_' + uuid4().hex
        candidate = dict(candidate_id=cid, camera_id=key[0], reason_codes=[key[1]], zone=key[2],
                         status='DETECTED', human_disposition=None, generation=0,
                         first_seen_pts=observation['pts'], last_pts=observation['pts'],
                         t0=None, t1=observation['t1'], t2=now, t3=None, t4=None, t5=None,
                         last_updated=now, merge_count=0, stage1=None, job_status='not_submitted',
                         observations=observation['observations'], ai_source='disabled',
                         assessment=None, error=None)
        self.candidates[cid] = candidate
        self.active[key] = cid
        if jpeg:
            (self.output/(cid+'.jpg')).write_bytes(jpeg)
        self.audit('detected', candidate)
        return candidate, True

    def update(self, cid, expected_generation=None, **fields):
        candidate = self.candidates[cid]
        if expected_generation is not None and (expected_generation != candidate['generation'] or candidate['human_disposition']):
            self.audit('stale_ai_result', {'candidate_id': cid, 'result': fields})
            return False
        candidate.update(fields, last_updated=time.time())
        self.audit('updated', candidate)
        return True

    def human(self, cid, action):
        candidate = self.candidates[cid]
        if candidate['human_disposition'] == action:
            return
        self.update(cid, human_disposition=action, generation=candidate['generation']+1)

    def snapshot(self):
        return copy.deepcopy(list(self.candidates.values()))
