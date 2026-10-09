from build_multiview_inventory import *
import cv2,zlib
from PIL import Image
PROMPT='제공된 영상에서 관찰되는 행동과 변화, 참여자 간 상호작용, 판단 근거와 불확실성을 설명하세요. 여러 영상이 있으면 시점별 관찰과 공통 사건 가능성을 비교하세요. 영상의 시작 시점이 같다고 가정하지 마세요. 보이지 않는 사실은 단정하지 마세요.'
METRICS=['cam_a_event_visibility','cam_b_event_visibility','view_difference','complementarity','occlusion_recovery','temporal_value','participant_clarity_gain','demo_suitability','single_view_ambiguity']
def boundary(v):
 cap=cv2.VideoCapture(v['local_video_path']);n=v['frames'];fps=v['fps'];black=[]
 for idx in sorted(set(list(range(min(30,n)))+list(range(max(0,n-30),n)))):
  cap.set(cv2.CAP_PROP_POS_FRAMES,idx);ok,im=cap.read()
  if not ok:raise RuntimeError('Boundary decode failed')
  if im.mean()<1 and im.max()<8:black.append(idx)
 cap.release();first=0;last=n-1
 while first in black:first+=1
 while last in black:last-=1
 return {'near_black_boundary_frames_zero_based':black,'rule':'mean < 1 and max < 8; first/last 30 frames only','first_nonblack_boundary_time':first/fps,'last_nonblack_boundary_end':(last+1)/fps}
