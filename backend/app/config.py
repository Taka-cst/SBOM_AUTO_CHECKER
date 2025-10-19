import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # アプリケーション設定
    APP_NAME: str = "SBOM Vulnerability Checker"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # データベース設定
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "sbom_checker"
    POSTGRES_USER: str = "sbom_admin"
    POSTGRES_PASSWORD: str = "password"
    
    # Redis設定
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    # バックエンドAPI設定
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_WORKERS: int = 4
    
    # セキュリティ設定
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    
    # ファイルアップロード設定
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB
    UPLOAD_DIR: str = "/app/uploads"
    
    # NVD API設定
    NVD_API_KEY: Optional[str] = None
    NVD_API_URL: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    # スキャナー設定
    SCANNER_UPDATE_INTERVAL: int = 43200  # 12時間
    SCANNER_BATCH_SIZE: int = 100
    
    # ログ設定
    LOG_LEVEL: str = "INFO"
    
    @property
    def DATABASE_URL(self) -> str:
        """データベース接続URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def REDIS_URL(self) -> str:
        """Redis接続URL"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    @property
    def CELERY_BROKER_URL(self) -> str:
        """Celeryブローカー URL"""
        return self.REDIS_URL
    
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """Celery結果バックエンド URL"""
        return self.REDIS_URL
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
