"""Shared utilities for aimux Claude Code and Codex hooks."""

# Pricing per token (USD) by model prefix
_PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4":   {"input": 15.00e-6, "output": 75.00e-6, "cache_write": 18.75e-6, "cache_read": 1.50e-6},
    "claude-sonnet-4": {"input":  3.00e-6, "output": 15.00e-6, "cache_write":  3.75e-6, "cache_read": 0.30e-6},
    "claude-haiku-4":  {"input":  0.80e-6, "output":  4.00e-6, "cache_write":  1.00e-6, "cache_read": 0.08e-6},
}
_DEFAULT_PRICING = _PRICING["claude-sonnet-4"]

# Pricing per token (USD) by model prefix, for Codex sessions
_CODEX_PRICING: dict[str, dict[str, float]] = {
    "gpt-5.1-codex": {"input": 1.25e-6, "output": 10.00e-6},
    "gpt-5-codex":   {"input": 1.25e-6, "output": 10.00e-6},
    "gpt-5.1":       {"input": 1.25e-6, "output": 10.00e-6},
    "gpt-5":         {"input": 1.25e-6, "output": 10.00e-6},
}
_CODEX_DEFAULT_PRICING = _CODEX_PRICING["gpt-5-codex"]
_CODEX_DEFAULT_CONTEXT_WINDOW = 272_000


def _pricing_for(model: str) -> dict[str, float]:
    for prefix, prices in _PRICING.items():
        if model.startswith(prefix):
            return prices
    return _DEFAULT_PRICING


def _codex_pricing_for(model: str) -> dict[str, float]:
    for prefix, prices in _CODEX_PRICING.items():
        if model.startswith(prefix):
            return prices
    return _CODEX_DEFAULT_PRICING


def parse_transcript(path: str) -> dict:
    """Parse a Claude Code or Codex transcript and return aggregated usage stats.

    Claude Code writes per-message JSONL entries that must be summed. Codex
    writes a rollout JSONL with a running `token_count` event whose totals
    are already cumulative, so the last one wins.

    Returns:
        input_tokens, output_tokens, cost_usd, context_input_tokens, context_window, model
    """
    import json

    total_input = 0
    total_output = 0
    total_cost = 0.0
    context_tokens = 0
    context_window = 200_000
    model = "claude-sonnet-4-6"
    seen_message_ids: set[str] = set()
    is_codex = False

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

                entry_type = entry.get("type")

                if entry_type == "turn_context":
                    is_codex = True
                    payload_model = entry.get("payload", {}).get("model")
                    if payload_model:
                        model = payload_model
                    continue

                if entry_type == "event_msg":
                    payload = entry.get("payload", {})
                    if payload.get("type") != "token_count":
                        continue
                    is_codex = True
                    info = payload.get("info") or {}
                    total_usage = info.get("total_token_usage", {})
                    total_input = total_usage.get("input_tokens", 0)
                    total_output = total_usage.get("output_tokens", 0)
                    context_tokens = info.get("last_token_usage", {}).get("total_tokens", 0)
                    context_window = info.get("model_context_window") or _CODEX_DEFAULT_CONTEXT_WINDOW
                    continue

                if entry_type != "assistant":
                    continue

                msg_id = entry.get("message", {}).get("id")
                if msg_id:
                    if msg_id in seen_message_ids:
                        continue
                    seen_message_ids.add(msg_id)

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
                context_tokens = inp + cache_write + cache_read
                context_window = 200_000

    except (OSError, PermissionError):
        pass

    if is_codex:
        prices = _codex_pricing_for(model)
        total_cost = total_input * prices["input"] + total_output * prices["output"]

    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "cost_usd": total_cost,
        "context_input_tokens": context_tokens,
        "context_window": context_window,
        "model": model,
    }


def context_pct(context_input_tokens: int, context_window: int) -> float:
    """Estimate context window usage percentage."""
    if context_window <= 0:
        return 0.0
    return min(100.0, (context_input_tokens / context_window) * 100)
