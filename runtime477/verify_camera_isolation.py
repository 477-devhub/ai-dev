"""Actual 8-source replay plus one deliberately missing camera. No API calls."""
import json
import subprocess
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT/'runtime477/runs'/('isolation_'+uuid4().hex)
    output.mkdir(parents=True)
    config = json.loads((ROOT/'runtime477/config.json').read_text())
    config['cameras'] = [{'camera_id': f'CAM_{i:02}', 'path': str(ROOT/f'data/mock_cctv/playback/CAM_{i:02}.mp4')}
                         for i in range(1, 10)]
    config['cameras'][8]['path'] = str(output/'deliberately_missing.mp4')
    path = output/'config.json'
    path.write_text(json.dumps(config))
    with (output/'stderr.log').open('wb') as log:
        proc = subprocess.Popen([str(ROOT/'experiments/p0_cv_only/.venv/Scripts/python.exe'),
            str(ROOT/'runtime477/stream_worker.py'), str(path)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log)
        events = []
        for line in proc.stdout:
            message = json.loads(line)
            if message['type'] == 'ready':
                proc.stdin.write(b'start\n')
                proc.stdin.flush()
            if message['type'] in ('camera_end', 'camera_error', 'finished'):
                events.append(message)
        code = proc.wait(timeout=10)
    errors = [e for e in events if e['type'] == 'camera_error']
    ended = [e for e in events if e['type'] == 'camera_end']
    passed = code == 0 and len(errors) == 1 and errors[0]['camera_id'] == 'CAM_09' and len(ended) == 8
    report = {'passed': passed, 'scope': '8 real MP4 + 1 deliberately missing camera; not latency benchmark', 'events': events}
    (output/'result.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({'passed': passed, 'ended': len(ended), 'errors': len(errors), 'report': str(output/'result.json')}))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
