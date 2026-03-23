"""Shared utilities for aimux Claude Code hooks."""

from __future__ import annotations

# Pricing per token (USD) by model prefix
_PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4":   {"input": 15.00e-6, "output": 75.00e-6, "cache_write": 18.75e-6, "cache_read": 1.50e-6},
    "claude-sonnet-4": {"input":  3.00e-6, "output": 15.00e-6, "cache_write":  3.75e-6, "cache_read": 0.30e-6},
    "claude-haiku-4":  {"input":  0.80e-6, "output":  4.00e-6, "cache_write":  1.00e-6, "cache_read": 0.08e-6},
}
_DEFAULT_PRICING = _PRICING["claude-sonnet-4"]


def _pricing_for(model: str) -> dict[str, float]:
    for prefix, prices in _PRICING.items():
        if model.startswith(prefix):
            return prices
    return _DEFAULT_PRICING


def parse_transcript(path: str) -> dict:
    """Parse a Claude Code transcript JSONL and return aggregated usage stats.

    Returns:
        input_tokens, output_tokens, cost_usd, context_input_tokens, model
    """
    import json

    total_input = 0
    total_output = 0
    total_cost = 0.0
    last_context_tokens = 0
    model = "claude-sonnet-4-6"

    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if entry.get("type") != "assistant":
                    continue

                msg = entry.get("message", {})
                usage = msg.get("usage", {})
                if not usage:
                    continue

                entry_model = msg.get("model", model)
                if entry_model:
                    model = entry_model

                prices = _pricing_for(model)

                inp = usage.get("input_tokens", 0)
                out = usage.get("output_tokens", 0)
                cache_write = usage.get("cache_creation_input_tokens", 0)
                cache_read = usage.get("cache_read_input_tokens", 0)

                total_input += inp + cache_write + cache_read
                total_output += out
                total_cost += (
                    inp * prices["input"]
                    + out * prices["output"]
                    + cache_write * prices["cache_write"]
                    + cache_read * prices["cache_read"]
                )
                last_context_tokens = inp + cache_write + cache_read

    except (OSError, PermissionError):
        pass

    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "cost_usd": total_cost,
        "context_input_tokens": last_context_tokens,
        "model": model,
    }


def context_pct(context_input_tokens: int, model: str) -> float:
    """Estimate context window usage percentage."""
    window = 200_000  # All current Claude models have 200K context
    return min(100.0, (context_input_tokens / window) * 100)
