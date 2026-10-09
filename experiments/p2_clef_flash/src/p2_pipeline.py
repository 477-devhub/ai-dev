"""P2 pipeline for one item: frozen P1 compact state (read-only) -> 1 Clef-Flash request -> frozen P1 adapter -> result.

Model input = frozen compact state text + frozen semantic questions only. No P1/P0 outputs, labels or grading.
"""
import time

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from clef_adapter import ClefAnswerNormalizer, load_p1_decision_adapter
from cloudflare_client import MODEL, MODEL_SELECTOR, unwrap
from compact_state_loader import load_input_fingerprint, load_state, verify_p1_freeze
from cost import PRICING, neurons, theoretical_cost_usd
from prediction_adapter import load_templates
from question_adapter import QuestionAdapter
from utils import BENCH_ROOT, P1_COMPACT_SCHEMA, P1_QUESTIONS_CONFIG, P2_CONFIG, load_json, read_allowed_json, sha256_bytes

CFG = load_json(P2_CONFIG)
PIPELINE_ACTUAL = CFG['pipeline_actual']
PIPELINE_SCHEMA_VALUE = CFG['pipeline_schema_value']
RUN_ID = CFG['run_id']
MODEL_ID = CFG['model_id']


class P2Pipeline:
    def __init__(self, client=None):
        self.p1_freeze = verify_p1_freeze()
        self.p1_qcfg = read_allowed_json(P1_QUESTIONS_CONFIG)
        self.qa = QuestionAdapter(self.p1_qcfg)
        da_mod, self.decision_adapter_sha = load_p1_decision_adapter(self.p1_freeze)
        self.adapter = da_mod.DecisionAdapter(self.p1_qcfg)
        self.index_answers = da_mod.index_answers
        self.tpl, self.tpl_info = load_templates(self.p1_freeze)
        self.norm = ClefAnswerNormalizer()
        self.client = client
        self.compact_validator = Draft202012Validator(read_allowed_json(P1_COMPACT_SCHEMA))
        pred = read_allowed_json(BENCH_ROOT / 'schemas' / 'prediction.schema.json')
        res = read_allowed_json(BENCH_ROOT / 'schemas' / 'result.schema.json')
        reg = Registry().with_resource(pred['$id'], Resource.from_contents(pred)).with_resource(res['$id'], Resource.from_contents(res))
        self.pred_schema, self.reg = pred, reg
        self.result_validator = Draft202012Validator(res, registry=reg)

    def prepare(self, item_id):
        t0 = time.perf_counter()
        st = load_state(item_id, self.p1_freeze['compact_state_sha256'])
        errs = list(self.compact_validator.iter_errors(st['compact']))
        if errs:
            raise ValueError(f'compact state invalid: {errs[0].message}')
        cams = [c['camera'] for c in st['compact']['cameras']]
        st['input_fingerprint'] = load_input_fingerprint(item_id)   # harness metadata for the result file; never sent
        semantic, clef_q = self.qa.build(st['compact']['task'], cams)
        st.update({'semantic_questions': semantic, 'clef_questions': clef_q, 'cameras': cams,
                   'load_ms': (time.perf_counter() - t0) * 1000})
        return st

    def adapt(self, compact, norm_answers, model):
        t0 = time.perf_counter()
        ans = self.index_answers(norm_answers)
        task = compact['task']
        if task == 'single':
            d = self.adapter.assessment(ans)
            pred, decision = self.tpl.single_prediction(d, compact['cameras'], model), d
        elif task == 'attention':
            att = self.adapter.attention(ans, [c['camera'] for c in compact['cameras']])
            pred, decision = self.tpl.attention_prediction(att, compact, model, self.p1_qcfg['adapter']['priority_weights']), att
        else:
            d = self.adapter.multi(ans)
            pred, decision = self.tpl.multi_prediction(d, compact, model), d
        return pred, decision, (time.perf_counter() - t0) * 1000

    def validate_prediction(self, pred, task, cameras):
        branch = {'single': 'single', 'attention': 'attention', 'multi_camera': 'multi'}[task]
        Draft202012Validator({'$ref': self.pred_schema['$id'] + '#/$defs/' + branch}, registry=self.reg).validate(pred)
        if task == 'attention':
            assert {x['camera'] for x in pred['assessments']} == set(cameras)
            assert {x['camera'] for x in pred['attention_queue']} == set(cameras) and {x['rank'] for x in pred['attention_queue']} == {1, 2, 3}
        if task == 'multi_camera':
            assert set(pred['camera_evidence']) == set(cameras)

    def run(self, item_id):
        prep = self.prepare(item_id)
        compact = prep['compact']
        rec = self.client.run(prep['state_text'], prep['clef_questions'])
        out = {'item_id': item_id, 'prep': prep, 'api': rec}
        if rec['status'] != 'ok':
            out['status'] = 'FAILED'
            return out
        body = unwrap(rec['response_body'])
        schema_issues = self.norm.validate_response(body)
        t0 = time.perf_counter()
        norm, issues = self.norm.normalize(prep['semantic_questions'], body.get('answers'))
        norm_ms = (time.perf_counter() - t0) * 1000
        model_returned = body.get('model')
        pred, decision, adapt_ms = self.adapt(compact, norm, model_returned or MODEL)
        self.validate_prediction(pred, compact['task'], prep['cameras'])
        usage = body.get('usage') or {}
        u = {'input_tokens': usage.get('input_tokens') if isinstance(usage.get('input_tokens'), int) else None,
             'output_tokens': usage.get('output_tokens') if isinstance(usage.get('output_tokens'), int) else None,
             'raw_usage_object': usage or None}
        cost = theoretical_cost_usd(u)
        api_ms = rec['timing']['last_attempt_ms']
        invalid = sum(1 for a in norm if a['type'] == 'refusal')
        rc = {
            'pipeline_actual': PIPELINE_ACTUAL,
            'pipeline_schema_value_note': 'result.schema.json enum allows only vlm_only/cv_llm; this is the P2 Clef-Flash pipeline.',
            'provider': CFG['provider'], 'decision_model': MODEL, 'model_input_selector': MODEL_SELECTOR,
            'decision_model_returned': model_returned, 'decision_endpoint': CFG['endpoint'], 'ai_gateway': False,
            'input_modality': 'text only (compact CV state string); no images',
            'compact_state_version': compact['schema_version'], 'compact_state_sha256': prep['compact_sha256'],
            'state_text_sha256': prep['state_text_sha256'],
            'compact_state_source': f'experiments/p1_decisions/compact_states/{item_id}.json (P1 frozen bytes, read-only; CV not re-run)',
            'decision_questions_version': self.p1_qcfg['decision_questions_version'],
            'clef_questions_version': self.qa.cfg['clef_questions_version'], 'question_count': len(prep['clef_questions']),
            'requests_for_item': 1,
            'usage': u, 'neurons_derived_from_published_rate': neurons(u),
            'external_api_cost_usd': cost,
            'theoretical_unit_cost_usd': cost,
            'actual_billed_cost_usd': None,
            'actual_billed_cost_note': 'not observable per request (Workers AI daily free Neuron allocation / account plan); not mixed with theoretical cost',
            'pricing': PRICING,
            'latency': {
                'definition': 'cached-state timing only (frozen compact state reused); NOT full end-to-end; result latency_ms left null',
                'state_load_ms': round(prep['load_ms'], 3),
                'request_total_ms': api_ms,
                'decision_api_latency_ms': api_ms,
                'decision_api_total_including_retries_ms': rec['timing']['total_including_retries_ms'],
                'provider_timing': rec.get('response_headers_subset', {}).get('server-timing'),
                'adapter_ms': round(norm_ms + adapt_ms, 3),
                'cached_state_pipeline_ms': round(prep['load_ms'] + rec['timing']['total_including_retries_ms'] + norm_ms + adapt_ms, 2),
            },
            'retry_count': rec['retry_count'], 'invalid_or_missing_answer_count': invalid, 'answer_issues': issues,
            'response_schema_issues': schema_issues, 'cf_ray': rec.get('cf_ray'),
            'adapter_provenance': {'decision_adapter': 'experiments/p1_decisions/src/decision_adapter.py (frozen bytes)',
                                   'decision_adapter_sha256': self.decision_adapter_sha, 'templates': self.tpl_info,
                                   'category_reconciliation': 'none (P1-v1 behaviour preserved)'},
            'decision_summary': _summ(decision, compact['task']),
            'raw_api_file': f'experiments/p2_clef_flash/raw_api/{item_id}.json',
            'llm_free_text_generation': False,
        }
        result = {
            'benchmark_version': '477-reasoning-v1', 'pipeline': PIPELINE_SCHEMA_VALUE, 'run_id': RUN_ID,
            'item_id': item_id, 'model_id': MODEL_ID,
            'runtime_config': rc,
            'input_fingerprint': prep['input_fingerprint'],
            'prediction': pred, 'human_grading': None, 'latency_ms': None, 'estimated_cost_usd': None,
            'input_tokens': u['input_tokens'], 'output_tokens': u['output_tokens'],
        }
        out.update({'status': 'ok', 'prediction': pred, 'decision': decision, 'result': result, 'cost': cost,
                    'normalized_answers': norm, 'invalid': invalid, 'raw_model_output': body})
        return out


