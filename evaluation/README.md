# 평가 (RAGAS)

각 RAG 기법을 동일 질문 셋에 대해 RAGAS 메트릭으로 정량 비교합니다.

## 1. 구성

1. `questions.jsonl` - 평가 질문 12개 (한국어 8 + 영어 4). 각 항목은 question, ground_truth, expected_doc_ids 포함
2. `ragas_eval.py` - 단일 기법 평가 스크립트
3. `compare.py` - 여러 기법 결과를 모아 비교 markdown 생성
4. `results/` - 평가 결과 (json + markdown), gitignore 됨

## 2. 메트릭 설명

1. Faithfulness - 생성된 답이 컨텍스트에 충실한지 (환각 여부)
2. Answer Relevancy - 답이 질문과 실제로 관련 있는지
3. Context Precision - 검색된 컨텍스트 중 정답에 기여한 비율
4. Context Recall - 정답에 필요한 정보가 검색에 다 포함됐는지 (ground_truth 필요)

## 3. 실행

```bash
docker compose up -d                                       # Qdrant
cp .env.example .env  # .env에 OPENAI_API_KEY 입력

# 단일 기법 평가
uv run python evaluation/ragas_eval.py --technique 01-naive --top-k 5

# 전 기법 순차 실행 (V1 + V2)
for t in 01-naive 02-hybrid-search 03-reranking 04-hyde 05-multi-query 06-parent-child 07-contextual-retrieval 08-self-rag 09-crag 10-graphrag 11-raptor 12-agentic-rag 13-adaptive-rag; do
  uv run python evaluation/ragas_eval.py --technique "$t" --top-k 5
done

# 비교 리포트 생성
uv run python evaluation/compare.py
```

## 4. 비용 추정

RAGAS는 평가 시 메트릭당 LLM 호출이 1-2회 발생합니다. 질문 20개 * 메트릭 4개 ≈ 80회 호출이 기본입니다.

공급자별 1회 평가 추정 비용

1. 미스트랄 (기본) - small 생성 + large 평가 기준 약 0.1-0.3 USD/회 실행
2. 오픈AI - mini 생성 + GPT-4o 평가 기준 약 1-2 USD/회 실행
3. 전 기법 13회 실행 - 미스트랄로 가면 약 2-5 USD, 오픈AI는 15-30 USD

V2 기법(GraphRAG/RAPTOR/Contextual Retrieval)은 인덱싱 LLM 비용이 추가로 발생합니다.

## 5. 주의 사항

1. RAGAS의 평가 LLM 호출이 한국어에서 영어만큼 잘 동작하는지는 별도 검증이 필요합니다. 일부 메트릭이 한국어에서 낮게/높게 편향될 수 있습니다.
2. 질문 셋이 매우 작아(12개) 통계적 신뢰도가 낮습니다. 실 데이터에서 의사결정에 쓰려면 50-100개 이상 권장합니다.
3. 평가 LLM 모델을 바꾸면 점수 절대값이 크게 변할 수 있어 시계열 비교는 같은 평가 LLM으로 통일하세요.
