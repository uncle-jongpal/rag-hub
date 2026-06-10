// Shared UI helpers for the Console app (window.RAGUI).
(function () {
  const { METRICS, METRIC_ORDER, TECH, metricVal, overall } = window.RAGLabels;
  const fmt = (v, d = 2) => (v == null || !isFinite(v)) ? "—" : v.toFixed(d);
  // live-tweakable: accent rgb + color scale mode read from globals
  const acc = () => window.__ragAccent || [15, 157, 118];
  const scale = () => window.__ragScale || "mono";
  const scoreBg = (v) => {
    if (v == null) return "#fbfbfb";
    const a = acc();
    if (scale() === "div") {
      if (v >= 0.5) { const k = (v - 0.5) / 0.5; return `rgba(${a[0]},${a[1]},${a[2]},${(0.06 + k * 0.5).toFixed(3)})`; }
      const k = (0.5 - v) / 0.5; return `rgba(196,69,63,${(0.06 + k * 0.5).toFixed(3)})`;
    }
    return `rgba(${a[0]},${a[1]},${a[2]},${(0.05 + v * 0.5).toFixed(3)})`;
  };
  const scoreInk = (v) => {
    if (v == null) return "var(--mut)";
    if (scale() === "div" && v < 0.5) return "#8a2f2b";
    return v >= 0.7 ? "var(--accent-ink)" : "var(--ink)";
  };

  // Radar chart. series: [{tech, color, fillOpacity}]
  function Radar({ series, size = 230, max = 1 }) {
    const cx = size / 2, cy = size / 2 - 4, R = size * 0.34;
    const ang = [-90, 0, 90, 180];
    const pt = (i, r) => {
      const a = ang[i] * Math.PI / 180;
      return [cx + Math.cos(a) * R * (r / max), cy + Math.sin(a) * R * (r / max)];
    };
    const rings = [0.25, 0.5, 0.75, 1];
    return (
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ display: "block" }}>
        {rings.map((r, k) => (
          <polygon key={k} points={[0,1,2,3].map((i)=>pt(i, r*max).join(",")).join(" ")} fill="none" stroke="#EBEDF0" strokeWidth="1" />
        ))}
        {[0,1,2,3].map((i)=>{ const [x,y]=pt(i,max); return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#EBEDF0" strokeWidth="1" />; })}
        {series.map((s, si) => {
          const vals = METRIC_ORDER.map((m) => metricVal(s.tech, m) ?? 0);
          const poly = vals.map((v, i) => pt(i, v).join(",")).join(" ");
          const col = s.color || "var(--accent)";
          return (
            <g key={si}>
              <polygon points={poly} fill={col} fillOpacity={s.fillOpacity ?? 0.16} stroke={col} strokeWidth="2" />
              {vals.map((v, i) => { const [x, y] = pt(i, v); return <circle key={i} cx={x} cy={y} r="3" fill={col} />; })}
            </g>
          );
        })}
        {METRIC_ORDER.map((m, i) => { const [x, y] = pt(i, max * 1.2); return (
          <text key={m} x={x} y={y} fontSize="10.5" fontWeight="600" fill="#7c828a" textAnchor="middle" dominantBaseline="middle" fontFamily="'IBM Plex Sans KR',sans-serif">{METRICS[m].abbr}</text>
        ); })}
      </svg>
    );
  }

  // Compact metric tooltip body for a technique
  function MetricTipBody({ tech }) {
    return (
      <React.Fragment>
        <b>{TECH[tech].ko}</b> · {TECH[tech].en}<br/>
        {METRIC_ORDER.map((m, i) => (
          <span key={m}>{METRICS[m].abbr} {fmt(metricVal(tech, m))}{i < 3 ? "  " : ""}</span>
        ))}
      </React.Fragment>
    );
  }

  function useHoverTip() {
    const [hover, setHover] = React.useState(null);
    const bind = (tech) => ({
      onMouseMove: (e) => setHover({ tech, x: e.clientX, y: e.clientY }),
      onMouseLeave: () => setHover(null),
    });
    const Tip = hover ? (
      <div className="tip mono" style={{ left: hover.x + 14, top: hover.y + 16 }}>
        <MetricTipBody tech={hover.tech} />
      </div>
    ) : null;
    return { bind, Tip };
  }

  window.RAGUI = { fmt, scoreBg, scoreInk, Radar, MetricTipBody, useHoverTip };
})();
