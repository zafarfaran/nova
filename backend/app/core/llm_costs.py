"""LLM cost calculation utilities."""

# Pricing per 1M tokens (as of 2025)
# Update these prices as needed
LLM_PRICING = {
    "openai": {
        "gpt-4o": {
            "input": 2.50,   # $2.50 per 1M input tokens
            "output": 10.00,  # $10.00 per 1M output tokens
        },
    },
    "anthropic": {
        "claude-sonnet-4-20250514": {
            "input": 3.00,   # $3.00 per 1M input tokens
            "output": 15.00,  # $15.00 per 1M output tokens
        },
    },
}


def calculate_llm_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Calculate cost for an LLM call.
    
    Args:
        provider: AI provider name (openai, anthropic)
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Cost in USD
    """
    pricing = LLM_PRICING.get(provider, {}).get(model, {})
    if not pricing:
        return 0.0
    
    input_cost = (input_tokens / 1_000_000) * pricing.get("input", 0)
    output_cost = (output_tokens / 1_000_000) * pricing.get("output", 0)
    
    return input_cost + output_cost
