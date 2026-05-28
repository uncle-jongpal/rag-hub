"""페이지 4 - 비용/지연 추적 시각화."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from dashboard.components.data import empty_state, latest_by_technique


def render_cost() -> None:
    st.header("4. 비용 / 지연 추적")
    st.caption("저장된 평가 결과의 usage 통계를 시각화합니다. 인덱싱과 추론을 분리해 봅니다.")

    results = latest_by_technique()
    if not results:
        empty_state()
        return

    rows: list[dict] = []
    for tech, item in sorted(results.items()):
        usage = item["data"].get("usage", {})
        idx_totals = usage.get("indexing", {}).get("totals", {})
        inf_totals = usage.get("inference", {}).get("totals", {})
        rows.append(
            {
                "technique": tech,
                "indexing_cost": float(idx_totals.get("cost_usd", 0.0)),
                "inference_cost": float(inf_totals.get("cost_usd", 0.0)),
                "indexing_calls": int(idx_totals.get("calls", 0)),
                "inference_calls": int(inf_totals.get("calls", 0)),
                "indexing_time": float(idx_totals.get("elapsed_seconds", 0.0)),
                "inference_time": float(inf_totals.get("elapsed_seconds", 0.0)),
                "indexing_tokens": int(idx_totals.get("input_tokens", 0)) + int(idx_totals.get("output_tokens", 0)),
                "inference_tokens": int(inf_totals.get("input_tokens", 0)) + int(inf_totals.get("output_tokens", 0)),
            }
        )

    if all(r["indexing_cost"] == 0 and r["inference_cost"] == 0 for r in rows):
        empty_state("저장된 결과에 usage 항목이 없습니다. 최신 ragas_eval.py 로 다시 실행하면 자동 캡처됩니다.")
        return

    st.subheader("비용 (USD) - 인덱싱 vs 추론")
    fig_cost = px.bar(
        rows,
        x="technique",
        y=["indexing_cost", "inference_cost"],
        barmode="stack",
        title="기법별 LLM 비용 합계",
        labels={"value": "USD", "variable": "단계"},
    )
    st.plotly_chart(fig_cost, use_container_width=True)

    st.subheader("LLM 호출 시간 (초)")
    fig_time = px.bar(
        rows,
        x="technique",
        y=["indexing_time", "inference_time"],
        barmode="stack",
        title="기법별 LLM 누적 호출 시간",
        labels={"value": "초", "variable": "단계"},
    )
    st.plotly_chart(fig_time, use_container_width=True)

    st.subheader("호출 수")
    fig_calls = px.bar(
        rows,
        x="technique",
        y=["indexing_calls", "inference_calls"],
        barmode="stack",
        title="기법별 LLM 호출 횟수",
    )
    st.plotly_chart(fig_calls, use_container_width=True)

    st.subheader("원본 표 (줄바꿈+콜론 형식)")
    for row in rows:
        with st.expander(row["technique"]):
            st.markdown(f"1. 인덱싱 비용 : ${row['indexing_cost']:.5f}")
            st.markdown(f"1. 추론 비용 : ${row['inference_cost']:.5f}")
            st.markdown(f"1. 인덱싱 호출 수 : {row['indexing_calls']}")
            st.markdown(f"1. 추론 호출 수 : {row['inference_calls']}")
            st.markdown(f"1. 인덱싱 시간 : {row['indexing_time']:.1f}초")
            st.markdown(f"1. 추론 시간 : {row['inference_time']:.1f}초")
            st.markdown(f"1. 인덱싱 토큰 합 : {row['indexing_tokens']}")
            st.markdown(f"1. 추론 토큰 합 : {row['inference_tokens']}")
