"""Offline evidence tests. No labels, prediction records, CV or API calls."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from compact_versions import prepare_compact
from compact_serializer import CompactSerializer
from compact_serializer_v2 import CompactSerializerV2
from utils import canonical_json, load_yaml, COMPACT_CONFIG
from jsonschema import Draft202012Validator, ValidationError

STATES = ROOT.parent / 'p0_cv_only/states'


def fixture(labels=('standing', 'horizontal', 'standing'), indices=(0, 1, 2), tracks=1):
    # Existing unlabeled Canonical structures are only templates; observations below are synthetic.
    originals = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(STATES.glob('ITEM_*.json'))]
    base = copy.deepcopy(originals[0])
    source = next(c for s in originals for c in s['cameras'] if c['tracks'] and c['pairwise_interactions'])
    cam = copy.deepcopy(source)
    base['input']['task'] = 'single'
    base['cross_camera'] = None
    base['cameras'] = [cam]
    cam['camera_id'] = 'CAM_01'
    cam['frame_count'] = 64
    cam['duration_sec'] = 63.033
    cam['sampling'] = {'timestamps_sec': list(range(64)), 'median_interval_sec': 1., 'max_interval_sec': 1., 'note': 'synthetic'}
    template_t = copy.deepcopy(source['tracks'][0])
    fi, di = template_t['observations'][0]
    template_d = copy.deepcopy(source['frames'][fi]['detections'][di])
    template_f = copy.deepcopy(source['frames'][0])
    cam['frames'] = []
    cam['tracks'] = []
    for i in range(64):
        f = copy.deepcopy(template_f)
        f.update(index=i, timestamp_sec=float(i), frame_number=i, detections=[], person_count=0)
        cam['frames'].append(f)
    for n in range(tracks):
        tid = f'T{n+1:02d}'
        t = copy.deepcopy(template_t)
        t['track_id'] = tid
        t['observations'] = [[i, n] for i in indices]
        t['posture']['timeline'] = [[float(i), lab, None if lab == 'unknown' else .8] for i, lab in zip(indices, labels)]
        t['detection'].update(first_seen_sec=float(indices[0]),last_seen_sec=float(indices[-1]),observed_frames=len(indices),visible_fraction=len(indices)/(indices[-1]-indices[0]+1),visible_fraction_of_clip=len(indices)/64,mean_detection_confidence=.8)
        t['reliability'].update(observed_frames=len(indices),visible_fraction=t['detection']['visible_fraction'],reliability_score=.8,association_confidence=.8,ambiguous_links=0,reliability_label='high')
        # Unmeasured synthetic geometry/motion/transition summaries must not inherit real values.
        for key in t['motion']:
            if key != 'units': t['motion'][key] = None
        for key in t['low_motion']:
            if key != 'semantics': t['low_motion'][key] = None
        for key in t['vertical_transition']:
            t['vertical_transition'][key] = None
        t['vertical_transition']['temporal_resolution_sec'] = 1.
        for i, lab in zip(indices, labels):
            d = copy.deepcopy(template_d)
            d['track_id'], d['det_index'] = tid, n
            d['posture'].update(label=lab,confidence=None if lab == 'unknown' else .8,basis='insufficient_keypoints' if lab == 'unknown' else 'keypoints')
            cam['frames'][i]['detections'].append(d)
            cam['frames'][i]['person_count'] += 1
        cam['tracks'].append(t)
    cam['pairwise_interactions'] = []
    cam['scene_observations'].update(fragment_links=[],track_entries=[{'track_id':t['track_id'],'time_sec':float(indices[0]),'type':'present_at_clip_start' if indices[0] == 0 else 'appears_mid_frame'} for t in cam['tracks']],track_exits=[{'track_id':t['track_id'],'time_sec':float(indices[-1]),'type':'present_at_clip_end' if indices[-1] == 63 else 'disappears_mid_frame'} for t in cam['tracks']],large_spatial_transitions=[],occlusion_candidates=[])
    cam['detection_summary'].update(person_count_min=0,person_count_max=tracks,person_count_median=0,frames_with_person_fraction=len(indices)/64)
    base['input'].update(camera_ids=['CAM_01'],frames_per_camera={'CAM_01':64},total_frames=64)
    return base


def pair_fixture(state):
    originals = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(STATES.glob('ITEM_*.json'))]
    src = next(p for s in originals for c in s['cameras'] for p in c['pairwise_interactions'])
    cam = state['cameras'][0]
    indices = [i for i, _ in cam['tracks'][0]['observations']]
    for a in range(len(cam['tracks'])):
        for b in range(a+1, len(cam['tracks'])):
            p = copy.deepcopy(src)
            p.update(pair_id=f'P{a}_{b}',track_a=cam['tracks'][a]['track_id'],track_b=cam['tracks'][b]['track_id'],co_observed_frames=len(indices),co_observed_start_sec=float(indices[0]),co_observed_end_sec=float(indices[-1]),close_proximity_fraction=1.,reliability=.8,minimum_normalized_distance=.3,mean_normalized_distance=.3,distance_series=[[float(i), .3, True] for i in indices])
            cam['pairwise_interactions'].append(p)
    return state


class CompactV2Tests(unittest.TestCase):
    def camera(self, s): return prepare_compact(s, 'v2')['compact']['cameras'][0]
    def track(self, s): return self.camera(s)['tracks'][0]

    def test_all_cached_samples_and_v1_exact_regression(self):
        source_validator = Draft202012Validator(json.loads((ROOT.parent/'p0_cv_only/schemas/canonical_cv_state.schema.json').read_text(encoding='utf-8')))
        for p in sorted(STATES.glob('ITEM_*.json')):
            s = json.loads(p.read_text(encoding='utf-8'))
            source_validator.validate(s)
            before = canonical_json(s)
            for version in ('v1','v2'):
                out = prepare_compact(s,version)
                self.assertIn(canonical_json(out['compact']),out['input_text'])
            expected = json.loads((ROOT/'compact_states'/p.name).read_text(encoding='utf-8'))
            self.assertEqual(canonical_json(expected),canonical_json(prepare_compact(s,'v1')['compact']))
            self.assertEqual(before,canonical_json(s))

    def test_clip_and_span_coverage(self):
        c = self.track(fixture(indices=(10,11,14)))['coverage']
        self.assertEqual(c['clip_sample_fraction'],round(3/64,3))
        self.assertEqual(c['span_sample_fraction'],.6)
        self.assertEqual(c['leading_unobserved_samples'],10)
        self.assertEqual(c['missing_inside_span_samples'],2)
        self.assertEqual(c['max_gap_bracket_sec'],3.)
        self.assertEqual(c['tail_unobserved_samples'],49)
        self.assertEqual(c['max_missing_run_samples'],49)
        self.assertEqual(c['last_sample_age_sec'],49.)

    def test_gap_breaks_low_runs(self):
        tr = self.track(fixture(('horizontal','horizontal','horizontal'),(0,1,4)))
        self.assertEqual(tr['temporal']['longest_low_adjacent_span_sec'],1.)
        self.assertEqual(len(tr['temporal']['runs']),2)

    def test_low_label_changes_still_adjacent(self):
        t = self.track(fixture(('crouched','horizontal','low_posture')))['temporal']
        self.assertEqual(t['longest_low_adjacent_span_sec'],2.)

    def test_unknown_breaks_low_runs(self):
        t = self.track(fixture(('horizontal','unknown','horizontal')))['temporal']
        self.assertEqual(t['low_adjacent_span_sec'],0.)
        self.assertEqual(t['unknown_posture_samples'],1)

    def test_recovery_and_unknown_differ(self):
        a = self.track(fixture(indices=(61,62,63)))['temporal']
        b = self.track(fixture(('standing','horizontal','unknown'),(61,62,63)))['temporal']
        self.assertEqual(a['low_to_standing_observations'],[[62.,63.,0,0]])
        self.assertEqual(a['low_observed_samples'],1)
        self.assertEqual(b['low_to_standing_observations'],[])
        self.assertEqual(b['last_sample_posture'],'unknown')
        self.assertEqual(b['last_known_posture'],'horizontal')

    def test_recovery_retains_gap_and_unknown(self):
        t = self.track(fixture(('horizontal','unknown','standing'),(0,2,4)))['temporal']
        self.assertEqual(t['low_to_standing_observations'],[[0.,4.,2,1]])

    def test_tail_not_observed(self):
        t = self.track(fixture())['temporal']
        self.assertEqual(t['last_sample_posture'],'not_observed')
        self.assertEqual(t['last_observed_posture'],'standing')

    def test_null_zero_quality_and_tracking(self):
        s = fixture(); q = s['cameras'][0]['quality']
        q.update(detection_dropout_rate=None,pose_visibility=0.)
        s['cameras'][0]['tracks'][0]['reliability']['association_confidence']=None
        c = self.camera(s)
        self.assertIsNone(c['quality']['cv_reliability'])
        self.assertFalse(c['quality']['aggregate_inputs_complete'])
        self.assertEqual(c['quality']['pose_visibility'],0.)
        self.assertIsNone(c['tracks'][0]['reliability'])
        q['detection_dropout_rate']=0.
        self.assertTrue(self.camera(s)['quality']['aggregate_inputs_complete'])

    def test_low_confidence_basis_preserved(self):
        s=fixture(('unknown',)*3)
        for f in s['cameras'][0]['frames'][:3]:
            f['detections'][0]['posture'].update(basis='low_confidence',confidence=.1)
        tr=self.track(s)['temporal']
        self.assertEqual(tr['runs'][0][3:], [.1,['low_confidence']])
        self.assertIsNone(tr['last_known_posture'])

    def test_unavailable_drop_does_not_claim_normal_measurement(self):
        s=fixture(); t=s['cameras'][0]['tracks'][0]
        t['vertical_transition']['upright_to_low_transition']=True
        out=self.track(s)['strongest_vertical_transition']['downward_change_bh']
        self.assertIsNone(out['value']); self.assertEqual(out['reliability'],'limited')

    def test_truncation_and_singleton(self):
        s=pair_fixture(fixture(tracks=8)); cam=s['cameras'][0]
        cam['tracks'][-1]['reliability']['observed_frames']=1
        src={'from_track':'T07','to_track':'T08','gap_sec':1.,'distance_body_heights':.4,'posture_change':None}
        cam['scene_observations']['fragment_links']=[src]
        c=self.camera(s); coverage=c['selection_coverage']
        self.assertEqual(len(c['tracks']),6); self.assertEqual(len(c['interactions']),4)
        self.assertEqual(coverage['tracks_omitted'],2)
        self.assertEqual(coverage['pairs_omitted'],24)
        self.assertEqual(coverage['omitted_tracks_with_low_samples'],2)
        self.assertEqual(coverage['fragment_links_omitted'],1)

    def test_pair_gap_close_duration(self):
        c=self.camera(pair_fixture(fixture(indices=(0,1,4),tracks=2)))
        p=c['interactions'][0]
        self.assertEqual(p['close_adjacent_span_sec'],1.)
        self.assertEqual(p['coverage']['missing_inside_span_samples'],2)
        self.assertEqual(p['distance_change_bh_per_sec'],0.)

    def test_contact_proxy_missing_terms_remain_unknown(self):
        s=pair_fixture(fixture(tracks=2)); p=s['cameras'][0]['pairwise_interactions'][0]
        p['contact_proxy']['score']=None
        p['contact_proxy']['terms']={k:None for k in p['contact_proxy']['terms']}
        out=self.camera(s)['interactions'][0]
        self.assertEqual(out['contact_proxy_terms_available'],0)
        self.assertIsNone(out['contact_proxy']['value'])

    def test_determinism_and_no_input_mutation(self):
        s=pair_fixture(fixture(tracks=8)); before=canonical_json(s)
        self.assertEqual(prepare_compact(s,'v2'),prepare_compact(copy.deepcopy(s),'v2'))
        self.assertEqual(before,canonical_json(s))

    def test_schema_rejects_extra_wrong_types(self):
        schema=json.loads((ROOT/'schemas/compact_decision_state_v2.schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        out=prepare_compact(fixture(),'v2')['compact']; out['cameras'][0]['tracks'][0]['coverage']['clip_sample_fraction']='unknown'
        with self.assertRaises(ValidationError): Draft202012Validator(schema).validate(out)

    def test_fragment_limit_and_omitted_transition_evidence(self):
        s=fixture(tracks=8); c=s['cameras'][0]
        c['tracks'][-1]['vertical_transition']['upright_to_low_transition']=True
        for n in range(1,7):
            c['scene_observations']['fragment_links'].append({'from_track':f'T{n:02d}','to_track':f'T{n+1:02d}',
                'gap_sec':1.,'distance_body_heights':.4,'posture_change':None})
        out=self.camera(s)
        self.assertEqual([t['track_ref'] for t in out['tracks']],['T1','T2','T3','T4','T5','T6'])
        self.assertEqual(len(out['scene']['fragment_links']),4)
        self.assertEqual(out['selection_coverage']['fragment_links_omitted'],2)
        self.assertEqual(out['selection_coverage']['omitted_tracks_with_upright_to_low'],1)

    def test_canonical_fixture_schema(self):
        schema=json.loads((ROOT.parent/'p0_cv_only/schemas/canonical_cv_state.schema.json').read_text(encoding='utf-8'))
        for s in (fixture(),fixture(('standing','horizontal','unknown'),(61,62,63))):
            Draft202012Validator(schema).validate(s)

    def test_invalid_version_and_timestamps(self):
        with self.assertRaises(ValueError): prepare_compact(fixture(),'v3')
        s=fixture(); s['cameras'][0]['sampling']['timestamps_sec'][2]=1.
        with self.assertRaises(ValueError): prepare_compact(s,'v2')

    def test_invalid_track_reference_and_pair_alignment(self):
        s=fixture(); s['cameras'][0]['frames'][0]['detections'][0]['track_id']='T99'
        with self.assertRaises(ValueError): prepare_compact(s,'v2')
        s=pair_fixture(fixture(tracks=2)); s['cameras'][0]['pairwise_interactions'][0]['distance_series'][0][0]=.5
        with self.assertRaises(ValueError): prepare_compact(s,'v2')

    def test_empty_camera_is_not_normal(self):
        s=fixture(); c=s['cameras'][0]; c['tracks']=[]
        for f in c['frames']: f['detections']=[]; f['person_count']=0
        for k in ('pose_visibility','detection_dropout_rate','track_fragmentation','occlusion_proxy','small_person_fraction','overall_cv_reliability'): c['quality'][k]=None
        c['quality']['overall_cv_reliability_label']='unknown'
        out=self.camera(s)
        self.assertEqual(out['tracks'],[])
        self.assertIsNone(out['quality']['cv_reliability'])


if __name__ == '__main__': unittest.main()
