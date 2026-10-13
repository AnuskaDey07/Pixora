"""Pixora configuration — env-driven via pydantic-settings."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Flask ---
    flask_env: str = Field(default="development", alias="FLASK_ENV")
    secret_key: str = Field(default="dev-secret-change-me", alias="SECRET_KEY")
    api_host_port: int = Field(default=5000, alias="API_HOST_PORT")

    # --- JWT ---
    jwt_secret_key: str = Field(default="dev-jwt-change-me", alias="JWT_SECRET_KEY")
    jwt_access_token_expires_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRES_MINUTES")
    jwt_refresh_token_expires_days: int = Field(default=14, alias="JWT_REFRESH_TOKEN_EXPIRES_DAYS")

    # --- Database ---
    database_url: str = Field(alias="DATABASE_URL")

    # --- Redis / Celery ---
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://redis:6379/1", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://redis:6379/2", alias="CELERY_RESULT_BACKEND")

    # --- MinIO / S3 ---
    minio_endpoint: str = Field(default="minio:9000", alias="MINIO_ENDPOINT")
    minio_root_user: str = Field(default="pixora", alias="MINIO_ROOT_USER")
    minio_root_password: str = Field(default="pixora_dev_minio", alias="MINIO_ROOT_PASSWORD")
    minio_use_ssl: bool = Field(default=False, alias="MINIO_USE_SSL")
    s3_bucket_uploads: str = Field(default="pixora-uploads", alias="S3_BUCKET_UPLOADS")
    s3_bucket_thumbs: str = Field(default="pixora-thumbs", alias="S3_BUCKET_THUMBS")
    s3_bucket_results: str = Field(default="pixora-results", alias="S3_BUCKET_RESULTS")
    s3_bucket_masks: str = Field(default="pixora-masks", alias="S3_BUCKET_MASKS")

    # --- Uploads ---
    max_content_length_mb: int = Field(default=50, alias="MAX_CONTENT_LENGTH_MB")
    allowed_image_mimes: str = Field(
        default="image/png,image/jpeg,image/webp",
        alias="ALLOWED_IMAGE_MIMES",
    )

    # --- ML ---
    ml_stub_mode: bool = Field(default=True, alias="ML_STUB_MODE")

    @property
    def allowed_mimes_set(self) -> set[str]:
        return {m.strip() for m in self.allowed_image_mimes.split(",") if m.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
