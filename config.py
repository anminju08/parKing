import os
from typing import Optional

class Settings:
    # 공공 API 설정
    PUBLIC_API_KEY: str = "ldsUnAd0IgYlk/QbU7ax9Sw9G3h0d3Cn2gTWiwnfwC2F8u6BplOoG2f/DLqvR7DM7QBVL+82rOS/x+2u2EhOPA=="
    PUBLIC_API_BASE_URL: str = "https://api.example.com"  # 실제 공공 API URL로 교체 필요
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # 게임 설정
    MAX_PLAYERS_PER_ROOM: int = 10
    GAME_UPDATE_INTERVAL: int = 2  # seconds
    
    # 환경변수에서 설정 로드
    @classmethod
    def load_from_env(cls):
        cls.PUBLIC_API_KEY = os.getenv("PUBLIC_API_KEY", cls.PUBLIC_API_KEY)
        cls.PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", cls.PUBLIC_API_BASE_URL)
        cls.HOST = os.getenv("HOST", cls.HOST)
        cls.PORT = int(os.getenv("PORT", cls.PORT))
        cls.DEBUG = os.getenv("DEBUG", "true").lower() == "true"

settings = Settings()
settings.load_from_env()