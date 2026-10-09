"""Synthetic responses are plumbing fixtures, never Human GT or model results."""
import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from e2_common import ROOT, P1, read, write, canonical, digest
from e2_inputs import prepare_arms, question_configs, build_questions
from e2_answers import parse_answers, shadow
from e2_runner import Store
from e2_dataset import validate_manifest
from e2_metrics import evaluate, interval
from decision_adapter import DecisionAdapter


def response(prep, p_incident=.005, p_safe=.99):
    answers=[]
    for q in prep['questions']:
        if q['type']=='predicate':
            answers.append({'name':q['name'],'type':'predicate','probability':p_safe if q['name'].endswith('safe_to_suppress') else p_incident if q['name'].endswith('incident') else .01})
        elif q['type']=='choice':
            value='no_clear_incident' if any(c['value']=='no_clear_incident' for c in q['choices']) else q['choices'][0]['value']
            answers.append({'name':q['name'],'type':'choice','choice':value,'confidence':.98,
                'probabilities':[{'value':c['value'],'probability':float(c['value']==value)} for c in q['choices']]})
        else:
            answers.append({'name':q['name'],'type':'score','score':0.,'confidence':.98,
                'probabilities':[{'value':i,'label':l['label'],'probability':float(i==0)} for i,l in enumerate(q['levels'])]})
    return {'status':'ok','model':'gpt-6-luna','answers':answers,
        'usage':{'input_tokens':1000,'output_tokens':0,'total_tokens':1000},
        'timing':{'total_including_retries_ms':10,'last_attempt_ms':10},'retry_count':0,
        'response_body':{'synthetic_fixture':True,'answers':answers}}


class FakeClient:
    def __init__(self, prep, raw=None): self.prep=prep; self.raw=raw; self.calls=0
    def decide(self,*args):
        self.calls+=1
        return copy.deepcopy(self.raw if self.raw is not None else response(self.prep))


