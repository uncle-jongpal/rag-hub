# 01. Naive RAG

가장 단순한 RAG 베이스라인입니다. 다른 기법의 성능 비교 기준점으로 사용합니다.

## 1. 동작 원리

1. 문서를 시멘틱 청크로 분할 (문단/문장 경계 기준, 최대 600자)
2. 각 청크를 BGE-M3 임베딩으로 벡터화
3. Qdrant에 저장 (cosine similarity)
4. 질문도 동일 임베딩으로 변환, top-k 검색
5. 검색 결과를 컨텍스트로 LLM 호출 후 답변 생성

## 2. 강점과 약점

강점
1. 구현이 매우 단순합니다 (수십 줄)
2. 도메인 의존 부품이 없어 시작하기 좋습니다
3. 비용이 낮습니다 (LLM 호출 1회)

약점
1. 검색이 의미 매칭에만 의존해 정확한 키워드 매칭(고유명사, 약어)이 약합니다
2. 청크 단독으로는 모호한 정보를 못 다룹니다
3. 질문 어휘가 문서 어휘와 다르면 검색이 빗나갑니다

## 3. 실행

```bash
docker compose up -d            # Qdrant 실행
uv run python techniques/01-naive/rag.py
```

## 4. 다음 단계

1. 02-hybrid-search 로 BM25를 더해 키워드 약점 보완
2. 03-reranking 으로 검색 정밀도 향상
3. 06-parent-child 로 청크 컨텍스트 부족 문제 해결

## 5. 참고 (References)

1. Lewis, P., et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS. - https://arxiv.org/abs/2005.11401
2. BGE-M3 임베딩 - https://arxiv.org/abs/2402.03216
3. 통합 인용은 docs/references.md 참조
