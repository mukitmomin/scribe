from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://scribe:scribe@db:5432/scribedb"
    google_api_key: str = ""
    use_mock_llm: bool = False
    multi_tenant_enabled: bool = False
    default_tenant_id: str = "default"
    cors_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
