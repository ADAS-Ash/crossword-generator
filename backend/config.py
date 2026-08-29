from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_provider: str = "mock"
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    admin_key: str = ""
    grid_size: int = 15
    word_count: int = 20

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
