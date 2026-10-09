"""P0-v1 deterministic rule engine over the Canonical CV State.

Reads only the CV state (observations) and configs/p0_v1.yaml. No LLM/VLM, no private data,
no item- or camera-specific branches. Produces per-camera assessments with risk components,
priority score and a separate confidence. Explanations are evidence templates only.
"""
import statistics

from feature_extractor import LOW_SET
from utils import clip01, rnd


def fmt(t):
    return f'{t:.1f}s'


class RuleEngine:
    def __init__(self, rules):
        self.r = rules

    # ------------------------------------------------------------------ public
    def assess_camera(self, cam):
        r = self.r
        tracks = {t['track_id']: t for t in cam['tracks']}
        cands = self._fall(cam, tracks) + self._conflict(cam, tracks)
        incident_tracks = {tid for c in cands for tid in c['track_ids']}
        cands += self._low_posture(cam, incident_tracks)
        if not cands:
            cands += self._movement(cam)
        q = cam['quality']
        cv_rel = q['overall_cv_reliability']
        if not cands:
            if cam['detection_summary']['total_detections'] == 0:
                cands.append(self._plain('no_person', cam, []))
            elif cv_rel is None or cv_rel < r['uncertain']['min_cv_reliability_for_negative']:
                cands.append(self._plain('uncertain', cam, []))
            else:
                cands.append(self._plain('none', cam, []))
        for c in cands:
            self._risk(c, cam)
        cands.sort(key=lambda c: (-c['priority_score'], -c['risk']['severity'], -c['confidence'], c['onset_sec'] if c['onset_sec'] is not None else 1e9))
        primary = cands[0]
        return {
            'camera': cam['camera_id'],
            'primary': primary,
            'candidates': cands,
            'event_type': r['event_types'][primary['kind']],
            'is_incident': bool(r['is_incident'][primary['kind']]),
            'risk': primary['risk'],
            'priority_score': primary['priority_score'],
            'confidence': primary['confidence'],
            'human_review_required': self._needs_review(primary),
            'observations': self._observations(cam, cands),
            'temporal_summary': self._temporal_summary(cam, cands),
            'uncertainties': self._uncertainties(cam, cands),
            'reason': self._reason(cam, cands),
        }

    # ------------------------------------------------------------------ candidate rules
    def _fall(self, cam, tracks):
        fc, out = self.r['fall_like'], []
        cv_rel = cam['quality']['overall_cv_reliability'] or 0.0
        for t in cam['tracks']:
            vt, low = t['vertical_transition'], t['low_motion']
            if not vt['upright_to_low_transition']:
                continue
            if (vt['confidence'] or 0) < fc['min_transition_confidence'] or (vt['max_downward_change'] or 0) < fc['min_downward_change_body_heights']:
                continue
            plm, plp = low['post_transition_low_motion_sec'] or 0, low['post_transition_low_posture_sec'] or 0
            if plm < fc['min_post_transition_low_motion_sec'] and plp < fc['min_post_transition_low_posture_sec']:
                continue
            trel = t['reliability']['reliability_score'] or 0.0
            ev = [
                (vt['transition_start_sec'], f"Track {t['track_id']} observed in standing posture at {fmt(vt['transition_start_sec'])} and in {vt['to_posture'].replace('_', ' ')} posture at {fmt(vt['transition_end_sec'])} (samples ~{vt['temporal_resolution_sec']:.2f}s apart)."),
                (vt['transition_end_sec'], f"Downward {vt['downward_change_basis'].replace('_', ' ')} change of about {vt['max_downward_change']:.2f} body heights between these samples."),
            ]
            if plm > 0:
                ev.append((vt['transition_end_sec'], f"Low sampled displacement continued for approximately {plm:.1f}s after the transition."))
            if plp > 0:
                ev.append((vt['transition_end_sec'] + plp, f"Low/horizontal posture proxy observed until {fmt(vt['transition_end_sec'] + plp)}."))
            out.append({
                'kind': 'fall', 'track_ids': [t['track_id']], 'onset_sec': vt['transition_start_sec'],
                'proxy_times': self._low_times(cam, [t['track_id']], vt['transition_end_sec']),
                'persist_sec': max(plp, plm), 'post_low_motion_sec': plm, 'evidence': ev,
                'confidence_raw': 0.5 * vt['confidence'] + 0.25 * trel + 0.25 * cv_rel,
                'involved': 1, 'basis': 'single_track',
            })
        for link in cam['scene_observations']['fragment_links']:
            pc = link['posture_change']
            if pc is None or (pc['downward_change'] or 0) < fc['min_downward_change_body_heights']:
                continue
            conf = (pc['confidence'] or 0) * fc['fragment_link_confidence_factor']
            if conf < fc['min_transition_confidence'] * fc['fragment_link_confidence_factor']:
                continue
            to = tracks[link['to_track']]
            dur = to['detection']['last_seen_sec'] - to['detection']['first_seen_sec']
            lowf = to['posture']['low_or_horizontal_fraction'] or 0
            if lowf < fc['fragment_min_low_fraction'] or dur < fc['min_post_transition_low_posture_sec']:
                continue
            if any(c['track_ids'] == [link['from_track']] or c['track_ids'] == [link['to_track']] for c in out):
                continue
            ev = [
                (link['from_end_sec'], f"Track {link['from_track']} last observed standing near {fmt(link['from_end_sec'])}; track {link['to_track']} starts {link['distance_body_heights']:.2f} body heights away at {fmt(link['to_start_sec'])} in {pc['to_posture'].replace('_', ' ')} posture (identity continuity not confirmed)."),
                (link['to_start_sec'], f"Downward change of about {pc['downward_change']:.2f} body heights across the two track fragments."),
                (to['detection']['last_seen_sec'], f"Track {link['to_track']} shows low/horizontal posture proxy in {lowf * 100:.0f}% of its posture samples until {fmt(to['detection']['last_seen_sec'])}."),
            ]
            trel = to['reliability']['reliability_score'] or 0.0
            out.append({
                'kind': 'fall', 'track_ids': [link['from_track'], link['to_track']], 'onset_sec': link['from_end_sec'],
                'proxy_times': self._low_times(cam, [link['to_track']], link['to_start_sec']),
                'persist_sec': dur, 'post_low_motion_sec': (to['low_motion']['low_motion_fraction'] or 0) * dur, 'evidence': ev,
                'confidence_raw': 0.5 * conf + 0.25 * trel + 0.25 * (cam['quality']['overall_cv_reliability'] or 0),
                'involved': 1, 'basis': 'fragment_link',
            })
        return out

    def _conflict(self, cam, tracks):
        cc, out = self.r['conflict_like'], []
        if cam['detection_summary']['person_count_max'] < cc['min_persons']:
            return out
        cv_rel = cam['quality']['overall_cv_reliability'] or 0.0
        for p in cam['pairwise_interactions']:
            if (p['reliability'] or 0) < cc['min_pair_reliability']:
                continue
            if (p['close_duration_sec'] or 0) < cc['min_close_duration_sec'] or (p['close_proximity_fraction'] or 0) < cc['min_close_proximity_fraction']:
                continue
            contact = p['contact_proxy']['score']
            if contact is None or contact < cc['min_contact_proxy']:
                continue
            cues = cc['cues']
            checks = {
                'rapid relative movement while close': (p['relative_motion_intensity_when_close'] or 0) >= cues['relative_motion_when_close_body_heights_per_sec'],
                'repeated approaches': p['repeated_approach_count'] >= cues['repeated_approach_count'],
                'rapid sampled limb motion': (p['rapid_limb_motion_score'] or 0) >= cues['rapid_limb_motion_score'],
                'arm extension toward the other person': (p['arm_extension_toward_other_score'] or 0) >= cues['arm_extension_toward_other_score'],
            }
            met = [k for k, v in checks.items() if v]
            if len(met) < cc['min_supporting_cues']:
                continue
            a, b = p['track_a'], p['track_b']
            ev = [
                (p['first_close_sec'], f"Two person tracks ({a}, {b}) were within about one body height of each other from {fmt(p['first_close_sec'])} to {fmt(p['last_close_sec'])} (close in {p['close_proximity_fraction'] * 100:.0f}% of {p['co_observed_frames']} co-observed samples)."),
                (p['first_close_sec'], f"Sampled relative movement while close averaged {p['relative_motion_intensity_when_close']:.2f} body heights/s; {p['repeated_approach_count']} approach event(s)."),
                (p['last_close_sec'], f"2D contact proxy {contact:.2f} (basis: {', '.join(p['contact_proxy']['basis']) or 'none'}); supporting cues: {', '.join(met)}. Physical contact is not established."),
            ]
            out.append({
                'kind': 'conflict', 'track_ids': [a, b], 'onset_sec': p['first_close_sec'],
                'proxy_times': self._close_times(cam, a, b), 'persist_sec': p['close_duration_sec'], 'evidence': ev,
                'contact': contact,
                'confidence_raw': 0.4 * contact + 0.2 * (p['reliability'] or 0) + 0.2 * len(met) / len(checks) + 0.2 * cv_rel,
                'involved': 2, 'basis': 'pairwise',
            })
        return out

    def _low_posture(self, cam, exclude):
        lc, out = self.r['low_posture_persistent'], []
        cv_rel = cam['quality']['overall_cv_reliability'] or 0.0
        for t in cam['tracks']:
            if t['track_id'] in exclude:
                continue
            ps = t['posture']
            dur = t['detection']['last_seen_sec'] - t['detection']['first_seen_sec']
            if ps['known_posture_observations'] < lc['min_known_posture_obs'] or (ps['low_or_horizontal_fraction'] or 0) < lc['min_low_fraction'] or dur < lc['min_duration_sec']:
                continue
            ev = [(t['detection']['first_seen_sec'], f"Track {t['track_id']} in low/horizontal posture proxy in {ps['low_or_horizontal_fraction'] * 100:.0f}% of posture samples between {fmt(t['detection']['first_seen_sec'])} and {fmt(t['detection']['last_seen_sec'])}.")]
            vt = t['vertical_transition']
            if vt['upright_to_low_transition']:
                # a transition WAS observed but missed the fall-like thresholds: say so, never claim it was absent
                ev.append((vt['transition_start_sec'], f"Standing posture at {fmt(vt['transition_start_sec'])} and {vt['to_posture'].replace('_', ' ')} posture at {fmt(vt['transition_end_sec'])} were observed, but this change did not meet all fall-like rule thresholds (transition confidence {vt['confidence']:.2f}, downward {vt['downward_change_basis'].replace('_', ' ')} change {vt['max_downward_change']:.2f} body heights)."))
            elif vt['upright_to_low_transition'] is False:
                ev[0] = (ev[0][0], ev[0][1][:-1] + '; no standing-to-low transition was observed in this track.')
            else:
                ev[0] = (ev[0][0], ev[0][1][:-1] + '; too few posture samples to assess an onset.')
            out.append({
                'kind': 'low_posture', 'track_ids': [t['track_id']], 'onset_sec': t['detection']['first_seen_sec'],
                'proxy_times': self._low_times(cam, [t['track_id']], t['detection']['first_seen_sec']),
                'persist_sec': dur, 'evidence': ev,
                'confidence_raw': 0.8 * (0.4 * ps['low_or_horizontal_fraction'] + 0.3 * (t['reliability']['reliability_score'] or 0) + 0.3 * cv_rel),
                'involved': 1, 'basis': 'single_track',
            })
        return out

    def _movement(self, cam):
        mc = self.r['movement']
        ev = []
        tracks = {t['track_id']: t for t in cam['tracks']}
        for e in cam['scene_observations']['track_entries']:
            if e['type'] in mc['entry_types'] and tracks[e['track_id']]['detection']['observed_frames'] >= mc['min_track_observations']:
                where = 'at the frame edge' if e['type'] == 'edge_entry' else 'away from the frame edge'
                ev.append((e['time_sec'], f"Track {e['track_id']} first appears {where} at {fmt(e['time_sec'])}."))
        for s in cam['scene_observations']['large_spatial_transitions']:
            if tracks[s['track_id']]['detection']['observed_frames'] >= mc['min_track_observations']:
                ev.append((s['start_sec'], f"Track {s['track_id']} moves from image position ({s['from_xy'][0]:.2f}, {s['from_xy'][1]:.2f}) to ({s['to_xy'][0]:.2f}, {s['to_xy'][1]:.2f}) between {fmt(s['start_sec'])} and {fmt(s['end_sec'])}."))
        if not ev:
            return []
        ev.sort(key=lambda x: x[0])
        c = self._plain('movement', cam, ev)
        c['onset_sec'] = ev[0][0]
        return [c]

    def _plain(self, kind, cam, ev):
        q = cam['quality']
        cv_rel = q['overall_cv_reliability']
        cc = self.r['confidence']
        if kind == 'no_person':
            conf = cc['no_person_scale'] * (1.0 - (q['dark_frame_fraction'] or 0))
            ev = ev or [(0.0, f"No person detected in any of the {cam['frame_count']} sampled frames.")]
        elif kind == 'movement':
            conf = 0.5 * (cam['detection_summary']['mean_detection_confidence'] or 0) + 0.5 * (cv_rel or 0)
        else:
            conf = cc['none_scale'] * (cv_rel or 0)
        if not ev:
            first = next((f for f in cam['frames'] if f['person_count'] > 0), None)
            ds = cam['detection_summary']
            ev = [((first or cam['frames'][0])['timestamp_sec'],
                   f"{ds['person_count_min']}-{ds['person_count_max']} person(s) detected per sampled frame (median {ds['person_count_median']:g}); no posture-transition or close-interaction rule fired.")]
        return {'kind': kind, 'track_ids': [], 'onset_sec': None, 'proxy_times': [], 'persist_sec': 0.0,
                'evidence': ev, 'confidence_raw': conf, 'involved': 0, 'basis': 'camera'}

    # ------------------------------------------------------------------ proxy timelines
    def _low_times(self, cam, track_ids, after):
        out = []
        for f in cam['frames']:
            if f['timestamp_sec'] < after - 1e-9:
                continue
            if any(d['track_id'] in track_ids and d['posture']['label'] in LOW_SET for d in f['detections']):
                out.append(f['timestamp_sec'])
        return out

    def _close_times(self, cam, a, b):
        p = next(p for p in cam['pairwise_interactions'] if p['track_a'] == a and p['track_b'] == b)
        return [t for t, _, close in p['distance_series'] if close]

    # ------------------------------------------------------------------ risk / confidence
    def _risk(self, c, cam):
        rr = self.r['risk']
        kind = c['kind']
        times = cam['sampling']['timestamps_sec']
        span = times[-1] if times else 0.0
        late_t = rr['late_phase_start'] * span
        late_frames = [f for f in cam['frames'] if f['timestamp_sec'] >= late_t]
        incident = bool(self.r['is_incident'][kind])
        sev = rr['severity_base'][kind]
        if kind == 'fall':
            sev += rr['severity_bonus']['fall_post_low_motion_per_10s'] * clip01(c['post_low_motion_sec'] / 10.0)
        elif kind == 'conflict':
            sev += rr['severity_bonus']['conflict_contact_proxy'] * c['contact']
        if incident or kind == 'low_posture':
            late_presence = (sum(1 for f in late_frames if f['timestamp_sec'] in set(c['proxy_times'])) / len(late_frames)) if late_frames else 0.0
            if incident:
                imm = rr['incident_imminence_floor'] + (1 - rr['incident_imminence_floor']) * late_presence
            else:
                imm = rr['non_incident_imminence_scale']['low_posture'] * late_presence
            others = max(0, cam['detection_summary']['person_count_max'] - c['involved'])
            exp = clip01((c['involved'] + 0.5 * others) / rr['exposure_ref_persons'])
            remaining = max(span - (c['onset_sec'] or 0.0), cam['sampling']['median_interval_sec'] or 1.0)
            pers = clip01(c['persist_sec'] / remaining)
        else:
            late_activity = (sum(1 for f in late_frames if f['person_count'] > 0) / len(late_frames)) if late_frames else 0.0
            imm = rr['non_incident_imminence_scale'][kind] * late_activity
            exp = rr['non_incident_exposure_scale'] * clip01(cam['detection_summary']['person_count_max'] / rr['exposure_ref_persons'])
            pers = rr['non_incident_persistence'][kind]
        risk = {'severity': rnd(clip01(sev), 3), 'imminence': rnd(clip01(imm), 3), 'exposure': rnd(clip01(exp), 3), 'persistence': rnd(clip01(pers), 3)}
        w = self.r['priority_weights']
        c['risk'] = risk
        c['priority_score'] = rnd(sum(w[k] * risk[k] for k in w), 4)   # confidence deliberately NOT multiplied in
        c['confidence'] = rnd(min(self.r['confidence']['max'], clip01(c['confidence_raw'])), 3)

    def _needs_review(self, c):
        return bool(self.r['is_incident'][c['kind']]) or c['kind'] in ('uncertain', 'low_posture') or c['confidence'] < self.r['human_review']['confidence_below']

    # ------------------------------------------------------------------ text (templates only)
    def _observations(self, cam, cands):
        rows = []
        for c in cands:
            rows.extend(c['evidence'])
        seen, out = set(), []
        for t, text in sorted(rows, key=lambda x: (x[0], x[1])):
            if text in seen:
                continue
            seen.add(text)
            out.append({'camera': cam['camera_id'], 'timestamp_sec': rnd(max(0.0, t), 2), 'description': text})
        return out[:self.r['observations']['max_per_camera']]

    def _temporal_summary(self, cam, cands):
        ds, s = cam['detection_summary'], cam['sampling']
        times = s['timestamps_sec']
        parts = [f"{cam['frame_count']} sampled frames over {times[-1]:.1f}s (~{s['median_interval_sec']:.2f}s apart); persons detected in {ds['frames_with_person_fraction'] * 100:.0f}% of samples (max {ds['person_count_max']} per frame)."]
        for c in sorted(cands, key=lambda c: c['onset_sec'] if c['onset_sec'] is not None else 1e9):
            if c['onset_sec'] is None:
                continue
            label = self.r['event_types'][c['kind']]
            end = max(c['proxy_times']) if c['proxy_times'] else None
            parts.append(f"{label} proxy from {fmt(c['onset_sec'])}" + (f", proxy still observed at {fmt(end)}" if end is not None else '') + '.')
        return ' '.join(parts)

    def _uncertainties(self, cam, cands):
        q, s = cam['quality'], cam['sampling']
        kinds = {c['kind'] for c in cands}
        u = [f"Sparse sampling: about {s['median_interval_sec']:.2f}s between canonical frames; brief actions between samples may be missed and speeds are coarse."]
        if 'fall' in kinds or 'low_posture' in kinds:
            u.append('The cause of a posture change (accidental, medical or intentional) cannot be determined from video; no diagnosis is implied.')
            u.append('Low sampled displacement does not establish that the person is motionless or unresponsive.')
        if 'conflict' in kinds:
            u.append('Physical contact, intent and roles cannot be established from 2D image-plane proximity and motion proxies.')
        if any(len(c['track_ids']) > 1 and c['basis'] == 'fragment_link' for c in cands):
            u.append('Evidence spans two track fragments; that they are the same person is not confirmed.')
        if (q.get('track_fragmentation') or 0) > 0.3 or any(t['reliability']['ambiguous_links'] for t in cam['tracks']):
            u.append('Track identity across samples is uncertain (fragmented or ambiguous associations).')
        if (q.get('small_person_fraction') or 0) > 0.3:
            u.append('Many person detections are small in the frame; pose keypoints and posture proxies are less reliable.')
        if q.get('pose_visibility') is not None and q['pose_visibility'] < 0.5:
            u.append('Low keypoint visibility; posture classification is often unknown.')
        if (q.get('dark_frame_fraction') or 0) > 0:
            u.append(f"{q['dark_frame_fraction'] * 100:.0f}% of sampled frames are very dark.")
        u.append('Scene semantics (gates, walls, restricted areas) are unavailable to this generic CV pipeline; boundary crossing, authorization and intent are not assessed.')
        return u

    def _reason(self, cam, cands):
        p = cands[0]
        r = p['risk']
        label = self.r['event_types'][p['kind']]
        txt = (f"P0 deterministic CV rules (no LLM). Primary pattern on {cam['camera_id']}: {label}"
               + (f" (tracks {', '.join(p['track_ids'])})" if p['track_ids'] else '')
               + f". Priority {p['priority_score']:.2f} from severity {r['severity']:.2f}, imminence {r['imminence']:.2f}, exposure {r['exposure']:.2f}, persistence {r['persistence']:.2f}; confidence {p['confidence']:.2f} reported separately"
               + f"; CV reliability {cam['quality']['overall_cv_reliability_label']}.")
        others = [self.r['event_types'][c['kind']] for c in cands[1:]]
        if others:
            txt += ' Other rule matches: ' + '; '.join(sorted(set(others))) + '.'
        return txt
