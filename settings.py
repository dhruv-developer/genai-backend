from pydantic import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str
    MONGO_DB: str = "aml_db"
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_URL: str = "https://generativelanguage.googleapis.com/v1beta/models"
    SERVICE_NAME: str = "aml-service"
    MAX_ALERTS: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
