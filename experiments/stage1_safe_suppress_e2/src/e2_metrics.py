"""Paired descriptive statistics; missing arms do not become normal observations."""
import math
import statistics
from collections import Counter

from e2_common import ROOT, read


def interval(k,n):
    if not n: return None
    z=1.959963984540054
    den=1+z*z/n; center=(k/n+z*z/(2*n))/den
    half=z*math.sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/den
    return {'wilson_two_sided_95':[max(0,center-half),min(1,center+half)],
        'zero_miss_exact_one_sided_95_upper':1-.05**(1/n) if k==0 else None,
        'unit':'candidate; assumes independent observations, not adjusted for shared scenes/groups'}


def scalar(result, key):
    p=result.get('parsed',{})
    if key=='safe':
        vals=list(p.get('safe_to_suppress',{}).values())
        return min(vals) if vals and all(v is not None for v in vals) else None
    d=p.get('common',{})
    if 'per_camera' in d:
        vals=[x.get(key) for x in d['per_camera'].values()]
        return max(vals) if vals and all(v is not None for v in vals) else None
    return d.get(key)


def distribution(vals):
    vals=[v for v in vals if v is not None]
    return {'n':len(vals),'min':min(vals),'max':max(vals),'mean':statistics.fmean(vals),'median':statistics.median(vals)} if vals else {'n':0}


def review_flag(result):
    common=result.get('parsed',{}).get('common',{})
    if 'per_camera' in common: return any(d['human_review_required'] for d in common['per_camera'].values())
    return common.get('human_review_required')


