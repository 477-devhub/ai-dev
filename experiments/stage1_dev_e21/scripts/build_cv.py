"""Reuse unchanged P0 StateBuilder camera extraction on E2.1 uniform64 clips."""
import argparse,hashlib,math,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from dev_common import ROOT,P0,read,write,sha
sys.path.insert(0,str(P0/'src'))
from state_builder import StateBuilder
from pose_detector import PoseDetector
from utils import load_yaml,CV_CONFIG_PATH
import cv2
from jsonschema import Draft202012Validator


def main():
    p=argparse.ArgumentParser(); p.add_argument('--limit',type=int,default=100); args=p.parse_args()
    pool=read(ROOT/'data/pool.json'); cfg=load_yaml(CV_CONFIG_PATH)
    detector=None; builder=None; done=0
    validator=Draft202012Validator(read(P0/'schemas/canonical_cv_state.schema.json'))
    for c in pool['candidates']:
        if done>=args.limit: break
        if c['cv_status']=='READY' and Path(c['canonical_cv_state_path']).is_file() and sha(c['canonical_cv_state_path'])==c['canonical_cv_state_sha256']: continue
        start=time.perf_counter()
        try:
            if sha(c['clip_path'])!=c['clip_sha256']: raise ValueError('clip altered')
            if detector is None: detector=PoseDetector(cfg); builder=StateBuilder(cfg,detector)
            cap=cv2.VideoCapture(c['clip_path']); count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps=cap.get(cv2.CAP_PROP_FPS)
            schedule=[math.floor(j*(count-1)/63+.5) for j in range(64)]
            if count<64 or fps<=0: raise ValueError('clip cannot provide 64 distinct uniform samples')
            frames=[]; h=hashlib.sha256()
            for j,fi in enumerate(schedule):
                cap.set(cv2.CAP_PROP_POS_FRAMES,fi); ok,bgr=cap.read()
                if not ok: raise ValueError('sample decode failed')
                rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB); h.update(rgb.tobytes()); frames.append((j,fi/fps,rgb))
            cap.release()
            timings={'cv_inference_ms':0.,'tracking_ms':0.,'feature_extraction_ms':0.}
            cam=builder._camera_state('CAM_01',frames,schedule,timings,None)
            fp=h.hexdigest(); cam['frame_fingerprint_sha256']=fp
            # Generic metadata uses valid cv-state-v1 item pattern; Candidate ID remains separate.
            state={'state_version':'cv-state-v1','generator':builder.generator_info(),
                'input':{'item_id':'ITEM_01','task':'single','frame_protocol':'uniform_total64_v1',
                    'input_fingerprint':fp,'benchmark_input_fingerprint':{'dataset':'e21-new-development',
                        'candidate_clip_sha256':c['clip_sha256'],'original_source_sha256':c['source_video_sha256'],
                        'source_window_sec':[c['clip_start_sec'],c['clip_end_sec']],
                        'sampling_protocol_id':'uniform_total64_v1','frame_numbers':schedule},
                    'total_frames':64,'camera_ids':['CAM_01'],'frames_per_camera':{'CAM_01':64},
                    'time_reference':'clip-relative seconds; no cross-camera synchronization'},'cameras':[cam],'cross_camera':None}
            validator.validate(state)
            dest=ROOT/'data/canonical'/f"{c['candidate_id']}.json"; write(dest,state)
            c.update(canonical_cv_state_path=str(dest.resolve()),canonical_cv_state_sha256=sha(dest),cv_status='READY',cv_error=None,
                cv_timing_ms=timings,cv_config_sha256=builder.cv_config_sha256,cv_code_sha256=builder.code_sha256,
                cv_clip_sha256=c['clip_sha256'],cv_frame_fingerprint_sha256=fp,cv_sample_count=64)
        except Exception as e: c.update(cv_status='FAILED',cv_error=f'{type(e).__name__}: {str(e)[:300]}')
        c['cv_wall_ms']=round((time.perf_counter()-start)*1000,2); done+=1
        write(ROOT/'data/pool.json',pool); print(c['candidate_id'],c['cv_status'],c.get('cv_error'),flush=True)
    print('processed',done)


if __name__=='__main__': main()
