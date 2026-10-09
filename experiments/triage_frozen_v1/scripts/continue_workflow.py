"""One-off continuation of the authorized run, with a calibration-policy gate before test."""
import argparse
import subprocess
import time
from common import ROOT, RUN, PLAN, read, write, now, verify_frozen, digest
from stream_worker import alive

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--cv-calibration-pid',type=int,required=True)
    ap.add_argument('--p4-calibration-pid',type=int,required=True)
    args=ap.parse_args()
    verify_frozen()
    code_lock=RUN/'CONTINUATION_LOCK.json'
    if code_lock.exists():
        raise RuntimeError('Continuation already launched; refusing concurrent workflow')
    write(code_lock,{'created_at':now(),'run_plan_sha256':digest(PLAN),
        'sha256':{name:digest(RUN/'scripts'/name) for name in ('stream_worker.py','continue_workflow.py')},
        'policy':'Waiting and process orchestration only; frozen model code and routing search plan unchanged'})
    logs=RUN/'logs';logs.mkdir(exist_ok=True)
    handles=[]
    def launch(env,script,extra,tag):
        stdout=(logs/f'{tag}.stdout.log').open('wb')
        stderr=(logs/f'{tag}.stderr.log').open('wb')
        handles.extend([stdout,stderr])
        return subprocess.Popen([str(ROOT/'experiments'/env/'.venv/Scripts/python.exe'),'-u',
            str(RUN/'scripts'/script),*extra],cwd=ROOT,stdout=stdout,stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW)
    def status(stage,state,extra=None):
        plan=read(PLAN)
        ids=plan[stage+'_ids']
        data={'updated_at':now(),'stage':stage,'state':state,'expected':len(ids),
            'completed':{m:sum((RUN/m/'results'/f'{i}.json').exists() for i in ids) for m in ['p1','p4']},
            'test_evaluation_completed':(RUN/'analysis/final_test_evaluation.json').exists(),
            'routing_policy_locked':(RUN/'routing_policy_lock.json').exists(),
            'post_test_retuning':False}
        if extra:data.update(extra)
        write(RUN/'workflow_status.json',data)
    stage='calibration'
    try:
        p1=launch('p1_decisions','stream_worker.py',['--stage',stage,'--cv-pid',str(args.cv_calibration_pid)],'p1_calibration')
        ids=read(PLAN)['calibration_ids']
        while True:
            status(stage,'RUNNING')
            p1_complete=all((RUN/'p1/results'/f'{i}.json').is_file() for i in ids)
            p4_complete=all((RUN/'p4/results'/f'{i}.json').is_file() for i in ids)
            if p1_complete and p4_complete:break
            if p1.poll() is not None and not p1_complete:
                raise RuntimeError('P1 calibration stopped before completion; inspect logs/attempts. Test remains unopened.')
            if not alive(args.p4_calibration_pid) and not p4_complete:
                raise RuntimeError('P4 calibration stopped before completion; inspect attempts. Test remains unopened.')
            time.sleep(10)
        # Complete all calibration outputs before reading calibration GT and locking policy.
        result=launch('p1_decisions','analyze.py',['--stage','calibration'],'calibration_analysis')
        if result.wait()!=0:raise RuntimeError('Calibration analysis failed; test remains unopened')
        stage='test'
        status(stage,'STARTING_AFTER_POLICY_LOCK')
        cv=launch('p0_cv_only','worker.py',['--model','cv','--stage','test'],'cv_test')
        p1=launch('p1_decisions','stream_worker.py',['--stage','test','--cv-pid',str(cv.pid)],'p1_test')
        p4=launch('p4_gpt61_sol_vision','worker.py',['--model','p4','--stage','test'],'p4_test')
        workers=[cv,p1,p4]
        while any(p.poll() is None for p in workers):
            status(stage,'RUNNING')
            if any(p.poll() not in (None,0) for p in workers):
                raise RuntimeError('A test worker failed; no automatic retry or threshold change')
            time.sleep(10)
        if any(p.returncode!=0 for p in workers):raise RuntimeError('Test inference incomplete')
        result=launch('p1_decisions','analyze.py',['--stage','test'],'final_test_analysis')
        if result.wait()!=0:raise RuntimeError('Final test evaluation failed; no repeat evaluation')
        status(stage,'COMPLETE')
    except Exception as error:
        status(stage,'BLOCKED_TECHNICAL',{'reason':str(error)})
        raise
    finally:
        for handle in handles:handle.close()

if __name__=='__main__':
    main()
