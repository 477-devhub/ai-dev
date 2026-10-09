"""Strict validation before unchanged DecisionAdapter. Never turn invalid into safe."""
import math

from e2_common import read, ROOT
from decision_adapter import DecisionAdapter


def number(x, lo=0., hi=1.):
    return isinstance(x,(float,int)) and not isinstance(x,bool) and math.isfinite(x) and lo<=x<=hi


def parse_answers(answers, questions, task, cameras):
    expected = {q['name']:q for q in questions}
    indexed, seen, invalid, refused = {}, set(), [], []
    if not isinstance(answers,list): answers=[]; invalid.append('answers_not_list')
    for a in answers:
        if not isinstance(a,dict) or not isinstance(a.get('name'),str) or a.get('name') not in expected:
            invalid.append('unexpected_or_unnamed_answer'); continue
        name=a['name']; q=expected[name]
        if name in seen:
            invalid.append('duplicate:'+name); indexed.pop(name,None); continue
        seen.add(name)
        if a.get('type')=='refusal':
            indexed[name]=a; refused.append(name); continue
        valid=a.get('type')==q['type']
        if q['type']=='predicate': valid &= number(a.get('probability'))
        else:
            valid &= number(a.get('confidence'))
            probs=a.get('probabilities')
            values=[c['value'] for c in q['choices']] if q['type']=='choice' else list(range(len(q['levels'])))
            valid &= isinstance(probs,list)
            if isinstance(probs,list):
                valid &= len(probs)==len(values) and all(isinstance(x,dict) and x.get('value') in values
                    and not isinstance(x.get('value'),bool) and number(x.get('probability')) for x in probs)
                if valid:
                    valid &= len({x['value'] for x in probs})==len(values) and abs(sum(x['probability'] for x in probs)-1)<=.005
                    if q['type']=='score': valid &= all(isinstance(x['value'],int) and not isinstance(x['value'],bool) for x in probs)
            if q['type']=='choice': valid &= a.get('choice') in values
            else:
                valid &= number(a.get('score'),0,len(values)-1)
                if valid:
                    valid &= all(x.get('label')==q['levels'][x['value']]['label'] for x in probs)
                    valid &= abs(sum(x['value']*x['probability'] for x in probs)-a['score'])<=.005
        if valid: indexed[name]=a
        else: invalid.append('invalid:'+name)
    missing=sorted(set(expected)-seen)
    adapter=DecisionAdapter(read(ROOT/'configs/original.json'))
    if task=='attention': common=adapter.attention(indexed,cameras)
    elif task=='multi_camera': common=adapter.multi(indexed)
    elif task=='single': common=adapter.assessment(indexed)
    else: raise ValueError('unsupported task')
    safe={name:a.get('probability') if a['type']=='predicate' else None for name,a in indexed.items()
          if name.endswith('safe_to_suppress')}
    for name in expected:
        if name.endswith('safe_to_suppress'): safe.setdefault(name,None)
    return {'common':common,'safe_to_suppress':safe,'typed_answers':indexed,
            'missing':missing,'refused':sorted(refused),'invalid':invalid,
            'complete':not missing and not refused and not invalid}


def shadow(parsed, task, policy):
    if not parsed['complete']: return False
    assessments=list(parsed['common']['per_camera'].values()) if task=='attention' else [parsed['common']]
    for d in assessments:
        if not (d['p_incident'] is not None and d['p_incident']<=policy['incident_max']
                and not d['human_review_required'] and not d['refused_questions']
                and d['category']=='no_clear_incident' and d['confidence']>=policy['adapter_confidence_min']): return False
    if 'safe_min' in policy:
        values=list(parsed['safe_to_suppress'].values())
        if not values or any(v is None or v<policy['safe_min'] for v in values): return False
    return True
