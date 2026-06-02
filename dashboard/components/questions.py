"""페이지 2 - 질문별로 기법들의 답변/컨텍스트를 나란히 비교."""

from __future__ import annotations

import streamlit as st

from dashboard.components.data import empty_state, latest_by_technique
from dashboard.components.labels import METRICS, technique_card, technique_ko


def render_questions() -> None:
    st.header("2. 질문별 결과 보기")
    st.caption("저장된 평가 결과에서 같은 질문에 대해 기법들이 어떤 답변과 컨텍스트를 만들었는지 비교합니다.")

    with st.expander("이 페이지 가이드", expanded=False):
        st.markdown("이 페이지는 한 질문을 골라 여러 기법의 답변을 나란히 비교하는 페이지입니다. 정답과 답변을 같이 보면 어느 기법이 환각을 일으키는지, 어느 기법이 핵심을 놓치는지 파악할 수 있습니다.")
        st.markdown("사용 흐름")
        st.markdown("1. 질문 드롭다운에서 보고 싶은 질문 선택")
        st.markdown("1. 비교할 기법을 여러 개 선택 (3개 이상 권장)")
        st.markdown("1. 정답(파란 박스)과 각 기법의 답변, 사용된 컨텍스트를 비교")

    results = latest_by_technique()
    if not results:
        empty_state()
        return

    questions: dict[str, dict[str, dict]] = {}
    for tech, item in results.items():
        by_q = item["data"].get("by_question", [])
        for row in by_q:
            q = row.get("question") or row.get("user_input", "")
            if not q:
                continue
            questions.setdefault(q, {})[tech] = row

    if not questions:
        empty_state("저장된 결과에 질문별 정보가 없습니다. ragas_eval.py 를 다시 실행하세요.")
        return

    q_list = list(questions.keys())
    selected_q = st.selectbox("질문 선택", q_list)
    techs_for_q = sorted(questions[selected_q].keys())
    selected_techs = st.multiselect(
        "기법 선택 (여러 개)",
        techs_for_q,
        default=techs_for_q[: min(3, len(techs_for_q))],
        format_func=technique_ko,
    )

    if not selected_techs:
        st.warning("기법을 1개 이상 선택하세요.")
        return

    sample = next(iter(questions[selected_q].values()))
    gt = sample.get("ground_truth") or sample.get("reference")
    if gt:
        st.markdown("정답 (ground truth)")
        st.info(gt)

    cols = st.columns(len(selected_techs))
    for col, tech in zip(cols, selected_techs, strict=True):
        row = questions[selected_q][tech]
        with col:
            st.subheader(technique_ko(tech))
            with st.expander("기법 설명", expanded=False):
                st.markdown(technique_card(tech))
            st.markdown("답변")
            st.write(row.get("answer", ""))
            st.markdown("사용된 컨텍스트")
            ctxs = row.get("contexts") or row.get("retrieved_contexts") or []
            for i, c in enumerate(ctxs, 1):
                preview = c if len(c) < 300 else c[:300] + "..."
                st.markdown(f"{i}. {preview}")

            # 메트릭 점수가 있으면 같이 표시
            shown_any = False
            for m_name, meta in METRICS.items():
                v = row.get(m_name)
                if v is None:
                    continue
                if not shown_any:
                    st.markdown("메트릭 점수")
                    shown_any = True
                try:
                    st.markdown(f"1. {meta['ko']} ({m_name}) : {float(v):.3f}")
                except (TypeError, ValueError):
                    st.markdown(f"1. {meta['ko']} ({m_name}) : 측정 실패")
