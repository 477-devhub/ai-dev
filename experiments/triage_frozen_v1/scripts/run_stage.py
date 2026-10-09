"""Run each stage in its original pinned Python runtime; no frozen experiment writes."""
import argparse
import subprocess
from common import ROOT, RUN, verify_frozen, stage_ids

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--stage',choices=['calibration','test'],required=True)
    args=ap.parse_args()
    verify_frozen()
    stage_ids(args.stage)
    for model,env in [('cv','p0_cv_only'),('p1','p1_decisions'),('p4','p4_gpt61_sol_vision')]:
        python=ROOT/'experiments'/env/'.venv/Scripts/python.exe'
        subprocess.run([str(python),'-u',str(RUN/'scripts/worker.py'),'--model',model,'--stage',args.stage],check=True,cwd=ROOT)
    python=ROOT/'experiments/p1_decisions/.venv/Scripts/python.exe'
    subprocess.run([str(python),'-u',str(RUN/'scripts/analyze.py'),'--stage',args.stage],check=True,cwd=ROOT)

if __name__=='__main__':
    main()
