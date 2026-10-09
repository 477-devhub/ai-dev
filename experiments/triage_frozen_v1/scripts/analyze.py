"""Evaluator-only analysis: calibration first, immutable policy, then exactly one test report."""
import argparse
from collections import Counter
from common import BENCH, RUN, PLAN, LOCK, read, write, digest, now, verify_frozen

def predictions(model,ids):
    return {item:read(RUN/model/'results'/f'{item}.json') for item in ids}

def can_suppress(result, threshold):
    d = result['decision']
    return bool(threshold > 0 and d.get('p_incident') is not None and d['p_incident'] <= threshold and
                not d.get('human_review_required',True) and not d.get('refused_questions') and
                d.get('category') == 'no_clear_incident' and (d.get('confidence') or 0) >= 0.90)

def surface_p4(result):
    d = result['decision']
    # Uncertainty/refusal requires operator attention; no unsafe forced NORMAL.
    return bool(d.get('is_incident') or d.get('human_review_required') or d.get('refused_questions'))

def evaluate(ids,gt,p1,p4,threshold):
    suppressed = [item for item in ids if can_suppress(p1[item],threshold)]
    normal = [item for item in ids if gt[item]['reference_binary']=='NORMAL']
    danger = [item for item in ids if gt[item]['reference_binary']=='DANGER']
    final = {item:False if item in suppressed else surface_p4(p4[item]) for item in ids}
    return {'samples':len(ids),'normal':len(normal),'danger':len(danger),
            'stage1_normal_suppressed':len(suppressed),
            'stage1_danger_suppressions':sum(item in suppressed for item in danger),
            'stage1_correct_normal_suppressions':sum(item in suppressed for item in normal),
            'routed_to_p4':len(ids)-len(suppressed),
            'final_danger_missed':sum(not final[item] for item in danger),
            'final_normal_surfaced':sum(final[item] for item in normal),
            'final_operator_queue':sum(final.values()),
            'normal_suppression_rate':sum(not final[item] for item in normal)/len(normal) if normal else None,
            'danger_surface_recall':sum(final[item] for item in danger)/len(danger) if danger else None}

def calibrate():
    lock = RUN/'routing_policy_lock.json'
    if lock.exists():
        raise RuntimeError('Routing policy is already locked; no threshold refitting allowed')
    plan = read(PLAN)
    ids = plan['calibration_ids']
    p1,p4 = predictions('p1',ids), predictions('p4',ids)
    # No test output files or test labels are read by this operation.
    gt_path = RUN/'analysis/calibration_gt.json'
    if digest(gt_path) != read(LOCK)['evaluator_gt_sha256']['calibration']:
        raise RuntimeError('Calibration GT drift')
    gt = read(gt_path)
    candidates = []
    for tn in plan['normal_threshold_grid']:
        metrics = evaluate(ids,gt,p1,p4,tn)
        candidates.append({'policy':'all_to_p4' if tn==0 else 'conservative_normal_then_p4','T_normal':tn,**metrics})
    safe = [c for c in candidates if c['stage1_danger_suppressions']==0]
    chosen = min(safe,key=lambda c:(-c['stage1_correct_normal_suppressions'],c['T_normal']))
    write(RUN/'analysis/calibration_candidates.json',candidates)
    write(lock,{'locked_at':now(),'selection_split':'calibration','calibration_ids':ids,
        'policy':chosen['policy'],'T_normal':chosen['T_normal'],'T_danger':plan['danger_threshold_fixed'],
        'direct_danger_branch_enabled':False,'danger_threshold_range':plan['danger_threshold_conservative_range'],
        'T_danger_fine_optimization':False,'calibration_dangers':3,
        'normal_guards':plan['normal_guards'],'calibration_metrics':chosen,
        'limitation':'Zero observed misses among 3 calibration dangers is not a safety guarantee; T_danger is not optimized',
        'post_test_retuning':False,
        'calibration_result_hashes':{f'{model}/{item}':digest(RUN/model/'results'/f'{item}.json') for model in ['p1','p4'] for item in ids},
        'run_plan_sha256':digest(PLAN)})
    write(RUN/'ROUTING_POLICY_SHA256.json',{'sha256':digest(lock),'locked_at':now()})
    print('Routing policy locked using calibration only:',chosen['policy'],'T_normal',chosen['T_normal'],'T_danger fixed, branch disabled')

def test():
    output = RUN/'analysis/final_test_evaluation.json'
    if output.exists():
        raise RuntimeError('Final test evaluation already exists; no repeat evaluation or post-test retuning')
    policy_path = RUN/'routing_policy_lock.json'
    policy = read(policy_path)
    plan = read(PLAN)
    if policy['run_plan_sha256'] != digest(PLAN) or policy['selection_split']!='calibration':
        raise RuntimeError('Calibration policy lock integrity failure')
    drift = [key for key,h in policy['calibration_result_hashes'].items()
             if digest(RUN/key.split('/')[0]/'results'/f"{key.split('/')[1]}.json")!=h]
    if drift:
        raise RuntimeError('Calibration outputs changed since policy lock')
    ids = plan['test_ids']
    p1,p4 = predictions('p1',ids),predictions('p4',ids)
    gt_path = RUN/'analysis/test_gt.json'
    if digest(gt_path) != read(LOCK)['evaluator_gt_sha256']['test']:
        raise RuntimeError('Test GT drift')
    gt = read(gt_path)
    metrics = evaluate(ids,gt,p1,p4,policy['T_normal'])
    write(output,{'evaluated_at':now(),'evaluation_number':1,'routing_policy_sha256':digest(policy_path),
        'policy':policy,'metrics':metrics,'test_result_hashes':{f'{model}/{item}':digest(RUN/model/'results'/f'{item}.json') for model in ['p1','p4'] for item in ids},
        'post_test_retuning':False})
    write(RUN/'RESULTS_LOCK.json',{'locked_at':now(),'final_test_report_sha256':digest(output),
        'routing_policy_sha256':digest(policy_path),'policy':'Final 22-item test is complete; no threshold changes or new inference runs'})
    (RUN/'analysis/cascade_report.md').write_text('# Frozen triage cascade analysis\n\n'+
        f"Calibration-selected policy: {policy['policy']}; T_normal={policy['T_normal']}; direct-danger branch disabled.\n\n"+
        'Final test metrics (one evaluation only):\n\n'+ '\n'.join(f'- {k}: {v}' for k,v in metrics.items())+
        '\n\nCalibration had 3 danger examples only; no T_danger fine optimization or post-test retuning.\n',encoding='utf-8')
    print('Final test evaluation complete (22 items):',metrics)

if __name__=='__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage',choices=['calibration','test'],required=True)
    args=ap.parse_args()
    verify_frozen()
    calibrate() if args.stage=='calibration' else test()
