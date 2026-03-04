from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openrouter_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENROUTER_API_KEY", "OPENAI_API_KEY"),
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        validation_alias=AliasChoices("OPENROUTER_BASE_URL", "OPENAI_BASE_URL"),
    )
    openrouter_model: str = Field(
        default="openai/gpt-4o-mini",
        validation_alias=AliasChoices("OPENROUTER_MODEL", "OPENAI_MODEL"),
    )

    database_url: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/carousel_ai"

    minio_endpoint: str = "minio:9000"
    minio_public_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False

    assets_bucket: str = "carousel-assets"
    exports_bucket: str = "carousel-exports"

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")


settings = Settings()
