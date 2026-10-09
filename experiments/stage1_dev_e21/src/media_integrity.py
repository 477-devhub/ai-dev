"""Hash, time and image fingerprint screening; similarity is never proof of independence."""
import math
import subprocess
import json
from pathlib import Path

from dev_common import ROOT,PROJECT,E2,read,sha,write,digest


def probe(path):
    x=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_streams','-show_format','-of','json',str(path)],timeout=30))
    s=x['streams'][0]; a,b=map(float,s['avg_frame_rate'].split('/'))
    fps=a/b
    return {'duration_sec':float(s.get('duration',x['format']['duration'])),'fps':fps,
        'frame_count':int(s.get('nb_frames',round(float(x['format']['duration'])*fps))),
        'width':s['width'],'height':s['height'],'codec':s['codec_name']}


def fingerprint(path,times=None):
    import numpy as np
    duration=probe(path)['duration_sec']
    times=times or [duration*f for f in (.05,.25,.5,.75,.95)]
    hashes=[]
    for t in times:
        raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-ss',str(t),'-threads','1','-i',str(path),
            '-frames:v','1','-vf','scale=9:8,format=gray','-f','rawvideo','pipe:1'],timeout=15)
        if len(raw)!=72: continue
        gray=np.frombuffer(raw,dtype=np.uint8).reshape(8,9)
        bits=(gray[:,1:]>gray[:,:-1]).reshape(-1)
        hashes.append(f'{sum(int(v)<<i for i,v in enumerate(bits)):016x}')
    return hashes


def similarity(a,b,max_hamming=6):
    if not a or not b: return False
    close=sum(any((int(x,16)^int(y,16)).bit_count()<=max_hamming for y in b) for x in a)
    return close>=min(3,len(a))


