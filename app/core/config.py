"""Application settings loaded from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://safecare:safecare@localhost:5432/safecare"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    dmdapi_base_url: str = "https://services.nhsbsa.nhs.uk/dmd-browser/"
    environment: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
