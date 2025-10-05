"""
Cloud-optimized configuration for FloatChat Backend
Supports Railway, Render, and other cloud platforms with zero-cost deployment
"""

import os
from urllib.parse import quote_plus

# Cloud Platform Detection
RAILWAY_ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT")
RENDER_ENVIRONMENT = os.getenv("RENDER")
IS_CLOUD = RAILWAY_ENVIRONMENT or RENDER_ENVIRONMENT

# Database Configuration - Cloud Optimized
if IS_CLOUD:
    # Use cloud database URL (Railway/Render provides this)
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Fallback to individual components
        DB_HOST = os.getenv("PGHOST", "localhost")
        DB_PORT = os.getenv("PGPORT", "5432")
        DB_NAME = os.getenv("PGDATABASE", "argo")
        DB_USER = os.getenv("PGUSER", "postgres")
        DB_PASSWORD = os.getenv("PGPASSWORD", "")
        DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    # Local development
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Arcombad1030")
    DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql+psycopg2://postgres:{quote_plus(DB_PASSWORD)}@localhost:5432/argo")

# LLM Configuration - Cloud Optimized
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "huggingface")  # Prefer HuggingFace for cloud
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# Use lighter models for cloud deployment
if IS_CLOUD:
    LLM_MODEL = os.getenv("LLM_MODEL", "microsoft/DialoGPT-medium")  # Lighter model
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
else:
    LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Ollama Configuration (mainly for local)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# ChromaDB Configuration - Cloud Optimized
if IS_CLOUD:
    CHROMA_PATH = os.getenv("CHROMA_PATH", "/tmp/chroma_db")  # Use tmp for cloud
    VECTOR_STORE = os.getenv("VECTOR_STORE", "memory")  # Use memory for cloud efficiency
else:
    CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
    VECTOR_STORE = os.getenv("VECTOR_STORE", "persistent")

# Performance Configuration - Cloud Optimized
if IS_CLOUD:
    MAX_FLOATS = int(os.getenv("MAX_FLOATS", "500"))  # Reduced for cloud
    MAX_DOCUMENTS = int(os.getenv("MAX_DOCUMENTS", "10000"))  # Reduced for cloud
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))  # Smaller batches
else:
    MAX_FLOATS = int(os.getenv("MAX_FLOATS", "1000"))
    MAX_DOCUMENTS = int(os.getenv("MAX_DOCUMENTS", "30000"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))

# Backend URL Configuration
if RAILWAY_ENVIRONMENT:
    BACKEND_URL = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN', 'localhost:8000')}"
elif RENDER_ENVIRONMENT:
    BACKEND_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost:8000')}"
else:
    BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# CORS Configuration for cloud
ALLOWED_ORIGINS = [
    "https://flowchat-ai.streamlit.app",  # Your Streamlit app
    "http://localhost:8501",  # Local development
    "https://localhost:8501"
]

print(f"🚀 Cloud Environment: {IS_CLOUD}")
print(f"🔗 Backend URL: {BACKEND_URL}")
print(f"🗄️ Vector Store: {VECTOR_STORE}")
print(f"🤖 LLM Provider: {LLM_PROVIDER}")