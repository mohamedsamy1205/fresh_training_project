from pydantic_settings import BaseSettings
from uuid import UUID

class Settings(BaseSettings):
    DATABASE_URL: str
    APP_NAME: str = "Task Manager API"
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    SERVER_METADATA_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    PUBLIC_KEY_PATH: str
    PRIVATE_KEY_PATH: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    MAIN_COMPANY_WALLET: UUID
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    OTEL_EXPORTER_OTLP_ENDPOINT: str
    OTEL_SERVICE_NAME: str

    class Config:
        env_file = ".env"

settings = Settings()