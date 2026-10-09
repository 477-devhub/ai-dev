import argparse, csv, json, os, shutil, zipfile, hashlib, statistics
from pathlib import Path
import xml.etree.ElementTree as ET
import cv2
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT.parent
VIDEO_EXT={'.mp4','.avi','.mov','.mkv'}
def dump(name,obj):
 (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
def csvwrite(name,rows,fields=None):
 with (ROOT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]),extrasaction='ignore');w.writeheader();w.writerows(rows)
def seconds(s):
 if not s:return None
 a=s.split(':');return sum(float(v)*60**i for i,v in enumerate(reversed(a)))
def tree(e):
 if not list(e):return e.text
 d={}
 for c in e:
  v=tree(c)
  if c.tag in d:
   if not isinstance(d[c.tag],list):d[c.tag]=[d[c.tag]]
   d[c.tag].append(v)
  else:d[c.tag]=v
 return d
def parse(raw):
 x=ET.fromstring(raw);fps=float(x.findtext('header/fps'));start=seconds(x.findtext('event/starttime'));ed=seconds(x.findtext('event/duration'))
 objects=[]
 for o in x.findall('object'):
  objects.append({'name':o.findtext('objectname'),'positions':[tree(p) for p in o.findall('position')],'actions':[{'name':a.findtext('actionname'),'frames':[{'start':int(f.findtext('start')),'end':int(f.findtext('end'))} for f in a.findall('frame')]} for a in o.findall('action')]})
 return {'filename':x.findtext('filename'),'event_type':x.findtext('event/eventname'),'duration':seconds(x.findtext('header/duration')),'fps':fps,'width':int(x.findtext('size/width')),'height':int(x.findtext('size/height')),'frames':int(x.findtext('header/frames')),'event_start':start,'event_end':round(start+ed,4),'event_duration':ed,'population_annotation':x.findtext('header/population'),'actions':sorted({a['name'] for o in objects for a in o['actions']}),'objects':objects,'source_ground_truth':tree(x),'annotation_sha256':hashlib.sha256(raw).hexdigest(),'has_bbox':any('bbox' in e.tag.lower() or 'bndbox' in e.tag.lower() for e in x.iter())}
def probe(p):
 cap=cv2.VideoCapture(str(p));ok=cap.isOpened()
 d={'video_probe_status':'opencv_verified' if ok else 'open_failed','video_duration':None,'video_fps':None,'video_width':None,'video_height':None,'video_frames':None}
 if ok:
  fps=cap.get(cv2.CAP_PROP_FPS);n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));d.update(video_duration=n/fps if fps else None,video_fps=fps,video_width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),video_height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),video_frames=n)
 cap.release();return d
