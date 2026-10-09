from benchmark_common import *
from validate_prediction import validate_result
import re,argparse
METRICS=['event_understanding','temporal_understanding','evidence_grounding','uncertainty_calibration']
PATTERNS={
 'unsupported medical diagnosis':r'\b(?:has|suffered|suffering from)\s+(?:a\s+)?(?:heart attack|stroke|seizure)|\bis (?:dead|unconscious)\b|심장마비|뇌졸중|의식을 잃었|사망했',
 'unsupported criminal intent':r'\b(?:intends? to (?:steal|rob)|criminal intent|planning (?:a )?(?:theft|burglary))\b|범죄 의도|훔치려|절도 목적',
 'unsupported authorization claim':r'\b(?:unauthorized|authorized|illegal entry|illegally entered)\b|출입 권한이 (?:있|없)|무단침입|불법 침입',
 'unsupported identity claim':r'\b(?:is the (?:owner|resident|thief)|identified as)\b|집주인이다|거주자이다|범인이다',
 'unsupported weapon claim':r'\b(?:holding|carrying|using) (?:a )?(?:gun|knife|weapon)\b|칼을 들|총을 들|무기를 사용',
 'unsupported cross-camera identity claim':r'\b(?:definitely|certainly|clearly) the same person\b|동일 인물임이 확실|확실히 같은 사람'}
NEGATION=r'\b(?:cannot|not|unknown|uncertain|unconfirmed|unable|undetermined)\b|알 수 없|판단할 수 없|확정할 수 없|불확실|단정할 수 없'
def screen(pred):
 # Text candidates only. Unsupportedness requires human visual adjudication; no keyword hit is official GT.
 strings=[]
 def collect(v):
  if isinstance(v,str):strings.append(v)
  elif isinstance(v,dict):
   for x in v.values():collect(x)
  elif isinstance(v,list):
   for x in v:collect(x)
 collect(pred);flags=[]
 for s in strings:
  for sentence in re.split(r'[.!?\n]',s):
   if re.search(NEGATION,sentence,re.I):continue
   for kind,pattern in PATTERNS.items():
    if re.search(pattern,sentence,re.I):flags.append({'type':kind,'text':sentence.strip(),'status':'suspected; requires human visual review'})
 return flags

def score_files(files):
 results=[read(p) for p in files]
 for result in results:validate_result(result)
 groups={}
 for result in results:
  key=(result['pipeline'],result['run_id']);group=groups.setdefault(key,{})
  if result['item_id'] in group:raise ValueError('Duplicate item within run')
  group[result['item_id']]=result
 summary={'benchmark_version':'477-reasoning-v1','scope':'Stage 2 reasoning on five fixed cases; no statistical generalization','runs':[]}
 reference=read(ROOT/'private_ground_truth/set04.json')['project_defined_reference']['reference_camera_order']
 for (pipeline,runid),items in groups.items():
  if len({r['model_id'] for r in items.values()})>1:raise ValueError('Mixed model IDs in one run')
  rows=[];graded={}
  for item_id,result in sorted(items.items()):
   human=result['human_grading'];ready=human is not None and all(human[k] is not None for k in METRICS)
   if ready:graded[item_id]={k:human[k] for k in METRICS}
   rows.append({'item_id':item_id,'status':'human_graded' if ready else 'pending_human_grading','rubric':graded.get(item_id),'total_out_of_8':sum(graded[item_id].values()) if ready else None,'confirmed_overclaims':human['overclaim_flags'] if human else None,'suspected_overclaims':screen(result['prediction']),'latency_ms':result['latency_ms'],'input_tokens':result['input_tokens'],'output_tokens':result['output_tokens'],'estimated_cost_usd':result['estimated_cost_usd']})
  attention=None
  if 'ITEM_04' in items:
   order=[x['camera'] for x in sorted(items['ITEM_04']['prediction']['attention_queue'],key=lambda x:x['rank'])];attention={'reference_provenance':'477 project-defined human reference, not AI Hub ground truth','top1_correct':order[0]==reference[0],'full_order_correct':order==reference,'predicted_camera_order':order}
  increment=None
  if all(x in graded for x in ['ITEM_05','ITEM_06','ITEM_07']):
   totals={x:sum(graded[x].values()) for x in ['ITEM_05','ITEM_06','ITEM_07']};increment={'definition':'AB total - max(A total, B total)','A_total_out_of_8':totals['ITEM_05'],'B_total_out_of_8':totals['ITEM_06'],'AB_total_out_of_8':totals['ITEM_07'],'multi_view_increment':totals['ITEM_07']-max(totals['ITEM_05'],totals['ITEM_06']),'per_metric_increment':{k:graded['ITEM_07'][k]-max(graded['ITEM_05'][k],graded['ITEM_06'][k]) for k in METRICS},'limitation':'One selected incident under matched-total-frame budget; not population improvement'}
  main_ids=['ITEM_01','ITEM_02','ITEM_03','ITEM_04','ITEM_07'];covered=sum(x in graded for x in main_ids);counts={k:{'core_correct_x_of_5':sum(graded[x][k]==2 for x in main_ids if x in graded),'graded_cases':covered,'denominator':5,'status':'complete' if covered==5 else 'incomplete; no missing grades imputed'} for k in METRICS}
  summary['runs'].append({'pipeline':pipeline,'run_id':runid,'items':rows,'main_case_rubric_counts':counts,'attention_ranking':attention,'multi_view_reasoning':increment,'missing_items':[f'ITEM_{i:02d}' for i in range(1,8) if f'ITEM_{i:02d}' not in items]})
 return summary
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('files',nargs='*',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.files:print('No results supplied. No predictions or performance scores generated.');raise SystemExit(0)
 try:
  summary=score_files(a.files)
  if a.output:
   out=a.output.resolve()
   if not out.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be inside results/')
   write(out,summary)
  else:print(json.dumps(summary,ensure_ascii=False,indent=2))
 except Exception as e:print(str(e),file=sys.stderr);raise SystemExit(1)
