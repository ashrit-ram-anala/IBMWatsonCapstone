"""Application configuration management."""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "IBM Banking Data Pipeline"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:4200", "http://localhost:8080"]

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/banking_pipeline",
        description="PostgreSQL database connection URL"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # IBM Watsonx
    WATSONX_API_KEY: str = Field(default="", description="IBM Watsonx API Key")
    WATSONX_PROJECT_ID: str = Field(default="", description="Watsonx Project ID")
    WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"
    WATSONX_VERSION: str = "2024-01-01"

    # IBM Cloud
    IBM_CLOUD_API_KEY: str = Field(default="", description="IBM Cloud API Key")
    IBM_CLOUD_REGION: str = "us-south"

    # Watsonx.ai Model
    WATSONX_MODEL_ID: str = "ibm/granite-13b-chat-v2"
    WATSONX_MAX_TOKENS: int = 1000
    WATSONX_TEMPERATURE: float = 0.7

    # Storage
    UPLOAD_DIR: str = "./uploads"
    PROCESSED_DIR: str = "./processed"
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB

    # Security
    SECRET_KEY: str = Field(default="change-me-in-production", description="Secret key for JWT")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Pipeline Configuration
    MAX_CONCURRENT_PIPELINES: int = 5
    PIPELINE_TIMEOUT_SECONDS: int = 3600
    ANOMALY_DETECTION_THRESHOLD: float = 0.75

    # Data Validation
    REQUIRED_COLUMNS: List[str] = [
        "transaction_id",
        "customer_id",
        "amount",
        "date",
        "status"
    ]
    MAX_NULL_PERCENTAGE: float = 0.05

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    def create_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.PROCESSED_DIR, exist_ok=True)

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
settings.create_directories()
