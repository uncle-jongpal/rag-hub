// Page 3 — 인터랙티브 검색 데모 (Interactive search demo)
// 라이브 백엔드 연동: 입력한 질문을 백엔드(/api/query)로 보내 실제 검색 + LLM
// 답변 + 토큰 사용량을 받아 그대로 표시한다. 예시 질문 목록만 평가셋에서 가져온다.
(function () {
  const { METRICS, METRIC_ORDER, TECH, usageTotals } = window.RAGLabels;
  const { fmt } = window.RAGUI;

  const STEPS = ["인덱스 로드", "검색 (retrieve)", "컨텍스트 선택", "LLM 답변 생성"];

  function PageDemo() {
    const order = window.RAG_DATA.order;
    const [tech, setTech] = React.useState("02-hybrid-search");
    const [topk, setTopk] = React.useState(5);
    const [query, setQuery] = React.useState("");
    const [phase, setPhase] = React.useState("idle"); // idle | running | done | error
    const [step, setStep] = React.useState(0);
    const [result, setResult] = React.useState(null);
    const timers = React.useRef([]);

    const suggestions = (window.RAG_DATA.techniques[tech].by_question || []).slice(0, 6).map((r) => r.q);

    const run = async () => {
      const q = query.trim();
      if (!q) return;
      timers.current.forEach(clearTimeout); timers.current = [];
      setPhase("running"); setStep(0); setResult(null);
      // 마지막 단계는 응답이 올 때까지 active 로 유지
      STEPS.forEach((_, i) => {
        if (i < STEPS.length - 1) timers.current.push(setTimeout(() => setStep(i + 1), 360 * (i + 1)));
      });
      try {
        const resp = await fetch("/api/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ technique: tech, query: q, top_k: topk }),
        });
        if (!resp.ok) throw new Error("백엔드 응답 오류 (" + resp.status + ")");
        const data = await resp.json();
        if (data.error) throw new Error(data.error);
        timers.current.forEach(clearTimeout);
        setStep(STEPS.length);
        const u = data.usage || {};
        setResult({
          row: { q, answer: data.answer || "", contexts: data.contexts || [] },
          perCall: {
            calls: u.calls || 0,
            tok: (u.input_tokens || 0) + (u.output_tokens || 0),
            sec: u.elapsed_seconds || 0,
            cost: u.cost_usd || 0,
          },
        });
        setPhase("done");
      } catch (e) {
        timers.current.forEach(clearTimeout);
        setResult({ error: String((e && e.message) || e) });
        setPhase("error");
      }
    };
    React.useEffect(() => () => timers.current.forEach(clearTimeout), []);

    const r = result && result.row;
    const ctxs = r ? (r.contexts || []).slice(0, topk) : [];

    return (
      <div className="wrap fadein">
        <div className="pagehead">
          <div className="eyebrow">03 · Interactive Search</div>
          <h1>인터랙티브 검색 데모</h1>
          <p>기법을 고르고 질문을 입력하면 백엔드가 실제로 검색 → 컨텍스트 선택 → 답변 생성을 실행하고, 답변·사용된 컨텍스트·토큰 사용량을 그대로 보여줍니다.</p>
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
            <div className="ph"><div className="t">실행 · Pipeline</div>{result && !result.error && <div className="meta mono">실시간</div>}</div>
            <div className="pb">
              {phase === "idle" && <div className="empty">질문을 입력하고 <span className="kbd">실행</span> 하세요.</div>}
              {(phase === "running" || phase === "done") && (
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
                  {phase === "running" && <div className="note" style={{ fontSize: 11, marginTop: 4 }}>처음 고른 기법은 인덱스 준비로 시간이 걸릴 수 있습니다.</div>}
                </div>
              )}
              {phase === "error" && result && (
                <div className="note" style={{ borderColor: "rgba(199,121,27,.3)", background: "rgba(199,121,27,.06)" }}>
                  <b style={{ color: "var(--warn)" }}>실행 실패</b> — {result.error}
                </div>
              )}
              {phase === "done" && result && (
                <div className="fadein" style={{ marginTop: 16, borderTop: "1px solid var(--line)", paddingTop: 14 }}>
                  <label className="fl">토큰 / 비용 (이번 호출)</label>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
                    {[["LLM 호출", result.perCall.calls, ""], ["토큰", result.perCall.tok.toLocaleString(), ""], ["시간", result.perCall.sec.toFixed(2), "s"]].map(([l, v, suf]) => (
                      <div key={l} style={{ background: "var(--soft)", border: "1px solid var(--line)", borderRadius: 8, padding: "11px 12px" }}>
                        <div style={{ fontSize: 10.5, color: "var(--mut)", marginBottom: 5 }}>{l}</div>
                        <div className="mono" style={{ fontSize: 18, fontWeight: 600 }}>{v}<small style={{ fontSize: 11, color: "var(--mut)" }}>{suf}</small></div>
                      </div>
                    ))}
                  </div>
                  <div className="note mono" style={{ marginTop: 12, fontSize: 11 }}>추정 비용 ${result.perCall.cost.toFixed(5)} — {window.RAGLabels.model}.</div>
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
              <div className="meta">질문: <b style={{ color: "var(--ink)" }}>{r.q}</b></div>
            </div>
            <div className="pb">
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
