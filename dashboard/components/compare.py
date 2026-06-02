"""페이지 1 - 기법 비교 (RAGAS 메트릭 차트)."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.data import METRIC_NAMES, empty_state, latest_by_technique
from dashboard.components.labels import (
    METRICS,
    TECHNIQUES,
    metric_desc,
    metric_ko,
    technique_card,
    technique_ko,
    technique_ko_full,
)

# 13개 기법용 색상 팔레트 (Plotly Vivid)
TECH_COLORS = [
    "#5e72e4", "#11cdef", "#2dce89", "#fb6340", "#f5365c",
    "#8965e0", "#ff9f43", "#172b4d", "#6c757d", "#11cdef",
    "#2dce89", "#fb6340", "#f5365c",
]


def render_compare() -> None:
    st.header("기법 비교 - RAGAS 메트릭")
    st.caption("저장된 평가 결과 중 기법별 가장 최신 1개씩 로드합니다. 점수는 0~1 범위이며 1에 가까울수록 좋습니다.")

    with st.expander("이 페이지 가이드", expanded=False):
        st.markdown("13개 RAG 기법을 4가지 메트릭으로 정량 비교합니다.")
        st.markdown("메트릭 설명")
        for name in METRIC_NAMES:
            st.markdown(f"1. {METRICS[name]['ko']} - {METRICS[name]['desc']}")
        st.markdown("그래프 보는 법 - 막대 차트는 한 메트릭 기준 기법 순위, 레이더 차트는 한 기법의 4가지 메트릭 균형. 하단 expander에서 기법별 의미와 점수를 같이 보세요.")

    results = latest_by_technique()
    if not results:
        empty_state()
        return

    rows: list[dict] = []
    for tech, item in sorted(results.items()):
        summary = item["data"].get("summary", {})
        row = {"기법": technique_ko(tech), "_tech_id": tech}
        for m in METRIC_NAMES:
            row[METRICS[m]["ko"]] = float(summary.get(m, 0.0))
        rows.append(row)

    # 1) 메트릭별 막대 차트
    st.subheader("막대 차트 - 한 메트릭으로 기법 순위")
    metric_choice = st.selectbox(
        "비교할 메트릭",
        METRIC_NAMES,
        index=0,
        format_func=metric_ko,
    )
    st.info(f"{metric_ko(metric_choice)} - {metric_desc(metric_choice)}")

    ko_choice = METRICS[metric_choice]["ko"]
    sorted_rows = sorted(rows, key=lambda r: r[ko_choice], reverse=True)
    fig = px.bar(
        sorted_rows,
        x=ko_choice,
        y="기법",
        text=ko_choice,
        orientation="h",
        title=f"{ko_choice} (1에 가까울수록 좋음)",
        color=ko_choice,
        color_continuous_scale="Tealgrn",
        range_color=[0, 1],
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside", cliponaxis=False)
    fig.update_layout(
        height=480,
        margin=dict(l=10, r=40, t=60, b=20),
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        bargap=0.45,
        font=dict(size=13),
        title=dict(font=dict(size=15)),
    )
    fig.update_xaxes(range=[0, 1.08], title="점수", showgrid=True, gridcolor="rgba(160,160,160,0.2)")
    fig.update_yaxes(title="", categoryorder="total ascending")
    st.plotly_chart(fig, use_container_width=True)

    # 2) 레이더 차트
    st.subheader("레이더 차트 - 4가지 메트릭 균형")
    st.caption("여러 기법을 같이 그리면 어느 메트릭에서 차이가 나는지 한눈에 보입니다.")
    tech_options = sorted(results.keys())
    selected = st.multiselect(
        "기법 선택 (여러 개)",
        tech_options,
        default=tech_options[: min(3, len(tech_options))],
        format_func=technique_ko,
    )
    if selected:
        ko_metrics = [METRICS[m]["ko"] for m in METRIC_NAMES]
        radar = go.Figure()
        for i, t in enumerate(selected):
            r = next(row for row in rows if row["_tech_id"] == t)
            color = TECH_COLORS[tech_options.index(t) % len(TECH_COLORS)]
            radar.add_trace(
                go.Scatterpolar(
                    r=[r[m] for m in ko_metrics] + [r[ko_metrics[0]]],
                    theta=ko_metrics + [ko_metrics[0]],
                    fill="toself",
                    name=technique_ko(t),
                    line=dict(color=color, width=2),
                    fillcolor=color,
                    opacity=0.35,
                )
            )
        radar.update_layout(
            polar=dict(
                radialaxis=dict(range=[0, 1], visible=True, showline=False, gridcolor="rgba(160,160,160,0.3)"),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            height=520,
            margin=dict(l=40, r=40, t=40, b=80),
            font=dict(size=13),
        )
        st.plotly_chart(radar, use_container_width=True)

    # 3) 기법별 상세
    st.subheader("기법별 상세 설명 + 점수")
    for row in sorted_rows:
        tid = row["_tech_id"]
        with st.expander(technique_ko_full(tid), expanded=False):
            st.markdown(technique_card(tid))
            st.markdown("점수")
            for m in METRIC_NAMES:
                ko = METRICS[m]["ko"]
                st.markdown(f"1. {ko} : {row[ko]:.3f}")
