"""Validate common-adapter-v2 outputs:
 - benchmark validate_prediction.py --result PASS for all 14 normalized files;
 - changed prediction paths are only *.event_type (anything else = FAIL);
 - decision fields unchanged vs v1 runtime decision_summary: p_incident, category, category confidence, risk x4,
   confidence, human_review, priority, attention order, same_incident (+ second_view_adds, multiview_value);
 - raw category preserved in metadata; is_incident/event_type consistent after v2;
 - v1 results and raw_api files byte-unchanged (vs normalize manifest); event_type_map identical to frozen P1 map.
Writes logs/validation.json."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from common_adapter_v2 import diff_paths, load_config  # noqa: E402
from normalize_p1_p2 import ITEMS, RESULTS, P1, P2, jload, jwrite, sha  # noqa: E402

DIR = {'p1': 'p1_decisions', 'p2': 'p2_clef_flash'}
INCIDENT_EVENT = re.compile(r'fall|person-down|physical conflict')


def units(pred, dsum, task):
    if task == 'attention':
        return [(a['camera'], a['assessment'], dsum['per_camera'][a['camera']]) for a in pred['assessments']]
    return [('single', pred, dsum)]


def main():
    cfg = load_config()
    ok, report = True, {'items': {}}
    if cfg['event_type_map'] != jload(P1 / 'configs' / 'decisions_questions_v1.json')['adapter']['event_type_map']:
        ok = False
        report['event_type_map_equal_p1'] = False
    else:
        report['event_type_map_equal_p1'] = True
    man = jload(ROOT / 'logs' / 'normalize_manifest.json')
    for pipe in ('p1', 'p2'):
        for item in ITEMS:
            k = f'{pipe}/{item}'
            v1p = RESULTS / DIR[pipe] / f'run_{item}.json'
            rawp = (P1 if pipe == 'p1' else P2) / 'raw_api' / f'{item}.json'
            v1, nz = jload(v1p), jload(ROOT / 'normalized' / pipe / f'run_{item}.json')
            errs = []
            if sha(v1p.read_bytes()) != man['items'][k]['v1_result_sha256'] or sha(rawp.read_bytes()) != man['items'][k]['raw_api_sha256']:
                errs.append('v1 result or raw_api changed')
            changed = diff_paths(v1['prediction'], nz['prediction'])
            bad = [c for c in changed if not c.endswith('event_type')]
            if bad:
                errs.append(f'forbidden prediction changes: {bad}')
            other = [c for c in diff_paths({k2: v for k2, v in v1.items() if k2 not in ('prediction', 'runtime_config', 'run_id')},
                                           {k2: v for k2, v in nz.items() if k2 not in ('prediction', 'runtime_config', 'run_id')})]
            if other:
                errs.append(f'result fields changed: {other}')
            rc1, rc2 = v1['runtime_config'], nz['runtime_config']
            if diff_paths({x: y for x, y in rc1.items()}, {x: y for x, y in rc2.items() if x != 'common_adapter_v2'}):
                errs.append('v1 runtime_config altered')
            task = jload(P1 / 'compact_states' / f'{item}.json')['task']
            meta = {a['assessment']: a for a in rc2['common_adapter_v2']['assessments']}
            ds = rc1['decision_summary']
            for label, a2, d in units(nz['prediction'], ds, task):
                a1 = units(v1['prediction'], ds, task)[[u[0] for u in units(v1['prediction'], ds, task)].index(label)][1]
                for f in ('is_incident', 'confidence', 'human_review_required', 'risk'):
                    if a1[f] != a2[f]:
                        errs.append(f'{label}.{f} changed')
                m = meta[label if task == 'attention' else ('single' if task == 'single' else 'multi_camera')]
                rd = m['raw_decision']
                if (rd['incident_probability'], rd['incident_category'], rd['incident_category_confidence']) != (d['p_incident'], d['category'], d['category_confidence']):
                    errs.append(f'{label}: raw decision not preserved')
                if a2['is_incident'] != (d['p_incident'] is not None and d['p_incident'] >= cfg['incident_threshold']):
                    errs.append(f'{label}: is_incident inconsistent with threshold')
                if (not a2['is_incident']) and INCIDENT_EVENT.search(a2['event_type']):
                    errs.append(f'{label}: residual contradiction is_incident=false + {a2["event_type"]}')
                if a2['is_incident'] and a2['event_type'] == 'no clear incident':
                    errs.append(f'{label}: residual reverse contradiction')
            if task == 'attention':
                if [q['camera'] for q in v1['prediction']['attention_queue']] != [q['camera'] for q in nz['prediction']['attention_queue']] \
                        or v1['prediction']['attention_queue'] != nz['prediction']['attention_queue']:
                    errs.append('attention order/priority changed')
            if task == 'multi_camera':
                for f in ('same_incident', 'additional_information_from_second_view', 'cross_camera_summary'):
                    if v1['prediction'][f] != nz['prediction'][f]:
                        errs.append(f'{f} changed')
            r = subprocess.run([sys.executable, 'scripts/validate_prediction.py', str(ROOT / 'normalized' / pipe / f'run_{item}.json'), '--result'],
                               cwd=PROJECT / 'benchmark_v1', capture_output=True, text=True)
            if r.returncode != 0:
                errs.append('validate_prediction FAIL: ' + (r.stdout + r.stderr).strip()[-200:])
            report['items'][k] = {'pass': not errs, 'errors': errs, 'changed_paths': changed,
                                  'unchanged_checked': ['p_incident', 'raw category', 'category confidence', 'is_incident', 'severity', 'imminence',
                                                        'exposure', 'persistence', 'confidence', 'human_review_required', 'attention priority/order',
                                                        'same_incident', 'all non-event_type prediction fields']}
            ok &= not errs
            print(k, 'PASS' if not errs else f'FAIL {errs}', '| changed:', changed or 'none')
    report['verdict'] = 'PASS' if ok else 'FAIL'
    report['event_type_changes'] = {p: sum(man['items'][f'{p}/{i}']['event_type_changes'] for i in ITEMS) for p in ('p1', 'p2')}
    jwrite(ROOT / 'logs' / 'validation.json', report)
    print('event_type changes:', report['event_type_changes'], '| VALIDATION', report['verdict'])
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
