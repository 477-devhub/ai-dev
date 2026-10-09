"""Evaluator-side preparation. Locks harness and conservative search plan before predictions."""
from common import ROOT, BENCH, RUN, PLAN, LOCK, read, write, digest, now

def main():
    if LOCK.exists():
        raise SystemExit('Harness already locked; refusing to replace protocol')
    benchmark_lock = read(BENCH/'BENCHMARK_LOCK.json')
    gt = read(BENCH/'private_ground_truth/triage_labels.json')['primary']
    calibration = sorted(r['candidate_id'] for r in gt if r['split'] == 'calibration')
    test = sorted(r['candidate_id'] for r in gt if r['split'] == 'test')
    assert (len(calibration),len(test)) == (15,22)
    # Evaluator files are physically split; calibration analysis never reads test GT.
    write(RUN/'analysis/calibration_gt.json',{r['candidate_id']:r for r in gt if r['split']=='calibration'})
    write(RUN/'analysis/test_gt.json',{r['candidate_id']:r for r in gt if r['split']=='test'})
    write(PLAN, {'benchmark_version':'477-triage-normal-v1','calibration_ids':calibration,'test_ids':test,
        'benchmark_lock_sha256':digest(BENCH/'BENCHMARK_LOCK.json'),
        'run_policy':'One frozen P1 and one frozen P4 inference per primary item; resume by reusing completed outputs',
        'test_gate':'Routing policy must be calibrated and locked before any test inference/evaluation',
        'challenge':'Not executed in this primary run; excluded from threshold fitting and primary denominator',
        'cv_aliases':{r['candidate_id']:f'ITEM_{index:02d}' for index,r in enumerate(sorted(gt,key=lambda r:r['candidate_id']),1)},
        'normal_threshold_grid':[0.0,0.01,0.025,0.05],
        'danger_threshold_conservative_range':[0.90,1.0], 'danger_threshold_fixed':1.0,
        'direct_danger_branch':'Disabled: high P1 scores go to P4; no fitting on three calibration dangers',
        'candidate_policies':['all_to_p4','conservative_normal_then_p4'],
        'normal_guards':'No refusal, P1 human_review_required=false, category=no_clear_incident, confidence>=0.90',
        'selection_rule':'Among calibration candidates with zero observed danger suppressions, maximize correctly suppressed normals; ties prefer lower threshold then all_to_p4',
        'failure_policy':'Systemic inference failure stops the batch; failed outputs are never replaced with fabricated predictions',
        'post_test_retuning':False,'created_at':now()})
    files = [PLAN, BENCH/'BENCHMARK_LOCK.json', BENCH/'public_manifest.json',
             BENCH/'manifests/evaluation_protocol.json'] + list((RUN/'scripts').glob('*.py'))
    for name, filename in [('p1_decisions','p1_freeze.json'),('p4_gpt61_sol_vision','p4_freeze.json'),
                           ('common_adapter_v2','common_adapter_v2_freeze.json')]:
        files.append(ROOT/'experiments'/name/'freeze'/filename)
    cvroot = ROOT/'experiments/p0_cv_only'
    files += list((cvroot/'src').glob('*.py')) + [cvroot/'configs/cv_state_v1.yaml',
              cvroot/'schemas/canonical_cv_state.schema.json',cvroot/'models/yolo26n-pose.pt']
    write(LOCK, {'locked_at':now(),'benchmark_lock_sha256':digest(BENCH/'BENCHMARK_LOCK.json'),
        'policy':'Dataset transport/schema harness only; frozen P1/P4 prompts, models and adapters are unchanged',
        'frame_protocol':'64 native-resolution canonical frames; timestamps from frozen schedule; lossless P4 WebP unchanged',
        'result_schema':'New triage harness envelope; original reasoning-v1 result enum cannot represent 37 TRIAGE IDs',
        'evaluator_gt_sha256':{s:digest(RUN/'analysis'/f'{s}_gt.json') for s in ('calibration','test')},
        'sha256':{str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in files}})
    print('Prepared and locked calibration 15 / test 22 execution plan. No inference performed.')

if __name__ == '__main__':
    main()
