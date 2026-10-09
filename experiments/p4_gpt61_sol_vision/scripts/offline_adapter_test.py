"""Offline (no API, no benchmark frames): synthetic frames + synthetic schema-valid outputs through raw visual adapter ->
frozen P1 adapter -> prediction -> common-adapter-v2 -> prediction schema, for single / attention / multi_camera;
cross-camera frame_ref must fail; schema frame_ref enums restricted per camera; lossless encode round-trip."""
import _bootstrap  # noqa: F401
import sys

from jsonschema import Draft202012Validator

import _synthetic
from image_encoder import encode_frames
from p4_pipeline import P4Pipeline
from raw_visual_adapter import FrameRefError


def synth(schema, v=0.37):
    if schema['type'] == 'object':
        return {k: synth(s, v) for k, s in schema['properties'].items()}
    if schema['type'] == 'array':
        return [synth(schema['items'], v)]
    if schema['type'] == 'string':
        return schema['enum'][0] if 'enum' in schema else 'synthetic text'
    return v


def main():
    p = P4Pipeline()
    ok = True
    for task in _synthetic.TASKS:
        try:
            fr = _synthetic.frames(task)
            urls, rows, _ = encode_frames(fr)
            cams = list(_synthetic.TASKS[task])
            tf = p.pb.text_format(task, cams, fr)
            Draft202012Validator.check_schema(tf['schema'])
            prep = {'task': task, 'cameras': cams, 'text_format': tf, 'table': {f['ref']: {'camera': f['camera'], 'timestamp_sec': f['timestamp_sec']} for f in fr}}
            parsed = synth(tf['schema'])
            final, d, raw, vis, meta, _ = p.adapt(prep, parsed, 'synthetic-offline')
            p.validate_prediction(final, task, cams)
            if task == 'attention':   # cite CAM_01 frame inside CAM_02 assessment -> must fail (schema and runtime)
                bad = synth(tf['schema'])
                bad['camera_assessments']['CAM_02']['evidence'][0]['frame_ref'] = 'F001'
                try:
                    p.adapt(prep, bad, 'x')
                    raise AssertionError('cross-camera frame_ref accepted')
                except Exception as e:
                    assert 'F001' in str(e) or isinstance(e, FrameRefError)
            print(f"{task}: PASS ({len(fr)} frames lossless {sum(r['roundtrip_equal'] for r in rows)}/{len(rows)}, rules {[a['rule'] for a in meta['assessments']]})")
        except Exception as e:
            ok = False
            print(f'{task}: FAIL {type(e).__name__}: {e}')
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
