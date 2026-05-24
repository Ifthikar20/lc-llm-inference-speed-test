from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    model: str = "deepseek-r1:14b"
    request_timeout: float = 300.0

    class Config:
        env_prefix = "LLM_"


settings = Settings()