def historical_index():
    paths=set()
    reg=read(E2/'data/exclusion_registry.json')
    # Use all historical evaluation clips + one raw source per known scene.
    # Full raw identity/hash/path registry remains in the E2 gate.
    seen_scenes=set()
    for s in read(PROJECT/'benchmark_triage_v1/manifests/source_manifest.json')['sources']:
        p=PROJECT/s['local_read_path']
        if p.is_file() and s['scene_group_id'] not in seen_scenes:
            paths.add(p); seen_scenes.add(s['scene_group_id'])
    for folder in ['benchmark_v1/media','benchmark_triage_v1/media','data/mock_cctv/media']:
        paths.update((PROJECT/folder).glob('*.mp4'))
    # Prior team frame hashes: detect same decoded RGB frames under renamed/reencoded inputs.
    frame_hashes=set()
    team=PROJECT.parent/'477_team_benchmark_v1/data/frames'
    team_records=[]
    for p in team.glob('*/manifest.json'):
        def visit(x):
            if isinstance(x,dict):
                if isinstance(x.get('sha256'),str): frame_hashes.add(x['sha256'])
                for v in x.values(): visit(v)
            elif isinstance(x,list):
                for v in x: visit(v)
        visit(read(p))
        import cv2
        manifest=read(p); groups={}
        for frame in manifest.get('frames',[]): groups.setdefault(frame['source_id'],[]).append(frame)
        for sid,frames in groups.items():
            ph=[]
            for j in sorted({0,len(frames)//2,len(frames)-1}):
                path=PROJECT.parent/'477_team_benchmark_v1'/frames[j]['image_path']
                if not path.exists(): continue
                gray=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE)
                if gray is None: continue
                gray=cv2.resize(gray,(9,8)); bits=(gray[:,1:]>gray[:,:-1]).reshape(-1)
                ph.append(f'{sum(int(v)<<i for i,v in enumerate(bits)):016x}')
            team_records.append({'path':f'TEAM:{manifest["item_id"]}:{sid}','dhash':ph})
    records=[]
    out={'records':records,'team_file_sha256':sorted(frame_hashes),'complete':False,
        'scope':'All historical benchmark MP4s + mock media + one available raw source per registered scene + available team PNG samples; not exhaustive raw-video comparison.',
        'note':'5-sample dHash conservative review flag, not identity proof; crops/mirrors/partial overlaps may evade it. Team original group mapping requires Human confirmation.'}
    for p in sorted(paths):
        try:
            d=probe(p)['duration_sec']; records.append({'path':str(p),'dhash':fingerprint(p,[d*.1,d*.5,d*.9])})
        except Exception as e: records.append({'path':str(p),'error':type(e).__name__})
        write(ROOT/'data/historical_fingerprints.json',out)
        print('history fingerprint',len(records),'/',len(paths),flush=True)
    out['complete']=True
    records.extend(team_records)
    write(ROOT/'data/historical_fingerprints.json',out); return out


def source_screen(source,index=None):
    reg=read(E2/'data/exclusion_registry.json'); issues=[]
    p=Path(source['source_video_path'])
    if not p.is_file(): return ['SOURCE_MISSING']
    actual=sha(p)
    if actual!=source['source_video_sha256']: issues.append('SOURCE_HASH_MISMATCH')
    if actual in reg['media_sha256'] or str(p.resolve()) in reg['known_source_paths']: issues.append('FROZEN_SOURCE_OVERLAP')
    for k,rk in [('source_id','source_ids'),('scene_group_id','scene_group_ids'),('physical_group_id','physical_group_ids')]:
        if source[k] in reg[rk]: issues.append('PREVIOUS_'+k.upper())
    if index:
        if index.get('complete') is False: issues.append('HISTORICAL_SCREEN_INCOMPLETE')
        fp=source.get('dhash') or fingerprint(p)
        for x in index['records']:
            if similarity(fp,x.get('dhash',[])): issues.append('NEAR_DUPLICATE_OR_PREVIOUS_SCENE:'+x['path'])
    return sorted(set(issues))


def validate_candidate(c,source):
    errors=[]
    if c['source_id']!=source['source_id'] or c['source_video_sha256']!=source['source_video_sha256']: errors.append('SOURCE_MAPPING')
    for key in ('scene_group_id','physical_group_id','camera_id'):
        if key in source and c.get(key)!=source[key]: errors.append('SOURCE_GROUP_MAPPING')
    for k in ('source_video_path','clip_path'):
        p=Path(c[k]); key=k.replace('_path','_sha256')
        if not p.is_file() or sha(p)!=c[key]: errors.append(k.upper()+'_HASH')
    try:
        d=probe(c['source_video_path'])['duration_sec']; a,b=c['clip_start_sec'],c['clip_end_sec']
        if any(isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) for x in (a,b)) or not 0<=a<b<=d+.05:
            errors.append('TIMESTAMP_RANGE')
        if abs(probe(c['clip_path'])['duration_sec']-(b-a))>.15: errors.append('CLIP_DURATION_MAPPING')
    except Exception: errors.append('VIDEO_PROBE_FAILED')
    if c.get('canonical_cv_state_path'):
        p=Path(c['canonical_cv_state_path'])
        if not p.is_file() or sha(p)!=c.get('canonical_cv_state_sha256'): errors.append('CANONICAL_HASH')
        else:
            state=read(p)
            from jsonschema import Draft202012Validator
            try: Draft202012Validator(read(PROJECT/'experiments/p0_cv_only/schemas/canonical_cv_state.schema.json')).validate(state)
            except Exception: errors.append('CANONICAL_SCHEMA')
            if state['input']['benchmark_input_fingerprint'].get('candidate_clip_sha256')!=c['clip_sha256']: errors.append('CANONICAL_CLIP_LINK')
            fp=state['input']['benchmark_input_fingerprint']
            if fp.get('original_source_sha256')!=c['source_video_sha256'] or fp.get('source_window_sec')!=[c['clip_start_sec'],c['clip_end_sec']]: errors.append('CANONICAL_SOURCE_WINDOW_LINK')
            if c.get('cv_clip_sha256')!=c['clip_sha256'] or c.get('cv_frame_fingerprint_sha256')!=state['cameras'][0]['frame_fingerprint_sha256']:
                errors.append('CV_PROVENANCE_LINK')
    else: errors.append('CV_NOT_READY')
    return errors
