"""Prepare analysis assets within the existing backend's 64 MiB limit."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent


def inspect(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height','-of','json',str(path)]))


def main():
    manifest=json.loads((HERE/'manifest.json').read_text(encoding='utf-8'))
    mapping={}
    records=[]
    for c in manifest['cameras']:
        source=ROOT/c['video_path']
        canonical=c['reused_from'] or c['camera_id']
        target=ROOT/'data/mock_cctv/analysis'/f'{canonical}.mp4'
        if source.stat().st_size>64*1024*1024:
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():
                subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(source),'-map','0:v:0','-c:v','libx264','-preset','fast','-crf','23','-fps_mode','passthrough','-an','-movflags','+faststart',str(target)],check=True)
            mode='h264_crf23_no_audio'
        else:
            target=source
            mode='original'
        if not 0<target.stat().st_size<=64*1024*1024:raise ValueError(f'Analysis asset exceeds limit: {target}')
        metadata=inspect(target)
        if abs(float(metadata['format']['duration'])-c['duration_sec'])>.05:raise ValueError('Duration changed')
        video=next(s for s in metadata['streams'] if s['codec_type']=='video')
        if (video['width'],video['height'])!=(c['width'],c['height']):raise ValueError('Resolution changed')
        with target.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        mapping[c['clip_ref']]=target.relative_to(ROOT/'data/mock_cctv').as_posix()
        records.append({'camera_id':c['camera_id'],'source_sha256':c['sha256'],'analysis_sha256':digest,'analysis_path':target.relative_to(ROOT).as_posix(),'preparation':mode,'bytes':target.stat().st_size,'duration_sec':float(metadata['format']['duration'])})
    (HERE/'analysis-asset-map.json').write_text(json.dumps(mapping,indent=2)+'\n',encoding='utf-8')
    (HERE/'analysis-assets.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    print('PASS: 9 registered analysis assets under 64 MiB, source durations and 1080p retained')


if __name__=='__main__':main()
