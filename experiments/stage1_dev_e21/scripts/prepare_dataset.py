"""Audit, explicit Human independence curation, finalized-only export, offline E2 prep."""
import argparse,collections,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from dev_common import ROOT,PROJECT,E2,read,write,sha,digest,now,PRIOR,LABELS
from media_integrity import validate_candidate,source_screen,similarity
from review_store import Reviews,export_review_problems


def inventory():
    known=read(E2/'data/exclusion_registry.json'); paths=[]; archives=[]
    for folder in ('data','downloads','benchmark_v1/media','benchmark_triage_v1/media'):
        for p in (PROJECT/folder).rglob('*'):
            if not p.is_file(): continue
            if p.suffix.lower() in ('.mp4','.avi','.mov','.mkv'):
                exact=str(p.resolve()) in known['known_source_paths']
                # Broad filesystem inventory, not mass hashing multi-GB unverified raw archives.
                paths.append({'path':str(p),'bytes':p.stat().st_size,'sha256':None,
                    'hash_status':'not computed in broad inventory; actual admitted E21 sources are hashed separately',
                    'status':'HISTORICAL_EXCLUDED' if exact else 'INDEPENDENCE_UNVERIFIED'})
            elif p.suffix.lower()=='.zip':
                try:
                    with zipfile.ZipFile(p) as z:
                        movies=[{'member':e.filename,'uncompressed_bytes':e.file_size} for e in z.infolist() if e.filename.lower().endswith(('.mp4','.avi','.mov','.mkv'))]
                    archives.append({'path':str(p),'video_members':movies,'status':'INDEPENDENCE_UNVERIFIED; same AIHub collection/session overlap must be resolved'})
                except Exception as e: archives.append({'path':str(p),'error':type(e).__name__})
    write(ROOT/'reports/local_inventory.json',{'raw_videos':paths,'archives':archives,'video_count':len(paths),
        'unknown_video_count':sum(p['status']=='INDEPENDENCE_UNVERIFIED' for p in paths),'new_gt_count':0,
        'note':'No source was admitted by filename or dataset action. Unregistered/ZIP members are not independent Human GT. Mock stream media is rights/group-unverified.'})
    print('local inventory',len(paths),'videos',len(archives),'archives')


