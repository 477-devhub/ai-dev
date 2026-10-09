"""P3 leakage audit -> logs/leakage_audit.json (after the model run, before result freeze / GT access).
Checks: model-path code/configs item-specific branching (FAIL) and term mentions (reported); sent state bytes ==
P1 input == P2 state (P1/P2 raw request hashes read here post-run only); sent instructions/schema == frozen rebuild;
no image/audio/tool in the request; model input free of labels, GT, grading or other-model outputs; runtime access audit;
API key absent from artifacts and results."""
import _bootstrap  # noqa: F401
import re

from process_log import log_event
from prompt_builder import PromptBuilder
from state_loader import load_state, verify_p1_freeze
from utils import (EXP_ROOT, ITEM_IDS, LOGS_DIR, P1_QUESTIONS_CONFIG, P1_ROOT, P2_ROOT, RAW_DIR, RESULTS_DIR, artifact_files, canonical_json,
                   load_api_key_env, load_json, scan_for_secret, sha256_bytes, write_json)

MODEL_PATH = ['src', 'configs', 'schemas', 'scripts/run_p3.py', 'scripts/smoke_test_p3.py', 'scripts/freeze_p3.py', 'scripts/offline_adapter_test.py']
TERMS = r'private_ground_truth|human_grading|README|BENCHMARK_LOCK|candidate_report|annotation|swoon|fight|trespass|falldown|climbwall|expected.?rank|results/p[0-2]_|S14|F01|MV05|ph_e2069'
BRANCH = r'(if|elif|==)[^\n]*(ITEM_0\d|ASSET_0\d|asset_0\d)'
INPUT_FORBIDDEN = (r'ITEM_0\d|ASSET_0\d|asset_0\d|\.mp4|swoon|fight|trespass|falldown|climbwall|punching|S14|F01|MV05|ph_e2069|'
                   r'ground.?truth|annotation|"event_type"|"is_incident"|attention_queue|priority_score|p_incident|human_grading|reviewer|'
                   r'gpt-6-luna|clef|decisions api|rubric|auto.?eval|category_match|normalized_event_target|data:image|base64')


def main():
    files = []
    for m in MODEL_PATH:
        p = EXP_ROOT / m
        files += [x for x in p.rglob('*') if x.is_file() and x.suffix in ('.py', '.json', '.txt')] if p.is_dir() else [p]
    mentions, branches = [], []
    for p in files:
        for n, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
            where = f'{p.relative_to(EXP_ROOT).as_posix()}:{n}'
            if re.search(TERMS, line, re.I):
                mentions.append({'where': where, 'line': line.strip()[:160]})
            if re.search(BRANCH, line) and 'choices=ITEM_IDS' not in line:
                branches.append({'where': where, 'line': line.strip()[:160]})
    p1 = verify_p1_freeze()
    pb = PromptBuilder()
    qkeys = [b['key'] for g in ('per_assessment_questions', 'attention_questions', 'multi_camera_questions') for b in load_json(P1_QUESTIONS_CONFIG)[g]]
    items = {}
    for item in ITEM_IDS:
        st = load_state(item, p1['compact_state_sha256'])
        raw = load_json(RAW_DIR / f'{item}.json')
        req = raw['request']
        p1req = load_json(P1_ROOT / 'raw_api' / f'{item}.json')['request']     # post-run parity only
        p2req = load_json(P2_ROOT / 'raw_api' / f'{item}.json')['request']
        cams = [c['camera'] for c in st['compact']['cameras']]
        instr = pb.instructions(st['compact']['task'], cams)
        tf = pb.text_format(st['compact']['task'], cams)
        instr_scan = instr
        for k in qkeys:   # question field names (e.g. same_incident) are frozen P1 question ids, not answers
            instr_scan = instr_scan.replace(k, '<q>')
        hit = re.search(INPUT_FORBIDDEN, st['state_text'], re.I) or re.search(INPUT_FORBIDDEN, instr_scan, re.I)
        res = load_json(RESULTS_DIR / f'run_{item}.json')
        body = raw['response']['response_body']
        items[item] = {
            'state_bytes_equal_p1_and_p2': req['state_sha256'] == p1req['input_sha256'] == p2req['state_sha256'] == st['state_text_sha256'],
            'compact_sha256_equal_p1_p2': req['compact_state_sha256'] == p1['compact_state_sha256'][item] == p1req['compact_state_sha256'] == p2req['compact_state_sha256'],
            'instructions_equal_frozen_rebuild': req['instructions'] == instr and req['instructions_sha256'] == sha256_bytes(instr.encode('utf-8')),
            'schema_equal_frozen_rebuild': req['text_format_sha256'] == sha256_bytes(canonical_json(tf).encode('utf-8')),
            'no_images_or_tools': (not body.get('tools')) and 'image' not in canonical_json(req).lower(),
            'reasoning_effort_high': (body.get('reasoning') or {}).get('effort') == 'high',
            'forbidden_text_in_model_input': hit.group(0) if hit else None,
            'runtime_access_audit_pass': res['runtime_config']['access_audit']['pass'],
        }
    load_api_key_env()
    scan = artifact_files(EXP_ROOT, RESULTS_DIR)
    leaks = scan_for_secret(scan)
    keys = [k for k in next(iter(items.values())) if k != 'forbidden_text_in_model_input']
    verdict = not branches and not leaks and all(all(v[k] for k in keys) and v['forbidden_text_in_model_input'] is None for v in items.values())
    out = {'verdict': 'PASS' if verdict else 'FAIL', 'model_path_files_scanned': len(files), 'term_mentions': mentions,
           'item_specific_branching': branches, 'items': items, 'api_key_found_in_files': leaks, 'artifact_files_scanned': len(scan),
           'note': 'Term mentions are deny-lists / docstrings; none is a model input. P1/P2 raw request hashes read only here, post-run.'}
    write_json(LOGS_DIR / 'leakage_audit.json', out)
    for m in mentions:
        print('mention ', m['where'], '|', m['line'][:110])
    print('item-specific branching:', branches or 'none')
    for k, v in items.items():
        print(k, v)
    print('API key in artifacts:', leaks or 'none', f'({len(scan)} files)')
    print('LEAKAGE AUDIT', out['verdict'])
    log_event('leakage_audit', {'verdict': out['verdict']})


if __name__ == '__main__':
    main()
