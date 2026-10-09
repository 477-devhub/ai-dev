"""EVALUATOR ONLY. Build evaluation/normalized_ground_truth_v1.json from benchmark_v1/private_ground_truth.

Runs only after freeze/p2_results_manifest.json exists (prediction freeze precedes any GT access). Not imported by
any model-path module. Source labels are normalized to observable-safe targets; they never imply diagnosis,
criminality, intent or authorization. Source label, human-verified observation and project-defined reference are
kept as separate fields; incident presence is scored only where a human-verified anchor exists.
"""
import _bootstrap  # noqa: F401
import datetime
import json
import sys

from process_log import log_event
from utils import BENCH_ROOT, EVAL_DIR, FREEZE_DIR, sha256_file, write_json

GT_DIR = BENCH_ROOT / 'private_ground_truth'

# source label -> observable-safe normalized target (meaning is limited to the observable pattern)
LABEL_NORMALIZATION = {
    'swoon': {'target': 'possible_fall_or_person_down', 'does_not_mean': ['medical fainting', 'unconsciousness', 'diagnosis']},
    'falldown': {'target': 'possible_fall_or_person_down', 'does_not_mean': ['medical cause', 'injury']},
    'fight': {'target': 'possible_physical_conflict', 'does_not_mean': ['criminal assault', 'intent', 'culpability']},
    '신체적 충돌을 동반한 싸움': {'target': 'possible_physical_conflict', 'does_not_mean': ['criminal assault', 'intent', 'culpability']},
    'trespass': {'target': 'possible_scene_or_boundary_entry', 'does_not_mean': ['unauthorized', 'illegal', 'criminal']},
    'climbwall': {'target': 'possible_scene_or_boundary_entry', 'does_not_mean': ['unauthorized', 'illegal', 'criminal']},
    'entry': {'target': 'possible_scene_or_boundary_entry', 'does_not_mean': ['unauthorized', 'illegal', 'criminal']},
}
MUST_REMAIN_UNKNOWN = {
    'possible_fall_or_person_down': {'medical_diagnosis': True, 'injury_severity': True, 'identity': True},
    'possible_physical_conflict': {'criminal_intent': True, 'weapon_unless_visible': True, 'identity': True},
    'possible_scene_or_boundary_entry': {'authorization': True, 'criminal_intent': True, 'identity': True},
}
FPS = 30.0


def load(name):
    return json.loads((GT_DIR / name).read_text(encoding='utf-8'))


def norm(label):
    return LABEL_NORMALIZATION[label]


def single(item, set_id, gt, *, ambiguous, incident_anchor, temporal=None, notes=None, camera='CAM_01'):
    label = gt['source_ground_truth']['source_event_label']
    n = norm(label)
    return {
        'item_id': item, 'set': set_id, 'task': 'single', 'cameras': [camera],
        'source_label': label,
        'normalized_event_target': n['target'], 'acceptable_categories': [n['target']],
        'normalization_does_not_mean': n['does_not_mean'],
        'human_verified_observation': {k: v for k, v in gt['human_verified_observation'].items() if k != 'provenance'},
        'project_reference': {k: gt['project_defined_reference'][k] for k in ('core_observable_sequence', 'expected_uncertainty')
                              if k in gt['project_defined_reference']},
        'must_remain_unknown': MUST_REMAIN_UNKNOWN[n['target']],
        'incident_presence_anchor': incident_anchor,
        'temporal_reference': temporal or {'status': 'requires_human_audit',
                                           'reason': 'no human-verified clip-relative event interval in the private benchmark; '
                                                     'AI Hub action frames are not treated as exact visual truth'},
        'ambiguous_case': ambiguous,
        'human_audit_required_for_final_quality': ambiguous,
        'notes': notes or [],
    }


