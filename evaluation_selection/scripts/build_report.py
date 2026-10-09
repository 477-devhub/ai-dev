from build_inventory import *
from PIL import Image
KEYS=['event_visibility','event_clarity','temporal_value','visual_quality','reasoning_value','demo_suitability','ambiguity']
FIELDS=['candidate_id','scenario','event_type','video_path','annotation_path','duration','fps','event_start','event_end']+KEYS+['contact_sheet_path','selection_reason','local_video_path','local_annotation_path','review_status','source_candidate_id','temporal_sheet_path','event_duration','annotation_duration']+[k+'_reason' for k in KEYS]
def link(p,label=None):
 return f'[{label or p}](<{str(p).replace(chr(92),"/")}>)'
def repair_order(r,key,path,cols,w):
 records=r.get(key,[]);order=sorted(range(len(records)),key=lambda i:records[i]['decoded_seconds'])
 if order==list(range(len(records))):return
 im=Image.open(path);new=im.copy();cellh=round(w*9/16)+47
 tiles=[im.crop((i%cols*w,i//cols*cellh+45,(i%cols+1)*w,(i//cols+1)*cellh+45)) for i in range(len(records))]
 for n,i in enumerate(order):new.paste(tiles[i],(n%cols*w,n//cols*cellh+45))
 new.save(path,quality=88);r[key]=[records[i] for i in order]
def main():
 inv=read('inventory_details.json');reviewed=read('review_shortlist.json')+read('alternate_views.json');cfg=read('review_decisions.json');by={r['candidate_id']:r for r in reviewed}
 for r in reviewed:
  repair_order(r,'sampled_frames',r['contact_sheet_path'],3,480);repair_order(r,'temporal_sampled_frames',r['temporal_sheet_path'],4,400)
 dump('reviewed_videos.json',reviewed)
 first_ids={r['candidate_id'] for r in read('review_shortlist.json')}
 dump('review_shortlist.json',[r for r in reviewed if r['candidate_id'] in first_ids])
 dump('alternate_views.json',[r for r in reviewed if r['candidate_id'] not in first_ids])
 # Merge only verified decoder metadata for six selectively extracted Fight files.
 for r in inv:
  matches=[v for v in reviewed if v['video_path']==r['video_path']]
  if matches:
   v=matches[0]
   for k in ['video_probe_status','video_duration','video_fps','video_width','video_height','video_frames','local_video_path','local_annotation_path']:
    if k in v:r[k]=v[k]
 dump('inventory_details.json',inv)
 flat=[]
 for r in inv:
  q={k:v for k,v in r.items() if k not in ['objects','source_ground_truth']};q['actions']='|'.join(r['actions']);flat.append(q)
 fields=list(dict.fromkeys(k for r in flat for k in r));csvwrite('dataset_inventory.csv',flat,fields)
 candidates=[]
 for scenario,ids in cfg['scenarios'].items():
  for n,cid in enumerate(ids,1):
   r=by[cid];v=cfg['reviews'][cid];c={**r,**v,**v['scores'],'candidate_id':f'D{n:02d}' if scenario=='D' else cid,'source_candidate_id':cid,'scenario':scenario,'annotation_duration':r['duration'],'duration':r['video_duration'] or r['duration'],'score_basis':'qualitative selection review, not source ground truth'}
   for k in KEYS:c[k+'_reason']=v['score_reasons'][k]
   candidates.append(c)
 dump('candidates.json',candidates);csvwrite('candidates.csv',candidates,FIELDS)
 facts=[]
 for r in inv:
  facts.append({'source':'AI Hub 이상행동 CCTV','source_video':r['video_path'],'source_annotation':r['annotation_path'],'event_type':r['event_type'],'event_start':r['event_start'],'event_end':r['event_end'],'annotation_summary':'event label: '+r['event_type']+'; actions: '+', '.join(r['actions']),'objects':r['objects'],'source_ground_truth':r['source_ground_truth'],'source_annotation_sha256':r['annotation_sha256'],'note':'Source facts retained even when video/annotation pairing is suspected. This file does not validate semantic pairing.'})
 dump('source_annotation_facts.json',facts)
 lines=['# 477 AI Evaluation Candidate Report','','## Dataset Summary','','이 보고서는 사람이 선택할 후보 목록이다. 최종 5개 선정, 위험 순위 정답, 모델 학습을 수행하지 않았다.','','검토 방법: 전체 118개 XML 및 파일 목록 조사 → annotation 기반 표본 21개 → Swoon 대체 시점 9개 추가 → 총 30개 영상의 사건 전후 9장과 시간순 24장 검토. 전체 영상 연속 재생 또는 전체 프레임 검토는 수행하지 않았다. 점수는 정성적 선정 판단이며 AI Hub 정답이 아니다.','', '경로: Windows 실제 경로 D:/projects/477 (요청한 /mnt/d/projects/477에 대응). ZIP의 absolute_archive_path::member는 원본 locator이며 실제 디코딩 파일 경로를 별도로 표시한다.','','| Event | 총 영상 | Annotation | 평균 XML duration | 실제 영상 메타데이터 확인 |','|---|---:|---:|---:|---:|']
 for e in ['fight','swoon','trespass']:
  rs=[r for r in inv if r['event_type']==e];lines.append(f'| {e} | {len(rs)} | {len(rs)} XML | {statistics.mean(r["duration"] for r in rs):.2f}s | {sum(r["video_probe_status"]=="opencv_verified" for r in rs)} |')
 lines+=['','XML은 MP4와 동일 stem이며 event/starttime+duration, object별 action/frame start/end 및 keyframe/keypoint를 제공한다. bbox와 제한구역 좌표는 없다. 4K/30 FPS는 모든 XML 및 70개 실제 영상 메타데이터에서 확인했다.','','## Review priorities','','아래 Top 3는 검토 순서 제안이며 최종 선정이 아니다. C는 평범한 이동과 맥락 판단을 우선하고, 담장 넘기 T06/T08은 명확한 비교 표본이다. B에는 명확성이 상대적으로 높은 4개와 차량 가림 조건부 2개가 포함된다. D는 A/C와 일부 영상을 공유하며 독립 샘플 수로 중복 계산하면 안 된다.','']
 for s,ids in cfg['top3'].items():
  if s=='D':ids=[next(c['candidate_id'] for c in candidates if c['scenario']=='D' and c['source_candidate_id']==i) for i in ids]
  lines.append(f'- Scenario {s} Top 3: '+', '.join(ids))
 titles={'A':'Clear Fight','B':'Clear Swoon','C':'Temporal Trespass','D':'Ambiguous Cases'}
 for s,title in titles.items():
  lines+=['',f'## Scenario {s} — {title}','']
  if s=='A':lines+=['Fight 후보 6개는 녹색 스튜디오 배경이다. 신체 충돌 동작을 평가할 수 있으나 실제 현장 CCTV의 배경·자연스러운 위험 맥락에 대한 대표성은 낮다.','']
  if s=='B':lines+=['S02/S04는 차량 가림 때문에 조건부 후순위이다. 표본 수를 채우려고 완전히 명확한 사례라고 표시하지 않았다. 누운 상태는 관찰할 수 있지만 의학적 실신 원인이나 의식 상태를 확정할 수 없다.','']
  if s=='D':lines+=['정상/비사건 negative 영상을 새로 만든 것이 아니다. 모두 source positive label이 있는 hard positive이며, false-positive rate 자체를 계산하려면 별도 정상 영상이 필요하다.','']
  for c in [c for c in candidates if c['scenario']==s]:
   lines += [f'### Candidate {c["candidate_id"]}',f'- Source review ID: {c["source_candidate_id"]}',f'- Video (원본): `{c["video_path"]}`',f'- Annotation (원본): `{c["annotation_path"]}`',f'- Video (재생 가능한 절대경로): {link(c["local_video_path"])}',f'- Annotation (실제 파일): {link(c.get("local_annotation_path") or c["annotation_path"])}',f'- Duration: {c["duration"]:.3f}s (영상); {c["annotation_duration"]:.3f}s (XML). FPS: {c["fps"]}.',f'- Event interval: {c["event_start"]:.1f}–{c["event_end"]:.1f}s (XML, {c["event_duration"]:.1f}s).',f'- Selection reason: {c["selection_reason"]}',f'- Status: {c["review_status"]}',f'- Source actions: {", ".join(c["actions"])}',f'- Sampled observations: {json.dumps(c["visual_observations"],ensure_ascii=False)}','- Scores:','','| 기준 | 점수 | 이유 |','|---|---:|---|']
   lines += [f'| {k} | {c[k]} | {c["score_reasons"][k]} |' for k in KEYS]
   lines += ['',f'- Contact sheet (9장): {link(c["contact_sheet_path"])}',f'- Temporal sheet (24장): {link(c["temporal_sheet_path"])}',f'![{c["candidate_id"]}]({str(c["contact_sheet_path"]).replace(chr(92),"/")})','']
 combinations=[];lines+=['## Scenario E — Attention Ranking','','원본 약 5분 전체는 동시 재생에 길다. 각 CAM의 아래 35초 구간을 seek해서 동시에 시작하는 가상 테스트를 제안한다. 재생 구간은 평가 제안이며 annotation을 수정한 정답 구간이 아니다. 파일 자르기/복사/동시 촬영 여부를 주장하지 않는다. Fight 구간은 긴 사건의 일부만 포함한다. 위험 우선순위 정답은 미정이다. 제한구역의 법적/운영상 지위는 annotation에 없으며 시각적 경계 통과만 기록한다.','']
 for comb in cfg['ranking']:
  cams={};lines += [f'### Combination {comb["combination_id"]}','']
  for cam,cid in comb['cameras'].items():
   r=by[cid];v=cfg['reviews'][cid];start=max(0,r['event_start']-5);end=min(r['video_duration'],start+35)
   cams[cam]={'candidate_id':cid,'event_type':r['event_type'],'video_path':r['video_path'],'local_video_path':r['local_video_path'],'annotation_path':r['annotation_path'],'duration':r['video_duration'],'event_duration':r['event_duration'],'event_start':r['event_start'],'event_end':r['event_end'],'suggested_playback_start':start,'suggested_playback_end':end,'suggested_playback_duration':end-start,**v['visual_observations']}
   lines += [f'#### {cam} = {r["event_type"]} ({cid})',f'- Video: {link(r["local_video_path"])}',f'- Source: `{r["video_path"]}`',f'- Annotation: `{r["annotation_path"]}`',f'- Duration: {r["video_duration"]:.3f}s; XML event duration: {r["event_duration"]:.1f}s.',f'- Suggested playback: {start:.1f}–{end:.1f}s ({end-start:.1f}s).',f'- Visible persons (sampled min–max): {v["visual_observations"]["visible_persons_range_in_sampled_frames"]}; XML population: {r["population_annotation"]}.',f'- Physical contact: {v["visual_observations"]["physical_contact_observed"]}; low movement after fall: {v["visual_observations"]["remains_motionless_in_sampled_frames"]}; boundary entry visible: {v["visual_observations"]["boundary_entry_visible"]}.',f'- Contact sheet: {link(r["contact_sheet_path"])}','']
  combinations.append({**comb,'cameras':cams,'priority_ground_truth':None,'simultaneity':'evaluation_assumption_only'})
  lines += ['Reason this combination is useful: '+comb['reason'],'']
 dump('ranking_combinations.json',combinations)
 lines+=['## Data issues and limitations','','- Swoon의 S07–S13은 XML/filename 주간과 실제 야간 영상이 불일치한다. 사건 구간에서도 일치하는 쓰러짐을 확인하지 못해 후보에서 제외했다. 원인을 복구 오류로 단정하지 않으며 원본 pairing 재검증이 필요하다.','- Swoon 11개 XML/영상 길이 차이; 세부 목록은 data_issues.json 및 dataset_structure.md 참조. 시간 오프셋을 임의 보정하지 않았다.','- F04 XML 종료 뒤에도 접촉이 관찰된다. Fight 여러 시점은 XML 시작 전 제스처도 있다. XML 이벤트 경계와 관찰 경계는 별개다.','- Frame 번호는 디코더 0-based이며 source XML의 indexing convention은 확인되지 않았다. seek 결과 실제 frame을 기록하며 한 프레임 수준 양자화로 경계 시점이 BEFORE/AFTER로 표시될 수 있다.','- XML population은 실제 보이는 사람 수와 다를 수 있다. 예: Fight 4명이 보이는 표본의 object/참여자는 일부 인물만 포함한다.','- motionless는 시간순 표본에서 자세 변화가 작다는 관찰이며 지속적 완전 무동작 측정이 아니다.','- 카메라·계절·source ID 간 상관성이 크다. 미래 모델 비교 시 동일 sampling/FPS/ROI/프롬프트 및 재생 구간을 고정하고 related ID를 분리 평가 데이터로 섞지 않아야 한다.','- 전체 Fight ZIP 54개 중 영상 검토는 6개에 한정된다. 후보는 전수 품질 순위가 아니다.','', '## Temporary extraction and storage','','임시 파일을 자동 삭제하지 않았다. 아래 파일은 ZIP에서 재생성할 수 있지만 삭제 전에 사용자가 확인해야 한다. 삭제하면 현재 Fight 로컬 재생 경로가 없어지며 contact sheet/원본 ZIP locator는 남는다.','']
 for item in read('temporary_files.json'):lines.append(f'- `{item["path"]}` — {item["size"]:,} bytes')
 lines += ['',f'- Fight extracted bytes: {sum(x["size"] for x in read("temporary_files.json")):,}.',f'- Temporary listing: {link(ROOT/"temporary_files.json")}.','- 현재 총 용량은 storage_summary.json에서 확인할 수 있다.','']
 (ROOT/'candidate_report.md').write_text('\n'.join(lines),encoding='utf-8')
 excluded=[{'candidate_id':cid,'video_path':by[cid]['video_path'],'annotation_path':by[cid]['annotation_path'],'reason':why,'contact_sheet_path':by[cid]['contact_sheet_path'],'temporal_sheet_path':by[cid]['temporal_sheet_path']} for cid,why in cfg['excluded'].items()];dump('excluded_review.json',excluded)
 dump('selection_summary.json',{'dataset_counts':{e:sum(r['event_type']==e for r in inv) for e in ['fight','swoon','trespass']},'candidate_counts':{s:sum(c['scenario']==s for c in candidates) for s in titles},'ranking_combinations':len(combinations),'unique_candidate_videos':len(set(c['video_path'] for c in candidates)),'reviewed_videos':len(reviewed),'excluded_pairing_suspects':len(excluded),'top3':cfg['top3']})
 structure=ROOT/'dataset_structure.md';s=structure.read_text(encoding='utf-8');marker='\n## Candidate video crosscheck and visual audit\n';s=s.split(marker)[0]+marker+'\nFight candidates: 6 actual MP4 metadata checks; remaining 48 XML-only. All probed sources are 3840x2160 / 30 FPS (minor floating point rates retained). Reviewed videos: 30. S07–S13 source/visual day-night and event mismatch suspected; see excluded_review.json. No semantic re-pairing performed. No bbox in any of 118 XML files.\n';structure.write_text(s,encoding='utf-8')
 print('Report:',len(candidates),'scenario rows;',len(set(c['video_path'] for c in candidates)),'unique videos;',len(combinations),'ranking combinations')
if __name__=='__main__':main()
