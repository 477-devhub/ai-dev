import asyncio
import json
import time
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from runtime477.state import Ledger
from runtime477.detection import Signals
from runtime477.ai import Analysis

CFG = json.loads((Path(__file__).parents[1]/'config.json').read_text())


def observation(pts=1, camera='CAM_01'):
    return dict(camera_id=camera, pts=pts, t1=time.time(), observations={'motion_fraction': .2})


def test_dedup_independent_signals_and_temporal_gap(tmp_path):
    ledger = Ledger(CFG, tmp_path)
    a, new = ledger.detect(observation(), {'reason': 'MOTION_CHANGE', 'zone': 'scene'})
    same, new2 = ledger.detect(observation(2), {'reason': 'MOTION_CHANGE', 'zone': 'scene'})
    separate, _ = ledger.detect(observation(2), {'reason': 'HORIZONTAL_PERSON_PROXY', 'zone': '0:0'})
    next_event, _ = ledger.detect(observation(8), {'reason': 'MOTION_CHANGE', 'zone': 'scene'})
    assert new and not new2 and a['candidate_id'] == same['candidate_id']
    assert len({a['candidate_id'], separate['candidate_id'], next_event['candidate_id']}) == 3
    assert a['first_seen_pts'] == 1 and a['last_pts'] == 2


def test_human_decision_and_generation_win(tmp_path):
    ledger = Ledger(CFG, tmp_path)
    c, _ = ledger.detect(observation(), {'reason': 'x', 'zone': 'scene'})
    ledger.human(c['candidate_id'], 'dismissed')
    assert not ledger.update(c['candidate_id'], 0, status='AI_DANGER_ESTIMATE')
    assert not ledger.update(c['candidate_id'], 1, status='AI_DANGER_ESTIMATE')
    assert c['human_disposition'] == 'dismissed'
    assert 'stale_ai_result' in (tmp_path/'audit.jsonl').read_text()


def test_real_pixels_sustain_and_camera_isolation():
    signals = Signals(CFG)
    black = np.zeros((360, 640, 3), np.uint8)
    white = np.full_like(black, 255)
    assert signals.observe('a', black, [])[0] == []
    # Use the configured sustain threshold rather than an old two-sample default.
    for sample in range(CFG['sustain_samples'] - 1):
        assert signals.observe('a', white if sample % 2 == 0 else black, [])[0] == []
    last_frame = white if CFG['sustain_samples'] % 2 else black
    triggered, _ = signals.observe('a', last_frame, [])
    assert triggered == [{'reason': 'MOTION_CHANGE', 'zone': 'scene'}]
    assert signals.observe('b', white, [])[0] == []
    assert signals.observe('a', last_frame, [])[0] == []


def test_queue_capacity_and_duplicate_requests(tmp_path):
    cfg = dict(CFG, ai_enabled=True, queue_size=1, max_ai_jobs=100)
    rt = SimpleNamespace(cfg=cfg, ledger=Ledger(cfg, tmp_path))
    analysis = Analysis(rt)
    a, _ = rt.ledger.detect(observation(), {'reason': 'a', 'zone': 'scene'})
    b, _ = rt.ledger.detect(observation(camera='CAM_02'), {'reason': 'a', 'zone': 'scene'})
    analysis.submit(a)
    analysis.submit(a)
    analysis.submit(b)
    assert analysis.p1.qsize() == 1
    assert b['status'] == 'REQUIRES_REVIEW' and b['error'] == 'QUEUE_BACKPRESSURE'


def test_p1_failure_preserves_candidate(tmp_path):
    async def run():
        cfg = dict(CFG, ai_enabled=True, post_roll_sec=0)
        rt = SimpleNamespace(cfg=cfg, ledger=Ledger(cfg, tmp_path), cameras={'CAM_01': {'pts': 1}})
        analysis = Analysis(rt)
        analysis.start()
        c, _ = rt.ledger.detect(observation(), {'reason': 'a', 'zone': 'scene'})
        analysis.submit(c)
        await asyncio.wait_for(analysis.p1.join(), 2)
        assert c['status'] == 'REQUIRES_REVIEW' and c['error'] == 'P1_FAILED'
        await analysis.close()
    asyncio.run(run())


def test_slow_failed_p4_does_not_block_new_candidate(tmp_path):
    async def run():
        cfg = dict(CFG, ai_enabled=True)
        rt = SimpleNamespace(cfg=cfg, ledger=Ledger(cfg, tmp_path))
        analysis = Analysis(rt)
        async def fail(*args):
            await asyncio.sleep(.05)
            raise TimeoutError()
        analysis.model = fail
        c, _ = rt.ledger.detect(observation(), {'reason': 'a', 'zone': 'scene'})
        analysis.p4.put_nowait((c['candidate_id'], 0, ({}, None)))
        worker = asyncio.create_task(analysis.worker('p4'))
        await asyncio.sleep(.01)
        other, created = rt.ledger.detect(observation(camera='CAM_02'), {'reason': 'a', 'zone': 'scene'})
        assert created and other['status'] == 'DETECTED'
        await asyncio.wait_for(analysis.p4.join(), 1)
        assert c['status'] == 'REQUIRES_REVIEW' and c['error'] == 'P4_FAILED'
        worker.cancel()
        await asyncio.gather(worker, return_exceptions=True)
    asyncio.run(run())


def test_capacity_never_silently_evicts(tmp_path):
    ledger = Ledger(dict(CFG, max_candidates=1), tmp_path)
    c, _ = ledger.detect(observation(), {'reason': 'a', 'zone': 'scene'})
    rejected, new = ledger.detect(observation(camera='CAM_02'), {'reason': 'a', 'zone': 'scene'})
    assert rejected is None and not new and c['candidate_id'] in ledger.candidates
    assert ledger.capacity_rejections == 1


def test_existing_p1_response_passes_execution_schema(tmp_path):
    """Recorded response is a schema regression fixture, never a live latency result."""
    async def run():
        from app.schemas.model import ModelInput, CameraContext, TimeWindow, EvidenceFrame
        root = Path(__file__).resolve().parents[2]
        recorded = json.loads((root/'experiments/p1_decisions/raw_api/ITEM_01.json').read_text(encoding='utf-8'))
        rt = SimpleNamespace(cfg=CFG, ledger=Ledger(CFG, tmp_path))
        analysis = Analysis(rt)
        async def fixture_stage(*args):
            return {'answers': recorded['response']['answers']}, 1
        analysis.stage = fixture_stage
        mi = ModelInput(sample_id='test', camera=CameraContext(id='CAM_01'), window=TimeWindow(start_ms=0, end_ms=1000),
                        evidence=[EvidenceFrame(frame_id='F001', timestamp_ms=0, media_ref='F001')])
        assessment, adapter = await analysis.model('p1', {}, mi)
        assert assessment.metadata.error_code is None
        assert assessment.needs_human_review and adapter.raw is not None
    asyncio.run(run())
