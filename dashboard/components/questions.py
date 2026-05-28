"""페이지 2 - 질문별로 기법들의 답변/컨텍스트를 나란히 비교."""

from __future__ import annotations

import streamlit as st

from dashboard.components.data import empty_state, latest_by_technique


def render_questions() -> None:
    st.header("2. 질문별 결과 보기")
    st.caption("저장된 평가 결과에서 같은 질문에 대해 기법들이 어떤 답변/컨텍스트를 만들었는지 비교합니다.")

    results = latest_by_technique()
    if not results:
        empty_state()
        return

    questions: dict[str, dict[str, dict]] = {}
    for tech, item in results.items():
        by_q = item["data"].get("by_question", [])
        for row in by_q:
            q = row.get("question", "")
            if not q:
                continue
            questions.setdefault(q, {})[tech] = row

    if not questions:
        empty_state("저장된 결과에 by_question 항목이 없습니다. ragas_eval.py 를 최신 버전으로 다시 실행하세요.")
        return

    q_list = list(questions.keys())
    selected_q = st.selectbox("질문 선택", q_list)
    techs_for_q = sorted(questions[selected_q].keys())
    selected_techs = st.multiselect("기법 선택 (여러 개)", techs_for_q, default=techs_for_q[: min(3, len(techs_for_q))])

    if not selected_techs:
        st.warning("기법을 1개 이상 선택하세요.")
        return

    sample = next(iter(questions[selected_q].values()))
    if "ground_truth" in sample:
        st.markdown("정답 (ground truth)")
        st.info(sample["ground_truth"])

    cols = st.columns(len(selected_techs))
    for col, tech in zip(cols, selected_techs, strict=True):
        row = questions[selected_q][tech]
        with col:
            st.subheader(tech)
            st.markdown("답변")
            st.write(row.get("answer", ""))
            st.markdown("사용된 컨텍스트")
            ctxs = row.get("contexts", [])
            for i, c in enumerate(ctxs, 1):
                preview = c if len(c) < 300 else c[:300] + "..."
                st.markdown(f"{i}. {preview}")