def main():
    if not (FREEZE_DIR / 'p2_results_manifest.json').exists():
        sys.exit('P2 results not frozen; ground truth must not be read yet')
    log_event('build_auto_ground_truth', {'phase': 'start'})
    s1, s2, s3, s4, s5 = (load(f'set0{i}.json') for i in range(1, 6))
    hv_fall_anchor = {'value': True, 'provenance': 'human_verified_observation: normal_movement_then_fall + remains_in_ground_posture_afterward',
                      'meaning': 'a person-down condition an operator should see; not a medical claim'}
    no_anchor = {'value': None, 'status': 'not_scored', 'reason': 'no human-verified incident-presence anchor; source-positive label alone is not used'}
    # SET03: visually inspected source times (human source-pixel review), converted to clip-relative seconds
    c3 = s3['project_defined_reference']['clip_selection']
    t0 = c3['selected_start_sec']
    temporal3 = {'status': 'scorable', 'provenance': 'project_defined_reference.clip_selection (visual source inspection, user-approved), not XML',
                 'key_transition': 'crossing the open gate', 'clip_interval_sec': [round(285.0 - t0, 2), round(286.0 - t0, 2)],
                 'tolerance_sec': 1.0, 'rule': 'temporal_hit if any prediction observation timestamp lies within the interval +/- tolerance'}
    items = {
        'ITEM_01': single('ITEM_01', 'SET01', s1, ambiguous=False, incident_anchor=hv_fall_anchor),
        'ITEM_02': single('ITEM_02', 'SET02', s2, ambiguous=False, incident_anchor=no_anchor),
        'ITEM_03': single('ITEM_03', 'SET03', s3, ambiguous=True, incident_anchor=no_anchor, temporal=temporal3,
                          notes=['ambiguous: only the observable entry category is auto-evaluated; authorization and criminal intent are not GT',
                                 s3['project_defined_reference'].get('correct_event_understanding_allows', '')]),
    }
    cams4 = s4['source_ground_truth']['cameras']
    ref4 = s4['project_defined_reference']
    labels4 = {c: cams4[c]['annotation']['event']['eventname'] for c in ('CAM_01', 'CAM_02', 'CAM_03')}
    items['ITEM_04'] = {
        'item_id': 'ITEM_04', 'set': 'SET04', 'task': 'attention', 'cameras': ['CAM_01', 'CAM_02', 'CAM_03'],
        'per_camera': {c: {'source_label': labels4[c], 'normalized_event_target': norm(labels4[c])['target'],
                           'acceptable_categories': [norm(labels4[c])['target']],
                           'must_remain_unknown': MUST_REMAIN_UNKNOWN[norm(labels4[c])['target']],
                           'incident_presence_anchor': hv_fall_anchor if c == 'CAM_01' else no_anchor}
                       for c in ('CAM_01', 'CAM_02', 'CAM_03')},
        'per_camera_label_source': 'set04 source cameras (S14 swoon = SET01 clip, F01 fight, T06 trespass = SET02 clip); CAM_01 anchor inherits SET01 human verification (byte-identical clip)',
        'source_candidates': {c: cams4[c]['source_candidate'] for c in ('CAM_01', 'CAM_02', 'CAM_03')},
        'reference_order': ref4['reference_camera_order'],
        'reference_provenance': '477 project-defined human reference (NOT AI Hub ground truth)',
        'reference_rationale': ref4['reference_rationale'],
        'ambiguous_case': False, 'human_audit_required_for_final_quality': False,
    }
    fight = norm(s5['source_ground_truth']['source_event_label'])
    p5 = s5['project_defined_reference']
    for item, cams, cond in (('ITEM_05', ['CAM_01'], 'MV05_A'), ('ITEM_06', ['CAM_02'], 'MV05_B'), ('ITEM_07', ['CAM_01', 'CAM_02'], 'MV05_AB')):
        items[item] = {
            'item_id': item, 'set': 'SET05', 'condition': cond, 'task': 'multi_camera' if item == 'ITEM_07' else 'single', 'cameras': cams,
            'source_label': s5['source_ground_truth']['source_event_label'],
            'normalized_event_target': fight['target'], 'acceptable_categories': [fight['target']],
            'normalization_does_not_mean': fight['does_not_mean'],
            'must_remain_unknown': dict(MUST_REMAIN_UNKNOWN[fight['target']], **({'cross_camera_identity': True, 'synchronization': True} if item == 'ITEM_07' else {})),
            'incident_presence_anchor': no_anchor,
            'temporal_reference': {'status': 'requires_human_audit', 'reason': 'no human-verified clip-relative interval; no official frame synchronization'},
            'ambiguous_case': False, 'human_audit_required_for_final_quality': False,
            'notes': [p5['grounded_complementarity_reference']] + (p5['limitations'] if item == 'ITEM_07' else []),
        }
    items['ITEM_07'].update({'same_incident_reference': p5['same_incident_reference'], 'same_incident_basis': p5['same_incident_basis'],
                             'expected_camera_count': 2, 'single_view_items': {'A': 'ITEM_05', 'B': 'ITEM_06'},
                             'multiview_increment_rubric': 'NOT auto-generated (0-8 human rubric only)'})
    out = {
        'version': 'normalized-ground-truth-v1',
        'built_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        'access': 'evaluator only; built after freeze/p2_results_manifest.json; never read by any model-execution path',
        'sources': {f'private_ground_truth/set0{i}.json': sha256_file(GT_DIR / f'set0{i}.json') for i in range(1, 6)},
        'label_normalization': LABEL_NORMALIZATION,
        'category_vocabulary': ['no_clear_incident', 'possible_fall_or_person_down', 'possible_physical_conflict',
                                'possible_scene_or_boundary_entry', 'other_safety_relevant', 'uncertain'],
        'items': items,
    }
    write_json(EVAL_DIR / 'normalized_ground_truth_v1.json', out)
    log_event('build_auto_ground_truth', {'phase': 'end', 'file': 'evaluation/normalized_ground_truth_v1.json'})
    print('wrote evaluation/normalized_ground_truth_v1.json')
    for k, v in items.items():
        print(k, v.get('normalized_event_target') or {c: x['normalized_event_target'] for c, x in v['per_camera'].items()},
              '| ambiguous' if v['ambiguous_case'] else '')


if __name__ == '__main__':
    main()
