from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    admin_username: str = "admin"
    admin_password: str = "admin123"
    secret_key: str = "change-me"
    database_url: str = "sqlite+aiosqlite:///data.db"
    cors_origins: list[str] = ["*"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
