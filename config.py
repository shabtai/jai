"""Shared configuration for LLM agents."""

# Model configuration for different providers
# Note: gemini-3-flash-preview has a PydanticAI limitation with thought_signature in tool calls
# Using gemini-2.5-flash instead, which works properly with tools
MODEL_CONFIG = {
    "openai": "openai:gpt-4o-mini",
    "gemini": "gemini-2.5-flash",
}

# Environment variable names for API keys
API_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}


def validate_provider(provider: str) -> str:
    """
    Validate provider and return the model identifier.

    Args:
        provider: LLM provider ('openai' or 'gemini')

    Returns:
        Model identifier string

    Raises:
        ValueError: If provider is not supported
    """
    if provider not in MODEL_CONFIG:
        raise ValueError(f"Unsupported provider: {provider}. Must be 'openai' or 'gemini'")
    return MODEL_CONFIG[provider]


def set_api_key(provider: str, api_key: str) -> None:
    """
    Set the API key environment variable for the provider.

    Args:
        provider: LLM provider ('openai' or 'gemini')
        api_key: API key for the provider
    """
    import os
    env_var = API_KEY_ENV[provider]
    os.environ[env_var] = api_key
