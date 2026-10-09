"""External API cost from actual Responses usage and the official Standard pricing recorded in configs/p4_v1.json.

uncached input = input_tokens - cached_tokens - cache_write_tokens (image tokens are inside provider input_tokens); output_tokens include reasoning tokens.
Returns None when usage is missing (never estimated).
"""
from utils import P4_CONFIG, load_json

PRICING = load_json(P4_CONFIG)['pricing']


def external_api_cost_usd(usage):
    if not usage or not isinstance(usage.get('input_tokens'), int) or not isinstance(usage.get('output_tokens'), int):
        return None
    det = usage.get('input_tokens_details') or {}
    cached, write = det.get('cached_tokens') or 0, det.get('cache_write_tokens') or 0
    n_in = usage['input_tokens']
    long = n_in > PRICING['long_context_threshold_tokens']
    mi = PRICING['long_context_multipliers']['input_and_cache'] if long else 1.0
    mo = PRICING['long_context_multipliers']['output'] if long else 1.0
    usd = ((n_in - cached - write) * PRICING['input_usd_per_1m_tokens'] * mi
           + cached * PRICING['cached_input_usd_per_1m_tokens'] * mi
           + write * PRICING['cache_write_usd_per_1m_tokens'] * mi
           + usage['output_tokens'] * PRICING['output_usd_per_1m_tokens'] * mo) / 1_000_000
    return round(usd, 10)
