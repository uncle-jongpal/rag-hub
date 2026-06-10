// Page 5 — 가이드 (Guide: metrics, techniques, interpretation)
(function () {
  const { METRICS, METRIC_ORDER, TECH } = window.RAGLabels;

  const METRIC_CALC = {
    faithfulness: "답변을 문장 단위로 쪼개고, 각 문장이 컨텍스트에 의해 지지되는지 LLM으로 판정합니다. 컨텍스트 밖 정보가 많을수록 점수가 떨어집니다.",
    answer_relevancy: "답변으로부터 가상의 질문 N개를 생성하고, 그 질문들과 원 질문의 임베딩 유사도를 평균냅니다. (본 레포는 BGE-M3 사용)",
    context_precision: "검색된 컨텍스트 중 정답에 직접 기여한 청크의 비율. 순위까지 반영해 앞순위에 정답이 있으면 점수가 높습니다.",
    context_recall: "정답 텍스트의 각 주장(claim)이 검색된 컨텍스트에 의해 지지되는 비율. 정답 라벨이 필요한 메트릭입니다.",
  };
  const INTERP = [
    ["충실도가 낮다", "환각 발생. 검색은 좋은데 LLM이 자료를 무시. 프롬프트 강화 또는 더 작은 모델 검토"],
    ["답변 적합성이 낮다", "답이 질문 핵심을 빗나감. 더 큰 LLM 또는 질문 처리(HyDE·Multi-query) 적용"],
    ["검색 정확도가 낮다", "무관한 청크가 많이 들어옴. Reranking 추가, 청크 크기 조정"],
    ["검색 완전성이 낮다", "정답에 필요한 정보가 검색에 빠짐. Hybrid Search·Multi-query·청크 오버랩 확대"],
  ];
  const  ORDER_REC = [
    "단순 임베딩 검색(01)로 베이스라인 확보 — 빠르게 동작 확인",
    "하이브리드 검색(02) 추가 — 한국어 환경에서 큰 효과, 운영 표준",
    "재정렬(03) — 검색 정확도가 답 품질의 병목이면 적용",
    "문맥 보강(07) — 청크 단독으로 모호한 도메인(법률·매뉴얼·사내 문서)",
    "가설 답변(04)·다중 질문(05) — 질문이 짧거나 모호할 때",
    "자가 평가(08)·교정(09) — 환각 통제, 검색 실패 회복",
    "그래프(10)·트리(11) — 요약형·전체 조망 질문이 많을 때",
    "에이전트(12)·적응형(13) — 다단계 추론, 질문 다양성이 큰 환경",
  ];

  function MetricCard({ m }) {
    const [open, setOpen] = React.useState(false);
    const M = METRICS[m];
    return (
      <div className="panel" style={{ cursor: "pointer" }} onClick={() => setOpen((o) => !o)}>
        <div className="ph"><div className="t">{M.ko} <span className="en">{M.en}</span></div><span style={{ color: "var(--mut)", fontSize: 14 }}>{open ? "–" : "+"}</span></div>
        <div className="pb">
          <div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--ink2)" }}>{M.desc}</div>
          {open && <div className="note" style={{ marginTop: 12 }}><b>계산 방식</b><br/>{METRIC_CALC[m]}</div>}
        </div>
      </div>
    );
  }

  function PageGuide() {
    return (
      <div className="wrap fadein" style={{ maxWidth: 1060 }}>
        <div className="pagehead">
          <div className="eyebrow">05 · Guide</div>
          <h1>가이드 — 메트릭과 기법 이해하기</h1>
          <p>처음 보는 사람도 따라갈 수 있는 학습 페이지입니다. RAG는 LLM이 외부 지식 베이스를 참조해 답을 만드는 방식이고, 그 안에서 다양한 검색·청크·평가 전략이 발전해왔습니다.</p>
        </div>

        <h2 style={{ fontSize: 16, fontWeight: 600, margin: "8px 0 14px" }}>RAGAS 메트릭 네 가지</h2>
        <div className="note" style={{ marginBottom: 14 }}>RAGAS는 LLM을 평가자로 활용해 RAG 품질을 정량화하는 프레임워크입니다. 카드를 누르면 계산 방식이 펼쳐집니다.</div>
        <div className="grid2" style={{ marginBottom: 30 }}>
          {METRIC_ORDER.map((m) => <MetricCard key={m} m={m} />)}
        </div>

        <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 14px" }}>결과 해석 가이드</h2>
        <div className="grid2" style={{ marginBottom: 30 }}>
          {INTERP.map(([k, v]) => (
            <div key={k} className="note" style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
              <span className="dotsm" style={{ background: "var(--warn)", marginTop: 6, flex: "0 0 auto" }}></span>
              <div><b>{k}</b><br/><span style={{ color: "var(--ink2)" }}>{v}</span></div>
            </div>
          ))}
        </div>

        <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 14px" }}>기법 13가지 한눈 보기</h2>
        <div className="grid3" style={{ marginBottom: 30 }}>
          {window.RAG_DATA.order.map((t) => {
            const T = TECH[t];
            return (
              <div key={t} className="panel">
                <div className="pb" style={{ display: "flex", flexDirection: "column", gap: 9 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span className="mono" style={{ fontSize: 11, color: "var(--mut)" }}>{T.num}</span>
                    <span className={"tag " + (T.family === "V1" ? "v1" : "v2")}>{T.family}</span>
                  </div>
                  <div><div style={{ fontSize: 14, fontWeight: 600 }}>{T.ko}</div><div style={{ fontSize: 11, color: "var(--mut)" }}>{T.en}</div></div>
                  <div style={{ fontSize: 12, lineHeight: 1.55, color: "var(--ink2)" }}>{T.summary}</div>
                  <div style={{ fontSize: 11.5, color: "var(--accent)" }}>✓ {T.good}</div>
                  <div style={{ fontSize: 11.5, color: "var(--warn)" }}>! {T.weak}</div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="grid2">
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 14px" }}>운영 시작 추천 순서</h2>
            <div className="panel"><div className="pb" style={{ display: "flex", flexDirection: "column", gap: 0 }}>
              {ORDER_REC.map((s, i) => (
                <div key={i} style={{ display: "flex", gap: 12, padding: "10px 0", borderBottom: i < ORDER_REC.length - 1 ? "1px solid var(--line)" : "none" }}>
                  <span className="mono" style={{ color: "var(--accent)", fontWeight: 600, flex: "0 0 auto" }}>{i + 1}</span>
                  <span style={{ fontSize: 12.5, lineHeight: 1.5 }}>{s}</span>
                </div>
              ))}
            </div></div>
          </div>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 14px" }}>한계 및 주의</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div className="note">본 평가는 데모셋(한 30 + 영 30) 기준입니다. 도메인 데이터로 재평가하지 않으면 운영 의사결정에 그대로 쓰기 어렵습니다.</div>
              <div className="note">일부 기법(GraphRAG·RAPTOR·Self-RAG·CRAG·Adaptive)은 원논문의 단순화 버전입니다. 풀스펙은 더 무겁고 정확합니다.</div>
              <div className="note">로컬 {window.RAGLabels.model} 추론으로 청구 비용은 $0이며, 토큰·시간만 추적됩니다.</div>
              <div className="note"><b>08 자가 평가 RAG</b>의 일부 메트릭이 0으로 나온 것은 평가 LLM 판정 실패로 측정되지 않은 케이스입니다 — 점수를 그대로 신뢰하기보다 재실행 권장.</div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  window.PageGuide = PageGuide;
})();
