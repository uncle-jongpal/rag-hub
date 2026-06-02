# 대시보드 + 13개 기법 코드를 한 컨테이너로 띄우는 이미지.
# Qdrant 는 별도 컨테이너에서 동작 (docker-compose 내부 네트워크로 접속).

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 시스템 의존성 (numpy/torch 빌드 시 필요한 빌드툴)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 먼저 복사해 캐시 활용
COPY pyproject.toml ./

# pyproject 만 있을 땐 소스 없이 의존성만 설치 (편집 모드 대신 일반 모드)
RUN pip install --upgrade pip && \
    pip install \
        "qdrant-client>=1.12.0" \
        "sentence-transformers>=3.3.0" \
        "transformers>=4.46.0" \
        "torch>=2.4.0" \
        "kiwipiepy>=0.20.0" \
        "rank-bm25>=0.2.2" \
        "openai>=1.55.0" \
        "anthropic>=0.40.0" \
        "tiktoken>=0.8.0" \
        "ragas>=0.3.9,<0.4.0" \
        "datasets>=3.0.0" \
        "python-dotenv>=1.0.1" \
        "pydantic>=2.9.0" \
        "pydantic-settings>=2.6.0" \
        "tenacity>=9.0.0" \
        "rich>=13.9.0" \
        "typer>=0.13.0" \
        "wikipedia-api>=0.7.0" \
        "numpy>=1.26.0" \
        "pandas>=2.2.0" \
        "scikit-learn>=1.5.0" \
        "streamlit>=1.40.0" \
        "plotly>=5.24.0" \
        "mistralai>=1.5.1,<2.0.0" \
        "langchain-mistralai>=0.2.0"

# 소스 코드 복사
COPY . .

EXPOSE 8501

# 컨테이너 내부 검색 경로 + Qdrant 호스트 (docker-compose 서비스 이름)
ENV PYTHONPATH=/app \
    QDRANT_URL=http://qdrant:6333

CMD ["streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
