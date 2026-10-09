"""Validate input locks; copy public inputs; isolate evaluator reference; lock before inference."""
import hashlib, shutil, zipfile
from common import *
def main():
    if (RUN/'RUN_LOCK.json').exists(): raise RuntimeError('Run already prepared')
    PUBLIC.mkdir(parents=True,exist_ok=True)
    lock=read(SOURCE/'benchmark.lock.json')
    aliases=read(SOURCE/'input_aliases.json');restored=[]
    for relative,h in lock.items():
        src=(SOURCE/relative).resolve()
        alias=relative;seen=set()
        while not src.exists() and alias in aliases:
            if alias in seen:raise RuntimeError('Alias cycle')
            seen.add(alias);alias=aliases[alias]
            if lock[alias]!=h:raise RuntimeError('Alias hash mismatch')
            src=(SOURCE/alias).resolve()
        if seen:restored.append(relative)
        if not src.is_relative_to(SOURCE.resolve()) or digest(src)!=h: raise RuntimeError('Team input drift '+relative)
        dst=PUBLIC/relative; dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
    for filename in ('README.md','TEAM_CONTRACT.md','scorer.lock.json'):
        shutil.copy2(SOURCE/filename,PUBLIC/filename)
    for src in (SOURCE/'pipeline477').glob('*.py'):
        dst=PUBLIC/'pipeline477'/src.name; dst.parent.mkdir(exist_ok=True); shutil.copy2(src,dst)
    scorer_lock=read(SOURCE/'scorer.lock.json')
    # Preserve all declared scorer dependencies byte-for-byte, with no execution of private labels.
    for relative,h in scorer_lock.items():
        if isinstance(h,str) and len(h)==64:
            src=SOURCE/relative
            if digest(src)!=h: raise RuntimeError('Scorer drift '+relative)
            dst=PUBLIC/relative; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    with zipfile.ZipFile('D:/projects/477_evaluator_reference_v1.zip') as z:
        reference_lock=json.loads(z.read('ground_truth/ai_review_v1/ground_truth.lock.json'))
        for name,h in reference_lock.items():
            if hashlib.sha256(z.read(name)).hexdigest()!=h: raise RuntimeError('Reference lock mismatch')
        target=RUN/'analysis/reference/sources.json'; target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(z.read('ground_truth/ai_review_v1/sources.json'))
        write(RUN/'analysis/reference/verified_lock.json',reference_lock)
    itemlist=read(PUBLIC/'items.json')['items']; work=[]
    for item in itemlist:
        manifest=read(PUBLIC/f"data/frames/{item['item_id']}/manifest.json")
        assert len(manifest['frames'])==64
        for source in item['sources']:
            rows=[r for r in manifest['frames'] if r['source_id']==source['source_id']]
            assert len(rows)==source['frame_count']
            work.append({'id':item['item_id']+'_'+source['source_id'],'item_id':item['item_id'],
                         'source_id':source['source_id'],'frame_count':len(rows),'cv_alias':f'ITEM_{len(work)+1:02d}'})
    assert len(work)==28 and sum(j['frame_count'] for j in work)==768
    policy=ROOT/'experiments/triage_frozen_v1/routing_policy_lock.json'
    assert digest(policy)==read(ROOT/'experiments/triage_frozen_v1/ROUTING_POLICY_SHA256.json')['sha256']
    shutil.copy2(policy,RUN/'routing_policy_lock.json')
    write(RUN/'run_plan.json',{'created_at':now(),'experiment':'frozen_p1_p4_on_team_inputs_v1',
        'identical_aliases_restored_in_working_copy':restored,
        'common_prompt_comparison_eligible':False,'prompt_protocol':'original frozen P1/P4 prompts unchanged; separate experiment',
        'source_execution':'one independent single-camera call per source occurrence; no cross-source tracking',
        'items':12,'source_occurrences':28,'unique_sources':6,'total_frames':768,'jobs':work,
        'sampling':'exact team manifest allocation; per-source count 10..64; no added frames or padding',
        'transport_schema_change':'CV total_frames const follows actual source allocation; other validation unchanged',
        'category_projection':{'no_clear_incident':'normal','possible_fall_or_person_down':'fall_ground_posture',
          'possible_physical_conflict':'physical_conflict','possible_scene_or_boundary_entry':'boundary_crossing',
          'other_safety_relevant':'uncertain','uncertain':'uncertain'},
        'category_limitation':'Frozen taxonomy cannot separately encode gate-entry or loitering; no GT-informed remapping',
        'threshold_refit':False,'reference_quality':'AI-reviewed demo reference, not independent human gold',
        'primary_sources_items':['P001','P002','P003','P004','P005','P006'],
        'repeated_bundles_items':['P007','P008','P009','P010','P011','P012'],
        'api_authorization':'User explicitly requested this additional benchmark evaluation after approving OpenAI frame/CV transmission; no GT transmission'})
    paths=list((RUN/'scripts').glob('*.py'))+[RUN/'run_plan.json',RUN/'routing_policy_lock.json']
    paths+=list(PUBLIC.rglob('*.json'))+list((PUBLIC/'pipeline477').glob('*.py'))
    paths+=list((PUBLIC/'prompts').glob('*'))+list(PUBLIC.rglob('*.png'))
    # Pin shared CV weights/code/config against the already frozen original harness.
    old=read(ROOT/'experiments/triage_frozen_v1/HARNESS_LOCK.json')['sha256']
    sha={p.relative_to(ROOT).as_posix():digest(p) for p in paths if p.is_file()}
    sha.update({p:h for p,h in old.items() if p.startswith('experiments/p0_cv_only/')})
    write(RUN/'RUN_LOCK.json',{'created_at':now(),'sha256':sha,'reference_sha256':digest(target),
                              'policy_sha256':digest(RUN/'routing_policy_lock.json')})
    write(RUN/'workflow_status.json',{'state':'PREPARED','updated_at':now(),'expected_per_model':28})
    print('Prepared: 12 items / 28 independent source jobs / 768 exact frames; inputs and reference verified')
if __name__=='__main__':main()
