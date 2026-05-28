# Dashboard (Streamlit)

평가 결과를 시각적으로 비교하고 인터랙티브 검색 데모를 실행하는 Streamlit 앱입니다.

## 1. 페이지 구성

1. 기법 비교 - 13개 기법의 RAGAS 4종 메트릭을 막대/레이더 차트로
2. 질문별 결과 - 같은 질문에 대한 기법별 답변/컨텍스트 나란히 비교
3. 인터랙티브 검색 - 기법 1개 선택 + 질문 입력 → 실시간 답변, 토큰/비용 표시
4. 비용/지연 추적 - 인덱싱/추론 단계의 LLM 비용 + 호출 시간 시각화

## 2. 실행

의존성 설치 방식은 conda + pip / uv / 일반 venv 중 환경에 맞춰 고르시면 됩니다. 루트 README의 "환경별 명령어 차이" 섹션을 참고하세요.

conda + pip 사용 예 (가장 흔한 윈도우 셋업)

```bash
conda activate rag-hub      # 이미 만든 환경이라 가정
docker compose up -d           # Qdrant
cp .env.example .env           # 윈도우는 copy. 그 후 키 입력

# 평가 결과 1-2개 미리 만들어두면 페이지 1, 2, 4가 즉시 동작합니다
python evaluation/ragas_eval.py --technique 01-naive --limit 5

# 대시보드 실행
streamlit run dashboard/app.py
```

uv 사용 시는 위 명령 앞에 `uv run` 만 붙이면 됩니다.

브라우저에서 http://localhost:8501 자동 열림.

## 3. 폴더 구조

```
dashboard/
├── app.py                 진입점 (페이지 라우팅)
├── components/
│   ├── data.py            평가 결과 JSON 로더 (캐시)
│   ├── compare.py         페이지 1
│   ├── questions.py       페이지 2
│   ├── demo.py            페이지 3
│   └── cost.py            페이지 4
└── README.md
```

## 4. 한계 / 주의

1. 페이지 3(인터랙티브 검색)은 최초 호출 시 임베딩 모델 로드 + Qdrant 인덱싱이 30초-2분 걸립니다. Streamlit cache_resource로 캐시됩니다
2. 평가 결과 JSON이 없으면 페이지 1/2/4는 빈 상태 메시지를 표시합니다 - 먼저 ragas_eval.py를 한 번 이상 실행하세요
3. 비용 수치는 OpenAI API 가격(2026-05 기준) 추정치입니다. 실제 청구액은 자체 모니터링과 같이 확인하세요
4. 본 대시보드는 단일 사용자 / 로컬 데모 목적입니다. 멀티 사용자 운영은 별도 인프라(인증, 동시성, 컨테이너 등) 필요
