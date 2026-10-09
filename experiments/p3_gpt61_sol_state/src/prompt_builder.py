"""Builds the P3 Responses request parts from frozen artifacts only:
  instructions = configs/p3_prompt_v1.txt + decision definitions rendered from the frozen P1 decisions_questions_v1.json
                 (same question wording, scope sentences, policy, category choices and level descriptions as P1/P2)
  input        = compact state text (byte-identical to the P1/P2 input)
  text.format  = strict json_schema built from schemas/p3_decision_output.schema.json for the task/cameras.
Nothing item-specific except the task type and the generic camera ids present in the state.
"""
import copy

from utils import P1_QUESTIONS_CONFIG, P3_PROMPT, P3_SCHEMA, read_allowed_json, read_allowed_text

OUTPUT_FIELD = {'predicate': 'probability', 'choice': 'value + confidence', 'score': 'score'}


def _fmt_question(q, field_prefix=''):
    name = field_prefix + q['key']
    if q['type'] == 'predicate':
        lines = [f"- {name}.probability: probability in [0,1] that the answer is yes. Question: {q['instructions']}"]
    elif q['type'] == 'choice':
        lines = [f"- {name}: choose exactly one value and give your confidence in [0,1]. Question: {q['instructions']}"]
        lines += [f"    * {c['value']}: {c['description']}" for c in q['choices']]
    else:
        n = len(q['levels'])
        lines = [f"- {name}.score: a value in [0,1]; anchors below, intermediate values allowed. Question: {q['instructions']}"]
        lines += [f"    * {k / (n - 1):.2f} = {l['label']}: {l['description']}" for k, l in enumerate(q['levels'])]
    return lines


class PromptBuilder:
    def __init__(self):
        self.base = read_allowed_text(P3_PROMPT).strip()
        self.q = read_allowed_json(P1_QUESTIONS_CONFIG)
        self.tpl = read_allowed_json(P3_SCHEMA)

    def instructions(self, task, cameras):
        q = self.q
        L = [self.base, '', 'Decision policy (applies to every decision): ' + q['policy'], '']
        per = [x for b in q['per_assessment_questions'] for x in _fmt_question(b)]
        if task == 'single':
            L += ['Task: one camera. ' + q['scope']['single'], 'Decisions (top-level fields):'] + per
        elif task == 'attention':
            L += ['Task: concurrent alerts from several cameras. Produce one assessment per camera under camera_assessments.<camera>.']
            L += ['For camera_assessments.' + c + ': ' + q['scope']['camera'].format(camera=c) for c in cameras]
            L += ['Decisions for each camera assessment:'] + per + ['', 'Additional decision (top-level field):']
            for b in q['attention_questions']:
                b = dict(b, choices=[c for c in b['choices'] if c['value'] in set(cameras) | {'no_clear_priority'}])
                L += [x.replace(f"- {b['key']}: choose exactly one value", f"- {b['key']}.camera: choose exactly one value") for x in _fmt_question(b)]
        elif task == 'multi_camera':
            L += ['Task: several camera views. ' + q['scope']['multi_camera'], 'Decisions (top-level fields):'] + per
            L += [x for b in q['multi_camera_questions'] for x in _fmt_question(b)]
        else:
            raise ValueError(task)
        return '\n'.join(L).strip() + '\n'

    def output_schema(self, task, cameras):
        t = copy.deepcopy(self.tpl)
        a = t['assessment']
        if task == 'single':
            return a
        if task == 'attention':
            af = t['attention_first']
            af['properties']['camera']['enum'] = list(cameras) + ['no_clear_priority']
            return {'type': 'object', 'additionalProperties': False, 'required': ['camera_assessments', 'attention_first'],
                    '$defs': {'assessment': a},
                    'properties': {'camera_assessments': {'type': 'object', 'additionalProperties': False, 'required': list(cameras),
                                                          'properties': {c: {'$ref': '#/$defs/assessment'} for c in cameras}},
                                   'attention_first': af}}
        if task == 'multi_camera':
            s = copy.deepcopy(a)
            s['properties'].update(t['multi_camera_extra'])
            s['required'] = s['required'] + list(t['multi_camera_extra'])
            return s
        raise ValueError(task)

    def text_format(self, task, cameras):
        return {'type': 'json_schema', 'name': f'p3_decision_{task}', 'strict': True, 'schema': self.output_schema(task, cameras)}
