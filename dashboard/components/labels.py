"""대시보드 전역 한국어 라벨 + 기법/메트릭 설명."""

# 메트릭 한국어 라벨 + 설명
METRICS = {
    "faithfulness": {
        "ko": "충실도",
        "desc": "생성된 답변이 검색된 컨텍스트에 충실한지 (환각 여부). 1에 가까울수록 답이 자료에 근거함",
    },
    "answer_relevancy": {
        "ko": "답변 적합성",
        "desc": "답변이 사용자 질문에 실제로 답하고 있는지. BGE-M3 로 질문/답변 임베딩 코사인 유사도를 계산 (LLM 호출 없이 측정, 무료 티어 영향 없음). 1에 가까울수록 질문과 잘 맞음",
    },
    "context_precision": {
        "ko": "검색 정확도",
        "desc": "검색된 컨텍스트 중 실제로 답에 필요한 비율. 1에 가까울수록 불필요한 청크가 적음",
    },
    "context_recall": {
        "ko": "검색 완전성",
        "desc": "정답에 필요한 정보가 검색에 다 포함됐는지. 1에 가까울수록 빠진 정보가 적음",
    },
}


def metric_ko(name: str) -> str:
    """faithfulness 같은 영문 메트릭명을 '충실도 (faithfulness)' 형태로 변환."""
    if name in METRICS:
        return f"{METRICS[name]['ko']} ({name})"
    return name


def metric_desc(name: str) -> str:
    return METRICS.get(name, {}).get("desc", "")


