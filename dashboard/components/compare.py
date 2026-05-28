"""페이지 1 - 기법 비교 (RAGAS 메트릭 차트)."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.data import METRIC_NAMES, empty_state, latest_by_technique


def render_compare() -> None:
    st.header("1. 기법 비교 - RAGAS 메트릭")
    st.caption("저장된 평가 결과(evaluation/results/) 중 기법별 가장 최신 1개씩 로드합니다.")

    results = latest_by_technique()
    if not results:
        empty_state()
        return

    rows: list[dict] = []
    for tech, item in sorted(results.items()):
        summary = item["data"].get("summary", {})
        row = {"technique": tech}
        for m in METRIC_NAMES:
            row[m] = float(summary.get(m, 0.0))
        rows.append(row)

    st.subheader("막대 차트 - 메트릭별 비교")
    metric_choice = st.selectbox("메트릭 선택", METRIC_NAMES, index=0)
    sorted_rows = sorted(rows, key=lambda r: r[metric_choice], reverse=True)
    fig = px.bar(
        sorted_rows,
        x="technique",
        y=metric_choice,
        text=metric_choice,
        title=f"{metric_choice} - 기법별 점수",
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig.update_yaxes(range=[0, 1])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("레이더 차트 - 한 기법의 4종 메트릭")
    techs = sorted(results.keys())
    selected = st.multiselect("기법 선택 (여러 개 가능)", techs, default=techs[: min(3, len(techs))])
    if selected:
        radar = go.Figure()
        for t in selected:
            r = next(row for row in rows if row["technique"] == t)
            radar.add_trace(
                go.Scatterpolar(
                    r=[r[m] for m in METRIC_NAMES] + [r[METRIC_NAMES[0]]],
                    theta=METRIC_NAMES + [METRIC_NAMES[0]],
                    fill="toself",
                    name=t,
                )
            )
        radar.update_layout(
            polar=dict(radialaxis=dict(range=[0, 1], visible=True)),
            showlegend=True,
        )
        st.plotly_chart(radar, use_container_width=True)

    st.subheader("원본 점수 (줄바꿈+콜론 형식)")
    for row in sorted_rows:
        with st.expander(row["technique"], expanded=False):
            for m in METRIC_NAMES:
                st.markdown(f"1. {m} : {row[m]:.3f}")
