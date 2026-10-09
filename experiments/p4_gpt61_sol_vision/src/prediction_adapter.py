"""Decision values (frozen P1 DecisionAdapter) + resolved visual evidence -> prediction.schema.json shape.

Vision -> Evidence (model-cited frame_ref + observable description; camera/timestamp looked up deterministically)
GPT-6.1 Sol -> Decision (typed estimates via the frozen adapter)
Explanation -> short model-generated temporal_summary / uncertainties / reason; attention queue and cross-camera texts are
deterministic templates (same structure as P1/P2/P3). event_type is set afterwards by common-adapter-v2.
"""
import types

from utils import P1_ROOT, sha256_bytes


def load_p1_decision_adapter(p1_freeze):
    rel = 'src/decision_adapter.py'
    src = (P1_ROOT / rel).read_bytes()
    if sha256_bytes(src) != p1_freeze['hashes'][rel]:
        raise RuntimeError(f'{rel} differs from p1_freeze.json')
    mod = types.ModuleType('p1_decision_adapter')
    exec(compile(src.decode('utf-8'), str(P1_ROOT / rel), 'exec'), mod.__dict__)
    return mod, sha256_bytes(src)


def _obs(evidence):
    return [{'camera': e['camera'], 'timestamp_sec': e['timestamp_sec'], 'description': e['description']} for e in evidence]


def single_prediction(d, vis, event_type_placeholder):
    return {
        'event_type': event_type_placeholder,
        'is_incident': bool(d['is_incident']),
        'observations': _obs(sorted(vis['evidence'], key=lambda e: (e['camera'], e['timestamp_sec']))),
        'temporal_summary': vis['temporal_summary'],
        'risk': {k: round(v, 4) for k, v in d['risk'].items()},
        'confidence': d['confidence'],
        'uncertainties': list(vis['uncertainties']),
        'reason': vis['reason'],
        'human_review_required': bool(d['human_review_required']),
    }


def attention_prediction(att, vis, cameras, weights):
    assessments = [{'camera': c, 'assessment': single_prediction(att['per_camera'][c], vis[c], '__set_by_common_adapter_v2__')} for c in cameras]
    af = att['attention_first_supplementary']
    queue = []
    for rank, c in enumerate(att['order'], 1):
        d = att['per_camera'][c]
        r = d['risk']
        txt = (f"Priority {d['priority_score']:.3f} = {weights['severity']}*severity {r['severity']:.2f} + {weights['imminence']}*imminence {r['imminence']:.2f} "
               f"+ {weights['exposure']}*exposure {r['exposure']:.2f} + {weights['persistence']}*persistence {r['persistence']:.2f} (GPT-6.1 Sol vision scores); "
               f"category '{d['category']}', confidence {d['confidence']:.2f} (not used in ranking).")
        if rank == 1:
            txt += (f" Supplementary attention_first answer: {af['choice']} (confidence {af['confidence']:.2f}); not used for the rank." if af
                    else ' Supplementary attention_first answer was refused.')
        queue.append({'camera': c, 'rank': rank, 'reason': txt})
    return {'assessments': assessments, 'attention_queue': queue}


def multi_prediction(d, vis, cameras):
    m = vis['multi']
    allev = [e for c in cameras for e in m['evidence_by_camera'][c]]
    base = single_prediction(d, {'evidence': allev, 'temporal_summary': m['temporal_summary'], 'uncertainties': m['uncertainties'],
                                 'reason': m['reason']}, '__set_by_common_adapter_v2__')
    base.update({
        'same_incident': bool(d['same_incident']),
        'camera_evidence': {c: _obs(sorted(m['evidence_by_camera'][c], key=lambda e: e['timestamp_sec'])) for c in cameras},
        'cross_camera_summary': (f"GPT-6.1 Sol same-incident probability {d['p_same_incident']:.2f} (threshold 0.5) -> same_incident={str(d['same_incident']).lower()}, "
                                 'judged from visual scene/action consistency across the two frame sequences. Camera synchronization is not confirmed by the input. '
                                 'Cross-camera identity is not confirmed.'),
        'additional_information_from_second_view': [
            f"GPT-6.1 Sol: second view adds useful evidence with probability {d['p_second_view_adds']:.2f}; multi-view evidence value {d['multiview_value']:.2f} (0-1)."],
    })
    return base
