# 07. Contextual Retrieval

Anthropic이 2024년 9월 공개한 기법. 각 청크를 임베딩하기 전에 LLM이 생성한 1-2문장 문서 맥락을 prepend합니다.

## 1. 동작 원리

1. 각 문서에 대해 청크를 분할
2. 각 청크마다 LLM에 (문서 전체 + 해당 청크)를 보내 "이 청크가 문서에서 어떤 위치/주제인지" 짧은 설명을 생성
3. 청크 앞에 그 설명을 붙여 임베딩 (augmented = "[문서 맥락] ... [내용] ...")
4. 검색은 augmented 청크 위에서 진행
5. LLM에 전달할 때는 원 청크(raw_chunk)만 사용해 토큰 절약 가능

## 2. 동기 (왜 효과적인가)

청크는 단독으로 보면 의미가 모호한 경우가 많습니다 (예: "이 회사는 작년 매출이 50% 늘었다" - 어느 회사인지 불명). 문서 맥락을 prepend하면 검색 모델이 청크를 그 문서의 맥락 안에서 매칭하게 됩니다. Anthropic 발표 기준 retrieval failure rate를 평균 49% 감소시켰습니다.

## 3. 강점과 약점

강점
1. 검색 정확도 향상이 큰 편 (Anthropic 벤치마크 기준)
2. 다른 기법과 직교적이라 결합이 쉬움 (Hybrid + Contextual, Rerank + Contextual 모두 가능)
3. 검색 시점 비용은 동일 (전처리 비용만 추가)

약점
1. 전처리 LLM 호출 비용이 큽니다 (청크 N개 * LLM 호출)
2. 긴 문서를 매 청크마다 다시 보내면 비용 폭증 - prompt caching 권장
3. 한국어에서 맥락 설명 품질은 LLM에 의존하므로 모델 선택이 영향을 줍니다

## 4. 비용 최적화

1. Anthropic Claude의 prompt caching 사용 시 문서 부분이 캐시되어 비용 90% 절감 가능
2. 오픈AI는 자동 prefix caching이 적용되어 동일 문서 prefix가 일정 시간 캐시됨
3. 본 구현은 단순화를 위해 캐싱을 활용하지 않음 - 대규모 사용 시 적용 권장

## 5. 실행

```bash
docker compose up -d
uv run python techniques/07-contextual-retrieval/rag.py
```

## 6. 참고

1. Anthropic 공식 발표 - https://www.anthropic.com/news/contextual-retrieval
2. Prompt Caching - https://docs.anthropic.com/claude/docs/prompt-caching
