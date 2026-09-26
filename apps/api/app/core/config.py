from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    azure_search_endpoint: str = ""
    azure_search_api_key: str = ""
    azure_search_index: str = "resolveai-knowledge"
    azure_search_api_version: str = "2024-07-01"
    azure_semantic_config: str = "resolveai-semantic"
    coveo_org_id: str = ""
    coveo_api_key: str = ""
    coveo_source_id: str = ""
    coveo_source_name: str = "ResolveAI Knowledge"
    coveo_experiment_pipeline: str = ""
    coveo_push_base_url: str = "https://api.cloud.coveo.com"
    coveo_search_endpoint: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    cors_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
