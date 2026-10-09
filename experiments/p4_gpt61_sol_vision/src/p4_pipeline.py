"""P4 pipeline for one item: canonical 64 frames (iter_model_frames) -> lossless WebP data URLs (in memory, round-trip
verified) -> 1 Responses request (gpt-6.1-sol, high, strict JSON, no tools, store=false) -> raw visual adapter ->
frozen P1 decision adapter -> prediction -> common-adapter-v2 -> validated result.
Model input = generic visual prompt + 64 frames + generic frame labels + schema only (no CV/compact state, no item id).
latency_ms in the result = full P4 path (frame decode start -> final prediction validation)."""
import time

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from common_adapter_bridge import load_common_adapter_v2
from cost import PRICING, external_api_cost_usd
from frame_loader import item_task, load_frames
from image_encoder import DETAIL, encode_frames
from openai_client import MAX_OUTPUT_TOKENS, MODEL, REASONING_EFFORT
from prediction_adapter import attention_prediction, load_p1_decision_adapter, multi_prediction, single_prediction
from raw_visual_adapter import PROBABILITY_SOURCE, RawVisualAdapter
from utils import BENCH_ROOT, P1_FREEZE, P1_QUESTIONS_CONFIG, P4_CONFIG, canonical_json, load_json, read_allowed_json, sha256_bytes
from visual_prompt_builder import VisualPromptBuilder

CFG = load_json(P4_CONFIG)
RUN_ID, MODEL_ID = CFG['run_id'], CFG['model_id']
PLACEHOLDER = '__set_by_common_adapter_v2__'


