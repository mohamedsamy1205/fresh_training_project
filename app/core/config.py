from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    APP_NAME: str = "Task Manager API"
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    SERVER_METADATA_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = ".env"

settings = Settings()