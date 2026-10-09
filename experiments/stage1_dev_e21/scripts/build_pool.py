"""Deterministic non-overlapping windows; no labels or P1/P4 selection."""
import argparse,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from dev_common import ROOT,read,write,sha
from media_integrity import probe,fingerprint,source_screen,historical_index


def main():
    p=argparse.ArgumentParser(); p.add_argument('--window-sec',type=float,default=30); p.add_argument('--max-per-source',type=int,default=1)
    p.add_argument('--historical-index',action='store_true'); args=p.parse_args()
    if args.window_sec<=0 or not 1<=args.max_per_source<=3: p.error('positive window, max-per-source 1..3')
    data=read(ROOT/'data/sources.json')
    idx=historical_index() if args.historical_index else read(ROOT/'data/historical_fingerprints.json') if (ROOT/'data/historical_fingerprints.json').exists() else None
    candidates=[]
    for source in data['sources']:
        info=probe(source['source_video_path']); source['metadata']=info; source['dhash']=fingerprint(source['source_video_path'])
        source['screening_issues']=source_screen(source,idx)
        for j in range(args.max_per_source):
            start=j*args.window_sec; end=min((j+1)*args.window_sec,info['duration_sec'])
            if end-start<2: break
            cid=f"DEV_{source['source_id'].split('_')[-1]}_{j+1:02d}"; clip=ROOT/'media/clips'/f'{cid}.mp4'; clip.parent.mkdir(parents=True,exist_ok=True)
            if not clip.exists():
                subprocess.run(['ffmpeg','-nostdin','-v','error','-i',source['source_video_path'],'-ss',str(start),'-t',str(end-start),
                    '-map','0:v:0','-an','-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(clip)],check=True)
            candidates.append({'candidate_id':cid,'source_id':source['source_id'],'scene_group_id':source['scene_group_id'],
                'physical_group_id':source['physical_group_id'],'camera_id':'CAM_01','source_video_path':source['source_video_path'],
                'source_video_sha256':source['source_video_sha256'],'clip_start_sec':start,'clip_end_sec':end,
                'clip_path':str(clip.resolve()),'clip_sha256':sha(clip),'canonical_cv_state_path':None,'canonical_cv_state_sha256':None,
                'cv_status':'PENDING','cv_error':None,'sampling_config':'uniform_total64_v1 round-half-up; RGB; clip-relative timestamps',
                'cv_config_version':'cv-state-v1','review_status':'UNREVIEWED','neutral_context':source['capture_context_neutral']})
    write(ROOT/'data/sources.json',data)
    existing=read(ROOT/'data/pool.json')['candidates'] if (ROOT/'data/pool.json').exists() else []
    prior={x['candidate_id']:x for x in existing}
    for c in candidates:
        old=prior.get(c['candidate_id'])
        if old and old['clip_sha256']==c['clip_sha256']:
            for k in ('canonical_cv_state_path','canonical_cv_state_sha256','cv_status','cv_error'): c[k]=old[k]
    write(ROOT/'data/pool.json',{'schema_version':'e21-pool-v1','selection':'First chronological non-overlapping window per source; max30sec. No P1/P4 or Human/action labels used.',
        'candidates':candidates,'source_count':len(data['sources']),'gt_distribution':None})
    print('pool candidates',len(candidates),'sources',len(data['sources']))


if __name__=='__main__': main()
