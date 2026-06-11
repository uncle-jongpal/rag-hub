# research-rag 백엔드 API 이미지.
# 13개 기법 코드 + 공통 모듈을 담고 FastAPI 로 검색/답변 엔드포인트를 제공한다.
# 벡터DB(Qdrant)는 별도 컨테이너에서 동작 (docker-compose 내부 네트워크로 접속).
# 빌드 컨텍스트는 레포 루트.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# numpy/torch 빌드에 필요한 빌드툴
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# torch 는 CPU 전용 빌드로 먼저 설치한다. 이 컨테이너는 GPU 를 쓰지 않으므로
# 기본(CUDA) 휠의 수 GB 짜리 NVIDIA 라이브러리를 받을 필요가 없다.
RUN pip install --upgrade pip && \
    pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.4.0"

# 나머지 의존성 (기존 대시보드 이미지와 동일 + FastAPI/uvicorn, streamlit 제외)
RUN pip install \
        "qdrant-client>=1.12.0" \
        "sentence-transformers>=3.3.0" \
        "transformers>=4.46.0" \
        "kiwipiepy>=0.20.0" \
        "rank-bm25>=0.2.2" \
        "openai>=1.55.0" \
        "anthropic>=0.40.0" \
        "tiktoken>=0.8.0" \
        "datasets>=3.0.0" \
        "python-dotenv>=1.0.1" \
        "pydantic>=2.9.0" \
        "pydantic-settings>=2.6.0" \
        "tenacity>=9.0.0" \
        "rich>=13.9.0" \
        "wikipedia-api>=0.7.0" \
        "numpy>=1.26.0" \
        "pandas>=2.2.0" \
        "scikit-learn>=1.5.0" \
        "mistralai>=1.5.1,<2.0.0" \
        "langchain-mistralai>=0.2.0" \
        "fastapi>=0.115.0" \
        "uvicorn>=0.32.0"

# 소스 코드 복사
COPY . .

EXPOSE 8000

# 컨테이너 내부 검색 경로 + Qdrant 호스트 (docker-compose 서비스 이름)
ENV PYTHONPATH=/app \
    QDRANT_URL=http://qdrant:6333

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
