"""P1 pipeline for one item: cached P0 CV state -> compact state -> 1 Decisions API request -> prediction -> result."""
import time

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from compact_serializer import CompactSerializer
from cost import PRICING, external_api_cost_usd
from decision_adapter import DecisionAdapter, index_answers
from decisions_client import MODEL, build_questions
from prediction_adapter import attention_prediction, multi_prediction, single_prediction
from state_loader import load_cv_state
from utils import (BENCH_ROOT, COMPACT_CONFIG, COMPACT_SCHEMA, QUESTIONS_CONFIG, canonical_json, load_json, load_yaml,
                   read_allowed_json, sha256_bytes)

PIPELINE_ACTUAL = 'p1_openai_decisions'
PIPELINE_SCHEMA_VALUE = 'cv_llm'   # frozen result.schema.json enum allows only vlm_only/cv_llm
RUN_ID = 'p1_decisions-v1'
MODEL_ID = 'p1_decisions:gpt-6-luna@v1-decisions'


class P1Pipeline:
    def __init__(self, client=None):
        self.compact_cfg = load_yaml(COMPACT_CONFIG)
        self.qcfg = load_json(QUESTIONS_CONFIG)
        self.ser = CompactSerializer(self.compact_cfg)
        self.adapter = DecisionAdapter(self.qcfg)
        self.client = client
        self.compact_validator = Draft202012Validator(load_json(COMPACT_SCHEMA))
        pred = read_allowed_json(BENCH_ROOT / 'schemas' / 'prediction.schema.json')
        res = read_allowed_json(BENCH_ROOT / 'schemas' / 'result.schema.json')
        reg = Registry().with_resource(pred['$id'], Resource.from_contents(pred)).with_resource(res['$id'], Resource.from_contents(res))
        self.pred_schema, self.reg = pred, reg
        self.result_validator = Draft202012Validator(res, registry=reg)

    def prepare(self, item_id):
        state = load_cv_state(item_id)
        t0 = time.perf_counter()
        compact = self.ser.serialize(state)
        text = self.ser.model_input_text(compact)
        ser_ms = (time.perf_counter() - t0) * 1000
        errs = list(self.compact_validator.iter_errors(compact))
        if errs:
            raise ValueError(f'compact state invalid: {errs[0].message}')
        questions = build_questions(compact['task'], [c['camera'] for c in compact['cameras']], self.qcfg)
        return {'state': state, 'compact': compact, 'input_text': text, 'questions': questions, 'serializer_ms': ser_ms,
                'compact_sha256': sha256_bytes(canonical_json(compact).encode('utf-8'))}

    def adapt(self, compact, answers, model):
        t0 = time.perf_counter()
        ans = index_answers(answers)
        task = compact['task']
        if task == 'single':
            d = self.adapter.assessment(ans)
            pred, decision = single_prediction(d, compact['cameras'], model), d
        elif task == 'attention':
            att = self.adapter.attention(ans, [c['camera'] for c in compact['cameras']])
            pred, decision = attention_prediction(att, compact, model, self.qcfg['adapter']['priority_weights']), att
        else:
            d = self.adapter.multi(ans)
            pred, decision = multi_prediction(d, compact, model), d
        canonical_json(pred)
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
        rec = self.client.decide(prep['input_text'], prep['questions'], MODEL)
        out = {'item_id': item_id, 'prep': prep, 'api': rec}
        if rec['status'] != 'ok':
            out['status'] = 'FAILED'
            return out
        pred, decision, adapt_ms = self.adapt(compact, rec['answers'], rec['model'])
        cams = [c['camera'] for c in compact['cameras']]
        self.validate_prediction(pred, compact['task'], cams)
        usage = rec['usage']
        cost = external_api_cost_usd(usage)
        api_ms = rec['timing']['last_attempt_ms']
        refusals = sum(1 for a in rec['answers'] if a['type'] == 'refusal')
        rc = {
            'pipeline_actual': PIPELINE_ACTUAL,
            'pipeline_schema_value_note': 'result.schema.json enum allows only vlm_only/cv_llm; this is the P1 Decisions-API pipeline.',
            'decision_model': MODEL, 'decision_model_returned': rec['model'], 'decision_endpoint': '/v1/decisions',
            'input_modality': 'text only (compact CV state); no images',
            'compact_state_version': self.compact_cfg['schema_version'], 'compact_state_sha256': prep['compact_sha256'],
            'decision_questions_version': self.qcfg['decision_questions_version'], 'question_count': len(prep['questions']),
            'source_cv_state': f'experiments/p0_cv_only/states/{item_id}.json (cv-state-v1, P0 cached; CV not re-run)',
            'requests_for_item': 1,
            'usage': {
                'input_tokens': usage.get('input_tokens'),
                'cached_tokens': (usage.get('input_tokens_details') or {}).get('cached_tokens'),
                'cache_write_tokens': (usage.get('input_tokens_details') or {}).get('cache_write_tokens'),
                'output_tokens': usage.get('output_tokens'),
                'reasoning_tokens': (usage.get('output_tokens_details') or {}).get('reasoning_tokens'),
                'total_tokens': usage.get('total_tokens'),
                'compute_units': usage.get('compute_units'),
            },
            'external_api_cost_usd': cost, 'pricing': PRICING,
            'latency': {
                'definition': 'cached-state timing only (P0 CV state reused); NOT full end-to-end; result latency_ms left null',
                'serializer_latency_ms': round(prep['serializer_ms'], 3),
                'decision_api_latency_ms': api_ms,
                'decision_api_total_including_retries_ms': rec['timing']['total_including_retries_ms'],
                'openai_processing_ms_header': rec['openai_processing_ms'],
                'adapter_latency_ms': round(adapt_ms, 3),
                'cached_state_pipeline_latency_ms': round(prep['serializer_ms'] + rec['timing']['total_including_retries_ms'] + adapt_ms, 2),
            },
            'retry_count': rec['retry_count'], 'refusal_count': refusals, 'request_id': rec['request_id'],
            'decision_summary': _summ(decision, compact['task']),
            'raw_api_file': f'experiments/p1_decisions/raw_api/{item_id}.json',
            'llm_free_text_generation': False,
        }
        result = {
            'benchmark_version': '477-reasoning-v1', 'pipeline': PIPELINE_SCHEMA_VALUE, 'run_id': RUN_ID,
            'item_id': item_id, 'model_id': MODEL_ID, 'runtime_config': rc,
            'input_fingerprint': prep['state']['input']['benchmark_input_fingerprint'],
            'prediction': pred, 'human_grading': None, 'latency_ms': None, 'estimated_cost_usd': None,
            'input_tokens': usage.get('input_tokens'), 'output_tokens': usage.get('output_tokens'),
        }
        self.result_validator.validate(result)
        out.update({'status': 'ok', 'prediction': pred, 'decision': decision, 'result': result, 'cost': cost, 'refusals': refusals})
        return out


def raw_record(out):
    """Raw API record for raw_api/: request summary + full response body. Never contains headers or the API key."""
    prep, api = out['prep'], out['api']
    return {
        'item_id': out['item_id'],
        'status': api['status'],
        'request': {
            'endpoint': '/v1/decisions', 'model': MODEL, 'input_modality': 'text',
            'input_sha256': sha256_bytes(prep['input_text'].encode('utf-8')), 'input_bytes': len(prep['input_text'].encode('utf-8')),
            'compact_state_sha256': prep['compact_sha256'],
            'questions': [{'name': q['name'], 'type': q['type']} for q in prep['questions']],
        },
        'response': {k: api.get(k) for k in ('http_status', 'request_id', 'openai_processing_ms', 'model', 'answers', 'usage', 'response_body')} if api['status'] == 'ok' else None,
        'errors': api.get('errors') or api.get('errors_before_success'),
        'timing': api['timing'], 'retry_count': api['retry_count'],
        'adapted_prediction': out.get('prediction'),
        'note': 'Authorization header and API key are never recorded.',
    }


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
