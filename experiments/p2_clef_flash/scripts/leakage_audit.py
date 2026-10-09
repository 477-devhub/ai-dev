"""P2 leakage audit -> logs/leakage_audit.json (runs after the model run, before result freeze / any GT access).
Checks:
 - model-path code/configs: forbidden source/label terms (reported) and item-specific branching (FAIL);
 - sent state == P1 sent input (byte-identical SHA256; P1 raw_api request hash read here post-run only) and == frozen compact;
 - model input (state + questions) contains no labels, P1/P0 predictions, GT or grading terms;
 - sent questions == questions rebuilt from the frozen configs;
 - runtime access audit of every item passed (no GT / grading / P0-P1 results opened);
 - Cloudflare credentials absent from every P2 artifact and result file."""
import _bootstrap  # noqa: F401
import re

from compact_state_loader import load_state, verify_p1_freeze
from process_log import log_event
from question_adapter import QuestionAdapter
from utils import (EXP_ROOT, ITEM_IDS, LOGS_DIR, P1_QUESTIONS_CONFIG, P1_ROOT, RAW_DIR, RESULTS_DIR, artifact_files, canonical_json,
                   load_cloudflare_env, load_json, scan_for_secrets, sha256_bytes, write_json)

MODEL_PATH_FILES = ['src', 'configs', 'schemas', 'scripts/run_p2.py', 'scripts/smoke_test_clef.py', 'scripts/freeze_p2.py',
                    'scripts/offline_adapter_test.py', 'scripts/inspect_cloudflare_schema.py']
TERMS = r'private_ground_truth|human_grading|README|BENCHMARK_LOCK|candidate_report|annotation|swoon|fight|trespass|falldown|climbwall|punching|expected.?rank|results/p0_cv_only|results/p1_decisions|S14|F01|MV05|ph_e2069'
BRANCH = r'(if|elif|==)[^\n]*(ITEM_0\d|ASSET_0\d|asset_0\d)'
INPUT_FORBIDDEN = (r'ITEM_0\d|ASSET_0\d|asset_0\d|\.mp4|swoon|fight|trespass|falldown|climbwall|punching|S14|F01|MV05|ph_e2069|'
                   r'ground.?truth|annotation|"event_type"|"is_incident"|"risk"|attention_queue|"same_incident"|priority_score|'
                   r'p_incident|human_grading|reviewer|gpt-6|openai|decisions api|rubric')


def main():
    files = []
    for m in MODEL_PATH_FILES:
        p = EXP_ROOT / m
        files += [x for x in p.rglob('*') if x.is_file() and x.suffix in ('.py', '.json')] if p.is_dir() else [p]
    mentions, branches = [], []
    for p in files:
        for n, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
            where = f'{p.relative_to(EXP_ROOT).as_posix()}:{n}'
            if re.search(TERMS, line, re.I):
                mentions.append({'where': where, 'line': line.strip()[:160]})
            if re.search(BRANCH, line) and 'choices=ITEM_IDS' not in line:
                branches.append({'where': where, 'line': line.strip()[:160]})
    p1 = verify_p1_freeze()
    qa = QuestionAdapter(load_json(P1_QUESTIONS_CONFIG))
    items = {}
    for item in ITEM_IDS:
        st = load_state(item, p1['compact_state_sha256'])
        raw = load_json(RAW_DIR / f'{item}.json')
        p1_raw_req = load_json(P1_ROOT / 'raw_api' / f'{item}.json')['request']   # post-run parity check only
        cams = [c['camera'] for c in st['compact']['cameras']]
        _, clef_q = qa.build(st['compact']['task'], cams)
        # state: full deny-list. questions: same deny-list applied to question *content* (instructions, criteria);
        # question ids are excluded because they are the frozen P1 question names (e.g. same_incident), not answers.
        q_content = canonical_json([[q['instructions'], q.get('criteria')] for q in clef_q.values()])
        hit = re.search(INPUT_FORBIDDEN, st['state_text'], re.I) or re.search(INPUT_FORBIDDEN, q_content, re.I)
        res = load_json(RESULTS_DIR / f'run_{item}.json')
        items[item] = {
            'state_sha256_sent': raw['request']['state_sha256'],
            'p2_state_bytes_equal_p1_input_bytes': raw['request']['state_sha256'] == p1_raw_req['input_sha256'] == st['state_text_sha256'],
            'compact_sha256_equal_p1_frozen': raw['request']['compact_state_sha256'] == p1['compact_state_sha256'][item] == p1_raw_req['compact_state_sha256'],
            'questions_equal_frozen_rebuild': raw['request']['questions_sha256'] == sha256_bytes(canonical_json(clef_q).encode('utf-8')),
            'question_names_equal_p1': [q['id'] for q in raw['request']['questions']] == [q['name'] for q in p1_raw_req['questions']],
            'question_count': len(clef_q),
            'forbidden_text_in_model_input': hit.group(0) if hit else None,
            'runtime_access_audit_pass': res['runtime_config']['access_audit']['pass'],
            'forbidden_paths_opened': res['runtime_config']['access_audit']['forbidden_paths_opened'],
        }
    load_cloudflare_env()
    scan = artifact_files(EXP_ROOT, RESULTS_DIR)
    leaks = scan_for_secrets(scan)
    keys = ('p2_state_bytes_equal_p1_input_bytes', 'compact_sha256_equal_p1_frozen', 'questions_equal_frozen_rebuild',
            'question_names_equal_p1', 'runtime_access_audit_pass')
    verdict = not branches and not leaks and all(all(v[k] for k in keys) and v['forbidden_text_in_model_input'] is None for v in items.values())
    out = {'verdict': 'PASS' if verdict else 'FAIL',
           'audit_script_revision': 'r2: first run flagged the ITEM_07 question id "same_incident" (a frozen P1 question name, '
                                    'not an answer); question ids are now excluded from the deny-list scan. No model-path change.',
           'model_path_files_scanned': len(files), 'term_mentions': mentions,
           'item_specific_branching': branches, 'items': items,
           'credentials_found_in_files': leaks, 'artifact_files_scanned_for_credentials': len(scan),
           'note': 'Term mentions are deny-lists / allowlist definitions / docstrings; none is a model input. '
                   'P1 raw_api request hashes are read only here, after the P2 model run, for byte-parity verification.'}
    write_json(LOGS_DIR / 'leakage_audit.json', out)
    for m in mentions:
        print('mention ', m['where'], '|', m['line'][:110])
    print('item-specific branching:', branches or 'none')
    for k, v in items.items():
        print(k, {x: v[x] for x in keys + ('forbidden_text_in_model_input', 'question_count')})
    print('credentials in artifacts:', leaks or 'none', f'({len(scan)} files scanned)')
    print('LEAKAGE AUDIT', out['verdict'])
    log_event('leakage_audit', {'verdict': out['verdict']})


if __name__ == '__main__':
    main()
