"""Token counter using tiktoken — no API call needed."""
import tiktoken
from functools import lru_cache
@lru_cache(maxsize=8)
def _get_encoder(model: str):
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")
def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    if not text:
        return 0
    encoder = _get_encoder(model)
    return len(encoder.encode(text))