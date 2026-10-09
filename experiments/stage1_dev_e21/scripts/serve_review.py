"""Loopback-only, blinded Human video review with Range support and atomic records."""
import argparse,json,re,secrets,sys
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from dev_common import ROOT,read,digest
from review_store import Reviews


def handler(pool,store,token):
    by_id={c['candidate_id']:c for c in pool['candidates']}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def respond(self,obj,status=200):
            b=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(status)
            self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b)))
            self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(b)
        def do_GET(self):
            u=urlsplit(self.path); query=parse_qs(u.query); reviewer=query.get('reviewer',[''])[0]
            if u.path=='/':
                b=(ROOT/'review/index.html').read_text(encoding='utf-8').replace('__TOKEN__',token).encode()
                self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
            if u.path=='/api/queue':
                self.respond([{'candidate_id':c['candidate_id'],'start_sec':c['clip_start_sec'],'end_sec':c['clip_end_sec'],
                    'context':c['neutral_context'],**store.public(c['candidate_id'],reviewer)} for c in pool['candidates']]); return
            match=re.fullmatch(r'/video/(DEV_[0-9]{3}_[0-9]{2})/(clip|original)',u.path)
            if not match or match[1] not in by_id: self.respond({'error':'not found'},404); return
            c=by_id[match[1]]; path=Path(c['clip_path' if match[2]=='clip' else 'source_video_path'])
            total=path.stat().st_size; start,end=0,total-1; code=200
            raw=self.headers.get('Range')
            if raw:
                m=re.fullmatch(r'bytes=(\d*)-(\d*)',raw)
                if not m or (not m[1] and not m[2]): self.respond({'error':'range'},416); return
                if not m[1]: start=max(0,total-int(m[2]))
                else: start=int(m[1]); end=min(total-1,int(m[2])) if m[2] else total-1
                if start>end or start>=total: self.respond({'error':'range'},416); return
                code=206
            self.send_response(code); self.send_header('Content-Type','video/mp4'); self.send_header('Accept-Ranges','bytes')
            self.send_header('Content-Length',str(end-start+1))
            if code==206: self.send_header('Content-Range',f'bytes {start}-{end}/{total}')
            self.end_headers()
            try:
                with path.open('rb') as f:
                    f.seek(start); left=end-start+1
                    while left:
                        b=f.read(min(left,1<<16)); self.wfile.write(b); left-=len(b)
            except (BrokenPipeError,ConnectionResetError): pass
        def do_POST(self):
            host=self.headers.get('Host',''); origin=self.headers.get('Origin')
            if self.headers.get('X-Review-Token')!=token or (origin and origin!=f'http://{host}'):
                self.respond({'error':'local request token/origin required'},403); return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=32768: raise ValueError('body size')
                body=json.loads(self.rfile.read(length)); cid=body['candidate_id']
                if cid not in by_id: raise ValueError('unknown candidate')
                if self.path=='/api/review':
                    c=by_id[cid]
                    media_hash=digest({k:c[k] for k in ('source_video_sha256','clip_sha256','clip_start_sec','clip_end_sec')})
                    status=store.save(cid,body['review'],media_hash)
                elif self.path=='/api/adjudicate':
                    if body.get('watched_original_context') is not True: raise ValueError('Human original review required')
                    store.adjudicate(cid,body['reviewer'],body['label'],body['reason']); status=store.status(cid)
                elif self.path=='/api/finalize':
                    store.finalize(cid,body['reviewer'],allow_single=body.get('allow_single') is True); status=store.status(cid)
                else: self.respond({'error':'not found'},404); return
                self.respond({'status':status,'manifest_updated':False,'note':'Finalized labels are exported only by prepare_dataset.py export after integrity/leakage checks.'})
            except (ValueError,KeyError,TypeError) as e: self.respond({'error':str(e)},400)
    return Handler


def main():
    p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=48771); args=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),handler(read(ROOT/'data/pool.json'),Reviews(),secrets.token_urlsafe(32)))
    print(f'Review: http://127.0.0.1:{args.port} (loopback only; no model outputs)',flush=True)
    server.serve_forever()


if __name__=='__main__': main()
