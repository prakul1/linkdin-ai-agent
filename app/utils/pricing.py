"""OpenAI model pricing (USD per 1M tokens)."""
MODEL_PRICING = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "text-embedding-3-small": (0.02, 0.0),
    "text-embedding-3-large": (0.13, 0.0),
    "text-embedding-ada-002": (0.10, 0.0),
}
def calculate_cost(model: str, tokens_in: int, tokens_out: int = 0) -> float:
    if model not in MODEL_PRICING:
        return 0.0
    input_price, output_price = MODEL_PRICING[model]
    cost = (tokens_in / 1_000_000) * input_price + (tokens_out / 1_000_000) * output_price
    return round(cost, 8)