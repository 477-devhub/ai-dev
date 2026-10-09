"""Schema validation helpers: Canonical CV State schema + the benchmark's own prediction/result validators."""
import sys

from jsonschema import Draft202012Validator

from utils import BENCH_ROOT, STATE_SCHEMA_PATH, read_json

FORBIDDEN_STATE_KEYS = ('fight_detected', 'swoon_detected', 'trespass_detected', 'criminal_detected', 'dangerous_person',
                        'fall_detected', 'event_type', 'is_incident', 'physical_contact')

_validator = None


def state_validator():
    global _validator
    if _validator is None:
        schema = read_json(STATE_SCHEMA_PATH)
        Draft202012Validator.check_schema(schema)
        _validator = Draft202012Validator(schema)
    return _validator


def _keys(v, out):
    if isinstance(v, dict):
        for k, x in v.items():
            out.add(k)
            _keys(x, out)
    elif isinstance(v, list):
        for x in v:
            _keys(x, out)
    return out


def validate_state(state):
    errors = sorted(state_validator().iter_errors(state), key=lambda e: list(e.path))
    if errors:
        e = errors[0]
        raise ValueError(f"State schema error at {'/'.join(map(str, e.path))}: {e.message} ({len(errors)} errors)")
    bad = _keys(state, set()) & set(FORBIDDEN_STATE_KEYS)
    if bad:
        raise ValueError(f'Event-semantic keys in CV state: {sorted(bad)}')
    if state['input']['total_frames'] != 64 or sum(c['frame_count'] for c in state['cameras']) != 64:
        raise ValueError('State does not cover exactly 64 canonical frames')
    return True


def benchmark_validators():
    sys.path.insert(0, str(BENCH_ROOT / 'scripts'))
    import validate_prediction as vp
    return vp.validate, vp.validate_result
