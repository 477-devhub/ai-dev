"""P0 end-to-end runner: canonical frames -> Canonical CV State -> P0 rules -> prediction / result JSON."""
import json
import platform
import statistics
import time

from pose_detector import PoseDetector
from prediction_adapter import attention_prediction, multi_prediction, single_prediction
from rule_engine import RuleEngine
from state_builder import StateBuilder
from utils import (CV_CONFIG_PATH, EXP_ROOT, RULE_CONFIG_PATH, load_yaml, sha256_file)

PIPELINE_ACTUAL = 'p0_cv_only'
# result.schema.json (frozen) only allows pipeline in {vlm_only, cv_llm}; P0 is recorded under the
# CV-based enum value and identified as p0_cv_only in run_id, model_id and runtime_config.
PIPELINE_SCHEMA_VALUE = 'cv_llm'
RUN_ID = 'p0_cv_only-v1'


class P0Runner:
    def __init__(self):
        self.cv_cfg = load_yaml(CV_CONFIG_PATH)
        self.rules = load_yaml(RULE_CONFIG_PATH)
        t0 = time.perf_counter()
        self.detector = PoseDetector(self.cv_cfg)
        self.model_load_ms = self.detector.load_ms
        self.warmup_ms = self.detector.warmup()
        self.init_ms = (time.perf_counter() - t0) * 1000
        self.builder = StateBuilder(self.cv_cfg, self.detector)
        self.engine = RuleEngine(self.rules)

    @property
    def model_id(self):
        i = self.detector.info
        return f"{PIPELINE_ACTUAL}:{i['name']}@ultralytics-{i['library_version']}+rules-{self.rules['rule_version']}"

    def runtime_config(self):
        import torch
        i = self.detector.info
        return {
            'pipeline_actual': PIPELINE_ACTUAL,
            'pipeline_schema_value_note': 'result.schema.json enum allows only vlm_only/cv_llm; P0 uses cv_llm but NO LLM/VLM is called.',
            'llm_or_vlm_used': False,
            'external_api_calls': 0,
            'external_api_cost_usd': 0.0,
            'local_compute_cost_usd': None,
            'cv_model': i,
            'cv_config_file': 'configs/cv_state_v1.yaml',
            'cv_config_sha256': sha256_file(CV_CONFIG_PATH),
            'rule_config_file': 'configs/p0_v1.yaml',
            'rule_config_sha256': sha256_file(RULE_CONFIG_PATH),
            'cv_code_sha256': self.builder.code_sha256,
            'state_version': self.cv_cfg['state_version'],
            'state_schema': 'schemas/canonical_cv_state.schema.json',
            'state_schema_sha256': sha256_file(EXP_ROOT / 'schemas' / 'canonical_cv_state.schema.json'),
            'frame_source': 'benchmark_v1/scripts/load_model_input.py::iter_model_frames (uniform_total64_v1)',
            'tracking': 'per-camera timestamp-aware sparse association (Hungarian), no cross-camera identity',
            'latency_definition': 'steady-state end-to-end per item with model already loaded: canonical frame decode + CV inference + tracking/features + state build + rules + prediction serialization; median of repeated runs',
            'environment': {
                'os': platform.platform(), 'python': platform.python_version(), 'torch': torch.__version__,
                'cuda_available': torch.cuda.is_available(), 'cuda_version': torch.version.cuda,
                'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            },
        }

    def run_item(self, item_id, use_cache=False, keep_frames=False):
        import torch
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
        t_start = time.perf_counter()
        state, timings, audit, kept = self.builder.build(item_id, use_cache=use_cache, keep_frames=keep_frames)
        t0 = time.perf_counter()
        assessments = [self.engine.assess_camera(c) for c in state['cameras']]
        task = state['input']['task']
        if task == 'single':
            prediction = single_prediction(assessments[0])
        elif task == 'attention':
            prediction = attention_prediction(assessments, self.rules)
        else:
            prediction = multi_prediction(assessments, state['cross_camera'], state['cameras'], self.rules)
        timings['rule_engine_ms'] = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        serialized = json.dumps(prediction, ensure_ascii=False, allow_nan=False)
        timings['serialization_ms'] = (time.perf_counter() - t0) * 1000
        timings['total_ms'] = (time.perf_counter() - t_start) * 1000
        timings['vram_peak_mb'] = torch.cuda.max_memory_allocated() / 2**20 if torch.cuda.is_available() else None
        timings['frames_per_sec'] = audit['frames_consumed'] / (timings['total_ms'] / 1000)
        return {'state': state, 'prediction': json.loads(serialized), 'assessments': assessments,
                'timings': timings, 'audit': audit, 'kept_frames': kept}

    def result_json(self, item_id, prediction, benchmark_fingerprint, latency_ms, runtime_config):
        return {
            'benchmark_version': '477-reasoning-v1',
            'pipeline': PIPELINE_SCHEMA_VALUE,
            'run_id': RUN_ID,
            'item_id': item_id,
            'model_id': self.model_id,
            'runtime_config': runtime_config,
            'input_fingerprint': benchmark_fingerprint,
            'prediction': prediction,
            'human_grading': None,
            'latency_ms': latency_ms,
            'estimated_cost_usd': None,
            'input_tokens': None,
            'output_tokens': None,
        }


def latency_stats(values):
    return {'median_ms': statistics.median(values), 'min_ms': min(values), 'max_ms': max(values), 'n': len(values), 'runs_ms': values}