def evaluate(candidates, results):
    # results indexed by (candidate_id, arm), including failed/not dispatched slots.
    ids=[c['candidate_id'] for c in candidates]
    labels={c['candidate_id']:c['human_gt']['label'] for c in candidates}
    complete_ids=[cid for cid in ids if all(results.get((cid,a),{}).get('status')=='COMPLETE' for a in 'ABCD')]
    settings_mismatch=[]
    for cid in list(complete_ids):
        settings=[results[(cid,a)].get('client_settings',{}) for a in 'ABCD']
        if any(s!=settings[0] for s in settings[1:]):
            complete_ids.remove(cid); settings_mismatch.append(cid)
    report={'status':'EVALUATED' if complete_ids else 'NOT EVALUATED','cohort_size':len(ids),
        'complete_paired_candidates':len(complete_ids),'incomplete_candidates':[cid for cid in ids if cid not in complete_ids],
        'paired_client_settings_mismatch':settings_mismatch,
        'metric_cohort':'complete A/B/C/D pairs only; failures listed separately and counted as escalate in all-candidate operational diagnostic',
        'gt_distribution':dict(Counter(labels.values())),'arms':{},'paired_comparisons':{},'failure_cases':[]}
    cfg=read(ROOT/'configs/experiment.json')
    for arm in 'ABCD':
        slots=[results.get((cid,arm),{'status':'NOT_RUN'}) for cid in ids]
        good=[results[(cid,arm)] for cid in complete_ids]
        stats={'status':'EVALUATED' if good else 'NOT EVALUATED','request_status':dict(Counter(r['status'] for r in slots)),
            'policies':{},'scores':{},'usage':{},'answer_issues':{k:sum(len(r.get('parsed',{}).get(k,[])) for r in slots) for k in ('missing','refused','invalid')}}
        for label in ['CLEAR_NORMAL','HARD_NEGATIVE_NORMAL','ANCHORED_DANGER','AMBIGUOUS']:
            cohort=[cid for cid in complete_ids if labels[cid]==label]
            stats['scores'][label]={key:distribution([scalar(results[(cid,arm)],key) for cid in cohort]) for key in ('p_incident','p_human_review','confidence','safe')}
        for policy in cfg['shadow_policies']:
            if policy.startswith('safe_') and arm in 'AC':
                stats['policies'][policy]={'status':'NOT APPLICABLE (safe question absent)'}; continue
            pstats={}
            for label in ['CLEAR_NORMAL','HARD_NEGATIVE_NORMAL','ANCHORED_DANGER','AMBIGUOUS']:
                cohort=[cid for cid in complete_ids if labels[cid]==label]
                k=sum(bool(results[(cid,arm)].get('shadow_suppression',{}).get(policy)) for cid in cohort)
                pstats[label]={'n':len(cohort),'shadow_suppressed':k,'rate':k/len(cohort) if cohort else None,'confidence_interval':interval(k,len(cohort))}
            suppressed=sum(bool(r.get('shadow_suppression',{}).get(policy)) for r in good)
            pstats['projected_p4_rate_complete_pairs']=(len(good)-suppressed)/len(good) if good else None
            all_supp=sum(r['status']=='COMPLETE' and bool(r.get('shadow_suppression',{}).get(policy)) for r in slots)
            pstats['projected_p4_rate_all_candidates_failures_escalate']=(len(ids)-all_supp)/len(ids) if ids else None
            stats['policies'][policy]=pstats
        for key in ('input_tokens','output_tokens','total_tokens'):
            stats['usage'][key]=distribution([r.get('raw_response',{}).get('usage',{}).get(key) for r in good])
        stats['usage']['usage_cost_usd']=distribution([r.get('usage_cost_usd') for r in good])
        stats['usage']['cache_reused_count']=sum(r.get('cache_reused',False) for r in good)
        stats['usage']['incremental_dispatch_cost_usd']=distribution([r.get('incremental_dispatch_cost_usd') for r in good])
        stats['usage']['api_latency_ms']=distribution([r.get('raw_response',{}).get('timing',{}).get('total_including_retries_ms') for r in good])
        stats['usage']['fresh_dispatch_api_latency_ms']=distribution([r.get('raw_response',{}).get('timing',{}).get('total_including_retries_ms') for r in good if not r.get('cache_reused')])
        stats['usage']['cache_note']='Cached provider usage/cost/timing describe original dispatch; incremental_dispatch_cost is zero for cache hits.'
        stats['usage']['compact_input_tokens_estimated']=distribution([r['request']['compact_input_tokens_estimated']['tokens'] for r in good])
        stats['usage']['feature_bytes']={group:distribution([r['request']['feature_bytes'][group] for r in good if r['request']['feature_bytes']])
            for group in ('coverage_gap_tail','posture_runs_recovery_unknown','detection_tracking_quality','interaction_evidence','selection_omission')}
        inc_safe=[(scalar(r,'p_incident'),scalar(r,'safe')) for r in good if scalar(r,'safe') is not None and scalar(r,'p_incident') is not None]
        stats['incident_safe_agreement']={'n':len(inc_safe),'diagnostic_both_high_05':sum(x>=.5 and y>=.5 for x,y in inc_safe),
            'note':'0.5 midpoint diagnostic only; safe is not incident complement or calibrated safety probability'}
        normal=[scalar(results[(cid,arm)],'p_incident') for cid in complete_ids if labels[cid] in ('CLEAR_NORMAL','HARD_NEGATIVE_NORMAL')]
        danger=[scalar(results[(cid,arm)],'p_incident') for cid in complete_ids if labels[cid]=='ANCHORED_DANGER']
        stats['normal_danger_overlap']={'normal_incident_range':distribution(normal),'danger_incident_range':distribution(danger)}
        for name,group in [('normal',('CLEAR_NORMAL','HARD_NEGATIVE_NORMAL')),('danger',('ANCHORED_DANGER',))]:
            stats['normal_danger_overlap'][name+'_safe_range']=distribution([scalar(results[(cid,arm)],'safe') for cid in complete_ids if labels[cid] in group])
        report['arms'][arm]=stats
    for left,right in [('A','B'),('A','C'),('B','D'),('C','D')]:
        paired=[]
        for cid in complete_ids:
            x,y=results[(cid,left)],results[(cid,right)]
            row={'candidate_id':cid,'gt':labels[cid]}
            for key in ('p_incident','p_human_review','confidence','safe'):
                a,b=scalar(x,key),scalar(y,key); row[key+'_delta']=b-a if a is not None and b is not None else None
            xp=x['parsed']['typed_answers']; yp=y['parsed']['typed_answers']
            common=set(xp)&set(yp)
            row['changed_common_answers']=[k for k in sorted(common) if xp[k]!=yp[k]]
            row['category_changed']=any(xp[k].get('choice')!=yp[k].get('choice') for k in common if k.endswith('incident_category'))
            row['human_review_flag_changed']=review_flag(x)!=review_flag(y)
            row['category_transitions']={k:{'before':xp[k].get('choice'),'after':yp[k].get('choice')}
                for k in sorted(common) if k.endswith('incident_category')}
            row['baseline_suppression_delta']=int(y['shadow_suppression']['baseline_guard'])-int(x['shadow_suppression']['baseline_guard'])
            row['input_tokens_delta']=(y['raw_response']['usage']['input_tokens']-x['raw_response']['usage']['input_tokens'])
            row['cost_delta_usd']=y['usage_cost_usd']-x['usage_cost_usd']
            paired.append(row)
        report['paired_comparisons'][left+'_vs_'+right]={'n':len(paired),'rows':paired,
            'mean_delta':{k:distribution([r[k] for r in paired]) for k in ('p_incident_delta','p_human_review_delta','confidence_delta','safe_delta','baseline_suppression_delta','input_tokens_delta','cost_delta_usd')}}
    interactions=[]
    for cid in complete_ids:
        r={a:results[(cid,a)] for a in 'ABCD'}
        vals=[scalar(r[a],'p_incident') for a in 'ABCD']
        interactions.append({'candidate_id':cid,'incident_state_x_question':(vals[3]-vals[2])-(vals[1]-vals[0]) if all(v is not None for v in vals) else None,
            'baseline_suppression_state_x_question':int(r['D']['shadow_suppression']['baseline_guard'])-int(r['C']['shadow_suppression']['baseline_guard'])-int(r['B']['shadow_suppression']['baseline_guard'])+int(r['A']['shadow_suppression']['baseline_guard'])})
    report['state_x_question_interaction']={'rows':interactions,'incident_difference_in_differences':distribution([r['incident_state_x_question'] for r in interactions])}
    for cid in ids:
        for arm in 'ABCD':
            r=results.get((cid,arm),{})
            inc,safe=scalar(r,'p_incident'),scalar(r,'safe')
            types=[]
            if r.get('status')!='COMPLETE': types.append('INCOMPLETE_ARM')
            if labels[cid]=='ANCHORED_DANGER' and safe is not None and safe>=.95: types.append('DANGER_HIGH_SAFE_SCORE')
            if labels[cid]=='ANCHORED_DANGER' and any(r.get('shadow_suppression',{}).values()): types.append('DANGER_SHADOW_SUPPRESSED')
            if labels[cid] in ('CLEAR_NORMAL','HARD_NEGATIVE_NORMAL') and inc is not None and inc>=.5: types.append('NORMAL_HIGH_INCIDENT')
            if types: report['failure_cases'].append({'candidate_id':cid,'arm':arm,'types':types,'request_hash':r.get('request_hash'),
                'p_incident':inc,'p_safe':safe,'parsed':r.get('parsed'),'evidence':r.get('request',{}).get('compact')})
    return report
