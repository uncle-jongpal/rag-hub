"""환경 설정 - .env에서 API 키와 모델명을 읽어옴."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API 키
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    cohere_api_key: str = ""
    mistral_api_key: str = ""

    # LLM 모델 (오픈AI 또는 미스트랄)
    llm_provider: str = "mistral"  # openai / anthropic / mistral
    gen_llm_model: str = "mistral-small-latest"
    eval_llm_model: str = "mistral-large-latest"

    # 로컬 모델 (무료)
    embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    log_level: str = "INFO"


settings = Settings()
