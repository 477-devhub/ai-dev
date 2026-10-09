"""Local-only, single-worker MVP server. Start playback explicitly after UI connects."""
import asyncio
import base64
import contextlib
import json
import os
import statistics
import sys
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from .state import Ledger
from .ai import Analysis

ROOT = Path(__file__).resolve().parents[1]


def summary(values):
    if not values:
        return None
    values = sorted(values)
    return {'count': len(values), 'mean': statistics.mean(values), 'p50': statistics.median(values),
            'p95': values[min(len(values)-1, int(len(values)*.95))], 'max': max(values)}


class Runtime:
    def __init__(self, cfg=None, output=None):
        self.cfg = cfg or json.loads((ROOT/'runtime477/config.json').read_text())
        self.cfg = dict(self.cfg)
        if os.getenv('RUNTIME_AI') == '1':
            self.cfg['ai_enabled'] = True
        if os.getenv('RUNTIME_MAX_AI_JOBS'):
            self.cfg['max_ai_jobs'] = int(os.environ['RUNTIME_MAX_AI_JOBS'])
        self.instance = uuid4().hex
        self.output = Path(output or ROOT/'runtime477/runs'/self.instance)
        self.ledger = Ledger(self.cfg, self.output)
        self.cv_python = os.getenv('RUNTIME_CV_PYTHON', str(ROOT/'experiments/p0_cv_only/.venv/Scripts/python.exe'))
        self.ai_python = os.getenv('RUNTIME_AI_PYTHON', str(ROOT.parent/'477-backend/.venv/Scripts/python.exe'))
        self.cameras = {f'CAM_{i:02}': {'camera_id': f'CAM_{i:02}', 'state': 'IDLE', 'pts': 0,
            'path': str(ROOT/f'data/mock_cctv/playback/CAM_{i:02}.mp4'),
            'original_path': str(ROOT/f'data/mock_cctv/media/CAM_{i:02}.mp4'), 'sampled': 0} for i in range(1, 10)}
        self.frames = {}
        self.epoch = None
        self.proc = None
        self.reader = self.monitor = None
        self.phase = 'IDLE'
        self.start_lock = asyncio.Lock()
        self.metrics = {'batch_ms': [], 'frame_to_observation_ms': [], 'decode_lag_ms': [],
                        'cpu_percent': [], 'gpu_percent': [], 'gpu_memory_mb': []}
        self.gpu_peak_allocated_mb = None
        self.analysis = Analysis(self)
        self.recorded = []
        if self.cfg['mode'] == 'RECORDED_RESULT_DEMO_MODE':
            self.recorded = json.loads(Path(self.cfg['recorded_results']).read_text(encoding='utf-8'))
            self.cfg['ai_enabled'] = False
        elif self.cfg['mode'] != 'LIVE_REPLAY_MODE':
            raise ValueError('unsupported_mode')

    async def start(self):
        async with self.start_lock:
            if self.phase != 'IDLE':
                return
            self.phase = 'WARMING_UP'
            payload = dict(self.cfg, cameras=list(self.cameras.values()))
            path = self.output/'run_config.json'
            path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
            self.analysis.start()
            self.monitor = asyncio.create_task(self.resources())
            log = (self.output/'cv-worker.log').open('wb')
            try:
                self.proc = await asyncio.create_subprocess_exec(self.cv_python, str(ROOT/'runtime477/stream_worker.py'),
                    str(path), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=log,
                    limit=4*1024*1024, cwd=str(ROOT))
            except Exception:
                self.phase = 'ERROR'
                raise
            finally:
                log.close()
            self.reader = asyncio.create_task(self.read_worker())

    async def read_worker(self):
        try:
            while line := await self.proc.stdout.readline():
                msg = json.loads(line)
                kind = msg['type']
                cid = msg.get('camera_id')
                if kind == 'ready':
                    self.ledger.audit('worker_ready', msg)
                    self.proc.stdin.write(b'start\n')
                    await self.proc.stdin.drain()
                elif kind == 'epoch':
                    self.epoch = msg['epoch']
                    self.phase = 'PLAYING'
                    self.ledger.audit('replay_epoch', msg)
                elif kind == 'frame':
                    self.frames[cid] = base64.b64decode(msg.pop('jpg'))
                    self.cameras[cid].update(msg, state='PLAYING')
                    self.metrics['decode_lag_ms'].append(msg['lag_ms'])
                elif kind == 'observation':
                    self.cameras[cid]['sampled'] += 1
                    self.metrics['batch_ms'].append(msg['batch_ms'])
                    self.metrics['frame_to_observation_ms'].append((msg['t1']-self.epoch-msg['pts'])*1000)
                    self.gpu_peak_allocated_mb = msg['gpu_peak_allocated_mb']
                    for signal in msg['reasons']:
                        candidate, created = self.ledger.detect(msg, signal, self.frames.get(cid))
                        if created:
                            if self.cfg['mode'] == 'RECORDED_RESULT_DEMO_MODE':
                                match = next((r for r in self.recorded if r['camera_id'] == cid and
                                    r['start_pts'] <= msg['pts'] <= r['end_pts']), None)
                                self.ledger.update(candidate['candidate_id'], status='REQUIRES_REVIEW',
                                    ai_source='recorded', job_status='recorded_result' if match else 'recorded_missing',
                                    recorded_result=match, error=None if match else 'NO_RECORDED_RESULT')
                            else:
                                self.analysis.submit(candidate)
                    self.ledger.audit('observation', msg)
                elif kind in ('camera_end', 'camera_error'):
                    self.cameras[cid].update(msg, state='ENDED' if kind == 'camera_end' else 'ERROR')
                    self.ledger.audit(kind, msg)
                elif kind == 'finished':
                    self.phase = 'FINISHED'
                    self.ledger.audit(kind, msg)
                self.save_metrics_if_finished()
            code = await self.proc.wait()
            if code or self.phase != 'FINISHED':
                self.phase = 'ERROR'
                self.ledger.audit('stream_worker_failed', {'exit_code': code})
        except asyncio.CancelledError:
            raise
        except Exception:
            self.phase = 'ERROR'
            self.ledger.audit('stream_reader_failed', {})

    async def resources(self):
        import psutil
        psutil.cpu_percent()
        while True:
            self.metrics['cpu_percent'].append(psutil.cpu_percent())
            try:
                proc = await asyncio.create_subprocess_exec('nvidia-smi', '--query-gpu=utilization.gpu,memory.used',
                    '--format=csv,noheader,nounits', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
                raw, _ = await asyncio.wait_for(proc.communicate(), 3)
                gpu, memory = [float(v.strip()) for v in raw.decode().splitlines()[0].split(',')]
                self.metrics['gpu_percent'].append(gpu)
                self.metrics['gpu_memory_mb'].append(memory)
            except Exception:
                if 'proc' in locals() and proc.returncode is None:
                    proc.kill()
                    await proc.wait()
            terminal = {'completed', 'completed_p1_shadow', 'disabled', 'rejected', 'failed', 'cancelled'}
            if self.phase == 'FINISHED' and all(c['job_status'] in terminal for c in self.ledger.candidates.values()):
                return
            await asyncio.sleep(1)

    def report(self):
        candidates = list(self.ledger.candidates.values())
        displayed = [c for c in candidates if c['t3'] is not None]
        elapsed = max((c.get('elapsed', c.get('pts', 0)) for c in self.cameras.values()), default=0)
        return {'instance': self.instance, 'mode': self.cfg['mode'], 'phase': self.phase,
            'time_to_first_alert_ms': None, 't0_annotation': 'NOT ANNOTATED; detector first seen is not human T0',
            'candidate_to_frontend_ms': summary([(c['t3']-c['t1'])*1000 for c in displayed]),
            'backend_to_frontend_ms': summary([(c['t3']-c['t2'])*1000 for c in displayed]),
            't3_clock_uncertainty_ms': summary([c['clock_uncertainty_ms'] for c in displayed]),
            'fast_cv_batch_ms_per_sample': summary(self.metrics['batch_ms']),
            'frame_to_observation_ms': summary(self.metrics['frame_to_observation_ms']),
            'decode_lag_ms': summary(self.metrics['decode_lag_ms']),
            'effective_decode_fps_aggregate': sum(c.get('decoded', 0) for c in self.cameras.values())/elapsed if elapsed else None,
            'effective_cv_fps_aggregate': sum(c['sampled'] for c in self.cameras.values())/elapsed if elapsed else None,
            'late_decode_rate': sum(c.get('late_frames', 0) for c in self.cameras.values())/max(1, sum(c.get('decoded', 0) for c in self.cameras.values())),
            'frame_drop_rate': (sum(max(0, c['expected_frames']-c.get('decoded', 0)) for c in self.cameras.values()) /
                max(1, sum(c['expected_frames'] for c in self.cameras.values())))
                if all('expected_frames' in c for c in self.cameras.values()) else None,
            'drop_note': 'Completed decoded count vs container frame count; intentional CV/display subsampling is excluded.',
            'cpu_utilization_percent': summary(self.metrics['cpu_percent']),
            'gpu_utilization_percent': summary(self.metrics['gpu_percent']),
            'gpu_memory_mb': summary(self.metrics['gpu_memory_mb']),
            'gpu_peak_allocated_mb': self.gpu_peak_allocated_mb,
            'ai': {k: summary(v) for k, v in self.analysis.metrics.items()},
            'queue': {'p1': self.analysis.p1.qsize(), 'p4': self.analysis.p4.qsize(), 'peak': self.analysis.peak},
            'candidates': len(candidates), 'frontend_displayed': len(displayed),
            'deduplication_rate': self.ledger.merges/max(1, self.ledger.triggers),
            'capacity_rejections': self.ledger.capacity_rejections,
            'cameras': [{k: v for k, v in c.items() if not k.endswith('path')} for c in self.cameras.values()]}

    def save_metrics_if_finished(self):
        if self.phase == 'FINISHED':
            (self.output/'metrics.json').write_text(json.dumps(self.report(), indent=2), encoding='utf-8')

    def snapshot(self):
        return {'instance': self.instance, 'revision': self.ledger.revision, 'phase': self.phase,
                'epoch': self.epoch, 'mode': self.cfg['mode'], 'ai_enabled': self.cfg['ai_enabled'],
                'cameras': [{k: v for k, v in c.items() if not k.endswith('path')} for c in self.cameras.values()],
                'candidates': self.ledger.snapshot(), 'queue': self.report()['queue'],
                'frames': {cid: base64.b64encode(jpg).decode() for cid, jpg in self.frames.items()}}

    async def close(self):
        if self.proc and self.proc.returncode is None:
            self.proc.kill()
            await self.proc.wait()
        for task in (self.reader, self.monitor):
            if task:
                task.cancel()
        await asyncio.gather(*(t for t in (self.reader, self.monitor) if t), return_exceptions=True)
        await self.analysis.close()
        (self.output/'metrics.json').write_text(json.dumps(self.report(), indent=2), encoding='utf-8')


class DisplayAck(BaseModel):
    t3_server_epoch: float = Field(gt=0, allow_inf_nan=False)
    clock_uncertainty_ms: float = Field(ge=0, le=10000, allow_inf_nan=False)


class HumanAck(BaseModel):
    action: str = Field(pattern='^(reviewed|dismissed|requires_review)$')


def create_app(runtime=None):
    rt = runtime or Runtime()
    @contextlib.asynccontextmanager
    async def lifespan(app):
        yield
        await rt.close()
    app = FastAPI(lifespan=lifespan)
    app.state.runtime = rt

    @app.get('/')
    async def index():
        return FileResponse(ROOT/'runtime477/ui.html')

    @app.get('/api/time')
    async def clock():
        return {'epoch': time.time()}

    @app.post('/api/start')
    async def start():
        await rt.start()
        return {'instance': rt.instance, 'phase': rt.phase}

    @app.get('/api/snapshot')
    async def snapshot():
        return rt.snapshot()

    @app.get('/api/metrics')
    async def metrics():
        return rt.report()

    @app.get('/stream/{camera}')
    async def stream(camera: str):
        if camera not in rt.cameras:
            raise HTTPException(404)
        async def frames():
            previous = None
            while True:
                jpg = rt.frames.get(camera)
                if jpg and jpg is not previous:
                    previous = jpg
                    yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'+jpg+b'\r\n'
                await asyncio.sleep(.1)
        return StreamingResponse(frames(), media_type='multipart/x-mixed-replace; boundary=frame')

    @app.get('/original/{camera}')
    async def original(camera: str):
        if camera not in rt.cameras:
            raise HTTPException(404)
        return FileResponse(rt.cameras[camera]['original_path'], media_type='video/mp4')

    @app.get('/evidence/{cid}/{frame}')
    async def evidence(cid: str, frame: str):
        if cid not in rt.ledger.candidates:
            raise HTTPException(404)
        allowed = {'preview': rt.output/(cid+'.jpg')}
        allowed.update({f'F{i:03d}': rt.output/(cid+f'_F{i:03d}.webp') for i in range(1, 65)})
        if frame not in allowed or not allowed[frame].is_file():
            raise HTTPException(404)
        return FileResponse(allowed[frame])

    @app.post('/api/candidates/{cid}/displayed')
    async def displayed(cid: str, ack: DisplayAck):
        c = rt.ledger.candidates.get(cid)
        if c is None:
            raise HTTPException(404)
        if not c['t2'] <= ack.t3_server_epoch <= time.time()+ack.clock_uncertainty_ms/1000:
            raise HTTPException(422, 'invalid_display_clock')
        if c['t3'] is None:
            rt.ledger.update(cid, t3=ack.t3_server_epoch, clock_uncertainty_ms=ack.clock_uncertainty_ms)
            rt.save_metrics_if_finished()
        return {'ok': True}

    @app.post('/api/candidates/{cid}/human')
    async def human(cid: str, ack: HumanAck):
        if cid not in rt.ledger.candidates:
            raise HTTPException(404)
        rt.ledger.human(cid, ack.action)
        return rt.snapshot()

    @app.websocket('/ws')
    async def events(ws: WebSocket):
        await ws.accept()
        queue = asyncio.Queue(1)
        rt.ledger.subscribers.add(queue)
        try:
            while True:
                await ws.send_json(rt.snapshot())
                try:
                    await asyncio.wait_for(queue.get(), .1)
                except TimeoutError:
                    pass
                await asyncio.sleep(.05)
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            rt.ledger.subscribers.discard(queue)
    return app


app = create_app()
