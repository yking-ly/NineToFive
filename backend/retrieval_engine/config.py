"""
Configuration settings for the retrieval engine.
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Paths - Updated for new directory structure
    # backend/retrieval_engine/config.py -> data/ is ../../data
    DATA_DIR: Path = Path(__file__).parent.parent.parent / "data"
    CHROMA_PERSIST_DIR: Path = Path(__file__).parent / "chroma_db"
    
    # ChromaDB Collections
    IPC_COLLECTION: str = "ipc"
    BNS_COLLECTION: str = "bns"
    MAPPING_COLLECTION: str = "mapping"
    CASE_LAWS_COLLECTION: str = "case_laws"
    
    # Embedding Model
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    EMBEDDING_DIMENSION: int = 768
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    # Cache TTLs (in seconds)
    QUERY_CACHE_TTL: int = 86400      # 24 hours
    EMBEDDING_CACHE_TTL: int = 604800  # 7 days
    SESSION_CACHE_TTL: int = 3600      # 1 hour
    
    # Retrieval Settings
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    
    # Chunking Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
