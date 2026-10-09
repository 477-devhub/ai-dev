"""Decision values + Compact Decision State -> benchmark_v1/schemas/prediction.schema.json (unchanged).

CV -> Evidence (deterministic templates from compact-state observations)
Decisions -> Decision (typed API answers via DecisionAdapter)
Template -> Explanation (no free-text generation, no second model call)
"""
MAX_OBS_PER_CAMERA = 8


def _fmt(x, d=1):
    return 'n/a' if x is None else f'{x:.{d}f}'


def camera_evidence(cam):
    """Observation sentences from compact-state fields only. Returns list of (t, description)."""
    rows = []
    p, s, win = cam['people'], cam['sampling'], cam['observation_window_sec'] or 0.0
    t0 = min([t['first_seen_sec'] for t in cam['tracks']], default=0.0)
    rows.append((t0, f"{p['count_min']}-{p['count_max']} person(s) detected per sampled frame (median {p['count_median']:g}); "
                     f"persons present in {p['frames_with_person_fraction'] * 100:.0f}% of {s['frame_count']} samples about {_fmt(s['median_interval_sec'], 2)}s apart; "
                     f"CV reliability {_fmt(cam['quality']['cv_reliability'], 2)}."))
    for t in cam['tracks'][:4]:
        r = t['track_ref']
        vt = t['strongest_vertical_transition']
        if vt.get('observed'):
            rows.append((vt['start_sec'], f"{r}: {vt['from']} posture proxy at {_fmt(vt['start_sec'])}s and {vt['to'].replace('_', ' ')} posture proxy at {_fmt(vt['end_sec'])}s "
                                          f"(transition confidence {_fmt(vt['confidence'], 2)}; downward change {_fmt(vt['downward_change_bh']['value'], 2)} body heights, reliability {vt['downward_change_bh']['reliability']})."))
            if (t['post_transition_low_posture_sec'] or 0) > 0:
                rows.append((vt['end_sec'], f"{r}: low/horizontal posture proxy persisted for about {_fmt(t['post_transition_low_posture_sec'])}s after the transition."))
        elif (t['longest_low_posture_run_sec'] or 0) >= 2.0:
            rows.append((t['first_seen_sec'], f"{r}: low/horizontal posture proxy over a run of about {_fmt(t['longest_low_posture_run_sec'])}s."))
        if t['appearance']['entered_frame']:
            how = 'at the frame edge' if t['appearance']['entry'] == 'edge_entry' else 'away from the frame edge'
            rows.append((t['first_seen_sec'], f"{r} first appears {how} at {_fmt(t['first_seen_sec'])}s."))
        if t['motion']['large_spatial_transition']:
            rows.append((t['first_seen_sec'], f"{r} moves about {_fmt(t['motion']['net_displacement_fh'], 2)} frame heights across the image between {_fmt(t['first_seen_sec'])}s and {_fmt(t['last_seen_sec'])}s."))
    for it in cam['interactions'][:2]:
        if not it['close_fraction']:
            continue
        a, b = it['tracks']
        rows.append((it['first_close_sec'] if it['first_close_sec'] is not None else it['co_observed_start_sec'],
                     f"{a} and {b}: minimum distance {_fmt(it['minimum_distance_bh'], 2)} body heights; close in {it['close_fraction'] * 100:.0f}% of {it['co_observed_frames']} co-observed samples "
                     f"(about {_fmt(it['close_duration_sec'])}s); relative motion when close {_fmt(it['relative_motion_when_close_bh_per_sec'], 2)} bh/s; "
                     f"contact proxy {_fmt(it['contact_proxy']['value'], 2)} (heuristic visual proxy, not confirmed contact)."))
    out, seen = [], set()
    for t, d in sorted(rows, key=lambda x: (x[0] or 0.0, x[1])):
        if d not in seen:
            seen.add(d)
            out.append({'camera': cam['camera'], 'timestamp_sec': round(min(max(0.0, t or 0.0), win), 2), 'description': d})
    return out[:MAX_OBS_PER_CAMERA]


def temporal_summary(cam):
    s, p = cam['sampling'], cam['people']
    parts = [f"{cam['camera']}: {s['frame_count']} samples over {_fmt(cam['observation_window_sec'])}s; up to {p['count_max']} person(s)."]
    for t in cam['tracks'][:4]:
        vt = t['strongest_vertical_transition']
        seg = f"{t['track_ref']} observed {_fmt(t['first_seen_sec'])}-{_fmt(t['last_seen_sec'])}s ({t['initial_posture'] or 'unknown'} -> {t['final_posture'] or 'unknown'})"
        if vt.get('observed'):
            seg += f", {vt['from']}-to-{vt['to'].replace('_', ' ')} change {_fmt(vt['start_sec'])}-{_fmt(vt['end_sec'])}s"
        parts.append(seg + '.')
    return ' '.join(parts)


