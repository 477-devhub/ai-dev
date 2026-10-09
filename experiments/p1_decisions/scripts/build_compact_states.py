"""Build compact_states/ITEM_XX.json (canonical JSON bytes) from P0 cv-state-v1 states + size/token manifest."""
import _bootstrap  # noqa: F401
import time

from compact_serializer import CompactSerializer
from state_loader import load_cv_state
from utils import (COMPACT_CONFIG, COMPACT_DIR, ITEM_IDS, P0_ROOT, canonical_json, count_tokens, load_yaml,
                   sha256_bytes, write_json)


def main():
    ser = CompactSerializer(load_yaml(COMPACT_CONFIG))
    manifest = {'schema_version': ser.cfg['schema_version'], 'items': {}}
    for item in ITEM_IDS:
        state = load_cv_state(item)
        t0 = time.perf_counter()
        compact = ser.serialize(state)
        text = canonical_json(compact)
        ms = (time.perf_counter() - t0) * 1000
        again = canonical_json(ser.serialize(load_cv_state(item)))
        if again != text:
            raise SystemExit(f'{item}: serializer not deterministic')
        data = text.encode('utf-8')
        (COMPACT_DIR / f'{item}.json').write_bytes(data)
        model_input = ser.model_input_text(compact)
        orig_bytes = (P0_ROOT / 'states' / f'{item}.json').stat().st_size
        manifest['items'][item] = {
            'compact_sha256': sha256_bytes(data), 'compact_bytes': len(data),
            'original_state_bytes': orig_bytes, 'reduction_pct': round(100 * (1 - len(data) / orig_bytes), 2),
            'model_input_bytes': len(model_input.encode('utf-8')),
            'model_input_tokens_estimate_o200k': count_tokens(model_input),
            'serializer_latency_ms': round(ms, 3),
        }
        print(item, manifest['items'][item])
    write_json(COMPACT_DIR / 'manifest.json', manifest)


if __name__ == '__main__':
    main()
