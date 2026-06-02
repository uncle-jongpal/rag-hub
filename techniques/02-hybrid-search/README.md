# 02. Hybrid Search

BM25(어휘 매칭) + Dense Embedding(의미 매칭)을 RRF로 결합합니다.

## 1. 동작 원리

1. 청크 단위로 BM25 인덱스(Kiwi 형태소 분석)와 Qdrant 벡터 인덱스를 동시에 구축
2. 질문이 들어오면 BM25와 Dense 양쪽에서 각각 후보 N개 검색
3. 두 결과의 순위를 RRF (Reciprocal Rank Fusion, score = sum(1/(k+rank)))로 합산
4. 통합 순위 top-k를 컨텍스트로 LLM 호출

## 2. 강점과 약점

강점
1. 고유명사/약어/제품명 등 어휘 매칭이 중요한 질문에 강합니다
2. RRF는 점수 스케일이 다른 시스템을 안전하게 결합합니다
3. 한국어 BM25에 Kiwi 형태소 분석을 적용해 조사/어미 노이즈를 줄입니다

약점
1. 두 시스템을 운영해야 해 구현 복잡도가 증가합니다
2. BM25는 동의어/문맥 매칭이 약합니다 (Dense가 보완)
3. RRF 상수 k(기본 60) 튜닝이 데이터셋에 따라 필요할 수 있습니다

## 3. 실행

```bash
docker compose up -d
uv run python techniques/02-hybrid-search/rag.py
```

## 4. 참고

1. RRF 원 논문 - Cormack et al., 2009 (https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
2. Kiwi 한국어 형태소 분석기 - https://github.com/bab2min/kiwipiepy
