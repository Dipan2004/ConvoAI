from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Agent System"
    app_version: str = "1.0.0"
    debug: bool = False

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    llm_model: str = "openai/gpt-oss-20b:free"
    llm_fallback: str = "google/gemini-2.0-flash:free"
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()