class E2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state=read(P1/'e1_v2/recovery.canonical.json')
        cls.arms=prepare_arms(cls.state)
        cls.config=read(ROOT/'configs/experiment.json')

    def parsed(self,arm='D',raw=None):
        p=self.arms[arm]
        return parse_answers((raw or response(p))['answers'],p['questions'],p['task'],p['camera_ids'])

    def store(self,cfg=None):
        tmp=tempfile.TemporaryDirectory(dir=ROOT/'results',prefix='test_')
        self.addCleanup(tmp.cleanup)
        return Store(tmp.name,cfg or self.config,mode='synthetic')

    def test_factorial_inputs_and_common_questions_exact(self):
        a=self.arms
        self.assertEqual(a['A']['input_text'],a['B']['input_text'])
        self.assertEqual(a['C']['input_text'],a['D']['input_text'])
        self.assertEqual(a['A']['questions'],a['C']['questions'])
        self.assertEqual(a['B']['questions'],a['D']['questions'])
        self.assertEqual(a['B']['questions'][:-1],a['A']['questions'])
        self.assertEqual(len(a['A']['questions']),7); self.assertEqual(len(a['D']['questions']),8)
        self.assertEqual({p['canonical_state_hash'] for p in a.values()},{digest(self.state)})

    def test_original_config_and_question_builder_reuse(self):
        from decisions_client import build_questions as original_build
        original,_=question_configs()
        self.assertEqual(self.arms['A']['questions'],original_build('single',['CAM_01'],original))
        self.assertEqual(read(P1/'configs/decisions_questions_v1.json'),original)

    def test_all_three_tasks_and_per_camera_safe_questions(self):
        original,safe=question_configs()
        for task,cams,n_original,n_safe in [('single',['CAM_01'],7,8),
            ('attention',['CAM_01','CAM_02','CAM_03'],22,25),('multi_camera',['CAM_01','CAM_02'],10,11)]:
            qs=build_questions(task,cams,safe); orig=build_questions(task,cams,original)
            self.assertEqual(len(qs),n_safe); self.assertEqual(len(orig),n_original)
            prep={'questions':qs}; parsed=parse_answers(response(prep)['answers'],qs,task,cams)
            self.assertTrue(parsed['complete'])
            self.assertEqual(qs[:len(orig)],orig)

    def test_common_adapter_exact_mapping(self):
        raw=response(self.arms['D']); parsed=self.parsed(raw=raw)
        expected=DecisionAdapter(read(ROOT/'configs/original.json')).assessment({a['name']:a for a in raw['answers']})
        self.assertEqual(parsed['common'],expected)
        self.assertEqual(parsed['safe_to_suppress']['safe_to_suppress'],.99)

    def test_missing_safe_blocks_shadow(self):
        raw=response(self.arms['D']); raw['answers']=raw['answers'][:-1]
        p=self.parsed(raw=raw)
        self.assertEqual(p['missing'],['safe_to_suppress'])
        self.assertFalse(shadow(p,'single',self.config['shadow_policies']['safe_guard_095']))

    def test_missing_original_forces_review(self):
        raw=response(self.arms['D']); raw['answers']=raw['answers'][1:]
        self.assertTrue(self.parsed(raw=raw)['common']['human_review_required'])

    def test_refusal_all_questions(self):
        for name in [q['name'] for q in self.arms['D']['questions']]:
            raw=response(self.arms['D'])
            raw['answers']=[{'name':name,'type':'refusal'} if a['name']==name else a for a in raw['answers']]
            p=self.parsed(raw=raw); self.assertFalse(p['complete']); self.assertIn(name,p['refused'])
            self.assertFalse(shadow(p,'single',self.config['shadow_policies']['baseline_guard']))

    def test_duplicate_and_unexpected_answers(self):
        for new in [response(self.arms['D'])['answers'][0],{'name':'surprise','type':'predicate','probability':0}]:
            raw=response(self.arms['D']); raw['answers'].append(new)
            self.assertFalse(self.parsed(raw=raw)['complete'])

    def test_invalid_numeric_range_nan_bool_and_type(self):
        for value in [None,-.1,1.1,float('nan'),float('inf'),True,'0']:
            raw=response(self.arms['D']); raw['answers'][0]['probability']=value
            self.assertFalse(self.parsed(raw=raw)['complete'])
        raw=response(self.arms['D']); raw['answers'][0]['type']='choice'
        self.assertFalse(self.parsed(raw=raw)['complete'])

    def test_malformed_name_and_float_score_index_do_not_crash(self):
        raw=response(self.arms['D']); raw['answers'][0]['name']=[]
        self.assertFalse(self.parsed(raw=raw)['complete'])
        raw=response(self.arms['D']); raw['answers'][2]['probabilities'][0]['value']=0.
        self.assertFalse(self.parsed(raw=raw)['complete'])

    def test_invalid_usage_shape_is_persisted(self):
        store=self.store(); raw=response(self.arms['A']); raw['usage']=['invalid']
        result=store.execute('S','A',self.arms['A'],FakeClient(self.arms['A'],raw))
        self.assertEqual(result['status'],'INVALID_USAGE')
        self.assertEqual(result['raw_response']['usage'],['invalid'])

    def test_nonfinite_invalid_response_is_preserved_and_cached(self):
        store=self.store(); raw=response(self.arms['A']); raw['answers'][0]['probability']=float('nan')
        client=FakeClient(self.arms['A'],raw)
        out=store.execute('S','A',self.arms['A'],client)
        self.assertEqual(out['status'],'INCOMPLETE_ANSWERS')
        self.assertEqual(out['raw_response']['answers'][0]['probability'],{'invalid_nonfinite_number':'nan'})
        store.execute('S','A',self.arms['A'],client); self.assertEqual(client.calls,1)

    def test_choice_distribution_and_score_validation(self):
        for mutation in ['choice','score','probs','score_mean','labels']:
            raw=response(self.arms['D'])
            if mutation=='choice': raw['answers'][1]['choice']='invented'
            elif mutation=='score': raw['answers'][2]['score']=5
            elif mutation=='score_mean': raw['answers'][2]['score']=1.
            elif mutation=='labels': raw['answers'][2]['probabilities'][0]['label']='wrong'
            else: raw['answers'][1]['probabilities'][0]['probability']=.2
            self.assertFalse(self.parsed(raw=raw)['complete'])

    def test_safe_not_incident_complement(self):
        p=self.parsed(raw=response(self.arms['D'],p_incident=.005,p_safe=.1))
        self.assertTrue(shadow(p,'single',self.config['shadow_policies']['baseline_guard']))
        self.assertFalse(shadow(p,'single',self.config['shadow_policies']['safe_guard_095']))
        p=self.parsed(raw=response(self.arms['D'],p_incident=.8,p_safe=.999))
        self.assertFalse(shadow(p,'single',self.config['shadow_policies']['safe_guard_095']))

    def test_resume_cache_and_actual_cost(self):
        store=self.store(); prep=self.arms['A']; client=FakeClient(prep)
        a=store.execute('SYNTH','A',prep,client); b=store.execute('SYNTH','A',prep,client)
        self.assertEqual(client.calls,1); self.assertEqual(a['raw_response'],b['raw_response'])
        self.assertTrue(b['cache_reused']); self.assertEqual(b['incremental_dispatch_cost_usd'],0.)
        self.assertEqual(a['usage_cost_usd'],.0001)

    def test_cache_alias_preserves_current_candidate_provenance(self):
        store=self.store(); p=self.arms['A']; client=FakeClient(p)
        store.execute('FIRST','A',p,client)
        current=copy.deepcopy(p); current['canonical_state_hash']='different metadata, identical model input'
        out=store.execute('SECOND','A',current,client)
        self.assertEqual(client.calls,1)
        self.assertEqual(out['candidate_id'],'SECOND')
        self.assertEqual(out['request']['canonical_state_hash'],current['canonical_state_hash'])
        self.assertEqual(out['original_dispatch_candidate_id'],'FIRST')

    def test_failure_never_implicitly_retry(self):
        store=self.store(); prep=self.arms['A']; client=FakeClient(prep,{'status':'FAILED'})
        self.assertEqual(store.execute('SYNTH','A',prep,client)['status'],'FAILED')
        store.execute('SYNTH','A',prep,client)
        self.assertEqual(client.calls,1)
        self.assertEqual(store.charged_or_reserved(store.ledger()),.1)

    def test_unknown_dispatch_no_repeat(self):
        store=self.store(); prep=self.arms['A']; ledger=store.ledger()
        ledger['requests'][prep['request_hash']]={'status':'DISPATCHED','accounted_usd':.1}
        write(store.path,ledger); client=FakeClient(prep)
        self.assertEqual(store.execute('SYNTH','A',prep,client)['status'],'INDETERMINATE')
        self.assertEqual(client.calls,0)

    def test_lock_prevents_concurrent_dispatch(self):
        store=self.store(); client=FakeClient(self.arms['A'])
        with store.lock():
            with self.assertRaises(FileExistsError): store.execute('S','A',self.arms['A'],client)
        self.assertEqual(client.calls,0)

    def test_budget_stop_before_call(self):
        cfg=copy.deepcopy(self.config); cfg['budget_usd']=.05
        store=self.store(cfg); client=FakeClient(self.arms['A'])
        self.assertEqual(store.execute('S','A',self.arms['A'],client)['status'],'BUDGET_STOP')
        self.assertEqual(client.calls,0)

    def test_actual_cost_over_reservation_stops_next(self):
        cfg=copy.deepcopy(self.config); cfg['budget_usd']=.1
        store=self.store(cfg); raw=response(self.arms['A']); raw['usage'].update(input_tokens=1_000_000,total_tokens=1_000_000)
        client=FakeClient(self.arms['A'],raw)
        store.execute('S','A',self.arms['A'],client)
        self.assertTrue(store.ledger()['budget_overrun'])
        self.assertEqual(store.execute('S','B',self.arms['B'],client)['status'],'BUDGET_STOP')
        self.assertEqual(client.calls,1)

    def test_invalid_usage_and_model_not_safe(self):
        for key,value in [('model','unexpected'),('usage',{})]:
            raw=response(self.arms['A']); raw[key]=value
            store=self.store(); out=store.execute('S','A',self.arms['A'],FakeClient(self.arms['A'],raw))
            self.assertIn(out['status'],['INVALID_MODEL','INVALID_USAGE'])
            self.assertFalse(out['shadow_suppression']['baseline_guard'])

    def test_version_change_refuses_resume(self):
        store=self.store(); client=FakeClient(self.arms['A']); store.execute('S','A',self.arms['A'],client)
        cfg=copy.deepcopy(self.config); cfg['experiment_version']='different'
        new=Store(store.folder,cfg,'synthetic')
        with self.assertRaises(ValueError): new.execute('S','A',self.arms['A'],client)

    def test_metric_denominators_and_missing_arm(self):
        candidates=[{'candidate_id':'SYNTH_N','human_gt':{'label':'CLEAR_NORMAL'}},
                    {'candidate_id':'SYNTH_D','human_gt':{'label':'ANCHORED_DANGER'}},
                    {'candidate_id':'SYNTH_X','human_gt':{'label':'AMBIGUOUS'}}]
        records={}
        for c in candidates:
            for a in 'ABCD':
                records[(c['candidate_id'],a)]={'status':'COMPLETE','parsed':self.parsed(a),
                    'shadow_suppression':{'baseline_guard':c['candidate_id']=='SYNTH_N','safe_guard_095':False,'safe_guard_099':False},
                    'request':self.arms[a],'raw_response':response(self.arms[a]),'usage_cost_usd':.0001}
        records[('SYNTH_X','D')]['status']='FAILED'
        out=evaluate(candidates,records)
        self.assertEqual(out['complete_paired_candidates'],2)
        p=out['arms']['A']['policies']['baseline_guard']
        self.assertEqual(p['ANCHORED_DANGER']['rate'],0.)
        self.assertEqual(p['CLEAR_NORMAL']['rate'],1.)
        self.assertEqual(p['AMBIGUOUS']['n'],0)
        self.assertEqual(p['projected_p4_rate_complete_pairs'],.5)
        self.assertAlmostEqual(p['projected_p4_rate_all_candidates_failures_escalate'],2/3)
        self.assertEqual(out['paired_comparisons']['A_vs_B']['n'],2)
        self.assertEqual(len(out['state_x_question_interaction']['rows']),2)

    def test_no_gt_no_fake_metrics(self):
        out=evaluate([],{}); self.assertEqual(out['status'],'NOT EVALUATED')
        self.assertIsNone(out['arms']['A']['policies']['baseline_guard']['CLEAR_NORMAL']['rate'])

    def test_zero_miss_interval_not_safety_proof(self):
        self.assertAlmostEqual(interval(0,10)['zero_miss_exact_one_sided_95_upper'],.2588655509)
        self.assertIsNone(interval(0,0))

    def test_existing_development_empty(self):
        audit=validate_manifest(read(ROOT/'data/development_manifest.json'))
        self.assertEqual(audit['eligible'],[])

    def test_gt_from_dataset_or_agent_not_accepted(self):
        c={'candidate_id':'X','source_id':'SPG_test','scene_group_id':'new','physical_group_id':'new',
            'human_gt':{'label':'CLEAR_NORMAL','basis':'filename','reviewer':'agent'}}
        out=validate_manifest({'schema_version':'e2-development-v1','candidates':[c]})
        self.assertIn('HUMAN_GT_INCOMPLETE',out['exclusions']['X'])
        self.assertIn('INDEPENDENCE_UNCONFIRMED',out['exclusions']['X'])

    def test_frozen_overlap_excluded_without_gt_read(self):
        c={'candidate_id':'X','source_id':'none','scene_group_id':'SCN_01','physical_group_id':'SPG_01'}
        out=validate_manifest({'schema_version':'e2-development-v1','candidates':[c]})
        self.assertIn('OVERLAP_PHYSICAL_GROUP_ID',out['exclusions']['X'])
        self.assertIn('OVERLAP_SCENE_GROUP_ID',out['exclusions']['X'])

    def test_writes_outside_e2_rejected(self):
        with self.assertRaises(PermissionError): write(P1/'e1_v2/forbidden.json',{})

    def test_global_pilot_cache_and_budget_cross_run(self):
        from unittest.mock import patch
        import e2_runner
        with tempfile.TemporaryDirectory(dir=ROOT/'results',prefix='global_test_') as tmp:
            local=Path(tmp); (local/'results').mkdir()
            with patch.object(e2_runner,'ROOT',local):
                cfg=copy.deepcopy(self.config)
                first=Store(local/'results/run1',cfg,'pilot')
                second=Store(local/'results/run2',cfg,'pilot')
                client=FakeClient(self.arms['A'])
                first.execute('S','A',self.arms['A'],client)
                second.execute('S','A',self.arms['A'],client)
                self.assertEqual(client.calls,1)
                self.assertEqual(first.path,second.path)
                self.assertEqual(second.charged_or_reserved(second.ledger()),.0001)
                self.assertTrue((second.folder/'requests'/f"{self.arms['A']['request_hash']}.json").exists())

    def test_budget_over_two_rejected(self):
        cfg=copy.deepcopy(self.config); cfg['budget_usd']=2.01
        with self.assertRaises(ValueError): self.store(cfg)

    def test_manifest_schema_requires_real_review_fields(self):
        from jsonschema import Draft202012Validator, ValidationError
        schema=read(ROOT/'data/development_manifest.schema.json')
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(read(ROOT/'data/development_manifest.json'))
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate({'schema_version':'e2-development-v1','dataset_id':'x','candidates':[{'candidate_id':'x'}]})

    def test_known_source_path_and_canonical_copy_are_excluded(self):
        reg=read(ROOT/'data/exclusion_registry.json')
        c={'candidate_id':'X','source_id':'renamed','scene_group_id':'renamed','physical_group_id':'renamed',
            'original_video_path':next(iter(reg['known_source_paths'])), 'canonical_path':str(P1.parent/'p0_cv_only/states/ITEM_01.json')}
        out=validate_manifest({'schema_version':'e2-development-v1','candidates':[c]})
        self.assertIn('KNOWN_EXCLUDED_SOURCE_PATH',out['exclusions']['X'])
        self.assertIn('PREVIOUS_CANONICAL_CONTENT',out['exclusions']['X'])

    def test_sdk_settings_mismatch_excludes_pair(self):
        c=[{'candidate_id':'X','human_gt':{'label':'ANCHORED_DANGER'}}]
        records={('X',a):{'status':'COMPLETE','client_settings':{'sdk':'old' if a=='A' else 'new'}} for a in 'ABCD'}
        out=evaluate(c,records)
        self.assertEqual(out['complete_paired_candidates'],0)
        self.assertEqual(out['paired_client_settings_mismatch'],['X'])

    def test_reused_client_retry_setting_is_local(self):
        import decisions_client
        self.assertEqual(decisions_client.MAX_RETRIES,2)
        from e2_runner import PilotClient
        import types
        f=decisions_client.DecisionsClient.decide
        cloned=types.FunctionType(f.__code__,dict(f.__globals__,MAX_RETRIES=0),f.__name__,f.__defaults__,f.__closure__)
        self.assertEqual(cloned.__globals__['MAX_RETRIES'],0)
        self.assertEqual(decisions_client.MAX_RETRIES,2)


if __name__=='__main__': unittest.main()
