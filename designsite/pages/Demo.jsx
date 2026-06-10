// Page 3 — 인터랙티브 검색 데모 (Interactive search demo)
// No live backend in the prototype: a typed/selected question is matched to the
// technique's real evaluated answer + contexts + token usage, with a simulated run.
(function () {
  const { METRICS, METRIC_ORDER, TECH, usageTotals } = window.RAGLabels;
  const { fmt } = window.RAGUI;

  const tokenize = (s) => (s || "").toLowerCase().replace(/[^가-힣a-z0-9\s]/g, " ").split(/\s+/).filter((w) => w.length > 1);
  function bestMatch(tech, query) {
    const qs = window.RAG_DATA.techniques[tech].by_question || [];
    const qtok = new Set(tokenize(query));
    let best = null, bestScore = -1;
    for (const r of qs) {
      const rtok = tokenize(r.q);
      let s = 0; for (const w of rtok) if (qtok.has(w)) s++;
      const ratio = rtok.length ? s / rtok.length : 0;
      if (ratio > bestScore) { bestScore = ratio; best = r; }
    }
    return { row: best, score: bestScore };
  }

  const STEPS = ["인덱스 로드", "검색 (retrieve)", "컨텍스트 선택", "LLM 답변 생성"];

  function PageDemo() {
    const order = window.RAG_DATA.order;
    const [tech, setTech] = React.useState("02-hybrid-search");
    const [topk, setTopk] = React.useState(5);
    const [query, setQuery] = React.useState("");
    const [phase, setPhase] = React.useState("idle"); // idle | running | done
    const [step, setStep] = React.useState(0);
    const [result, setResult] = React.useState(null);
    const timers = React.useRef([]);

    const suggestions = (window.RAG_DATA.techniques[tech].by_question || []).slice(0, 6).map((r) => r.q);

    const run = () => {
      if (!query.trim()) return;
      timers.current.forEach(clearTimeout); timers.current = [];
      setPhase("running"); setStep(0); setResult(null);
      STEPS.forEach((_, i) => timers.current.push(setTimeout(() => setStep(i + 1), 380 * (i + 1))));
      timers.current.push(setTimeout(() => {
        const m = bestMatch(tech, query);
        const u = usageTotals(tech);
        const nq = (window.RAG_DATA.techniques[tech].by_question || []).length || 1;
        setResult({
          row: m.row, score: m.score,
          perCall: { calls: Math.max(1, Math.round(u.infCalls / nq)), tok: Math.round(u.infTok / nq), sec: u.infSec / nq },
        });
        setPhase("done");
      }, 380 * (STEPS.length + 1)));
    };
    React.useEffect(() => () => timers.current.forEach(clearTimeout), []);

    const r = result && result.row;
    const ctxs = r ? (r.contexts || []).slice(0, topk) : [];

    return (
      <div className="wrap fadein">
        <div className="pagehead">
          <div className="eyebrow">03 · Interactive Search</div>
          <h1>인터랙티브 검색 데모</h1>
          <p>기법을 고르고 질문을 입력하면 검색 → 컨텍스트 → 답변 흐름을 실행합니다. 이 프로토타입은 평가셋에 기록된 실제 답변·컨텍스트·토큰 사용량을 매칭해 보여줍니다.</p>
        </div>

        <div className="grid2" style={{ alignItems: "start" }}>
          {/* control */}
          <div className="panel">
            <div className="ph"><div className="t">질의 · Query</div></div>
            <div className="pb" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div>
                <label className="fl">기법 · Technique</label>
                <select className="input" value={tech} onChange={(e) => { setTech(e.target.value); setPhase("idle"); setResult(null); }}>
                  {order.map((t) => <option key={t} value={t}>{TECH[t].num} · {TECH[t].ko} ({TECH[t].en})</option>)}
                </select>
                <div className="note" style={{ marginTop: 10 }}><b>{TECH[tech].ko}</b> — {TECH[tech].summary}</div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 120px", gap: 12, alignItems: "end" }}>
                <div>
                  <label className="fl">질문 입력 · Question</label>
                  <input className="input" value={query} placeholder="예) 한글을 창제한 조선의 왕은?" onChange={(e) => setQuery(e.target.value)}
                         onKeyDown={(e) => { if (e.key === "Enter") run(); }} />
                </div>
                <div>
                  <label className="fl">top_k</label>
                  <input className="input mono" type="number" min={1} max={10} value={topk} onChange={(e) => setTopk(Math.max(1, Math.min(10, +e.target.value || 1)))} />
                </div>
              </div>
              <div>
                <label className="fl">예시 질문 · Try one</label>
                <div className="chips">
                  {suggestions.map((s) => <div key={s} className="chip" style={{ fontSize: 11.5, padding: "6px 11px" }} onClick={() => setQuery(s)}>{s}</div>)}
                </div>
              </div>
              <button className="btn primary" onClick={run} disabled={!query.trim() || phase === "running"}>
                {phase === "running" ? "실행 중…" : "검색 실행 →"}
              </button>
            </div>
          </div>

          {/* run status / usage */}
          <div className="panel">
            <div className="ph"><div className="t">실행 · Pipeline</div>{result && <div className="meta mono">match {Math.round(result.score * 100)}%</div>}</div>
            <div className="pb">
              {phase === "idle" && <div className="empty">질문을 입력하고 <span className="kbd">실행</span> 하세요.</div>}
              {phase !== "idle" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {STEPS.map((s, i) => {
                    const state = step > i ? "done" : (step === i && phase === "running" ? "active" : "pending");
                    return (
                      <div key={s} className="dotline" style={{ fontSize: 12.5, color: state === "pending" ? "var(--faint)" : "var(--ink)" }}>
                        <span className="dotsm" style={{ background: state === "done" ? "var(--accent)" : state === "active" ? "var(--warn)" : "var(--line)" }}></span>
                        {s} {state === "done" && <span style={{ color: "var(--accent)", marginLeft: 4 }}>✓</span>}{state === "active" && <span style={{ color: "var(--warn)", marginLeft: 4 }}>…</span>}
                      </div>
                    );
                  })}
                </div>
              )}
              {phase === "done" && result && (
                <div className="fadein" style={{ marginTop: 16, borderTop: "1px solid var(--line)", paddingTop: 14 }}>
                  <label className="fl">토큰 / 비용 (이번 호출 추정)</label>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
                    {[["LLM 호출", result.perCall.calls, ""], ["토큰", result.perCall.tok.toLocaleString(), ""], ["시간", result.perCall.sec.toFixed(2), "s"]].map(([l, v, suf]) => (
                      <div key={l} style={{ background: "var(--soft)", border: "1px solid var(--line)", borderRadius: 8, padding: "11px 12px" }}>
                        <div style={{ fontSize: 10.5, color: "var(--mut)", marginBottom: 5 }}>{l}</div>
                        <div className="mono" style={{ fontSize: 18, fontWeight: 600 }}>{v}<small style={{ fontSize: 11, color: "var(--mut)" }}>{suf}</small></div>
                      </div>
                    ))}
                  </div>
                  <div className="note mono" style={{ marginTop: 12, fontSize: 11 }}>비용 $0.00 — 로컬 {window.RAGLabels.model} (무료). 토큰은 추론 누적 ÷ 질문 수 추정.</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* answer + contexts */}
        {phase === "done" && r && (
          <div className="panel fadein" style={{ marginTop: 16 }}>
            <div className="ph">
              <div className="t">답변 · Answer</div>
              <div className="meta">가장 가까운 평가 질문: <b style={{ color: "var(--ink)" }}>{r.q}</b></div>
            </div>
            <div className="pb">
              {result.score < 0.34 && <div className="note" style={{ marginBottom: 14, borderColor: "rgba(199,121,27,.3)", background: "rgba(199,121,27,.06)" }}><b style={{ color: "var(--warn)" }}>데모 안내</b> — 입력 질문과 평가셋의 일치도가 낮습니다. 가장 가까운 기록 결과를 보여줍니다.</div>}
              <div style={{ fontSize: 14, lineHeight: 1.7, whiteSpace: "pre-wrap", marginBottom: 18 }}>{r.answer}</div>
              <label className="fl">사용된 컨텍스트 · top_k = {topk}</label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {ctxs.map((c, i) => (
                  <div key={i} className="note" style={{ fontSize: 12, lineHeight: 1.6 }}>
                    <span className="mono" style={{ color: "var(--accent)", marginRight: 6 }}>{String(i + 1).padStart(2, "0")}</span>{c}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }
  window.PageDemo = PageDemo;
})();
