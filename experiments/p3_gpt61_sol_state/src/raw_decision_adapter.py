"""P3 structured output -> canonical raw decision representation -> P1 typed-answer records.

canonical(): provider-neutral raw record per assessment (incident_probability, raw_category, raw_category_confidence,
severity..persistence in [0,1], human_review_probability, probability_source='model_generated_estimate').
to_p1_answers(): the representation the frozen P1 DecisionAdapter consumes (predicate probability, choice
choice/confidence, score = value*(n_levels-1) so the frozen adapter's score/(n_levels-1) returns the same 0-1 value).
A refusal turns every question into {'type':'refusal'} (frozen P1 refusal path). Values are copied, never rescaled
beyond that exact linear mapping.
"""
PROBABILITY_SOURCE = 'model_generated_estimate'
RISK = ('severity', 'imminence', 'exposure', 'persistence')


def canonical(a):
    return {'incident_probability': a['incident']['probability'],
            'raw_category': a['incident_category']['value'], 'raw_category_confidence': a['incident_category']['confidence'],
            **{k: a[k]['score'] for k in RISK},
            'human_review_probability': a['human_review']['probability'],
            'probability_source': PROBABILITY_SOURCE}


class RawDecisionAdapter:
    def __init__(self, p1_qcfg):
        self.levels = {b['key']: len(b['levels']) for b in p1_qcfg['per_assessment_questions'] + p1_qcfg['multi_camera_questions']
                       if b['type'] == 'score'}

    def _assessment_answers(self, a, prefix=''):
        c = canonical(a)
        return [
            {'type': 'predicate', 'name': prefix + 'incident', 'probability': c['incident_probability']},
            {'type': 'choice', 'name': prefix + 'incident_category', 'choice': c['raw_category'], 'confidence': c['raw_category_confidence'],
             'probabilities': None},
            *[{'type': 'score', 'name': prefix + k, 'score': c[k] * (self.levels[k] - 1), 'confidence': None, 'probabilities': None} for k in RISK],
            {'type': 'predicate', 'name': prefix + 'human_review', 'probability': c['human_review_probability']},
        ]

    def convert(self, task, parsed, semantic_names):
        """Returns (p1_style_answers, canonical_raw). parsed=None means refusal."""
        if parsed is None:
            return [{'type': 'refusal', 'name': n} for n in semantic_names], None
        if task == 'single':
            return self._assessment_answers(parsed), {'assessment': canonical(parsed)}
        if task == 'attention':
            ans, raw = [], {'per_camera': {}}
            for cam, a in parsed['camera_assessments'].items():
                ans += self._assessment_answers(a, cam.lower().replace('_', '') + '_')
                raw['per_camera'][cam] = canonical(a)
            af = parsed['attention_first']
            ans.append({'type': 'choice', 'name': 'attention_first', 'choice': af['camera'], 'confidence': af['confidence'], 'probabilities': None})
            raw['attention_first'] = {'camera': af['camera'], 'confidence': af['confidence'], 'probability_source': PROBABILITY_SOURCE}
            return ans, raw
        ans = self._assessment_answers(parsed)
        ans += [{'type': 'predicate', 'name': 'same_incident', 'probability': parsed['same_incident']['probability']},
                {'type': 'predicate', 'name': 'second_view_adds', 'probability': parsed['second_view_adds']['probability']},
                {'type': 'score', 'name': 'multiview_value', 'score': parsed['multiview_value']['score'] * (self.levels['multiview_value'] - 1),
                 'confidence': None, 'probabilities': None}]
        raw = {'assessment': canonical(parsed), 'same_incident_probability': parsed['same_incident']['probability'],
               'second_view_adds_probability': parsed['second_view_adds']['probability'],
               'multiview_value': parsed['multiview_value']['score'], 'probability_source': PROBABILITY_SOURCE}
        return ans, raw
