"""Loads the frozen common-adapter-v2 (hash-checked against its freeze record) and applies it unchanged."""
import json
import types

from utils import CA2_FREEZE, CA2_ROOT, read_allowed_bytes, read_allowed_json, sha256_bytes


def load_common_adapter_v2():
    fr = read_allowed_json(CA2_FREEZE)
    srcs = {rel: read_allowed_bytes(CA2_ROOT / rel) for rel in fr['hashes']}
    bad = [rel for rel, b in srcs.items() if sha256_bytes(b) != fr['hashes'][rel]]
    if bad or not fr.get('frozen'):
        raise RuntimeError(f'common-adapter-v2 differs from its freeze: {bad}')
    mod = types.ModuleType('common_adapter_v2')
    mod.__file__ = str(CA2_ROOT / 'src' / 'common_adapter_v2.py')
    exec(compile(srcs['src/common_adapter_v2.py'].decode('utf-8'), str(CA2_ROOT / 'src' / 'common_adapter_v2.py'), 'exec'), mod.__dict__)
    cfg = json.loads(srcs['config/adapter_v2.json'].decode('utf-8'))
    return mod.CommonAdapterV2(cfg), {'freeze_frozen_at': fr['frozen_at'], 'hashes': fr['hashes']}
