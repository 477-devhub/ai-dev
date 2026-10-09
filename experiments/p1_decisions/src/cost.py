"""External API cost from actual Decisions usage. Never estimated when usage or pricing linkage is unclear."""

PRICING = {
    'model': 'gpt-6-luna',
    'endpoint': '/v1/decisions',
    'service_tier': 'standard (default; no tier parameter sent)',
    'input_usd_per_1m_tokens': 0.10,
    'billing_rule': 'Decisions API: input tokens only; no cache-read, cache-write or output-token charges',
    'long_context_threshold_tokens': 272000,
    'long_context_input_multiplier': 2.0,
    'pricing_source': 'https://developers.openai.com/api/docs/guides/decisions (pricing paragraph: "input costs $0.10 per 1M tokens. You pay only for input tokens")',
    'pricing_cross_check': 'https://developers.openai.com/api/docs/models/gpt-6-luna lists Standard text rates input $0.10, cached $0.01, cache write $0.125, output $0.50 per 1M (chat endpoints); the Decisions-specific rule above was applied.',
    'pricing_checked_date': '2026-10-07',
    'regional_processing_premium_applied': False,
}


def external_api_cost_usd(usage):
    if not usage or usage.get('input_tokens') is None:
        return None
    n = usage['input_tokens']
    mult = PRICING['long_context_input_multiplier'] if n > PRICING['long_context_threshold_tokens'] else 1.0
    return round(n * PRICING['input_usd_per_1m_tokens'] * mult / 1_000_000, 10)
