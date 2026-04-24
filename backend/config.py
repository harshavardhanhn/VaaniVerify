from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    admin_username: str = "admin"
    admin_password: str = "admin123"
    auth_session_secret: str = "super-secret-key-12345"
    auth_session_ttl_minutes: int = 60

    app_name: str = "Automaton AI Voice Bot"
    app_env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8000
    
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "VaaniVerify"
    
    twilio_enabled: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    public_base_url: str = ""
    
    max_retries: int = 2
    default_language: str = "en"

    class Config:
        env_file = ".env"
        extra = "allow"

@lru_cache
def get_settings():
    return Settings()
