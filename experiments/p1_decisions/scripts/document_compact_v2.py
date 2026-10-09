"""Generate complete schema inventories and v2 field reference, offline."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fields(schema):
    def walk(node, path):
        if '$ref' in node:
            node = dict(schema['$defs'][node['$ref'].split('/')[-1]], **{k:v for k,v in node.items() if k != '$ref'})
        yield path, node
        for key, value in node.get('properties', {}).items():
            yield from walk(value, f'{path}.{key}' if path else key)
        if isinstance(node.get('items'), dict): yield from walk(node['items'],path+'[]')
        for branch in node.get('oneOf', []):
            if branch.get('type') != 'null': yield from walk(branch,path)
    return list(walk(schema,''))


def dtype(n):
    if 'enum' in n: return 'enum ' + json.dumps(n['enum'],ensure_ascii=False)
    if 'const' in n: return 'const ' + json.dumps(n['const'])
    if 'oneOf' in n: return 'object / null'
    return str(n.get('type','object'))


def nullable(n):
    t=n.get('type',[])
    return '예' if t == 'null' or 'null' in (t if isinstance(t,list) else []) or None in n.get('enum',[]) or any(x.get('type')=='null' for x in n.get('oneOf',[])) else '아니오'


RENAMES = {
 'camera':'camera_id', 'observation_window_sec':'duration_sec', 'cv_reliability':'overall_cv_reliability',
 'cv_reliability_label':'overall_cv_reliability_label', 'count_min':'person_count_min', 'count_max':'person_count_max',
 'count_median':'person_count_median', 'track_ref':'track_id (T01→T1)', 'reliability':'reliability_score / pair reliability',
 'minimum_distance_bh':'minimum_normalized_distance', 'mean_distance_bh':'mean_normalized_distance',
 'close_fraction':'close_proximity_fraction', 'approach_rate_bh_per_sec':'approach_rate', 'approach_events':'repeated_approach_count',
 'relative_motion_when_close_bh_per_sec':'relative_motion_intensity_when_close',
 'arm_extension_score':'arm_extension_toward_other_score', 'contact_proxy':'contact_proxy.score',
 'mean_speed_bh_per_sec':'body_height_speed_mean', 'max_speed_bh_per_sec':'body_height_speed_max',
 'net_displacement_fh':'net_displacement', 'entry':'scene_observations.track_entries.type', 'exit':'scene_observations.track_exits.type',
 'tracks':'track_a / track_b (per-camera refs)', 'distance_bh':'distance_body_heights',
 'from':'from_posture', 'to':'to_posture', 'observed':'upright_to_low_transition',
 'start_sec':'transition_start_sec', 'end_sec':'transition_end_sec', 'duration_sec':'transition_duration_sec',
 'downward_change_bh':'max_downward_change / fragment posture_change.downward_change',
 'visibility_complementarity':'visibility_complementarity_score',
 'camera_a_visibility_drop_observed':'camera_a_visibility_drop', 'camera_b_visibility_drop_observed':'camera_b_visibility_drop',
 'person_count_by_phase':'phase_curves[camera].count',
}


def legacy_source(path):
    k=path.rsplit('.',1)[-1].replace('[]','')
    if path in ('cameras','cameras[]'): return 'state.cameras'
    if k=='tracks' and '.interactions' not in path: return 'camera.tracks (v1 selection)'
    if k=='interactions': return 'camera.pairwise_interactions (v1 selection)'
    if k=='scene': return 'camera.scene_observations'
    if k=='cross_camera': return 'state.cross_camera (base observations only)'
    if k=='strongest_vertical_transition': return 'camera.tracks.vertical_transition (strongest Canonical observation)'
    if k=='temporal': return 'camera.frames.detections.posture / tracks.observations'
    if k=='coverage': return 'camera.tracks.observations / sampling.timestamps_sec; pairs use index intersection'
    if k=='selection_coverage': return 'whole camera tracks/pairs/fragment_links vs selected sets'
    if k in ('schema_version','evidence_semantics'): return 'serializer constant'
    if k=='task': return 'input.task'
    if k=='initial_posture': return 'tracks.posture.timeline (first non-unknown)'
    if 'posture_distribution' in path: return 'tracks.posture.timeline (all detected observations; unknown included)'
    if k in ('tracks_total','tracks_included'): return 'len(camera.tracks) / selected tracks'
    if k in ('entered_frame','exited_frame'): return 'scene track entry/exit type membership'
    if k in ('person_entry_observed','person_exit_observed','large_spatial_transition_observed','occlusion_candidate_count'):
        return 'whole camera.scene_observations (any / count)'
    if k=='large_spatial_transition': return 'scene_observations.large_spatial_transitions (track membership)'
    if k in ('sync_confirmed','identity_link_confirmed','same_person_confirmed','boundary_semantics_available','authorization_known'):
        return 'false constant: unconfirmed / unavailable (not negation of event)'
    if k=='boundary_crossing': return 'null constant: no scene ROI semantics'
    if k=='alignment': return 'normalized clip phase only constant'
    if k in ('value','note') or k=='reliability' and any(x in path for x in ('proxy','score','similarity','downward_change')):
        return legacy_source(path.rsplit('.',1)[0]) + ' (proxy value / explicit limitation)'
    base='camera'
    if '.quality.' in path: base='camera.quality'
    elif '.people.' in path: base='camera.detection_summary'
    elif '.sampling.' in path: base='camera.sampling'
    elif '.interactions' in path: base='camera.pairwise_interactions'
    elif '.scene.' in path: base='camera.scene_observations'
    elif '.tracks' in path:
        base='camera.tracks'
        if '.motion.' in path: base += '.motion / low_motion'
        elif 'vertical_transition' in path: base += '.vertical_transition'
        elif k in ('observed_frames','ambiguous_links','reliability','reliability_label'): base += '.reliability'
        elif k in ('first_seen_sec','last_seen_sec'): base += '.detection'
    elif path.startswith('cross_camera'): base='cross_camera'
    return base + '.' + RENAMES.get(k,k)


def units(path,n):
    if 'x-units' in n: return n['x-units']
    k=path.rsplit('.',1)[-1]
    if 'bh_per_sec' in k: return 'body heights / second'
    if 'fh_per_sec' in k: return 'frame heights / second'
    if '_sec' in k: return 'seconds (clip-relative)'
    if '_bh' in k: return 'body heights'
    if '_fh' in k: return 'frame heights'
    if 'fraction' in k or 'reliability' in k or 'confidence' in k or 'score' in k or 'similarity' in k: return '0..1 proxy / enum'
    if any(x in k for x in ('count','frames','links','total','included')): return 'count'
    return 'dimensionless / enum / structure'


def main():
    canonical=json.loads((ROOT.parent/'p0_cv_only/schemas/canonical_cv_state.schema.json').read_text(encoding='utf-8'))
    v1=json.loads((ROOT/'schemas/compact_decision_state.schema.json').read_text(encoding='utf-8'))
    v2=json.loads((ROOT/'schemas/compact_decision_state_v2.schema.json').read_text(encoding='utf-8'))
    lines=['# E1 전체 Feature 및 필드 참조', '',
        'Schema의 전체 경로 목록이다. 배열 tuple의 원소 의미는 Schema description과 README를 참조한다. Canonical metadata·signature는 모델 입력에서 제외한다.', '',
        '## Canonical 전체 Feature', '', '| 경로 | 타입 | Nullable | Schema 의미 |','|---|---|---|---|']
    for path,n in fields(canonical):
        if path: lines.append(f"| `{path}` | {dtype(n)} | {nullable(n)} | {n.get('description','원본 Schema 필드; 계산 방식은 README의 코드 분석 참조')} |")
    lines += ['', '## Compact v1 전체 Feature', '', '| 경로 | 타입 | Nullable | Canonical 원천 / 계산 |','|---|---|---|---|']
    for path,n in fields(v1):
        if path: lines.append(f'| `{path}` | {dtype(n)} | {nullable(n)} | {legacy_source(path)} |')
    lines += ['', '## Compact v2 전체 필드', '', '| 경로 | 타입 | Nullable | 단위 | Canonical 원천 | 의미 / 요약 |','|---|---|---|---|---|---|']
    for path,n in fields(v2):
        if path:
            source=n.get('x-canonical-source',legacy_source(path))
            desc=n.get('description','v1 관측 요약 유지; 원천 값의 null을 보존')
            if 'x-summary' in n: desc += ' ' + n['x-summary']
            lines.append(f'| `{path}` | {dtype(n)} | {nullable(n)} | {units(path,n)} | {source} | {desc} |')
    (ROOT/'e1_v2/field_reference.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__': main()
