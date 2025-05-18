from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "AudiobookBay Enhanced API"
    DEBUG: bool = False

    # AudiobookBay specific
    AUDIOBOOK_BAY_COOKIE: Optional[str] = None # Add your cookie here via .env

    # qBittorrent settings - will be populated from .env
    QBITTORRENT_HOST: str = "localhost"
    QBITTORRENT_PORT: int = 8080
    QBITTORRENT_USERNAME: str | None = None
    QBITTORRENT_PASSWORD: str | None = None
    QBITTORRENT_CATEGORY: str = "audiobooks"
    QBITTORRENT_SAVE_PATH_BASE: str = "/downloads/audiobooks/"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 