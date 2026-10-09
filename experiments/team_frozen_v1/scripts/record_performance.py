"""Supplement completed scores with fixed-policy routing replay and execution provenance.

No model calls, no fitted thresholds, no changes to the completed score summary.
"""
import statistics
from common import *
from analyze import suppress
def main():
    verify()
    result_lock=read(RUN/'RESULTS_LOCK.json')
    assert digest(RUN/'analysis/summary.json')==result_lock['summary_sha256']
    target=RUN/'analysis/performance_record.md'
    if target.exists():raise RuntimeError('Performance record already exists')
    summary=read(RUN/'analysis/summary.json');policy=read(RUN/'routing_policy_lock.json')
    ref=RUN/'analysis/reference/sources.json'
    assert digest(ref)==read(RUN/'RUN_LOCK.json')['reference_sha256']
    gt=read(ref);rows=[];execution={}
    for j in jobs():
        p1=read(RUN/'p1/results'/f"{j['id']}.json");p4=read(RUN/'p4/results'/f"{j['id']}.json")
        for model in ('p1','p4'):
            assert digest(RUN/model/'results'/f"{j['id']}.json")==result_lock['result_hashes'][model+'/'+j['id']]
        blocked=suppress(p1['decision'],policy);d=p4['decision']
        reference=gt[j['source_id']].get('clef') or {}
        required=reference.get('invoke_vlm') if reference.get('reviewed') is True else None
        rows.append({'item_id':j['item_id'],'source_id':j['source_id'],'would_invoke_p4':not blocked,
            'reference_requires_vlm':required,'required_call_would_be_missed':required is True and blocked,
            'final_operator_surface':False if blocked else bool(d['is_incident'] or d['human_review_required'] or d['refused_questions']),
            'offline_replay':True})
    for model in ('p1','p4'):
        rr=[read(RUN/model/'results'/f"{j['id']}.json") for j in jobs()]
        api=[r['api_timing']['total_including_retries_ms']/1000 for r in rr]
        execution[model]={'successful_requests':len(rr),'successful_run_retries':sum(r['retry_count'] or 0 for r in rr),
            'returned_models':sorted({r['returned_model'] for r in rr}),
            'api_latency_median_sec':statistics.median(api),'api_latency_sum_sec':sum(api),
            'estimated_api_cost_usd_at_frozen_pricing':summary['execution'][model]['estimated_api_cost_usd'],
            'cost_basis':'actual provider token usage times frozen historical pricing; not invoice actual',
            'latency_basis':'provider request path including retries; excludes CV/encoding/waiting; not live-cascade end-to-end latency'}
    plan=read(RUN/'run_plan.json');routing={}
    for group,ids in [('single_source_primary',plan['primary_sources_items']),('all_occurrences',[f'P{i:03d}' for i in range(1,13)])]:
        rr=[r for r in rows if r['item_id'] in ids]
        routing[group]={'occurrences':len(rr),'would_invoke_p4':sum(r['would_invoke_p4'] for r in rr),
            'would_suppress':sum(not r['would_invoke_p4'] for r in rr),
            'reviewed_required_calls':sum(r['reference_requires_vlm'] is True for r in rr),
            'required_calls_would_be_missed':sum(r['required_call_would_be_missed'] for r in rr),
            'final_operator_queue':sum(r['final_operator_surface'] for r in rr),
            'normal_false_alarm_rate':None,'unnecessary_call_rate':None,'measured_live_cascade_savings':None}
    detail={'created_at':now(),'routing_policy_sha256':digest(RUN/'routing_policy_lock.json'),'threshold_refit':False,
        'routing_replay':routing,'execution':execution,'rows':rows,
        'initial_connection_failure':{'archived_job':'P001_SRC01','transport_attempts':3,'retry_count':2,'received_http_response':False,
            'generated_prediction':False,'archive':'transport_failure_01','successful_evaluation_restarted_with_approved_network':True},
        'api_failure_fallback_predictions':0,'human_labels_generated':False}
    write(RUN/'analysis/routing_execution_record.json',detail)
    text=(RUN/'analysis/report.md').read_text(encoding='utf-8')
    text+='\n## Routing replay against reviewed call-need reference\n\n'
    text+='| Group | Would invoke P4 | Required calls missed | Final operator queue |\n|---|---:|---:|---:|\n'
    for name,r in routing.items():
        text+=f"| {name} | {r['would_invoke_p4']}/{r['occurrences']} | {r['required_calls_would_be_missed']}/{r['reviewed_required_calls']} | {r['final_operator_queue']} |\n"
    text+='\nCall-need reference is not a binary danger/normal label. Operator queue size is a count, not a human-GT recall score.\n'
    text+='\n## API execution and cost\n\n| Model | Successful requests | Median API seconds | Estimated USD |\n|---|---:|---:|---:|\n'
    for model,r in execution.items():
        cost=r['estimated_api_cost_usd_at_frozen_pricing'];cost_text='unknown' if cost is None else f'{cost:.6f}'
        text+=f"| {model} | {r['successful_requests']} | {r['api_latency_median_sec']:.2f} | {cost_text} |\n"
    text+='\nCost uses actual API token usage and frozen historical pricing, not invoice actual. API timing excludes CV and image preparation.\n'
    text+='\n## Transport incident\n\nInitial sandboxed P4 connection failed before any HTTP response or prediction (3 transport attempts). '
    text+='Records are retained in transport_failure_01. After approved network access, the evaluation succeeded. '
    text+='Successful-run retry counts exclude that initial connection sequence; no fallback prediction was generated.\n'
    text+='\nPrior human-GT benchmark (74 frozen files), final Test report and policy hashes were verified unchanged; see prior_freeze_verification.json.\n'
    target.write_text(text,encoding='utf-8')
    write(RUN/'PERFORMANCE_RECORD_LOCK.json',{'created_at':now(),'record_sha256':digest(target),
        'routing_execution_sha256':digest(RUN/'analysis/routing_execution_record.json'),
        'completed_summary_sha256':result_lock['summary_sha256'],'supplement_script_sha256':digest(Path(__file__))})
    print('Performance record complete; no inference or threshold fitting performed')
if __name__=='__main__':main()
