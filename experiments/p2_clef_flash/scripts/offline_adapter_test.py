"""Offline checks (no API call, no model output):
1. semantic question parity: P2 semantic_questions() == P1 decisions_client.build_questions (function extracted from the
   frozen P1 source by AST, hash-checked) for every item task/camera set;
2. Clef wire format: ids/order/instructions/choices/levels preserved; predicate->noul only;
3. synthetic Clef-shaped answers -> normalizer -> frozen P1 adapter -> prediction schema, incl. invalid/missing answers.
Synthetic values are neutral placeholders for code-path testing only and are never written as results."""
import _bootstrap  # noqa: F401
import ast
import sys

from p2_pipeline import P2Pipeline
from utils import P1_ROOT, sha256_bytes


def p1_build_questions(p1_freeze):
    rel = 'src/decisions_client.py'
    src = (P1_ROOT / rel).read_bytes()
    assert sha256_bytes(src) == p1_freeze['hashes'][rel], 'P1 decisions_client.py changed'
    tree = ast.parse(src.decode('utf-8'))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'build_questions')
    ns = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), 'p1_build_questions', 'exec'), ns)
    return ns['build_questions']


def synth_clef(clef_q, mode):
    out = {}
    for i, (k, q) in enumerate(clef_q.items()):
        if mode == 'invalid' and i % 2 == 0:
            if i % 4 == 0:
                continue                       # missing answer
            out[k] = {'type': q['type']}        # schema-invalid answer
            continue
        if q['type'] == 'noul':
            out[k] = {'type': 'noul', 'noul': 0.5}
        elif q['type'] == 'choice':
            n = len(q['criteria'])
            out[k] = {'type': 'choice', 'choice': next(iter(q['criteria'])), 'confidence': 1 / n,
                      'probabilities': {c: 1 / n for c in q['criteria']}}
        else:
            n = len(q['criteria'])
            out[k] = {'type': 'score', 'score': (n - 1) / 2, 'confidence': 1 / n, 'legend': {str(j): c for j, c in enumerate(q['criteria'])},
                      'probabilities': {str(j): 1 / n for j in range(n)}}
    return out


def main(items=('ITEM_01', 'ITEM_02', 'ITEM_03', 'ITEM_04', 'ITEM_05', 'ITEM_06', 'ITEM_07')):
    p = P2Pipeline()
    build = p1_build_questions(p.p1_freeze)
    ok = True
    for item in items:
        prep = p.prepare(item)
        task, cams = prep['compact']['task'], prep['cameras']
        try:
            sem = prep['semantic_questions']
            assert sem == build(task, cams, p.p1_qcfg), 'semantic questions differ from P1 build_questions'
            cq = prep['clef_questions']
            assert list(cq) == [s['name'] for s in sem], 'ids/order differ'
            for s in sem:
                c = cq[s['name']]
                assert c['instructions'] == s['instructions']
                assert c['type'] == {'predicate': 'noul', 'choice': 'choice', 'score': 'score'}[s['type']]
                if s['type'] == 'choice':
                    assert list(c['criteria'].items()) == [(x['value'], x['description']) for x in s['choices']]
                elif s['type'] == 'score':
                    assert c['criteria'] == [{'label': x['label'], 'description': x['description']} for x in s['levels']]
                else:
                    assert 'criteria' not in c
            print(f"{item} task={task} questions={len(cq)}: semantic parity with P1 PASS")
            for mode in ('valid', 'invalid'):
                norm, issues = p.norm.normalize(sem, synth_clef(cq, mode))
                pred, _, _ = p.adapt(prep['compact'], norm, 'synthetic-offline')
                p.validate_prediction(pred, task, cams)
                if mode == 'invalid':
                    assert issues
                    flags = [pred['human_review_required']] if 'human_review_required' in pred else [a['assessment']['human_review_required'] for a in pred['assessments']]
                    assert all(flags), 'invalid/missing answers must force human review'
                print(f"{item} mode={mode}: adapter + prediction schema PASS")
        except Exception as e:
            ok = False
            print(f'{item}: FAIL {type(e).__name__}: {e}')
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
