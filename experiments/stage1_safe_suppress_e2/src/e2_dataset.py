"""Human provenance + independent group audit. No model-derived GT accepted."""
import csv
from collections import Counter
from pathlib import Path

from e2_common import PROJECT, ROOT, read, write, file_hash, digest

LABELS=['CLEAR_NORMAL','HARD_NEGATIVE_NORMAL','ANCHORED_DANGER','AMBIGUOUS']


def repository_audit():
    source_path=PROJECT/'benchmark_triage_v1/manifests/source_manifest.json'
    split_path=PROJECT/'benchmark_triage_v1/manifests/split_manifest.json'
    scene_path=PROJECT/'benchmark_triage_v1/manifests/scene_manifest.json'
    sources=read(source_path)['sources']; split=read(split_path); scene=read(scene_path)
    blocked_groups=set(split['split_groups']) | {s['split_group_id'] for s in sources if s['used_in_reasoning_v1']}
    blocked_scenes={s['scene_group_id'] for s in sources if s['split_group_id'] in blocked_groups}
    blocked_sources={s['source_id'] for s in sources if s['split_group_id'] in blocked_groups}
    hashes=set()
    for name in ('benchmark_triage_v1/public_manifest.json','benchmark_triage_v1/challenge_public_manifest.json'):
        for item in read(PROJECT/name)['items']:
            hashes.update(c['sha256'] for c in item['cameras'])
    hashes.update(m['sha256'] for m in read(PROJECT/'benchmark_v1/public_manifest.json')['media'].values())
    build=read(PROJECT/'benchmark_v1/private_ground_truth/media_build_records.json')
    hashes.update(x['source_sha256'] for x in build.values() if x.get('source_sha256'))
    rows=list(csv.DictReader((PROJECT/'benchmark_triage_v1/review/human_review_queue.csv').open(encoding='utf-8-sig')))
    pool=list(csv.DictReader((PROJECT/'benchmark_triage_v1/candidate_pool/candidates.csv').open(encoding='utf-8-sig')))
    eligible_reviewed=[x for x in rows if x['review_label'] and x['split_group_id'] not in blocked_groups
        and x['scene_group_id'] not in blocked_scenes and x['source_video_id'] not in blocked_sources]
    # Copy only neutral provenance to queue; never existing GT, dataset labels or discovery hints.
    queue=[]
    for x in pool:
        reasons=[]
        if x['source_video_id'] in blocked_sources: reasons.append('SOURCE_USED_OR_SHARED_GROUP')
        if x['scene_group_id'] in blocked_scenes: reasons.append('SCENE_USED_OR_SHARED_GROUP')
        if x['split_group_id'] in blocked_groups: reasons.append('PHYSICAL_GROUP_USED')
        queue.append({'queue_id':x['window_id'],'source_id':x['source_video_id'],
            'scene_group_id':x['scene_group_id'],'physical_group_id':x['split_group_id'],
            'start_sec':x['start_sec'],'end_sec':x['end_sec'],
            'eligibility':'EXCLUDED' if reasons else 'NEEDS_INDEPENDENCE_AND_HUMAN_REVIEW',
            'exclusion_reasons':';'.join(reasons),'human_label':'','reviewer':'','reviewed_at':''})
    known_paths={str((PROJECT/s['local_read_path']).resolve()):s['source_id'] for s in sources}
    known_paths.update({str((PROJECT/s['original_path']).resolve()):s['source_id'] for s in sources if '::' not in s['original_path']})
    known_paths.update({str(Path(x['source_path']).resolve()):'previous_reasoning_source' for x in build.values() if x.get('source_path')})
    canonical_hashes=[file_hash(p) for folder in ['experiments/p0_cv_only/states','experiments/triage_frozen_v1/cv_states']
                      for p in (PROJECT/folder).glob('*.json')]
    exclusion={'schema_version':'e2-exclusions-v1','source_ids':sorted(blocked_sources),
        'scene_group_ids':sorted(blocked_scenes),'physical_group_ids':sorted(blocked_groups),
        'media_sha256':sorted(hashes),'known_source_paths':known_paths,'previous_canonical_sha256':sorted(canonical_hashes),
        'manifest_hashes':{str(p.relative_to(PROJECT)):file_hash(p) for p in (source_path,split_path,scene_path)}}
    write(ROOT/'data/exclusion_registry.json',exclusion)
    qpath=ROOT/'data/human_review_queue.csv'
    with qpath.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(queue[0])); writer.writeheader(); writer.writerows(queue)
    stats={'source_count':len(sources),'candidate_pool_windows':len(pool),'review_queue_count':len(rows),
        'existing_reviewed_count':sum(bool(x['review_label']) for x in rows),
        'frozen_primary_count':len(split['primary_candidate_ids']),
        'challenge_count':len(split['ambiguous_candidate_ids']),
        'independent_human_gt_count':len(eligible_reviewed),
        'eligible_gt_distribution':dict(Counter(x['review_label'] for x in eligible_reviewed)),
        'blocked_physical_groups':sorted(blocked_groups),'blocked_scene_count':len(blocked_scenes),
        'pool_eligible_by_known_groups':sum(x['eligibility']!='EXCLUDED' for x in queue),
        'limitations':['Grouped local candidate pool audit, not proof that all raw downloads are exhausted.',
            'Evaluation-selection agent visual reviews and source XML are not Human GT.',
            'Other team frozen media must be checked by future human independence review; current eligible count zero.'],
        'status':'NO_ELIGIBLE_HUMAN_GT' if not eligible_reviewed else 'REQUIRES_MANIFEST_REVIEW',
        'registry_hash':digest(exclusion)}
    team_manifest=PROJECT.parent/'477_team_benchmark_v1/items.json'
    if team_manifest.is_file():
        team=read(team_manifest)
        stats['additional_previous_team_items']=team['item_count']
        stats['team_source_identity_limit']='Generic SRCxx IDs; no verified raw scene/physical source mapping in public items.json. Future Human independence audit must include this dataset.'
    write(ROOT/'reports/dataset_audit.json',stats)
    return stats


