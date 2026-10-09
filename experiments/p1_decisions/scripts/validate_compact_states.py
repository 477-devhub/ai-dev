"""Validate compact_states/*.json: schema, forbidden keys/strings, determinism vs. fresh serialization, SHA256 manifest."""
import _bootstrap  # noqa: F401
import re
import sys

from jsonschema import Draft202012Validator

from compact_serializer import CompactSerializer
from state_loader import load_cv_state
from utils import COMPACT_CONFIG, COMPACT_DIR, COMPACT_SCHEMA, ITEM_IDS, canonical_json, load_json, load_yaml, sha256_bytes

FORBIDDEN_TEXT = r'ITEM_0\d|ASSET_0\d|asset_0\d|\.mp4|swoon|fight|trespass|falldown|climbwall|punching|S14|T06\b|T03\b|F01|MV05|ph_e2069|private|ground.?truth|annotation|event_type|is_incident|attention_queue|same_incident'


def main():
    cfg = load_yaml(COMPACT_CONFIG)
    ser = CompactSerializer(cfg)
    schema = load_json(COMPACT_SCHEMA)
    Draft202012Validator.check_schema(schema)
    v = Draft202012Validator(schema)
    man = load_json(COMPACT_DIR / 'manifest.json')
    ok = True
    for item in ITEM_IDS:
        try:
            raw = (COMPACT_DIR / f'{item}.json').read_bytes()
            obj = load_json(COMPACT_DIR / f'{item}.json')
            errs = sorted(v.iter_errors(obj), key=lambda e: list(e.path))
            if errs:
                raise ValueError(f"schema: {'/'.join(map(str, errs[0].path))}: {errs[0].message}")
            ser.check_forbidden(obj)
            text = raw.decode('utf-8')
            # track refs like T3 are generic; only flag zero-padded source-style IDs (T03/T06) via word boundaries above
            m = re.search(FORBIDDEN_TEXT, text, re.I)
            if m:
                raise ValueError(f'forbidden text in compact state: {m.group(0)!r}')
            if canonical_json(ser.serialize(load_cv_state(item))).encode('utf-8') != raw:
                raise ValueError('file differs from fresh deterministic serialization')
            if sha256_bytes(raw) != man['items'][item]['compact_sha256']:
                raise ValueError('SHA256 differs from manifest')
            print(f'{item}: PASS ({len(raw)} bytes, sha256 {sha256_bytes(raw)[:12]}...)')
        except Exception as e:
            ok = False
            print(f'{item}: FAIL - {e}')
    print('ALL COMPACT STATES VALID' if ok else 'COMPACT STATE VALIDATION FAILED')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
