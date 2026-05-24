from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    model: str = "llama3.1:8b"
    request_timeout: float = 300.0
    keep_alive: str = "10m"

    class Config:
        env_prefix = "LLM_"


settings = Settings()
