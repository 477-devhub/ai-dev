from benchmark_common import *
import zipfile,xml.etree.ElementTree as ET,shutil,os
from datetime import datetime,timezone,timedelta

def annotation(locator):
 if '::' in locator:
  archive,member=locator.split('::',1)
  with zipfile.ZipFile(archive) as z:raw=z.read(member);info=z.getinfo(member)
  provenance={'archive':archive,'member':member,'member_crc':info.CRC}
 else:raw=Path(locator).read_bytes();provenance={'path':locator}
 digest=hashlib.sha256(raw).hexdigest()
 if locator.lower().endswith('.xml'):
  root=ET.fromstring(raw);payload={'format':'XML','raw_xml':raw.decode('utf-8-sig'),'event':{e.tag:e.text for e in root.findall('.//event/*')},'source_frame_convention':'as supplied; no frame index conversion'}
 else:payload={'format':'JSON','annotation':json.loads(raw)}
 return {'dataset':'AI Hub source data','source_locator':locator,'source_annotation_sha256':digest,'provenance':provenance,**payload}
def main():
 if (ROOT/'BENCHMARK_LOCK.json').exists():
  from validate_benchmark import check
  print(json.dumps(check()));print('Existing frozen v1 validated; no files rewritten. Changes require benchmark_v2.');return
 plan=read(ROOT/'private_ground_truth/build_plan.json')
 from build_media import main as media_main
 media_main();records=read(ROOT/'private_ground_truth/media_build_records.json')
 public_media={}
 for alias,target in plan['opaque_aliases'].items():
  p=ROOT/'media'/alias;m=probe(p);public_media['ASSET_'+alias[6:8]]={'path':'media/'+alias,'sha256':sha(p),**{k:m[k] for k in ['duration','fps','width','height','frame_count']}}
 write(ROOT/'public_manifest.json',{'benchmark_version':plan['benchmark_version'],'media':public_media})
 spec=[('ITEM_01','single',['ASSET_01']),('ITEM_02','single',['ASSET_02']),('ITEM_03','single',['ASSET_03']),('ITEM_04','attention',['ASSET_01','ASSET_04','ASSET_02']),('ITEM_05','single',['ASSET_05']),('ITEM_06','single',['ASSET_06']),('ITEM_07','multi_camera',['ASSET_05','ASSET_06'])]
 items=[{'item_id':i,'task':task,'cameras':[{'camera':f'CAM_{n:02d}','asset':a} for n,a in enumerate(assets,1)]} for i,task,assets in spec]
 # B-only uses generic CAM_02 to preserve attribution across A/B/AB, without implying source identity.
 items[5]['cameras'][0]['camera']='CAM_02'
 protocol={'id':'uniform_total64_v1','transport':'decoded RGB frames','total_frames_per_item':64,'allocation':'equal per camera, remainder to cameras in manifest order','frame_selection':'round-half-up(j*(frame_count-1)/(allocation-1)), j=0..allocation-1','timestamps':'zero-based output frame number / 30, relative to each clip; no cross-camera synchronization asserted','image_size':[1920,1080],'prompt_language':'English','model_input_policy':'pixels, generic camera IDs, neutral relative times, common prompt and response structure only'}
 write(ROOT/'model_input/scenarios.json',{'benchmark_version':plan['benchmark_version'],'protocol':protocol,'items':items})
 annotations={recipe['source_annotation']:annotation(recipe['source_annotation']) for recipe in plan['recipes']}
 source_records=read(ROOT/'private_ground_truth/source_candidate_records.json')
 for recipe in plan['recipes']:
  cid=recipe['source_candidate']
  if cid in source_records and annotations[recipe['source_annotation']]['source_annotation_sha256']!=source_records[cid]['annotation_sha256']:raise RuntimeError('Source annotation changed since approved selection')
 common={'event_understanding':{'0':'Core observable event misunderstood.','1':'Partial core event, missing material visible behavior.','2':'Core observable behavior correct; source class is not required if facts are accurate.'},'temporal_understanding':{'0':'Ordering/persistence materially wrong.','1':'Some sequence captured.','2':'Core before/transition/after relationship correct.'},'evidence_grounding':{'0':'No support or material invented evidence.','1':'Partly visible support.','2':'Clear visible evidence attributed to correct camera/time.'},'uncertainty_calibration':{'0':'Unsupported intent, diagnosis, authorization, identity or cross-camera fact asserted.','1':'Some uncertainty but facts and inferences mixed.','2':'Observable facts and unknowns clearly separated.'}}
 def base(setid,source,observed,reference):return {'scenario_id':setid,'source_ground_truth':source,'human_verified_observation':observed,'project_defined_reference':{'provenance':'477 project-defined human reference','rubric_anchors':common,**reference}}
 r=plan['recipes'];sg=lambda index:annotations[r[index]['source_annotation']]
 gt1=base('set01',{**sg(0),'source_event_label':'swoon','source_clip_range_sec':[225.6,260.6]},{'provenance':'user original-video verification','normal_movement_then_fall':True,'remains_in_ground_posture_afterward':True},{'core_observable_sequence':['normal movement','fall','continued ground posture'],'expected_uncertainty':['medical cause and injury severity cannot be established from the video'],'risk_reasoning_expectation':'Reason about immediate welfare and persistence without a diagnostic or numerical risk target.'})
 gt2=base('set02',{**sg(1),'source_event_label':'trespass','source_clip_range_sec':[252.8,287.8]},{'provenance':'user original-video verification','starts_outside_wall':True,'crosses_over_wall':True,'moves_inside':True},{'core_observable_sequence':['outside physical boundary','climbs/crosses wall','moves inside'],'expected_uncertainty':['authorization and legal status are not established by visible boundary crossing']})
 gt3=base('set03',{**sg(2),'source_event_label':'trespass','source_event_interval_sec':[218.1,288.3],'source_clip_range_sec':[256.0,291.0]},{'provenance':'user original-video verification','observed_gate_entry':True,'looks_around_before_entry':True,'authorization_visible':False,'criminal_intent_visible':False},{'core_observable_sequence':['gate-side direction changes','final re-approach','gate opening and entry'],'expected_uncertainty':['authorization cannot be determined from video','intent cannot be determined from video'],'clip_selection':plan['t03_selection'],'correct_event_understanding_allows':'neutral entry through a gate; not required to claim unlawful entry'})
 gt4=base('set04',{'dataset':'AI Hub 이상행동 CCTV','cameras':{'CAM_01':{'source_candidate':'S14','annotation':sg(0),'source_clip_range_sec':[225.6,260.6]},'CAM_02':{'source_candidate':'F01','annotation':sg(3),'source_clip_range_sec':[116.5,151.5]},'CAM_03':{'source_candidate':'T06','annotation':sg(1),'source_clip_range_sec':[252.8,287.8]}}},{'provenance':'user approved final source selection','approved_clips':['S14','F01','T06']},{'reference_source_order':['S14','F01','T06'],'reference_camera_order':['CAM_01','CAM_02','CAM_03'],'reference_rationale':['person falls and remains down','sustained physical conflict','person crosses physical boundary'],'simultaneity':'hypothetical concurrent alerts for evaluation; not actual shared recording time','risk_numeric_ground_truth':None})
 gt5=base('set05',{**sg(4),'source_event_label':'신체적 충돌을 동반한 싸움','source_locator':'ph_e2069','pairing_rule':'two videos explicitly co-listed in source JSON','official_frame_synchronization':None,'camera_sources':{cam:mv['source_video'] for cam,mv in plan['multiview_source_record']['cameras'].items()}},{'provenance':'user verified both original views and approved pair for evaluation','two_views_reviewed':True,'suitable_for_evaluation':True},{'conditions':{'MV05_A':'ITEM_05','MV05_B':'ITEM_06','MV05_AB':'ITEM_07'},'same_incident_reference':True,'same_incident_basis':'source JSON co-listing plus human-approved source pair; no exact frame mapping supplied','grounded_complementarity_reference':'CAM_01 foliage obscures much of later interaction; CAM_02 provides road-side interaction, low body posture and later movement. No medical diagnosis or person identity certainty implied.','multi_view_increment':'AB rubric total minus max(A rubric total, B rubric total)','limitations':['B-only is strong; AB>A alone is insufficient','each clip has independent time origin','same person correspondence requires evidence; no universal re-identification ground truth','whole clips preserve short final black source frames'],'risk_numeric_ground_truth':None})
 for n,gt in enumerate([gt1,gt2,gt3,gt4,gt5],1):write(ROOT/f'private_ground_truth/set{n:02d}.json',gt)
 # Preserve original video hashes and existing selection files without requiring originals for portable runtime validation.
 original_checks={rec['source_path']:{'sha256_before':rec['source_sha256'],'sha256_after':sha(rec['source_path'])} for rec in records.values()}
 if any(v['sha256_before']!=v['sha256_after'] for v in original_checks.values()):raise RuntimeError('Original video changed')
 old=read(ROOT/'private_ground_truth/initial_protection_snapshot.json')
 if any(sha(Path(path))!=h for path,h in old.items()):raise RuntimeError('Existing selection results changed')
 write(ROOT/'private_ground_truth/source_preservation_validation.json',{'videos':original_checks,'existing_selection_artifacts_unchanged':True,'source_annotation_hashes_verified':True})
 media={}
 for p in sorted((ROOT/'media').glob('*.mp4')):
  if '.partial.' in p.name:raise RuntimeError('Unfinished media present')
  media['media/'+p.name]={'sha256':sha(p),**probe(p)}
 source_report=[f'| {x["name"]} | {records[x["name"]]["source_clip_start_sec"]:.3f}–{records[x["name"]]["source_clip_end_sec"]:.3f}s | {records[x["name"]]["output_metadata"]["duration"]:.6f}s |' for x in r]
 readme='''# 477-reasoning-v1

**Stage 2 — AI Reasoning / Attention Orchestration Benchmark.** Candidate events are already selected. This package tests visual/temporal understanding, risk reasoning, uncertainty, attention and multi-camera evidence. It does not test detector recall/FPR or end-to-end deployment performance. Five human-approved cases, seven execution conditions; no candidate replacement. No external API, CV model or LLM run was performed. Results directories are empty.

## Frozen cases

SET01 S14: normal movement → fall → ground posture, 225.6–260.6s.
SET02 T06: outside wall → wall crossing → inside movement, 252.8–287.8s.
SET03 T03: **256.0–291.0s, 35 seconds**, the minimum allowed 35–45s length. Gate-side looking/direction changes, moving away, final approach, opening/entry (~285–286s) and inside position follow continuously. The initial approach around 212s cannot fit with actual entry in a 45s clip; the final re-approach is included. Head/direction changes are visible; criminal intent and authorization are not established. Selection was made from source pixel inspection, not the XML label. Source selection notes and review crops are private; evaluation is uncropped full frame.
SET04 R01: hypothetical concurrent independent alerts. CAM_01=S14, CAM_02=F01, CAM_03=T06. Reference order **S14 > F01 > T06** is **477 project-defined human reference**, not AI Hub ground truth. No numerical risk targets. Recording simultaneity is not claimed.
SET05 MV05/ph_e2069: whole CAM A/c1 and CAM B/c2 source durations, including short last black frames. No official precise synchronization. Compare A, B and AB; key increment is AB minus best single, not AB minus A alone.

| Encoded media | Source range | Actual duration |
|---|---|---|
'''+ '\n'.join(source_report)+'''

## Media and privacy

Six source clips encoded once with libx264 CRF 18, medium, Lanczos 1920×1080, CFR 30 FPS, yuv420p, no audio, metadata stripped. Four original single-camera sources were 3840×2160 at 30000/1001 FPS, so scaling and FPS normalization are deliberate. MV05 originals were H.264 1080p/30 FPS; whole temporal clips retained under the same encoding recipe. All conditions and pipelines reuse the exact same output bytes. Encoder version/command, original metadata, source ranges and hashes are private provenance.

Requested descriptive media names are human-facing only. SET04 CAM A/C are byte-identical hardlinks (copy fallback) of SET01/02, never re-encoded. Six additional asset_01.mp4…asset_06.mp4 aliases are also hardlinks/copy fallback. **Only opaque aliases in public_manifest.json are allowed for harness loading; upload display names are generic CAM_01, CAM_02, CAM_03.** Do not send directory listings, descriptive filenames, README, BENCHMARK_LOCK.json or private_ground_truth to models.

model_input/scenarios.json contains only opaque item/asset IDs, generic camera IDs, neutral task and frozen sampling protocol. prompt_v1.txt is English and common to both pipelines. There is no event class list or same-incident answer in it. Observation time is clip-relative for each camera, never annotation time or synchronized absolute time.

Source labels/XML/captions/answers/CoT, source filenames/IDs, evidence frame annotations, expected ranking, clip rationale and grading references live under private_ground_truth only. Each set JSON explicitly separates source_ground_truth, human_verified_observation and project_defined_reference. The standalone load_model_input.py has no private-data imports or paths; it reads only public artifacts and evaluation media. The combined benchmark folder is for evaluators, not a model upload bundle.

## Fixed fair input protocol

Primary protocol **uniform_total64_v1**: exactly 64 decoded RGB frames per item, allocated equally among cameras with remainder to manifest order. Uniform frame selection includes clip endpoints: round-half-up(j*(N-1)/(K-1)). Single A/B receive 64 frames; AB receives 32 per view. Attention receives 22/21/21. Timestamps are selected output-frame number divided by 30. Thus both pipelines see identical pixels and timeline, and multi-view does not get twice the total frame budget. This matched-budget comparison has lower per-camera temporal density in multi-view; interpret missing detail accordingly. Native-video transport or a per-camera budget is a different protocol requiring an explicit new version/experiment definition, not a silent replacement.

load_model_input.load_item returns harness-only media locators, expected fingerprint, generic prompt and task-specific schema. **iter_model_frames(item_id)** streams canonical frames in memory via ffmpeg, returning only RGB bytes, generic camera ID and neutral relative timestamp. It writes no frames and calls no models. The harness must actually send these canonical frames, not upload the whole MP4 and report a fictional 64-frame fingerprint. Paths and item IDs stay in harness metadata, not prompt text. CV+LLM may compute features from exactly these frames; no additional source frames, private answers or annotations may be introduced. Record CV checkpoints/configuration and LLM/model settings in runtime_config. Use the same text/schema, decoding, frame schedule and comparable generation settings. Input hashes and frame indices are mandatory in measured results. End-to-end reasoning latency/cost should include all CV and LLM stages, preprocessing and upload as declared in runtime_config; do not compare partially timed pipelines.

## Condition mapping (evaluator only)

- ITEM_01=SET01; ITEM_02=SET02; ITEM_03=SET03.
- ITEM_04=SET04, CAM_01/CAM_02/CAM_03 as above.
- ITEM_05=MV05_A/CAM_01; ITEM_06=MV05_B/CAM_02; ITEM_07=MV05_AB/both.

## Schemas and scoring

prediction.schema.json: single assessment, three-camera attention assessments/queue, or multi-camera assessment with same_incident, camera_evidence, cross_camera_summary and additional_information_from_second_view. Runtime validator selects the required shape by item, checks timestamps and camera attribution, and forces exactly three unique ranking cameras/ranks. event_type is free text: no label choices supplied. All risk components and confidence are predictions bounded 0–1, never numerical ground truth.

result.schema.json includes pipeline, run/model/config, exact input fingerprint, prediction, human_grading and nullable latency_ms/input_tokens/output_tokens/estimated_cost_usd. No fake result or prediction is provided. For a real future run, use null for unavailable usage/latency/cost rather than invented values. human_grading is null until a named reviewer assigns the four 0/1/2 scores (Event, Temporal, Evidence, Uncertainty); anchors are in private set files. A second reviewer/adjudication is advisable; values are project rubric, not official AI Hub metrics. Risk reasoning is inspected through reason/evidence and human notes, with no numerical risk target.

score_results.py validates actual results and their exact fingerprints before scoring. It does not invent semantic grades, use a judge model or fill missing grades with zero. Report scenario scores and x/5 with explicit coverage; never percent accuracy/generalization from these five cases. SET05 A/B are additional conditions; main five-case summary counts SET01–04 and SET05 AB. Attention Top-1 and full-order compare the private project reference. Multi-view Increment = AB rubric total (0–8) minus max(A total, B total); per-metric increments also reported. Scores remain null/pending until the three conditions are human-graded.

Six overclaim types: unsupported diagnosis, criminal intent, authorization, identity, weapon, cross-camera identity. Human flags require an exact output quote and visual-support explanation. Lightweight keyword screening adds **suspected** review flags only; it cannot establish unsupportedness, may miss paraphrases or confuse negation, and never counts as confirmed without human adjudication. No official severity/risk/priority/confidence ground truth was invented.

## Commands

From D:/projects/477/benchmark_v1 (WSL mapping /mnt/d/projects/477/benchmark_v1):

```bash
python scripts/validate_benchmark.py
python scripts/build_benchmark.py
# Frozen build only validates, never rewrites. Actual changes require a new benchmark_v2 package.
python scripts/load_model_input.py ITEM_07
# Future real predictions/results only:
python scripts/validate_prediction.py results/vlm_only/run_ITEM_01.json --result
python scripts/score_results.py results/vlm_only/run_*.json --output results/vlm_only/summary.json
```

On Windows use installed Python with jsonschema (currently D:/Users/suncastle/anaconda3/python.exe). ffmpeg/ffprobe must be on PATH; no packages or models installed here. PowerShell wildcard expansion for score_results is not guaranteed: pass explicit filenames or use Python/glob to enumerate; summary.json is an aggregate, not a result-schema input.

## Lock and protection

BENCHMARK_LOCK.json fixes SHA256, duration, frame count, encoding and all reusable/opaque media files; it also hashes prompt, schemas, scripts, private references and review artifacts. Validation fails for changed bytes, durations, hashes, missing files, private hints/public source filenames, model loader private imports/paths or invalid schema definitions. Results and Python cache are outside locked artifacts. Do not alter the lock to conceal changed media. Source video before/after hashes and previous selection artifact hashes were checked at freeze, original ZIPs/media/annotations were not edited. Runtime validation is portable and does not require original archive availability. Semantic leakage validation complements exact schema/key allowlists and hashes; it cannot audit an external uploader implementation or model provider hidden preprocessing.

All writes are under benchmark_v1. Storage checked before media encoding (>2 GiB headroom required). Original large source videos were not copied wholesale except temporal content needed for approved short clips. No automatic temp deletion. Private inspection images/caches are frozen audit material. Rebuilding on another ffmpeg/platform may not reproduce byte-identical encodes; the frozen hashed media are the authoritative identical inputs. Keep v1 read-only in comparison runs and create v2 for changes. These few selected/staged CCTV examples are a diagnostic benchmark, not deployment safety evidence.
'''
 (ROOT/'README.md').write_text(readme,encoding='utf-8')
 lock={'benchmark_version':plan['benchmark_version'],'frozen':True,'scope':plan['stage'],'created_at':datetime.now(timezone(timedelta(hours=9))).isoformat(),'duration_tolerance_sec':.04,'media':media,'identical_content_pairs':[['media/set01_swoon.mp4','media/set04_cam_a_swoon.mp4'],['media/set02_trespass.mp4','media/set04_cam_c_trespass.mp4']]+[['media/'+alias,'media/'+target] for alias,target in plan['opaque_aliases'].items()],'private_files_model_input_policy':'never loaded by model-input loader','artifacts_sha256':{}}
 for p in sorted(ROOT.rglob('*')):
  if not p.is_file() or p.name=='BENCHMARK_LOCK.json' or 'results' in p.relative_to(ROOT).parts or '__pycache__' in p.parts or p.suffix=='.pyc' or p.parent==ROOT/'media':continue
  lock['artifacts_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
 write(ROOT/'BENCHMARK_LOCK.json',lock)
 from validate_benchmark import check
 print(json.dumps(check(),ensure_ascii=False))
if __name__=='__main__':main()
