import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CONTENT_DIR = BASE_DIR / "content"
DOCS_DIR = BASE_DIR / "docs"
BACKUP_DIR = BASE_DIR / "backups"
LABS_DIR = BASE_DIR / "labs"
STATIC_DIR = BASE_DIR / "frontend" / "static"

class Config:
    VERSION = "3.0.0"
    PLATFORM_NAME = "Billinger Enterprise DevOps & SRE Platform"
    HOST = os.environ.get("BILLINGER_HOST", "0.0.0.0")
    PORT = int(os.environ.get("BILLINGER_PORT", 8080))
    DEBUG = os.environ.get("BILLINGER_DEBUG", "false").lower() == "true"
    SECRET_KEY = os.environ.get("BILLINGER_SECRET_KEY", "b1ll1ng3r-s3cur3-k3y-pr0d-2026")
    
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    CONTENT_DIR = CONTENT_DIR
    DOCS_DIR = DOCS_DIR
    BACKUP_DIR = BACKUP_DIR
    LABS_DIR = LABS_DIR
    STATIC_DIR = STATIC_DIR
    
    DB_PATH = os.environ.get("BILLINGER_DB_PATH", str(DATA_DIR / "billinger.db"))
    TOKEN_DIR = DATA_DIR / "secure_tokens"
    
    MIN_RAM_MB = 2048
    RECOMMENDED_RAM_MB = 4096
    MAX_SANDBOX_TIMEOUT_SEC = 30
    OFFLINE_ONLY = os.environ.get("BILLINGER_OFFLINE_MODE", "false").lower() == "true"
    
    DEFAULT_AI_PROVIDER = "gemini"
    DEFAULT_AI_MODEL = "gemini-1.5-flash"
    AI_FALLBACK_ORDER = ["gemini", "groq", "openai", "openrouter"]
    
    @classmethod
    def ensure_directories(cls):
        for path in [DATA_DIR, cls.TOKEN_DIR, CONTENT_DIR, DOCS_DIR, BACKUP_DIR, LABS_DIR, STATIC_DIR]:
            path.mkdir(parents=True, exist_ok=True)
