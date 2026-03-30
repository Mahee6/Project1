from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    whatsapp_verify_token: str
    whatsapp_access_token: str
    whatsapp_phone_number_id: str
    whatsapp_app_secret: str

    azure_storage_connection_string: str
    azure_blob_container_name: str = "whatsapp-archive"

    frontend_url: str = "http://localhost:5173"
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