class P4Pipeline:
    def __init__(self, client=None):
        self.p1_freeze = read_allowed_json(P1_FREEZE)
        self.qcfg = read_allowed_json(P1_QUESTIONS_CONFIG)
        if sha256_bytes(P1_QUESTIONS_CONFIG.read_bytes()) != self.p1_freeze['hashes']['configs/decisions_questions_v1.json']:
            raise RuntimeError('P1 questions config differs from p1_freeze.json')
        self.pb = VisualPromptBuilder()
        self.raw_adapter = RawVisualAdapter(self.qcfg)
        da, self.da_sha = load_p1_decision_adapter(self.p1_freeze)
        self.adapter, self.index_answers = da.DecisionAdapter(self.qcfg), da.index_answers
        self.ca2, self.ca2_info = load_common_adapter_v2()
        self.client = client
        pred = read_allowed_json(BENCH_ROOT / 'schemas' / 'prediction.schema.json')
        res = read_allowed_json(BENCH_ROOT / 'schemas' / 'result.schema.json')
        reg = Registry().with_resource(pred['$id'], Resource.from_contents(pred)).with_resource(res['$id'], Resource.from_contents(res))
        self.pred_schema, self.reg = pred, reg
        self.result_validator = Draft202012Validator(res, registry=reg)

    def prepare(self, item_id):
        """Decode + encode + build request. Returns prep dict (data URLs kept in memory only)."""
        frames, decode_ms, per_cam, fp = load_frames(item_id)
        urls, rows, enc_t = encode_frames(frames)
        t0 = time.perf_counter()
        cams = list(per_cam)
        task = item_task(item_id)
        content = self.pb.content(task, cams, frames, urls, DETAIL)
        tf = self.pb.text_format(task, cams, frames)
        req_text = self.pb.request_text(content)
        build_ms = (time.perf_counter() - t0) * 1000
        table = {f['ref']: {'camera': f['camera'], 'timestamp_sec': f['timestamp_sec']} for f in frames}
        for f in frames:
            f.pop('rgb24')   # free pixel memory; hashes kept
        payload_bytes = sum(len(u) for u in urls) + len(req_text.encode('utf-8')) + len(canonical_json(tf))
        return {'item_id': item_id, 'task': task, 'cameras': cams, 'per_camera_frames': per_cam, 'frames': frames, 'table': table,
                'content': content, 'text_format': tf, 'request_text': req_text, 'manifest_rows': rows, 'input_fingerprint': fp,
                'request_text_sha256': sha256_bytes(req_text.encode('utf-8')), 'schema_sha256': sha256_bytes(canonical_json(tf).encode('utf-8')),
                'payload_bytes_estimate': payload_bytes,
                'timing': {'frame_decode_ms': round(decode_ms, 2), **enc_t, 'request_build_ms': round(build_ms, 2)}}

    def adapt(self, prep, parsed, model):
        t0 = time.perf_counter()
        Draft202012Validator(prep['text_format']['schema']).validate(parsed)
        answers, raw, vis = self.raw_adapter.convert(prep['task'], parsed, prep['cameras'], prep['table'])
        ans = self.index_answers(answers)
        task, cams = prep['task'], prep['cameras']
        if task == 'single':
            d = self.adapter.assessment(ans)
            pred = single_prediction(d, vis['single'], PLACEHOLDER)
        elif task == 'attention':
            d = self.adapter.attention(ans, cams)
            pred = attention_prediction(d, vis, cams, self.qcfg['adapter']['priority_weights'])
        else:
            d = self.adapter.multi(ans)
            pred = multi_prediction(d, vis, cams)
        final, meta = self.ca2.apply(pred, d, task)
        if PLACEHOLDER in canonical_json(final):
            raise RuntimeError('event_type placeholder survived common-adapter-v2')
        return final, d, raw, vis, meta, (time.perf_counter() - t0) * 1000

    def validate_prediction(self, pred, task, cameras):
        branch = {'single': 'single', 'attention': 'attention', 'multi_camera': 'multi'}[task]
        Draft202012Validator({'$ref': self.pred_schema['$id'] + '#/$defs/' + branch}, registry=self.reg).validate(pred)
        if task == 'attention':
            assert {x['camera'] for x in pred['assessments']} == set(cameras)
            assert {x['camera'] for x in pred['attention_queue']} == set(cameras) and {x['rank'] for x in pred['attention_queue']} == {1, 2, 3}
            for a in pred['assessments']:
                assert all(o['camera'] == a['camera'] for o in a['assessment']['observations']), 'camera attribution'
        if task == 'multi_camera':
            assert set(pred['camera_evidence']) == set(cameras)
            assert all(o['camera'] == c for c, obs in pred['camera_evidence'].items() for o in obs), 'camera attribution'

    def run(self, item_id):
        t_full = time.perf_counter()
        prep = self.prepare(item_id)
        rec = self.client.decide(prep['content'], prep['text_format'], MODEL)
        out = {'item_id': item_id, 'prep': prep, 'api': rec}
        if rec['status'] != 'ok':
            out['status'] = 'FAILED'
            return out
        try:
            final, decision, raw, vis, meta, adapt_ms = self.adapt(prep, rec['parsed'], rec['model'] or MODEL)
            self.validate_prediction(final, prep['task'], prep['cameras'])
        except Exception as e:
            rec['status'] = 'schema_or_frame_ref_failure'
            rec['adapter_error'] = f'{type(e).__name__}: {str(e)[:400]}'
            out['status'] = 'FAILED'
            return out
        full_ms = (time.perf_counter() - t_full) * 1000
        u = rec['usage'] or {}
        di, do = u.get('input_tokens_details') or {}, u.get('output_tokens_details') or {}
        cost = external_api_cost_usd(u)
        t = prep['timing']
        rc = {
            'pipeline_actual': CFG['pipeline_actual'], 'pipeline_schema_value_note': 'result.schema.json enum vlm_only/cv_llm; P4 is VLM-only',
            'provider': 'openai', 'model': MODEL, 'decision_model_returned': rec['model'], 'endpoint': CFG['endpoint'],
            'reasoning_effort': REASONING_EFFORT, 'reasoning_effort_returned': rec.get('reasoning_effort_returned'),
            'service_tier_requested': 'default (not sent)', 'service_tier_returned': rec.get('service_tier'),
            'tools_enabled': [], 'tools_returned': rec.get('tools_returned'), 'store': False, 'max_output_tokens': MAX_OUTPUT_TOKENS,
            'input_modality': 'vision', 'frame_protocol': 'uniform_total64_v1', 'canonical_loader': 'benchmark_v1/scripts/load_model_input.py iter_model_frames',
            'total_images': len(prep['frames']), 'images_per_camera': prep['per_camera_frames'], 'image_detail': DETAIL,
            'transport': 'lossless_webp', 'lossless_roundtrip_verified': f"{sum(r['roundtrip_equal'] for r in prep['manifest_rows'])}/{len(prep['manifest_rows'])}",
            'cv_state_sent': False, 'compact_state_sent': False, 'common_adapter': 'v2',
            'structured_outputs': {'type': 'json_schema', 'strict': True, 'name': prep['text_format']['name'], 'schema_sha256': prep['schema_sha256']},
            'request_text_sha256': prep['request_text_sha256'], 'payload_bytes_estimate': prep['payload_bytes_estimate'],
            'frame_manifest_file': f'experiments/p4_gpt61_sol_vision/logs/frame_manifest_{item_id}.json',
            'probability_source': PROBABILITY_SOURCE, 'raw_decision_canonical': raw,
            'visual_evidence_resolved': vis,
            'usage': {'input_tokens': u.get('input_tokens'), 'cached_input_tokens': di.get('cached_tokens'), 'cache_write_tokens': di.get('cache_write_tokens'),
                      'output_tokens': u.get('output_tokens'), 'reasoning_tokens': do.get('reasoning_tokens'), 'total_tokens': u.get('total_tokens')},
            'external_api_cost_usd': cost, 'pricing': PRICING,
            'latency': {'definition': 'full P4 visual path: iter_model_frames start -> final prediction validation (includes encode, round-trip check, base64, upload, provider processing, adapter)',
                        **t, 'api_request_total_ms': rec['timing']['total_including_retries_ms'], 'api_last_attempt_ms': rec['timing']['last_attempt_ms'],
                        'openai_processing_ms_header': rec.get('openai_processing_ms'), 'adapter_ms': round(adapt_ms, 3), 'full_pipeline_ms': round(full_ms, 2)},
            'retry_count': rec['retry_count'], 'request_id': rec['request_id'],
            'decision_summary': _summ(decision, prep['task']), 'common_adapter_v2': meta, 'common_adapter_v2_freeze': self.ca2_info,
            'decision_adapter_sha256': self.da_sha, 'raw_api_file': f'experiments/p4_gpt61_sol_vision/raw_api/{item_id}.json',
        }
        result = {'benchmark_version': '477-reasoning-v1', 'pipeline': CFG['pipeline_schema_value'], 'run_id': RUN_ID, 'item_id': item_id,
                  'model_id': MODEL_ID, 'runtime_config': rc, 'input_fingerprint': prep['input_fingerprint'], 'prediction': final,
                  'human_grading': None, 'latency_ms': round(full_ms, 2), 'estimated_cost_usd': None,
                  'input_tokens': u.get('input_tokens'), 'output_tokens': u.get('output_tokens')}
        self.result_validator.validate(result)
        out.update({'status': 'ok', 'prediction': final, 'decision': decision, 'result': result, 'raw_canonical': raw})
        return out


