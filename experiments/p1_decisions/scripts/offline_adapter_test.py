"""Offline check of question building + adapters + schema validation with synthetic typed answers (no API call).
Exercises predicate/choice/score parsing and the refusal path for every task type. Synthetic values are neutral
placeholders for code-path testing only and are never written as results."""
import _bootstrap  # noqa: F401
import sys

from p1_pipeline import P1Pipeline


def synth(questions, refuse_every=0):
    out = []
    for i, q in enumerate(questions):
        if refuse_every and i % refuse_every == 0:
            out.append({'type': 'refusal', 'name': q['name']})
        elif q['type'] == 'predicate':
            out.append({'type': 'predicate', 'name': q['name'], 'probability': 0.5})
        elif q['type'] == 'choice':
            n = len(q['choices'])
            out.append({'type': 'choice', 'name': q['name'], 'choice': q['choices'][0]['value'], 'confidence': 1 / n,
                        'probabilities': [{'value': c['value'], 'probability': 1 / n} for c in q['choices']]})
        else:
            n = len(q['levels'])
            out.append({'type': 'score', 'name': q['name'], 'score': (n - 1) / 2, 'confidence': 1 / n,
                        'probabilities': [{'label': l['label'], 'value': j, 'probability': 1 / n} for j, l in enumerate(q['levels'])]})
    return out


def main(items=('ITEM_01', 'ITEM_04', 'ITEM_07')):
    p = P1Pipeline()
    ok = True
    for item in items:
        prep = p.prepare(item)
        for refuse in (0, 2):
            pred, dec, _ = p.adapt(prep['compact'], synth(prep['questions'], refuse), 'synthetic-offline')
            try:
                p.validate_prediction(pred, prep['compact']['task'], [c['camera'] for c in prep['compact']['cameras']])
                if refuse:
                    flags = [pred['human_review_required']] if 'human_review_required' in pred else [a['assessment']['human_review_required'] for a in pred['assessments']]
                    assert all(flags), 'refusal must force human review'
                print(f"{item} task={prep['compact']['task']} questions={len(prep['questions'])} refusal_mode={bool(refuse)}: PASS")
            except Exception as e:
                ok = False
                print(f'{item} refusal_mode={bool(refuse)}: FAIL {e}')
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
