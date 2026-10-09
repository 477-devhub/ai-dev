"""Create lightweight local video-wall assets while preserving source media."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--frontend-root',type=Path)
    parser.add_argument('--refresh-camera',choices=[f'CAM_{i:02d}' for i in range(1,10)],help='Regenerate a changed camera without reencoding other videos')
    args=parser.parse_args()
    manifest=json.loads((ROOT/'mock_cctv/manifest.json').read_text(encoding='utf-8'))
    output=ROOT/'data/mock_cctv/playback'
    output.mkdir(parents=True,exist_ok=True)
    for c in manifest['cameras']:
        target=output/f'{c["camera_id"]}.mp4'
        if not target.exists() or args.refresh_camera==c['camera_id']:
            if c['reused_from']:
                shutil.copyfile(output/f'{c["reused_from"]}.mp4',target)
            else:
                subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-threads','2','-i',str(ROOT/c['video_path']),'-map','0:v:0','-vf','scale=640:360','-c:v','libx264','-preset','veryfast','-crf','23','-threads','2','-fps_mode','passthrough','-an','-movflags','+faststart',str(target)],check=True)
        info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=width,height','-of','json',str(target)]))
        if abs(float(info['format']['duration'])-c['duration_sec'])>.05 or (info['streams'][0]['width'],info['streams'][0]['height'])!=(640,360):
            raise ValueError(f'Invalid playback derivative: {target}')
        if args.frontend_root:
            destination=args.frontend_root/'public/mock-cctv-media'/target.name
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(target,destination)
    print('PASS: 9 lightweight playback assets, source durations retained')


if __name__=='__main__':main()
