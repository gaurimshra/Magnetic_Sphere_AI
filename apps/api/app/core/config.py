from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


API_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    app_name: str = "MagneticSphere AI"
    app_env: str = "development"
    frontend_origin: str = "http://localhost:3000"
    enable_live_integrations: bool = False

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "opportunity_memory"
    vector_size: int = 384

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str | None = None

    database_url: str = "sqlite:///./magneticsphere.db"
    redis_url: str = "redis://localhost:6379/0"

    slack_webhook_url: str | None = None
    slack_bot_token: str | None = None
    slack_channel_id: str | None = None
    hubspot_access_token: str | None = None
    hubspot_api_key: str | None = None
    hubspot_base_url: str = "https://api.hubapi.com"

    github_token: str | None = None
    github_api_url: str = "https://api.github.com"

    news_api_key: str | None = None
    news_api_url: str = "https://newsapi.org/v2/everything"
    news_api_page_size: int = 20
    external_request_timeout: float = 5.0
    news_rss_feeds: str = "https://techcrunch.com/tag/artificial-intelligence/feed/,https://www.prnewswire.com/news-releases/news-releases-list.rss"
    target_keywords: str = "AI,MLOps,cloud AI,automation,healthcare AI,computer vision,funding,hiring"
    target_companies_json: str | None = None

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", API_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def normalize_aliases(self) -> "Settings":
        if not self.hubspot_access_token and self.hubspot_api_key:
            self.hubspot_access_token = self.hubspot_api_key
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
