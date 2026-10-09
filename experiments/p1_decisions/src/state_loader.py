"""Loads P0 Canonical CV States through the P1 input allowlist and validates them against the P0 schema."""
from jsonschema import Draft202012Validator

from utils import P0_ROOT, read_allowed_json

_validator = None


def load_cv_state(item_id):
    global _validator
    if _validator is None:
        _validator = Draft202012Validator(read_allowed_json(P0_ROOT / 'schemas' / 'canonical_cv_state.schema.json'))
    state = read_allowed_json(P0_ROOT / 'states' / f'{item_id}.json')
    errs = list(_validator.iter_errors(state))
    if errs:
        raise ValueError(f'{item_id}: P0 state fails cv-state-v1 schema: {errs[0].message}')
    return state
