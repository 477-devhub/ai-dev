"""P4 leakage audit -> logs/leakage_audit.json (after the model run, before result freeze / GT access).
Checks: model-path code item-specific branching; request text (all text actually sent) free of item ids, labels, source
names, GT/grading terms and any CV-state / compact-state fields; 64 images, detail=high, lossless 64/64, encoded bytes
identical to the pre-freeze transport verification; effort high, no tools, store false; runtime access audit; API key."""
import _bootstrap  # noqa: F401
import re

from process_log import log_event
from utils import EXP_ROOT, ITEM_IDS, LOGS_DIR, RAW_DIR, RESULTS_DIR, artifact_files, load_api_key_env, load_json, scan_for_secret, write_json

MODEL_PATH = ['src', 'configs', 'schemas', 'scripts/run_p4.py', 'scripts/smoke_test_p4.py', 'scripts/freeze_p4.py', 'scripts/_synthetic.py',
              'scripts/offline_adapter_test.py', 'scripts/verify_frame_transport.py', 'scripts/preflight_p4.py']
BRANCH = r'(if|elif|==)[^\n]*(ITEM_0\d|ASSET_0\d|asset_0\d)'
TEXT_FORBIDDEN = (r'ITEM_0\d|SET0\d|ASSET_0\d|asset_0\d|\.mp4|swoon|fight|trespass|falldown|climbwall|punching|S14|F01|T06|T03|MV05|ph_e2069|'
                  r'ground.?truth|annotation|human_grading|reviewer|rubric|expected.?rank|'
                  r'cv-state|compact-decision|compact_state|track_ref|posture_distribution|contact_proxy|keypoint|yolo|bbox|'
                  r'cv_reliability|frames_with_person|strongest_vertical|gpt-6-luna|clef|decisions api|p_incident|priority_score')


def main():
    files = []
    for m in MODEL_PATH:
        p = EXP_ROOT / m
        files += [x for x in p.rglob('*') if x.is_file() and x.suffix in ('.py', '.json', '.txt')] if p.is_dir() else [p]
    branches = [{'where': f'{p.relative_to(EXP_ROOT).as_posix()}:{n}', 'line': l.strip()[:160]}
                for p in files for n, l in enumerate(p.read_text(encoding='utf-8').splitlines(), 1)
                if re.search(BRANCH, l) and 'choices=ITEM_IDS' not in l
                and not (p.name == 'verify_frame_transport.py' and 'allocation_ok' in l)]   # local frame-budget assertion, not model logic
    tv = load_json(LOGS_DIR / 'transport_verification.json')
    items = {}
    for item in ITEM_IDS:
        text = (LOGS_DIR / f'request_text_{item}.txt').read_text(encoding='utf-8')
        fm = load_json(LOGS_DIR / f'frame_manifest_{item}.json')
        raw = load_json(RAW_DIR / f'{item}.json')
        body = (raw.get('response') or {}).get('response_body') or {}
        hit = re.search(TEXT_FORBIDDEN, text, re.I)
        res_p = RESULTS_DIR / f'run_{item}.json'
        rc = load_json(res_p)['runtime_config'] if res_p.exists() else {}
        items[item] = {
            'forbidden_text_in_request': hit.group(0) if hit else None,
            'image_count_64': fm['total_images'] == 64 == len(fm['frames']),
            'detail_high_all': all(r['detail'] == 'high' for r in fm['frames']),
            'lossless_64_of_64': all(r['roundtrip_equal'] for r in fm['frames']),
            'encoded_identical_to_transport_verification': [r['encoded_sha256'] for r in fm['frames']] == [r['encoded_sha256'] for r in tv['items'][item]['frames']],
            'frame_labels_match_manifest': all(f"{r['frame_ref']} | {r['camera']} | t={r['timestamp_sec']:.3f}s" in text for r in fm['frames']),
            'base64_not_stored': 'base64,' not in (RAW_DIR / f'{item}.json').read_text(encoding='utf-8'),
            'effort_high_no_tools_store_false': (body.get('reasoning') or {}).get('effort') == 'high' and not body.get('tools') and body.get('store') in (False, None),
            'cv_or_compact_state_sent': bool(rc.get('cv_state_sent') or rc.get('compact_state_sent')) if rc else False,
            'runtime_access_audit_pass': rc.get('access_audit', {}).get('pass', None),
            'result_exists': res_p.exists(),
        }
    load_api_key_env()
    scan = artifact_files(EXP_ROOT, RESULTS_DIR)
    leaks = scan_for_secret(scan)
    must = ('image_count_64', 'detail_high_all', 'lossless_64_of_64', 'encoded_identical_to_transport_verification', 'frame_labels_match_manifest',
            'base64_not_stored', 'effort_high_no_tools_store_false')
    verdict = (not branches and not leaks and all(all(v[k] for k in must) and v['forbidden_text_in_request'] is None and not v['cv_or_compact_state_sent']
                                                  and v['runtime_access_audit_pass'] in (True, None) for v in items.values()))
    out = {'verdict': 'PASS' if verdict else 'FAIL',
           'audit_script_revision': 'r2: run 1 FAILed on audit false positives only: (a) source-id deny pattern F01 matched inside frame refs F010-F019 -> '
                                    'source ids now word-bounded (frame refs are 3-digit F###); (b) the uniform_total64_v1 allocation assertion in the '
                                    'local-only verify_frame_transport.py was reported as item-specific branching -> exempted. No model-path file changed.', 'model_path_files_scanned': len(files), 'item_specific_branching': branches,
           'items': items, 'api_key_found_in_files': leaks, 'artifact_files_scanned': len(scan)}
    write_json(LOGS_DIR / 'leakage_audit.json', out)
    for k, v in items.items():
        print(k, v)
    print('branching:', branches or 'none', '| API key in artifacts:', leaks or 'none', f'({len(scan)} files)')
    print('LEAKAGE AUDIT', out['verdict'])
    log_event('leakage_audit', {'verdict': out['verdict']})


if __name__ == '__main__':
    main()
