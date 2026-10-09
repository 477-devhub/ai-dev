from build_multiview_inventory import *
import cv2,numpy as np,zlib
from PIL import Image,ImageFont,ImageDraw
FONT=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16) if sys.platform=='win32' else ImageFont.load_default()
def probe(path):
 cap=cv2.VideoCapture(str(path));fps=cap.get(cv2.CAP_PROP_FPS);n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));d={'fps':fps,'frames':n,'duration':n/fps,'width':int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),'height':int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))};cap.release();return d
def frame(v,t):
 cap=cv2.VideoCapture(v['local_video_path']);t=max(0,min(t,v['duration']-1/v['fps']));cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=cap.read();idx=int(cap.get(cv2.CAP_PROP_POS_FRAMES))-1;cap.release()
 if not ok:raise RuntimeError('Decode failure')
 actual=idx/v['fps'];phase='BEFORE' if actual<v['event_start'] else 'AFTER' if actual>v['event_end'] else 'EVENT'
 return Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)),{'time_seconds':actual,'frame_zero_based':idx,'phase':phase}
def cell(im,rec,cam,w):
 h=round(w*9/16);tile=Image.new('RGB',(w,h+42),'#162130');tile.paste(im.resize((w,h)),(0,0));d=ImageDraw.Draw(tile);d.text((5,h+2),f'{cam} {rec["time_seconds"]:05.2f}s | f{rec["frame_zero_based"]}',font=FONT,fill='white');d.text((5,h+21),rec['phase'],font=FONT,fill='#8dcfff');return tile
def main():
 pairs=read('annotation_shortlist_private.json');tmp=ROOT/'tmp';tmp.mkdir(exist_ok=True);(ROOT/'contact_sheets').mkdir(exist_ok=True)
 needed=sum(v['file_size'] for p in pairs for v in p['cameras'].values() if not (tmp/v['zip_member']).exists());free=shutil.disk_usage(ROOT).free
 dump('capacity_check.json',{'free_bytes_before':free,'planned_extraction_bytes':needed,'method':'shutil.disk_usage, Windows equivalent of df -h /mnt/d/projects/477','only_annotation_shortlisted_members':True})
 if free<needed+1024**3:raise RuntimeError('Insufficient storage')
 zpath=next((DATA/'downloads/multiview_fight').rglob('VS*.zip'));extracted=[]
 with zipfile.ZipFile(zpath) as z:
  for p in pairs:
   cache={}
   for c in ['c1','c2']:
    v=p['cameras'][c];target=(tmp/v['zip_member']).resolve()
    if not target.is_relative_to(tmp.resolve()):raise RuntimeError('Unsafe ZIP path')
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
     with z.open(v['zip_member']) as src,target.open('xb') as dst:shutil.copyfileobj(src,dst,1024*1024)
    if target.stat().st_size!=v['file_size']:raise RuntimeError('Incomplete extraction')
    v['local_video_path']=str(target);v.update(probe(target));fr=v['source_evidence_frame_range'];v['event_start']=fr[0]/v['fps'];v['event_end']=fr[1]/v['fps'];v['event_duration_estimate']=(fr[1]-fr[0])/v['fps']
    v['suggested_clip_start']=max(0,v['event_start']-7);v['suggested_clip_end']=min(v['duration'],v['event_end']+7);v['clip_limitation']='source ends near evidence range end; requested post-event context may be absent'
    a,b=v['event_start'],v['event_end'];times=sorted([max(0,a-5),max(0,a-1),a]+[a+(b-a)*f for f in [.15,.35,.55,.75]]+[b,min(v['duration']-1/v['fps'],b+5)])
    ims=[];recs=[]
    for t in times:
     im,rec=frame(v,t);ims.append(im);recs.append(rec)
    cache[c]=(ims,recs);w=480;h=312;sheet=Image.new('RGB',(3*w,3*h+45),'#162130');d=ImageDraw.Draw(sheet);d.text((8,8),f'{p["pair_id"]} {c} | PRIVATE REVIEW; evidence-based sampling',font=FONT,fill='white')
    for i,(im,rec) in enumerate(zip(ims,recs)):sheet.paste(cell(im,rec,c,w),(i%3*w,i//3*h+45))
    path=ROOT/'contact_sheets'/f'{p["pair_id"]}_cam_{"a" if c=="c1" else "b"}.jpg';sheet.save(path,quality=90);v['contact_sheet_path']=str(path);v['contact_frames']=recs
    # Dense full-clip sequence for temporal visual review, 1Hz, memory only.
    times=list(range(int(v['duration'])+1));w=320;ch=222;cols=6;sheet=Image.new('RGB',(cols*w,((len(times)+cols-1)//cols)*ch+45),'#162130');d=ImageDraw.Draw(sheet);d.text((8,8),f'{p["pair_id"]} {c} | Full duration 1Hz review (not model input)',font=FONT,fill='white');dense=[]
    for i,t in enumerate(times):
     im,rec=frame(v,t);dense.append(rec);sheet.paste(cell(im,rec,c,w),(i%cols*w,i//cols*ch+45))
    path=ROOT/'contact_sheets'/f'{p["pair_id"]}_cam_{"a" if c=="c1" else "b"}_temporal.jpg';sheet.save(path,quality=90);v['temporal_sheet_path']=str(path);v['temporal_frames']=dense
    extracted.append({'path':str(target),'size':target.stat().st_size,'source_member':v['zip_member'],'crc':v['zip_crc']})
   # Columns share relative phase within each evidence interval, never claimed to be synchronized timestamps.
   w=320;ch=222;pair=Image.new('RGB',(9*w,2*ch+70),'#162130');d=ImageDraw.Draw(pair);d.text((8,5),f'{p["pair_id"]} | EVENT-PHASE ALIGNMENT ONLY; independent timestamps; no verified synchronization',font=FONT,fill='white');d.text((8,28),'before / just before / support start / 15% / 35% / 55% / 75% / support end / after-or-last-frame',font=FONT,fill='white')
   for row,c in enumerate(['c1','c2']):
    for i,(im,rec) in enumerate(zip(*cache[c])):pair.paste(cell(im,rec,c,w),(i*w,row*ch+70))
   path=ROOT/'contact_sheets'/f'{p["pair_id"]}_pair.jpg';pair.save(path,quality=90);p['pair_contact_sheet_path']=str(path)
   p['evidence_onset_offset_b_minus_a']=p['cameras']['c2']['event_start']-p['cameras']['c1']['event_start'];p['estimated_time_offset']=p['evidence_onset_offset_b_minus_a'];p['estimated_time_offset_basis']='difference of prose evidence tracking-start frames / actual FPS; event-phase estimate, NOT sync'
   p['sync_disagreement_seconds']=p['evidence_onset_offset_b_minus_a']-p['timestamp_derived_offset_b_minus_a'];print(p['pair_id'],'review sheets ready',flush=True)
 dump('reviewed_pairs_private.json',pairs);dump('temporary_files.json',extracted)
if __name__=='__main__':main()
