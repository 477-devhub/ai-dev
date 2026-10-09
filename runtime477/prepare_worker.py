"""Same native RGB/uniform64/lossless-WebP protocol, bounded background CPU.

This runtime sampler leaves the frozen sampler intact. No reduced frame input.
"""
import hashlib
import io
import json
import math
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image


def main():
    request, directory = Path(sys.argv[1]), Path(sys.argv[2])
    p = json.loads(request.read_text())
    timings = {}
    started = time.perf_counter()
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-threads', '1',
        '-select_streams', 'v:0', '-show_frames', '-show_entries',
        'frame=best_effort_timestamp_time,width,height', '-of', 'json', p['path']],
        stderr=subprocess.DEVNULL, timeout=90))['frames']
    timings['pts_probe_ms'] = (time.perf_counter()-started)*1000
    available = [(i, f) for i, f in enumerate(probe) if 0 <= float(f['best_effort_timestamp_time'])*1000 <= p['end_ms']]
    if len(available) < 64:
        raise ValueError('insufficient_frames')
    schedule = [available[int(math.floor(j*(len(available)-1)/63+.5))] for j in range(64)]
    width, height = schedule[0][1]['width'], schedule[0][1]['height']
    if width*height > 1920*1080 or any((f['width'], f['height']) != (width, height) for _, f in schedule):
        raise ValueError('resolution_budget')
    expression = '+'.join(f'eq(n,{i})' for i, f in schedule)
    started = time.perf_counter()
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-threads', '1', '-i', p['path'],
        '-vf', "select='"+expression+"'", '-fps_mode', 'passthrough', '-threads', '1',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'], stderr=subprocess.DEVNULL, timeout=90)
    timings['decode_ms'] = (time.perf_counter()-started)*1000
    size = width*height*3
    if len(raw) != size*64:
        raise ValueError('decode_count')
    started = time.perf_counter()
    def encode(item):
        j, (_, frame) = item
        rgb = raw[j*size:(j+1)*size]
        image = Image.frombytes('RGB', (width, height), rgb)
        buf = io.BytesIO()
        image.save(buf, format='WEBP', lossless=True, quality=50, method=2)
        if Image.open(io.BytesIO(buf.getvalue())).convert('RGB').tobytes() != rgb:
            raise ValueError('roundtrip')
        ref = f'F{j+1:03d}'
        (directory/(ref+'.webp')).write_bytes(buf.getvalue())
        return {'ref': ref, 'timestamp_ms': round(float(frame['best_effort_timestamp_time'])*1000),
                'rgb_sha256': hashlib.sha256(rgb).hexdigest()}
    with ThreadPoolExecutor(max_workers=2) as pool:
        frames = list(pool.map(encode, enumerate(schedule)))
    timings['lossless_encode_and_verify_ms'] = (time.perf_counter()-started)*1000
    (directory/'result.json').write_text(json.dumps({'frames': frames,
        'frame_numbers': [i for i, f in schedule], 'timings': timings}), encoding='utf-8')


if __name__ == '__main__':
    main()
