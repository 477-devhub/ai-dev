"""Maps P0 rule-engine assessments onto benchmark_v1/schemas/prediction.schema.json (unchanged)."""
from utils import rnd

QUEUE_KEYS = {
    'priority_score_desc': lambda a, i: -a['priority_score'],
    'severity_desc': lambda a, i: -a['risk']['severity'],
    'confidence_desc': lambda a, i: -a['confidence'],
    'input_camera_order_asc': lambda a, i: i,
}


def single_prediction(a):
    return {
        'event_type': a['event_type'],
        'is_incident': a['is_incident'],
        'observations': a['observations'],
        'temporal_summary': a['temporal_summary'],
        'risk': a['risk'],
        'confidence': a['confidence'],
        'uncertainties': a['uncertainties'],
        'reason': a['reason'],
        'human_review_required': a['human_review_required'],
    }


def order_assessments(assessments, tie_break):
    idx = list(range(len(assessments)))
    idx.sort(key=lambda i: tuple(QUEUE_KEYS[k](assessments[i], i) for k in tie_break))
    return idx


def attention_prediction(assessments, rules):
    order = order_assessments(assessments, rules['attention']['tie_break'])
    queue = []
    for rank, i in enumerate(order, start=1):
        a = assessments[i]
        r = a['risk']
        reason = (f"Priority score {a['priority_score']:.3f} = 0.35*severity {r['severity']:.2f} + 0.30*imminence {r['imminence']:.2f} "
                  f"+ 0.20*exposure {r['exposure']:.2f} + 0.15*persistence {r['persistence']:.2f}; P0 pattern: {a['event_type']}; "
                  f"confidence {a['confidence']:.2f} (not used in ranking).")
        if rank < len(order):
            nxt = assessments[order[rank]]
            if nxt['priority_score'] == a['priority_score']:
                reason += ' Tie on priority broken by configured order: ' + ', '.join(rules['attention']['tie_break']) + '.'
        queue.append({'camera': a['camera'], 'rank': rank, 'reason': reason})
    return {
        'assessments': [{'camera': a['camera'], 'assessment': single_prediction(a)} for a in assessments],
        'attention_queue': queue,
    }


def multi_prediction(assessments, cross, cam_states, rules):
    mc = rules['multi_camera']
    order = order_assessments(assessments, rules['attention']['tie_break'])
    primary = assessments[order[0]]
    risk = {k: max(a['risk'][k] for a in assessments) for k in ('severity', 'imminence', 'exposure', 'persistence')}
    enough = all(sum(1 for t in c['tracks'] if t['detection']['observed_frames'] >= mc['min_track_observations_each_camera']) > 0 for c in cam_states)
    score = cross['same_incident_similarity_score'] if cross else None
    same = bool(enough and score is not None and score >= mc['same_incident_threshold'])
    ca, cb = cross['camera_a'], cross['camera_b']
    observations = [o for a in assessments for o in a['observations']]
    uncertainties = []
    for a in assessments:
        for u in a['uncertainties']:
            if u not in uncertainties:
                uncertainties.append(u)
    uncertainties += [
        'The two clips have independent time origins and no confirmed synchronization; only normalized-phase comparisons were made.',
        'Person identity across cameras is not linked or confirmed by this CV-only pipeline.',
        f"same_incident is a threshold ({mc['same_incident_threshold']}) on a low-level observation-similarity score ({_f(score)}), not a verified correspondence.",
    ]
    summary = (f"Observation-pattern similarity between {ca} and {cb}: {_f(score)} "
               f"(person count {_f(cross['person_count_similarity'])}, temporal pattern {_f(cross['temporal_pattern_similarity'])}, "
               f"motion peaks {_f(cross['motion_peak_similarity'])}, incident signature {_f(cross['incident_signature_similarity'])}, "
               f"posture transition {_f(cross['posture_transition_similarity'])}). "
               + ('The two camera streams show similar observation patterns' if same else 'The observation patterns are not similar enough to treat the views as the same incident')
               + ', but identity continuity and time synchronization cannot be confirmed by this CV-only pipeline. '
               f"Visibility complementarity score {_f(cross['visibility_complementarity_score'])}.")
    extra = []
    labels = {a['camera']: a for a in assessments}
    for a, b in ((ca, cb), (cb, ca)):
        ka = {c['kind'] for c in labels[a]['candidates']}
        kb = {c['kind'] for c in labels[b]['candidates']}
        for kind in sorted(ka - kb):
            if kind in ('none', 'no_person', 'uncertain'):
                continue
            onset = next(c['onset_sec'] for c in labels[a]['candidates'] if c['kind'] == kind)
            extra.append(f"{a} shows a '{rules['event_types'][kind]}' pattern" + (f" from {onset:.1f}s ({a} clip time)" if onset is not None else '') + f" that is not detected in {b}.")
    if cross['camera_b_has_observations_during_a_low_visibility_phase']:
        extra.append(f"{cb} has person observations during normalized phases where {ca} person visibility is low: {_phases(cross['camera_a_low_visibility_phases'])}.")
    if cross['camera_a_has_observations_during_b_low_visibility_phase']:
        extra.append(f"{ca} has person observations during normalized phases where {cb} person visibility is low: {_phases(cross['camera_b_low_visibility_phases'])}.")
    qa, qb = (next(c for c in cam_states if c['camera_id'] == x)['quality'] for x in (ca, cb))
    if qa.get('pose_visibility') is not None and qb.get('pose_visibility') is not None and abs(qa['pose_visibility'] - qb['pose_visibility']) >= 0.15:
        better = ca if qa['pose_visibility'] > qb['pose_visibility'] else cb
        extra.append(f"{better} provides higher keypoint visibility ({max(qa['pose_visibility'], qb['pose_visibility']):.2f} vs {min(qa['pose_visibility'], qb['pose_visibility']):.2f}) for posture proxies.")
    reason = (f"Primary assessment taken from {primary['camera']} (highest P0 priority); risk components are the element-wise maximum across cameras. "
              + primary['reason'])
    return {
        'event_type': primary['event_type'],
        'is_incident': any(a['is_incident'] for a in assessments),
        'observations': observations,
        'temporal_summary': ' '.join(f"[{a['camera']}] {a['temporal_summary']}" for a in assessments),
        'risk': risk,
        'confidence': primary['confidence'],
        'uncertainties': uncertainties,
        'reason': reason,
        'human_review_required': any(a['human_review_required'] for a in assessments),
        'same_incident': same,
        'camera_evidence': {a['camera']: a['observations'] for a in assessments},
        'cross_camera_summary': summary,
        'additional_information_from_second_view': extra,
    }


def _f(x):
    return 'n/a' if x is None else f'{x:.2f}'


def _phases(ph):
    return ', '.join(f'{a:.2f}-{b:.2f}' for a, b in ph[:6]) + (' ...' if len(ph) > 6 else '')
