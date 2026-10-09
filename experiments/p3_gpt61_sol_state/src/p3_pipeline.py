"""P3 pipeline for one item: frozen compact state -> 1 Responses request (gpt-6.1-sol, high, strict JSON, no tools)
-> canonical raw decision -> frozen P1 decision adapter + templates -> common-adapter-v2 -> result.
Model input = frozen prompt/definitions + frozen compact state text only."""
import time

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from common_adapter_bridge import load_common_adapter_v2
from cost import PRICING, external_api_cost_usd
from openai_client import MAX_OUTPUT_TOKENS, MODEL, REASONING_EFFORT
from prediction_adapter import load_p1_decision_adapter, load_templates
from prompt_builder import PromptBuilder
from raw_decision_adapter import PROBABILITY_SOURCE, RawDecisionAdapter
from state_loader import load_input_fingerprint, load_state, verify_p1_freeze
from utils import BENCH_ROOT, P1_COMPACT_SCHEMA, P1_QUESTIONS_CONFIG, P3_CONFIG, canonical_json, load_json, read_allowed_json, sha256_bytes

CFG = load_json(P3_CONFIG)
RUN_ID, MODEL_ID = CFG['run_id'], CFG['model_id']


def semantic_names(task, cameras, qcfg):
    keys = [b['key'] for b in qcfg['per_assessment_questions']]
    if task == 'single':
        return keys
    if task == 'attention':
        return [c.lower().replace('_', '') + '_' + k for c in cameras for k in keys] + [b['key'] for b in qcfg['attention_questions']]
    return keys + [b['key'] for b in qcfg['multi_camera_questions']]


