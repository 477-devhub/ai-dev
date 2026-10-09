"""Label-free offline size/token/serialization measurements; no inference claims."""
import argparse
import copy
import json
import os
import statistics
import sys
import time
from pathlib import Path

import _bootstrap
from compact_serializer import CompactSerializer
from compact_serializer_v2 import CompactSerializerV2
from compact_versions import prepare_compact
from utils import COMPACT_CONFIG, P0_ROOT, canonical_json, load_yaml, read_allowed_json, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iterations', type=int, default=100)
    args = parser.parse_args()
    if args.iterations < 1: parser.error('iterations must be positive')
    root = Path(__file__).resolve().parents[1]
    dest = root / 'e1_v2'
    try:
        local_cache = dest / '.cache'
        if (local_cache / 'fb374d419588a4632f3f557e76b4b70aebbca790').is_file():
            os.environ['TIKTOKEN_CACHE_DIR'] = str(local_cache)
        import tiktoken
        enc = tiktoken.get_encoding('o200k_base')
        tokenize = lambda text: len(enc.encode(text))
        method = 'tiktoken o200k_base proxy estimate; not verified GPT-6 Luna / Decisions billing tokenizer; no questions or API envelope included'
    except (ImportError, OSError, ValueError):
        tokenize = lambda text: (len(text.encode('utf-8')) + 3) // 4
        method = 'UTF-8 bytes / 4 heuristic estimate, not API tokens'
    serializers = {'v1': CompactSerializer(load_yaml(COMPACT_CONFIG)), 'v2': CompactSerializerV2(load_yaml(COMPACT_CONFIG))}
    rows = []
    for path in sorted((P0_ROOT / 'states').glob('ITEM_*.json')):
        state = read_allowed_json(path)
        row = {'sample':path.name}
        for version, ser in serializers.items():
            prep = prepare_compact(state,version)
            for _ in range(10): ser.model_input_text(ser.serialize(state))
            elapsed = []
            for _ in range(args.iterations):
                start=time.perf_counter_ns()
                ser.model_input_text(ser.serialize(state))
                elapsed.append((time.perf_counter_ns()-start)/1e6)
            row[version] = {'json_bytes':len(canonical_json(prep['compact']).encode('utf-8')),
                'estimated_json_tokens':tokenize(canonical_json(prep['compact'])),
                'estimated_input_text_tokens':tokenize(prep['input_text']),
                'serialization_median_ms':round(statistics.median(elapsed),4)}
        rows.append(row)
    mean = {v:{key:round(statistics.fmean(r[v][key] for r in rows),4) for key in rows[0][v]} for v in ('v1','v2')}
    delta = mean['v2']['estimated_input_text_tokens'] - mean['v1']['estimated_input_text_tokens']
    report = {'samples':'7 legacy unlabeled Canonical states, not Frozen calibration/test; no labels or predictions read',
        'token_method':method,'timing':'warm cached serialize + canonical JSON + unchanged preamble; excludes validation, IO, CV, API and queue; 10 warmups per sample/version',
        'iterations':args.iterations,'rows':rows,'mean':mean,
        'estimated_incremental_input_cost_usd':round(delta*.10/1e6,9),
        'cost_assumption':'Repository frozen Decisions input rate $0.10 / 1M tokens, assumed unchanged, no current price verification; estimate only'}
    write_json(dest/'comparison.json', report)
    sys.path.insert(0,str(root/'tests'))
    from test_compact_v2 import fixture
    for name, labels in [('recovery',('standing','horizontal','standing')),('unknown_tail',('standing','horizontal','unknown'))]:
        state=fixture(labels,(61,62,63))
        state['cameras'][0]['quality']['detection_dropout_rate']=None
        write_json(dest/f'{name}.canonical.json',state)
        for version in ('v1','v2'):
            write_json(dest/f'{name}.{version}.json',prepare_compact(state,version)['compact'])
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__': main()
