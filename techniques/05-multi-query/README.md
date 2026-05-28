# 05. Multi-query Retrieval

LLM으로 질문을 여러 표현으로 확장한 뒤 각각 검색하고 결과를 RRF로 통합합니다.

## 1. 동작 원리

1. LLM에 원 질문을 다양한 표현/관점 4개로 다시 쓰도록 요청
2. 원 질문 + 4개 변형 총 5개 쿼리로 임베딩 검색 수행
3. 5개 결과 순위를 RRF (1/(k+rank))로 합산
4. 통합 순위 top-k로 LLM 호출

## 2. 강점과 약점

강점
1. 사용자 질문이 짧거나 모호할 때 회수율(Recall)을 크게 높입니다
2. 동의어/패러프레이즈 변형이 어휘 매칭 약점을 보완합니다
3. RRF로 안정적 통합 가능

약점
1. 검색 호출이 N배 증가 (지연 + 비용)
2. LLM 호출이 한 번 추가됨
3. 변형 질문 품질이 LLM에 의존하므로 모델 선택에 민감

## 3. 실행

```bash
docker compose up -d
uv run python techniques/05-multi-query/rag.py
```

## 4. 변형

1. Step-back prompting - 더 추상적인 상위 질문 1개로 변환 (반대 방향)
2. Query decomposition - 복잡한 질문을 더 작은 하위 질문 여러 개로 쪼개기
3. RAG-Fusion - 본 기법의 변형, 변형 질문 수와 RRF 가중치를 다르게 잡습니다

## 5. 참고 (References)

1. LangChain MultiQueryRetriever - https://python.langchain.com/docs/how_to/MultiQueryRetriever/
2. Raudaschl, A. (2023). "Forget RAG, the Future is RAG-Fusion." - https://towardsdatascience.com/forget-rag-the-future-is-rag-fusion-1147298d8ad1
3. Zheng, H., et al. (2023). "Take a Step Back: Evoking Reasoning via Abstraction in LLMs." - https://arxiv.org/abs/2310.06117
4. 통합 인용은 docs/references.md 의 "3-2. Multi-query / RAG-Fusion", "3-3. Step-back Prompting" 참조