def validate_manifest(manifest):
    registry=read(ROOT/'data/exclusion_registry.json')
    if manifest.get('schema_version')!='e2-development-v1': raise ValueError('manifest schema_version')
    candidates=manifest.get('candidates')
    if not isinstance(candidates,list): raise ValueError('candidates must be list')
    seen=set(); reasons={}; eligible=[]
    for c in candidates:
        cid=c.get('candidate_id'); errors=[]
        if not isinstance(cid,str) or not cid or cid in seen: raise ValueError('missing/duplicate candidate_id')
        seen.add(cid)
        for key, registry_key in [('source_id','source_ids'),('scene_group_id','scene_group_ids'),('physical_group_id','physical_group_ids')]:
            if not c.get(key): errors.append('MISSING_'+key.upper())
            elif c[key] in registry[registry_key]: errors.append('OVERLAP_'+key.upper())
        h=c.get('human_gt',{})
        if h.get('label') not in LABELS or h.get('basis')!='human_original_video' or not h.get('reviewer') or not h.get('reviewed_at') or h.get('watched_full_window') is not True or not h.get('observable_summary'):
            errors.append('HUMAN_GT_INCOMPLETE')
        independence=c.get('independence',{})
        required_prior={'477-triage-normal-v1','477-reasoning-v1','new477-total64-v1'}
        if independence.get('status')!='confirmed' or not independence.get('reviewer') or not independence.get('evidence') or not independence.get('checked_at') or not required_prior.issubset(set(independence.get('checked_datasets',[]))):
            errors.append('INDEPENDENCE_UNCONFIRMED')
        video=Path(c.get('original_video_path','__missing__'))
        if not video.is_absolute(): video=PROJECT/video
        if str(video.resolve()) in registry['known_source_paths']: errors.append('KNOWN_EXCLUDED_SOURCE_PATH')
        if not video.is_file(): errors.append('ORIGINAL_VIDEO_MISSING')
        else:
            hv=file_hash(video)
            if hv!=c.get('original_video_sha256'): errors.append('VIDEO_HASH_MISMATCH')
            if hv in registry['media_sha256']: errors.append('MEDIA_CONTENT_OVERLAP')
        state=Path(c.get('canonical_path','__missing__'))
        if not state.is_absolute(): state=PROJECT/state
        if not state.is_file(): errors.append('CANONICAL_MISSING')
        else:
            if file_hash(state)!=c.get('canonical_sha256'): errors.append('CANONICAL_HASH_MISMATCH')
            if file_hash(state) in registry['previous_canonical_sha256']: errors.append('PREVIOUS_CANONICAL_CONTENT')
            # Previous cached CV and synthetic examples cannot be mislabeled as independent.
            if any(part in state.parts for part in ('triage_frozen_v1','team_frozen_v1','p0_cv_only','e1_v2')):
                errors.append('PREVIOUS_OR_SYNTHETIC_CANONICAL')
            provenance=c.get('cv_provenance',{})
            if provenance.get('original_video_sha256')!=c.get('original_video_sha256') or provenance.get('canonical_sha256')!=c.get('canonical_sha256') or not provenance.get('builder_version'):
                errors.append('CV_MEDIA_LINK_UNCONFIRMED')
        import math
        if not isinstance(c.get('start_sec'),(int,float)) or not isinstance(c.get('end_sec'),(int,float)) or not math.isfinite(c.get('start_sec',0)) or not math.isfinite(c.get('end_sec',0)) or c.get('start_sec',0)<0 or c.get('end_sec',0)<=c.get('start_sec',0):
            errors.append('INVALID_WINDOW')
        reasons[cid]=sorted(set(errors))
        if not errors: eligible.append(c)
    return {'eligible':eligible,'exclusions':reasons,'registry_hash':digest(registry),
        'gt_distribution':dict(Counter(c['human_gt']['label'] for c in eligible))}
