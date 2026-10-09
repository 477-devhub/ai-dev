"""Local reviewer server for the blind grading pack (127.0.0.1 only, stdlib).

Serves ONLY whitelisted resources:
  /                         -> redirect to /review/review.html
  /review/<asset>           -> review.html, app.js, style.css, data/rubric.json
  /blind_manifest.json      -> blind manifest (no system identities)
  /cases/ITEM_XX/<file>     -> system_A.json, system_B.json, reference.json
  /video/ITEM_XX/CAM_0Y     -> benchmark media streamed read-only (HTTP Range for seeking); the browser never sees
                               the media path or file name, only the generic camera label in the URL
  POST /api/save/<reviewer> -> writes grades/<reviewer>.json (write-only; grades are never served back)
reveal_map_private.json, grades/, scripts/, config/, output/ and anything else are never served.
"""
import argparse
import json
import re
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PACK = Path(__file__).resolve().parents[1]
BENCH = PACK.parents[1] / 'benchmark_v1'
STATIC = {'review.html': 'text/html; charset=utf-8', 'app.js': 'text/javascript; charset=utf-8',
          'style.css': 'text/css; charset=utf-8', 'data/rubric.json': 'application/json; charset=utf-8'}
CASE_FILES = {'system_A.json', 'system_B.json', 'reference.json'}
REVIEWER_RE = re.compile(r'^[A-Za-z0-9_-]{1,40}$')


def build_video_map():
    """(item, camera) -> absolute media path, resolved server-side from public benchmark files only."""
    scen = json.loads((BENCH / 'model_input' / 'scenarios.json').read_text(encoding='utf-8-sig'))
    media = json.loads((BENCH / 'public_manifest.json').read_text(encoding='utf-8-sig'))['media']
    out = {}
    for it in scen['items']:
        for c in it['cameras']:
            p = (BENCH / media[c['asset']]['path']).resolve()
            if not p.is_relative_to((BENCH / 'media').resolve()):
                raise ValueError('unsafe media path')
            out[(it['item_id'], c['camera'])] = p
    return out


VIDEOS = build_video_map()


class Handler(BaseHTTPRequestHandler):
    server_version = 'GradingPack/1'

    def log_message(self, fmt, *args):
        sys.stderr.write('%s %s\n' % (self.command, self.path.split('?')[0]))

    def _send(self, code, body=b'', ctype='text/plain; charset=utf-8', extra=None):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/':
            return self._send(302, b'', extra={'Location': '/review/review.html'})
        if path.startswith('/review/'):
            rel = path[len('/review/'):]
            if rel in STATIC:
                return self._send(200, (PACK / 'review' / rel).read_bytes(), STATIC[rel])
        if path == '/blind_manifest.json':
            return self._send(200, (PACK / 'blind_manifest.json').read_bytes(), 'application/json; charset=utf-8')
        m = re.fullmatch(r'/cases/(ITEM_0[1-7])/([A-Za-z_]+\.json)', path)
        if m and m.group(2) in CASE_FILES:
            return self._send(200, (PACK / 'cases' / m.group(1) / m.group(2)).read_bytes(), 'application/json; charset=utf-8')
        m = re.fullmatch(r'/video/(ITEM_0[1-7])/(CAM_0[1-3])', path)
        if m and (m.group(1), m.group(2)) in VIDEOS:
            return self._video(VIDEOS[(m.group(1), m.group(2))])
        return self._send(404, b'not found')

    def _video(self, p):
        size = p.stat().st_size
        rng = self.headers.get('Range')
        start, end, code = 0, size - 1, 200
        if rng:
            mm = re.match(r'bytes=(\d*)-(\d*)', rng)
            if mm:
                if mm.group(1):
                    start = int(mm.group(1))
                    end = int(mm.group(2)) if mm.group(2) else size - 1
                elif mm.group(2):
                    start = max(0, size - int(mm.group(2)))
                end = min(end, size - 1)
                if start > end:
                    return self._send(416, b'', extra={'Content-Range': f'bytes */{size}'})
                code = 206
        length = end - start + 1
        self.send_response(code)
        self.send_header('Content-Type', 'video/mp4')
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(length))
        self.send_header('Content-Disposition', 'inline')
        if code == 206:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        if self.command == 'HEAD':
            return
        with p.open('rb') as f:          # read-only; media is never copied or modified
            f.seek(start)
            remaining = length
            try:
                while remaining > 0:
                    chunk = f.read(min(1 << 20, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
            except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
                pass

    def do_POST(self):
        m = re.fullmatch(r'/api/save/([^/]+)', self.path.split('?', 1)[0])
        if not m or not REVIEWER_RE.match(m.group(1)):
            return self._send(400, b'bad reviewer id')
        n = int(self.headers.get('Content-Length') or 0)
        if n <= 0 or n > 5_000_000:
            return self._send(400, b'bad length')
        try:
            data = json.loads(self.rfile.read(n).decode('utf-8'))
        except Exception:
            return self._send(400, b'invalid json')
        if data.get('reviewer_id') != m.group(1):
            return self._send(400, b'reviewer id mismatch')
        out = PACK / 'grades' / f'{m.group(1)}.json'
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return self._send(200, json.dumps({'saved': f'grades/{out.name}'}).encode(), 'application/json')


def free_port(preferred):
    for port in [preferred] + list(range(preferred + 1, preferred + 30)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    raise RuntimeError('no free port')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=json.loads((PACK / 'config' / 'build_config.json').read_text(encoding='utf-8'))['port'])
    a = ap.parse_args()
    if not (PACK / 'blind_manifest.json').is_file():
        sys.exit('Run scripts/build_grading_pack.py first.')
    port = free_port(a.port)
    srv = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'Grading UI: http://127.0.0.1:{port}/review/review.html')
    print(f'Second reviewer: http://127.0.0.1:{port}/review/review.html?reviewer=reviewer_02')
    print('Press Ctrl+C to stop.')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
