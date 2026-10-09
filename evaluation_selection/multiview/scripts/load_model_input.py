"""Offline preparation only; never reads private annotations or calls APIs."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ALLOWED={'cam_a_video','cam_b_video','conditions','fixed_general_prompt','media_policy'}
def prepare(pair_id,condition):
 rows=json.loads((ROOT/'model_input_only.json').read_text(encoding='utf-8'))
 row=next(r for r in rows if r['pair_id']==pair_id)
 assert set(row)=={'pair_id','model_input'}
 inp=row['model_input'];assert set(inp)==ALLOWED
 assert condition in {'single_a','single_b','multi_ab'}
 return {'prompt':inp['fixed_general_prompt'],'media':[{'display_label':'CAM A' if c=='cam_a' else 'CAM B','local_path':inp[c+'_video']} for c in inp['conditions'][condition]]}
if __name__=='__main__':
 import argparse,sys
 sys.stdout.reconfigure(encoding='utf-8')
 p=argparse.ArgumentParser();p.add_argument('pair_id');p.add_argument('condition',choices=['single_a','single_b','multi_ab']);a=p.parse_args();print(json.dumps(prepare(a.pair_id,a.condition),ensure_ascii=False,indent=2))
