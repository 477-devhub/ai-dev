"""GT-blind workers reuse the byte-identical frozen computation and API clients."""
import argparse
import sys
import time
from common import ROOT, BENCH, RUN, PLAN, read, write, now, verify_frozen, stage_ids, install_model_boundary, digest

def cv(stage):
    import public_loader
    sys.path.insert(0,str(ROOT/'experiments/p0_cv_only/src'))
    from utils import load_yaml, CV_CONFIG_PATH
    import frame_source
    from pose_detector import PoseDetector
    from state_builder import StateBuilder
    from jsonschema import Draft202012Validator
    frame_source.lmi = public_loader
    cfg = load_yaml(CV_CONFIG_PATH)
    detector = PoseDetector(cfg)
    detector.warmup()
    builder = StateBuilder(cfg,detector)
    schema = read(ROOT/'experiments/p0_cv_only/schemas/canonical_cv_state.schema.json')
    validator = Draft202012Validator(schema)
    aliases = read(PLAN)['cv_aliases']
    for item in stage_ids(stage):
        dst = RUN/'cv_states'/f'{item}.json'
        if dst.exists():
            if digest(dst) != read(RUN/'cv_logs'/f'{item}.json')['cv_state_sha256']:
                raise RuntimeError('Completed CV state drift; no silent rebuild')
            print(f'CV {item}: reuse completed state',flush=True)
            continue
        state,timing,audit,_ = builder.build(item,use_cache=False)
        # Frozen CV schema restricts harness IDs to ITEM_##; alias is stripped by the frozen serializer.
        state['input']['item_id'] = aliases[item]
        validator.validate(state)
        write(dst,state)
        write(RUN/'cv_logs'/f'{item}.json',{'item_id':item,'alias':aliases[item],'timing':timing,'audit':audit,
                                        'cv_state_sha256':digest(dst),'rule_engine_executed':False})
        print(f'CV {item}: 64 frames complete',flush=True)

def models(model,stage):
    root = ROOT/'experiments'/('p1_decisions' if model=='p1' else 'p4_gpt61_sol_vision')
    sys.path.insert(0,str(root/'src'))
    if model == 'p1':
        import p1_pipeline as pipeline
        from decisions_client import DecisionsClient
        from jsonschema import Draft202012Validator
        state_schema = read(ROOT/'experiments/p0_cv_only/schemas/canonical_cv_state.schema.json')
        def load_state(item):
            obj = read(RUN/'cv_states'/f'{item}.json')
            Draft202012Validator(state_schema).validate(obj)
            return obj
        pipeline.load_cv_state = load_state
        pipe = pipeline.P1Pipeline(DecisionsClient())
    else:
        import public_loader
        import frame_loader
        import p4_pipeline as pipeline
        from openai_client import ResponsesClient
        frame_loader._loader = public_loader
        pipe = pipeline.P4Pipeline(ResponsesClient())
    for item in stage_ids(stage):
        result_path = RUN/model/'results'/f'{item}.json'
        raw_path = RUN/model/'raw_api'/f'{item}.json'
        attempt = RUN/model/'attempts'/f'{item}.json'
        if result_path.exists():
            if digest(result_path) != read(attempt)['result_sha256'] or digest(raw_path) != read(attempt)['raw_sha256']:
                raise RuntimeError('Completed model output drift; no silent rerun')
            print(f'{model.upper()} {item}: reuse completed inference',flush=True)
            continue
        if attempt.exists():
            raise RuntimeError(f'{model} {item}: prior attempt exists; no automatic repeat inference allowed')
        t0 = time.perf_counter()
        prep = pipe.prepare(item)
        # Mark before the external request, so a crash cannot silently consume a second evaluation.
        write(attempt,{'item_id':item,'stage':stage,'started_at':now(),'status':'STARTED'})
        if model=='p1':
            api = pipe.client.decide(prep['input_text'],prep['questions'])
        else:
            api = pipe.client.decide(prep['content'],prep['text_format'])
        out = {'item_id':item,'prep':prep,'api':api}
        if api['status'] != 'ok':
            write(raw_path,pipeline.raw_record(out))
            write(attempt,{'item_id':item,'stage':stage,'status':'FAILED','finished_at':now(),
                           'failure':api.get('status'),'retry_count':api.get('retry_count'),
                           'error_types':[e.get('error_type') for e in api.get('errors',[])],
                           'http_statuses':[e.get('status') for e in api.get('errors',[])]})
            raise RuntimeError(f'{model.upper()} {item}: API failed; batch stopped, no prediction invented')
        try:
            if model=='p1':
                prediction,decision,adapter_ms = pipe.adapt(prep['compact'],api['answers'],api['model'])
                pipe.validate_prediction(prediction,'single',['CAM_01'])
                out['prediction'] = prediction
            else:
                prediction,decision,raw,vis,adapter_meta,adapter_ms = pipe.adapt(prep,api['parsed'],api['model'])
                pipe.validate_prediction(prediction,'single',['CAM_01'])
                out.update({'prediction':prediction,'raw_canonical':raw})
        except Exception as error:
            write(raw_path,pipeline.raw_record(out))
            write(attempt,{'item_id':item,'stage':stage,'status':'ADAPTER_FAILED','error_type':type(error).__name__,
                           'finished_at':now()})
            raise
        write(raw_path,pipeline.raw_record(out))
        result = {'benchmark_version':'477-triage-normal-v1','item_id':item,'stage':stage,'model':model,
                  'frozen_model_returned':api.get('model'),'prediction':prediction,'decision':decision,
                  'usage':api.get('usage'),'api_timing':api.get('timing'),
                  'retry_count':api.get('retry_count'),'full_harness_ms':round((time.perf_counter()-t0)*1000,2),
                  'completed_at':now(),'human_grading':None,
                  'input_fingerprint':prep['state']['input']['benchmark_input_fingerprint'] if model=='p1' else prep['input_fingerprint']}
        if model=='p4':
            write(RUN/model/'frame_manifests'/f'{item}.json',pipeline.frame_manifest(prep))
            result['adapter_metadata'] = adapter_meta
        write(result_path,result)
        write(attempt,{'item_id':item,'stage':stage,'status':'COMPLETE','finished_at':now(),
                       'raw_sha256':digest(raw_path),'result_sha256':digest(result_path)})
        # Never print test predictions or metrics in the inference worker.
        print(f'{model.upper()} {item}: inference complete',flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model',choices=['cv','p1','p4'],required=True)
    ap.add_argument('--stage',choices=['calibration','test'],required=True)
    args = ap.parse_args()
    verify_frozen()
    stage_ids(args.stage)
    install_model_boundary()
    if args.model=='cv':
        cv(args.stage)
    else:
        models(args.model,args.stage)

if __name__ == '__main__':
    main()