def inventory():
 ROOT.mkdir(exist_ok=True);rows=[];snap=[];zpath=next((DATA/'downloads/fight').rglob('insidedoor_04.zip'))
 with zipfile.ZipFile(zpath) as z:
  names={i.filename:i for i in z.infolist() if not i.is_dir()}
  for name,i in sorted(names.items()):
   snap.append({'member':name,'size':i.file_size,'compressed_size':i.compress_size,'crc':i.CRC})
   if Path(name).suffix.lower() not in VIDEO_EXT:continue
   ann=str(Path(name).with_suffix('.xml')).replace('\\','/');a=parse(z.read(ann)) if ann in names else {}
   rows.append({**a,'video_path':str(zpath)+'::'+name,'annotation_path':str(zpath)+'::'+ann,'zip_path':str(zpath),'zip_member':name,'local_video_path':None,'file_size':i.file_size,'metadata_source':'AI_Hub_XML','video_probe_status':'not_extracted','video_duration':None,'video_fps':None,'video_width':None,'video_height':None,'video_frames':None})
 for event in ['swoon','trespass']:
  base=next(p for p in (DATA/'data/recovered').rglob('extracted') if event in str(p))
  for p in sorted(base.rglob('*')):
   if p.suffix.lower() not in VIDEO_EXT:continue
   ann=p.with_suffix('.xml');a=parse(ann.read_bytes()) if ann.exists() else {}
   rows.append({**a,'video_path':str(p.resolve()),'annotation_path':str(ann.resolve()),'zip_path':None,'zip_member':None,'local_video_path':str(p.resolve()),'file_size':p.stat().st_size,'metadata_source':'AI_Hub_XML_with_video_crosscheck',**probe(p)})
 dump('inventory_details.json',rows);dump('zip_listing.json',snap)
 flat=[]
 for r in rows:
  q={k:v for k,v in r.items() if k not in ['objects','source_ground_truth']};q['actions']='|'.join(r['actions']);flat.append(q)
 csvwrite('dataset_inventory.csv',flat)
 lines=['# Dataset structure','', 'Windows native execution. Requested /mnt/d/projects/477 maps to D:/projects/477.','', 'MP4 + same-directory, identical-stem XML. ZIP members use archive absolute path::member syntax; this is a locator, not an extracted file. No original renamed or changed.','', 'XML: annotation/folder, filename, source, size, header, event, repeated object. Event interval = event/starttime + event/duration, seconds. Object/action/frame has inclusive-looking start/end indices; source frame indexing is not explicitly documented, so no zero/one-based assumption is asserted. Contact sheet indices are decoder zero-based indices.','', 'Objects contain person keypoints at keyframes and action intervals. Keypoints are not bounding boxes. Population is an annotation value, not a measured visible-person count. No severity/risk/priority/confidence ground truth exists in these fields.','', 'All XML parsed directly; source XML tree and SHA256 retained in inventory_details.json. ZIP not extracted for inventory. OpenCV is used because ffprobe/ffmpeg are absent from PATH. Fight metadata is annotation-only until candidate extraction.','']
 for e in ['fight','swoon','trespass']:
  rs=[r for r in rows if r['event_type']==e];lines += [f'## {e}',f'- Videos: {len(rs)}; paired XML: {len(rs)}; MP4.',f'- Mean XML duration: {statistics.mean(r["duration"] for r in rs):.3f} sec.',f'- FPS: {sorted(set(r["fps"] for r in rs))}; resolution: {sorted(set((r["width"],r["height"]) for r in rs))}.',f'- Total video bytes: {sum(r["file_size"] for r in rs)}.',f'- Action labels: {sorted(set(a for r in rs for a in r["actions"]))}.',f'- Bbox present: {sum(r["has_bbox"] for r in rs)}; objects, keyframes and action frame intervals present.',f'- Event duration range: {min(r["event_duration"] for r in rs):.1f}–{max(r["event_duration"] for r in rs):.1f} sec.','']
 issues=[]
 for r in rows:
  if r['event_end']>r['duration']+.2:issues.append(r['filename']+': event past video end')
  if r['video_duration'] and abs(r['video_duration']-r['duration'])>.2:issues.append(r['filename']+f': XML/video duration difference {r["video_duration"]-r["duration"]:.3f}s')
  for o in r['objects']:
   for a in o['actions']:
    for f in a['frames']:
     if f['end']<f['start'] or f['end']>r['frames']+1:issues.append(r['filename']+': invalid/out-of-range action frame')
 lines+=['## Audit findings',*['- '+s for s in issues],'- Multiple camera/season versions share source IDs: candidates are not independent events. Keep related IDs together in any future split.','- Trespass annotations describe climbwall or pulling/walking; restricted-area geometry and legal access rights are not supplied.','- 145-5 cam02 spring trespass event is unusually long (208.9s); do not silently repair it.']
 (ROOT/'dataset_structure.md').write_text('\n'.join(lines),encoding='utf-8');dump('data_issues.json',issues)
 print('Inventory:',{e:sum(r['event_type']==e for r in rows) for e in ['fight','swoon','trespass']},'issues',len(issues))
if __name__=='__main__':inventory()
