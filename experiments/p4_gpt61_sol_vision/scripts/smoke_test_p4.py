"""Synthetic integration smoke test (synthetic shapes only; no benchmark frames before freeze).
Checks: multiple image input, detail=high, strict structured output for single / attention / multi_camera, frame_ref
evidence resolution + per-camera attribution, usage incl. image tokens + reasoning tokens, effort high, no tools,
service tier recorded, latency, request-size accounting, refusal/incomplete classification, API key not stored."""
import _bootstrap  # noqa: F401
import datetime
import subprocess
import sys

import _synthetic
from access_audit import AccessAudit
from cost import external_api_cost_usd
from image_encoder import DETAIL, encode_frames
from openai_client import ResponsesClient, classify
from p4_pipeline import P4Pipeline
from utils import LOGS_DIR, RAW_DIR, artifact_files, scan_for_secret, write_json

LIMIT_BYTES = 512 * 1024 * 1024


def check(res, name, ok, detail=''):
    res.append({'check': name, 'pass': bool(ok), 'detail': detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f' - {detail}' if detail else ''))


def main():
    res, calls = [], {}
    p = P4Pipeline(ResponsesClient())
    with AccessAudit() as audit:
        for task in _synthetic.TASKS:
            fr = _synthetic.frames(task)
            cams = list(_synthetic.TASKS[task])
            urls, rows, enc_t = encode_frames(fr)
            content = p.pb.content(task, cams, fr, urls, DETAIL)
            tf = p.pb.text_format(task, cams, fr)
            payload = sum(len(u) for u in urls)
            rec = p.client.decide(content, tf)
            calls[task] = {'n_images': len(fr), 'payload_bytes': payload, 'manifest': rows, 'request_text': p.pb.request_text(content),
                           'api': {k: v for k, v in rec.items() if k != 'response_body'}}
            check(res, f'{task}: HTTP 200 with {len(fr)} images (detail={DETAIL})', rec.get('http_status') == 200,
                  f"status {rec['status']} retries {rec['retry_count']}" + ('' if 'http_status' in rec else ' ' + str(rec.get('errors'))[:400]))
            if rec['status'] != 'ok':
                continue
            prep = {'task': task, 'cameras': cams, 'text_format': tf, 'table': {f['ref']: {'camera': f['camera'], 'timestamp_sec': f['timestamp_sec']} for f in fr}}
            try:
                final, d, raw, vis, meta, _ = p.adapt(prep, rec['parsed'], rec['model'])
                p.validate_prediction(final, task, cams)
                check(res, f'{task}: strict output + frame_ref evidence resolved + prediction schema', True)
            except Exception as e:
                check(res, f'{task}: strict output + frame_ref evidence resolved + prediction schema', False, f'{type(e).__name__}: {e}'[:300])
            u = rec['usage'] or {}
            check(res, f'{task}: usage parsed (image tokens in input)', isinstance(u.get('input_tokens'), int),
                  f"in={u.get('input_tokens')} cached={(u.get('input_tokens_details') or {}).get('cached_tokens')} out={u.get('output_tokens')} "
                  f"reasoning={(u.get('output_tokens_details') or {}).get('reasoning_tokens')} cost=${external_api_cost_usd(u)}")
            check(res, f'{task}: effort high / no tools / tier recorded', rec.get('reasoning_effort_returned') == 'high' and not rec.get('tools_returned'),
                  f"effort={rec.get('reasoning_effort_returned')} tools={rec.get('tools_returned')} service_tier={rec.get('service_tier')}")
            check(res, f'{task}: latency + request size', payload < LIMIT_BYTES, f"{rec['timing']['last_attempt_ms']} ms; payload {payload} bytes")
    k = (classify({'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'refusal', 'refusal': 'x'}]}]})[0],
         classify({'status': 'incomplete', 'output': []})[0],
         classify({'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': '{bad'}]}]})[0])
    check(res, 'refusal / incomplete / parse-failure classification', k == ('refusal', 'incomplete', 'parse_failure'), str(k))
    r = subprocess.run([sys.executable, 'scripts/offline_adapter_test.py'], capture_output=True, text=True)
    check(res, 'offline adapter test (incl. cross-camera frame_ref rejection)', r.returncode == 0)
    rep = audit.report()
    check(res, 'no forbidden file access', rep['pass'], str(rep['forbidden_paths_opened'][:3]))
    write_json(RAW_DIR / 'smoke_synthetic.json', {'kind': 'synthetic smoke (shapes; not benchmark)', 'calls': calls, 'note': 'base64 payloads not stored'})
    leaks = scan_for_secret(artifact_files())
    check(res, 'API key not in artifacts', not leaks, str(leaks))
    passed = all(x['pass'] for x in res)
    write_json(LOGS_DIR / 'smoke_test.json', {'passed': passed, 'at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'checks': res,
                                              'benchmark_items_used': [], 'access_audit': rep})
    print('SMOKE TEST', 'PASS' if passed else 'FAIL')
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
