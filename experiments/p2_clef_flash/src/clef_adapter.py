"""Clef-Flash answers -> P1 normalized answer records -> frozen P1 DecisionAdapter (unchanged bytes).

normalize(): wire-format conversion only (noul -> predicate probability; probabilities object -> P1 list form). Raw Clef
values are copied, never rescaled. A missing or schema-invalid answer becomes {'type': 'refusal'} so the frozen P1
refusal path applies (Clef defines no refusal type).
load_p1_decision_adapter(): imports experiments/p1_decisions/src/decision_adapter.py from its exact bytes after checking
the SHA256 recorded in p1_freeze.json, so P1 and P2 share one deterministic mapping (thresholds, confidence formula,
score normalization, priority weights, attention tie-break, event_type map - no reconciliation).
"""
import math
import types

from jsonschema import Draft202012Validator

from utils import CLEF_RESPONSE_SCHEMA, P1_ROOT, load_json, sha256_bytes

PROB_SUM_TOL = 0.02


def _load_frozen_module(rel, p1_freeze, name):
    src = (P1_ROOT / rel).read_bytes()
    if sha256_bytes(src) != p1_freeze['hashes'][rel]:
        raise RuntimeError(f'{rel} differs from p1_freeze.json')
    mod = types.ModuleType(name)
    mod.__file__ = str(P1_ROOT / rel)
    exec(compile(src.decode('utf-8'), mod.__file__, 'exec'), mod.__dict__)
    return mod, sha256_bytes(src)


def load_p1_decision_adapter(p1_freeze):
    return _load_frozen_module('src/decision_adapter.py', p1_freeze, 'p1_decision_adapter')


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _probs_ok(d):
    return isinstance(d, dict) and d and all(_num(v) and 0 <= v <= 1 for v in d.values()) and abs(sum(d.values()) - 1) <= PROB_SUM_TOL


def _level_index(key, levels, legend):
    """Map a Clef score probability key to the 0-based level index (keys are level indices per the live schema)."""
    k = str(key)
    if k.isdigit() and int(k) < len(levels):
        return int(k)
    for i, l in enumerate(levels):
        if k == l['label']:
            return i
    return None


class ClefAnswerNormalizer:
    def __init__(self):
        self.validator = Draft202012Validator(load_json(CLEF_RESPONSE_SCHEMA))

    def validate_response(self, out):
        return [f"{'/'.join(map(str, e.path))}: {e.message}" for e in self.validator.iter_errors(out)]

    def normalize(self, semantic, answers):
        """Returns (normalized_answers_in_question_order, issues)."""
        norm, issues = [], []
        for q in semantic:
            name, a = q['name'], (answers or {}).get(q['name'])
            rec, why = None, None
            if not isinstance(a, dict):
                why = 'missing'
            elif q['type'] == 'predicate':
                if a.get('type') == 'noul' and _num(a.get('noul')) and 0 <= a['noul'] <= 1:
                    rec = {'type': 'predicate', 'name': name, 'probability': a['noul']}
                else:
                    why = 'invalid noul'
            elif q['type'] == 'choice':
                vals = [c['value'] for c in q['choices']]
                p = a.get('probabilities')
                if (a.get('type') == 'choice' and a.get('choice') in vals and _num(a.get('confidence')) and _probs_ok(p)
                        and set(p) <= set(vals)):
                    rec = {'type': 'choice', 'name': name, 'choice': a['choice'], 'confidence': a['confidence'],
                           'probabilities': [{'value': v, 'probability': p.get(v, 0.0)} for v in vals]}
                else:
                    why = 'invalid choice'
            else:
                lv = q['levels']
                p = a.get('probabilities')
                idx = {k: _level_index(k, lv, a.get('legend')) for k in (p or {})} if isinstance(p, dict) else {}
                if (a.get('type') == 'score' and _num(a.get('score')) and _num(a.get('confidence')) and _probs_ok(p)
                        and all(i is not None for i in idx.values()) and len(set(idx.values())) == len(idx)):
                    by = {idx[k]: v for k, v in p.items()}
                    rec = {'type': 'score', 'name': name, 'score': a['score'], 'confidence': a['confidence'],
                           'probabilities': [{'label': l['label'], 'value': i, 'probability': by.get(i, 0.0)} for i, l in enumerate(lv)]}
                else:
                    why = 'invalid score'
            if rec is None:
                rec = {'type': 'refusal', 'name': name}
                issues.append({'question': name, 'reason': why})
            norm.append(rec)
        extra = sorted(set(answers or {}) - {q['name'] for q in semantic})
        if extra:
            issues.append({'unexpected_answer_ids': extra})
        return norm, issues
