from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Agent System"
    app_version: str = "1.0.0"
    debug: bool = False

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    model_name: str = "qwen/qwen-2.5-72b-instruct"
    model_fallback: str = "minimax/minimax-01"
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2
    llm_max_tokens: int = 1000
    llm_temperature: float = 0.2

    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_device: str = "cpu"

    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "knowledge_base"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_ttl_seconds: int = 86400

    intent_confidence_high: float = 0.85
    intent_confidence_medium: float = 0.60

    rag_top_k_dense: int = 10
    rag_top_k_sparse: int = 10
    rag_top_k_final: int = 3
    rag_min_relevance_score: float = 0.70

    max_conversation_turns: int = 6
    max_message_length: int = 2000
    rate_limit_per_minute: int = 20

    prompts_dir: str = "./prompts"

    langsmith_api_key: Optional[str] = None
    langsmith_project: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()