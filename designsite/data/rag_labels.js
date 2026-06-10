// Shared labels + helpers for the RAG Frame redesign.
// Bilingual (KO / EN). Translated from dashboard/components/labels.py.
window.RAGLabels = (function () {
  const METRICS = {
    faithfulness:      { key: "faithfulness",      ko: "충실도",      en: "Faithfulness",      abbr: "충실도",   desc: "생성된 답변이 검색된 컨텍스트에 충실한지(환각 여부). 1에 가까울수록 답이 자료에 근거함.", descEn: "Is the answer grounded in the retrieved context (no hallucination)." },
    answer_relevancy:  { key: "answer_relevancy",  ko: "답변 적합성", en: "Answer Relevancy",   abbr: "적합성",   desc: "답변이 사용자 질문에 실제로 답하고 있는지. 질문/답변 임베딩 코사인 유사도로 측정.", descEn: "Does the answer actually address the user's question." },
    context_precision: { key: "context_precision", ko: "검색 정확도", en: "Context Precision",  abbr: "정확도",   desc: "검색된 컨텍스트 중 실제로 답에 필요한 비율. 1에 가까울수록 불필요한 청크가 적음.", descEn: "Share of retrieved context that was actually useful." },
    context_recall:    { key: "context_recall",    ko: "검색 완전성", en: "Context Recall",     abbr: "완전성",   desc: "정답에 필요한 정보가 검색에 다 포함됐는지. 1에 가까울수록 빠진 정보가 적음.", descEn: "Did retrieval capture everything the answer needs." },
  };
  const METRIC_ORDER = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"];

  const TECH = {
    "01-naive":               { num: "01", ko: "단순 임베딩 검색", en: "Naive RAG",            family: "V1", summary: "임베딩으로 top-k 검색 후 LLM 호출. 가장 단순한 베이스라인.", good: "비교 기준점, 빠른 프로토타입", weak: "고유명사 매칭, 짧은 청크에서 모호한 답" },
    "02-hybrid-search":       { num: "02", ko: "하이브리드 검색", en: "Hybrid Search",         family: "V1", summary: "BM25(어휘) + 임베딩(의미)을 RRF로 결합.", good: "고유명사·약어 많은 한국어 도메인, 운영 기본", weak: "검색기 2개 운영으로 약간의 복잡도" },
    "03-reranking":           { num: "03", ko: "재정렬", en: "Reranking",                     family: "V1", summary: "1차 검색 N개를 cross-encoder로 정밀 재정렬.", good: "검색 정밀도가 병목일 때", weak: "1차 검색이 빠뜨린 문서는 못 살림. GPU 권장" },
    "04-hyde":                { num: "04", ko: "가설 답변 검색", en: "HyDE",                    family: "V1", summary: "LLM이 만든 가상의 답변 임베딩으로 검색.", good: "질문이 짧거나 어휘가 문서와 동떨어진 경우", weak: "LLM 호출 1회 추가, 가설이 빗나가면 역효과" },
    "05-multi-query":         { num: "05", ko: "다중 질문", en: "Multi-query",                 family: "V1", summary: "질문을 여러 표현으로 확장 후 RRF 합산.", good: "모호한 질문, 회수율 향상이 필요할 때", weak: "검색 호출 N배, LLM 비용 증가" },
    "06-parent-child":        { num: "06", ko: "부모-자식 청크", en: "Parent-Child",           family: "V1", summary: "작은 청크로 검색 + 큰 부모 청크로 컨텍스트 확장.", good: "긴 문서, 청크 단독 의미가 부족한 도메인", weak: "LLM 입력 토큰 증가" },
    "07-contextual-retrieval":{ num: "07", ko: "문맥 보강 검색", en: "Contextual Retrieval",   family: "V1", summary: "각 청크 앞에 문서 맥락을 prepend 후 임베딩 (Anthropic 2024).", good: "단독으로 모호한 청크가 많은 도메인", weak: "인덱싱 시 청크당 LLM 호출 — 비용 큼" },
    "08-self-rag":            { num: "08", ko: "자가 평가 RAG", en: "Self-RAG",                family: "V2", summary: "LLM이 검색 필요 여부 + 청크 유용성을 스스로 판단.", good: "불필요한 검색 절약, 환각 제어", weak: "청크당 평가 호출, 분류 정확도에 의존" },
    "09-crag":                { num: "09", ko: "교정 RAG", en: "Corrective RAG",              family: "V2", summary: "검색 신뢰도 평가 후 부족하면 질문 재작성·재검색.", good: "검색 품질 변동이 큰 도메인, 실패 회복", weak: "평가·재시도 비용, 평가자 정확도 의존" },
    "10-graphrag":            { num: "10", ko: "그래프 RAG", en: "GraphRAG",                  family: "V2", summary: "엔티티·관계 그래프 + 커뮤니티 요약 인덱스 (MS 2024 단순화).", good: "전체 조망·요약형 질문", weak: "인덱싱 비용 매우 큼, 단답형 사실 질문은 약함" },
    "11-raptor":              { num: "11", ko: "RAPTOR 트리", en: "RAPTOR",                    family: "V2", summary: "청크 클러스터링 + LLM 요약으로 깊이 3 트리 구축.", good: "장문·다중 문서 QA, 디테일+요약 동시 필요", weak: "인덱싱 비용, 작은 데이터셋엔 과한 추상화" },
    "12-agentic-rag":         { num: "12", ko: "에이전트형 RAG", en: "Agentic RAG",            family: "V2", summary: "LLM이 검색·계산 도구를 능동 호출 (ReAct).", good: "다단계·혼합 추론 어시스턴트", weak: "LLM 호출 3–5배, 파싱 오류 위험" },
    "13-adaptive-rag":        { num: "13", ko: "적응형 RAG", en: "Adaptive RAG",              family: "V2", summary: "질문 복잡도 분류 후 전략 분기.", good: "질문 다양성이 큰 환경, 비용·품질 자동 최적화", weak: "분류 호출 추가, 오분류 시 부적절한 전략" },
  };

  function metricVal(tech, mkey) {
    const d = window.RAG_DATA.techniques[tech];
    if (!d) return null;
    const v = d.summary[mkey];
    return (typeof v === "number" && isFinite(v)) ? v : null;
  }
  function overall(tech) {
    const d = window.RAG_DATA.techniques[tech];
    if (!d) return null;
    const vals = METRIC_ORDER.map((m) => d.summary[m]).filter((v) => typeof v === "number" && isFinite(v));
    if (!vals.length) return null;
    return vals.reduce((a, b) => a + b, 0) / vals.length;
  }
  function usageTotals(tech) {
    const u = window.RAG_DATA.techniques[tech].usage;
    const idx = u.indexing, inf = u.inference;
    return {
      idxCalls: idx.calls, infCalls: inf.calls,
      idxSec: idx.elapsed_seconds, infSec: inf.elapsed_seconds,
      idxTok: idx.input_tokens + idx.output_tokens, infTok: inf.input_tokens + inf.output_tokens,
      calls: idx.calls + inf.calls,
    };
  }

  return { METRICS, METRIC_ORDER, TECH, metricVal, overall, usageTotals,
           order: () => window.RAG_DATA.order,
           model: "Qwen3.6-27B-FP8", dataset: "한국어 30 · 영어 30 · 위키 샘플" };
})();
