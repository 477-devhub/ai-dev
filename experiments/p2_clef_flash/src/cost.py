"""External API cost from authoritative Clef-Flash usage only. Never estimated when usage is missing.

theoretical_unit_cost_usd = usage.input_tokens x published rate (USD per 1M input tokens; no output-token price).
actual_billed_cost_usd    = not observable per request (daily free Neuron allocation, account plan) -> null unless known.
"""
from utils import P2_CONFIG, load_json

PRICING = load_json(P2_CONFIG)['pricing']


def theoretical_cost_usd(usage):
    if not usage or not isinstance(usage.get('input_tokens'), int):
        return None
    return round(usage['input_tokens'] * PRICING['input_usd_per_1m_tokens'] / 1_000_000, 10)


def neurons(usage):
    if not usage or not isinstance(usage.get('input_tokens'), int):
        return None
    return round(usage['input_tokens'] * PRICING['neurons_per_1m_input_tokens'] / 1_000_000, 4)
