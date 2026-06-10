// Page 1 — 기법 비교 (Technique Comparison)
(function () {
  const { METRICS, METRIC_ORDER, TECH, metricVal, overall, usageTotals, model, dataset } = window.RAGLabels;
  const { fmt, scoreBg, scoreInk, Radar, useHoverTip } = window.RAGUI;
  const CMP = ["var(--accent)", "#5b6370", "#c7791b"];

  function PageCompare() {
    const order = window.RAG_DATA.order;
    const [metric, setMetric] = React.useState("overall");
    const score = (t) => metric === "overall" ? overall(t) : metricVal(t, metric);
    const ranked = [...order].sort((a, b) => (score(b) ?? -1) - (score(a) ?? -1));
    const maxV = Math.max(...ranked.map((t) => score(t) ?? 0)) || 1;
    const top = ranked[0];
    const avg = order.reduce((s, t) => s + (overall(t) ?? 0), 0) / order.length;
    const [sel, setSel] = React.useState(top);
    const [cmp, setCmp] = React.useState([]);
    const { bind, Tip } = useHoverTip();

    const toggleCmp = (t) => setCmp((c) => c.includes(t) ? c.filter((x) => x !== t) : (c.length >= 2 ? [c[1], t] : [...c, t]));
    const series = [{ tech: sel, color: CMP[0], fillOpacity: 0.16 }, ...cmp.map((t, i) => ({ tech: t, color: CMP[i + 1], fillOpacity: 0.06 }))];
    const S = TECH[sel], u = usageTotals(sel);

    return (
      <div className="wrap fadein">
        <div className="pagehead">
          <div className="eyebrow">01 · Technique Comparison</div>
          <h1>기법 비교 — RAGAS 메트릭</h1>
          <p>13개 기법을 같은 평가셋 위에서 4개 메트릭으로 정량 비교합니다. 점수는 0–1, 1에 가까울수록 좋습니다. 막대·표의 행을 누르면 아래에서 상세를 봅니다.</p>
        </div>

        <div className="kpis">
          <div className="kpi"><div className="l"><span>Techniques</span><span>기법</span></div><div className="n mono">13</div><div className="d">V1 검색·쿼리 7 · V2 구조·에이전트 6</div></div>
          <div className="kpi"><div className="l"><span>Metrics</span><span>RAGAS</span></div><div className="n mono">4</div><div className="d">충실도·적합성·정확도·완전성</div></div>
          <div className="kpi"><div className="l"><span>Top Overall</span><span>최고</span></div><div className="n mono" style={{ color: "var(--accent)" }}>{fmt(overall(top))}</div><div className="d">{TECH[top].ko} ({TECH[top].en})</div></div>
          <div className="kpi"><div className="l"><span>Mean Overall</span><span>평균</span></div><div className="n mono">{fmt(avg)}</div><div className="d">13개 기법 종합 평균</div></div>
        </div>

        <div className="grid2" style={{ marginBottom: 16 }}>
          {/* ranking */}
          <div className="panel">
            <div className="ph">
              <div className="t">순위 <span className="en">Ranking</span></div>
              <div className="seg">
                <div className={"sg" + (metric === "overall" ? " on" : "")} onClick={() => setMetric("overall")}>종합</div>
                {METRIC_ORDER.map((m) => <div key={m} className={"sg" + (metric === m ? " on" : "")} onClick={() => setMetric(m)}>{METRICS[m].abbr}</div>)}
              </div>
            </div>
            {ranked.map((t, i) => {
              const v = score(t);
              return (
                <div key={t} className={"brow" + (i === 0 ? " top1" : "") + (t === sel ? " sel" : "")}
                     style={{ gridTemplateColumns: "22px 1fr 150px 46px" }}
                     onClick={() => setSel(t)} {...bind(t)}>
                  <div className="rk mono">{String(i + 1).padStart(2, "0")}</div>
                  <div className="nm kr">{TECH[t].ko}<span className="en">{TECH[t].en}</span></div>
                  <div className="track"><div className="fill" style={{ width: ((v ?? 0) / maxV * 100) + "%" }}></div></div>
                  <div className="val mono">{fmt(v)}</div>
                </div>
              );
            })}
          </div>

          {/* matrix */}
          <div className="panel">
            <div className="ph"><div className="t">메트릭 매트릭스 <span className="en">Matrix</span></div><div className="meta mono">0.00 – 1.00</div></div>
            <div className="scrollx">
              <table className="mtx">
                <thead><tr>
                  <th className="l">기법</th>
                  {METRIC_ORDER.map((m) => <th key={m}>{METRICS[m].abbr}</th>)}
                  <th style={{ color: "var(--accent)" }}>종합</th>
                </tr></thead>
                <tbody>
                  {order.map((t) => (
                    <tr key={t} className={t === sel ? "sel" : ""} onClick={() => setSel(t)} {...bind(t)}>
                      <td className="l kr">{TECH[t].num}<small>{TECH[t].en}</small></td>
                      {METRIC_ORDER.map((m) => { const v = metricVal(t, m); return <td key={m} className="mono" style={{ background: scoreBg(v), color: scoreInk(v) }}>{fmt(v)}</td>; })}
                      {(() => { const v = overall(t); return <td className="mono" style={{ background: scoreBg(v), color: scoreInk(v), fontWeight: 700 }}>{fmt(v)}</td>; })()}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* detail */}
        <div className="panel">
          <div className="ph">
            <div className="t">기법 상세 <span className="en">Detail · {S.en}</span></div>
            <span className={"tag " + (S.family === "V1" ? "v1" : "v2")}>{S.family} · {S.family === "V1" ? "검색·쿼리·청킹" : "자가교정·구조·에이전트"}</span>
          </div>
          <div className="pb" style={{ display: "grid", gridTemplateColumns: "250px 1fr 1.1fr", gap: 24, alignItems: "start" }}>
            <div>
              <Radar series={series} size={250} />
              <div className="chips" style={{ marginTop: 6, justifyContent: "center" }}>
                <span className="dotline"><span className="dotsm" style={{ background: CMP[0] }}></span>{S.ko}</span>
              </div>
            </div>

            <div>
              <div style={{ fontSize: 17, fontWeight: 600, marginBottom: 2 }}>{S.ko}</div>
              <div style={{ fontSize: 12, color: "var(--mut)", marginBottom: 16 }}>{TECH[sel].num} · {S.en}</div>
              {METRIC_ORDER.map((m) => { const v = metricVal(sel, m); return (
                <div key={m} style={{ marginBottom: 13 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 5 }}>
                    <span>{METRICS[m].ko} <span style={{ color: "var(--mut)" }}>{METRICS[m].en}</span></span>
                    <span className="mono" style={{ fontWeight: 600 }}>{fmt(v)}</span>
                  </div>
                  <div className="track"><div className="fill" style={{ width: ((v ?? 0) * 100) + "%" }}></div></div>
                </div>
              ); })}
              <div className="note" style={{ marginTop: 16 }}>
                <b>종합 {fmt(overall(sel))}</b> · 인덱싱 {u.idxCalls.toLocaleString()}콜 · 추론 {u.infCalls}콜 · 인덱싱 {Math.round(u.idxSec)}s
              </div>
            </div>

            <div>
              <div className="note" style={{ marginBottom: 12 }}><b>한 줄 요약</b><br/>{S.summary}</div>
              <div style={{ display: "flex", gap: 12 }}>
                <div className="note" style={{ flex: 1, borderColor: "rgba(15,157,118,.3)", background: "rgba(15,157,118,.05)" }}><b style={{ color: "var(--accent)" }}>잘 맞는 경우</b><br/>{S.good}</div>
                <div className="note" style={{ flex: 1, borderColor: "rgba(199,121,27,.3)", background: "rgba(199,121,27,.05)" }}><b style={{ color: "var(--warn)" }}>주의할 점</b><br/>{S.weak}</div>
              </div>
              <div style={{ marginTop: 16 }}>
                <label className="fl">레이더에 겹쳐 비교 (최대 2개)</label>
                <div className="chips">
                  {order.filter((t) => t !== sel).map((t) => (
                    <div key={t} className={"chip" + (cmp.includes(t) ? " on" : "")} onClick={() => toggleCmp(t)} style={{ fontSize: 11, padding: "5px 10px" }}>{TECH[t].ko}</div>
                  ))}
                </div>
                {cmp.length > 0 && (
                  <div className="chips" style={{ marginTop: 10 }}>
                    {cmp.map((t, i) => <span key={t} className="dotline"><span className="dotsm" style={{ background: CMP[i + 1] }}></span>{TECH[t].ko}</span>)}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        {Tip}
      </div>
    );
  }
  window.PageCompare = PageCompare;
})();
