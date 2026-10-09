"""Offline P1-v1 / P2-v1 -> common-adapter-v2 normalization. No API call. Frozen v1 artifacts are read-only.

Per item:
 1. re-derive the decision from the stored raw answers with the frozen P1 decision_adapter.py (hash-checked);
 2. rebuild the v1 prediction with the frozen templates and require byte-equality with the stored v1 prediction
    (proves the offline path reproduces the official v1 record exactly);
 3. apply common-adapter-v2 to the stored v1 prediction (only event_type may change);
 4. write normalized/<p1|p2>/run_ITEM_XX.json (result.schema shape) + logs/normalize_manifest.json.
"""
import ast
import copy
import datetime
import hashlib
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from common_adapter_v2 import CommonAdapterV2, diff_paths  # noqa: E402

P1 = PROJECT / 'experiments' / 'p1_decisions'
P2 = PROJECT / 'experiments' / 'p2_clef_flash'
RESULTS = PROJECT / 'benchmark_v1' / 'results'
ITEMS = [f'ITEM_{i:02d}' for i in range(1, 8)]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def jload(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def jwrite(p, v):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def frozen_module(root, rel, expected, name, subs=()):
    src = (root / rel).read_bytes()
    if sha(src) != expected:
        raise SystemExit(f'{root.name}/{rel} differs from its freeze record')
    text = src.decode('utf-8')
    for old, new in subs:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    m = types.ModuleType(name)
    exec(compile(text, str(root / rel), 'exec'), m.__dict__)
    return m


def p2_substitutions(p2_freeze):
    rel = 'src/prediction_adapter.py'
    src = (P2 / rel).read_bytes()
    if sha(src) != p2_freeze['hashes'][rel]:
        raise SystemExit('P2 prediction_adapter.py differs from p2_freeze.json')
    tree = ast.parse(src.decode('utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.Assign) and n.targets[0].id == 'PROVIDER_SUBSTITUTIONS')
    return ast.literal_eval(node.value)


def main():
    p1f, p2f = jload(P1 / 'freeze' / 'p1_freeze.json'), jload(P2 / 'freeze' / 'p2_freeze.json')
    qcfg = jload(P1 / 'configs' / 'decisions_questions_v1.json')
    if sha((P1 / 'configs' / 'decisions_questions_v1.json').read_bytes()) != p1f['hashes']['configs/decisions_questions_v1.json']:
        raise SystemExit('P1 questions config changed')
    da = frozen_module(P1, 'src/decision_adapter.py', p1f['hashes']['src/decision_adapter.py'], 'p1_da')
    adapter = da.DecisionAdapter(qcfg)
    tpl = {'p1': frozen_module(P1, 'src/prediction_adapter.py', p1f['hashes']['src/prediction_adapter.py'], 'p1_tpl'),
           'p2': frozen_module(P1, 'src/prediction_adapter.py', p1f['hashes']['src/prediction_adapter.py'], 'p2_tpl', p2_substitutions(p2f))}
    v2 = CommonAdapterV2()
    manifest = {'built_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'api_calls': 0,
                'adapter_config_sha256': sha((ROOT / 'config' / 'adapter_v2.json').read_bytes()),
                'adapter_src_sha256': sha((ROOT / 'src' / 'common_adapter_v2.py').read_bytes()), 'items': {}}
    for pipe, rdir, raw_root in (('p1', 'p1_decisions', P1), ('p2', 'p2_clef_flash', P2)):
        for item in ITEMS:
            res_path = RESULTS / rdir / f'run_{item}.json'
            raw_path = raw_root / 'raw_api' / f'{item}.json'
            v1 = jload(res_path)
            raw = jload(raw_path)
            answers = raw['response']['answers'] if pipe == 'p1' else raw['normalized_answers']
            ans = da.index_answers(answers)
            compact = jload(P1 / 'compact_states' / f'{item}.json')
            if sha((P1 / 'compact_states' / f'{item}.json').read_bytes()) != p1f['compact_state_sha256'][item]:
                raise SystemExit(f'{item}: compact state changed')
            task, model = compact['task'], v1['runtime_config']['decision_model_returned']
            t = tpl[pipe]
            if task == 'single':
                dec = adapter.assessment(ans)
                rebuilt = t.single_prediction(dec, compact['cameras'], model)
            elif task == 'attention':
                dec = adapter.attention(ans, [c['camera'] for c in compact['cameras']])
                rebuilt = t.attention_prediction(dec, compact, model, qcfg['adapter']['priority_weights'])
            else:
                dec = adapter.multi(ans)
                rebuilt = t.multi_prediction(dec, compact, model)
            reproduce = diff_paths(v1['prediction'], rebuilt)
            if reproduce:
                raise SystemExit(f'{pipe} {item}: offline v1 rebuild differs from stored v1 prediction at {reproduce[:5]}')
            pred2, meta = v2.apply(v1['prediction'], dec, task)
            changed = diff_paths(v1['prediction'], pred2)
            out = copy.deepcopy(v1)
            out['run_id'] = v1['run_id'] + '+common-adapter-v2'
            out['prediction'] = pred2
            out['runtime_config'] = dict(v1['runtime_config'], common_adapter_v2=dict(
                meta, source_v1_result=f'benchmark_v1/results/{rdir}/run_{item}.json', source_v1_result_sha256=sha(res_path.read_bytes()),
                source_raw_api=f'experiments/{raw_root.name}/raw_api/{item}.json', source_raw_api_sha256=sha(raw_path.read_bytes()),
                offline_rebuild_equals_v1=True, api_calls=0,
                note='v1 result is the official raw experiment record; this file is the normalized common-adapter-v2 presentation'))
            jwrite(ROOT / 'normalized' / pipe / f'run_{item}.json', out)
            manifest['items'][f'{pipe}/{item}'] = {'v1_result_sha256': sha(res_path.read_bytes()), 'raw_api_sha256': sha(raw_path.read_bytes()),
                                                   'normalized_sha256': sha((ROOT / 'normalized' / pipe / f'run_{item}.json').read_bytes()),
                                                   'changed_prediction_paths': changed, 'event_type_changes': meta['event_type_changes'],
                                                   'rules': [a['rule'] for a in meta['assessments']]}
            print(f"{pipe} {item}: v1 rebuild OK; changed={changed or 'none'}; rules={[a['rule'] for a in meta['assessments']]}")
    jwrite(ROOT / 'logs' / 'normalize_manifest.json', manifest)


if __name__ == '__main__':
    main()
