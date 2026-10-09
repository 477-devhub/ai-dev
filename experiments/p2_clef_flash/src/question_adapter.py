"""P1 semantic questions (frozen decisions_questions_v1.json) -> Clef-Flash typed questions (API representation only).

semantic_questions() reproduces P1 decisions_client.build_questions exactly (same names, order, scope + instructions +
policy string, choices, levels). to_clef() changes only the wire format: predicate -> noul, choices -> criteria object,
levels -> criteria array. No wording, choice or level is added, removed or changed.
"""
import re

from utils import CLEF_QUESTIONS_CONFIG, load_json

ID_RE = re.compile(r'^[A-Za-z0-9_.\-]{1,100}$')


def semantic_questions(task, cameras, qcfg):
    """Identical to experiments/p1_decisions/src/decisions_client.py build_questions (P1-v1)."""
    pol = qcfg['policy']

    def q(base, scope, prefix=''):
        out = {'type': base['type'], 'name': prefix + base['key'], 'instructions': f"{scope} {base['instructions']} {pol}"}
        if base['type'] == 'choice':
            out['choices'] = [dict(c) for c in base['choices']]
        if base['type'] == 'score':
            out['levels'] = [dict(l) for l in base['levels']]
        return out

    qs = []
    if task == 'single':
        qs = [q(b, qcfg['scope']['single']) for b in qcfg['per_assessment_questions']]
    elif task == 'attention':
        for cam in cameras:
            scope = qcfg['scope']['camera'].format(camera=cam)
            qs += [q(b, scope, cam.lower().replace('_', '') + '_') for b in qcfg['per_assessment_questions']]
        allowed = set(cameras) | {'no_clear_priority'}
        for b in qcfg['attention_questions']:
            b = dict(b, choices=[c for c in b['choices'] if c['value'] in allowed])
            qs.append(q(b, ''))
    elif task == 'multi_camera':
        scope = qcfg['scope']['multi_camera']
        qs = [q(b, scope) for b in qcfg['per_assessment_questions'] + qcfg['multi_camera_questions']]
    else:
        raise ValueError(task)
    for x in qs:
        x['instructions'] = x['instructions'].strip()
    return qs


class QuestionAdapter:
    def __init__(self, p1_qcfg):
        self.p1 = p1_qcfg
        self.cfg = load_json(CLEF_QUESTIONS_CONFIG)
        self.type_map = self.cfg['type_map']

    def semantic(self, task, cameras):
        return semantic_questions(task, cameras, self.p1)

    def to_clef(self, semantic):
        out = {}
        for s in semantic:
            if not ID_RE.match(s['name']) or s['name'] in out:
                raise ValueError(f"question id not representable in Clef: {s['name']}")
            q = {'type': self.type_map[s['type']], 'instructions': s['instructions']}
            if s['type'] == 'choice':
                q['criteria'] = {c['value']: c['description'] for c in s['choices']}
            elif s['type'] == 'score':
                q['criteria'] = [{'label': l['label'], 'description': l['description']} for l in s['levels']]
            out[s['name']] = q
        if not 1 <= len(out) <= 64:
            raise ValueError(f'Clef supports 1-64 questions per request, got {len(out)}')
        return out

    def build(self, task, cameras):
        sem = self.semantic(task, cameras)
        return sem, self.to_clef(sem)