def frame_manifest(prep):
    return {'item_id_harness_only': prep['item_id'], 'protocol': 'uniform_total64_v1', 'task': prep['task'], 'images_per_camera': prep['per_camera_frames'],
            'total_images': len(prep['manifest_rows']), 'detail': DETAIL, 'transport': 'lossless_webp', 'base64_payload_stored': False,
            'payload_bytes_estimate': prep['payload_bytes_estimate'], 'frames': prep['manifest_rows']}


def raw_record(out):
    prep, api = out['prep'], out['api']
    body = api.get('response_body')
    return {'item_id': out['item_id'], 'status': api['status'],
            'request': {'endpoint': '/v1/responses', 'model': MODEL, 'reasoning': {'effort': REASONING_EFFORT}, 'tools': 'none (parameter not sent)',
                        'store': False, 'service_tier': 'not sent (default)', 'max_output_tokens': MAX_OUTPUT_TOKENS,
                        'message': 'one user message: 1 task input_text + 64 x (frame label input_text, input_image detail=high)',
                        'request_text_file': f"logs/request_text_{out['item_id']}.txt", 'request_text_sha256': prep['request_text_sha256'],
                        'images': f"{len(prep['manifest_rows'])} lossless WebP data URLs (payloads not stored; see logs/frame_manifest_{out['item_id']}.json)",
                        'text_format': prep['text_format'], 'text_format_sha256': prep['schema_sha256']},
            'response': {k: api.get(k) for k in ('http_status', 'request_id', 'openai_processing_ms', 'model', 'response_status', 'incomplete_details',
                                                 'service_tier', 'parsed', 'refusal', 'usage', 'reasoning_effort_returned')} | {'response_body': body} if 'http_status' in api else None,
            'raw_decision_canonical': out.get('raw_canonical'), 'errors': api.get('errors') or api.get('errors_before_success'),
            'adapter_error': api.get('adapter_error'), 'timing': {**prep['timing'], 'api': api['timing']}, 'retry_count': api['retry_count'],
            'final_prediction': out.get('prediction'), 'note': 'Authorization header, API key and image base64 payloads are never recorded.'}


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
