// Page 4 — 비용 / 지연 추적 (Cost & latency)
(function () {
  const { TECH, usageTotals, model, dataset } = window.RAGLabels;
  const IDX = "#5b6370", INF = "#0f9d76";

  const MEASURES = {
    calls: { ko: "LLM 호출 수", en: "Calls", unit: "", fmt: (v) => v.toLocaleString(), get: (u) => [u.idxCalls, u.infCalls] },
    time:  { ko: "호출 시간",   en: "Time",  unit: "s", fmt: (v) => v >= 100 ? Math.round(v).toLocaleString() : v.toFixed(1), get: (u) => [u.idxSec, u.infSec] },
    tokens:{ ko: "토큰 합",     en: "Tokens",unit: "", fmt: (v) => v.toLocaleString(), get: (u) => [u.idxTok, u.infTok] },
  };

  function PageCost() {
    const order = window.RAG_DATA.order;
    const [measure, setMeasure] = React.useState("calls");
    const M = MEASURES[measure];
    const rows = order.map((t) => { const u = usageTotals(t); const [a, b] = M.get(u); return { t, idx: a, inf: b, total: a + b }; });
    const sorted = [...rows].sort((x, y) => y.total - x.total);
    const max = Math.max(...rows.map((r) => r.total)) || 1;
    const heaviestIdx = [...rows].sort((a, b) => b.idx - a.idx)[0];

    return (
      <div className="wrap fadein">
        <div className="pagehead">
          <div className="eyebrow">04 · Cost & Latency</div>
          <h1>비용 / 지연 추적</h1>
          <p>각 기법이 얼마나 무거운지 정량 비교합니다. <b style={{color:"var(--ink)"}}>인덱싱</b>은 문서를 가공·저장하는 1회성 작업, <b style={{color:"var(--ink)"}}>추론</b>은 질문마다 반복되는 작업입니다. 운영 비용은 추론을 더 중요하게 보세요.</p>
        </div>

        <div className="kpis" style={{ gridTemplateColumns: "repeat(3,1fr)" }}>
          <div className="kpi"><div className="l"><span>Heaviest indexing</span><span>최대 인덱싱</span></div><div className="n kr" style={{ fontSize: 19, fontWeight: 600 }}>{TECH[heaviestIdx.t].ko}</div><div className="d">청크당 LLM 호출 {heaviestIdx.idx.toLocaleString()}회</div></div>
          <div className="kpi"><div className="l"><span>Model</span><span>모델</span></div><div className="n" style={{ fontSize: 17, fontWeight: 600 }}>{model}</div><div className="d">로컬 추론 · 청구 비용 $0.00</div></div>
          <div className="kpi"><div className="l"><span>Dataset</span><span>데이터셋</span></div><div className="n" style={{ fontSize: 17, fontWeight: 600 }}>한 30 · 영 30</div><div className="d">{dataset}</div></div>
        </div>

        <div className="panel" style={{ marginBottom: 16 }}>
          <div className="ph">
            <div className="t">{M.ko} <span className="en">{M.en} · 인덱싱 vs 추론</span></div>
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{ display: "flex", gap: 14 }}>
                <span className="dotline"><span className="dotsm" style={{ background: IDX }}></span>인덱싱</span>
                <span className="dotline"><span className="dotsm" style={{ background: INF }}></span>추론</span>
              </div>
              <div className="seg">
                {Object.keys(MEASURES).map((k) => <div key={k} className={"sg" + (measure === k ? " on" : "")} onClick={() => setMeasure(k)}>{MEASURES[k].ko}</div>)}
              </div>
            </div>
          </div>
          <div className="pb">
            {sorted.map((r) => (
              <div key={r.t} style={{ display: "grid", gridTemplateColumns: "172px 1fr 120px", alignItems: "center", gap: 14, padding: "8px 0" }}>
                <div className="kr" style={{ fontSize: 12.5, fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{TECH[r.t].ko}</div>
                <div style={{ display: "flex", height: 16, background: "var(--line2)", borderRadius: 4, overflow: "hidden" }}>
                  <div title={"인덱싱 " + M.fmt(r.idx)} style={{ width: (r.idx / max * 100) + "%", background: IDX, transition: "width .5s cubic-bezier(.2,.7,.2,1)" }}></div>
                  <div title={"추론 " + M.fmt(r.inf)} style={{ width: (r.inf / max * 100) + "%", background: INF, transition: "width .5s cubic-bezier(.2,.7,.2,1)" }}></div>
                </div>
                <div className="mono" style={{ fontSize: 12, textAlign: "right", color: "var(--ink2)" }}>
                  <span style={{ color: IDX }}>{M.fmt(r.idx)}</span> / <span style={{ color: INF }}>{M.fmt(r.inf)}</span>{M.unit}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="ph"><div className="t">상세 · Breakdown</div><div className="meta mono">idx = 인덱싱 · inf = 추론</div></div>
          <div className="scrollx">
            <table className="mtx">
              <thead><tr>
                <th className="l">기법</th>
                <th>인덱싱 호출</th><th>추론 호출</th>
                <th>인덱싱 시간(s)</th><th>추론 시간(s)</th>
                <th>인덱싱 토큰</th><th>추론 토큰</th>
              </tr></thead>
              <tbody>
                {order.map((t) => { const u = usageTotals(t); return (
                  <tr key={t}>
                    <td className="l kr" style={{ fontWeight: 500 }}>{TECH[t].ko}<small>{TECH[t].num}</small></td>
                    <td className="mono" style={{ fontWeight: 400 }}>{u.idxCalls.toLocaleString()}</td>
                    <td className="mono" style={{ fontWeight: 400 }}>{u.infCalls}</td>
                    <td className="mono" style={{ fontWeight: 400 }}>{u.idxSec >= 100 ? Math.round(u.idxSec).toLocaleString() : u.idxSec.toFixed(1)}</td>
                    <td className="mono" style={{ fontWeight: 400 }}>{u.infSec.toFixed(1)}</td>
                    <td className="mono" style={{ fontWeight: 400 }}>{u.idxTok.toLocaleString()}</td>
                    <td className="mono" style={{ fontWeight: 400 }}>{u.infTok.toLocaleString()}</td>
                  </tr>
                ); })}
              </tbody>
            </table>
          </div>
        </div>
        <div className="note" style={{ marginTop: 16 }}>인덱싱 호출이 큰 <b>문맥 보강(07)·그래프(10)·RAPTOR(11)</b>는 청크마다 LLM을 호출해 인덱스를 만듭니다. 한 번만 드는 비용이지만 초기 구축 시간이 깁니다. 나머지 기법은 인덱싱에 LLM을 쓰지 않아 추론 비용만 발생합니다.</div>
      </div>
    );
  }
  window.PageCost = PageCost;
})();
