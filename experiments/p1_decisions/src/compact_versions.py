"""Explicit offline E2 input selection; no API/client imports or routing changes."""
from pathlib import Path

from jsonschema import Draft202012Validator

from compact_serializer import CompactSerializer
from compact_serializer_v2 import CompactSerializerV2
from utils import COMPACT_CONFIG, COMPACT_SCHEMA, load_json, load_yaml


def prepare_compact(state, version='v1'):
    if version not in ('v1', 'v2'):
        raise ValueError('version must be v1 or v2')
    cfg = load_yaml(COMPACT_CONFIG)
    serializer = CompactSerializer(cfg) if version == 'v1' else CompactSerializerV2(cfg)
    schema = COMPACT_SCHEMA if version == 'v1' else Path(__file__).resolve().parents[1] / 'schemas/compact_decision_state_v2.schema.json'
    compact = serializer.serialize(state)
    Draft202012Validator(load_json(schema)).validate(compact)
    return {'compact': compact, 'input_text': serializer.model_input_text(compact),
            'compact_sha256': serializer.digest(compact)}
