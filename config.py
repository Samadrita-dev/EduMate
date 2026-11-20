import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of EduMate
BASE_DIR = Path(__file__).resolve().parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

# App Details
APP_NAME = "EduMate"
APP_TAGLINE = "Your Intelligent Academic Companion"
VERSION = "1.0.0"

# Database Configuration
DB_PATH = BASE_DIR / "edumate.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Ollama LLM Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "20.0"))

# RAG & ChromaDB Configuration
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"
DOCUMENTS_DIR = BASE_DIR / "documents"
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Academic Defaults
DEFAULT_ATTENDANCE_REQUIREMENT = 75.0  # percentage
DEFAULT_STUDENT_ID = 1  # Aarav Sharma default session
