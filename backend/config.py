from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_api_key: str | None = None
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_provider: str = "Groq"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    @property
    def llm_configured(self) -> bool:
        key = (self.llm_api_key or "").strip()
        if not key:
            return False
        lowered = key.lower()
        return "your-key" not in lowered and lowered not in {"gsk_...", "sk-..."}


settings = Settings()
