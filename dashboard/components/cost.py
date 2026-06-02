"""페이지 4 - 비용/지연 추적 시각화."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from dashboard.components.data import empty_state, latest_by_technique
from dashboard.components.labels import technique_ko


def render_cost() -> None:
    st.header("4. 비용 / 지연 추적")
    st.caption("저장된 평가 결과의 토큰 사용량과 시간을 시각화합니다. 인덱싱 단계와 추론 단계를 분리해 봅니다.")

    with st.expander("이 페이지 가이드", expanded=False):
        st.markdown("이 페이지는 기법별로 얼마나 무거운지를 정량적으로 보는 페이지입니다. 비용/시간/호출수 세 축으로 비교합니다.")
        st.markdown("표시되는 비용은 LLM 공급자의 유료 단가를 기준으로 환산한 추정치입니다. 미스트랄 무료 티어 사용 시 실제 청구는 0 이며, 본 레포는 가격 테이블을 0 으로 두어서 추정 비용도 0 으로 표시됩니다.")
        st.markdown("인덱싱 단계 - 문서를 벡터/그래프/트리로 가공해 저장하는 1회성 작업")
        st.markdown("추론 단계 - 사용자 질문을 받아 검색 + 답변 생성하는 반복 작업")
        st.markdown("판단 기준 - 인덱싱 비용은 한 번만 들고 추론 비용은 호출당 발생하므로 운영 비용 비교는 추론 비용을 더 중요하게 보세요.")

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
                "기법": technique_ko(tech),
                "인덱싱 비용 (USD)": float(idx_totals.get("cost_usd", 0.0)),
                "추론 비용 (USD)": float(inf_totals.get("cost_usd", 0.0)),
                "인덱싱 호출수": int(idx_totals.get("calls", 0)),
                "추론 호출수": int(inf_totals.get("calls", 0)),
                "인덱싱 시간 (초)": float(idx_totals.get("elapsed_seconds", 0.0)),
                "추론 시간 (초)": float(inf_totals.get("elapsed_seconds", 0.0)),
                "인덱싱 토큰합": int(idx_totals.get("input_tokens", 0)) + int(idx_totals.get("output_tokens", 0)),
                "추론 토큰합": int(inf_totals.get("input_tokens", 0)) + int(inf_totals.get("output_tokens", 0)),
            }
        )

    if all(r["인덱싱 비용 (USD)"] == 0 and r["추론 비용 (USD)"] == 0 and r["인덱싱 호출수"] == 0 and r["추론 호출수"] == 0 for r in rows):
        empty_state("저장된 결과에 토큰 사용량 정보가 없습니다. 최신 ragas_eval.py 로 다시 실행하면 자동 캡처됩니다.")
        return

    common_layout = dict(
        plot_bgcolor="rgba(0,0,0,0)",
        bargap=0.45,
        font=dict(size=13),
        height=420,
        margin=dict(l=40, r=20, t=60, b=120),
        legend=dict(orientation="h", yanchor="bottom", y=-0.45, xanchor="center", x=0.5),
    )
    palette = ["#5e72e4", "#11cdef"]

    st.subheader("LLM 호출 횟수 (인덱싱 vs 추론)")
    st.caption("미스트랄 무료 티어는 분당 호출 한도가 있어서, 호출수가 많은 기법일수록 평가 시간이 오래 걸립니다.")
    fig_calls = px.bar(
        rows,
        x="기법",
        y=["인덱싱 호출수", "추론 호출수"],
        barmode="stack",
        title="기법별 LLM 호출 횟수",
        labels={"value": "호출 수", "variable": "단계"},
        color_discrete_sequence=palette,
    )
    fig_calls.update_layout(**common_layout)
    fig_calls.update_xaxes(tickangle=-20, title="")
    st.plotly_chart(fig_calls, use_container_width=True)

    st.subheader("LLM 호출에 걸린 시간 (초)")
    st.caption("호출 한 건당 응답 시간 합계. 지연이 크면 사용자 체감 응답성이 떨어집니다.")
    fig_time = px.bar(
        rows,
        x="기법",
        y=["인덱싱 시간 (초)", "추론 시간 (초)"],
        barmode="stack",
        title="기법별 LLM 누적 호출 시간",
        labels={"value": "초", "variable": "단계"},
        color_discrete_sequence=palette,
    )
    fig_time.update_layout(**common_layout)
    fig_time.update_xaxes(tickangle=-20, title="")
    st.plotly_chart(fig_time, use_container_width=True)

    st.subheader("추정 비용 (USD)")
    st.caption("미스트랄 무료 티어 운영 시 0 으로 표시됩니다. 유료 전환 검토 시 이 값이 실비용 기준이 됩니다.")
    fig_cost = px.bar(
        rows,
        x="기법",
        y=["인덱싱 비용 (USD)", "추론 비용 (USD)"],
        barmode="stack",
        title="기법별 LLM 비용 합계",
        labels={"value": "USD", "variable": "단계"},
        color_discrete_sequence=palette,
    )
    fig_cost.update_layout(**common_layout)
    fig_cost.update_xaxes(tickangle=-20, title="")
    st.plotly_chart(fig_cost, use_container_width=True)

    st.subheader("기법별 상세 (줄바꿈 + 콜론 형식)")
    for row in rows:
        with st.expander(row["기법"]):
            st.markdown(f"1. 인덱싱 비용 : ${row['인덱싱 비용 (USD)']:.5f}")
            st.markdown(f"1. 추론 비용 : ${row['추론 비용 (USD)']:.5f}")
            st.markdown(f"1. 인덱싱 호출수 : {row['인덱싱 호출수']}")
            st.markdown(f"1. 추론 호출수 : {row['추론 호출수']}")
            st.markdown(f"1. 인덱싱 시간 : {row['인덱싱 시간 (초)']:.1f} 초")
            st.markdown(f"1. 추론 시간 : {row['추론 시간 (초)']:.1f} 초")
            st.markdown(f"1. 인덱싱 토큰 합 : {row['인덱싱 토큰합']}")
            st.markdown(f"1. 추론 토큰 합 : {row['추론 토큰합']}")
