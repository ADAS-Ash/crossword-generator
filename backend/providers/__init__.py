from .base import BaseProvider
from .mock import MockProvider
from backend.config import settings


def get_provider(name: str | None = None, api_key: str | None = None) -> BaseProvider:
    name = name or settings.llm_provider
    match name:
        case "gemini":
            from .gemini import GeminiProvider
            return GeminiProvider(api_key=api_key or settings.gemini_api_key)
        case "claude":
            from .claude import ClaudeProvider
            return ClaudeProvider(api_key=api_key or settings.anthropic_api_key)
        case "mock":
            return MockProvider()
        case _:
            raise ValueError(f"Unknown LLM provider: {name}")
