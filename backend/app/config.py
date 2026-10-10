from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Nebius Token Factory Configuration
    nebius_base_url: str = Field(
        default="https://api.tokenfactory.us-central1.nebius.com/v1/",
        validation_alias="NEBIUS_BASE_URL"
    )
    nebius_api_key: Optional[str] = Field(
        default=None,
        validation_alias="NEBIUS_API_KEY"
    )
    nebius_model: str = Field(
        default="nvidia/Nemotron-3-Ultra-550b-a55b",
        validation_alias="NEBIUS_MODEL"
    )

    # Server Configuration
    host: str = Field(default="127.0.0.1", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    debug: bool = Field(default=False, validation_alias="DEBUG")

    # Guardrails and Limits
    max_repair_attempts: int = Field(default=2, validation_alias="MAX_REPAIR_ATTEMPTS")
    test_timeout_seconds: int = Field(default=60, validation_alias="TEST_TIMEOUT_SECONDS")
    max_model_calls_per_task: int = Field(default=8, validation_alias="MAX_MODEL_CALLS_PER_TASK")

settings = Settings()