def main():
 pairs=read('reviewed_pairs_private.json');decisions={d['pair_id']:d for d in read('review_decisions_private.json')};candidates=[];manifest=[];flat=[];inv=[]
 for p in pairs:
  d=decisions[p['pair_id']];s=d['scores'];gain=round(.35*s['complementarity']+.25*s['occlusion_recovery']+.20*s['participant_clarity_gain']+.20*s['view_difference'],2)
  p['same_incident_association']='source_JSON_co_listing; visual scenes/clothing/action progression consistent; no official per-frame cross-camera identity or sync'
  for v in p['cameras'].values():
   v['boundary_quality']=boundary(v);q=v['boundary_quality'];v['suggested_clip_start']=max(v['suggested_clip_start'],q['first_nonblack_boundary_time']);v['suggested_clip_end']=min(v['suggested_clip_end'],q['last_nonblack_boundary_end'])
  c={'pair_id':p['pair_id'],'incident_id':p['incident_id'],'event_type':p['event_type'],'cameras':p['cameras'],'estimated_time_offset':p['estimated_time_offset'],'offset_basis':p['estimated_time_offset_basis'],'timestamp_derived_offset_b_minus_a':p['timestamp_derived_offset_b_minus_a'],'sync_status':p['sync_status'],'source_actions_private':p['source_actions_private'],'number_of_people_annotation':p['number_of_people_annotation'],'annotation_reason_for_candidate':p['annotation_reason_for_candidate'],'pair_contact_sheet_path':p['pair_contact_sheet_path'],'multi_view_gain':gain,'gain_role':'subjective selection heuristic, not official GT or model performance',**d};candidates.append(c)
  inputs={'cam_a_video':p['cameras']['c1']['local_video_path'],'cam_b_video':p['cameras']['c2']['local_video_path'],'conditions':{'single_a':['cam_a'],'single_b':['cam_b'],'multi_ab':['cam_a','cam_b']},'fixed_general_prompt':PROMPT,'media_policy':'original decoded pixels only; generic CAM A/B labels; full source video or uniform frames using the same predeclared schedule for all conditions; do not send review sheets, source filenames, annotation-selected sampling, annotations or scores'}
  private={'event_type':p['event_type'],'source_annotation_a':p['cameras']['c1']['source_annotation'],'source_annotation_b':p['cameras']['c2']['source_annotation'],'source_ground_truth':p['ground_truth_private'],'time_alignment_private':{k:p[k] for k in ['estimated_time_offset','estimated_time_offset_basis','timestamp_derived_offset_b_minus_a','sync_status','offset_convention']},'withheld_from_model':['event label','caption','VQA question and answer','reasoning / CoT','ground-truth descriptions','evidence/object/bbox/frame annotations','annotation-selected sheets and clip bounds','source filenames and scores']}
  manifest.append({'pair_id':p['pair_id'],'model_input':inputs,'ground_truth_private':private,'selection_review_private':d})
  r={k:c[k] for k in ['pair_id','incident_id','event_type','status','selection_reason','annotation_reason_for_candidate','number_of_people_annotation','estimated_time_offset','offset_basis','timestamp_derived_offset_b_minus_a','sync_status','multi_view_gain','pair_contact_sheet_path']};r.update(s)
  ir={k:p[k] for k in ['pair_id','incident_id','incident_id_basis','event_type','valid_pair','same_incident_association','pairing_rule','estimated_time_offset','estimated_time_offset_basis','timestamp_derived_offset_b_minus_a','sync_status']}
  for cam,l in [('c1','a'),('c2','b')]:
   v=p['cameras'][cam]
   for key,target in [('local_video_path','video'),('source_video','source_archive_video'),('source_annotation','annotation'),('duration','duration'),('fps','fps'),('event_start','event_start'),('event_end','event_end'),('event_duration_estimate','event_duration'),('suggested_clip_start','clip_start'),('suggested_clip_end','clip_end'),('contact_sheet_path','contact_sheet'),('boundary_quality','boundary_quality')]:r[f'cam_{l}_{target}']=v[key]
   r[f'cam_{l}_description']=c['cam_'+l+'_observation']
   for key,target in [('source_video','video'),('local_video_path','local_video'),('source_annotation','annotation'),('duration','duration'),('fps','fps'),('width','width'),('height','height'),('frames','frames'),('file_size','file_size'),('source_evidence_frame_range','evidence_frame_range'),('event_start','event_start'),('event_end','event_end'),('number_of_annotated_people','people')]:ir[f'cam_{l}_{target}']=v[key]
   ir[f'cam_{l}_id']=cam
  r['source_actions_private']=p['source_actions_private'];r['score_reasons']=d['score_reasons'];r['limitations']=d['limitations'];flat.append(r);inv.append(ir)
 candidates.sort(key=lambda c:c['multi_view_gain'],reverse=True);rank={c['pair_id']:i+1 for i,c in enumerate(candidates)}
 for c in candidates:c['recommendation_rank']=rank[c['pair_id']]
 for r in flat:r['recommendation_rank']=rank[r['pair_id']]
 writecsv('multiview_candidates.csv',sorted(flat,key=lambda r:r['recommendation_rank']));dump('multiview_candidates.json',candidates);dump('multiview_inventory.json',pairs);writecsv('multiview_inventory.csv',inv);dump('multiview_eval_manifest.json',manifest);dump('model_input_only.json',[{'pair_id':m['pair_id'],'model_input':m['model_input']} for m in manifest])
 lines=['# 477 AI Multi-camera Candidate Report','','## Dataset Structure','','- Total videos: 10 MP4, actual 30 FPS, 1920×1080, approximately 30–32 seconds each.','- Total annotations: 5 JSON. Total valid pairs: 5. All five reviewed; five retained including two lower-gain comparisons.','- Event class (private): 신체적 충돌을 동반한 싸움.','- Pairing rule: one source JSON explicitly co-lists c1/c2 files, each resolves uniquely. No explicit official incident_id/pair_id. MV IDs are local, annotation stems are locators.','- Synchronization: no official sync. Coarse recording clocks disagree with evidence onset differences. Neither establishes exact frame correspondence.','- Review: full-duration 1 Hz decoded temporal sheets + nine evidence-centered keyframes per camera. This is not continuous playback; brief contact between samples can be missed. Human final video verification remains necessary.','- EVENT/BEFORE/AFTER means position relative to evidence tracking range, not official exact action boundaries. Source 0/1-based indexing is unspecified; decoder frame numbers are zero based.','- All reports, inventories and contact sheets contain private answer hints: never send to the evaluated model. Use model_input_only.json. No VLM API experiment run.','','## Top Candidates','',*[f'{i+1}. {c["pair_id"]} — Gain {c["multi_view_gain"]:.2f}/5 — {c["selection_reason"]}' for i,c in enumerate(candidates[:3])],'','Gain = 0.35×complementarity + 0.25×occlusion_recovery + 0.20×participant_clarity_gain + 0.20×view_difference. Candidate-ordering heuristic only, not measured performance or source ground truth. Scores 1–5; ambiguity 1=clear, 5=ambiguous (more constrained view). No final pair selected.']
 for c in candidates:
  lines+=['','---','',f'## {c["pair_id"]}','','### Source','',f'Pair ID: {c["pair_id"]}; source locator: {c["incident_id"]}; role: {c["status"]}.']
  for cam,l in [('c1','A'),('c2','B')]:
   v=c['cameras'][cam];lines+=['',f'CAM {l} ({cam}):',f'- video: `{v["local_video_path"]}`',f'- original ZIP member: `{v["source_video"]}`',f'- annotation: `{v["source_annotation"]}`',f'- duration: {v["duration"]:.3f}s; FPS {v["fps"]:g}; {v["width"]}×{v["height"]}; {v["file_size"]:,} bytes.',f'- event support estimate: {v["event_start"]:.3f}–{v["event_end"]:.3f}s; tracking range {v["source_evidence_frame_range"]}; NOT exact official event bounds.',f'- people: {v["number_of_annotated_people"]} jointly annotated; sparse IDs {v["source_object_ids"]}; not all background pedestrians.',f'- suggested clip (not generated): {v["suggested_clip_start"]:.3f}–{v["suggested_clip_end"]:.3f}s ({v["suggested_clip_end"]-v["suggested_clip_start"]:.3f}s).',f'- near-black boundary frames: {v["boundary_quality"]["near_black_boundary_frames_zero_based"]}.']
  lines+=['',f'Estimated B media time − A: {c["estimated_time_offset"]:+.3f}s from evidence onset; coarse-clock alternative {c["timestamp_derived_offset_b_minus_a"]:+.1f}s. Neither proves sync.','','### What CAM A shows','',c['cam_a_observation'],'','### What CAM B shows','',c['cam_b_observation'],'','### Why multi-view helps','',c['why_multiview_helps'],'','### Limitations','',c['limitations'],'','5–10 seconds after the event is not guaranteed by these short source clips. No missing context synthesized. Pair sheet columns align independent event-support phases, not the same real moment.','','### Scores','','| Metric | Score | Selection reason |','|---|---:|---|',*[f'| {k} | {c["scores"][k]} | {c["score_reasons"][k]} |' for k in METRICS],f'| Multi-view gain (heuristic) | {c["multi_view_gain"]:.2f} | Ranking only |','','### Suggested evaluation','','CAM A only: A pixels + fixed generic prompt; assess observable interaction, evidence and uncertainty.','','CAM B only: B pixels + identical prompt; essential strong single-view baseline.','','CAM A + B: both pixel streams + identical prompt. Require camera-attributed evidence and no assumed sync. Compare with BOTH singles; AB better than A alone does not prove gain beyond B. Predeclare frame/token budgets and matched-total-budget sensitivity. Private clip suggestions above are not the current model-input schedule.','','### Contact sheets','']
  for cam,l in [('c1','A'),('c2','B')]:
   v=c['cameras'][cam]
   for key,label in [('contact_sheet_path',f'CAM {l}'),('temporal_sheet_path',f'CAM {l} full-duration 1 Hz')]:lines.append(f'- {label}: [{Path(v[key]).name}]({Path(v[key]).as_posix()})')
  path=Path(c['pair_contact_sheet_path']);lines.append(f'- Pair: [{path.name}]({path.as_posix()})')
 (ROOT/'multiview_candidate_report.md').write_text('\n'.join(lines),encoding='utf-8')
 old_ok=all(filehash(ROOT.parent/n)==h for n,h in read('existing_result_snapshot.json').items());zip_ok=all(filehash(Path(p))==v['sha256'] for p,v in read('source_zip_snapshot.json').items());crc_ok=True
 for f in read('temporary_files.json'):
  crc=0
  with Path(f['path']).open('rb') as stream:
   for chunk in iter(lambda:stream.read(1024*1024),b''):crc=zlib.crc32(chunk,crc)
  crc_ok=crc_ok and (crc&0xffffffff)==f['crc']
 for x in read('model_input_only.json'):
  assert set(x)=={'pair_id','model_input'} and set(x['model_input'])=={'cam_a_video','cam_b_video','conditions','fixed_general_prompt','media_policy'}
 for c in candidates:
  assert all(1<=v<=5 for v in c['scores'].values())
  for v in c['cameras'].values():
   assert 15<=v['suggested_clip_end']-v['suggested_clip_start']<=35
   assert v['suggested_clip_end']<=v['duration']
   assert all(0<=f['frame_zero_based']<v['frames'] for f in v['contact_frames'])
 for p in (ROOT/'contact_sheets').glob('*.jpg'):
  with Image.open(p) as im:im.verify()
 assert old_ok and zip_ok and crc_ok
 summary={'source_video_count':10,'annotation_count':5,'valid_pair_count':5,'visual_review_pair_count':5,'candidate_pair_count':5,'top3':[c['pair_id'] for c in candidates[:3]],'highest_gain':{'pair_id':candidates[0]['pair_id'],'gain':candidates[0]['multi_view_gain']},'extracted_bytes':sum(f['size'] for f in read('temporary_files.json')),'multiview_bytes':sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()),'old_results_sha256_unchanged':old_ok,'source_zips_sha256_unchanged':zip_ok,'extracted_members_crc_match':crc_ok,'contact_sheets_verified':len(list((ROOT/'contact_sheets').glob('*.jpg'))),'no_model_api_called':True,'no_final_pair_selected':True};dump('validation_summary.json',summary)
 structure=ROOT/'dataset_structure.md';base=structure.read_text(encoding='utf-8').split('\n## Decoder and review findings')[0]
 structure.write_text(base+'\n## Decoder and review findings\n\n- Ten videos: measured 30 FPS, 1920×1080. Final inventory contains durations, frame counts and file sizes.\n- JSON pair associations visually consistent; no per-frame cross-camera identity or exact sync.\n- Some evidence ends equal/exceed last zero-based frame. Source indexing convention unknown; only decode seeking clamped, annotation unchanged.\n- MV04/MV05 have short boundary black frames. Private clip proposals avoid confirmed boundary black frames; originals and sheets retain them.\n- Annotation-first shortlist has all five available incidents. Ten selected members extracted: 743,055,292 bytes. No derived clips generated.\n- Review sampled full duration at 1 Hz plus evidence anchors; final human playback still required.\n',encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
