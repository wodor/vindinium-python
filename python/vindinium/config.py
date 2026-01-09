"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Server
    host: str = "localhost"
    port: int = 9000
    
    # Database
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "vindinium"
    
    # Security
    secret_key: str = "change-me-in-production"
    
    # Game
    default_max_turns: int = 300
    move_timeout_seconds: int = 10
    
    class Config:
        env_file = ".env"


settings = Settings()
