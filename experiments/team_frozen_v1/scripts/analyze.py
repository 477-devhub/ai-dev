"""Read reference only after inference, with fixed taxonomy projection and fixed routing."""
import csv
from collections import Counter
from common import *
AXES=('severity','imminence','exposure','persistence')
def suppress(d,policy):
    return bool(policy['T_normal']>0 and d.get('p_incident') is not None and d['p_incident']<=policy['T_normal']
        and not d.get('human_review_required',True) and not d.get('refused_questions')
        and d.get('category')=='no_clear_incident' and (d.get('confidence') or 0)>=0.90)
def assessment(r,manifest,projection):
    d=r['decision']; evidence=[]
    if r['model']=='p4':
        source_frames=[f for f in manifest['frames'] if f['source_id']==r['source_id']]
        refs={f'F{i+1:03d}':f['frame_id'] for i,f in enumerate(source_frames)}
        evidence=[refs[e['frame_ref']] for e in r['visual']['single']['evidence']]
    # P1 provides observation summaries, not frame evidence: never manufacture citations.
    return {'source_id':r['source_id'],'event_type':projection.get(d.get('category'),'uncertain'),
        'event_confidence':d.get('category_confidence') or 0,
        'risk_axes':{k:None if k in d.get('refused_questions',[]) else d['risk'][k] for k in AXES},
        'evidence_refs':list(dict.fromkeys(evidence)),'needs_human_review':d['human_review_required'],
        'uncertainty_reason':'; '.join(d.get('refused_questions',[])) or ('Model uncertainty' if d['human_review_required'] else None)}
