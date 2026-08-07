from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AURA - Autonomous Unified Research Agent"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    SUPABASE_DB_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        description="Async PostgreSQL connection string for Supabase",
    )
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="", description="Supabase service role key")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    GEMINI_API_KEY: str = Field(default="", description="Gemini API key")
    DOCKER_IMAGE_NAME: str = Field(
        default="aura-agent-runner:latest",
        description="Docker image name for execution sandbox",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
