"""Frozen computation; variable source suballocation at the transport boundary only."""
import argparse, time
from common import *
def cv():
    import public_loader
    sys.path.insert(0,str(ROOT/'experiments/p0_cv_only/src'))
    from utils import load_yaml,CV_CONFIG_PATH
    import frame_source
    from pose_detector import PoseDetector
    from state_builder import StateBuilder
    from jsonschema import Draft202012Validator
    frame_source.lmi=public_loader
    cfg=load_yaml(CV_CONFIG_PATH); detector=PoseDetector(cfg); detector.warmup(); builder=StateBuilder(cfg,detector)
    for j in jobs():
        item=j['id']; dst=RUN/'cv_states'/f'{item}.json'
        if dst.exists():
            assert digest(dst)==read(RUN/'cv_logs'/f'{item}.json')['sha256'];continue
        frame_source.TOTAL_FRAMES=j['frame_count']
        state,timing,audit,_=builder.build(item,use_cache=False)
        state['input']['item_id']=j['cv_alias']
        Draft202012Validator(schema_for(j['frame_count'])).validate(state)
        write(dst,state);write(RUN/'cv_logs'/f'{item}.json',{'timing':timing,'audit':audit,'sha256':digest(dst),'rule_engine_executed':False})
        print('CV',item,'complete',flush=True)
def models(model,cv_pid=None):
    env='p1_decisions' if model=='p1' else 'p4_gpt61_sol_vision'
    sys.path.insert(0,str(ROOT/'experiments'/env/'src'))
    from cost import external_api_cost_usd, PRICING
    if model=='p1':
        import p1_pipeline as pipeline
        from decisions_client import DecisionsClient
        from jsonschema import Draft202012Validator
        def load_state(item):
            from ctypes import windll
            path=RUN/'cv_states'/f'{item}.json'
            while not path.exists() or not (RUN/'cv_logs'/f'{item}.json').exists():
                handle=windll.kernel32.OpenProcess(0x100000,False,cv_pid)
                alive=bool(handle) and windll.kernel32.WaitForSingleObject(handle,0)==258
                if handle:windll.kernel32.CloseHandle(handle)
                if not alive: raise RuntimeError('CV producer exited before state completed')
                time.sleep(3)
            assert digest(path)==read(RUN/'cv_logs'/f'{item}.json')['sha256']
            state=read(path);Draft202012Validator(schema_for(job(item)['frame_count'])).validate(state);return state
        pipeline.load_cv_state=load_state;pipe=pipeline.P1Pipeline(DecisionsClient())
    else:
        import public_loader, frame_loader
        import p4_pipeline as pipeline
        from openai_client import ResponsesClient
        frame_loader._loader=public_loader
        pipeline.load_frames=public_loader.load_frames
        pipe=pipeline.P4Pipeline(ResponsesClient())
    for j in jobs():
        item=j['id']; result=RUN/model/'results'/f'{item}.json';attempt=RUN/model/'attempts'/f'{item}.json';raw=RUN/model/'raw_api'/f'{item}.json'
        if result.exists():
            assert digest(result)==read(attempt)['result_sha256'];assert digest(raw)==read(attempt)['raw_sha256'];continue
        if attempt.exists():raise RuntimeError('Previous attempt exists; refusing silent rerun '+item)
        started=time.perf_counter();prep=pipe.prepare(item)
        # Keep actual requests as text/schema/frame IDs, never base64 or secrets.
        request={'frame_ids':[r['frame_id'] for r in __import__('public_loader').rows(item)]}
        if model=='p1':request.update(input_text=prep['input_text'],questions=prep['questions'])
        else:request.update(input_text=prep['request_text'],text_format=prep['text_format'])
        write(RUN/model/'requests'/f'{item}.json',request)
        write(attempt,{'status':'STARTED','started_at':now(),'item':item})
        api=pipe.client.decide(prep['input_text'],prep['questions']) if model=='p1' else pipe.client.decide(prep['content'],prep['text_format'])
        out={'item_id':item,'prep':prep,'api':api}
        write(raw,pipeline.raw_record(out))
        if api['status']!='ok':
            write(attempt,{'status':'FAILED','finished_at':now(),'failure':api['status'],'retry_count':api.get('retry_count')})
            raise RuntimeError(model+' API failure; no fabricated output '+item)
        try:
            if model=='p1':pred,decision,ms=pipe.adapt(prep['compact'],api['answers'],api['model']);visual=None
            else:
                pred,decision,canonical,visual,meta,ms=pipe.adapt(prep,api['parsed'],api['model'])
                out['raw_canonical']=canonical
                write(RUN/model/'frame_manifests'/f'{item}.json',pipeline.frame_manifest(prep))
            pipe.validate_prediction(pred,'single',['CAM_01'])
        except Exception as error:
            write(attempt,{'status':'ADAPTER_FAILED','error_type':type(error).__name__,'finished_at':now()});raise
        out['prediction']=pred;write(raw,pipeline.raw_record(out))
        write(result,{'item_id':j['item_id'],'source_id':j['source_id'],'job_id':item,'model':model,
            'returned_model':api.get('model'),'frame_count':j['frame_count'],'prediction':pred,'decision':decision,
            'visual':visual,'usage':api.get('usage'),'api_timing':api.get('timing'),'retry_count':api.get('retry_count'),
            'estimated_api_cost_usd':external_api_cost_usd(api.get('usage')),'pricing_snapshot':PRICING,
            'full_harness_ms':round((time.perf_counter()-started)*1000,2),'completed_at':now(),
            'input_fingerprint':prep['state']['input']['benchmark_input_fingerprint'] if model=='p1' else prep['input_fingerprint']})
        write(attempt,{'status':'COMPLETE','finished_at':now(),'result_sha256':digest(result),'raw_sha256':digest(raw)})
        print(model.upper(),item,'complete',flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--model',choices=['cv','p1','p4'],required=True);ap.add_argument('--cv-pid',type=int);args=ap.parse_args()
    verify();boundary()
    cv() if args.model=='cv' else models(args.model,args.cv_pid)
