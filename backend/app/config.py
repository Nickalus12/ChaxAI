import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / '.env'

load_dotenv(dotenv_path=ENV_PATH)

VECTOR_DIR = os.getenv('VECTORSTORE_DIR', str(BASE_DIR / 'vectorstore'))


def get_openai_key() -> str:
    """Retrieve the OpenAI API key from the environment."""
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        raise RuntimeError('OPENAI_API_KEY is not set')
    return key
