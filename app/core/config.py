from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SRKASSE_",
        env_file=".env",
        extra="ignore",
    )

    database_url: str = Field(..., validation_alias="SRKASSE_DB_URL")
    secret_key: str = Field(..., validation_alias="SRKASSE_SECRET_KEY")
    access_token_expire_minutes: int = Field(
        60, validation_alias="SRKASSE_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    algorithm: str = Field("HS256", validation_alias="SRKASSE_ALGORITHM")


settings = Settings()
