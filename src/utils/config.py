import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Configurable Directories (can be set in .env or fallback to defaults)
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")
VECTOR_DB_DIR = BASE_DIR / os.getenv("VECTOR_DB_DIR", "vector_db")
LOGS_DIR = BASE_DIR / os.getenv("LOGS_DIR", "logs")

# Ensure critical directories exist
for directory in [DATA_DIR, VECTOR_DB_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Embedding Configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")

# Chunking Configuration
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", 1000))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("DEFAULT_CHUNK_OVERLAP", 200))

# Retrieval Defaults
DEFAULT_RETRIEVE_K = int(os.getenv("DEFAULT_RETRIEVE_K", 20))
DEFAULT_RERANK_K = int(os.getenv("DEFAULT_RERANK_K", 5))

# Export settings
PDF_EXPORT_DIR = DATA_DIR / "exports"
PDF_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
