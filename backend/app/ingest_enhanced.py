import os
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import logging

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / '.env'

load_dotenv(dotenv_path=ENV_PATH)

# Create directories if they don't exist
for dir_name in ['vectorstore', 'cache', 'logs', 'docs']:
    dir_path = BASE_DIR / dir_name
    dir_path.mkdir(exist_ok=True)

# Directories
VECTOR_DIR = os.getenv("VECTORSTORE_DIR", str(BASE_DIR / "vectorstore"))
DOCS_DIR = BASE_DIR / "docs"
CACHE_DIR = BASE_DIR / "cache"

# API Configuration
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
API_TOKENS = [t.strip() for t in os.getenv("API_TOKENS", "").split(",") if t.strip()]
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))

# Grok Configuration
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_API_BASE = os.getenv("GROK_API_BASE", "https://api.x.ai/v1")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-beta")
GROK_TEMPERATURE = float(os.getenv("GROK_TEMPERATURE", "0.7"))
GROK_MAX_TOKENS = int(os.getenv("GROK_MAX_TOKENS", "2000"))
GROK_STREAMING = os.getenv("GROK_STREAMING", "true").lower() == "true"

# OpenAI for embeddings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Security
encryption_key = os.getenv("ENCRYPTION_KEY")
if not encryption_key:
    encryption_key = Fernet.generate_key().decode()
    print(f"Generated encryption key: {encryption_key}")
    print("Add this to your .env file as ENCRYPTION_KEY=")

ENCRYPTION_KEY = encryption_key
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Rate Limiting
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
LOG_FILE = os.getenv("LOG_FILE", "logs/chaxai.log")
AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "logs/audit.log")

# Multi-tenant
ENABLE_MULTI_TENANT = os.getenv("ENABLE_MULTI_TENANT", "false").lower() == "true"
DEFAULT_TENANT_ID = os.getenv("DEFAULT_TENANT_ID", "default")

# Analytics
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
ANALYTICS_DB = os.getenv("ANALYTICS_DB", "sqlite:///analytics.db")

def get_encryption_cipher():
    """Get Fernet cipher for encryption/decryption."""
    return Fernet(ENCRYPTION_KEY.encode())

def configure_logging():
    """Configure comprehensive logging with rotation."""
    from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
    
    # Ensure log directory exists
    log_dir = Path(LOG_FILE).parent
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    # Main application logger
    app_logger = logging.getLogger("chaxai")
    app_logger.setLevel(LOG_LEVEL)
    
    if LOG_FILE:
        app_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=10_000_000, backupCount=5
        )
        app_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )
        )
        app_logger.addHandler(app_handler)
    
    # Audit logger
    if AUDIT_LOG_FILE:
        audit_log_dir = Path(AUDIT_LOG_FILE).parent
        audit_log_dir.mkdir(exist_ok=True)
        
        audit_logger = logging.getLogger("chaxai.audit")
        audit_handler = TimedRotatingFileHandler(
            AUDIT_LOG_FILE, when="midnight", interval=1, backupCount=30
        )
        audit_handler.setFormatter(
            logging.Formatter("%(asctime)s [AUDIT] %(message)s")
        )
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)

def validate_config():
    """Validate required configuration values."""
    errors = []
    
    if not GROK_API_KEY:
        errors.append("GROK_API_KEY is required")
    
    if not OPENAI_API_KEY and EMBEDDING_MODEL.startswith("text-embedding"):
        errors.append("OPENAI_API_KEY is required for embeddings")
    
    if ENABLE_MULTI_TENANT and not JWT_SECRET_KEY:
        errors.append("JWT_SECRET_KEY is required for multi-tenant mode")
    
    if errors:
        for error in errors:
            print(f"Configuration Error: {error}")
        # Don't raise for local testing
        print("Warning: Running with configuration errors")