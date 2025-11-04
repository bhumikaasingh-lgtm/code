"""
Configuration file for the RAG System
"""
import os
from typing import Optional

class Config:
    """Main configuration class for the RAG system"""
    
    # Weaviate Configuration
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    WEAVIATE_API_KEY: Optional[str] = os.getenv("WEAVIATE_API_KEY", None)
    WEAVIATE_CLASS_NAME: str = "IssueChunk"
    
    # Embedding Model Configuration
    EMBEDDING_MODEL_NAME: str = "intfloat/e5-large-v2"
    EMBEDDING_DIMENSION: int = 1024
    EMBEDDING_DEVICE: str = "cpu"  # or "cuda" if GPU available
    
    # LLM Configuration
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "meta-llama/Llama-3.2-3B-Instruct")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    USE_OPENAI: bool = os.getenv("USE_OPENAI", "false").lower() == "true"
    
    # Chunking Configuration
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # Search Configuration
    DEFAULT_ALPHA: float = 0.5  # Hybrid search balance (0=keyword, 1=semantic)
    DEFAULT_TOP_K: int = 5
    
    # Data Configuration
    DATA_PATH: str = "/workspace/all_issues_for_test.csv"
    
    # API Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    
    # Frontend Configuration
    FRONTEND_PORT: int = 8501
    BACKEND_URL: str = os.getenv("BACKEND_URL", f"http://localhost:{BACKEND_PORT}")
    
    # RAGAS Configuration
    RAGAS_TEST_SIZE: int = 10
    RAGAS_EMBEDDING_MODEL: str = EMBEDDING_MODEL_NAME
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.USE_OPENAI and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set when USE_OPENAI is True")
        return True


# Validate configuration on import
Config.validate()
