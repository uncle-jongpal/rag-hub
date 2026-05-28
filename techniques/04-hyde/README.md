# 04. HyDE (Hypothetical Document Embeddings)

질문 자체가 아닌 LLM이 생성한 가상 답변의 임베딩으로 검색합니다.

## 1. 동작 원리

1. 질문이 들어오면 LLM에게 "정확성과 무관하게 답변 스타일의 단락을 생성"하도록 호출
2. 생성된 가설 답변을 임베딩 (질문 임베딩 대신)
3. 그 임베딩으로 벡터 검색 후 일반 RAG와 동일하게 LLM 호출

## 2. 동기 (왜 효과적인가)

질문과 답변은 어휘/문체가 다를 수 있어 직접 임베딩하면 의미적 거리가 멉니다 ("BGE-M3가 뭐예요?" vs "BGE-M3는 BAAI의 다국어 임베딩 모델입니다"). HyDE는 답변 어휘 분포에 맞춰 검색해 매칭률을 높입니다.

## 3. 강점과 약점

강점
1. 도메인 사전 학습 없이도 어휘 분포를 맞춰 검색 품질 향상 가능
2. 구현이 단순합니다 (LLM 호출 한 줄 추가)
3. 짧고 모호한 질문에 특히 효과적입니다

약점
1. LLM 호출이 한 번 추가되어 지연/비용 증가 (보통 +1초, +수백 토큰)
2. 가설 답변이 빗나가면 검색이 더 나빠지기도 합니다 (특정 도메인)
3. Reranker와 결합하면 효과가 중복될 수 있어 둘 중 하나만 쓰는 게 좋을 수 있습니다

## 4. 실행

```bash
docker compose up -d
uv run python techniques/04-hyde/rag.py
```

## 5. 변형

1. 가설 답변을 여러 개 생성해 평균 임베딩 사용 (안정성 향상)
2. 원 질문 임베딩 + HyDE 임베딩을 가중 평균

## 6. 참고 (References)

1. Gao, L., Ma, X., Lin, J., & Callan, J. (2022). "Precise Zero-Shot Dense Retrieval without Relevance Labels." - https://arxiv.org/abs/2212.10496
2. 통합 인용은 docs/references.md 의 "3-1. HyDE" 참조
