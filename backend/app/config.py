from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./settleit.db"
    secret_key: str = "change-me-in-prod-settleit-default-key"
    token_expire_hours: int = 24
    cors_origins: str = "*"

    submission_seconds: int = 60
    voting_seconds: int = 45
    min_players: int = 2
    max_players: int = 20
    max_options_per_player: int = 5
    fuzzy_threshold: int = 85


settings = Settings()
