from benchmark_common import *
import os,shutil,concurrent.futures

def main():
 if (ROOT/'BENCHMARK_LOCK.json').exists():raise RuntimeError('Frozen v1 cannot be rebuilt; validate it or explicitly create v2')
 plan=read(ROOT/'private_ground_truth/build_plan.json');free=shutil.disk_usage(ROOT).free
 if free<2*1024**3:raise RuntimeError('Need at least 2 GiB headroom')
 statefile=ROOT/'private_ground_truth/media_build_records.json';state=read(statefile) if statefile.exists() else {}
 def encode(recipe):
  name=recipe['name'];target=ROOT/'media'/name;source=Path(recipe['source_video']);input_sha=sha(source);meta=probe(source)
  recipe_hash=hashlib.sha256(json.dumps({'recipe':recipe,'encoding':plan['encoding'],'source_sha':input_sha},sort_keys=True).encode()).hexdigest()
  if target.exists():
   rec=state.get(name)
   if not rec or rec['recipe_sha256']!=recipe_hash or sha(target)!=rec['sha256']:raise RuntimeError('Unverified pre-existing output '+name)
   return name,rec
  partial=ROOT/'media'/(name+'.partial.mp4');cmd=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-ss',str(recipe['start_sec']),'-i',str(source),'-map','0:v:0']
  if recipe['end_sec'] is not None:cmd+=['-t',str(recipe['end_sec']-recipe['start_sec']),'-frames:v',str(round((recipe['end_sec']-recipe['start_sec'])*30))]
  cmd+=['-vf','scale=1920:1080:flags=lanczos,fps=30:start_time=0,setsar=1','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p','-threads','4','-filter_threads','1','-an','-map_metadata','-1','-map_chapters','-1','-movflags','+faststart',str(partial)]
  subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE);out=probe(partial);expected=recipe['end_sec']-recipe['start_sec'] if recipe['end_sec'] is not None else meta['duration']
  if abs(out['duration']-expected)>.04:raise RuntimeError('Duration mismatch '+name)
  partial.replace(target)
  return name,{'sha256':sha(target),'recipe_sha256':recipe_hash,'source_sha256':input_sha,'source_metadata':meta,'output_metadata':out,'source_path':str(source),'source_clip_start_sec':recipe['start_sec'],'source_clip_end_sec':recipe['end_sec'] if recipe['end_sec'] is not None else meta['duration'],'ffmpeg_command_private':cmd,'ffmpeg_version':subprocess.check_output(['ffmpeg','-version'],encoding='utf-8').splitlines()[0]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  futures=[pool.submit(encode,x) for x in plan['recipes']]
  for fut in concurrent.futures.as_completed(futures):
   name,record=fut.result();state[name]=record;write(statefile,state);print(name+' encoded',flush=True)
 for target_name,src_name in {**plan['reuse'],**plan['opaque_aliases']}.items():
  target=ROOT/'media'/target_name;src=ROOT/'media'/src_name
  if target.exists():
   if sha(target)!=sha(src):raise RuntimeError('Reuse differs '+target_name)
  else:
   try:os.link(src,target)
   except OSError:shutil.copyfile(src,target)
  if sha(target)!=sha(src):raise RuntimeError('Reuse mismatch')
 print('Media: six encodes, two set reuse files and six opaque aliases',flush=True)
if __name__=='__main__':main()