def uncertainties(cams, refused, multi=False):
    u = []
    ivals = sorted({_fmt(c['sampling']['median_interval_sec'], 2) for c in cams})
    u.append(f"Sparse sampling (about {', '.join(ivals)}s between frames); brief actions between samples may be missed.")
    u.append('Boundary semantics (gates, walls, restricted areas) are unavailable; authorization cannot be determined.')
    if any((c['quality']['track_fragmentation'] or 0) > 0.3 or any(t['reliability_label'] == 'low' or t['ambiguous_links'] for t in c['tracks']) for c in cams):
        u.append('Track association reliability is limited (fragmented or ambiguous tracks).')
    if any(c['interactions'] for c in cams):
        u.append('Contact, arm-extension and limb-motion values are heuristic 2D proxies, not confirmed physical contact or actions.')
    if any(t['strongest_vertical_transition'].get('observed') for c in cams for t in c['tracks']):
        u.append('Posture labels are automatic proxies; the cause of a posture change and any medical condition cannot be determined.')
    if any((c['quality']['pose_visibility'] or 1) < 0.5 for c in cams):
        u.append('Low keypoint visibility limits posture estimates.')
    if any((c['quality']['dark_frame_fraction'] or 0) > 0 for c in cams):
        u.append('Some sampled frames are very dark.')
    if multi:
        u.append('Camera synchronization is not confirmed; only normalized clip phases are compared.')
        u.append('Cross-camera identity is not confirmed.')
    for r in refused:
        u.append(f"The decision '{r}' was refused by the Decisions API and treated as unknown.")
    if any(k.split('_', 1)[-1] in ('severity', 'imminence', 'exposure', 'persistence') or k in ('severity', 'imminence', 'exposure', 'persistence') for k in refused):
        u.append('A refused risk component is reported as the uninformative midpoint 0.5 only because the output schema requires a number.')
    return u


def reason(d, model):
    r = d['risk']
    cat = d['category'] if d['category'] is not None else 'refused'
    return (f"OpenAI Decisions API ({model}) typed answers over the compact CV observation state (text only, no images): "
            f"incident probability {_fmt(d['p_incident'], 2)}; category '{cat}' (confidence {_fmt(d['category_confidence'], 2)}); "
            f"severity {r['severity']:.2f}, imminence {r['imminence']:.2f}, exposure {r['exposure']:.2f}, persistence {r['persistence']:.2f} (0-1); "
            f"human-review probability {_fmt(d['p_human_review'], 2)}. Observation texts are generated deterministically from CV features, not by the model.")


def single_prediction(d, cams, model, multi=False):
    obs = [o for c in cams for o in camera_evidence(c)]
    return {
        'event_type': d['event_type'],
        'is_incident': bool(d['is_incident']),
        'observations': obs,
        'temporal_summary': ' '.join(temporal_summary(c) for c in cams),
        'risk': {k: round(v, 4) for k, v in d['risk'].items()},
        'confidence': d['confidence'],
        'uncertainties': uncertainties(cams, d['refused_questions'], multi),
        'reason': reason(d, model),
        'human_review_required': bool(d['human_review_required']),
    }


def attention_prediction(att, compact, model, weights):
    cams = {c['camera']: c for c in compact['cameras']}
    assessments = [{'camera': c, 'assessment': single_prediction(att['per_camera'][c], [cams[c]], model)} for c in cams]
    af = att['attention_first_supplementary']
    queue = []
    for rank, c in enumerate(att['order'], 1):
        d = att['per_camera'][c]
        r = d['risk']
        txt = (f"Priority {d['priority_score']:.3f} = {weights['severity']}*severity {r['severity']:.2f} + {weights['imminence']}*imminence {r['imminence']:.2f} "
               f"+ {weights['exposure']}*exposure {r['exposure']:.2f} + {weights['persistence']}*persistence {r['persistence']:.2f} (Decisions API scores); "
               f"category '{d['category']}', confidence {d['confidence']:.2f} (not used in ranking).")
        if rank == 1:
            txt += (f" Supplementary attention_first answer: {af['choice']} (confidence {af['confidence']:.2f}); not used for the rank." if af
                    else ' Supplementary attention_first answer was refused.')
        queue.append({'camera': c, 'rank': rank, 'reason': txt})
    return {'assessments': assessments, 'attention_queue': queue}


def multi_prediction(d, compact, model):
    cams = compact['cameras']
    x = compact['cross_camera']
    base = single_prediction(d, cams, model, multi=True)
    a, b = x['camera_a'], x['camera_b']
    summary = (f"Decisions API same-incident probability {_fmt(d['p_same_incident'], 2)} (threshold 0.5) -> same_incident={str(d['same_incident']).lower()}. "
               f"Base CV cross-camera observations: temporal pattern similarity {_fmt(x['temporal_pattern_similarity']['value'], 2)}, "
               f"motion peak similarity {_fmt(x['motion_peak_similarity']['value'], 2)}, posture transition similarity {_fmt(x['posture_transition_similarity']['value'], 2)}, "
               f"person count similarity {_fmt(x['person_count_similarity']['value'], 2)} (all limited-reliability, normalized-phase comparisons); "
               f"visibility complementarity {_fmt(x['visibility_complementarity'], 2)}. Camera synchronization is not confirmed. Cross-camera identity is not confirmed.")
    extra = [f"Decisions API: second view adds useful evidence with probability {_fmt(d['p_second_view_adds'], 2)}; multi-view evidence value {_fmt(d['multiview_value'], 2)} (0-1)."]
    ph = lambda lst: ', '.join(f'{p:.2f}-{q:.2f}' for p, q in lst[:6]) + (' ...' if len(lst) > 6 else '')
    if x['camera_b_has_observations_during_a_low_visibility_phase']:
        extra.append(f"{b} has person observations during normalized phases where {a} person visibility is low: {ph(x['camera_a_low_visibility_phases'])}.")
    if x['camera_a_has_observations_during_b_low_visibility_phase']:
        extra.append(f"{a} has person observations during normalized phases where {b} person visibility is low: {ph(x['camera_b_low_visibility_phases'])}.")
    base.update({
        'same_incident': bool(d['same_incident']),
        'camera_evidence': {c['camera']: camera_evidence(c) for c in cams},
        'cross_camera_summary': summary,
        'additional_information_from_second_view': extra,
    })
    return base
