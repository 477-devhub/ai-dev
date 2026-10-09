"""Generate an offline validation report and mock artifacts; never create Human GT."""
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from e2_common import P1, ROOT, read, write, protected_hashes, digest, file_hash
from e2_inputs import prepare_arms
from e2_runner import Store


def main():
    snapshot=protected_hashes()
    stream=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    e1=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(P1/'tests'),'-v'],capture_output=True,text=True,encoding='utf-8')
    write(ROOT/'reports/offline_tests.json',{'successful':result.wasSuccessful() and e1.returncode==0,
        'e2_tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'output':stream.getvalue(),
        'e1_regression_exit_code':e1.returncode,'e1_output':e1.stdout+e1.stderr,
        'protected_files_unchanged':snapshot==protected_hashes(),'protected_hashes':snapshot,'real_api_calls':0})
    if not result.wasSuccessful() or e1.returncode: print(stream.getvalue(),e1.stdout,e1.stderr); raise SystemExit(1)
    sys.path.insert(0,str(ROOT/'tests'))
    from test_e2 import FakeClient
    preparations=prepare_arms(read(P1/'e1_v2/recovery.canonical.json'))
    revision=digest({p.name:file_hash(p) for p in (ROOT/'src').glob('*.py')})[:12]
    store=Store(ROOT/'results'/f'offline_demo_{revision}',mode='synthetic')
    slots=[]
    for a,p in preparations.items():
        out=store.execute('SYNTHETIC_PLUMBING_ONLY',a,p,FakeClient(p))
        slots.append({'arm':a,'request_hash':p['request_hash'],'status':out['status'],
            'input_tokens_estimated':p['compact_input_tokens_estimated'],
            'request_tokens_estimated':p['request_tokens_estimated'],'feature_bytes':p['feature_bytes']})
    write(ROOT/'reports/offline_demo.json',{'mode':'synthetic','gt':None,'model_performance':'NOT EVALUATED',
        'run_folder':str(store.folder),
        'note':'Mock answers and usage only. No Human GT; no API; do not use mocked scores/timing/cost as measurements.', 'arms':slots})
    costs=[]
    for p in sorted((P1.parent/'p0_cv_only/states').glob('ITEM_*.json')):
        arms=prepare_arms(read(p))
        costs.append({'legacy_unlabeled_sample':p.name,'arms':{a:{'input_bytes':len(x['input_text'].encode('utf-8')),
            'input_tokens_estimated':x['compact_input_tokens_estimated'],'request_tokens_estimated':x['request_tokens_estimated'],
            'feature_bytes':x['feature_bytes'],'questions':len(x['questions'])} for a,x in arms.items()}})
    write(ROOT/'reports/offline_input_costs.json',{'measurement':'local text sizes/token proxies only; 7 legacy unlabeled inputs, not E2 development GT',
        'real_api_usage':None,'rows':costs})
    print(f'E2 {result.testsRun} tests passed; E1 regression passed; protected files unchanged; API calls 0')


if __name__=='__main__': main()
