"""Claude prices used by the cost meter (USD per million tokens).

tire-agent calls Claude through Amazon Bedrock's US inference profiles (`us.anthropic.*`, decision #156).
Haiku 5.5 rates come from the AWS Pricing API (AmazonBedrockFoundationModels, us-east-1, 2026-11-06),
regional/standard: input 0.11, output 0.55, cache read 0.011, 5-minute cache write 0.1375 (1.25x input),
1-hour cache write 2x input. Global profiles are 10% cheaper but had worse tail latency. Sonnet and Opus
apply the same 1.10 regional premium to first-party list prices and are used only for eval comparisons.
AWS Cost Explorer is the cross-check.
"""

from __future__ import annotations

PRICES = {  # model: (input, output, cache_read) on Bedrock US inference profiles
    "claude-haiku-5-5": (0.11, 0.55, 0.011),
    "claude-sonnet-5-5": (2.20, 11.00, 0.22),
    "claude-opus-5-5": (4.40, 22.00, 0.22),
}
CACHE_WRITE_5M_MULTIPLIER = 1.25
CACHE_WRITE_1H_MULTIPLIER = 2.0


def cost_usd(model: str, usage: dict) -> float:
    """Cost of one model call from LangChain `usage_metadata`. Unknown models raise (fail loudly)."""
    if model not in PRICES:
        raise KeyError(
            f"no price for {model!r}; add it to tire_agent/pricing.py"
        )
    p_in, p_out, p_cache = PRICES[model]
    details = usage.get("input_token_details") or {}
    cache_read = details.get("cache_read", 0) or 0
    # LangChain reports cache writes as ephemeral_5m/1h_input_tokens (cache_creation stays 0), on both
    # Anthropic and Bedrock. Older payloads only had cache_creation, so fall back to it.
    write_5m = details.get("ephemeral_5m_input_tokens")
    if write_5m is None:
        write_5m = details.get("cache_creation", 0) or 0
    write_1h = details.get("ephemeral_1h_input_tokens", 0) or 0
    fresh = max(usage.get("input_tokens", 0) - cache_read - write_5m - write_1h, 0)
    return (
        fresh * p_in
        + write_5m * p_in * CACHE_WRITE_5M_MULTIPLIER
        + write_1h * p_in * CACHE_WRITE_1H_MULTIPLIER
        + cache_read * p_cache
        + usage.get("output_tokens", 0) * p_out
    ) / 1e6
