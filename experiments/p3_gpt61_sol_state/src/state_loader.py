"""Read-only access to the frozen P1 compact-decision-state-v1 bytes (shared by P1/P2/P3).

verify_p1_freeze(): all P1 frozen hashes (configs, serializer, adapters, 7 compact states) must match -> else FAIL.
load_state(): exact frozen bytes and the identical model input text P1/P2 sent (P1 preamble + '\\n\\n' + compact bytes).
"""
import json

import yaml

from utils import (ITEM_IDS, P0_ROOT, P1_COMPACT_CONFIG, P1_COMPACT_DIR, P1_FREEZE, P1_ROOT, read_allowed_bytes,
                   read_allowed_json, sha256_bytes)


class FreezeError(RuntimeError):
    pass


def verify_p1_freeze():
    fr = read_allowed_json(P1_FREEZE)
    bad = [rel for rel, h in fr['hashes'].items() if sha256_bytes((P1_ROOT / rel).read_bytes()) != h]
    bad += [f'compact_states/{i}.json' for i in ITEM_IDS
            if sha256_bytes(read_allowed_bytes(P1_COMPACT_DIR / f'{i}.json')) != fr['compact_state_sha256'][i]]
    if bad or fr.get('state_version') != 'compact-decision-state-v1':
        raise FreezeError(f'P1 frozen artifact hash mismatch: {bad}')
    return fr


def preamble():
    return yaml.safe_load(read_allowed_bytes(P1_COMPACT_CONFIG).decode('utf-8'))['model_input_preamble'].strip()


def load_state(item_id, frozen_hashes):
    raw = read_allowed_bytes(P1_COMPACT_DIR / f'{item_id}.json')
    sha = sha256_bytes(raw)
    if sha != frozen_hashes[item_id]:
        raise FreezeError(f'{item_id}: compact state hash differs from p1_freeze.json')
    text = raw.decode('utf-8')
    model_input = preamble() + '\n\n' + text
    return {'compact': json.loads(text), 'compact_sha256': sha, 'state_text': model_input,
            'state_text_sha256': sha256_bytes(model_input.encode('utf-8'))}


def load_input_fingerprint(item_id):
    """Benchmark input fingerprint for result.schema.json (harness metadata; never sent to the model)."""
    return read_allowed_json(P0_ROOT / 'states' / f'{item_id}.json')['input']['benchmark_input_fingerprint']