def export(include_single=False):
    sys.path.insert(0,str(E2/'src'))
    from e2_dataset import validate_manifest
    from e2_inputs import prepare_arms
    from jsonschema import Draft202012Validator
    data=read(ROOT/'data/sources.json'); sources={s['source_id']:s for s in data['sources']}
    pool=read(ROOT/'data/pool.json'); Draft202012Validator(read(ROOT/'data/pool.schema.json')).validate(pool)
    ids=[c['candidate_id'] for c in pool['candidates']]
    if len(ids)!=len(set(ids)): raise ValueError('duplicate pool candidate ID')
    reviews=Reviews(); candidates=[]; exclusions={}; prep=[]
    historical=read(ROOT/'data/historical_fingerprints.json') if (ROOT/'data/historical_fingerprints.json').exists() else None
    labels={k:{'reviewed':0,'finalized':0} for k in LABELS}
    states=collections.Counter(); cv=collections.Counter(); integrity={}
    for c in pool['candidates']:
        cid=c['candidate_id']; s=sources[c['source_id']]; r=reviews.get(cid); states[reviews.status(cid)]+=1; cv[c['cv_status']]+=1
        for x in Reviews.current(r): labels[x['label']]['reviewed']+=1
        if r['finalization']: labels[r['finalization']['label']]['finalized']+=1
        problems=validate_candidate(c,s)+source_screen(s,historical)
        try: Draft202012Validator(read(ROOT/'data/human_review.schema.json')).validate(r)
        except Exception: problems.append('HUMAN_REVIEW_SCHEMA_INVALID')
        if s.get('independence_status')!='CONFIRMED' or not s.get('independence'): problems.append('INDEPENDENCE_UNVERIFIED')
        media_hash=digest({k:c[k] for k in ('source_video_sha256','clip_sha256','clip_start_sec','clip_end_sec')})
        problems.extend(export_review_problems(r,include_single,media_hash))
        integrity[cid]=problems
        # Prepare real unlabelled model inputs even before Human labeling; never an API request.
        if c['cv_status']=='READY' and not any(x.startswith('CANONICAL') for x in problems):
            try:
                arms=prepare_arms(read(c['canonical_cv_state_path']))
                prep.append({'candidate_id':cid,'canonical_sha256':c['canonical_cv_state_sha256'],
                    'arms':{a:{'request_hash':x['request_hash'],'input_hash':x['input_hash'],'prompt_hash':x['prompt_hash']} for a,x in arms.items()}})
                for a,x in arms.items(): write(ROOT/'data/prepared'/cid/f'{a}.json',x)
            except Exception as e: problems.append('COMPACT_PREP_FAILED:'+type(e).__name__)
        if problems: exclusions[cid]=sorted(set(problems)); continue
        f=r['finalization']; rr=Reviews.current(r)
        summary='\n'.join(x['observable_summary'] for x in rr)
        item={'candidate_id':cid,'source_id':c['source_id'],'scene_group_id':c['scene_group_id'],'physical_group_id':c['physical_group_id'],
            'original_video_path':c['source_video_path'],'original_video_sha256':c['source_video_sha256'],
            'start_sec':c['clip_start_sec'],'end_sec':c['clip_end_sec'],'canonical_path':c['canonical_cv_state_path'],
            'canonical_sha256':c['canonical_cv_state_sha256'],'human_gt':{'label':f['label'],'basis':'human_original_video',
                'reviewer':';'.join(x['reviewer'] for x in rr),'reviewed_at':f['finalized_at'],'watched_full_window':True,'observable_summary':summary},
            'independence':s['independence'],'cv_provenance':{'original_video_sha256':c['source_video_sha256'],
                'canonical_sha256':c['canonical_cv_state_sha256'],'builder_version':'e21-unchanged-p0-uniform64-v1'}}
        candidates.append(item)
    manifest={'schema_version':'e2-development-v1','dataset_id':'e21-independent-human-development-v1','candidates':candidates}
    Draft202012Validator(read(E2/'data/development_manifest.schema.json')).validate(manifest)
    gate=validate_manifest(manifest)
    for cid,errors in gate['exclusions'].items():
        if errors: exclusions[cid]=errors
    manifest['candidates']=gate['eligible']
    write(ROOT/'data/development_manifest.json',manifest)
    # Reserve these admitted/curated development groups against any future calibration/safety test reuse.
    write(ROOT/'data/development_group_registry.json',{'purpose':'Exclude used Development collection groups from future independent safety test; no forced split',
        'source_ids':sorted({c['source_id'] for c in pool['candidates']}),
        'scene_group_ids':sorted({c['scene_group_id'] for c in pool['candidates']}),
        'physical_group_ids':sorted({c['physical_group_id'] for c in pool['candidates']})})
    write(ROOT/'reports/readiness.json',{'candidate_count':len(pool['candidates']),'source_count':len(sources),
        'physical_group_count':len({s['physical_group_id'] for s in sources.values()}),'scene_group_count':len({s['scene_group_id'] for s in sources.values()}),
        'cv_status':dict(cv),'review_status':dict(states),'human_gt':labels,'finalized_eligible':len(gate['eligible']),
        'abcd_prepared':len(prep),'api_calls':0,'paid_pilot_ready':bool(gate['eligible']),
        'integrity_or_admission_issues':exclusions,'registry_hash':gate['registry_hash'],
        'single_reviewer_included_by_explicit_option':include_single,'source_candidate_counts':dict(collections.Counter(c['source_id'] for c in pool['candidates']))})
    write(ROOT/'reports/abcd_alignment.json',prep)
    print('eligible finalized',len(gate['eligible']),'ABCD prepared',len(prep),'CV',dict(cv))


def main():
    p=argparse.ArgumentParser(); p.add_argument('phase',choices=['inventory','export','confirm-independence'])
    p.add_argument('--source-id'); p.add_argument('--reviewer'); p.add_argument('--evidence'); p.add_argument('--checked-datasets',nargs='+')
    p.add_argument('--include-single-reviewer',action='store_true'); args=p.parse_args()
    if args.phase=='inventory': inventory(); return
    if args.phase=='export': export(args.include_single_reviewer); return
    if not args.source_id or not args.reviewer or not args.evidence or not set(PRIOR).issubset(set(args.checked_datasets or [])):
        p.error('Human curator source ID/reviewer/evidence and all three prior dataset checks required')
    data=read(ROOT/'data/sources.json'); s=next(x for x in data['sources'] if x['source_id']==args.source_id)
    index=read(ROOT/'data/historical_fingerprints.json')
    issues=source_screen(s,index)
    if issues: p.error('overlap flags require separate evidence-based resolution, cannot bypass: '+str(issues))
    s['independence_status']='CONFIRMED'; s['independence']={'status':'confirmed','reviewer':args.reviewer,
        'checked_at':now(),'evidence':args.evidence,'checked_datasets':args.checked_datasets}
    write(ROOT/'data/sources.json',data); print('Human independence attestation saved; no GT label generated.')


if __name__=='__main__': main()
