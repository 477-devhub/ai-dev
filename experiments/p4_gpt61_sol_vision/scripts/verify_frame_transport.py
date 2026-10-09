"""Local-only transport verification on the real canonical frames (no API call, nothing sent to any model):
7/7 items x 64/64 frames: iter_model_frames -> lossless WebP (in memory) -> local decode -> SHA256 equality.
Also checks the uniform_total64_v1 allocation (64 total; AB 32+32; attention 22+21+21). Writes logs/transport_verification.json."""
import _bootstrap  # noqa: F401
import datetime
import sys

from frame_loader import load_frames
from image_encoder import KW, encode_frames
from utils import ITEM_IDS, LOGS_DIR, write_json


def main():
    out, ok = {'at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'encoder': {'format': 'lossless_webp', **KW}, 'items': {}}, True
    for item in ITEM_IDS:
        try:
            frames, dec_ms, per_cam, fp = load_frames(item)
            urls, rows, t = encode_frames(frames)
            n_ok = sum(r['roundtrip_equal'] for r in rows)
            out['items'][item] = {'images': len(rows), 'images_per_camera': per_cam, 'roundtrip_equal': f'{n_ok}/{len(rows)}',
                                  'encoded_bytes_total': sum(r['encoded_bytes'] for r in rows), 'data_url_bytes_total': sum(len(u) for u in urls),
                                  'frame_decode_ms': round(dec_ms, 1), **t,
                                  'frames': [{k: r[k] for k in ('frame_ref', 'camera', 'timestamp_sec', 'rgb_sha256', 'encoded_bytes', 'encoded_sha256', 'roundtrip_rgb_sha256')} for r in rows]}
            ok &= n_ok == 64 == len(rows)
            print(f"{item}: {per_cam} lossless {n_ok}/{len(rows)}, {out['items'][item]['data_url_bytes_total'] / 1e6:.1f} MB data URLs, "
                  f"decode {dec_ms / 1000:.1f}s encode {t['image_encode_ms'] / 1000:.1f}s")
        except Exception as e:
            ok = False
            out['items'][item] = {'error': f'{type(e).__name__}: {e}'}
            print(item, 'FAIL', e)
    alloc = {i: out['items'][i].get('images_per_camera') for i in ITEM_IDS}
    out['allocation_ok'] = (alloc['ITEM_04'] == {'CAM_01': 22, 'CAM_02': 21, 'CAM_03': 21} and alloc['ITEM_07'] == {'CAM_01': 32, 'CAM_02': 32}
                            and all(sum(v.values()) == 64 for v in alloc.values() if v))
    out['verdict'] = 'PASS' if ok and out['allocation_ok'] else 'FAIL'
    write_json(LOGS_DIR / 'transport_verification.json', out)
    print('TRANSPORT VERIFICATION', out['verdict'], '| allocation ok:', out['allocation_ok'])
    sys.exit(0 if out['verdict'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
