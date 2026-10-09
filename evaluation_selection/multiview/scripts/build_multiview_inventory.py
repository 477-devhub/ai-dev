import csv,json,zipfile,hashlib,re,shutil,sys
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT.parent.parent
sys.stdout.reconfigure(encoding='utf-8')
def dump(name,obj): (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def writecsv(name,rows):
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with (ROOT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows])
def filehash(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def main():
 base=DATA/'downloads/multiview_fight';zp=next(base.rglob('VS*.zip'));ap=next(base.rglob('VL*.zip'));pairs=[];snap={};issues=[]
 for p in [zp,ap]:
  with zipfile.ZipFile(p) as z:snap[str(p)]={'size':p.stat().st_size,'sha256':filehash(p),'members':[{'name':i.filename,'size':i.file_size,'compressed_size':i.compress_size,'crc':i.CRC} for i in z.infolist() if not i.is_dir()]}
 with zipfile.ZipFile(zp) as vs,zipfile.ZipFile(ap) as vl:
  videos=[i for i in vs.infolist() if not i.is_dir()];names={i.filename:i for i in videos};annotations=[i for i in vl.infolist() if i.filename.endswith('.json')]
  for n,info in enumerate(sorted(annotations,key=lambda i:i.filename),1):
   raw=vl.read(info.filename);a=json.loads(raw);views={v['view']:v for v in a['videos']};linked={};valid=set(views)=={'c1','c2'} and len(a['videos'])==2
   for cam in ['c1','c2']:
    v=views[cam];matches=[m for m in names if Path(m).name==v['filename']]
    if len(matches)!=1:valid=False;issues.append(info.filename+' '+cam+': unresolved or ambiguous video');continue
    m=matches[0];ev=a['annotations']['evidence'][cam];match=re.search(r'프레임 범위\s*(\d+)\s*[~～-]\s*(\d+)',ev['evidence_text']);fr=list(map(int,match.groups())) if match else None
    ids=sorted({t.strip() for token in ev['obj_id'] for t in token.split(',')});linked[cam]={'source_video':str(zp)+'::'+m,'zip_member':m,'file_size':names[m].file_size,'zip_crc':names[m].CRC,'source_annotation':str(ap)+'::'+info.filename,'metadata':v,'source_evidence_frame_range':fr,'evidence_keyframes':ev['frame_id'],'source_object_ids':ids,'number_of_annotated_people':len(ids),'camera_description_private':a['annotations']['caption'][cam]['cot'],'fps':None,'event_start':None,'event_end':None,'event_interval_basis':'evidence_text tracking range; not an explicit numeric event interval','local_video_path':None}
    if fr and any(f<fr[0] or f>fr[1] for f in ev['frame_id']):issues.append(info.filename+' '+cam+': evidence keyframe outside prose tracking range')
   va,vb=views['c1'],views['c2'];dt=lambda v:datetime.fromisoformat(v['date']+'T'+v['time']);timestamp_guess=(dt(va)-dt(vb)).total_seconds()
   p={'pair_id':f'MV{n:02d}','incident_id':Path(info.filename).stem,'incident_id_basis':'annotation filename stem, not an explicit official ID field','pairing_rule':'one source JSON videos array explicitly lists c1/c2; each filename resolves uniquely to source ZIP member','same_incident_association':'source_JSON_co_listing; visual confirmation pending','valid_pair':valid,'event_type':a['annotations']['event_class'],'source_annotation':str(ap)+'::'+info.filename,'annotation_member':info.filename,'annotation_sha256':hashlib.sha256(raw).hexdigest(),'cameras':linked,'timestamp_derived_offset_b_minus_a':timestamp_guess,'timestamp_offset_limit':'coarse date/time fields, no frame-level synchronization semantics supplied','estimated_time_offset':None,'offset_convention':'corresponding B media time minus A media time, t_B=t_A+offset','sync_status':'no_explicit_sync_metadata','ground_truth_private':a}
   pairs.append(p)
 dump('source_zip_snapshot.json',snap);dump('multiview_inventory.json',pairs);dump('structure_issues.json',issues)
 flat=[]
 for p in pairs:
  r={k:p[k] for k in ['pair_id','incident_id','incident_id_basis','event_type','valid_pair','same_incident_association','pairing_rule','estimated_time_offset','timestamp_derived_offset_b_minus_a','sync_status']}
  for cam,name in [('c1','a'),('c2','b')]:
   v=p['cameras'][cam];r.update({f'cam_{name}_video':v['source_video'],f'cam_{name}_annotation':v['source_annotation'],f'cam_{name}_id':cam,f'cam_{name}_duration_annotation':v['metadata']['length'],f'cam_{name}_evidence_frame_range':v['source_evidence_frame_range'],f'cam_{name}_number_of_people_annotation':v['number_of_annotated_people']})
  flat.append(r)
 writecsv('multiview_inventory.csv',flat)
 lines=['# Multi-view dataset structure','',f'- Dataset key (user supplied): 71953. Local source ZIP: `{zp}`.',f'- Label ZIP: `{ap}`.',f'- Source MP4: {len(videos)}; JSON: {len(annotations)}; valid linked pairs: {sum(p["valid_pair"] for p in pairs)}. Two cameras per source JSON.','- ZIP layout: ph_eNNNN/ph_eNNNN_c1.mp4 and _c2.mp4; labels ph_eNNNN/ph_eNNNN.json.','- Pair association comes from the JSON videos array, not a filename-only inference. No explicit pair_id/incident_id field. MV IDs are local review IDs. Annotation stems are source locators.','- Event class: 신체적 충돌을 동반한 싸움. JSON videos has filename, dimensions (1920x1080), date/time, length, distribution, camera hardware model, angle, source and view. Camera hardware identifiers are not unique incident IDs. Source codes or/re are retained without guessing their meaning.','- Camera-specific caption.caption_text and caption.cot stage descriptions; common question and answer; camera-specific evidence_text, frame_id, obj_id, obj_bbox, obj_label. A question/answer pair exists, not a separate VQA list.','- FPS absent from source JSON. Numeric event_start/end absent; prose evidence frame range describes tracking consistency. Derived seconds require actual decoder FPS and remain event-support sampling estimates, not corrected official event times.','- obj_id strings jointly list people 1,2. Three sparse boxes per view correspond to evidence points; no continuous per-person bbox tracks supplied. Bounding-box axis convention is not explicitly defined. No independent keyframe images inside ZIP.','- No explicit sync offset/frame mapping. Coarse recording time differs by 1–3 sec; not a synchronization guarantee. Event onset difference will be stored separately from any visual correspondence estimate.','- All five local pairs are the shortlist: requested 15–20 cannot be produced from five incidents. No old candidates rerun or modified.','- Caption, CoT, answer, event class, evidence frame/object descriptions and annotation-selected sampling are private review data. Model loader must use only sanitized video/image media and a fixed generic prompt.','', '## Initial structure inconsistencies',*['- '+s for s in issues],'','Existing candidate_report.md, candidates.csv, candidates.json, dataset_structure.md read before this work; SHA256 snapshot stored separately for preservation verification.']
 (ROOT/'dataset_structure.md').write_text('\n'.join(lines),encoding='utf-8')
 old=ROOT.parent;dump('existing_result_snapshot.json',{n:hashlib.sha256((old/n).read_bytes()).hexdigest() for n in ['candidate_report.md','candidates.csv','candidates.json','dataset_structure.md']})
 print('Structure:',len(videos),'MP4;',len(annotations),'JSON;',len(pairs),'paired incidents')
if __name__=='__main__':main()
