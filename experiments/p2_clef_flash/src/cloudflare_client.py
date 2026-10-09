"""Direct Workers AI REST client for @cf/cloudflare/clef-flash (no SDK, no AI Gateway).

- Credentials only from the environment / experiments/.env; never stored, logged or echoed (error texts are redacted).
- Explicit connect/read timeouts. Retries (max 2, exponential backoff + jitter) only for network/timeout errors,
  429, 5xx and Cloudflare temporary-capacity errors. 400/401/403/404/422 / invalid schema are never retried.
- Returns a JSON-safe record: full response body, HTTP status, Cloudflare ray id, timing, retry count.
"""
import os
import random
import time

import httpx

from utils import load_cloudflare_env, redact

MODEL = '@cf/cloudflare/clef-flash'
MODEL_SELECTOR = 'clef-flash'
URL = 'https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/' + MODEL
CONNECT_TIMEOUT_SEC = 10.0
READ_TIMEOUT_SEC = 120.0
MAX_RETRIES = 2
BACKOFF_BASE_SEC = 1.0
JITTER_SEC = 0.25
CAPACITY_HINTS = ('capacity', 'temporarily unavailable', 'overloaded', 'try again')


def _retryable_status(status, body_text):
    if status == 429 or 500 <= status < 600:
        return True
    return status not in (400, 401, 403, 404, 422) and status >= 400 and any(h in body_text.lower() for h in CAPACITY_HINTS)


class CloudflareClient:
    def __init__(self):
        if not load_cloudflare_env():
            raise RuntimeError('CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN not available in environment or experiments/.env')
        self._url = URL.format(acc=os.environ['CLOUDFLARE_ACCOUNT_ID'])
        self._http = httpx.Client(timeout=httpx.Timeout(READ_TIMEOUT_SEC, connect=CONNECT_TIMEOUT_SEC),
                                  headers={'Authorization': f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}",
                                           'Content-Type': 'application/json'})
        self.http_client_version = f'httpx {httpx.__version__}'

    def run(self, state, questions):
        payload = {'model': MODEL_SELECTOR, 'state': state, 'questions': questions}
        attempts, errors = 0, []
        t_total = time.perf_counter()
        while True:
            attempts += 1
            t0 = time.perf_counter()
            try:
                r = self._http.post(self._url, json=payload)
                elapsed = (time.perf_counter() - t0) * 1000
            except (httpx.TransportError,) as e:   # connect/read timeouts, network errors
                errors.append({'attempt': attempts, 'error_type': type(e).__name__, 'status': None, 'message': redact(str(e))[:300]})
                if attempts > MAX_RETRIES:
                    return self._failed(errors, attempts, t_total)
                self._sleep(attempts)
                continue
            text = r.text
            try:
                body = r.json()
            except Exception:
                body = None
            ok = r.status_code == 200 and isinstance(body, dict) and body.get('success', True) is not False
            if ok:
                return {
                    'status': 'ok', 'http_status': r.status_code,
                    'cf_ray': r.headers.get('cf-ray'),
                    'cf_ai_req_id': r.headers.get('cf-ai-req-id'),
                    'response_body': body,
                    'response_headers_subset': {k: r.headers.get(k) for k in ('cf-ray', 'cf-ai-req-id', 'server-timing', 'content-type') if r.headers.get(k)},
                    'timing': {'last_attempt_ms': round(elapsed, 2), 'total_including_retries_ms': round((time.perf_counter() - t_total) * 1000, 2)},
                    'retry_count': attempts - 1, 'errors_before_success': errors,
                }
            err = {'attempt': attempts, 'error_type': 'http_error', 'status': r.status_code, 'cf_ray': r.headers.get('cf-ray'),
                   'message': redact(text)[:800]}
            errors.append(err)
            if _retryable_status(r.status_code, text) and attempts <= MAX_RETRIES:
                self._sleep(attempts)
                continue
            return self._failed(errors, attempts, t_total)

    @staticmethod
    def _sleep(attempts):
        time.sleep(BACKOFF_BASE_SEC * 2 ** (attempts - 1) + random.uniform(0, JITTER_SEC))

    @staticmethod
    def _failed(errors, attempts, t_total):
        return {'status': 'FAILED', 'errors': errors, 'retry_count': attempts - 1,
                'timing': {'total_including_retries_ms': round((time.perf_counter() - t_total) * 1000, 2)}}


def unwrap(body):
    """Workers AI REST wraps model output as {'result': {...}, 'success': true, ...}; accept a bare object too."""
    if isinstance(body, dict) and isinstance(body.get('result'), dict) and 'answers' in body['result']:
        return body['result']
    return body
