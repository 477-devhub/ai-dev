from benchmark_common import *
import re,ast
from jsonschema import Draft202012Validator
from referencing import Registry,Resource

def check(root=ROOT):
 lock=read(root/'BENCHMARK_LOCK.json');errors=[]
 def fail(message):errors.append(message)
 if lock.get('benchmark_version')!='477-reasoning-v1' or lock.get('frozen') is not True:fail('Benchmark lock not frozen v1')
 for rel,entry in lock['media'].items():
  try:
   p=safe(root,rel)
   if not p.is_file():fail('Missing media: '+rel);continue
   if sha(p)!=entry['sha256']:fail('SHA256 mismatch: '+rel)
   meta=probe(p)
   if abs(meta['duration']-entry['duration'])>lock['duration_tolerance_sec']:fail('Duration mismatch: '+rel)
   if any(meta[k]!=entry[k] for k in ['frame_count','width','height','codec','pixel_format','audio_streams']) or abs(meta['fps']-30)>.001:fail('Media metadata mismatch: '+rel)
   if any(t in str(meta['format_tags']).lower() for t in ['swoon','fight','trespass','ph_e2069']):fail('Source label in MP4 tags: '+rel)
  except Exception as e:fail('Media check failed '+rel+': '+str(e))
 for rel,h in lock['artifacts_sha256'].items():
  try:
   p=safe(root,rel)
   if not p.is_file():fail('Missing frozen artifact: '+rel)
   elif sha(p)!=h:fail('Artifact SHA256 mismatch: '+rel)
  except Exception as e:fail('Artifact check '+rel+': '+str(e))
 for a,b in lock['identical_content_pairs']:
  if sha(root/a)!=sha(root/b):fail('Reused media byte mismatch: '+a)
 public=read(root/'public_manifest.json');scenarios=read(root/'model_input/scenarios.json')
 if set(public)!={'benchmark_version','media'}:fail('Unexpected public manifest keys')
 if set(scenarios)!={'benchmark_version','protocol','items'}:fail('Unexpected scenario keys')
 forbidden=r'swoon|fight|trespass|falldown|punching|climbwall|AI\s*Hub\s*answer|caption|\bCoT\b|S14|T06|T03|F01|MV05|ph_e2069|private_ground_truth|\.xml|\.zip|annotation|expected_ranking|reference_priority'
 for rel in ['public_manifest.json','model_input/scenarios.json','model_input/prompt_v1.txt','schemas/prediction.schema.json']:
  p=root/rel;content=p.read_text(encoding='utf-8-sig')
  if p.suffix=='.json':content=json.dumps(json.loads(content),ensure_ascii=False)
  if re.search(forbidden,content,re.I):fail('Annotation/source leakage in '+rel)
 for aid,m in public['media'].items():
  if not re.fullmatch(r'ASSET_\d{2}',aid) or set(m)!={'path','sha256','duration','fps','width','height','frame_count'}:fail('Unexpected public asset keys')
  if not re.fullmatch(r'media/asset_\d{2}\.mp4',m['path']):fail('Non-opaque media locator')
  if m['path'] not in lock['media'] or m['sha256']!=lock['media'][m['path']]['sha256']:fail('Public asset hash mismatch')
  if abs(m['duration']-lock['media'][m['path']]['duration'])>.001 or any(m[k]!=lock['media'][m['path']][k] for k in ['fps','width','height','frame_count']):fail('Public asset metadata mismatch')
 if [x['item_id'] for x in scenarios['items']]!=[f'ITEM_{i:02d}' for i in range(1,8)]:fail('Seven frozen conditions missing/changed')
 from load_model_input import load_item
 from validate_prediction import schemas
 for item in scenarios['items']:
  if set(item)!={'item_id','task','cameras'}:fail('Unexpected item fields')
  for camera in item['cameras']:
   if set(camera)!={'camera','asset'} or camera['asset'] not in public['media']:fail('Unexpected camera fields')
  loaded=load_item(item['item_id'])
  if sum(len(h['frame_numbers']) for h in loaded['media_handles_private_to_harness'])!=64:fail('Frozen total-frame budget mismatch')
  for h in loaded['media_handles_private_to_harness']:
   if not re.fullmatch(r'CAM_0[123]\.mp4',h['upload_name']):fail('Non-generic upload name')
 # Structural separation: loader only has explicit public artifacts/media, with no private import/read path.
 loader=(root/'scripts/load_model_input.py').read_text(encoding='utf-8-sig')
 if re.search(r'private_ground_truth|BENCHMARK_LOCK|source_candidate|source_annotation',loader):fail('Loader reads private material')
 tree=ast.parse(loader)
 allowed={'json','math','hashlib','sys','pathlib','argparse','subprocess'}
 for node in ast.walk(tree):
  if isinstance(node,ast.Import) and any(a.name not in allowed for a in node.names):fail('Unapproved loader import')
  if isinstance(node,ast.ImportFrom) and node.module not in allowed:fail('Unapproved loader import')
 for p in (root/'model_input').rglob('*'):
  if p.is_file() and p.name not in {'scenarios.json','prompt_v1.txt'}:fail('Unexpected model_input file: '+p.name)
 if lock['private_files_model_input_policy']!='never loaded by model-input loader':fail('Private separation policy missing')
 p,r,registry=schemas();Draft202012Validator.check_schema(p);Draft202012Validator.check_schema(r)
 Draft202012Validator(r,registry=registry)
 if errors:raise ValueError('\n'.join(errors))
 return {'annotation_leakage':'PASS','missing_files':0,'hash_mismatch':0,'schema_validation':'PASS','media_files':len(lock['media']),'conditions':7,'frozen':True}
if __name__=='__main__':
 try:print(json.dumps(check(),ensure_ascii=False))
 except Exception as e:print('Validation FAILED: '+str(e),file=sys.stderr);raise SystemExit(1)
