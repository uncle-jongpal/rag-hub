# 03. Reranking

1차 임베딩 검색 결과 N개를 cross-encoder로 재정렬해 정밀도를 높입니다.

## 1. 동작 원리

1. 임베딩 + Qdrant로 1차 검색 (보통 30-50개 후보)
2. BGE-reranker-v2-m3 cross-encoder로 (query, chunk) 쌍을 입력해 점수 산출
3. 점수 내림차순으로 top-k만 LLM에 전달

## 2. 강점과 약점

강점
1. cross-encoder는 query/chunk를 함께 보고 점수를 매겨 bi-encoder 대비 정확도가 높습니다
2. 작은 후보 셋에만 적용하므로 운영 비용이 감당 가능합니다
3. 로컬 모델(BGE-reranker)로 무료 실행이 가능합니다

약점
1. 1차 검색이 빠뜨린 문서는 reranker도 못 살립니다 (recall은 1차에 의존)
2. 후보 수 N이 커지면 지연이 선형 증가합니다
3. 다국어 reranker가 한국어 도메인 특수 용어에는 약할 수 있어 사전 검증이 필요합니다

## 3. 실행

```bash
docker compose up -d
uv run python techniques/03-reranking/rag.py
```

## 4. 변형 가능성

1. Hybrid Search (02번) + Reranking 조합이 실무 표준입니다. 02번 코드와 본 코드를 합쳐 직접 만들 수 있습니다
2. Cohere Rerank API로 교체하면 무료 GPU 없이도 운영 가능 (유료)
3. ColBERT-style late interaction을 두면 효율/품질 트레이드오프가 또 다릅니다

## 5. 참고 (References)

1. Reimers, N., & Gurevych, I. (2019). "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks." (cross/bi-encoder 차이) - https://arxiv.org/abs/1908.10084
2. BGE-reranker-v2-m3 모델 - https://huggingface.co/BAAI/bge-reranker-v2-m3
3. Cohere Rerank API - https://docs.cohere.com/docs/rerank-overview
4. 통합 인용은 docs/references.md 의 "2-4. BGE Reranker", "2-5. Cross-encoder vs Bi-encoder" 참조