def main():
    verify();output=RUN/'analysis/summary.json'
    if output.exists():raise RuntimeError('Evaluation already complete; no overwrite or retuning')
    lock=read(RUN/'RUN_LOCK.json');ref=RUN/'analysis/reference/sources.json'
    assert digest(ref)==lock['reference_sha256']
    plan=read(RUN/'run_plan.json');policy=read(RUN/'routing_policy_lock.json');assert digest(RUN/'routing_policy_lock.json')==lock['policy_sha256']
    sys.path.insert(0,str(PUBLIC));from pipeline477.metrics import evaluate_item,validate_ground_truth
    gt=read(ref);validation=validate_ground_truth(gt,read(PUBLIC/'data/sources.json'));assert validation['valid'],validation
    results={m:{j['id']:read(RUN/m/'results'/f"{j['id']}.json") for j in jobs()} for m in ('p1','p4')}
    for m in results:
        for j in jobs():
            a=read(RUN/m/'attempts'/f"{j['id']}.json")
            assert a['status']=='COMPLETE' and a['result_sha256']==digest(RUN/m/'results'/f"{j['id']}.json")
    per_item=[];per_source=[];routes=[]
    skipped={'status':'skipped','executed':False,'output':None}
    for item in read(PUBLIC/'items.json')['items']:
        manifest=read(PUBLIC/f"data/frames/{item['item_id']}/manifest.json")
        manifest['output_schema']=read(PUBLIC/'schemas/vlm_output.schema.json')
        rr={m:[results[m][item['item_id']+'_'+s['source_id']] for s in item['sources']] for m in results}
        adapted={m:[assessment(r,manifest,plan['category_projection']) for r in rr[m]] for m in rr}
        # Simulation reuses independently collected outputs. Actual P4 calls are always 28.
        cascade=[];clef=[]
        for index,source in enumerate(item['sources']):
            sid=source['source_id'];p1=rr['p1'][index];p4=rr['p4'][index];blocked=suppress(p1['decision'],policy)
            route={'source_id':sid,'invoke_vlm':not blocked};clef.append(route)
            routes.append({'item_id':item['item_id'],**route,'simulation_only':True})
            cascade.append(adapted['p1'][index] if blocked else adapted['p4'][index])
        for model,entries in [*adapted.items(),('cascade',cascade)]:
            record={'status':'ok','executed':True,'model':model,'output':{'assessments':entries},'active_sources':manifest['sources']}
            item_gt={sid:gt[sid] for sid in manifest['sources'] if sid in gt}
            metrics=evaluate_item(manifest,item_gt,{'yolo':skipped,'clef':skipped,'vlm':record})
            metrics['clef']['used']=False
            metrics['yolo']['used']=False
            for key in ('true_positives','false_positives','false_negatives','precision','recall','map50'):
                metrics['yolo'][key]=None
            metrics['yolo']['per_class']={}
            write(RUN/'submissions'/model/f"{item['item_id']}.json",{'protocol':'separate frozen-prompt experiment','vlm':record,'metrics':metrics})
            rows=metrics['vlm']['per_source'];reviewed=[r for r in rows.values() if r['expected_event_type'] is not None]
            correct=sum(r['semantic_correct'] is True for r in reviewed)
            per_item.append({'model':model,'item_id':item['item_id'],'sources':len(rows),'reviewed':len(reviewed),
                'correct':correct,'accuracy':correct/len(reviewed) if reviewed else None,'all_sources_correct':all(r['semantic_correct'] is True for r in reviewed),
                'output_format_valid':metrics['vlm']['output_format_valid'],'input_reference_valid':metrics['vlm']['input_reference_valid']})
            for sid,r in rows.items():per_source.append({'model':model,'item_id':item['item_id'],'source_id':sid,**r})
    summary={'completed_at':now(),'experiment':plan['experiment'],'reference_quality':plan['reference_quality'],
        'common_prompt_comparison_eligible':False,'threshold_refit':False,'routing_policy_sha256':lock['policy_sha256'],
        'human_labels_generated':False,'reference_sent_to_api':False,'unique_sources':6,'repeated_source_occurrences':28,
        'model_calls':{m:len(results[m]) for m in results},'models':{}}
    for model in ('p1','p4','cascade'):
        summary['models'][model]={}
        for group,identifiers in [('single_source_primary',plan['primary_sources_items']),('repeated_bundles',plan['repeated_bundles_items']),('all_items_descriptive',[i['item_id'] for i in read(PUBLIC/'items.json')['items']])]:
            rows=[r for r in per_source if r['model']==model and r['item_id'] in identifiers and r['expected_event_type'] is not None]
            items=[r for r in per_item if r['model']==model and r['item_id'] in identifiers]
            summary['models'][model][group]={'correct':sum(r['semantic_correct'] is True for r in rows),'denominator':len(rows),
                'accuracy':sum(r['semantic_correct'] is True for r in rows)/len(rows),'all_sources_correct_items':sum(r['all_sources_correct'] for r in items),'items':len(items),
                'confusion':[{'expected':a,'predicted':b,'count':n} for (a,b),n in Counter((r['expected_event_type'],r['predicted_event_type']) for r in rows).items()]}
    summary['execution']={m:{'success':len(results[m]),'retry_count':sum(r['retry_count'] or 0 for r in results[m].values()),
        'api_error_fallback_count':0,'refusal_jobs':sum(bool(r['decision']['refused_questions']) for r in results[m].values()),
        'estimated_api_cost_usd':sum(r['estimated_api_cost_usd'] for r in results[m].values()) if all(r['estimated_api_cost_usd'] is not None for r in results[m].values()) else None,
        'measured_full_harness_ms_sum':sum(r['full_harness_ms'] for r in results[m].values())} for m in results}
    summary['cascade_simulation']={'would_route_to_p4':sum(r['invoke_vlm'] for r in routes),'would_suppress':sum(not r['invoke_vlm'] for r in routes),
        'actual_p4_calls':28,'measured_api_call_savings':None,'note':'Offline replay; latency and savings not measured as a live cascade'}
    write(RUN/'analysis/routes.json',routes);write(output,summary)
    for filename,rows in [('per_item.csv',per_item),('per_source.csv',per_source)]:
        with (RUN/'analysis'/filename).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    report=['# Team benchmark: frozen P1/P4 separate experiment','','AI-reviewed demo reference; not human gold. Six unique videos reused across 12 items.','',
        'Original frozen prompts/models/adapters maintained. Team common prompt was not used: not eligible for the common-prompt leaderboard.',
        'Each source is run independently using exactly its allocated frames. No synchronization/identity assumptions. No threshold refit.',
        'Frozen taxonomy cannot separately encode gate entry or loitering. Fixed projection was locked before inference.','',
        '| Model | Six single-source primary | All 28 occurrences (descriptive only) |','|---|---:|---:|']
    for m,v in summary['models'].items():
        a=v['single_source_primary'];b=v['all_items_descriptive'];report.append(f"| {m} | {a['correct']}/{a['denominator']} ({a['accuracy']:.1%}) | {b['correct']}/{b['denominator']} ({b['accuracy']:.1%}) |")
    report+=['','## Execution',json.dumps(summary['execution'],ensure_ascii=False,indent=2),'',
        'Cascade is an offline replay of the prior locked policy; P4 actually executed all 28 source jobs. No measured routing savings are claimed.',
        'P1 has no frame-specific evidence references; none were fabricated. Object detection scores were not measured in this run.',
        'No normal controls: normal false-alarm rate, unnecessary-call rate and routing savings effectiveness are unmeasurable.',
        'Prior human-GT final Test outputs and thresholds remain unchanged. No human labels were generated.']
    (RUN/'analysis/report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    write(RUN/'RESULTS_LOCK.json',{'completed_at':now(),'summary_sha256':digest(output),'policy_sha256':lock['policy_sha256'],
        'result_hashes':{m+'/'+j['id']:digest(RUN/m/'results'/f"{j['id']}.json") for m in results for j in jobs()}})
    print('Evaluation complete',flush=True)
if __name__=='__main__':main()
