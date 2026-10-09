"""Request-size preflight (no API call) from logs/transport_verification.json + the real request text/schema size:
image count, encoded bytes, base64 payload bytes vs documented limits (512 MB / request, 1,500 images / request) and a
token ESTIMATE vs the 1,050,000-token context (estimate rule recorded in configs/p4_v1.json; provider usage is authoritative).
On any violation the item is marked FAIL; nothing is downscaled, re-encoded lossy or dropped."""
import _bootstrap  # noqa: F401
import datetime
import math
import sys

from utils import ITEM_IDS, LOGS_DIR, P4_CONFIG, load_json, write_json

CFG = load_json(P4_CONFIG)
LIM = CFG['api_limits_checked']
PROMPT_OVERHEAD_BYTES = 64 * 1024   # task prompt + 64 labels + schema JSON (measured < 40 KB) + JSON envelope


def est_tokens(w, h):
    s = min(1.0, 2048 / max(w, h))                     # fit within 2048x2048
    w2, h2 = w * s, h * s
    patches = math.ceil(w2 / 32) * math.ceil(h2 / 32)
    if patches > 2500:                                 # 2,500-patch budget
        s2 = math.sqrt(2500 / patches)
        patches = math.ceil(w2 * s2 / 32) * math.ceil(h2 * s2 / 32)
    return math.ceil(patches * 1.2)


def main():
    tv = load_json(LOGS_DIR / 'transport_verification.json')
    if tv['verdict'] != 'PASS':
        sys.exit('transport verification not PASS')
    out, ok = {'at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'limits': LIM,
               'token_estimate_rule': CFG['preflight_token_estimate_rule'], 'items': {}}, True
    for item in ITEM_IDS:
        v = tv['items'][item]
        payload = v['data_url_bytes_total'] + PROMPT_OVERHEAD_BYTES
        tok = 64 * est_tokens(1920, 1080) + 5000
        row = {'images': v['images'], 'encoded_bytes': v['encoded_bytes_total'], 'base64_payload_bytes': v['data_url_bytes_total'],
               'request_bytes_estimate': payload, 'payload_fraction_of_limit': round(payload / LIM['max_payload_bytes_per_request'], 3),
               'estimated_input_tokens': tok, 'estimated_input_cost_usd': round(tok * CFG['pricing']['input_usd_per_1m_tokens'] / 1e6, 4),
               'within_image_count': v['images'] <= LIM['max_images_per_request'],
               'within_payload': payload < LIM['max_payload_bytes_per_request'],
               'within_context': tok < LIM['context_window_tokens'] and tok <= CFG['pricing']['long_context_threshold_tokens']}
        row['pass'] = row['within_image_count'] and row['within_payload'] and row['within_context'] and v['images'] == 64
        ok &= row['pass']
        out['items'][item] = row
        print(item, row)
    out['verdict'] = 'PASS' if ok else 'FAIL'
    out['note'] = 'Estimates only; per-image tokens assume detail=high keeps 1920x1080 (2,040 patches <= 2,500). Cost reported later from provider usage.'
    write_json(LOGS_DIR / 'preflight.json', out)
    print('PREFLIGHT', out['verdict'])
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
