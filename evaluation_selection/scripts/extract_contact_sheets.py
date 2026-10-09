from build_inventory import *
from PIL import Image,ImageDraw,ImageFont
import math
FONT=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',17) if os.name=='nt' else ImageFont.load_default()
def stamp(t):return f'{int(t)//60:02d}:{t%60:04.1f}'
def intervals(r,name=None):
 return sorted([(f['start']/r['fps'],f['end']/r['fps'],a['name']) for o in r['objects'] for a in o['actions'] for f in a['frames'] if name is None or a['name']==name])
def sheet(r,times,path,cols=3,w=480):
 times=sorted(times)
 cap=cv2.VideoCapture(r['local_video_path']);fps=cap.get(cv2.CAP_PROP_FPS);dur=cap.get(cv2.CAP_PROP_FRAME_COUNT)/fps;h=round(w*9/16);cellh=h+47
 im=Image.new('RGB',(cols*w,math.ceil(len(times)/cols)*cellh+45),'#151b25');d=ImageDraw.Draw(im);d.text((8,8),f'{r["candidate_id"]} {r["filename"]}',font=FONT,fill='white');records=[]
 for n,t in enumerate(times):
  t=max(0,min(t,dur-1/fps));cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read();idx=int(cap.get(cv2.CAP_PROP_POS_FRAMES))-1
  if not ok:raise RuntimeError(f'Decode failure {r["filename"]} {t}')
  actual=idx/fps;label='BEFORE' if actual<r['event_start'] else 'AFTER' if actual>r['event_end'] else 'EVENT'
  x=n%cols*w;y=n//cols*cellh+45
  im.paste(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).resize((w,h)),(x,y));d.text((x+7,y+h+3),f'{stamp(actual)} | frame {idx} | {label}',font=FONT,fill='white');d.text((x+7,y+h+24),f'XML {r["event_start"]:.1f}-{r["event_end"]:.1f}s',font=FONT,fill='#88ccff');records.append({'requested_seconds':t,'decoded_frame_zero_based':idx,'decoded_seconds':actual,'phase':label})
 cap.release();im.save(path,quality=88);return records
def main():
 chosen=read('review_shortlist.json');(ROOT/'contact_sheets').mkdir(exist_ok=True);tmp=ROOT/'tmp/fight';tmp.mkdir(parents=True,exist_ok=True)
 need=sum(r['file_size'] for r in chosen if r['zip_path'] and not (tmp/r['zip_member']).exists());free=shutil.disk_usage(ROOT).free
 dump('capacity_check.json',{'free_bytes_before':free,'planned_extract_bytes':need,'method':'shutil.disk_usage (Windows equivalent of df -h)','requested_linux_command':'df -h /mnt/d/projects/477'})
 if free<need+2*1024**3:raise RuntimeError('Insufficient space')
 extracted=[]
 for r in chosen:
  if r['zip_path']:
   target=(tmp/r['zip_member']).resolve()
   if not target.is_relative_to(tmp.resolve()):raise RuntimeError('Unsafe zip path')
   target.parent.mkdir(parents=True,exist_ok=True)
   with zipfile.ZipFile(r['zip_path']) as z:
    if not target.exists():
     with z.open(r['zip_member']) as src,target.open('xb') as dst:shutil.copyfileobj(src,dst,1024*1024)
    if target.stat().st_size!=r['file_size']:raise RuntimeError('Incomplete extraction')
    ann=r['zip_member'].rsplit('.',1)[0]+'.xml';ap=tmp/ann
    if not ap.exists():ap.write_bytes(z.read(ann))
   r['local_video_path']=str(target);r['local_annotation_path']=str(ap);r.update(probe(target));extracted.extend([{'path':str(target),'size':target.stat().st_size},{'path':str(ap),'size':ap.stat().st_size}])
  start,end=r['event_start'],r['event_end'];span=end-start
  times=[start-6,start-1,start,start+span*.15,start+span*.35,start+span*.55,start+span*.8,end,end+6]
  if r['event_type']=='swoon':
   falls=intervals(r,'falldown');a,b,_=falls[0];times=[start-6,start-1,start,(start+a)/2,a,(a+b)/2,b,end,end+8]
  elif r['event_type']=='fight':
   acts=intervals(r);attack=[(a+b)/2 for a,b,n in acts if n in ['punching','pushing','kicking']];times=[start-6,start-1,start]+[attack[min(len(attack)-1,int((len(attack)-1)*f))] for f in [0,.33,.66,1]]+[end,end+6]
  r['sampled_frames']=sheet(r,times,r['contact_sheet_path'])
  # A denser ordered sequence: inspect transitions, not a single image. No full-frame dumps.
  if r['event_type']=='swoon':
   falls=intervals(r,'falldown');a,b,_=falls[0];ts=[start-5,start-1]+[a-2+i*(b-a+6)/17 for i in range(18)]+[end+v for v in [1,3,6,10]]
  elif r['event_type']=='fight':
   hits=intervals(r,'punching');a,b,_=hits[0];ts=[start-5,start,start+1]+[a-2+i*(b-a+4)/14 for i in range(15)]+[start+span*v for v in [.35,.5,.65,.8,1]]+[end+5]
  else:ts=[start-5+i*(span+10)/23 for i in range(24)]
  r['temporal_sampled_frames']=sheet(r,ts,r['temporal_sheet_path'],cols=4,w=400)
  print(r['candidate_id'],'sheets ready',flush=True)
 dump('review_shortlist.json',chosen);dump('temporary_files.json',extracted)
 print('Extracted bytes:',sum(e['size'] for e in extracted))
if __name__=='__main__':main()
