"""Bounded stage queues using the existing frozen adapters and execution boundary.

P4 stays native-resolution, uniform 64 frames. Preparation only uses the already
observed source interval; it never inspects future replay frames.
"""
import asyncio
import os
import sys
import time
import json
from uuid import uuid4
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = Path(os.environ.get('RUNTIME_BACKEND_ROOT', str(ROOT.parent/'477-backend')))
sys.path.insert(0, str(BACKEND))


class Analysis:
    def __init__(self, runtime):
        self.rt = runtime
        self.p1 = asyncio.Queue(runtime.cfg['queue_size'])
        self.p4 = asyncio.Queue(runtime.cfg['queue_size'])
        self.tasks = []
        self.submitted = set()
        self.peak = {'p1': 0, 'p4': 0}
        self.metrics = {'prepare_ms': [], 'full_cv_ms': [], 'p1_api_ms': [], 'p4_api_ms': []}

    def start(self):
        self.tasks = [asyncio.create_task(self.worker('p1')), asyncio.create_task(self.worker('p4'))]

    def submit(self, candidate):
        cid = candidate['candidate_id']
        if cid in self.submitted:
            return
        self.submitted.add(cid)
        if not self.rt.cfg['ai_enabled']:
            self.rt.ledger.update(cid, status='REQUIRES_REVIEW', error='AI_DISABLED', job_status='disabled')
            return
        if len(self.submitted) > self.rt.cfg['max_ai_jobs'] or self.p1.full():
            self.rt.ledger.update(cid, status='REQUIRES_REVIEW', error='QUEUE_BACKPRESSURE', job_status='rejected', ai_source='not_called')
            return
        self.rt.ledger.update(cid, status='SCREENING', job_status='queued_p1', ai_source='live')
        self.p1.put_nowait((cid, candidate['generation'], None))
        self.peak['p1'] = max(self.peak['p1'], self.p1.qsize())

    async def stage(self, stage, payload):
        from app.models.adapters.cascade_media import run_worker
        started = time.perf_counter()
        artifact = self.rt.output/(stage+'_'+uuid4().hex)
        if stage == 'p1':
            await asyncio.to_thread(artifact.with_suffix('.input.json').write_text, json.dumps(payload), encoding='utf-8')
        python = self.rt.cv_python if stage == 'cv' else self.rt.ai_python
        if stage == 'prepare':
            from .media import prepare
            result = await prepare(payload['path'], payload['end_ms'], python, self.rt.cfg['ai_timeout_sec'])
        else:
            result = await run_worker(stage, dict(payload, max_retries=0), python_executable=python,
                                      timeout_sec=self.rt.cfg['ai_timeout_sec'])
        duration = (time.perf_counter()-started)*1000
        await asyncio.to_thread(artifact.with_suffix('.result.json').write_text,
            json.dumps({k: v for k, v in result.items() if k != '_assets'}, ensure_ascii=False), encoding='utf-8')
        self.rt.ledger.audit('stage_finished', {'stage': stage, 'status': result.get('status', 'ok'),
            'wrapper_ms': duration, 'error_type': result.get('error_type'), 'error_code': result.get('error_code')})
        if result.get('status', 'ok') != 'ok':
            raise ValueError(stage+'_failed')
        if stage in ('p1', 'p4'):
            # Existing client latency is provider-call time; wrapper duration is separate.
            latency = result.get('timing', {}).get('total_including_retries_ms')
            if latency is not None:
                self.metrics[stage+'_api_ms'].append(latency)
        else:
            self.metrics['full_cv_ms' if stage == 'cv' else 'prepare_ms'].append(duration)
        return result, duration

    async def model(self, stage, payload, model_input):
        from app.models.base import ModelAdapter
        from app.models.execution import execute
        from app.models.adapters.assessment_mapper import decision_from_answers, guards, map_decision, visual_decision
        from app.schemas.model import ModelAssessment, ModelMetadata, StageRecord
        owner = self
        class StageAdapter(ModelAdapter):
            name = 'cascade_v1'
            raw = None
            decision = None
            async def evaluate(self, mi):
                result, duration = await owner.stage(stage, payload)
                self.raw = result
                trace = [StageRecord(stage=stage, status='ok', latency_ms=duration, attempts=1)]
                if stage == 'p1':
                    self.decision = decision_from_answers(result['answers'])
                    if all(guards(self.decision)):
                        return map_decision(self.decision, mode='frozen_cascade_v1', stage='p1', trace=trace)
                    return ModelAssessment(event_type='uncertain', event_confidence=0, risk_axes=None, needs_human_review=True,
                        evidence_refs=[], metadata=ModelMetadata(adapter=self.name, model='gpt-6-luna', stage_trace=trace))
                decision, visual = visual_decision(result['parsed'], payload['frames'])
                self.decision = decision
                return map_decision(decision, mode='shadow', stage='p4', trace=trace, visual=visual)
        adapter = StageAdapter()
        assessment = await execute(adapter, model_input, self.rt.cfg['ai_timeout_sec']+5)
        return assessment, adapter

    async def worker(self, stage):
        queue = getattr(self, stage)
        while True:
            cid, generation, prepared = await queue.get()
            try:
                c = self.rt.ledger.candidates[cid]
                if c['generation'] != generation or c['human_disposition']:
                    continue
                if stage == 'p1':
                    await asyncio.sleep(self.rt.cfg['post_roll_sec'])
                    camera = self.rt.cameras[c['camera_id']]
                    end = camera.get('pts', c['last_pts'])
                    if end < 3:
                        raise ValueError('insufficient_temporal_evidence')
                    # Preserve 64/native frame protocol, use observed history to include onset.
                    self.rt.ledger.update(cid, generation, job_status='preparing')
                    source = Path(camera['original_path'])
                    record, _ = await self.stage('prepare', {'path': str(source), 'end_ms': int(end*1000)})
                    frames = [{'ref': f['ref'], 'camera': 'CAM_01', 'timestamp_sec': f['timestamp_ms']/1000}
                              for f in record['frames']]
                    assets = {ref+'.webp': blob for ref, blob in record['_assets'].items()}
                    payload = {'frames': frames, 'frame_numbers': record['frame_numbers'], '_assets': assets,
                               'weights_path': str(ROOT/'experiments/p0_cv_only/models/yolo26n-pose.pt')}
                    for ref, blob in assets.items():
                        await asyncio.to_thread((self.rt.output/(cid+'_'+ref)).write_bytes, blob)
                    self.rt.ledger.update(cid, generation, job_status='full_cv_background')
                    cv, _ = await self.stage('cv', payload)
                    if c['generation'] != generation or c['human_disposition']:
                        continue
                    from app.schemas.model import ModelInput, CameraContext, TimeWindow, EvidenceFrame
                    mi = ModelInput(sample_id=cid, camera=CameraContext(id=c['camera_id']),
                        window=TimeWindow(start_ms=0, end_ms=int(end*1000)),
                        evidence=[EvidenceFrame(frame_id=f['ref'], timestamp_ms=f['timestamp_ms'], media_ref=f['ref'])
                                  for f in record['frames']])
                    self.rt.ledger.update(cid, generation, job_status='running_p1')
                    assessment, adapter = await self.model('p1', {'state': cv['state']}, mi)
                    if assessment.metadata.error_code:
                        raise ValueError('p1_failed')
                    normal = assessment.event_type == 'normal'
                    contract = {'schema_version': '1.0', 'candidate_id': cid, 'camera_id': c['camera_id'],
                                'decision': 'NORMAL' if normal else 'SUSPICIOUS',
                                'action': 'SUPPRESS' if normal else 'ESCALATE_P4',
                                'reason_codes': c['reason_codes'], 'router_version': 'runtime-shadow-v1'}
                    accepted = self.rt.ledger.update(cid, generation, t4=time.time(), stage1=contract,
                        status='AI_NORMAL_ESTIMATE' if normal else 'ANALYZING',
                        job_status='completed_p1_shadow' if normal else 'queued_p4',
                        suppression_applied=False, assessment=assessment.model_dump(mode='json'))
                    if not accepted or normal:
                        continue
                    if self.p4.full():
                        raise ValueError('p4_backpressure')
                    self.p4.put_nowait((cid, generation, (payload, mi)))
                    self.peak['p4'] = max(self.peak['p4'], self.p4.qsize())
                else:
                    payload, mi = prepared
                    self.rt.ledger.update(cid, generation, job_status='running_p4')
                    assessment, adapter = await self.model('p4', payload, mi)
                    if assessment.metadata.error_code:
                        raise ValueError('p4_failed')
                    from app.models.adapters.frozen_v1.common_adapter_v2 import CommonAdapterV2
                    normalized = CommonAdapterV2().reconcile(adapter.decision)['normalized_decision']
                    status = ('AI_DANGER_ESTIMATE' if normalized['is_incident'] else
                              'AI_NORMAL_ESTIMATE' if not assessment.needs_human_review else 'REQUIRES_REVIEW')
                    self.rt.ledger.update(cid, generation, t5=time.time(), status=status, job_status='completed',
                                          assessment=assessment.model_dump(mode='json'))
            except asyncio.CancelledError:
                self.rt.ledger.update(cid, generation, status='REQUIRES_REVIEW', error='JOB_CANCELLED', job_status='cancelled')
                raise
            except Exception:
                self.rt.ledger.update(cid, generation, status='REQUIRES_REVIEW', error=stage.upper()+'_FAILED', job_status='failed')
            finally:
                queue.task_done()
                if hasattr(self.rt, 'save_metrics_if_finished'):
                    self.rt.save_metrics_if_finished()

    async def close(self):
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        for queue in (self.p1, self.p4):
            while not queue.empty():
                cid, gen, _ = queue.get_nowait()
                self.rt.ledger.update(cid, gen, status='REQUIRES_REVIEW', error='JOB_CANCELLED', job_status='cancelled')
                queue.task_done()
