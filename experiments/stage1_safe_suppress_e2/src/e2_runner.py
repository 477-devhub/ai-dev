"""Persistent at-most-once dispatch ledger. Indeterminate attempts never auto retry."""
import contextlib
import copy
import os
import math
import types
from pathlib import Path

from e2_common import ROOT, read, write, digest, now, protected_hashes
from e2_inputs import prepare_arms
from e2_answers import parse_answers, shadow


def json_safe_invalid(value):
    if isinstance(value,float) and not math.isfinite(value):
        return {'invalid_nonfinite_number':repr(value)}
    if isinstance(value,dict): return {k:json_safe_invalid(v) for k,v in value.items()}
    if isinstance(value,list): return [json_safe_invalid(v) for v in value]
    return value


class Store:
    def __init__(self, folder, cfg=None, mode='pilot'):
        self.folder=Path(folder).resolve()
        if not self.folder.is_relative_to(ROOT/'results'): raise ValueError('run folder must be under E2/results')
        self.folder.mkdir(parents=True,exist_ok=True)
        self.cfg=cfg or read(ROOT/'configs/experiment.json')
        if not 0 < self.cfg['budget_usd'] <= 2 or self.cfg['model']!='gpt-6-luna' or self.cfg['endpoint']!='/v1/decisions':
            raise ValueError('E2 requires GPT-6 Luna Decisions and budget in (0,$2]')
        self.mode=mode
        self.path=ROOT/'results/pilot_ledger.json' if mode=='pilot' else self.folder/'ledger.json'
        self.cache=ROOT/'results/pilot_request_cache' if mode=='pilot' else self.folder/'response_cache'
        self.version_hash=digest({'experiment':self.cfg,'code':protected_hashes(),
            'e2_code':{p.name:__import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src').glob('*.py')}})

    @contextlib.contextmanager
    def lock(self):
        path=ROOT/'results/.pilot.lock' if self.mode=='pilot' else self.folder/'.run.lock'
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        try:
            os.write(fd, str(os.getpid()).encode()); os.close(fd); yield
        finally:
            path.unlink(missing_ok=True)

    def ledger(self):
        if self.path.exists():
            ledger=read(self.path)
            if ledger['mode']!=self.mode or (self.mode!='pilot' and ledger['run_version_hash']!=self.version_hash):
                raise ValueError('run version/mode changed: create a new run directory')
            if ledger.get('billing_hash')!=self.billing_hash():
                raise ValueError('billing/budget settings changed; cannot reset shared budget implicitly')
            return ledger
        return {'mode':self.mode,'run_version_hash':self.version_hash,'billing_hash':self.billing_hash(),
                'budget_usd':self.cfg['budget_usd'],'requests':{}}

    def billing_hash(self):
        return digest({k:self.cfg[k] for k in ('budget_usd','input_rate_usd_per_1m',
            'long_context_threshold_tokens','long_context_multiplier','per_request_reservation_usd')})

    def charged_or_reserved(self, ledger):
        return sum(r['accounted_usd'] for r in ledger['requests'].values())

    def execute(self, candidate_id, arm, prep, client):
        # One lock spans dispatch. Crash leaves lock + DISPATCHED, requiring operator review.
        with self.lock():
            ledger=self.ledger()
            key=prep['request_hash']
            if key in ledger['requests']:
                path=self.cache/f'{key}.json'
                if path.is_file():
                    cached=read(path)
                    ledger['requests'][key]['status']=cached['status']
                    if cached.get('usage_cost_usd') is not None:
                        ledger['requests'][key]['accounted_usd']=cached['usage_cost_usd']
                    if self.charged_or_reserved(ledger)>self.cfg['budget_usd']: ledger['budget_overrun']=True
                    write(self.path,ledger)
                    cached=dict(cached,candidate_id=candidate_id,arm=arm,request=prep,
                        cache_reused=True,incremental_dispatch_cost_usd=0.,
                        original_dispatch_candidate_id=cached['candidate_id'],
                        original_dispatch_arm=cached['arm'])
                    write(self.folder/'requests'/f'{key}.json',cached)
                    write(self.folder/'slots'/f'{digest([candidate_id,arm])}.json',cached)
                    return cached
                return {'status':'INDETERMINATE','request_hash':key}
            reserve=self.cfg['per_request_reservation_usd']
            if self.charged_or_reserved(ledger)+reserve>self.cfg['budget_usd']+1e-12:
                return {'status':'BUDGET_STOP','request_hash':key}
            ledger['requests'][key]={'status':'DISPATCHED','accounted_usd':reserve,'created_at':now(),
                'run_version_hash':self.version_hash,'dispatch_settings':getattr(client,'metadata',{'mode':'synthetic'})}
            write(self.path,ledger)  # write-before-network: interrupted calls never silently resend
            artifact={'schema_version':'e2-result-v1','candidate_id':candidate_id,'arm':arm,
                'mode':self.mode,'request_hash':key,'request':prep,'run_version_hash':self.version_hash,
                'model':self.cfg['model'],'endpoint':self.cfg['endpoint'],'created_at':now()}
            artifact['client_settings']=getattr(client,'metadata',{'mode':'synthetic'})
            try:
                raw=client.decide(prep['input_text'],prep['questions'],self.cfg['model'])
            except Exception as e:
                # Exception type only: SDK errors might contain authorization headers.
                raw={'status':'FAILED','error_type':type(e).__name__}
            if not isinstance(raw,dict):
                raw={'status':'FAILED','error_type':'InvalidTopLevelResponse','raw_invalid':raw}
            artifact['raw_response']=raw
            usage=raw.get('usage') if isinstance(raw.get('usage'),dict) else {}
            count=usage.get('input_tokens')
            valid_count=isinstance(count,int) and not isinstance(count,bool) and count>0
            valid_usage=valid_count and all(isinstance(usage.get(k),int) and not isinstance(usage.get(k),bool)
                and usage[k]>=0 for k in ('output_tokens','total_tokens'))
            if valid_usage: valid_usage=usage['total_tokens']>=count+usage['output_tokens']
            cost=count*self.cfg['input_rate_usd_per_1m']/1e6*(self.cfg['long_context_multiplier'] if count>self.cfg['long_context_threshold_tokens'] else 1) if valid_count else None
            artifact['usage_cost_usd']=cost
            artifact['cache_reused']=False
            artifact['incremental_dispatch_cost_usd']=cost
            artifact['cost_definition']='Provider reported usage times verified rate; invoice not verified. Failed unknown usage retains reservation.'
            if raw.get('status')=='ok':
                parsed=parse_answers(raw.get('answers'),prep['questions'],prep['task'],prep['camera_ids'])
                artifact['parsed']=parsed
                artifact['status']='COMPLETE' if parsed['complete'] else 'INCOMPLETE_ANSWERS'
                if raw.get('model')!=self.cfg['model']:
                    artifact['status']='INVALID_MODEL'
                if not valid_usage:
                    artifact['status']='INVALID_USAGE'
                artifact['shadow_suppression']={name:shadow(parsed,prep['task'],policy) if artifact['status']=='COMPLETE' else False
                    for name,policy in self.cfg['shadow_policies'].items()
                    if 'safe_min' not in policy or arm in ('B','D')}
            else: artifact['status']='FAILED'
            artifact['raw_response']=json_safe_invalid(raw)
            # Store raw response first. If interrupted before ledger update, resume loads it.
            write(self.cache/f'{key}.json',artifact)
            write(self.folder/'requests'/f'{key}.json',artifact)
            write(self.folder/'slots'/f'{digest([candidate_id,arm])}.json',artifact)
            ledger['requests'][key].update(status=artifact['status'],accounted_usd=cost if cost is not None else reserve)
            if self.charged_or_reserved(ledger)>self.cfg['budget_usd']:
                ledger['budget_overrun']=True
            write(self.path,ledger)
            return artifact


class PilotClient:
    def __init__(self):
        from decisions_client import DecisionsClient
        self.inner=DecisionsClient()
        if str(self.inner.client.base_url)!='https://api.openai.com/v1/':
            raise ValueError('E2 pilot requires official default API base URL')
        # Reuse the exact client call/parser, but disable application retries in this local wrapper.
        # Retrying a timeout could duplicate billing. Original module/constants remain unchanged.
        base=DecisionsClient.decide
        glob=dict(base.__globals__,MAX_RETRIES=0)
        self.method=types.MethodType(types.FunctionType(base.__code__,glob,base.__name__,base.__defaults__,base.__closure__),self.inner)
        self.metadata={'sdk_version':self.inner.sdk_version,'http_client_version':self.inner.http_client_version,
            'connect_timeout_sec':10,'read_timeout_sec':120,'sdk_retries':0,'application_retries':0,
            'base_url':str(self.inner.client.base_url),'model':'gpt-6-luna','endpoint':'/v1/decisions'}

    def decide(self,*args): return self.method(*args)


def plan(candidates, cfg=None):
    cfg=cfg or read(ROOT/'configs/experiment.json')
    tasks=[]
    for c in candidates:
        from jsonschema import Draft202012Validator
        from e2_common import PROJECT
        state=read(c['canonical_path'])
        Draft202012Validator(read(PROJECT/'experiments/p0_cv_only/schemas/canonical_cv_state.schema.json')).validate(state)
        prep=prepare_arms(state)
        # Rotate arm order across candidates: avoid all v1 requests preceding all v2 requests.
        offset=int(digest(c['candidate_id'])[:8],16)%4
        arms=list('ABCD'); arms=arms[offset:]+arms[:offset]
        tasks += [(c,arm,prep[arm]) for arm in arms]
    unique={p['request_hash']:p for _,_,p in tasks}
    estimate=sum(p['request_tokens_estimated']['tokens']*cfg['input_rate_usd_per_1m']/1e6 for p in unique.values())
    return tasks, {'requests':len(tasks),'unique_requests':len(unique),'estimated_input_cost_usd':estimate,
        'reserved_maximum_cost_usd':len(unique)*cfg['per_request_reservation_usd'],
        'budget_usd':cfg['budget_usd'],'maximum_note':'Conservative local reservation, not a provider-enforced invoice cap. No retries; unknown usage remains reserved.'}
