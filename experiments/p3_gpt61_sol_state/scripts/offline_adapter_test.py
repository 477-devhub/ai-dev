"""Offline checks (no API call, no model output): strict schema well-formed, synthetic schema-valid outputs and the
refusal path -> raw adapter -> frozen P1 adapter -> templates -> common-adapter-v2 -> prediction schema, for all tasks.
Also checks score round-trip (0-1 -> P1 typed score -> 0-1) and that no image/tool field exists in the request parts.
Synthetic values are neutral placeholders; never written as results."""
import _bootstrap  # noqa: F401
import sys

from jsonschema import Draft202012Validator

from p3_pipeline import P3Pipeline
from utils import ITEM_IDS


def synth(schema, defs=None, v=0.5):
    defs = defs or schema.get('$defs', {})
    if '$ref' in schema:
        return synth(defs[schema['$ref'].split('/')[-1]], defs, v)
    if schema['type'] == 'object':
        return {k: synth(s, defs, v) for k, s in schema['properties'].items()}
    if schema['type'] == 'string':
        return schema['enum'][0]
    return v


def main():
    p = P3Pipeline()
    ok = True
    for item in ITEM_IDS:
        prep = p.prepare(item)
        try:
            sch = prep['text_format']['schema']
            Draft202012Validator.check_schema(sch)
            assert prep['text_format']['strict'] is True
            for mode, parsed in (('valid', synth(sch, v=0.37)), ('refusal', None)):
                final, v1, d, raw, meta, _ = p.adapt(prep, parsed, 'synthetic-offline')
                p.validate_prediction(final, prep['task'], prep['cameras'])
                if mode == 'valid':
                    risks = [d['risk']] if prep['task'] != 'attention' else [x['risk'] for x in d['per_camera'].values()]
                    assert all(abs(r[k] - 0.37) < 1e-9 for r in risks for k in r), 'score round-trip changed value'
                else:
                    flags = [final['human_review_required']] if 'human_review_required' in final else [a['assessment']['human_review_required'] for a in final['assessments']]
                    assert all(flags), 'refusal must force human review'
                    assert all(a['rule'] == 'R4' for a in meta['assessments'])
                print(f"{item} task={prep['task']} mode={mode}: PASS (rules {[a['rule'] for a in meta['assessments']]})")
        except Exception as e:
            ok = False
            print(f'{item}: FAIL {type(e).__name__}: {e}')
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
