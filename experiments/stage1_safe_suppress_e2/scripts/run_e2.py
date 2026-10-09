"""E2 offline preparation / guarded pilot / paired analysis. No P4 imports."""
import argparse
import copy
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from e2_common import ROOT, PROJECT, read, write, digest, protected_hashes
from e2_dataset import repository_audit, validate_manifest
from e2_runner import Store, PilotClient, plan
from e2_metrics import evaluate


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase',choices=['audit','prepare','pilot','analyze'])
    p.add_argument('--manifest',type=Path,default=ROOT/'data/development_manifest.json')
    p.add_argument('--run',default='pilot_v1')
    p.add_argument('--max-candidates',type=int,default=2)
    args=p.parse_args()
    if Path(args.run).name!=args.run: p.error('run must be a directory name')
    if args.max_candidates<1: p.error('max-candidates must be positive')
    if args.phase=='audit': print(repository_audit()); return
    cfg=read(ROOT/'configs/experiment.json'); manifest=read(args.manifest)
    from jsonschema import Draft202012Validator
    Draft202012Validator(read(ROOT/'data/development_manifest.schema.json')).validate(manifest)
    audit=validate_manifest(manifest); eligible=copy.deepcopy(audit['eligible'][:args.max_candidates])
    for c in eligible:
        path=Path(c['canonical_path']); c['canonical_path']=str(path if path.is_absolute() else PROJECT/path)
    folder=ROOT/'results'/args.run
    if args.phase=='analyze':
        locked=read(folder/'plan.json')
        if locked['manifest_hash']!=digest(manifest): raise ValueError('manifest changed')
        records={}
        for slot in locked['slots']:
            path=folder/'slots'/f"{digest([slot['candidate_id'],slot['arm']])}.json"
            records[(slot['candidate_id'],slot['arm'])]=read(path) if path.is_file() else {'status':'NOT_RUN'}
        write(folder/'analysis.json',evaluate(locked['candidates'],records)); print('analysis written'); return
    tasks, budget=plan(eligible,cfg)
    data={'manifest_hash':digest(manifest),'registry_hash':audit['registry_hash'],'candidates':eligible,
        'budget_plan':budget,'excluded':audit['exclusions'],'protected_hashes':protected_hashes(),
        'slots':[{'candidate_id':c['candidate_id'],'arm':a,'request_hash':prep['request_hash']} for c,a,prep in tasks]}
    if (folder/'plan.json').exists():
        old=read(folder/'plan.json')
        if old!=data: raise ValueError('plan changed: use new run id')
    else: write(folder/'plan.json',data)
    for c,a,prep in tasks:
        write(folder/'prepared'/f"{digest([c['candidate_id'],a])}.json",prep)
    if args.phase=='prepare': print(budget); return
    if not eligible:
        write(folder/'pilot_status.json',{'status':'NOT EVALUATED','reason':'NO_ELIGIBLE_INDEPENDENT_HUMAN_GT','api_calls':0})
        print('NOT EVALUATED: no eligible independent Human GT. API calls=0'); return
    if budget['reserved_maximum_cost_usd']>cfg['budget_usd']: raise ValueError('planned reservation exceeds budget; reduce max-candidates')
    # Instantiate client only after data, hashes, cost and plan have been validated.
    client=PilotClient(); write(folder/'client_settings.json',client.metadata)
    store=Store(folder,cfg,'pilot')
    execution=[]
    for c,a,prep in tasks:
        result=store.execute(c['candidate_id'],a,prep,client)
        execution.append({'candidate_id':c['candidate_id'],'arm':a,'request_hash':prep['request_hash'],'status':result['status']})
        write(folder/'execution_status.json',execution)
        print(c['candidate_id'],a,result['status'])
        if result['status'] in ('BUDGET_STOP','INDETERMINATE'): break
    records={}
    for c,a,prep in tasks:
        path=folder/'slots'/f"{digest([c['candidate_id'],a])}.json"
        records[(c['candidate_id'],a)]=read(path) if path.is_file() else {'status':'NOT_RUN'}
    write(folder/'analysis.json',evaluate(eligible,records))


if __name__=='__main__': main()
