"""One resident YOLO model, nine independent paced decoders, latest-frame sampling.

stdout is bounded-by-pipe JSON IPC. Model diagnostics go to stderr.
"""
import base64
import contextlib
import json
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import cv2
from runtime477.detection import Signals


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    output = sys.stdout
    lock = threading.Lock()
    def emit(message):
        with lock:
            output.write(json.dumps(message, separators=(',', ':')) + '\n')
            output.flush()
    cv2.setNumThreads(1)
    started = time.perf_counter()
    with contextlib.redirect_stdout(sys.stderr):
        import torch
        from ultralytics import YOLO
        torch.set_num_threads(2)
        model = YOLO(str(ROOT/'experiments/p0_cv_only/models/yolo26n-pose.pt'))
        device = 0 if torch.cuda.is_available() else 'cpu'
        kwargs = dict(imgsz=cfg['imgsz'], conf=cfg['confidence'], classes=[0], device=device,
                      half=device == 0, verbose=False, max_det=40)
        import numpy as np
        # Keep inference batch shape stable when short clips end (avoids late cold kernels).
        dummy = np.zeros((360, 640, 3), dtype=np.uint8)
        model.predict([dummy] * 9, **kwargs)
    emit({'type': 'ready', 'cold_start_ms': (time.perf_counter()-started)*1000,
          'device': str(device), 'torch': torch.__version__})
    if sys.stdin.readline().strip() != 'start':
        return
    epoch = time.time()
    origin = time.perf_counter()
    latest, ended = {}, set()
    slots = threading.Lock()
    emit({'type': 'epoch', 'epoch': epoch})

    def decode(camera):
        cid = camera['camera_id']
        cap = cv2.VideoCapture(camera['path'])
        decoded = displayed = late = 0
        next_display = 0.0
        last_pts = 0.0
        try:
            if not cap.isOpened():
                raise ValueError('open_failed')
            fps = cap.get(cv2.CAP_PROP_FPS)
            expected_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if fps <= 0:
                raise ValueError('invalid_fps')
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                pts = cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                if decoded and pts <= last_pts:
                    raise ValueError('non_monotonic_pts')
                last_pts = pts
                delay = origin + pts - time.perf_counter()
                if delay > 0:
                    time.sleep(delay)
                lag = max(0, time.perf_counter()-origin-pts)
                decoded += 1
                if lag > 1/fps:
                    late += 1
                with slots:
                    latest[cid] = (decoded, pts, frame, lag)
                if pts >= next_display:
                    next_display = pts + 1/cfg['display_fps']
                    ok, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if ok:
                        displayed += 1
                        emit({'type': 'frame', 'camera_id': cid, 'pts': pts, 'lag_ms': lag*1000,
                              'decoded': decoded, 'displayed': displayed, 'late_frames': late,
                              'source_fps': fps, 'jpg': base64.b64encode(jpg).decode()})
            emit({'type': 'camera_end', 'camera_id': cid, 'pts': last_pts,
                  'decoded': decoded, 'late_frames': late, 'displayed': displayed,
                  'elapsed': time.perf_counter()-origin, 'source_fps': fps, 'expected_frames': expected_frames})
        except Exception as exc:
            emit({'type': 'camera_error', 'camera_id': cid, 'error': type(exc).__name__})
        finally:
            cap.release()
            with slots:
                ended.add(cid)

    threads = [threading.Thread(target=decode, args=(c,), daemon=True) for c in cfg['cameras']]
    for thread in threads:
        thread.start()
    signals = Signals(cfg)
    seen = {}
    while True:
        tick = time.perf_counter()
        with slots:
            batch = [(cid, value) for cid, value in latest.items() if value[0] != seen.get(cid)]
            all_ended = len(ended) == len(threads)
        if batch:
            t = time.perf_counter()
            with contextlib.redirect_stdout(sys.stderr):
                inputs = [value[2] for cid, value in batch]
                results = model.predict(inputs + [dummy] * (9-len(inputs)), **kwargs)[:len(inputs)]
            batch_ms = (time.perf_counter()-t)*1000
            for (cid, (number, pts, frame, lag)), result in zip(batch, results):
                reasons, values = signals.observe(cid, frame, result.boxes.xyxy.cpu().tolist())
                seen[cid] = number
                emit({'type': 'observation', 'camera_id': cid, 'pts': pts, 't1': time.time(),
                      'frame_number': number, 'batch_ms': batch_ms, 'batch_size': len(batch),
                      'reasons': reasons, 'observations': values,
                      'gpu_peak_allocated_mb': torch.cuda.max_memory_allocated()/1024**2 if device == 0 else None})
        if all_ended:
            break
        time.sleep(max(0, 1/cfg['sample_fps']-(time.perf_counter()-tick)))
    for thread in threads:
        thread.join()
    emit({'type': 'finished', 'elapsed': time.perf_counter()-origin})


if __name__ == '__main__':
    main()