# 기법 한국어 이름 + 한두 줄 설명 + 강점/약점
# ko_short : 차트 라벨용 짧은 이름 (영문 괄호 없이)
# ko : 전체 이름 (한국어 + 영문 괄호)
TECHNIQUES = {
    "01-naive": {
        "ko_short": "단순 임베딩 검색",
        "ko": "단순 임베딩 검색 (Naive RAG)",
        "summary": "임베딩으로 top-k 검색 후 LLM 호출. 가장 단순한 베이스라인",
        "good_for": "비교 기준점, 빠른 프로토타입",
        "weak_for": "고유명사 매칭, 청크가 짧으면 모호한 답",
    },
    "02-hybrid-search": {
        "ko_short": "하이브리드 검색",
        "ko": "하이브리드 검색 (Hybrid Search)",
        "summary": "BM25(어휘 매칭) + 임베딩(의미 매칭)을 RRF로 결합",
        "good_for": "고유명사/약어 많은 한국어 도메인, 일반 RAG 운영 기본",
        "weak_for": "두 검색기 동시 운영으로 약간의 복잡도 증가",
    },
    "03-reranking": {
        "ko_short": "재정렬",
        "ko": "재정렬 (Reranking)",
        "summary": "1차 검색 N개를 cross-encoder 로 정밀 재정렬",
        "good_for": "검색 정밀도가 답 품질의 병목일 때, 정확한 답이 중요한 도메인",
        "weak_for": "1차 검색이 빠뜨린 문서는 못 살림. GPU 권장",
    },
    "04-hyde": {
        "ko_short": "가설 답변 검색",
        "ko": "가설 답변 검색 (HyDE)",
        "summary": "LLM이 만든 가상의 답변 임베딩으로 검색",
        "good_for": "질문이 짧거나 어휘가 문서와 동떨어진 경우",
        "weak_for": "LLM 호출 1회 추가, 가설이 빗나가면 역효과",
    },
    "05-multi-query": {
        "ko_short": "다중 질문",
        "ko": "다중 질문 (Multi-query)",
        "summary": "질문을 여러 표현으로 LLM 확장 후 결과를 RRF 합산",
        "good_for": "모호한 질문, 회수율(Recall) 향상이 필요할 때",
        "weak_for": "검색 호출 N배, LLM 비용 증가",
    },
    "06-parent-child": {
        "ko_short": "부모-자식 청크",
        "ko": "부모-자식 청크 (Parent-Child)",
        "summary": "작은 청크로 검색 정밀도 확보 + 큰 부모 청크로 LLM 컨텍스트",
        "good_for": "긴 문서, 청크 단독 의미가 부족한 도메인",
        "weak_for": "LLM 입력 토큰 증가",
    },
    "07-contextual-retrieval": {
        "ko_short": "문맥 보강 검색",
        "ko": "문맥 보강 검색 (Contextual Retrieval)",
        "summary": "각 청크 앞에 문서 맥락 1-2문장을 LLM 으로 prepend 후 임베딩 (Anthropic 2024)",
        "good_for": "단독으로는 모호한 청크가 많은 도메인 (법률/메뉴얼/사내 문서)",
        "weak_for": "인덱싱 시 청크당 LLM 호출 - 비용 큼 (prompt caching 권장)",
    },
    "08-self-rag": {
        "ko_short": "자가 평가 RAG",
        "ko": "자가 평가 RAG (Self-RAG)",
        "summary": "LLM 이 검색 필요 여부 + 청크 유용성을 스스로 판단",
        "good_for": "단순 질문(산수, 상식)에 불필요한 검색 절약, 환각 제어",
        "weak_for": "청크당 평가 LLM 호출로 비용 증가, 분류 정확도에 의존",
    },
    "09-crag": {
        "ko_short": "교정 RAG",
        "ko": "교정 RAG (Corrective RAG)",
        "summary": "검색 신뢰도 평가 후 부족하면 질문 재작성/재검색",
        "good_for": "검색 결과 품질 변동이 큰 도메인, 검색 실패 회복",
        "weak_for": "평가 LLM 호출 + 재시도 비용, 평가자 정확도에 의존",
    },
    "10-graphrag": {
        "ko_short": "그래프 RAG",
        "ko": "그래프 RAG (GraphRAG)",
        "summary": "엔티티/관계 그래프 + 커뮤니티 요약 인덱스 (Microsoft 2024 단순화)",
        "good_for": "전체 조망/요약형 질문 ('이 도메인의 주요 X는?')",
        "weak_for": "인덱싱 비용 매우 큼 (청크당 LLM 호출), 단답형 사실 질문은 약함",
    },
    "11-raptor": {
        "ko_short": "RAPTOR 트리",
        "ko": "RAPTOR 트리",
        "summary": "청크 클러스터링 + LLM 요약으로 깊이 3 트리 구축",
        "good_for": "장문/다중 문서 QA, 디테일과 요약 동시에 필요할 때",
        "weak_for": "인덱싱 LLM 비용, 작은 데이터셋에서는 상위 레벨이 과한 추상화",
    },
    "12-agentic-rag": {
        "ko_short": "에이전트형 RAG",
        "ko": "에이전트형 RAG (Agentic, ReAct)",
        "summary": "LLM 이 검색/계산 등 도구를 능동 호출 (ReAct 패턴)",
        "good_for": "다단계/혼합 추론, 도구 결합 필요한 어시스턴트",
        "weak_for": "LLM 호출 3-5배, 파싱 오류 위험, 큰 모델 권장",
    },
    "13-adaptive-rag": {
        "ko_short": "적응형 RAG",
        "ko": "적응형 RAG (Adaptive)",
        "summary": "질문 복잡도(simple/single/multi-hop) 분류 후 전략 분기",
        "good_for": "질문 다양성이 큰 환경, 비용/품질 자동 최적화",
        "weak_for": "분류 LLM 호출 추가, 오분류 시 부적절한 전략",
    },
}


def technique_ko(tid: str) -> str:
    """차트/드롭다운용 짧은 이름 - 한국어만."""
    if tid in TECHNIQUES:
        return TECHNIQUES[tid].get("ko_short", TECHNIQUES[tid]["ko"])
    return tid


def technique_ko_full(tid: str) -> str:
    """상세 페이지용 풀 이름 - 한국어 + 영문 괄호."""
    if tid in TECHNIQUES:
        return TECHNIQUES[tid]["ko"]
    return tid


def technique_card(tid: str) -> str:
    """대시보드에 표시할 기법 한 줄 요약 카드."""
    if tid not in TECHNIQUES:
        return tid
    t = TECHNIQUES[tid]
    return (
        f"{t['ko']}\n\n"
        f"한 줄 요약 - {t['summary']}\n\n"
        f"잘 맞는 경우 - {t['good_for']}\n\n"
        f"주의할 점 - {t['weak_for']}"
    )