class P3Pipeline:
    def __init__(self, client=None):
        self.p1_freeze = verify_p1_freeze()
        self.qcfg = read_allowed_json(P1_QUESTIONS_CONFIG)
        self.pb = PromptBuilder()
        self.raw_adapter = RawDecisionAdapter(self.qcfg)
        da, self.da_sha = load_p1_decision_adapter(self.p1_freeze)
        self.adapter, self.index_answers = da.DecisionAdapter(self.qcfg), da.index_answers
        self.tpl, self.tpl_info = load_templates(self.p1_freeze)
        self.ca2, self.ca2_info = load_common_adapter_v2()
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
        task = st['compact']['task']
        cams = [c['camera'] for c in st['compact']['cameras']]
        st.update({'task': task, 'cameras': cams, 'input_fingerprint': load_input_fingerprint(item_id),
                   'instructions': self.pb.instructions(task, cams), 'text_format': self.pb.text_format(task, cams),
                   'names': semantic_names(task, cams, self.qcfg)})
        st['instructions_sha256'] = sha256_bytes(st['instructions'].encode('utf-8'))
        st['schema_sha256'] = sha256_bytes(canonical_json(st['text_format']).encode('utf-8'))
        st['load_ms'] = (time.perf_counter() - t0) * 1000
        return st

    def adapt(self, prep, parsed, model):
        """parsed=None -> refusal path. Returns (final_pred, v1_style_pred, decision, raw_canonical, ca2_meta, ms)."""
        t0 = time.perf_counter()
        if parsed is not None:
            Draft202012Validator(prep['text_format']['schema']).validate(parsed)
        answers, raw = self.raw_adapter.convert(prep['task'], parsed, prep['names'])
        ans = self.index_answers(answers)
        compact, task = prep['compact'], prep['task']
        if task == 'single':
            d = self.adapter.assessment(ans)
            pred = self.tpl.single_prediction(d, compact['cameras'], model)
        elif task == 'attention':
            d = self.adapter.attention(ans, prep['cameras'])
            pred = self.tpl.attention_prediction(d, compact, model, self.qcfg['adapter']['priority_weights'])
        else:
            d = self.adapter.multi(ans)
            pred = self.tpl.multi_prediction(d, compact, model)
        final, meta = self.ca2.apply(pred, d, task)
        return final, pred, d, raw, meta, (time.perf_counter() - t0) * 1000

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
        rec = self.client.decide(prep['instructions'], prep['state_text'], prep['text_format'], MODEL)
        out = {'item_id': item_id, 'prep': prep, 'api': rec}
        if rec['status'] not in ('ok', 'refusal'):
            out['status'] = 'FAILED'
            return out
        try:
            final, v1pred, decision, raw, meta, adapt_ms = self.adapt(prep, rec['parsed'] if rec['status'] == 'ok' else None, rec['model'] or MODEL)
        except Exception as e:   # strict-schema violation despite strict mode -> parse failure policy
            rec['status'] = 'parse_failure'
            rec['adapter_error'] = f'{type(e).__name__}: {str(e)[:300]}'
            out['status'] = 'FAILED'
            return out
        self.validate_prediction(final, prep['task'], prep['cameras'])
        u = rec['usage'] or {}
        det_in, det_out = u.get('input_tokens_details') or {}, u.get('output_tokens_details') or {}
        cost = external_api_cost_usd(u)
        api_ms = rec['timing']['last_attempt_ms']
        rc = {
            'pipeline_actual': CFG['pipeline_actual'],
            'pipeline_schema_value_note': 'result.schema.json enum allows only vlm_only/cv_llm; this is the P3 GPT-6.1 Sol state-reasoning pipeline.',
            'provider': CFG['provider'], 'decision_model': MODEL, 'decision_model_returned': rec['model'], 'decision_endpoint': CFG['endpoint'],
            'reasoning_effort': REASONING_EFFORT, 'reasoning_effort_returned': rec.get('reasoning_effort_returned'),
            'tools_enabled': [], 'tools_returned': rec.get('tools_returned'), 'store': False, 'max_output_tokens': MAX_OUTPUT_TOKENS,
            'structured_outputs': {'type': 'json_schema', 'strict': True, 'name': prep['text_format']['name'], 'schema_sha256': prep['schema_sha256']},
            'input_modality': 'text only (instructions + compact CV state); no images, no audio',
            'compact_state_version': prep['compact']['schema_version'], 'compact_state_sha256': prep['compact_sha256'],
            'state_text_sha256': prep['state_text_sha256'], 'instructions_sha256': prep['instructions_sha256'],
            'compact_state_source': f'experiments/p1_decisions/compact_states/{item_id}.json (P1 frozen bytes, read-only)',
            'decision_questions_version': self.qcfg['decision_questions_version'], 'p3_prompt_version': 'p3-prompt-v1',
            'requests_for_item': 1, 'response_status': rec['status'], 'refusal': rec.get('refusal'),
            'probability_source': PROBABILITY_SOURCE,
            'probability_source_note': CFG['probability_source_note'],
            'raw_decision_canonical': raw,
            'usage': {'input_tokens': u.get('input_tokens'), 'cached_input_tokens': det_in.get('cached_tokens'),
                      'cache_write_tokens': det_in.get('cache_write_tokens'), 'output_tokens': u.get('output_tokens'),
                      'reasoning_tokens': det_out.get('reasoning_tokens'), 'total_tokens': u.get('total_tokens')},
            'external_api_cost_usd': cost, 'pricing': PRICING,
            'latency': {
                'definition': 'cached-state timing only (frozen compact state reused): state -> GPT API -> adapter; NOT full end-to-end; result latency_ms left null',
                'state_load_ms': round(prep['load_ms'], 3),
                'request_total_ms': api_ms,
                'decision_api_total_including_retries_ms': rec['timing']['total_including_retries_ms'],
                'openai_processing_ms_header': rec.get('openai_processing_ms'),
                'adapter_ms': round(adapt_ms, 3),
                'cached_state_pipeline_ms': round(prep['load_ms'] + rec['timing']['total_including_retries_ms'] + adapt_ms, 2),
            },
            'retry_count': rec['retry_count'], 'refusal_count': 1 if rec['status'] == 'refusal' else 0, 'request_id': rec['request_id'],
            'decision_summary': _summ(decision, prep['task']),
            'v1_style_event_types': _event_types(v1pred, prep['task']),
            'common_adapter_v2': meta, 'common_adapter_v2_freeze': self.ca2_info,
            'adapter_provenance': {'decision_adapter_sha256': self.da_sha, 'templates': self.tpl_info},
            'raw_api_file': f'experiments/p3_gpt61_sol_state/raw_api/{item_id}.json',
            'llm_free_text_generation': False,
        }
        result = {
            'benchmark_version': '477-reasoning-v1', 'pipeline': CFG['pipeline_schema_value'], 'run_id': RUN_ID,
            'item_id': item_id, 'model_id': MODEL_ID, 'runtime_config': rc, 'input_fingerprint': prep['input_fingerprint'],
            'prediction': final, 'human_grading': None, 'latency_ms': None, 'estimated_cost_usd': None,
            'input_tokens': u.get('input_tokens'), 'output_tokens': u.get('output_tokens'),
        }
        self.result_validator.validate(result)
        out.update({'status': 'ok', 'prediction': final, 'decision': decision, 'result': result, 'cost': cost, 'raw_canonical': raw})
        return out


def raw_record(out):
    prep, api = out['prep'], out['api']
    return {
        'item_id': out['item_id'], 'status': api['status'],
        'request': {'endpoint': '/v1/responses', 'model': MODEL, 'reasoning': {'effort': REASONING_EFFORT}, 'tools': 'none (parameter not sent)',
                    'store': False, 'max_output_tokens': MAX_OUTPUT_TOKENS, 'input_modality': 'text',
                    'state_sha256': prep['state_text_sha256'], 'state_bytes': len(prep['state_text'].encode('utf-8')),
                    'compact_state_sha256': prep['compact_sha256'], 'instructions_sha256': prep['instructions_sha256'],
                    'instructions': prep['instructions'], 'text_format': prep['text_format'], 'text_format_sha256': prep['schema_sha256']},
        'response': {k: api.get(k) for k in ('http_status', 'request_id', 'openai_processing_ms', 'model', 'response_status', 'incomplete_details',
                                             'parsed', 'refusal', 'usage', 'reasoning_effort_returned', 'response_body')} if 'http_status' in api else None,
        'raw_decision_canonical': out.get('raw_canonical'),
        'errors': api.get('errors') or api.get('errors_before_success'), 'adapter_error': api.get('adapter_error'),
        'timing': api['timing'], 'retry_count': api['retry_count'],
        'final_prediction': out.get('prediction'),
        'note': 'Authorization header and API key are never recorded.',
    }


def _event_types(pred, task):
    if task == 'attention':
        return {a['camera']: a['assessment']['event_type'] for a in pred['assessments']}
    return pred['event_type']


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
