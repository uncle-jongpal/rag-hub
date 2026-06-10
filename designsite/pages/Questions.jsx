// Page 2 — 질문별 결과 (Per-question comparison)
(function () {
  const { METRICS, METRIC_ORDER, TECH, overall } = window.RAGLabels;
  const { fmt, scoreBg, scoreInk } = window.RAGUI;

  // build question -> { tech: row }
  function buildIndex() {
    const idx = {};
    for (const t of window.RAG_DATA.order) {
      for (const r of window.RAG_DATA.techniques[t].by_question || []) {
        if (!r.q) continue;
        (idx[r.q] = idx[r.q] || {})[t] = r;
      }
    }
    return idx;
  }
  const ScoreBadge = ({ v }) => (
    <span className="badge-score mono" style={{ background: scoreBg(v), color: scoreInk(v) }}>{fmt(v)}</span>
  );

  function PageQuestions() {
    const idx = React.useMemo(buildIndex, []);
    const questions = Object.keys(idx);
    const [q, setQ] = React.useState(questions[0]);
    const techsForQ = Object.keys(idx[q] || {}).sort();
    const byOverall = [...window.RAG_DATA.order].sort((a, b) => (overall(b) ?? -1) - (overall(a) ?? -1));
    const [techs, setTechs] = React.useState(byOverall.slice(0, 3));
    const active = techs.filter((t) => idx[q] && idx[q][t]);
    const sample = idx[q] ? Object.values(idx[q])[0] : null;
    const gt = sample && (sample.reference || "");

    const toggle = (t) => setTechs((c) => c.includes(t) ? c.filter((x) => x !== t) : [...c, t]);

    return (
      <div className="wrap fadein">
        <div className="pagehead">
          <div className="eyebrow">02 · Per-Question Results</div>
          <h1>질문별 결과 보기</h1>
          <p>같은 질문에 대해 기법들이 어떤 답변과 컨텍스트를 만들었는지 나란히 비교합니다. 정답과 비교해 어느 기법이 환각을 일으키는지, 핵심을 놓치는지 파악할 수 있습니다.</p>
        </div>

        <div className="panel" style={{ marginBottom: 16 }}>
          <div className="pb" style={{ display: "grid", gridTemplateColumns: "1fr", gap: 14 }}>
            <div>
              <label className="fl">질문 선택 · Question ({questions.length}개)</label>
              <select className="input" value={q} onChange={(e) => setQ(e.target.value)}>
                {questions.map((qq, i) => <option key={qq} value={qq}>{String(i + 1).padStart(2, "0")} · {qq}</option>)}
              </select>
            </div>
            <div>
              <label className="fl">비교할 기법 · Techniques ({active.length} / {techsForQ.length})</label>
              <div className="chips">
                {techsForQ.map((t) => (
                  <div key={t} className={"chip" + (techs.includes(t) ? " on" : "")} onClick={() => toggle(t)} style={{ fontSize: 11.5, padding: "6px 11px" }}>
                    {TECH[t].ko}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {gt ? (
          <div className="note" style={{ marginBottom: 16, borderColor: "rgba(15,157,118,.3)", background: "rgba(15,157,118,.05)" }}>
            <b style={{ color: "var(--accent)" }}>정답 · Ground Truth</b><br/>{gt}
          </div>
        ) : null}

        {active.length === 0 ? (
          <div className="panel"><div className="empty">기법을 1개 이상 선택하세요.</div></div>
        ) : (
          <div className="scrollx">
            <div style={{ display: "grid", gridAutoFlow: "column", gridAutoColumns: "minmax(340px, 1fr)", gap: 16 }}>
              {active.map((t) => {
                const r = idx[q][t];
                return (
                  <div key={t} className="panel fadein" style={{ display: "flex", flexDirection: "column" }}>
                    <div className="ph">
                      <div className="t kr">{TECH[t].ko}<span className="en">{TECH[t].en}</span></div>
                      <span className={"tag " + (TECH[t].family === "V1" ? "v1" : "v2")}>{TECH[t].family}</span>
                    </div>
                    <div className="pb" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                      <div>
                        <label className="fl">답변 · Answer</label>
                        <div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--ink)", whiteSpace: "pre-wrap" }}>{r.answer || "—"}</div>
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 8 }}>
                        {METRIC_ORDER.map((m) => (
                          <div key={m} style={{ textAlign: "center" }}>
                            <div style={{ fontSize: 9.5, color: "var(--mut)", textTransform: "uppercase", letterSpacing: ".04em", marginBottom: 5 }}>{METRICS[m].abbr}</div>
                            <ScoreBadge v={r[m]} />
                          </div>
                        ))}
                      </div>
                      <div>
                        <label className="fl">사용된 컨텍스트 · Contexts ({(r.contexts || []).length})</label>
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                          {(r.contexts || []).map((c, i) => (
                            <div key={i} className="note" style={{ fontSize: 11.5, lineHeight: 1.55, padding: "9px 11px" }}>
                              <span className="mono" style={{ color: "var(--accent)", marginRight: 6 }}>{i + 1}</span>{c}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  }
  window.PageQuestions = PageQuestions;
})();
