"""Observation-only v2. Reuses v1 selection, never changes the frozen v1 path.

Adjacent means adjacent *sample indices*, never continuous video evidence.
Missing samples are not evidence of absence. No new event thresholds are used.
"""
from compact_serializer import CompactSerializer, LOW


class CompactSerializerV2(CompactSerializer):
    def serialize(self, state):
        if state['state_version'] != 'cv-state-v1':
            raise ValueError('v2 requires cv-state-v1')
        out = super().serialize(state)
        out['schema_version'] = 'compact-decision-state-v2'
        out['evidence_semantics'] = (
            'Sample observations only; missing is not absence. Runs and adjacent spans do not prove continuity. '
            'Recovery does not erase earlier low posture. Motion summaries may bridge missed samples. '
            'Proximity/contact proxies do not establish collision, assault or intent. '
            'null=measurement unavailable; unknown=detected but posture unresolved; '
            'not_observed=no detection assigned at that sample. No normal/abnormal event verdicts.')
        self.check_forbidden(out)
        return out

    def coverage(self, indices, times):
        ids = sorted(set(indices))
        gaps = [(a, b) for a, b in zip(ids, ids[1:]) if b > a + 1]
        return {
            'clip_sample_fraction': self.f(len(ids) / len(times)),
            'span_sample_fraction': self.f(len(ids) / (ids[-1] - ids[0] + 1)) if ids else None,
            'missing_inside_span_samples': sum(b - a - 1 for a, b in gaps),
            'max_missing_run_samples': max([b - a - 1 for a, b in gaps] +
                ([ids[0], len(times) - 1 - ids[-1]] if ids else [len(times)])),
            'leading_unobserved_samples': ids[0] if ids else len(times),
            'max_gap_bracket_sec': self.f(max((times[b] - times[a] for a, b in gaps), default=0)),
            'max_observation_interval_sec': self.f(max((times[b] - times[a] for a, b in zip(ids, ids[1:])), default=0)) if len(ids) > 1 else None,
            'tail_unobserved_samples': len(times) - 1 - ids[-1] if ids else len(times),
            'last_sample_age_sec': self.f(times[-1] - times[ids[-1]]) if ids else None,
        }

    def temporal(self, rows, times):
        # rows: (sample index, Canonical frame detection). Keep every change and gap.
        runs = []
        for i, d in rows:
            p = d['posture']
            conf = p['confidence']
            basis = p['basis']
            if runs and runs[-1][1] == i - 1 and runs[-1][2] == p['label']:
                r = runs[-1]
                r[1] = i
                r[3] = None if r[3] is None or conf is None else self.f(min(r[3], conf))
                r[4] = sorted(set(r[4] + [basis]))
            else:
                runs.append([i, i, p['label'], self.f(conf), [basis]])
        lows = [(i, d) for i, d in rows if d['posture']['label'] in LOW]
        low_spans, span = [], 0.0
        for (a, da), (b, db) in zip(rows, rows[1:]):
            if b == a + 1 and da['posture']['label'] in LOW and db['posture']['label'] in LOW:
                span += times[b] - times[a]
            else:
                low_spans.append(span)
                span = 0.0
        low_spans.append(span)
        recoveries = []
        pending = None
        for i, d in rows:
            lab = d['posture']['label']
            if lab in LOW:
                pending = i
            elif lab == 'standing' and pending is not None:
                between = [(j, x) for j, x in rows if pending < j <= i]
                recoveries.append([self.f(times[pending]), self.f(times[i]),
                                   i - pending - len(between),
                                   sum(x['posture']['label'] == 'unknown' for _, x in between)])
                pending = None
        known = [(i, d) for i, d in rows if d['posture']['label'] != 'unknown']
        return {
            'runs': runs,
            'low_observed_samples': len(lows),
            'unknown_posture_samples': sum(d['posture']['label'] == 'unknown' for _, d in rows),
            'low_adjacent_span_sec': self.f(sum(low_spans)),
            'longest_low_adjacent_span_sec': self.f(max(low_spans)),
            'last_observed_posture': rows[-1][1]['posture']['label'] if rows else None,
            'last_known_posture': known[-1][1]['posture']['label'] if known else None,
            'last_known_posture_sec': self.f(times[known[-1][0]]) if known else None,
            'last_sample_posture': rows[-1][1]['posture']['label'] if rows and rows[-1][0] == len(times) - 1 else 'not_observed',
            'low_to_standing_observations': recoveries,
        }

    def camera(self, cam):
        out, ref = super().camera(cam)
        times = cam['sampling']['timestamps_sec']
        if len(times) != cam['frame_count'] or any(b <= a for a, b in zip(times, times[1:])):
            raise ValueError('sample timestamps must match frame count and increase')
        out['sampling']['timestamps_sec'] = [self.f(t) for t in times]
        q = cam['quality']
        # Canonical aggregate used dropout-or-zero. Do not expose it as complete reliability.
        complete = all(q.get(k) is not None for k in ('pose_visibility', 'detection_dropout_rate',
                       'track_fragmentation', 'occlusion_proxy', 'small_person_fraction', 'dark_frame_fraction'))
        if not complete:
            out['quality']['cv_reliability'] = None
            out['quality']['cv_reliability_label'] = 'unknown'
        out['quality']['aggregate_inputs_complete'] = complete
        for k in ('mean_brightness', 'mean_contrast', 'mean_sharpness'):
            out['quality'][k] = self.f(q.get(k))
        by_id = {t['track_id']: t for t in cam['tracks']}
        reverse = {v: k for k, v in ref.items()}
        for tr in out['tracks']:
            t = by_id[reverse[tr['track_ref']]]
            rows = self.rows(cam, t)
            ids = [i for i, _ in rows]
            tr.pop('visible_fraction')
            tr.pop('final_posture')
            tr.pop('longest_low_posture_run_sec')
            tr.pop('post_transition_low_posture_sec')
            tr['coverage'] = self.coverage(ids, times)
            tr['temporal'] = self.temporal(rows, times)
            tr['mean_detection_confidence'] = self.f(t['detection']['mean_detection_confidence'])
            tr['association_confidence'] = self.f(t['reliability']['association_confidence'])
            if tr['association_confidence'] is None:
                tr['reliability'], tr['reliability_label'] = None, 'unknown'
            tr['fragment_link_candidates'] = sum(l['from_track'] == t['track_id'] or l['to_track'] == t['track_id']
                                                  for l in cam['scene_observations']['fragment_links'])
            transition = tr['strongest_vertical_transition']
            if transition.get('observed'):
                self.unavailable_drop(transition['downward_change_bh'], t['vertical_transition']['downward_change_basis'])
        pair_map = {tuple(sorted((p['track_a'], p['track_b']))): p for p in cam['pairwise_interactions']}
        included_pairs = set()
        for p in out['interactions']:
            key = tuple(sorted(reverse[r] for r in p['tracks']))
            included_pairs.add(key)
            src = pair_map[key]
            co = sorted(set(i for i, _ in by_id[key[0]]['observations']) & set(i for i, _ in by_id[key[1]]['observations']))
            p['coverage'] = self.coverage(co, times)
            series = src['distance_series']
            if len(series) != len(co) or any(abs(x[0] - times[i]) > 0.001 for i, x in zip(co, series)):
                raise ValueError('pair distance series must align with co-observed samples')
            adjacent = [(a, b, x, y) for a, b, x, y in zip(co, co[1:], series, series[1:]) if b == a + 1]
            p.pop('close_duration_sec')
            p['close_adjacent_span_sec'] = self.f(sum(times[b] - times[a] for a, b, x, y in adjacent if x[2] and y[2]))
            p['distance_change_bh_per_sec'] = self.f(sum((y[1] - x[1]) for a, b, x, y in adjacent) /
                sum(times[b] - times[a] for a, b, x, y in adjacent)) if adjacent else None
            p['relative_motion_mean_bh_per_sec'] = self.f(src['relative_motion_intensity'])
            p['contact_proxy_terms_available'] = sum(v is not None for v in src['contact_proxy']['terms'].values())
        omitted = [t for t in cam['tracks'] if t['track_id'] not in ref]
        omitted_pairs = [p for p in cam['pairwise_interactions'] if tuple(sorted((p['track_a'], p['track_b']))) not in included_pairs]
        links = cam['scene_observations']['fragment_links']
        link_sources = {(l['from_track'], l['to_track']): l for l in links}
        for link in out['scene']['fragment_links']:
            if link['posture_change'] is not None:
                src = link_sources[(reverse[link['from_track']], reverse[link['to_track']])]['posture_change']
                self.unavailable_drop(link['posture_change']['downward_change_bh'], src['downward_change_basis'])
        included_links = {(reverse[l['from_track']], reverse[l['to_track']]) for l in out['scene']['fragment_links']}
        out['selection_coverage'] = {
            'tracks_omitted': len(omitted),
            'pairs_total': len(cam['pairwise_interactions']), 'pairs_included': len(included_pairs),
            'pairs_omitted': len(omitted_pairs),
            'fragment_links_total': len(links), 'fragment_links_included': len(included_links),
            'fragment_links_omitted': len(links) - len(included_links),
            'omitted_tracks_with_low_samples': sum(any(x[1] in LOW for x in t['posture']['timeline']) for t in omitted),
            'omitted_tracks_with_upright_to_low': sum(t['vertical_transition']['upright_to_low_transition'] is True for t in omitted),
            'omitted_tracks_with_unknown_posture': sum(any(x[1] == 'unknown' for x in t['posture']['timeline']) for t in omitted),
            'omitted_pairs_with_close_samples': sum(any(x[2] for x in p['distance_series']) for p in omitted_pairs),
            'omitted_fragment_posture_changes': sum(l['posture_change'] is not None for l in links
                 if (l['from_track'], l['to_track']) not in included_links),
        }
        return out, ref

    @staticmethod
    def unavailable_drop(value, basis):
        if value['value'] is None or basis not in ('hip', 'bbox_top'):
            value['reliability'] = 'limited'
            value['note'] = 'downward measurement or basis unavailable'

    @staticmethod
    def rows(cam, track):
        rows = []
        for i, j in sorted(track['observations']):
            d = cam['frames'][i]['detections'][j]
            if d['track_id'] != track['track_id']:
                raise ValueError('observation reference does not match track')
            rows.append((i, d))
        return rows
