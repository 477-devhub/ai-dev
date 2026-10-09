"""Read-only access to the frozen P1 compact-decision-state-v1 artifacts.

verify_p1_freeze(): every hash in p1_freeze.json (configs, schema, serializer, adapters, 7 compact states) must match,
otherwise FAIL. load_state(): returns the exact frozen bytes and the model input text P1 sent
(preamble + '\\n\\n' + compact bytes). No re-serialization, no added features, no P1 predictions.
"""
import json

from utils import (ITEM_IDS, P0_ROOT, P1_COMPACT_CONFIG, P1_COMPACT_DIR, P1_FREEZE, P1_ROOT, load_yaml, read_allowed_bytes,
                   read_allowed_json, sha256_bytes)


class FreezeError(RuntimeError):
    pass


def verify_p1_freeze():
    fr = read_allowed_json(P1_FREEZE)
    bad = []
    for rel, h in fr['hashes'].items():
        p = P1_ROOT / rel
        try:
            got = sha256_bytes(p.read_bytes())   # P1 source/config files: hash only (not model input)
        except FileNotFoundError:
            got = None
        if got != h:
            bad.append(rel)
    for item in ITEM_IDS:
        if sha256_bytes(read_allowed_bytes(P1_COMPACT_DIR / f'{item}.json')) != fr['compact_state_sha256'][item]:
            bad.append(f'compact_states/{item}.json')
    if fr.get('state_version') != 'compact-decision-state-v1' or not fr.get('frozen'):
        bad.append('p1_freeze.json:state_version/frozen')
    if bad:
        raise FreezeError(f'P1 frozen artifact hash mismatch: {bad}')
    return fr


def preamble():
    cfg = load_yaml(P1_COMPACT_CONFIG)
    return cfg['model_input_preamble'].strip()


def load_state(item_id, frozen_hashes):
    raw = read_allowed_bytes(P1_COMPACT_DIR / f'{item_id}.json')
    sha = sha256_bytes(raw)
    if sha != frozen_hashes[item_id]:
        raise FreezeError(f'{item_id}: compact state hash differs from p1_freeze.json')
    text = raw.decode('utf-8')
    compact = json.loads(text)
    model_input = preamble() + '\n\n' + text
    return {'compact': compact, 'compact_bytes': raw, 'compact_sha256': sha, 'state_text': model_input,
            'state_text_sha256': sha256_bytes(model_input.encode('utf-8'))}


def load_input_fingerprint(item_id):
    """Benchmark input fingerprint (prompt/schema/media hashes + frame numbers) of the canonical frames behind the CV
    state, as P1 recorded it. Harness metadata for result.schema.json only; it is not part of the Clef input."""
    return read_allowed_json(P0_ROOT / 'states' / f'{item_id}.json')['input']['benchmark_input_fingerprint']
