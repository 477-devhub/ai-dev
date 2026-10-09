"""Single authorized evaluation, no hidden reruns or parameter search."""
import subprocess,time
from common import *
def main():
    verify()
    if (RUN/'WORKFLOW_STARTED.json').exists():raise RuntimeError('Workflow already started')
    write(RUN/'WORKFLOW_STARTED.json',{'started_at':now()})
    handles=[];processes=[]
    def launch(env,script,args,tag):
        folder=RUN/'logs';folder.mkdir(exist_ok=True)
        out=(folder/(tag+'.stdout.log')).open('wb');err=(folder/(tag+'.stderr.log')).open('wb');handles.extend([out,err])
        p=subprocess.Popen([str(ROOT/'experiments'/env/'.venv/Scripts/python.exe'),'-u',str(RUN/'scripts'/script),*args],
            cwd=ROOT,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        processes.append(p);return p
    def status(state,**extra):
        write(RUN/'workflow_status.json',{'state':state,'updated_at':now(),'expected_per_model':28,
            'completed':{m:len(list((RUN/m/'results').glob('*.json'))) for m in ('p1','p4')},
            'cv_completed':len(list((RUN/'cv_states').glob('*.json'))),'threshold_refit':False,**extra})
    try:
        cv=launch('p0_cv_only','worker.py',['--model','cv'],'cv')
        p1=launch('p1_decisions','worker.py',['--model','p1','--cv-pid',str(cv.pid)],'p1')
        p4=launch('p4_gpt61_sol_vision','worker.py',['--model','p4'],'p4')
        write(RUN/'worker_pids.json',{'cv':cv.pid,'p1':p1.pid,'p4':p4.pid})
        while any(p.poll() is None for p in (cv,p1,p4)):
            status('RUNNING')
            if any(p.poll() not in (None,0) for p in (cv,p1,p4)):raise RuntimeError('Inference worker failed; inspect logs, no automatic rerun')
            time.sleep(5)
        if any(p.returncode!=0 for p in (cv,p1,p4)):raise RuntimeError('Incomplete inference')
        status('EVALUATING')
        analysis=launch('p1_decisions','analyze.py',[],'analysis')
        if analysis.wait()!=0:raise RuntimeError('Scoring failed')
        status('COMPLETE',report='analysis/report.md')
    except Exception as error:
        for p in processes:
            if p.poll() is None:p.terminate()
        status('BLOCKED_TECHNICAL',reason=str(error));raise
    finally:
        for h in handles:h.close()
if __name__=='__main__':main()
