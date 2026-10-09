"""P1 leakage audit -> logs/leakage_audit.json.
Checks: forbidden source/label terms and item-specific branching in code/configs; P0 decision fields or labels in
compact states / model input; sent input == frozen compact state; runtime access audit; API key in artifacts."""
import _bootstrap  # noqa: F401
import os
import re

from compact_serializer import CompactSerializer
from utils import (COMPACT_CONFIG, COMPACT_DIR, EXP_ROOT, ITEM_IDS, LOGS_DIR, RAW_DIR, RESULTS_DIR, load_api_key_env, load_json,
                   load_yaml, sha256_bytes, write_json)

TERMS = r'private_ground_truth|README|BENCHMARK_LOCK|candidate_report|annotation|swoon|fight|trespass|falldown|climbwall|punching|expected.?rank|results/p0_cv_only|S14|F01|MV05|ph_e2069'
BRANCH = r'(if|elif|==)[^\n]*(ITEM_0\d|ASSET_0\d|asset_0\d)'
INPUT_FORBIDDEN = r'ITEM_0\d|ASSET_0\d|asset_0\d|\.mp4|swoon|fight|trespass|falldown|climbwall|punching|S14|F01|MV05|ph_e2069|ground.?truth|annotation|"event_type"|"is_incident"|"risk"|attention_queue|"same_incident"|same_incident_similarity|incident_signature|priority_score'


def main():
    files = [p for d in ('src', 'scripts', 'configs', 'schemas') for p in (EXP_ROOT / d).rglob('*')
             if p.is_file() and p.suffix in ('.py', '.yaml', '.json') and p.name != 'leakage_audit.py']
    mentions, branches = [], []
    for p in files:
        for n, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
            where = f'{p.relative_to(EXP_ROOT).as_posix()}:{n}'
            if re.search(TERMS, line, re.I):
                mentions.append({'where': where, 'line': line.strip()[:160]})
            if re.search(BRANCH, line) and 'choices=ITEM_IDS' not in line:
                branches.append({'where': where, 'line': line.strip()[:160]})
    ser = CompactSerializer(load_yaml(COMPACT_CONFIG))
    inputs = {}
    for item in ITEM_IDS:
        compact = load_json(COMPACT_DIR / f'{item}.json')
        ser.check_forbidden(compact)
        text = ser.model_input_text(compact)
        hit = re.search(INPUT_FORBIDDEN, text, re.I)
        raw = load_json(RAW_DIR / f'{item}.json')
        sent_matches = raw['request']['input_sha256'] == sha256_bytes(text.encode('utf-8'))
        res = load_json(RESULTS_DIR / f'run_{item}.json')
        inputs[item] = {'forbidden_text_in_model_input': hit.group(0) if hit else None,
                        'sent_input_equals_frozen_compact_state': sent_matches,
                        'runtime_access_audit_pass': res['runtime_config']['access_audit']['pass']}
    load_api_key_env()
    key = os.environ.get('OPENAI_API_KEY', '')
    scan = [p for p in list(EXP_ROOT.rglob('*')) + list(RESULTS_DIR.rglob('*')) if p.is_file() and '.venv' not in p.parts]
    leaks = [str(p) for p in scan if len(key) >= 8 and key in p.read_text(encoding='utf-8', errors='ignore')]
    verdict = (not branches and not leaks and all(v['forbidden_text_in_model_input'] is None and v['sent_input_equals_frozen_compact_state']
                                                  and v['runtime_access_audit_pass'] for v in inputs.values()))
    out = {'verdict': 'PASS' if verdict else 'FAIL', 'files_scanned': len(files), 'term_mentions': mentions,
           'item_specific_branching': branches, 'model_inputs': inputs, 'api_key_found_in_files': leaks, 'artifact_files_scanned_for_key': len(scan),
           'note': 'Term mentions are deny-lists/allowlist definitions/docstrings; none is a decision input.'}
    write_json(LOGS_DIR / 'leakage_audit.json', out)
    for m in mentions:
        print('mention ', m['where'], '|', m['line'][:110])
    print('item-specific branching:', branches or 'none')
    print('model inputs:', inputs)
    print('API key in artifacts:', leaks or 'none', f'({len(scan)} files scanned)')
    print('LEAKAGE AUDIT', out['verdict'])


if __name__ == '__main__':
    main()
