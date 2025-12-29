"""LLM adapter package."""
from app.llm.base import (
    LLMProvider,
    LLMConfig,
    LLMResponse,
    Message,
    StreamChunk,
    PromptBuilder,
)
from app.llm.ollama_provider import (
    OllamaProvider,
    SESSION_PLAN_SCHEMA,
    ADAPTATION_RESPONSE_SCHEMA,
)

__all__ = [
    "LLMProvider",
    "LLMConfig",
    "LLMResponse",
    "Message",
    "StreamChunk",
    "PromptBuilder",
    "OllamaProvider",
    "SESSION_PLAN_SCHEMA",
    "ADAPTATION_RESPONSE_SCHEMA",
]


def get_llm_provider() -> LLMProvider:
    """
    Factory function to get the configured LLM provider.
    
    Returns the appropriate provider based on settings.
    Currently only Ollama is implemented; future providers
    (OpenAI, Anthropic, etc.) can be added here.
    """
    from app.config.settings import get_settings
    
    settings = get_settings()
    
    if settings.llm_provider == "ollama":
        return OllamaProvider()
    else:
        # Future: Add other providers
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
