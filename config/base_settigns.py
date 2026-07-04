__all__ = ('settings',)
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    API_ID: int
    API_HASH: str
    PHONE: str

    OPENAI_API_KEY: str
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=True,
    )


settings = AppConfig()
