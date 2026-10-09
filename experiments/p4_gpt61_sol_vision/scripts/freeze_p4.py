"""Freeze P4-v1 after smoke + transport verification + schema checks + preflight PASS, before any benchmark request.
Writes freeze/p4_freeze.json (no overwrite)."""
import _bootstrap  # noqa: F401
import datetime
import glob
import sys

from common_adapter_bridge import load_common_adapter_v2
from process_log import log_event
from utils import EXP_ROOT, FREEZE_DIR, LOGS_DIR, RAW_DIR, RESULTS_DIR, load_json, sha256_file, write_json

FROZEN = ['configs/p4_v1.json', 'configs/visual_prompt_v1.txt', 'schemas/visual_single.schema.json', 'schemas/visual_attention.schema.json',
          'schemas/visual_multi.schema.json', 'src/image_encoder.py', 'src/visual_prompt_builder.py', 'src/raw_visual_adapter.py',
          'src/prediction_adapter.py',
          # additional files whose behaviour defines P4-v1 outputs
          'src/frame_loader.py', 'src/openai_client.py', 'src/p4_pipeline.py', 'src/common_adapter_bridge.py', 'src/cost.py',
          'src/utils.py', 'src/access_audit.py']


def main():
    gates = {'smoke': load_json(LOGS_DIR / 'smoke_test.json')['passed'],
             'transport': load_json(LOGS_DIR / 'transport_verification.json')['verdict'] == 'PASS',
             'preflight': load_json(LOGS_DIR / 'preflight.json')['verdict'] == 'PASS'}
    if not all(gates.values()):
        sys.exit(f'gates not passed: {gates}')
    out = FREEZE_DIR / 'p4_freeze.json'
    if out.exists():
        sys.exit('freeze/p4_freeze.json already exists; P4-v1 is frozen (create p4-v2 for changes)')
    if glob.glob(str(RAW_DIR / 'ITEM_*.json')) or (RESULTS_DIR.exists() and list(RESULTS_DIR.glob('run_*.json'))):
        sys.exit('benchmark outputs already exist; freeze must precede them')
    _, ca2 = load_common_adapter_v2()
    rec = {'p4_version': 'p4-v1', 'model': 'gpt-6.1-sol', 'endpoint': '/v1/responses', 'reasoning_effort': 'high', 'service_tier': 'default',
           'tools': [], 'store': False, 'image_detail': 'high', 'transport': 'lossless_webp q50 m2', 'frame_protocol': 'uniform_total64_v1',
           'frozen': True, 'frozen_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
           'gates': gates, 'hashes': {f: sha256_file(EXP_ROOT / f) for f in FROZEN},
           'transport_verification_sha256': sha256_file(LOGS_DIR / 'transport_verification.json'),
           'preflight_sha256': sha256_file(LOGS_DIR / 'preflight.json'),
           'common_adapter_v2_freeze': ca2,
           'benchmark_responses_seen_before_freeze': False, 'benchmark_frames_sent_to_api_before_freeze': False,
           'semantic_changes_after_benchmark_output': [],
           'pre_freeze_integration_fixes': ['src/access_audit.py: shell heredoc dropped a backslash (SyntaxError); restored before any API call'],
           'note': 'Any change to prompt/detail/transport/category/effort/sampling/frame count/evidence limit/threshold/adapter after benchmark output is P4-v2.'}
    write_json(out, rec)
    log_event('p4_frozen', {'file': 'freeze/p4_freeze.json'})
    print('FROZEN', out)
    for f, h in rec['hashes'].items():
        print(f'  {h}  {f}')


if __name__ == '__main__':
    main()