def raw_record(out):
    """raw_api/ record: request summary (no headers/credentials) + full response body + normalized answers."""
    prep, api = out['prep'], out['api']
    return {
        'item_id': out['item_id'], 'status': api['status'],
        'request': {
            'endpoint': CFG['endpoint'], 'model': MODEL, 'model_selector': MODEL_SELECTOR, 'input_modality': 'text',
            'state_sha256': prep['state_text_sha256'], 'state_bytes': len(prep['state_text'].encode('utf-8')),
            'compact_state_sha256': prep['compact_sha256'],
            'questions': [{'id': k, 'type': v['type']} for k, v in prep['clef_questions'].items()],
            'questions_sha256': sha256_bytes(_cj(prep['clef_questions']).encode('utf-8')),
        },
        'response': {'http_status': api.get('http_status'), 'cf_ray': api.get('cf_ray'),
                     'headers_subset': api.get('response_headers_subset'), 'body': api.get('response_body')} if api['status'] == 'ok' else None,
        'normalized_answers': out.get('normalized_answers'),
        'errors': api.get('errors') or api.get('errors_before_success'),
        'timing': api['timing'], 'retry_count': api['retry_count'],
        'adapted_prediction': out.get('prediction'),
        'note': 'Authorization header, API token and account id are never recorded.',
    }


def _cj(v):
    from utils import canonical_json
    return canonical_json(v)


def _summ(decision, task):
    def one(d):
        return {k: d[k] for k in ('p_incident', 'is_incident', 'category', 'category_confidence', 'risk', 'priority_score',
                                  'confidence', 'p_human_review', 'human_review_required', 'refused_questions')}
    if task == 'attention':
        return {'per_camera': {c: one(d) for c, d in decision['per_camera'].items()}, 'order': decision['order'],
                'attention_first_supplementary': decision['attention_first_supplementary']}
    s = one(decision)
    if task == 'multi_camera':
        s.update({k: decision[k] for k in ('p_same_incident', 'same_incident', 'p_second_view_adds', 'second_view_adds', 'multiview_value')})
    return s
