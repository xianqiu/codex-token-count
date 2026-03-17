from __future__ import annotations

from ..config import PricingConfig


def estimate_cost(usage: dict[str, int], pricing: PricingConfig | None) -> dict[str, object] | None:
    if pricing is None:
        return None

    input_cost = round((usage["non_cached_input_tokens"] / 1_000_000) * pricing.input_per_million_usd, 2)
    cached_cost = round((usage["cached_input_tokens"] / 1_000_000) * pricing.cached_input_per_million_usd, 2)
    output_cost = round((usage["output_tokens"] / 1_000_000) * pricing.output_per_million_usd, 2)
    total_cost = round(input_cost + cached_cost + output_cost, 2)

    return {
        "currency": "USD",
        "input_cost_usd": input_cost,
        "cached_input_cost_usd": cached_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": total_cost,
        "pricing": {
            "input_per_million_usd": pricing.input_per_million_usd,
            "cached_input_per_million_usd": pricing.cached_input_per_million_usd,
            "output_per_million_usd": pricing.output_per_million_usd,
        },
    }
