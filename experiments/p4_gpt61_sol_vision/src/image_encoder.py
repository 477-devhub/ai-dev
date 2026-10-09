"""In-memory lossless WebP transport for canonical RGB frames (no image files written, no base64 stored).

encode_frames(): parallel lossless WebP encode, local decode round-trip, SHA256(decoded RGB) == SHA256(source RGB)
required for every frame; returns data URLs (kept only in memory) and a manifest without payloads.
"""
import base64
import io
import time
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

from utils import P4_CONFIG, load_json, sha256_bytes

_T = load_json(P4_CONFIG)['image_transport']
KW = _T['pillow_save_kwargs']
THREADS = _T['parallel_encode_threads']
DETAIL = load_json(P4_CONFIG)['image_detail']
MIME = 'image/webp'


def _encode(f):
    buf = io.BytesIO()
    Image.frombytes('RGB', (f['width'], f['height']), f['rgb24']).save(buf, 'WEBP', **KW)
    return buf.getvalue()


def _roundtrip_sha(enc):
    return sha256_bytes(Image.open(io.BytesIO(enc)).convert('RGB').tobytes())


class TransportError(RuntimeError):
    pass


def encode_frames(frames):
    """Returns (data_urls, manifest_rows, timing). Raises TransportError if any frame is not bit-exact."""
    t0 = time.perf_counter()
    with ThreadPoolExecutor(THREADS) as ex:
        encoded = list(ex.map(_encode, frames))
    enc_ms = (time.perf_counter() - t0) * 1000
    t1 = time.perf_counter()
    with ThreadPoolExecutor(THREADS) as ex:
        rts = list(ex.map(_roundtrip_sha, encoded))
    rt_ms = (time.perf_counter() - t1) * 1000
    t2 = time.perf_counter()
    urls = [f'data:{MIME};base64,' + base64.b64encode(e).decode('ascii') for e in encoded]
    b64_ms = (time.perf_counter() - t2) * 1000
    rows = []
    for f, e, rt, u in zip(frames, encoded, rts, urls):
        rows.append({'frame_ref': f['ref'], 'camera': f['camera'], 'timestamp_sec': f['timestamp_sec'], 'rgb_sha256': f['rgb_sha256'],
                     'transport_format': 'lossless_webp', 'encoded_bytes': len(e), 'encoded_sha256': sha256_bytes(e),
                     'data_url_bytes': len(u), 'roundtrip_rgb_sha256': rt, 'roundtrip_equal': rt == f['rgb_sha256'], 'detail': DETAIL})
    bad = [r['frame_ref'] for r in rows if not r['roundtrip_equal']]
    if bad:
        raise TransportError(f'lossless round-trip failed for {bad}')
    return urls, rows, {'image_encode_ms': round(enc_ms, 2), 'roundtrip_verify_ms': round(rt_ms, 2), 'base64_build_ms': round(b64_ms, 2)}
