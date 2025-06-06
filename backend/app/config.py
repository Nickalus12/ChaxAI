import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / '.env'

load_dotenv(dotenv_path=ENV_PATH)

VECTOR_DIR = os.getenv("VECTORSTORE_DIR", str(BASE_DIR / "vectorstore"))
DOCS_DIR = BASE_DIR / "docs"
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
API_TOKENS = [t.strip() for t in os.getenv("API_TOKENS", "").split(",") if t.strip()]
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
LOG_FILE = os.getenv("LOG_FILE", "")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
ANTHROPIC_API_BASE = os.getenv("ANTHROPIC_API_BASE", "https://api.anthropic.com")
GROK_API_BASE = os.getenv("GROK_API_BASE", "https://api.groq.com/openai/v1")



def get_api_key(provider: str) -> str:
    """Return the API key for the chosen provider."""
    mapping = {
        "openai": "OPENAI_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
        "grok": "GROK_API_KEY",
    }
    env_var = mapping.get(provider)
    if not env_var:
        raise ValueError(f"Unsupported provider: {provider}")
    key = os.getenv(env_var)
    if not key:
        raise RuntimeError(f"{env_var} is not set")
    return key


def get_openai_key() -> str:
    """Compatibility wrapper for OpenAI API key."""
    return get_api_key("openai")


def get_api_base(provider: str) -> str:
    mapping = {
        "openai": OPENAI_API_BASE,
        "claude": ANTHROPIC_API_BASE,
        "grok": GROK_API_BASE,
    }
    base = mapping.get(provider)
    if not base:
        raise ValueError(f"Unsupported provider: {provider}")
    return base


def configure_logging() -> None:
    """Configure basic logging according to ``LOG_LEVEL``."""
    import logging
    handlers = [logging.StreamHandler()]
    if LOG_FILE:
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
        handlers.append(file_handler)

    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )
