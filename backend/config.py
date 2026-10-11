from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_provider: str = "mock"
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    admin_key: str = ""
    grid_size: int = 15
    word_count: int = 20
    rate_limit_per_day: int = 5
    adsense_publisher_id: str = ""
    gemini_model: str = "gemini-3.6-flash"
    # Comma-separated models tried in order on retries when the primary fails (blank = no fallback)
    gemini_fallback_models: str = "gemini-3.5-flash,gemini-3.5-flash-lite"
    # After a search-quota 429, generate without Google Search for this long
    gemini_search_cooldown_seconds: int = 600
    claude_model: str = "claude-sonnet-4-20250514"
    llm_max_attempts: int = 3
    llm_retry_base_delay: float = 1.0
    llm_timeout_seconds: float = 60.0
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
