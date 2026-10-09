"""Isolated regressions + integrity reports. All paid API calls remain zero."""
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from dev_common import ROOT,PROJECT,read,write,protected


def main():
    before=protected(); runs=[]
    for name,folder in [('E21',ROOT/'tests'),('E2',PROJECT/'experiments/stage1_safe_suppress_e2/tests'),('E1',PROJECT/'experiments/p1_decisions/tests')]:
        p=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(folder),'-v'],capture_output=True,text=True,encoding='utf-8',errors='replace')
        runs.append({'suite':name,'exit_code':p.returncode,'output':p.stdout+p.stderr})
    after=protected()
    write(ROOT/'reports/tests.json',{'successful':all(x['exit_code']==0 for x in runs),'suites':runs,
        'protected_files_unchanged':before==after,'protected_hashes':before,'paid_api_calls':0,
        'note':'Synthetic reviews in temporary fixtures only. No production Human GT generated.'})
    print([(x['suite'],x['exit_code']) for x in runs],'protected unchanged',before==after)
    if any(x['exit_code'] for x in runs): raise SystemExit(1)


if __name__=='__main__': main()
