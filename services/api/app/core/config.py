from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./leadforge.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "development-only-change-me"
    google_places_api_key: str | None = None
    google_sheets_spreadsheet_id: str | None = None
    google_service_account_file: str | None = None
    groq_api_key: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
