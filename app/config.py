from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost/mha"
    SECRET_KEY: str = "changeme-dev-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALLOWED_IPS: list[str] = []

    class Config:
        env_file = ".env"

settings = Settings()
