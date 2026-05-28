from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_ENV: str

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    STORAGE_ROOT: str = "backend/storage"

    model_config = SettingsConfigDict(
        env_file="backend/.env",
        extra="ignore"
    )


settings = Settings()
